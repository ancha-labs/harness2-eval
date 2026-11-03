# Results and evidence

[Summary](summary.md) and [results.json](results.json) preserve the measured values. Each model-driven score is copied from its completed run. The two control scores are normalized from the required-check fields of the original Ancha summaries. The Opus episode reused the original baseline; its JSON row points to that same score file. There are 24 distinct score files: 22 model-driven worlds and two controls.

[Selection and frozen plans](selection/README.md) record the protocol. [Editor notes](editor-notes/README.md) are original model responses and may make claims contradicted by the checks. [Short trajectory excerpts](trajectory-excerpts.md) support the polling observation. Raw model event streams and full trajectories are excluded.

## Per-run scores

| Run | Required checks | All required passed |
|---|---:|---|
| [null](runs/null/score.json) | 0/8 | false |
| [oncall-k1-baseline-status-request](runs/oncall-k1-baseline-status-request/score.json) | 7/8 | false |
| [oncall-k1-probe-status-request-agg1](runs/oncall-k1-probe-status-request-agg1/score.json) | 7/8 | false |
| [oncall-k1-probe-status-request-dom1](runs/oncall-k1-probe-status-request-dom1/score.json) | 7/8 | false |
| [oncall-k1-probe-status-request-inv1](runs/oncall-k1-probe-status-request-inv1/score.json) | 7/8 | false |
| [oncall-opus-probe-status-request-agg1](runs/oncall-opus-probe-status-request-agg1/score.json) | 8/8 | true |
| [oncall-opus-probe-status-request-dom1](runs/oncall-opus-probe-status-request-dom1/score.json) | 3/8 | false |
| [oncall-opus-probe-status-request-inv1](runs/oncall-opus-probe-status-request-inv1/score.json) | 8/8 | true |
| [oracle](runs/oracle/score.json) | 8/8 | true |
| [validation-base-bad-deploy-1](runs/validation-base-bad-deploy-1/score.json) | 7/7 | true |
| [validation-base-false-alarm-1](runs/validation-base-false-alarm-1/score.json) | 5/5 | true |
| [validation-base-status-request-1](runs/validation-base-status-request-1/score.json) | 7/8 | false |
| [validation-base-status-request-2](runs/validation-base-status-request-2/score.json) | 7/8 | false |
| [validation-base-status-request-3](runs/validation-base-status-request-3/score.json) | 2/8 | false |
| [validation-opus-selected-bad-deploy-1](runs/validation-opus-selected-bad-deploy-1/score.json) | 7/7 | true |
| [validation-opus-selected-false-alarm-1](runs/validation-opus-selected-false-alarm-1/score.json) | 5/5 | true |
| [validation-opus-selected-status-request-1](runs/validation-opus-selected-status-request-1/score.json) | 8/8 | true |
| [validation-opus-selected-status-request-2](runs/validation-opus-selected-status-request-2/score.json) | 8/8 | true |
| [validation-opus-selected-status-request-3](runs/validation-opus-selected-status-request-3/score.json) | 7/8 | false |
| [validation-selected-bad-deploy-1](runs/validation-selected-bad-deploy-1/score.json) | 7/7 | true |
| [validation-selected-false-alarm-1](runs/validation-selected-false-alarm-1/score.json) | 5/5 | true |
| [validation-selected-status-request-1](runs/validation-selected-status-request-1/score.json) | 7/8 | false |
| [validation-selected-status-request-2](runs/validation-selected-status-request-2/score.json) | 7/8 | false |
| [validation-selected-status-request-3](runs/validation-selected-status-request-3/score.json) | 7/8 | false |
