"""Admin-gated endpoints: reconciliation, ops health, ledger integrity.

Authorization model (pilot-grade, pragmatic):
  - Admin access is an allowlist of email addresses in settings.ADMIN_EMAILS.
  - The allowlist lives in env config, not the DB — so granting admin can't
    be done by anyone with DB write access, and revocation is a deploy away.
  - Every admin hit is logged at INFO level.

This is the absolute minimum viable admin surface. Before any real traffic:
  - Add a second factor on admin-flagged users
  - Move to a role column on users once multiple ops people exist
  - Send admin-hit logs to a separate audit stream (Sentry breadcrumb or
    dedicated log sink), not just app logs.
"""

import logging
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.services.reconciliation import (
    AccountDrift,
    ReconciliationReport,
    UnbalancedInternalTx,
    run_reconciliation,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def require_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Auth dependency: current user's email must be in ADMIN_EMAILS."""
    allowlist = settings.admin_emails_list
    if not allowlist:
        # Fail closed: no one is admin unless ADMIN_EMAILS is explicitly set.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is not configured on this environment",
        )
    if current_user.email not in allowlist:
        logger.warning(
            f"Admin access denied for {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    return current_user


class AccountDriftResponse(BaseModel):
    account_id: int
    user_id: int
    currency: str
    balance: Decimal
    ledger_net: Decimal
    drift: Decimal


class UnbalancedInternalTxResponse(BaseModel):
    transaction_id: int
    debit_total: Decimal
    credit_total: Decimal


class ReconciliationResponse(BaseModel):
    timestamp: str
    invariant_ok: bool
    account_count: int
    transaction_count: int
    ledger_entry_count: int
    total_balance: Decimal
    ledger_credits_total: Decimal
    ledger_debits_total: Decimal
    ledger_net: Decimal
    global_drift: Decimal
    per_currency: dict
    account_violations: List[AccountDriftResponse]
    unbalanced_internal: List[UnbalancedInternalTxResponse]


def _serialize_drift(d: AccountDrift) -> AccountDriftResponse:
    return AccountDriftResponse(
        account_id=d.account_id,
        user_id=d.user_id,
        currency=d.currency,
        balance=d.balance,
        ledger_net=d.ledger_net,
        drift=d.drift,
    )


def _serialize_unbalanced(
    u: UnbalancedInternalTx,
) -> UnbalancedInternalTxResponse:
    return UnbalancedInternalTxResponse(
        transaction_id=u.transaction_id,
        debit_total=u.debit_total,
        credit_total=u.credit_total,
    )


def _serialize_report(r: ReconciliationReport) -> ReconciliationResponse:
    return ReconciliationResponse(
        timestamp=r.timestamp or "",
        invariant_ok=r.invariant_ok,
        account_count=r.account_count,
        transaction_count=r.transaction_count,
        ledger_entry_count=r.ledger_entry_count,
        total_balance=r.total_balance,
        ledger_credits_total=r.ledger_credits_total,
        ledger_debits_total=r.ledger_debits_total,
        ledger_net=r.ledger_net,
        global_drift=r.global_drift,
        per_currency=r.per_currency,
        account_violations=[_serialize_drift(d) for d in r.account_violations],
        unbalanced_internal=[
            _serialize_unbalanced(u) for u in r.unbalanced_internal
        ],
    )


@router.get("/reconciliation", response_model=ReconciliationResponse)
async def get_reconciliation(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Full ledger integrity report.

    Returns HTTP 200 regardless of whether violations exist — the response
    body's `invariant_ok` flag is the canonical health signal. Ops / cron
    should page on `invariant_ok == false` OR `global_drift != 0`.
    """
    logger.info(f"Reconciliation check requested by admin={admin.email}")
    report = run_reconciliation(db)

    if not report.invariant_ok:
        logger.error(
            f"LEDGER INTEGRITY VIOLATION: "
            f"global_drift={report.global_drift} "
            f"account_violations={len(report.account_violations)} "
            f"unbalanced_internal={len(report.unbalanced_internal)}"
        )

    return _serialize_report(report)


@router.get("/health/ledger")
async def ledger_health_summary(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lightweight health check — just the pass/fail bit + top-line totals.

    Cheaper than /reconciliation (same query path but trimmed response).
    Designed to be pollable from a status page or uptime monitor.
    """
    report = run_reconciliation(db)
    return {
        "invariant_ok": report.invariant_ok,
        "timestamp": report.timestamp,
        "account_count": report.account_count,
        "total_balance": str(report.total_balance),
        "ledger_net": str(report.ledger_net),
        "global_drift": str(report.global_drift),
        "violations": {
            "accounts": len(report.account_violations),
            "internal_transfers": len(report.unbalanced_internal),
        },
    }
