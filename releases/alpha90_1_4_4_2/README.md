# SynBioCrow V2.0 Alpha90.1.4.4.2

Schema-Aware Golden Graph Reconstruction & Bridge Qualification.

This release parses each Golden native JSON graph and paired SBML representation independently, matches reaction steps by compound InChIKey signatures, determines whether graph ordering is unique and acyclic, and freezes only performance-blind bridge qualifications. It does not read SynBioCrow prediction routes and performs no scoring.

A case is `GRAPH_BRIDGE_CERTIFIED` only when JSON and SBML cross-validate one-to-one, orientation is uniform, and the reaction dependency graph has a unique acyclic order. Ambiguous, incomplete, or unsupported cases remain outside any later exact-path denominator.

Packaged verification: 5/5 tests passed; all notebook code cells compile.