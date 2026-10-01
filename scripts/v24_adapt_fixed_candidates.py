#!/usr/bin/env python3
"""Convert existing candidate routes into SynBioCrow 2.4 ranking features."""
import argparse, json
from dataclasses import asdict
from pathlib import Path
from synbiocrow.v24.adapters import load_fixed_candidates
from synbiocrow.v24.feature_matrix import write_feature_csv
from synbiocrow.v24.manifests import sha256_file

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input",help="Existing JSON, JSONL, or CSV candidate-route artifact")
    ap.add_argument("--out",default="synbiocrow_2_4_1_features.csv")
    ap.add_argument("--manifest",default="synbiocrow_2_4_1_adapter_manifest.json")
    args=ap.parse_args()
    routes=load_fixed_candidates(args.input)
    write_feature_csv(routes,args.out)
    manifest={
      "adapter":"SynBioCrow 2.4.1 fixed-candidate evidence adapter",
      "generation_invoked":False,
      "input":str(Path(args.input)),
      "input_sha256":sha256_file(args.input),
      "output":str(Path(args.out)),
      "output_sha256":sha256_file(args.out),
      "route_count":len(routes),
      "reaction_count":sum(len(r.reactions) for r in routes),
    }
    Path(args.manifest).write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2,sort_keys=True))
if __name__=="__main__": main()
