import hashlib
import io
import zipfile

from synbiocrow.v24.release23_verify import _parse_manifest, _parse_table


def test_parse_manifest():
    x = _parse_manifest("a=1\nb = two\n")
    assert x == {"a": "1", "b": "two"}


def test_parse_table():
    text = (
        "arm,partial_recovery_targets,exact_top10,exact_top50\n"
        "ensemble,19,0,2\n"
    )
    t = _parse_table(text)
    assert t["ensemble"]["partial_recovery_targets"] == "19"
    assert t["ensemble"]["exact_top50"] == "2"


def test_recorded_digest_is_not_byte_verification():
    # The 2.4.5 design explicitly distinguishes a digest written in a manifest
    # from possession/verification of the corresponding original artifact.
    manifest = _parse_manifest("sealed_predictions_sha256=" + "a"*64)
    assert manifest["sealed_predictions_sha256"] == "a"*64
    # There is intentionally no implication here that any file with this digest exists.
