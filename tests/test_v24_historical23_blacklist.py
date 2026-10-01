from synbiocrow.v24.historical23_blacklist import (
    reconstruct_split, heldout_id_sha256, validate_reconstruction,
)

def actual_ids():
    # Synthetic fixture with 77 ACTUAL source IDs supplied explicitly.
    return [f"pid-{i:03d}" for i in range(77)]

def test_exact_split_counts():
    dev,held=reconstruct_split(actual_ids())
    assert len(dev)==12
    assert len(held)==65
    assert set(dev).isdisjoint(held)

def test_split_is_deterministic_for_same_actual_ids():
    ids=actual_ids()
    assert reconstruct_split(ids)==reconstruct_split(ids)
    assert heldout_id_sha256(ids)==heldout_id_sha256(ids)

def test_reconstruction_rejects_missing_actual_ids():
    try:
        reconstruct_split(actual_ids()[:-1])
    except ValueError as exc:
        assert "expected 77 actual pathway IDs" in str(exc)
    else:
        raise AssertionError("expected source-ID count failure")

def test_validate_reconstruction():
    validate_reconstruction(actual_ids())
