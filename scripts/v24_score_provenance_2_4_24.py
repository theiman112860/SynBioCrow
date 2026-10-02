#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.score_provenance_2_4_24 import provenance
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ranked",required=True);ap.add_argument("--audit",required=True);ap.add_argument("--decomposition",required=True);ap.add_argument("--counterfactual",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);ranked=json.loads(Path(a.ranked).read_text());aud=json.loads(Path(a.audit).read_text());dec=json.loads(Path(a.decomposition).read_text());cf=json.loads(Path(a.counterfactual).read_text());man=json.loads(Path(a.split_manifest).read_text())
 ids={r["record_id"] for r in dec["records"] if r["failure_mode"]=="RANKING_LIMITED"};rby={};[rby.setdefault(r["record_id"],[]).append(r) for r in ranked];aby={r["record_id"]:r["candidate_audit"] for r in aud}
 records=[]
 for rid in sorted(ids):
  best=max(aby[rid],key=lambda x:x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1);records.append({"record_id":rid,"candidate_id":best["candidate_id"],**provenance(rby[rid],"candidate:"+best["candidate_id"])})
 summary={"schema":"synbiocrow.v24.score-provenance.v1","version":"2.4.24","records":records,"counterfactual_source_version":cf["version"],"ranking_policy_changed":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"score_provenance_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
