# Methodology

Patrick Liu, Ancha. The study ran on 2026-11-03 UTC using Harness² commit `6868817518876de8fd170c6a8354daca273b6191`, with its tracked implementation unchanged. The paper is [Harness²: Recursive Agent Harnessing for an Open World](https://arxiv.org/abs/2610.14224), arXiv:2610.14224. [Upstream source](https://github.com/google-research/harness2) supplies the recursion, proposer contracts, tree handling and OpenCode substrate.

## Execution

The upstream deterministic demo ran both parallel and sequential `k=2` modes: 2 tasks completed, 0 failed, 28 Python executions and 32 scripted editor calls. A focused suite passed 17 tests and 39 subtests. Scripted editors check the mechanics; they do not establish model-driven discovery. No professional benchmark from the paper was run.

The model-driven experiment used the original on-call v1 system prompt with OpenCode 1.14.18. Ancha CLI 0.1.4 supplied fresh local Slack, GitHub, Datadog and PagerDuty twins for every execution. The experimental MCP stdio bridge wrapped the example's original native-SDK tools. CLI 0.1.5 native endpoints, available through `ancha mcp config`, were not used.

The status-request task requires acknowledging an incident, investigating logs and metrics, repairing a configuration through a pull request, observing deployment and recovery, and replying in the actual human request thread. The human asks at 90 seconds; fault resolution cannot begin before 120 seconds. Time scale is 1. Null failed 0/8 required checks and oracle passed 8/8, with valid trials. The model baseline passed 7/8 in 220.715 seconds and missed the request thread.

Each optimization episode called the actual `harness2.core.recursion.run_parallel(k=1)` with one editor and one rollout worker. General and domain proposal sessions each edited a candidate; the composer received their edits and behavior and produced the fourth executed harness. Editor sessions had 35 steps and a 300-second timeout. The executor had 55 steps and a 540-second process timeout. The bridge tool timeout was 70 seconds; the surrounding Ancha command timeout was 650 seconds.

The substrate has eight component categories: system prompt, guardrails, long-term memory, tool descriptions, subagents, skills, scripts and plugins. This adapter activates always-on prompts and skills. Unsupported executable component edits are rejected. The selected trees retain the unused component placeholders and empty files byte for byte.

## Scoring and selection

Only required deterministic state/trace checks enter the score. The score is the fraction of required checks passed in a valid trial. A full pass requires all such checks. Optional language-model quality judges received no key and were skipped; a skipped judge is not a pass. Authored checks cover explicit operational state and native calls, and do not certify explanation quality.

The editor/composer context contains task text, rendered tool trajectories and the agent's own response. It excludes scene files, seed definitions, control companions, required-check definitions and verdicts. Numerical scoring is kept outside the core refinement context.

After execution, an external selection step chooses the highest-scoring valid executed harness. Ties prefer composition, then baseline. The source uses stable candidate order for any remaining tie. This verdict-guided selection extends the paper's verifier-free protocol. The Sonnet episode selected composition on a 7/8 tie and showed no development-score gain. The Opus episode selected composition on an 8/8 tie with its general proposal.

The paper's professional tasks, executors, provider routes, full editing surface and continual-library experiments differ from this setup. This study tests a single-step adapter integration and frozen selected harnesses. It does not measure professional benchmark performance or learning across a stream of tasks.

## Comparison and freeze policy

Sonnet optimization and its ten frozen validation runs finished before the Opus episode. The [comparison plan](../results/selection/editor-comparison-plan.json) was recorded before any Opus completion and allowed one additional episode. Only the editor model changed. Opus received the exact original baseline evidence, with [hashes](../results/selection/shared-baseline.json), and no Sonnet candidates or validation outcomes. The baseline is counted once in the 22 distinct model-driven world runs.

The [first validation plan](../results/selection/validation/plan.json) froze Sonnet-selected files before three fresh repeats of status-request for baseline and selected, interleaved in a predeclared order. Baseline and selected then each ran bad-deploy and false-alarm once. The [second validation plan](../results/selection/validation-opus/plan.json) froze Opus-selected and ran three fresh status-request trials plus one of each held-out scene. Its baseline controls were the earlier runs, rather than contemporaneous interleaving. No validation outcome caused edits or selection.

Status-request repeats use `l18-fixed`; held-out scenes use `l18-heldout-<task>` with new IDs, matched across harnesses. Those exact seed strings are experimental inputs. Fixed seeds reset world data, while remote model sampling and elapsed time remain variable. There is one completed optimization episode per editor. These samples support an exploratory case study, without a general model ranking.

## Isolation

The launcher uses a separate HOME and XDG state, a no-login Ancha credentials path and local execution. The parent Ancha process has no OpenRouter key, preserving optional-judge skipping. A mode-0600 runtime key file passes the caller's environment key across that process boundary to OpenCode. The bridge receives no model key and rejects non-loopback twin hosts. Twin API credentials are simulated values injected by Ancha.

OpenCode's executor permissions allow world tools and skills and restrict file reads to its workspace. Editor permissions scope reads and edits to the supplied context and output. These controls are application permissions, not an OS sandbox or a network firewall. They do not prove protection against retrieval of public grading material. A simulated `production` ref represents local twin state.

## Models, timing and cost

Executor: `openrouter/anthropic/claude-haiku-5.5`. First editor/composer: `openrouter/anthropic/claude-sonnet-4.6`. Second editor/composer: `openrouter/anthropic/claude-opus-4.8`. OpenCode also used `anthropic/claude-haiku-4.5` for session titles. [Historical pricing](../cost/model-prices.md) records standard and cache rates; [runtime versions](../results/runtime-versions.json) records the installed tools.

The final settled OpenRouter meter was $3.169185647, with two identical final readings. It includes both editor episodes, validation, setup/smoke calls, incidental title calls and two failed editor-launcher attempts. Intermediate meter deltas can lag and cannot be assigned as exact per-call bills. OpenCode step costs are separate estimates. The original $24 stop threshold remains in the metering helper.

The [Sonnet workflow time](../cost/workflow-time.json) is 1192.2781008761376 seconds including baseline. The [Opus follow-up](../cost/opus-workflow-time.json) is 940.6871629580855 seconds and reuses baseline. These intervals exclude setup, failed launcher attempts, smoke calls, research/authoring and frozen validation. Wall time includes model latency and waits.

## Public evidence

The [results index](../results/README.md) contains every distinct model-driven score plus normalized null/oracle controls. The shared baseline has a single full score file. Editor/composer responses are original model output and may disagree with measured outcomes. Short trajectory excerpts support the Slack polling claim. Raw streams, complete trajectories, account state and downloaded paper content are excluded.

Portability edits replace machine paths, expose configuration via environment variables, use the active Python interpreter and relocate the bridge import. The runtime key path replaces the private original key-file location. Frozen harnesses, scene inputs, seeds, required checks, numeric results and unit prices are unchanged. The source incident-pack README's development-checkout instructions were replaced with public relative-path examples. Model identifiers and fictional `.test` identities remain functional experiment data. The original comparison plan's work deadline was omitted; its scientific decisions and timestamp remain.

The original install was editable from the pinned checkout. The public git requirement installs that same revision without copying the upstream repository or the paper. No BibTeX is included; the arXiv title and identifier were verified directly.
