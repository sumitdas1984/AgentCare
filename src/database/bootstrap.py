"""Apply the AgentCare schema to the configured database.

Usage:
    python -m src.database.bootstrap             # uses AGENTCARE_DATABASE_URL
    python -m src.database.bootstrap sqlite:///:memory:

Idempotent: re-running leaves existing tables untouched (CREATE TABLE IF NOT EXISTS).
"""

from pathlib import Path

from sqlalchemy import create_engine, text

from .base import engine_url


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def bootstrap(database_url: str | None = None) -> None:
    """Apply schema.sql to the database at ``database_url``.

    Falls back to the URL resolved by ``src.database.base.engine_url``.
    The PRAGMA hook in ``base.py`` ensures FK enforcement on every connection.
    """
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    engine = create_engine(database_url or engine_url())

    try:
        with engine.begin() as conn:
            for stmt in _split_statements(schema_sql):
                conn.exec_driver_sql(stmt)
    finally:
        engine.dispose()

    # Sanity check: confirm critical tables exist (raises if bootstrap silently did nothing).
    expected = {"User", "Department", "Appointment", "WorkflowRun", "AuditEvent"}
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    present = {row[0] for row in rows}
    missing = expected - present
    if missing:
        raise RuntimeError(f"bootstrap incomplete, missing tables: {sorted(missing)}")


def _split_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements, dropping comments and blanks.

    SQLite's DBAPI driver rejects multi-statement scripts at the cursor layer
    (it allows only one statement per ``execute()``), so we split on ``;`` and
    skip comment-only / blank chunks before sending each one.
    """
    statements: list[str] = []
    for raw in sql.split(";"):
        lines = [
            line
            for line in raw.splitlines()
            if line.strip() and not line.lstrip().startswith("--")
        ]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            statements.append(cleaned)
    return statements


if __name__ == "__main__":
    bootstrap()
