from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from statistics import median

from rdkit import Chem
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from synbiocrow.ensemble import resolve_compound
from synbiocrow.ensemble.graph import build_reaction_graph

ARMS=("doranet","retrobiocat2","retropath_standalone")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def canon(smiles:str, *, stereo:bool)->str:
    m=Chem.MolFromSmiles(smiles.strip())
    if m is None:
        return smiles.strip()
    if not stereo:
        Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=stereo)

def split_rxn(rxn:str, *, stereo:bool):
    if ">>" in rxn:
        left,right=rxn.split(">>",1)
        lhs=[x for x in left.split(".") if x.strip()]
        rhs=[x for x in right.split(".") if x.strip()]
    elif " = " in rxn:
        left,right=rxn.split(" = ",1)
        lhs=[x for x in left.split(" + ") if x.strip()]
        rhs=[x for x in right.split(" + ") if x.strip()]
    else:
        raise ValueError(f"Unsupported reaction: {rxn!r}")
    return tuple(sorted(canon(x,stereo=stereo) for x in lhs)),tuple(sorted(canon(x,stereo=stereo) for x in rhs))

def forwardize(reactions, *, stereo:bool):
    # Backend candidates are stored retrosynthetically: target -> precursors.
    out=[]
    for r in reversed(reactions):
        lhs,rhs=split_rxn(r,stereo=stereo)
        out.append((rhs,lhs))
    return out

def truth_route(rec, *, stereo:bool):
    return [split_rxn(r["reaction_smiles"],stereo=stereo) for r in rec["reactions"]]

def lcs(a,b):
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b,1):
            cur.append(prev[j-1]+1 if x==y else max(prev[j],cur[-1]))
        prev=cur
    return prev[-1]

def compare(pred,truth):
    ps=set(pred); ts=set(truth); inter=len(ps&ts)
    precision=inter/len(ps) if ps else 0.0
    recall=inter/len(ts) if ts else 0.0
    return {
        "predicted_reactions":len(pred),
        "truth_reactions":len(truth),
        "exact_reaction_overlap":inter,
        "reaction_precision":precision,
        "reaction_recall":recall,
        "reaction_f1":(2*precision*recall/(precision+recall)) if precision+recall else 0.0,
        "ordered_lcs_fraction":lcs(pred,truth)/max(1,len(truth)),
        "exact_route_match":pred==truth,
        "length_difference":len(pred)-len(truth),
    }

def route_metrics(routes,truth,*,stereo:bool):
    rows=[]
    for rank,route in enumerate(routes,1):
        pred=forwardize(route.get("reactions",[]),stereo=stereo)
        m=compare(pred,truth)
        m["rank"]=rank
        rows.append(m)
    best=max(rows,key=lambda x:(x["reaction_recall"],x["ordered_lcs_fraction"],x["reaction_precision"],-x["rank"])) if rows else None
    topk={str(k):any(x["exact_route_match"] for x in rows[:k]) for k in (1,5,10,25,50)}
    return {"prediction_count":len(routes),"best":best,"exact_recovery_topk":topk}

def infer_step_metadata(route,backend_id):
    metas=route.get("step_metadata")
    if metas:
        return list(metas)
    # Backward-compatible repair for already-sealed V4 predictions.
    prov=route.get("provenance") or {}
    orientation=prov.get("graph_orientation")
    if backend_id=="retropath_standalone":
        side="right" if orientation=="product_to_substrate" else "left"
        return [{"retrosynthetic_parent_side":side,"graph_orientation":orientation} for _ in route.get("reactions",[])]
    return [{} for _ in route.get("reactions",[])]

def rebuild_ensemble(record,max_steps=8,max_routes=100):
    candidates=[]
    for bid in ARMS:
        for route in record["arms"].get(bid,{}).get("routes",[]):
            reactions=route.get("reactions",[])
            rules=route.get("rules") or [None]*len(reactions)
            metas=infer_step_metadata(route,bid)
            steps=tuple(
                ReactionStep(
                    reaction=rxn,
                    rule_id=rules[j] if j<len(rules) else None,
                    source_backend=bid,
                    metadata=metas[j] if j<len(metas) else {},
                )
                for j,rxn in enumerate(reactions)
            )
            candidates.append(PathwayCandidate(
                candidate_id=route.get("candidate_id",f"{bid}-{len(candidates)}"),
                target_smiles=record["target_smiles"],
                steps=steps,
                source_backends=tuple(route.get("source_backends") or (bid,)),
                provenance=route.get("provenance") or {},
            ))
    graph=build_reaction_graph(candidates)
    # Strict graph keys preserve stereo. If strict sink reachability fails, also
    # report a connectivity-level graph audit separately below.
    target_key=resolve_compound(record["target_smiles"],source="request").key
    sink_keys={resolve_compound(x,source="request").key for x in record.get("sink_smiles",[])}
    eids=graph.find_routes(target_key,sink_keys,max_steps=max_steps,max_routes=max_routes) if sink_keys else []
    routes=[]
    for rank,path in enumerate(eids,1):
        routes.append({
            "rank":rank,
            "edge_ids":path,
            "reactions":[graph.edges[e].reaction for e in path],
            "source_backends":[list(graph.edges[e].source_backends) for e in path],
        })
    return routes,{
        "compound_count":len(graph.compounds),
        "edge_count":len(graph.edges),
        "backends":list(graph.backend_set()),
        "composite_edge_count":graph.composite_edge_count(),
    }

def aggregate(rows,arm,mode):
    vals=[r["modes"][mode]["arms"][arm] for r in rows]
    recalls=[(x.get("best") or {}).get("reaction_recall",0.0) for x in vals]
    return {
        "targets":len(vals),
        "exact_top1":sum(x["exact_recovery_topk"]["1"] for x in vals),
        "exact_top5":sum(x["exact_recovery_topk"]["5"] for x in vals),
        "exact_top10":sum(x["exact_recovery_topk"]["10"] for x in vals),
        "exact_top50":sum(x["exact_recovery_topk"]["50"] for x in vals),
        "partial_recovery_targets":sum(r>0 for r in recalls),
        "mean_best_reaction_recall":sum(recalls)/max(1,len(recalls)),
        "median_best_reaction_recall":median(recalls) if recalls else None,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--benchmark",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    pred_path=Path(args.predictions); bench_path=Path(args.benchmark)
    preds=json.loads(pred_path.read_text())
    bench=json.loads(bench_path.read_text())
    truth={r["pathway_id"]:r for r in bench["records"] if r.get("split")=="development"}

    rows=[]
    for rec in preds["records"]:
        pid=rec["target_id"]
        t=truth[pid]
        repaired_routes,graph_summary=rebuild_ensemble(rec,preds.get("max_route_steps",8),preds.get("max_routes",100))
        arms={a:rec["arms"].get(a,{}).get("routes",[]) for a in ARMS}
        arms["ensemble"]=repaired_routes

        modes={}
        for mode,stereo in (("strict_stereo",True),("connectivity",False)):
            tr=truth_route(t,stereo=stereo)
            modes[mode]={"arms":{a:route_metrics(routes,tr,stereo=stereo) for a,routes in arms.items()}}
        rows.append({
            "pathway_id":pid,
            "target_name":rec["target_name"],
            "truth_steps":len(t["reactions"]),
            "repaired_ensemble_route_count":len(repaired_routes),
            "repaired_ensemble_graph":graph_summary,
            "modes":modes,
        })

    summary={"strict_stereo":{},"connectivity":{}}
    for mode in summary:
        for arm in (*ARMS,"ensemble"):
            summary[mode][arm]=aggregate(rows,arm,mode)

    payload={
        "schema":"synbiocrow.galaxy_development_evaluation.v2",
        "predictions_sha256":sha256(pred_path),
        "benchmark_sha256":sha256(bench_path),
        "truth_accessed":True,
        "ensemble_rebuilt_offline":True,
        "ensemble_repair_note":"RetroPath orientation recovered from sealed candidate provenance; no backend chemistry rerun.",
        "modes":{
            "strict_stereo":"Exact canonical reaction identity including stereochemistry.",
            "connectivity":"Canonical reaction identity after removing stereochemistry; useful for source formats that omit stereo."
        },
        "summary":summary,
        "records":rows,
    }
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"galaxy_development_evaluation_v2.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
