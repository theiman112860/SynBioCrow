# SynBioCrow V2.0 Alpha90.1.5.7

Specialist Engine Consolidation & Live Recovery.

This release removes the historical-file-discovery dependency from the specialist recovery path. The SOURCE package itself now contains a native learned/inverse-template specialist engine, a versioned benchmark-blind reaction-class template library, and an explicit RetroBioCat/RBC2 adapter. Specialist dispatch therefore exists on a clean Colab runtime even when no Alpha60/63/RBC2 historical source directories are present.

The embedded learned engine applies fixed generic retrosynthetic reaction-class templates and returns proposals through the common SynBioCrow Route contract. The RBC2 adapter invokes an installed `rbc2` or `retrobiocat` implementation when available, with explicit package/data/API diagnostics when it is not. Missing RBC2 dependencies are never silently interpreted as chemical failure.

Specialists activate only after the ordinary Alpha87.11 backends plus backend-activation recovery return no usable proposals. Their candidates are unioned/deduplicated and passed through the validated Alpha90.1.5 evidence-preserving recovery orchestrator. Golden identities and benchmark outcomes remain post-hoc only.

The notebook is self-contained with the validated engine overlay and reference manifests, bounded Drive discovery, RDKit pre-import certification, per-target checkpointing, live progress/elapsed/ETA, Drive-first ALL_OUTPUTS persistence, and a rescue-download cell. No predecessor artifact uploads are required.

Packaged verification: 6/6 tests passed and all 8 executable notebook cells compile after fresh re-extraction.