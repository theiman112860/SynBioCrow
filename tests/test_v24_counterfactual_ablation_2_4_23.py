from synbiocrow.v24.counterfactual_ablation_2_4_23 import residual_rank
def test_residual_rank():
 rows=[{"route_id":"a","rank":1,"coverage_adjusted_score":3,"precedent_step_fraction":3},{"route_id":"b","rank":2,"coverage_adjusted_score":2,"precedent_step_fraction":2},{"route_id":"c","rank":3,"coverage_adjusted_score":1.1,"precedent_step_fraction":1}]
 assert residual_rank(rows,"c","precedent_step_fraction") in (1,2,3)
