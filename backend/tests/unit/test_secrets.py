"""Unit tests for the secrets provider abstraction."""

import builtins
import importlib

import pytest


@pytest.fixture
def fresh_secrets(monkeypatch):
    """Reload app.core.secrets so the module-level singleton resets per test."""
    import app.core.secrets as secrets_mod

    importlib.reload(secrets_mod)
    monkeypatch.setattr(secrets_mod, "_provider_singleton", None)
    return secrets_mod


@pytest.mark.unit
class TestLocalEnvProvider:
    def test_returns_value_from_environ(self, fresh_secrets, monkeypatch):
        monkeypatch.setenv("ZIPPIE_TEST_SECRET", "the-value")
        provider = fresh_secrets.LocalEnvProvider()
        assert provider.get("ZIPPIE_TEST_SECRET") == "the-value"

    def test_falls_back_to_default_when_missing(self, fresh_secrets, monkeypatch):
        monkeypatch.delenv("ZIPPIE_MISSING_SECRET", raising=False)
        provider = fresh_secrets.LocalEnvProvider()
        assert provider.get("ZIPPIE_MISSING_SECRET", "fallback") == "fallback"
        assert provider.get("ZIPPIE_MISSING_SECRET") is None


@pytest.mark.unit
class TestGetProvider:
    def test_env_is_default(self, fresh_secrets, monkeypatch):
        monkeypatch.delenv("SECRETS_PROVIDER", raising=False)
        provider = fresh_secrets.get_provider()
        assert isinstance(provider, fresh_secrets.LocalEnvProvider)

    def test_env_explicit(self, fresh_secrets, monkeypatch):
        monkeypatch.setenv("SECRETS_PROVIDER", "env")
        provider = fresh_secrets.get_provider()
        assert isinstance(provider, fresh_secrets.LocalEnvProvider)

    def test_aws_without_boto3_raises(self, fresh_secrets, monkeypatch):
        monkeypatch.setenv("SECRETS_PROVIDER", "aws")
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "boto3":
                raise ImportError("No module named 'boto3'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(RuntimeError, match="boto3"):
            fresh_secrets.get_provider()

    def test_unknown_provider_raises(self, fresh_secrets, monkeypatch):
        monkeypatch.setenv("SECRETS_PROVIDER", "vault")
        with pytest.raises(RuntimeError, match="Unknown SECRETS_PROVIDER"):
            fresh_secrets.get_provider()
