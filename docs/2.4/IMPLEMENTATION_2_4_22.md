# SynBioCrow 2.4.22 — Pairwise Ranking Suppression Audit

2.4.21 is rejected as a ranking policy. The best corrected internal-anchor candidate worsened from rank 99 to 110 for curcumin and from 433 to 1822 for jasmonic acid. Marginal positive Spearman associations therefore did not compose safely under equal weighting.

2.4.22 returns to the frozen 2.4.16 ordering and performs no reranking. For each ranking-limited development target it takes the best corrected internal-anchor candidate and compares its feature values directly with every candidate currently ranked above it. The output reports the fraction of outranking candidates with greater/lower values, the median above-candidate value, and the target-minus-median difference for each feature.

This diagnoses which existing signals systematically suppress the biologically relevant near-miss candidate. 2.4.21 remains preserved as a negative experiment. Validation/evaluation truth remains sealed.
