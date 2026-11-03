<notes>
Evidence base: one rollout (base1.md) and its deliverable (answer.txt). No
divergence available, so edits trace to a concrete omission/risk in that single
run. The run handled the procedure well — acked the page, read the runbook from
the incident channel, compared config/runtime.ts across the pre-deploy and
deploy commits, found concurrency 32 -> 3 in commit a0f94a3, opened+merged PR #1
to restore 32, waited for deploy success, and correctly held off on declaring
recovery until the Datadog monitor "Orders request failures" returned to OK and
error logs stopped. I did not touch any of that; it is already correct, and
duplicating it would only dilute context.

CHANGE 1 — new skill skills/incident-status-update/SKILL.md, with a trigger line
added to systemprompt.md step 5 (same edit, as validation requires).
Moment: base1.md line 74 / answer.txt line 14. The agent's closing line states
"The request-thread status reply that a human will ask for hasn't come up yet,
so I didn't post one." The task (task.md) explicitly requires: "A human will
request status during the incident: reply in the request thread with current
impact, action and next update, preserving uncertainty until recovery is
observed." The run treated this as conditional on a message appearing and so
never produced the required status deliverable in its defined shape. That is the
one clear failure. I encoded it as the DOM artifact contract it is — a status
post must carry all three named parts (current impact / action / next update)
and must not claim recovery until the runbook's recovery signal is observed —
because it has a recognisable trigger (a status request / each major incident
step) and should cost nothing until that situation arises. Put it in a skill
rather than always-on prose for that reason. The trigger line also tells the
agent the request is standing from the moment it is paged, directly countering
the "hasn't come up yet" reasoning that caused the miss.

Why the skill carries procedure, not matter facts: it points the agent to read
the runbook in the incident Slack channel for WHICH monitor/metric defines
recovery, rather than hard-coding "Orders request failures" / config/runtime.ts
/ a0f94a3. Those are this matter's facts (verified here, but wrong anchors for
the next incident), so per the mission they stay out of the harness; the skill
states only the reusable structure and the uncertainty discipline, which the
runbook in base1.md line 8 itself insists on ("do not report recovery until the
monitor confirms it").

No other edits. guardrails.md and LongTermMEMORY.md left empty — I found no
short rule that applies to EVERY task here and is not already covered, and the
mission warns against paying always-on budget for prose. systemprompt's existing
timestamp rule (use the incident's own timestamps) was already honoured by the
run, so I left it. The procedure steps the run already got right are unchanged.
</notes>
