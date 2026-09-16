from pathlib import Path

import pytest

pytestmark = pytest.mark.contract


def test_certification_fails_closed(alpha90):
    cert, evidence = alpha90.certify([])
    assert set(cert) == set(alpha90.EXPECTED)
    assert all(v["status"] == "BLOCK" for v in cert.values())
    assert all(evidence[k] == [] for k in alpha90.EXPECTED)


def test_exact_counts_without_provenance_do_not_pass(alpha90):
    rows = []
    for kind, expected in alpha90.EXPECTED.items():
        rows.append({
            "archive": "untrusted.txt",
            "member": kind,
            "sha256": "0" * 64,
            "provenance_signal": False,
            "laser_signal": kind == "LASER",
            "golden_signal": kind == "Golden",
            "building_signal": kind == "building_blocks_437",
            "pathway_signal": True,
            "structure_count": expected,
        })
    cert, _ = alpha90.certify(rows)
    assert all(v["status"] == "BLOCK" for v in cert.values())


def test_golden_requires_pathway_semantics(alpha90):
    row = {
        "archive": "supplementary_data.zip",
        "member": "golden_targets.csv",
        "sha256": "1" * 64,
        "provenance_signal": True,
        "laser_signal": False,
        "golden_signal": True,
        "building_signal": False,
        "pathway_signal": False,
        "structure_count": 20,
    }
    cert, _ = alpha90.certify([row])
    assert cert["Golden"]["status"] == "BLOCK"


def test_alpha90_2_requires_all_three_gates(alpha90, tmp_path):
    rows = []
    for kind, expected in alpha90.EXPECTED.items():
        rows.append({
            "archive": "ACS_supplementary_data.zip",
            "member": f"{kind}_pathway.csv",
            "sha256": kind.encode().hex().ljust(64, "0")[:64],
            "provenance_signal": True,
            "laser_signal": kind == "LASER",
            "golden_signal": kind == "Golden",
            "building_signal": kind == "building_blocks_437",
            "pathway_signal": True,
            "structure_count": expected,
        })
    cert, _ = alpha90.certify(rows)
    assert all(v["status"] == "PASS" for v in cert.values())
    rows[-1]["structure_count"] = 436
    cert, _ = alpha90.certify(rows)
    assert cert["building_blocks_437"]["status"] == "BLOCK"
