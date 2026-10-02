# SynBioCrow 2.4.24 — Route-Level Score Provenance Audit

2.4.23 rules out a single global precedent correction. Removing precedent improves jasmonic acid from rank 433 to 170, but worsens curcumin from 99 to 404. Removing Rhea/EC context gives a smaller jasmonic-acid improvement (433 to 351), while curcumin changes only 99 to 96.

2.4.24 therefore adopts no new ranking weights. It exposes the persisted frozen 2.4.16 score and feature state for each best internal-anchor near miss and representative routes above it (top, quartile positions, and immediate predecessor), including missingness. This is intended to identify score calibration and coverage-adjustment artifacts before changing ranking semantics.

Validation/evaluation truth remains sealed; no generation is invoked.
