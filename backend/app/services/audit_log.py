"""Append-only audit event log.

Audit events ride on the caller's DB transaction — this module never commits.
That's deliberate: auditing that isn't atomic with the state change is worthless.
If the state change rolls back, so does the audit row.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.db import models


def record_event(
    db: Session,
    source: str,
    event_type: str,
    subject_type: Optional[str] = None,
    subject_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    payload: Optional[dict] = None,
) -> None:
    """Append one audit event. Caller owns the transaction — we don't commit."""
    db.add(models.AuditEvent(
        source=source,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor_user_id=actor_user_id,
        payload=payload,
    ))
