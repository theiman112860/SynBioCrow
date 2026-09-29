# SynBioCrow 2.2.0 RC2 Release Notes

SynBioCrow 2.2.0 RC2 is a release-candidate maintenance update following published RC1 acceptance testing.

## Changes from RC1

- Updated the engine contract test to include the certified `retropath_standalone` backend in the default registry.
- Bumped package metadata to `2.2.0rc2`.
- Preserved the KNIME-free RetroPath certification policy and evidence.
- No scientific algorithm or pathway-generation behavior was intentionally changed relative to RC1.
- Candidate / Mature / Certified lifecycle semantics remain unchanged.

## Why RC2 exists

Published RC1 acceptance testing found one stale unit-test assertion that still expected the pre-standalone four-backend registry. The runtime itself was correct; the test contract was not. RC2 fixes that inconsistency so the published release artifact can pass its own clean-install test suite.

## RetroPath standalone status

- execution-ready: true
- certification-ready: true
- KNIME required for primary 2.2 runtime: false
- historical compound-transition equivalence fixture: 34/34 exact transitions

## Release policy

RC1 remains immutable and reproducible. RC2 is built from the corrected development lineage and should be subjected to the same published-artifact acceptance process before promotion to final 2.2.0.
