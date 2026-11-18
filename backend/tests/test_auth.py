import pytest
from httpx import AsyncClient
from app.core.security import get_password_hash
from app.models.user import User, UserRole
import uuid


@pytest.mark.asyncio
async def test_auth_and_rbac_flow(client: AsyncClient, db_session):
    # 1. Create a doctor user and a receptionist user
    doc_id = uuid.uuid4()
    doc_user = User(
        id=doc_id,
        email="test.doc@clinicflow.med",
        password_hash=get_password_hash("DocPass123!"),
        full_name="Dr. Test Physician",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    rec_id = uuid.uuid4()
    rec_user = User(
        id=rec_id,
        email="test.rec@clinicflow.med",
        password_hash=get_password_hash("RecPass123!"),
        full_name="Receptionist Tester",
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    db_session.add_all([doc_user, rec_user])
    await db_session.commit()

    # 2. Test successful login
    resp = await client.post("/auth/login", json={
        "email": "test.doc@clinicflow.med",
        "password": "DocPass123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "doctor"
    doctor_token = data["access_token"]

    # 3. Test invalid login password
    bad_resp = await client.post("/auth/login", json={
        "email": "test.doc@clinicflow.med",
        "password": "WrongPassword!"
    })
    assert bad_resp.status_code == 401

    # 4. Test RBAC: Doctor attempting to access Admin-only audit logs should return 403 Forbidden
    audit_resp = await client.get(
        "/audit/",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert audit_resp.status_code == 403
    assert "Access forbidden" in audit_resp.json()["detail"]

    # 5. Test Profile endpoint (/auth/me)
    me_resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test.doc@clinicflow.med"
