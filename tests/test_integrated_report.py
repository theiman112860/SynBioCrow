import unittest
from synbiocrow_core.integrated_report import build_integrated_report


class IntegratedReportTests(unittest.TestCase):
    def test_reachable_with_provenance(self):
        graph = {"target": "T", "graph_reachable": True,
                 "reaction_evidence": [{"reaction_id": "r1", "engine": "DORAnet",
                                        "evidence_ref": "fixture:1"}]}
        report = build_integrated_report(graph)
        self.assertEqual(report["candidate_rank"]["rank"], 1)
        self.assertEqual(report["biochemical_evidence"]["route_evidence_status"]["thermodynamics"], "NOT_EVALUATED")
        self.assertEqual(report["scientific_certification"], "NOT_CERTIFIED")

    def test_unreachable_has_no_rank(self):
        graph = {"target": "T", "graph_reachable": False, "reaction_evidence": []}
        report = build_integrated_report(graph)
        self.assertIsNone(report["candidate_rank"])

    def test_citation_required(self):
        graph = {"target": "T", "graph_reachable": True,
                 "reaction_evidence": [{"reaction_id": "r1", "engine": "DORAnet", "evidence_ref": "fixture:1"}]}
        with self.assertRaises(ValueError):
            build_integrated_report(graph, {"r1": {"enzyme_support": {"state": "SUPPORTED"}}})


if __name__ == "__main__":
    unittest.main()
