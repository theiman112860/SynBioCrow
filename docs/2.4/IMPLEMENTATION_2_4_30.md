# SynBioCrow 2.4.30 — Multivariate Interaction Audit

2.4.29 showed that collapsing the exactly duplicated template/domain/type metadata block while preserving its total frozen weight changes none of the four development near-miss ranks. Therefore metadata duplication affects geometry but is not the immediate cause of scalar rank order.

2.4.30 tests the remaining hypothesis: pathway proximity depends on interactions among precedent, feasibility, route length, and contextual evidence rather than on any single marginal feature. It fits a transparent ridge model on development candidates using the frozen evidence variables plus selected pairwise interaction terms and reports standardized coefficients and in-sample explanatory power.

This is diagnostic only. No production ranking change, no generation, and no validation/evaluation truth access.
