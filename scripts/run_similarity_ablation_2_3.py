from __future__ import annotations

import argparse, hashlib, json, math, time
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem, rdFingerprintGenerator, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

ARMS=("doranet","retrobiocat2","retropath_standalone")
POLICIES=("2d_only","3d_first","3d_only")
MORGAN=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def canon(smiles:str)->str:
    raw=(smiles or "").strip()
    if not raw:
        return raw
    m=Chem.MolFromSmiles(raw)
    if m is None:
        return raw
    Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=False)


def split_rxn(rxn:str):
    if ">>" in rxn:
        left,right=rxn.split(">>",1); sep="."
    elif " = " in rxn:
        left,right=rxn.split(" = ",1); sep=" + "
    else:
        return (),()
    lhs=tuple(canon(x) for x in left.split(sep) if x.strip())
    rhs=tuple(canon(x) for x in right.split(sep) if x.strip())
    return lhs,rhs


def largest_components(side):
    rows=[]
    for smi in side:
        m=Chem.MolFromSmiles(smi)
        if m is None:
            continue
        rows.append((m.GetNumHeavyAtoms(),smi))
    if not rows:
        return ()
    rows.sort(key=lambda x:(-x[0],x[1]))
    max_heavy=rows[0][0]
    # Preserve all tied major components; cap at two for co-substrate cases.
    return tuple(s for h,s in rows if h==max_heavy)[:2]


class MoleculeSimilarity:
    def __init__(self,seed=20230930):
        self.seed=int(seed)
        self.fp={}
        self.usr={}
        self.conformer_attempted=set()
        self.conformer_success=set()
        self.conformer_failed=set()
        self.pair_calls=defaultdict(int)
        self.fallback_calls=0

    def _mol(self,smi):
        return Chem.MolFromSmiles(smi)

    def fingerprint(self,smi):
        smi=canon(smi)
        if smi not in self.fp:
            m=self._mol(smi)
            self.fp[smi]=MORGAN.GetFingerprint(m) if m is not None else None
        return self.fp[smi]

    def usr_descriptor(self,smi):
        smi=canon(smi)
        if smi in self.usr:
            return self.usr[smi]
        self.conformer_attempted.add(smi)
        m=self._mol(smi)
        if m is None or m.GetNumHeavyAtoms()<2:
            self.usr[smi]=None
            self.conformer_failed.add(smi)
            return None
        try:
            mh=Chem.AddHs(m)
            params=AllChem.ETKDGv3()
            params.randomSeed=self.seed
            params.useRandomCoords=False
            cid=AllChem.EmbedMolecule(mh,params)
            if cid<0:
                raise ValueError("ETKDG embedding failed")
            try:
                AllChem.UFFOptimizeMolecule(mh,confId=cid,maxIters=200)
            except Exception:
                pass
            self.usr[smi]=tuple(float(x) for x in rdMolDescriptors.GetUSRCAT(mh,confId=cid))
            self.conformer_success.add(smi)
        except Exception:
            self.usr[smi]=None
            self.conformer_failed.add(smi)
        return self.usr[smi]

    def sim2d(self,a,b):
        self.pair_calls["2d"]+=1
        fa=self.fingerprint(a); fb=self.fingerprint(b)
        if fa is None or fb is None:
            return None
        return float(DataStructs.TanimotoSimilarity(fa,fb))

    def sim3d(self,a,b):
        self.pair_calls["3d"]+=1
        da=self.usr_descriptor(a); db=self.usr_descriptor(b)
        if da is None or db is None:
            return None
        return float(rdMolDescriptors.GetUSRScore(da,db))

    def pair(self,a,b,policy):
        if policy=="2d_only":
            return self.sim2d(a,b),False
        if policy=="3d_only":
            return self.sim3d(a,b),False
        if policy=="3d_first":
            v=self.sim3d(a,b)
            if v is not None:
                return v,False
            self.fallback_calls+=1
            return self.sim2d(a,b),True
        raise ValueError(policy)


def set_similarity(a,b,policy,sim):
    aa=largest_components(a); bb=largest_components(b)
    if not aa or not bb:
        return None,0
    vals=[]; fallbacks=0
    # Symmetric best-match mean, robust to one-vs-two major-component cases.
    for x in aa:
        cand=[]
        for y in bb:
            v,f=sim.pair(x,y,policy)
            if v is not None:
                cand.append(v); fallbacks+=int(f)
        if not cand:
            return None,fallbacks
        vals.append(max(cand))
    for y in bb:
        cand=[]
        for x in aa:
            v,f=sim.pair(x,y,policy)
            if v is not None:
                cand.append(v); fallbacks+=int(f)
        if not cand:
            return None,fallbacks
        vals.append(max(cand))
    return mean(vals),fallbacks


def reaction_similarity(a_rxn,b_rxn,policy,sim):
    al,ar=split_rxn(a_rxn); bl,br=split_rxn(b_rxn)
    if not al or not ar or not bl or not br:
        return None,0
    # Direction-independent because generator reaction orientation differs.
    l1,f1=set_similarity(al,bl,policy,sim)
    r1,f2=set_similarity(ar,br,policy,sim)
    l2,f3=set_similarity(al,br,policy,sim)
    r2,f4=set_similarity(ar,bl,policy,sim)
    direct=None if l1 is None or r1 is None else (l1+r1)/2.0
    reverse=None if l2 is None or r2 is None else (l2+r2)/2.0
    vals=[x for x in (direct,reverse) if x is not None]
    return (max(vals) if vals else None),f1+f2+f3+f4


def stable_union_routes(record):
    seen=set(); out=[]
    for bid in ARMS:
        for r in record.get("arms",{}).get(bid,{}).get("routes",[]):
            key=tuple(r.get("reactions",[]))
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({
                "reactions":list(key),
                "source_backends":[bid],
            })
    return out


def forwardize(reactions):
    out=[]
    for r in reversed(reactions):
        lhs,rhs=split_rxn(r)
        out.append((tuple(sorted(rhs)),tuple(sorted(lhs))))
    return out


def truth_route(rec):
    return [split_rxn(x["reaction_smiles"]) for x in rec["reactions"]]


def exact_connectivity(route,truth):
    return forwardize(route.get("reactions",[]))==truth_route(truth)


def literature_corpus(dev_records):
    out=[]
    for rec in dev_records:
        for rxn in rec["reactions"]:
            out.append({
                "pathway_id":rec["pathway_id"],
                "target_name":rec["target_name"],
                "reaction_smiles":rxn["reaction_smiles"],
                "ec_numbers":tuple(sorted(set(rxn.get("ec_numbers") or []))),
            })
    return out


def route_evidence_score(route,corpus,policy,sim):
    step_scores=[]; fallback_pairs=0
    best_hits=[]
    for rxn in route.get("reactions",[]):
        best=None; best_row=None
        for ev in corpus:
            v,fb=reaction_similarity(rxn,ev["reaction_smiles"],policy,sim)
            fallback_pairs+=fb
            if v is None:
                continue
            if best is None or v>best:
                best=v; best_row=ev
        if best is None:
            return None,fallback_pairs,best_hits
        step_scores.append(best)
        best_hits.append({
            "score":best,
            "pathway_id":best_row["pathway_id"] if best_row else None,
            "target_name":best_row["target_name"] if best_row else None,
            "ec_numbers":list(best_row["ec_numbers"]) if best_row else [],
        })
    return (mean(step_scores) if step_scores else None),fallback_pairs,best_hits


def rank_routes(routes,corpus,policy,sim,truth):
    rows=[]; fallbacks=0
    for i,route in enumerate(routes):
        score,fb,hits=route_evidence_score(route,corpus,policy,sim)
        fallbacks+=fb
        rows.append({
            "route_index":i,
            "score":score,
            "reaction_count":len(route.get("reactions",[])),
            "source_backends":route.get("source_backends",[]),
            "exact_connectivity_match":exact_connectivity(route,truth),
            "best_evidence_hits":hits,
        })
    ranked=[x for x in rows if x["score"] is not None]
    ranked.sort(key=lambda x:(-x["score"],x["reaction_count"],x["route_index"]))
    for rank,row in enumerate(ranked,1):
        row["rank"]=rank
    exact_ranks=[x["rank"] for x in ranked if x["exact_connectivity_match"]]
    return {
        "ranked_route_count":len(ranked),
        "unscored_route_count":len(rows)-len(ranked),
        "exact_route_rank":min(exact_ranks) if exact_ranks else None,
        "top_route_index":ranked[0]["route_index"] if ranked else None,
        "top_score":ranked[0]["score"] if ranked else None,
        "fallback_pair_count":fallbacks,
        "routes":ranked,
    }


def aggregate(target_rows,policy):
    vals=[r["policies"][policy] for r in target_rows]
    exact=[x["exact_route_rank"] for x in vals if x["exact_route_rank"] is not None]
    return {
        "targets":len(vals),
        "targets_with_scored_routes":sum(x["ranked_route_count"]>0 for x in vals),
        "targets_with_exact_route":len(exact),
        "exact_top1":sum(r<=1 for r in exact),
        "exact_top5":sum(r<=5 for r in exact),
        "exact_top10":sum(r<=10 for r in exact),
        "exact_top25":sum(r<=25 for r in exact),
        "exact_top50":sum(r<=50 for r in exact),
        "exact_mrr":mean(1.0/r for r in exact) if exact else None,
        "median_exact_rank":median(exact) if exact else None,
        "mean_top_score":mean(x["top_score"] for x in vals if x["top_score"] is not None)
                         if any(x["top_score"] is not None for x in vals) else None,
        "fallback_pair_count":sum(x["fallback_pair_count"] for x in vals),
    }


def ec_neighbor_eval(corpus,policy,sim):
    # Leave-one-pathway-out evidence retrieval. Only queries with at least one
    # exact EC label and at least one relevant reaction in another pathway count.
    rows=[]
    for i,q in enumerate(corpus):
        qec={x for x in q["ec_numbers"] if x and "-" not in x}
        if not qec:
            continue
        candidates=[]
        for j,c in enumerate(corpus):
            if i==j or c["pathway_id"]==q["pathway_id"]:
                continue
            cec={x for x in c["ec_numbers"] if x and "-" not in x}
            if not cec:
                continue
            relevant=bool(qec&cec)
            v,_=reaction_similarity(q["reaction_smiles"],c["reaction_smiles"],policy,sim)
            if v is not None:
                candidates.append((v,relevant))
        if not candidates or not any(rel for _,rel in candidates):
            continue
        candidates.sort(key=lambda x:-x[0])
        ranks=[k for k,(_,rel) in enumerate(candidates,1) if rel]
        rows.append({
            "best_relevant_rank":min(ranks),
            "top1":min(ranks)<=1,
            "top5":min(ranks)<=5,
            "top10":min(ranks)<=10,
        })
    return {
        "evaluable_queries":len(rows),
        "top1":sum(x["top1"] for x in rows),
        "top5":sum(x["top5"] for x in rows),
        "top10":sum(x["top10"] for x in rows),
        "mrr":mean(1.0/x["best_relevant_rank"] for x in rows) if rows else None,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--targets-dir",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--predictions",required=True)
    ap.add_argument("--benchmark",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--seed",type=int,default=20230930)
    args=ap.parse_args()

    targets_dir=Path(args.targets_dir)
    manifest=json.loads(Path(args.manifest).read_text())
    pred_path=Path(args.predictions)
    actual=sha256(pred_path)
    if actual!=manifest["predictions_sha256"]:
        raise RuntimeError("sealed prediction hash mismatch")

    bench=json.loads(Path(args.benchmark).read_text())
    dev=[r for r in bench["records"] if r.get("split")=="development"]
    truth={r["pathway_id"]:r for r in dev}
    corpus=literature_corpus(dev)

    preds=json.loads(pred_path.read_text())
    order=[r["target_id"] for r in preds["records"]]
    sim=MoleculeSimilarity(seed=args.seed)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    target_rows=[]
    t0=time.perf_counter()
    for n,pid in enumerate(order,1):
        path=targets_dir/f"{pid}.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        rec=json.loads(path.read_text())
        routes=stable_union_routes(rec)
        row={
            "pathway_id":pid,
            "target_name":rec.get("target_name"),
            "candidate_route_count":len(routes),
            "policies":{},
        }
        print(f"[SIM ABLATION] {n}/{len(order)} {pid} {rec.get('target_name')} routes={len(routes)}",flush=True)
        for policy in POLICIES:
            pr=rank_routes(routes,corpus,policy,sim,truth[pid])
            row["policies"][policy]=pr
            print(f"[SIM ABLATION]   {policy} scored={pr['ranked_route_count']} exact_rank={pr['exact_route_rank']} top={pr['top_score']}",flush=True)
        target_rows.append(row)

    summary={policy:aggregate(target_rows,policy) for policy in POLICIES}
    ec_eval={policy:ec_neighbor_eval(corpus,policy,sim) for policy in POLICIES}

    disagreements={
        "top_route_2d_vs_3d_first":sum(
            r["policies"]["2d_only"]["top_route_index"]!=r["policies"]["3d_first"]["top_route_index"]
            for r in target_rows
            if r["policies"]["2d_only"]["top_route_index"] is not None
            and r["policies"]["3d_first"]["top_route_index"] is not None
        ),
        "top_route_2d_vs_3d_only":sum(
            r["policies"]["2d_only"]["top_route_index"]!=r["policies"]["3d_only"]["top_route_index"]
            for r in target_rows
            if r["policies"]["2d_only"]["top_route_index"] is not None
            and r["policies"]["3d_only"]["top_route_index"] is not None
        ),
    }

    payload={
        "schema":"synbiocrow.similarity_ablation.v1",
        "scope":"development_split_only",
        "truth_accessed":True,
        "benchmark_truth_used_for_learning":False,
        "prediction_sha256":actual,
        "development_pathway_count":len(dev),
        "literature_reaction_corpus_count":len(corpus),
        "policies":{
            "2d_only":"Morgan radius-2 2048-bit fingerprint / Tanimoto",
            "3d_first":"USRCAT on deterministic ETKDGv3 conformers; per-pair 2D fallback when 3D unavailable",
            "3d_only":"USRCAT only; routes with an unscorable reaction are excluded from 3D-only ranking",
        },
        "reaction_similarity":"direction-independent mean of major-component side similarities",
        "route_score":"mean over route steps of best literature-reaction evidence similarity",
        "summary":summary,
        "leave_one_pathway_out_ec_neighbor_retrieval":ec_eval,
        "policy_disagreements":disagreements,
        "descriptor_audit":{
            "unique_3d_attempted":len(sim.conformer_attempted),
            "unique_3d_success":len(sim.conformer_success),
            "unique_3d_failed":len(sim.conformer_failed),
            "3d_success_fraction":len(sim.conformer_success)/max(1,len(sim.conformer_attempted)),
            "fallback_pair_calls":sim.fallback_calls,
            "pair_calls":dict(sim.pair_calls),
            "failed_smiles":sorted(sim.conformer_failed)[:100],
            "seed":args.seed,
        },
        "runtime_seconds":time.perf_counter()-t0,
        "records":target_rows,
    }
    result=out/"similarity_ablation_development.json"
    result.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print("\nFINAL SUMMARY")
    print(json.dumps({
        "summary":summary,
        "ec_neighbor_retrieval":ec_eval,
        "policy_disagreements":disagreements,
        "descriptor_audit":payload["descriptor_audit"],
        "runtime_seconds":payload["runtime_seconds"],
    },indent=2,sort_keys=True),flush=True)
    print("RESULT",result,flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
