from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
from rdkit import Chem

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("panel")
    ap.add_argument("--expected-target-count",type=int,default=24)
    ap.add_argument("--allow-subset",action="store_true",
                    help="Validate a focused subset without requiring 6 classes x 4 targets")
    args=ap.parse_args()
    path=Path(args.panel)
    payload=json.loads(path.read_text())
    targets=payload["targets"]
    assert len(targets)==args.expected_target_count, (
        len(targets), args.expected_target_count
    )
    ids=[x["target_id"] for x in targets]
    assert len(ids)==len(set(ids)), "duplicate target_id"
    classes=Counter(x["chemical_class"] for x in targets)
    if not args.allow_subset:
        assert len(classes)==6, classes
        assert set(classes.values())=={4}, classes
    canonical={}
    for row in targets:
        mol=Chem.MolFromSmiles(row["target_smiles"])
        assert mol is not None, row["target_id"]
        can=Chem.MolToSmiles(mol,isomericSmiles=True)
        assert can not in canonical, f"duplicate structure: {row['target_id']} and {canonical[can]}"
        canonical[can]=row["target_id"]
        target_can=Chem.MolToSmiles(mol,isomericSmiles=True)
        for smi in row.get("sink_smiles",[]):
            sink_mol=Chem.MolFromSmiles(smi)
            assert sink_mol is not None, (row["target_id"],smi)
            sink_can=Chem.MolToSmiles(sink_mol,isomericSmiles=True)
            assert sink_can != target_can, f"target appears in sink set: {row['target_id']}"
    pks=[x for x in targets if "biopks_retrotide" in x.get("applicable_backends",[])]
    assert all(x["chemical_class"]=="polyketide_derived" for x in pks)
    report={
        "status":"PASS","panel_id":payload.get("panel_id"),"target_count":len(targets),
        "class_counts":dict(sorted(classes.items())),"unique_structures":len(canonical),
        "biopks_retrotide_applicable_targets":len(pks),
        "panel_sha256":sha256(path),
        "validation_mode":"FOCUSED_SUBSET" if args.allow_subset else "FULL_24_TARGET_PANEL",
        "expected_target_count":args.expected_target_count,
    }
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
