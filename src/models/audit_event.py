"""AuditEvent ORM model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from ..database.base import Base


class AuditEvent(Base):
    __tablename__ = "AuditEvent"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(36), nullable=False)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=False)
    # SQL column is `metadata`; Python attribute is `metadata_json` to avoid
    # shadowing SQLAlchemy's `Base.metadata`.
    metadata_json = Column("metadata", Text)
    created_at = Column(DateTime, default=datetime.utcnow)
