"""Curation helpers for new SynBioCrow 2.4 benchmark records.

No external database is queried here. These functions operate on harvested
metadata and enforce deterministic normalization, deduplication, blacklist
checking, and family grouping.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import hashlib
import json
import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class HarvestedPathwayRecord:
    source_record_id: str
    target_name: str
    target_structure: str
    source_ids: Tuple[str, ...]
    source_type: str
    literature_ids: Tuple[str, ...] = ()
    pathway_label: Optional[str] = None
    chemistry_class: Optional[str] = None
    mapping_quality: str = "unreviewed"
    notes: Optional[str] = None


@dataclass(frozen=True)
class CuratedPathwayRecord:
    record_id: str
    target_id: str
    target_name: str
    normalized_target: str
    family_id: str
    source_ids: Tuple[str, ...]
    literature_ids: Tuple[str, ...]
    chemistry_class: Optional[str]
    mapping_quality: str
    historical_23_member: bool = False
    curation_flags: Tuple[str, ...] = ()


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def normalize_structure_text(value: str) -> str:
    """Text-level normalization only.

    Chemical canonicalization belongs in the chemistry layer (e.g. RDKit).
    This function intentionally does not pretend that raw text normalization
    yields canonical chemical identity.
    """
    return re.sub(r"\s+", "", value.strip())


def stable_target_id(normalized_target: str) -> str:
    return "target:" + hashlib.sha256(normalized_target.encode("utf-8")).hexdigest()[:20]


def stable_record_id(source_record_id: str, normalized_target: str) -> str:
    payload = source_record_id.strip() + "\n" + normalized_target
    return "rec:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def family_id_from_key(family_key: str) -> str:
    key = family_key.strip().casefold()
    return "family:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def curate_record(
    raw: HarvestedPathwayRecord,
    *,
    family_key: str,
    frozen23_target_ids: Sequence[str] = (),
    frozen23_normalized_targets: Sequence[str] = (),
) -> CuratedPathwayRecord:
    normalized_target = normalize_structure_text(raw.target_structure)
    target_id = stable_target_id(normalized_target)
    historical = (
        target_id in set(frozen23_target_ids)
        or normalized_target in set(frozen23_normalized_targets)
    )
    flags = []
    if raw.mapping_quality == "unreviewed":
        flags.append("mapping-unreviewed")
    if not raw.literature_ids:
        flags.append("no-literature-id")
    if not raw.chemistry_class:
        flags.append("chemistry-class-missing")
    if historical:
        flags.append("frozen-2.3-member")
    return CuratedPathwayRecord(
        record_id=stable_record_id(raw.source_record_id, normalized_target),
        target_id=target_id,
        target_name=raw.target_name.strip(),
        normalized_target=normalized_target,
        family_id=family_id_from_key(family_key),
        source_ids=tuple(sorted(set(raw.source_ids))),
        literature_ids=tuple(sorted(set(raw.literature_ids))),
        chemistry_class=raw.chemistry_class,
        mapping_quality=raw.mapping_quality,
        historical_23_member=historical,
        curation_flags=tuple(sorted(set(flags))),
    )


def deduplicate_curated(records: Sequence[CuratedPathwayRecord]) -> Tuple[List[CuratedPathwayRecord], List[dict]]:
    """Deduplicate by normalized target identity.

    Multiple sources for the same target collapse into one record only when
    family assignment agrees. Conflicting family assignments fail closed.
    """
    by_target: Dict[str, CuratedPathwayRecord] = {}
    audit: List[dict] = []
    for r in records:
        old = by_target.get(r.target_id)
        if old is None:
            by_target[r.target_id] = r
            continue
        if old.normalized_target != r.normalized_target:
            raise ValueError("target-id collision")
        if old.family_id != r.family_id:
            raise ValueError(
                f"conflicting family assignment for {r.target_id}: "
                f"{old.family_id} vs {r.family_id}"
            )
        merged = CuratedPathwayRecord(
            record_id=min(old.record_id, r.record_id),
            target_id=r.target_id,
            target_name=old.target_name if len(old.target_name) <= len(r.target_name) else r.target_name,
            normalized_target=r.normalized_target,
            family_id=r.family_id,
            source_ids=tuple(sorted(set(old.source_ids + r.source_ids))),
            literature_ids=tuple(sorted(set(old.literature_ids + r.literature_ids))),
            chemistry_class=old.chemistry_class or r.chemistry_class,
            mapping_quality=(
                old.mapping_quality if old.mapping_quality == r.mapping_quality
                else "needs-review"
            ),
            historical_23_member=old.historical_23_member or r.historical_23_member,
            curation_flags=tuple(sorted(set(old.curation_flags + r.curation_flags + ("deduplicated",)))),
        )
        by_target[r.target_id] = merged
        audit.append({
            "target_id": r.target_id,
            "action": "merge-duplicate-target",
            "source_record_ids": [old.record_id, r.record_id],
        })
    return sorted(by_target.values(), key=lambda x: x.target_id), audit


def to_benchmark_jsonl(records: Sequence[CuratedPathwayRecord]) -> str:
    rows = []
    for r in records:
        rows.append(json.dumps({
            "record_id": r.record_id,
            "target_id": r.target_id,
            "target_name": r.target_name,
            "normalized_target": r.normalized_target,
            "family_id": r.family_id,
            "source_ids": list(r.source_ids),
            "chemistry_class": r.chemistry_class,
            "mapping_quality": r.mapping_quality,
            "route_length": None,
            "evidence_density": "unknown",
            "historical_23_member": r.historical_23_member,
        }, sort_keys=True))
    return "\n".join(rows) + ("\n" if rows else "")
