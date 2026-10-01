"""External truth-lock metadata for the SynBioCrow 2.4 untouched evaluation set.

This module never stores pathway truth. It stores only an external artifact
digest and optional escrow metadata so the working repository can prove that
truth was fixed before prediction generation without exposing it to ranking code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class TruthLock:
    benchmark_id: str
    evaluation_record_count: int
    truth_artifact_sha256: str
    created_before_prediction_seal: bool
    escrow_location: Optional[str] = None
    note: Optional[str] = None

    def validate(self) -> None:
        if self.evaluation_record_count <= 0:
            raise ValueError("evaluation_record_count must be positive")
        if len(self.truth_artifact_sha256) != 64:
            raise ValueError("truth_artifact_sha256 must be SHA-256")
        int(self.truth_artifact_sha256, 16)
        if not self.created_before_prediction_seal:
            raise ValueError("truth lock must predate prediction sealing")

    def canonical_json(self) -> str:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def write_truth_lock(lock: TruthLock, path: str) -> str:
    lock.validate()
    Path(path).write_text(
        json.dumps(asdict(lock), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
