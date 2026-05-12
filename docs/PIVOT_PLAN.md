# Pivot Plan — Zippie → Paynow Connect

**Status:** Draft — awaiting approval before Phase 1 ships.
**Date:** 2026-05-12
**Author:** Engineering

---

## 1. Context

Zippie was built as a consumer P2P wallet with an internal float and a double-entry ledger; Paynow was used only at the on-ramp (top-up) and off-ramp (cash-out) edges. The float model bought sub-50ms internal P2P at the cost of MSB-style operational burden: trust-account custody, ledger reconciliation against Paynow settlement, and an RBZ position paper to defend the model.

We are pivoting to **Paynow Connect** — a white-label B2B SaaS that sits on top of Paynow rails (positioned analogously to Stripe Connect). The product no longer holds money. Every P2P transfer is a Paynow account-to-account push between the sender's and recipient's Paynow IDs.

## 2. Decisions locked

| # | Decision | Rationale |
|---|---|---|
| 1 | **Routing**: Paynow account-to-account push API. | No float held; rails do the movement. |
| 2 | **Product**: White-label / B2B SaaS for businesses (SACCOs, schools, merchants). Multi-tenant. | Higher contract value than consumer; aligns with Paynow's distribution. |
| 3 | **Ledger fate**: Keep `transactions` + `ledger_entries` as audit-only records. Drop balance authority. | Receipts, dispute resolution, tenant reporting — without taking on custody. |
| 4 | **Identity**: Paynow ID is the user's primary identity. Registration requires linking a Paynow ID. | Recipients are addressable on the rails by definition. |

## 3. What gets invalidated

- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — the "Float Model" thesis is dead. The whole "instant P2P internal ledger" argument doesn't apply.
- [docs/RBZ_POSITION_PAPER.md](RBZ_POSITION_PAPER.md) — no float means a different regulatory posture: we are now a **software vendor to a licensed PSP (Paynow)**, not an entity holding customer funds.
- Reconciliation service (`backend/app/services/reconciliation.py`) — there's nothing to reconcile against settlement because we never hold money.

These get rewritten in Phase 4, not deleted yet.

## 4. Phased plan

### Phase 1 — Backend data model & transaction flow

**Goal:** Backend speaks Paynow-ID + tenant. Old float code paths removed. Frontend may temporarily break — that's fine, Phase 2 fixes it.

**Schema changes** (one Alembic migration):

```sql
-- new
CREATE TABLE tenants (
  id            SERIAL PRIMARY KEY,
  slug          VARCHAR UNIQUE NOT NULL,
  name          VARCHAR NOT NULL,
  paynow_integration_id   VARCHAR,         -- per-tenant Paynow merchant creds
  paynow_integration_key  VARCHAR,         -- encrypted at rest (Phase 1 stores plain; Phase 3 wraps with KMS)
  brand_config  JSONB,                     -- logo_url, primary_color, app_name, etc.
  is_active     BOOLEAN DEFAULT TRUE,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ
);

-- users gains paynow_id + tenant_id
ALTER TABLE users ADD COLUMN paynow_id VARCHAR;
ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE UNIQUE INDEX uq_users_tenant_paynow_id ON users (tenant_id, paynow_id) WHERE paynow_id IS NOT NULL;

-- transactions gains rails fields
ALTER TABLE transactions ADD COLUMN sender_paynow_id    VARCHAR;
ALTER TABLE transactions ADD COLUMN recipient_paynow_id VARCHAR;
ALTER TABLE transactions ADD COLUMN paynow_transfer_ref VARCHAR;  -- rails reference returned by A2A push
ALTER TABLE transactions ADD COLUMN tenant_id           INTEGER REFERENCES tenants(id);
CREATE INDEX ix_transactions_paynow_transfer_ref ON transactions (paynow_transfer_ref);
```

`accounts` and `accounts.balance` are left in place for Phase 1 (used by audit ledger writes). They get removed in Phase 4 after we're sure no read-path depends on them.

**Service layer — pluggable rails adapter:**

```python
# backend/app/services/paynow_rails.py
class PaynowRailsAdapter(Protocol):
    def transfer_p2p(self, *, sender_paynow_id, recipient_paynow_id,
                     amount, reference, tenant) -> dict: ...
    def verify_paynow_id(self, paynow_id) -> dict: ...   # {valid, display_name?}
    def lookup_paynow_id(self, paynow_id) -> dict: ...   # {display_name}
    def get_balance(self, paynow_id) -> dict: ...
```

Three implementations ship in Phase 1:

| Adapter | Status | Use |
|---|---|---|
| `MockAdapter` | Default in tests | Deterministic responses; no network. |
| `MerchantCollectPayoutAdapter` | **Default in dev + prod** | Workaround using today's Paynow merchant SDK. Each P2P = `initiate_mobile_checkout` from sender → `payout` to recipient. USSD prompt per send (10s–2min UX). **No float held — regulatory goal met.** |
| `A2APushAdapter` | Stub (`NotImplementedError`) | Placeholder for real Paynow account-to-account push API. Wired in when API details land. |

Adapter selection via env var: `PAYNOW_RAILS_ADAPTER=merchant_collect_payout` (default) | `a2a_push` | `mock`. The signature accepts a `tenant` arg so a single backend routes through different Paynow merchant credentials per tenant.

**Recipient discovery — DB-first, rails-second:**

`GET /resolve-recipient?paynow_id=…` order:
1. Look up local user by `paynow_id` → if found, return display name + tenant context.
2. Call adapter's `verify_paynow_id(paynow_id)` → if rails confirm, return what they give us.
3. Fall back to "ID is well-formed, recipient unknown" — the actual `transfer_p2p` will fail loud if rails reject.

DB-first matches how Venmo / Cash App work (send to known users), so this isn't a hack — it's the right model.

**Paynow ID validation — lenient now, tighten later:**

```python
PAYNOW_ID_REGEX = r"^[A-Za-z0-9._-]{4,32}$"  # permissive; tighten once format confirmed
```

Tightening is a 5-minute follow-up migration (add CHECK constraint) when the real format is known.

**API surface changes:**

| Endpoint | Change |
|---|---|
| `POST /auth/register` | Requires `paynow_id`. Validates format (regex / Paynow lookup). |
| `POST /transactions` (sent) | Calls `transfer_p2p()` instead of internal debit/credit. Writes audit-only `LedgerEntry` after success. No `accounts.balance` mutation. |
| `POST /transactions` (request) | Unchanged. |
| `GET /resolve-recipient?paynow_id=…` | Resolves a Paynow ID → display name. Querystring renamed from `query` → `paynow_id`. |
| `GET /balance` | Deprecated. Returns `410 Gone` with `Link` header to `GET /paynow/balance`. |
| `GET /paynow/balance` | New. Proxies Paynow's balance query for the current user's Paynow ID. |
| `POST /paynow/topup/initiate` | **Removed.** Returns `410 Gone`. |
| `POST /paynow/initiate` | Removed for "sent" txns (no longer two-step). Kept only for "request" → manual settlement flow if we keep that. |
| `POST /paynow/webhook` | Kept. Now handles A2A push completion / failure callbacks. |
| `GET /paynow/status/{id}` | Kept. Polls A2A push status. |

**Tests rewritten:**
- `tests/integration/test_concurrency.py` — no internal ledger to test concurrent debit/credit on. New test: 50 parallel A2A pushes with a mocked `transfer_p2p` verifies idempotency on `paynow_transfer_ref` UNIQUE.
- `tests/api/test_transactions.py` — assert `transfer_p2p` called with correct args; assert audit ledger entry written; assert no balance mutation.
- New `tests/api/test_tenants.py` — tenant-scoped Paynow credential resolution.

**Migration safety:**
- All schema changes are additive (no DROP COLUMN in Phase 1).
- Existing wallet balances are not touched. If we ever want to refund existing float users, we have the data.
- `paynow_id` is nullable in the schema and enforced at the API layer — this lets us seed test data and run the migration before all users have linked.

### Phase 2 — Frontend

- **Register page:** add Paynow ID input + "Verify" button (calls a backend endpoint that hits Paynow lookup).
- **SendMoney page:** input becomes Paynow ID, no balance pill, copy reads "Sending from your Paynow account".
- **TransactionHistory:** show `paynow_transfer_ref` as the receipt anchor.
- **TopUp page:** delete.
- **Tenant theming:** `AuthContext` loads `brand_config` and injects CSS vars at the layout root.

### Phase 3 — Multi-tenancy admin

- Tenant signup (self-serve or admin-provisioned — decide later).
- Per-tenant admin console: brand config, user list, transaction log, Paynow credential management.
- Billing hooks (Stripe or Paynow-side subscription — decide later).
- KMS-wrapped tenant credential storage.

### Phase 4 — Documentation & cleanup

- Rewrite [ARCHITECTURE.md](ARCHITECTURE.md) for Paynow-rails-per-transfer.
- Rewrite [RBZ_POSITION_PAPER.md](RBZ_POSITION_PAPER.md) for software-vendor posture.
- Delete `backend/app/services/reconciliation.py`.
- Drop `accounts.balance` column. Decide whether to drop the `accounts` table entirely or repurpose as "linked Paynow IDs" for users with multiple Paynow accounts.

## 5. Rename scope (Zippie → Paynow Connect)

Bundled into Phase 1 to avoid a two-step migration. Mechanical changes:

- `package.json` `name`, `pyproject.toml` `[project].name`
- `README.md` title + body
- `backend/app/api/v1/payments.py` reference prefix: new transactions use `PNC-{uuid12}-{id}`; the parser at [`_parse_tx_id_from_reference`](../backend/app/api/v1/payments.py#L457) keeps accepting `ZIPPIE-` prefix for in-flight transactions issued before the cutover.
- Database default name `zippie_db` → `paynow_connect_db` (env-driven, so existing deployments stay on `zippie_db` unless they choose to migrate).
- Audit event sources, log lines, docstrings.
- Frontend `index.html` title, `App.tsx` brand string — minimal touch in Phase 1; full UI rebrand in Phase 2.

## 6. Resolved blockers (Phase 1 is unblocked)

| Old blocker | Resolution |
|---|---|
| Paynow A2A push API specifics | Pluggable adapter pattern. Ship with `MerchantCollectPayoutAdapter` as default; swap to `A2APushAdapter` when API lands (one env var change). |
| Paynow ID format | Lenient regex now, tighten via follow-up migration when format confirmed. |
| Recipient discovery | DB-first lookup; adapter as fallback. Matches Venmo/Cash App pattern. |

## 7. Remaining open questions (non-blocking)

1. **Tenant onboarding model.** Self-serve vs. sales-led. Affects Phase 3 only.
2. **Existing float users.** Any live balances in prod? Phase 1 is additive — doesn't touch existing `accounts.balance` — so it's safe to ship without knowing. Phase 4 cleanup is gated on this answer.

## 8. Risk register

| Risk | Mitigation |
|---|---|
| Paynow A2A push API doesn't exist or doesn't behave as expected. | Service abstraction means we can swap implementation. Worst case: fall back to merchant-collect + payout per transfer (slower, still no float). |
| Existing users have float balance we can't honor. | Phase 1 is additive — we don't touch balances. Phase 4 cleanup is gated on confirming no live balances exist. |
| Per-transfer latency degrades UX vs. current sub-50ms ledger writes. | Acceptable per pivot decision. Frontend should add optimistic UI + clear "pending" state. |
| Tenant credential leak (per-tenant Paynow keys in DB). | Phase 1 stores plain; Phase 3 wraps with KMS before any tenant is onboarded. Document this in the migration. |

## 9. Sign-off

Phase 1 ships once this plan is approved. Adapter pattern absorbs the API/format/discovery unknowns; float-balance question is non-blocking because Phase 1 is additive.
