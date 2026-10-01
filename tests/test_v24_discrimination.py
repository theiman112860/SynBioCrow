import pytest
from synbiocrow.v24.discrimination import EvidenceValue, RouteEvidence, score_route

def test_missing_is_not_negative_and_coverage_caps_score():
    r=RouteEvidence("r1","dev1","development",{
        "reaction_compatibility":EvidenceValue(1.0,("rhea:1",)),
        "enzyme_precedent":EvidenceValue(1.0,("uniprot:P1",)),
    })
    s=score_route(r)
    assert s.observed_mean==1.0
    assert s.observed_components==2
    assert s.evidence_coverage==pytest.approx(2/7)
    assert s.coverage_adjusted_score==pytest.approx(2/7)
    assert "thermodynamic_support" in s.missing_components

def test_observed_value_requires_provenance():
    r=RouteEvidence("r1","dev1","development",{
        "reaction_compatibility":EvidenceValue(0.8,()),
    })
    with pytest.raises(ValueError,match="provenance"):
        score_route(r)

def test_validation_is_sealed():
    r=RouteEvidence("r1","val1","validation",{})
    with pytest.raises(ValueError,match="development-only"):
        score_route(r)

def test_negative_evidence_is_allowed_with_provenance():
    r=RouteEvidence("r1","dev1","development",{
        "reaction_compatibility":EvidenceValue(0.0,("audit:test",)),
    })
    s=score_route(r)
    assert s.observed_mean==0.0
    assert s.coverage_adjusted_score==0.0
