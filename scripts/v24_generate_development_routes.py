#!/usr/bin/env python3
"""SynBioCrow 2.4.13 development-only route generation."""
import argparse, hashlib, json
from dataclasses import asdict
from pathlib import Path
from synbiocrow import DesignRequest, SynBioCrowEngine, design
from synbiocrow.execution import json_safe

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tranche",required=True)
    ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--state-dir",required=True)
    ap.add_argument("--max-route-steps",type=int,default=8)
    ap.add_argument("--max-routes",type=int,default=100)
    args=ap.parse_args()

    tranche=json.loads(Path(args.tranche).read_text())
    manifest=json.loads(Path(args.split_manifest).read_text())
    records={r["record_id"]:r for r in tranche["records"]}
    dev=[x for x in manifest["records"] if x["split"]=="development"]
    sealed=[x["record_id"] for x in manifest["records"] if x["split"]!="development"]
    if len(dev)!=4:
        raise ValueError(f"expected frozen four-target development set, found {len(dev)}")

    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    engine=SynBioCrowEngine()
    readiness=engine.backend_readiness()
    available=tuple(k for k,v in readiness.items() if v.get("available"))
    (out/"backend_readiness.json").write_text(json.dumps(readiness,indent=2,sort_keys=True)+"\n")
    if not available:
        raise RuntimeError("no SynBioCrow generator backend reports available")

    results=[]
    for i,item in enumerate(dev,1):
        rid=item["record_id"]
        if rid in sealed:
            raise RuntimeError(f"firewall violation: {rid}")
        rec=records[rid]
        print(f"[2.4.13] target {i}/4 | {rid} | {rec['target_name']}",flush=True)
        req=DesignRequest(
            target_smiles=rec["normalized_target"],
            mode="biosynthesis",
            backend_ids=available,
            sink_smiles=(),
            max_route_steps=args.max_route_steps,
            max_routes=args.max_routes,
        )
        try:
            res=design(req,engine=engine,state_root=args.state_dir,resume=True)
            payload=json_safe(res)
            status="complete"
            err=None
        except Exception as exc:
            payload=None
            status="error"
            err=f"{type(exc).__name__}: {exc}"
        row={
            "record_id":rid,"target_name":rec["target_name"],
            "target_smiles":rec["normalized_target"],"split":"development",
            "status":status,"error":err,"result":payload,
        }
        (out/f"{rid}.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
        results.append({
            "record_id":rid,"target_name":rec["target_name"],"status":status,
            "error":err,
            "candidate_count":len(payload.get("candidates",[])) if payload else 0,
            "route_count":len(payload.get("routes",[])) if payload else 0,
        })

    summary={
        "schema":"synbiocrow.v24.development-generation.v1",
        "version":"2.4.13",
        "split_manifest_sha256":manifest.get("manifest_sha256"),
        "tranche_sha256":sha256_file(args.tranche),
        "available_backends":list(available),
        "sealed_validation_record_ids":sealed,
        "targets":results,
        "validation_truth_accessed":False,
        "tuning_performed":False,
    }
    (out/"generation_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
