"""Audit event log integration tests.

Audit events must be atomic with the state change that triggered them.
If the outer DB transaction rolls back, the audit row must roll back too.
"""

import pytest
from sqlalchemy import inspect

from app.api.v1.payments import _complete_transaction
from app.core.security import get_password_hash
from app.db import models


@pytest.mark.integration
class TestAuditLogInternalTransfer:
    def test_internal_transfer_writes_one_audit_event(
        self, authenticated_client, test_account, db_session, test_user
    ):
        recipient = models.User(
            email="audit-recipient@example.com",
            phone="+263700000777",
            full_name="Audit Recipient",
            hashed_password=get_password_hash("x"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(recipient)
        db_session.commit()

        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 25,
                "currency": "USD",
                "recipient": "audit-recipient@example.com",
                "description": "audited transfer",
            },
        )
        assert response.status_code == 200, response.text
        tx_id = response.json()["id"]

        events = (
            db_session.query(models.AuditEvent).filter(models.AuditEvent.subject_id == tx_id).all()
        )
        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == "transaction.internal_transfer_completed"
        assert ev.source == "system"
        assert ev.subject_type == "transaction"
        assert ev.actor_user_id == test_user.id
        assert ev.payload["amount"] == "25.0"
        assert ev.payload["currency"] == "USD"
        assert "mirror_transaction_id" in ev.payload
        assert ev.payload["recipient_user_id"] == recipient.id


@pytest.mark.integration
class TestAuditLogPaynowFlow:
    def test_pending_paynow_send_has_no_audit_event_until_completion(
        self, authenticated_client, test_account, db_session
    ):
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 40,
                "currency": "USD",
                "recipient": "not-a-zippie-user@example.com",
                "description": "external send",
            },
        )
        assert response.status_code == 200
        tx_id = response.json()["id"]
        assert response.json()["status"] == "pending"

        events = (
            db_session.query(models.AuditEvent).filter(models.AuditEvent.subject_id == tx_id).all()
        )
        assert events == []

        transaction = db_session.query(models.Transaction).get(tx_id)
        assert _complete_transaction(db_session, transaction) is True

        events = (
            db_session.query(models.AuditEvent).filter(models.AuditEvent.subject_id == tx_id).all()
        )
        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == "transaction.completed"
        assert ev.source == "system"
        assert ev.payload["amount"] == "40.00"
        assert ev.payload["currency"] == "USD"


@pytest.mark.integration
class TestAuditLogAdminReconciliation:
    def test_admin_reconciliation_writes_audit_event(
        self, authenticated_client, test_user, db_session, monkeypatch
    ):
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS",
            test_user.email,
        )
        response = authenticated_client.get("/api/v1/admin/reconciliation")
        assert response.status_code == 200

        events = (
            db_session.query(models.AuditEvent)
            .filter(models.AuditEvent.event_type == "admin.reconciliation_check")
            .all()
        )
        assert len(events) == 1
        ev = events[0]
        assert ev.source == "admin"
        assert ev.actor_user_id == test_user.id
        assert ev.payload["invariant_ok"] is True
        assert ev.payload["global_drift"] == "0"
        assert ev.payload["violation_count"] == 0


@pytest.mark.integration
class TestAuditEventImmutabilityConventions:
    """Documentation test: the invariant that audit rows are immutable is
    enforced by convention, not a DB CHECK. This test pins the schema so
    any future change that would enable in-place mutation (adding an
    updated_at or status column, for instance) breaks loudly.
    """

    def test_no_updated_at_or_status_columns(self):
        cols = {c.name for c in inspect(models.AuditEvent).columns}
        assert "updated_at" not in cols
        assert "status" not in cols
        # These are the only columns allowed on AuditEvent
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
