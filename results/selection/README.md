# Selection and frozen validation

- [Sonnet selection](oncall-k1/selection.json): composition selected on a tie, with 7/8 required checks.
- [Opus selection](oncall-opus/selection.json): composition selected on a tie with the general candidate, with 8/8 required checks.
- [Tie rule](tie-rule.md): declared before candidate selection and implemented by the adapter.
- [Editor comparison plan](editor-comparison-plan.json): one additional episode with the same starting evidence and executor.
- [Sonnet validation plan](validation/plan.json): ten interleaved baseline/selected checks and frozen selected-file hashes.
- [Opus validation plan](validation-opus/plan.json): five selected-only checks, with earlier baseline controls reused.
- [Shared baseline](shared-baseline.json): original artifact hashes and the published baseline score location.

Frozen file hashes are unchanged and can be checked against [Sonnet-selected](../../harnesses/sonnet-selected) and [Opus-selected](../../harnesses/opus-selected). Fixed seed strings are opaque experimental inputs and are preserved verbatim. No validation result entered optimization or selection. The comparison plan is an experiment protocol. Its execution deadline has been omitted from the public copy.
