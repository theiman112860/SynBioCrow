# SynBioCrow 2.4.0 implementation checkpoint

## Scope

This checkpoint introduces additive, standard-library-only contracts for evidence-aware ranking and leakage-resistant benchmark manifests.

It intentionally does **not** change candidate generation.

## Modules

- `synbiocrow/v24/evidence.py`
  - `ReactionEvidence`
  - `RouteEvidence`
  - `RankingFeatureVector`
  - evidence aggregation with explicit missingness

- `synbiocrow/v24/manifests.py`
  - `BenchmarkRecord`
  - `BenchmarkManifest`
  - `SealedPredictionManifest`
  - deterministic canonical manifest hashing
  - evaluation/development leakage guard
  - explicit historical-2.3 non-tunable split

## Scientific invariants

1. Unknown evidence is never converted to positive support.
2. Evidence aggregation cannot promote lifecycle state.
3. The 2.3 historical benchmark is structurally non-tunable.
4. A target cannot occur in both tuning and untouched-evaluation partitions.
5. Predictions cannot be sealed if evaluation truth was accessed first.
6. Candidate generation is unchanged in this checkpoint.

## Next checkpoint

2.4.1 should add an adapter that converts existing SynBioCrow route artifacts into these contracts and emits a feature matrix for **fixed-candidate ranking experiments**.  Only after adapter regression tests pass should a new ranking policy be introduced.
