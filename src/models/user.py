"""User and PatientProfile ORM models."""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class User(Base):
    __tablename__ = "User"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient_profile = relationship(
        "PatientProfile", back_populates="user", uselist=False
    )
    escalations_reviewed = relationship(
        "Escalation", back_populates="reviewer"
    )


class PatientProfile(Base):
    __tablename__ = "PatientProfile"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("User.id"))
    date_of_birth = Column(Date, nullable=False)
    phone = Column(String(20))
    preferred_language = Column(String(50))
    emergency_contact = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")
    documents = relationship("PatientDocument", back_populates="patient")
    workflow_runs = relationship("WorkflowRun", back_populates="patient")
    reminders = relationship("Reminder", back_populates="patient")
