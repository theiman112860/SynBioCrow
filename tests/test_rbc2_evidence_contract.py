"""Deterministic evidence-contract tests; no synthetic evidence is accepted as native."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_rbc2_evidence import EXPECTED_COMMIT, validate


def fixture():
    return {
        "engine": "RetroBioCat2", "source_commit": EXPECTED_COMMIT,
        "targets": [{"smiles": "CCCC=O", "status": "NATIVE_EXECUTED", "count": 1,
                     "reactions": [{"target_smiles": "CCCC=O", "engine": "RetroBioCat2",
                                    "source_commit": EXPECTED_COMMIT,
                                    "reaction_smiles": "CCCC=O>>CCC=O",
                                    "reaction_smiles_parseable": True,
                                    "candidate_only": True}]}],
    }


class EvidenceContractTests(unittest.TestCase):
    def test_valid_shape_only(self):
        self.assertEqual(validate(fixture(), ["CCCC=O"]), [])

    def test_zero_reactions_not_pass(self):
        report = fixture()
        report["targets"][0]["reactions"] = []
        report["targets"][0]["count"] = 0
        self.assertTrue(validate(report, ["CCCC=O"]))

    def test_missing_target_not_pass(self):
        self.assertTrue(validate(fixture(), ["O=C(O)CCO"]))

    def test_wrong_commit_not_pass(self):
        report = fixture()
        report["source_commit"] = "wrong"
        self.assertTrue(validate(report, ["CCCC=O"]))

    def test_unparseable_not_pass(self):
        report = fixture()
        report["targets"][0]["reactions"][0]["reaction_smiles_parseable"] = False
        self.assertTrue(validate(report, ["CCCC=O"]))

    def test_native_failure_not_pass(self):
        report = fixture()
        report["targets"][0]["status"] = "TARGET_FAILED"
        self.assertTrue(validate(report, ["CCCC=O"]))


if __name__ == "__main__":
    unittest.main()
