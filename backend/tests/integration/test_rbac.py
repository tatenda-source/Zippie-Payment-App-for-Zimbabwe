"""RBAC integration tests.

Covers require_role() exact-match semantics and require_any_admin() bridge
(role=='admin' OR email in ADMIN_EMAILS). Also confirms the existing admin
endpoints still work via the email allowlist path after we reimplemented
require_admin on top of require_any_admin.
"""

import pytest
from faker import Faker
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import get_current_user
from app.core.rbac import VALID_ROLES, require_any_admin, require_role
from app.core.security import get_password_hash
from app.db import models
from app.db.database import get_db

fake = Faker()


def _make_user(db_session, *, role="user", email=None):
    user = models.User(
        email=email or fake.email(),
        phone=fake.phone_number(),
        full_name=fake.name(),
        hashed_password=get_password_hash("TestPassword123"),
        is_active=True,
        is_verified=True,
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPassword123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _rbac_app(db_session):
    """Tiny FastAPI app with endpoints guarded by rbac dependencies,
    sharing the test DB session and get_current_user from the real app."""
    app = FastAPI()

    @app.get("/admin-only")
    def admin_only(u: models.User = Depends(require_role("admin"))):
        return {"email": u.email, "role": u.role}

    @app.get("/admin-or-ops")
    def admin_or_ops(u: models.User = Depends(require_role("admin", "ops"))):
        return {"email": u.email, "role": u.role}

    @app.get("/any-admin")
    def any_admin(u: models.User = Depends(require_any_admin)):
        return {"email": u.email, "role": u.role}

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.mark.integration
class TestValidRoles:
    def test_canonical_set(self):
        assert VALID_ROLES == frozenset(
            {"user", "admin", "support", "ops", "finance"}
        )

    def test_require_role_rejects_unknown_role_at_definition(self):
        with pytest.raises(ValueError):
            require_role("superuser")


@pytest.mark.integration
class TestRequireRole:
    def test_403_when_role_mismatch(self, client, db_session):
        user = _make_user(db_session, role="user")
        token = _login(client, user.email)

        with TestClient(_rbac_app(db_session)) as tc:
            r = tc.get(
                "/admin-only", headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 403

    def test_200_when_role_matches(self, client, db_session):
        user = _make_user(db_session, role="admin")
        token = _login(client, user.email)

        with TestClient(_rbac_app(db_session)) as tc:
            r = tc.get(
                "/admin-only", headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_200_for_any_listed_role(self, client, db_session):
        user = _make_user(db_session, role="ops")
        token = _login(client, user.email)

        with TestClient(_rbac_app(db_session)) as tc:
            r = tc.get(
                "/admin-or-ops",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200
        assert r.json()["role"] == "ops"

    def test_no_implicit_hierarchy_admin_not_granted_by_ops_endpoint_only(
        self, client, db_session
    ):
        """require_role("ops") must NOT grant admin. Exact-match semantics."""
        user = _make_user(db_session, role="admin")
        token = _login(client, user.email)

        app = FastAPI()

        @app.get("/ops-only")
        def ops_only(u: models.User = Depends(require_role("ops"))):
            return {"ok": True}

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as tc:
            r = tc.get(
                "/ops-only", headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 403


@pytest.mark.integration
class TestRequireAnyAdmin:
    def test_allowlist_bootstrap_path(
        self, client, db_session, monkeypatch
    ):
        """Email in ADMIN_EMAILS grants admin even when role=='user'."""
        user = _make_user(db_session, role="user")
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS", user.email
        )
        token = _login(client, user.email)

        with TestClient(_rbac_app(db_session)) as tc:
            r = tc.get(
                "/any-admin", headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 200

    def test_role_path(self, client, db_session, monkeypatch):
        """role=='admin' grants admin even when email NOT in allowlist."""
        user = _make_user(db_session, role="admin")
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS",
            "someone-else@example.com",
        )
        token = _login(client, user.email)

        with TestClient(_rbac_app(db_session)) as tc:
            r = tc.get(
                "/any-admin", headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 200

    def test_403_when_neither(self, client, db_session, monkeypatch):
        user = _make_user(db_session, role="user")
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS",
            "someone-else@example.com",
        )
        token = _login(client, user.email)

        with TestClient(_rbac_app(db_session)) as tc:
            r = tc.get(
                "/any-admin", headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 403


@pytest.mark.integration
class TestExistingAdminEndpointsStillWork:
    """After reimplementing require_admin on top of require_any_admin, the
    email-allowlist bootstrap path must continue to work for the existing
    /reconciliation and /health/ledger endpoints — even when user.role=='user'.
    """

    def test_reconciliation_allowlist_path_with_user_role(
        self, authenticated_client, test_user, monkeypatch
    ):
        assert test_user.role == "user"
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS", test_user.email
        )
        r = authenticated_client.get("/api/v1/admin/reconciliation")
        assert r.status_code == 200

    def test_ledger_health_allowlist_path_with_user_role(
        self, authenticated_client, test_user, monkeypatch
    ):
        assert test_user.role == "user"
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS", test_user.email
        )
        r = authenticated_client.get("/api/v1/admin/health/ledger")
        assert r.status_code == 200

    def test_reconciliation_denied_when_neither_allowlist_nor_role(
        self, authenticated_client, test_user, monkeypatch
    ):
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_EMAILS", ""
        )
        r = authenticated_client.get("/api/v1/admin/reconciliation")
        assert r.status_code == 403
