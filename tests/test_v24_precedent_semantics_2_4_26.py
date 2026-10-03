from synbiocrow.v24.precedent_semantics_2_4_26 import candidate_precedent_audit
def test_semantics():
 c={"candidate_id":"x","steps":[{"metadata":{"precedents":[{"reaction":"A>>B"}]}},{"metadata":{}}]}
 a=candidate_precedent_audit(c);assert a["precedent_step_fraction"]==0.5;assert a["precedent_classes"]["structured_reaction"]==1
