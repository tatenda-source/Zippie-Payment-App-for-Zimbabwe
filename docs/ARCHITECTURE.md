# Zippie Architecture — Paynow Gateway + Instant P2P

## The Problem

Paynow is a merchant-to-customer gateway. Every transaction flows through mobile money rails
(EcoCash, OneMoney) which require USSD prompts and user approval (10s–2min).

You cannot build **instant P2P** by calling Paynow on every transfer. A "Venmo for Zimbabwe"
needs sub-second transfers, and rails are too slow.

## The Insight

**Don't touch the rails on every transfer.** Use Paynow only at the edges:

- **ON-RAMP** (top-up): user pulls money from EcoCash → Zippie wallet
- **OFF-RAMP** (cash out): user pushes money from Zippie wallet → EcoCash
- **P2P**: internal ledger update only. Never touches Paynow.

This is the **Float Model**. It's how Chipper Cash, PayPal, Venmo, Cash App, and M-Pesa all work.

---

## Architecture Diagram

```
 ┌─────────┐                                                           ┌─────────┐
 │ User A  │                                                           │ User B  │
 │  📱     │                                                           │  📱     │
 └────┬────┘                                                           └────┬────┘
      │                                                                     │
      │  SEND $20 (instant, <50ms)                       RECEIVE $20        │
      │                                                                     │
      ▼                                                                     ▼
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │                           ZIPPIE PLATFORM                                     │
 │                                                                               │
 │  ┌──────────────┐   ┌────────────────────────┐   ┌────────────────────────┐   │
 │  │  React App   │──▶│   FastAPI Backend      │──▶│   PostgreSQL           │   │
 │  │  (mobile)    │   │   Auth / Payments      │   │   Users, Wallets,      │   │
 │  │              │   │                        │   │   Transactions         │   │
 │  └──────────────┘   └───────────┬────────────┘   └────────────────────────┘   │
 │                                 │                                             │
 │                                 ▼                                             │
 │                 ┌────────────────────────────────┐                            │
 │                 │    ★  INTERNAL LEDGER  ★       │                            │
 │                 │                                │                            │
 │                 │  • Wallets (USD, ZWL per user) │  ← instant P2P lives here  │
 │                 │  • Double-entry journal        │                            │
 │                 │  • Atomic debit/credit         │                            │
 │                 │  • No external calls           │                            │
 │                 └────────────────┬───────────────┘                            │
 │                                  │                                            │
 │                                  │ only at edges                              │
 │                                  ▼                                            │
 │                 ┌────────────────────────────────┐                            │
 │                 │   Paynow Integration Layer     │                            │
 │                 │                                │                            │
 │                 │  ┌────────────┐ ┌────────────┐ │                            │
 │                 │  │  Top-up    │ │  Withdraw  │ │                            │
 │                 │  │ (on-ramp)  │ │ (off-ramp) │ │                            │
 │                 │  └──────┬─────┘ └──────┬─────┘ │                            │
 │                 │         │              │       │                            │
 │                 │  ┌──────┴──────────────┴─────┐ │                            │
 │                 │  │   Webhook handler +       │ │                            │
 │                 │  │   status poller           │ │                            │
 │                 │  └───────────────────────────┘ │                            │
 │                 └────────────────┬───────────────┘                            │
 └──────────────────────────────────┼────────────────────────────────────────────┘
                                    │ HTTPS (Merch API)
                                    │
                                    ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                         PAYNOW GATEWAY                                       │
 │                                                                              │
 │    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
 │    │   Merch API  │    │   Payout     │    │   Webhooks   │                  │
 │    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
 │           └──────────┬────────┴────────────┬──────┘                          │
 │                      ▼                     │                                 │
 │              ┌───────────────┐              │                                │
 │              │ Hyperswitch   │ ← routing    │                                │
 │              │ Vault / Sift  │ ← fraud      │                                │
 │              └───────┬───────┘              │                                │
 │                      │                      │                                │
 │                      ▼                      │                                │
 │              ┌───────────────┐              │                                │
 │              │     RAILS     │              │                                │
 │              │  • EcoCash    │              │                                │
 │              │  • OneMoney   │              │                                │
 │              │  • Omari      │              │                                │
 │              │  • InnBucks   │              │                                │
 │              │  • ZimSwitch  │              │                                │
 │              └───────┬───────┘              │                                │
 │                      │                      │                                │
 │                      ▼                      │                                │
 │              ┌───────────────┐              │                                │
 │              │  Fin Core     │              │                                │
 │              │  Ledger/Recon │              │                                │
 │              │  Settlement   │              │                                │
 │              └───────────────┘              │                                │
 └──────────────────────┬───────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │  Mobile Money     │
              │  Provider         │  ← Only touched for on-ramp/off-ramp
              │  (cash in/out)    │
              └───────────────────┘
```

---

## The Three Flows

### Flow 1: TOP-UP (On-Ramp)

```
 User A                Zippie                    Paynow              EcoCash
   │                     │                          │                   │
   │  "Top up $50"       │                          │                   │
   ├────────────────────▶│                          │                   │
   │                     │  initiate_mobile_checkout│                   │
   │                     ├─────────────────────────▶│                   │
   │                     │                          │  USSD prompt      │
   │                     │                          ├──────────────────▶│
   │                     │                          │                   │
   │  "Enter PIN on *151#"                          │                   │
   │◀───────────────────────────────────────────────────────────────────┤
   │                     │                          │                   │
   │  [user enters PIN]                             │                   │
   ├───────────────────────────────────────────────────────────────────▶│
   │                     │                          │  confirmed        │
   │                     │                          │◀──────────────────┤
   │                     │   webhook: paid          │                   │
   │                     │◀─────────────────────────┤                   │
   │                     │                          │                   │
   │                     │  ★ credit wallet: +$50   │                   │
   │                     │    update ledger         │                   │
   │                     │                          │                   │
   │  "Wallet topped up" │                          │                   │
   │◀────────────────────┤                          │                   │
```

### Flow 2: P2P TRANSFER (The Instant Part) ⚡

```
 User A                         Zippie                             User B
   │                               │                                 │
   │  "Send $20 to User B"         │                                 │
   ├──────────────────────────────▶│                                 │
   │                               │                                 │
   │                               │  ★ INTERNAL LEDGER (atomic)     │
   │                               │    • check User A balance ≥ $20 │
   │                               │    • DEBIT User A wallet: -$20  │
   │                               │    • CREDIT User B wallet: +$20 │
   │                               │    • journal entry              │
   │                               │    • ~5ms total                 │
   │                               │                                 │
   │                               │  push: "You received $20"       │
   │                               ├────────────────────────────────▶│
   │  "Sent ✓"                     │                                 │
   │◀──────────────────────────────┤                                 │
   │                                                                 │
   │  <50ms round-trip. No Paynow. No rails. No waiting.             │
```

### Flow 3: CASH-OUT (Off-Ramp)

```
 User B                Zippie                    Paynow              EcoCash
   │                     │                          │                   │
   │  "Withdraw $20"     │                          │                   │
   ├────────────────────▶│                          │                   │
   │                     │  ★ debit wallet: -$20    │                   │
   │                     │    mark pending          │                   │
   │                     │                          │                   │
   │                     │  payout request          │                   │
   │                     ├─────────────────────────▶│                   │
   │                     │                          │  disbursement     │
   │                     │                          ├──────────────────▶│
   │                     │                          │                   │
   │                     │                          │  confirmed        │
   │                     │                          │◀──────────────────┤
   │                     │   webhook: paid          │                   │
   │                     │◀─────────────────────────┤                   │
   │                     │                          │                   │
   │                     │  mark withdrawal done    │                   │
   │                     │                          │                   │
   │  "$20 sent to 077.."│                          │                   │
   │◀────────────────────┤                          │                   │
   │                     │                          │                   │
   │       💰 User B's phone receives $20 via EcoCash                   │
```

---

## Where Zippie Plugs Into Paynow

Only at **three points**:

| Integration | Paynow Endpoint | When |
|-------------|----------------|------|
| **Top-up (on-ramp)** | `paynow.send_mobile()` | User loads wallet from EcoCash/OneMoney |
| **Cash-out (off-ramp)** | Paynow Payout API | User withdraws wallet to EcoCash/OneMoney |
| **Webhook receiver** | `POST /paynow/webhook` | Confirms top-up or cash-out completed |

**Everything else stays internal.** P2P, balance checks, transaction history, requests —
all handled by Zippie's own database.

---

## Why This Wins

| Metric | Current Approach | Float Model |
|--------|-----------------|-------------|
| P2P latency | 30s–2min (USSD) | <50ms (ledger) |
| Failure mode | Network timeout | Atomic rollback |
| Cost per P2P | Paynow fee every time | ~0 (free after top-up) |
| UX | Enter PIN on every send | Enter PIN only on top-up |
| Works offline? | No (needs mobile network) | P2P yes (backend only) |
| Regulatory | Paynow compliance | Paynow compliance on edges + internal AML |

**Float economics**: 1 top-up transaction might generate 20 internal P2P transfers before
cash-out. You pay gateway fees once, amortize over many free transfers.

---

## What Zippie Already Has (vs. What's Needed)

### ✓ Already built
- User auth (JWT)
- Accounts (USD, ZWL wallets) — **this IS the ledger**
- Transaction journal (pending/completed/failed)
- Paynow integration for mobile + web checkout (currently on send)
- FastAPI + PostgreSQL + React

### ✗ Missing for full Float Model
1. **Top-up screen** — new UI flow that calls the existing `initiate_paynow_payment` endpoint but credits wallet instead of creating a "send"
2. **Cash-out screen** — new UI flow + backend endpoint that debits wallet and calls Paynow Payout API
3. **Refactor SendMoney** — remove the Paynow call, replace with internal atomic ledger transfer (debit sender, credit recipient)
4. **Recipient lookup** — need to resolve `phone/email → zippie user_id` for internal transfers (skip for non-users, fallback to Paynow send)
5. **Reconciliation job** — daily cron that verifies sum-of-wallets == Paynow merchant balance

### Migration path (minimum viable changes)

**Phase 1** — Internal P2P (the big win)
- Add `recipient_user_id` to Transaction model
- Modify `/payments/transactions` endpoint: if recipient is a Zippie user, do atomic debit/credit and mark completed immediately. Otherwise keep current Paynow flow.
- UI: add a "Zippie contacts" section to SendMoney

**Phase 2** — Top-up flow
- New endpoint `/payments/paynow/topup/initiate` (reuses paynow_service)
- On webhook confirmation, credit the user's primary account
- New screen `TopUp.tsx`

**Phase 3** — Cash-out flow
- New endpoint `/payments/paynow/withdraw/initiate`
- Debit wallet, call Paynow Payout API
- New screen `CashOut.tsx`

**Phase 4** — Non-user sends (fallback)
- If recipient is not a Zippie user, route through current Paynow mobile checkout
- Still works, just not instant

---

## The Pitch for the Boss

> "We increase Paynow transaction volume by concentrating high-frequency P2P
> inside a single merchant float, and only touching rails at system edges.
> We are a volume amplifier, not a competitor.
>
> Inside Zippie, users send to each other in milliseconds. Outside Zippie,
> every dollar moves through Paynow's rails — which means every dollar earns
> Paynow fees. One top-up of $50 can generate 20 internal transfers before
> cash-out. That's 20x the engagement on the same dollar of float."

---

# Part 2: Risks & Controls

Architecture solves **latency**. It doesn't solve **correctness, risk, or regulation**.
Below are the six categories that break wallet startups, and the concrete controls
Zippie needs before shipping real money.

## 1. Ledger Correctness

**Problem:** Race conditions, split-brain ledger, stale reads.

**Current state — ❌ HAS BUGS**

`backend/app/api/v1/payments.py::_complete_transaction`:
```python
account = db.query(models.Account).get(transaction.account_id)
account.balance -= transaction.amount  # ⚠️ No row lock!
```

Two concurrent webhooks for the same sender can both read balance=100 and
both deduct, leaving 80 instead of 60. The atomic `UPDATE WHERE status='pending'`
protects the transaction row but NOT the account balance.

**Controls needed:**
- **Row locking**: `SELECT ... FOR UPDATE` on sender account before debit
- **Double-entry ledger**: new `ledger_entries` table, every transaction creates
  balanced DR/CR pair, sum must always = 0
- **Strict DB transactions**: debit + credit + journal in a single commit
- **Invariant check**: `sum(wallet.balance) == sum(positive_ledger_entries)` always

**Minimum schema change:**
```sql
CREATE TABLE ledger_entries (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(id),
    account_id INTEGER REFERENCES accounts(id),
    amount NUMERIC(18, 2) NOT NULL,  -- signed: negative = debit, positive = credit
    balance_after NUMERIC(18, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ledger_tx ON ledger_entries(transaction_id);
CREATE INDEX idx_ledger_account ON ledger_entries(account_id, created_at);
```

Every transfer creates exactly 2 entries that sum to 0.

## 2. Float & Liquidity Risk

**Problem:** Zippie holds customer money. If Paynow merchant account is frozen,
drained, or hits daily limits, users can't cash out. Bank run risk.

**Current state — ❌ Not addressed**

**Controls needed:**
- **100% float backing**: at all times, `sum(wallet.balance) <= paynow_merchant_balance`
- **Daily reconciliation cron**: pull Paynow merchant balance, compare to ledger sum, alert on drift
- **Minimum float buffer**: reject top-ups if merchant account is within 10% of limit
- **Float health dashboard**: single-pane view of ledger sum, Paynow balance, daily deltas
- **Cash-out queue + throttle**: if 80% of users try to withdraw simultaneously, queue with SLA instead of failing

## 3. Fraud & Abuse

**Problem:** Instant P2P = instant fraud. Stolen account logs in, sends to mule,
mule cashes out. Rails-based transfers have natural friction (USSD PIN delay).
Internal ledger has none.

**Current state — ❌ No limits, no risk scoring**

**Controls needed (in order of urgency):**
1. **Velocity limits** — per-user per-hour, per-day caps (e.g. $200/day for new users)
2. **Cash-out cooldown** — 24h hold on first top-up before withdrawal allowed
3. **KYC gate** — phone + email verified before any P2P, full KYC before >$100/day
4. **Risk scoring on cash-out** — flag if: account age <7d, multiple top-up sources,
   recipient of many small transfers (mule pattern)
5. **Device fingerprinting** — same device sending/receiving = suspicious
6. **Transaction reversal window** — 30-second "undo" before P2P is final (optional)

Most of these are code, not ML. Simple rules catch 90% of fraud.

## 4. Idempotency & Webhook Handling

**Problem:** Paynow retries webhooks. Network errors cause client retries.
Without idempotency, users get double-credited.

**Current state — ⚠️ Partial**

The `_complete_transaction` atomic update is idempotent-ish — but only by transaction ID.
If Paynow sends the same webhook twice for the same `reference`, we'd process it twice
because nothing tracks "already processed Paynow reference X".

**Controls needed:**
- **Idempotency keys on all write endpoints** — client sends `X-Idempotency-Key` header,
  server stores key → response, returns cached on retry
- **Paynow reference dedup** — unique index on `transaction_metadata->>'paynow_reference'`,
  webhook handler rejects duplicates
- **Webhook event log** — append-only table of every webhook received (for audit + replay)

**Schema:**
```sql
CREATE TABLE webhook_events (
    id SERIAL PRIMARY KEY,
    source VARCHAR NOT NULL,  -- 'paynow'
    reference VARCHAR NOT NULL UNIQUE,  -- dedup key
    raw_payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 5. Migration UX (Instant vs Slow Sends)

**Problem:** Users confused why Send to Alice is instant but Send to Bob takes 2 minutes.

**Current state — ❌ Not designed**

**Controls needed:**
- **Recipient lookup before send** — as user types phone/email, check "is this a Zippie user?"
- **Clear visual split in UI**:
  - ⚡ **Zippie user** — "Instant, free"
  - 📲 **Mobile money** — "Via EcoCash, 1-2 min, small fee"
- **Separate confirm screens** — different copy, different expectations
- **Default to Zippie users** in contact picker, fallback to phone entry

## 6. Regulatory Reality

**Problem:** Zippie holds stored value. RBZ may classify us as a Payment Service Provider
or Money Transmitter regardless of where the float physically sits.

**Current state — ❌ No conversation started**

**Controls needed:**
- **Early RBZ conversation** — before launch, not after
- **Conservative limits during pilot** — $50/day per user, $500/month, cap total float
- **100% float in Paynow merchant account** (no investing, no lending)
- **Clear T&Cs** — Zippie is a technology layer, Paynow is the money services provider
- **KYC tiers** — phone verified ($50/day), ID verified ($500/day), full KYC ($5000/day)
- **Audit trail** — immutable transaction log, exportable for regulator on demand

---

# Part 3: Critical Fixes Before Demo

If we want this to be demo-able with real money, these are the **non-negotiables** in order:

## P0 — Fix Before Any Real Transaction

1. **Row locking in `_complete_transaction`** — add `SELECT ... FOR UPDATE` on account
2. **Paynow reference dedup** — unique index + webhook rejection
3. **Ledger entries table** — even if we don't refactor reads yet, start writing DR/CR pairs

## P1 — Fix Before External Launch

4. **Velocity limits** — daily/hourly caps per user
5. **Cash-out 24h cooldown** for new accounts
6. **Daily reconciliation job** — ledger sum vs Paynow merchant balance
7. **Phone + email verification gate** before first P2P

## P2 — Fix Before Scale

8. **Full KYC flow** — ID upload, selfie match
9. **Risk scoring service** — rule-based, catches common mule patterns
10. **Webhook event log** — audit + replay capability
11. **Idempotency keys** on top-up/withdraw endpoints

---

## CTO Verdict — Self-Assessment

| Dimension | Previous Score | After This Review |
|-----------|---------------|-------------------|
| Architecture | 9.5/10 | 9.5/10 |
| Business Model | 9/10 | 9/10 |
| **Risk Awareness** | needs work | documented ✓ |
| **Regulatory Planning** | needs work | documented ✓ |
| **Code Correctness** | 7/10 | **2 known bugs logged** |

The architecture is right. The business model is right. But there's a **live race condition
in production code** and **no fraud controls at all**. Before showing a boss this is demo-ready,
P0 must be fixed.
