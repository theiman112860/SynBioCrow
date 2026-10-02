from synbiocrow.v24.failure_decomposition_2_4_19 import classify,percentile
def test_modes():
 assert classify(.5,100,1000)=="RANKING_LIMITED"
 assert classify(.3,20,1000)=="GENERATION_COVERAGE_LIMITED"
 assert classify(.3,100,1000)=="GENERATION_AND_RANKING_LIMITED"
 assert classify(.5,20,1000)=="CANDIDATE_PRESENT_AND_RANKED"
 assert percentile(1,100)==0.0
