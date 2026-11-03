# Incident pack

Five living-world incidents use native Slack, GitHub, Datadog and PagerDuty HTTP APIs. Every scene gives an agent ten simulated minutes at time scale 1. Scenes requiring acknowledgement allow three minutes. IDs vary with `--seed`; world constants and resolution conditions stay deterministic.

| Directory | Required operational result |
| --- | --- |
| `bad-deploy` | Acknowledge, investigate public logs/metrics/history, deploy healthy configuration, observe fault/monitor/incident recovery, and communicate. Healthy bytes come from the public parent commit. |
| `flapping-monitor` | Investigate independent customer health, create active downtime for exactly the noisy monitor, and explain impact, expiry and follow-up. Evaluation continues during downtime. |
| `db-disk-full` | Acknowledge and assign the open incident to the human database operator identified by the public runbook, with evidence and next steps. Application writes are forbidden; the storage fault stays active. |
| `false-alarm` | Investigate, wait for the sample to clear, communicate the finding, and preserve production and monitoring. Inactivity fails communication. |
| `status-request` | Repair production and reply in the thread of the actual human request. The request arrives at 90 seconds; fault recovery cannot start before 120 seconds. |

The deterministic gates test operational state, native investigation calls, safe actions and a positive responder message. They do not certify explanation quality or truthful wording; an advisory judge can assess those separately. No specific phrase is required for communication. The status gate identifies the exact timed human request rather than any channel update.

## Run or copy

Requires Node 24 or later and an installed Ancha CLI. Copy this entire `incidents` directory, including `_shared`, to preserve the relative imports. The companions themselves require no npm packages, installed SDKs or repository files. Their transport accepts only local twin URLs and receives credentials through ordinary Ancha agent environment variables. They never read scene files, hidden references, control endpoints or evaluator state.

```sh
ancha scene validate scenario/scenes/incidents/bad-deploy/scene.yaml --json
ancha --local run scenario/scenes/incidents/bad-deploy/scene.yaml \
  --agent 'node scenario/scenes/incidents/bad-deploy/oracle.ts' --seed demo --json
ancha --local run scenario/scenes/incidents/bad-deploy/scene.yaml \
  --agent 'node scenario/scenes/incidents/bad-deploy/null.ts' --seed demo --json
```

The oracle is a scripted reference, not an AI-model evaluation. It should produce a valid passing run and exit cleanly. The null performs native observations and exits cleanly; its run is valid but fails required outcome checks, so Ancha exits 1. Repeat with other directory names to run the remaining scenes.

The reference repair usually takes about 45 seconds; false alarm about 30 seconds; status request about 150 seconds. Actual completion depends on API/process timing. Human escalation and downtime companions can finish promptly after establishing their outcomes.

## Outcome check contracts

```yaml
state:
  datadog.downtime:
    monitor: $monitor
    remaining_gte: 1m
    duration_lte: 10m
```

At capture, at least one uncanceled downtime must target exactly the referenced Datadog monitor, have `start <= now < end`, retain at least the requested remaining time, and have total `end - start` no larger than the duration bound. Boundaries are inclusive except the active interval's end. A scheduled, expired, canceled, all-monitor or wrong-monitor downtime and a legacy mute do not satisfy this assertion. This is an outcome assertion; it does not infer a causal trace link from a nearby native API call.

```yaml
state:
  pagerduty.incident: { service: $service, first: true }
  status: acknowledged
  assigned_to: [$storage]
```

`assigned_to` is a nonempty array of distinct PagerDuty user references. It requires the exact final assignee set, independent of ordering. Extra bot assignees fail. Reference kind and service ownership are validated when the scene loads. The disk-full policy initially targets only the bot and has no automatic human escalation, so handoff requires agent intervention.

