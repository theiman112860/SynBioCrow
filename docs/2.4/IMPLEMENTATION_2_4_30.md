# SynBioCrow 2.4.30 — Nonlinear Multivariate Interaction Audit

This stage tests whether corrected internal-anchor pathway proximity is encoded nonlinearly in the existing development evidence representation.

Models compared:
- frozen 2.4.16 scalar score,
- ridge regression on the 13 evidence variables,
- ridge regression with selected pairwise interactions,
- random forest,
- gradient boosting.

Evaluation:
- five-fold development-only cross-validation within each target,
- CV R², RMSE, and Pearson correlation,
- permutation importance for fitted models,
- gradient-boosting response surfaces for precedent × feasibility, precedent × route length, and feasibility × route length.

This is diagnostic only. It does not change production ranking, invoke generation, or access validation/evaluation truth.
