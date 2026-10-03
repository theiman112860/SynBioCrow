from synbiocrow.v24.multivariate_route_space_2_4_27 import zscore_matrix,euclidean_distance_matrix,mantel_style
def test_shapes():
 rows=[{"route_length":1},{"route_length":2},{"route_length":3}]
 X,_=zscore_matrix(rows);D=euclidean_distance_matrix(X);assert len(D)==3 and D[0][0]==0
def test_mantel_identical():
 D=[[0,1,2],[1,0,1],[2,1,0]];r=mantel_style(D,D,permutations=10,seed=1);assert round(r["correlation"],6)==1
