# SynBioCrow 2.4.7 — source acquisition and curation layer

## Purpose

2.4.7 turns benchmark source acquisition into an auditable pipeline before any new ranking experiment begins.

It does not claim a finished dataset.

## Source registry

The initial registry defines source roles rather than copying databases into the repository.

Initial source classes:
- Rhea release 142: reaction/evidence annotation;
- BRENDA 2026.1: enzyme/pathway cross-checking;
- primary peer-reviewed literature: preferred pathway-truth provenance.

Database-derived evidence and literature-derived pathway truth remain separate concepts.

## Curation pipeline

`HarvestedPathwayRecord`
→ text/identity normalization
→ frozen-2.3 blacklist check
→ stable target/record IDs
→ family assignment
→ duplicate-target merge
→ mapping-review flags
→ benchmark JSONL

## Deduplication

Duplicate targets are merged only when their family assignments agree.

Conflicting family assignments fail closed because silently choosing one could create split leakage.

Merged records retain all source and literature identifiers.

## Family grouping

Family keys are curated metadata and are converted into stable hashed family IDs.

Examples of useful family concepts include:
- common target scaffold;
- biosynthetic product family;
- shared terminal transformation class;
- closely related homologous products.

Family assignment should be conservative: when uncertain, mark for review rather than creating a false separation.

## Frozen 2.3 blacklist

Targets known to belong to the frozen 2.3 Galaxy holdout are marked
`historical_23_member: true`.

The 2.4.6 split layer already forbids these records from development/validation.

## Mapping review

Every curated record retains a mapping-quality state.

Unreviewed mappings are not silently promoted.

Before benchmark freeze, each included record should have:
- reviewed target structure mapping;
- primary source identifier;
- family assignment review;
- duplicate audit;
- provenance sufficient to reconstruct the curation decision.

## Source snapshot

The next populated benchmark release should freeze:
- source registry;
- harvested metadata;
- curation audit;
- curated public benchmark records;
- external evaluation truth digest.

All are hashed before model training.

## Next checkpoint

2.4.8 should populate an initial **development/validation source tranche** from primary literature and curated databases, explicitly excluding all frozen 2.3 holdout targets.

The untouched evaluation tranche should be assembled and escrowed separately, with only its public metadata and truth digest entering the repository.
