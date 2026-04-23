"""Role-based access control.

Role hierarchy (for reference, not enforced — check exact match):
  user      — default. Can only access their own data.
  support   — read customer profiles, dispute history. No balance changes.
  ops       — reconciliation, ledger health, feature flags. No customer data writes.
  finance   — financial reports, float dashboard. Read-only on accounting.
  admin     — everything. Granted sparingly.

API pattern: @router.get("...", dependencies=[Depends(require_role("admin", "ops"))])
"""

import logging

from fastapi import Depends, HTTPException, status

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.db import models

logger = logging.getLogger(__name__)

VALID_ROLES: frozenset = frozenset({"user", "admin", "support", "ops", "finance"})


def require_role(*allowed: str):
    """FastAPI dependency factory. 403 if current_user.role not in allowed.

    No implicit hierarchy — require_role("admin") does NOT grant "ops" access.
    Caller lists every role explicitly. Matches AWS/GCP IAM semantics.
    """
    allowed_set = frozenset(allowed)
    unknown = allowed_set - VALID_ROLES
    if unknown:
        raise ValueError(f"require_role: unknown role(s) {unknown}")

    def _check(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        if current_user.role not in allowed_set:
            logger.warning(
                f"RBAC denied: user={current_user.email} role={current_user.role} "
                f"needed one of {sorted(allowed_set)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )
        return current_user

    return _check


def require_any_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Allow if role=="admin" OR email in ADMIN_EMAILS allowlist.

    Bootstrap bridge: lets the pre-RBAC email allowlist keep working while
    new users get provisioned via role='admin'. Safe to keep both paths
    indefinitely; safer still to retire the allowlist once every admin has
    role='admin' set.
    """
    if current_user.role == "admin":
        return current_user
    allowlist = settings.admin_emails_list
    if allowlist and current_user.email.lower() in allowlist:
        return current_user
    logger.warning(f"Admin access denied for {current_user.email} (role={current_user.role})")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized",
    )
