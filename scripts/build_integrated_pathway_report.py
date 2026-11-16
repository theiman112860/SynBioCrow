#!/usr/bin/env python3
"""Produce one report from a normalized historical archive and optional curated evidence."""
import argparse
import json
from pathlib import Path
from synbiocrow_core.legacy_adapter import report_from_legacy_archive
from synbiocrow_core.integrated_report import build_integrated_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--target", required=True)
    parser.add_argument("--seed", action="append", default=[])
    parser.add_argument("--evidence", type=Path, help="Optional JSON keyed by reaction ID")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8")) if args.evidence else {}
    graph = report_from_legacy_archive(args.archive, args.seed, args.target)
    report = build_integrated_report(graph, evidence)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
