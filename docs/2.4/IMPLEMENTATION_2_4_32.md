# SynBioCrow 2.4.32 — High-Tail Out-of-Fold Ranking Audit

2.4.31 showed that nonlinear regression of mean pathway similarity is not a safe reranking objective. Although 2.4.30 nonlinear models had strong cross-validated correlation with similarity, the best internal-anchor route worsened severely for dammaradienol, jasmonic acid, and MIBK under OOF regression ranking.

2.4.32 changes the objective from predicting mean similarity to discriminating the rare high-similarity tail within each development target.

Default definition:
- top 10% of corrected internal-anchor similarity within each target.

Models:
- out-of-fold random forest classifier,
- out-of-fold gradient boosting classifier,
- mean-probability ensemble.

Reported diagnostics:
- ROC AUC,
- average precision,
- precision@10,
- precision@50,
- recall@50,
- rank of the single best corrected internal-anchor candidate.

This remains development-only diagnostic evidence. It does not change production ranking, invoke generation, or access validation/evaluation truth.
