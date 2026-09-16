# SynBioCrow V2.0 Alpha90.1.4.4

Validated Golden-20 scorer/bridge connection.

This release consumes the exact sealed Alpha90.1.4.3 predictions and certified Golden primary artifact. It builds and freezes a performance-blind reference bridge before scoring. Only explicit stable reference identifiers (Rhea IDs or explicit reaction SMILES) may qualify a case. Case mapping is based on reference/name semantics only and is frozen before route outcomes are scored. Unbridgeable cases are excluded from the exact-path denominator rather than converted into misses.

The release computes S@1/S@3/S@5/S@10 and MRR only when a nonzero defensible denominator exists; otherwise it explicitly withholds exact-path metrics. No post-hoc aliases, gap reconstruction, prediction rewriting, chemistry/search tuning, or Alpha90.2 authorization is permitted.

Packaged verification: 5/5 tests passed; all notebook code cells compile.