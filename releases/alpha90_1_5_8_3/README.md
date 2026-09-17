# SynBioCrow V2.0 Alpha90.1.5.8.3

Crash-Safe Campaign Rerun.

This release reruns the Alpha90.1.5.8 A/B/C campaign with durable per-case Drive persistence. Each completed case is atomically written locally, atomically copied to `/content/drive/MyDrive/SynBioCrow/alpha90_1_5_8_3/checkpoint.json`, accompanied by telemetry snapshots, and read-back verified before the next case begins. The notebook resumes by case ID and skips already durable cases.

The heterogeneous telemetry writer computes the union of keys across all rows before CSV serialization, preventing the late `DictWriter` field mismatch that terminated Alpha90.1.5.8 after all 20 cases had completed. Final report generation is downstream of durable scientific state.

Golden information remains post-hoc only; the A/B/C proposal, specialist recovery, and continuity-ranking logic is unchanged from Alpha90.1.5.8. The package remains self-contained with the validated engine overlay, consolidated specialist engines, bounded Drive discovery, RDKit certification, live progress/elapsed/ETA, Drive-first ALL_OUTPUTS persistence, and rescue download.

Packaged verification: 6/6 tests passed from the final ZIP and all notebook code cells compile after fresh extraction.