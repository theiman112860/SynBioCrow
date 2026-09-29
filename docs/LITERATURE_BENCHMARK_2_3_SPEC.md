# SynBioCrow 2.3 literature-grounded pathway benchmark

## Purpose

The initial 24-target panel characterizes breadth, runtime behavior, failure modes, and route diversity. It is not sufficient to establish biological usefulness of the predicted pathways.

This benchmark asks a stronger question:

> Given a target compound, a chassis (or explicit precursor set), and a literature-supported engineered biosynthetic pathway, can SynBioCrow recover the known pathway or a close biochemical equivalent, and how highly is it ranked?

The design follows the style of Galaxy-SynBioCAD and RetroBioCat literature validation while retaining SynBioCrow's explicit provenance/evidence semantics.

## Benchmark unit

One benchmark record corresponds to one literature-supported pathway and contains target compound, chassis/source-metabolite set, literature citation, ordered heterologous reactions, substrates/products, EC numbers where reported, enzymes/genes where reported, experimental status, pathway length, and notes on cofactors/direction.

## Inclusion policy

Include a pathway only if the source supports enough chemistry to reconstruct the main substrate/product transformation sequence.

Preferred evidence order:
1. peer-reviewed experimental pathway demonstrated in an engineered organism;
2. peer-reviewed in vitro multi-enzyme cascade with explicit transformations;
3. curated benchmark pathway from a published retrosynthesis study whose provenance points to primary literature.

Do not silently infer missing reactions, enzymes, or cofactors.

## Split policy

Keep benchmark truth independent of ranking-model fitting. Use development, benchmark, and optional sealed holdout splits. The final manuscript must state exactly which records were visible during development.

## Pathway matching

Evaluate at multiple levels rather than relying on one arbitrary threshold.

Reaction-level metrics: exact normalized reaction overlap, precision, recall, F1, and ordered longest-common-subsequence fraction.

Pathway-level metrics: reaction recall, reaction precision, ordered overlap, endpoint agreement, and route-length difference.

Top-K recovery: Top 1, 5, 10, 25, and 50; also record best matching rank, best matching score, and number of generated routes considered.

## Per-engine comparison

Evaluate DORAnet, RetroBioCat2, RetroPath standalone, and the reaction-graph ensemble under the same target/chassis definition. Include BioPKS/RetroTide only when its specialized runtime is sufficiently reliable for the relevant subset.

## Ensemble-specific endpoints

Report separately whether: (1) a known pathway is recovered by an individual engine; (2) recovered by the ensemble; (3) ensemble improves best rank; (4) ensemble increases reaction recall; (5) a route contains edges from more than one backend; (6) a known pathway is recovered only through cross-engine composition.

## Similarity-policy ablation

Compare 3D-first with 2D fallback, 2D-only, and 3D-only-when-available using fixed generated route/evidence pools where possible.

Primary outcomes: literature-pathway Top-K recovery, reaction/evidence precedent Top-K recovery, best-match rank, enzyme-evidence availability, routes surviving evidence/ranking thresholds, runtime, conformer success/fallback rate.

A 3D benefit should be claimed only when it improves a validation endpoint, not merely because it returns different analogues.

## Suggested manuscript endpoints

Primary: proportion of literature pathways recovered in Top 10 and Top 50, median best-match rank, and median reaction recall of the best prediction.

Secondary: exact route recovery, partial route recovery, ensemble rank improvement, multi-backend route fraction, runtime, failure/abstention rates, and 3D-vs-2D ablation effects.

## Initial target size

Start with 10-15 development pathways to validate matching and curation. Then expand toward roughly 40-60 targets/pathways if curation quality and reproducible execution permit. Quality of route definitions matters more than matching Galaxy-SynBioCAD's dataset size exactly.
