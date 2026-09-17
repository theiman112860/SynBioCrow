# SynBioCrow V2.0 Alpha90.1.5

Proposal/Search/Pruning Recovery Engine.

This is the first post-audit engine-improvement release. It adds a benchmark-blind recovery layer at the orchestration boundary after backend proposal generation and before destructive beam pruning/ranking. The layer performs cross-engine candidate union, chemically normalized identity deduplication, optional engine-diversity preservation, explicit pruning telemetry, and a bounded high-evidence rescue lane for proposals that would otherwise be removed by score/beam/per-engine-cap pruning.

The rescue lane is generic and fixed independently of Golden-20: at most 20% of the configured beam and no more than six proposals. Candidate recovery score combines native engine score, pre-existing evidence strength, and source diversity. Golden identities, benchmark labels, missing-step tables, aliases, and benchmark-derived thresholds are not accepted by the API.

The release also provides a non-destructive overlay builder for an exact frozen Alpha87.11 SOURCE ZIP. The original frozen ZIP is copied and hashed into the overlay bundle and is never edited in place. Alpha90.2 remains separately gated.

Packaged verification: 8/8 tests passed and all 7 executable notebook code cells compile after fresh re-extraction.