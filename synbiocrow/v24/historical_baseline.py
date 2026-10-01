"""Historical-only baseline readiness and policy-order diagnostics.

This module never consumes evaluation truth and never tunes policy weights.
It exists to (a) verify fixed candidate/route reconstruction, (b) determine
whether historical ranking inputs are actually present, and (c) compare policy
orderings descriptively without claiming improvement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .benchmark23 import Historical23RouteSet
from .ranking import POLICIES, RankingPolicy, rank


@dataclass(frozen=True)
class HistoricalBaselineStatus:
    target_id: str
    route_count: int
    has_structural_2d: bool
    has_structural_3d: bool
    has_reaction_evidence: bool
    has_reviewed_enzyme_evidence: bool
    has_rhea_exact_evidence: bool
    has_thermo_evidence: bool
    historical_2d_baseline_reproducible: bool
    reason: str


def assess_route_set(route_set: Historical23RouteSet) -> HistoricalBaselineStatus:
    routes = list(route_set.routes)
    has_2d = bool(routes) and all(r.features.structural_2d is not None for r in routes)
    has_3d = bool(routes) and all(r.features.structural_3d is not None for r in routes)
    has_reaction = any((r.features.reaction_evidence_fraction or 0.0) > 0.0 for r in routes)
    has_reviewed = any((r.features.reviewed_enzyme_fraction or 0.0) > 0.0 for r in routes)
    has_rhea = any((r.features.rhea_exact_fraction or 0.0) > 0.0 for r in routes)
    has_thermo = any((r.features.thermo_coverage_fraction or 0.0) > 0.0 for r in routes)

    if not routes:
        reproducible = False
        reason = "no persisted ensemble routes"
    elif not has_2d:
        reproducible = False
        reason = "persisted route graph lacks frozen route-level 2D ranking scores"
    else:
        reproducible = True
        reason = "route-level 2D ranking scores present for every persisted route"

    return HistoricalBaselineStatus(
        target_id=route_set.target_id,
        route_count=len(routes),
        has_structural_2d=has_2d,
        has_structural_3d=has_3d,
        has_reaction_evidence=has_reaction,
        has_reviewed_enzyme_evidence=has_reviewed,
        has_rhea_exact_evidence=has_rhea,
        has_thermo_evidence=has_thermo,
        historical_2d_baseline_reproducible=reproducible,
        reason=reason,
    )


def policy_order_diagnostics(
    route_set: Historical23RouteSet,
    policies: Sequence[RankingPolicy] = POLICIES,
) -> List[dict]:
    """Return descriptive fixed-candidate orderings with no truth labels."""
    rows: List[dict] = []
    for policy in policies:
        ranked = rank(route_set.routes, policy)
        for row in ranked:
            rows.append({
                "target_id": route_set.target_id,
                "target_name": route_set.target_name,
                "policy_id": policy.policy_id,
                "route_id": row["route_id"],
                "rank": row["rank"],
                "score": row["score"],
                "observed_weighted_features": row["observed_weighted_features"],
                "historical_only": True,
                "tuning_permitted": False,
                "truth_consumed": False,
            })
    return rows


def summarize_readiness(route_sets: Iterable[Historical23RouteSet]) -> dict:
    statuses = [assess_route_set(x) for x in route_sets]
    return {
        "target_count": len(statuses),
        "targets_with_routes": sum(s.route_count > 0 for s in statuses),
        "targets_with_reproducible_2d_baseline": sum(
            s.historical_2d_baseline_reproducible for s in statuses
        ),
        "targets_with_any_reaction_evidence": sum(s.has_reaction_evidence for s in statuses),
        "targets_with_any_reviewed_enzyme_evidence": sum(
            s.has_reviewed_enzyme_evidence for s in statuses
        ),
        "targets_with_any_rhea_exact_evidence": sum(s.has_rhea_exact_evidence for s in statuses),
        "targets_with_any_thermo_evidence": sum(s.has_thermo_evidence for s in statuses),
        "historical_only": True,
        "tuning_permitted": False,
        "truth_consumed": False,
    }
