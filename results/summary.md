# Measured results

Development: fractions of required checks passed, with the same 7/8 baseline for both episodes.

| Editor | General probe | Domain probe | Composed run |
|---|---:|---:|---:|
| Sonnet 4.6 | 7/8 | 7/8 | 7/8 |
| Opus 4.8 | 8/8 | 3/8 | 8/8 |

Frozen validation: full passes per attempt.

| Harness | status-request | bad-deploy | false-alarm |
|---|---:|---:|---:|
| Baseline | 0/3 | 1/1 | 1/1 |
| Sonnet-selected | 0/3 | 1/1 | 1/1 |
| Opus-selected | 2/3 | 1/1 | 1/1 |

The 22 unique model-driven runs and two controls are indexed in [per-run scores](README.md). No invalid trials occurred. One repeated Opus run answered the thread but omitted the metric query.

## Upstream verification

The deterministic upstream demo completed 2 tasks with 0 failures, 28 Python executions and 32 scripted editor calls, in parallel and sequential `k=2` modes. The focused upstream suite passed 17 tests and 39 subtests in 20.32 seconds. Those checks were performed during the original study; the compact public evidence records their aggregates in [results.json](results.json).

## Controls

| Agent | Required checks | Valid | All required passed |
|---|---:|---|---|
| null | 0/8 | True | False |
| oracle | 8/8 | True | True |

## Harness² k=1 development task: Sonnet 4.6

| Run | Required checks | All required passed | Wall s | Failed checks |
|---|---:|---|---:|---|
| baseline-status-request | 7/8 | False | 220.715 | answered_request_thread |
| probe-status-request-agg1 | 7/8 | False | 205.389 | answered_request_thread |
| probe-status-request-dom1 | 7/8 | False | 204.195 | answered_request_thread |
| probe-status-request-inv1 | 7/8 | False | 315.452 | investigated |

## Harness² k=1 development task: Opus 4.8

| Run | Required checks | All required passed | Wall s | Failed checks |
|---|---:|---|---:|---|
| baseline-status-request | 7/8 | False | 220.715 | answered_request_thread |
| probe-status-request-agg1 | 8/8 | True | 211.501 | none |
| probe-status-request-dom1 | 3/8 | False | 188.223 | investigated, deployed_repair, fault_recovered, healthy_monitor, incident_recovered |
| probe-status-request-inv1 | 8/8 | True | 255.401 | none |

The baseline in this table is the exact reused original artifact; it is not a new execution. See [shared baseline](selection/shared-baseline.json).

## Frozen-harness validation

| Task | Phase | Harness | Full passes / trials | Required checks | Mean wall s | Failed checks |
|---|---|---|---|---:|---:|---|
| bad-deploy | validation | base | 1/1 | 7/7 | 82.942 | none |
| bad-deploy | validation | selected | 1/1 | 7/7 | 97.090 | none |
| bad-deploy | validation-opus | selected | 1/1 | 7/7 | 161.165 | none |
| false-alarm | validation | base | 1/1 | 5/5 | 80.497 | none |
| false-alarm | validation | selected | 1/1 | 5/5 | 49.028 | none |
| false-alarm | validation-opus | selected | 1/1 | 5/5 | 82.516 | none |
| status-request | validation | base | 0/3 | 16/24 | 176.108 | answered_request_thread, deployed_repair, fault_recovered, healthy_monitor, incident_recovered, investigated |
| status-request | validation | selected | 0/3 | 21/24 | 220.355 | answered_request_thread |
| status-request | validation-opus | selected | 2/3 | 23/24 | 250.024 | investigated |

OpenRouter initial usage: $0.000000000; latest usage: $3.169185647; difference: $3.169185647. Metering as of 2026-11-03T05:44:00.172340+00:00. Endpoint updates can lag.

OpenCode event cost sums are estimates and omit incidental title calls. The final settled key meter includes failed launchers, smoke calls, optimization and validation.
