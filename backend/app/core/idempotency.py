"""Idempotency-key middleware helper.

Pattern:
  1. Client sends `X-Idempotency-Key: <uuid>` with POST.
  2. Handler calls `check_idempotency(db, user, key, path)` FIRST.
  3. If cached: returns the cached response (status + body).
  4. If not cached: handler does its work, then calls `store_idempotency(db, user, key, path, status, body)` before returning.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import models

TTL = timedelta(hours=24)


def _validate(key: Optional[str]) -> Optional[str]:
    if key is None:
        return None
    if not isinstance(key, str) or len(key) < 1 or len(key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Idempotency-Key",
        )
    return key


def check_idempotency(
    db: Session,
    user: models.User,
    key: Optional[str],
    request_path: str,
) -> Optional[Tuple[int, dict]]:
    key = _validate(key)
    if not key:
        return None
    row = (
        db.query(models.IdempotencyKey)
        .filter(
            models.IdempotencyKey.key == key,
            models.IdempotencyKey.user_id == user.id,
            models.IdempotencyKey.path == request_path,
        )
        .first()
    )
    if row is None:
        return None
    # TTL check — treat expired rows as a miss; client should resend with fresh key.
    created = row.created_at
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if created is not None and datetime.now(timezone.utc) - created > TTL:
        return None
    return row.response_status, row.response_body or {}


def store_idempotency(
    db: Session,
    user: models.User,
    key: Optional[str],
    request_path: str,
    response_status: int,
    response_body: dict,
) -> None:
    key = _validate(key)
    if not key:
        return
    db.add(
        models.IdempotencyKey(
            key=key,
            user_id=user.id,
            method="POST",
            path=request_path,
            response_status=response_status,
            response_body=response_body,
        )
    )
    db.flush()
