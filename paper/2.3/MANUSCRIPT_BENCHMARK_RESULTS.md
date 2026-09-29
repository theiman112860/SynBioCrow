# SynBioCrow 2.3 consolidated manuscript benchmark

| Arm | Candidate coverage | Route coverage | Candidates | Routes |
|---|---:|---:|---:|---:|
| doranet | 24/24 (100.0%) | 2/24 (8.3%) | 2128 | 9 |
| retrobiocat2 | 19/24 (79.2%) | 4/24 (16.7%) | 566 | 8 |
| retropath_standalone | 19/24 (79.2%) | 0/24 (0.0%) | 344 | 0 |
| ensemble | 24/24 (100.0%) | 3/24 (12.5%) | 3067 | 26 |

**Interpretation.** The 24-target general-backend benchmark is now complete. DORAnet produced candidates for all 24 targets; RetroBioCat2 and RetroPath standalone each produced candidates for 19/24. Ensemble metrics use persisted ensemble checkpoints where available, V2.8 results for resveratrol/phloretin, and a fixed-parser offline reconstruction for naringenin. BioPKS/RetroTide is reported separately as a runtime/execution limitation rather than a scientific no-hit. No holdout truth was accessed.

Ensemble-only route targets: none.
