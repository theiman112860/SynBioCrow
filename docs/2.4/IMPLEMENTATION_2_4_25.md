# SynBioCrow 2.4.25 — Exact Score-Formula Recovery and Coverage Audit

The frozen 2.4.16 implementation was recovered directly from `synbiocrow/v24/native_discrimination_2_4_16.py`.

The score is:
1. clip bounded evidence/feasibility features to [0,1];
2. convert route length to `min(route_length,12)/12`;
3. compute the weighted numerator over observed components only;
4. divide by the sum of absolute weights of observed components;
5. multiply the resulting raw score by `observed_component_count / 13`.

Therefore missingness is penalized a second time by an **unweighted count-based coverage multiplier**. Missing a 0.15-weight feature reduces coverage by the same 1/13 as missing the 1.00-weight Rhea feature.

2.4.25 first verifies exact reconstruction against persisted 2.4.16 raw and adjusted scores. It then reports a weight-aware coverage alternative (`observed_abs_weight / total_abs_weight`) purely as a diagnostic and shows the resulting rank movement for the ranking-limited development near-miss candidates.

No alternative is adopted as production ranking in this stage. Validation/evaluation truth remains sealed and no generation is invoked.
