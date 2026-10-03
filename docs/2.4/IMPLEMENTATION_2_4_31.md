# SynBioCrow 2.4.31 — Out-of-Fold Nonlinear Reranking Counterfactual

2.4.30 showed that nonlinear models extract substantially more development pathway-proximity signal from the existing evidence representation than the frozen 2.4.16 scalar score.

2.4.31 asks the ranking-relevant question: does that extra signal actually move the best corrected internal-anchor route upward?

To avoid same-candidate training leakage, every candidate receives an out-of-fold prediction from a model trained on the other four folds. It compares:
- frozen 2.4.16 rank,
- out-of-fold random forest rank,
- out-of-fold gradient boosting rank,
- mean nonlinear ensemble rank.

This remains development-only diagnostic evidence. It does not change production ranking and does not access validation/evaluation truth.
