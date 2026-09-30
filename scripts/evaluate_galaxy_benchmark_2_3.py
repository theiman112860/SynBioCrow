from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from statistics import mean, median

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*")

BACKENDS=("doranet","retrobiocat2","retropath_standalone")
MORGAN=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def canon(smiles,stereo=False):
    raw=(smiles or "").strip()
    if not raw:return raw
    m=Chem.MolFromSmiles(raw)
    if m is None:return raw
    if not stereo: Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=stereo)

def split_rxn(rxn,stereo=False):
    if ">>" in rxn:
        left,right=rxn.split(">>",1); sep="."
    elif " = " in rxn:
        left,right=rxn.split(" = ",1); sep=" + "
    else:
        return (),()
    lhs=tuple(sorted(canon(x,stereo) for x in left.split(sep) if x.strip()))
    rhs=tuple(sorted(canon(x,stereo) for x in right.split(sep) if x.strip()))
    return lhs,rhs

def forwardize(reactions,stereo=False):
    out=[]
    for r in reversed(reactions):
        lhs,rhs=split_rxn(r,stereo)
        out.append((rhs,lhs))
    return out

def truth_route(rec,stereo=False):
    return [split_rxn(x["reaction_smiles"],stereo) for x in rec.get("reactions",[])]

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
        "reaction_precision":p,
        "reaction_recall":r,
        "reaction_f1":2*p*r/(p+r) if p+r else 0.0,
        "ordered_lcs_fraction":lcs(pred,truth)/max(1,len(truth)),
        "exact_route_match":pred==truth,
    }

def largest(side):
    rows=[]
    for smi in side:
        m=Chem.MolFromSmiles(smi)
        if m is not None: rows.append((m.GetNumHeavyAtoms(),canon(smi,False)))
    if not rows:return ()
    rows.sort(key=lambda x:(-x[0],x[1]))
    mh=rows[0][0]
    return tuple(s for h,s in rows if h==mh)[:2]

_FP={}
def fp(smi):
    smi=canon(smi,False)
    if smi not in _FP:
        m=Chem.MolFromSmiles(smi)
        _FP[smi]=MORGAN.GetFingerprint(m) if m is not None else None
    return _FP[smi]

def molsim(a,b):
    fa,fb=fp(a),fp(b)
    if fa is None or fb is None:return None
    return float(DataStructs.TanimotoSimilarity(fa,fb))

def setsim(a,b):
    aa,bb=largest(a),largest(b)
    if not aa or not bb:return None
    vals=[]
    for x in aa:
        cand=[molsim(x,y) for y in bb]
        cand=[v for v in cand if v is not None]
        if not cand:return None
        vals.append(max(cand))
    for y in bb:
        cand=[molsim(x,y) for x in aa]
        cand=[v for v in cand if v is not None]
        if not cand:return None
        vals.append(max(cand))
    return mean(vals)

def rxnsim(a,b):
    al,ar=split_rxn(a,False); bl,br=split_rxn(b,False)
    if not al or not ar or not bl or not br:return None
    d1,d2=setsim(al,bl),setsim(ar,br)
    r1,r2=setsim(al,br),setsim(ar,bl)
    vals=[]
    if d1 is not None and d2 is not None: vals.append((d1+d2)/2)
    if r1 is not None and r2 is not None: vals.append((r1+r2)/2)
    return max(vals) if vals else None

def dev_corpus(records):
    out=[]
    for rec in records:
        if rec.get("split")!="development":continue
        for rxn in rec.get("reactions",[]):
            out.append(rxn["reaction_smiles"])
    return out

def route_score(route,corpus):
    scores=[]
    for rxn in route.get("reactions",[]):
        vals=[rxnsim(rxn,e) for e in corpus]
        vals=[v for v in vals if v is not None]
        if not vals:return None
        scores.append(max(vals))
    return mean(scores) if scores else None

def route_pool(record):
    seen=set(); out=[]
    for bid in BACKENDS:
        for r in record.get("arms",{}).get(bid,{}).get("routes",[]):
            key=tuple(r.get("reactions",[]))
            if key and key not in seen:
                seen.add(key)
                out.append({"reactions":list(key),"source_backends":[bid],"origin":"constituent"})
    for r in record.get("arms",{}).get("ensemble",{}).get("routes",[]):
        key=tuple(r.get("reactions",[]))
        if key and key not in seen:
            seen.add(key)
            src=r.get("source_backends",[])
            out.append({"reactions":list(key),"source_backends":src,"origin":"ensemble_graph"})
    return out

def rank_pool(routes,corpus):
    rows=[]
    for i,r in enumerate(routes):
        s=route_score(r,corpus)
        if s is None: continue
        rows.append({**r,"score":s,"original_index":i})
    rows.sort(key=lambda x:(-x["score"],len(x["reactions"]),x["original_index"]))
    for i,r in enumerate(rows,1): r["rank"]=i
    return rows

def evaluate_routes(routes,truth_rec,stereo):
    t=truth_route(truth_rec,stereo)
    rows=[]
    for rank,r in enumerate(routes,1):
        m=compare(forwardize(r.get("reactions",[]),stereo),t)
        m["rank"]=rank; rows.append(m)
    best=max(rows,key=lambda x:(x["reaction_recall"],x["ordered_lcs_fraction"],x["reaction_precision"],-x["rank"])) if rows else None
    exact=[x["rank"] for x in rows if x["exact_route_match"]]
    return {
        "prediction_count":len(routes),
        "best":best,
        "exact_route_rank":min(exact) if exact else None,
        "exact_recovery_topk":{str(k):any(x["exact_route_match"] for x in rows[:k]) for k in (1,5,10,25,50)}
    }

def summarize(records,mode,arm):
    vals=[r["modes"][mode][arm] for r in records]
    recalls=[(x.get("best") or {}).get("reaction_recall",0.0) for x in vals]
    exact=[x["exact_route_rank"] for x in vals if x.get("exact_route_rank") is not None]
    return {
        "denominator":len(vals),
        "exact_top1":sum(x["exact_recovery_topk"]["1"] for x in vals),
        "exact_top5":sum(x["exact_recovery_topk"]["5"] for x in vals),
        "exact_top10":sum(x["exact_recovery_topk"]["10"] for x in vals),
        "exact_top50":sum(x["exact_recovery_topk"]["50"] for x in vals),
        "partial_recovery_targets":sum(r>0 for r in recalls),
        "mean_best_reaction_recall":mean(recalls) if recalls else 0.0,
        "median_best_reaction_recall":median(recalls) if recalls else None,
        "exact_mrr":mean(1.0/r for r in exact) if exact else None,
        "median_exact_rank":median(exact) if exact else None,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--benchmark",required=True)
    ap.add_argument("--panel",required=True)
    ap.add_argument("--predictions-dir",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--policy-file",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    bench=json.loads(Path(args.benchmark).read_text())
    panel=json.loads(Path(args.panel).read_text())
    manifest=json.loads(Path(args.manifest).read_text())
    pred_dir=Path(args.predictions_dir)

    if sha256(pred_dir/"sealed_predictions.json")!=manifest["predictions_sha256"]:
        raise RuntimeError("sealed prediction hash mismatch")

    corpus=dev_corpus(bench["records"])
    truth={r["pathway_id"]:r for r in bench["records"] if r.get("split")=="benchmark"}
    runnable={t["target_id"] for t in panel["targets"]}
    excluded={x["target_id"]:x for x in panel.get("excluded_targets",[])}

    rows=[]
    for pid,rec in truth.items():
        if pid in excluded:
            empty={
                "prediction_count":0,"best":None,"exact_route_rank":None,
                "exact_recovery_topk":{str(k):False for k in (1,5,10,25,50)}
            }
            rows.append({
                "pathway_id":pid,"target_name":rec.get("target_name"),
                "status":excluded[pid]["status"],
                "modes":{
                    "strict_stereo":{**{b:empty for b in BACKENDS},"ensemble":empty},
                    "connectivity":{**{b:empty for b in BACKENDS},"ensemble":empty},
                }
            })
            continue

        path=pred_dir/"targets"/f"{pid}.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        pred=json.loads(path.read_text())
        pools={b:pred.get("arms",{}).get(b,{}).get("routes",[]) for b in BACKENDS}
        pools["ensemble"]=rank_pool(route_pool(pred),corpus)

        modes={}
        for mode,stereo in (("strict_stereo",True),("connectivity",False)):
            modes[mode]={b:evaluate_routes(pools[b],rec,stereo) for b in (*BACKENDS,"ensemble")}
        rows.append({"pathway_id":pid,"target_name":rec.get("target_name"),"status":"RUNNABLE","modes":modes})

    summary={mode:{arm:summarize(rows,mode,arm) for arm in (*BACKENDS,"ensemble")}
             for mode in ("strict_stereo","connectivity")}

    payload={
        "schema":"synbiocrow.galaxy_benchmark_evaluation.v1",
        "benchmark_denominator":len(truth),
        "runnable_targets":len(runnable),
        "mapping_limited_targets":len(excluded),
        "truth_accessed":True,
        "benchmark_truth_used_for_learning":False,
        "similarity_policy":"frozen_2d_primary_morgan_tanimoto",
        "policy_file_sha256":sha256(Path(args.policy_file)),
        "predictions_sha256":manifest["predictions_sha256"],
        "development_evidence_corpus_reactions":len(corpus),
        "summary":summary,
        "records":rows,
    }
    Path(args.output).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))
    print("BENCHMARK DENOMINATOR",len(truth))
    print("RUNNABLE",len(runnable),"MAPPING_LIMITED",len(excluded))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
