from __future__ import annotations

import argparse, json, hashlib
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--normalized-benchmark",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    src=Path(args.normalized_benchmark)
    payload=json.loads(src.read_text(encoding="utf-8"))
    targets=[]
    for rec in payload.get("records",[]):
        if rec.get("split")!="development":
            continue
        if not rec.get("target_smiles"):
            continue
        targets.append({
            "target_id":rec["pathway_id"],
            "target_name":rec["target_name"],
            "target_smiles":rec["target_smiles"],
            "chemical_class":"literature_development",
            "sink_smiles":list(rec.get("chassis",{}).get("source_metabolites") or []),
            "chassis":rec.get("chassis",{}).get("organism"),
            "applicable_backends":["doranet","retrobiocat2","retropath_standalone"],
            "notes":"Truth-stripped development input derived from Galaxy-SynBioCAD Supplementary Dataset 2."
        })

    out={
        "schema":"synbiocrow.literature_prediction_panel.v1",
        "panel_id":"galaxy_literature_development_truth_stripped",
        "source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
        "truth_accessed_for_panel_construction":True,
        "truth_fields_in_output":False,
        "targets":targets,
    }
    Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "target_count":len(targets),
        "target_ids":[x["target_id"] for x in targets],
        "truth_fields_in_output":False,
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
