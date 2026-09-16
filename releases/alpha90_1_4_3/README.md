# SynBioCrow V2.0 Alpha90.1.4.3

Corrected sealed Golden-20 evaluation using the certified Alpha90.1.4.2.3 molecular-identity execution contract and frozen Alpha87.11 engine.

Each Golden target is parsed from its original InChI, assigned an InChIKey, normalized to deterministic canonical isomeric SMILES, and executed only through that identity-preserving representation. Checkpoints are bound to original input, molecular identity, canonical execution target, engine SHA, and identity-manifest SHA. All 20 predictions are sealed before any certified Golden reference access.

This release reports route-positive execution coverage and provenance only. Exact-pathway S@K/MRR remains withheld until a separately validated scorer/bridge contract is connected. Alpha90.2 remains blocked. Packaged verification: 5/5 tests passed; notebook code cells compile.