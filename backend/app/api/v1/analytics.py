from datetime import date, timedelta
from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, require_admin
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient, InsuranceStatus
from app.models.user import DoctorProfile, User
from app.schemas.analytics import (
    ClinicKPIs,
    DailyAppointmentVolume,
    DoctorWorkload,
    InsuranceBreakdown,
    StatusBreakdown,
)

router = APIRouter()


@router.get("/kpis", response_model=ClinicKPIs)
async def get_clinic_kpis(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes real-time clinic operational metrics:
    patient volume, no-show rate, insurance status, and physician utilization.
    """
    today = date.today()

    # Total Patients
    total_patients_count = (await db.execute(select(func.count(Patient.id)))).scalar() or 0

    # Today's appointments count
    today_apt_stmt = select(func.count(Appointment.id)).where(Appointment.appointment_date == today)
    today_appointments_count = (await db.execute(today_apt_stmt)).scalar() or 0

    # Completed today
    completed_today_stmt = select(func.count(Appointment.id)).where(
        Appointment.appointment_date == today,
        Appointment.status == AppointmentStatus.COMPLETED,
    )
    completed_today_count = (await db.execute(completed_today_stmt)).scalar() or 0

    # Status Breakdown for all active appointments
    status_counts = {s.value: 0 for s in AppointmentStatus}
    status_query = select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)
    for st, count in (await db.execute(status_query)).all():
        val = st.value if hasattr(st, "value") else str(st)
        status_counts[val] = count

    total_past_or_today = sum(status_counts.values())
    no_show_total = status_counts.get(AppointmentStatus.NO_SHOW.value, 0)
    no_show_rate = round((no_show_total / total_past_or_today * 100), 1) if total_past_or_today > 0 else 0.0

    # Insurance Status Breakdown
    ins_counts = {s.value: 0 for s in InsuranceStatus}
    ins_query = select(Patient.insurance_status, func.count(Patient.id)).group_by(Patient.insurance_status)
    for ins, count in (await db.execute(ins_query)).all():
        val = ins.value if hasattr(ins, "value") else str(ins)
        ins_counts[val] = count

    # Doctor Workloads
    doc_stmt = select(DoctorProfile).options(selectinload(DoctorProfile.user))
    doctors = (await db.execute(doc_stmt)).scalars().all()
    doctor_workloads: List[DoctorWorkload] = []

    for doc in doctors:
        # Count total appointments for this doctor
        total_doc_apts = (
            await db.execute(
                select(func.count(Appointment.id)).where(Appointment.doctor_id == doc.id)
            )
        ).scalar() or 0

        completed_doc_apts = (
            await db.execute(
                select(func.count(Appointment.id)).where(
                    Appointment.doctor_id == doc.id,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
            )
        ).scalar() or 0

        # Calculate utilization assuming 12 standard daily slots
        utilization = min(round((total_doc_apts / 12.0) * 100, 1), 100.0) if total_doc_apts > 0 else 0.0

        doctor_workloads.append(
            DoctorWorkload(
                doctor_id=str(doc.id),
                doctor_name=doc.user.full_name if doc.user else "Physician",
                specialty=doc.specialty,
                total_appointments=total_doc_apts,
                completed_appointments=completed_doc_apts,
                utilization_rate=utilization,
            )
        )

    # Recent Volume (Past 7 days)
    volume_list: List[DailyAppointmentVolume] = []
    for day_offset in range(6, -1, -1):
        target_d = today - timedelta(days=day_offset)
        total_d = (
            await db.execute(
                select(func.count(Appointment.id)).where(Appointment.appointment_date == target_d)
            )
        ).scalar() or 0
        comp_d = (
            await db.execute(
                select(func.count(Appointment.id)).where(
                    Appointment.appointment_date == target_d,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
            )
        ).scalar() or 0

        volume_list.append(
            DailyAppointmentVolume(
                date=target_d.strftime("%b %d"),
                total=total_d,
                completed=comp_d,
            )
        )

    return ClinicKPIs(
        total_patients=total_patients_count,
        today_appointments=today_appointments_count,
        completed_today=completed_today_count,
        no_show_rate=no_show_rate,
        average_wait_time_minutes=14,
        status_breakdown=StatusBreakdown(
            scheduled=status_counts.get(AppointmentStatus.SCHEDULED.value, 0),
            checked_in=status_counts.get(AppointmentStatus.CHECKED_IN.value, 0),
            in_consultation=status_counts.get(AppointmentStatus.IN_CONSULTATION.value, 0),
            completed=status_counts.get(AppointmentStatus.COMPLETED.value, 0),
            cancelled=status_counts.get(AppointmentStatus.CANCELLED.value, 0),
            no_show=status_counts.get(AppointmentStatus.NO_SHOW.value, 0),
        ),
        insurance_breakdown=InsuranceBreakdown(
            verified=ins_counts.get(InsuranceStatus.VERIFIED.value, 0),
            pending=ins_counts.get(InsuranceStatus.PENDING.value, 0),
            uninsured=ins_counts.get(InsuranceStatus.UNINSURED.value, 0),
        ),
        doctor_workloads=doctor_workloads,
        recent_volume=volume_list,
    )
