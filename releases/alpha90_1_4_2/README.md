# SynBioCrow V2.0 Alpha90.1.4.2

Golden input-representation contract audit and normalization repair.

Two Golden targets are executed twice through the exact frozen Alpha87.11 API: original InChI and identity-preserving RDKit canonical SMILES. Molecular identity is checked by InChIKey roundtrip. No chemistry, search-depth, timeout, ranking, sink, or benchmark-specific tuning changes are permitted. A normalization rule is authorized only if representation alone rescues both probes.

Packaged verification: 5/5 tests passed; notebook code cells compile.
