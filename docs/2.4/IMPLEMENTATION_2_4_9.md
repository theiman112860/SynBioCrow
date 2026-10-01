# SynBioCrow 2.4.9 — frozen 2.3 pathway blacklist recovery

## Result

The released 2.3 normalization code provides a deterministic split rule over the
77 Galaxy-SynBioCAD literature pathways:

1. pathway IDs are hashed with SHA-256;
2. IDs are ordered by digest;
3. the first 12 become development;
4. the remaining 65 become the held-out benchmark.

2.4.9 reconstructs those 65 held-out pathway IDs exactly.

Held-out pathway-ID-set SHA-256:

`c7c43814c973e941172b18b8745ba7e79bcaa4e4e193bfde473b796415bbd58f`

The recovered set includes the known mapping-limited record `literature_10`.

## Important distinction

This reconstructs the exact **pathway-ID blacklist**, but not yet the complete
**target-name/structure blacklist**.

The public v2.3.0 release-support package does not contain
`galaxy_literature_benchmark_normalized.json`, and the original Supplementary
Dataset 2 XLSX was not available in the current workspace.

Therefore target overlap for the new 2.4 tranche remains unresolved until one of
those source-truth artifacts is recovered.

## Correction to 2.4.8

MIBK has been returned from `verified_excluded` to `pending`.

A 2025 first de novo biosynthesis report proves novelty of that route, not absence
of the compound from the 2022 Galaxy target set.

No 2.4.8 record is currently promotable to development/validation.

## Next completion condition

2.4.9 target-identity recovery completes when either:

- `galaxy_literature_benchmark_normalized.json` is recovered, or
- the original Galaxy-SynBioCAD Supplementary Dataset 2 XLSX is supplied.

The recovery script should then map all 77 pathway IDs to canonical target
structures, select the exact 65 held-out IDs, deduplicate target identities, and
mechanically resolve every pending 2.4 tranche record.

Until then, the split freeze remains blocked.
