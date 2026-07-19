"""Typed exceptions raised by the auth layer.

A future HTTP layer should translate:
  - ``InvalidCredentialsError`` → 401
  - ``InvalidSessionError`` → 401
  - ``PermissionDeniedError`` → 403
  - ``ValueError`` (duplicate email / unknown role) → 400
"""


class AuthError(Exception):
    """Base class for every error the auth layer can raise."""


class InvalidCredentialsError(AuthError):
    """Wrong email or password."""


class InvalidSessionError(AuthError):
    """Token is unknown, expired, or revoked."""


class PermissionDeniedError(AuthError):
    """Authenticated but lacks the role required by the called endpoint."""
