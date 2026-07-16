"""Security helpers: password hashing, JWT access/refresh tokens, hashing utils."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from .config import get_settings

settings = get_settings()

_PBKDF2_ROUNDS = 240_000
_PBKDF2_ALGO = "sha256"


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2_{_PBKDF2_ALGO}${_PBKDF2_ROUNDS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        _, rounds_s, salt_hex, dk_hex = stored.split("$")
        rounds = int(rounds_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(dk_hex)
    except (ValueError, AttributeError):
        return False
    dk = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode(), salt, rounds)
    return hmac.compare_digest(dk, expected)


def sha256_hex(value: str) -> str:
    """Return the SHA-256 hex digest of a string (for device/token hashing)."""
    return hashlib.sha256(value.encode()).hexdigest()


def _create_token(subject: str, role: str, ttl_seconds: int, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str) -> str:
    return _create_token(subject, role, settings.access_token_ttl_seconds, "access")


def create_refresh_token(subject: str, role: str) -> str:
    return _create_token(subject, role, settings.refresh_token_ttl_seconds, "refresh")


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt exceptions on failure."""
    return jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
