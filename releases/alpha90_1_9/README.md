# SynBioCrow V2.0 Alpha90.1.9

Unified Reaction Knowledge Warehouse + Automated Gap-Repair Engine.

This release consolidates reaction knowledge acquisition, normalization, deduplication, provenance/confidence scoring, gap repair, bidirectional closure, and pathway graph reconciliation into one benchmark-blind automated campaign. The warehouse can ingest bounded local/Drive corpora from existing SynBioCrow/Rhea/patent caches and source-specific exports such as EnzymeMap, MetaNetX, RetroRules, ORD subsets, BKMS-derived files, and related reaction datasets.

Network acquisition is optional and capped. Large corpora are cached and may be supplied locally rather than blindly downloaded. Reaction indexing and graph bridges use exact canonical molecular identity. Biological and synthetic evidence remain distinct in provenance.

For each target, the campaign preserves the validated A/B/C/E/F branches and adds G: warehouse-assisted gap repair followed by a second graph-reconciliation pass. Existing protected routes remain available; warehouse edges are additive. Golden identities and benchmark outcomes are post-hoc only.

Durable per-case Drive checkpointing, automatic resume, union-schema telemetry, Drive-first ALL_OUTPUTS persistence, and rescue download remain enabled.

Packaged verification: 5/5 tests passed, all 9 executable notebook cells compile, and a fresh-extraction reaction-deduplication smoke test passed.
