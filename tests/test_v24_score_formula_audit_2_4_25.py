from synbiocrow.v24.score_formula_audit_2_4_25 import exact_score_provenance
def test_count_vs_weight_coverage():
 r={"route_id":"x","route_length":3,"rhea_connectivity_fraction":None,"ec_context_fraction":1,"reviewed_ec_context_fraction":1,"step_feasibility_mean":1,"step_feasibility_min":1,"filter_score_mean":1,"filter_score_min":1,"precedent_step_fraction":1,"rule_coverage_fraction":1,"template_metadata_fraction":1,"reaction_domain_fraction":1,"reaction_type_fraction":1}
 p=exact_score_provenance(r)
 assert p["observed_component_count"]==12
 assert p["count_coverage"]==12/13
 assert p["weight_coverage"] != p["count_coverage"]
