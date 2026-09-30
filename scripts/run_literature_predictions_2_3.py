from __future__ import annotations

import argparse, hashlib, json, subprocess, time
from dataclasses import asdict
from pathlib import Path

from synbiocrow import SynBioCrowEngine
from synbiocrow.ensemble import resolve_compound

BACKENDS=("doranet","retrobiocat2","retropath_standalone")

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

def candidate_route(candidate):
    return {
        "candidate_id":candidate.candidate_id,
        "source_backends":list(candidate.source_backends),
        "reactions":[s.reaction for s in candidate.steps],
        "rules":[s.rule_id for s in candidate.steps],
        "provenance":dict(candidate.provenance or {}),
    }

def ensemble_routes(engine,candidates,target_smiles,sinks,max_steps,max_routes):
    graph=engine.build_ensemble(candidates)
    target_key=resolve_compound(target_smiles,source="request").key
    sink_keys={resolve_compound(x,source="request").key for x in sinks}
    edge_routes=graph.find_routes(target_key,sink_keys,max_steps=max_steps,max_routes=max_routes) if sinks else []
    routes=[]
    for rank,eids in enumerate(edge_routes,1):
        routes.append({
            "rank":rank,
            "edge_ids":eids,
            "reactions":[graph.edges[eid].reaction for eid in eids],
            "source_backends":[list(graph.edges[eid].source_backends) for eid in eids],
            "rule_ids":[list(graph.edges[eid].rule_ids) for eid in eids],
        })
    return routes,{
        "compound_count":len(graph.compounds),
        "edge_count":len(graph.edges),
        "backends":list(graph.backend_set()),
        "composite_edge_count":graph.composite_edge_count(),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--max-route-steps",type=int,default=8)
    ap.add_argument("--max-routes",type=int,default=100)
    args=ap.parse_args()

    root=Path(__file__).resolve().parents[1]
    panel_path=Path(args.panel)
    panel=json.loads(panel_path.read_text())
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    targets_dir=out/"targets"; targets_dir.mkdir(exist_ok=True)

    engine=SynBioCrowEngine()
    readiness=engine.backend_readiness()
    for bid in BACKENDS:
        if not readiness.get(bid,{}).get("available",False):
            raise RuntimeError(f"Required backend unavailable: {bid}: {readiness.get(bid)}")

    all_records=[]
    for i,target in enumerate(panel["targets"],1):
        target_path=targets_dir/f"{target['target_id']}.json"
        if target_path.is_file():
            rec=json.loads(target_path.read_text())
            all_records.append(rec)
            print(f"[SEALED] {i}/{len(panel['targets'])} {target['target_id']} RESUME cached",flush=True)
            continue

        print(f"[SEALED] {i}/{len(panel['targets'])} {target['target_id']} {target['target_name']}",flush=True)
        arms={}
        union_candidates=[]
        for bid in BACKENDS:
            t0=time.perf_counter()
            backend=engine.backends.get(bid)
            try:
                candidates=list(backend.generate(target["target_smiles"],options={}))
                status="COMPLETE" if candidates else "NO_HIT"
                arms[bid]={
                    "status":status,
                    "elapsed_seconds":time.perf_counter()-t0,
                    "candidate_count":len(candidates),
                    "routes":[candidate_route(c) for c in candidates[:100]],
                }
                union_candidates.extend(candidates)
            except Exception as exc:
                arms[bid]={
                    "status":"ERROR",
                    "elapsed_seconds":time.perf_counter()-t0,
                    "candidate_count":0,
                    "routes":[],
                    "error_type":type(exc).__name__,
                    "error":str(exc),
                }
            print(f"[SEALED]   {bid} {arms[bid]['status']} candidates={arms[bid]['candidate_count']} elapsed={arms[bid]['elapsed_seconds']:.1f}s",flush=True)

        ens_routes,graph_summary=ensemble_routes(
            engine,union_candidates,target["target_smiles"],target.get("sink_smiles",[]),
            args.max_route_steps,args.max_routes
        )
        arms["ensemble"]={
            "status":"COMPLETE" if union_candidates else "NO_HIT",
            "candidate_count":len(union_candidates),
            "route_count":len(ens_routes),
            "routes":ens_routes,
            "graph_summary":graph_summary,
        }

        rec={
            "target_id":target["target_id"],
            "target_name":target["target_name"],
            "target_smiles":target["target_smiles"],
            "sink_smiles":target.get("sink_smiles",[]),
            "chassis":target.get("chassis"),
            "arms":arms,
        }
        target_path.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
        all_records.append(rec)

    predictions={
        "schema":"synbiocrow.galaxy_literature_predictions.v1",
        "panel_id":panel.get("panel_id"),
        "truth_accessed":False,
        "backends":list(BACKENDS),
        "max_route_steps":args.max_route_steps,
        "max_routes":args.max_routes,
        "records":all_records,
    }
    pred_path=out/"sealed_predictions.json"
    pred_path.write_text(json.dumps(predictions,indent=2,sort_keys=True)+"\n")
    digest=sha256(pred_path)

    manifest={
        "schema":"synbiocrow.galaxy_literature_predictions_manifest.v1",
        "git_commit":git_head(root),
        "panel_sha256":sha256(panel_path),
        "predictions_sha256":digest,
        "target_count":len(all_records),
        "truth_accessed":False,
        "backend_readiness":readiness,
        "sealed":True,
    }
    (out/"sealed_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps(manifest,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
