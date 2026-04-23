# Database Outage

## Symptom

One or more of:
- `GET /health` returns `{"status":"unhealthy","database":"disconnected"}` (implemented in `backend/app/main.py`).
- Every write endpoint (`POST /api/v1/payments/transactions`, `/auth/register`, `/paynow/*`) returns 500 or 503.
- Sentry spike on `OperationalError`, `could not connect to server`, `psycopg2.OperationalError`, or connection-pool exhaustion.
- Uptime monitor red on `/health`.
- Hosting provider dashboard (Render / Railway / RDS / etc.) shows Postgres instance in a non-running state.

## Severity

**SEV-1.** Full outage on all write paths. Reads partially degraded.

## Time-to-resolve target

20 minutes from page to resolution or graceful degradation.

## What happens to user data

Nothing. The DB is either up or down — there is no half-written state because every write path commits atomically. FastAPI's error handlers convert `OperationalError` into 5xx responses before any partial state can leak. Users see errors; they do not see corrupted balances.

This is by design — no action is needed to "protect" user data during the outage. Protect the reconciliation instead: do not write compensating records by hand while the DB is flaky; wait for it to be solidly back.

## 1. Confirm it's the DB, not us (first 2 minutes)

```bash
# App-level health
curl -s https://<api-host>/health
# Expect during outage: 503 {"status":"unhealthy","database":"disconnected","error":"..."}

# Direct psql from a trusted host / bastion
psql "$DATABASE_URL" -c "SELECT 1;"
# If this also fails, the DB itself is down. If it succeeds, the app-side connection pool is the issue.
```

Also check the hosting-provider status page (Render status, Railway status, AWS RDS console).

## 2. Triage by category

### A. DB instance is down (psql fails too)

- Hosting-provider outage: check their status page. If confirmed, wait — our job is comms, not repair.
- DB instance crashed / OOM: restart via provider dashboard. Expect 2–5 minute recovery with WAL replay.
- Disk full: provider dashboard, upgrade storage tier. Irrecoverable without provider intervention if autoscaling is off.

### B. App cannot reach DB (psql works from bastion, app 503s)

- Network / VPC / firewall: check the provider's network panel. Did something change (security group, private network peer)?
- DNS: `nslookup <db-host>`. If the host resolves on the bastion but not inside the app network, that's the issue.
- Credentials: `DATABASE_URL` env var is correct? Recently rotated?
- Connection pool exhausted: restart the workers (Render / Railway redeploy). Long-term: investigate slow queries holding connections.

### C. App-side pool misconfiguration

- SQLAlchemy pool size vs DB `max_connections`: if we added workers and did not scale the DB, the pool might be hitting `max_connections`.
- Check Postgres logs for `FATAL: remaining connection slots are reserved`.

## 3. Mitigation

There is no "keep accepting writes locally and sync later" strategy for a payments system. Do not attempt one. Every write must hit the authoritative ledger or not happen.

The app's FastAPI error handlers already turn DB failures into 5xx for the client. This is the correct behaviour — "we're down, try again" beats "we accepted your transfer but you will never see it again."

User-visible comms:

**In-app banner:**
> Zippie is temporarily unavailable. Your wallet balance is safe. We'll be back shortly.

**Status page:** mark operational → degraded or outage, depending on scope.

## 4. Hosting-specific recovery

(Fill in actual hosting details once confirmed. Template:)

### If on Render

- Dashboard → Postgres instance → Restart, or promote a replica.
- Logs: Dashboard → Postgres → Logs tab.
- Connection: check the external `DATABASE_URL` in the app env tab matches the one in the Postgres service.

### If on Railway

- Dashboard → Postgres plugin → Restart.
- Logs: click the Postgres service → Deployments → Logs.

### If self-hosted

- SSH to the box, `systemctl status postgresql`, `journalctl -u postgresql -n 200`.
- Disk: `df -h`.
- Replica failover: if a replica is configured, promote it and repoint `DATABASE_URL`.

## 5. Verify recovery

Once the DB is back:

```bash
curl -s https://<api-host>/health | jq
# Expect: {"status":"healthy","database":"connected",...}

# Smoke test the hot path (one internal transfer between two test accounts)
curl -s -X POST https://<api-host>/api/v1/payments/transactions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"transaction_type":"sent","amount":1,"recipient":"test-other@example.com","currency":"USD","account_id":<id>}'

# Ledger integrity check — nothing weird happened during the outage
curl -s https://<api-host>/api/v1/admin/reconciliation -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.invariant_ok, .global_drift'
# Expect: true, "0"
```

Announce recovery in the incident channel and to users (banner down, status page green).

## Post-incident

- **Post-mortem: required.** Capture RTO (time from first 503 to `/health` green) and RPO (any committed transactions lost — should be zero). Within 72h.
- **If RTO > SLA:** the post-mortem's top action item is DB redundancy — read replicas with automatic failover, or a managed HA tier. The current single-instance setup is acceptable for pilot but not for scale.
- **Check the audit trail** — did `audit_events` capture the failed window? Were any transactions in a weird interim state? (There should not be. Verify anyway.)
- **Review connection-pool sizing** if the cause was pool exhaustion.
- **Update this runbook** with the actual hosting-provider playbook once we confirm the first live outage on this stack.
