# SynBioCrow V2.0 Alpha90.1.2.7

**Benchmark Lineage Reconstruction**

This release changes strategy. It searches the actual Git history of the pinned public BioNavi-NP and RetroPathRL repositories for historical benchmark artifacts and preprocessing lineage instead of rescanning only current files.

- Golden 20 remains frozen at the certified SHA.
- LASER 152 can pass only if a historically source-semantic 152-member artifact is found and its identities form the expected 152-of-159 subset with exactly seven exclusions.
- Building blocks 437 can pass only if a historically source-semantic 437-member artifact is recovered from Git history.
- If historical evidence is absent or ambiguous, the state is `HISTORICAL_PROVENANCE_UNAVAILABLE` and Alpha90.2 stays blocked.
- Alpha87.11 is never run or modified. No benchmark scoring/tuning or count fitting occurs.
