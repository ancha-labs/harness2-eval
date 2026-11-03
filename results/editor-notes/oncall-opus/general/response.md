<notes>
Evidence: one rollout (base1). It handled the mechanics well — acknowledged
immediately (step 5), found the runbook, diagnosed concurrency 32->3 from commit
a0f94a3 in config/runtime.ts, opened+merged PR #1, and correctly withheld the
"recovered" claim until the monitor returned to OK and error logs stopped (steps
50-60). I did NOT touch any of that; the runs already got it right, and MISSION
says not to restate what works.

The one real divergence from the task: the task states "A human will request status
during the incident: reply in the request thread." In base1 the agent read the
incident channel exactly once (step 7) and never re-read it. It posted two top-level
channel messages (steps 20, 61) but never a threaded reply, and it finished having
explicitly noted the gap at line 74: "The request-thread status reply that a human
will ask for hasn't come up yet, so I didn't post one." So the agent raced to
resolution (five world_wait calls) and called finish without ever polling for the
human's request, leaving a named deliverable unmet. Two concrete sub-failures behind
that moment:
  - it never re-read Slack, so a request posted after step 7 would be invisible; and
  - every status post used world_slack_post with only `channel` (steps 20, 61) — no
    thread_ts — so even had it replied, it would have been a channel post, not a
    reply "in the request thread" as asked.

Fix — new skill skills/status-request/SKILL.md, triggered from systemprompt.md:
This is a narrow, recognisable multi-step procedure with a clear trigger, so a skill
is the cheap on-demand form rather than always-on prose. The skill carries the two
things base1 got wrong as workspace-anchored fact: (1) the request is a NEW human
message that appears after the first channel read, so poll the channel at each
checkpoint (after each world_wait, after deploy, before finishing); (2) reply IN the
thread by passing the human message's `ts` as `thread_ts` on world_slack_post — a
bare channel post does not satisfy "reply in the request thread." It restates the
reply's required content (current impact, action, next update) and the task's
uncertainty rule only as the completion condition for this procedure, not as new
domain rules.

Fix — trigger line in systemprompt.md (required; added in the same edit):
Added a short always-on line naming `status-request` verbatim so the skill can load,
plus the one fact base1 most needed and could have acted on by itself: the request
is not present at the start, so re-read the channel and do not finish before checking
for it. This is the "divergence the agent could already handle if told" — the cheapest
win. I kept it to four lines and attached it to the existing step list rather than
adding a free-floating block, to limit always-on cost.

Not done, and why:
  - No plugin hook on world_finish to hard-block exit before a thread reply exists.
    MISSION reserves a defensive hook for REPEATED evidence that clear prose is
    skipped; I have one run, and a hook also cannot reliably verify a *threaded*
    reply was posted, so it risks blocking valid completion. If future rollouts show
    the agent still finishing without the thread reply despite the prose, a
    finish-time poll-and-reply hook becomes justified.
  - No script/subagent: there is no repeated deterministic extraction or
    large-input/small-output investigation here; the work is sequencing, not
    computation.
  - Left guardrails.md, LongTermMEMORY.md, tool_guidance.md and the diagnosis
    procedure unchanged — nothing in the trajectory argues for changing them, and the
    timestamp guidance in systemprompt was already used correctly.
</notes>
