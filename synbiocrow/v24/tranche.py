"""Provisional source-tranche handling for SynBioCrow 2.4.8.

A tranche record may be chemically and bibliographically reviewed while its
membership in the frozen 2.3 holdout remains unresolved. Such a record MUST NOT
be promoted into development/validation until the exclusion review is VERIFIED.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


class HistoricalExclusionStatus(str, Enum):
    PENDING = "pending"
    VERIFIED_EXCLUDED = "verified_excluded"
    BLOCKED_HISTORICAL_23 = "blocked_historical_23"


@dataclass(frozen=True)
class TrancheRecord:
    record_id: str
    target_name: str
    normalized_target: str
    family_key: str
    source_ids: Tuple[str, ...]
    primary_doi: str
    pubchem_cid: Optional[str]
    publication_year: int
    chemistry_class: str
    mapping_quality: str
    historical_exclusion_status: HistoricalExclusionStatus
    exclusion_basis: str
    notes: Optional[str] = None

    def validate(self) -> None:
        if not self.record_id or not self.target_name or not self.normalized_target:
            raise ValueError("record identity and normalized target are required")
        if not self.primary_doi:
            raise ValueError("primary DOI is required")
        if self.mapping_quality not in {"reviewed", "needs-review"}:
            raise ValueError("unsupported mapping_quality")
        if self.historical_exclusion_status == HistoricalExclusionStatus.VERIFIED_EXCLUDED:
            if not self.exclusion_basis.strip():
                raise ValueError("verified exclusion requires an explicit basis")

    @property
    def promotable(self) -> bool:
        return (
            self.mapping_quality == "reviewed"
            and self.historical_exclusion_status == HistoricalExclusionStatus.VERIFIED_EXCLUDED
        )


@dataclass
class SourceTranche:
    tranche_id: str
    version: str
    records: List[TrancheRecord]

    def validate(self) -> None:
        seen_ids = set()
        seen_targets = {}
        for r in self.records:
            r.validate()
            if r.record_id in seen_ids:
                raise ValueError(f"duplicate record_id: {r.record_id}")
            seen_ids.add(r.record_id)
            if r.normalized_target in seen_targets:
                raise ValueError(
                    f"duplicate normalized target: {r.target_name} and "
                    f"{seen_targets[r.normalized_target]}"
                )
            seen_targets[r.normalized_target] = r.target_name

    def promotable_records(self) -> List[TrancheRecord]:
        self.validate()
        return [r for r in self.records if r.promotable]

    def pending_records(self) -> List[TrancheRecord]:
        self.validate()
        return [
            r for r in self.records
            if r.historical_exclusion_status == HistoricalExclusionStatus.PENDING
        ]

    def canonical_json(self) -> str:
        self.validate()
        payload = {
            "tranche_id": self.tranche_id,
            "version": self.version,
            "records": [
                {
                    **asdict(r),
                    "historical_exclusion_status": r.historical_exclusion_status.value,
                }
                for r in sorted(self.records, key=lambda x: x.record_id)
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def load_tranche(path: str) -> SourceTranche:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    records = []
    for x in obj["records"]:
        records.append(
            TrancheRecord(
                record_id=x["record_id"],
                target_name=x["target_name"],
                normalized_target=x["normalized_target"],
                family_key=x["family_key"],
                source_ids=tuple(x["source_ids"]),
                primary_doi=x["primary_doi"],
                pubchem_cid=x.get("pubchem_cid"),
                publication_year=int(x["publication_year"]),
                chemistry_class=x["chemistry_class"],
                mapping_quality=x["mapping_quality"],
                historical_exclusion_status=HistoricalExclusionStatus(
                    x["historical_exclusion_status"]
                ),
                exclusion_basis=x.get("exclusion_basis", ""),
                notes=x.get("notes"),
            )
        )
    out = SourceTranche(
        tranche_id=obj["tranche_id"],
        version=obj["version"],
        records=records,
    )
    out.validate()
    return out
