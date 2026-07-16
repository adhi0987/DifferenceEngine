"""Pydantic request/response schemas and the standard API envelope."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    details: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: Optional[T] = None
    error: Optional[ApiError] = None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
Role = Literal["student", "faculty", "admin"]


class RegisterRequest(BaseModel):
    institutionalId: str
    fullName: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: Role = "student"


class RegisteredUser(BaseModel):
    userId: str
    email: EmailStr
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    deviceHash: str | None = None


class LoginUser(BaseModel):
    id: str
    fullName: str
    role: Role


class LoginData(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: LoginUser


class LogoutRequest(BaseModel):
    deviceHash: str | None = None


# ---------------------------------------------------------------------------
# Courses / enrollment
# ---------------------------------------------------------------------------
class CourseOut(BaseModel):
    courseId: str
    courseCode: str
    courseName: str
    sectionId: str
    sectionName: str


class CreateCourseRequest(BaseModel):
    courseCode: str
    courseName: str
    departmentId: str | None = None
    syllabusSummary: str | None = None
    sectionName: str
    academicTerm: str
    facultyId: str | None = None


class CreateCourseData(BaseModel):
    courseId: str
    sectionId: str


class CreateEnrollmentRequest(BaseModel):
    studentId: str
    sectionId: str


class EnrollmentData(BaseModel):
    enrollmentId: str
    studentId: str
    sectionId: str
    enrollmentStatus: str


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
class CreateSessionRequest(BaseModel):
    sectionId: str
    classroomId: str | None = None
    topicTitle: str
    sessionDate: date
    startTime: datetime


class SessionData(BaseModel):
    sessionId: str
    sectionId: str
    topicTitle: str
    status: str
    startTime: datetime


class LiveSessionData(BaseModel):
    sessionId: str
    status: str
    attendanceCount: int
    verifiedCount: int
    pendingReviewCount: int


# ---------------------------------------------------------------------------
# QR / attendance
# ---------------------------------------------------------------------------
class QrData(BaseModel):
    sessionId: str
    qrPayload: str
    validUntil: datetime
    rotationSeconds: int


class ProximitySignal(BaseModel):
    wifiSsidHash: str | None = None
    beaconHash: str | None = None


class CheckInRequest(BaseModel):
    sessionId: str
    qrPayload: str
    deviceHash: str | None = None
    proximitySignal: ProximitySignal | None = None


class CheckInData(BaseModel):
    attendanceId: str
    verificationStatus: str
    checkInTime: datetime | None = None
    riskScore: int
    reason: str | None = None


class AttendanceSummaryData(BaseModel):
    courseId: str
    totalSessions: int
    attendedSessions: int
    attendancePercentage: float
    currentTier: str


class OverrideRequest(BaseModel):
    verificationStatus: Literal[
        "verified", "pending_review", "rejected", "manual_override"
    ]
    remarks: str | None = None


class OverrideData(BaseModel):
    attendanceId: str
    verificationStatus: str


# ---------------------------------------------------------------------------
# Quizzes
# ---------------------------------------------------------------------------
class LaunchQuizRequest(BaseModel):
    questionId: str
    durationSeconds: int = 60


class LaunchQuizData(BaseModel):
    sessionQuizId: str
    questionId: str
    launchedAt: datetime
    closesAt: datetime
    status: str


class ActiveQuizData(BaseModel):
    sessionQuizId: str
    topic: str
    questionText: str
    optionA: str | None = None
    optionB: str | None = None
    optionC: str | None = None
    optionD: str | None = None
    closesAt: datetime


class QuizResponseRequest(BaseModel):
    selectedOption: str | None = None
    freeTextAnswer: str | None = None


class QuizResponseData(BaseModel):
    responseId: str
    isCorrect: bool | None = None


class QuizAnalyticsOption(BaseModel):
    option: str
    count: int


class QuizAnalyticsData(BaseModel):
    sessionId: str
    quizzes: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Resources / rewards
# ---------------------------------------------------------------------------
class CreateResourceRequest(BaseModel):
    courseId: str
    title: str
    resourceType: str
    fileUrl: str
    topic: str | None = None
    requiredTier: Literal["bronze", "silver", "gold", "platinum"] = "bronze"


class ResourceData(BaseModel):
    resourceId: str
    title: str
    resourceType: str
    topic: str | None = None
    requiredTier: str
    fileUrl: str | None = None
    locked: bool = False


class RewardData(BaseModel):
    courseId: str
    attendancePercentage: float
    participationScore: float
    currentTier: str
    nextTier: str | None = None
    tiers: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Analytics / audit
# ---------------------------------------------------------------------------
class CourseAnalyticsData(BaseModel):
    courseId: str
    totalSessions: int
    averageAttendancePercentage: float
    totalStudents: int
    weakTopics: list[dict[str, Any]]


class AuditLogEntry(BaseModel):
    id: str
    actorUserId: str | None
    action: str
    entityType: str
    entityId: str | None
    createdAt: datetime
