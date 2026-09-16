# SynBioCrow

SynBioCrow is an agentic, evidence-aware orchestration platform for computational biosynthetic pathway design. The project grew from a ChemCrow-inspired concept into a multi-engine DBTL-oriented system that coordinates retrosynthesis, pathway evidence, enzyme/sequence selection, feasibility analysis, provenance, and reproducible decision gates.

## Current development lineage

The active research lineage is **SynBioCrow V2.0 Alpha90.1.2.3**.

Alpha90.1.2.3 is intentionally a **canonical benchmark-artifact acquisition and certification repair**, not Alpha90.2. Alpha90.2 remains blocked until the frozen external-benchmark prerequisites are independently certified:

- LASER benchmark: exactly 152 canonical projects
- Golden benchmark: exactly 20 canonical pathways
- extended building-block library: exactly 437 canonical members

The Alpha87.11/Alpha90 scientific contracts are frozen for this certification work. The benchmark is not used for parameter tuning, publication prose is not used to reconstruct missing benchmark data, and expensive frozen campaigns are not rerun when their artifacts already exist.

## Architecture direction

SynBioCrow is best understood as an orchestration and evidence layer rather than a single retrosynthesis algorithm. The long-term architecture is designed to incorporate established tools where they are strongest, including rule/template, database/similarity, learned, and hybrid retrosynthesis engines, plus downstream enzyme, sequence, metabolic, process, and DBTL components.

A key roadmap item for Alpha91 is direct **Galaxy-SynBioCAD integration**. Galaxy-SynBioCAD should be treated as an established capability provider that SynBioCrow can invoke and reconcile with other engines, rather than only as a competitor. Related systems under active capability/architecture comparison include Galaxy-SynBioCAD, BioNavi-NP, RetroPathRL, RetroPath2.0, and RetroBioCat.

## Repository migration status

This repository originally contained early SynBioCrow notebooks and prototypes. Those files are being preserved while the modern V2.0 lineage is migrated in a controlled branch-based refresh.

The `alpha90-refresh` branch contains the currently available Alpha90.1.2.3 certification source and documentation. It does **not** claim to be the complete accumulated Alpha73-90 engine source; the current Alpha90.1.2.3 package is a narrow repair module. The complete engine will be migrated only from verified packaged source artifacts so that historical functionality is not silently lost.

## Current release material

See `releases/alpha90_1_2_3/` for the exact Alpha90.1.2.3 source currently staged for migration, and `docs/CURRENT_STATUS.md` for the migration and certification state.

## Reproducibility policy

Generated campaign outputs, large benchmark corpora, caches, environment directories, and large `ALL_OUTPUTS.zip` bundles should not be committed directly to Git. Small manifests, provenance records, hashes, source code, notebooks, tests, and documentation belong in the repository; large artifacts should be referenced by immutable hashes and external provenance.

## Historical material

The original notebooks and prototype code currently remain at repository root while the migration is staged. They will be moved under `legacy/` only after the modern engine source has been fully reconstructed and reviewed on the migration branch.
