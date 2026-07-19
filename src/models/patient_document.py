"""PatientDocument ORM model."""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database.base import Base


class PatientDocument(Base):
    __tablename__ = "PatientDocument"

    id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), ForeignKey("PatientProfile.id"))
    document_type = Column(String(100))
    file_path = Column(String(512), nullable=False)
    document_date = Column(Date)
    checksum = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("PatientProfile", back_populates="documents")
