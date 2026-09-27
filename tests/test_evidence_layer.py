import unittest
from unittest.mock import patch

from synbiocrow.core.models import PathwayCandidate, ReactionStep, LifecycleState
from synbiocrow.ensemble import build_reaction_graph, resolve_retropath_graph_identities, RetroPathIdentityRecord
from synbiocrow.evidence import (
    GateDecision,
    RheaHit,
    stoichiometric_closure,
    rhea_evidence_for_edge,
    enzyme_evidence_for_exact_rhea,
    evaluate_route_evidence,
)
from synbiocrow.evidence.uniprot import UniProtEnzymeHit


class FakeRhea:
    def __init__(self, hits):
        self.hits = hits
    def search_inchikeys(self, keys, limit=50):
        return list(self.hits)


class FakeUniProt:
    def __init__(self, hits):
        self.hits = hits
    def reviewed_for_rhea(self, rhea_id, size=25):
        return list(self.hits)


class EvidenceLayerTests(unittest.TestCase):
    def test_closure_passes_balanced_reaction(self):
        step = ReactionStep("CCO = CCO")
        result = stoichiometric_closure(step)
        self.assertEqual(result.decision, GateDecision.PASS)

    def test_closure_handles_charged_smiles_without_bad_split(self):
        step = ReactionStep("[NH4+] = [NH4+]")
        result = stoichiometric_closure(step)
        self.assertEqual(result.decision, GateDecision.PASS)

    def test_closure_fails_unbalanced_reaction(self):
        step = ReactionStep("CC = C")
        result = stoichiometric_closure(step)
        self.assertEqual(result.decision, GateDecision.FAIL)

    def test_rhea_contextual_match_abstains(self):
        cand = PathwayCandidate(
            "c1","CCO",
            (ReactionStep("CCO = CC=O", source_backend="doranet", metadata={"direction":"retro"}),),
            ("doranet",),
        )
        graph = build_reaction_graph([cand])
        edge = next(iter(graph.edges.values()))
        gate, hits = rhea_evidence_for_edge(
            graph, edge,
            FakeRhea([RheaHit("RHEA:12345","demo")]),
        )
        self.assertEqual(gate.decision, GateDecision.ABSTAIN)
        self.assertEqual(len(hits), 1)

    def test_explicit_rhea_id_without_equation_abstains(self):
        cand = PathwayCandidate(
            "c1","CCO",
            (ReactionStep(
                "CCO = CC=O",
                source_backend="doranet",
                metadata={"direction":"retro","rhea_id":"12345"},
            ),),
            ("doranet",),
        )
        graph = build_reaction_graph([cand])
        edge = next(iter(graph.edges.values()))
        gate, hits = rhea_evidence_for_edge(
            graph, edge,
            FakeRhea([RheaHit("RHEA:12345","demo")]),
        )
        self.assertEqual(gate.decision, GateDecision.ABSTAIN)
        self.assertEqual(gate.evidence, ("RHEA:12345",))

    def test_exact_rhea_reviewed_uniprot_can_pass(self):
        gate, hits = enzyme_evidence_for_exact_rhea(
            ["RHEA:12345"],
            FakeUniProt([
                UniProtEnzymeHit("P12345","DEMO_ECOLI","Demo enzyme","Escherichia coli",300)
            ]),
        )
        self.assertEqual(gate.decision, GateDecision.PASS)
        self.assertEqual(gate.evidence, ("P12345",))

    def test_no_exact_rhea_means_enzyme_abstention(self):
        gate, hits = enzyme_evidence_for_exact_rhea([], FakeUniProt([]))
        self.assertEqual(gate.decision, GateDecision.ABSTAIN)
        self.assertEqual(hits, [])

    def test_retropath_mapping_unlocks_canonical_join(self):
        rp = PathwayCandidate(
            "rp","CCO",
            (ReactionStep(
                "CMPD_X = CMPD_T",
                source_backend="retropath2",
                metadata={"retrosynthetic_parent_side":"right"},
            ),),
            ("retropath2",),
        )
        rb = PathwayCandidate(
            "rb","CCO",
            (ReactionStep(
                "CC=O = CC",
                source_backend="retrobiocat2",
                metadata={"retrosynthetic_parent_side":"left"},
            ),),
            ("retrobiocat2",),
        )
        g = build_reaction_graph([rp, rb])
        mapped = resolve_retropath_graph_identities(
            g,
            {
                "CMPD_T": RetroPathIdentityRecord("CMPD_T","CCO"),
                "CMPD_X": RetroPathIdentityRecord("CMPD_X","CC=O"),
            },
        )
        self.assertIn("retropath2", mapped.backend_set())
        self.assertIn("retrobiocat2", mapped.backend_set())

    def test_route_evidence_never_auto_promotes(self):
        cand = PathwayCandidate(
            "c1","CCO",
            (ReactionStep(
                "CCO = CCO",
                source_backend="doranet",
                metadata={"direction":"retro","rhea_id":"12345"},
            ),),
            ("doranet",),
        )
        graph = build_reaction_graph([cand])
        edge_id = next(iter(graph.edges))
        report = evaluate_route_evidence(
            graph,
            [edge_id],
            rhea_client=FakeRhea([RheaHit("RHEA:12345","demo")]),
            uniprot_client=FakeUniProt([
                UniProtEnzymeHit("P12345","DEMO","Demo enzyme","E. coli",300)
            ]),
        )
        self.assertEqual(report.lifecycle, LifecycleState.CANDIDATE)
        self.assertEqual(report.overall, GateDecision.PASS)


if __name__ == "__main__":
    unittest.main()
