"""Session ORM model (added in FEATURE-1.2 for DB-backed sessions)."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database.base import Base


class Session(Base):
    __tablename__ = "Session"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("User.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
