"""Tests for FEATURE-1.2 — Authentication & RBAC.

One test per acceptance criterion. The AC language is quoted verbatim in
each test so the link between test and AC is obvious.
"""

import pytest

from src.auth.exceptions import (
    InvalidCredentialsError,
    InvalidSessionError,
    PermissionDeniedError,
)


# --- AC1 — Patients and staff can register and log in ---
def test_ac1_register_and_login_returns_role_correct_token(fresh_db, session_for):
    """AC1: Patients and staff can register and log in.

    Registers one patient and one staff user, logs each back in, and
    verifies the returned tokens resolve to users with the expected roles.
    """
    from src.auth import current_user, login, register

    Session = session_for

    with Session() as s:
        register("alice@example.com", "hunter2", role="patient", name="Alice", session=s)
        register("bob@example.com", "s3cr1ty", role="staff", name="Bob", session=s)

    with Session() as s:
        token_patient = login("alice@example.com", "hunter2", session=s)
        token_staff = login("bob@example.com", "s3cr1ty", session=s)

    # Tokens are 64-char hex strings; unique per login.
    assert isinstance(token_patient, str) and len(token_patient) == 64
    assert isinstance(token_staff, str) and len(token_staff) == 64
    assert token_patient != token_staff

    # Wrong password is rejected.
    with Session() as s, pytest.raises(InvalidCredentialsError):
        login("alice@example.com", "wrong", session=s)

    # Tokens resolve to the correct users.
    with Session() as s:
        u_patient = current_user(token_patient, session=s)
        u_staff = current_user(token_staff, session=s)

    assert u_patient.email == "alice@example.com"
    assert u_patient.role == "patient"
    assert u_staff.email == "bob@example.com"
    assert u_staff.role == "staff"


# --- AC2 — Backend rejects patient-role calls to staff endpoints with 403 ---
def test_ac2_role_enforcement_blocks_patient_from_staff_endpoint(
    fresh_db, session_for
):
    """AC2: Backend rejects patient-role calls to staff endpoints with 403.

    A function wrapped in ``@require_role("staff")`` raises
    ``PermissionDeniedError`` when called with a patient's token.
    """
    from src.auth import login, register, require_role

    Session = session_for
    with Session() as s:
        register("alice@example.com", "hunter2", role="patient", session=s)
    with Session() as s:
        token = login("alice@example.com", "hunter2", session=s)

    @require_role("staff")
    def list_audit(*, token: str, session=None):  # noqa: ARG001
        return ["audit row 1", "audit row 2"]

    with pytest.raises(PermissionDeniedError):
        list_audit(token=token, session=Session())


# --- AC3 — Sessions persist via DB-backed tokens ---
def test_ac3_token_resolves_after_original_session_closed(fresh_db, session_for):
    """AC3: Sessions persist via DB-backed tokens.

    A token obtained in one Session must resolve when looked up from a
    brand-new Session against the same database, proving the token is
    persisted in the DB (not held in process memory).
    """
    from src.auth import current_user, login, register

    Session = session_for
    with Session() as s:
        register("alice@example.com", "hunter2", role="patient", session=s)

    # First session: obtain the token, then close it.
    with Session() as first_session:
        token = login("alice@example.com", "hunter2", session=first_session)
        # first_session goes out of scope and closes here.

    # Second session: brand-new Session object, same DB. The token must
    # still resolve.
    with Session() as second_session:
        user = current_user(token=token, session=second_session)

    assert user.email == "alice@example.com"
    assert user.role == "patient"

    # An unknown token is rejected with InvalidSessionError.
    with Session() as s, pytest.raises(InvalidSessionError):
        current_user("not-a-real-token", session=s)
