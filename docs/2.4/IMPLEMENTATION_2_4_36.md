# SynBioCrow 2.4.36 — Development Ranking Policy Freeze Candidate

2.4.35 produced the first target-level transfer-stable representation. After converting each evidence feature to a within-target percentile, the leave-one-target-out linear pairwise ranker improved both best-equivalent and median-equivalent rank for all four development targets:

- curcumin: best 99→82, median 245→147
- dammaradienol: best 38→12, median 280→128
- jasmonic acid: best 433→107, median 1701→799
- MIBK: best 34→16, median 94→70

The nonlinear model was less stable, particularly on MIBK, so 2.4.36 selects the simpler target-relative linear pairwise representation as the development policy candidate.

This stage:
- freezes feature order and normalization semantics,
- fits deterministic development-only pairwise logistic coefficients,
- records a SHA-256 for the policy JSON,
- reproduces target-level LOTO development evidence,
- keeps validation and evaluation truth sealed.

Production ranking is not changed yet. The next scientific step after verifying this package is a single locked validation exposure using the frozen policy.
