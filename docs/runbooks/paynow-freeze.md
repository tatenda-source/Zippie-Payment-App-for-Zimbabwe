# Paynow Merchant Freeze

## Symptom

One or more of:
- `POST /api/v1/payments/paynow/initiate` or `/paynow/topup/initiate` returns 4xx from the Paynow API (not our validation — the Paynow call itself).
- Paynow merchant dashboard shows status "Under Review" or "Suspended" for integration ID `23657`.
- Email from Paynow referencing underwriting, compliance, AML, volume anomaly, or business-model mismatch.
- Payouts / cash-outs failing with a Paynow-side error.
- All newly initiated top-ups failing 100%, but internal P2P works fine.

This is the existential kill-vector documented in [`../VC_ANALYSIS.md`](../VC_ANALYSIS.md) and [`../ARCHITECTURE.md`](../ARCHITECTURE.md) Part 2 section 2. The float model means customer wallets are still solvent against the merchant-account balance we already hold — but no money can enter or leave the system until Paynow unfreezes us.

## Severity

**SEV-1.** Existential. Page founder immediately.

## Time-to-resolve target

"As fast as Paynow will respond." Typical merchant-account reviews take 24–72 hours; high-severity anti-fraud freezes can last weeks. Our job is to minimise user damage while we wait.

## 1. Immediate — freeze the rails (first 2 minutes)

Stop attempting to call Paynow. Leave internal P2P up — that is the whole point of the float model.

Set on the production host and redeploy:

```
FEATURE_TOPUP=false
FEATURE_PAYNOW_CHECKOUT=false
FEATURE_INTERNAL_P2P=true     # leave on — users can still send to each other
FEATURE_CASHOUT=false          # cash-out is Paynow-dependent; kill it too
```

Verify top-ups are now gracefully 503ing:

```bash
curl -X POST https://<api-host>/api/v1/payments/paynow/topup/initiate \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"amount":10,"payment_channel":"ecocash","phone_number":"+263771234567"}'
# Expect: 503 {"detail":"Feature 'topup' is disabled"}
```

Verify internal P2P still works (send $1 between two test accounts). If it does, we have bought time.

## 2. Communicate to users (first 15 minutes)

Users will notice immediately. Get ahead of the support inbox.

**Status banner (in-app):**
> Top-ups and cash-outs are temporarily paused. Sending money to other Zippie users still works normally. Your wallet balance is safe. We'll update here when the issue is resolved.

**SMS template (to users who attempted a top-up in the last 24h):**
> Zippie: top-ups and cash-outs are briefly paused. Money inside Zippie — including sending to friends — is unaffected. Your balance is safe. Updates at <status-url>.

**Email template (same audience):**
> Subject: Zippie top-ups paused — wallets safe
>
> Hi [name],
>
> Top-ups and cash-outs through our payment partner are temporarily paused while we resolve an issue with them. Sending money to other Zippie users continues to work normally, and your wallet balance is fully safe.
>
> We'll email you the moment top-ups and cash-outs are back. In the meantime, if you need help, reply to this email.
>
> — The Zippie team

Do not name Paynow in user comms unless legal advises otherwise. "Our payment partner" is sufficient and preserves our relationship.

## 3. Escalate to Paynow

Primary contact: Paynow merchant support.
- Phone first, email for the paper trail.
- Cite integration ID `23657`.
- Ask three questions: (a) what is the status, (b) what does Paynow need from us, (c) ETA.

If Paynow cites a business-model mismatch (they onboarded us as e-commerce, our actual usage is P2P wallet): this is the #1 cause of aggregator-model freezes per `../ARCHITECTURE.md` Part 2 section 7. Come prepared with:
- Transaction volume and average size.
- User count.
- Description of the float model and why our usage pattern is regular (high volume of small internal P2P, lower volume of on-ramp / off-ramp through Paynow).
- Willingness to re-underwrite under the correct category.

## 4. Diagnose what triggered it

Probable causes, roughly in order of likelihood:
1. **Volume spike** we didn't warn them about. First marketing push, partnership, referral loop. Their risk algorithm auto-freezes anomalies.
2. **Business-model mismatch** surfacing in an audit. See above.
3. **Pattern mistaken for fraud.** Many small same-direction transfers can look like money laundering (structuring). Our legitimate P2P pattern overlaps with it.
4. **Chargeback / dispute** on a single high-value transaction.
5. **KYC gap on a specific user** that Paynow's fraud partner flagged.

Pull our recent Paynow-side transactions to build the defence:

```sql
SELECT COUNT(*), SUM(amount), currency, DATE_TRUNC('day', created_at) AS day
FROM transactions
WHERE payment_method IN ('ecocash','onemoney','web','paynow_topup')
  AND status='completed'
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY currency, day ORDER BY day DESC;
```

## 5. Pre-mitigation — second rail

The Tier 3 / Sprint 2 roadmap item "Second rail relationship (direct EcoCash or CBZ-Iveri)" exists specifically for this incident. If that relationship is live, failover to it now.

**Until that relationship exists, this incident is "wait for Paynow."** There is no alternate rail to fail over to. Document this reality in the post-mortem, and use it to justify the second-rail work.

See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) Part 2 section 2 ("Float & Liquidity Risk") and Part 3 P1 item #14.

## 6. Unfreeze checklist

When Paynow lifts the freeze:

1. Smoke-test one $1 top-up against a staff phone. Confirm webhook arrives.
2. Smoke-test one $1 cash-out. Confirm payout reaches the staff phone.
3. Re-enable `FEATURE_TOPUP=true`, then `FEATURE_PAYNOW_CHECKOUT=true` (leave `FEATURE_CASHOUT` off if cash-out is a separate feature-flagged code path on release).
4. Announce to users (SMS + email + in-app banner removal).
5. Watch Sentry and `webhook_events` for 30 minutes to confirm volume is flowing.

## Post-incident

- **Post-mortem: required.** Within 72h. Use [`../post-mortem-template.md`](../post-mortem-template.md).
- **Priority-bump the second-rail relationship** (P1 #14 in `../ARCHITECTURE.md`). This incident's existence is the justification.
- **Update merchant-clarity item** (P1 #13) if not done: explicit written confirmation from Paynow on our business category.
- **Review volume-warning protocol.** Next time we expect a spike (marketing, partnership), email Paynow a heads-up at least 48h in advance.
- **Consider per-day volume caps** at the application layer so we don't ever trip Paynow's threshold unknowingly.
