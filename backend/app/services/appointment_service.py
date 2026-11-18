from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import DoctorProfile, User
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, SlotAvailability
from app.core.audit import log_audit_event


STANDARD_SLOTS = [
    ("09:00", "09:30"),
    ("09:30", "10:00"),
    ("10:00", "10:30"),
    ("10:30", "11:00"),
    ("11:00", "11:30"),
    ("11:30", "12:00"),
    ("13:30", "14:00"),
    ("14:00", "14:30"),
    ("14:30", "15:00"),
    ("15:00", "15:30"),
    ("15:30", "16:00"),
    ("16:00", "16:30"),
]


async def check_doctor_availability(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    appointment_date: date,
) -> List[SlotAvailability]:
    """Returns availability for all standard consultation slots for a doctor on a specific date."""
    # Fetch all active (non-cancelled) appointments for that doctor and date
    stmt = select(Appointment.start_time).where(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
    )
    result = await db.execute(stmt)
    booked_times = {row[0].strftime("%H:%M") for row in result.all()}

    slots = []
    for start, end in STANDARD_SLOTS:
        slots.append(
            SlotAvailability(
                start_time=start,
                end_time=end,
                is_available=(start not in booked_times),
            )
        )
    return slots


async def create_appointment_with_lock(
    db: AsyncSession,
    appointment_in: AppointmentCreate,
    current_user: User,
    ip_address: str,
) -> Appointment:
    """
    Creates an appointment atomically.
    Executes a SELECT FOR UPDATE to prevent race-condition double-booking.
    """
    # 1. Verify doctor exists and is active
    doc_stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.id == appointment_in.doctor_id)
    )
    doctor = (await db.execute(doc_stmt)).scalar_one_or_none()
    if not doctor or not doctor.is_available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The specified doctor is unavailable or does not exist.",
        )

    # 2. Verify patient exists
    pat_stmt = select(Patient).where(Patient.id == appointment_in.patient_id)
    patient = (await db.execute(pat_stmt)).scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found.",
        )

    # 3. Check for conflicting appointments with row-level lock
    # In PostgreSQL, with_for_update locks any conflicting row found.
    conflict_stmt = (
        select(Appointment)
        .where(
            Appointment.doctor_id == appointment_in.doctor_id,
            Appointment.appointment_date == appointment_in.appointment_date,
            Appointment.start_time == appointment_in.start_time,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
        )
    )
    if "postgresql" in settings.DATABASE_URL:
        conflict_stmt = conflict_stmt.with_for_update()
    existing_conflict = (await db.execute(conflict_stmt)).scalar_one_or_none()

    if existing_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Double-Booking Prevented: Dr. {doctor.user.full_name} is already booked at {appointment_in.start_time.strftime('%H:%M')} on {appointment_in.appointment_date}.",
        )

    # 4. Insert the new appointment
    new_appointment = Appointment(
        id=uuid.uuid4(),
        patient_id=appointment_in.patient_id,
        doctor_id=appointment_in.doctor_id,
        appointment_date=appointment_in.appointment_date,
        start_time=appointment_in.start_time,
        end_time=appointment_in.end_time,
        status=AppointmentStatus.SCHEDULED,
        reason_for_visit=appointment_in.reason_for_visit,
        reminder_sent=False,
    )
    db.add(new_appointment)
    await db.flush()

    # 5. Log HIPAA audit event
    await log_audit_event(
        db=db,
        action="CREATE_APPOINTMENT",
        resource_type="APPOINTMENT",
        resource_id=str(new_appointment.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=ip_address,
        details={
            "patient_mrn": patient.mrn,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "doctor_name": doctor.user.full_name,
            "date": str(appointment_in.appointment_date),
            "start_time": appointment_in.start_time.strftime("%H:%M"),
        },
    )

    return new_appointment
