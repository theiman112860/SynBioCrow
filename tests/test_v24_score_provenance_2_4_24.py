from synbiocrow.v24.score_provenance_2_4_24 import provenance
def test_provenance():
 rows=[{"route_id":"a","rank":1,"coverage_adjusted_score":2},{"route_id":"b","rank":2,"coverage_adjusted_score":1}]
 x=provenance(rows,"b");assert x["target"]["rank_2_4_16"]==2 and x["score_distribution"]["outranking_n"]==1
