# SynBioCrow 2.2.0 Release Notes

SynBioCrow 2.2.0 promotes the accepted 2.2.0 RC2 lineage to final release.

## Promotion basis

Published RC2 acceptance completed with all gates passing:

- published asset digests: PASS
- package/tag commit match: PASS
- manifest inventory: PASS
- clean install from published source artifact: PASS
- packaged tests: PASS
- M7 release-readiness: PASS
- M9 package check: PASS
- public README/install contract: PASS
- RetroPath standalone equivalence certificate: PASS

Accepted RC2 commit:

`631bac03b9a930a29721b955d1a06515942df23c`

Accepted RC2 source ZIP SHA256:

`cacec275839f4fccb36f5c6732ab99d4c132c92c09e89c6ce3df86c86687dca5`

Acceptance report SHA256:

`db4d601dc82768916f2a80190b3c45dde13c4a864c304f16636f10f937447237`

Acceptance bundle SHA256:

`ba0b5ae9f11ba073a0e2f015b548051bfaa76f2483a5eac63b50c6d8ab293c73`

## Generator/runtime status

- DORAnet: integrated and available
- RetroBioCat2: integrated and available
- BioPKS/RetroTide: integrated; real bridge smoke test passes
- RetroPath standalone: integrated, execution-ready, and certification-ready
- Legacy RetroPath2/KNIME: retained for historical/reference compatibility only
- KNIME is not required for the primary SynBioCrow 2.2 runtime

## RetroPath standalone certification

Certification policy:

`EXACT_COMPOUND_TRANSITION_MULTISET`

Historical r20220104 lycopene fixture result:

- historical transitions: 34
- standalone transitions: 34
- exact compound-transition matches: 34/34
- missing transitions: 0
- novel transitions: 0
- precision: 1.0
- recall: 1.0
- Jaccard: 1.0

Rule/evidence aggregation and some reaction-string serialization differ between the independent standalone implementation and the historical KNIME workflow. These differences are documented and are not treated as compound-transition chemistry differences.

## Scientific lifecycle

Candidate, Mature, and Certified states remain distinct. Computational certification and backend equivalence do not constitute experimental validation of a pathway or DNA construct.

## Final release policy

The final 2.2.0 package is a metadata/release promotion from the accepted RC2 lineage. No intentional scientific algorithm or pathway-generation behavior changes are introduced by the promotion itself.
