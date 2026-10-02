from synbiocrow.v24.internal_anchor_audit_2_4_18_1 import audit_candidate
def test_target_name_exclusion():
 c={"candidate_id":"x","steps":[{"reaction":"CCO>>CC=O"}]}
 a=[{"name":"product","canonical_smiles":"CC=O"},{"name":"ethanol","canonical_smiles":"CCO"}]
 r=audit_candidate(c,a,"product","CC=O")
 assert r["internal_anchor_count"]==1 and r["anchor_near_misses"][0]["anchor_name"]=="ethanol"
