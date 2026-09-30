# SynBioCrow 2.3 similarity policy

## Decision

The default evidence-similarity policy for SynBioCrow 2.3 is **2D-first / 2D-primary**.

- Primary molecular similarity: Morgan fingerprint / Tanimoto.
- Optional secondary signal: USRCAT 3D similarity when a conformer is available.
- 3D is not used as a universal first-choice ranking signal in 2.3.
- Missing 3D descriptors never count as negative biochemical evidence.

## Basis

The 12-path Galaxy development ablation compared:
1. 2D-only;
2. 3D-first with 2D fallback;
3. 3D-only.

The stricter leave-one-pathway-out route-ranking analysis produced:

- 2D exact Top-1: 1/12
- 2D exact Top-5: 2/12
- 2D exact MRR: 0.75
- 3D-first exact Top-1: 1/12
- 3D-first exact Top-5: 1/12
- 3D-first exact MRR: 0.5294
- 3D-only exact Top-1: 1/12
- 3D-only exact Top-5: 1/12
- 3D-only exact MRR: 0.5294

Leave-one-pathway-out EC-neighbor retrieval also favored 2D slightly:
- 2D Top-1: 9/10, MRR 0.925
- 3D-first Top-1: 8/10, MRR 0.900
- 3D-only Top-1: 8/10, MRR 0.900

3D-first changed the top-ranked route on 10/12 development targets relative to 2D, showing that 3D materially perturbs route ordering without improving validated recovery in this dataset.

Notable examples:
- sabinene exact route: rank 2 under 2D, rank 17 under 3D-first/3D-only;
- valencene exact route: rank 1 under all policies.

## Interpretation

The present data do not support a universal 3D-first default. USRCAT remains valuable as:
- an optional secondary feature;
- a chemical-class-specific diagnostic;
- an ablation signal;
- a future feature for retrospective or experimental enzyme-performance studies.

## Experimental limitation

This computational study cannot determine whether enzymes prioritized by 2D or 3D similarity produce higher titer, yield, productivity, catalytic efficiency, or in-vivo pathway performance. That requires matched experimental testing or carefully harmonized retrospective enzyme-performance data.

## Freeze rule

The 65-path Galaxy benchmark must be evaluated with this policy frozen. The benchmark split must not be used to tune or revise the policy before primary scoring is completed.
