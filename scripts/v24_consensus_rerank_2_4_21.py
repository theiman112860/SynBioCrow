#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.consensus_rerank_2_4_21 import rerank_all,CONSENSUS_FEATURES

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--attribution",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());audit=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());attr=json.loads(Path(a.attribution).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 ranking_ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"}
 if ranking_ids != set(attr["ranking_limited_record_ids"]):raise ValueError("ranking-limited scope mismatch")
 # Guard: every selected feature must have strictly positive attribution on both targets.
 amap={r["record_id"]:{x["feature"]:x["spearman_vs_internal_anchor_similarity"] for x in r["feature_attribution"]} for r in attr["records"]}
 for f in CONSENSUS_FEATURES:
  vals=[amap[rid].get(f) for rid in sorted(ranking_ids)]
  if any(v is None or v<=0 for v in vals):raise ValueError(f"consensus feature not positive on all ranking-limited targets: {f} {vals}")
 reranked=rerank_all(ranked,ranking_ids)
 aby={r["record_id"]:{x["candidate_id"]:x for x in r["candidate_audit"]} for r in audit}
 evaluations=[]
 for rid in sorted(ranking_ids):
  rows=[x for x in reranked if x["record_id"]==rid]; ar=aby[rid]
  best=max(ar.values(),key=lambda x:(x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1))
  target_route="candidate:"+best["candidate_id"]
  old_rank=best["rank_2_4_16"]
  new=next((x["rank_2_4_21"] for x in rows if x["route_id"]==target_route),None)
  evaluations.append({"record_id":rid,"best_internal_anchor_candidate":best["candidate_id"],"best_internal_anchor_similarity_mean":best["internal_anchor_similarity_mean"],"rank_2_4_16":old_rank,"rank_2_4_21":new,"rank_improvement":(old_rank-new) if old_rank is not None and new is not None else None})
 summary={"schema":"synbiocrow.v24.consensus-positive-rerank.v1","version":"2.4.21","consensus_features":list(CONSENSUS_FEATURES),"weighting":"equal weight on within-target feature percentiles; no fitted numeric weights","ranking_limited_record_ids":sorted(ranking_ids),"generation_repair_record_ids":sorted({r["record_id"] for r in dec["records"] if "GENERATION" in r["failure_mode"]}),"evaluations":evaluations,"development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),"validation_truth_accessed":False,"evaluation_truth_accessed":False,"generation_invoked":False,"validation_ranking_not_run":True}
 (out/"consensus_reranked_routes.json").write_text(json.dumps(reranked,indent=2,sort_keys=True)+"\n")
 (out/"consensus_rerank_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
