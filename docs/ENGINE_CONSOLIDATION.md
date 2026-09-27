# SynBioCrow 2.2 engine consolidation

## Completed milestones

### M0 — release preservation and core contracts — COMPLETE
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
- conservative source-scoped unresolved identities
- reaction hyperedges with per-engine provenance
- bounded composite route discovery

### M3 — evidence and closure — IN PROGRESS
Implemented:
- RetroPath identifier→structure remapping contract
- stoichiometric atom/formal-charge closure
- Rhea participant/evidence client
- exact-Rhea confirmation policy
- reviewed UniProt evidence only for exact Rhea mappings
- route-level evidence aggregation
- no automatic lifecycle promotion

Pending:
- quantitative thermodynamics
- richer exact reaction-direction/stoichiometry matching
- enzyme family/context layer
- evidence-aware ranking

See [EVIDENCE_LAYER.md](EVIDENCE_LAYER.md).

## Future milestones

### M4 — sequence + construct design optimization
- evidence-backed enzyme sequence selection
- verified CDS acquisition
- amino-acid/CDS consistency
- nucleotide optimization while preserving protein sequence by default
- chassis-aware codon optimization
- promoter/RBS/terminator selection and cassette assembly
- construct QC and provenance

### M5 — specialized generators
- migrate proven BioPKS / RetroTide branch
- integrate specialized edges into ensemble graph
- keep specialized outputs Candidate by default

### M6 — user-facing execution
- public engine API
- CLI
- Colab runner
- backend bootstrap/readiness
- persistence/resume

### M7 — computational Test layer
- integrated regression
- reproducibility panel
- route/construct validation
- performance/provenance reports

### M8 — Learn / closed-loop DBTL
- consume structured Test outcomes
- update ranking and backend weighting
- update route/design priorities
- preserve evidence-gated lifecycle policy

### M9 — 2.2 release candidate + paper/reproducibility package

## Frozen scientific policies

- Paper-1/v0.21 baseline stays frozen.
- benchmark-v2 truth stays isolated.
- Candidate / Mature / Certified remain separate.
- no fabricated chemistry, cofactors, enzyme evidence, thermodynamics, kinetics, or sequences.
- Rhea remains evidence/closure infrastructure, not an independent generator.
- specialized backends default to Candidate.
