from synbiocrow.v24.metadata_block_collapse_2_4_29 import score
def test_score():
 r={"route_length":2,"template_metadata_fraction":1,"reaction_domain_fraction":1,"reaction_type_fraction":1}
 assert score(r) is not None
