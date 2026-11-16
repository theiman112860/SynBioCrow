"""Single conservative report combining graph evidence, annotation, and ranking."""
from __future__ import annotations
from typing import Mapping
from .biochemical_evidence import annotate_route
from .pathway_ranking import rank_candidate_routes


def build_integrated_report(graph_report: Mapping, evidence: Mapping[str, Mapping] | None = None) -> dict:
    evidence = evidence or {}
    annotated = annotate_route(graph_report, evidence)
    ranked = rank_candidate_routes([graph_report])
    return {
        "schema": "synbiocrow.integrated-pathway-report.v1",
        "target": graph_report.get("target"),
        "graph_reachable": bool(graph_report.get("graph_reachable")),
        "graph": dict(graph_report),
        "biochemical_evidence": annotated,
        "candidate_rank": ranked[0] if ranked else None,
        "scientific_certification": "NOT_CERTIFIED",
        "limitations": [
            "Graph reachability does not establish biochemical feasibility",
            "Missing reaction evidence is NOT_EVALUATED",
            "Single-candidate ranking is descriptive, not comparative",
        ],
    }
