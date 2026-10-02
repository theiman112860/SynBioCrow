from synbiocrow.v24.ranking_attribution_2_4_20 import spearman
def test_spearman_direction():
 assert round(spearman([1,2,3],[1,2,3]),6)==1
 assert round(spearman([1,2,3],[3,2,1]),6)==-1
