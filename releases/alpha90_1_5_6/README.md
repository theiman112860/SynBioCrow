# SynBioCrow V2.0 Alpha90.1.5.6

Learned + Enzymatic Zero-Pool Proposal Recovery.

This engine release extends the Alpha90.1.5 recovery stack with benchmark-blind specialist dispatch for targets that still have zero usable proposals after the normal Alpha87.11 backends and Alpha90.1.5.5 backend-activation recovery complete. It activates two accumulated specialist capability families when available: learned/inverse-template proposal modules and RetroBioCat/RBC2 enzymatic proposal modules.

Specialist discovery is bounded to known historical SynBioCrow/resource roots and an installed `rbc2` package. Historical modules must expose a supported proposal entrypoint (`generate_routes`, `propose_routes`, `predict_routes`, `search_routes`, `retrosynthesize`, `run_retro`, or `run_retrosynthesis`). Incompatible old APIs are recorded explicitly as `DISCOVERED_INCOMPATIBLE` rather than silently ignored. Negative zero-route caches are treated as evidence only and never suppress specialist dispatch.

Specialist outputs are normalized into the common Alpha87.11 Route contract, unioned and deduplicated, then passed through the validated Alpha90.1.5 evidence-preserving recovery orchestrator. Golden identities and benchmark outcomes are not available to specialist selection or dispatch; the frozen Golden reference is used only after route lists are frozen for post-hoc evaluation.

The notebook is self-contained with embedded engine overlay/manifests, bounded Drive discovery, RDKit pre-import certification, per-target checkpointing, live progress/elapsed/ETA, Drive-first ALL_OUTPUTS persistence, and a rescue-download cell. No predecessor upload prompts are required.

Packaged verification: 5/5 tests passed and all 8 executable notebook code cells compile after fresh re-extraction.