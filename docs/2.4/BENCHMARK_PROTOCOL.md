# SynBioCrow 2.4 benchmark protocol

## 1. Objective

Evaluate whether new biochemical-discrimination and ranking methods improve route prioritization beyond SynBioCrow 2.3 without using the frozen 2.3 held-out benchmark for optimization.

## 2. Benchmark firewall

### 2.3 historical benchmark

The 65-path Galaxy held-out benchmark from SynBioCrow 2.3 is **sealed historical evidence**.

Permitted uses:
- regression checks that do not influence model selection;
- reporting previously frozen 2.3 results;
- compatibility tests for schemas and scoring code.

Prohibited uses:
- feature selection;
- hyperparameter tuning;
- threshold setting;
- ranking-policy selection;
- error-driven rule addition;
- benchmark-specific alias or mapping repair;
- training examples;
- manual route promotion.

Any 2.4 code path that reads 2.3 truth must run in an explicit historical-report mode that cannot write ranking parameters.

## 3. New 2.4 dataset split

Create three disjoint partitions from sources not used as the 2.3 holdout:

### Development set
Used for:
- feature engineering;
- ranking-model fitting;
- threshold selection;
- ablation design;
- error analysis.

### Validation set
Used for:
- model selection;
- calibration;
- stopping decisions.

### Untouched evaluation set
Used exactly once after policy freeze.

Requirements:
- target identity and literature pathway provenance recorded before prediction;
- pathway truth inaccessible to generation and ranking during the sealed run;
- deterministic compound normalization;
- exact source snapshot/hash recorded;
- duplicate and near-duplicate targets removed across splits;
- chemically related target families grouped to reduce leakage where feasible;
- pathway records tagged by chemistry class, route length, enzyme evidence density, and mapping quality.

## 4. Truth representation

For each benchmark pathway, record where available:
- target compound;
- normalized target structure;
- precursor/sink assumptions;
- ordered literature reaction sequence;
- strict stereochemical reaction identity;
- connectivity-level reaction identity;
- EC annotations;
- enzyme/protein accessions;
- cofactors;
- literature reference;
- host/chassis context;
- mapping confidence;
- provenance for every field.

Unknown fields remain unknown.

## 5. Prediction sealing

Before evaluation truth is opened:
1. generate candidates;
2. rank candidates with the frozen 2.4 policy;
3. persist predictions;
4. write manifest;
5. compute SHA-256 digests;
6. record software commit, model version, dependency snapshot, and random seeds;
7. prohibit regeneration after truth access except for explicitly labeled technical-recovery runs.

## 6. Primary metrics

### Route retrieval
- exact Top-1;
- exact Top-5;
- exact Top-10;
- exact Top-50;
- exact-route MRR.

### Partial recovery
- fraction of targets with any literature-reaction overlap;
- best reaction recall per target;
- mean/median best reaction recall.

### Ranking quality
- rank of first exact route;
- rank of best partial route;
- NDCG or equivalent graded metric where reaction-level relevance permits.

### Calibration and abstention
- calibration of route-confidence scores;
- error rate conditional on confidence;
- abstention rate;
- selective-risk curve.

### Operational
- runtime;
- backend failure rate;
- mapping-limited rate;
- route-count distribution.

## 7. Required ablations

At minimum compare:
1. 2.3 frozen 2D-primary ranking baseline;
2. structural similarity only;
3. enzyme/evidence only;
4. thermodynamic/cofactor features only where available;
5. engine-agreement features only;
6. combined 2.4 model;
7. combined model with each major feature family removed.

Candidate generation must be held fixed for ranking ablations whenever possible.

## 8. Leakage checks

Before any evaluation:
- verify no evaluation pathway IDs in training/development;
- verify no exact reaction-truth rows imported into feature-generation tables;
- verify literature-pathway identity is absent from ranking inputs;
- verify target-family grouping rules;
- verify no post-holdout parameter writes.

## 9. Failure classification

Every evaluation target receives one non-tuning primary failure label:
- exact recovery;
- partial recovery;
- complete predicted route but zero literature overlap;
- no complete route;
- mapping-limited;
- backend runtime failure;
- evaluation artifact failure.

Secondary labels may capture ranking failure, missing evidence, stereochemical mismatch, cofactor mismatch, or unsupported transformation.

## 10. Policy freeze

Before untouched evaluation:
- ranking weights/model frozen;
- thresholds frozen;
- feature definitions frozen;
- normalization rules frozen;
- evaluation code frozen;
- all artifacts hashed.

Any subsequent change creates a new experiment version and requires a new untouched evaluation set.
