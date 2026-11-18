import asyncio
from datetime import date, time
import pytest
import uuid
from httpx import AsyncClient
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole, DoctorProfile
from app.models.patient import Patient, InsuranceStatus


@pytest.mark.asyncio
async def test_appointment_double_booking_prevention(client: AsyncClient, db_session):
    # Setup test doctor and test patient
    doc_user = User(
        id=uuid.uuid4(),
        email="doc.concurrent@clinicflow.med",
        password_hash=get_password_hash("Pass123!"),
        full_name="Dr. Concurrent",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db_session.add(doc_user)
    await db_session.flush()

    doctor_prof = DoctorProfile(
        id=uuid.uuid4(),
        user_id=doc_user.id,
        specialty="General",
        license_number="LIC-CONC-01",
        room_number="101",
        consultation_fee=150.0,
        is_available=True,
    )
    pat1 = Patient(
        id=uuid.uuid4(),
        mrn="CF-2026-TEST1",
        first_name="Patient",
        last_name="One",
        date_of_birth=date(1990, 1, 1),
        gender="Male",
        phone="555-001",
        email="p1@example.com",
        insurance_status=InsuranceStatus.VERIFIED,
    )
    pat2 = Patient(
        id=uuid.uuid4(),
        mrn="CF-2026-TEST2",
        first_name="Patient",
        last_name="Two",
        date_of_birth=date(1992, 2, 2),
        gender="Female",
        phone="555-002",
        email="p2@example.com",
        insurance_status=InsuranceStatus.VERIFIED,
    )
    rec_user = User(
        id=uuid.uuid4(),
        email="rec.concurrent@clinicflow.med",
        password_hash=get_password_hash("Pass123!"),
        full_name="Receptionist",
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    db_session.add_all([doctor_prof, pat1, pat2, rec_user])
    await db_session.commit()

    rec_token = create_access_token(
        subject=rec_user.id,
        role=rec_user.role.value,
        email=rec_user.email,
    )
    headers = {"Authorization": f"Bearer {rec_token}"}

    target_date = "2026-12-01"
    start_time = "09:30:00"
    end_time = "10:00:00"

    # 1. Book first appointment - Should succeed with 201
    resp1 = await client.post(
        "/appointments/",
        headers=headers,
        json={
            "patient_id": str(pat1.id),
            "doctor_id": str(doctor_prof.id),
            "appointment_date": target_date,
            "start_time": start_time,
            "end_time": end_time,
            "reason_for_visit": "First booking",
        },
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["status"] == "Scheduled"

    # 2. Attempt duplicate booking for same doctor, date & start_time - MUST fail with 409 Conflict
    resp2 = await client.post(
        "/appointments/",
        headers=headers,
        json={
            "patient_id": str(pat2.id),
            "doctor_id": str(doctor_prof.id),
            "appointment_date": target_date,
            "start_time": start_time,
            "end_time": end_time,
            "reason_for_visit": "Conflicting second booking attempt",
        },
    )
    assert resp2.status_code == 409
    assert "Double-Booking Prevented" in resp2.json()["detail"]
