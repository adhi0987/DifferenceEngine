"""Course and enrollment APIs (section 10.2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_roles
from ..services import audit

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=schemas.ApiResponse[list[schemas.CourseOut]])
def list_courses(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Return course sections visible to the current user."""
    stmt = select(models.CourseSection, models.Course).join(
        models.Course, models.Course.id == models.CourseSection.course_id
    )

    if user.role == "student":
        stmt = stmt.join(
            models.Enrollment,
            models.Enrollment.section_id == models.CourseSection.id,
        ).where(
            models.Enrollment.student_id == user.id,
            models.Enrollment.enrollment_status == "active",
        )
    elif user.role == "faculty":
        stmt = stmt.where(models.CourseSection.faculty_id == user.id)
    # admin sees everything

    rows = db.execute(stmt).all()
    data = [
        schemas.CourseOut(
            courseId=course.id,
            courseCode=course.course_code,
            courseName=course.course_name,
            sectionId=section.id,
            sectionName=section.section_name,
        )
        for section, course in rows
    ]
    return schemas.ApiResponse(data=data)


@router.post(
    "/admin/courses",
    response_model=schemas.ApiResponse[schemas.CreateCourseData],
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    body: schemas.CreateCourseRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("admin")),
):
    if body.facultyId:
        faculty = db.get(models.User, body.facultyId)
        if not faculty or faculty.role != "faculty":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid facultyId")

    course = models.Course(
        department_id=body.departmentId,
        course_code=body.courseCode,
        course_name=body.courseName,
        syllabus_summary=body.syllabusSummary,
    )
    db.add(course)
    db.flush()

    section = models.CourseSection(
        course_id=course.id,
        faculty_id=body.facultyId,
        section_name=body.sectionName,
        academic_term=body.academicTerm,
    )
    db.add(section)
    db.flush()
    audit.record(db, user.id, "COURSE_CREATED", "course", course.id)
    db.commit()

    return schemas.ApiResponse(
        message="Course created",
        data=schemas.CreateCourseData(courseId=course.id, sectionId=section.id),
    )


@router.post(
    "/admin/enrollments",
    response_model=schemas.ApiResponse[schemas.EnrollmentData],
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    body: schemas.CreateEnrollmentRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("admin")),
):
    student = db.get(models.User, body.studentId)
    if not student or student.role != "student":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid studentId")
    section = db.get(models.CourseSection, body.sectionId)
    if not section:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid sectionId")

    existing = db.scalar(
        select(models.Enrollment).where(
            models.Enrollment.student_id == body.studentId,
            models.Enrollment.section_id == body.sectionId,
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Student already enrolled")

    enrollment = models.Enrollment(
        student_id=body.studentId, section_id=body.sectionId
    )
    db.add(enrollment)
    db.flush()
    audit.record(db, user.id, "STUDENT_ENROLLED", "enrollment", enrollment.id)
    db.commit()

    return schemas.ApiResponse(
        message="Student enrolled",
        data=schemas.EnrollmentData(
            enrollmentId=enrollment.id,
            studentId=enrollment.student_id,
            sectionId=enrollment.section_id,
            enrollmentStatus=enrollment.enrollment_status,
        ),
    )
