from synbiocrow.v24.multivariate_interaction_2_4_30 import design
def test_design():
 X,y,ids,n=design([{"route_id":"x","similarity":0.5,"precedent_step_fraction":1,"step_feasibility_mean":0.5,"route_length":2}])
 assert len(X)==1 and len(X[0])==len(n) and y==[0.5]
