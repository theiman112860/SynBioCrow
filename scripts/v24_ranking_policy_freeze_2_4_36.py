#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.ranking_policy_freeze_2_4_36 import matrix,percentile_transform,max_equivalent_ids,FEATURES

def pair_training(X,y,max_pairs=80000,seed=2436):
    rng=np.random.default_rng(seed);X=np.asarray(X,float);y=np.asarray(y,float);n=len(y)
    P=[];L=[];tries=0
    while len(L)<max_pairs and tries<max_pairs*20:
        i,j=rng.integers(0,n,2);tries+=1
        if i==j:continue
        d=y[i]-y[j]
        if abs(d)<=1e-12:continue
        z=X[i]-X[j];lab=1 if d>0 else 0
        P.append(z);L.append(lab);P.append(-z);L.append(1-lab)
    return np.asarray(P,float),np.asarray(L,int)

def ranks(ids,scores):
    order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))
    return {ids[i]:r+1 for r,i in enumerate(order)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ranked",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    ranked=json.loads(Path(a.ranked).read_text())
    aud=json.loads(Path(a.audit).read_text())
    man=json.loads(Path(a.split_manifest).read_text())

    dev={r["record_id"] for r in man["records"] if r["split"]=="development"}
    sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
    aby={r["record_id"]:r["candidate_audit"] for r in aud}
    rby={}
    for r in ranked:rby.setdefault(r["record_id"],[]).append(r)

    by={}
    for rid in sorted(dev):
        aa={x["candidate_id"]:x for x in aby[rid]}
        rows=[]
        for r in rby[rid]:
            cid=str(r["route_id"]).removeprefix("candidate:")
            if cid in aa:
                x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)
        X,y,ids=matrix(rows)
        by[rid]=(rows,percentile_transform(X),y,ids)

    # Freeze candidate coefficients trained on all development targets only.
    Xall=[];yall=[]
    for rid,(rows,X,y,ids) in by.items():
        Xall.extend(X.tolist());yall.extend(y)
    from sklearn.linear_model import LogisticRegression
    P,L=pair_training(Xall,yall)
    model=LogisticRegression(C=1.0,max_iter=3000,solver="lbfgs").fit(P,L)
    coef=model.coef_.ravel().tolist()
    intercept=float(model.intercept_[0])

    # Reproduce LOTO development evidence for the chosen representation.
    loto=[]
    for hold,(rows_h,Xh,yh,idsh) in by.items():
        Xtr=[];ytr=[]
        for rid,(rows,X,y,ids) in by.items():
            if rid==hold:continue
            Xtr.extend(X.tolist());ytr.extend(y)
        P2,L2=pair_training(Xtr,ytr,seed=24360+len(loto))
        m=LogisticRegression(C=1.0,max_iter=3000,solver="lbfgs").fit(P2,L2)
        score=Xh@m.coef_.ravel()
        rm=ranks(idsh,score);eq=max_equivalent_ids(idsh,yh)
        fr={r["route_id"]:int(r["rank"]) for r in rows_h}
        fv=[fr[x] for x in eq];rv=[rm[x] for x in eq]
        loto.append({"record_id":hold,"candidate_count":len(idsh),"max_equivalent_count":len(eq),
                     "frozen_best_equivalent_rank":min(fv),"policy_best_equivalent_rank":min(rv),
                     "frozen_median_equivalent_rank":float(np.median(fv)),
                     "policy_median_equivalent_rank":float(np.median(rv))})

    policy={
      "schema":"synbiocrow.v24.target-relative-linear-pairwise-policy.v1",
      "version":"2.4.36",
      "feature_order":list(FEATURES),
      "normalization":"within-target percentile ranks with average ranks for ties",
      "pairwise_training":"zero-gap pairs excluded; symmetric difference pairs; logistic regression C=1.0 lbfgs",
      "coefficients":coef,
      "intercept":intercept,
      "training_scope":"development targets only",
      "validation_truth_accessed":False,
      "evaluation_truth_accessed":False
    }
    policy_bytes=(json.dumps(policy,indent=2,sort_keys=True)+"\n").encode()
    policy_sha=hashlib.sha256(policy_bytes).hexdigest()
    (out/"ranking_policy_2_4_36.json").write_bytes(policy_bytes)

    summary={
      "schema":"synbiocrow.v24.ranking-policy-freeze-candidate.v1",
      "version":"2.4.36",
      "selected_policy":"target-relative linear pairwise",
      "selection_basis":"2.4.35 leave-one-target-out development transfer improved best-equivalent and median-equivalent rank for all four development targets",
      "loto_reproduction":loto,
      "policy_sha256":policy_sha,
      "production_ranking_changed":False,
      "validation_truth_accessed":False,
      "evaluation_truth_accessed":False,
      "sealed_nondevelopment_record_ids":sorted(sealed)
    }
    (out/"ranking_policy_freeze_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
