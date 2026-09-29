# RetroPath Standalone Equivalence Certificate

SynBioCrow 2.2 RC uses the KNIME-free `TraceLD/retropath` standalone engine as the primary RetroPath-compatible runtime. The historical `brsynth/retropath2-wrapper` + KNIME stack remains available only as a legacy/reference implementation.

## Validation fixture

Historical source:

`brsynth/retropath2-wrapper` commit `d9948aa1672873d1e3c1905a355f62f714946e67`

Fixture:

`tests/data/lycopene/out/r20220104/results.7325.csv`

Standalone runtime:

`TraceLD/retropath` release `v0.0.1-alpha`

Validated Linux release archive SHA256:

`0cf49589334c99750bfd1d495ad47356498ab4205cf5b227c2c3c28212238755`

## Chemical equivalence result

Certification policy:

`EXACT_COMPOUND_TRANSITION_MULTISET`

Compared fields:

- Substrate InChI
- Product InChI
- In Sink
- Iteration

Result:

- historical rows: 34
- standalone rows: 34
- exact compound-transition match: PASS
- intersection: 34
- missing from standalone: 0
- novel in standalone: 0
- precision: 1.0
- recall: 1.0
- Jaccard: 1.0

## Known representation differences

The independent standalone implementation is not byte-for-byte identical to the historical KNIME workflow output.

Observed comparison results:

- reaction-string projection: 26/34 matching
- rule-transition projection: 12/34 matching
- evidence-transition projection: 8/34 matching

These differences are treated as implementation-level serialization / rule-evidence aggregation differences. They do not alter the validated compound-transition graph for this fixture.

## Release policy

For SynBioCrow 2.2 RC:

- `retropath_standalone.execution_ready = true`
- `retropath_standalone.certification_ready = true`
- legacy `retropath2`/KNIME may remain non-execution-ready
- KNIME is not required for the primary SynBioCrow 2.2 RetroPath runtime
- Candidate/Mature/Certified lifecycle rules remain unchanged
- this certificate does not imply experimental validation of generated chemistry
