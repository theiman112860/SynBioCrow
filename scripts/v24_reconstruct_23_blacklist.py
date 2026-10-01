#!/usr/bin/env python3
"""Emit the exact frozen 2.3 Galaxy held-out pathway-ID blacklist."""
import argparse, json
from pathlib import Path
from synbiocrow.v24.historical23_blacklist import (
    reconstruct_split, heldout_id_sha256, validate_reconstruction,
)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="synbiocrow_2_3_galaxy_heldout_pathway_blacklist.json")
    args=ap.parse_args()
    validate_reconstruction()
    dev,held=reconstruct_split()
    payload={
      "source_pathway_count":77,
      "development_count":12,
      "heldout_count":65,
      "development_pathway_ids":dev,
      "heldout_pathway_ids":held,
      "heldout_pathway_id_set_sha256":heldout_id_sha256(),
      "target_identity_blacklist_complete":False,
      "note":"Pathway IDs are exact. Target name/structure mapping requires the normalized Galaxy Dataset 2 truth artifact."
    }
    Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
