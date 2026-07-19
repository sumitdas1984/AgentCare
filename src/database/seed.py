"""Synthetic seed data for local development.

Populates:
  - 1 patient user  (alice@example.com / patient-pass)
  - 1 staff user    (bob@example.com   / staff-pass)
  - 3 Departments (Cardiology, Dermatology, Orthopedics)
  - 5 Doctors (across the departments)
  - 40 AppointmentSlots (2 days × 4 slots × 5 doctors)

All non-user IDs are deterministic via ``uuid.uuid5`` so re-running this
script does not duplicate rows (idempotent). The two seeded users have
fixed UUIDs so tests and demos can refer to them by id, but their
passwords are bcrypt-hashed and **must** be re-seeded if you change them
locally (the seed is idempotent on count, not on password).

No real PII.

Note: model imports are deferred to inside ``seed()`` / ``summary()`` to
break the circular import through ``src.models`` → ``src.database.base``.

Note: ``seed()`` and ``summary()`` accept an optional ``session``. Pass one
bound to a private engine to seed a database other than the module-level
one (used by the test suite). When omitted, they fall back to the production
``SessionLocal``.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..auth.passwords import hash_password
from .base import SessionLocal


_DEPARTMENTS = [
    ("Cardiology", "11111111-1111-1111-1111-111111111111"),
    ("Dermatology", "22222222-2222-2222-2222-222222222222"),
    ("Orthopedics", "33333333-3333-3333-3333-333333333333"),
]

_DOCTORS = [
    ("Doctor Cardiology One", _DEPARTMENTS[0][1]),
    ("Doctor Cardiology Two", _DEPARTMENTS[0][1]),
    ("Doctor Dermatology One", _DEPARTMENTS[1][1]),
    ("Doctor Orthopedics One", _DEPARTMENTS[2][1]),
    ("Doctor Orthopedics Two", _DEPARTMENTS[2][1]),
]

_DAYS_AHEAD = 2
_SLOTS_PER_DAY = 4
_START_HOUR = 9  # first slot starts at 09:00 local


# Seeded users — fixed UUIDs and well-known credentials so demos and tests
# can log in without first registering. Both passwords are weak by design
# and only safe for local development.
_SEED_USERS = [
    {
        "id": "aaaaaaaa-0000-0000-0000-000000000001",
        "email": "alice@example.com",
        "name": "Alice Patient",
        "role": "patient",
        "password": "patient-pass",
    },
    {
        "id": "bbbbbbbb-0000-0000-0000-000000000002",
        "email": "bob@example.com",
        "name": "Bob Staff",
        "role": "staff",
        "password": "staff-pass",
    },
]


def _doctor_id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"doctor:{name}"))


def _slot_id(doctor_name: str, start_iso: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"slot:{doctor_name}:{start_iso}"))


def seed(session: Optional[Session] = None) -> None:
    """Insert seed data if not already present.

    If ``session`` is omitted, ``SessionLocal()`` is used. The function
    never closes a session it didn't open.
    """
    # Deferred to break the import cycle described in the module docstring.
    from ..models import AppointmentSlot, Department, Doctor, User

    own_session = session is None
    session = session if session is not None else SessionLocal()

    try:
        if session.query(Department).count() > 0:
            return  # idempotent: already seeded

        # Seed users first (other tables may FK to them in future features).
        for spec in _SEED_USERS:
            session.add(
                User(
                    id=spec["id"],
                    name=spec["name"],
                    email=spec["email"],
                    password_hash=hash_password(spec["password"]),
                    role=spec["role"],
                    created_at=datetime.utcnow(),
                )
            )

        for name, dept_id in _DEPARTMENTS:
            session.add(
                Department(
                    id=dept_id,
                    name=name,
                    description=f"{name} department (synthetic seed)",
                    active=True,
                )
            )

        for name, dept_id in _DOCTORS:
            session.add(
                Doctor(
                    id=_doctor_id(name),
                    department_id=dept_id,
                    name=name,
                    active=True,
                )
            )
        session.flush()

        base_time = (
            datetime.utcnow().replace(microsecond=0, second=0, minute=0)
            + timedelta(days=1, hours=_START_HOUR)
        )
        for name, _ in _DOCTORS:
            for day_offset in range(_DAYS_AHEAD):
                for slot_idx in range(_SLOTS_PER_DAY):
                    start = base_time + timedelta(days=day_offset, hours=slot_idx)
                    session.add(
                        AppointmentSlot(
                            id=_slot_id(name, start.isoformat()),
                            doctor_id=_doctor_id(name),
                            start_time=start,
                            end_time=start + timedelta(hours=1),
                            status="available",
                        )
                    )

        session.commit()
    finally:
        if own_session:
            session.close()


def summary(session: Optional[Session] = None) -> dict[str, int]:
    """Return counts of seeded entities (for the verification script)."""
    from ..models import AppointmentSlot, Department, Doctor, User

    own_session = session is None
    session = session if session is not None else SessionLocal()
    try:
        return {
            "users": session.query(User).count(),
            "departments": session.query(Department).count(),
            "doctors": session.query(Doctor).count(),
            "slots": session.query(AppointmentSlot).count(),
        }
    finally:
        if own_session:
            session.close()


if __name__ == "__main__":
    # Run via: python -m src.database.bootstrap && python -m src.database.seed
    seed()
