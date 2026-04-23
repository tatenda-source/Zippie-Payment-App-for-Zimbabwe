"""
Config-driven feature flags.

Kill-switches readable at request time (not import time) so tests and
ops can toggle them without a redeploy. Flag names are snake_case strings
(e.g. "topup") and map to uppercase FEATURE_* fields on Settings.
"""

from typing import Callable

from fastapi import HTTPException, status

from app.core.config import settings


def is_enabled(flag_name: str) -> bool:
    """Return True if the named feature flag is enabled.

    Reads from `settings` at call time so monkeypatch in tests works.
    Unknown flags are treated as disabled (fail-closed).
    """
    attr = f"FEATURE_{flag_name.upper()}"
    return bool(getattr(settings, attr, False))


def require_feature(flag_name: str) -> Callable[[], None]:
    """FastAPI dependency factory that 503s when the flag is off."""

    def _dep() -> None:
        if not is_enabled(flag_name):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Feature '{flag_name}' is disabled",
            )

    return _dep
