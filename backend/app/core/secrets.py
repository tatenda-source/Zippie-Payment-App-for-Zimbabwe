"""Secrets provider abstraction.

Secrets come from one of two sources at runtime:
  - env: os.environ (or .env file via python-dotenv). Default. Used for
    local dev and anywhere config is injected at deploy time.
  - aws: AWS Secrets Manager. Resolved at startup; values cached in-memory
    for the process lifetime.

Switch via SECRETS_PROVIDER env var. Fail-closed: unknown provider raises at
import time so a misconfigured deploy dies immediately, not silently.

Why a layer at all on a pilot-stage app: rotating PAYNOW_INTEGRATION_KEY in
production should not require a code deploy. This module is the seam where
that rotation eventually happens.

Note: pydantic-settings (app.core.config) still reads os.environ directly.
This provider is for code paths that need to resolve a secret outside the
pydantic pipeline (e.g. re-reading a rotated Paynow key mid-run). Future
work: route Settings through this provider.
"""

import abc
import os
from typing import Dict, Optional


class SecretsProvider(abc.ABC):
    @abc.abstractmethod
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        ...


class LocalEnvProvider(SecretsProvider):
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(name, default)


class AwsSecretsManagerProvider(SecretsProvider):
    """Resolves secrets from AWS Secrets Manager under a prefixed key.

    Key layout: {prefix}/{environment}/{name}, e.g. zippie/production/PAYNOW_INTEGRATION_KEY.
    Values cached in-memory for the process lifetime; restart the app to pick
    up rotated values.
    """

    def __init__(
        self,
        region: Optional[str] = None,
        prefix: str = "zippie",
        environment: Optional[str] = None,
    ):
        try:
            import boto3  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "boto3 is required for SECRETS_PROVIDER=aws. "
                "Install with: pip install boto3"
            ) from e

        self._region = region or os.environ.get("AWS_REGION", "af-south-1")
        self._prefix = prefix
        self._environment = environment or os.environ.get("ENVIRONMENT", "development")
        self._client = boto3.client("secretsmanager", region_name=self._region)
        self._cache: Dict[str, Optional[str]] = {}

    def _key(self, name: str) -> str:
        return f"{self._prefix}/{self._environment}/{name}"

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        if name in self._cache:
            return self._cache[name] if self._cache[name] is not None else default

        try:
            response = self._client.get_secret_value(SecretId=self._key(name))
            value = response.get("SecretString")
        except Exception:
            value = None

        self._cache[name] = value
        return value if value is not None else default


_provider_singleton: Optional[SecretsProvider] = None


def get_provider() -> SecretsProvider:
    """Return the configured secrets provider singleton.

    Reads SECRETS_PROVIDER env var. Valid values: "env" (default), "aws".
    Unknown values raise RuntimeError.
    """
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton

    kind = os.environ.get("SECRETS_PROVIDER", "env").lower()
    if kind == "env":
        _provider_singleton = LocalEnvProvider()
    elif kind == "aws":
        prefix = os.environ.get("AWS_SECRETS_PREFIX", "zippie")
        _provider_singleton = AwsSecretsManagerProvider(prefix=prefix)
    else:
        raise RuntimeError(
            f"Unknown SECRETS_PROVIDER={kind!r}. Valid values: 'env', 'aws'."
        )
    return _provider_singleton


class _LazySingleton:
    def __getattr__(self, item):
        return getattr(get_provider(), item)


secrets_provider: SecretsProvider = _LazySingleton()  # type: ignore[assignment]
