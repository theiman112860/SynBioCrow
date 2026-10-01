"""Verify the public SynBioCrow 2.3 release-support package.

This verifier distinguishes three states:
1. release-package byte verified;
2. frozen manifest values verified;
3. original frozen artifact bytes verified (only if those files are supplied).

It never equates a recorded digest with possession of the underlying artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional
from zipfile import ZipFile

from .galaxy23 import FROZEN_EXPECTED, FROZEN_HASHES

EXPECTED_RELEASE_ZIP_SHA256 = "2be72abfd4d3fc123d22a09002dc6718c4f7f33b2d0cf4ed40884e8463fd5462"
EXPECTED_FREEZE_COMMIT = "39b3b21d8a5018001746a1ad783859cba75f9ad5"
EXPECTED_FREEZE_PACKAGE_SHA256 = "67bea03543b60f4299aace5e1de674357e9ffed88e1a2d2fc21dc47c83cfcaf6"
EXPECTED_SIMILARITY_SHA256 = "7448c031189a1c42a13f16c1856efef30c95de19a0059f5c87166b4ddcced7e4"
EXPECTED_MANUSCRIPT_SHA256 = "b25abe53beb07511e2ff375a6f37e4bb9f51381ccbbf76a5044f49b0bc6d9539"

MANIFEST_MEMBER = "SynBioCrow_2_3_RELEASE_SUPPORT/FROZEN_SCIENTIFIC_MANIFEST.txt"
TABLE_MEMBER = "SynBioCrow_2_3_RELEASE_SUPPORT/manuscript_assets/table_benchmark_summary.csv"
README_MEMBER = "SynBioCrow_2_3_RELEASE_SUPPORT/RELEASE_PACKAGE_README.md"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _parse_manifest(text: str) -> Dict[str, str]:
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _parse_table(text: str) -> Dict[str, dict]:
    rows = {}
    for row in csv.DictReader(io.StringIO(text)):
        rows[row["arm"]] = row
    return rows


@dataclass(frozen=True)
class Release23Verification:
    release_zip_sha256: str
    release_zip_verified: bool
    manifest_verified: bool
    aggregate_metrics_verified: bool
    sealed_predictions_manifest_confirmed: bool
    scored_benchmark_manifest_confirmed: bool
    error_analysis_manifest_confirmed: bool
    sealed_predictions_bytes_verified: bool
    scored_benchmark_bytes_verified: bool
    error_analysis_bytes_verified: bool
    original_artifacts_present: bool
    historical_only: bool = True
    tuning_permitted: bool = False

    @property
    def complete_byte_verification(self) -> bool:
        return (
            self.release_zip_verified
            and self.manifest_verified
            and self.aggregate_metrics_verified
            and self.sealed_predictions_bytes_verified
            and self.scored_benchmark_bytes_verified
            and self.error_analysis_bytes_verified
        )


def verify_release_support_zip(
    zip_path: str,
    artifact_paths: Optional[Mapping[str, str]] = None,
) -> Release23Verification:
    release_digest = sha256_file(zip_path)
    release_ok = release_digest == EXPECTED_RELEASE_ZIP_SHA256

    with ZipFile(zip_path) as z:
        names = set(z.namelist())
        missing = [x for x in (MANIFEST_MEMBER, TABLE_MEMBER, README_MEMBER) if x not in names]
        if missing:
            raise ValueError(f"release-support package missing required members: {missing}")

        manifest = _parse_manifest(z.read(MANIFEST_MEMBER).decode("utf-8"))
        table = _parse_table(z.read(TABLE_MEMBER).decode("utf-8"))

    expected_manifest = {
        "scientific_freeze_commit": EXPECTED_FREEZE_COMMIT,
        "freeze_package_sha256": EXPECTED_FREEZE_PACKAGE_SHA256,
        "sealed_predictions_sha256": FROZEN_HASHES["sealed_predictions"],
        "scored_galaxy_benchmark_sha256": FROZEN_HASHES["scored_benchmark"],
        "error_analysis_sha256": FROZEN_HASHES["error_analysis"],
        "similarity_policy_sha256": EXPECTED_SIMILARITY_SHA256,
        "frozen_manuscript_sha256": EXPECTED_MANUSCRIPT_SHA256,
        "heldout_denominator": "65",
        "runnable_targets": "64",
        "benchmark_truth_used_for_learning": "false",
        "post_holdout_ranking_tuning": "false",
    }
    manifest_ok = all(manifest.get(k) == v for k, v in expected_manifest.items())

    expected_table = {
        "doranet": {"partial_recovery_targets": "0", "exact_top10": "0", "exact_top50": "0"},
        "retrobiocat2": {"partial_recovery_targets": "13", "exact_top10": "0", "exact_top50": "0"},
        "retropath_standalone": {"partial_recovery_targets": "9", "exact_top10": "0", "exact_top50": "2"},
        "ensemble": {"partial_recovery_targets": "19", "exact_top10": "0", "exact_top50": "2"},
    }
    metrics_ok = True
    for arm, expected in expected_table.items():
        if arm not in table:
            metrics_ok = False
            break
        for k, v in expected.items():
            if table[arm].get(k) != v:
                metrics_ok = False
                break

    supplied = dict(artifact_paths or {})
    def byte_verified(key: str, expected: str) -> bool:
        path = supplied.get(key)
        return bool(path and Path(path).is_file() and sha256_file(path) == expected)

    sealed_bytes = byte_verified("sealed_predictions", FROZEN_HASHES["sealed_predictions"])
    scored_bytes = byte_verified("scored_benchmark", FROZEN_HASHES["scored_benchmark"])
    error_bytes = byte_verified("error_analysis", FROZEN_HASHES["error_analysis"])

    return Release23Verification(
        release_zip_sha256=release_digest,
        release_zip_verified=release_ok,
        manifest_verified=manifest_ok,
        aggregate_metrics_verified=metrics_ok,
        sealed_predictions_manifest_confirmed=(
            manifest.get("sealed_predictions_sha256") == FROZEN_HASHES["sealed_predictions"]
        ),
        scored_benchmark_manifest_confirmed=(
            manifest.get("scored_galaxy_benchmark_sha256") == FROZEN_HASHES["scored_benchmark"]
        ),
        error_analysis_manifest_confirmed=(
            manifest.get("error_analysis_sha256") == FROZEN_HASHES["error_analysis"]
        ),
        sealed_predictions_bytes_verified=sealed_bytes,
        scored_benchmark_bytes_verified=scored_bytes,
        error_analysis_bytes_verified=error_bytes,
        original_artifacts_present=all(
            supplied.get(k) and Path(supplied[k]).is_file()
            for k in ("sealed_predictions", "scored_benchmark", "error_analysis")
        ),
    )
