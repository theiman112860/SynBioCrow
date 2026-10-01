"""Leakage-resistant benchmark and sealed-prediction manifests."""
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BenchmarkSplit(str, Enum):
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    EVALUATION = "evaluation"
    HISTORICAL_23 = "historical_2_3"


@dataclass(frozen=True)
class BenchmarkRecord:
    record_id: str
    target_id: str
    split: BenchmarkSplit
    source_ids: Tuple[str, ...]
    truth_sha256: Optional[str] = None
    family_id: Optional[str] = None
    mapping_quality: Optional[str] = None

    @property
    def tunable(self) -> bool:
        return self.split in (BenchmarkSplit.DEVELOPMENT, BenchmarkSplit.VALIDATION)


@dataclass
class BenchmarkManifest:
    benchmark_id: str
    version: str
    records: List[BenchmarkRecord] = field(default_factory=list)
    truth_locked: bool = True
    historical_23_tuning_forbidden: bool = True

    def validate(self) -> None:
        ids = [r.record_id for r in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate benchmark record_id")
        targets_by_split: Dict[str, set] = {}
        for r in self.records:
            targets_by_split.setdefault(r.split.value, set()).add(r.target_id)
            if r.split == BenchmarkSplit.HISTORICAL_23 and r.tunable:
                raise AssertionError("2.3 historical records can never be tunable")
        eval_targets = targets_by_split.get(BenchmarkSplit.EVALUATION.value, set())
        tune_targets = (
            targets_by_split.get(BenchmarkSplit.DEVELOPMENT.value, set())
            | targets_by_split.get(BenchmarkSplit.VALIDATION.value, set())
        )
        overlap = eval_targets & tune_targets
        if overlap:
            raise ValueError(f"evaluation target leakage: {sorted(overlap)}")

    def canonical_json(self) -> str:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SealedPredictionManifest:
    experiment_id: str
    software_commit: str
    ranking_policy_id: str
    benchmark_manifest_sha256: str
    prediction_sha256: str
    dependency_sha256: Optional[str] = None
    random_seeds: Tuple[int, ...] = ()
    truth_accessed_before_seal: bool = False

    def validate(self) -> None:
        if self.truth_accessed_before_seal:
            raise ValueError("cannot seal predictions after evaluation truth access")
        for name in ("benchmark_manifest_sha256", "prediction_sha256"):
            value = getattr(self, name)
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
                raise ValueError(f"{name} is not a SHA-256 digest")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
