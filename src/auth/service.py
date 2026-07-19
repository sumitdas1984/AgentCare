"""Auth service: registration, login, logout, current_user, require_role.

All session state lives in the DB. Tokens are opaque 64-char hex strings;
never parse them.

Every public function accepts ``*, session: Optional[Session] = None``:
when omitted, the module-level ``SessionLocal`` is used. Tests pass a
session bound to a private engine to keep state isolated.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from sqlalchemy.orm import Session

from ..database.base import SessionLocal
from ..models import Session as SessionModel
from ..models import User
from .exceptions import (
    InvalidCredentialsError,
    InvalidSessionError,
    PermissionDeniedError,
)
from .passwords import hash_password, verify_password


# Session lifetime. Future: configurable via env or per-role policy.
_SESSION_TTL = timedelta(hours=24)

_VALID_ROLES = {"patient", "staff"}


def register(
    email: str,
    password: str,
    role: str,
    name: Optional[str] = None,
    *,
    session: Optional[Session] = None,
) -> User:
    """Register a new user. Raises ``ValueError`` on duplicate email
    or unknown role.

    ``name`` defaults to the local-part of the email.
    """
    if role not in _VALID_ROLES:
        raise ValueError(f"role must be 'patient' or 'staff', got {role!r}")

    own_session = session is None
    session = session if session is not None else SessionLocal()
    try:
        if session.query(User).filter_by(email=email).one_or_none() is not None:
            raise ValueError(f"email {email!r} already registered")

        user = User(
            id=str(uuid.uuid4()),
            name=name or email.split("@", 1)[0],
            email=email,
            password_hash=hash_password(password),
            role=role,
            created_at=datetime.utcnow(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        if own_session:
            session.close()


def login(
    email: str,
    password: str,
    *,
    session: Optional[Session] = None,
) -> str:
    """Verify credentials and return an opaque session token.

    Token format: 64 hex chars (32 random bytes from ``secrets``).
    """
    own_session = session is None
    session = session if session is not None else SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("invalid email or password")

        token = secrets.token_hex(32)
        session.add(
            SessionModel(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + _SESSION_TTL,
                created_at=datetime.utcnow(),
            )
        )
        session.commit()
        return token
    finally:
        if own_session:
            session.close()


def logout(
    token: str,
    *,
    session: Optional[Session] = None,
) -> None:
    """Invalidate ``token`` by deleting its Session row. No-op if unknown."""
    own_session = session is None
    session = session if session is not None else SessionLocal()
    try:
        row = session.query(SessionModel).filter_by(token=token).one_or_none()
        if row is not None:
            session.delete(row)
            session.commit()
    finally:
        if own_session:
            session.close()


def current_user(
    token: str,
    *,
    session: Optional[Session] = None,
) -> User:
    """Resolve a token to its ``User`` or raise ``InvalidSessionError``.

    Checks both presence and ``expires_at``.
    """
    own_session = session is None
    session = session if session is not None else SessionLocal()
    try:
        row = session.query(SessionModel).filter_by(token=token).one_or_none()
        if row is None:
            raise InvalidSessionError("unknown session token")
        if row.expires_at < datetime.utcnow():
            raise InvalidSessionError("session has expired")
        user = session.query(User).filter_by(id=row.user_id).one()
        return user
    finally:
        if own_session:
            session.close()


def require_role(required_role: str):
    """Decorator factory: the wrapped function must accept ``token`` (str)
    and ``session`` (Optional[Session]) keyword arguments. Resolves the
    token to a ``User`` and rejects calls from anyone whose ``role`` does
    not match ``required_role``.

    Usage:
        @require_role("staff")
        def list_audit(*, token, session=None):
            ...

    Raises ``PermissionDeniedError`` if the caller's role is wrong.
    """
    if required_role not in _VALID_ROLES:
        raise ValueError(f"unknown role {required_role!r}")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, token: str, session: Optional[Session] = None, **kwargs):
            user = current_user(token=token, session=session)
            if user.role != required_role:
                raise PermissionDeniedError(
                    f"requires role {required_role!r}, caller has {user.role!r}"
                )
            return func(*args, token=token, session=session, **kwargs)

        return wrapper

    return decorator
