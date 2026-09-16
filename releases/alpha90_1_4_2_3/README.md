# SynBioCrow V2.0 Alpha90.1.4.2.3

Canonical Molecular Identity Execution Contract Repair.

This release freezes an external, identity-preserving execution boundary in front of the frozen Alpha87.11 engine. It accepts SMILES or InChI, derives InChIKey identity, derives deterministic canonical isomeric SMILES, verifies the identity after roundtrip, and preserves both original and execution representations in provenance.

Alpha87.11 source and scientific parameters remain unchanged. No benchmark-specific aliases, chemistry transformations, search tuning, or ranking changes are permitted. This release certifies the repair only and does not rerun Golden-20.

Packaged verification: 5/5 tests passed; all notebook code cells compile.