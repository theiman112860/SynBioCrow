import unittest

from synbiocrow.core.models import PathwayCandidate, ReactionStep
from synbiocrow.ensemble import build_reaction_graph


class RoutePreservationGraphTests(unittest.TestCase):
    def test_reaction_smiles_separator_is_supported(self):
        c=PathwayCandidate(
            candidate_id="x",
            target_smiles="CCO",
            steps=(ReactionStep(
                reaction="CCO>>CC=O.O",
                source_backend="doranet",
                metadata={"direction":"retro"},
            ),),
            source_backends=("doranet",),
        )
        g=build_reaction_graph([c])
        self.assertEqual(len(g.edges),1)

    def test_union_preserves_component_edges(self):
        a=PathwayCandidate(
            candidate_id="a",target_smiles="CCO",
            steps=(ReactionStep("CCO>>CC=O.O",source_backend="doranet",metadata={"direction":"retro"}),),
            source_backends=("doranet",),
        )
        b=PathwayCandidate(
            candidate_id="b",target_smiles="CCO",
            steps=(ReactionStep("CCO>>CC.O",source_backend="retrobiocat2"),),
            source_backends=("retrobiocat2",),
        )
        ga=build_reaction_graph([a])
        gu=build_reaction_graph([a,b])
        a_signatures={(e.parent_key,tuple(sorted(e.precursor_keys))) for e in ga.edges.values()}
        u_signatures={(e.parent_key,tuple(sorted(e.precursor_keys))) for e in gu.edges.values()}
        self.assertTrue(a_signatures.issubset(u_signatures))


if __name__=="__main__":
    unittest.main()
