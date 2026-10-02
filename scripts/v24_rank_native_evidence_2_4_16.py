#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from synbiocrow.v24.native_discrimination_2_4_16 import (
    candidate_native_features,load_enriched_rows,merge_and_rank,score_diversity,DEFAULT_WEIGHTS
)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",required=True)
    ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--enriched-rows")
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    man=json.loads(Path(a.split_manifest).read_text())
    dev=[r for r in man["records"] if r["split"]=="development"]
    sealed=[r["record_id"] for r in man["records"] if r["split"]!="development"]

    native=[]
    target_counts={}
    for r in dev:
        p=Path(a.input_dir)/(r["record_id"]+".json")
        if not p.is_file(): raise FileNotFoundError(p)
        obj=json.loads(p.read_text())
        if obj.get("split")!="development": raise ValueError("non-development artifact refused")
        rows=candidate_native_features(p)
        native.extend(rows)
        target_counts[r["record_id"]]=len(rows)

    enriched=load_enriched_rows(a.enriched_rows)
    ranked=merge_and_rank(native,enriched,DEFAULT_WEIGHTS)
    diversity=score_diversity(ranked)

    (out/"native_feature_rows.json").write_text(json.dumps(native,indent=2,sort_keys=True)+"\n")
    (out/"native_enriched_ranked_routes.json").write_text(json.dumps(ranked,indent=2,sort_keys=True)+"\n")
    (out/"ranking_policy_2_4_16.json").write_text(json.dumps({
      "schema":"synbiocrow.v24.native-ranking-policy.v1",
      "version":"2.4.16",
      "weights":DEFAULT_WEIGHTS,
      "fit_performed":False,
      "labels_used":False,
      "missing_evidence_policy":"missing_is_missing; observed-component normalization plus coverage ceiling",
      "generation_invoked":False,
      "validation_truth_accessed":False,
      "evaluation_truth_accessed":False,
      "rhea_semantics":"participant-set context only unless explicit exact reaction contract exists",
      "uniprot_semantics":"EC-linked reviewed proteins are context/family evidence only",
    },indent=2,sort_keys=True)+"\n")

    cols=["record_id","target_name","route_id","rank","coverage_adjusted_score","raw_score",
          "component_coverage","route_length","step_feasibility_mean","step_feasibility_min",
          "filter_score_mean","filter_score_min","precedent_total","precedent_step_fraction",
          "rule_coverage_fraction","template_metadata_fraction","reaction_domain_fraction",
          "reaction_type_fraction","rhea_connectivity_fraction","ec_context_fraction",
          "reviewed_ec_context_fraction"]
    with (out/"native_enriched_ranked_routes.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
        for x in ranked:w.writerow({k:x.get(k) for k in cols})

    summary={
      "schema":"synbiocrow.v24.native-discrimination-run.v1",
      "version":"2.4.16",
      "development_record_ids":[r["record_id"] for r in dev],
      "sealed_nondevelopment_record_ids":sealed,
      "candidate_count":len(ranked),
      "candidate_count_by_record":target_counts,
      "score_diversity":diversity,
      "external_enrichment_rows_loaded":len(enriched),
      "generation_invoked":False,
      "validation_truth_accessed":False,
      "evaluation_truth_accessed":False,
      "tuning_performed":False,
      "labels_used":False,
    }
    (out/"native_discrimination_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
