"""End-to-end tests covering the AttendIQ COA Phase 1 API flows."""
from __future__ import annotations

from tests.conftest import auth, login


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "healthy"


def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "institutionalId": "NEW001",
            "fullName": "New Student",
            "email": "new@attendiq.edu",
            "password": "secret123",
            "role": "student",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True

    token = login(client, "new@attendiq.edu", "secret123")
    assert token

    # Wrong password rejected.
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "new@attendiq.edu", "password": "wrong"},
    )
    assert bad.status_code == 401


def test_role_based_access(client):
    student = login(client, "student1@attendiq.edu")
    # Students cannot create courses.
    resp = client.post(
        "/api/v1/admin/courses",
        headers=auth(student),
        json={
            "courseCode": "X",
            "courseName": "X",
            "sectionName": "s",
            "academicTerm": "t",
        },
    )
    assert resp.status_code == 403


def _course_and_section(client, token):
    resp = client.get("/api/v1/courses", headers=auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data
    return data[0]["courseId"], data[0]["sectionId"]


def test_full_attendance_and_quiz_flow(client):
    faculty = login(client, "faculty@attendiq.edu")
    student = login(client, "student1@attendiq.edu")

    course_id, section_id = _course_and_section(client, faculty)

    # Create a session.
    resp = client.post(
        "/api/v1/faculty/sessions",
        headers=auth(faculty),
        json={
            "sectionId": section_id,
            "topicTitle": "Cache Mapping",
            "sessionDate": "2026-07-16",
            "startTime": "2026-07-16T10:00:00+00:00",
        },
    )
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["data"]["sessionId"]

    # Cannot get QR before session is active.
    resp = client.get(
        f"/api/v1/faculty/sessions/{session_id}/qr", headers=auth(faculty)
    )
    assert resp.status_code == 409

    # Start session.
    resp = client.post(
        f"/api/v1/faculty/sessions/{session_id}/start", headers=auth(faculty)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "active"

    # Get QR.
    resp = client.get(
        f"/api/v1/faculty/sessions/{session_id}/qr", headers=auth(faculty)
    )
    assert resp.status_code == 200, resp.text
    qr_payload = resp.json()["data"]["qrPayload"]

    # Student check-in with valid QR.
    resp = client.post(
        "/api/v1/student/attendance/check-in",
        headers=auth(student),
        json={"sessionId": session_id, "qrPayload": qr_payload},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["verificationStatus"] in ("verified", "pending_review")

    # Duplicate check-in rejected.
    resp = client.post(
        "/api/v1/student/attendance/check-in",
        headers=auth(student),
        json={"sessionId": session_id, "qrPayload": qr_payload},
    )
    assert resp.status_code == 409

    # Invalid QR rejected.
    other = login(client, "student2@attendiq.edu")
    resp = client.post(
        "/api/v1/student/attendance/check-in",
        headers=auth(other),
        json={"sessionId": session_id, "qrPayload": "bogus.signature"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "QR_EXPIRED"

    # Live dashboard reflects one attendee.
    resp = client.get(
        f"/api/v1/faculty/sessions/{session_id}/live", headers=auth(faculty)
    )
    assert resp.json()["data"]["attendanceCount"] == 1

    # --- Quiz flow ---
    # Find a question id via analytics-free path: use quiz launch with a known topic.
    # We fetch questions by launching one from the seeded bank. Get question id
    # by creating a quiz through course question lookup is not exposed, so we
    # rely on the seeded questions through a direct DB-independent approach:
    # launch requires questionId, so query the course's questions via a helper.
    question_id = _first_question_id(client, faculty, course_id)

    resp = client.post(
        f"/api/v1/faculty/sessions/{session_id}/quizzes",
        headers=auth(faculty),
        json={"questionId": question_id, "durationSeconds": 120},
    )
    assert resp.status_code == 201, resp.text
    session_quiz_id = resp.json()["data"]["sessionQuizId"]

    # Student sees active quiz.
    resp = client.get(
        f"/api/v1/student/sessions/{session_id}/active-quiz", headers=auth(student)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["sessionQuizId"] == session_quiz_id

    # Student submits correct answer (seeded correct option is 'C' for cache mapping).
    resp = client.post(
        f"/api/v1/student/quizzes/{session_quiz_id}/responses",
        headers=auth(student),
        json={"selectedOption": "C"},
    )
    assert resp.status_code == 201, resp.text

    # Quiz analytics.
    resp = client.get(
        f"/api/v1/faculty/sessions/{session_id}/quiz-analytics", headers=auth(faculty)
    )
    assert resp.status_code == 200
    quizzes = resp.json()["data"]["quizzes"]
    assert quizzes and quizzes[0]["totalResponses"] == 1

    # Attendance summary.
    resp = client.get(
        f"/api/v1/student/attendance/summary?courseId={course_id}",
        headers=auth(student),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["attendedSessions"] == 1


def test_resource_access_control(client):
    faculty = login(client, "faculty@attendiq.edu")
    student = login(client, "student1@attendiq.edu")
    course_id, _ = _course_and_section(client, faculty)

    resp = client.get(
        f"/api/v1/student/resources?courseId={course_id}", headers=auth(student)
    )
    assert resp.status_code == 200, resp.text
    resources = resp.json()["data"]
    assert resources
    # With no attendance, bronze+ tiers are locked (student tier is 'none').
    locked = {r["title"]: r["locked"] for r in resources}
    assert all(locked.values())


def test_override_and_audit(client):
    admin = login(client, "admin@attendiq.edu")
    faculty = login(client, "faculty@attendiq.edu")
    student = login(client, "student1@attendiq.edu")
    course_id, section_id = _course_and_section(client, faculty)

    # Create+start session, get QR, check-in.
    session_id = _active_session(client, faculty, section_id)
    qr_payload = client.get(
        f"/api/v1/faculty/sessions/{session_id}/qr", headers=auth(faculty)
    ).json()["data"]["qrPayload"]
    attendance_id = client.post(
        "/api/v1/student/attendance/check-in",
        headers=auth(student),
        json={"sessionId": session_id, "qrPayload": qr_payload},
    ).json()["data"]["attendanceId"]

    # Faculty overrides.
    resp = client.post(
        f"/api/v1/faculty/attendance/{attendance_id}/override",
        headers=auth(faculty),
        json={"verificationStatus": "manual_override", "remarks": "Present in class"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["verificationStatus"] == "manual_override"

    # Admin can read audit logs; students cannot.
    resp = client.get("/api/v1/admin/audit-logs", headers=auth(admin))
    assert resp.status_code == 200
    actions = {e["action"] for e in resp.json()["data"]}
    assert "ATTENDANCE_OVERRIDE" in actions

    resp = client.get("/api/v1/admin/audit-logs", headers=auth(student))
    assert resp.status_code == 403


def test_course_analytics(client):
    faculty = login(client, "faculty@attendiq.edu")
    course_id, _ = _course_and_section(client, faculty)
    resp = client.get(
        f"/api/v1/faculty/analytics/course/{course_id}", headers=auth(faculty)
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["totalStudents"] == 5


# --- helpers that use only the public API + the app DB session ------------
def _active_session(client, faculty, section_id):
    session_id = client.post(
        "/api/v1/faculty/sessions",
        headers=auth(faculty),
        json={
            "sectionId": section_id,
            "topicTitle": "Session",
            "sessionDate": "2026-07-16",
            "startTime": "2026-07-16T10:00:00+00:00",
        },
    ).json()["data"]["sessionId"]
    client.post(f"/api/v1/faculty/sessions/{session_id}/start", headers=auth(faculty))
    return session_id


def _first_question_id(client, faculty, course_id):
    """Fetch a seeded question id straight from the app database."""
    import app.models as models
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        q = db.query(models.QuizQuestion).filter(
            models.QuizQuestion.course_id == course_id,
            models.QuizQuestion.topic == "Cache Mapping",
        ).first()
        return q.id
    finally:
        db.close()
