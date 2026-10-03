# SynBioCrow 2.4.29 — Metadata-Block Collapse Counterfactual

2.4.28 found that template_metadata_fraction, reaction_domain_fraction, and reaction_type_fraction are exactly identical for 100% of candidates in every development target, with pairwise Pearson r=1.0.

2.4.29 collapses those three copies into a single metadata block while preserving their combined frozen 2.4.16 weight (0.20 + 0.15 + 0.15 = 0.50). This isolates the effect of representation redundancy from the effect of changing the metadata signal's aggregate importance.

The experiment reports rank movement of the best corrected internal-anchor candidate for every development target. It is counterfactual only: no production ranking change, no generation, and no validation/evaluation truth access.
