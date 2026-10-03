#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
from synbiocrow.v24.high_tail_rank_2_4_32 import matrix,tail_labels

def folds(n,k=5,seed=2432):
    rng=np.random.default_rng(seed)
    idx=np.arange(n);rng.shuffle(idx)
    return np.array_split(idx,k)

def oof_prob(X,labels,factory,k=5):
    X=np.asarray(X,float);labels=np.asarray(labels,int)
    p=np.empty(len(labels),float)
    for test in folds(len(labels),min(k,len(labels))):
        train=np.setdiff1d(np.arange(len(labels)),test)
        if len(train)<4 or len(np.unique(labels[train]))<2:
            p[test]=labels[train].mean() if len(train) else labels.mean()
            continue
        m=factory();m.fit(X[train],labels[train]);p[test]=m.predict_proba(X[test])[:,1]
    return p

def rank_of(ids,scores,target_id):
    order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))
    return 1+order.index(ids.index(target_id))

def precision_at_k(labels,scores,k):
    order=np.argsort(-np.asarray(scores,float))[:k]
    lab=np.asarray(labels,int)
    return float(lab[order].mean()) if len(order) else None

def recall_at_k(labels,scores,k):
    order=np.argsort(-np.asarray(scores,float))[:k]
    lab=np.asarray(labels,int)
    pos=lab.sum()
    return float(lab[order].sum()/pos) if pos else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ranked",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--tail-quantile",type=float,default=0.90)
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

    from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
    from sklearn.metrics import average_precision_score,roc_auc_score

    records=[]
    for rid in sorted(dev):
        aa={x["candidate_id"]:x for x in aby[rid]}
        rows=[]
        for r in rby[rid]:
            cid=str(r["route_id"]).removeprefix("candidate:")
            if cid in aa:
                x=dict(r);x["similarity"]=aa[cid].get("internal_anchor_similarity_mean");rows.append(x)

        X,y,ids=matrix(rows)
        labels,thr=tail_labels(y,a.tail_quantile)
        best_idx=max(range(len(y)),key=lambda i:y[i]);best_id=ids[best_idx]
        frozen_rank=int(next(r["rank"] for r in rows if r["route_id"]==best_id))

        rf=lambda:RandomForestClassifier(n_estimators=350,max_depth=8,min_samples_leaf=5,class_weight="balanced",random_state=2432,n_jobs=-1)
        gb=lambda:GradientBoostingClassifier(n_estimators=220,max_depth=3,learning_rate=0.03,subsample=0.8,random_state=2432)

        prf=oof_prob(X,labels,rf,5)
        pgb=oof_prob(X,labels,gb,5)
        pens=(prf+pgb)/2.0

        def metrics(p):
            arr=np.asarray(labels,int)
            return {
                "roc_auc":float(roc_auc_score(arr,p)) if len(np.unique(arr))>1 else None,
                "average_precision":float(average_precision_score(arr,p)) if arr.sum()>0 else None,
                "precision_at_10":precision_at_k(labels,p,min(10,len(labels))),
                "precision_at_50":precision_at_k(labels,p,min(50,len(labels))),
                "recall_at_50":recall_at_k(labels,p,min(50,len(labels))),
                "best_internal_anchor_rank":rank_of(ids,p,best_id)
            }

        records.append({
            "record_id":rid,
            "candidate_count":len(y),
            "tail_quantile":a.tail_quantile,
            "tail_similarity_threshold":thr,
            "tail_positive_count":int(sum(labels)),
            "best_internal_anchor_route_id":best_id,
            "best_internal_anchor_similarity":float(y[best_idx]),
            "frozen_rank":frozen_rank,
            "random_forest":metrics(prf),
            "gradient_boosting":metrics(pgb),
            "ensemble":metrics(pens)
        })

    summary={
        "schema":"synbiocrow.v24.high-tail-oof-ranking.v1",
        "version":"2.4.32",
        "objective":"out-of-fold discrimination of the within-target high-similarity tail rather than mean similarity regression",
        "records":records,
        "production_ranking_changed":False,
        "generation_invoked":False,
        "validation_truth_accessed":False,
        "evaluation_truth_accessed":False,
        "sealed_nondevelopment_record_ids":sorted(sealed)
    }
    (out/"high_tail_oof_ranking_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
