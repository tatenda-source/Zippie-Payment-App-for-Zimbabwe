# Incident Response

Process doc. Not a runbook. For "what do I do when X is broken," see [`runbooks/`](runbooks/).

## SEV levels

| Level | Definition | Examples | Response time | Founder page? |
|-------|------------|----------|---------------|----------------|
| **SEV-1** | Money at risk, full outage, or existential vendor risk. | Ledger drift, Paynow freeze, DB outage, webhook hash secret leaked. | Acknowledge < 5 min. Mitigation started < 15 min. | Yes, any hour. |
| **SEV-2** | Degraded service, partial outage, user-impacting but bounded. | Webhook delays, rate-limit spikes, login slow, one Paynow channel (EcoCash) down. | Acknowledge < 30 min during business hours. | Business hours only unless user impact is growing. |
| **SEV-3** | Minor / cosmetic. No user impact or internal-only. | Sentry noise, log-format regression, stale dashboard, a single account drift inside reconciliation tolerance. | Next business day. | No. |

Pick the higher level if you are unsure. Downgrading later is cheap. Discovering mid-incident that a "SEV-2" is actually SEV-1 is not.

## Paging path

### Current (pilot phase)

One name: the founder. All SEV-1 and SEV-2 pages go to the founder's phone directly (SMS + call). SEV-3 goes to email.

There is no rotation and no secondary. That is a known gap — see "Eventual path" below.

### Eventual path (before external users > 100)

1. **Primary on-call** — pager hits phone, 5-min ack SLA.
2. **Secondary on-call** — paged if primary does not ack in 10 min.
3. **Engineering manager** — paged if both primary and secondary miss, or on explicit escalation from the incident commander.
4. **Founder** — paged on SEV-1 only, for awareness, not for response.

Tool: PagerDuty or equivalent (Opsgenie, Grafana OnCall). Rotation: weekly, two engineers.

## Communications

### Internal (response team)

- **One channel per incident.** Name convention: `#inc-YYYYMMDD-<short-name>` (e.g. `#inc-20260422-ledger-drift`). Close the channel on resolution; archive for post-mortem.
- **One incident commander (IC).** Named explicitly in the first message. IC coordinates; other responders execute. No parallel decision-making.
- **Status updates every 15 min** in the channel, even if the update is "still investigating." Silence is worse than "no change."
- **No side-channels.** Decisions happen in the incident channel, in writing, with timestamps. DMs and voice calls are fine for thinking; conclusions go back to the channel.

### External (users)

Use the lightest touch that keeps users informed.

- **Status page** (placeholder: `status.zippie.co.zw`). Marks: operational / degraded / partial outage / full outage. Update on every SEV-1 and SEV-2.
- **In-app banner** — one-liner on the home screen during active SEV-1 / SEV-2. Copy comes from the runbook (each runbook has a template).
- **SMS / email** — only when individual users were affected and need to be notified (e.g. stuck top-up, adjustment posted). Templates live in the relevant runbooks.

Never name third-party vendors in user comms unless legal has signed off. "Our payment partner" > "Paynow."

## War-room protocol

During active SEV-1 / SEV-2:

1. IC declares the incident in the channel and pins the message.
2. IC assigns roles: **operator** (executes runbook steps), **scribe** (timestamps every action in the channel), **comms** (user-facing updates).
3. One voice. Everyone else reads, does not ping the operator with suggestions unless they see a mistake.
4. IC calls resolution when the symptom is gone AND the root cause is understood (or a bounded unknown is documented).

If you are not assigned a role, stay quiet unless asked. The on-call engineer at 3am does not need 4 well-meaning Slack threads.

## Post-mortem

Use [`post-mortem-template.md`](post-mortem-template.md). Fill in within 72 hours of resolution. Publish in the repo under `docs/post-mortems/YYYY-MM-DD-<slug>.md`.

| Incident | Post-mortem? |
|----------|--------------|
| SEV-1 | Required. |
| SEV-2 with user impact | Required. |
| SEV-2 with no user impact | Optional (recommended if novel). |
| SEV-3 | Optional. |

Post-mortems are **blameless**. Focus is on process and systems, not people. "The deploy pipeline allowed an unreviewed migration" — yes. "X should have caught this" — no.

## After the incident

1. Post-mortem filed within 72h.
2. Action items tracked in the normal issue tracker, each with an owner and a due date.
3. If a runbook was wrong or missing, fix it in the same PR as the post-mortem.
4. Review in the next weekly engineering sync. Update this doc if the process itself failed.
