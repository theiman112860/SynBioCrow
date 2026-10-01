#!/usr/bin/env python3
"""Verify SynBioCrow 2.3 release-support metadata and optional frozen artifacts."""
import argparse
import json
from dataclasses import asdict

from synbiocrow.v24.release23_verify import verify_release_support_zip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release_support_zip")
    ap.add_argument("--sealed-predictions")
    ap.add_argument("--scored-benchmark")
    ap.add_argument("--error-analysis")
    ap.add_argument("--out", default="synbiocrow_2_4_5_release23_verification.json")
    args = ap.parse_args()

    supplied = {
        "sealed_predictions": args.sealed_predictions,
        "scored_benchmark": args.scored_benchmark,
        "error_analysis": args.error_analysis,
    }
    supplied = {k: v for k, v in supplied.items() if v}

    result = verify_release_support_zip(args.release_support_zip, supplied)
    payload = asdict(result)
    payload["complete_byte_verification"] = result.complete_byte_verification
    payload["historical_only"] = True
    payload["tuning_permitted"] = False

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
