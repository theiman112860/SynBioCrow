# SynBioCrow V2.0 Alpha90.1.6.2

Evidence-Guided Precursor Frontier Selection.

Builds on Alpha90.1.6.1 parent-preserving recursive assembly. Before recursive expansion, unresolved precursors are ranked with fixed benchmark-blind biochemical evidence: Rhea/EC/enzymatic provenance, biological provenance, molecular accessibility/resolvability, heteroatom signal, patent-only signal, and uncertainty. The highest-evidence frontier states are expanded first while cycle control, parent preservation, intrinsic dominance filtering, specialist recovery, and durable per-case Drive checkpointing remain unchanged.

Golden identities, Golden case labels, benchmark outcomes, and benchmark-derived thresholds are not inputs to frontier scoring. Golden remains post-hoc evaluation only.

The recursive telemetry records frontier score and component features for every attempted precursor, allowing direct comparison of pathway quality and search efficiency against the Alpha90.1.6.1 baseline.

Packaged verification: 9/9 tests passed and all 9 executable notebook code cells compile after fresh generation.