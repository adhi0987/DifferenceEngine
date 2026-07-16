"""Tests for the Phase 2 AI submission pipeline (heuristic path)."""
from __future__ import annotations

from tests.conftest import auth, login


def _course_id(client, token):
    resp = client.get("/api/v1/courses", headers=auth(token))
    return resp.json()["data"][0]["courseId"]


def test_ai_submission_end_to_end(client):
    student = login(client, "student1@attendiq.edu")
    faculty = login(client, "faculty@attendiq.edu")
    course_id = _course_id(client, faculty)

    # Upload a text "transcript" (OCR sidecar/text path keeps this deps-free).
    answer = (
        "Pipeline hazards include structural hazards, data hazards and control "
        "hazards. Forwarding is used to reduce stalls."
    )
    resp = client.post(
        "/api/v1/student/ai/uploads",
        headers=auth(student),
        files={"file": ("answer.txt", answer, "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    image_url = resp.json()["data"]["imageFileUrl"]
    assert image_url.startswith("storage://")

    # Create submission (background task runs synchronously under TestClient).
    resp = client.post(
        "/api/v1/student/ai/submissions",
        headers=auth(student),
        json={"courseId": course_id, "imageFileUrl": image_url},
    )
    assert resp.status_code == 201, resp.text
    submission_id = resp.json()["data"]["submissionId"]

    # Retrieve processed result.
    resp = client.get(
        f"/api/v1/student/ai/submissions/{submission_id}", headers=auth(student)
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["processingStatus"] == "completed"
    assert "hazard" in data["extractedText"].lower()

    fb = data["modelFeedback"]
    assert fb["inferredTopic"] == "Pipelining"
    assert "Data hazard" in fb["detectedConcepts"]
    assert "Branch prediction" in fb["missingConcepts"]
    assert fb["conceptCoverageScore"] > 0
    assert isinstance(fb["recommendedResources"], list)


def test_ai_submission_ownership(client):
    student1 = login(client, "student1@attendiq.edu")
    student2 = login(client, "student2@attendiq.edu")
    faculty = login(client, "faculty@attendiq.edu")
    course_id = _course_id(client, faculty)

    resp = client.post(
        "/api/v1/student/ai/uploads",
        headers=auth(student1),
        files={"file": ("a.txt", "cache mapping direct mapped", "text/plain")},
    )
    image_url = resp.json()["data"]["imageFileUrl"]
    submission_id = client.post(
        "/api/v1/student/ai/submissions",
        headers=auth(student1),
        json={"courseId": course_id, "imageFileUrl": image_url},
    ).json()["data"]["submissionId"]

    # Another student cannot read it.
    resp = client.get(
        f"/api/v1/student/ai/submissions/{submission_id}", headers=auth(student2)
    )
    assert resp.status_code == 403
