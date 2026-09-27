# SynBioCrow 2.2 engine consolidation

## Completed

- M0 release preservation and core contracts
- M1 generator adapters
- M2 reaction-level cross-engine ensemble graph
- M3 evidence and thermodynamics
- M4 sequence + construct optimization
- M5 BioPKS / RetroTide specialized integration
- M6 unified execution API / CLI / Colab / resume
- M7 computational Test / reproducibility / release-readiness
- M8 Learn / closed-loop DBTL

### M8 components
- structured Test outcome schema
- versioned learning policy
- bounded backend-weight updates
- bounded route-feature updates
- bounded construct-feature updates
- deterministic route/construct ranking
- deterministic audit digest
- append-only JSONL learning audit
- `synbiocrow learn` CLI
- explicit lifecycle_effect=NONE contract
- no automatic lifecycle promotion

See [M8_LEARN_DBTL.md](M8_LEARN_DBTL.md).

## Next: M9 — 2.2 release candidate + paper package

- require green full CI
- finalize README and architecture docs
- generate 2.2 release manifest
- hash release files
- build source/reproducibility archive
- create release candidate tag/package
- prepare paper Methods / Results / reproducibility material
- merge consolidation PR only after release gate passes
