# SynBioCrow 2.4.33 — Tie-Aware Pairwise Learning-to-Rank

2.4.32 showed that top-decile classification can discriminate high-similarity regions (ROC-AUC roughly 0.75–0.90) but still does not reliably place an arbitrarily selected best route near the top.

A key measurement issue is similarity ties. For dammaradienol, the top-decile threshold equals the maximum similarity, so many candidates are equally best under the current pathway-proximity metric. Evaluating only one arbitrary member of that equivalence set is misleading.

2.4.33 therefore:
- ignores zero-gap similarity pairs during pairwise training,
- trains five-fold out-of-fold pairwise linear logistic and nonlinear histogram-gradient-boosting preference models,
- scores candidates only with models trained on other candidates,
- reports best, median, and worst ranks for the full max-similarity equivalence set,
- includes a standardized linear/nonlinear ensemble.

This is development-only diagnostic evidence. No production ranking change, generation, or validation/evaluation truth access.
