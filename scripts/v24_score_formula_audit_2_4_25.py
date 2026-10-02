#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.score_formula_audit_2_4_25 import verify_exact,rerank_weight_coverage
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"};ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"}
 rby={};[rby.setdefault(r["record_id"],[]).append(r) for r in ranked];aby={r["record_id"]:r["candidate_audit"] for r in aud}
 records=[];all_exact=True
 for rid in sorted(ids):
  best=max(aby[rid],key=lambda x:x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1)
  target="candidate:"+best["candidate_id"]; rows=rby[rid]
  t=next(x for x in rows if x["route_id"]==target); ver=verify_exact(t);all_exact=all_exact and ver["raw_match"] and ver["adjusted_match"]
  diag=rerank_weight_coverage(rows); new=next(x["diagnostic_weight_coverage_rank"] for x in diag if x["route_id"]==target)
  records.append({"record_id":rid,"candidate_id":best["candidate_id"],"rank_2_4_16":int(t["rank"]),"diagnostic_weight_coverage_rank":new,"rank_change":int(t["rank"])-new,"exact_formula_verification":ver})
 summary={"schema":"synbiocrow.v24.score-formula-audit.v1","version":"2.4.25","formula_source":"synbiocrow/v24/native_discrimination_2_4_16.py","exact_reconstruction_pass":all_exact,"records":records,"coverage_diagnostic":"count coverage = observed_component_count / 13; alternative shown only as diagnostic: observed_abs_weight / total_abs_weight","production_ranking_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False,"development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed)}
 (out/"score_formula_audit_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
 if not all_exact:raise RuntimeError("failed to reproduce frozen 2.4.16 score exactly")
if __name__=="__main__":main()
