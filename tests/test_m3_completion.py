import unittest

from synbiocrow.core.models import PathwayCandidate, ReactionStep, LifecycleState
from synbiocrow.ensemble import build_reaction_graph
from synbiocrow.evidence import (
    GateDecision, RheaHit, UniProtEnzymeHit,
    ThermodynamicResult, evaluate_route_evidence,
)

class FakeRhea:
    def search_inchikeys(self, keys, limit=50):
        return [RheaHit("RHEA:12345","ethanol = acetaldehyde",("EC:1.1.1.1",))]

class FakeUniProt:
    def reviewed_for_rhea(self, rid, size=25):
        return [UniProtEnzymeHit("P12345","DEMO","Demo enzyme","E. coli",300)]
    def reviewed_for_ec(self, ec, size=25):
        return [UniProtEnzymeHit("P54321","CTX","Context enzyme","Bacillus",280)]

class FakeThermo:
    def compute(self, formula):
        return ThermodynamicResult(-12.5,1.2,7.0,0.25,298.15,formula)

class M3CompletionTests(unittest.TestCase):
    def test_exact_rhea_thermo_enzyme_can_all_pass_without_promotion(self):
        cand=PathwayCandidate(
            "c1","CCO",
            (ReactionStep(
                "CCO = CC=O",
                source_backend="doranet",
                metadata={
                    "direction":"retro",
                    "rhea_id":"12345",
                    "rhea_equation":"ethanol = acetaldehyde",
                    "equilibrator_formula":"kegg:C00469 = kegg:C00084",
                },
            ),),
            ("doranet",),
        )
        g=build_reaction_graph([cand])
        eid=next(iter(g.edges))
        report=evaluate_route_evidence(
            g,[eid],
            rhea_client=FakeRhea(),
            uniprot_client=FakeUniProt(),
            thermo_client=FakeThermo(),
        )
        e=report.edge_reports[0]
        self.assertEqual(e.rhea.decision,GateDecision.PASS)
        self.assertEqual(e.thermodynamics.decision,GateDecision.PASS)
        self.assertEqual(e.enzyme.decision,GateDecision.PASS)
        self.assertEqual(e.enzyme_context.decision,GateDecision.PASS)
        self.assertEqual(report.lifecycle,LifecycleState.CANDIDATE)
        self.assertEqual(report.overall,GateDecision.PASS)

    def test_rhea_id_without_equation_stays_abstain(self):
        cand=PathwayCandidate(
            "c1","CCO",
            (ReactionStep("CCO = CC=O",source_backend="doranet",
             metadata={"direction":"retro","rhea_id":"12345"}),),
            ("doranet",),
        )
        g=build_reaction_graph([cand])
        eid=next(iter(g.edges))
        report=evaluate_route_evidence(
            g,[eid],rhea_client=FakeRhea(),uniprot_client=FakeUniProt(),thermo_client=FakeThermo()
        )
        self.assertEqual(report.edge_reports[0].rhea.decision,GateDecision.ABSTAIN)

if __name__=="__main__": unittest.main()
