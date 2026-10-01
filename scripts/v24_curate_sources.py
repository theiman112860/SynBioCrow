#!/usr/bin/env python3
"""Curate harvested pathway metadata into SynBioCrow 2.4 benchmark records."""
import argparse
import json
from pathlib import Path

from synbiocrow.v24.curation import (
    HarvestedPathwayRecord,
    curate_record,
    deduplicate_curated,
    to_benchmark_jsonl,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("harvest_jsonl")
    ap.add_argument("--out", default="synbiocrow_2_4_curated_records.jsonl")
    ap.add_argument("--audit", default="synbiocrow_2_4_curation_audit.json")
    ap.add_argument("--frozen23-targets", help="JSON array of normalized target strings to blacklist")
    args = ap.parse_args()

    frozen = []
    if args.frozen23_targets:
        frozen = json.loads(Path(args.frozen23_targets).read_text(encoding="utf-8"))

    curated = []
    for lineno, line in enumerate(Path(args.harvest_jsonl).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        family_key = obj.pop("family_key", None)
        if not family_key:
            raise ValueError(f"line {lineno}: family_key is required")
        raw = HarvestedPathwayRecord(
            source_record_id=str(obj["source_record_id"]),
            target_name=str(obj["target_name"]),
            target_structure=str(obj["target_structure"]),
            source_ids=tuple(str(x) for x in obj.get("source_ids", [])),
            source_type=str(obj["source_type"]),
            literature_ids=tuple(str(x) for x in obj.get("literature_ids", [])),
            pathway_label=obj.get("pathway_label"),
            chemistry_class=obj.get("chemistry_class"),
            mapping_quality=obj.get("mapping_quality", "unreviewed"),
            notes=obj.get("notes"),
        )
        curated.append(
            curate_record(
                raw,
                family_key=family_key,
                frozen23_normalized_targets=frozen,
            )
        )

    deduped, audit = deduplicate_curated(curated)
    Path(args.out).write_text(to_benchmark_jsonl(deduped), encoding="utf-8")
    Path(args.audit).write_text(
        json.dumps({
            "input_record_count": len(curated),
            "curated_record_count": len(deduped),
            "duplicate_merge_count": len(audit),
            "historical_23_blacklist_hits": sum(r.historical_23_member for r in deduped),
            "records_needing_mapping_review": sum(r.mapping_quality != "reviewed" for r in deduped),
            "audit": audit,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"curated={len(deduped)} duplicates_merged={len(audit)}")


if __name__ == "__main__":
    main()
