import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from synbiocrow.core.errors import BackendExecutionError
from synbiocrow.core.models import LifecycleState
from synbiocrow.generators.retropath import (
    RETROPATH_NO_SOLUTION,
    RetroPathBackend,
    RetroPathSettings,
    _parse_out_paths,
)


class RetroPathAdapterTests(unittest.TestCase):
    def test_parse_out_paths_groups_complete_pathways(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "out_paths.csv"
            p.write_text(
                '"Path ID","Unique ID","Rule ID","Left","Right"\n'
                '"1","rxn1","ruleA","A:B","C"\n'
                '"1","rxn2","ruleB","C","TARGET"\n'
                '"2","rxn3","ruleC","D","TARGET"\n',
                encoding="utf-8",
            )
            out = _parse_out_paths(
                p,
                target_smiles="CCO",
                provenance={"backend": "retropath2"},
            )
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[0].steps), 2)
        self.assertEqual(out[0].steps[0].reaction, "A + B = C")
        self.assertEqual(out[0].steps[0].rule_id, "ruleA")
        self.assertEqual(out[0].lifecycle, LifecycleState.CANDIDATE)
        self.assertEqual(out[0].source_backends, ("retropath2",))

    def test_candidate_ids_are_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "out_paths.csv"
            p.write_text(
                '"Path ID","Unique ID","Rule ID","Left","Right"\n'
                '"1","rxn1","ruleA","A","TARGET"\n',
                encoding="utf-8",
            )
            a = _parse_out_paths(p, target_smiles="CCO", provenance={})
            b = _parse_out_paths(p, target_smiles="CCO", provenance={})
        self.assertEqual(a[0].candidate_id, b[0].candidate_id)

    def test_no_solution_code_is_successful_no_hit(self):
        with tempfile.TemporaryDirectory() as td:
            rules = Path(td) / "rules.csv"; rules.write_text("x\n1\n")
            sink = Path(td) / "sink.csv"; sink.write_text("name,inchi\na,InChI=1S/H2O/h1H2\n")
            backend = RetroPathBackend(RetroPathSettings(str(rules), str(sink)))
            class FakeMod:
                @staticmethod
                def retropath2(**kwargs):
                    return RETROPATH_NO_SOLUTION, {}
            with patch.object(backend, "available", return_value=True), patch(
                "synbiocrow.generators.retropath.importlib.import_module",
                return_value=FakeMod,
            ), patch(
                "synbiocrow.generators.retropath._write_source_csv",
                return_value="InChI=1S/C2H6O",
            ):
                out = backend.generate("CCO")
        self.assertEqual(out, [])
        self.assertEqual(backend.last_run_stats["status"], "COMPLETE")
        self.assertTrue(backend.last_run_stats["no_hit"])

    def test_non_success_code_is_execution_error(self):
        with tempfile.TemporaryDirectory() as td:
            rules = Path(td) / "rules.csv"; rules.write_text("x\n1\n")
            sink = Path(td) / "sink.csv"; sink.write_text("name,inchi\na,InChI=1S/H2O/h1H2\n")
            backend = RetroPathBackend(RetroPathSettings(str(rules), str(sink)))
            class FakeMod:
                @staticmethod
                def retropath2(**kwargs):
                    return 2, {}
            with patch.object(backend, "available", return_value=True), patch(
                "synbiocrow.generators.retropath.importlib.import_module",
                return_value=FakeMod,
            ), patch(
                "synbiocrow.generators.retropath._write_source_csv",
                return_value="InChI=1S/C2H6O",
            ):
                with self.assertRaises(BackendExecutionError):
                    backend.generate("CCO")
        self.assertEqual(backend.last_run_stats["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
