from synbiocrow.v24.adapters import adapt_route
from synbiocrow.v24.ranking import BASELINE_2D, REACTION_EVIDENCE, rank, score

def test_missing_features_do_not_become_support():
    r=adapt_route({"route_id":"x","reactions":[{"id":"r"}]})
    s,n=score(r,REACTION_EVIDENCE)
    assert s==0.0
    assert n==2  # explicit zero evidence fractions; 2D itself is missing

def test_evidence_can_discriminate_fixed_candidates():
    a=adapt_route({"route_id":"a","similarity_2d":0.5,"reactions":[{"id":"r1","rhea_id":"RHEA:1","rhea_exact":True}]})
    b=adapt_route({"route_id":"b","similarity_2d":0.5,"reactions":[{"id":"r2"}]})
    assert rank([b,a],REACTION_EVIDENCE)[0]["route_id"]=="a"

def test_baseline_uses_same_candidates():
    a=adapt_route({"route_id":"a","similarity_2d":0.8,"reactions":[{"id":"r1"}]})
    b=adapt_route({"route_id":"b","similarity_2d":0.2,"reactions":[{"id":"r2","uniprot":"P1"}]})
    rows=rank([a,b],BASELINE_2D)
    assert [x["route_id"] for x in rows]==["a","b"]
