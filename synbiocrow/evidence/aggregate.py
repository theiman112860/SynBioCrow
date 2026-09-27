from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from synbiocrow.ensemble.graph import EnsembleGraph
from synbiocrow.core.models import LifecycleState
from .closure import stoichiometric_closure
from .gates import GateDecision, GateResult, require_all
from .rhea import RheaClient, rhea_evidence_for_edge
from .uniprot import UniProtRheaClient, enzyme_evidence_for_exact_rhea

@dataclass(frozen=True)
class EdgeEvidenceReport:
    edge_id: str
    closure: GateResult
    rhea: GateResult
    enzyme: GateResult
    exact_rhea_ids: tuple[str, ...] = ()
    reviewed_uniprot_accessions: tuple[str, ...] = ()

    @property
    def overall(self) -> GateDecision:
        return require_all((self.closure, self.rhea, self.enzyme))

@dataclass(frozen=True)
class RouteEvidenceReport:
    edge_reports: tuple[EdgeEvidenceReport, ...]
    lifecycle: LifecycleState = LifecycleState.CANDIDATE

    @property
    def overall(self) -> GateDecision:
        return require_all(report.overall for report in self.edge_reports)

    @property
    def exact_rhea_ids(self) -> tuple[str, ...]:
        return tuple(sorted({rid for r in self.edge_reports for rid in r.exact_rhea_ids}))

    @property
    def reviewed_uniprot_accessions(self) -> tuple[str, ...]:
        return tuple(sorted({acc for r in self.edge_reports for acc in r.reviewed_uniprot_accessions}))

def evaluate_route_evidence(
    graph: EnsembleGraph,
    edge_ids: Iterable[str],
    *,
    rhea_client: RheaClient | None = None,
    uniprot_client: UniProtRheaClient | None = None,
) -> RouteEvidenceReport:
    rhea_client = rhea_client or RheaClient()
    uniprot_client = uniprot_client or UniProtRheaClient()
    reports = []

    for edge_id in edge_ids:
        edge = graph.edges[edge_id]

        # Closure operates on the normalized reaction text.
        from synbiocrow.core.models import ReactionStep
        step = ReactionStep(
            reaction=edge.reaction,
            source_backend="ensemble",
            metadata={},
        )
        closure = stoichiometric_closure(step)

        rhea_gate, rhea_hits = rhea_evidence_for_edge(graph, edge, rhea_client)
        exact_ids = tuple(sorted({
            h.rhea_id for h in rhea_hits
            if h.rhea_id and h.rhea_id in set(rhea_gate.evidence)
        })) if rhea_gate.decision is GateDecision.PASS else ()

        enzyme_gate, enzyme_hits = enzyme_evidence_for_exact_rhea(
            list(exact_ids), uniprot_client
        )

        reports.append(
            EdgeEvidenceReport(
                edge_id=edge_id,
                closure=closure,
                rhea=rhea_gate,
                enzyme=enzyme_gate,
                exact_rhea_ids=exact_ids,
                reviewed_uniprot_accessions=tuple(
                    sorted(h.accession for h in enzyme_hits if h.accession)
                ),
            )
        )

    # Evidence reports never auto-promote lifecycle state.
    return RouteEvidenceReport(tuple(reports), LifecycleState.CANDIDATE)
