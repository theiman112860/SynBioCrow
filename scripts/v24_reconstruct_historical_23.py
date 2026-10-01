#!/usr/bin/env python3
"""Reconstruct and verify persisted 2.3 ensemble routes without regeneration."""
import argparse, csv, json
from pathlib import Path

from synbiocrow.v24.benchmark23 import load_historical_23_routes
from synbiocrow.v24.manifests import sha256_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--out", default="synbiocrow_2_4_3_historical23_routes.csv")
    ap.add_argument("--manifest", default="synbiocrow_2_4_3_manifest.json")
    args = ap.parse_args()

    sets = load_historical_23_routes(args.bundle)
    rows = []
    for s in sets:
        for r in s.routes:
            f = r.features
            rows.append({
                "target_id": s.target_id,
                "target_name": s.target_name,
                "run_id": s.run_id,
                "route_id": r.route_id,
                "route_length": f.route_length,
                "engine_count": f.engine_count,
                "reaction_evidence_fraction": f.reaction_evidence_fraction,
                "reviewed_enzyme_fraction": f.reviewed_enzyme_fraction,
                "rhea_exact_fraction": f.rhea_exact_fraction,
                "thermo_coverage_fraction": f.thermo_coverage_fraction,
                "unsupported_edge_count": f.unsupported_edge_count,
            })

    fieldnames = [
        "target_id","target_name","run_id","route_id","route_length",
        "engine_count","reaction_evidence_fraction","reviewed_enzyme_fraction",
        "rhea_exact_fraction","thermo_coverage_fraction","unsupported_edge_count",
    ]
    with open(args.out, "w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    manifest = {
        "adapter": "SynBioCrow 2.4.3 historical-2.3 route reconstruction",
        "historical_only": True,
        "tuning_permitted": False,
        "generation_invoked": False,
        "truth_consumed": False,
        "input_sha256": sha256_file(args.bundle),
        "output_sha256": sha256_file(args.out),
        "target_count": len(sets),
        "route_count": len(rows),
        "candidate_count": sum(s.candidate_count for s in sets),
        "reconstructed_edge_count_sum": sum(s.edge_count for s in sets),
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
