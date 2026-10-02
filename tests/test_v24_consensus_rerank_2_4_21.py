from synbiocrow.v24.consensus_rerank_2_4_21 import rerank_target
def test_consensus_rerank():
 rows=[
  {"route_id":"a","rank":2,"coverage_adjusted_score":.3,"route_length":3,"precedent_step_fraction":1.0,"template_metadata_fraction":1.0,"reaction_domain_fraction":1.0,"reaction_type_fraction":1.0},
  {"route_id":"b","rank":1,"coverage_adjusted_score":.9,"route_length":1,"precedent_step_fraction":0.0,"template_metadata_fraction":0.0,"reaction_domain_fraction":0.0,"reaction_type_fraction":0.0},
 ]
 r=rerank_target(rows)
 assert r[0]["route_id"]=="a" and r[0]["rank_2_4_21"]==1
