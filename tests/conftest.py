"""Shared pytest fixtures.

The fixture below provisions a fresh SQLite database file per test, attaches
the FK-enforcement PRAGMA hook, runs the schema bootstrap against it, and
yields a session factory. Each test gets a clean DB; pytest's ``tmp_path``
handles cleanup.
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def fresh_db(tmp_path: Path) -> Engine:
    """Return a fresh SQLite engine with schema.sql applied and FKs on.

    Tests can bind a session to this engine and use ``src.database.seed.seed``
    with an explicit session to populate it.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'agentcare.db'}", future=True)

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        if engine.dialect.name == "sqlite":
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA foreign_keys = ON")
            cur.close()

    # Apply schema.sql via the production code path (so we exercise it).
    from src.database.bootstrap import bootstrap

    bootstrap(engine=engine)

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_for(fresh_db: Engine):
    """Return a callable that opens a session bound to ``fresh_db``."""
    Session = sessionmaker(bind=fresh_db, autoflush=False, autocommit=False)

    def _open() -> Session:
        return Session()

    return _open
