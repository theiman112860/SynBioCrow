import unittest
from synbiocrow_core.biochemical_evidence import annotate_route


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.route = {"target": "T", "graph_reachable": True,
                      "reaction_evidence": [{"reaction_id": "r1"}, {"reaction_id": "r2"}]}

    def test_missing_is_unknown(self):
        report = annotate_route(self.route, {})
        self.assertEqual(report["route_evidence_status"]["enzyme_support"], "NOT_EVALUATED")
        self.assertFalse(report["biochemically_validated"])

    def test_supported_requires_citation(self):
        with self.assertRaises(ValueError):
            annotate_route(self.route, {"r1": {"enzyme_support": {"state": "SUPPORTED"}}})

    def test_partial_support_remains_unknown(self):
        report = annotate_route(self.route, {"r1": {"enzyme_support": {"state": "SUPPORTED", "citation": "doi:example"}}})
        self.assertEqual(report["route_evidence_status"]["enzyme_support"], "NOT_EVALUATED")

    def test_contradiction_propagates(self):
        report = annotate_route(self.route, {"r2": {"thermodynamics": {"state": "CONTRADICTED", "citation": "experiment:1"}}})
        self.assertEqual(report["route_evidence_status"]["thermodynamics"], "CONTRADICTED")

    def test_complete_support_still_not_certified(self):
        evidence = {rid: {dim: {"state": "SUPPORTED", "citation": "curated:1"}
                    for dim in ("enzyme_support", "thermodynamics", "cofactor_balance", "host_feasibility")}
                    for rid in ("r1", "r2")}
        report = annotate_route(self.route, evidence)
        self.assertEqual(report["route_evidence_status"]["enzyme_support"], "SUPPORTED")
        self.assertFalse(report["biochemically_validated"])


if __name__ == "__main__":
    unittest.main()
