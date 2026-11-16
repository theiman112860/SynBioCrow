"""Evidence-aware prioritization without fabricated biochemical probabilities."""
from __future__ import annotations
from typing import Mapping, Sequence
from .biochemical_evidence import annotate_route, DIMENSIONS


def prioritize_evidence_annotated_routes(candidates: Sequence[Mapping], evidence: Mapping[str, Mapping]) -> list[dict]:
    """Conservatively triage graph candidates using cited evidence.

    Contradictions last; fewer unknown reaction-dimension checks first; then
    fewer steps. A supported citation is evidence *annotation*, not proof.
    """
    result = []
    for route in candidates:
        if not route.get("graph_reachable") or not route.get("reaction_evidence"):
            continue
        annotations = annotate_route(route, evidence)
        statuses = [a["dimensions"][dimension]["state"]
                    for a in annotations["reaction_annotations"] for dimension in DIMENSIONS]
        contradictions = statuses.count("CONTRADICTED")
        unknown = statuses.count("NOT_EVALUATED")
        supported = statuses.count("SUPPORTED")
        result.append({
            "target": route.get("target"),
            "reaction_ids": [r["reaction_id"] for r in route["reaction_evidence"]],
            "reaction_count": len(route["reaction_evidence"]),
            "supported_checks": supported,
            "unknown_checks": unknown,
            "contradicted_checks": contradictions,
            "route_evidence_status": annotations["route_evidence_status"],
            "triage": "CONTRADICTION_REVIEW" if contradictions else
                      "EVIDENCE_GAPS" if unknown else "ANNOTATED_REVIEW",
            "scientific_certification": "NOT_CERTIFIED",
            "biochemically_validated": False,
        })
    result.sort(key=lambda x: (bool(x["contradicted_checks"]), x["unknown_checks"],
                               x["reaction_count"], x["reaction_ids"]))
    for rank, item in enumerate(result, start=1):
        item["triage_rank"] = rank
    return result
