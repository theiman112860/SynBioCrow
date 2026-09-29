# SynBioCrow: integrating complementary retrosynthesis engines for evidence-aware biosynthetic pathway design

## Abstract

Retrobiosynthesis seeks biosynthetic routes to a desired chemical by working backward from the target toward compounds that can be supplied by a host organism or a defined precursor set. A growing collection of computational tools can perform this search, but they do so with different reaction rules, search strategies, biochemical assumptions, and representations. As a result, one system may recover transformations or pathways that another misses, while downstream tasks such as enzyme selection, thermodynamic evaluation, and construct design remain fragmented across separate software environments.

Here we describe SynBioCrow, a computational framework that runs multiple retrosynthesis engines independently, normalizes their predictions into a shared reaction representation, and combines them at the reaction-graph level while retaining engine provenance. The system separates pathway proposal from biochemical evidence and from downstream sequence and construct design. Its current implementation integrates DORAnet, RetroBioCat2, a KNIME-free RetroPath-compatible runtime, and a specialized BioPKS/RetroTide bridge. Rather than assuming that an ensemble must outperform every constituent tool, we evaluate candidate coverage, complete-route recovery, route preservation under graph union, runtime failure modes, and recovery of literature-supported pathways. We additionally test whether 3D-first molecular similarity provides measurable value over 2D-only similarity for evidence retrieval and pathway ranking.

The initial 24-target benchmark demonstrates broad candidate-generation coverage but does not, by itself, establish ensemble-only route recovery. This motivates a second benchmark centered on literature-validated pathways and controlled ablations of graph integration, similarity policy, and evidence-aware ranking. SynBioCrow is intended as an evidence-aware integration framework for computational pathway design rather than as a replacement for any single retrosynthesis algorithm.

## 1. Introduction

### 1.1 Retrobiosynthesis and the pathway-design problem

Metabolic engineering increasingly asks cells to produce molecules that are absent from, or only weakly connected to, their native metabolism. Designing such pathways by hand quickly becomes difficult. For a desired product, a researcher must identify chemically plausible transformations, connect those transformations to metabolites available in a host, find enzymes capable of catalyzing the reactions, and decide which of many possible pathways is worth testing.

Retrobiosynthesis addresses the first part of this problem by reversing the usual direction of pathway design. Instead of beginning with a host metabolite and asking what can be made from it, the search begins with the target molecule and works backward through plausible biochemical transformations until it reaches a defined set of available precursors. The result is not necessarily a single pathway. It is often a reaction network from which many candidate routes can be enumerated and ranked.

This idea is powerful because generalized biochemical transformations can suggest routes that do not exist as complete native pathways in any one organism. It is also difficult for the same reason. As reaction rules are generalized and applied iteratively, the search space expands rapidly. Choices about reaction rules, enzyme knowledge, pruning, search depth, compound identity, and pathway ranking therefore have a large effect on what is found.

### 1.2 Different approaches expose different parts of biosynthetic space

Existing retrosynthesis systems approach this search in different ways. Rule-based network-expansion methods apply generalized biochemical transformations to explore reaction space. RetroPath2.0 is a prominent example of this approach and was designed specifically for metabolic engineers. Other network-generation frameworks, including Pickaxe and DORAnet, emphasize configurable reaction rules, network expansion, filtering, and flexible exploration of biochemical or hybrid chemical spaces.

A second family is more explicitly centered on biocatalysis. RetroBioCat, for example, encodes biocatalytic reaction knowledge and connects predicted transformations to literature precedent and enzyme information. This produces a different search bias from a broad rule-expansion system: it can be more closely tied to known biocatalytic chemistry, but its coverage depends on the transformations and precedents represented in the knowledge base.

More recent systems also use learned reaction prediction, tree search, or learned ranking to prioritize promising transformations and control combinatorial growth. Specialized generators add another dimension. Polyketide biosynthesis, for example, has architecture that can be better captured by dedicated models than by general reaction rules.

These approaches are not interchangeable. They make different assumptions and fail in different ways. That observation motivates SynBioCrow.

### 1.3 The integration problem

In practice, pathway design is fragmented. Retrosynthesis tools differ in their reaction representations, scoring systems, dependencies, and definitions of success. A transformation proposed by one engine may never be considered by another. Even after a candidate route is found, the researcher still has to evaluate reaction evidence, enzyme precedent, thermodynamic feasibility, and the genetic sequence needed to build the pathway.

A straightforward response would be to choose one retrosynthesis package and accept its search space. SynBioCrow takes a different approach. It treats independent engines as complementary sources of candidate reactions. Their outputs are normalized into a shared reaction graph, where pathways can be reconstructed from edges contributed by more than one backend. Crucially, the framework retains provenance so that a route can still be traced back to the engines and evidence that produced its component reactions.

This leads to a testable hypothesis rather than an assumption: independent engines should explore partially overlapping reaction spaces, and graph-level integration may increase pathway-search breadth, route diversity, or robustness to individual-engine failure. Whether it actually recovers complete pathways that no single engine can find must be determined experimentally.

### 1.4 From pathway proposal to evidence-aware design

A predicted reaction is not the same thing as a validated reaction, and a predicted pathway is not the same thing as an experimentally viable pathway. SynBioCrow therefore separates generation from evidence. Reaction proposals can be annotated with exact or contextual database evidence, enzyme candidates, and thermodynamic information, while missing information remains explicitly unresolved rather than being converted into a positive score.

The same distinction is carried into downstream design. Candidate pathways may be connected to enzyme sequences and digital construct designs, but computational Candidate, Mature, and Certified states remain distinct from physical validation. This separation is intended to make the workflow useful for design without overstating the certainty of its predictions.

### 1.5 Study objectives

This study asks five questions:

1. How do the integrated retrosynthesis engines differ in candidate and complete-route coverage across a chemically diverse panel?
2. Does graph-level integration preserve all valid routes found by individual engines, and does it recover additional routes or increase route diversity?
3. How well does SynBioCrow recover literature-supported or expert-validated biosynthetic pathways compared with its constituent engines and other open systems where a fair comparison is possible?
4. Does 3D-first molecular similarity improve evidence retrieval or pathway ranking relative to 2D-only similarity, and in what chemical contexts?
5. Can pathway generation, evidence, enzyme selection, and digital construct design be connected in one reproducible workflow without conflating computational prediction with experimental validation?

## 2. System overview

SynBioCrow separates pathway generation, reaction-graph integration, evidence evaluation, enzyme/sequence resolution, construct design, and bounded learning into explicit computational stages.

[Figure 1: end-to-end workflow]

### 2.1 Independent generator layer

Current generator families include:
- DORAnet;
- RetroBioCat2;
- RetroPath standalone / RetroRules;
- BioPKS / RetroTide as a specialized PKS backend.

Each engine runs independently and returns Candidate records with backend provenance.

### 2.2 Reaction-graph integration

Candidate reactions are normalized to molecular identities and represented as retrosynthetic graph edges. Duplicate or equivalent edges can retain multiple backend sources. Route enumeration is performed on the union graph, allowing a route to contain edges proposed by different engines.

A core software invariant is monotonicity: adding candidate edges to the graph must not remove the reachability of a route already present in a constituent graph. The route-preservation audit tests this invariant explicitly and distinguishes graph loss from top-K enumeration effects.

### 2.3 Evidence and lifecycle

Evidence is evaluated separately from generation. Missing evidence produces abstention rather than implicit support. Candidate, Mature, and Certified computational states remain separate and do not imply experimental validation.

## 3. Methods

### 3.1 Initial 24-target breadth benchmark

The first benchmark spans six chemical classes and measures:
- candidate coverage;
- complete-route coverage;
- number of generated candidates;
- runtime and backend failure modes;
- reaction-graph union size;
- route diversity.

This benchmark is intended to characterize system behavior, not to serve as the primary biological-validity benchmark.

### 3.2 Route-preservation audit

For every target with a complete route from an individual backend, the exact normalized reaction-edge sequence is compared with the ensemble graph. The audit records:
- whether every component edge remains present after union;
- whether the exact route is returned within the ensemble route-enumeration cap;
- whether a missing route reflects graph loss or enumeration order/truncation.

No retrosynthesis backend is rerun for this audit; it operates on persisted candidate checkpoints.

### 3.3 Literature-grounded pathway benchmark

The main biological benchmark follows the style of published retrosynthesis studies that compare generated pathways with literature- or expert-validated pathways. A curated target set will record, where available:
- target compound;
- host/chassis or precursor set;
- known reaction sequence;
- EC or enzyme annotations;
- literature source.

Evaluation will include:
- top-1, top-5, and top-10 pathway recovery;
- partial pathway recovery;
- reaction-level overlap;
- route length;
- enzyme-evidence availability;
- runtime.

### 3.4 Cross-tool comparisons

Comparisons will be performed only where target, precursor/chassis assumptions, route depth, and success definitions can be made sufficiently comparable. Constituent-engine ablations provide the primary baseline. External open-source systems may be included when reproducible execution and aligned inputs are available.

### 3.5 3D/2D molecular-similarity ablation

SynBioCrow currently prefers USRCAT 3D similarity when a usable conformer is available and falls back to 2D similarity otherwise. This policy will be evaluated rather than assumed beneficial.

Three policies will be compared:
1. 3D-first with 2D fallback;
2. 2D-only;
3. 3D-only for compounds with valid conformers.

The ablation will measure:
- known-pathway retrieval at top-1/top-5/top-10;
- reaction/evidence precedent retrieval;
- route survival after evidence filtering;
- route diversity;
- enzyme-support availability;
- runtime;
- fallback frequency;
- cases in which the chosen precedent or route rank changes.

The purpose is to determine where 3D similarity adds information beyond topology, not to establish a universal preference for 3D methods.

## 4. Results

### 4.1 Initial breadth benchmark

[Insert frozen 24-target results after route-preservation audit.]

### 4.2 Route-preservation audit

[Insert monotonicity versus enumeration result.]

### 4.3 Literature-grounded pathway recovery

[Primary manuscript benchmark.]

### 4.4 Similarity-policy ablation

[3D-first versus 2D-only versus 3D-only.]

### 4.5 Evidence-aware route prioritization

[Evidence/thermodynamics/enzyme-support results.]

### 4.6 End-to-end construct-design example

[Representative pathway-to-construct case study.]

## 5. Discussion

The discussion should distinguish three different questions that are easy to conflate: whether the ensemble broadens reaction coverage, whether it increases route diversity, and whether it makes previously unsolved targets solvable. These are separate outcomes and should be reported separately.

If the ensemble does not produce many ensemble-only route targets, that result should be reported directly. The value of integration may instead lie in broader candidate coverage, alternative routes, fault tolerance, provenance, and downstream evidence integration. The literature-grounded benchmark will determine whether those properties translate into better recovery of biologically useful pathways.

## 6. Limitations

- computational predictions are not experimental validation;
- benchmarks are sensitive to precursor/sink definitions and route-depth limits;
- constituent tools have different intended domains and are not always directly comparable;
- BioPKS/RetroTide currently has runtime limitations in the benchmark environment;
- 3D similarity depends on conformer generation and may add cost without improving retrieval for all chemistry;
- known-pathway benchmarks favor chemistry represented in the literature.

## 7. Reproducibility and availability

[Release, commit, DOI, frozen benchmark hashes, audit artifacts.]
