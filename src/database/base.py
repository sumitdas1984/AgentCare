"""SQLAlchemy engine, session factory, and declarative Base for AgentCare."""

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.environ.get("AGENTCARE_DATABASE_URL", "sqlite:///./agentcare.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite enforces FKs only when this PRAGMA is ON, and it's per-connection."""
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


Base = declarative_base()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def engine_url() -> str:
    """Return the resolved database URL."""
    return DATABASE_URL
