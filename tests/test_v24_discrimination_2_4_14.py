from pathlib import Path
import json
import pytest

from synbiocrow.v24.discrimination_2_4_14 import (
    RouteFeatureRow,
    score_feature_row,
    rank_feature_rows,
    fit_development_weights,
)

def _row(route_id="r1", split="development", coverage=1.0):
    comps={
        "reaction_evidence_fraction":1.0,
        "reviewed_enzyme_fraction":None if coverage<1 else 1.0,
        "ec_evidence_fraction":0.5,
        "rhea_exact_fraction":0.5,
        "rhea_connectivity_fraction":0.5,
        "thermo_coverage_fraction":None if coverage<1 else 0.5,
        "mapping_confidence_mean":None,
        "engine_count_scaled":0.5,
        "cross_engine_edge_fraction":0.0,
        "route_length_scaled":0.25,
        "unsupported_edge_fraction":0.0,
        "currency_burden_fraction":0.0,
    }
    observed=sum(v is not None for v in comps.values())
    return RouteFeatureRow(
        record_id="dev1",target_name="x",route_id=route_id,split=split,
        route_length=3,engine_count=2,component_values=comps,
        observed_feature_count=observed,total_feature_count=len(comps),
        evidence_coverage=observed/len(comps),source_artifact="fixture.json",
    )

def test_missing_evidence_is_missing_and_coverage_limited():
    complete=_row("complete",coverage=1.0)
    sparse=_row("sparse",coverage=0.5)
    raw_c,adj_c=score_feature_row(complete)
    raw_s,adj_s=score_feature_row(sparse)
    assert sparse.evidence_coverage < complete.evidence_coverage
    assert adj_s == pytest.approx(raw_s*sparse.evidence_coverage)
    assert adj_c == pytest.approx(raw_c*complete.evidence_coverage)

def test_rank_rejects_nondevelopment():
    with pytest.raises(ValueError,match="development-only"):
        rank_feature_rows([_row("v1",split="validation")])

def test_fit_rejects_nondevelopment():
    rows=[_row("r1"),_row("r2",split="validation")]
    with pytest.raises(ValueError,match="development-only"):
        fit_development_weights(rows,{"r1":1.0,"r2":0.0})

def test_fit_requires_real_label_contrast():
    rows=[_row("r1"),_row("r2")]
    with pytest.raises(ValueError,match="differing relevance"):
        fit_development_weights(rows,{"r1":1.0,"r2":1.0})
