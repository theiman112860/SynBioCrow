# SynBioCrow 2.4.14 — Evidence-Aware Route Discrimination

## Purpose

2.4.14 ends the MIBK-specific generator-repair loop and moves SynBioCrow 2.4 back to its primary research objective: discriminate among persisted candidate pathways using biochemical evidence and transparent route-level features.

## Scientific boundary

- Generation is **not invoked** in this stage.
- Inputs are persisted artifacts for the four development records in `split_manifest_2_4_11.json`.
- Validation records (`post2022-bakuchiol-2024`, `post2022-allitol-2025`) are sealed and are not opened by the ranking runner.
- No evaluation truth is accessed.
- The historical 65-path Galaxy benchmark remains frozen and is not a tuning set.
- Missing evidence remains missing; it is never silently converted to negative evidence.
- Candidate/Mature/Certified lifecycle state is not promoted by ranking.

## Ranked objects

The runner ranks:
1. every persisted candidate pathway in each development artifact, even when strict frozen-sink closure is zero; and
2. any strict ensemble routes that are present.

This avoids conflating route generation failure with the downstream discrimination problem.

## Features

The provisional transparent policy includes:
- explicit reaction-evidence fraction
- reviewed-enzyme fraction
- EC-evidence fraction
- exact and connectivity-level Rhea fractions
- thermodynamic coverage
- mapping confidence when present
- independent-engine count
- cross-engine edge fraction
- route length
- unsupported-edge fraction
- currency/cofactor burden

Observed weighted features are normalized over observed evidence, then multiplied by an evidence-coverage ceiling.

## Calibration

No route-level gold labels currently exist for the four development targets. Therefore the default 2.4.14 run does **not** pretend to train a model.

A deterministic development-only calibration interface is included for later use when genuine development labels are available. The fitter refuses validation/evaluation rows.

## Outputs

- `feature_rows.json`
- `ranked_routes.json`
- `ranked_routes.csv`
- `ranking_policy.json`
- `discrimination_summary.json`

These outputs are development artifacts only and are not certification results.
