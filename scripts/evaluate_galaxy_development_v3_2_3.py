from __future__ import annotations

import argparse, hashlib, json
from collections import defaultdict, deque
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

def canon(smiles:str, stereo:bool)->str:
    m=Chem.MolFromSmiles(smiles.strip())
    if m is None:
        return smiles.strip()
    if not stereo:
        Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=stereo)

def split_rxn(rxn:str, stereo:bool):
    if ">>" in rxn:
        left,right=rxn.split(">>",1)
        lhs=[x for x in left.split(".") if x.strip()]
        rhs=[x for x in right.split(".") if x.strip()]
    elif " = " in rxn:
        left,right=rxn.split(" = ",1)
        lhs=[x for x in left.split(" + ") if x.strip()]
        rhs=[x for x in right.split(" + ") if x.strip()]
    else:
        raise ValueError(rxn)
    return tuple(sorted(canon(x,stereo) for x in lhs)),tuple(sorted(canon(x,stereo) for x in rhs))

def forwardize(reactions,stereo):
    out=[]
    for r in reversed(reactions):
        lhs,rhs=split_rxn(r,stereo)
        out.append((rhs,lhs))
    return out

def truth_route(rec,stereo):
    return [split_rxn(x["reaction_smiles"],stereo) for x in rec["reactions"]]

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
    p=inter/len(ps) if ps else 0.0
    r=inter/len(ts) if ts else 0.0
    return {
        "predicted_reactions":len(pred),
        "truth_reactions":len(truth),
        "exact_reaction_overlap":inter,
        "reaction_precision":p,
        "reaction_recall":r,
        "reaction_f1":2*p*r/(p+r) if p+r else 0.0,
        "ordered_lcs_fraction":lcs(pred,truth)/max(1,len(truth)),
        "exact_route_match":pred==truth,
        "length_difference":len(pred)-len(truth),
    }

def route_metrics(routes,truth,stereo):
    rows=[]
    for rank,route in enumerate(routes,1):
        m=compare(forwardize(route.get("reactions",[]),stereo),truth)
        m["rank"]=rank
        rows.append(m)
    best=max(rows,key=lambda x:(x["reaction_recall"],x["ordered_lcs_fraction"],x["reaction_precision"],-x["rank"])) if rows else None
    return {
        "prediction_count":len(routes),
        "best":best,
        "exact_recovery_topk":{str(k):any(x["exact_route_match"] for x in rows[:k]) for k in (1,5,10,25,50)}
    }

def infer_meta(route,bid):
    metas=route.get("step_metadata")
    if metas: return list(metas)
    prov=route.get("provenance") or {}
    if bid=="retropath_standalone":
        orientation=prov.get("graph_orientation")
        side="right" if orientation=="product_to_substrate" else "left"
        return [{"retrosynthetic_parent_side":side,"graph_orientation":orientation} for _ in route.get("reactions",[])]
    return [{} for _ in route.get("reactions",[])]

def serialized_candidates(record):
    out=[]
    for bid in ARMS:
        for route in record["arms"].get(bid,{}).get("routes",[]):
            reactions=route.get("reactions",[])
            rules=route.get("rules") or [None]*len(reactions)
            metas=infer_meta(route,bid)
            steps=tuple(ReactionStep(
                reaction=rxn,
                rule_id=rules[j] if j<len(rules) else None,
                source_backend=bid,
                metadata=metas[j] if j<len(metas) else {}
            ) for j,rxn in enumerate(reactions))
            out.append(PathwayCandidate(
                candidate_id=route.get("candidate_id",f"{bid}-{len(out)}"),
                target_smiles=record["target_smiles"],
                steps=steps,
                source_backends=tuple(route.get("source_backends") or (bid,)),
                provenance=route.get("provenance") or {},
            ))
    return out

def strict_ensemble(record,max_steps,max_routes):
    cands=serialized_candidates(record)
    g=build_reaction_graph(cands)
    tk=resolve_compound(record["target_smiles"],source="request").key
    sk={resolve_compound(x,source="request").key for x in record.get("sink_smiles",[])}
    paths=g.find_routes(tk,sk,max_steps=max_steps,max_routes=max_routes) if sk else []
    return [{"rank":i+1,"reactions":[g.edges[e].reaction for e in path]} for i,path in enumerate(paths)]

def parent_side(step):
    explicit=(step.metadata or {}).get("retrosynthetic_parent_side")
    if explicit in {"left","right"}: return explicit
    if step.source_backend=="retrobiocat2": return "left"
    if step.source_backend=="doranet":
        return "left" if (step.metadata or {}).get("direction","retro")=="retro" else "right"
    if step.source_backend in {"retropath2","retropath_standalone"}: return "right"
    return "left"

def connectivity_ensemble(record,max_steps,max_routes):
    # Build a stereo-stripped graph directly from serialized candidates.
    by_parent=defaultdict(list)
    edge_rxn={}
    for cand in serialized_candidates(record):
        for step in cand.steps:
            lhs,rhs=split_rxn(step.reaction,stereo=False)
            side=parent_side(step)
            parents=lhs if side=="left" else rhs
            precursors=rhs if side=="left" else lhs
            for p in parents:
                key=(p,tuple(sorted(precursors)),step.reaction)
                eid=hashlib.sha256(repr(key).encode()).hexdigest()[:24]
                by_parent[p].append((eid,tuple(sorted(precursors))))
                edge_rxn[eid]=step.reaction

    target=canon(record["target_smiles"],False)
    sinks={canon(x,False) for x in record.get("sink_smiles",[])}
    routes=[]
    q=deque([(frozenset([target]),tuple())])
    seen=set()
    while q and len(routes)<max_routes:
        frontier,used=q.popleft()
        if frontier.issubset(sinks):
            routes.append(list(used)); continue
        if len(used)>=max_steps: continue
        state=(frontier,used)
        if state in seen: continue
        seen.add(state)
        unresolved=sorted(frontier-sinks)[0]
        for eid,precursors in by_parent.get(unresolved,[]):
            nf=set(frontier); nf.remove(unresolved); nf.update(precursors)
            q.append((frozenset(nf),used+(eid,)))
    return [{"rank":i+1,"reactions":[edge_rxn[e] for e in path]} for i,path in enumerate(routes)]

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
    preds=json.loads(pred_path.read_text()); bench=json.loads(bench_path.read_text())
    truth={r["pathway_id"]:r for r in bench["records"] if r.get("split")=="development"}

    rows=[]
    for rec in preds["records"]:
        t=truth[rec["target_id"]]
        strict_routes=strict_ensemble(rec,preds.get("max_route_steps",8),preds.get("max_routes",100))
        conn_routes=connectivity_ensemble(rec,preds.get("max_route_steps",8),preds.get("max_routes",100))
        modes={}
        for mode,stereo,ens in (("strict_stereo",True,strict_routes),("connectivity",False,conn_routes)):
            tr=truth_route(t,stereo)
            armroutes={a:rec["arms"].get(a,{}).get("routes",[]) for a in ARMS}
            armroutes["ensemble"]=ens
            modes[mode]={"arms":{a:route_metrics(routes,tr,stereo) for a,routes in armroutes.items()}}
        rows.append({
            "pathway_id":rec["target_id"],
            "target_name":rec["target_name"],
            "truth_steps":len(t["reactions"]),
            "strict_ensemble_route_count":len(strict_routes),
            "connectivity_ensemble_route_count":len(conn_routes),
            "modes":modes,
        })

    summary={"strict_stereo":{},"connectivity":{}}
    for mode in summary:
        for arm in (*ARMS,"ensemble"):
            summary[mode][arm]=aggregate(rows,arm,mode)

    payload={
        "schema":"synbiocrow.galaxy_development_evaluation.v3",
        "predictions_sha256":sha256(pred_path),
        "benchmark_sha256":sha256(bench_path),
        "truth_accessed":True,
        "backend_chemistry_rerun":False,
        "connectivity_graph_rebuilt_without_stereochemistry":True,
        "summary":summary,
        "records":rows,
    }
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"galaxy_development_evaluation_v3.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
