# SynBioCrow V2.0 Alpha90.1.7

Bidirectional Pathway Closure + Automated Multi-Repair Campaign.

This release combines several previously separate recovery and assembly behaviors into one benchmark-blind automated strategy ladder: ordinary backend generation, specialist zero-pool recovery, parent-preserving recursive assembly, a fixed generic reachable-metabolite frontier, meet-in-the-middle closure scoring, adaptive bounded compute policy, durable per-case Drive checkpointing, automatic resume, heterogeneous telemetry, and post-hoc A/B/C/D/E evaluation.

Branch E grows backward from target-derived routes toward a fixed non-Golden reachable-metabolite frontier. Exact frontier matches close a state and stop further expansion. Non-exact states are prioritized by similarity to the reachable frontier plus a generic complexity term. Parent-preserving dominance filtering remains active, so the validated shallow route set cannot be discarded merely because deeper recursion generated more chemistry.

The adaptive policy is fixed before evaluation and depends only on raw proposal count and generic target complexity. Golden identities, Golden case labels, benchmark outcomes, and benchmark-derived thresholds are not inputs to route generation, frontier selection, closure, or policy decisions.

Every completed case is atomically persisted to Drive and verified before the next case begins. The notebook resumes missing cases only and produces A/B/C/D/E route-quality plus search-efficiency telemetry.

Packaged verification: 6/6 tests passed and all 9 executable notebook code cells compile after fresh generation.