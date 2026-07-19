"""AppointmentSlot ORM model."""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database.base import Base


class AppointmentSlot(Base):
    __tablename__ = "AppointmentSlot"

    id = Column(String(36), primary_key=True)
    doctor_id = Column(String(36), ForeignKey("Doctor.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), default="available")

    doctor = relationship("Doctor", back_populates="slots")
    appointments = relationship("Appointment", back_populates="slot")
