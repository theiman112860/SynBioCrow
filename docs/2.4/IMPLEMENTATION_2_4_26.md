# SynBioCrow 2.4.26 — Backend / Metadata Score-Bias Audit

2.4.25 exactly reproduced the frozen 2.4.16 score and showed that replacing count-based coverage with weight-aware coverage leaves the curcumin and jasmonic-acid near-miss ranks unchanged (99 and 433).

Both near-miss routes observe 11/13 components. The only missing components are filter_score_mean and filter_score_min; Rhea/EC context values are observed zeros.

2.4.26 therefore tests whether score/rank distributions and metadata availability differ systematically by source backend family. It reports backend-family counts, score/rank distributions, top-50 fractions, feature means, feature observation fractions, and backend composition of routes outranking each literature-near development candidate.

Diagnostic only: no ranking policy change, no generation, and validation/evaluation truth remains sealed.
