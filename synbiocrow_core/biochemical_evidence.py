"""Conservative, auditable per-reaction biochemical evidence annotations."""
from __future__ import annotations
from typing import Mapping, Sequence

STATES = {"SUPPORTED", "CONTRADICTED", "NOT_EVALUATED"}
DIMENSIONS = ("enzyme_support", "thermodynamics", "cofactor_balance", "host_feasibility")


def annotate_route(route: Mapping, evidence: Mapping[str, Mapping]) -> dict:
    """Annotate graph route without turning unknown evidence into a PASS.

    Evidence is keyed by stable reaction ID; each dimension has a state and
    a non-empty citation when SUPPORTED or CONTRADICTED.
    """
    reactions = route.get("reaction_evidence", [])
    annotations = []
    for reaction in reactions:
        rid = reaction["reaction_id"]
        raw = evidence.get(rid, {})
        fields = {}
        for dimension in DIMENSIONS:
            item = raw.get(dimension, {"state": "NOT_EVALUATED"})
            state = item.get("state", "NOT_EVALUATED")
            if state not in STATES:
                raise ValueError(f"{rid}/{dimension}: invalid state {state!r}")
            citation = item.get("citation")
            if state != "NOT_EVALUATED" and (not isinstance(citation, str) or not citation.strip()):
                raise ValueError(f"{rid}/{dimension}: evidence citation required")
            fields[dimension] = {"state": state, "citation": citation if state != "NOT_EVALUATED" else None}
        annotations.append({"reaction_id": rid, "dimensions": fields})
    aggregate = {}
    for dimension in DIMENSIONS:
        states = [entry["dimensions"][dimension]["state"] for entry in annotations]
        aggregate[dimension] = (
            "CONTRADICTED" if "CONTRADICTED" in states
            else "SUPPORTED" if states and all(s == "SUPPORTED" for s in states)
            else "NOT_EVALUATED"
        )
    return {
        "target": route.get("target"),
        "graph_reachable": bool(route.get("graph_reachable")),
        "reaction_evidence": list(reactions),
        "reaction_annotations": annotations,
        "route_evidence_status": aggregate,
        "biochemically_validated": False,
        "certification": "NOT_CERTIFIED",
    }
