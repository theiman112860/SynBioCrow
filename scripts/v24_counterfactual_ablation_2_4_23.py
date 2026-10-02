#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.counterfactual_ablation_2_4_23 import active_components,residual_rank
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"};ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"}
 rby={};[rby.setdefault(r["record_id"],[]).append(r) for r in ranked];aby={r["record_id"]:r["candidate_audit"] for r in aud};records=[]
 for rid in sorted(ids):
  best=max(aby[rid],key=lambda x:x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1);tr="candidate:"+best["candidate_id"];rows=rby[rid];old=int(next(x["rank"] for x in rows if x["route_id"]==tr))
  comps=active_components(rows);abl=[]
  for c in comps:
   if c["coverage"]>=.95 and c["pearson_vs_frozen_score"] is not None and abs(c["pearson_vs_frozen_score"])>.05:
    nr=residual_rank(rows,tr,c["feature"]);abl.append({"feature":c["feature"],"pearson_vs_frozen_score":c["pearson_vs_frozen_score"],"rank_2_4_16":old,"counterfactual_rank":nr,"rank_improvement":old-nr if nr else None})
  abl.sort(key=lambda x:-(x["rank_improvement"] if x["rank_improvement"] is not None else -10**9))
  records.append({"record_id":rid,"candidate_id":best["candidate_id"],"best_internal_anchor_similarity_mean":best["internal_anchor_similarity_mean"],"active_component_diagnostics":comps,"single_component_counterfactuals":abl})
 summary={"schema":"synbiocrow.v24.counterfactual-ablation.v1","version":"2.4.23","records":records,"development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),"method":"OLS residualization of one persisted feature from frozen coverage_adjusted_score; diagnostic only","ranking_policy_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"counterfactual_ablation_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
