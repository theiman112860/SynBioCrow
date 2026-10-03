from synbiocrow.v24.correlated_feature_block_2_4_28 import block_stats,collapsed_block_score
def test_redundancy():
 rows=[{"template_metadata_fraction":x,"reaction_domain_fraction":x,"reaction_type_fraction":x} for x in (0,0.5,1)]
 s=block_stats(rows);assert s["identical_within_route_fraction"]==1;assert round(s["pairwise_pearson"]["template_metadata_fraction__reaction_domain_fraction"],6)==1
 assert collapsed_block_score(rows[1])==0.5
