from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from synbiocrow import DesignRequest, SynBioCrowEngine, design


PRIMARY_BACKENDS=("doranet","retrobiocat2","retropath_standalone","biopks_retrotide")


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(root:Path)->str:
    try:
        return subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    except Exception:
        return "UNKNOWN"


def load_panel(path:Path)->list[dict[str,Any]]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    rows=payload.get("targets") if isinstance(payload,dict) else payload
    if not isinstance(rows,list) or not rows:
        raise ValueError("Benchmark panel must contain a non-empty targets list")
    required=("target_id","target_name","target_smiles","chemical_class")
    seen=set()
    out=[]
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("Each target must be a JSON object")
        missing=[k for k in required if not row.get(k)]
        if missing:
            raise ValueError(f"Target missing required fields {missing}: {row}")
        if row["target_id"] in seen:
            raise ValueError(f"Duplicate target_id: {row['target_id']}")
        seen.add(row["target_id"])
        copy=dict(row)
        copy["sink_smiles"]=list(copy.get("sink_smiles") or [])
        applicable=copy.get("applicable_backends")
        if applicable is None:
            applicable=list(PRIMARY_BACKENDS)
        applicable=tuple(str(x) for x in applicable)
        unknown=[x for x in applicable if x not in PRIMARY_BACKENDS]
        if unknown:
            raise ValueError(f"Unknown applicable_backends {unknown} for {copy['target_id']}")
        copy["applicable_backends"]=list(applicable)
        out.append(copy)
    return out


def run_arm(
    target:dict[str,Any],
    backend_ids:tuple[str,...],
    *,
    engine:SynBioCrowEngine,
    state_root:Path,
    max_route_steps:int,
    max_routes:int,
)->dict[str,Any]:
    request=DesignRequest(
        target_smiles=target["target_smiles"],
        mode="biosynthesis",
        backend_ids=backend_ids,
        sink_smiles=tuple(target.get("sink_smiles") or ()),
        max_route_steps=max_route_steps,
        max_routes=max_routes,
    )
    t0=time.perf_counter()
    try:
        result=design(
            request,
            engine=engine,
            state_root=str(state_root),
            resume=False,
        )
        elapsed=time.perf_counter()-t0
        status="COMPLETE"
        if not result.candidates:
            # Distinguish scientific no-hit from unavailable/error arms using backend status.
            states=[x.get("status") for x in result.backend_status.values()]
            status="NO_HIT" if states and all(x=="COMPLETE" for x in states) else "INCOMPLETE"
        return {
            "status":status,
            "elapsed_seconds":elapsed,
            "candidate_count":len(result.candidates),
            "route_count":len(result.routes),
            "graph_summary":result.graph_summary,
            "backend_status":result.backend_status,
            "run_id":result.run_id,
        }
    except Exception as exc:
        return {
            "status":"ERROR",
            "elapsed_seconds":time.perf_counter()-t0,
            "candidate_count":0,
            "route_count":0,
            "graph_summary":{},
            "backend_status":{},
            "error_type":type(exc).__name__,
            "error":str(exc),
        }


def summarize(records:list[dict[str,Any]])->dict[str,Any]:
    arms=sorted({arm for r in records for arm in r["arms"]})
    summary={"target_count":len(records),"arms":{},"ensemble_only_route_targets":[]}
    for arm in arms:
        rows=[r["arms"][arm] for r in records if arm in r["arms"]]
        times=[float(x["elapsed_seconds"]) for x in rows if x.get("status")!="ERROR"]
        coverage=sum(1 for x in rows if x.get("candidate_count",0)>0)
        route_cov=sum(1 for x in rows if x.get("route_count",0)>0)
        summary["arms"][arm]={
            "targets":len(rows),
            "candidate_coverage_count":coverage,
            "candidate_coverage_fraction":coverage/max(1,len(rows)),
            "route_coverage_count":route_cov,
            "route_coverage_fraction":route_cov/max(1,len(rows)),
            "status_counts":{s:sum(1 for x in rows if x.get("status")==s) for s in sorted({x.get("status") for x in rows})},
            "runtime_median_seconds":statistics.median(times) if times else None,
            "runtime_min_seconds":min(times) if times else None,
            "runtime_max_seconds":max(times) if times else None,
        }
    for r in records:
        ensemble=r["arms"].get("ensemble",{})
        indiv=[r["arms"].get(b,{}) for b in PRIMARY_BACKENDS]
        if ensemble.get("route_count",0)>0 and all(x.get("route_count",0)==0 for x in indiv):
            summary["ensemble_only_route_targets"].append(r["target_id"])
    return summary


def write_csv(records:list[dict[str,Any]],path:Path)->None:
    rows=[]
    for rec in records:
        for arm,data in rec["arms"].items():
            rows.append({
                "target_id":rec["target_id"],
                "target_name":rec["target_name"],
                "chemical_class":rec["chemical_class"],
                "arm":arm,
                "status":data.get("status"),
                "elapsed_seconds":data.get("elapsed_seconds"),
                "candidate_count":data.get("candidate_count"),
                "route_count":data.get("route_count"),
                "compound_count":data.get("graph_summary",{}).get("compound_count"),
                "edge_count":data.get("graph_summary",{}).get("edge_count"),
                "composite_edge_count":data.get("graph_summary",{}).get("composite_edge_count"),
            })
    fields=list(rows[0]) if rows else []
    with path.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--max-route-steps",type=int,default=8)
    ap.add_argument("--max-routes",type=int,default=100)
    ap.add_argument("--no-resume",action="store_true",help="Ignore completed per-target JSON files")
    args=ap.parse_args()

    root=Path(__file__).resolve().parents[1]
    panel_path=Path(args.panel).resolve()
    out=Path(args.output_dir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    raw_dir=out/"targets"
    raw_dir.mkdir(exist_ok=True)
    state_root=out/"state"
    state_root.mkdir(exist_ok=True)

    targets=load_panel(panel_path)
    engine=SynBioCrowEngine()
    readiness=engine.backend_readiness()
    available_primary=tuple(
        b for b in PRIMARY_BACKENDS
        if b in engine.backend_ids() and readiness.get(b,{}).get("available",False)
    )

    records=[]
    for i,target in enumerate(targets,1):
        target_path=raw_dir/f"{target['target_id']}.json"
        if target_path.is_file() and not args.no_resume:
            try:
                rec=json.loads(target_path.read_text(encoding="utf-8"))
                records.append(rec)
                print(f"[BENCHMARK] {i}/{len(targets)} {target['target_id']} RESUME cached",flush=True)
                continue
            except Exception as exc:
                print(f"[BENCHMARK] cache invalid for {target['target_id']}: {exc}; rerunning",flush=True)
        print(f"[BENCHMARK] {i}/{len(targets)} {target['target_id']} {target['target_name']}",flush=True)
        arms={}
        applicable=set(target.get("applicable_backends") or PRIMARY_BACKENDS)
        for bid in PRIMARY_BACKENDS:
            if bid not in applicable:
                arms[bid]={
                    "status":"NOT_APPLICABLE",
                    "elapsed_seconds":0.0,
                    "candidate_count":0,
                    "route_count":0,
                }
                continue
            if bid not in engine.backend_ids():
                arms[bid]={"status":"UNKNOWN_BACKEND","elapsed_seconds":0.0,"candidate_count":0,"route_count":0}
                continue
            if not readiness.get(bid,{}).get("available",False):
                arms[bid]={
                    "status":"SKIPPED_UNAVAILABLE",
                    "elapsed_seconds":0.0,
                    "candidate_count":0,
                    "route_count":0,
                    "readiness":readiness.get(bid,{})
                }
                continue
            arms[bid]=run_arm(
                target,(bid,),engine=engine,state_root=state_root,
                max_route_steps=args.max_route_steps,max_routes=args.max_routes,
            )
        ensemble_backends=tuple(b for b in available_primary if b in applicable)
        arms["ensemble"]=run_arm(
            target,ensemble_backends,engine=engine,state_root=state_root,
            max_route_steps=args.max_route_steps,max_routes=args.max_routes,
        ) if ensemble_backends else {
            "status":"SKIPPED_UNAVAILABLE","elapsed_seconds":0.0,
            "candidate_count":0,"route_count":0,
        }
        rec={
            "target_id":target["target_id"],
            "target_name":target["target_name"],
            "target_smiles":target["target_smiles"],
            "chemical_class":target["chemical_class"],
            "sink_smiles":target.get("sink_smiles",[]),
            "blind_group":target.get("blind_group"),
            "notes":target.get("notes"),
            "applicable_backends":target.get("applicable_backends"),
            "arms":arms,
        }
        records.append(rec)
        target_path.write_text(
            json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8"
        )

    aggregate=summarize(records)
    aggregate_path=out/"benchmark_summary.json"
    aggregate_path.write_text(json.dumps(aggregate,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(records,out/"benchmark_long.csv")

    manifest={
        "schema":"synbiocrow.benchmark.v2_3.v1",
        "git_commit":git_head(root),
        "panel_path":str(panel_path),
        "panel_sha256":sha256(panel_path),
        "target_count":len(targets),
        "primary_backends":list(PRIMARY_BACKENDS),
        "available_primary_backends":list(available_primary),
        "backend_readiness":readiness,
        "max_route_steps":args.max_route_steps,
        "max_routes":args.max_routes,
        "truth_accessed":False,
        "resume_enabled":not args.no_resume,
        "aggregate_sha256":sha256(aggregate_path),
    }
    manifest_path=out/"benchmark_manifest.json"
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps(aggregate,indent=2,sort_keys=True),flush=True)
    print(f"[BENCHMARK] manifest={manifest_path}")
    print(f"[BENCHMARK] summary={aggregate_path}")
    print("[BENCHMARK] truth_accessed=False")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
