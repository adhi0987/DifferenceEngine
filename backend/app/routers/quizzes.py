"""Quiz and participation APIs (section 10.5)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles
from ..services import audit, rewards
from .sessions import _get_owned_session

router = APIRouter(tags=["quizzes"])


@router.post(
    "/faculty/sessions/{session_id}/quizzes",
    response_model=schemas.ApiResponse[schemas.LaunchQuizData],
    status_code=status.HTTP_201_CREATED,
)
def launch_quiz(
    session_id: str,
    body: schemas.LaunchQuizRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    session = _get_owned_session(db, user, session_id)
    if session.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Session is not active")

    question = db.get(models.QuizQuestion, body.questionId)
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid questionId")

    now = datetime.now(timezone.utc)
    session_quiz = models.SessionQuiz(
        session_id=session.id,
        question_id=question.id,
        launched_at=now,
        closes_at=now + timedelta(seconds=max(body.durationSeconds, 5)),
        status="active",
    )
    db.add(session_quiz)
    db.flush()
    audit.record(db, user.id, "QUIZ_LAUNCHED", "session_quiz", session_quiz.id)
    db.commit()

    return schemas.ApiResponse(
        message="Quiz launched",
        data=schemas.LaunchQuizData(
            sessionQuizId=session_quiz.id,
            questionId=question.id,
            launchedAt=session_quiz.launched_at,
            closesAt=session_quiz.closes_at,
            status=session_quiz.status,
        ),
    )


@router.get(
    "/student/sessions/{session_id}/active-quiz",
    response_model=schemas.ApiResponse[schemas.ActiveQuizData],
)
def active_quiz(
    session_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    session = db.get(models.ClassSession, session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    now = datetime.now(timezone.utc)
    session_quiz = db.scalar(
        select(models.SessionQuiz)
        .where(
            models.SessionQuiz.session_id == session_id,
            models.SessionQuiz.status == "active",
            models.SessionQuiz.closes_at > now,
        )
        .order_by(models.SessionQuiz.launched_at.desc())
    )
    if not session_quiz:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active quiz")

    q = session_quiz.question
    return schemas.ApiResponse(
        data=schemas.ActiveQuizData(
            sessionQuizId=session_quiz.id,
            topic=q.topic,
            questionText=q.question_text,
            optionA=q.option_a,
            optionB=q.option_b,
            optionC=q.option_c,
            optionD=q.option_d,
            closesAt=session_quiz.closes_at,
        )
    )


@router.post(
    "/student/quizzes/{session_quiz_id}/responses",
    response_model=schemas.ApiResponse[schemas.QuizResponseData],
    status_code=status.HTTP_201_CREATED,
)
def submit_response(
    session_quiz_id: str,
    body: schemas.QuizResponseRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    session_quiz = db.get(models.SessionQuiz, session_quiz_id)
    if not session_quiz:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz not found")

    now = datetime.now(timezone.utc)
    closes_at = session_quiz.closes_at
    if closes_at.tzinfo is None:
        closes_at = closes_at.replace(tzinfo=timezone.utc)
    if session_quiz.status != "active" or closes_at < now:
        raise HTTPException(status.HTTP_409_CONFLICT, "Quiz is closed")

    existing = db.scalar(
        select(models.QuizResponse).where(
            models.QuizResponse.session_quiz_id == session_quiz_id,
            models.QuizResponse.student_id == user.id,
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Response already submitted")

    question = session_quiz.question
    is_correct = None
    if question.correct_option and body.selectedOption:
        is_correct = (
            body.selectedOption.strip().lower()
            == question.correct_option.strip().lower()
        )

    response = models.QuizResponse(
        session_quiz_id=session_quiz_id,
        student_id=user.id,
        selected_option=body.selectedOption,
        free_text_answer=body.freeTextAnswer,
        is_correct=is_correct,
    )
    db.add(response)
    db.flush()

    session = db.get(models.ClassSession, session_quiz.session_id)
    if session:
        section = db.get(models.CourseSection, session.section_id)
        if section:
            rewards.recompute_reward_status(db, user.id, section.course_id)
    db.commit()

    return schemas.ApiResponse(
        message="Response recorded",
        data=schemas.QuizResponseData(responseId=response.id, isCorrect=is_correct),
    )


@router.get(
    "/faculty/sessions/{session_id}/quiz-analytics",
    response_model=schemas.ApiResponse[schemas.QuizAnalyticsData],
)
def quiz_analytics(
    session_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    _get_owned_session(db, user, session_id)

    session_quizzes = db.scalars(
        select(models.SessionQuiz).where(models.SessionQuiz.session_id == session_id)
    ).all()

    quizzes = []
    for sq in session_quizzes:
        rows = db.execute(
            select(
                models.QuizResponse.selected_option,
                func.count(models.QuizResponse.id),
            )
            .where(models.QuizResponse.session_quiz_id == sq.id)
            .group_by(models.QuizResponse.selected_option)
        ).all()
        total = sum(count for _, count in rows)
        correct = db.scalar(
            select(func.count(models.QuizResponse.id)).where(
                models.QuizResponse.session_quiz_id == sq.id,
                models.QuizResponse.is_correct.is_(True),
            )
        ) or 0
        quizzes.append(
            {
                "sessionQuizId": sq.id,
                "topic": sq.question.topic,
                "questionText": sq.question.question_text,
                "totalResponses": total,
                "correctResponses": correct,
                "accuracy": round((correct / total) * 100, 2) if total else 0.0,
                "optionBreakdown": [
                    {"option": opt, "count": count} for opt, count in rows
                ],
            }
        )

    return schemas.ApiResponse(
        data=schemas.QuizAnalyticsData(sessionId=session_id, quizzes=quizzes)
    )
