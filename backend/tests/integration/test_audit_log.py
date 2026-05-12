"""Audit event log integration tests.

Audit events must be atomic with the state change that triggered them.
Post-pivot, every rails-routed transfer writes a
`transaction.rails_transfer_initiated` event; completion writes a
`transaction.completed` event.
"""

import pytest
from sqlalchemy import inspect

from app.api.v1.payments import _complete_transaction
from app.db import models


@pytest.mark.integration
class TestAuditLogRailsTransfer:
    def test_rails_transfer_writes_one_audit_event(
        self, authenticated_client, test_account, test_recipient, db_session, test_user
    ):
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 25,
                "currency": "USD",
                "recipient": test_recipient.email,
                "description": "audited transfer",
            },
        )
        assert response.status_code == 200, response.text
        tx_id = response.json()["id"]

        events = (
            db_session.query(models.AuditEvent)
            .filter(models.AuditEvent.subject_id == tx_id)
            .all()
        )
        # rails_transfer_initiated on send; transaction.completed when the
        # mock adapter resolves synchronously.
        event_types = sorted(e.event_type for e in events)
        assert "transaction.rails_transfer_initiated" in event_types

        init = next(e for e in events if e.event_type == "transaction.rails_transfer_initiated")
        assert init.source == "system"
        assert init.subject_type == "transaction"
        assert init.actor_user_id == test_user.id
        assert init.payload["amount"] == "25.0"
        assert init.payload["currency"] == "USD"
        assert init.payload["sender_paynow_id"] == test_user.paynow_id
        assert init.payload["recipient_paynow_id"] == test_recipient.paynow_id


@pytest.mark.integration
class TestAuditLogCompletion:
    def test_completion_writes_audit_event(
        self, authenticated_client, test_account, test_recipient, db_session
    ):
        """Calling _complete_transaction on a pending tx writes one event."""
        # Create a "received" pending transaction directly (no rails call).
        tx = models.Transaction(
            user_id=test_recipient.id,
            account_id=None,
            transaction_type="received",
            amount=40,
            currency="USD",
            recipient=test_recipient.email,
            status="pending",
            payment_method="paynow_rails",
        )
        db_session.add(tx)
        db_session.commit()
        db_session.refresh(tx)

        assert _complete_transaction(db_session, tx) is True

        events = (
            db_session.query(models.AuditEvent)
            .filter(
                models.AuditEvent.subject_id == tx.id,
                models.AuditEvent.event_type == "transaction.completed",
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].payload["currency"] == "USD"


@pytest.mark.integration
class TestAuditEventImmutabilityConventions:
    """The invariant that audit rows are immutable is enforced by convention.

    This pins the schema so any future change that would enable in-place
    mutation (adding updated_at or status) breaks loudly.
    """

    def test_no_updated_at_or_status_columns(self):
        cols = {c.name for c in inspect(models.AuditEvent).columns}
        assert "updated_at" not in cols
        assert "status" not in cols
        expected = {
            "id",
            "source",
            "event_type",
            "subject_type",
            "subject_id",
            "actor_user_id",
            "payload",
            "created_at",
        }
        assert cols == expected

    def test_created_at_has_server_default(self):
        created_at = inspect(models.AuditEvent).columns["created_at"]
        assert created_at.server_default is not None
        assert created_at.nullable is False
