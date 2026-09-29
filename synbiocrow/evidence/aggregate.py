from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from synbiocrow.ensemble.graph import EnsembleGraph
from synbiocrow.core.models import LifecycleState, ReactionStep
from .closure import stoichiometric_closure
from .gates import GateDecision, GateResult, require_all
from .rhea import RheaClient, rhea_evidence_for_edge
from .uniprot import UniProtRheaClient, enzyme_evidence_for_exact_rhea, enzyme_context_for_ecs
from .thermodynamics import EquilibratorThermoClient, thermodynamic_evidence_for_edge, ThermodynamicResult

@dataclass(frozen=True)
class EdgeEvidenceReport:
    edge_id: str
    closure: GateResult
    rhea: GateResult
    thermodynamics: GateResult
    enzyme: GateResult
    enzyme_context: GateResult
    exact_rhea_ids: tuple[str, ...] = ()
    reviewed_uniprot_accessions: tuple[str, ...] = ()
    contextual_uniprot_accessions: tuple[str, ...] = ()
    thermodynamic_result: ThermodynamicResult | None = None

    @property
    def overall(self) -> GateDecision:
        return require_all((self.closure, self.rhea, self.thermodynamics, self.enzyme))

@dataclass(frozen=True)
class RouteEvidenceReport:
    edge_reports: tuple[EdgeEvidenceReport, ...]
    lifecycle: LifecycleState = LifecycleState.CANDIDATE

    @property
    def overall(self) -> GateDecision:
        return require_all(report.overall for report in self.edge_reports)

def evaluate_route_evidence(
    graph: EnsembleGraph,
    edge_ids: Iterable[str],
    *,
    rhea_client: RheaClient | None = None,
    uniprot_client: UniProtRheaClient | None = None,
    thermo_client: EquilibratorThermoClient | None = None,
) -> RouteEvidenceReport:
    rhea_client = rhea_client or RheaClient()
    uniprot_client = uniprot_client or UniProtRheaClient()
    thermo_client = thermo_client or EquilibratorThermoClient()
    reports = []

    for edge_id in edge_ids:
        edge = graph.edges[edge_id]
        closure = stoichiometric_closure(ReactionStep(reaction=edge.reaction, source_backend="ensemble"))
        rhea_gate, rhea_hits = rhea_evidence_for_edge(graph, edge, rhea_client)
        exact_ids = tuple(sorted(set(rhea_gate.evidence))) if rhea_gate.decision is GateDecision.PASS else ()
        thermo_gate, thermo_result = thermodynamic_evidence_for_edge(edge, thermo_client)
        enzyme_gate, enzyme_hits = enzyme_evidence_for_exact_rhea(list(exact_ids), uniprot_client)
        ecs=sorted({ec for hit in rhea_hits for ec in hit.ec})
        context_gate, context_hits = enzyme_context_for_ecs(ecs, uniprot_client)
        reports.append(EdgeEvidenceReport(
            edge_id=edge_id,
            closure=closure,
            rhea=rhea_gate,
            thermodynamics=thermo_gate,
            enzyme=enzyme_gate,
            enzyme_context=context_gate,
            exact_rhea_ids=exact_ids,
            reviewed_uniprot_accessions=tuple(sorted(h.accession for h in enzyme_hits if h.accession)),
            contextual_uniprot_accessions=tuple(sorted(h.accession for h in context_hits if h.accession)),
            thermodynamic_result=thermo_result,
        ))

    return RouteEvidenceReport(tuple(reports), LifecycleState.CANDIDATE)
