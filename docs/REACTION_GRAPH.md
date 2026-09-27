# Reaction-level ensemble graph

Status: **implemented for SynBioCrow 2.2 consolidation**.

This replaces simple whole-pathway deduplication with a shared reaction
hypergraph across generator outputs.

## Identity policy

Molecular tokens that parse as SMILES are canonicalized with RDKit and keyed
primarily by InChIKey. This allows the same molecule emitted by DORAnet and
RetroBioCat2 to become the same graph node.

Tokens that do **not** parse as molecular structures are preserved as
source-scoped raw identities. In particular, unresolved RetroPath compound IDs
are not silently joined to another engine's molecule.

## Reaction hyperedges

Each normalized reaction becomes a retrosynthetic hyperedge:

`parent compound -> precursor set`

Every edge retains contributing backend(s), candidate IDs, rule IDs, original
reaction text, and backend-specific provenance. If two engines produce the same
canonical transformation, a single edge retains both engine identities.

## Composite route discovery

`EnsembleGraph.find_routes()` performs bounded structural closure from a
target node to a supplied sink set. A returned route may contain edges from
multiple engines.

This is the first implementation of the central SynBioCrow ensemble hypothesis:
a complete route can be assembled from reaction edges contributed by different
independent generators even when no single generator returned the complete
route.

## Deliberate limits

Graph closure is **not certification**. It does not imply reaction evidence,
thermodynamic feasibility, enzyme identity, expression, or experimental
viability. Returned composites remain Candidate until downstream gates pass.

RetroPath identifier resolution remains a separate identity-resolution task.
