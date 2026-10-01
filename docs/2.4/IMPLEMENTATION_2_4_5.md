# SynBioCrow 2.4.5 — public release-support verification

## Exact public release asset

GitHub release:
- tag: `v2.3.0`
- release: SynBioCrow 2.3.0
- release asset: `SynBioCrow_2_3_RELEASE_SUPPORTING_DATA.zip`

GitHub reports the asset digest:

`2be72abfd4d3fc123d22a09002dc6718c4f7f33b2d0cf4ed40884e8463fd5462`

The mounted local release asset was independently SHA-256 checked and matched that digest.

## What the release-support ZIP contains

The package contains:
- frozen scientific manifest;
- manuscript benchmark summary table;
- benchmark figures;
- manuscript asset review;
- release-package README.

It intentionally does **not** contain the original:
- sealed prediction artifact;
- scored Galaxy benchmark artifact;
- error-analysis artifact;
- similarity-policy artifact;
- frozen manuscript artifact.

The package README explicitly states that those original frozen artifacts are not replaced by the release-support package; only their SHA-256 digests are recorded.

## Verification achieved in 2.4.5

### Byte verified
- public release-support ZIP itself.

### Manifest confirmed
- scientific freeze commit;
- freeze package SHA-256;
- sealed prediction SHA-256;
- scored Galaxy benchmark SHA-256;
- error-analysis SHA-256;
- similarity-policy SHA-256;
- frozen manuscript SHA-256;
- held-out denominator = 65;
- runnable targets = 64;
- benchmark truth used for learning = false;
- post-holdout ranking tuning = false.

### Aggregate benchmark presentation verified
The included CSV independently records:
- ensemble partial recovery 19/65;
- RetroBioCat2 13/65;
- RetroPath standalone 9/65;
- DORAnet 0/65;
- exact Top-10 = 0 for all systems;
- exact Top-50 = 2/65 for RetroPath and ensemble.

The asset review also records the frozen failure counts:
- 42/65 complete routes with zero literature overlap;
- 17/65 partial recovery;
- 2/65 exact recovery;
- 3/65 backend runtime failure;
- 1/65 mapping-limited.

## What is not yet byte verified

The current mounted workspace does not contain files whose SHA-256 values equal:
- sealed predictions: `68fbf9440eecf3103ca70734bc7d71514978fbeab008ba0ab1734cab030f1200`;
- scored benchmark: `4ccfb292295e9017098c061b36baacf1fcacf8ff95182a114b66ee4d7977d809`;
- error analysis: `c7c960a866e3347e7355773648fc875243778a6e6f8ecbc8f2f7937ebefdd764`.

Therefore 2.4.5 reports those three as **manifest-confirmed, not artifact-byte-verified**.

This distinction is mandatory. A checksum recorded in a manifest is not equivalent to possession of the original bytes.

## Scientific firewall

All 2.4.5 outputs remain:
- `historical_only: true`;
- `tuning_permitted: false`.

The verifier has no ranking-model update path.

## Completion criterion

2.4.5 becomes complete byte-level historical verification only if the three original frozen artifacts are supplied and independently match their recorded SHA-256 values.

This completion does not unlock them for tuning. They remain historical-only.

## Next step

Begin the **new 2.4 benchmark construction** in parallel rather than delaying new research on retrieval of historical artifacts.

If the original three frozen files are later recovered, rerun `scripts/v24_verify_release23.py` with the optional artifact paths to complete byte verification.
