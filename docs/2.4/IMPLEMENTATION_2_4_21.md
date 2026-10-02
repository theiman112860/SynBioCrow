# SynBioCrow 2.4.21 — Consensus-Positive Development Reranker

2.4.20 identified a consistent ranking pattern for curcumin and jasmonic acid. Features positively associated with corrected target-excluded internal-anchor proximity in both targets are route length, precedent-step fraction, template metadata coverage, reaction-domain coverage, and reaction-type coverage. Rhea/EC context is conflicting across the two targets, and step feasibility is not directionally consistent.

2.4.21 therefore makes the first targeted ranking correction without fitting arbitrary numeric weights. Each consensus-positive feature is converted to a within-target percentile and the five percentiles are averaged equally. The frozen 2.4.16 score is used only as a secondary tie-breaker.

The policy is evaluated only on the two development targets already classified as ranking-limited. MIBK and dammaradienol remain generation-repair targets. Validation ranking is not run and validation/evaluation truth remains sealed.
