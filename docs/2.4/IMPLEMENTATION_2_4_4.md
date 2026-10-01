# SynBioCrow 2.4.4 — historical baseline readiness

## Purpose

2.4.4 makes the boundary between **historical reproduction** and **new 2.4 model development** executable.

It does not claim that the 24-target breadth bundle contains the frozen 2D route-ranking scores used in the later Galaxy benchmark.

## Breadth-benchmark result

The 2.3 manuscript breadth bundle can reconstruct:
- persisted candidate records;
- exact ensemble graph edge IDs;
- exact persisted route membership/order of edge IDs;
- backend/rule/candidate provenance;
- explicit evidence fields present in persisted metadata.

It does **not** provide a frozen route-level 2D score for every reconstructed ensemble route.

Therefore 2.4.4 records:

`historical_2d_baseline_reproducible: false`

for route sets lacking those scores.

This is a deliberate fail-closed result. A deterministic route-ID tie break is not mislabeled as the historical 2D baseline.

## Descriptive policy diagnostics

The runner may calculate provisional 2.4 policy orderings on the same fixed candidate pool to verify software behavior.

These rows are marked:
- `historical_only: true`
- `tuning_permitted: false`
- `truth_consumed: false`

No route movement in this historical artifact may be used to choose or change 2.4 weights.

## Frozen Galaxy holdout contract

2.4.4 adds a strict historical contract for the published 65-path Galaxy result:

- denominator: 65
- runnable: 64
- mapping-limited target: `literature_10`
- ensemble partial recovery: 19/65
- RetroBioCat2 partial recovery: 13/65
- RetroPath partial recovery: 9/65
- DORAnet partial recovery: 0/65
- exact Top-50 connectivity routes: 2/65 for RetroPath and ensemble
- exact Top-10: 0 for all systems

Frozen artifact hashes retained by the contract:
- sealed predictions: `68fbf9440eecf3103ca70734bc7d71514978fbeab008ba0ab1734cab030f1200`
- scored benchmark: `4ccfb292295e9017098c061b36baacf1fcacf8ff95182a114b66ee4d7977d809`
- error analysis: `c7c960a866e3347e7355773648fc875243778a6e6f8ecbc8f2f7937ebefdd764`

The contract may verify a future uploaded aggregate historical summary. It does not expose a tuning API and intentionally does not accept arbitrary per-target truth rows.

## Scientific interpretation

2.4.4 answers a methodological question:

> What portion of the published 2.3 behavior can be reproduced from the persisted generation artifacts alone?

Answer:
- exact route graph reconstruction: yes;
- evidence/provenance reconstruction: yes, where explicitly persisted;
- published Galaxy route ranking: not from the 24-target breadth bundle alone.

That missing distinction is now represented explicitly in code instead of being left to analyst judgment.

## Next checkpoint

2.4.5 should ingest the frozen 65-path sealed-prediction/scored-summary package when available and verify the published historical metrics and exact route ranks **without permitting any 2.4 parameter change**.

New 2.4 ranking development still requires a separate development/validation dataset and a new untouched evaluation set.
