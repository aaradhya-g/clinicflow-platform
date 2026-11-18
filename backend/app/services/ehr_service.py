from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.appointment import Appointment, AppointmentStatus
from app.models.clinical import ClinicalConsultation, Prescription, VitalsRecord
from app.models.patient import Patient, PatientMedicalHistory
from app.models.user import User, DoctorProfile
from app.schemas.clinical import ConsultationCreate
from app.core.audit import log_audit_event


async def get_patient_ehr_timeline(
    db: AsyncSession,
    patient_id: uuid.UUID,
    current_user: User,
    ip_address: str,
) -> Dict[str, Any]:
    """Retrieves full longitudinal medical record timeline for a patient."""
    # 1. Fetch patient with baseline medical history
    pat_stmt = (
        select(Patient)
        .options(selectinload(Patient.medical_history))
        .where(Patient.id == patient_id)
    )
    patient = (await db.execute(pat_stmt)).scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # 2. Fetch past consultations with doctor and prescriptions
    consult_stmt = (
        select(ClinicalConsultation)
        .options(
            selectinload(ClinicalConsultation.prescriptions),
            selectinload(ClinicalConsultation.appointment).selectinload(Appointment.vitals),
            selectinload(ClinicalConsultation.appointment).selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
        )
        .where(ClinicalConsultation.patient_id == patient_id)
        .order_by(ClinicalConsultation.created_at.desc())
    )
    consultations = (await db.execute(consult_stmt)).scalars().all()

    # Log HIPAA read access
    await log_audit_event(
        db=db,
        action="READ_PATIENT_EHR",
        resource_type="PATIENT",
        resource_id=str(patient.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=ip_address,
        details={"patient_mrn": patient.mrn, "patient_name": f"{patient.first_name} {patient.last_name}"},
    )

    history_data = None
    if patient.medical_history:
        history_data = {
            "blood_type": patient.medical_history.blood_type,
            "allergies": patient.medical_history.allergies,
            "chronic_conditions": patient.medical_history.chronic_conditions,
            "current_medications": patient.medical_history.current_medications,
            "surgical_history": patient.medical_history.surgical_history,
        }

    encounters = []
    for c in consultations:
        apt = c.appointment
        vitals_dict = None
        if apt and apt.vitals:
            vitals_dict = {
                "bp": f"{apt.vitals.systolic_bp}/{apt.vitals.diastolic_bp}",
                "heart_rate": apt.vitals.heart_rate,
                "temperature_c": float(apt.vitals.temperature_c),
                "spo2": apt.vitals.spo2_percentage,
                "bmi": float(apt.vitals.bmi) if apt.vitals.bmi else None,
            }

        encounters.append({
            "id": str(c.id),
            "date": str(c.created_at.date()),
            "doctor_name": apt.doctor.user.full_name if (apt and apt.doctor and apt.doctor.user) else "Attending Physician",
            "specialty": apt.doctor.specialty if (apt and apt.doctor) else "Clinical Medicine",
            "chief_complaint": c.chief_complaint,
            "clinical_notes": c.clinical_notes,
            "diagnosis_codes": c.diagnosis_codes,
            "follow_up_date": str(c.follow_up_date) if c.follow_up_date else None,
            "vitals": vitals_dict,
            "prescriptions": [
                {
                    "medication_name": rx.medication_name,
                    "dosage": rx.dosage,
                    "frequency": rx.frequency,
                    "duration": rx.duration,
                    "instructions": rx.instructions,
                }
                for rx in c.prescriptions
            ],
        })

    return {
        "patient": {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": str(patient.date_of_birth),
            "gender": patient.gender,
            "phone": patient.phone,
            "email": patient.email,
            "insurance_provider": patient.insurance_provider,
            "insurance_policy_number": patient.insurance_policy_number,
            "insurance_status": patient.insurance_status.value,
        },
        "medical_history": history_data,
        "encounters": encounters,
    }


async def record_clinical_consultation(
    db: AsyncSession,
    consultation_in: ConsultationCreate,
    current_user: User,
    ip_address: str,
) -> ClinicalConsultation:
    """Records doctor's clinical findings, diagnoses, and structured prescriptions."""
    # Find appointment and doctor
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor),
            selectinload(Appointment.patient),
            selectinload(Appointment.vitals),
        )
        .where(Appointment.id == consultation_in.appointment_id)
    )
    appointment = (await db.execute(stmt)).scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    # Verify existing consultation doesn't already exist
    existing_stmt = select(ClinicalConsultation).where(ClinicalConsultation.appointment_id == consultation_in.appointment_id)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A clinical consultation has already been recorded for this appointment.",
        )

    # Create consultation
    consultation = ClinicalConsultation(
        id=uuid.uuid4(),
        appointment_id=consultation_in.appointment_id,
        patient_id=consultation_in.patient_id,
        doctor_id=appointment.doctor_id,
        chief_complaint=consultation_in.chief_complaint,
        clinical_notes=consultation_in.clinical_notes,
        diagnosis_codes=consultation_in.diagnosis_codes,
        follow_up_date=consultation_in.follow_up_date,
    )
    db.add(consultation)
    await db.flush()

    # Add structured prescriptions
    rx_names = []
    for rx_in in consultation_in.prescriptions:
        prescription = Prescription(
            id=uuid.uuid4(),
            consultation_id=consultation.id,
            patient_id=consultation_in.patient_id,
            medication_name=rx_in.medication_name,
            dosage=rx_in.dosage,
            frequency=rx_in.frequency,
            duration=rx_in.duration,
            instructions=rx_in.instructions,
        )
        db.add(prescription)
        rx_names.append(rx_in.medication_name)

    # Mark appointment as Completed
    appointment.status = AppointmentStatus.COMPLETED
    await db.flush()

    # Log HIPAA audit event
    await log_audit_event(
        db=db,
        action="COMPLETE_CONSULTATION",
        resource_type="CONSULTATION",
        resource_id=str(consultation.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=ip_address,
        details={
            "patient_mrn": appointment.patient.mrn,
            "prescriptions_count": len(consultation_in.prescriptions),
            "prescribed_medications": rx_names,
            "diagnosis_count": len(consultation_in.diagnosis_codes),
        },
    )

    return consultation
