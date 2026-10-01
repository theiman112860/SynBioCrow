# SynBioCrow 2.4 benchmark workspace

This directory contains only **public benchmark metadata and templates**.

It must not contain the untouched evaluation truth before prediction sealing.

## Intake

Create candidate records as JSONL using `record_template.jsonl`.

Required fields:
- `record_id`
- `target_id`
- `target_name`
- `normalized_target`
- `family_id`
- `source_ids`

Optional metadata:
- chemistry class
- mapping quality
- route length
- evidence density
- `historical_23_member`

## Split construction

Run:

`python scripts/v24_build_benchmark_plan.py records.jsonl`

The split is deterministic and grouped by `family_id`; it does not inspect pathway truth.

Default allocation:
- 60% development
- 20% validation
- 20% untouched evaluation

Exact realized proportions depend on family grouping.

## Truth handling

Untouched-evaluation pathway truth must be stored outside the working repository.

Only its SHA-256 digest may appear in the public benchmark manifest before prediction generation.

Do not commit:
- literature route sequences for evaluation records;
- exact reaction truth for evaluation records;
- evaluation EC/enzyme truth that would reveal pathway identity;
- post-holdout error labels.

## Frozen 2.3 exclusion

Any record known to be part of the frozen 2.3 Galaxy holdout must set:

`"historical_23_member": true`

Such records are rejected from development and validation.
