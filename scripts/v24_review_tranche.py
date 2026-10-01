#!/usr/bin/env python3
"""Report promotion readiness for a SynBioCrow 2.4 source tranche."""
import argparse
import json
from dataclasses import asdict

from synbiocrow.v24.tranche import load_tranche


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tranche_json")
    ap.add_argument("--out", default="synbiocrow_2_4_8_tranche_review.json")
    args = ap.parse_args()

    t = load_tranche(args.tranche_json)
    promotable = t.promotable_records()
    pending = t.pending_records()
    blocked = [
        r for r in t.records
        if r.historical_exclusion_status.value == "blocked_historical_23"
    ]

    payload = {
        "tranche_id": t.tranche_id,
        "tranche_sha256": t.sha256(),
        "record_count": len(t.records),
        "promotable_count": len(promotable),
        "pending_historical_crosscheck_count": len(pending),
        "blocked_historical_23_count": len(blocked),
        "ready_for_split_freeze": len(pending) == 0 and len(blocked) == 0 and len(promotable) > 0,
        "promotable_record_ids": [r.record_id for r in promotable],
        "pending_record_ids": [r.record_id for r in pending],
        "blocked_record_ids": [r.record_id for r in blocked],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
