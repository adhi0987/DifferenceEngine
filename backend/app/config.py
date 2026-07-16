"""Application configuration.

Values are read from environment variables so the same code runs locally
and in deployment. Sensible defaults are provided for local development.
"""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Runtime settings for the AttendIQ COA backend."""

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "AttendIQ COA")
        self.api_prefix: str = os.getenv("API_PREFIX", "/api/v1")

        # SQLite by default for zero-config local runs. Point DATABASE_URL at a
        # PostgreSQL instance (postgresql+psycopg://...) for production.
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./attendiq.db"
        )

        # Auth / JWT
        self.jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_ttl_seconds: int = int(
            os.getenv("ACCESS_TOKEN_TTL_SECONDS", "3600")
        )
        self.refresh_token_ttl_seconds: int = int(
            os.getenv("REFRESH_TOKEN_TTL_SECONDS", str(60 * 60 * 24 * 7))
        )

        # Rotating QR token lifetime (seconds).
        self.qr_rotation_seconds: int = int(os.getenv("QR_ROTATION_SECONDS", "30"))

        # Allow open registration for the MVP demo. In production this would be
        # gated behind institutional identity verification.
        self.allow_open_registration: bool = (
            os.getenv("ALLOW_OPEN_REGISTRATION", "true").lower() == "true"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
