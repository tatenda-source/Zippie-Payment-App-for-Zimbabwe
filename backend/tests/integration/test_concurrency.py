"""
Brutal concurrency test for the internal ledger.

This test is the answer to the CTO review: it proves that when 50 concurrent
transfers race for the same sender's balance, the final state is mathematically
correct — no lost updates, no overdrafts, no phantom ledger entries.

If this test ever fails, the financial core is broken. Do not ship.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.api.v1.payments import _internal_transfer
from app.core.config import settings
from app.db import models
from app.db.database import Base


@pytest.fixture(scope="module")
def engine():
    """Use the real Postgres DB — SQLite cannot test SELECT FOR UPDATE correctly."""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture
def session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_users(session_factory):
    """Create a sender with $500 and a recipient with $0.

    Cleans up afterwards so the test can run repeatedly.
    """
    session = session_factory()
    try:
        # Clean up any stale test users from a previous run.
        # audit_events and idempotency_keys don't have ORM-level cascade
        # relationships on User (by design — audit_events outlive users), so we
        # bulk-clear them first. accounts/transactions DO cascade via the ORM
        # relationship, so session.delete(user) handles those naturally.
        stale_emails = ["sender-ctest@zippie.test", "recipient-ctest@zippie.test"]
        stale = session.query(models.User).filter(models.User.email.in_(stale_emails)).all()
        stale_user_ids = [u.id for u in stale]
        if stale_user_ids:
            session.query(models.AuditEvent).filter(
                models.AuditEvent.actor_user_id.in_(stale_user_ids)
            ).delete(synchronize_session=False)
            session.query(models.IdempotencyKey).filter(
                models.IdempotencyKey.user_id.in_(stale_user_ids)
            ).delete(synchronize_session=False)
            for u in stale:
                session.delete(u)  # ORM delete → cascades to accounts + transactions
        session.commit()

        sender = models.User(
            email="sender-ctest@zippie.test",
            phone="+263770000001",
            full_name="Concurrency Sender",
            hashed_password="not-a-real-hash",
        )
        recipient = models.User(
            email="recipient-ctest@zippie.test",
            phone="+263770000002",
            full_name="Concurrency Recipient",
            hashed_password="not-a-real-hash",
        )
        session.add_all([sender, recipient])
        session.flush()

        sender_account = models.Account(
            user_id=sender.id,
            name="Main",
            currency="USD",
            account_type="primary",
            balance=500.00,
        )
        recipient_account = models.Account(
            user_id=recipient.id,
            name="Main",
            currency="USD",
            account_type="primary",
            balance=0.00,
        )
        session.add_all([sender_account, recipient_account])
        session.commit()

        yield {
            "sender_id": sender.id,
            "recipient_id": recipient.id,
            "sender_account_id": sender_account.id,
            "recipient_account_id": recipient_account.id,
            "initial_sender_balance": 500.00,
            "initial_recipient_balance": 0.00,
        }

        # Cleanup. Order matters: child rows without ORM cascades first
        # (ledger_entries, audit_events, idempotency_keys), then transactions
        # + accounts, then users via session.delete (which ORM-cascades
        # accounts/transactions — belt-and-suspenders).
        session.query(models.LedgerEntry).filter(
            models.LedgerEntry.account_id.in_([sender_account.id, recipient_account.id])
        ).delete(synchronize_session=False)
        session.query(models.AuditEvent).filter(
            models.AuditEvent.actor_user_id.in_([sender.id, recipient.id])
        ).delete(synchronize_session=False)
        session.query(models.IdempotencyKey).filter(
            models.IdempotencyKey.user_id.in_([sender.id, recipient.id])
        ).delete(synchronize_session=False)
        session.query(models.Transaction).filter(
            models.Transaction.user_id.in_([sender.id, recipient.id])
        ).delete(synchronize_session=False)
        session.delete(sender_account)
        session.delete(recipient_account)
        session.delete(sender)
        session.delete(recipient)
        session.commit()
    finally:
        session.close()


def _run_single_transfer(session_factory, test_users, amount):
    """Attempt a single $amount transfer in its own DB session (simulates request)."""
    session = session_factory()
    try:
        sender = session.query(models.User).get(test_users["sender_id"])
        recipient = session.query(models.User).get(test_users["recipient_id"])
        sender_account = session.query(models.Account).get(test_users["sender_account_id"])
        try:
            _internal_transfer(
                db=session,
                sender_user=sender,
                sender_account=sender_account,
                recipient_user=recipient,
                recipient_identifier=recipient.email,
                amount=amount,
                description="concurrency-test",
            )
            return "success"
        except HTTPException as e:
            if "Insufficient balance" in e.detail:
                return "insufficient"
            raise
    finally:
        session.close()


def test_concurrent_transfers_preserve_balance(session_factory, test_users):
    """50 concurrent $10 transfers on a $500 sender.

    Expected outcome:
      - Exactly 50 succeed (500 / 10 = 50)
      - Sender ends at $0
      - Recipient ends at $500
      - 50 transaction records + 100 ledger entries (1 DR + 1 CR per transfer)
      - sum(debits) == sum(credits) (ledger balances)
    """
    NUM_TRANSFERS = 50
    AMOUNT = 10.00

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(_run_single_transfer, session_factory, test_users, AMOUNT)
            for _ in range(NUM_TRANSFERS)
        ]
        results = [f.result() for f in as_completed(futures)]

    successes = results.count("success")
    insufficient = results.count("insufficient")

    # Verify final state
    session = session_factory()
    try:
        sender_account = session.query(models.Account).get(test_users["sender_account_id"])
        recipient_account = session.query(models.Account).get(test_users["recipient_account_id"])

        expected_successes = int(test_users["initial_sender_balance"] / AMOUNT)

        # Assert: correct number of transfers succeeded
        assert successes == expected_successes, (
            f"Expected {expected_successes} successful transfers, got {successes}. "
            f"Insufficient: {insufficient}. This means row locking is BROKEN."
        )

        # Assert: sender balance is exactly zero (no lost updates)
        assert sender_account.balance == 0.00, (
            f"Sender balance should be 0.00, got {sender_account.balance}. "
            f"This means concurrent updates corrupted the balance."
        )

        # Assert: recipient balance is exactly the total sent
        expected_recipient_balance = (
            test_users["initial_recipient_balance"] + expected_successes * AMOUNT
        )
        assert recipient_account.balance == expected_recipient_balance, (
            f"Recipient balance should be {expected_recipient_balance}, "
            f"got {recipient_account.balance}."
        )

        # Assert: double-entry ledger invariant holds
        sender_debits = (
            session.query(func.coalesce(func.sum(models.LedgerEntry.amount), 0))
            .filter(
                models.LedgerEntry.account_id == sender_account.id,
                models.LedgerEntry.direction == "debit",
            )
            .scalar()
        )
        recipient_credits = (
            session.query(func.coalesce(func.sum(models.LedgerEntry.amount), 0))
            .filter(
                models.LedgerEntry.account_id == recipient_account.id,
                models.LedgerEntry.direction == "credit",
            )
            .scalar()
        )

        assert (
            sender_debits == expected_successes * AMOUNT
        ), f"Sum of debits ({sender_debits}) != expected ({expected_successes * AMOUNT})"
        assert (
            recipient_credits == expected_successes * AMOUNT
        ), f"Sum of credits ({recipient_credits}) != expected ({expected_successes * AMOUNT})"
        assert (
            sender_debits == recipient_credits
        ), f"Ledger imbalance: debits={sender_debits}, credits={recipient_credits}"

        # Assert: number of transaction records matches successes
        # (each internal transfer creates 2: one 'sent', one 'received')
        tx_count = (
            session.query(models.Transaction)
            .filter(
                models.Transaction.description == "concurrency-test",
            )
            .count()
        )
        assert (
            tx_count == expected_successes * 2
        ), f"Expected {expected_successes * 2} transactions, got {tx_count}"
    finally:
        session.close()


def test_concurrent_transfers_partial_overspend(session_factory, test_users):
    """60 concurrent $10 transfers on a $500 sender — 10 should fail.

    This proves the system correctly rejects overspending under contention.
    """
    NUM_TRANSFERS = 60
    AMOUNT = 10.00

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(_run_single_transfer, session_factory, test_users, AMOUNT)
            for _ in range(NUM_TRANSFERS)
        ]
        results = [f.result() for f in as_completed(futures)]

    successes = results.count("success")
    insufficient = results.count("insufficient")

    expected_successes = int(test_users["initial_sender_balance"] / AMOUNT)
    expected_failures = NUM_TRANSFERS - expected_successes

    session = session_factory()
    try:
        sender_account = session.query(models.Account).get(test_users["sender_account_id"])

        assert (
            successes == expected_successes
        ), f"Expected {expected_successes} successes, got {successes}"
        assert (
            insufficient == expected_failures
        ), f"Expected {expected_failures} failures, got {insufficient}"
        assert sender_account.balance == 0.00, (
            f"Sender balance should be exactly 0, got {sender_account.balance}. "
            f"This means the system allowed an overdraft."
        )
    finally:
        session.close()
