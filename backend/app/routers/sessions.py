"""Class session APIs (section 10.3)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles
from ..services import audit

router = APIRouter(tags=["sessions"])


def _owned_section_or_403(db: Session, user: models.User, section_id: str) -> models.CourseSection:
    section = db.get(models.CourseSection, section_id)
    if not section:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Section not found")
    if user.role == "faculty" and section.faculty_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your section")
    return section


def _get_owned_session(db: Session, user: models.User, session_id: str) -> models.ClassSession:
    session = db.get(models.ClassSession, session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if user.role == "faculty":
        section = db.get(models.CourseSection, session.section_id)
        if not section or section.faculty_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your session")
    return session


@router.post(
    "/faculty/sessions",
    response_model=schemas.ApiResponse[schemas.SessionData],
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    body: schemas.CreateSessionRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    _owned_section_or_403(db, user, body.sectionId)
    if body.classroomId and not db.get(models.Classroom, body.classroomId):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid classroomId")

    session = models.ClassSession(
        section_id=body.sectionId,
        classroom_id=body.classroomId,
        topic_title=body.topicTitle,
        session_date=body.sessionDate,
        start_time=body.startTime,
        status="scheduled",
        created_by=user.id,
    )
    db.add(session)
    db.flush()
    audit.record(db, user.id, "SESSION_CREATED", "class_session", session.id)
    db.commit()

    return schemas.ApiResponse(
        message="Session created",
        data=_session_data(session),
    )


@router.post(
    "/faculty/sessions/{session_id}/start",
    response_model=schemas.ApiResponse[schemas.SessionData],
)
def start_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    session = _get_owned_session(db, user, session_id)
    if session.status == "closed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Session already closed")
    session.status = "active"
    audit.record(db, user.id, "SESSION_STARTED", "class_session", session.id)
    db.commit()
    return schemas.ApiResponse(message="Session started", data=_session_data(session))


@router.post(
    "/faculty/sessions/{session_id}/close",
    response_model=schemas.ApiResponse[schemas.SessionData],
)
def close_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    session = _get_owned_session(db, user, session_id)
    session.status = "closed"
    session.end_time = datetime.now(timezone.utc)
    # Revoke outstanding QR tokens.
    for token in db.scalars(
        select(models.QrToken).where(
            models.QrToken.session_id == session.id,
            models.QrToken.is_revoked.is_(False),
        )
    ):
        token.is_revoked = True
    audit.record(db, user.id, "SESSION_CLOSED", "class_session", session.id)
    db.commit()
    return schemas.ApiResponse(message="Session closed", data=_session_data(session))


@router.get(
    "/faculty/sessions/{session_id}/live",
    response_model=schemas.ApiResponse[schemas.LiveSessionData],
)
def live_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    session = _get_owned_session(db, user, session_id)

    def _count(*statuses: str) -> int:
        stmt = select(func.count(models.AttendanceRecord.id)).where(
            models.AttendanceRecord.session_id == session.id
        )
        if statuses:
            stmt = stmt.where(
                models.AttendanceRecord.verification_status.in_(statuses)
            )
        return db.scalar(stmt) or 0

    return schemas.ApiResponse(
        data=schemas.LiveSessionData(
            sessionId=session.id,
            status=session.status,
            attendanceCount=_count(),
            verifiedCount=_count("verified", "manual_override"),
            pendingReviewCount=_count("pending_review"),
        )
    )


def _session_data(session: models.ClassSession) -> schemas.SessionData:
    return schemas.SessionData(
        sessionId=session.id,
        sectionId=session.section_id,
        topicTitle=session.topic_title,
        status=session.status,
        startTime=session.start_time,
    )
