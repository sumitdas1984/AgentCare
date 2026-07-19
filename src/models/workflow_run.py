"""WorkflowRun ORM model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class WorkflowRun(Base):
    __tablename__ = "WorkflowRun"

    id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), ForeignKey("PatientProfile.id"))
    current_step = Column(String(100))
    state = Column(Text)
    status = Column(String(50), default="running")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    patient = relationship("PatientProfile", back_populates="workflow_runs")
    escalations = relationship("Escalation", back_populates="workflow_run")
