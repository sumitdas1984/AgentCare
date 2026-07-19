"""Appointment ORM model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class Appointment(Base):
    __tablename__ = "Appointment"

    id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), ForeignKey("PatientProfile.id"))
    doctor_id = Column(String(36), ForeignKey("Doctor.id"))
    slot_id = Column(String(36), ForeignKey("AppointmentSlot.id"))
    status = Column(String(50), default="pending")
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    patient = relationship("PatientProfile", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    slot = relationship("AppointmentSlot", back_populates="appointments")
