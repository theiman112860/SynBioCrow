# SynBioCrow 2.4.2 — observed-schema regression + provisional ranking harness

## Historical artifact inspected

Uploaded artifact:
`SynBioCrow_Engine_Core_VNEXT_0_3_51_7_ALL_OUTPUTS (1)(1).zip`

SHA-256:
`32947b28537e97a886774e7c7a04bd52222242e3903f58ac91363a7489ba2f5b`

Release metadata identifies it as:
- `EngineCore-vNext0.3.51.7`
- `2.1.0.dev72.7`

It is therefore **not** a final SynBioCrow 2.3 held-out benchmark artifact.

## What it contains

The scientific-gate assessment contains six BioPKS+DORAnet Candidate pathways, six reaction records, pinned upstream rule provenance, route feasibility values, explicit evidence gaps, and `benchmark_v2_truth_accessed: false`.

All six remain Candidate; none are Mature or Certified.

## Observed schema additions

The conservative adapter now recognizes two fields because they were directly observed:
- route ID: `candidate_pathway_id`
- reaction representation: `reactions[].raw`

The route-level `backend` is propagated to reaction engine provenance only when the reaction lacks its own engine field.

No broad permissive aliases were added.

## Evidence interpretation

Explicit strings such as:
- `NO_DIRECT_ENZYME_IDENTITY_FOR_THIS_EXACT_REACTION`
- `NOT_QUANTIFIED_NO_FABRICATION`

are **not** converted into positive evidence.

The historical `net_feasibility` field is not treated as ground-truth biochemical evidence by the 2.4 evidence contract.

## Ranking harness

2.4.2 adds provisional, interpretable fixed-candidate policies:
- frozen-style 2D-only baseline;
- 2D + reaction evidence;
- 2D + reviewed-enzyme evidence;
- 2D + engine agreement;
- provisional combined policy.

These weights are scaffolding for development experiments, not a frozen 2.4 scientific policy.

Missing weighted features are omitted from the score and the number of observed weighted features is reported.

## Critical limitation

This historical artifact is suitable for adapter regression and evidence-missingness behavior. It is **not** suitable for testing improvement over the final 2.3 Galaxy ranking because it predates 2.3 and contains a narrow BioPKS+DORAnet candidate set.

The next required artifact remains a frozen final-2.3 candidate-route/scoring bundle for the first authentic fixed-candidate baseline comparison.
