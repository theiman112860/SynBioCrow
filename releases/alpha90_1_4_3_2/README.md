# SynBioCrow V2.0 Alpha90.1.4.3.2

Frozen Golden Pathway Concordance Audit.

This diagnostic release preserves the official Alpha90.1.4.3.1 exact-path results unchanged: route-positive coverage 18/20, ordered product-identity S@1/S@3/S@5/S@10 = 0/20, and MRR = 0.0. It does not rerun Alpha87.11, generate new routes, modify the frozen Golden bridge, choose aliases, or tune the benchmark.

Against the same immutable prediction seal and bridge manifest, it computes diagnostic-only concordance measures: Golden identity recovery, forward/reverse ordered longest-common-subsequence overlap, positional matches, prefix/suffix agreement, path-length delta, first divergence, and orientation diagnostics. Partial concordance is explicitly prohibited from being promoted to exact success.

Packaged verification: 5/5 tests passed; all notebook code cells compile; a full dry run against the real frozen inputs completed successfully.