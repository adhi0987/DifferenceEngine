"""Audit logging helper (FR-16, section 8.19)."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .. import models


def record(
    db: Session,
    actor_user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    meta: dict | None = None,
) -> models.AuditLog:
    log = models.AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=json.dumps(meta) if meta else None,
    )
    db.add(log)
    db.flush()
    return log
