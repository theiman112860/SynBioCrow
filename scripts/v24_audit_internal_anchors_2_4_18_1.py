#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from synbiocrow.v24.development_truth_2_4_17 import resolve_truth,resolve_pubchem_name
from synbiocrow.v24.internal_anchor_audit_2_4_18_1 import audit_candidate
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input-dir",required=True);ap.add_argument("--ranked-json",required=True);ap.add_argument("--truth",required=True);ap.add_argument("--split-manifest",required=True);ap.add_argument("--cache");ap.add_argument("--out-dir",required=True);a=ap.parse_args()
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);man=json.loads(Path(a.split_manifest).read_text());dev={r["record_id"] for r in man["records"] if r["split"]=="development"};sealed={r["record_id"] for r in man["records"] if r["split"]!="development"}
 cache=json.loads(Path(a.cache).read_text()) if a.cache and Path(a.cache).is_file() else {};truth=resolve_truth(json.loads(Path(a.truth).read_text()),cache)
 if "coenzyme A" not in cache:cache["coenzyme A"]=resolve_pubchem_name("coenzyme A")
 coa=cache.get("coenzyme A")
 if not coa:raise RuntimeError("could not resolve coenzyme A for carrier-aware correction")
 ranked=json.loads(Path(a.ranked_json).read_text());by={}
 for x in ranked:by.setdefault(x["record_id"],[]).append(x)
 results=[]
 for tr in truth["records"]:
  rid=tr["record_id"]
  if rid not in dev:raise ValueError("non-development truth refused")
  obj=json.loads((Path(a.input_dir)/(rid+".json")).read_text());rank={str(x["route_id"]).removeprefix("candidate:"):int(x["rank"]) for x in by.get(rid,[])}
  cs=[]
  for c in (obj.get("result") or {}).get("candidates") or []:
   q=audit_candidate(c,tr["anchors"],obj.get("target_name"),obj.get("normalized_target") or obj.get("target_smiles") or c.get("target_smiles"),coa);q["rank_2_4_16"]=rank.get(q["candidate_id"]);cs.append(q)
  cs.sort(key=lambda x:(-(x["internal_anchor_similarity_mean"] if x["internal_anchor_similarity_mean"] is not None else -1),x["rank_2_4_16"] or 10**9))
  top={}
  for k in (1,5,10,50,100):
   rr=[x for x in cs if x["rank_2_4_16"] and x["rank_2_4_16"]<=k];top[str(k)]=max((x["internal_anchor_similarity_mean"] for x in rr if x["internal_anchor_similarity_mean"] is not None),default=None)
  results.append({"record_id":rid,"target_name":obj.get("target_name"),"best_candidate":cs[0]["candidate_id"] if cs else None,"best_candidate_rank_2_4_16":cs[0]["rank_2_4_16"] if cs else None,"best_internal_anchor_similarity_mean":cs[0]["internal_anchor_similarity_mean"] if cs else None,"topk_max_internal_anchor_similarity_mean":top,"candidate_audit":cs})
 summary={"schema":"synbiocrow.v24.internal-anchor-near-miss.v2","version":"2.4.18.1","records":[{k:v for k,v in r.items() if k!="candidate_audit"} for r in results],"target_anchor_excluded_by_identity":True,"coa_carrier_adjustment":True,"development_record_ids":sorted(dev),"sealed_nondevelopment_record_ids":sorted(sealed),"ranking_tuned":False,"generation_invoked":False,"validation_truth_accessed":False,"evaluation_truth_accessed":False}
 (out/"corrected_internal_anchor_audit.json").write_text(json.dumps(results,indent=2,sort_keys=True)+"\n");(out/"corrected_internal_anchor_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");(out/"pubchem_anchor_cache.json").write_text(json.dumps(cache,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
