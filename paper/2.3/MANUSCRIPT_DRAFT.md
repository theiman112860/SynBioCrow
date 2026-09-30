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

[Figure 2: multistep ensemble-route construction example using 1,4-butanediol]

**Figure 2. Multistep construction of a SynBioCrow ensemble route.** A real benchmark target, 1,4-butanediol, is used to illustrate the routing logic. Backend-specific candidate reactions are first generated independently. These reactions are normalized to canonical compound identities and merged into a shared reaction graph while preserving backend provenance on each edge. SynBioCrow then enumerates coherent target-to-sink routes through the union graph. The figure is schematic for readability: it illustrates the graph-merging and route-extraction logic using chemistry observed in the benchmark lineage, but does not imply that every displayed edge was recovered by every backend in the same run.

### 2.1 Independent generator layer

Current generator families include:
- DORAnet;
- RetroBioCat2;
- RetroPath standalone / RetroRules;
- BioPKS / RetroTide as a specialized PKS backend.

Each engine runs independently and returns Candidate records with backend provenance.

### 2.2 Reaction-graph integration

Candidate reactions are normalized to molecular identities and represented as retrosynthetic graph edges. Duplicate or equivalent edges can retain multiple backend sources. Route enumeration is performed on the union graph, allowing a route to contain edges proposed by different engines. Figure 2 illustrates this process with a multistep 1,4-butanediol example: backend-specific candidate reactions converge on a common normalized graph, from which a coherent route is extracted while edge-level provenance is retained.

A core software invariant is monotonicity: adding candidate edges to the graph must not remove the reachability of a route already present in a constituent graph. The route-preservation audit tests this invariant explicitly and distinguishes graph loss from top-K enumeration effects.

### 2.3 Evidence and lifecycle

Evidence is evaluated separately from generation. Missing evidence produces abstention rather than implicit support. Candidate, Mature, and Certified computational states remain separate and do not imply experimental validation.

### 2.4 Computational Design-Build-Test-Learn

SynBioCrow implements a bounded computational Design-Build-Test-Learn (DBTL) loop. Design comprises multi-backend pathway generation, graph integration, route enumeration, and ranking. Build refers to digital construct design from provenance-backed protein and coding-sequence evidence, including translation validation, synonymous codon optimization, sequence QC, and promoter-RBS-CDS-terminator cassette assembly. Test evaluates route closure, Rhea support, enzyme evidence, thermodynamics, reproducibility, and construct QC. Learn updates only backend, route-feature, and construct-feature prioritization weights from structured TestOutcome records.

The learning layer is intentionally constrained. It cannot create missing evidence, alter evidence-gate outcomes, invent reactions or sequences, access protected benchmark truth, or promote a Candidate to Mature or Certified. Lifecycle promotion remains controlled by explicit evidence policy.

### 2.5 Chemical-retrosynthesis proposal adapters

SynBioCrow can in principle accept routes from conventional chemical retrosynthesis planners as an additional proposal source. Such routes are not automatically considered biosynthetic. Instead, each chemical step must be normalized and mapped to plausible biochemical transformations, enzyme or EC precedent, cofactor requirements, thermodynamic feasibility, and chassis-available precursors. Protecting-group chemistry, non-biological stoichiometric reagents, and reaction conditions without a documented biochemical analogue remain unresolved or rejected. This adapter architecture is included as an extension point in 2.3 but is not included in the present benchmark claims.

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

### 3.5 Computational DBTL case study

A computational DBTL case study reuses persisted benchmark candidates without rerunning retrosynthesis. The 1,4-butanediol route is used to demonstrate Design and Test, including evidence-aware route features. The Build stage executes only when provenance-backed protein, CDS, and regulatory-part sequences are available; otherwise it records an explicit abstention rather than fabricating sequence evidence. A second target, 3-hydroxypropionic acid, provides multiple alternative ensemble routes for a Learn-stage demonstration in which bounded policy updates alter route-prioritization weights while leaving evidence and lifecycle state unchanged.

### 3.6 3D/2D molecular-similarity ablation

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

Across the 24-target panel, DORAnet produced candidates for all 24 targets, while RetroBioCat2 and RetroPath standalone each produced candidates for 19 targets. Complete routes were recovered for four targets by at least one individual backend: lactic acid, 3-hydroxypropionic acid, 1,4-butanediol, and putrescine.

The reaction-graph ensemble preserved route-positive coverage for all four of these targets. It returned 23 routes for lactic acid, reached the 100-route enumeration cap for 3-hydroxypropionic acid, returned one route for 1,4-butanediol, and returned two routes for putrescine. These results indicate that the ensemble can substantially expand route diversity for some already-solvable targets, although the present 24-target panel did not contain a target solved exclusively by cross-engine graph integration.

BioPKS/RetroTide was evaluated separately because its specialized PKS design stage and its downstream enzymatic-continuation stage have very different computational behavior. PKS-only generation completed successfully for both naringenin and pinocembrin, producing 25 candidate PKS designs in 17.8 s and 11.3 s, respectively. The upstream combined BioPKS/DORAnet continuation, however, repeatedly exceeded bounded runtime limits during one-generation network expansion.

To distinguish runtime failure from biochemical reachability, we replaced the Cartesian network expansion with direct enzymatic-rule application to the saved PKS products. A complete one-step screen of the JN1224MIN rule set generated 3,409 unique products for naringenin and 2,717 for pinocembrin in 35.1 s and 29.2 s, respectively, but produced no exact target hit. A subsequent checkpointed beam search explored up to three enzymatic steps with a beam width of 12. No exact target was recovered within those bounds. The best 2D similarity improved from 0.227 at depth 1 to 0.351 at depth 3 for naringenin and from 0.263 to 0.526 for pinocembrin. These results support retaining BioPKS/RetroTide as a specialized PKS generator while treating post-PKS completion as a separate bounded search problem rather than interpreting the earlier timeouts as biochemical no-hits.

### 4.2 Route-preservation audit

Because an earlier aggregate summary appeared to show fewer route-positive targets for the ensemble than for RetroBioCat2 alone, we performed an offline route-preservation audit using the persisted candidate checkpoints. No retrosynthesis backend was rerun.

Four targets contained at least one complete individual-engine route. The audit compared each individual route with the union graph at the normalized reaction-edge level. Across all audited routes, the ensemble showed:

- graph-monotonicity violations: 0;
- missing individual reaction edges after union: 0;
- individual routes absent from the ensemble enumeration: 0;
- enumeration/truncation losses at the 100-route cap: 0.

Thus, every complete route found by an individual backend remained present and was returned by the ensemble. The earlier lower ensemble route-coverage figure was therefore an artifact of a damaged intermediate aggregate rather than a property of the reaction graph.

The most pronounced increase in route diversity occurred for 3-hydroxypropionic acid: DORAnet returned one complete route and RetroBioCat2 returned three, whereas the ensemble returned the maximum 100 routes permitted by the benchmark cap. Lactic acid likewise increased from ten individual routes in total (eight DORAnet and two RetroBioCat2) to 23 ensemble routes. These results support a route-diversity benefit of graph integration on some solvable targets, while not yet demonstrating ensemble-only target recovery.

### 4.3 BioPKS/RetroTide specialist qualification

BioPKS/RetroTide behaved differently from the general retrosynthesis backends and was therefore evaluated as a specialist rather than folded indiscriminately into the 24-target panel. PKS-only generation was successful for both canonical flavanone targets tested. Naringenin produced 25 PKS designs in 17.8 s, and pinocembrin produced 25 designs in 11.3 s.

The downstream BioPKS continuation stage calls DORAnet to search for enzymatic transformations from the PKS product to the final target. In the unmodified combined workflow this stage exceeded the runtime bound for both targets. Atom-count filtering, a reduced DORAnet ruleset, and precursor/product SMARTS prefilters reduced the nominal search space but did not make the Cartesian network expansion tractable.

We therefore tested the same one-step enzymatic chemistry by direct reaction-rule execution, avoiding network Cartesian expansion. This screen evaluated 1,224 rules and completed in under 36 s per target. For naringenin, 461 valid rule/slot applications generated 3,409 unique products; for pinocembrin, 372 valid applications generated 2,717 unique products. Neither target was recovered in one step.

A resumable direct beam search then explored up to three enzymatic steps using a beam width of 12. No exact target was found within these bounds. For naringenin, the best 2D similarity increased from 0.227 at depth 1 to 0.300 at depth 2 and 0.351 at depth 3. For pinocembrin, it increased from 0.263 to 0.389 and 0.526. The search completed all three depths and terminated normally with no exact hit.

These observations justify a narrower role for BioPKS/RetroTide in the present manuscript: it is retained as a specialized PKS design engine, while post-PKS enzymatic completion is reported separately and is not allowed to block or redefine the performance of the general DORAnet/RetroBioCat2/RetroPath ensemble.

### 4.4 Literature-grounded pathway recovery

A deterministic 12-pathway development subset was selected from the Galaxy-SynBioCAD literature benchmark independently of SynBioCrow prediction performance. Predictions were generated and SHA-256 sealed before access to the literature reaction truth. DORAnet, RetroBioCat2, RetroPath standalone, and the reaction-graph ensemble were then evaluated against the known pathways using both strict stereochemical reaction identity and a connectivity-level comparison in which stereochemistry was removed before matching.

Under strict stereochemical identity, no backend recovered a complete literature pathway. RetroBioCat2 partially recovered one target, yielding a mean best reaction recall of 0.028 across the 12 pathways. DORAnet and RetroPath standalone showed no strict reaction overlap in this subset. The ensemble preserved the RetroBioCat2 partial recovery and likewise achieved a mean best reaction recall of 0.028.

Connectivity-level evaluation changed the picture for RetroPath standalone. RetroPath exactly recovered the one-step literature pathways for sabinene and valencene at rank 1 and partially recovered miltiradiene, giving exact Top-1 recovery for 2 of 12 pathways and partial reaction recovery for 3 of 12. RetroBioCat2 partially recovered pentadecane. DORAnet showed no literature reaction overlap in the development subset.

The ensemble preserved all constituent-backend routes and therefore retained the same underlying exact recoveries and partial matches. Across the 12 targets it achieved partial reaction recovery for four targets and a mean best reaction recall of 0.211. Because the preserved ensemble routes were ordered by a deterministic truth-independent serialization rule rather than by a biochemical ranking function, the exact sabinene and valencene routes appeared at ranks 44 and 68, respectively. Consequently, the current development run demonstrates route preservation and broader aggregate reaction recovery, but not improved Top-K ranking. No cross-engine-only route was recovered under the bounded composition search.

The state-capped cross-engine composition search expanded at most 15,000 graph states per target. Five connectivity-level targets and four strict-stereo targets reached this cap, so absence of a cross-engine-only route should be interpreted as a bounded negative result rather than proof that no such route exists. These development-set results therefore support the use of the ensemble as a route-preserving integration layer while motivating a separate ranking model and a larger literature benchmark before making stronger claims about retrieval performance.

### 4.5 Computational DBTL demonstration

[Design → Test → Build-or-abstain → Learn case-study results.]

### 4.6 Similarity-policy ablation

[3D-first versus 2D-only versus 3D-only.]

### 4.7 Evidence-aware route prioritization

[Evidence/thermodynamics/enzyme-support results.]

### 4.8 End-to-end construct-design example

[Representative pathway-to-construct case study.]

## 5. Discussion

The discussion should distinguish three different questions that are easy to conflate: whether the ensemble broadens reaction coverage, whether it increases route diversity, and whether it makes previously unsolved targets solvable. These are separate outcomes and should be reported separately.

The initial breadth benchmark does not show ensemble-only target recovery, and that negative result should be reported directly. It does, however, show that graph integration preserves every complete individual route tested and can greatly expand route diversity for some targets. The literature development benchmark extends that conclusion: the ensemble preserved exact connectivity-level RetroPath recoveries for sabinene and valencene and partial matches from RetroPath and RetroBioCat2, but it did not improve Top-K ranking because the current ensemble serialization is not yet a biological ranking model. No cross-engine-only literature route was recovered under the state-capped search. The practical value demonstrated so far therefore lies in route preservation, broader aggregate reaction recovery, provenance retention, and alternative-route integration, while rank improvement and ensemble-only recovery remain hypotheses for the larger benchmark and ranking ablations.

## 6. Limitations

- computational predictions are not experimental validation;
- benchmarks are sensitive to precursor/sink definitions and route-depth limits;
- constituent tools have different intended domains and are not always directly comparable;
- BioPKS/RetroTide PKS design is operational, but its default post-PKS DORAnet network expansion is computationally expensive for the tested flavanone intermediates; a bounded direct search found no exact continuation within three enzymatic steps;
- 3D similarity depends on conformer generation and may add cost without improving retrieval for all chemistry;
- known-pathway benchmarks favor chemistry represented in the literature.

## 7. Reproducibility and availability

[Release, commit, DOI, frozen benchmark hashes, audit artifacts.]
