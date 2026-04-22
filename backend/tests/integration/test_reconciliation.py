"""Reconciliation service + admin endpoint integration tests."""

from decimal import Decimal

import pytest

from app.api.v1.payments import (
    _build_paynow_reference,
    _parse_tx_id_from_reference,
)
from app.core.security import get_password_hash
from app.db import models
from app.services.reconciliation import run_reconciliation


@pytest.mark.integration
class TestReconciliationService:
    """Direct tests of run_reconciliation — no HTTP layer."""

    def test_empty_db_is_clean(self, db_session):
        report = run_reconciliation(db_session)
        assert report.invariant_ok
        assert report.account_count == 0
        assert report.global_drift == Decimal(0)
        assert report.account_violations == []
        assert report.unbalanced_internal == []

    def test_account_without_ledger_entries_but_zero_balance_is_clean(
        self, db_session, test_user
    ):
        account = models.Account(
            user_id=test_user.id,
            name="Empty Wallet",
            balance=Decimal(0),
            currency="USD",
        )
        db_session.add(account)
        db_session.commit()

        report = run_reconciliation(db_session)
        assert report.invariant_ok
        assert report.account_count == 1

    def test_account_balance_matching_ledger_entries_is_clean(
        self, db_session, test_user
    ):
        """$100 credit + $30 debit → balance should be $70, no drift."""
        account = models.Account(
            user_id=test_user.id,
            name="W",
            balance=Decimal("70.00"),
            currency="USD",
        )
        db_session.add(account)
        db_session.flush()

        tx = models.Transaction(
            user_id=test_user.id,
            account_id=account.id,
            transaction_type="received",
            amount=Decimal("100.00"),
            currency="USD",
            recipient=test_user.email,
            status="completed",
            payment_method="paynow_topup",
        )
        db_session.add(tx)
        db_session.flush()

        db_session.add(
            models.LedgerEntry(
                transaction_id=tx.id,
                account_id=account.id,
                amount=Decimal("100.00"),
                direction="credit",
                balance_after=Decimal("100.00"),
            )
        )
        tx2 = models.Transaction(
            user_id=test_user.id,
            account_id=account.id,
            transaction_type="sent",
            amount=Decimal("30.00"),
            currency="USD",
            recipient="external@x.com",
            status="completed",
            payment_method="ecocash",
        )
        db_session.add(tx2)
        db_session.flush()
        db_session.add(
            models.LedgerEntry(
                transaction_id=tx2.id,
                account_id=account.id,
                amount=Decimal("30.00"),
                direction="debit",
                balance_after=Decimal("70.00"),
            )
        )
        db_session.commit()

        report = run_reconciliation(db_session)
        assert report.invariant_ok, (
            f"Expected clean invariant. violations="
            f"{report.account_violations}"
        )
        assert report.total_balance == Decimal("70.00")
        assert report.ledger_credits_total == Decimal("100.00")
        assert report.ledger_debits_total == Decimal("30.00")
        assert report.ledger_net == Decimal("70.00")
        assert report.global_drift == Decimal(0)

    def test_balance_drift_is_detected(self, db_session, test_user):
        """Corrupt a balance column and confirm drift surfaces."""
        account = models.Account(
            user_id=test_user.id,
            name="Drifty",
            # Balance says $150 but there are no ledger entries. Drift = $150.
            balance=Decimal("150.00"),
            currency="USD",
        )
        db_session.add(account)
        db_session.commit()

        report = run_reconciliation(db_session)
        assert not report.invariant_ok
        assert report.global_drift == Decimal("150.00")
        assert len(report.account_violations) == 1
        violation = report.account_violations[0]
        assert violation.account_id == account.id
        assert violation.balance == Decimal("150.00")
        assert violation.ledger_net == Decimal(0)
        assert violation.drift == Decimal("150.00")

    def test_unbalanced_internal_transfer_is_detected(
        self, db_session, test_user
    ):
        """Internal Zippie tx with only a debit (no credit) should be flagged."""
        account = models.Account(
            user_id=test_user.id,
            name="W",
            balance=Decimal(0),
            currency="USD",
        )
        db_session.add(account)
        db_session.flush()

        tx = models.Transaction(
            user_id=test_user.id,
            account_id=account.id,
            transaction_type="sent",
            amount=Decimal("20.00"),
            currency="USD",
            recipient="r@x.com",
            status="completed",
            payment_method="zippie_internal",
        )
        db_session.add(tx)
        db_session.flush()
        db_session.add(
            models.LedgerEntry(
                transaction_id=tx.id,
                account_id=account.id,
                amount=Decimal("20.00"),
                direction="debit",
                balance_after=Decimal("-20.00"),
            )
        )
        db_session.commit()

        report = run_reconciliation(db_session)
        assert len(report.unbalanced_internal) == 1
        unbal = report.unbalanced_internal[0]
        assert unbal.transaction_id == tx.id
        assert unbal.debit_total == Decimal("20.00")
        assert unbal.credit_total == Decimal(0)
        assert not report.invariant_ok


@pytest.mark.integration
class TestReconciliationEndToEnd:
    """Full flow: drive transactions through the real API, then prove
    run_reconciliation() sees them and reports zero drift.

    This is the canonical smoke test for the ledger + reconciliation pair.
    If someone adds a new transfer type and forgets to write the second
    ledger entry, this test fails.
    """

    def test_internal_transfer_leaves_ledger_clean(
        self, authenticated_client, test_account, db_session, test_user
    ):
        # Give the sender $500 with a bootstrap ledger CREDIT that matches.
        # In production this credit would be written by the top-up flow;
        # here we forge it directly so the invariant (balance == ledger_net)
        # holds from the start of the test.
        acc = (
            db_session.query(models.Account)
            .filter(models.Account.id == test_account.id)
            .first()
        )
        acc.balance = Decimal("500.00")

        bootstrap_tx = models.Transaction(
            user_id=test_user.id,
            account_id=acc.id,
            transaction_type="received",
            amount=Decimal("500.00"),
            currency="USD",
            recipient=test_user.email,
            status="completed",
            payment_method="paynow_topup",
        )
        db_session.add(bootstrap_tx)
        db_session.flush()
        db_session.add(
            models.LedgerEntry(
                transaction_id=bootstrap_tx.id,
                account_id=acc.id,
                amount=Decimal("500.00"),
                direction="credit",
                balance_after=Decimal("500.00"),
            )
        )
        db_session.commit()

        # Create a Zippie recipient so the internal-transfer path fires
        recipient = models.User(
            email="e2e-recipient@example.com",
            phone="+263700000555",
            full_name="E2E",
            hashed_password=get_password_hash("x"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(recipient)
        db_session.commit()

        # Drive three transfers via the real API endpoint
        for amount in (25, 50, 75):
            response = authenticated_client.post(
                "/api/v1/payments/transactions",
                json={
                    "account_id": test_account.id,
                    "transaction_type": "sent",
                    "amount": amount,
                    "currency": "USD",
                    "recipient": "e2e-recipient@example.com",
                    "description": f"E2E transfer ${amount}",
                },
            )
            assert response.status_code == 200, response.text
            assert response.json()["status"] == "completed"

        # Balances should be sender: 500 - 150 = 350, recipient: 150
        db_session.expire_all()
        sender_acc = (
            db_session.query(models.Account)
            .filter(models.Account.id == test_account.id)
            .first()
        )
        recipient_acc = (
            db_session.query(models.Account)
            .filter(models.Account.user_id == recipient.id)
            .first()
        )
        assert sender_acc.balance == Decimal("350.00")
        assert recipient_acc.balance == Decimal("150.00")

        # And reconciliation must be clean — balance == ledger_net for every
        # account, every internal tx has balanced DR/CR, global drift = 0.
        report = run_reconciliation(db_session)
        assert report.invariant_ok, (
            f"Reconciliation failed after E2E transfers. "
            f"account_violations={report.account_violations} "
            f"unbalanced_internal={report.unbalanced_internal} "
            f"global_drift={report.global_drift}"
        )
        assert report.global_drift == Decimal(0)
        assert report.total_balance == Decimal("500.00")  # 350 + 150
        # 1 bootstrap credit + 3 internal transfers × 2 entries each = 7
        assert report.ledger_entry_count == 7
        # 500 bootstrap credit + 150 sum of internal credits
        assert report.ledger_credits_total == Decimal("650.00")
        assert report.ledger_debits_total == Decimal("150.00")


@pytest.mark.integration
class TestAdminGate:
    """Admin endpoint authorization."""

    def test_reconciliation_requires_admin_allowlist(
        self, authenticated_client
    ):
        """Default empty ADMIN_EMAILS → everyone is denied (fail-closed)."""
        response = authenticated_client.get("/api/v1/admin/reconciliation")
        assert response.status_code == 403

    def test_reconciliation_rejects_non_admin_even_when_allowlist_set(
        self, authenticated_client, monkeypatch
    ):
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS",
            "someone-else@example.com",
        )
        response = authenticated_client.get("/api/v1/admin/reconciliation")
        assert response.status_code == 403

    def test_reconciliation_allows_admin_from_allowlist(
        self, authenticated_client, test_user, monkeypatch
    ):
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS",
            test_user.email,
        )
        response = authenticated_client.get("/api/v1/admin/reconciliation")
        assert response.status_code == 200
        body = response.json()
        assert body["invariant_ok"] is True
        assert "timestamp" in body
        assert "per_currency" in body

    def test_ledger_health_summary_gated_same_way(
        self, authenticated_client, test_user, monkeypatch
    ):
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS",
            test_user.email,
        )
        response = authenticated_client.get("/api/v1/admin/health/ledger")
        assert response.status_code == 200
        assert response.json()["invariant_ok"] is True


@pytest.mark.unit
class TestPaynowReferenceParsing:
    """The reference format is ZIPPIE-{uuid12}-{tx_id}, with legacy support."""

    def test_roundtrip_new_format(self):
        ref = _build_paynow_reference(42)
        assert ref.startswith("ZIPPIE-")
        assert ref.endswith("-42")
        # The uuid segment must be long enough to be unguessable
        middle = ref[len("ZIPPIE-"): -len("-42")]
        assert len(middle) >= 8
        assert _parse_tx_id_from_reference(ref) == 42

    def test_two_references_for_same_tx_differ(self):
        """The UUID segment must randomize between calls."""
        a = _build_paynow_reference(7)
        b = _build_paynow_reference(7)
        assert a != b

    def test_legacy_format_still_parses(self):
        assert _parse_tx_id_from_reference("ZIPPIE-123") == 123

    def test_invalid_input_returns_none(self):
        assert _parse_tx_id_from_reference("") is None
        assert _parse_tx_id_from_reference("not-a-zippie-ref") is None
        assert _parse_tx_id_from_reference("ZIPPIE-abc") is None
        assert _parse_tx_id_from_reference(None) is None
