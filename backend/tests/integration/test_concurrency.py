"""Concurrency tests for the rails-adapter transfer path.

Post-pivot there is no internal float to race for. The concurrency
property we care about now is that paynow_transfer_ref is unique per
transaction — two threads that race to create a transfer never write
duplicate rails references, and the webhook handler can dedup safely on
that key.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.api.v1.payments import _rails_transfer
from app.core.config import settings
from app.db import models
from app.db.database import Base


@pytest.fixture(scope="module")
def engine():
    """Use the real Postgres DB — SQLite cannot test concurrent INSERTs well."""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture
def session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def parties(session_factory):
    """Sender + recipient with linked Paynow IDs. Cleans up afterwards."""
    session = session_factory()
    try:
        stale_emails = ["sender-ctest@paynow-connect.test", "recipient-ctest@paynow-connect.test"]
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
                session.delete(u)
        session.commit()

        sender = models.User(
            email="sender-ctest@paynow-connect.test",
            phone="+263770000001",
            full_name="Concurrency Sender",
            hashed_password="not-a-real-hash",
            paynow_id="pn-sender-ctest",
            is_verified=True,
        )
        recipient = models.User(
            email="recipient-ctest@paynow-connect.test",
            phone="+263770000002",
            full_name="Concurrency Recipient",
            hashed_password="not-a-real-hash",
            paynow_id="pn-recipient-ctest",
            is_verified=True,
        )
        session.add_all([sender, recipient])
        session.commit()

        yield {"sender_id": sender.id, "recipient_paynow_id": recipient.paynow_id}

        session.query(models.AuditEvent).filter(
            models.AuditEvent.actor_user_id.in_([sender.id, recipient.id])
        ).delete(synchronize_session=False)
        session.query(models.IdempotencyKey).filter(
            models.IdempotencyKey.user_id.in_([sender.id, recipient.id])
        ).delete(synchronize_session=False)
        session.query(models.Transaction).filter(
            models.Transaction.user_id.in_([sender.id, recipient.id])
        ).delete(synchronize_session=False)
        session.delete(sender)
        session.delete(recipient)
        session.commit()
    finally:
        session.close()


def _run_single_transfer(session_factory, parties, amount):
    """One transfer in its own DB session — simulates one request."""
    session = session_factory()
    try:
        sender = session.query(models.User).get(parties["sender_id"])
        tx = _rails_transfer(
            db=session,
            sender_user=sender,
            recipient_identifier="recipient-ctest@paynow-connect.test",
            recipient_paynow_id=parties["recipient_paynow_id"],
            amount=Decimal(str(amount)),
            currency="USD",
            description="concurrency-test",
        )
        return tx.paynow_transfer_ref
    finally:
        session.close()


def test_concurrent_transfers_all_unique_references(session_factory, parties):
    """50 concurrent rails transfers must produce 50 unique paynow_transfer_refs."""
    NUM = 50
    AMOUNT = 1.00

    with ThreadPoolExecutor(max_workers=20) as ex:
        refs = [
            f.result()
            for f in as_completed(
                [
                    ex.submit(_run_single_transfer, session_factory, parties, AMOUNT)
                    for _ in range(NUM)
                ]
            )
        ]

    # All non-empty
    assert all(r for r in refs)
    # All unique
    assert len(set(refs)) == NUM

    session = session_factory()
    try:
        # Persisted refs are unique too — the DB UNIQUE constraint would have
        # caused IntegrityError on any collision.
        tx_count = (
            session.query(func.count(models.Transaction.id))
            .filter(models.Transaction.description == "concurrency-test")
            .scalar()
        )
        assert tx_count == NUM
    finally:
        session.close()
