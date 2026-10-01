#!/usr/bin/env python3
"""Recover exact frozen 2.3 target identities and resolve the 2.4 source tranche."""
import argparse
import json
from pathlib import Path

from synbiocrow.v24.target_blacklist import (
    build_blacklist,
    records_from_dataset2_xlsx,
    records_from_normalized_json,
    resolve_tranche,
    sha256_file,
)


def main():
    ap=argparse.ArgumentParser()
    src=ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dataset2-xlsx")
    src.add_argument("--normalized-json")
    ap.add_argument("--tranche",required=True)
    ap.add_argument("--out-dir",default="synbiocrow_2_4_10_target_blacklist")
    args=ap.parse_args()

    if args.dataset2_xlsx:
        source=args.dataset2_xlsx
        records=records_from_dataset2_xlsx(source)
        repairs=list(getattr(records_from_dataset2_xlsx,"last_repairs",[]))
        kind="galaxy_synbiocad_supplementary_dataset_2_xlsx"
    else:
        source=args.normalized_json
        records=records_from_normalized_json(source)
        repairs=[]
        kind="synbiocrow_2_3_normalized_galaxy_json"

    out=Path(args.out_dir)
    out.mkdir(parents=True,exist_ok=True)
    blacklist=build_blacklist(records,source_kind=kind,source_sha256=sha256_file(source))
    resolution=resolve_tranche(args.tranche,blacklist)

    blacklist_path=out/"frozen23_heldout_target_blacklist.json"
    blacklist_path.write_text(json.dumps({
        "schema":"synbiocrow.v24.frozen23_target_blacklist.v1",
        "source_kind":blacklist.source_kind,
        "source_sha256":blacklist.source_sha256,
        "blacklist_sha256":blacklist.sha256(),
        "heldout_pathway_count":blacklist.heldout_pathway_count,
        "heldout_unique_target_count":blacklist.heldout_unique_target_count,
        "targets":[
            {
              "pathway_id":x.pathway_id,
              "target_name":x.target_name,
              "target_inchi":x.target_inchi,
              "target_smiles":x.target_smiles,
              "split":x.split,
            } for x in blacklist.heldout_targets
        ],
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")

    (out/"source_repairs.json").write_text(
        json.dumps({
            "repair_count":len(repairs),
            "repairs":repairs,
        },indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )

    (out/"tranche_resolution.json").write_text(
        json.dumps({k:v for k,v in resolution.items() if k!="updated_tranche"},indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )
    (out/"source_tranche_v1_resolved.json").write_text(
        json.dumps(resolution["updated_tranche"],indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )

    summary={
        "source_sha256":sha256_file(source),
        "blacklist_sha256":blacklist.sha256(),
        "heldout_pathway_count":blacklist.heldout_pathway_count,
        "heldout_unique_target_count":blacklist.heldout_unique_target_count,
        "verified_excluded_count":resolution["verified_excluded_count"],
        "blocked_historical_23_count":resolution["blocked_historical_23_count"],
        "pending_count":resolution["pending_count"],
        "split_freeze_ready":resolution["pending_count"]==0,
        "source_repair_count":len(repairs),
        "out_dir":str(out),
    }
    (out/"recovery_summary.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print(json.dumps(summary,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
