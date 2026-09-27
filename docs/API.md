# API

`SynBioCrowRelease(path)` loads a sealed final release directory and immediately validates the frozen policy contract.

Methods:
- `status()` — release engineering and scientific-count summary.
- `policies()` — frozen release policies.
- `specialized_summary()` — BioPKS/RetroTide Candidate summary and abstention reasons.
- `abstention_ledger()` — exact frozen abstention record.
- `provenance()` — source release/hash provenance.
- `verify_files()` — SHA-256 verification for release files recorded in the manifest.

This API is intentionally read-only.
