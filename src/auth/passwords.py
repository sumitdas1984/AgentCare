"""bcrypt-backed password hashing.

Cost factor can be lowered in tests via the ``AGENTCARE_BCRYPT_ROUNDS`` env
var. Production leaves it at the library default (12).
"""

import os

import bcrypt

_BCRYPT_ROUNDS = int(os.environ.get("AGENTCARE_BCRYPT_ROUNDS", "12"))


def hash_password(plaintext: str) -> str:
    """Hash a password with bcrypt. Returns a self-contained hash string."""
    if not plaintext:
        raise ValueError("password must be non-empty")
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return True iff ``plaintext`` matches the stored bcrypt ``hashed``.

    Returns False (rather than raises) for any malformed input so the
    caller doesn't have to distinguish "wrong password" from "corrupt hash".
    """
    if not plaintext or not hashed:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
