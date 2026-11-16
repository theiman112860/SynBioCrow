import unittest
from synbiocrow_core.evidence_aware_ranking import prioritize_evidence_annotated_routes


def route(rid):
    return {"target": "T", "graph_reachable": True,
            "reaction_evidence": [{"reaction_id": rid, "engine": "DORAnet", "evidence_ref": "archive:1"}]}


class EvidenceAwareRankingTests(unittest.TestCase):
    def test_unknown_never_becomes_supported(self):
        result = prioritize_evidence_annotated_routes([route("r1")], {})
        self.assertEqual(result[0]["unknown_checks"], 4)
        self.assertEqual(result[0]["triage"], "EVIDENCE_GAPS")

    def test_cited_support_prioritized(self):
        result = prioritize_evidence_annotated_routes([route("r1"), route("r2")],
            {"r2": {"enzyme_support": {"state": "SUPPORTED", "citation": "curation:1"}}})
        self.assertEqual(result[0]["reaction_ids"], ["r2"])

    def test_contradiction_requires_review(self):
        result = prioritize_evidence_annotated_routes([route("r1"), route("r2")],
            {"r1": {"thermodynamics": {"state": "CONTRADICTED", "citation": "curation:2"}}})
        self.assertEqual(result[-1]["triage"], "CONTRADICTION_REVIEW")

    def test_invalid_uncited_evidence_rejected(self):
        with self.assertRaises(ValueError):
            prioritize_evidence_annotated_routes([route("r1")],
                {"r1": {"enzyme_support": {"state": "SUPPORTED"}}})


if __name__ == "__main__":
    unittest.main()
