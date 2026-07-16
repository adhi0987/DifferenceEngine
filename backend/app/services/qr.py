"""Rotating QR token service.

The QR payload is a signed, short-lived token bound to a class session. It is
self-contained (HMAC signed) so the check-in endpoint can validate it without a
database round trip, while a hash is also persisted in ``qr_tokens`` for audit
and revocation support.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone

from ..config import get_settings

settings = get_settings()


def _sign(message: bytes) -> str:
    sig = hmac.new(settings.jwt_secret.encode(), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def _window(rotation_seconds: int, at: float | None = None) -> int:
    now = at if at is not None else time.time()
    return int(now // rotation_seconds)


def generate_payload(session_id: str, at: float | None = None) -> tuple[str, datetime]:
    """Generate the current QR payload and its expiry timestamp."""
    rotation = settings.qr_rotation_seconds
    window = _window(rotation, at)
    body = {"sid": session_id, "w": window}
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    payload = f"{b64}.{_sign(raw)}"
    valid_until = datetime.fromtimestamp((window + 1) * rotation, tz=timezone.utc)
    return payload, valid_until


def payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_payload(session_id: str, payload: str, at: float | None = None) -> bool:
    """Validate a QR payload for a session, allowing the current or previous window.

    A one-window grace period tolerates clock skew and scan latency.
    """
    try:
        b64, sig = payload.split(".", 1)
        padded = b64 + "=" * (-len(b64) % 4)
        raw = base64.urlsafe_b64decode(padded)
        body = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return False

    if body.get("sid") != session_id:
        return False
    if not hmac.compare_digest(sig, _sign(raw)):
        return False

    rotation = settings.qr_rotation_seconds
    current = _window(rotation, at)
    return body.get("w") in (current, current - 1)
