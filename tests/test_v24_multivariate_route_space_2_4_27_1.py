from synbiocrow.v24.multivariate_route_space_2_4_27_1 import *
def test_bounded_subset():
 rows=[{"rank":i+1,"internal_anchor_similarity_mean":i/1000} for i in range(1000)]
 idx=deterministic_subset(rows,max_n=300);assert len(idx)==300 and len(set(idx))==300
def test_concordance_identical():
 X=[[0],[1],[2],[3]];r=sampled_concordance(X,X,max_pairs=100,permutations=10,seed=1);assert round(r["correlation"],6)==1
