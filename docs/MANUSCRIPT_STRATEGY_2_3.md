# SynBioCrow manuscript strategy — 2.3

## Narrative target

Use the Galaxy-SynBioCAD paper as the closest stylistic model: explain the engineering problem first, describe the computational workflow in biologically meaningful terms, benchmark against literature/validated pathways and competing methods, then discuss what the integrated workflow adds. Avoid presenting SynBioCrow as a collection of software adapters.

The paper should read as a computational synthetic-biology paper, not as a release note.

## Introduction structure

### 1. What retrobiosynthesis is

Define retrobiosynthesis as computational pathway design that begins from a desired target molecule and searches backward through plausible biochemical transformations until reaching metabolites available to a host/chassis or a specified precursor set.

Explain why it matters:
- industrial biotechnology and metabolic engineering increasingly target chemicals not reached by native pathways;
- manually designing pathways becomes difficult as reaction space grows;
- enzyme promiscuity and generalized reaction rules expand the accessible chemical space but also create combinatorial explosion;
- predicted chemistry alone is insufficient because pathway ranking also depends on enzyme evidence, thermodynamics, host compatibility, and construct design.

Keep this section compact and biological. Do not turn it into a textbook history.

### 2. Main computational approaches

Describe the major families in plain language:

1. **Rule/template-based network expansion**  
   Generalized biochemical reaction rules are applied iteratively to a target or precursor pool. Examples include RetroPath2.0 and Pickaxe. Strengths: interpretability, broad reaction-space exploration, configurable chemistry. Weaknesses: combinatorial growth, rule-set dependence, ranking and pruning sensitivity.

2. **Enzyme/biocatalysis-centered retrosynthesis**  
   Search is organized around transformations for which enzyme classes or literature precedent are known. RetroBioCat is the clearest example. Strengths: enzyme-aware plausibility and biocatalytic interpretability. Weaknesses: coverage is bounded by known transformation classes and substrate precedent.

3. **Search/planning and learned approaches**  
   Tree search, neural models, learned reaction prediction, or learned ranking can prioritize promising transformations and reduce search cost. These methods may improve search efficiency but inherit training-domain and ranking-model biases.

4. **Specialized biosynthetic-family methods**  
   Systems such as PKS-focused generators exploit biosynthetic architecture that is poorly represented by general retrosynthesis rules.

The important point is not that one family is universally better. They expose different search spaces and failure modes.

### 3. The practical gap

Frame the problem around fragmentation:
- tools use different representations and runtimes;
- a pathway found by one engine may be invisible to another;
- reaction proposal, route enumeration, enzyme evidence, thermodynamics and genetic design are often separate workflows;
- no single score should be allowed to masquerade as biochemical evidence;
- end-to-end reproducibility is difficult when optional scientific runtimes fail independently.

### 4. SynBioCrow hypothesis

State the hypothesis conservatively:

> Independent retrosynthetic engines explore partially overlapping reaction spaces. Integrating their outputs at the normalized reaction-graph level may increase pathway-search breadth, route diversity, and robustness to individual-engine failure while preserving the provenance needed for evidence-aware downstream design.

Do **not** claim ensemble-only route recovery unless the benchmark demonstrates it.

## Results structure modeled after Galaxy-SynBioCAD

Galaxy-SynBioCAD is a useful model because it moves from integrated workflow description to concrete pathway benchmarks, literature/expert validation, pathway scoring, and downstream genetic design rather than making the software architecture itself the main result.

Suggested SynBioCrow Results flow:

1. **End-to-end workflow**
   Target -> independent generators -> normalized reaction graph -> route enumeration -> evidence/thermodynamics -> enzyme/sequence resolution -> construct candidate.

2. **Backend characterization**
   What each engine contributes, what chemistry it covers, and its runtime/readiness constraints.

3. **Historical compatibility**
   RetroPath standalone equivalence against the archived RetroPath2 fixture.

4. **Cross-engine benchmark**
   Per-engine candidate coverage, route coverage, runtime, failures/abstentions, union coverage.

5. **Route-preservation / ensemble audit**
   Demonstrate that unioning graphs cannot silently destroy valid individual routes. Distinguish graph reachability from top-K route enumeration.

6. **Known-pathway retrieval benchmark**
   This should become the main manuscript-quality comparison, closer to Galaxy-SynBioCAD:
   - targets with literature- or expert-validated biosynthetic pathways;
   - rank/retrieval of known pathways;
   - top-1/top-5/top-10 recovery;
   - partial pathway recovery;
   - route similarity;
   - runtime.

7. **Comparison with other retrosynthesis systems**
   Compare only where input/output assumptions are reasonably aligned. At minimum report RetroBioCat, RetroPath/RetroRules and DORAnet as constituent baselines; where feasible include an external comparator such as Pickaxe or another published open-source system.

8. **Similarity ablation**
   Compare 3D-first/2D-fallback, 2D-only, and 3D-only behavior.

9. **Evidence-aware ranking and downstream design**
   Show how predicted routes are filtered/annotated without converting missing evidence into false certainty.

## 3D versus 2D similarity experiment

The current USRCAT-first design should be treated as a hypothesis to test.

### Why 3D might help

3D shape/pharmacophore similarity can identify molecules with similar spatial arrangements of interaction features even when their 2D topology is different. This can support scaffold-hopping-style analogies and may recover candidate biochemical precedents that 2D fingerprints rank poorly.

### Why 3D may not help

- conformer generation introduces cost and uncertainty;
- a single conformer may not represent the biologically relevant shape;
- biochemical transformations are often controlled by local reactive motifs that 2D fingerprints may capture sufficiently;
- broader structural analogies may increase false positives rather than useful routes.

### Required ablation

Run the same evidence/ranking workflow under three policies:

A. **3D-first, 2D fallback** — current policy  
B. **2D-only**  
C. **3D-only when conformers are available**

Measure:
- known-pathway retrieval at top-1/top-5/top-10;
- reaction/evidence precedent retrieval;
- number of routes surviving evidence thresholds;
- route novelty/diversity;
- enzyme-support availability;
- runtime;
- percentage requiring fallback;
- cases where 3D changes the selected precedent or route rank.

The useful claim is not "3D is better." The useful result is **where 3D materially changes retrieval and whether those changes improve validated-pathway recovery**.

## Benchmark design inspired by the literature

Galaxy-SynBioCAD benchmarked against literature and expert-validated pathways and reported whether validated pathways appeared among highly ranked predictions. RetroBioCat used literature biocatalytic cascades as a test set. EnzRetro explicitly compared pathway reconstruction against competing enzymatic retrosynthesis tools. Pickaxe and RetroPath2 emphasize reaction-space coverage, rule behavior, and controlled network expansion.

SynBioCrow should therefore use two complementary benchmarks:

### Benchmark A — breadth / system behavior
The current 24-target panel:
- candidate coverage;
- route coverage;
- runtime;
- backend failure taxonomy;
- union size and route diversity;
- fault tolerance.

### Benchmark B — biological/pathway validity
A literature-grounded set:
- known engineered pathway targets;
- known reaction sequence / EC information where available;
- target + chassis or precursor-set definition;
- top-K pathway retrieval;
- partial-path recovery;
- route similarity;
- enzyme evidence;
- thermodynamic availability.

Benchmark B should carry more weight in the manuscript than raw candidate counts.

## Writing style

The paper should sound like a scientist explaining a system they built, not like an AI-generated product description.

Prefer:
- concrete claims tied to experiments;
- normal prose with varied sentence length;
- explicit limitations near the relevant result;
- biological motivation before implementation detail;
- terms used consistently.

Avoid:
- repetitive phrases such as "robust," "comprehensive," "novel," and "state-of-the-art";
- long lists of features in prose;
- inflated statements unsupported by benchmark data;
- claiming that a computational Candidate is experimentally feasible;
- excessive sectioning where a normal paragraph is clearer.

## Immediate experimental sequence

1. Route-preservation monotonicity audit — no chemistry rerun.
2. Recompute ensemble route metrics if the audit exposes enumeration artifacts.
3. Build a literature-grounded known-pathway benchmark, following the Galaxy-SynBioCAD style.
4. Run 3D/2D similarity ablation on that benchmark.
5. Add external/system comparisons where input assumptions permit.
6. Update Results and Discussion only after those analyses are frozen.
