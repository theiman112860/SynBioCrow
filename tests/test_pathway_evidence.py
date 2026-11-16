import unittest
from synbiocrow_core.pathway_evidence import Reaction, trace_pathway


def r(name, inputs, outputs):
    return Reaction(name, tuple(inputs), tuple(outputs), "native-test", "fixture:1")


class PathwayEvidenceTests(unittest.TestCase):
    def test_multi_reactant_requires_all_inputs(self):
        result = trace_pathway([r("a", ["A", "B"], ["T"])], ["A"], "T")
        self.assertFalse(result["graph_reachable"])
        self.assertEqual(result["target_producing_reaction_gaps"][0]["missing_reactants"], ["B"])

    def test_dependency_complete_route(self):
        result = trace_pathway([r("a", ["A"], ["B"]), r("b", ["B", "C"], ["T"])], ["A", "C"], "T")
        self.assertTrue(result["graph_reachable"])
        self.assertEqual({x["reaction_id"] for x in result["reaction_evidence"]}, {"a", "b"})
        self.assertFalse(result["biochemically_validated"])

    def test_no_reverse_edges(self):
        self.assertFalse(trace_pathway([r("a", ["T"], ["A"])], ["A"], "T")["graph_reachable"])

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            trace_pathway([r("x", ["A"], ["B"]), r("x", ["B"], ["C"])], ["A"], "C")

    def test_target_seed_is_not_discovery(self):
        result = trace_pathway([], ["T"], "T")
        self.assertTrue(result["graph_reachable"])
        self.assertEqual(result["reaction_evidence"], [])

    def test_missing_provenance_rejected(self):
        with self.assertRaises(ValueError):
            Reaction("a", ("A",), ("B",), "engine", "")


if __name__ == "__main__":
    unittest.main()
