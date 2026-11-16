#!/usr/bin/env python3
"""Report graph pathway evidence from existing SynBioCrow normalized archive."""
import argparse
import json
from pathlib import Path
from synbiocrow_core.legacy_adapter import report_from_legacy_archive


def main():
    p = argparse.ArgumentParser()
    p.add_argument("archive", type=Path)
    p.add_argument("--target", required=True, help="Target SMILES, exact graph identifier")
    p.add_argument("--seed", action="append", default=[], help="Explicit starting SMILES; repeat for each")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    report = report_from_legacy_archive(args.archive, args.seed, args.target)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
