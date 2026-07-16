"""Reward and participation computation service (section 4.14, FR-11/FR-14)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models

_TIER_ORDER = ["none", "bronze", "silver", "gold", "platinum"]


def _course_id_for_section(db: Session, section_id: str) -> str | None:
    section = db.get(models.CourseSection, section_id)
    return section.course_id if section else None


def compute_attendance_percentage(db: Session, student_id: str, course_id: str) -> tuple[int, int, float]:
    """Return (total_sessions, attended_sessions, percentage) for a course."""
    section_ids = db.scalars(
        select(models.CourseSection.id).where(
            models.CourseSection.course_id == course_id
        )
    ).all()
    if not section_ids:
        return 0, 0, 0.0

    total_sessions = db.scalar(
        select(func.count(models.ClassSession.id)).where(
            models.ClassSession.section_id.in_(section_ids),
            models.ClassSession.status.in_(["active", "closed"]),
        )
    ) or 0

    attended = db.scalar(
        select(func.count(func.distinct(models.AttendanceRecord.session_id)))
        .join(
            models.ClassSession,
            models.ClassSession.id == models.AttendanceRecord.session_id,
        )
        .where(
            models.ClassSession.section_id.in_(section_ids),
            models.AttendanceRecord.student_id == student_id,
            models.AttendanceRecord.verification_status.in_(
                ["verified", "manual_override"]
            ),
        )
    ) or 0

    pct = round((attended / total_sessions) * 100, 2) if total_sessions else 0.0
    return total_sessions, attended, pct


def compute_participation_score(db: Session, student_id: str, course_id: str) -> float:
    """Participation score: number of correct quiz responses in the course."""
    correct = db.scalar(
        select(func.count(models.QuizResponse.id))
        .join(
            models.SessionQuiz,
            models.SessionQuiz.id == models.QuizResponse.session_quiz_id,
        )
        .join(
            models.ClassSession,
            models.ClassSession.id == models.SessionQuiz.session_id,
        )
        .join(
            models.CourseSection,
            models.CourseSection.id == models.ClassSession.section_id,
        )
        .where(
            models.CourseSection.course_id == course_id,
            models.QuizResponse.student_id == student_id,
            models.QuizResponse.is_correct.is_(True),
        )
    ) or 0
    return float(correct)


def determine_tier(
    db: Session, course_id: str, attendance_pct: float, participation: float
) -> tuple[str, str | None, list[dict]]:
    """Resolve the highest tier the student qualifies for, plus the next tier."""
    policies = db.scalars(
        select(models.RewardPolicy).where(models.RewardPolicy.course_id == course_id)
    ).all()

    tiers = []
    for p in policies:
        tiers.append(
            {
                "tier": p.tier_name,
                "minAttendancePercentage": float(p.min_attendance_percentage),
                "minParticipationScore": float(p.min_participation_score),
            }
        )
    tiers.sort(key=lambda t: _tier_rank(t["tier"]))

    current = "none"
    for t in tiers:
        if (
            attendance_pct >= t["minAttendancePercentage"]
            and participation >= t["minParticipationScore"]
        ):
            if _tier_rank(t["tier"]) > _tier_rank(current):
                current = t["tier"]

    next_tier = None
    for t in tiers:
        if _tier_rank(t["tier"]) > _tier_rank(current):
            next_tier = t["tier"]
            break

    return current, next_tier, tiers


def _tier_rank(tier: str) -> int:
    return _TIER_ORDER.index(tier) if tier in _TIER_ORDER else 0


def tier_at_least(current: str, required: str) -> bool:
    return _tier_rank(current) >= _tier_rank(required)


def recompute_reward_status(
    db: Session, student_id: str, course_id: str
) -> models.StudentRewardStatus:
    """Recompute and persist a student's reward status for a course."""
    _, _, pct = compute_attendance_percentage(db, student_id, course_id)
    participation = compute_participation_score(db, student_id, course_id)
    tier, _, _ = determine_tier(db, course_id, pct, participation)

    status = db.scalar(
        select(models.StudentRewardStatus).where(
            models.StudentRewardStatus.student_id == student_id,
            models.StudentRewardStatus.course_id == course_id,
        )
    )
    if status is None:
        status = models.StudentRewardStatus(
            student_id=student_id, course_id=course_id
        )
        db.add(status)

    status.attendance_percentage = pct
    status.participation_score = participation
    status.current_tier = tier
    status.updated_at = datetime.now(timezone.utc)
    db.flush()
    return status
