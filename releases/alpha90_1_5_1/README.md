# SynBioCrow V2.0 Alpha90.1.5.1

RDKit Dependency Bootstrap Repair for the Proposal/Search/Pruning Recovery Engine.

Alpha90.1.5 relied on RDKit for chemically normalized proposal identity and duplicate-aware cross-engine union, but its Colab notebook ran packaged tests before explicitly certifying that RDKit was installed. In runtimes without RDKit, concrete molecules degraded to raw-string identities, causing chemistry-dependent deduplication tests to fail.

Alpha90.1.5.1 fixes that bootstrap defect. The notebook now installs RDKit when needed, smoke-tests canonical molecular identity conversion before running pytest, and the engine module treats missing RDKit as an explicit hard dependency error rather than silently falling back to raw-string chemistry identity. Wildcard species remain abstract non-identities.

The scientific recovery contract is otherwise unchanged: benchmark-blind cross-engine candidate union, chemical-identity deduplication, engine-diversity preservation, pruning telemetry, and a bounded high-evidence rescue lane. No Golden-20 identities or benchmark-derived tuning enter the recovery API.

Packaged verification: 9/9 tests passed and all 7 executable notebook cells compile after fresh re-extraction.