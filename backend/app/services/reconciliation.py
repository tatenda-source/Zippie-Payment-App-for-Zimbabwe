"""Ledger reconciliation — pure functions that check integrity invariants.

The job of this module is to answer, at any point in time, three questions:

  1. For every account, does `balance` equal `SUM(credits) - SUM(debits)`
     across its ledger entries? Any account where these disagree is drift —
     the wallet either lost or gained money without a corresponding
     ledger movement, which is an invariant violation.

  2. Globally, does `SUM(all account balances)` equal
     `SUM(all credit ledger entries) - SUM(all debit ledger entries)`?
     This is the system-wide health metric — the single number an ops
     dashboard should surface.

  3. For every completed *internal* P2P transfer (payment_method =
     'zippie_internal'), does the transaction have exactly one balanced
     debit/credit pair in ledger_entries?

Paynow-routed transactions are single-entry by design (the counterparty is
external to the system), so they're excluded from check (3).

These functions do not mutate state. They can be called safely from any
read-only context: admin endpoint, cron job, test assertion, etc.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models


@dataclass
class AccountDrift:
    """One account whose balance column disagrees with its ledger entries."""

    account_id: int
    user_id: int
    currency: str
    balance: Decimal
    ledger_net: Decimal
    drift: Decimal


@dataclass
class UnbalancedInternalTx:
    """An internal P2P transfer that isn't balanced (DR != CR)."""

    transaction_id: int
    debit_total: Decimal
    credit_total: Decimal


@dataclass
class ReconciliationReport:
    timestamp: Optional[str] = None
    account_count: int = 0
    transaction_count: int = 0
    ledger_entry_count: int = 0

    # Global totals
    total_balance: Decimal = Decimal(0)
    ledger_credits_total: Decimal = Decimal(0)
    ledger_debits_total: Decimal = Decimal(0)
    ledger_net: Decimal = Decimal(0)  # credits - debits
    global_drift: Decimal = Decimal(0)  # total_balance - ledger_net

    # Per-currency breakdown (for ops visibility)
    per_currency: dict = field(default_factory=dict)

    # Per-account drift violations
    account_violations: List[AccountDrift] = field(default_factory=list)

    # Unbalanced internal transfers
    unbalanced_internal: List[UnbalancedInternalTx] = field(default_factory=list)

    @property
    def invariant_ok(self) -> bool:
        """True iff the ledger is fully consistent (no drift anywhere)."""
        return (
            self.global_drift == Decimal(0)
            and not self.account_violations
            and not self.unbalanced_internal
        )


def _d(value) -> Decimal:
    """Coerce None/float/Decimal/int to Decimal cleanly."""
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def run_reconciliation(db: Session) -> ReconciliationReport:
    """Compute the full reconciliation report in one read-only pass."""
    from datetime import datetime, timezone

    report = ReconciliationReport(
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    # 1. Per-account drift check
    # Pull ledger net (credits - debits) per account in a single query.
    credits_col = func.coalesce(
        func.sum(
            models.LedgerEntry.amount
        ).filter(models.LedgerEntry.direction == "credit"),
        0,
    )
    debits_col = func.coalesce(
        func.sum(
            models.LedgerEntry.amount
        ).filter(models.LedgerEntry.direction == "debit"),
        0,
    )

    per_account_rows = (
        db.query(
            models.Account.id,
            models.Account.user_id,
            models.Account.currency,
            models.Account.balance,
            credits_col.label("credits"),
            debits_col.label("debits"),
        )
        .outerjoin(
            models.LedgerEntry,
            models.LedgerEntry.account_id == models.Account.id,
        )
        .group_by(models.Account.id)
        .all()
    )

    per_currency: dict = {}

    for row in per_account_rows:
        balance = _d(row.balance)
        credits = _d(row.credits)
        debits = _d(row.debits)
        net = credits - debits
        drift = balance - net

        report.account_count += 1
        report.total_balance += balance
        report.ledger_credits_total += credits
        report.ledger_debits_total += debits

        ccy = row.currency or "USD"
        bucket = per_currency.setdefault(
            ccy,
            {
                "balance": Decimal(0),
                "credits": Decimal(0),
                "debits": Decimal(0),
                "account_count": 0,
            },
        )
        bucket["balance"] += balance
        bucket["credits"] += credits
        bucket["debits"] += debits
        bucket["account_count"] += 1

        if drift != 0:
            report.account_violations.append(
                AccountDrift(
                    account_id=row.id,
                    user_id=row.user_id,
                    currency=ccy,
                    balance=balance,
                    ledger_net=net,
                    drift=drift,
                )
            )

    report.ledger_net = (
        report.ledger_credits_total - report.ledger_debits_total
    )
    report.global_drift = report.total_balance - report.ledger_net
    report.per_currency = {
        ccy: {
            "balance": str(b["balance"]),
            "credits": str(b["credits"]),
            "debits": str(b["debits"]),
            "net": str(b["credits"] - b["debits"]),
            "drift": str(b["balance"] - (b["credits"] - b["debits"])),
            "account_count": b["account_count"],
        }
        for ccy, b in per_currency.items()
    }

    report.transaction_count = db.query(models.Transaction).count()
    report.ledger_entry_count = db.query(models.LedgerEntry).count()

    # 2. Unbalanced internal transfers
    # _internal_transfer() writes two Transaction rows per transfer — one from
    # the sender's perspective (type='sent') that holds both ledger entries
    # (the DR/CR pair), and a mirror row from the recipient's perspective
    # (type='received') that has no ledger entries (the mirror is a history
    # view, not a money movement). Only the 'sent' row is the authoritative
    # money movement, so we check only those.
    internal_tx_rows = (
        db.query(
            models.Transaction.id,
            func.coalesce(
                func.sum(models.LedgerEntry.amount).filter(
                    models.LedgerEntry.direction == "debit"
                ),
                0,
            ).label("debit_total"),
            func.coalesce(
                func.sum(models.LedgerEntry.amount).filter(
                    models.LedgerEntry.direction == "credit"
                ),
                0,
            ).label("credit_total"),
        )
        .outerjoin(
            models.LedgerEntry,
            models.LedgerEntry.transaction_id == models.Transaction.id,
        )
        .filter(
            models.Transaction.payment_method == "zippie_internal",
            models.Transaction.status == "completed",
            models.Transaction.transaction_type == "sent",
        )
        .group_by(models.Transaction.id)
        .all()
    )

    for tx_row in internal_tx_rows:
        debit = _d(tx_row.debit_total)
        credit = _d(tx_row.credit_total)
        if debit != credit or debit == 0:
            report.unbalanced_internal.append(
                UnbalancedInternalTx(
                    transaction_id=tx_row.id,
                    debit_total=debit,
                    credit_total=credit,
                )
            )

    return report
