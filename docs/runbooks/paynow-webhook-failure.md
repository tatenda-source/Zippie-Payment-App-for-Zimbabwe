# Paynow Webhook Failure

## Symptom

One or more of:
- Users report "I topped up but my wallet is still empty."
- Transactions with `status='pending'` and `payment_method IN ('ecocash','onemoney','web','paynow_topup')` older than 10 minutes.
- Sentry spike on `Paynow webhook received with invalid hash` (429 validation failures at `/api/v1/payments/paynow/webhook`).
- Paynow merchant dashboard shows successful payments that never arrived at our endpoint.
- `webhook_events` table has no new rows in the last 15 minutes despite top-up volume.

## Severity

**SEV-2.** Service degraded. On-ramps stuck; internal P2P unaffected. Page primary on-call.

## Time-to-resolve target

30 minutes from page to mitigation (users unstuck via polling fallback). Root-cause resolution may take longer if Paynow is at fault.

## 1. Triage — is it us or them? (first 5 minutes)

```sql
-- Any webhooks received in the last 15 minutes?
SELECT source, reference, received_at, processed_at
FROM webhook_events
WHERE received_at > NOW() - INTERVAL '15 minutes'
ORDER BY received_at DESC LIMIT 50;
```

- **Rows exist, `processed_at` is populated:** webhooks are arriving and being processed — problem is elsewhere. Check ledger drift, check user-facing error.
- **Rows exist, `processed_at` is NULL:** webhook handler is crashing mid-processing. Jump to section 3.
- **No rows at all:** webhooks are not arriving. Jump to section 2.

Also check Sentry for the last 30 minutes filtered to `paynow_webhook`. Hash-validation failures (`Paynow webhook received with invalid hash`) mean Paynow changed the signing secret or our `PAYNOW_INTEGRATION_KEY` drifted — reconcile via the Paynow merchant dashboard.

## 2. Webhooks not arriving

Verify our endpoint is reachable from Paynow's side:

```bash
curl -v -X POST https://<api-host>/api/v1/payments/paynow/webhook -d 'test=1'
# Expect: 403 Invalid hash (means the route is live and hash validation fires)
```

If that 403s: our endpoint works, Paynow is not calling us. Log into the Paynow merchant dashboard, integration ID `23657`, check:
- Delivery attempts for recent transactions. Are they retrying? What error is Paynow seeing?
- Webhook URL setting. Does it still point to `/api/v1/payments/paynow/webhook` on the current host? (If we changed hosts or DNS without updating Paynow, this is the cause.)

If the endpoint returns anything other than 403 Invalid hash (e.g. 502, 504, connection refused): the issue is infra. Check load balancer, Render/Railway status, DNS.

## 3. Webhook arriving but not processed

Look at `webhook_events` rows with `processed_at IS NULL`:

```sql
SELECT reference, raw_payload, received_at FROM webhook_events
WHERE processed_at IS NULL AND source='paynow' AND received_at > NOW() - INTERVAL '1 hour'
ORDER BY received_at DESC;
```

Then check application logs for errors around those `received_at` timestamps. Likely causes:
- `_complete_transaction` raised an exception mid-flight (e.g. FK violation, constraint violation).
- DB deadlock or timeout on `SELECT FOR UPDATE`.
- `_parse_tx_id_from_reference` returned None because Paynow sent an unexpected reference format.

## 4. Mitigation — unstick users via polling fallback

The `/api/v1/payments/paynow/status/{transaction_id}` endpoint polls Paynow directly via `poll_url` stored in `transaction_metadata`, bypassing webhooks entirely. It calls `_complete_transaction` on success. This is the fallback path by design.

Find stuck transactions and poll each one:

```sql
SELECT id, user_id, amount, currency, created_at
FROM transactions
WHERE status='pending'
  AND payment_method IN ('ecocash','onemoney','web','paynow_topup')
  AND created_at < NOW() - INTERVAL '5 minutes'
ORDER BY created_at ASC;
```

Script to poll each (run from a trusted host with a valid admin/ops bearer token — note: `/paynow/status/{id}` requires the transaction owner's token, not an admin token; for ops unblocking, run this per-user or extend the endpoint for ops use):

```bash
for TX_ID in 101 102 103; do
  curl -s -X GET "https://<api-host>/api/v1/payments/paynow/status/$TX_ID" \
       -H "Authorization: Bearer $USER_TOKEN"
  echo
done
```

Each successful poll flips the transaction to `completed` and credits the wallet.

For a bulk unstick without per-user tokens: write a one-off script that iterates pending topups, fetches `poll_url` from `transaction_metadata`, calls `paynow_service.check_status(poll_url)`, and runs `_complete_transaction()` on paid results. Post the script to the incident channel, not to the repo.

## 5. If webhooks are permanently broken (Paynow-side)

Deploy the polling fallback as a scheduled task:
- Every 60 seconds, scan for `transactions` with `status='pending'`, `payment_method IN (...)`, `created_at > NOW() - INTERVAL '30 minutes'`, call `paynow_service.check_status()` on each.
- This turns webhooks into a latency optimization instead of a dependency.

## Post-incident

- **Post-mortem:** required if webhook failures exceed **5% of top-up volume for > 1 hour**, or if any user experienced > 30 minutes of pending-wallet confusion. Otherwise optional. Within 72h.
- **Notify affected users** that top-ups may have arrived late. Refund / comp at founder's discretion.
- **Escalate to Paynow merchant support** (phone + email, integration ID `23657`) with timestamps and delivery-attempt logs if the failure was on their side.
- **Action item:** if we do not yet have the cron-based polling fallback from section 5, file it. Webhooks should never be the only path to transaction completion.
