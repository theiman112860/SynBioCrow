#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.ranking_policy_freeze_2_4_36_1 import matrix,percentile_transform,deterministic_within_target_pairs,max_equivalent_ids,FEATURES

def ranks(ids,scores):
    order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))
    return {ids[i]:r+1 for r,i in enumerate(order)}

def pool_pairs(by,target_ids):
    Ps=[];Ls=[]
    for rid in sorted(target_ids):
        rows,X,y,ids=by[rid]
        P,L=deterministic_within_target_pairs(X,y,ids)
        if len(L):
            Ps.append(P);Ls.append(L)
    return np.vstack(Ps),np.concatenate(Ls)

def fit_model(P,L):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=1.0,max_iter=3000,solver="lbfgs",random_state=0).fit(P,L)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True)
    ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());man=json.loads(Path(a.split_manifest).read_text())
    dev={r["record_id"] for r in man["records"] if r["split"]=="development"}
    sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
    aby={r["record_id"]:r["candidate_audit"] for r in aud};rby={}
    for r in ranked:rby.setdefault(r["record_id"],[]).append(r)

    by={}
    for rid in sorted(dev):
        aa={x["candidate_id"]:x for x in aby[rid]};rows=[]
        for r in rby[rid]:
            cid=str(r["route_id"]).removeprefix("candidate:")
            if cid in aa:
                x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
        X,y,ids=matrix(rows);by[rid]=(rows,percentile_transform(X),y,ids)

    # Hard LOTO reproduction with deterministic within-target pairs only.
    loto=[]
    for hold in sorted(dev):
        train=sorted(dev-{hold})
        P,L=pool_pairs(by,train);m=fit_model(P,L)
        rows_h,Xh,yh,idsh=by[hold];score=Xh@m.coef_.ravel();rm=ranks(idsh,score)
        eq=max_equivalent_ids(idsh,yh);fr={r["route_id"]:int(r["rank"]) for r in rows_h}
        fv=[fr[x] for x in eq];rv=[rm[x] for x in eq]
        loto.append({"record_id":hold,"train_targets":train,"candidate_count":len(idsh),"pair_count":int(len(L)),
                     "max_equivalent_count":len(eq),"frozen_best_equivalent_rank":min(fv),
                     "policy_best_equivalent_rank":min(rv),"frozen_median_equivalent_rank":float(np.median(fv)),
                     "policy_median_equivalent_rank":float(np.median(rv))})

    # Final development-only policy.
    P,L=pool_pairs(by,dev);m=fit_model(P,L)
    policy={"schema":"synbiocrow.v24.target-relative-linear-pairwise-policy.v2",
            "version":"2.4.36.1","feature_order":list(FEATURES),
            "normalization":"within-target percentile ranks with average ranks for ties",
            "pair_construction":"deterministic within-target only; similarity-sorted fixed offsets 1,2,4,8,16,32,64,128,256,512,1024; zero-gap pairs excluded; symmetric differences",
            "cross_target_pair_labels":False,"logistic_regression":{"C":1.0,"solver":"lbfgs","max_iter":3000,"random_state":0},
            "coefficients":m.coef_.ravel().tolist(),"intercept":float(m.intercept_[0]),
            "development_pair_count":int(len(L)),"training_scope":"development targets only",
            "validation_truth_accessed":False,"evaluation_truth_accessed":False}
    pb=(json.dumps(policy,indent=2,sort_keys=True)+"\n").encode();sha=hashlib.sha256(pb).hexdigest()
    (out/"ranking_policy_2_4_36_1.json").write_bytes(pb)
    summary={"schema":"synbiocrow.v24.ranking-policy-freeze-candidate.v2","version":"2.4.36.1",
             "selected_policy":"deterministic target-relative linear pairwise, within-target preference labels only",
             "loto_reproduction":loto,"policy_sha256":sha,"production_ranking_changed":False,
             "validation_truth_accessed":False,"evaluation_truth_accessed":False,
             "sealed_nondevelopment_record_ids":sorted(sealed)}
    (out/"ranking_policy_freeze_summary_2_4_36_1.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
