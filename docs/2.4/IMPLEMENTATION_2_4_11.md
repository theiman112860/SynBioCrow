# SynBioCrow 2.4.11 — first frozen development/validation split

## 2.4.10 recovery result

The successful 2.4.10 Colab recovery used Galaxy-SynBioCAD Supplementary Dataset 2:

- source bytes: 56,329;
- source SHA-256: `bb15a7729bb5dbd0d6a03caeb90d511b029b13f11ac3f82949f6fddc7ec4f366`;
- exact held-out pathways: 65;
- unique held-out target structures: 48;
- target-blacklist SHA-256: `0f28013c770acdc4d7e8afd5112ce043f930c70ba4fc642bb624947c5dea6eb1`;
- source repairs: 1, the previously audited malformed InChI in `literature_10`;
- pending tranche records: 0;
- historical-overlap blocks: 0;
- verified-excluded new targets: 6/6.

The benchmark firewall therefore passes.

## Frozen pilot split

Because the first source tranche contains only six eligible targets, 2.4.11
freezes a pilot 4/2 development/validation split rather than presenting it as a
final large benchmark.

Policy:

`SHA-256(record_id) ascending; first four = development; final two = validation`

Development:
- methyl isobutyl ketone;
- jasmonic acid;
- dammaradienol;
- curcumin.

Untouched validation:
- bakuchiol;
- D-allitol.

Split-manifest SHA-256:

`d9ad5c58ae11cb1798974341231e3854cf09ff34cb1d552836caa551707e0f98`

## Rules from this checkpoint onward

1. Validation membership is immutable for this pilot.
2. Validation truth must not be used for scoring-weight optimization.
3. New targets may be appended only through a new tranche with the same
   historical-exclusion gate.
4. Any larger benchmark gets a new manifest/version rather than silently
   changing this split.
5. The frozen 2.3 Galaxy benchmark remains historical evidence only and is not a
   2.4 tuning set.

## Next checkpoint

2.4.12 should begin biochemical discrimination on the four development targets:
reaction identity/compatibility, enzyme precedent, EC evidence, cofactors,
thermodynamic evidence where available, and pathway context. The two validation
targets remain sealed until a scoring policy is frozen.
