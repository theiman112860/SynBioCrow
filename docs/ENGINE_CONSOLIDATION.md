# SynBioCrow 2.2 engine consolidation

## Completed

- M0 release preservation and core contracts
- M1 generator adapters
- M2 reaction-level cross-engine ensemble graph
- M3 evidence, exact Rhea, enzyme evidence, thermodynamics
- M4 sequence + construct optimization

### M4 components
- explicit UniProt protein sequence acquisition
- coordinate-bounded NCBI CDS acquisition
- exact CDS -> protein translation validation
- amino-acid-preserving synonymous codon optimization
- deterministic sequence QC
- provenance-only standard regulatory-part references
- verified-sequence requirement before assembly
- promoter/RBS/CDS/terminator cassette assembly
- deterministic multi-gene construct assembly
- Candidate-only lifecycle

See [M4_SEQUENCE_CONSTRUCTS.md](M4_SEQUENCE_CONSTRUCTS.md).

## Next

### M5 — specialized generators
- migrate proven BioPKS / RetroTide 2.1 branch
- integrate specialized edges into the ensemble graph
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
- structured Test outcomes feed ranking and design policy
- backend weighting and route prioritization
- sequence/cassette design learning
- lifecycle remains evidence-gated

### M9 — 2.2 release candidate + paper package
