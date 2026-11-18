from fastapi import APIRouter
from app.api.v1 import (
    analytics,
    appointments,
    audit,
    auth,
    consultations,
    patients,
    queue,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients & Insurance"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments & Scheduling"])
api_router.include_router(queue.router, prefix="/queue", tags=["Triage & Clinic Queue"])
api_router.include_router(consultations.router, prefix="/consultations", tags=["Clinical EHR & Prescriptions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Clinic Operational Analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["HIPAA Audit Logs"])
api_router.include_router(users.router, prefix="/users", tags=["Staff & Doctors"])
