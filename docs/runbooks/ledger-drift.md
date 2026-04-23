# Ledger Drift

## Symptom

One or more of:
- `GET /api/v1/admin/reconciliation` returns `invariant_ok: false`.
- `global_drift != 0` in the reconciliation payload.
- `account_violations` is non-empty (some account's `balance` does not equal its `ledger_net`).
- `unbalanced_internal` is non-empty (an internal P2P transaction has DR != CR).

Any of these means the double-entry invariant — `sum(wallet.balance) == sum(positive_ledger_entries)` — has been violated. Customer money is at risk until reconciled.

## Severity

**SEV-1.** Money-at-risk. Page immediately. See [`../incident-response.md`](../incident-response.md).

## Time-to-resolve target

60 minutes from page to "freeze + diagnosis complete + adjustment staged." Full resolution (adjustment posted, root cause identified) may take longer; freezing writes is the 60-minute gate.

## 1. Freeze new transactions (first 2 minutes)

Set both feature flags to `false`. This 503s new P2P and Paynow checkouts but leaves reads and existing pending transactions intact.

Render / Railway / equivalent: set environment variables, redeploy.

```
FEATURE_INTERNAL_P2P=false
FEATURE_PAYNOW_CHECKOUT=false
FEATURE_TOPUP=false
```

Flag logic: `backend/app/core/features.py` → `is_enabled()` reads `settings.FEATURE_*` at request time, so redeploy is required (config is read at app start via Pydantic `BaseSettings`).

Verify freeze took effect:

```bash
curl -X POST https://<api-host>/api/v1/payments/transactions -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"transaction_type":"sent","amount":1,"recipient":"test@example.com","currency":"USD"}'
# Expect: 503 {"detail":"Feature 'internal_p2p' is disabled"}
```

Announce freeze in the incident channel with timestamp.

## 2. Capture the evidence (next 5 minutes)

Before touching data, snapshot the reconciliation report and the affected accounts. This is the forensic baseline.

```bash
curl -s https://<api-host>/api/v1/admin/reconciliation -H "Authorization: Bearer $ADMIN_TOKEN" | tee /tmp/recon-$(date +%s).json
```

Save `/tmp/recon-*.json` to the incident channel as an attachment. Do not lose this file.

## 3. Diagnose

Query the DB read-only (use the replica if available). For each account in `account_violations`:

```sql
-- Ledger trail
SELECT id, transaction_id, amount, direction, balance_after, created_at
FROM ledger_entries WHERE account_id = <account_id> ORDER BY created_at, id;

-- Current balance + last-update
SELECT id, user_id, balance, currency, updated_at FROM accounts WHERE id = <account_id>;

-- Audit trail
SELECT source, event_type, actor_user_id, payload, created_at FROM audit_events
WHERE payload::text LIKE '%"sender_account_id": <account_id>%'
   OR payload::text LIKE '%"recipient_account_id": <account_id>%'
ORDER BY created_at DESC LIMIT 200;

-- Signature of bypassed-service-layer mutation: accounts.updated_at newer than last ledger entry
SELECT a.updated_at, MAX(l.created_at) AS last_ledger FROM accounts a
LEFT JOIN ledger_entries l ON l.account_id = a.id WHERE a.id = <account_id> GROUP BY a.updated_at;
```

For each unbalanced internal tx: `SELECT * FROM ledger_entries WHERE transaction_id = <tx_id> ORDER BY direction;`

## 4. Common causes

1. **Race in `_internal_transfer`.** Should not happen — `payments.py` uses `SELECT FOR UPDATE` + `populate_existing()` on both accounts, ordered by ID. If this is the cause, `backend/tests/integration/test_concurrency.py` has regressed. Check git log on `payments.py` and `models.py`.
2. **Paynow webhook double-credit.** Should not happen — `WebhookEvent` has UNIQUE `(source, reference)` and the handler inserts via `db.begin_nested()`. Look for `audit_events` where `event_type='transaction.completed'` fires twice for the same `subject_id`, and for `webhook_events.processed_at IS NULL` (handler crashed mid-flight).
3. **Direct DB mutation bypassing service layer.** Someone ran `UPDATE accounts SET balance = ...`. Diagnostic: `accounts.updated_at` newer than latest `ledger_entries.created_at` (query in section 3). Check bastion shell history and recent Alembic migrations.
4. **Alembic migration bug.** New migration changed column types or dropped constraints. Look at `backend/alembic/versions/` since last clean reconciliation.

## 5. Recovery — adjustment ledger entry

Once root cause is understood, balance the account with an explicit adjustment. Do this inside a single DB transaction. **Never** `UPDATE accounts SET balance` without a matching `ledger_entries` row — that is exactly what got us here.

Template (adjust numbers; `<tx_id>` is a new transaction created for this adjustment):

```sql
BEGIN;

-- 1. Create the adjustment transaction (ops attribution)
INSERT INTO transactions (user_id, account_id, transaction_type, amount, currency,
                          recipient, status, payment_method, description, created_at)
VALUES (<owner_user_id>, <account_id>, 'adjustment', <abs_drift_amount>, '<currency>',
        '<owner_email>', 'completed', 'ops_adjustment',
        'Ledger drift adjustment — incident <INC-ID>', NOW())
RETURNING id;  -- capture as <tx_id>

-- 2. Write the balancing ledger entry
-- direction = 'credit' if drift is negative (account under-funded vs ledger)
-- direction = 'debit'  if drift is positive (account over-funded vs ledger)
INSERT INTO ledger_entries (transaction_id, account_id, amount, direction, balance_after, created_at)
VALUES (<tx_id>, <account_id>, <abs_drift_amount>, '<credit_or_debit>',
        <new_balance_after_adjustment>, NOW());

-- 3. Update the account balance to match
UPDATE accounts SET balance = <new_balance_after_adjustment>, updated_at = NOW()
WHERE id = <account_id>;

-- 4. Record the manual adjustment in the audit log (ops attribution)
INSERT INTO audit_events (source, event_type, subject_type, subject_id, actor_user_id, payload, created_at)
VALUES ('ops', 'ledger.manual_adjustment', 'account', <account_id>, <ops_user_id>,
        '{"incident_id":"<INC-ID>","drift":"<drift>","direction":"<direction>","reason":"<one-liner>"}',
        NOW());

-- 5. Verify the invariant holds for this account before committing
-- (sum of credits minus sum of debits should equal the new balance)
SELECT a.balance,
       COALESCE(SUM(CASE WHEN l.direction='credit' THEN l.amount ELSE -l.amount END), 0) AS ledger_net
FROM accounts a LEFT JOIN ledger_entries l ON l.account_id = a.id
WHERE a.id = <account_id> GROUP BY a.balance;
-- If balance == ledger_net, COMMIT. Otherwise ROLLBACK and re-diagnose.

COMMIT;
```

Re-run `GET /api/v1/admin/reconciliation` and confirm `invariant_ok: true`.

## 6. Unfreeze

Restore flags to `true` only after reconciliation passes and root cause is mitigated:

1. `FEATURE_INTERNAL_P2P=true`, smoke-test one transfer.
2. `FEATURE_PAYNOW_CHECKOUT=true`, `FEATURE_TOPUP=true`, smoke-test one top-up.
3. Announce unfreeze.

## Post-incident

- **Post-mortem: required.** Use [`../post-mortem-template.md`](../post-mortem-template.md). Within 72h.
- **Notify:** founder + any user whose account was adjusted (transparency; include the adjusted amount and reason).
- **Update the audit dashboard** if drift went undetected for > 1 hour — either the check isn't running often enough or the alert routing is broken.
- **Add a regression test** covering the root cause (ideally before the post-mortem is signed off).
- **Revisit reconciliation cadence.** If we don't have a cron yet, this incident bumps P1 item #9 to P0. See `../ARCHITECTURE.md` Part 3.
