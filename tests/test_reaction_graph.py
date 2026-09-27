import unittest
from synbiocrow.core.models import PathwayCandidate,ReactionStep
from synbiocrow.ensemble import build_reaction_graph, resolve_compound, IdentityState

class EnsembleGraphTests(unittest.TestCase):
    def cand(self,cid,backend,reaction,parent_side=None):
        meta={}
        if parent_side: meta["retrosynthetic_parent_side"]=parent_side
        return PathwayCandidate(
            cid,"T",(ReactionStep(reaction,source_backend=backend,metadata=meta),),(backend,)
        )

    def test_same_reaction_merges_backend_provenance(self):
        cs=[
            self.cand("a","doranet","CCO = CC=O","left"),
            self.cand("b","retrobiocat2","CCO = CC=O","left"),
        ]
        g=build_reaction_graph(cs)
        self.assertEqual(len(g.edges),1)
        e=next(iter(g.edges.values()))
        self.assertEqual(e.source_backends,("doranet","retrobiocat2"))
        self.assertEqual(set(e.candidate_ids),{"a","b"})
        self.assertEqual(g.composite_edge_count(),1)

    def test_canonical_smiles_cross_engine_route(self):
        cs=[
            self.cand("a","doranet","CCO = CC=O","left"),
            self.cand("b","retrobiocat2","CC=O = CC","left"),
        ]
        g=build_reaction_graph(cs)
        target=resolve_compound("CCO",source="doranet").key
        sink={resolve_compound("CC",source="retrobiocat2").key}
        routes=g.find_routes(target,sink,max_steps=3)
        self.assertEqual(len(routes),1)
        engines={b for eid in routes[0] for b in g.edges[eid].source_backends}
        self.assertEqual(engines,{"doranet","retrobiocat2"})

    def test_unresolved_labels_do_not_cross_engine_join(self):
        cs=[
            self.cand("a","doranet","TARGET_TOKEN = INTERMEDIATE_TOKEN","left"),
            self.cand("b","retrobiocat2","INTERMEDIATE_TOKEN = SINK_TOKEN","left"),
        ]
        g=build_reaction_graph(cs)
        target=resolve_compound("TARGET_TOKEN",source="doranet").key
        sink={resolve_compound("SINK_TOKEN",source="retrobiocat2").key}
        self.assertEqual(g.find_routes(target,sink,max_steps=3),[])

    def test_retropath_identifiers_are_preserved_raw(self):
        rp=self.cand("r","retropath2","CMPD_A = CMPD_B","right")
        d=self.cand("d","doranet","CMPD_A = CCO","left")
        g=build_reaction_graph([rp,d])
        raw=[c for c in g.compounds.values() if c.display=="CMPD_A"]
        self.assertGreaterEqual(len(raw),2)
        self.assertTrue(all(c.state in {IdentityState.RAW,IdentityState.UNRESOLVED} for c in raw))

if __name__=="__main__":unittest.main()
