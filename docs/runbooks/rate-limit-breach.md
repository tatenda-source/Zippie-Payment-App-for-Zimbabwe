# Rate Limit Breach

## Symptom

One or more of:
- Users reporting `429 Too Many Requests` from the app.
- Sentry spike on `slowapi` rate-limit exceeded errors.
- Worker memory growing unbounded (slowapi uses in-memory per-worker storage — see `backend/app/core/rate_limit.py`).
- Sustained 429 rate on a specific endpoint: `/api/v1/payments/transactions` (30/min), `/api/v1/payments/paynow/webhook` (60/min), `/api/v1/admin/reconciliation` (10/min), `/api/v1/admin/health/ledger` (30/min).

## Severity

**SEV-2** by default. Escalates to SEV-1 if the rate-limited endpoint is the Paynow webhook and real payments are being rejected.

## Time-to-resolve target

30 minutes from page to mitigation.

## 1. Triage — attack or legitimate traffic? (first 5 minutes)

Check the 429 response distribution by source IP in the access log / Sentry:

```
# Render log / Railway log / whatever log aggregator we use
# Filter: status=429 last 30 minutes, group by remote_addr
```

- **Concentrated on 1–3 IPs, bursty, non-human pattern:** attack. Jump to section 3.
- **Distributed across many IPs, matches real users we know about:** legitimate traffic outgrew the limit. Jump to section 2.
- **All from a single IP that belongs to a partner or monitor (e.g. uptime probe hitting `/admin/health/ledger`):** misconfiguration. Whitelist or lower probe frequency.

Also query audit events for admin endpoints:

```sql
SELECT actor_user_id, event_type, COUNT(*)
FROM audit_events
WHERE source='admin' AND created_at > NOW() - INTERVAL '30 minutes'
GROUP BY actor_user_id, event_type ORDER BY 3 DESC;
```

## 2. Legitimate traffic exceeding limit

Limits live in `backend/app/core/rate_limit.py` (`limiter` instance) and are applied per-endpoint via `@limiter.limit("N/minute")` decorators in `payments.py` and `admin.py`.

Raising a limit requires a code change and redeploy (the limits are decorator arguments, not config). Steps:

1. Edit the `@limiter.limit(...)` decorator on the affected endpoint in `backend/app/api/v1/payments.py` or `admin.py`.
2. Commit with message `chore: raise rate limit on <endpoint> during incident <INC-ID>` so the change is attributable.
3. Deploy.
4. Confirm 429 rate drops.

**Do not raise the Paynow webhook limit (`60/minute`) without first confirming Paynow is not retrying us into a loop.** If Paynow is retrying because our handler is crashing, see [`paynow-webhook-failure.md`](paynow-webhook-failure.md) first — raising the limit would mask the real bug.

## 3. Attack traffic

If the 429s are from 1–3 IPs hitting a write endpoint repeatedly, the rate limit is working as intended — it is refusing the attacker. Two next steps:

1. **Block at the infra layer.** Add the offending IP(s) to the load-balancer / reverse-proxy / Cloudflare blocklist. This removes the request from ever reaching the worker, eliminates CPU and memory cost, and prevents slowapi's in-memory counter dict from growing.
2. **Preserve evidence.** Copy the log rows (IP, User-Agent, timestamps, targeted endpoints) to a `/tmp/incident-<ID>-blocked-ips.log` file for the post-mortem and, if needed, for a formal abuse report to the hosting provider.

Do not attempt to block at the application layer — slowapi's `key_func=get_remote_address` is already doing that, and the blocklist logic would need its own redeploy. Infra-level blocking is faster and stronger.

## 4. Memory exhaustion from slowapi storage

slowapi's default storage is in-memory per worker process. Under heavy attack or long uptime it can grow unbounded. Symptom: worker RSS trends upward and does not plateau.

**Mitigation (immediate):** restart the worker. This clears the in-memory counter dict. Under Render/Railway, trigger a redeploy or manual restart.

**Recovery (one-time, if not already done):** switch to Redis-backed storage:

```python
# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
```

This also fixes the multi-worker problem (in-memory storage is per-process, so limits are actually `N * workers` per minute globally — not what we want). Already called out in `backend/app/core/rate_limit.py` and in the file header comment.

## TODO — Redis-backed storage

This is the long-standing fix. File: `backend/app/core/rate_limit.py`. Required before we run more than 1 worker in production. Adds `REDIS_URL` hard dependency — the app should fail to start on missing Redis, not silently fall back to in-memory.

## Post-incident

- **Post-mortem:** required if attack traffic caused user-facing 429s on write endpoints. Optional for legitimate-traffic overflow (just raise the limit and move on).
- **Notify affected users** only if a meaningful cohort saw 429s on `POST /api/v1/payments/transactions` (they think the send failed; they may retry, over-send, or lose trust).
- **Action item:** if this incident was caused by in-memory storage growth, the Redis migration becomes P0 before the next deploy.
- **Alert calibration:** are we paging early enough? If the 429 rate hit 10% of requests before alerting, the alert threshold is too high.
