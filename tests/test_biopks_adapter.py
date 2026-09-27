import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from synbiocrow.core.models import LifecycleState
from synbiocrow.generators.biopks import BioPKSBackend, normalize_biopks_payload
from synbiocrow.ensemble import build_reaction_graph

class BioPKSAdapterTests(unittest.TestCase):
    def fixture(self):
        return {
            "schema":"synbiocrow.biopks.external.v1",
            "status":"COMPLETE",
            "routes":[{
                "candidate_id":"BIOPKS-DEMO",
                "route_class":"PKS_SPECIALIST",
                "score":0.73,
                "specialist_sequence_complete":False,
                "experimental_validation_claimed":False,
                "steps":[
                    {
                        "step_type":"PKS_ASSEMBLY",
                        "module_architecture":[{"index":1,"domains":["KS","AT","ACP"]}],
                    },
                    {
                        "step_type":"POST_PKS",
                        "reaction":"CCO = CC=O",
                        "rule_id":"rule_demo",
                        "score":0.8,
                    }
                ]
            }]
        }

    def test_normalization_keeps_candidate_and_only_explicit_reactions(self):
        out=normalize_biopks_payload(self.fixture(),target_smiles="CCO")
        self.assertEqual(len(out),1)
        c=out[0]
        self.assertEqual(c.candidate_id,"BIOPKS-DEMO")
        self.assertEqual(c.lifecycle,LifecycleState.CANDIDATE)
        self.assertEqual(c.source_backends,("biopks_retrotide",))
        self.assertEqual(len(c.steps),1)
        self.assertEqual(c.steps[0].reaction,"CCO = CC=O")
        self.assertFalse(c.provenance["specialist_sequence_complete"])

    def test_specialized_reaction_enters_shared_graph(self):
        c=normalize_biopks_payload(self.fixture(),target_smiles="CCO")[0]
        g=build_reaction_graph([c])
        self.assertIn("biopks_retrotide",g.backend_set())
        self.assertEqual(len(g.edges),1)

    def test_bridge_contract_executes_external_runner(self):
        with tempfile.TemporaryDirectory() as td:
            runner=Path(td)/"bridge.py"
            payload=self.fixture()
            runner.write_text(
                "import sys,json\n"
                "_=json.load(sys.stdin)\n"
                f"print(json.dumps({payload!r}))\n",
                encoding="utf-8",
            )
            backend=BioPKSBackend(runner=str(runner))
            with patch.dict(os.environ,{"SYNBIOCROW_BIOPKS_ACK_LICENSE":"1"},clear=False):
                out=backend.generate("CCO")
            self.assertEqual(len(out),1)
            self.assertEqual(backend.last_run_stats["status"],"COMPLETE")

    def test_zero_routes_is_successful_no_hit(self):
        with tempfile.TemporaryDirectory() as td:
            runner=Path(td)/"bridge.py"
            runner.write_text(
                "import sys,json\n_=json.load(sys.stdin)\n"
                "print(json.dumps({'schema':'synbiocrow.biopks.external.v1','status':'NO_HIT','routes':[]}))\n",
                encoding="utf-8",
            )
            backend=BioPKSBackend(runner=str(runner))
            with patch.dict(os.environ,{"SYNBIOCROW_BIOPKS_ACK_LICENSE":"1"},clear=False):
                out=backend.generate("CCO")
            self.assertEqual(out,[])
            self.assertTrue(backend.last_run_stats["no_hit"])

if __name__=="__main__":
    unittest.main()
