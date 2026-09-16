from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_frozen_constants(alpha90):
    assert alpha90.VERSION == "Alpha90.1.2.3"
    assert alpha90.FROZEN_ENGINE == "Alpha87.11"
    assert alpha90.EXPECTED == {
        "LASER": 152,
        "Golden": 20,
        "building_blocks_437": 437,
    }


def test_sha256_path_is_stable(alpha90, tmp_path):
    p = tmp_path / "artifact.bin"
    p.write_bytes(b"SynBioCrow")
    assert alpha90.sha256_path(p) == "cefd1cc13b3a6d2a88f1ff2e6d07a2a4372fbe76040b68d379d2af87d4fd645d"
    assert alpha90.sha256_path(p) == alpha90.sha256_path(p)


def test_structure_token_extraction_is_deduplicated(alpha90):
    text = "smiles\nCCO\nCCO\nCC(=O)O\n"
    inchis, smiles = alpha90._structure_tokens(text)
    assert inchis == set()
    assert "CCO" in smiles
    assert "CC(=O)O" in smiles
    assert len(smiles) == 2


def test_bounded_discovery_respects_name_terms(alpha90, tmp_path):
    (tmp_path / "LASER_support.zip").write_bytes(b"x")
    (tmp_path / "unrelated.txt").write_text("x")
    found = alpha90.bounded_drive_discovery([tmp_path], name_terms=["laser"])
    assert [p.name for p in found] == ["LASER_support.zip"]
