# Runbooks Index

Operator documentation for Zippie production incidents. Every runbook is self-contained: symptom, severity, TTR, copy-pasteable commands, post-incident steps.

Process docs (not runbooks) live one level up:
- [`../incident-response.md`](../incident-response.md) — SEV levels, paging, comms, war-room.
- [`../post-mortem-template.md`](../post-mortem-template.md) — fill-in-the-blank post-mortem.

Background (read once, not at 3am):
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — float model, ledger invariants, kill-vectors.
- [`../VC_ANALYSIS.md`](../VC_ANALYSIS.md) — risk categories, regulatory posture.

## SEV-1 (money at risk, full page)

- [`ledger-drift.md`](ledger-drift.md) — `/admin/reconciliation` returns `invariant_ok=false` or `global_drift != 0`. Freeze, diagnose, adjust, post-mortem.
- [`paynow-freeze.md`](paynow-freeze.md) — Paynow merchant account frozen or under review. Internal P2P survives; on/off-ramps stop.
- [`database-outage.md`](database-outage.md) — Postgres unavailable; `/health` returns `database=disconnected`; every write 500s.

## SEV-2 (degraded service, page business hours or if user-impacting)

- [`paynow-webhook-failure.md`](paynow-webhook-failure.md) — webhooks stop arriving or stop being processed; top-ups stuck pending.
- [`rate-limit-breach.md`](rate-limit-breach.md) — 429 spike or slowapi in-memory storage exhaustion.

## SEV-3 (minor / cosmetic, handle next business day)

None yet. Add here as they emerge: Sentry noise, log-format regressions, single-account drift inside tolerance, etc.

## When a runbook is wrong

If the runbook didn't match reality during an incident, fix it in the post-mortem action items. Stale runbooks are worse than no runbooks.
