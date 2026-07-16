"""Authentication APIs (section 10.1)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user
from ..security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    sha256_hex,
    verify_password,
)
from ..services import audit

router = APIRouter(tags=["auth"])
settings = get_settings()


@router.post("/auth/register", response_model=schemas.ApiResponse[schemas.RegisteredUser])
def register(body: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if not settings.allow_open_registration and body.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration restricted")

    existing = db.scalar(
        select(models.User).where(
            (models.User.email == body.email)
            | (models.User.institutional_id == body.institutionalId)
        )
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Email or institutional ID already registered"
        )

    user = models.User(
        institutional_id=body.institutionalId,
        full_name=body.fullName,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.flush()
    audit.record(db, user.id, "USER_REGISTERED", "user", user.id)
    db.commit()

    return schemas.ApiResponse(
        message="User registered successfully",
        data=schemas.RegisteredUser(userId=user.id, email=user.email, role=user.role),
    )


@router.post("/auth/login", response_model=schemas.ApiResponse[schemas.LoginData])
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")

    access = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id, user.role)

    if body.deviceHash:
        existing = db.scalar(
            select(models.DeviceSession).where(
                models.DeviceSession.user_id == user.id,
                models.DeviceSession.device_hash == sha256_hex(body.deviceHash),
                models.DeviceSession.is_active.is_(True),
            )
        )
        expires = datetime.now(timezone.utc) + timedelta(
            seconds=settings.refresh_token_ttl_seconds
        )
        if existing:
            existing.session_expires_at = expires
        else:
            db.add(
                models.DeviceSession(
                    user_id=user.id,
                    device_hash=sha256_hex(body.deviceHash),
                    session_expires_at=expires,
                )
            )
    db.commit()

    return schemas.ApiResponse(
        message="Login successful",
        data=schemas.LoginData(
            accessToken=access,
            refreshToken=refresh,
            expiresIn=settings.access_token_ttl_seconds,
            user=schemas.LoginUser(
                id=user.id, fullName=user.full_name, role=user.role
            ),
        ),
    )


@router.post("/auth/logout", response_model=schemas.ApiResponse[None])
def logout(
    body: schemas.LogoutRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = select(models.DeviceSession).where(
        models.DeviceSession.user_id == user.id,
        models.DeviceSession.is_active.is_(True),
    )
    if body.deviceHash:
        query = query.where(
            models.DeviceSession.device_hash == sha256_hex(body.deviceHash)
        )
    for session in db.scalars(query):
        session.is_active = False
    db.commit()
    return schemas.ApiResponse(message="Logged out successfully")
