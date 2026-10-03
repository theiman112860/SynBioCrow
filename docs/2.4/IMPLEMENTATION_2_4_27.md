# SynBioCrow 2.4.27 — Multivariate Route-Space Diagnostic

2.4.27 compares candidate routes in two independent geometries.

**Evidence space** uses the 13 frozen 2.4.16 ranking variables, z-scored within each development target. PCA and classical MDS summarize the geometry.

**Pathway space** uses the corrected 2.4.18.1 target-excluded internal-anchor similarity profile. Classical MDS summarizes this route-to-literature geometry.

A Mantel-style permutation test compares the pairwise distance matrices. This asks whether candidates that are similar under SynBioCrow's evidence/metadata representation are also similar in literature-pathway proximity.

The goal is diagnostic: identify clusters or axes where evidence-space geometry and pathway-space geometry disagree, and overlay frozen rank, score, backend provenance, and corrected internal-anchor similarity.

No production ranking change, no generation, and no validation/evaluation truth access.
