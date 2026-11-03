# On-call scenario

This directory preserves the example used by the adapter: world definitions, seeds, required checks, starting instructions, SDK tools and scripted control companions. All scene data and executable source are copied unchanged. Runtime ownership databases, connection files, installed packages and generated output are excluded.

- [ancha.yaml](ancha.yaml) is the original example configuration. Its default `agent.ts` command belonged to the example runner; use the explicit `--agent` commands in the [root README](../README.md#reproduce).
- [agent-v1.ts](agent-v1.ts) contains the starting `SYSTEM` prompt. The study extracts that prompt and replaces the original model loop with OpenCode.
- [tools.ts](tools.ts) is the native-SDK tool implementation used in every probe.
- [agent-v2.ts](agent-v2.ts), [agent-v3.ts](agent-v3.ts), [tools-v1.ts](tools-v1.ts) and [tools-v2.ts](tools-v2.ts) retain the other example snapshots; they are not evaluated as separate agents in this study.
- [Incident pack](scenes/incidents/README.md) describes all five copied scenes and their oracle/null companions. The study used [status-request](scenes/incidents/status-request/scene.yaml), [bad-deploy](scenes/incidents/bad-deploy/scene.yaml) and [false-alarm](scenes/incidents/false-alarm/scene.yaml).
- [package.json](package.json) and [package-lock.json](package-lock.json) preserve the original SDK dependency declarations and resolutions. The historical CLI devDependency does not set the globally invoked CLI version.

The fictional users, repository names and `.test` addresses are seed data for local twins. They are not operator identities or service credentials. The `production` branch and deployment are simulated world state. The scene's advisory quality judge remains skipped in the study; only required state/trace checks enter the score.

The status request arrives after 90 simulated seconds. Recovery cannot start before 120 seconds. Time scale remains 1. Repeated status runs use the exact seed `l18-fixed`; held-out checks use `l18-heldout-bad-deploy` and `l18-heldout-false-alarm`, matched across harnesses. These opaque seed bytes are preserved because they determine resource IDs.
