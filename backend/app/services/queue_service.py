from datetime import date, datetime, timezone
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.appointment import Appointment, AppointmentStatus
from app.models.clinical import VitalsRecord
from app.models.patient import Patient
from app.models.user import User, DoctorProfile
from app.schemas.clinical import VitalsCreate
from app.core.audit import log_audit_event


# Valid state transitions: Scheduled -> Checked-In -> In-Consultation -> Completed
ALLOWED_TRANSITIONS = {
    AppointmentStatus.SCHEDULED: [AppointmentStatus.CHECKED_IN, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW],
    AppointmentStatus.CHECKED_IN: [AppointmentStatus.IN_CONSULTATION, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW],
    AppointmentStatus.IN_CONSULTATION: [AppointmentStatus.COMPLETED],
    AppointmentStatus.COMPLETED: [],
    AppointmentStatus.CANCELLED: [],
    AppointmentStatus.NO_SHOW: [],
}


async def transition_queue_status(
    db: AsyncSession,
    appointment_id: uuid.UUID,
    new_status: AppointmentStatus,
    current_user: User,
    ip_address: str,
) -> Appointment:
    """Safely transitions an appointment along the clinical queue state machine."""
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
            selectinload(Appointment.vitals),
        )
        .where(Appointment.id == appointment_id)
    )
    appointment = (await db.execute(stmt)).scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment record not found.",
        )

    current_status = appointment.status
    if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid queue transition: Cannot transition appointment from '{current_status.value}' to '{new_status.value}'.",
        )

    # Clinical validation: Vitals must be recorded before entering consultation
    if new_status == AppointmentStatus.IN_CONSULTATION and not appointment.vitals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Triage protocol violation: Vital signs must be recorded before patient can enter consultation.",
        )

    appointment.status = new_status
    await db.flush()

    # Log audit event
    await log_audit_event(
        db=db,
        action="UPDATE_QUEUE_STATUS",
        resource_type="APPOINTMENT",
        resource_id=str(appointment.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=ip_address,
        details={
            "previous_status": current_status.value,
            "new_status": new_status.value,
            "patient_mrn": appointment.patient.mrn,
        },
    )

    return appointment


async def record_triage_vitals(
    db: AsyncSession,
    vitals_in: VitalsCreate,
    current_user: User,
    ip_address: str,
) -> VitalsRecord:
    """Records intake vitals and computes BMI automatically."""
    # Check appointment
    stmt = select(Appointment).where(Appointment.id == vitals_in.appointment_id)
    appointment = (await db.execute(stmt)).scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found for vitals intake.",
        )

    # Check if vitals already recorded for this visit
    existing_stmt = select(VitalsRecord).where(VitalsRecord.appointment_id == vitals_in.appointment_id)
    existing_vitals = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing_vitals:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vitals have already been recorded for this appointment.",
        )

    # Calculate BMI if weight and height provided
    computed_bmi = None
    if vitals_in.weight_kg and vitals_in.height_cm and vitals_in.height_cm > 0:
        height_m = vitals_in.height_cm / 100.0
        computed_bmi = round(vitals_in.weight_kg / (height_m * height_m), 1)

    vitals = VitalsRecord(
        id=uuid.uuid4(),
        appointment_id=vitals_in.appointment_id,
        patient_id=vitals_in.patient_id,
        recorded_by_user_id=current_user.id,
        systolic_bp=vitals_in.systolic_bp,
        diastolic_bp=vitals_in.diastolic_bp,
        heart_rate=vitals_in.heart_rate,
        temperature_c=vitals_in.temperature_c,
        spo2_percentage=vitals_in.spo2_percentage,
        respiratory_rate=vitals_in.respiratory_rate or 16,
        weight_kg=vitals_in.weight_kg,
        height_cm=vitals_in.height_cm,
        bmi=computed_bmi,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(vitals)
    await db.flush()

    await log_audit_event(
        db=db,
        action="RECORD_VITALS",
        resource_type="VITALS",
        resource_id=str(vitals.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=ip_address,
        details={
            "appointment_id": str(vitals_in.appointment_id),
            "bp": f"{vitals_in.systolic_bp}/{vitals_in.diastolic_bp}",
            "heart_rate": vitals_in.heart_rate,
            "spo2": vitals_in.spo2_percentage,
            "temperature_c": float(vitals_in.temperature_c),
            "bmi": computed_bmi,
        },
    )

    return vitals
