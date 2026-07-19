"""Escalation ORM model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class Escalation(Base):
    __tablename__ = "Escalation"

    id = Column(String(36), primary_key=True)
    workflow_run_id = Column(String(36), ForeignKey("WorkflowRun.id"))
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="open")
    reviewed_by = Column(String(36), ForeignKey("User.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow_run = relationship("WorkflowRun", back_populates="escalations")
    reviewer = relationship("User", back_populates="escalations_reviewed")
