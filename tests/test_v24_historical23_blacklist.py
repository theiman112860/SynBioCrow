from synbiocrow.v24.historical23_blacklist import (
    reconstruct_split, heldout_id_sha256, validate_reconstruction,
)

def test_exact_split_counts():
    dev,held=reconstruct_split()
    assert len(dev)==12
    assert len(held)==65
    assert set(dev).isdisjoint(held)

def test_known_mapping_limited_record_is_heldout():
    _,held=reconstruct_split()
    assert "literature_10" in held

def test_blacklist_digest_is_frozen():
    assert heldout_id_sha256()=="c7c43814c973e941172b18b8745ba7e79bcaa4e4e193bfde473b796415bbd58f"
    validate_reconstruction()
