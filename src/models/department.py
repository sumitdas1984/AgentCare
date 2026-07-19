"""Department and Doctor ORM models."""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class Department(Base):
    __tablename__ = "Department"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)

    doctors = relationship("Doctor", back_populates="department")


class Doctor(Base):
    __tablename__ = "Doctor"

    id = Column(String(36), primary_key=True)
    department_id = Column(String(36), ForeignKey("Department.id"))
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="doctors")
    slots = relationship("AppointmentSlot", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
