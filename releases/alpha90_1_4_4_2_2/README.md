# SynBioCrow V2.0 Alpha90.1.4.4.2.2

SBML Reaction-Role Semantic Reconstruction.

This reference-only repair freezes the resolved Golden JSON pathway semantics from Alpha90.1.4.4.2.1 and replaces the over-aggressive SBML boundary heuristic. An empty stoichiometric side is diagnostic only and is no longer sufficient to classify a reaction as boundary. One special production/output reaction may be excluded only through one corpus-wide native SBML semantic rule derived from reaction IDs/names, objective membership, annotations, groups, and related source-native metadata. No case-specific reaction removal is permitted.

After that special role is removed, the remaining native `reaction_1..reaction_n` sequence must be unique, contiguous, and equal in cardinality to the independently reconstructed JSON ordered steps before a performance-blind ordinal bridge is certified. No SynBioCrow prediction routes are read and no benchmark scoring or tuning is performed.

Packaged verification: 5/5 tests passed; all notebook code cells compile.