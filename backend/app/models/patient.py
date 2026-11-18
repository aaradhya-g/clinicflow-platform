import enum
import uuid
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy import Date, Enum, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class InsuranceStatus(str, enum.Enum):
    VERIFIED = "Verified"
    PENDING = "Pending"
    UNINSURED = "Uninsured"


class Patient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "patients"

    mrn: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_status: Mapped[InsuranceStatus] = mapped_column(
        Enum(InsuranceStatus, values_callable=lambda x: [e.value for e in x]),
        default=InsuranceStatus.PENDING,
        nullable=False,
    )

    # Relationships
    medical_history: Mapped[Optional["PatientMedicalHistory"]] = relationship(
        "PatientMedicalHistory",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class PatientMedicalHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "patient_medical_histories"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    blood_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    allergies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    chronic_conditions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    current_medications: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    surgical_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    patient: Mapped["Patient"] = relationship("Patient", back_populates="medical_history")
