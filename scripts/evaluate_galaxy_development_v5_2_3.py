from __future__ import annotations

import argparse, gc, hashlib, json
from collections import defaultdict, deque
from pathlib import Path
from statistics import median

from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")

ARMS=("doranet","retrobiocat2","retropath_standalone")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def canon(smiles, stereo):
    raw=(smiles or "").strip()
    if not raw: return raw
    m=Chem.MolFromSmiles(raw)
    if m is None: return raw
    if not stereo: Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=stereo)

def split_rxn(rxn, stereo):
    if ">>" in rxn:
        left,right=rxn.split(">>",1); sep="."
    elif " = " in rxn:
        left,right=rxn.split(" = ",1); sep=" + "
    else:
        return (),()
    lhs=tuple(sorted(canon(x,stereo) for x in left.split(sep) if x.strip()))
    rhs=tuple(sorted(canon(x,stereo) for x in right.split(sep) if x.strip()))
    return lhs,rhs

def forwardize(reactions, stereo):
    out=[]
    for r in reversed(reactions):
        lhs,rhs=split_rxn(r,stereo)
        out.append((rhs,lhs))
    return out

def truth_route(rec, stereo):
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

def stable_union_routes(record):
    # Guaranteed monotonic ensemble: preserve every backend route verbatim.
    seen=set(); out=[]
    for bid in ARMS:
        for r in record["arms"].get(bid,{}).get("routes",[]):
            key=tuple(r.get("reactions",[]))
            if key in seen: continue
            seen.add(key)
            out.append({
                "reactions":list(key),
                "source_backends":[bid],
                "route_origin":"constituent_preserved",
            })
    # Ranking is truth-independent and deterministic.
    out.sort(key=lambda r:(len(r["reactions"]), tuple(r["reactions"]), tuple(r["source_backends"])))
    for i,r in enumerate(out,1): r["rank"]=i
    return out

def route_step_meta(route,bid):
    metas=route.get("step_metadata")
    if metas: return list(metas)
    prov=route.get("provenance") or {}
    if bid=="retropath_standalone":
        orientation=prov.get("graph_orientation")
        side="right" if orientation=="product_to_substrate" else "left"
        return [{"retrosynthetic_parent_side":side,"graph_orientation":orientation} for _ in route.get("reactions",[])]
    return [{} for _ in route.get("reactions",[])]

def parent_side(bid,meta):
    explicit=(meta or {}).get("retrosynthetic_parent_side")
    if explicit in {"left","right"}: return explicit
    if bid=="retrobiocat2": return "left"
    if bid=="doranet": return "left" if (meta or {}).get("direction","retro")=="retro" else "right"
    if bid in {"retropath2","retropath_standalone"}:
        return "left" if (meta or {}).get("graph_orientation")=="substrate_to_product" else "right"
    return "left"

def build_graph(record,stereo):
    by_parent=defaultdict(list); edge_rxn={}; edge_src={}; n=0
    for bid in ARMS:
        for route in record["arms"].get(bid,{}).get("routes",[]):
            rxns=route.get("reactions",[]); metas=route_step_meta(route,bid)
            for j,rxn in enumerate(rxns):
                lhs,rhs=split_rxn(rxn,stereo)
                side=parent_side(bid,metas[j] if j<len(metas) else {})
                parents=lhs if side=="left" else rhs
                precursors=rhs if side=="left" else lhs
                for p in parents:
                    n+=1; eid=f"e{n}"
                    by_parent[p].append((eid,tuple(sorted(precursors))))
                    edge_rxn[eid]=rxn; edge_src[eid]=bid
    return by_parent,edge_rxn,edge_src

def bounded_cross_engine_routes(record,stereo,max_steps,max_routes,max_states):
    by_parent,edge_rxn,edge_src=build_graph(record,stereo)
    target=canon(record["target_smiles"],stereo)
    sinks={canon(x,stereo) for x in record.get("sink_smiles",[])}
    if not sinks:
        return [],{"states_expanded":0,"state_cap_hit":False}

    routes=[]; q=deque([(frozenset([target]),tuple(),frozenset())]); seen=set(); states=0
    while q and len(routes)<max_routes and states<max_states:
        frontier,used,used_edges=q.popleft(); states+=1
        if frontier.issubset(sinks):
            srcs={edge_src[e] for e in used}
            if len(srcs)>1:
                routes.append(list(used))
            continue
        if len(used)>=max_steps: continue
        state=(frontier,used)
        if state in seen: continue
        seen.add(state)
        unresolved=sorted(frontier-sinks)[0]
        for eid,precursors in by_parent.get(unresolved,()):
            if eid in used_edges: continue
            nf=set(frontier); nf.remove(unresolved); nf.update(precursors)
            q.append((frozenset(nf),used+(eid,),used_edges|{eid}))
    out=[]
    for i,path in enumerate(routes,1):
        out.append({
            "rank":i,
            "reactions":[edge_rxn[e] for e in path],
            "source_backends":[edge_src[e] for e in path],
            "route_origin":"cross_engine_composed",
        })
    return out,{"states_expanded":states,"state_cap_hit":states>=max_states and bool(q)}

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
    ap.add_argument("--targets-dir",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--benchmark",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--max-states",type=int,default=15000)
    args=ap.parse_args()

    targets_dir=Path(args.targets_dir)
    manifest=json.loads(Path(args.manifest).read_text())
    predictions_path=Path(args.predictions)
    actual=sha256(predictions_path)
    if actual!=manifest["predictions_sha256"]:
        raise RuntimeError("sealed prediction hash mismatch")

    bench=json.loads(Path(args.benchmark).read_text())
    truth={r["pathway_id"]:r for r in bench["records"] if r.get("split")=="development"}

    # Use sealed_predictions only for target order/config, then release it.
    preds=json.loads(predictions_path.read_text())
    order=[r["target_id"] for r in preds["records"]]
    max_steps=preds.get("max_route_steps",8); max_routes=preds.get("max_routes",100)
    del preds; gc.collect()

    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    cache_dir=out/"targets"; cache_dir.mkdir(exist_ok=True)
    rows=[]

    for i,pid in enumerate(order,1):
        cache=cache_dir/f"{pid}.json"
        if cache.is_file():
            row=json.loads(cache.read_text()); rows.append(row)
            print(f"[EVAL V5] {i}/{len(order)} {pid} RESUME",flush=True)
            continue

        target_file=targets_dir/f"{pid}.json"
        if not target_file.is_file():
            raise FileNotFoundError(target_file)
        rec=json.loads(target_file.read_text())
        t=truth[pid]
        print(f"[EVAL V5] {i}/{len(order)} {pid} {rec['target_name']}",flush=True)

        preserved=stable_union_routes(rec)
        modes={}
        for mode,stereo in (("strict_stereo",True),("connectivity",False)):
            tr=truth_route(t,stereo)
            cross,audit=bounded_cross_engine_routes(rec,stereo,max_steps,max_routes,args.max_states)
            ensemble=preserved+cross
            armroutes={a:rec["arms"].get(a,{}).get("routes",[]) for a in ARMS}
            armroutes["ensemble"]=ensemble
            modes[mode]={
                "preserved_route_count":len(preserved),
                "cross_engine_route_count":len(cross),
                "ensemble_route_count":len(ensemble),
                "cross_engine_search_audit":audit,
                "arms":{a:route_metrics(routes,tr,stereo) for a,routes in armroutes.items()}
            }
            print(f"[EVAL V5]   {mode} preserved={len(preserved)} cross={len(cross)} states={audit['states_expanded']} cap={audit['state_cap_hit']}",flush=True)

        row={"pathway_id":pid,"target_name":rec["target_name"],"truth_steps":len(t["reactions"]),"modes":modes}
        cache.write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
        rows.append(row)
        del rec,modes
        gc.collect()

    summary={"strict_stereo":{},"connectivity":{}}
    for mode in summary:
        for arm in (*ARMS,"ensemble"):
            summary[mode][arm]=aggregate(rows,arm,mode)
        summary[mode]["cross_engine_targets"]=sum(r["modes"][mode]["cross_engine_route_count"]>0 for r in rows)
        summary[mode]["state_cap_targets"]=sum(r["modes"][mode]["cross_engine_search_audit"]["state_cap_hit"] for r in rows)

    payload={
        "schema":"synbiocrow.galaxy_development_evaluation.v5",
        "predictions_sha256":actual,
        "truth_accessed":True,
        "backend_chemistry_rerun":False,
        "ensemble_policy":"constituent-route preservation plus state-capped cross-engine composition",
        "max_cross_engine_states_per_target":args.max_states,
        "summary":summary,
        "records":rows,
    }
    (out/"galaxy_development_evaluation_v5.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print("\nFINAL SUMMARY")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
