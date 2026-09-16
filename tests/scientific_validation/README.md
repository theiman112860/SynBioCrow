# Scientific validation tests

This directory is reserved for expensive, explicitly invoked SynBioCrow scientific validation campaigns.

Normal GitHub CI MUST NOT execute LASER 152, Golden 20, the 437-building-block campaign, full retrosynthesis campaigns, large external-engine searches, or other long-running scientific evaluations.

Scientific validation must use frozen inputs with provenance and hashes, record the exact SynBioCrow engine/version and dependency environment, preserve raw outputs, and distinguish validation from parameter tuning.

For the Alpha90 lineage, Alpha90.2 remains prohibited until the independent canonical-artifact certification gates for LASER 152, Golden 20, and the 437-member building-block library all pass. External benchmark results must not be used to tune the frozen Alpha87.11/Alpha90 engine.
