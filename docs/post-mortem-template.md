# Post-Mortem: <INCIDENT-TITLE>

**This document is blameless.** Focus is on process and systems, not on the people involved. If a name appears, it is because a role (e.g. incident commander) is being referenced, not because anyone is at fault. Humans operate systems. Systems that depend on humans being perfect are broken systems.

---

## 1. Summary

One sentence. What happened.

> Example: On 2026-04-22, a ledger-drift check returned `invariant_ok=false` for two user accounts after a failed migration left three ledger entries orphaned from their transactions.

## 2. Incident metadata

| Field | Value |
|-------|-------|
| Incident ID | `INC-YYYYMMDD-<slug>` |
| SEV level | SEV-1 / SEV-2 / SEV-3 |
| Started | `YYYY-MM-DD HH:MM UTC` (first symptom / first alert) |
| Detected | `YYYY-MM-DD HH:MM UTC` (when a human was looking at it) |
| Mitigated | `YYYY-MM-DD HH:MM UTC` (user-visible impact stopped) |
| Resolved | `YYYY-MM-DD HH:MM UTC` (root cause fixed, not just worked around) |
| Duration (MTTR) | From Started to Mitigated |
| Incident commander | @role |
| Runbook used | [`runbooks/<name>.md`](runbooks/<name>.md) or "no runbook existed" |

## 3. Impact

Be specific. Numbers.

- **Users affected:** <count> / <total active> (<pct>%)
- **Dollars at risk / stuck:** $<amount>
- **Transactions affected:** <count> — of which <count> completed incorrectly, <count> failed, <count> stuck pending
- **Data loss:** yes / no — if yes, what
- **SLA impact:** <up-time percentage change> / none
- **External (press, regulator, Paynow) awareness:** yes / no

If the answer to any of the above is "we don't know," that is a finding — add it to section 10.

## 4. Timeline

Minute-by-minute. Pull from the incident channel scribe log. UTC.

```
HH:MM  First symptom (alert fired / user reported / graph turned red)
HH:MM  Acknowledged by @role
HH:MM  Incident declared SEV-X, channel #inc-... opened
HH:MM  IC assigned: @role
HH:MM  Action: <what was done>
HH:MM  Observation: <what was seen>
HH:MM  Decision: <what was chosen, by whom, why>
HH:MM  Mitigation applied — user impact stops
HH:MM  Root cause identified
HH:MM  Fix deployed
HH:MM  Resolution called
```

## 5. Root cause (5 whys)

Drill down from the proximate symptom to the systemic cause. Stop at the layer where a reasonable fix is possible (usually 4–6 whys).

1. **Why did X happen?** — Because Y.
2. **Why did Y happen?** — Because Z.
3. **Why did Z happen?** — Because W.
4. **Why did W happen?** — Because V.
5. **Why did V happen?** — Because <systemic cause>.

State the systemic cause in one sentence.

## 6. What went well

- <thing>
- <thing>

Name the safety nets that actually worked. Dedup constraints that fired. Row locks that held. Runbooks that were accurate. Alerts that fired on time. Credit the system, not individuals — this is how we reinforce what to keep.

## 7. What went badly

- <thing>
- <thing>

Gaps. Alerts that did not fire. Runbooks that were wrong or missing. Tests that should have caught this. Processes that added friction. Timeouts that were too loose or too tight. Again: systems and process, not people.

## 8. Detection

- **Did an alert fire? Which one?**
- **Was MTTD acceptable?** Target: < 5 min for SEV-1, < 15 min for SEV-2. Actual: <duration>.
- **If MTTD was slow:** what signal would have caught it faster? (e.g. "reconciliation should run every 5 minutes, not nightly.")
- **Was the right person paged?** If the wrong person, or nobody, was paged — add an action item.

## 9. Mitigation

- **Did the runbook work?** Yes / partially / no / no runbook existed.
- **What was missing from the runbook?** Specific commands, specific flags, specific decision criteria.
- **How close was the MTTR to the runbook's TTR target?**
- **Did we have to improvise?** What part of the response was not pre-documented?

If we improvised, the improvisation probably belongs in the runbook now.

## 10. Action items

Each item: owner, due date, priority. Put them in the issue tracker immediately, link here.

| # | Item | Owner | Due | Priority |
|---|------|-------|-----|----------|
| 1 | <concrete change> | @role | `YYYY-MM-DD` | P0 / P1 / P2 |
| 2 | ... | | | |
| 3 | If any runbook was missing or wrong, fix it. | @role | within 1 week | P0 |

Action items must be **concrete** (not "improve monitoring") and **owned** (a person, a date). Anything softer than that will not happen.

## 11. Lessons learned

Two or three sentences. What would a smart new engineer need to know to avoid repeating this? What is the category of mistake (e.g. "we trusted a vendor's webhooks as the only delivery path," "we did not have row-level locks on a balance mutation," "we deployed a migration without a dry run on staging")?

These lessons feed into code review, onboarding, and architecture decisions. Write them so they generalise.

## 12. Appendix

- Link to the incident channel archive.
- Screenshots of graphs / dashboards during the incident.
- Relevant SQL queries run.
- Logs snippets (scrub secrets and user PII before committing).
- Paynow / vendor correspondence (if any).
