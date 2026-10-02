from synbiocrow.v24.internal_anchor_audit_2_4_18 import audit_candidate
def test_target_is_excluded():
 c={"candidate_id":"x","steps":[{"reaction":"CCO>>CC=O"}]}
 a=[{"name":"target","canonical_smiles":"CC=O"},{"name":"ethanol","canonical_smiles":"CCO"}]
 r=audit_candidate(c,a,"CC=O")
 assert r["internal_anchor_count"]==1
 assert r["anchor_near_misses"][0]["anchor_name"]=="ethanol"
 assert r["anchor_near_misses"][0]["best_similarity"]==1.0
