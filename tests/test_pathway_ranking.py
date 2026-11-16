import unittest
from synbiocrow_core.pathway_ranking import rank_candidate_routes


def route(ids, engines, reachable=True):
    return {"target": "T", "graph_reachable": reachable,
            "reaction_evidence": [{"reaction_id": rid, "engine": eng, "evidence_ref": "fixture:1"}
                                  for rid, eng in zip(ids, engines)]}


class RankingTests(unittest.TestCase):
    def test_shorter_graph_witness_first(self):
        result = rank_candidate_routes([route(["a", "b"], ["A", "B"]), route(["c"], ["A"])])
        self.assertEqual(result[0]["reaction_ids"], ["c"])
        self.assertEqual(result[0]["thermodynamics"], "NOT_EVALUATED")

    def test_engine_diversity_tiebreak(self):
        result = rank_candidate_routes([route(["a", "b"], ["A", "A"]), route(["c", "d"], ["A", "B"])])
        self.assertEqual(result[0]["engine_count"], 2)

    def test_unreachable_and_stock_target_excluded(self):
        self.assertEqual(rank_candidate_routes([route(["a"], ["A"], False), route([], [])]), [])

    def test_missing_provenance_excluded(self):
        candidate = route(["a"], ["A"])
        candidate["reaction_evidence"][0]["evidence_ref"] = ""
        self.assertEqual(rank_candidate_routes([candidate]), [])


if __name__ == "__main__":
    unittest.main()
