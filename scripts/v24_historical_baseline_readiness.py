#!/usr/bin/env python3
"""Assess what can and cannot be reproduced from a frozen 2.3 breadth bundle."""
import argparse
import csv
import json
from pathlib import Path

from synbiocrow.v24.benchmark23 import load_historical_23_routes
from synbiocrow.v24.historical_baseline import (
    assess_route_set,
    policy_order_diagnostics,
    summarize_readiness,
)
from synbiocrow.v24.manifests import sha256_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--status", default="synbiocrow_2_4_4_readiness.json")
    ap.add_argument("--orders", default="synbiocrow_2_4_4_policy_orders.csv")
    args = ap.parse_args()

    route_sets = load_historical_23_routes(args.bundle)
    statuses = [assess_route_set(x) for x in route_sets]
    rows = []
    for x in route_sets:
        rows.extend(policy_order_diagnostics(x))

    if rows:
        with open(args.orders, "w", newline="", encoding="utf-8") as h:
            w = csv.DictWriter(h, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    else:
        Path(args.orders).write_text("", encoding="utf-8")

    payload = {
        "checkpoint": "SynBioCrow 2.4.4 historical baseline readiness",
        "bundle_sha256": sha256_file(args.bundle),
        "historical_only": True,
        "tuning_permitted": False,
        "truth_consumed": False,
        "generation_invoked": False,
        "summary": summarize_readiness(route_sets),
        "targets": [s.__dict__ for s in statuses],
        "policy_order_csv": args.orders,
        "policy_order_csv_sha256": sha256_file(args.orders),
    }
    Path(args.status).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
