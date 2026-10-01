# SynBioCrow 2.4.8 — first real source tranche

## What changed

2.4.8 adds the first real, literature-backed source tranche for the new 2.4
benchmark program.

The tranche contains six structure-resolved targets:
- curcumin;
- bakuchiol;
- dammaradienol;
- methyl isobutyl ketone (MIBK);
- jasmonic acid;
- D-allitol.

Each record has:
- primary DOI;
- PubChem structure identifier;
- normalized target structure;
- chemistry class;
- family key;
- mapping-review state;
- historical-2.3 exclusion state and explicit basis.

## Important conservative gate

The full frozen 65-target Galaxy target list is not present in the public
release-support package currently available to 2.4.

Therefore post-2022 publication date is **not** treated as automatic proof that a
target is absent from the 2.3 holdout.

2.4.8 introduces an explicit state machine:
- `pending`;
- `verified_excluded`;
- `blocked_historical_23`.

Only `verified_excluded` + `mapping_quality=reviewed` records are promotable
to the development/validation benchmark.

## Current tranche readiness

Five records intentionally remain pending frozen-2.3 target cross-check.

MIBK is provisionally `verified_excluded` based on the 2025 primary report of
a novel de novo biosynthetic route from glucose, which postdates the
Galaxy-SynBioCAD benchmark lineage. If the exact 65-target frozen list is later
recovered, this record must still be mechanically cross-checked.

## Scientific value

This checkpoint begins real dataset construction while preserving the benchmark
firewall.

It avoids the two dangerous shortcuts:
1. assuming every recent publication is automatically a new target;
2. reusing the known 2.3 holdout because it is convenient.

## Next checkpoint

2.4.9 should recover or reconstruct the exact frozen 65-target target-identity
blacklist and mechanically resolve all pending tranche records.

Only then should the first development/validation split be frozen.
