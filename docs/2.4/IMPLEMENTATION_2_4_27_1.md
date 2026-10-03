# SynBioCrow 2.4.27.1 — Bounded Multivariate Route-Space Repair

2.4.27 timed out because it materialized full O(n^2) distance matrices and repeatedly permuted/reindexed them during the Mantel-style test. With thousands of candidates this is unnecessarily expensive.

2.4.27.1 keeps PCA exact over all development candidates, but bounds expensive geometry:
- deterministic MDS subset capped at 300 candidates per target,
- preserves top-ranked routes and highest internal-anchor-similarity routes before deterministic sampling,
- samples at most 50,000 route pairs for evidence-vs-pathway distance concordance,
- uses 100 deterministic permutations,
- avoids full n-by-n Python list matrices for the full candidate set.

No ranking policy changes, no generation, and no validation/evaluation truth access.
