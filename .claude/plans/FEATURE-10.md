# FEATURE-10 Plan — Authentication & RBAC

## Context

- **GitHub issue:** [#10 — FEATURE-1.2](https://github.com/sumitdas1984/AgentCare/issues/10)
- **Parent:** [EPIC-1](https://github.com/sumitdas1984/AgentCare/issues/3) (Project Foundation & Data Layer) → INITIATIVE-1
- **Depends on:** [FEATURE-1.1 (#9)](https://github.com/sumitdas1984/AgentCare/issues/9) — landed in `development`. The `User` table from FEATURE-1.1 is the substrate here.
- **Branch:** `feature/FEATURE-10` (synced from `development`)
- **Why this exists second:** Without auth, no other agent or UI can know who is calling. It's the next hard dependency after the schema.

## Scope (FEATURE-level acceptance criteria)

- AC1 — Patients and staff can register and log in.
- AC2 — Backend rejects patient-role calls to staff endpoints with 403.
- AC3 — Sessions persist via DB-backed tokens.

## Stories covered

- **STORY-1.2.1** — User registration & login
- **STORY-1.2.2** — Role enforcement (patient / staff)
- **STORY-1.2.3** — Session management

## Implementation approach

### Library choices

- **Password hashing:** **bcrypt** — declared in `pyproject.toml`. Argon2 was the other PRD-allowed option; bcrypt wins on tooling maturity + simpler API.
- **No HTTP framework yet.** Story 1.2.x defines service-layer methods, not endpoints. The future HTTP layer (FastAPI or similar) will translate `@require_role` failures to 403. The two Streamlit UIs (FEATURE-5.1 / 5.2) call the service layer directly.
- **No JWT.** The AC explicitly says "DB-backed tokens", so we issue opaque tokens and look them up server-side.

### Architecture

New package: `src/auth/`

```
src/auth/
├── __init__.py        # public exports
├── exceptions.py      # InvalidCredentialsError, PermissionDeniedError, ...
├── passwords.py       # bcrypt hash + verify
└── service.py         # register, login, logout, current_user, require_role
```

`require_role` is implemented as a **service-layer decorator**, not HTTP middleware — same reason: no HTTP framework yet. The decorator raises `PermissionDeniedError`; the future HTTP layer will translate it to 403.

### Schema addition — new `Session` table

FEATURE-1.1's schema (PRD §6) does not include a sessions table. To satisfy AC3 (DB-backed tokens) we need persistent session state. Two options were considered:

1. Add `session_token` + `session_expires_at` columns to `User`.
2. Add a new `Session` table.

Option 2 is cleaner: keeps `User` lean, gives sessions their own lifecycle, leaves room for future fields (`ip_address`, `user_agent`, `revoked_at`, …). One additional table on top of PRD §6 is a small, well-justified deviation.

New table:

```sql
CREATE TABLE Session (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES User(id),
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_session_token ON Session(token);
CREATE INDEX ix_session_user_id ON Session(user_id);
```

Indexes mirror the hot-path index pattern from FEATURE-1.1.

**Backward compatibility note:** the existing FEATURE-1.1 test (`test_ac1_bootstrap_creates_all_eleven_tables`) uses `EXPECTED_TABLES.issubset(actual)` — adding a 12th table does **not** break it.

### Session lifecycle

- **Token format:** 32 random bytes → 64 hex chars. Opaque, not parseable.
- **TTL:** 24 hours from issuance (configurable later).
- **Login:** verify password → generate token → insert `Session` row → return token.
- **`current_user(token)`:** lookup by token → check `expires_at` → return `User` (or raise `InvalidSessionError`).
- **Logout:** delete the row.

### Role enforcement

`@require_role("staff")` is a service-layer decorator that:

1. Calls `current_user(token)` to identify the caller.
2. Raises `PermissionDeniedError` if the caller's role doesn't match.

For now the decorator takes a token argument explicitly — there is no implicit request context. A future HTTP layer can wrap it in middleware that pulls the token from headers.

### Test plan (one test per AC)

- **AC1** — register a patient and a staff user, log each back in, assert returned user has expected role.
- **AC2** — register a patient, attempt a staff-only service call, assert `PermissionDeniedError`.
- **AC3** — log in, get a token, close the session, open a new one against the same DB, call `current_user(token)` → still succeeds (proves the token is in the DB, not in-process).

`pytest` fixtures follow the pattern from `tests/conftest.py` (`fresh_db`, `session_for`) plus a new `auth_service` fixture that wires the service-layer functions to the test DB.

## Files in scope

| Path | Change |
|---|---|
| `pyproject.toml` | + `bcrypt>=4.0,<5.0` |
| `src/database/schema.sql` | + `Session` table + 2 indexes |
| `src/models/session.py` | new ORM model |
| `src/models/__init__.py` | re-export `Session` |
| `src/auth/__init__.py` | re-export public API |
| `src/auth/passwords.py` | bcrypt hash + verify |
| `src/auth/service.py` | register, login, logout, current_user, require_role |
| `src/auth/exceptions.py` | typed auth errors |
| `tests/test_feature_1_2.py` | 3 tests (one per AC) |
| `tests/conftest.py` | + `auth_service` fixture |
| `.claude/plans/FEATURE-10.md` | this file |

## Verification

```bash
uv run pytest tests/ -v
```

Expected:

```
tests/test_feature_1_1.py::test_ac1_bootstrap_creates_all_eleven_tables PASSED
tests/test_feature_1_1.py::test_ac2_orm_navigates_relationships PASSED
tests/test_feature_1_1.py::test_ac3_seed_meets_minimum_counts_and_uses_uuid_ids PASSED
tests/test_feature_1_1.py::test_ac4_bootstrap_is_idempotent PASSED
tests/test_feature_1_2.py::test_ac1_register_and_login PASSED
tests/test_feature_1_2.py::test_ac2_role_enforcement PASSED
tests/test_feature_1_2.py::test_ac3_session_persistence PASSED

7 passed in <1s
```

Plus a manual sanity check (Streamlit UIs land later):

```python
from src.auth import register, login, require_role
from src.auth.exceptions import PermissionDeniedError

u = register("alice@example.com", "hunter2", role="patient")
token = login("alice@example.com", "hunter2")
@require_role("staff")
def list_audit():
    ...
try:
    list_audit(token=token)
except PermissionDeniedError:
    print("blocked as expected")
```

## What's left to iterate (not blocking)

1. **No `FEATURE-1.1` follow-up items.** The deprecation warning + `PatientProfile.user_id` `NOT NULL UNIQUE` + slot determinism are tracked in `.claude/plans/FEATURE-9.md` and can roll into a follow-up PR any time.
2. **No FastAPI / HTTP layer.** Stories 1.2.1–1.2.3 describe service-layer methods. When FEATURE-5.1 / 5.2 land, the Streamlit UIs will call these services directly. A future "HTTP layer" feature can wrap them.
3. **No password reset / email verification / 2FA** — explicitly out of MVP scope.
4. **No rate limiting on login attempts.** Worth adding before any real deployment; defer until hackathon submission.
5. **bcrypt cost factor is hardcoded** at the library default. Fine for now; revisit if we benchmark.
6. **`Session` table is single-instance per user** (login from a second device overwrites the first). For the MVP this is acceptable; multi-session-per-user would be a future change.

## Critical files to read before iterating

- `src/database/schema.sql` — adding the `Session` table; keep FK to `User(id)` enforced
- `src/database/base.py` — engine/session; `require_role` will need to use it
- `src/auth/service.py` — keep public API small (`register`, `login`, `logout`, `current_user`, `require_role`)
- `tests/conftest.py` — pattern for fixtures; `auth_service` should mirror `seeded_db`

## Out of scope (deferred to other features)

- FEATURE-2.1 / 2.2 — agent runtime + LangGraph state machine (depends on auth for actor IDs)
- FEATURE-5.1 / 5.2 — Streamlit UIs (call into `src.auth`)
- STORY-6.2.1 — `.env.example` (will document `ANTHROPIC_API_KEY` then; auth doesn't need new env vars in this scaffold)