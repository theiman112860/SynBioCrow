# SynBioCrow 2.4.13.6 — cross-engine frontier diagnostics

2.4.13.5 exposed 4,308 RetroBioCat2 explored partial pathways across the four
frozen development targets and merged them with DORAnet. No sink-connected
route closed. Curcumin produced one composite reaction edge; the other three
targets produced none.

2.4.13.6 keeps the same frozen targets, sink panel, and search bounds and adds
truth-independent graph-frontier diagnostics:

- unique compounds contributed by each backend;
- exact compound overlap between DORAnet and RetroBioCat2;
- top non-identical cross-engine compound pairs by Morgan/Tanimoto similarity;
- each backend's nearest explored compound to every frozen sink.

These measurements distinguish three possible next repairs: identity
normalization, graph bridging between chemically near frontiers, or inadequate
sink/coverage reach. No validation truth is accessed and no ranking/search
parameter is tuned.
