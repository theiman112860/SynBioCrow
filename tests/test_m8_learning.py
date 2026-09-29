import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from synbiocrow import SynBioCrowEngine
from synbiocrow.core.models import LifecycleState, PathwayCandidate, ReactionStep
from synbiocrow.ensemble import build_reaction_graph
from synbiocrow.learning import (
    LearningPolicy,
    TestOutcome,
    apply_test_outcomes,
    route_feature_matrix,
    LearningAuditLog,
)

class M8LearningTests(unittest.TestCase):
    def test_backend_update_is_bounded(self):
        policy=LearningPolicy(max_delta_per_update=0.05)
        outcomes=(TestOutcome(
            outcome_id="o1",
            kind="backend",
            subject_id="run-1",
            backend_id="doranet",
            reward=1.0,
        ),)
        new,update=apply_test_outcomes(policy,outcomes,learning_rate=1.0)
        self.assertAlmostEqual(new.backend_weights["doranet"],1.05)
        self.assertAlmostEqual(update.backend_deltas["doranet"],0.05)

    def test_outcome_order_does_not_change_digest(self):
        policy=LearningPolicy()
        a=TestOutcome("a","backend","x",1.0,backend_id="doranet")
        b=TestOutcome("b","backend","y",-1.0,backend_id="retrobiocat2")
        _,u1=apply_test_outcomes(policy,[a,b])
        _,u2=apply_test_outcomes(policy,[b,a])
        self.assertEqual(u1.audit_digest,u2.audit_digest)

    def test_route_feedback_changes_ranking_not_lifecycle(self):
        policy=LearningPolicy()
        outcomes=(
            TestOutcome(
                "r1","route","route-good",1.0,
                features={"backend_diversity":1.0,"route_length":-1.0},
            ),
        )
        learned,_=apply_test_outcomes(policy,outcomes)
        ranked=SynBioCrowEngine().rank_routes(
            {
                "route-short-diverse":{"backend_diversity":2.0,"route_length":1.0},
                "route-long-single":{"backend_diversity":1.0,"route_length":4.0},
            },
            learned,
        )
        self.assertEqual(ranked[0][0],"route-short-diverse")

        candidate=PathwayCandidate(
            "c","CCO",(ReactionStep("CCO = CC",source_backend="doranet"),),("doranet",)
        )
        self.assertEqual(candidate.lifecycle,LifecycleState.CANDIDATE)

    def test_construct_feedback_updates_only_construct_weights(self):
        policy=LearningPolicy()
        outcome=TestOutcome(
            "c1","construct","construct-a",1.0,
            features={"qc_pass":1.0,"gc_deviation":-0.5},
        )
        learned,update=apply_test_outcomes(policy,[outcome])
        self.assertIn("qc_pass",learned.construct_feature_weights)
        self.assertEqual(dict(learned.backend_weights),{})
        self.assertEqual(dict(learned.route_feature_weights),{})
        self.assertTrue(update.construct_feature_deltas)

    def test_route_feature_matrix_is_deterministic(self):
        cands=[
            PathwayCandidate(
                "a","CCO",(ReactionStep(
                    "CCO = CC=O",source_backend="doranet",
                    metadata={"retrosynthetic_parent_side":"left"},
                ),),("doranet",)
            ),
            PathwayCandidate(
                "b","CCO",(ReactionStep(
                    "CC=O = CC",source_backend="retrobiocat2",
                    metadata={"retrosynthetic_parent_side":"left"},
                ),),("retrobiocat2",)
            ),
        ]
        graph=build_reaction_graph(cands)
        routes=[list(graph.edges)]
        m1=route_feature_matrix(graph,routes)
        m2=route_feature_matrix(graph,routes)
        self.assertEqual(m1,m2)

    def test_audit_log_is_append_only_and_says_no_lifecycle_effect(self):
        engine=SynBioCrowEngine()
        policy=LearningPolicy()
        outcomes=(TestOutcome("o1","backend","x",0.5,backend_id="doranet"),)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"learn.jsonl"
            new,update=engine.learn(policy,outcomes,audit_log=str(p))
            records=LearningAuditLog(p).read_all()
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]["lifecycle_effect"],"NONE")
        self.assertEqual(records[0]["policy_after"]["version"],2)
        self.assertEqual(records[0]["update"]["audit_digest"],update.audit_digest)

if __name__=="__main__":
    unittest.main()
