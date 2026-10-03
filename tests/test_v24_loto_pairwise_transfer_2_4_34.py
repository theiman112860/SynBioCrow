from synbiocrow.v24.loto_pairwise_transfer_2_4_34 import matrix,max_equivalent_ids
def test_equiv():
 X,y,ids=matrix([{"route_id":"a","similarity":0.4},{"route_id":"b","similarity":0.4},{"route_id":"c","similarity":0.1}])
 assert set(max_equivalent_ids(ids,y))=={"a","b"} and len(X)==3
