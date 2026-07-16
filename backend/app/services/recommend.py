"""Recommendation engine: map missing COA concepts to curated resources.

Given the missing concepts (and inferred topic) from concept extraction, find
active resources for the course whose ``topic`` best matches, ranked so that
topic-aligned material surfaces first. Falls back to the course's general
resources when no topic match exists.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def recommend(
    db: Session,
    course_id: str,
    inferred_topic: str | None,
    missing_concepts: list[str],
    limit: int = 5,
) -> list[dict]:
    resources = db.scalars(
        select(models.Resource).where(
            models.Resource.course_id == course_id,
            models.Resource.is_active.is_(True),
        )
    ).all()

    needles = [c.lower() for c in missing_concepts]
    if inferred_topic:
        needles.append(inferred_topic.lower())

    scored: list[tuple[int, models.Resource]] = []
    for r in resources:
        haystack = f"{r.topic or ''} {r.title}".lower()
        score = sum(1 for n in needles if n and n in haystack)
        if score:
            scored.append((score, r))

    scored.sort(key=lambda t: t[0], reverse=True)
    chosen = [r for _, r in scored[:limit]]

    # If nothing matched, recommend a couple of general resources for the course.
    if not chosen:
        chosen = resources[:limit]

    return [
        {"resourceId": r.id, "title": r.title, "requiredTier": r.required_tier}
        for r in chosen
    ]
