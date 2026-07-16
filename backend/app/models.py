"""SQLAlchemy ORM models mapping the AttendIQ COA schema (section 8)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    institutional_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # student|faculty|admin
    phone_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    department_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("departments.id"), nullable=True
    )
    course_code: Mapped[str] = mapped_column(String(30), nullable=False)
    course_name: Mapped[str] = mapped_column(String(150), nullable=False)
    syllabus_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class CourseSection(Base):
    __tablename__ = "course_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    faculty_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    section_name: Mapped[str] = mapped_column(String(100), nullable=False)
    academic_term: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    course: Mapped[Course] = relationship()


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("course_sections.id"), nullable=False
    )
    enrollment_status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    room_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    room_name: Mapped[str] = mapped_column(String(150), nullable=False)
    building_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    wifi_ssid_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    beacon_id_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("course_sections.id"), nullable=False
    )
    classroom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("classrooms.id"), nullable=True
    )
    topic_title: Mapped[str] = mapped_column(String(200), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    section: Mapped[CourseSection] = relationship()
    classroom: Mapped[Classroom | None] = relationship()


class QrToken(Base):
    __tablename__ = "qr_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("class_sessions.id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("class_sessions.id"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    enrollment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("enrollments.id"), nullable=True
    )
    check_in_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False)
    qr_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    device_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    proximity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class DeviceSession(Base):
    __tablename__ = "device_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    device_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    login_ip_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    session_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String(150), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_b: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_c: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_d: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_option: Mapped[str | None] = mapped_column(String(10), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SessionQuiz(Base):
    __tablename__ = "session_quizzes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("class_sessions.id"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quiz_questions.id"), nullable=False
    )
    launched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closes_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")

    question: Mapped[QuizQuestion] = relationship()


class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_quiz_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("session_quizzes.id"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    selected_option: Mapped[str | None] = mapped_column(String(10), nullable=True)
    free_text_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_time: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(150), nullable=True)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    required_tier: Mapped[str] = mapped_column(String(30), default="bronze")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class RewardPolicy(Base):
    __tablename__ = "reward_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    tier_name: Mapped[str] = mapped_column(String(30), nullable=False)
    min_attendance_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    min_participation_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class StudentRewardStatus(Base):
    __tablename__ = "student_reward_status"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    attendance_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    participation_score: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    current_tier: Mapped[str] = mapped_column(String(30), default="none")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ResourceAccessLog(Base):
    __tablename__ = "resource_access_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resources.id"), nullable=False)
    access_time: Mapped[datetime] = mapped_column(DateTime, default=_now)
    access_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    denial_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AiSubmission(Base):
    __tablename__ = "ai_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("class_sessions.id"), nullable=True
    )
    image_file_url: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    processing_status: Mapped[str] = mapped_column(String(30), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
