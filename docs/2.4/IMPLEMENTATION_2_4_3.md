# SynBioCrow 2.4.3 — exact reconstruction of frozen 2.3 breadth-benchmark routes

## Artifact

`SynBioCrow_2_3_MANUSCRIPT_BENCHMARK_V2_RESULTS(1).zip`

SHA-256:

`c4f61f1970872a2a6a47cc7615b10f7866f720c8ebef34f983933742a51a19a1`

The bundle contains the 24-target SynBioCrow 2.3 manuscript **breadth benchmark** with persisted candidate, graph-summary, result and route state.

It is not the separate 65-path Galaxy held-out literature benchmark.

## Key schema

Individual backend outputs persist `PathwayCandidate` records with:
- `candidate_id`
- `source_backends`
- `steps[].reaction`
- `steps[].rule_id`
- `steps[].source_backend`
- nested backend metadata/evidence

Persisted ensemble routes are ordered lists of graph edge identifiers such as:

`rxn:5d08421cd957d457c203b145`

## Exact route reconstruction

2.4.3 imports the released `v2.3.0` reaction-graph implementation and rebuilds the graph from persisted candidates.

The released edge identifier is:

1. resolve parent and precursor compounds using released canonical identity logic;
2. form the payload from canonical parent key plus sorted precursor keys;
3. SHA-256 the payload;
4. use the first 24 hexadecimal characters with prefix `rxn:`.

A sampled complete 1,4-butanediol ensemble route reproduced **4/4 persisted edge IDs exactly** before this implementation was committed.

The adapter now fails closed when:
- any persisted route edge does not reconstruct;
- reconstructed graph edge count differs from the persisted graph summary;
- the bundle does not explicitly assert `truth_accessed: false`.

## Scientific firewall

This module reads only persisted generation-state material needed for route reconstruction.

It does not consume literature benchmark truth and writes manifests with:
- `historical_only: true`
- `tuning_permitted: false`
- `generation_invoked: false`
- `truth_consumed: false`

Thus this artifact may validate compatibility and reproduce published breadth behavior, but it cannot be used to tune 2.4.

## Evidence extraction

Evidence is derived only from explicit persisted fields, including:
- EC annotations;
- Rhea identifiers if present;
- RetroBioCat precedent records;
- explicit enzyme names/choices;
- explicit thermodynamic values if present;
- engine/candidate/rule provenance.

Missing values remain missing.

## Resulting role in 2.4

2.4.3 establishes that SynBioCrow can reconstruct the exact persisted 2.3 route graph and convert it into the new evidence feature contracts without rerunning generators.

The next scientifically decisive artifact is still the frozen **65-path Galaxy held-out candidate/scoring bundle**, which is needed only to reproduce the published 2.3 ranking baseline. It remains historical and non-tunable.
