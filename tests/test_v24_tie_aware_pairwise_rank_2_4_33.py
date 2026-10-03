from synbiocrow.v24.tie_aware_pairwise_rank_2_4_33 import matrix,max_equivalent_ids
def test_equivalence():
 rows=[{"route_id":"a","similarity":0.5},{"route_id":"b","similarity":0.5},{"route_id":"c","similarity":0.2}]
 X,y,ids=matrix(rows);assert set(max_equivalent_ids(ids,y))=={"a","b"} and len(X)==3
