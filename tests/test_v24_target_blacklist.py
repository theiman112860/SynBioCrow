from synbiocrow.v24.target_blacklist import (
    HistoricalTarget, build_blacklist,
)
from synbiocrow.v24.historical23_blacklist import reconstruct_split


def test_blacklist_requires_all_65_ids():
    _,held=reconstruct_split()
    rows=[
        HistoricalTarget(pid,pid,"InChI=1S/CH4/h1H4","C","benchmark")
        for pid in held[:-1]
    ]
    try:
        build_blacklist(rows,source_kind="test",source_sha256="a"*64)
    except ValueError as exc:
        assert "missing held-out" in str(exc)
    else:
        raise AssertionError("expected incomplete blacklist failure")


def test_blacklist_accepts_exact_65_ids():
    _,held=reconstruct_split()
    rows=[
        HistoricalTarget(pid,pid,"InChI=1S/CH4/h1H4","C","benchmark")
        for pid in held
    ]
    b=build_blacklist(rows,source_kind="test",source_sha256="a"*64)
    assert b.heldout_pathway_count==65
    assert b.heldout_unique_target_count==1
