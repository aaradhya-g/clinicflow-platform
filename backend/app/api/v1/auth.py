from datetime import timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.core.audit import log_audit_event
from app.api.deps import get_db, get_current_user, get_client_ip
from app.models.user import User, UserRole, DoctorProfile
from app.schemas.auth import LoginRequest, RefreshRequest, Token, TokenPayload

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates credentials and returns JWT access & refresh tokens."""
    stmt = (
        select(User)
        .options(selectinload(User.doctor_profile))
        .where(User.email == login_data.email.lower().strip())
    )
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
    )

    client_ip = get_client_ip(request)
    await log_audit_event(
        db=db,
        action="LOGIN_SUCCESS",
        resource_type="USER",
        resource_id=str(user.id),
        user_id=user.id,
        role=user.role.value,
        ip_address=client_ip,
        details={"email": user.email, "role": user.role.value},
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
        full_name=user.full_name,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generates a new access token using a valid refresh token."""
    try:
        payload = decode_token(refresh_data.refresh_token)
        token_payload = TokenPayload(**payload)
        if token_payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: Expected refresh token",
            )
        user_id = uuid.UUID(token_payload.sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or exists",
        )

    new_access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
    )

    return Token(
        access_token=new_access_token,
        refresh_token=refresh_data.refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
        full_name=user.full_name,
    )


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns profile and clinical metadata for authenticated user."""
    stmt = (
        select(User)
        .options(selectinload(User.doctor_profile))
        .where(User.id == current_user.id)
    )
    user = (await db.execute(stmt)).scalar_one()

    profile_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
    }

    if user.doctor_profile:
        profile_data["doctor_profile"] = {
            "id": str(user.doctor_profile.id),
            "specialty": user.doctor_profile.specialty,
            "license_number": user.doctor_profile.license_number,
            "room_number": user.doctor_profile.room_number,
            "consultation_fee": float(user.doctor_profile.consultation_fee),
            "is_available": user.doctor_profile.is_available,
        }

    return profile_data


@router.post("/demo-login/{role}", response_model=Token)
async def demo_role_login(
    role: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Convenience endpoint for instantaneous 1-click role testing.
    Finds the primary demo user for 'admin', 'doctor', or 'receptionist'.
    """
    target_role = role.lower()
    if target_role not in [UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.RECEPTIONIST.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo role '{role}'. Allowed: admin, doctor, receptionist",
        )

    stmt = select(User).where(User.role == target_role, User.is_active == True)
    user = (await db.execute(stmt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No seeded demo user found for role '{role}'. Please run the database seed script.",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
    )

    client_ip = get_client_ip(request)
    await log_audit_event(
        db=db,
        action="DEMO_SWITCH_LOGIN",
        resource_type="USER",
        resource_id=str(user.id),
        user_id=user.id,
        role=user.role.value,
        ip_address=client_ip,
        details={"demo_role": user.role.value, "email": user.email},
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
        full_name=user.full_name,
    )
