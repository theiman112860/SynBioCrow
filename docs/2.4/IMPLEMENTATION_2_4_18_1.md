# SynBioCrow 2.4.18.1 — Corrected Internal-Anchor Audit

2.4.18 revealed two measurement artifacts. First, target exclusion was incomplete for jasmonic acid, dammaradienol and curcumin, so the final product leaked into the "internal" anchor metric. Second, whole-molecule Morgan similarity can make different acyl-CoA species look deceptively similar because the large CoA carrier dominates the fingerprint.

2.4.18.1 corrects both issues before any generation or ranking decision is made. Target anchors are excluded explicitly by name/structure identity. CoA-named anchors receive a carrier-adjusted similarity that subtracts the candidate's similarity to coenzyme A and normalizes by the anchor-versus-carrier baseline.

This is a measurement repair only. The 2.4.16 ordering is frozen; no weights are changed, no generators are invoked, and validation/evaluation truth remains sealed.
