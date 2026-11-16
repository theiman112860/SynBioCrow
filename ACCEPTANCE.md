# SynBioCrow Core v1.0 acceptance

The core is CERTIFIED only when **all seven** engines have independently evidenced:
1. Pinned installation/restore manifests with reproducibility evidence.
2. Genuine engine-native, target-specific execution within supported chemistry, without swallowed internal failures.
3. Validated native output extraction with full provenance, hashes and direction; PKS designs remain typed designs.

Cross-engine requirements:
4. Reaction normalization and deduplication retain source references, reactant/product direction and reaction identities.
5. Multi-reactant pathway search requires all substrates and explicit seed provenance.
6. At least one traceable potential pathway is reproducible from reaction IDs. No biochemical certification is inferred.

Allowed gate values: PASS_REPRODUCED, PASS_HISTORICAL_EVIDENCE, FAIL, NOT_VERIFIED. Historical evidence alone does not qualify for certification. Missing evidence is NOT_VERIFIED, never PASS.

Run one bounded certification campaign: reuse pinned environments and archived evidence; test only changed or missing gates. For a failed gate, open one isolated repair task and update FAILURE_LEDGER.md. Never restart all seven engines without a documented cross-cutting reason.

Product development may continue while core certification is pending. Certification is not a prerequisite for independent features.
