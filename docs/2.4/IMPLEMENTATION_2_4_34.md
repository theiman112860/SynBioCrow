# SynBioCrow 2.4.34 — Leave-One-Target-Out Pairwise Transfer

2.4.33 produced the first consistently encouraging development ranking result. Best max-equivalent rank improved for all four targets, including 99→3 for curcumin, 38→1 for dammaradienol, 433→38–53 for jasmonic acid, and 34→6–13 for MIBK.

However, candidate-level OOF still trains on other labeled candidates from the same target. That is appropriate for diagnostic leakage control but insufficient to establish transfer to a genuinely unseen target.

2.4.34 is therefore a harder generalization test:
- hold out one entire development target,
- train pairwise linear and nonlinear preference models only on the other development targets,
- score the held-out target with zero label exposure from that target,
- evaluate the full maximum-similarity equivalence set,
- compare frozen, linear, nonlinear, and ensemble rankings.

Only if this target-level transfer is reasonably stable should a development ranking policy be considered for freezing before touching validation. Validation/evaluation truth remains sealed.
