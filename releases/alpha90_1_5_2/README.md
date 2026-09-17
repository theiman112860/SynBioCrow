# SynBioCrow V2.0 Alpha90.1.5.2

RDKit Pre-Import Dependency Repair for the Proposal/Search/Pruning Recovery Engine.

Alpha90.1.5.1 still imported the recovery module before the notebook installed RDKit. Because the module caches its RDKit availability at import time, a later installation left `_HAVE_RDKIT=False` and caused the generic conformance run to fail. Alpha90.1.5.2 fixes the bootstrap order: Drive mount -> RDKit install/smoke test -> SOURCE extraction -> module import -> packaged tests -> generic recovery conformance -> optional Alpha87.11 overlay.

The recovery engine logic remains benchmark-blind and otherwise unchanged. Golden identities, benchmark labels, and benchmark-derived thresholds are not used. Missing RDKit is treated as a dependency/bootstrap issue rather than silently degrading chemical identity normalization.

A regression test verifies that the RDKit bootstrap cell precedes the module-import cell. Packaged verification: 10/10 tests passed and all 7 notebook code cells compile after fresh re-extraction.