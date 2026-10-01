from synbiocrow.v24 import (
    BenchmarkManifest, BenchmarkRecord, BenchmarkSplit, EvidenceLevel,
    ReactionEvidence, SealedPredictionManifest, aggregate_route_evidence,
)


def test_unknown_is_not_support():
    r = ReactionEvidence("r1")
    agg = aggregate_route_evidence("route", [r])
    assert agg.supported_reactions == 0
    assert agg.unknown_evidence_reactions == 1


def test_explicit_evidence_aggregates():
    r = ReactionEvidence(
        "r1", engines=("retrobiocat2", "retropath2"),
        rhea_exact=True, reviewed_uniprot=("P12345",),
        evidence_level=EvidenceLevel.REVIEWED,
        provenance=("Rhea:12345", "UniProt:P12345"),
    )
    agg = aggregate_route_evidence("route", [r])
    assert agg.supported_reactions == 1
    assert agg.rhea_exact_reactions == 1
    assert agg.reviewed_enzyme_reactions == 1
    assert len(agg.independent_engines) == 2


def test_historical_23_is_never_tunable():
    r = BenchmarkRecord("old1", "target1", BenchmarkSplit.HISTORICAL_23, ("galaxy",))
    assert not r.tunable


def test_evaluation_overlap_is_rejected():
    m = BenchmarkManifest("b", "1", records=[
        BenchmarkRecord("a", "same", BenchmarkSplit.DEVELOPMENT, ("s1",)),
        BenchmarkRecord("b", "same", BenchmarkSplit.EVALUATION, ("s2",)),
    ])
    try:
        m.validate()
    except ValueError as exc:
        assert "leakage" in str(exc)
    else:
        raise AssertionError("expected leakage failure")


def test_seal_rejects_prior_truth_access():
    x = SealedPredictionManifest(
        "e", "abc", "rank-v1", "0"*64, "1"*64,
        truth_accessed_before_seal=True,
    )
    try:
        x.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("expected truth-access failure")


def test_manifest_hash_is_deterministic():
    m = BenchmarkManifest("b", "1", records=[
        BenchmarkRecord("a", "t1", BenchmarkSplit.DEVELOPMENT, ("s1",)),
        BenchmarkRecord("b", "t2", BenchmarkSplit.EVALUATION, ("s2",)),
    ])
    assert m.sha256() == m.sha256()
    assert len(m.sha256()) == 64
