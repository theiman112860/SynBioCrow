# SynBioCrow V2.0 Alpha90.1.5.8

Unified Specialist Ranking + Pathway Assembly Improvement.

This release builds on Alpha90.1.5.7's self-contained specialist consolidation and shifts the engineering target from route-positive coverage to route composition and ranking. Alpha90.1.5.7 achieved route-positive output for all 20 frozen Golden targets; Alpha90.1.5.8 therefore preserves proposal generation and adds benchmark-blind continuity-aware route assembly/ranking over the unified candidate pool.

The ranking layer uses generic route evidence only: engine/source diversity, biological evidence, route confidence, step continuity, precursor/product identity continuity where available, route completeness, and penalties for unresolved or abstract transitions. It does not receive Golden identities, Golden step labels, case names, or benchmark-derived thresholds. Frozen A routes and the Alpha90.1.5.7 proposal/recovery path remain available for A/B/C comparison, with Golden opened only after route lists are sealed.

The package remains self-contained and retains the embedded inverse-template specialist, RBC2/RetroBioCat adapter, validated Alpha87.11 overlay, bounded Drive discovery, RDKit certification, checkpointing, live progress/elapsed/ETA, Drive-first ALL_OUTPUTS persistence, and rescue download. No predecessor artifact uploads are required.