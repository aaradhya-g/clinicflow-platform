from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user, get_client_ip, require_receptionist, require_any_staff
from app.models.patient import Patient, PatientMedicalHistory, InsuranceStatus
from app.models.user import User
from app.schemas.patient import (
    InsuranceStatusUpdate,
    PatientCreate,
    PatientRead,
    PatientUpdate,
)
from app.core.audit import log_audit_event

router = APIRouter()


@router.get("/", response_model=List[PatientRead])
async def list_patients(
    query: Optional[str] = Query(None, description="Search by name, MRN, phone or email"),
    insurance_status: Optional[InsuranceStatus] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Lists registered patients with optional full-text search and insurance filter."""
    stmt = select(Patient).options(selectinload(Patient.medical_history))

    if query:
        search_pattern = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.mrn.ilike(search_pattern),
                Patient.phone.ilike(search_pattern),
                Patient.email.ilike(search_pattern),
            )
        )

    if insurance_status:
        stmt = stmt.where(Patient.insurance_status == insurance_status)

    stmt = stmt.order_by(Patient.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    patients = result.scalars().all()
    return patients


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a single patient record including baseline medical history."""
    stmt = (
        select(Patient)
        .options(selectinload(Patient.medical_history))
        .where(Patient.id == patient_id)
    )
    patient = (await db.execute(stmt)).scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    client_ip = get_client_ip(request)
    await log_audit_event(
        db=db,
        action="VIEW_PATIENT",
        resource_type="PATIENT",
        resource_id=str(patient.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=client_ip,
        details={"mrn": patient.mrn},
    )

    return patient


@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient_in: PatientCreate,
    request: Request,
    current_user: User = Depends(require_receptionist),
    db: AsyncSession = Depends(get_db),
):
    """Registers a new patient and creates baseline medical history."""
    # Generate unique MRN (Medical Record Number): CF-2026-XXXX
    count_stmt = select(func.count(Patient.id))
    current_count = (await db.execute(count_stmt)).scalar() or 0
    mrn = f"CF-2026-{(current_count + 1):04d}"

    # Verify email uniqueness
    email_check = (await db.execute(select(Patient).where(Patient.email == patient_in.email))).scalar_one_or_none()
    if email_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with this email address already exists.",
        )

    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        mrn=mrn,
        first_name=patient_in.first_name.strip(),
        last_name=patient_in.last_name.strip(),
        date_of_birth=patient_in.date_of_birth,
        gender=patient_in.gender,
        phone=patient_in.phone.strip(),
        email=patient_in.email.lower().strip(),
        address=patient_in.address,
        emergency_contact=patient_in.emergency_contact,
        insurance_provider=patient_in.insurance_provider,
        insurance_policy_number=patient_in.insurance_policy_number,
        insurance_status=patient_in.insurance_status,
    )
    db.add(patient)

    # Add baseline medical history if provided
    med_history_obj = None
    if patient_in.medical_history:
        med_history_obj = PatientMedicalHistory(
            id=uuid.uuid4(),
            patient_id=patient_id,
            blood_type=patient_in.medical_history.blood_type,
            allergies=patient_in.medical_history.allergies or [],
            chronic_conditions=patient_in.medical_history.chronic_conditions or [],
            current_medications=patient_in.medical_history.current_medications or [],
            surgical_history=patient_in.medical_history.surgical_history,
        )
        db.add(med_history_obj)
    else:
        med_history_obj = PatientMedicalHistory(
            id=uuid.uuid4(),
            patient_id=patient_id,
            blood_type=None,
            allergies=[],
            chronic_conditions=[],
            current_medications=[],
        )
        db.add(med_history_obj)

    await db.flush()

    client_ip = get_client_ip(request)
    await log_audit_event(
        db=db,
        action="REGISTER_PATIENT",
        resource_type="PATIENT",
        resource_id=str(patient.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=client_ip,
        details={
            "mrn": mrn,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "insurance_status": patient.insurance_status.value,
        },
    )

    # Reload patient with medical history
    reload_stmt = (
        select(Patient)
        .options(selectinload(Patient.medical_history))
        .where(Patient.id == patient_id)
    )
    return (await db.execute(reload_stmt)).scalar_one()


@router.patch("/{patient_id}/insurance", response_model=PatientRead)
async def update_insurance_status(
    patient_id: uuid.UUID,
    insurance_in: InsuranceStatusUpdate,
    request: Request,
    current_user: User = Depends(require_receptionist),
    db: AsyncSession = Depends(get_db),
):
    """Updates patient insurance verification status (Verified, Pending, Uninsured)."""
    stmt = (
        select(Patient)
        .options(selectinload(Patient.medical_history))
        .where(Patient.id == patient_id)
    )
    patient = (await db.execute(stmt)).scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    old_status = patient.insurance_status
    patient.insurance_status = insurance_in.insurance_status
    if insurance_in.insurance_provider is not None:
        patient.insurance_provider = insurance_in.insurance_provider
    if insurance_in.insurance_policy_number is not None:
        patient.insurance_policy_number = insurance_in.insurance_policy_number

    await db.flush()

    client_ip = get_client_ip(request)
    await log_audit_event(
        db=db,
        action="UPDATE_INSURANCE_STATUS",
        resource_type="PATIENT",
        resource_id=str(patient.id),
        user_id=current_user.id,
        role=current_user.role.value,
        ip_address=client_ip,
        details={
            "mrn": patient.mrn,
            "old_status": old_status.value,
            "new_status": patient.insurance_status.value,
        },
    )

    return patient
