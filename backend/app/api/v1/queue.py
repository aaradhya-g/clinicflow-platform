from datetime import date
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user, get_client_ip, require_any_staff, require_doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.models.clinical import VitalsRecord
from app.models.user import DoctorProfile, User
from app.schemas.appointment import AppointmentRead, AppointmentStatusUpdate
from app.schemas.clinical import VitalsCreate, VitalsRead
from app.services.queue_service import record_triage_vitals, transition_queue_status
from app.api.v1.appointments import serialize_appointment

router = APIRouter()


@router.get("/live", response_model=List[AppointmentRead])
async def get_live_queue(
    target_date: Optional[date] = None,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns today's live clinic triage queue board for receptionists and clinical staff.
    Includes active visits across all doctors with vitals indicators.
    """
    check_date = target_date or date.today()

    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.vitals),
            selectinload(Appointment.consultation),
        )
        .where(
            Appointment.appointment_date == check_date,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
        )
        .order_by(Appointment.start_time.asc())
    )
    result = await db.execute(stmt)
    appointments = result.scalars().all()
    return [serialize_appointment(apt) for apt in appointments]


@router.get("/today/doctor", response_model=List[AppointmentRead])
async def get_doctor_today_queue(
    doctor_profile_id: Optional[uuid.UUID] = Query(None, description="Doctor profile ID override for admin inspection"),
    target_date: Optional[date] = None,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns today's filtered queue for a physician showing triage vitals upfront.
    If current_user is a doctor, defaults to their own profile.
    """
    doc_id = doctor_profile_id
    if not doc_id:
        if current_user.doctor_profile:
            doc_id = current_user.doctor_profile.id
        else:
            # If admin querying without param, pick the first doctor
            first_doc = (await db.execute(select(DoctorProfile))).scalars().first()
            if first_doc:
                doc_id = first_doc.id

    if not doc_id:
        return []

    check_date = target_date or date.today()

    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.vitals),
            selectinload(Appointment.consultation),
        )
        .where(
            Appointment.doctor_id == doc_id,
            Appointment.appointment_date == check_date,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
        )
        .order_by(Appointment.start_time.asc())
    )
    result = await db.execute(stmt)
    appointments = result.scalars().all()
    return [serialize_appointment(apt) for apt in appointments]


@router.post("/vitals", response_model=VitalsRead, status_code=status.HTTP_201_CREATED)
async def intake_vitals(
    vitals_in: VitalsCreate,
    request: Request,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Records triage vital signs during patient intake and calculates BMI."""
    client_ip = get_client_ip(request)
    vitals = await record_triage_vitals(
        db=db,
        vitals_in=vitals_in,
        current_user=current_user,
        ip_address=client_ip,
    )
    return vitals


@router.get("/vitals/{appointment_id}", response_model=Optional[VitalsRead])
async def get_appointment_vitals(
    appointment_id: uuid.UUID,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves recorded vitals for a specific appointment."""
    stmt = select(VitalsRecord).where(VitalsRecord.appointment_id == appointment_id)
    vitals = (await db.execute(stmt)).scalar_one_or_none()
    return vitals


@router.post("/{appointment_id}/transition", response_model=AppointmentRead)
async def transition_appointment(
    appointment_id: uuid.UUID,
    transition_in: AppointmentStatusUpdate,
    request: Request,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """
    Enforces clinical queue progression state machine.
    Scheduled -> Checked-In -> In-Consultation -> Completed.
    """
    client_ip = get_client_ip(request)
    updated_apt = await transition_queue_status(
        db=db,
        appointment_id=appointment_id,
        new_status=transition_in.status,
        current_user=current_user,
        ip_address=client_ip,
    )
    return serialize_appointment(updated_apt)
