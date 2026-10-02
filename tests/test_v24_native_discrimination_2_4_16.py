import json
from synbiocrow.v24.native_discrimination_2_4_16 import merge_and_rank,score_diversity

def test_missing_external_evidence_stays_missing():
    native=[{"record_id":"dev","target_name":"x","route_id":"candidate:a","route_length":2,
      "source_backends":["rbc2"],"step_feasibility_mean":0.8,"step_feasibility_min":0.7,
      "filter_score_mean":0.6,"filter_score_min":0.5,"precedent_total":2,"precedent_step_fraction":1.0,
      "rule_coverage_fraction":1.0,"template_metadata_fraction":1.0,
      "reaction_domain_fraction":1.0,"reaction_type_fraction":1.0}]
    r=merge_and_rank(native,[])[0]
    assert r["rhea_connectivity_fraction"] is None
    assert r["coverage_adjusted_score"] is not None

def test_native_signal_breaks_ties():
    base={"record_id":"dev","target_name":"x","route_length":2,"source_backends":["rbc2"],
      "filter_score_mean":0.6,"filter_score_min":0.5,"precedent_total":1,"precedent_step_fraction":0.5,
      "rule_coverage_fraction":1.0,"template_metadata_fraction":1.0,
      "reaction_domain_fraction":1.0,"reaction_type_fraction":1.0}
    a=dict(base,route_id="candidate:a",step_feasibility_mean=0.9,step_feasibility_min=0.8)
    b=dict(base,route_id="candidate:b",step_feasibility_mean=0.4,step_feasibility_min=0.3)
    r=merge_and_rank([a,b],[])
    assert r[0]["route_id"]=="candidate:a"
    d=score_diversity(r)
    assert d["dev"]["distinct_score_count"]==2
