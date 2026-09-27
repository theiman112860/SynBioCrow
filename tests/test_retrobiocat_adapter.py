import unittest
from unittest.mock import patch

from synbiocrow.core.errors import BackendExecutionError
from synbiocrow.core.models import LifecycleState
from synbiocrow.generators.retrobiocat import (
    RBC2Settings,
    RetroBioCatBackend,
    _pathway_to_candidate,
)


class FakePrecedent:
    def __init__(self, similarity=0.91):
        self.similarity = similarity


class FakeReaction:
    def __init__(self, product, substrates, name, score=0.5):
        self.product = product
        self.substrates = list(substrates)
        self.name = name
        self.score = score
        self.rxn_type = "retrobiocat"
        self.rxn_domain = "biocatalysis"
        self.template_metadata = {"family": name}
        self.feasability_filter_scores = {"demo": score}
        self.precedents = [FakePrecedent()]
        self.data = {}
        self.unique_id = "RANDOM-UUID-MUST-NOT-AFFECT-ID"


class FakePathway:
    target_smi = "CCO"
    pathway_length = 2

    def __init__(self):
        self.reactions = [
            FakeReaction("CC=O", ["CC"], "reduction_step", 0.7),
            FakeReaction("CCO", ["CC=O"], "oxidation_step", 0.8),
        ]

    def end_smis(self):
        return ["CC"]


class FakeConfig:
    def __init__(self):
        self.max_search_time = 60
        self.max_iterations = None
        self.max_length = 4
        self.chemistry_filter = "default"


class FakeMCTS:
    solved = [FakePathway()]
    should_error = False

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def run(self):
        if self.should_error:
            raise RuntimeError("fixture runtime failure")

    def get_run_stats(self):
        return {"iterations": 9, "run_time": 0.1, "solved": len(self.solved)}

    def get_solved_pathways(self):
        return list(self.solved)


class FakeExpanderModule:
    @staticmethod
    def get_expanders(names):
        assert names == ["retrobiocat"]
        return ["FAKE_RETROBIOCAT_EXPANDER"]


class FakeMCTSModule:
    MCTS = FakeMCTS


class FakeConfigModule:
    MCTS_Config = FakeConfig


def fake_import(name):
    if name == "rbc2.mcts.mcts":
        return FakeMCTSModule
    if name == "rbc2.configs.mcts_config":
        return FakeConfigModule
    if name == "rbc2.expansion.expander_repository":
        return FakeExpanderModule
    raise ImportError(name)


class RetroBioCatAdapterTests(unittest.TestCase):
    def tearDown(self):
        FakeMCTS.solved = [FakePathway()]
        FakeMCTS.should_error = False

    def test_normalization_is_target_first_and_deterministic(self):
        p = FakePathway()
        a = _pathway_to_candidate(
            p, target_smiles="CCO", rbc2_version="2026.2.27",
            search_stats={"status": "COMPLETE"}
        )
        b = _pathway_to_candidate(
            p, target_smiles="CCO", rbc2_version="2026.2.27",
            search_stats={"status": "COMPLETE"}
        )
        self.assertEqual(a.candidate_id, b.candidate_id)
        self.assertEqual(a.steps[0].reaction, "CCO = CC=O")
        self.assertEqual(a.steps[1].reaction, "CC=O = CC")
        self.assertEqual(a.lifecycle, LifecycleState.CANDIDATE)
        self.assertEqual(a.source_backends, ("retrobiocat2",))
        self.assertEqual(a.provenance["end_smiles"], ["CC"])
        self.assertEqual(a.steps[0].metadata["precedents"][0]["similarity"], 0.91)

    def test_generate_uses_native_mcts_contract(self):
        backend = RetroBioCatBackend(
            RBC2Settings(max_search_time=7, max_iterations=33, max_length=3)
        )
        with patch.object(backend, "available", return_value=True), patch(
            "synbiocrow.generators.retrobiocat.importlib.import_module",
            side_effect=fake_import,
        ), patch(
            "synbiocrow.generators.retrobiocat.importlib_metadata.version",
            return_value="2026.2.27",
        ):
            out = backend.generate("CCO")
        self.assertEqual(len(out), 1)
        self.assertEqual(backend.last_run_stats["status"], "COMPLETE")
        self.assertEqual(backend.last_run_stats["solved_pathways"], 1)
        self.assertEqual(out[0].provenance["rbc2_version"], "2026.2.27")

    def test_zero_solved_is_successful_no_hit(self):
        FakeMCTS.solved = []
        backend = RetroBioCatBackend()
        with patch.object(backend, "available", return_value=True), patch(
            "synbiocrow.generators.retrobiocat.importlib.import_module",
            side_effect=fake_import,
        ), patch(
            "synbiocrow.generators.retrobiocat.importlib_metadata.version",
            return_value="2026.2.27",
        ):
            out = backend.generate("CCO")
        self.assertEqual(out, [])
        self.assertEqual(backend.last_run_stats["status"], "COMPLETE")
        self.assertEqual(backend.last_run_stats["solved_pathways"], 0)

    def test_runtime_failure_is_not_no_hit(self):
        FakeMCTS.should_error = True
        backend = RetroBioCatBackend()
        with patch.object(backend, "available", return_value=True), patch(
            "synbiocrow.generators.retrobiocat.importlib.import_module",
            side_effect=fake_import,
        ):
            with self.assertRaises(BackendExecutionError):
                backend.generate("CCO")
        self.assertEqual(backend.last_run_stats["status"], "ERROR")
        self.assertEqual(backend.last_run_stats["error_type"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
