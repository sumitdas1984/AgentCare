"""Synthetic seed data for local development.

Populates:
  - 3 Departments (Cardiology, Dermatology, Orthopedics)
  - 5 Doctors (across the departments)
  - 40 AppointmentSlots (2 days × 4 slots × 5 doctors)

All IDs are deterministic via ``uuid.uuid5`` so re-running this script does
not duplicate rows (idempotent). No real PII.

Note: model imports are deferred to inside ``seed()`` / ``summary()`` to
break the circular import through ``src.models`` → ``src.database.base``.
"""

import uuid
from datetime import datetime, timedelta

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


def _doctor_id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"doctor:{name}"))


def _slot_id(doctor_name: str, start_iso: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"slot:{doctor_name}:{start_iso}"))


def seed() -> None:
    """Insert seed data if not already present."""
    # Deferred to break the import cycle described in the module docstring.
    from ..models import AppointmentSlot, Department, Doctor

    session = SessionLocal()
    try:
        if session.query(Department).count() > 0:
            return  # idempotent: already seeded

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
        session.close()


def summary() -> dict[str, int]:
    """Return counts of seeded entities (for the verification script)."""
    from ..models import AppointmentSlot, Department, Doctor

    session = SessionLocal()
    try:
        return {
            "departments": session.query(Department).count(),
            "doctors": session.query(Doctor).count(),
            "slots": session.query(AppointmentSlot).count(),
        }
    finally:
        session.close()


if __name__ == "__main__":
    # Run via: python -m src.database.bootstrap && python -m src.database.seed
    seed()
