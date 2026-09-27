# SynBioCrow 2.2 engine consolidation

## Completed

- M0 release preservation and core contracts
- M1 generator adapters
- M2 reaction-level cross-engine ensemble graph
- M3 evidence and thermodynamics
- M4 sequence + construct optimization
- M5 BioPKS / RetroTide specialized integration
- M6 unified execution API / CLI / Colab / resume

### M6 components
- public `DesignRequest` / `DesignResult`
- top-level `design(...)` execution API
- deterministic request-derived run IDs
- backend readiness and per-backend status
- bounded multi-backend Candidate generation
- shared graph construction
- bounded target-to-sink route reconstruction
- atomic JSON stage persistence
- checkpoint resume without rerunning completed Candidate generation
- `synbiocrow readiness` CLI
- `synbiocrow design` CLI
- backend bootstrap advice
- Google Colab runner with Drive persistence and rescue ZIP

See [M6_EXECUTION.md](M6_EXECUTION.md).

## Next

### M7 — computational Test layer
- integrated frozen-policy regression
- reproducibility target panel
- backend/runtime matrix
- deterministic serialization checks
- route/construct validation
- performance/provenance report
- CI gates for 2.2 release readiness

### M8 — Learn / closed-loop DBTL
- structured Test outcomes feed ranking and design policy
- backend weighting and route prioritization
- sequence/cassette design learning
- lifecycle remains evidence-gated

### M9 — 2.2 release candidate + paper package
