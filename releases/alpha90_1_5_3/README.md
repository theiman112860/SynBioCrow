# SynBioCrow V2.0 Alpha90.1.5.3

Live Proposal-Stream Integration & Frozen A/B Evaluation.

This release integrates the Alpha90.1.5 recovery layer at the real Alpha87.11 backend-candidate/orchestration boundary. For each target, all enabled backends execute once to create a single raw candidate pool. That exact pool is then forked into two deterministic branches: A uses the frozen Alpha87.11 orchestrator unchanged; B uses the generic Alpha90.1.5.3 evidence-preserving recovery orchestrator. This single-generation design avoids chemistry reruns between A and B and isolates the effect of orchestration/recovery.

The recovery branch is benchmark-blind. Golden identities, Golden route labels, benchmark success/failure information, and benchmark-derived thresholds are not available to branch B. The corrected Golden reference is opened only after both route lists are frozen, for post-hoc exact-path and ordered-LCS evaluation.

The notebook uses bounded Drive discovery, RDKit pre-import certification, per-target checkpointing, existing route/resource caches where available, live progress/elapsed/ETA, Drive-first ALL_OUTPUTS persistence, and a standalone rescue-download cell.

Packaged verification: 3/3 integration tests passed and all 8 executable notebook code cells compile after fresh re-extraction.