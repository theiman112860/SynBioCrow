# SynBioCrow 2.4 experimental specification

## Hypothesis

SynBioCrow 2.3 showed that the ensemble can broaden reaction recovery while exact-route ranking remains weak. The 2.4 hypothesis is that **explicit biochemical evidence and cross-engine context can improve route ranking beyond structural similarity alone**.

## Ranking unit

A route is ranked as a structured object containing:
- ordered normalized reactions;
- backend provenance per edge;
- route length;
- target-to-sink closure;
- structural-similarity features;
- reaction-evidence features;
- enzyme-evidence features;
- EC specificity;
- cofactor requirements;
- thermodynamic evidence where available;
- engine support/agreement;
- evidence missingness;
- mapping confidence;
- route diversity/redundancy indicators.

Missing evidence is encoded as missing/unknown, never as positive support.

## Feature families

### A. Structural context
- Morgan/Tanimoto 2D similarity;
- optional USRCAT 3D secondary signal;
- substrate/product similarity to precedent reactions;
- scaffold and functional-group compatibility.

### B. Reaction evidence
- exact Rhea match;
- connectivity-level Rhea match;
- rule/predecessor provenance;
- literature precedent count;
- evidence recency/source class where appropriate.

### C. Enzyme evidence
- reviewed UniProt support;
- EC specificity;
- sequence provenance;
- substrate-precedent compatibility;
- multiple independent enzyme candidates;
- evidence quality and missingness.

### D. Thermodynamic/cofactor context
- quantitative thermodynamic evidence when available;
- directionality consistency;
- ATP/NAD(P)H/cofactor burden;
- cofactor regeneration requirement;
- redox consistency.

### E. Engine ensemble context
- number of independent engines supporting an edge;
- engine diversity across a route;
- agreement/disagreement pattern;
- edge uniqueness;
- whether route is constituent-preserved or cross-engine-composed.

### F. Route-level context
- route length;
- branch complexity;
- unsupported-edge count;
- evidence bottleneck score;
- precursor/sink compatibility;
- estimated carbon-loss count where derivable from balanced stoichiometry.

## Models

Begin with interpretable baselines before complex learned ranking:
1. weighted linear/logistic route score;
2. gradient-boosted ranking model;
3. pairwise ranking model;
4. optional graph-aware model only if simpler models saturate.

Primary scientific claims must remain interpretable through ablations and feature attribution.

## Training policy

- train only on development data;
- validation data selects model/hyperparameters;
- no untouched-evaluation access during training;
- 2.3 held-out truth excluded;
- all training examples retain source provenance.

## Evidence gates versus rank score

Evidence gates and route ranking are separate.

A high rank does not imply Mature or Certified status.
A route may rank first while remaining Candidate if required evidence is missing.
Lifecycle promotion remains governed by explicit evidence policy.

## Expected 2.4 outputs

For every target:
- ranked route list;
- component feature values;
- evidence/missingness summary;
- confidence/calibration value;
- lifecycle state;
- provenance graph;
- reason codes for ranking and abstention.

## Acceptance criteria

2.4 is considered scientifically successful only if the untouched evaluation demonstrates one or more of:
- improved exact Top-K recovery versus frozen 2.3 ranking baseline;
- improved exact-route MRR;
- improved partial-route prioritization at fixed candidate generation;
- better calibrated confidence/abstention;
- improved ranking within difficult failure classes.

An increase in raw route count alone is not a 2.4 success criterion.

## Negative-result policy

If evidence-aware ranking does not improve untouched evaluation:
- report the result;
- preserve sealed predictions;
- localize failure modes;
- do not tune against the failed holdout;
- define the next experiment using a new evaluation set.
