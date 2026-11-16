"""Transparent, non-probabilistic ranking of candidate graph routes.

Missing biochemical evidence is explicitly unknown, not assumed favorable.
"""
from __future__ import annotations
from typing import Mapping, Sequence


def rank_candidate_routes(routes: Sequence[Mapping]) -> list[dict]:
    """Sort graph-reachable routes by documented, deterministic heuristics.

    Rank only reachable, nontrivial routes. Fewer reactions first, then more
    independently represented engines, then stable reaction-ID ordering.
    Never call the resulting ordering biochemical feasibility or probability.
    """
    ranked = []
    for route in routes:
        if not route.get("graph_reachable"):
            continue
        evidence = route.get("reaction_evidence", [])
        if not evidence:
            continue  # target was already in stock; no pathway was discovered
        if any(not r.get("evidence_ref") or not r.get("reaction_id") or not r.get("engine") for r in evidence):
            continue
        engines = sorted({r["engine"] for r in evidence})
        ids = sorted(r["reaction_id"] for r in evidence)
        ranked.append({
            "target": route.get("target"),
            "reaction_count": len(evidence),
            "engine_count": len(engines),
            "engines": engines,
            "reaction_ids": ids,
            "ranking_basis": "graph_size_then_engine_diversity_not_biochemical_probability",
            "thermodynamics": "NOT_EVALUATED",
            "enzyme_support": "NOT_EVALUATED",
            "cofactor_balance": "NOT_EVALUATED",
            "host_feasibility": "NOT_EVALUATED",
            "experimental_validation": "NOT_EVALUATED",
            "biochemically_validated": False,
        })
    ranked.sort(key=lambda r: (r["reaction_count"], -r["engine_count"], r["reaction_ids"]))
    for i, route in enumerate(ranked, start=1):
        route["rank"] = i
    return ranked
