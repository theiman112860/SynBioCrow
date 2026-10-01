"""SynBioCrow 2.4 benchmark-construction contracts.

This module constructs split metadata and sealed truth manifests for a new
2.4 benchmark.  It deliberately keeps untouched-evaluation truth out of the
working benchmark manifest.

Design rules:
- no records from the frozen 2.3 holdout may enter development/validation;
- family-level grouping prevents close pathway families from crossing splits;
- split assignment is deterministic and versioned;
- untouched-evaluation truth is referenced only by external digest;
- duplicate targets and family leakage fail closed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .manifests import BenchmarkSplit


FROZEN_23_BENCHMARK_ID = "synbiocrow-2.3-galaxy-heldout"
DEFAULT_SPLIT_SALT = "SynBioCrow-2.4-benchmark-v1"


@dataclass(frozen=True)
class Benchmark24Record:
    record_id: str
    target_id: str
    target_name: str
    normalized_target: str
    family_id: str
    source_ids: Tuple[str, ...]
    chemistry_class: Optional[str] = None
    mapping_quality: Optional[str] = None
    route_length: Optional[int] = None
    evidence_density: Optional[str] = None
    historical_23_member: bool = False

    def public_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AssignedBenchmark24Record:
    record: Benchmark24Record
    split: BenchmarkSplit

    @property
    def tunable(self) -> bool:
        return self.split in (BenchmarkSplit.DEVELOPMENT, BenchmarkSplit.VALIDATION)


@dataclass
class Benchmark24Plan:
    benchmark_id: str
    version: str
    split_salt: str
    assignments: List[AssignedBenchmark24Record] = field(default_factory=list)
    evaluation_truth_external: bool = True
    evaluation_truth_sha256: Optional[str] = None
    source_snapshot_sha256: Optional[str] = None

    def validate(self) -> None:
        ids = [x.record.record_id for x in self.assignments]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate record_id")

        targets: Dict[str, BenchmarkSplit] = {}
        families: Dict[str, BenchmarkSplit] = {}
        for x in self.assignments:
            r = x.record
            if r.target_id in targets and targets[r.target_id] != x.split:
                raise ValueError(f"target leakage across splits: {r.target_id}")
            targets[r.target_id] = x.split

            if r.family_id in families and families[r.family_id] != x.split:
                raise ValueError(f"family leakage across splits: {r.family_id}")
            families[r.family_id] = x.split

            if r.historical_23_member and x.tunable:
                raise ValueError(
                    f"frozen 2.3 record cannot enter tunable 2.4 split: {r.record_id}"
                )

        if any(x.split == BenchmarkSplit.EVALUATION for x in self.assignments):
            if not self.evaluation_truth_external:
                raise ValueError("evaluation truth must remain external")
            if self.evaluation_truth_sha256 is not None:
                _validate_sha256(self.evaluation_truth_sha256)

        if self.source_snapshot_sha256 is not None:
            _validate_sha256(self.source_snapshot_sha256)

    def public_manifest(self) -> dict:
        self.validate()
        return {
            "benchmark_id": self.benchmark_id,
            "version": self.version,
            "split_salt": self.split_salt,
            "evaluation_truth_external": self.evaluation_truth_external,
            "evaluation_truth_sha256": self.evaluation_truth_sha256,
            "source_snapshot_sha256": self.source_snapshot_sha256,
            "assignments": [
                {"split": x.split.value, **x.record.public_dict()}
                for x in self.assignments
            ],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.public_manifest(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _validate_sha256(value: str) -> None:
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise ValueError("not a SHA-256 digest")


def deterministic_family_split(
    family_id: str,
    *,
    salt: str = DEFAULT_SPLIT_SALT,
    development_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> BenchmarkSplit:
    """Assign a family deterministically without consulting pathway truth."""
    if development_fraction <= 0 or validation_fraction < 0:
        raise ValueError("invalid split fractions")
    if development_fraction + validation_fraction >= 1:
        raise ValueError("evaluation fraction must be positive")

    h = hashlib.sha256(f"{salt}\n{family_id}".encode("utf-8")).digest()
    u = int.from_bytes(h[:8], "big") / float(2**64)
    if u < development_fraction:
        return BenchmarkSplit.DEVELOPMENT
    if u < development_fraction + validation_fraction:
        return BenchmarkSplit.VALIDATION
    return BenchmarkSplit.EVALUATION


def build_plan(
    records: Sequence[Benchmark24Record],
    *,
    benchmark_id: str = "synbiocrow-2.4-ranking-benchmark",
    version: str = "2.4.0",
    salt: str = DEFAULT_SPLIT_SALT,
    development_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    evaluation_truth_sha256: Optional[str] = None,
    source_snapshot_sha256: Optional[str] = None,
) -> Benchmark24Plan:
    family_split: Dict[str, BenchmarkSplit] = {}
    assignments: List[AssignedBenchmark24Record] = []
    for r in records:
        split = family_split.setdefault(
            r.family_id,
            deterministic_family_split(
                r.family_id,
                salt=salt,
                development_fraction=development_fraction,
                validation_fraction=validation_fraction,
            ),
        )
        assignments.append(AssignedBenchmark24Record(r, split))

    plan = Benchmark24Plan(
        benchmark_id=benchmark_id,
        version=version,
        split_salt=salt,
        assignments=assignments,
        evaluation_truth_external=True,
        evaluation_truth_sha256=evaluation_truth_sha256,
        source_snapshot_sha256=source_snapshot_sha256,
    )
    plan.validate()
    return plan


def records_from_jsonl(path: str) -> List[Benchmark24Record]:
    rows: List[Benchmark24Record] = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        required = (
            "record_id", "target_id", "target_name", "normalized_target",
            "family_id", "source_ids",
        )
        missing = [k for k in required if k not in obj]
        if missing:
            raise ValueError(f"line {lineno}: missing fields {missing}")
        rows.append(
            Benchmark24Record(
                record_id=str(obj["record_id"]),
                target_id=str(obj["target_id"]),
                target_name=str(obj["target_name"]),
                normalized_target=str(obj["normalized_target"]),
                family_id=str(obj["family_id"]),
                source_ids=tuple(str(x) for x in obj["source_ids"]),
                chemistry_class=obj.get("chemistry_class"),
                mapping_quality=obj.get("mapping_quality"),
                route_length=(
                    int(obj["route_length"]) if obj.get("route_length") is not None else None
                ),
                evidence_density=obj.get("evidence_density"),
                historical_23_member=bool(obj.get("historical_23_member", False)),
            )
        )
    return rows


def write_public_manifest(plan: Benchmark24Plan, path: str) -> str:
    Path(path).write_text(
        json.dumps(plan.public_manifest(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
