from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.patient import InsuranceStatus


class MedicalHistoryBase(BaseModel):
    blood_type: Optional[str] = None
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    surgical_history: Optional[str] = None


class MedicalHistoryRead(MedicalHistoryBase):
    id: uuid.UUID
    patient_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str
    email: EmailStr
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_status: InsuranceStatus = InsuranceStatus.PENDING


class PatientCreate(PatientBase):
    medical_history: Optional[MedicalHistoryBase] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_status: Optional[InsuranceStatus] = None


class InsuranceStatusUpdate(BaseModel):
    insurance_status: InsuranceStatus
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None


class PatientRead(PatientBase):
    id: uuid.UUID
    mrn: str
    created_at: datetime
    updated_at: datetime
    medical_history: Optional[MedicalHistoryRead] = None

    model_config = ConfigDict(from_attributes=True)
