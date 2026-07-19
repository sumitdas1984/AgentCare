# FEATURE-9 Plan — Persistent Relational Schema (SQLite default)

## Context

- **GitHub issue:** [#9 — FEATURE-1.1](https://github.com/sumitdas1984/AgentCare/issues/9)
- **Parent:** EPIC-1 (Project Foundation & Data Layer) → INITIATIVE-1 (AgentCare MVP)
- **PRD reference:** `docs/PRD.md` §6 (the 11 SQL tables) and §8 (repo structure)
- **Branch:** `feature/FEATURE-9` (synced from `development`)
- **Why this exists first:** No other agent, UI, or auth code can run without the schema. It is the hard dependency for EPIC-1 → EPIC-6.

## Scope (FEATURE-level acceptance criteria)

- AC1 — Schema matches PRD §6 verbatim.
- AC2 — ORM navigates relationships without raw SQL.
- AC3 — Seed produces ≥3 departments, ≥5 doctors, ≥20 future slots, all synthetic.
- AC4 — Bootstrap is idempotent.

## Stories covered

- **STORY-1.1.1** — Schema for the 11 core entities
- **STORY-1.1.2** — SQLAlchemy ORM models
- **STORY-1.1.3** — Synthetic seed data module

## Implementation approach

- **Source of truth:** `src/database/schema.sql` (hand-written, transcribed from PRD §6).
- **Bootstrap:** Apply the schema via SQLAlchemy. Split statements before executing because SQLite's `cursor.execute()` rejects multi-statement scripts.
- **ORM:** SQLAlchemy 2.x declarative base; one model per table; relationships wired (`Doctor.department`, `Appointment.slot`, `WorkflowRun.escalations`, etc.).
- **Engine / session:** Centralized in `src/database/base.py`. A `connect` event listener enables `PRAGMA foreign_keys = ON` on every SQLite connection (per-connection, not persistent).
- **Seed:** Deterministic UUIDs via `uuid.uuid5(NAMESPACE_DNS, ...)`. Idempotent — guarded by a `Department.count() > 0` early-return.

## Schema decisions / corrections vs PRD §6

PRD §6 contains pseudo-SQL with the inline form `column TYPE FOREIGN KEY REFERENCES x(id)`, which SQLite rejects because `FOREIGN KEY` only belongs in a separate table-constraint clause. The translated schema uses the correct inline form `column TYPE REFERENCES x(id)` and keeps all other column/constraint details verbatim.

Other schema notes:

- BOOLEAN rendered as `INTEGER 0/1` (SQLite stores no native boolean; SQLAlchemy maps it back via the `Boolean` type).
- TIMESTAMP/DATE stored as `TEXT` by SQLite; SQLAlchemy maps them to `DateTime`/`Date`.
- Hot-path indexes added: `Appointment(patient_id)`, `WorkflowRun(status)`, `Escalation(status)`.

## Files in this scaffold

| Path | Role |
|---|---|
| `pyproject.toml` | + `sqlalchemy>=2.0,<3.0` |
| `src/database/schema.sql` | 11 tables + 3 indexes (PRD §6) |
| `src/database/base.py` | engine, `SessionLocal`, `Base`, FK PRAGMA hook |
| `src/database/bootstrap.py` | `bootstrap(database_url=None)` — idempotent applier |
| `src/database/seed.py` | `seed()`, `summary()` — 3 depts / 5 doctors / 40 slots |
| `src/database/__init__.py` | re-exports `bootstrap`, `seed` |
| `src/models/base.py` *(implicit via `src/database/base.py`)* | declarative `Base` |
| `src/models/user.py` | `User`, `PatientProfile` |
| `src/models/department.py` | `Department`, `Doctor` |
| `src/models/appointment_slot.py` | `AppointmentSlot` |
| `src/models/appointment.py` | `Appointment` |
| `src/models/patient_document.py` | `PatientDocument` |
| `src/models/workflow_run.py` | `WorkflowRun` |
| `src/models/reminder.py` | `Reminder` |
| `src/models/escalation.py` | `Escalation` |
| `src/models/audit_event.py` | `AuditEvent` (column `metadata`, attr `metadata_json` to avoid `Base.metadata` shadow) |
| `src/models/__init__.py` | re-exports for `from src.models import …` convenience |
| `src/__init__.py` | package marker |
| `.gitignore` | + `*.db`, `*.sqlite`, `*.sqlite3`, `/data/` |

## Verification (already passed on the scaffold)

```bash
uv run python -m src.database.bootstrap          # creates tables
uv run python -m src.database.seed               # populates fixtures
uv run python -m src.database.seed               # re-run: no duplicates (idempotent)
uv run python -c "from src.models import SessionLocal, Department
with SessionLocal() as s:
    print(s.query(Department).filter_by(name='Cardiology').one().doctors[0].slots[0].start_time)"
```

Expected outputs captured at scaffold time:

```
Seeded: {'departments': 3, 'doctors': 5, 'slots': 40}
After re-seeding: {'departments': 3, 'doctors': 5, 'slots': 40}
Cardiology: 2 doctors, 16 slots
  First slot: 2026-07-20 14:00:00 (available)
FK enforcement: ON (correctly rejected bad doctor_id)
```

## What's left to iterate (not blockers)

Priority order — top is highest.

1. **`datetime.utcnow()` deprecation warning** on Python 3.13. Switch to `datetime.now(UTC)` in `seed.py`. (Quick win.)
2. **`PatientProfile.user_id` should be `NOT NULL UNIQUE`** — one profile per user is the real-world invariant. Not in PRD §6 verbatim, but a correctness gap. Add to `schema.sql` and ORM.
3. **RuntimeWarning on `python -m src.database.bootstrap`** — `src.database.__init__.py` eagerly imports `bootstrap`, which causes Python's import machinery to flag the re-import. Cosmetic; fix by removing the eager re-export in `__init__.py` (callers can do `from src.database.bootstrap import bootstrap`).
4. **Circular-import fragility** — model imports inside `seed.py` are deferred into the function body to break the cycle. If anyone adds another eager top-level import in `seed.py`, the cycle will recur. Worth a comment in `seed.py` (already present) and a guard test.
5. **Slot start times shift on each fresh seed** — depend on `datetime.utcnow()`. For reproducible tests, anchor to a fixed `START_DATE` env var or generate times relative to a known offset.
6. **No unit tests yet** — ACs are met functionally but not locked in. Add `pytest` + a few fixtures (empty DB, seeded DB) and assert counts + FK rejection.
7. **No Alembic / migrations** — schema changes today require a manual re-bootstrap. Acceptable for the MVP, but worth tracking for the next iteration.
8. **No role/status enums** — `role VARCHAR(50)` and `status VARCHAR(50)` accept any string. Either add `CHECK` constraints or rely on app-level validation. (Currently app-level is fine for the MVP.)
9. **Engine/session singletons in `base.py`** — convenient for the scaffold; for tests that need per-test isolation, consider exposing a `make_engine(url)` factory instead of a module-level singleton.
10. **`AuditEvent.metadata` shadow** — currently worked around by naming the Python attr `metadata_json`. Consider a `Mapped[dict]` JSON column instead, for cleaner Python ergonomics.

## Critical files to read before iterating

- `docs/PRD.md` — §6 schema, §8 repo layout
- `src/database/schema.sql` — DDL source of truth
- `src/database/base.py` — engine/session/PRAGMA setup
- `src/database/bootstrap.py` — statement-splitting strategy (must change together if dialect targets change)
- `src/database/seed.py` — has the deferred-import comment that protects the cycle

## Out of scope (deferred to other features)

- FEATURE-1.2 (Auth & RBAC) — needs the schema done; that's why we did this first.
- EPIC-2 orchestration, EPIC-3 domain agents, etc.
- Streamlit UIs, real LLM client wiring, Alembic migrations, OpenTelemetry — all later.