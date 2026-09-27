import unittest
from pathlib import Path

from synbiocrow.verification import (
    verify_frozen_2_1,
    run_reproducibility_panel,
    build_release_readiness_report,
)

class M7VerificationTests(unittest.TestCase):
    def test_frozen_release_contract_passes(self):
        report=verify_frozen_2_1(Path(__file__).resolve().parents[1])
        self.assertTrue(report.passed,report.details)
        self.assertTrue(report.checks["benchmark_truth_isolated"])
        self.assertTrue(report.checks["paper1_frozen"])
        self.assertTrue(report.checks["lifecycle_separation"])

    def test_reproducibility_panel_passes(self):
        report=run_reproducibility_panel()
        self.assertTrue(report.passed,report.checks)
        self.assertEqual(report.metrics["route_count"],1)
        self.assertEqual(report.metrics["route_edge_count"],2)

    def test_readiness_has_no_core_blockers(self):
        report=build_release_readiness_report(Path(__file__).resolve().parents[1])
        self.assertTrue(report.core_release_ready,report.blockers)
        self.assertEqual(report.blockers,())

if __name__=="__main__":
    unittest.main()
