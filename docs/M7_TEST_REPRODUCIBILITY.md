# M7 Computational Test and Reproducibility

M7 is the release-readiness verification layer for SynBioCrow 2.2.

## Frozen-policy regression

The sealed 2.1 release files are treated as read-only regression anchors.
M7 verifies that the published scientific invariants still say:

- benchmark-v2 truth was not accessed
- Paper-1 baseline was not modified
- search breadth was unchanged
- Candidate/Mature/Certified separation is preserved
- specialized pathways remain 6 Candidate / 0 Mature / 0 Certified
- the 19 candidate constructs remain recorded
- the BioPKS leading candidate remains an explicit evidence abstention
- the 2.1 scientific payload was not rerun or changed

M7 does not reopen or rescore the protected holdout.

## Hermetic reproducibility panel

A dependency-light panel verifies deterministic core behavior without live web
services or mutable backend data:

- cross-engine DORAnet + RetroBioCat2 composite route recovery
- duplicate reaction-edge provenance merge
- deterministic construct design
- amino-acid preservation during synonymous DNA optimization
- Candidate-only lifecycle

The panel emits a stable digest.

## Runtime matrix

Backend readiness is reported separately from core release readiness.

Optional runtime absence (for example KNIME, RBC2 assets, or BioPKS) is a
warning, not a core failure. This prevents machine-specific external runtime
availability from masquerading as a scientific regression.

## Release-readiness gate

Run:

```bash
python scripts/m7_release_readiness.py
```

The command writes:

`m7_release_readiness_report.json`

and exits nonzero only when a core release blocker is present.

## CI

CI runs the complete unittest suite on Python 3.10–3.12, the pinned DORAnet API
contract, and the M7 release-readiness gate on Python 3.12.
