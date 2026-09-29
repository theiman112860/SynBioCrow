import tempfile
import unittest
from pathlib import Path

from synbiocrow.core.models import PathwayCandidate, ReactionStep
from synbiocrow.generators.registry import BackendRegistry
from synbiocrow.engine import SynBioCrowEngine
from synbiocrow.execution import DesignRequest, design, RunStateStore

class FakeBackend:
    backend_id="fake"
    calls=0
    def runtime_info(self):
        return {"available":True,"configured":True}
    def generate(self,target_smiles,*,options=None):
        type(self).calls += 1
        return [PathwayCandidate(
            "fake-1",target_smiles,
            (ReactionStep(f"{target_smiles} = CC",source_backend="fake",
             metadata={"retrosynthetic_parent_side":"left"}),),
            ("fake",),
        )]

class M6ExecutionTests(unittest.TestCase):
    def setUp(self):
        FakeBackend.calls=0

    def engine(self):
        return SynBioCrowEngine(backends=BackendRegistry([FakeBackend()]))

    def test_public_design_workflow(self):
        with tempfile.TemporaryDirectory() as td:
            result=design(
                DesignRequest("CCO",backend_ids=("fake",),sink_smiles=("CC",)),
                engine=self.engine(),
                state_root=td,
            )
            self.assertEqual(result.backend_status["fake"]["status"],"COMPLETE")
            self.assertEqual(len(result.candidates),1)
            self.assertEqual(len(result.routes),1)
            self.assertEqual(result.diagnostics["scientific_state"],"CANDIDATE_ONLY")
            self.assertTrue((Path(td)/result.run_id/"result.json").exists())

    def test_resume_does_not_rerun_candidate_generation(self):
        with tempfile.TemporaryDirectory() as td:
            req=DesignRequest("CCO",backend_ids=("fake",),sink_smiles=("CC",))
            first=design(req,engine=self.engine(),state_root=td,resume=True)
            self.assertEqual(FakeBackend.calls,1)
            second=design(req,engine=self.engine(),state_root=td,resume=True)
            self.assertEqual(FakeBackend.calls,1)
            self.assertEqual(first.run_id,second.run_id)
            self.assertEqual(len(second.candidates),1)

    def test_run_id_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            req=DesignRequest("CCO",backend_ids=("fake",))
            x=design(req,engine=self.engine(),state_root=a)
            y=design(req,engine=self.engine(),state_root=b)
            self.assertEqual(x.run_id,y.run_id)

    def test_manifest_lists_checkpoint_stages(self):
        with tempfile.TemporaryDirectory() as td:
            result=design(
                DesignRequest("CCO",backend_ids=("fake",)),
                engine=self.engine(),
                state_root=td,
            )
            store=RunStateStore(td)
            stages=store.completed_stages(result.run_id)
            self.assertIn("candidates",stages)
            self.assertIn("graph_summary",stages)
            self.assertIn("result",stages)

    def test_nonbiosynthesis_fails_explicitly(self):
        with self.assertRaises(ValueError):
            design(
                DesignRequest("CCO",mode="non-biosynthesis",backend_ids=("fake",)),
                engine=self.engine(),
            )

    def test_hybrid_reports_current_limit(self):
        result=design(
            DesignRequest("CCO",mode="hybrid",backend_ids=("fake",)),
            engine=self.engine(),
        )
        self.assertEqual(result.diagnostics["mode"],"hybrid")
        self.assertIn("currently registered generators",result.diagnostics["mode_note"])

if __name__=="__main__":
    unittest.main()
