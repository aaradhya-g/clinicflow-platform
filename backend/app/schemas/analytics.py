from typing import Dict, List
from pydantic import BaseModel


class StatusBreakdown(BaseModel):
    scheduled: int = 0
    checked_in: int = 0
    in_consultation: int = 0
    completed: int = 0
    cancelled: int = 0
    no_show: int = 0


class InsuranceBreakdown(BaseModel):
    verified: int = 0
    pending: int = 0
    uninsured: int = 0


class DoctorWorkload(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: str
    total_appointments: int
    completed_appointments: int
    utilization_rate: float


class DailyAppointmentVolume(BaseModel):
    date: str
    total: int
    completed: int


class ClinicKPIs(BaseModel):
    total_patients: int
    today_appointments: int
    completed_today: int
    no_show_rate: float
    average_wait_time_minutes: int
    status_breakdown: StatusBreakdown
    insurance_breakdown: InsuranceBreakdown
    doctor_workloads: List[DoctorWorkload]
    recent_volume: List[DailyAppointmentVolume]
