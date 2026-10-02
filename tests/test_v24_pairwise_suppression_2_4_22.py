from synbiocrow.v24.pairwise_suppression_2_4_22 import audit_target,compare_failed_policy
def test_pairwise():
 rows=[{"route_id":"candidate:a","rank":2,"route_length":2},{"route_id":"candidate:b","rank":1,"route_length":4}]
 best={"candidate_id":"a","internal_anchor_similarity_mean":.5}
 r=audit_target(rows,best)
 x=next(q for q in r["feature_suppression_audit"] if q["feature"]=="route_length")
 assert x["fraction_above_greater"]==1.0 and x["target_minus_median"]==-2
 assert compare_failed_policy({"evaluations":[{"rank_improvement":-1}]})["all_worsened"]
