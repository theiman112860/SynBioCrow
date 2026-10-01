from __future__ import annotations
import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path

BACKENDS=("doranet","retrobiocat2","retropath_standalone")

def classify(rec,pred=None):
    if rec.get("status")=="MAPPING_LIMITED":
        return "MAPPING_LIMITED"
    conn=rec["modes"]["connectivity"]
    ens=conn["ensemble"]
    if ens.get("exact_route_rank") is not None:
        return "EXACT_ROUTE_RECOVERED"
    if (ens.get("best") or {}).get("reaction_recall",0)>0:
        return "PARTIAL_ROUTE_RECOVERY"
    if pred is not None:
        statuses={b:pred.get("arms",{}).get(b,{}).get("status") for b in BACKENDS}
        if any(v=="ERROR" for v in statuses.values()):
            return "BACKEND_RUNTIME_FAILURE"
        route_counts={b:len(pred.get("arms",{}).get(b,{}).get("routes",[])) for b in BACKENDS}
        if sum(route_counts.values())==0:
            cand_counts={b:pred.get("arms",{}).get(b,{}).get("candidate_count",0) for b in BACKENDS}
            if sum(cand_counts.values())==0:
                return "NO_CANDIDATE_CHEMISTRY"
            return "CANDIDATES_NO_COMPLETE_ROUTE"
        return "COMPLETE_ROUTES_NO_TRUTH_OVERLAP"
    return "UNCLASSIFIED"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scored",required=True)
    ap.add_argument("--predictions-dir",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    scored=json.loads(Path(args.scored).read_text())
    pred_dir=Path(args.predictions_dir)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for rec in scored["records"]:
        pred=None
        p=pred_dir/"targets"/f"{rec['pathway_id']}.json"
        if p.is_file(): pred=json.loads(p.read_text())
        cat=classify(rec,pred)
        conn=rec["modes"]["connectivity"]["ensemble"]
        strict=rec["modes"]["strict_stereo"]["ensemble"]
        rows.append({
            "pathway_id":rec["pathway_id"],
            "target_name":rec.get("target_name"),
            "failure_mode":cat,
            "connectivity_best_recall":(conn.get("best") or {}).get("reaction_recall",0.0),
            "connectivity_exact_rank":conn.get("exact_route_rank"),
            "strict_best_recall":(strict.get("best") or {}).get("reaction_recall",0.0),
            "prediction_count":conn.get("prediction_count",0),
        })
    counts=Counter(r["failure_mode"] for r in rows)
    payload={
        "schema":"synbiocrow.galaxy_benchmark_error_analysis.v1",
        "non_tuning":True,
        "benchmark_truth_used_for_learning":False,
        "denominator":len(rows),
        "counts":dict(sorted(counts.items())),
        "records":rows,
    }
    (out/"galaxy_benchmark_error_analysis.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    with (out/"galaxy_benchmark_error_analysis.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps(payload["counts"],indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
