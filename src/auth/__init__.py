"""Authentication & RBAC service for AgentCare.

Provides:
  - register / login / logout / current_user
  - ``@require_role(...)`` decorator
  - bcrypt-backed password hashing
  - typed exceptions for every failure mode

The functions accept an optional ``session=`` keyword so tests can drive
them against a private engine. Production callers omit it and get the
module-level ``SessionLocal``.
"""

from .exceptions import (
    AuthError,
    InvalidCredentialsError,
    InvalidSessionError,
    PermissionDeniedError,
)
from .passwords import hash_password, verify_password
from .service import (
    current_user,
    login,
    logout,
    register,
    require_role,
)

__all__ = [
    "AuthError",
    "InvalidCredentialsError",
    "InvalidSessionError",
    "PermissionDeniedError",
    "hash_password",
    "verify_password",
    "register",
    "login",
    "logout",
    "current_user",
    "require_role",
]
