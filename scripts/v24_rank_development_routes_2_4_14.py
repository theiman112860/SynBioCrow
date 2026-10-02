#!/usr/bin/env python3
"""Build SynBioCrow 2.4.14 evidence-aware rankings from persisted development artifacts."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

from synbiocrow.v24.discrimination_2_4_14 import (
    DEFAULT_WEIGHTS,
    extract_development_features,
    fit_development_weights,
    rank_feature_rows,
    ranked_to_dicts,
    rows_to_dicts,
)

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",required=True)
    ap.add_argument("--split-manifest",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--labels-json")
    a=ap.parse_args()

    inp=Path(a.input_dir)
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(Path(a.split_manifest).read_text())
    dev=[r for r in manifest["records"] if r["split"]=="development"]
    sealed=[r["record_id"] for r in manifest["records"] if r["split"]!="development"]

    all_rows=[]
    artifact_rows=[]
    for rec in dev:
        p=inp/f'{rec["record_id"]}.json'
        if not p.is_file():
            raise FileNotFoundError(f"missing development artifact: {p}")
        obj=json.loads(p.read_text())
        if obj.get("record_id")!=rec["record_id"] or obj.get("split")!="development":
            raise ValueError(f"development artifact identity/split mismatch: {p}")
        rows=extract_development_features(p)
        artifact_rows.append({
            "record_id":rec["record_id"],
            "target_name":rec["target_name"],
            "artifact":str(p),
            "artifact_sha256":sha256_file(p),
            "feature_route_count":len(rows),
        })
        all_rows.extend(rows)

    if not all_rows:
        raise RuntimeError("no persisted candidate pathways or strict routes available for discrimination")

    weights=dict(DEFAULT_WEIGHTS)
    calibration=None
    if a.labels_json:
        labels_obj=json.loads(Path(a.labels_json).read_text())
        if labels_obj.get("split")!="development":
            raise ValueError("labels-json must declare split='development'")
        labels={str(k):float(v) for k,v in (labels_obj.get("labels") or {}).items()}
        calibration=fit_development_weights(all_rows,labels)
        weights=dict(calibration["weights"])

    ranked=rank_feature_rows(all_rows,weights)

    (out/"feature_rows.json").write_text(json.dumps(rows_to_dicts(all_rows),indent=2,sort_keys=True)+"\n")
    (out/"ranked_routes.json").write_text(json.dumps(ranked_to_dicts(ranked),indent=2,sort_keys=True)+"\n")
    with (out/"ranked_routes.csv").open("w",newline="",encoding="utf-8") as fh:
        cols=["record_id","target_name","route_id","rank","coverage_adjusted_score",
              "raw_observed_score","evidence_coverage","observed_feature_count",
              "route_length","engine_count"]
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for r in ranked:
            d=r.__dict__
            w.writerow({k:d.get(k) for k in cols})

    policy={
        "schema":"synbiocrow.v24.discrimination-policy.v1",
        "version":"2.4.14",
        "policy_id":"2.4.14-evidence-aware-default" if calibration is None else "2.4.14-development-calibrated",
        "weights":weights,
        "calibration":calibration,
        "fit_split":"development" if calibration is not None else None,
        "missing_evidence_policy":"missing_is_missing; observed-feature normalization plus evidence-coverage ceiling",
        "candidate_policy":"persisted_candidate_pathways_plus_strict_ensemble_routes",
        "generation_invoked":False,
        "validation_truth_accessed":False,
        "evaluation_truth_accessed":False,
        "sealed_nondevelopment_record_ids":sorted(sealed),
    }
    (out/"ranking_policy.json").write_text(json.dumps(policy,indent=2,sort_keys=True)+"\n")

    by_target={}
    for r in ranked:
        by_target.setdefault(r.record_id,0); by_target[r.record_id]+=1
    summary={
        "schema":"synbiocrow.v24.discrimination-run.v1",
        "version":"2.4.14",
        "split_manifest_sha256":manifest.get("manifest_sha256"),
        "development_record_ids":[r["record_id"] for r in dev],
        "sealed_nondevelopment_record_ids":sorted(sealed),
        "artifact_inputs":artifact_rows,
        "feature_route_count":len(all_rows),
        "ranked_route_count":len(ranked),
        "ranked_route_count_by_record":by_target,
        "policy_id":policy["policy_id"],
        "generation_invoked":False,
        "validation_truth_accessed":False,
        "evaluation_truth_accessed":False,
        "tuning_performed":calibration is not None,
    }
    (out/"discrimination_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
