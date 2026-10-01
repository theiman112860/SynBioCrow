from synbiocrow.v24.curation import (
    HarvestedPathwayRecord, curate_record, deduplicate_curated,
)


def raw(src, target="CCO", literature=("DOI:1",)):
    return HarvestedPathwayRecord(
        source_record_id=src,
        target_name="ethanol",
        target_structure=target,
        source_ids=(src,),
        source_type="literature",
        literature_ids=literature,
        chemistry_class="alcohol",
        mapping_quality="reviewed",
    )


def test_duplicate_target_merges_sources():
    a = curate_record(raw("A"), family_key="alcohols")
    b = curate_record(raw("B"), family_key="alcohols")
    rows, audit = deduplicate_curated([a,b])
    assert len(rows) == 1
    assert rows[0].source_ids == ("A","B")
    assert len(audit) == 1


def test_family_conflict_fails_closed():
    a = curate_record(raw("A"), family_key="fam-a")
    b = curate_record(raw("B"), family_key="fam-b")
    try:
        deduplicate_curated([a,b])
    except ValueError as exc:
        assert "conflicting family" in str(exc)
    else:
        raise AssertionError("expected family conflict")


def test_frozen23_blacklist_marks_record():
    a = curate_record(
        raw("A", target="CCO"),
        family_key="alcohols",
        frozen23_normalized_targets=("CCO",),
    )
    assert a.historical_23_member
    assert "frozen-2.3-member" in a.curation_flags
