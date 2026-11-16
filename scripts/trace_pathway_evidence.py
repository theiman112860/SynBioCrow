#!/usr/bin/env python3
"""Trace candidate routes from a normalized, explicit JSON input.

Input schema:
{"target":"T","seeds":["A"],"reactions":[{"reaction_id":"r1",
"reactants":["A"],"products":["T"],"engine":"...", "evidence_ref":"..."}]}
"""
import argparse
import json
from pathlib import Path
from synbiocrow_core.pathway_evidence import Reaction, trace_pathway


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    required = {"target", "seeds", "reactions"}
    if not required.issubset(raw):
        raise ValueError("missing required keys: " + ", ".join(sorted(required - set(raw))))
    reactions = [
        Reaction(
            reaction_id=item["reaction_id"],
            reactants=tuple(item["reactants"]),
            products=tuple(item["products"]),
            engine=item["engine"],
            evidence_ref=item["evidence_ref"],
        )
        for item in raw["reactions"]
    ]
    report = trace_pathway(reactions, raw["seeds"], raw["target"])
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
