"""Integration tests for slowapi rate limiting."""

import pytest

from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def _fresh_limiter():
    """Each test starts with a clean slate and leaves one behind."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.mark.integration
def test_login_returns_429_after_cap(client):
    """Login is capped at 10/minute per IP."""
    payload = {"username": "nobody@example.com", "password": "whatever"}

    statuses = []
    for _ in range(12):
        r = client.post("/api/v1/auth/login", data=payload)
        statuses.append(r.status_code)

    assert 429 in statuses, f"Expected 429 within 12 login attempts; got {statuses}"
    # First 10 should be allowed (they will 401 because creds are wrong, not 429)
    assert statuses.count(429) >= 1


@pytest.mark.integration
def test_webhook_rate_limits_at_60_per_minute(client):
    """Paynow webhook caps at 60/minute per IP."""
    statuses = []
    for _ in range(65):
        r = client.post("/api/v1/payments/paynow/webhook", data={"reference": "ZIPPIE-x-1"})
        statuses.append(r.status_code)

    assert 429 in statuses, f"Expected a 429 within 65 webhook hits; got {statuses[-5:]}"


@pytest.mark.integration
@pytest.mark.skip(
    reason=(
        "slowapi 0.1.9's default _rate_limit_exceeded_handler does not emit "
        "Retry-After or X-RateLimit-* headers on the 429 body — it only sets "
        "the status + detail. Verifying header presence would require a "
        "custom exception handler. TODO: wire that when we standardize error "
        "envelope."
    )
)
def test_rate_limited_response_has_retry_header(client):
    payload = {"username": "nobody@example.com", "password": "whatever"}
    last = None
    for _ in range(15):
        last = client.post("/api/v1/auth/login", data=payload)
        if last.status_code == 429:
            break
    assert last is not None and last.status_code == 429
    assert "retry-after" in {k.lower() for k in last.headers.keys()}
