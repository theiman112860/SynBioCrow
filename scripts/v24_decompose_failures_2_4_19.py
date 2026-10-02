#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from synbiocrow.v24.failure_decomposition_2_4_19 import decompose
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--audit",required=True);ap.add_argument("--ranking-summary",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 audit=json.loads(Path(a.audit).read_text());rs=json.loads(Path(a.ranking_summary).read_text());man=json.loads(Path(a.split_manifest).read_text())
 dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 counts=rs["candidate_count_by_record"];rows=[decompose(r,counts[r["record_id"]]) for r in audit["records"]]
 if {x["record_id"] for x in rows}!=dev:raise ValueError("development scope mismatch")
 summary={"schema":"synbiocrow.v24.failure-decomposition.v1","version":"2.4.19","records":rows,
 "development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),
 "thresholds_are_diagnostic_not_fitted":True,"ranking_tuned":False,"generation_invoked":False,
 "validation_truth_accessed":False,"evaluation_truth_accessed":False,
 "interpretation":{"RANKING_LIMITED":"meaningful internal-anchor near miss exists but is not in top 50",
 "GENERATION_COVERAGE_LIMITED":"best near miss is below 0.45 despite appearing in top 50",
 "GENERATION_AND_RANKING_LIMITED":"best near miss is below 0.45 and below top 50",
 "CANDIDATE_PRESENT_AND_RANKED":"near miss >=0.45 and rank <=50"}}
 (out/"failure_decomposition_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
