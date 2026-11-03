---
name: status-reply
description: Compose a human-requested status update in the incident thread.
---

# Status Reply

## When to use
A human asks for a status during an active incident. Reply in the same thread (the channel where the request appeared, using the message's thread timestamp if available).

## Required structure — three parts, in this order

1. **Impact** — what is currently broken and for how long (use incident timestamps, not your clock). Include scope if known (e.g. all orders requests, specific region).
2. **Action** — what you have done and what is happening right now (e.g. PR merged, deploy in progress, waiting for monitor).
3. **Next update** — the specific trigger or time at which you will post again (e.g. "after the monitor clears" or "in 5 minutes if the monitor has not cleared").

## Uncertainty rule
Do not declare recovery until the Datadog monitor returns to OK **and** you have confirmed no new error logs in the last minute. If the deploy has succeeded but the monitor is still Alert, say so explicitly — "deploy succeeded; waiting for backlog to drain and monitor to clear" — do not imply recovery. Preserve stated uncertainty until it resolves.

## Checks before sending
- All three parts present: impact, action, next update.
- No recovery language unless the monitor is OK and error logs are absent.
- Incident ID (PagerDuty) and PR number (if open) included for traceability.
