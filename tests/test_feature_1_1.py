"""Tests for FEATURE-1.1 — Persistent relational schema (SQLite default).

One test per acceptance criterion. The AC language is quoted verbatim in
each test so the link between test and AC is obvious.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker


# All 11 entities required by PRD §6. If bootstrap ever stops creating one
# of these, AC1 fails.
EXPECTED_TABLES = {
    "User",
    "PatientProfile",
    "Department",
    "Doctor",
    "AppointmentSlot",
    "Appointment",
    "PatientDocument",
    "WorkflowRun",
    "Reminder",
    "Escalation",
    "AuditEvent",
}


# --- AC1 — Schema matches PRD §6 verbatim ---
def test_ac1_bootstrap_creates_all_eleven_tables(fresh_db):
    """AC1: Schema matches PRD §6 verbatim.

    Asserts every table named in the PRD's 11-entity schema is present after
    bootstrap runs.
    """
    with fresh_db.connect() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
    actual = {row[0] for row in rows}

    missing = EXPECTED_TABLES - actual
    assert not missing, f"bootstrap did not create tables: {sorted(missing)}"


# --- AC2 — ORM navigates relationships without raw SQL ---
def test_ac2_orm_navigates_relationships(seeded_db):
    """AC2: ORM navigates relationships without raw SQL.

    Walks ``dept.doctors → doctor.slots → slot.start_time`` using only ORM
    attributes; no manual SQL joins.
    """
    from src.models import Department

    with seeded_db() as s:
        cardiology = s.query(Department).filter_by(name="Cardiology").one()
        assert cardiology.doctors, "Department.doctors should populate via relationship"
        first_doctor = cardiology.doctors[0]
        assert first_doctor.slots, "Doctor.slots should populate via relationship"
        first_slot = first_doctor.slots[0]
        assert first_slot.start_time is not None
        assert first_slot.status == "available"


# --- AC3 — Seed produces ≥3 departments, ≥5 doctors, ≥20 future slots, all synthetic ---
def test_ac3_seed_meets_minimum_counts_and_uses_uuid_ids(seeded_db):
    """AC3: Seed produces ≥3 departments, ≥5 doctors, ≥20 future slots, all synthetic.

    Counts and verifies every primary key is a UUID (i.e. synthetic, never
    real-world IDs).
    """
    from src.models import AppointmentSlot, Department, Doctor

    with seeded_db() as s:
        depts = s.query(Department).all()
        docs = s.query(Doctor).all()
        slots = s.query(AppointmentSlot).all()

    assert len(depts) >= 3, f"need ≥3 departments, got {len(depts)}"
    assert len(docs) >= 5, f"need ≥5 doctors, got {len(docs)}"
    assert len(slots) >= 20, f"need ≥20 slots, got {len(slots)}"

    # All IDs are valid UUIDs (synthetic, not real-world identifiers).
    for record in (*depts, *docs, *slots):
        try:
            uuid.UUID(record.id)
        except ValueError as e:
            raise AssertionError(
                f"{type(record).__name__}.id={record.id!r} is not a UUID"
            ) from e


# --- AC4 — Bootstrap is idempotent ---
def test_ac4_bootstrap_is_idempotent(fresh_db_with_no_seed):
    """AC4: Bootstrap is idempotent.

    Running bootstrap twice against the same engine is a no-op the second
    time — table set after the second call equals the table set after the
    first, and all 11 expected tables are present.
    """
    from src.database.bootstrap import bootstrap

    engine = fresh_db_with_no_seed

    bootstrap(engine=engine)
    with engine.connect() as conn:
        tables_after_first = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }

    bootstrap(engine=engine)
    with engine.connect() as conn:
        tables_after_second = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }

    assert tables_after_first == tables_after_second, (
        f"second bootstrap changed table set: "
        f"{tables_after_first ^ tables_after_second}"
    )
    assert EXPECTED_TABLES.issubset(tables_after_second)


# --- Composite fixtures built on top of `fresh_db` (in conftest.py) ---


@pytest.fixture
def seeded_db(fresh_db):
    """``fresh_db`` with seed data loaded; yields a session factory."""
    from src.database.seed import seed

    Session = sessionmaker(bind=fresh_db, autoflush=False, autocommit=False)
    with Session() as s:
        seed(session=s)
    return Session


@pytest.fixture
def fresh_db_with_no_seed(tmp_path):
    """A clean engine without bootstrap applied.

    The AC4 idempotency test uses this so it can bootstrap once and capture
    the table set, then bootstrap again and compare.
    """
    engine = create_engine(
        f"sqlite:///{tmp_path / 'no_seed.db'}", future=True
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        if engine.dialect.name == "sqlite":
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA foreign_keys = ON")
            cur.close()

    try:
        yield engine
    finally:
        engine.dispose()
