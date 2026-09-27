# SynBioCrow 2.2 engine consolidation

## Completed

- M0 release preservation and core contracts
- M1 generator adapters
- M2 reaction-level cross-engine ensemble graph
- M3 evidence, exact Rhea, enzyme evidence, thermodynamics
- M4 sequence + construct optimization
- M5 BioPKS / RetroTide specialized-generator integration

### M5 components
- external BioPKS bridge contract retained
- no BioPKS source vendoring
- explicit upstream license acknowledgement
- flexible normalization of BioPKS/RetroTide routes
- architecture-only PKS steps retained as provenance, not fake reactions
- explicit specialist reactions added to the shared ensemble graph
- Candidate-only default
- bounded no-hit distinct from runtime failure
- hermetic bridge/normalization tests

See [M5_BIOPKS_RETROTIDE.md](M5_BIOPKS_RETROTIDE.md).

## Next

### M6 — user-facing execution
- public design API
- CLI
- Colab runner
- backend bootstrap/readiness
- bounded persistence/resume
- unified progress/diagnostics

### M7 — computational Test layer
- integrated regression
- reproducibility panel
- route/construct validation
- backend/runtime matrix
- performance/provenance reports

### M8 — Learn / closed-loop DBTL
- structured Test outcomes feed ranking and design policy
- backend weighting and route prioritization
- sequence/cassette design learning
- lifecycle remains evidence-gated

### M9 — 2.2 release candidate + paper package
