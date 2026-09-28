import unittest
from synbiocrow.core.models import LifecycleState,ReactionStep,PathwayCandidate
from synbiocrow.evidence.gates import GateDecision,GateResult,require_all
from synbiocrow.lifecycle.policy import PromotionPolicy
from synbiocrow.ensemble.graph import union_candidates
from synbiocrow.generators.registry import default_registry
from synbiocrow.core.errors import BackendUnavailableError

class EngineContractTests(unittest.TestCase):
    def test_registry_contains_planned_live_families(self):
        self.assertEqual(default_registry().ids(),("biopks_retrotide","doranet","retrobiocat2","retropath2","retropath_standalone"))
    def test_unmigrated_backend_fails_closed(self):
        with self.assertRaises(BackendUnavailableError): default_registry().get("doranet").generate("CCO")
    def test_evidence_abstention_blocks_promotion(self):
        self.assertEqual(PromotionPolicy().promote(LifecycleState.CANDIDATE,GateDecision.ABSTAIN),LifecycleState.CANDIDATE)
    def test_pass_promotes_one_level_only(self):
        self.assertEqual(PromotionPolicy().promote(LifecycleState.CANDIDATE,GateDecision.PASS),LifecycleState.MATURE)
    def test_require_all_is_fail_closed(self):
        rs=[GateResult("closure",GateDecision.PASS,"balanced"),GateResult("enzyme",GateDecision.ABSTAIN,"missing")]
        self.assertEqual(require_all(rs),GateDecision.ABSTAIN)
    def test_union_deduplicates_without_promotion(self):
        c1=PathwayCandidate("a","CCO",(ReactionStep("A = B"),),("x",))
        c2=PathwayCandidate("b","CCO",(ReactionStep("A = B"),),("y",))
        out=union_candidates([c1,c2]); self.assertEqual(len(out),1); self.assertEqual(out[0].lifecycle,LifecycleState.CANDIDATE)

if __name__=="__main__": unittest.main()
