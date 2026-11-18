from datetime import date, datetime
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class VitalsCreate(BaseModel):
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    systolic_bp: int = Field(..., ge=40, le=260, description="Systolic Blood Pressure (mmHg)")
    diastolic_bp: int = Field(..., ge=30, le=160, description="Diastolic Blood Pressure (mmHg)")
    heart_rate: int = Field(..., ge=30, le=240, description="Heart Rate / Pulse (BPM)")
    temperature_c: float = Field(..., ge=30.0, le=45.0, description="Body Temperature (°C)")
    spo2_percentage: int = Field(..., ge=50, le=100, description="Pulse Oximetry (%)")
    respiratory_rate: Optional[int] = Field(16, ge=6, le=60, description="Breaths per minute")
    weight_kg: Optional[float] = Field(None, ge=1.0, le=500.0)
    height_cm: Optional[float] = Field(None, ge=30.0, le=250.0)


class VitalsRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    recorded_by_user_id: Optional[uuid.UUID] = None
    systolic_bp: int
    diastolic_bp: int
    heart_rate: int
    temperature_c: float
    spo2_percentage: int
    respiratory_rate: Optional[int] = 16
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None


class PrescriptionRead(PrescriptionCreate):
    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationCreate(BaseModel):
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    chief_complaint: str
    clinical_notes: str  # SOAP Notes
    diagnosis_codes: List[Dict[str, str]] = []  # [{"code": "I10", "name": "Essential Hypertension"}]
    follow_up_date: Optional[date] = None
    prescriptions: List[PrescriptionCreate] = []


class ConsultationRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    chief_complaint: str
    clinical_notes: str
    diagnosis_codes: List[Dict[str, str]]
    follow_up_date: Optional[date] = None
    created_at: datetime
    prescriptions: List[PrescriptionRead] = []

    model_config = ConfigDict(from_attributes=True)
