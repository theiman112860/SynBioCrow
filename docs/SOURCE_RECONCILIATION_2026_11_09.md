# SBC-SOURCE-001 — Uploaded source reconciliation (2026-11-09)

## Goal
Identify the authoritative inputs before changing scientific code.

## Evidence inspected
- `SynBioCrow_V14_SEVEN_ENGINE_SOURCE.zip` (uploaded; 10 entries): `v14_master.py`, `runner.py`, `native_exchange.py`, `native_adapter_v13_3.py`, five engine-install/native notebooks, `README_V14.md`.
- `SynBioCrow_Seven_Engine_Canonical_V2_SOURCE.zip` (uploaded; 3 entries): `SynBioCrow_Seven_Engine_Canonical_V2.ipynb`, `RetroBioCat2_NATIVE_VERIFIED_REFERENCE.ipynb`, `README.md`.
- Separate uploaded `SynBioCrow_Seven_Engine_Canonical_V2.ipynb`.

## Findings
1. V14 is the broader orchestration scaffold. Its own README says it is **not** proof of seven successful native searches.
2. V14 engine slots: `doranet`, `retrobiocat2`, `retrotide`, `traceld_retropath2`, `biopks_retrotide`, `aizynthfinder`, `chemenzyretroplanner`. BioPKS target-specific search is explicitly unresolved; RetroPath2 example uses pinocembrin, not the common acetic acid target; ChemEnzy remote submission is opt-in.
3. V14's `v14_master.py` executes a V13.3 native adapter for three engines and reports structural candidate graph edges. It does not certify stoichiometric closure or genuine seven-engine success.
4. Canonical V2 README identifies an RBC2 native reference at upstream commit `c5f32561b1ed99d0701a6dbb472dc448d6c082e8`, with the other six slots explicitly `NOT_CONFIGURED`.
5. Do **not** count RetroTide and BioPKS/RetroTide as independently proven engines without establishing distinct native generation capabilities.
6. GitHub `develop/2.4` is older than these uploaded Colab snapshots. Neither ZIP should be overwritten by that branch.

## Decision
Preserve V14 as the orchestration **candidate** and Canonical V2 as the RBC2 **reference**. Neither is yet the certified canonical scientific baseline. Do not silently replace V14's RBC2 adapter with the reference until native entrypoints, output schemas, dependencies, and provenance are compared.

## Next bounded task: SBC-SOURCE-002
**Goal:** compare the two RBC2 native entrypoints and define a minimal target-specific smoke contract.

**Context:** V14's V13.3 adapter may have unresolved RBC2 contracts; Canonical V2 contains a later reference runner.

**Constraints:** no changes to frozen 2.3, held-out Galaxy benchmark, or scientific claims; no synthetic reaction evidence; no new unrelated audits; preserve both original ZIPs.

**Done when:** documented interface map (install, native call, target input, output artifact, error status, provenance); one deterministic contract test that can run without pretending to execute RBC2; exact Colab-native validation command identified. Native scientific PASS requires actual Colab evidence, not static inspection.

**Status:** source inventory PASS; scientific runtime validation INCONCLUSIVE.
