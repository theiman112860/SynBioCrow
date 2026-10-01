#!/usr/bin/env python3
"""Build a deterministic, family-grouped SynBioCrow 2.4 benchmark plan."""
import argparse
import json

from synbiocrow.v24.benchmark24 import (
    build_plan,
    records_from_jsonl,
    write_public_manifest,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records_jsonl")
    ap.add_argument("--out", default="synbiocrow_2_4_benchmark_manifest.json")
    ap.add_argument("--benchmark-id", default="synbiocrow-2.4-ranking-benchmark")
    ap.add_argument("--version", default="2.4.0")
    ap.add_argument("--salt", default="SynBioCrow-2.4-benchmark-v1")
    ap.add_argument("--development-fraction", type=float, default=0.60)
    ap.add_argument("--validation-fraction", type=float, default=0.20)
    ap.add_argument("--evaluation-truth-sha256")
    ap.add_argument("--source-snapshot-sha256")
    args = ap.parse_args()

    records = records_from_jsonl(args.records_jsonl)
    plan = build_plan(
        records,
        benchmark_id=args.benchmark_id,
        version=args.version,
        salt=args.salt,
        development_fraction=args.development_fraction,
        validation_fraction=args.validation_fraction,
        evaluation_truth_sha256=args.evaluation_truth_sha256,
        source_snapshot_sha256=args.source_snapshot_sha256,
    )
    write_public_manifest(plan, args.out)

    counts = {}
    for a in plan.assignments:
        counts[a.split.value] = counts.get(a.split.value, 0) + 1

    print(json.dumps({
        "benchmark_manifest": args.out,
        "benchmark_manifest_sha256": plan.sha256(),
        "record_count": len(plan.assignments),
        "split_counts": counts,
        "evaluation_truth_external": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
