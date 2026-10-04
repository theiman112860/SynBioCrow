from synbiocrow.v24.ranking_policy_freeze_2_4_36_1 import percentile_transform,deterministic_within_target_pairs
def test_deterministic_pairs():
    X=percentile_transform([[0],[1],[2],[3]])
    y=[0.1,0.2,0.2,0.4];ids=["a","b","c","d"]
    P1,L1=deterministic_within_target_pairs(X,y,ids);P2,L2=deterministic_within_target_pairs(X,y,ids)
    assert (P1==P2).all() and (L1==L2).all() and len(L1)>0
