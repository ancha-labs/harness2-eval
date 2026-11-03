# Experiment adapter

The adapter calls Harness² at the revision pinned in [requirements.txt](requirements.txt). Its custom `BinaryProposer` launches the installed OpenCode npm binary instead of a Bun source checkout. Core proposal and composition logic are unchanged.

| File | Role |
|---|---|
| [adapter.py](adapter.py) | Build the base harness from `agent-v1.ts`; launch fresh Ancha worlds; render execution evidence; call `run_parallel(k=1)`; select externally by required checks. |
| [probe-agent.py](probe-agent.py) | Materialize prompts/skills, write a scoped OpenCode configuration and launch its executor against the bridge. |
| [compare.py](compare.py) | Freeze selected hashes, declare the interleaved or selected-only schedule, and check that hashes remain unchanged. |
| [lab_env.py](lab_env.py) | Create an isolated HOME/XDG environment, omit inherited account credentials and record command metadata. |
| [cost.py](cost.py) | Read allowlisted OpenRouter meter fields before/after batches and enforce the original $24 stop threshold. |
| [summarize.py](summarize.py) | Rebuild tables from a complete new run's raw receipt layout, control summaries, meter and upstream demo/test outputs. |
| [prepare.py](prepare.py) | Copy an optional external scenario export and download research/pricing inputs into the runtime receipt directory. The checked-in scenario is already prepared. |
| [settings.py](settings.py) | Resolve repository, runtime, scenario and credential-file paths. |

The [root README](../README.md#reproduce) gives the recorded sequence. Outputs from new experiments go to `.work/receipts/`, separate from the published [results](../results/README.md). `summarize.py` expects the original full receipt layout, including `demo/demo.json` and `upstream-tests.log`; it is not a converter for the compact public evidence. Capture those upstream inputs before invoking it. `prepare.py` is optional and downloads paper material only into ignored runtime output.

## Configuration

Run with Python 3.12 or 3.13 after installing the pinned requirement. The original installation was an editable checkout; the git requirement resolves the same exact revision for portability. Node 24 must be on PATH, with global `ancha` and `opencode` executables installed. The default Python executor is the interpreter running the adapter.

| Environment variable | Default or use |
|---|---|
| `OPENROUTER_API_KEY` | Required for `lab_env.py --paid`; supplied by the caller's environment. |
| `H2_WORKDIR` | Repository `.work/`; generated HOME, XDG, npm cache and probe workspaces. |
| `H2_RECEIPTS` | `.work/receipts/`; raw outputs for new experiments. |
| `H2_SCENARIO` | Repository `scenario/`. |
| `H2_SCENARIO_SOURCE` | The same scenario directory; optionally copy another example export in `prepare.py`. |
| `H2_KEY_FILE` | `.work/home/openrouter-key`; private runtime file used across Ancha's key-free parent and executor boundary. |
| `H2_EDITOR_MODEL` | `openrouter/anthropic/claude-sonnet-4.6`; use the recorded Opus ID for the second episode. |
| `H2_EXECUTOR_MODEL` | `openrouter/anthropic/claude-haiku-5.5`; changing this defines a different experiment. |
| `DOCKER_CONFIG` | Caller value, otherwise the caller's standard `.docker` directory, matching the original launcher's setting. |

Path overrides should be absolute. The launcher forwards `H2_*` settings; the adapter explicitly passes its path and executor overrides across Ancha’s filtered child environment. It builds PATH from the active environment, prefixed with the repository virtualenv and isolated npm prefix. It does not forward provider credentials except the explicitly requested OpenRouter key. Keep keys out of positional arguments and command metadata.

With `--paid`, the launcher creates or replaces the runtime key file with mode 0600. Ancha itself receives no model key, so optional quality judges remain skipped. The probe reads this file into its OpenCode environment. The MCP bridge receives an empty model key and only uses the local twin connections. Remove the runtime credential after the experiment:

```sh
rm -f .work/home/openrouter-key
```

If `H2_KEY_FILE` was overridden, remove that file instead. Runtime output and credentials are ignored by Git. No key is embedded in source or recorded evidence.

Each executed tree has eight component categories: system prompt, guardrails, long-term memory, tool descriptions, subagents, skills, scripts and plugins. This experiment activates always-on text and skills only. Unsupported executable script/plugin/subagent edits are rejected. The four model-driven executions per episode are baseline, general probe, domain probe and composition; the second episode reuses baseline evidence.

Portability edits replace machine paths with these settings, move the bridge import to the published scenario directory and replace the private machine key location with the caller-supplied key. Seeds, budgets, task parsing, scoring, selection and model defaults retain the recorded behavior.
