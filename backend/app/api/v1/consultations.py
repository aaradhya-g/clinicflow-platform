from typing import Any, Dict
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user, get_client_ip, require_doctor, require_any_staff
from app.models.clinical import ClinicalConsultation
from app.models.user import User
from app.schemas.clinical import ConsultationCreate, ConsultationRead
from app.services.ehr_service import get_patient_ehr_timeline, record_clinical_consultation

router = APIRouter()


@router.get("/patient/{patient_id}/timeline")
async def get_ehr_timeline(
    patient_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full longitudinal electronic health record timeline for a patient."""
    client_ip = get_client_ip(request)
    return await get_patient_ehr_timeline(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
        ip_address=client_ip,
    )


@router.post("/", response_model=ConsultationRead, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation_in: ConsultationCreate,
    request: Request,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a completed physician consultation.
    Saves SOAP clinical notes, ICD diagnosis codes, and generates structured prescriptions.
    Automatically moves the appointment to 'Completed'.
    """
    client_ip = get_client_ip(request)
    consultation = await record_clinical_consultation(
        db=db,
        consultation_in=consultation_in,
        current_user=current_user,
        ip_address=client_ip,
    )

    # Reload with prescriptions for serialization
    stmt = (
        select(ClinicalConsultation)
        .options(selectinload(ClinicalConsultation.prescriptions))
        .where(ClinicalConsultation.id == consultation.id)
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return loaded


@router.get("/{consultation_id}", response_model=ConsultationRead)
async def get_consultation(
    consultation_id: uuid.UUID,
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Fetches a specific clinical encounter record."""
    stmt = (
        select(ClinicalConsultation)
        .options(selectinload(ClinicalConsultation.prescriptions))
        .where(ClinicalConsultation.id == consultation_id)
    )
    consultation = (await db.execute(stmt)).scalar_one_or_none()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found",
        )
    return consultation
