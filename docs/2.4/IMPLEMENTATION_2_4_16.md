# SynBioCrow 2.4.16 — Dense Generator-Native Evidence Ranking

2.4.15 showed that external Rhea/UniProt context is sparse across the 5,839 persisted development candidates, but the candidate artifacts already contain dense generator-native evidence: step feasibility, feasibility-filter scores, precedents, template metadata, reaction domains/types, and rule coverage.

2.4.16 therefore combines:
- generator-native feasibility and precedent evidence;
- template/rule/domain/type coverage;
- 2.4.15 Rhea/EC/UniProt contextual evidence when available;
- a small route-length penalty.

No labels are used and no weights are fit. Missing evidence stays missing. Validation/evaluation records remain sealed. This is a development ranking diagnostic, not certification or lifecycle promotion.

The principal success criterion is improved within-target score diversity compared with 2.4.14, while retaining transparent provenance and firewall guarantees.
