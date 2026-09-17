# SynBioCrow V2.0 Alpha90.1.5.8.2

Crash-Safe Checkpoint Recovery Repair.

This recovery-only release never reruns chemistry and never fabricates missing Alpha90.1.5.8 C-branch results from Alpha90.1.5.7. It performs bounded recovery from the exact known Alpha90.1.5.8 runtime/Drive directories, checkpoint JSON files, case CSVs, and partial/final ALL_OUTPUTS ZIPs. The candidate with the largest unique case count is selected deterministically.

Recovered state is persisted to Drive immediately before report generation. If all 20 cases are recovered, the repair regenerates the A/B/C summary and heterogeneous CSV-safe outputs. If fewer than 20 are recoverable, it emits a precise chemistry-resume-required diagnosis and packages that result rather than silently rerunning the campaign.

Future campaign contract: every completed case and telemetry increment must be persisted to Drive before the next case begins; report/CSV generation is downstream of durable checkpoints and cannot strand completed chemistry.

Packaged verification: 5/5 tests passed and all 7 notebook code cells compile after fresh extraction.