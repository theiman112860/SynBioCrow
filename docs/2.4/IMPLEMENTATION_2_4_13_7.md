# SynBioCrow 2.4.13.7 — reachability and identity-granularity audit

2.4.13.6.2 showed that MIBK and jasmonic-acid graphs contain an exact acetate
sink globally while strict AND-route closure remains zero. It also exposed
cross-engine compound pairs with Morgan/Tanimoto 1.0 but different strict
InChIKeys, especially for dammaradienol and jasmonic acid.

This checkpoint does not add reactions and does not tune search.

It measures:
1. sink nodes present anywhere in the graph;
2. sink nodes reachable from the requested target under OR reachability;
3. full strict hypergraph/AND closure (unchanged);
4. a diagnostic-only connectivity graph in which stereochemical identity is
   removed before canonical SMILES comparison;
5. the number of strict nodes and cross-engine identity groups collapsed by
   that connectivity representation;
6. whether the existing reaction set closes under connectivity-level identity.

Any connectivity-level route is diagnostic evidence only. It must not be
promoted as a stereochemically certified route without subsequent evidence.
Validation records remain sealed.
