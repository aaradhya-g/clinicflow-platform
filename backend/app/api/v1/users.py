from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, require_any_staff, require_admin
from app.models.user import DoctorProfile, User, UserRole
from app.schemas.user import DoctorProfileRead, UserRead

router = APIRouter()


@router.get("/doctors", response_model=List[DoctorProfileRead])
async def list_doctors(
    current_user: User = Depends(require_any_staff),
    db: AsyncSession = Depends(get_db),
):
    """Returns active doctors with specialty, room number, and availability."""
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.is_available == True)
    )
    result = await db.execute(stmt)
    profiles = result.scalars().all()

    doctor_list = []
    for p in profiles:
        doctor_list.append(
            DoctorProfileRead(
                id=p.id,
                user_id=p.user_id,
                specialty=p.specialty,
                license_number=p.license_number,
                room_number=p.room_number,
                consultation_fee=float(p.consultation_fee),
                is_available=p.is_available,
                full_name=p.user.full_name if p.user else None,
                email=p.user.email if p.user else None,
            )
        )
    return doctor_list


@router.get("/staff", response_model=List[UserRead])
async def list_staff(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to view clinic staff directory."""
    stmt = select(User).order_by(User.role.asc(), User.full_name.asc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.patch("/doctors/{doctor_id}/availability", response_model=DoctorProfileRead)
async def toggle_doctor_availability(
    doctor_id: uuid.UUID,
    is_available: bool,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to update doctor availability for scheduling."""
    stmt = (
        select(DoctorProfile)
        .options(selectinload(DoctorProfile.user))
        .where(DoctorProfile.id == doctor_id)
    )
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found",
        )

    profile.is_available = is_available
    await db.flush()

    return DoctorProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        specialty=profile.specialty,
        license_number=profile.license_number,
        room_number=profile.room_number,
        consultation_fee=float(profile.consultation_fee),
        is_available=profile.is_available,
        full_name=profile.user.full_name if profile.user else None,
        email=profile.user.email if profile.user else None,
    )
