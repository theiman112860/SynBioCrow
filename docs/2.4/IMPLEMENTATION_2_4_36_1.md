# SynBioCrow 2.4.36.1 — Deterministic Within-Target Ranking Policy Freeze Candidate

The first 2.4.36 freeze package was internally hash-valid, but its leave-one-target-out replay did not exactly reproduce 2.4.35 because pair training still depended on stochastic pair sampling.

A second methodological issue was also identified: the 2.4.35/2.4.36 training pool could form pairwise labels between candidates from different targets. Corrected internal-anchor similarity is target-specific, so cross-target similarity comparisons are not a defensible preference label.

2.4.36.1 fixes both issues:
- all preference pairs are generated within target only;
- zero-gap pairs are excluded;
- deterministic fixed similarity-order offsets are used instead of random sampling;
- each target is percentile-normalized from unlabeled evidence values before pair construction;
- within-target pair sets are pooled only after labels are formed;
- the final development-only coefficients and policy JSON are hashed.

Validation and evaluation truth remain sealed. Production ranking remains unchanged. Validation must not be exposed unless this deterministic LOTO replay is stable and improves all development targets sufficiently to justify the locked policy.
