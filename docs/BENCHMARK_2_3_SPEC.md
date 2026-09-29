# SynBioCrow 2.3 manuscript benchmark specification

## Purpose

This benchmark is the first scientific-analysis milestone after the frozen SynBioCrow 2.2.0 release. It is designed to quantify **breadth, complementarity, route recovery, abstention/failure behavior, and runtime** across generator families without modifying the 2.2 release or weakening existing holdout boundaries.

## Experimental unit

One benchmark target is one JSON record with:

- `target_id`
- `target_name`
- `target_smiles`
- `chemical_class`
- `sink_smiles`
- optional `notes`
- optional `blind_group`

The benchmark runner does not require truth labels. If truth or reference routes exist, they must be evaluated by a separate scoring step that respects the existing sealed/blinded contract.

## Generator arms

Primary manuscript arms:

1. `doranet`
2. `retrobiocat2`
3. `retropath_standalone`
4. `biopks_retrotide` when applicable
5. all available primary generators combined

The legacy KNIME `retropath2` backend is excluded from the primary benchmark because SynBioCrow 2.2 established `retropath_standalone` as the primary certified runtime. It may be used in reference-only diagnostics.

## Per-target measurements

For each backend arm:

- backend readiness
- execution status
- wall-clock runtime
- candidate count
- route count to supplied sink set
- graph compound count
- graph edge count
- error type/message if execution fails

For the ensemble arm:

- union candidate count
- union route count
- graph compound count
- graph edge count
- composite edge count
- backends contributing to the union graph

## Derived manuscript metrics

Across the panel:

### Coverage
Fraction of targets for which a backend produces at least one Candidate.

### Route-completion coverage
Fraction of targets for which at least one route reaches the supplied sink set.

### Ensemble gain
Targets solved by the ensemble but by no individual backend.

### Complementarity
For each target and backend, number/fraction of reaction edges uniquely contributed by that backend to the union graph.

### Overlap
Pairwise reaction-edge overlap between backend outputs after canonical reaction-graph normalization.

### Failure taxonomy
Counts of:
- COMPLETE
- NO_HIT
- SKIPPED_UNAVAILABLE
- ERROR
- timeout (when explicitly surfaced)
- configuration/runtime missing

### Runtime
Median, IQR, and range by backend and chemical class.

## Scientific safeguards

- Candidate/Mature/Certified lifecycle semantics remain unchanged.
- Generator output does not constitute evidence.
- Missing runtime/data is reported as unavailable, not zero scientific capability.
- Missing truth is not inferred.
- No blind/holdout truth is accessed by the generation runner.
- Panel metadata must identify any targets whose selection was informed by known benchmark truth.

## Freeze policy

Every manuscript benchmark run must record:

- Git commit
- panel SHA-256
- runtime versions when available
- backend readiness snapshot
- per-target raw JSON result
- aggregate JSON/CSV summary
- run manifest SHA-256

Figures/tables should be generated only from frozen result artifacts.
