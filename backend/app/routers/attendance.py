"""QR and attendance APIs (section 10.4) including the verification engine."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_roles
from ..security import sha256_hex
from ..services import audit, qr, rewards
from .sessions import _get_owned_session

router = APIRouter(tags=["attendance"])


@router.get(
    "/faculty/sessions/{session_id}/qr",
    response_model=schemas.ApiResponse[schemas.QrData],
)
def get_qr(
    session_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    session = _get_owned_session(db, user, session_id)
    if session.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Session is not active")

    payload, valid_until = qr.generate_payload(session.id)
    db.add(
        models.QrToken(
            session_id=session.id,
            token_hash=qr.payload_hash(payload),
            valid_from=datetime.now(timezone.utc),
            valid_until=valid_until,
        )
    )
    db.commit()

    return schemas.ApiResponse(
        data=schemas.QrData(
            sessionId=session.id,
            qrPayload=payload,
            validUntil=valid_until,
            rotationSeconds=qr.settings.qr_rotation_seconds,
        )
    )


@router.post(
    "/student/attendance/check-in",
    response_model=schemas.ApiResponse[schemas.CheckInData],
)
def check_in(
    body: schemas.CheckInRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    session = db.get(models.ClassSession, body.sessionId)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if session.status != "active":
        raise _rejected("SESSION_INACTIVE", "The class session is not open for check-in")

    enrollment = db.scalar(
        select(models.Enrollment).where(
            models.Enrollment.student_id == user.id,
            models.Enrollment.section_id == session.section_id,
            models.Enrollment.enrollment_status == "active",
        )
    )
    if not enrollment:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You are not enrolled in this section"
        )

    existing = db.scalar(
        select(models.AttendanceRecord).where(
            models.AttendanceRecord.session_id == session.id,
            models.AttendanceRecord.student_id == user.id,
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already checked in")

    # --- Verification engine ---------------------------------------------
    qr_verified = qr.verify_payload(session.id, body.qrPayload)
    if not qr_verified:
        raise _rejected("QR_EXPIRED", "The QR token is no longer valid")

    device_verified = False
    if body.deviceHash:
        device_verified = (
            db.scalar(
                select(models.DeviceSession).where(
                    models.DeviceSession.user_id == user.id,
                    models.DeviceSession.device_hash == sha256_hex(body.deviceHash),
                    models.DeviceSession.is_active.is_(True),
                )
            )
            is not None
        )

    proximity_verified = False
    reason = None
    if session.classroom_id and body.proximitySignal:
        classroom = db.get(models.Classroom, session.classroom_id)
        if classroom and classroom.wifi_ssid_hash:
            proximity_verified = (
                body.proximitySignal.wifiSsidHash == classroom.wifi_ssid_hash
                or body.proximitySignal.beaconHash == classroom.beacon_id_hash
            )
        else:
            proximity_verified = True  # No configured signal to check against.
    else:
        # Proximity optional: absence does not reject, but adds risk.
        proximity_verified = not bool(session.classroom_id)

    risk_score = _risk_score(qr_verified, device_verified, proximity_verified)
    if risk_score <= 40:
        verification_status = "verified"
    else:
        verification_status = "pending_review"
        reason = "QR valid but proximity/device signal was not available"

    record = models.AttendanceRecord(
        session_id=session.id,
        student_id=user.id,
        enrollment_id=enrollment.id,
        check_in_time=datetime.now(timezone.utc),
        verification_status=verification_status,
        qr_verified=qr_verified,
        device_verified=device_verified,
        proximity_verified=proximity_verified,
        risk_score=risk_score,
    )
    db.add(record)
    db.flush()
    audit.record(db, user.id, "ATTENDANCE_CHECKIN", "attendance_record", record.id)

    section = db.get(models.CourseSection, session.section_id)
    if section:
        rewards.recompute_reward_status(db, user.id, section.course_id)
    db.commit()

    return schemas.ApiResponse(
        success=True,
        message=(
            "Attendance marked successfully"
            if verification_status == "verified"
            else "Attendance submitted for review"
        ),
        data=schemas.CheckInData(
            attendanceId=record.id,
            verificationStatus=verification_status,
            checkInTime=record.check_in_time,
            riskScore=risk_score,
            reason=reason,
        ),
    )


@router.get(
    "/student/attendance/summary",
    response_model=schemas.ApiResponse[schemas.AttendanceSummaryData],
)
def attendance_summary(
    courseId: str = Query(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    total, attended, pct = rewards.compute_attendance_percentage(
        db, user.id, courseId
    )
    status_row = rewards.recompute_reward_status(db, user.id, courseId)
    db.commit()

    return schemas.ApiResponse(
        data=schemas.AttendanceSummaryData(
            courseId=courseId,
            totalSessions=total,
            attendedSessions=attended,
            attendancePercentage=pct,
            currentTier=status_row.current_tier,
        )
    )


@router.post(
    "/faculty/attendance/{attendance_id}/override",
    response_model=schemas.ApiResponse[schemas.OverrideData],
)
def override_attendance(
    attendance_id: str,
    body: schemas.OverrideRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    record = db.get(models.AttendanceRecord, attendance_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attendance record not found")

    session = db.get(models.ClassSession, record.session_id)
    if user.role == "faculty" and session:
        section = db.get(models.CourseSection, session.section_id)
        if not section or section.faculty_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your session")

    record.verification_status = body.verificationStatus
    if body.remarks:
        record.remarks = body.remarks
    audit.record(
        db,
        user.id,
        "ATTENDANCE_OVERRIDE",
        "attendance_record",
        record.id,
        {"status": body.verificationStatus},
    )

    if session:
        section = db.get(models.CourseSection, session.section_id)
        if section:
            rewards.recompute_reward_status(db, record.student_id, section.course_id)
    db.commit()

    return schemas.ApiResponse(
        message="Attendance status updated",
        data=schemas.OverrideData(
            attendanceId=record.id, verificationStatus=record.verification_status
        ),
    )


def _risk_score(qr_ok: bool, device_ok: bool, proximity_ok: bool) -> int:
    score = 0
    if not qr_ok:
        score += 60
    if not device_ok:
        score += 25
    if not proximity_ok:
        score += 30
    return min(score, 100)


def _rejected(code: str, details: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": code, "details": details},
    )
