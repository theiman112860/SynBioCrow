# SynBioCrow V2.0 Alpha90.1.4.3.3

Golden Pathway Divergence & Failure Attribution.

This diagnostic-only release explains why the immutable sealed Alpha90.1.4.3 predictions fail to reproduce complete Golden pathways under the corrected Alpha90.1.4.3.2.5.2 evaluation contract. It does not alter predictions, exact S@K/MRR, the 20-pathway/70-step reference, search parameters, or ranking.

For every frozen route it records ordered identity matches, first divergence, missing Golden step positions, extra predicted steps, route length difference, and backend/route-class provenance. The best frozen route per case is then classified diagnostically as near-Golden, partial concordance, low concordance, no Golden-intermediate recovery, or no route. Patent-hybrid, Rhea, wildcard and other step provenance are reported descriptively only.

A full real-artifact dry run completed against all 20 Golden cases and 169 sealed routes. Preliminary diagnostic distribution: 5 partial-concordance cases, 9 low-concordance cases, 4 route-positive cases with no Golden-intermediate recovery, and 2 no-route cases; no case reached the >=0.75 near-Golden threshold. Mean best-route source-aware ordered LCS was approximately 0.249. Exact metrics remain frozen and unchanged.

Packaged verification: 4/4 tests passed and all notebook code cells compile after fresh re-extraction.