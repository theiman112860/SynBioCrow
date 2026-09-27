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

Unmigrated scientific backends intentionally raise `BackendUnavailableError`.

## Migration order

1. DORAnet adapter
2. RetroBioCat2 adapter
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
