import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class VitalsRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "vitals_records"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    recorded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    systolic_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    spo2_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=16)
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    bmi: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="vitals")


class ClinicalConsultation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clinical_consultations"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("doctor_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_notes: Mapped[str] = mapped_column(Text, nullable=False)  # Full SOAP notes
    diagnosis_codes: Mapped[List[Dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="consultation")
    prescriptions: Mapped[List["Prescription"]] = relationship(
        "Prescription",
        back_populates="consultation",
        cascade="all, delete-orphan",
    )


class Prescription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prescriptions"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clinical_consultations.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )

    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    consultation: Mapped["ClinicalConsultation"] = relationship(
        "ClinicalConsultation",
        back_populates="prescriptions",
    )
