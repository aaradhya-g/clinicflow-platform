from datetime import date, datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user, get_client_ip, require_receptionist, require_any_staff
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import DoctorProfile, User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentStatusUpdate,
    SlotAvailability,
)
from app.services.appointment_service import (
    check_doctor_availability,
    create_appointment_with_lock,
)
from app.core.audit import log_audit_event

router = APIRouter()


def serialize_appointment(apt: Appointment) -> AppointmentRead:
    """Helper to convert ORM appointment to enriched read schema."""
    return AppointmentRead(
        id=apt.id,
        patient_id=apt.patient_id,
        doctor_id=apt.doctor_id,
        appointment_date=apt.appointment_date,
        start_time=apt.start_time,
        end_time=apt.end_time,
        status=apt.status,
        reason_for_visit=apt.reason_for_visit,
        reminder_sent=apt.reminder_sent,
        created_at=apt.created_at,
        patient_name=f"{apt.patient.first_name} {apt.patient.last_name}" if apt.patient else None,
        patient_mrn=apt.patient.mrn if apt.patient else None,
        patient_gender=apt.patient.gender if apt.patient else None,
        patient_dob=apt.patient.date_of_birth if apt.patient else None,
        insurance_status=apt.patient.insurance_status.value if apt.patient else None,
        doctor_name=apt.doctor.user.full_name if (apt.doctor and apt.doctor.user) else None,
        doctor_specialty=apt.doctor.specialty if apt.doctor else None,
        room_number=apt.doctor.room_number if apt.doctor else None,
        has_vitals=apt.vitals is not None,
        has_consultation=apt.consultation is not None,
    )


@router.get("/", response_model=List[AppointmentRead])
async def list_appointments(
    appointment_date: Optional[date] = None,
    doctor_id: Optional[uuid.UUID] = None,
    patient_id: Optional[uuid.UUID] = None,
    status_filter: Optional[AppointmentStatus] = None,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Lists appointments with optional filters for clinical schedule planning."""
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.vitals),
            selectinload(Appointment.consultation),
        )
    )

    if appointment_date:
        stmt = stmt.where(Appointment.appointment_date == appointment_date)
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter)

    stmt = stmt.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc())
    result = await db.execute(stmt)
    appointments = result.scalars().all()
    return [serialize_appointment(apt) for apt in appointments]


@router.get("/slots", response_model=List[SlotAvailability])
async def get_doctor_slots(
    doctor_id: uuid.UUID = Query(..., description="Target Doctor Profile ID"),
    target_date: date = Query(..., description="Date for consultation slot check"),
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Calculates available consultation slots for a doctor on a specific date."""
    return await check_doctor_availability(
        db=db,
        doctor_id=doctor_id,
        appointment_date=target_date,
    )


@router.post("/", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_in: AppointmentCreate,
    request: Request,
    current_user: User = Depends(require_receptionist),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates an appointment atomically using pessimistic row locks.
    Prevents double-booking race conditions.
    """
    client_ip = get_client_ip(request)
    created_apt = await create_appointment_with_lock(
        db=db,
        appointment_in=appointment_in,
        current_user=current_user,
        ip_address=client_ip,
    )

    # Reload with joined data for clean serialization
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.vitals),
            selectinload(Appointment.consultation),
        )
        .where(Appointment.id == created_apt.id)
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return serialize_appointment(loaded)


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
async def update_appointment_status(
    appointment_id: uuid.UUID,
    status_in: AppointmentStatusUpdate,
    request: Request,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Updates appointment status with audit trail."""
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.vitals),
            selectinload(Appointment.consultation),
        )
        .where(Appointment.id == appointment_id)
    )
    appointment = (await db.execute(stmt)).scalar_one_or_none()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    old_status = appointment.status
    appointment.status = status_in.status
    await db.flush()

    client_ip = get_client_ip(request)
    await log_audit_event(
        db=db,
        action="UPDATE_APPOINTMENT_STATUS",
        resource_type="APPOINTMENT",
        resource_id=str(appointment.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=client_ip,
        details={"old_status": old_status.value, "new_status": appointment.status.value},
    )

    return serialize_appointment(appointment)
