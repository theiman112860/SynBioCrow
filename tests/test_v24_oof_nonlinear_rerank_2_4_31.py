from synbiocrow.v24.oof_nonlinear_rerank_2_4_31 import matrix
def test_matrix():
 X,y,ids=matrix([{"route_id":"r1","similarity":0.4,"route_length":2}])
 assert len(X)==1 and len(X[0])==13 and y==[0.4] and ids==["r1"]
