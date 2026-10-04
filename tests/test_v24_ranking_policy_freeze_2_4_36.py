from synbiocrow.v24.ranking_policy_freeze_2_4_36 import percentile_transform
def test_percentile_ties():
    R=percentile_transform([[1],[1],[3]])
    assert R.shape==(3,1)
    assert R[0,0]==R[1,0]
    assert R[2,0]==1
