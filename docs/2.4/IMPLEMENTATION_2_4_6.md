# SynBioCrow 2.4.6 — new benchmark construction framework

## Purpose

2.4.6 begins the genuinely new 2.4 evaluation program.

It does **not** populate a benchmark by reusing the frozen 65-path Galaxy holdout.
Instead, it makes benchmark intake and sealing rules executable before any new
ranking optimization begins.

## New components

### `Benchmark24Record`
Public metadata for a prospective benchmark target:
- target identity and normalized representation;
- pathway-family grouping;
- source provenance;
- chemistry class;
- mapping quality;
- route length when known;
- evidence-density class;
- explicit frozen-2.3 membership flag.

### Deterministic family-aware split
Assignments are determined from:
- a versioned split salt;
- `family_id`;
- fixed development/validation/evaluation fractions.

Pathway truth is not consulted.

Related target families remain in one split to reduce leakage.

### External truth lock
Untouched evaluation truth is not stored in the working repository.

The public benchmark can store only:
- evaluation record count;
- external truth artifact SHA-256;
- optional escrow/location note;
- proof that the truth artifact was fixed before prediction sealing.

### Fail-closed leakage checks
Construction fails if:
- duplicate record IDs occur;
- one target appears across multiple splits;
- one family appears across multiple splits;
- a known frozen 2.3 record enters development/validation;
- evaluation truth is configured as internal;
- malformed SHA-256 values are supplied.

## Default split

The default target is:
- 60% development;
- 20% validation;
- 20% untouched evaluation.

Because assignment is family grouped, exact record percentages may differ.

The realized split distribution must be reported.

## What is not yet done

2.4.6 is the benchmark **construction machinery**, not the final dataset.

No new pathway records are claimed in this checkpoint.

The next step is source acquisition and curation from literature/database material
that was not part of the frozen 2.3 holdout, followed by:
1. deduplication;
2. family assignment;
3. mapping review;
4. source snapshot hashing;
5. external evaluation-truth sealing;
6. public manifest freeze.

## Scientific rule

The new 2.4 ranking hypothesis will be considered tested only on the untouched
evaluation split produced by this framework after ranking policy freeze.
