# SynBioCrow 2.2 — manuscript scaffold

## Working title
**SynBioCrow: an evidence-aware multi-engine framework for computational biosynthetic pathway and construct design**

## Abstract
Synthetic-biology pathway design often requires combining complementary retrosynthesis, biocatalysis, specialized biosynthesis, evidence, and construct-design tools that expose incompatible runtimes and data models. SynBioCrow 2.2 consolidates these functions behind explicit computational contracts that separate generator proposal, reaction-level graph integration, evidence, construct design, testing, and learning.

The 2.2 system integrates four generator families—DORAnet, RetroBioCat2, RetroPath/RetroRules, and BioPKS/RetroTide—into a shared Candidate representation and reaction-level ensemble graph. Evidence handling uses explicit PASS/FAIL/ABSTAIN semantics so contextual database hits, model scores, or missing data cannot be silently promoted into exact reaction or enzyme evidence. The digital Build layer verifies CDS-to-protein identity, preserves selected amino-acid sequences during synonymous redesign by default, applies deterministic sequence quality control, and assembles provenance-backed Candidate cassettes. Structured Test outcomes can update bounded, versioned ranking policy without changing evidence or lifecycle state.

A major runtime simplification in 2.2 is replacement of the primary KNIME-dependent RetroPath workflow with a standalone RetroPath-compatible implementation. On the archived RetroPath2 r20220104 lycopene fixture, the standalone runtime reproduced the historical compound-transition multiset exactly: 34/34 transitions, precision 1.0, recall 1.0, Jaccard 1.0, with zero missing and zero novel transitions. Rule/evidence aggregation and some reaction-string serialization differed between implementations and are treated as implementation-level differences rather than evidence of identical internal execution.

SynBioCrow 2.2.0 is released as a reproducible computational research artifact with per-file SHA-256 inventory, release-readiness gates, and a Zenodo archive (DOI: 10.5281/zenodo.23027052). Candidate, Mature, and Certified computational states remain distinct and do not imply experimental validation.

## 1. Introduction

### 1.1 Motivation
Computational cell-factory design is rarely a single-model problem. General reaction-network expansion, enzyme-centered retrosynthesis, rule-based retrosynthesis, polyketide-specific design, reaction evidence, thermodynamics, enzyme provenance, and construct design each address different parts of the problem and often require different data representations and runtimes.

### 1.2 Problem statement
A useful synthetic-biology design system must do more than call multiple generators. It must:
- normalize heterogeneous pathway proposals into a common representation;
- combine complementary reaction edges without losing provenance;
- separate proposal from evidence and lifecycle promotion;
- preserve uncertainty and abstention;
- connect chemistry to sequence and construct design;
- remain reproducible across optional or external scientific runtimes.

### 1.3 SynBioCrow 2.2 contribution
SynBioCrow 2.2 provides a consolidated computational framework with:
1. a shared Candidate contract across four generator families;
2. reaction-level cross-engine graph union;
3. fail-closed evidence semantics;
4. provenance-backed sequence and construct design;
5. bounded Test/Learn feedback that cannot bypass evidence gates;
6. a KNIME-free primary RetroPath-compatible runtime validated against an archived historical fixture;
7. release-level reproducibility artifacts and cryptographic inventory.

### 1.4 Claims deliberately not made
SynBioCrow 2.2 does not claim that a computational Candidate expresses successfully, has experimentally validated enzyme activity, produces useful flux, is nontoxic, is manufacturable, or is experimentally certified.

## 2. System architecture

SynBioCrow separates generator proposal, graph integration, evidence, construct design, testing, and learning into explicit contracts.

Suggested Figure 1: end-to-end architecture from target molecule through generator ensemble, reaction-graph union, evidence, thermodynamics, sequence/CDS resolution, cassette design, and Candidate → Mature → Certified lifecycle.

## 3. Methods

### 3.1 Generator ensemble
The release integrates:
- **DORAnet** for general biosynthetic reaction-network generation;
- **RetroBioCat2** for enzyme-centered biocatalytic retrosynthesis;
- **RetroPath standalone / RetroRules** for rule-based reaction-space expansion;
- **BioPKS / RetroTide** for specialized PKS pathway design.

Generator outputs are normalized to Candidate records. Runtime failure is represented separately from a bounded no-hit.

### 3.2 Reaction-level graph union
Normalized reactions are represented as retrosynthetic hyperedges and merged on canonical molecular identity when structures are available. Per-engine provenance is retained so composite routes can be assembled from independent backend contributions without erasing their source.

### 3.3 Evidence model
Evidence includes:
- atom/formal-charge closure;
- exact Rhea identifier/equation confirmation;
- reviewed UniProt exact/context evidence;
- optional eQuilibrator thermodynamics.

Missing evidence yields ABSTAIN rather than implicit PASS.

### 3.4 Lifecycle semantics
Candidate, Mature, and Certified states are distinct. Generator output alone cannot promote a pathway or construct. Promotion is evidence-gated, and learning/ranking layers cannot create evidence.

### 3.5 Sequence and construct design
Verified CDS coordinates must translate exactly to the selected protein. Synonymous redesign preserves amino-acid sequence by default. Regulatory sequences require explicit provenance. Digital Build outputs remain computational Candidate constructs.

### 3.6 Test and Learn
M7 verifies frozen policy and reproducibility contracts. M8 performs bounded, versioned prioritization updates. Learning may alter prioritization but cannot modify evidence or lifecycle state.

### 3.7 RetroPath standalone runtime
The primary 2.2 RetroPath-compatible runtime is the standalone implementation rather than the legacy KNIME workflow. Legacy RetroPath2/KNIME remains available for historical/reference compatibility but is not required for the primary 2.2 runtime.

### 3.8 RetroPath equivalence policy
The archived r20220104 lycopene fixture was used for implementation-level comparison. Certification uses the policy:

`EXACT_COMPOUND_TRANSITION_MULTISET`

The comparison is defined over substrate InChI, product InChI, sink membership, and iteration. Rule IDs, EC aggregation, scores, and reaction-string serialization are retained as diagnostic comparisons but are not required to be byte-for-byte identical between independent implementations.

### 3.9 Reproducibility and release packaging
The sealed 2.1 state is retained as a read-only regression anchor. The M9 package builder records:
- release commit;
- per-file SHA-256 hashes;
- release-readiness status;
- reproducibility digest;
- protected truth-boundary policy;
- RetroPath runtime/equivalence policy.

The final 2.2.0 archive is available at DOI 10.5281/zenodo.23027052.

## 4. Results

### 4.1 Engine consolidation
SynBioCrow 2.2 integrates four generator families behind a shared Candidate contract and reaction-level ensemble graph.

### 4.2 Composite-route capability
Hermetic tests recover target-to-sink routes assembled from reaction edges contributed by independent backends, demonstrating that route construction is not restricted to single-engine pathways.

### 4.3 Fail-closed evidence behavior
PASS/FAIL/ABSTAIN semantics prevent contextual hits or model scores from being represented as exact reaction/enzyme evidence when the required evidence is absent.

### 4.4 Digital Build behavior
The Build layer verifies CDS-to-protein identity, preserves amino-acid sequence during synonymous redesign, applies deterministic quality-control rules, and produces Candidate cassettes with provenance.

### 4.5 DBTL behavior
Structured Test outcomes update versioned ranking policy through bounded deterministic updates with no direct lifecycle effect.

### 4.6 KNIME-free RetroPath equivalence
On the archived RetroPath2 r20220104 lycopene fixture:
- historical compound transitions: 34;
- standalone compound transitions: 34;
- exact compound-transition matches: 34/34;
- missing transitions: 0;
- novel transitions: 0;
- precision: 1.0;
- recall: 1.0;
- Jaccard: 1.0.

Diagnostic implementation-level comparisons were not identical:
- reaction-string projection: 26/34 matching;
- rule-transition projection: 12/34 matching;
- evidence-transition projection: 8/34 matching.

These differences show that chemical transition equivalence does not imply identical internal serialization, rule attribution, or evidence aggregation.

### 4.7 Release verification
SynBioCrow 2.2.0 passed:
- full packaged test suite;
- M7 release-readiness gate;
- M9 package check;
- package/commit consistency verification;
- published RC2 artifact acceptance before final promotion.

The final 2.2.0 source reproducibility ZIP is tied to release commit:
`1e54f885120209746a385443b9390590d442dc4c`

Final source ZIP SHA-256:
`413c704a6446a503ba982f5312093f96877db7be7c1c6e8aebf11ec51913a1c6`

Zenodo DOI:
`10.5281/zenodo.23027052`

## 5. Discussion

### 5.1 Ensemble design as reaction-graph integration
The central design choice is to combine engines at the reaction-graph level instead of selecting a single preferred retrosynthesis system. This allows complementary generators to contribute edges to routes that may not be available from one backend alone.

### 5.2 Proposal is not evidence
Separating generation from evidence reduces the risk that a model score, contextual annotation, or generator confidence is mistaken for experimentally supported chemistry or enzyme identity.

### 5.3 Runtime independence and reproducibility
Removing KNIME from the primary RetroPath path materially simplifies Colab and reproducible execution. The historical implementation remains useful as a reference, while the standalone implementation supplies the primary execution path.

### 5.4 Interpretation of RetroPath equivalence
The 34/34 compound-transition match supports chemical/topological equivalence on the tested fixture. It does not establish full equivalence of every rule assignment, score, EC annotation, or serialized reaction string, and it does not establish equivalence on untested chemical classes.

### 5.5 Digital DBTL scope
SynBioCrow implements digital Design, Build, Test, and bounded Learn contracts. These computational stages are distinct from physical synthesis, expression, assay, or experimental optimization.

## 6. Limitations
Current limitations include:
- no claim of experimental pathway or construct validation;
- limited standalone RetroPath equivalence evidence from one historical fixture;
- optional external scientific runtimes and data assets remain operational dependencies;
- enzyme evidence and thermodynamics may be unavailable for many generated steps;
- specialized PKS validation remains narrower than general pathway-generation coverage;
- broader cross-compound benchmarking is still needed.

## 7. Reproducibility and availability
Software release: SynBioCrow 2.2.0  
GitHub tag: `v2.2.0`  
Frozen release commit: `1e54f885120209746a385443b9390590d442dc4c`  
Zenodo DOI: `10.5281/zenodo.23027052`

The release package includes a manifest with per-file SHA-256 hashes and a source reproducibility ZIP.

## 8. Planned figures and tables

### Figures
1. SynBioCrow 2.2 architecture and lifecycle.
2. Reaction-level multi-engine graph union and composite-route assembly.
3. Evidence-gating model showing PASS/FAIL/ABSTAIN.
4. RetroPath standalone vs historical r20220104 equivalence result.
5. Digital Build and DBTL flow from enzyme evidence to Candidate cassette and bounded Learn feedback.

### Tables
1. Generator/runtime roles and readiness requirements.
2. Evidence types and lifecycle effects.
3. RetroPath equivalence projections.
4. Release/reproducibility artifacts and hashes.

## 9. Manuscript gaps that require additional work
The current repository supports the architecture, lifecycle, RetroPath fixture equivalence, release verification, and computational contracts above. It does **not yet contain enough result detail** to support the following stronger manuscript claims without additional experiments or analysis:
- broad performance comparison across many target compounds;
- quantitative superiority of the ensemble over individual generators;
- generalized standalone RetroPath equivalence across multiple chemical classes;
- quantitative enzyme-evidence precision/recall;
- thermodynamic success rates across a representative benchmark;
- construct-quality comparisons across chassis or design methods.

These should become the primary analysis targets for the next manuscript/2.3 phase rather than being inferred from the current release.
