# SynBioCrow 2.4.18 — Internal-Anchor Structural Near-Miss Audit

2.4.17 found that all exact anchor hits were the final target itself. No internal literature anchor was recovered by exact canonical structure. Therefore 2.4.17 is not evidence of literature-pathway recovery.

2.4.18 excludes the target molecule and measures Morgan/Tanimoto structural proximity between molecules actually appearing in each persisted development candidate and the literature-supported internal pathway anchors.

This is diagnostic, not tuning. It asks whether failures are near misses consistent with representation/mapping or whether candidate chemistry occupies a different region of chemical space. The frozen 2.4.16 ordering is retained only to report where the best near-miss candidates currently rank. Validation/evaluation truth remains sealed.
