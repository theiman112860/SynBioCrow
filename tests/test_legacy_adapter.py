import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from synbiocrow_core.legacy_adapter import adapt_legacy_reactions, report_from_legacy_archive


def record(rid="r1"):
    return {"id": rid, "engine": "DORAnet", "substrates": ["A", "B"],
            "products": ["T"], "direction": "native_forward",
            "source_file": "evidence.json", "source_sha256": "a" * 64}


class LegacyAdapterTests(unittest.TestCase):
    def test_real_archive_field_contract(self):
        good, bad = adapt_legacy_reactions([record()])
        self.assertEqual(len(good), 1)
        self.assertFalse(bad)
        self.assertIn("sha256=", good[0].evidence_ref)

    def test_missing_provenance_quarantined(self):
        bad_record = record()
        del bad_record["source_sha256"]
        good, bad = adapt_legacy_reactions([bad_record])
        self.assertFalse(good)
        self.assertEqual(len(bad), 1)

    def test_json_archive_requires_all_reactants(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reactions.json"
            path.write_text(json.dumps([record()]), encoding="utf-8")
            report = report_from_legacy_archive(path, ["A"], "T")
            self.assertFalse(report["graph_reachable"])
            self.assertEqual(report["target_producing_reaction_gaps"][0]["missing_reactants"], ["B"])

    def test_zip_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "results.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("combined_reaction_candidates.json", json.dumps([record()]))
            report = report_from_legacy_archive(path, ["A", "B"], "T")
            self.assertTrue(report["graph_reachable"])
            self.assertEqual(report["scientific_status"], "UNCERTIFIED_GRAPH_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
