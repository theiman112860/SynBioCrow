# SynBioCrow 2.2 engine consolidation

This branch converts the accumulated development lineage into a maintainable package without changing the sealed 2.1 scientific release.

## Phase 0 — contracts and CI

Implemented:
- core immutable data contracts
- generator adapter registry
- reaction-path union contract
- fail-closed evidence gates
- Candidate / Mature / Certified promotion policy
- protein/CDS and cassette records
- JSON persistence
- engine shell
- hermetic contract tests
- GitHub Actions CI

## Phase 1 — DORAnet

Status: **live bounded adapter implemented**.

- DORAnet 0.5.7a1 optional runtime target
- live enzymatic `generate_network` API binding
- one-generation retro direct-rule probe
- deterministic normalization to `PathwayCandidate`
- rule/version/index provenance
- Candidate-only lifecycle
- explicit refusal of multi-generation search until graph reconstruction is migrated
- hermetic fake-network tests
- real upstream API smoke script

See [DORANET_ADAPTER.md](DORANET_ADAPTER.md).

## Phase 2 — RetroBioCat2

Status: **native bounded MCTS adapter implemented**.

- pinned upstream source lineage at commit `c5f32561...`
- native `MCTS` + `get_expanders(["retrobiocat"])` binding
- bounded search settings for time, iterations, and pathway length
- solved RBC2 pathways normalized into `PathwayCandidate`
- deterministic IDs independent of RBC2 random UUIDs
- reaction score/template/precedent provenance retained
- successful zero-route search represented as bounded no-hit
- installed-but-broken runtime represented as `BackendExecutionError`
- Candidate-only lifecycle
- hermetic native-contract tests and real API smoke script

See [RETROBIOCAT2_ADAPTER.md](RETROBIOCAT2_ADAPTER.md).

## Remaining migration order

1. ~~DORAnet adapter~~
2. ~~RetroBioCat2 adapter~~
3. RetroPath2 / RetroRules adapter
4. reaction-level ensemble union with per-engine provenance
5. Rhea / thermodynamic / enzyme evidence adapters
6. UniProt/RefSeq sequence and cassette pipeline
7. proven BioPKS / RetroTide adapter from the 2.1 lineage
8. CLI, Colab runner, and public execution API

## Frozen scientific policies

- Paper-1/v0.21 baseline stays frozen.
- benchmark-v2 truth stays isolated.
- Candidate / Mature / Certified remain separate.
- no fabricated chemistry, cofactors, enzyme evidence, thermodynamics, kinetics, or sequences.
- Rhea remains evidence/closure infrastructure, not an independent generator.
- specialized backends default to Candidate.
