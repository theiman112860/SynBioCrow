# SynBioCrow 2.2 engine consolidation

This branch converts the accumulated development lineage into a maintainable package without changing the sealed 2.1 scientific release.

## Milestone status

### M0 — release preservation and package contracts — COMPLETE
- sealed 2.1 scientific release untouched
- typed core contracts
- Candidate / Mature / Certified lifecycle
- fail-closed evidence semantics
- persistence and CI foundation

### M1 — independent generator adapters — COMPLETE
- DORAnet live bounded adapter
- RetroBioCat2 native bounded MCTS adapter
- RetroPath2 / RetroRules two-stage adapter

### M2 — reaction-level ensemble graph — COMPLETE
- canonical molecular identity for structural SMILES
- conservative source-scoped identity for unresolved tokens
- retrosynthetic reaction hyperedges
- per-edge backend, candidate, rule, and provenance retention
- duplicate transformation provenance merge
- bounded composite route discovery from target to sink
- cross-engine route recovery demonstrated in hermetic tests

This is the first implementation of the central SynBioCrow ensemble hypothesis:
reaction edges from independent generators can be joined into a complete route
that no single generator returned independently.

See [REACTION_GRAPH.md](REACTION_GRAPH.md).

## Next milestones

### M3 — evidence and closure
- RetroPath identifier-to-structure resolution
- Rhea evidence / reaction closure adapter
- thermodynamic adapter
- enzyme evidence adapter
- evidence-aware composite route scoring without lifecycle auto-promotion

### M4 — sequence and construct completion
- UniProt / RefSeq protein/CDS provenance
- cassette/construct pipeline
- preserve source organism vs chassis distinction
- construct Candidate / Mature / Certified contracts

### M5 — specialized generators
- migrate proven BioPKS / RetroTide 2.1 adapter
- retain specialized outputs as Candidate by default
- integrate specialized edges into reaction graph

### M6 — user-facing execution
- public engine execution API
- CLI
- top-to-bottom Colab runner
- bounded lineage-aware persistence/resume
- backend readiness and diagnostics

### M7 — release regression and benchmark
- integrated frozen-policy regression
- reproducibility target panel independent of protected holdout
- performance/provenance report
- 2.2 release candidate

## Backend installation policy

`pip install synbiocrow` installs the SynBioCrow core package, not every
scientific backend.

Scientific generators remain optional because they have large and sometimes
conflicting dependency/runtime requirements:

- **DORAnet**: explicit optional extra currently available as `.[doranet]`.
- **RetroBioCat2**: separate pinned research runtime; not installed by core.
- **RetroPath2 / RetroRules**: separate runtime requiring wrapper, rp2paths,
  RDKit, KNIME, rules, and sink resources; not installed by core.
- **BioPKS / RetroTide**: will remain optional when migrated.

`SynBioCrowEngine.backend_readiness()` provides one programmatic report of
which registered backends are actually available/configured.

## Frozen scientific policies

- Paper-1/v0.21 baseline stays frozen.
- benchmark-v2 truth stays isolated.
- Candidate / Mature / Certified remain separate.
- no fabricated chemistry, cofactors, enzyme evidence, thermodynamics, kinetics, or sequences.
- Rhea remains evidence/closure infrastructure, not an independent generator.
- specialized backends default to Candidate.
