from synbiocrow.v24.development_truth_2_4_17 import reaction_molecules,score_candidate
def test_anchor_recall():
    a=[{"name":"ethanol","canonical_smiles":"CCO"},{"name":"acetate","canonical_smiles":"CC(=O)O"}]
    c={"candidate_id":"x","steps":[{"reaction":"CCO>>CC=O"}]}
    s=score_candidate(c,a)
    assert s["anchor_recall"]==0.5
    assert s["anchor_hits"]==["ethanol"]
