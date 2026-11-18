from datetime import date, time, datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    start_time: time
    end_time: time
    reason_for_visit: str


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    reason_for_visit: str
    reminder_sent: bool
    created_at: datetime

    # Denormalized / Joined fields for UI convenience
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_dob: Optional[date] = None
    insurance_status: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    room_number: Optional[str] = None
    has_vitals: bool = False
    has_consultation: bool = False

    model_config = ConfigDict(from_attributes=True)


class SlotAvailability(BaseModel):
    start_time: str
    end_time: str
    is_available: bool
