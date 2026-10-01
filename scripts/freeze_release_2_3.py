from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",required=True)
    ap.add_argument("--sealed-dir",required=True)
    ap.add_argument("--scored",required=True)
    ap.add_argument("--error-analysis",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    root=Path(args.repo_root); sealed=Path(args.sealed_dir); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    files={
        "sealed_predictions":sealed/"sealed_predictions.json",
        "sealed_manifest":sealed/"sealed_manifest.json",
        "benchmark_seal":sealed/"benchmark_seal.json",
        "scored_benchmark":Path(args.scored),
        "error_analysis":Path(args.error_analysis),
        "similarity_policy":root/"docs/SIMILARITY_POLICY_2_3.md",
        "manuscript":root/"paper/2.3/MANUSCRIPT_DRAFT.md",
    }
    missing=[str(p) for p in files.values() if not p.is_file()]
    if missing: raise FileNotFoundError("Missing freeze inputs: "+", ".join(missing))
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    payload={
        "schema":"synbiocrow.release_freeze_2_3.v1",
        "git_commit":head,
        "branch":"develop/2.3",
        "scientific_policy":{
            "benchmark_truth_used_for_learning":False,
            "heldout_denominator":65,
            "runnable_targets":64,
            "similarity_default":"2D-primary Morgan/Tanimoto",
            "ranking_tuning_after_holdout":False,
        },
        "artifacts":{k:{"path":str(p),"sha256":sha256(p)} for k,p in files.items()},
    }
    freeze=out/"SYNBIOCROW_2_3_FREEZE_MANIFEST.json"
    freeze.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
