import enum
import uuid
from datetime import date, time
from typing import Optional
from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, String, Text, Time, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    CHECKED_IN = "Checked-In"
    IN_CONSULTATION = "In-Consultation"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No-Show"


class Appointment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "appointments"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("doctor_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    reason_for_visit: Mapped[str] = mapped_column(Text, nullable=False)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    doctor: Mapped["DoctorProfile"] = relationship("DoctorProfile", back_populates="appointments")
    vitals: Mapped[Optional["VitalsRecord"]] = relationship(
        "VitalsRecord",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    consultation: Mapped[Optional["ClinicalConsultation"]] = relationship(
        "ClinicalConsultation",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Composite unique constraint to guarantee no two appointments book the same doctor slot
        UniqueConstraint("doctor_id", "appointment_date", "start_time", name="uq_doctor_date_slot"),
        # Index on (doctor_id, appointment_date) for schedule filtering
        Index("ix_appointments_doctor_date", "doctor_id", "appointment_date"),
        # Index on (appointment_date, status) for receptionist live queue
        Index("ix_appointments_date_status", "appointment_date", "status"),
        # Index on (appointment_date, reminder_sent) for 24h cron reminder worker
        Index("ix_appointments_reminder", "appointment_date", "reminder_sent"),
    )
