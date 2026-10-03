from synbiocrow.v24.multivariate_interaction_2_4_30 import design
def test_designs():
 rows=[{"route_id":"x","similarity":0.5,"precedent_step_fraction":1,"step_feasibility_mean":0.5,"route_length":2}]
 X,y,ids,n=design(rows,False);Xi,yi,_,ni=design(rows,True)
 assert len(X)==1 and len(X[0])==13
 assert len(Xi[0])==18
 assert y==yi==[0.5]
