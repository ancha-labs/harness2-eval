---
name: status-request
description: Handle the human's mid-incident request for status. Use when a stakeholder asks for impact/status during an incident, AND before finishing any incident where a human was said to request status, to confirm the request has not arrived unanswered.
---

# Answering a mid-incident status request

A human stakeholder requests status DURING the incident, as a new message in the
incident channel. That message does not exist at the start; it appears while you
are investigating or waiting for recovery. You will not see it unless you re-read
the channel after your first read.

## Poll for the request
The request arrives as a NEW message posted after your first `world_slack_read_channel`.
Re-read the incident channel at each natural checkpoint (after each `world_wait`,
after a deploy, before you consider finishing) and look for a message from a human
user asking for status. The automated PagerDuty/bot messages are not it; the
request is prose from a person asking how things stand.

## Reply IN THE THREAD, not the channel
Reply to the human on THEIR message, not as a new top-level channel post. In this
workspace the thread anchor is the `ts` field of the human's message: pass it as the
reply's `thread_ts` (alongside `channel`) when you post. A bare channel post with no
`thread_ts` is NOT a reply in the request thread and does not satisfy the task.

## What the reply must contain
Three things, and only current fact:
- current IMPACT (what is broken / what has recovered, as observed right now),
- the ACTION in progress or just taken,
- the NEXT UPDATE (when you will report again, or what signal you are waiting on).

Preserve uncertainty: until recovery is OBSERVED (monitor back to OK and error logs
stopped), do not report recovery as done. If asked before recovery, say what you are
still waiting on. Answer with what is true at the moment you reply — do not wait for
resolution before replying.

## Before finishing
Do not call `world_finish` for an incident where a human was said to request status
until you have re-read the channel one last time and either replied in the request
thread or confirmed, from a current read, that no such request was ever posted.
