"""Seed the database with demo data for local development and testing.

Run with:  python -m app.seed
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from . import models
from .database import SessionLocal, init_db
from .security import hash_password, sha256_hex

DEMO_PASSWORD = "Password@123"


def _get_or_create_user(db, *, institutional_id, full_name, email, role) -> models.User:
    user = db.scalar(select(models.User).where(models.User.email == email))
    if user:
        return user
    user = models.User(
        institutional_id=institutional_id,
        full_name=full_name,
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.scalar(select(models.User).limit(1)):
            print("Database already seeded; skipping.")
            return

        admin = _get_or_create_user(
            db,
            institutional_id="ADM001",
            full_name="System Admin",
            email="admin@attendiq.edu",
            role="admin",
        )
        faculty = _get_or_create_user(
            db,
            institutional_id="FAC001",
            full_name="Dr. Ada Lovelace",
            email="faculty@attendiq.edu",
            role="faculty",
        )
        students = [
            _get_or_create_user(
                db,
                institutional_id=f"COA2026{i:03d}",
                full_name=f"Student {i}",
                email=f"student{i}@attendiq.edu",
                role="student",
            )
            for i in range(1, 6)
        ]

        department = models.Department(name="Computer Science", code="CSE")
        db.add(department)
        db.flush()

        course = models.Course(
            department_id=department.id,
            course_code="COA301",
            course_name="Computer Organization and Architecture",
            syllabus_summary="CPU organization, pipelining, cache, memory hierarchy, I/O.",
        )
        db.add(course)
        db.flush()

        section = models.CourseSection(
            course_id=course.id,
            faculty_id=faculty.id,
            section_name="COA-A",
            academic_term="Semester 3",
        )
        db.add(section)
        db.flush()

        classroom = models.Classroom(
            room_code="LAB-COA-02",
            room_name="COA Lab 2",
            building_name="Engineering Block",
            wifi_ssid_hash=sha256_hex("CAMPUS-COA-WIFI"),
        )
        db.add(classroom)
        db.flush()

        for student in students:
            db.add(models.Enrollment(student_id=student.id, section_id=section.id))

        # Reward policies (tiers).
        policies = [
            ("bronze", 40, 0),
            ("silver", 60, 1),
            ("gold", 75, 3),
            ("platinum", 90, 5),
        ]
        for tier, att, part in policies:
            db.add(
                models.RewardPolicy(
                    course_id=course.id,
                    tier_name=tier,
                    min_attendance_percentage=att,
                    min_participation_score=part,
                )
            )

        # Quiz question bank.
        questions = [
            ("Cache Mapping", "Which cache mapping allows a block to go into any line?",
             "Direct", "Set-associative", "Fully associative", "None", "C"),
            ("Pipelining", "A data hazard occurs when:",
             "Two instructions need the same register value in sequence",
             "The clock is too slow", "Memory is full", "The cache misses", "A"),
            ("Addressing Modes", "In immediate addressing, the operand is:",
             "In a register", "Part of the instruction", "In memory", "On the stack", "B"),
        ]
        for topic, q, a, b, c, d, correct in questions:
            db.add(
                models.QuizQuestion(
                    course_id=course.id,
                    topic=topic,
                    question_text=q,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    option_d=d,
                    correct_option=correct,
                    created_by=faculty.id,
                )
            )

        # Resources across tiers.
        resources = [
            ("COA Lecture Notes - Unit 1", "notes", "CPU Organization", "bronze"),
            ("Previous Year Questions", "pyq", "Full Syllabus", "silver"),
            ("Cache Lab Solutions", "lab_solution", "Cache Mapping", "gold"),
            ("Full Mock Test Pack", "practice_test", "Full Syllabus", "platinum"),
        ]
        for title, rtype, topic, tier in resources:
            db.add(
                models.Resource(
                    course_id=course.id,
                    uploaded_by=faculty.id,
                    title=title,
                    resource_type=rtype,
                    topic=topic,
                    file_url=f"https://files.attendiq.edu/{title.replace(' ', '_')}.pdf",
                    required_tier=tier,
                )
            )

        # A scheduled session for demos.
        now = datetime.now(timezone.utc)
        db.add(
            models.ClassSession(
                section_id=section.id,
                classroom_id=classroom.id,
                topic_title="Pipeline Hazards",
                session_date=date.today(),
                start_time=now + timedelta(minutes=5),
                status="scheduled",
                created_by=faculty.id,
            )
        )

        db.commit()
        print("Seed complete.")
        print(f"  Admin:   admin@attendiq.edu / {DEMO_PASSWORD}")
        print(f"  Faculty: faculty@attendiq.edu / {DEMO_PASSWORD}")
        print(f"  Student: student1@attendiq.edu / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
