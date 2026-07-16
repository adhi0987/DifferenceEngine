"""Analytics and audit APIs (section 10.7)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles

router = APIRouter(tags=["analytics"])


@router.get(
    "/faculty/analytics/course/{course_id}",
    response_model=schemas.ApiResponse[schemas.CourseAnalyticsData],
)
def course_analytics(
    course_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    section_ids = db.scalars(
        select(models.CourseSection.id).where(
            models.CourseSection.course_id == course_id
        )
    ).all()

    total_sessions = 0
    total_students = 0
    if section_ids:
        total_sessions = db.scalar(
            select(func.count(models.ClassSession.id)).where(
                models.ClassSession.section_id.in_(section_ids),
                models.ClassSession.status.in_(["active", "closed"]),
            )
        ) or 0
        total_students = db.scalar(
            select(func.count(func.distinct(models.Enrollment.student_id))).where(
                models.Enrollment.section_id.in_(section_ids),
                models.Enrollment.enrollment_status == "active",
            )
        ) or 0

    avg_attendance = db.scalar(
        select(func.avg(models.StudentRewardStatus.attendance_percentage)).where(
            models.StudentRewardStatus.course_id == course_id
        )
    )
    avg_attendance = round(float(avg_attendance), 2) if avg_attendance is not None else 0.0

    # Weak topics: quiz topics with the lowest accuracy.
    rows = db.execute(
        select(
            models.QuizQuestion.topic,
            func.count(models.QuizResponse.id),
            func.sum(
                cast(models.QuizResponse.is_correct, Integer)
            ),
        )
        .join(models.SessionQuiz, models.SessionQuiz.question_id == models.QuizQuestion.id)
        .join(
            models.QuizResponse,
            models.QuizResponse.session_quiz_id == models.SessionQuiz.id,
        )
        .where(models.QuizQuestion.course_id == course_id)
        .group_by(models.QuizQuestion.topic)
    ).all()

    weak_topics = []
    for topic, total, correct in rows:
        correct = correct or 0
        accuracy = round((correct / total) * 100, 2) if total else 0.0
        weak_topics.append(
            {"topic": topic, "responses": total, "accuracy": accuracy}
        )
    weak_topics.sort(key=lambda t: t["accuracy"])

    return schemas.ApiResponse(
        data=schemas.CourseAnalyticsData(
            courseId=course_id,
            totalSessions=total_sessions,
            averageAttendancePercentage=avg_attendance,
            totalStudents=total_students,
            weakTopics=weak_topics[:5],
        )
    )


@router.get(
    "/admin/audit-logs",
    response_model=schemas.ApiResponse[list[schemas.AuditLogEntry]],
)
def audit_logs(
    entityType: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("admin")),
):
    stmt = select(models.AuditLog).order_by(models.AuditLog.created_at.desc())
    if entityType:
        stmt = stmt.where(models.AuditLog.entity_type == entityType)
    stmt = stmt.limit(limit)

    logs = db.scalars(stmt).all()
    data = [
        schemas.AuditLogEntry(
            id=log.id,
            actorUserId=log.actor_user_id,
            action=log.action,
            entityType=log.entity_type,
            entityId=log.entity_id,
            createdAt=log.created_at,
        )
        for log in logs
    ]
    return schemas.ApiResponse(data=data)
