from synbiocrow.v24.backend_bias_audit_2_4_26 import audit
def test_backend_groups():
 rows=[{"route_id":"a","rank":1,"coverage_adjusted_score":.2,"source_backends":["x"]},{"route_id":"b","rank":2,"coverage_adjusted_score":.1,"source_backends":["y"]}]
 x=audit(rows,"b");assert x["target_backend_family"]=="y" and x["outrankers_n"]==1
