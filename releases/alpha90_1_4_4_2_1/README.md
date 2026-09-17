# SynBioCrow V2.0 Alpha90.1.4.4.2.1

Native Edge Semantics + SBML Boundary-Reaction Reconciliation.

This bounded reference-only repair resolves the two issues isolated by Alpha90.1.4.4.2: native Cytoscape edge interpretation and the systematic extra SBML boundary/source/sink reaction. The two possible JSON edge conventions are evaluated globally against the paired SBML primary-reference representation; a single convention is frozen only when uniquely supported by reference agreement plus the source-native reaction-node InChIKey side. SBML boundary reactions are classified by one frozen corpus-wide rule. No prediction routes are read and no benchmark scoring is performed.

Packaged verification: 5/5 tests passed; all notebook code cells compile.