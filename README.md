# SynBioCrow

SynBioCrow is an **agentic, evidence-aware orchestration platform for computational biosynthetic pathway design and cell-factory engineering**. The project began as a ChemCrow-inspired concept and has evolved into a multi-engine system that coordinates retrosynthesis, biochemical evidence, enzyme/sequence selection, pathway feasibility, provenance, evaluation firewalls, and reproducible DBTL-style decision workflows.

## What SynBioCrow does

The current V2 architecture is designed to orchestrate rather than replace established biosynthesis tools. Its accumulated capabilities include:

- **Multi-engine retrosynthesis orchestration** across rule/template, database/similarity, learned/inverse-template, patent-hybrid, Rhea/known-reaction, and external-engine pathways.
- **Evidence-aware route reconciliation** that preserves provenance across engines and can combine route evidence rather than treating a single search engine as authoritative.
- **Canonical molecular-identity handling** using identity-preserving normalization so equivalent SMILES/InChI serializations execute through one deterministic internal representation.
- **Enzyme and sequence candidate generation/selection**, including downstream evidence enrichment and protein-candidate workflows.
- **Knowledge integration** from biochemical resources such as Rhea, UniProt, PubChem, ChEBI, PubMed, KEGG/MetaCyc-style pathway context, and other external evidence sources where available.
- **Feasibility and process analysis**, including metabolic/process constraints, kinetic/enzyme-capacity analyses, calibration experiments, and DBTL-oriented design decisions.
- **Benchmark/evaluation firewalls** that separate frozen route generation from reference reconstruction, scoring, post-hoc interpretation, and claim authorization.
- **Checkpointed, reproducible execution** with bounded artifact discovery, immutable hashes/manifests, resumable Colab workflows, automated tests, progress/elapsed/ETA reporting, Drive-first persistence, and rescue download support.
- **Paper-oriented evidence ledgers** that distinguish primary results, diagnostics, prospective tests, post-hoc interpretation, and excluded/unsupported claims.

## Current development lineage

The active research lineage is **SynBioCrow V2.0 Alpha90.1.4.x**. The most recent packaged repair is **Alpha90.1.4.3.2.3.2**, a self-contained bootstrap for native Golden compound-node pathway reconstruction.

The scientific engine used for the current frozen evaluation lineage remains **Alpha87.11**. Later Alpha90.x work has focused primarily on execution-contract repair, benchmark provenance, representation invariance, reference reconstruction, and evaluation integrity rather than benchmark-driven tuning of the frozen engine.

## Current Golden-20 evaluation status

A corrected, identity-normalized Golden-20 execution produced **routes for 18 of 20 targets (90% route-positive coverage)** from the frozen engine. That is a route-generation coverage result, not yet a final exact-pathway claim.

Subsequent work uncovered several evaluation-pipeline representation issues, including target serialization sensitivity and ambiguity in how the Golden primary artifact encodes ordered molecular identities. Those issues are being repaired before any exact-pathway metric is treated as publication-grade. In particular, the current lineage reconstructs Golden pathways from the **actual native compound nodes and certified graph-edge semantics**, rather than inferring compound identity from reaction-node IDs.

This repository therefore intentionally distinguishes:

- **validated route-generation coverage**;
- **frozen prediction artifacts and seals**;
- **reference-bridge reconstruction**;
- **diagnostic concordance analyses**; and
- **publication-authorized exact-pathway claims**.

A result is not promoted from one category to another merely because doing so would improve benchmark performance.

## Benchmark provenance policy

Alpha90.1.3 froze the benchmark-provenance policy after extensive canonical-artifact recovery work:

- **Golden-20** is retained as a certified canonical external benchmark.
- Historical **LASER-152** canonical membership remains unavailable from the public lineage examined.
- The historical **437-building-block** canonical membership likewise remains unavailable.
- Reproducible public substitute datasets may be analyzed only when clearly labeled as noncanonical substitutes.
- **Alpha90.2 remains blocked under the original all-three-canonical-artifact rule**; that rule has not been silently relaxed.

## Architecture direction

SynBioCrow should be understood as an **agentic orchestration and evidence layer**, not simply as another standalone retrosynthesis algorithm. The goal is to invoke specialized tools where they are strongest, reconcile their outputs, track the evidence behind decisions, and carry candidate pathways into enzyme/sequence, feasibility, process, and DBTL analysis.

A major Alpha91 roadmap item is direct **Galaxy-SynBioCAD integration**. Galaxy-SynBioCAD is especially important because the original SynBioCrow concept envisioned using established SynBioCAD capabilities as part of a broader agentic workflow. The intended framing is therefore complementary: SynBioCrow can call and reconcile Galaxy-SynBioCAD capabilities alongside other engines rather than positioning itself only as a competitor.

Systems included in the Paper-1 capability/architecture comparison include:

- Galaxy-SynBioCAD
- BioNavi-NP
- RetroPathRL
- RetroPath2.0
- RetroBioCat
- SynBioCrow

## Reproducibility and scientific integrity

The V2 lineage uses several safeguards that are now treated as architectural requirements:

- frozen scientific-engine artifacts for benchmark evaluation;
- prediction sealing before reference access;
- immutable SHA-256 provenance for key artifacts;
- performance-blind reference qualification;
- canonical molecular-identity contracts;
- explicit claim ledgers;
- no benchmark-specific chemistry tuning during evaluation repair;
- no silent substitution of noncanonical artifacts for historical canonical benchmarks;
- exact packaged-source tests before release;
- bounded Google Drive discovery rather than unbounded artifact scans; and
- preservation of expensive frozen campaign artifacts instead of rerunning them unnecessarily.

## Repository migration status

This GitHub repository originally contained early SynBioCrow notebooks and prototypes. Modern V2 material is being migrated in a controlled branch-based refresh so historical functionality is not accidentally lost.

The active staging branch is **`alpha90-refresh`**. It contains the growing Alpha90 release/documentation lineage, while the default `main` branch is intentionally left unchanged until the accumulated engine, notebooks, tests, documentation, and CI structure are consolidated and reviewed together.

The repository is **not yet the complete accumulated Alpha73-90 engine**. Some Alpha90 release folders currently contain release notes or narrow repair modules rather than the entire historical system. The planned consolidation milestone is to migrate verified engine source from the accumulated packaged artifacts into a clean V2 repository layout, run CI, and merge through a controlled pull request.

## Planned repository structure

The target organization is approximately:

```text
SynBioCrow/
├── src/synbiocrow/          # accumulated engine and orchestration code
├── notebooks/               # canonical runnable Colab/Jupyter workflows
├── tests/                   # unit, contract, regression, and integration tests
├── benchmarks/              # small manifests/contracts; no large corpora
├── docs/                    # architecture, evaluation, provenance, Paper-1 support
├── releases/                # compact release notes/contracts for frozen lineages
├── examples/                # small reproducible examples
└── legacy/                  # preserved original notebooks/prototypes
```

## Git and artifact policy

Large benchmark corpora, caches, environments, and `ALL_OUTPUTS.zip` campaign bundles should **not** be committed directly to Git. The repository should contain source, notebooks, tests, manifests, small provenance records, hashes, and documentation. Large immutable artifacts should be referenced by their hashes and external provenance/location.

## Near-term milestones

1. Complete the current Golden native compound-node reference reconstruction and freeze the validated identity bridge.
2. Re-run only the reference/concordance/scoring layers required by the corrected bridge; do not rerun expensive frozen route-generation campaigns unnecessarily.
3. Consolidate the accumulated SynBioCrow V2 engine into the repository with unit/contract/integration tests and CI.
4. Update Paper 1 with the sourced capability/architecture comparison and the final benchmark claims supported by the frozen evidence ledger.
5. Open the repository-modernization pull request and, after review/CI, merge the validated V2 structure to `main`.
6. Begin the Alpha91 architecture roadmap, including direct Galaxy-SynBioCAD integration and broader external-engine orchestration.
