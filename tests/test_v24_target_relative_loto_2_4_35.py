from synbiocrow.v24.target_relative_loto_2_4_35 import percentile_transform
def test_percentiles():
 X=[[1,5],[2,5],[3,9]];R=percentile_transform(X)
 assert R.shape==(3,2) and R[0,0]==0 and R[2,0]==1
