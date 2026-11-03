<notes>

## Changes made

### 1. `systemprompt.md` — added step 6: human status-request handling

**Trajectory moment:** base1.md line 73 (deliverable answer.txt line 14): the agent itself flags "The request-thread status reply that a human will ask for hasn't come up yet, so I didn't post one." The task states unambiguously "A human will request status during the incident: reply in the request thread with current impact, action and next update, preserving uncertainty until recovery is observed." No human message appeared in the simulation, so the agent never had to act on it — but the task guarantees it will appear. The existing step 5 ("Keep the team informed in the incident channel") does not cover the reply-in-thread pattern or the explicit preservation-of-uncertainty requirement. Added step 6 to name the trigger (a human status post in the channel), the required response shape (impact, action, next-update time), and the uncertainty constraint, in line with what the task asks for. This is a short always-on rule that applies to every run of this task.

### 2. `LongTermMEMORY.md` — workspace facts from the rollout

**Trajectory moment:** base1.md lines 3-8 (channel discovery + runbook), lines 9-10 (commit list), lines 12-13 (monitor list), lines 16-19 (file fetch). The agent spent four tool calls discovering the Slack channel id, the repository name, the config path, the monitor name and id, and the recovery signal. These are stable, verified facts about this workspace that the next run will need again. Recording them directly removes the rediscovery cost and eliminates the risk of mis-joining or picking the wrong monitor. All entries are labelled "in this workspace" and sourced from the observed tool responses, not inferred.

No other changes. The agent's sequencing (acknowledge → investigate → PR → wait for deploy → wait for monitor → confirm logs → resolve → finish) was correct throughout. The existing timestamp instruction in systemprompt.md was followed correctly. No repeated mechanical errors or ignored invariants were observed that would justify a script or plugin.

</notes>
