from synbiocrow.v24.tranche import (
    HistoricalExclusionStatus, SourceTranche, TrancheRecord,
)


def rec(status, mapping="reviewed"):
    return TrancheRecord(
        record_id="r1",
        target_name="x",
        normalized_target="CCO",
        family_key="fam",
        source_ids=("doi:1",),
        primary_doi="10.1/example",
        pubchem_cid="1",
        publication_year=2025,
        chemistry_class="test",
        mapping_quality=mapping,
        historical_exclusion_status=status,
        exclusion_basis="checked against frozen list" if status == HistoricalExclusionStatus.VERIFIED_EXCLUDED else "",
    )


def test_pending_record_is_not_promotable():
    assert not rec(HistoricalExclusionStatus.PENDING).promotable


def test_verified_record_is_promotable():
    assert rec(HistoricalExclusionStatus.VERIFIED_EXCLUDED).promotable


def test_needs_review_mapping_is_not_promotable():
    assert not rec(HistoricalExclusionStatus.VERIFIED_EXCLUDED, "needs-review").promotable


def test_tranche_hash_is_deterministic():
    t = SourceTranche("t", "1", [rec(HistoricalExclusionStatus.PENDING)])
    assert t.sha256() == t.sha256()
