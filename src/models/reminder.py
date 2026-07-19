"""Reminder ORM model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database.base import Base


class Reminder(Base):
    __tablename__ = "Reminder"

    id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), ForeignKey("PatientProfile.id"))
    appointment_id = Column(String(36), ForeignKey("Appointment.id"))
    reminder_type = Column(String(100))
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="scheduled")

    patient = relationship("PatientProfile", back_populates="reminders")
    appointment = relationship("Appointment")
