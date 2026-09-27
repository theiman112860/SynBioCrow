# SynBioCrow 2.2 engine consolidation

This branch converts the accumulated development lineage into a maintainable package without changing the sealed 2.1 scientific release.

## Completed foundations

- core immutable data contracts
- generator registry
- fail-closed evidence gates
- Candidate / Mature / Certified promotion policy
- sequence/CDS and cassette records
- persistence helpers
- engine shell
- hermetic tests and GitHub Actions CI

## DORAnet

**Live bounded adapter implemented.**

- one-generation enzymatic retro direct-rule probe
- deterministic `PathwayCandidate` normalization
- rule/version/index provenance
- Candidate-only lifecycle
- multi-generation blocked until graph reconstruction is migrated

## RetroBioCat2

**Native bounded MCTS adapter implemented.**

- native `MCTS` + RetroBioCat expander
- bounded time/iterations/path length
- solved pathways normalized into `PathwayCandidate`
- deterministic IDs independent of RBC2 random UUIDs
- precedent/template/score provenance retained
- successful zero-route search separated from runtime failure

## RetroPath2 / RetroRules

**Live two-stage adapter implemented.**

- current `retropath2_wrapper` Python API for metabolic-scope generation
- explicit RetroRules/sink resource configuration
- RDKit SMILES → InChI source preparation
- current `rp2paths` pathway enumeration
- `out_paths.csv` normalization into Candidate pathways
- return code 11 handled as successful bounded no-hit
- execution/configuration failures surfaced as `BackendExecutionError`
- RetroPath compound identifiers preserved explicitly pending graph identity resolution
- no arbitrary scope reaction is mislabeled as a complete route

## Remaining migration order

1. ~~DORAnet adapter~~
2. ~~RetroBioCat2 adapter~~
3. ~~RetroPath2 / RetroRules adapter~~
4. **reaction-level ensemble graph + per-engine provenance**
5. Rhea evidence / closure adapter
6. thermodynamic adapter
7. enzyme evidence
8. UniProt / RefSeq sequence/CDS pipeline
9. cassette/construct pipeline
10. BioPKS / RetroTide proven 2.1 adapter
11. CLI / Colab runner / public execution API
12. integrated regression against frozen policies

## Frozen scientific policies

- Paper-1/v0.21 baseline stays frozen.
- benchmark-v2 truth stays isolated.
- Candidate / Mature / Certified remain separate.
- no fabricated chemistry, cofactors, enzyme evidence, thermodynamics, kinetics, or sequences.
- Rhea remains evidence/closure infrastructure, not an independent generator.
- specialized backends default to Candidate.
