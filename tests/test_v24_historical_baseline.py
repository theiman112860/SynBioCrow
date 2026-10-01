from synbiocrow.v24.adapters import AdaptedRoute
from synbiocrow.v24.benchmark23 import Historical23RouteSet
from synbiocrow.v24.evidence import RankingFeatureVector
from synbiocrow.v24.galaxy23 import frozen_reference_summary
from synbiocrow.v24.historical_baseline import assess_route_set


def _route(route_id, structural_2d=None, reaction_evidence_fraction=0.0):
    return AdaptedRoute(
        route_id=route_id,
        reactions=(),
        features=RankingFeatureVector(
            route_id=route_id,
            structural_2d=structural_2d,
            reaction_evidence_fraction=reaction_evidence_fraction,
        ),
        source_format="test",
    )


def test_baseline_not_claimed_when_2d_scores_missing():
    s = Historical23RouteSet(
        target_id="t",
        target_name="T",
        run_id="r",
        routes=(_route("a"), _route("b")),
        candidate_count=2,
        edge_count=2,
    )
    status = assess_route_set(s)
    assert status.route_count == 2
    assert not status.historical_2d_baseline_reproducible
    assert "lacks frozen route-level 2D" in status.reason


def test_baseline_reproducible_only_when_all_2d_scores_present():
    s = Historical23RouteSet(
        target_id="t",
        target_name="T",
        run_id="r",
        routes=(_route("a", 0.7), _route("b", 0.2)),
        candidate_count=2,
        edge_count=2,
    )
    assert assess_route_set(s).historical_2d_baseline_reproducible


def test_frozen_galaxy_reference_is_historical_only():
    s = frozen_reference_summary()
    assert s.denominator == 65
    assert s.runnable == 64
    assert s.metrics["ensemble_partial"] == 19
    assert s.metrics["retropath_exact_top50"] == 2
    assert s.historical_only
    assert not s.tuning_permitted
