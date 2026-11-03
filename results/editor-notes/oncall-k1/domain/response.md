<notes>

## Changes made

### 1. New skill: `skills/status-reply/SKILL.md`

**Trajectory moment:** base1 line 74 — the agent notes "The request-thread status reply that a human will ask for hasn't come up yet, so I didn't post one." The task specification explicitly requires: "A human will request status during the incident: reply in the request thread with current impact, action and next update, preserving uncertainty until recovery is observed." The agent had no harness guidance on what this reply must contain, so it produced nothing. This is a concrete omission traceable to the gap between the task requirement and the current harness.

**What the skill encodes:**
- The required three-part structure (impact / action / next update) that the task names explicitly.
- The uncertainty rule: do not claim recovery until the Datadog monitor is OK *and* no error logs in the last minute. The runbook in this trajectory (base1 line 8) stated "do not report recovery until the monitor confirms it," and the agent respected this in its own recovery check (lines 50–58) — but had no structure to apply the same discipline to a mid-incident human-requested status reply.
- A pre-send checklist so the agent can verify the reply is complete before posting.

This is a skill (not always-on text) because the trigger is recognisable and bounded: it fires only when a human asks for status. Zero cost on all other steps.

### 2. Edit to `systemprompt.md` step 5 — trigger line

Added: "When a human asks for a status update, load the `status-reply` skill." This is required for the skill to survive validation (a skill not named in always-on text is never opened). The addition is one clause on an existing line — no net cost increase of consequence, and it makes the skill exist.

## What was not changed

- `guardrails.md`, `LongTermMEMORY.md`, `tool_descriptions/tool_guidance.md` — the base run followed all constraints without violation; no rules need reinforcing.
- The core investigation and repair procedure in `systemprompt.md` — the agent executed steps 1–6 correctly and in the right order. Rewriting what already worked changes behaviour the runs got right.
- No workspace-specific facts (channel ID, repo name, monitor ID, concurrency values) are encoded in durable memory — those are facts of this incident, not domain constants, and would be wrong anchors for the next task.

</notes>
