"""Property-based tests for the double-entry ledger invariants.

We fuzz sequences of internal P2P transfers among a small pool of users and
assert run_reconciliation() stays clean after every sequence: per-account
balance == ledger_net, global drift zero, every internal tx balanced.
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.api.v1.payments import _internal_transfer
from app.core.security import get_password_hash
from app.db import models
from app.services.reconciliation import run_reconciliation


def _bootstrap_user(db, idx: int, starting_balance: Decimal):
    user = models.User(
        email=f"prop-user-{idx}@example.com",
        phone=f"+2637000001{idx:02d}",
        full_name=f"Prop User {idx}",
        hashed_password=get_password_hash("x"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()

    account = models.Account(
        user_id=user.id,
        name=f"Prop Wallet {idx}",
        balance=starting_balance,
        currency="USD",
        account_type="primary",
        is_active=True,
    )
    db.add(account)
    db.flush()

    bootstrap_tx = models.Transaction(
        user_id=user.id,
        account_id=account.id,
        transaction_type="received",
        amount=starting_balance,
        currency="USD",
        recipient=user.email,
        status="completed",
        payment_method="paynow_topup",
    )
    db.add(bootstrap_tx)
    db.flush()
    db.add(
        models.LedgerEntry(
            transaction_id=bootstrap_tx.id,
            account_id=account.id,
            amount=starting_balance,
            direction="credit",
            balance_after=starting_balance,
        )
    )
    return user, account


op_strategy = st.tuples(
    st.integers(min_value=0, max_value=2),
    st.integers(min_value=0, max_value=2),
    st.integers(min_value=1, max_value=50_000),
)

starting_balance_strategy = st.decimals(
    min_value=Decimal("100.00"),
    max_value=Decimal("10000.00"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)


@pytest.mark.integration
class TestLedgerInvariantsUnderFuzzing:
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        balances=st.lists(starting_balance_strategy, min_size=3, max_size=3),
        ops=st.lists(op_strategy, max_size=20),
    )
    def test_reconciliation_stays_clean_under_random_transfer_sequences(
        self, db_session, balances, ops
    ):
        # Fresh pool of 3 users per Hypothesis example.
        # db_session is function-scoped but Hypothesis reuses it across
        # examples; wipe the tables we touch so each example starts empty.
        db_session.rollback()
        db_session.query(models.LedgerEntry).delete()
        db_session.query(models.Transaction).delete()
        db_session.query(models.Account).delete()
        db_session.query(models.User).delete()
        db_session.commit()

        users_and_accounts = [_bootstrap_user(db_session, i, balances[i]) for i in range(3)]
        db_session.commit()

        for sender_idx, recipient_idx, amount_cents in ops:
            if sender_idx == recipient_idx:
                continue
            sender_user, sender_account = users_and_accounts[sender_idx]
            recipient_user, _ = users_and_accounts[recipient_idx]
            amount = Decimal(str(amount_cents)) / Decimal("100")
            try:
                _internal_transfer(
                    db_session,
                    sender_user,
                    sender_account,
                    recipient_user,
                    recipient_user.email,
                    amount,
                    None,
                )
            except HTTPException:
                # Legitimate rejection (insufficient balance, self-send, etc.)
                db_session.rollback()

        report = run_reconciliation(db_session)
        assert report.invariant_ok is True, (
            f"Invariant violated. "
            f"balances={balances} ops={ops} "
            f"account_violations={report.account_violations} "
            f"unbalanced_internal={report.unbalanced_internal} "
            f"global_drift={report.global_drift}"
        )
        assert report.global_drift == Decimal(0)
        assert len(report.account_violations) == 0
        assert len(report.unbalanced_internal) == 0
