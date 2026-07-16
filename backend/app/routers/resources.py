"""Resource and reward APIs (section 10.6)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles
from ..services import audit, rewards

router = APIRouter(tags=["resources"])


@router.post(
    "/faculty/resources",
    response_model=schemas.ApiResponse[schemas.ResourceData],
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    body: schemas.CreateResourceRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("faculty", "admin")),
):
    if not db.get(models.Course, body.courseId):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid courseId")

    resource = models.Resource(
        course_id=body.courseId,
        uploaded_by=user.id,
        title=body.title,
        resource_type=body.resourceType,
        topic=body.topic,
        file_url=body.fileUrl,
        required_tier=body.requiredTier,
    )
    db.add(resource)
    db.flush()
    audit.record(db, user.id, "RESOURCE_CREATED", "resource", resource.id)
    db.commit()

    return schemas.ApiResponse(
        message="Resource created",
        data=schemas.ResourceData(
            resourceId=resource.id,
            title=resource.title,
            resourceType=resource.resource_type,
            topic=resource.topic,
            requiredTier=resource.required_tier,
            fileUrl=resource.file_url,
            locked=False,
        ),
    )


@router.get(
    "/student/resources",
    response_model=schemas.ApiResponse[list[schemas.ResourceData]],
)
def list_resources(
    courseId: str = Query(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    status_row = rewards.recompute_reward_status(db, user.id, courseId)
    current_tier = status_row.current_tier

    resources = db.scalars(
        select(models.Resource).where(
            models.Resource.course_id == courseId,
            models.Resource.is_active.is_(True),
        )
    ).all()

    data = []
    for r in resources:
        unlocked = rewards.tier_at_least(current_tier, r.required_tier)
        db.add(
            models.ResourceAccessLog(
                student_id=user.id,
                resource_id=r.id,
                access_allowed=unlocked,
                denial_reason=None if unlocked else f"Requires {r.required_tier} tier",
            )
        )
        data.append(
            schemas.ResourceData(
                resourceId=r.id,
                title=r.title,
                resourceType=r.resource_type,
                topic=r.topic,
                requiredTier=r.required_tier,
                fileUrl=r.file_url if unlocked else None,
                locked=not unlocked,
            )
        )
    db.commit()
    return schemas.ApiResponse(data=data)


@router.get(
    "/student/rewards",
    response_model=schemas.ApiResponse[schemas.RewardData],
)
def get_rewards(
    courseId: str = Query(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    status_row = rewards.recompute_reward_status(db, user.id, courseId)
    _, next_tier, tiers = rewards.determine_tier(
        db,
        courseId,
        float(status_row.attendance_percentage),
        float(status_row.participation_score),
    )
    db.commit()

    return schemas.ApiResponse(
        data=schemas.RewardData(
            courseId=courseId,
            attendancePercentage=float(status_row.attendance_percentage),
            participationScore=float(status_row.participation_score),
            currentTier=status_row.current_tier,
            nextTier=next_tier,
            tiers=tiers,
        )
    )
