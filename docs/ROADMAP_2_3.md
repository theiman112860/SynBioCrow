# SynBioCrow 2.3 development roadmap

SynBioCrow 2.3 starts from the released 2.2.0 public baseline. The 2.2.0 tag and release branch remain immutable.

## Primary objective
Shift from integration plumbing to **scientific breadth, benchmarking, and manuscript-grade evidence**.

## Workstreams

### 1. Multi-compound benchmark panel
Build a curated benchmark spanning multiple biosynthetic/industrial chemical classes. Preserve blinded truth boundaries where applicable.

Outputs:
- per-engine coverage;
- ensemble coverage;
- route completion;
- overlap/complementarity;
- abstention/failure taxonomy;
- runtime and reproducibility metrics.

### 2. Ensemble contribution analysis
Quantify when reaction-graph union recovers complete routes that no individual backend recovers alone.

Outputs:
- unique edge contributions by engine;
- composite-route counts;
- ablation analysis;
- engine-pair/engine-family complementarity.

### 3. RetroPath standalone generalization
Expand beyond the single archived lycopene fixture.

Outputs:
- multiple historical fixtures/targets where available;
- exact compound-transition comparison;
- rule/evidence attribution diagnostics;
- mismatch categorization.

### 4. Evidence and thermodynamics
Measure evidence availability and abstention explicitly rather than treating missing evidence as failure.

Outputs:
- Rhea exact-support rate;
- reviewed UniProt exact/context-support rate;
- thermodynamic evaluation availability;
- PASS/FAIL/ABSTAIN distributions.

### 5. BioPKS/RetroTide validation
Broaden the specialized PKS test set and document where the specialized generator adds unique routes or construct-relevant designs.

### 6. Construct-design evaluation
Evaluate deterministic sequence/construct QC across representative enzymes and chassis while preserving amino-acid sequence by default.

### 7. Manuscript package
Turn `paper/2.2/MANUSCRIPT.md` into a submission-ready paper with:
- literature-supported Introduction;
- complete benchmark Methods;
- quantitative Results;
- figures/tables generated from frozen result artifacts;
- limitations and reproducibility appendix.

## Release discipline
- 2.2.0 remains frozen.
- New code goes to `develop/2.3`.
- Manuscript claims must point to frozen result artifacts.
- Candidate/Mature/Certified semantics remain unchanged.
- No benchmark holdout truth is accessed outside the established evaluation contract.
