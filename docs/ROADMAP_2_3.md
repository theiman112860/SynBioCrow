# SynBioCrow 2.3 development roadmap

SynBioCrow 2.3 starts from the released 2.2.0 public baseline. The 2.2.0 tag and release branch remain immutable.

## Primary objective
Shift from integration plumbing to **scientific breadth, benchmarking, and manuscript-grade evidence**.

## Workstreams

### 1. Multi-compound benchmark panel — INITIAL PASS COMPLETE
The initial 24-target breadth benchmark is complete. Route-preservation auditing confirmed that every individual complete route survived graph union and was returned by the ensemble. The benchmark now serves primarily as a system-behavior and route-diversity benchmark rather than the main biological-validity benchmark.

Outputs:
- per-engine coverage;
- ensemble coverage;
- route completion;
- overlap/complementarity;
- abstention/failure taxonomy;
- runtime and reproducibility metrics.

### 2. Ensemble contribution analysis — PARTIALLY COMPLETE
The route-preservation audit found zero graph-monotonicity violations and zero enumeration losses across all route-positive targets. The ensemble substantially increased route diversity for some solvable targets (for example, 3-hydroxypropionic acid reached the 100-route cap), but the current panel contains no ensemble-only target recovery. The next analysis should quantify edge-level complementarity and composite-route composition within the expanded ensemble route sets.

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
Continue `paper/2.3/MANUSCRIPT_DRAFT.md` as the submission-oriented paper, using the Galaxy-SynBioCAD style of biological problem framing, literature-grounded pathway validation, comparative benchmarking, and downstream design. Include:
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
