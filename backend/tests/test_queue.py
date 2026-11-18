from datetime import date, time
import pytest
import uuid
from httpx import AsyncClient
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole, DoctorProfile
from app.models.patient import Patient, InsuranceStatus


@pytest.mark.asyncio
async def test_queue_state_machine_and_vitals(client: AsyncClient, db_session):
    # Setup test users
    doc_user = User(
        id=uuid.uuid4(),
        email="doc.queue@clinicflow.med",
        password_hash=get_password_hash("Pass123!"),
        full_name="Dr. Queue Tester",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    rec_user = User(
        id=uuid.uuid4(),
        email="rec.queue@clinicflow.med",
        password_hash=get_password_hash("Pass123!"),
        full_name="Receptionist Queue",
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    db_session.add_all([doc_user, rec_user])
    await db_session.flush()

    doctor_prof = DoctorProfile(
        id=uuid.uuid4(),
        user_id=doc_user.id,
        specialty="Pediatrics",
        license_number="LIC-PED-99",
        room_number="102",
        consultation_fee=160.0,
        is_available=True,
    )
    pat = Patient(
        id=uuid.uuid4(),
        mrn="CF-2026-QUEUE",
        first_name="Queue",
        last_name="Patient",
        date_of_birth=date(1995, 5, 5),
        gender="Female",
        phone="555-QUEUE",
        email="queue@example.com",
        insurance_status=InsuranceStatus.VERIFIED,
    )
    db_session.add_all([doctor_prof, pat])
    await db_session.commit()

    rec_token = create_access_token(rec_user.id, rec_user.role.value, rec_user.email)
    doc_token = create_access_token(doc_user.id, doc_user.role.value, doc_user.email)
    rec_headers = {"Authorization": f"Bearer {rec_token}"}
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # 1. Book appointment (starts in 'Scheduled')
    book_resp = await client.post(
        "/appointments/",
        headers=rec_headers,
        json={
            "patient_id": str(pat.id),
            "doctor_id": str(doctor_prof.id),
            "appointment_date": "2026-12-05",
            "start_time": "14:00:00",
            "end_time": "14:30:00",
            "reason_for_visit": "Fever and cough",
        },
    )
    assert book_resp.status_code == 201
    apt_id = book_resp.json()["id"]

    # 2. Check-in patient
    checkin_resp = await client.post(
        f"/queue/{apt_id}/transition",
        headers=rec_headers,
        json={"status": "Checked-In"},
    )
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["status"] == "Checked-In"

    # 3. Attempting to enter 'In-Consultation' BEFORE recording vitals must fail with 400
    bad_transition = await client.post(
        f"/queue/{apt_id}/transition",
        headers=doc_headers,
        json={"status": "In-Consultation"},
    )
    assert bad_transition.status_code == 400
    assert "Vital signs must be recorded" in bad_transition.json()["detail"]

    # 4. Record vitals
    vitals_resp = await client.post(
        "/queue/vitals",
        headers=rec_headers,
        json={
            "appointment_id": apt_id,
            "patient_id": str(pat.id),
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "temperature_c": 37.2,
            "spo2_percentage": 99,
            "respiratory_rate": 16,
            "weight_kg": 65.0,
            "height_cm": 170.0,
        },
    )
    assert vitals_resp.status_code == 201
    assert vitals_resp.json()["bmi"] == 22.5

    # 5. Now entering 'In-Consultation' succeeds
    good_transition = await client.post(
        f"/queue/{apt_id}/transition",
        headers=doc_headers,
        json={"status": "In-Consultation"},
    )
    assert good_transition.status_code == 200
    assert good_transition.json()["status"] == "In-Consultation"
