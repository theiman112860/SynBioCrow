from __future__ import annotations

import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path

from rdkit import Chem

def split_structures(value):
    if value is None:
        return []
    s=str(value).strip()
    if not s:
        return []
    if "_InChI=" in s:
        parts=s.split("_InChI=")
        out=[parts[0]]
        out.extend("InChI="+p for p in parts[1:])
        return [x.strip() for x in out if x.strip()]
    return [s]

def inchi_to_smiles(inchi):
    if not inchi:
        return None
    m=Chem.MolFromInchi(str(inchi),sanitize=True,removeHs=True)
    if m is None:
        return None
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=True)

def split_field(value, sep=";"):
    if value is None:
        return []
    return [x.strip() for x in str(value).split(sep) if x and x.strip()]

def stable_dev_ids(pathway_ids,n=12):
    ranked=sorted(pathway_ids,key=lambda x:hashlib.sha256(x.encode()).hexdigest())
    return set(ranked[:n])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw-json",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--development-count",type=int,default=12)
    args=ap.parse_args()

    raw=json.loads(Path(args.raw_json).read_text())
    pathway_rows=raw["sheets"]["literature_pathway"]
    matching_rows=raw["sheets"].get("literature_matching_score",[])

    by_pid=defaultdict(list)
    for row in pathway_rows:
        by_pid[str(row["pathway_lit_ID"]).strip()].append(row)

    match_by_pid={}
    for row in matching_rows:
        pid=str(row.get("pathway_lit_ID","")).strip()
        if pid:
            match_by_pid[pid]=row

    dev_ids=stable_dev_ids(list(by_pid),min(args.development_count,len(by_pid)))
    records=[]
    errors=[]
    converted_structures=0
    total_structures=0

    for pid in sorted(by_pid,key=lambda x:int(re.search(r"(\d+)$",x).group(1)) if re.search(r"(\d+)$",x) else x):
        rows=sorted(by_pid[pid],key=lambda r:int(r["step"]))
        first=rows[0]
        target_inchi=str(first["target_structure"]).strip()
        target_smiles=inchi_to_smiles(target_inchi)
        total_structures += 1
        if target_smiles:
            converted_structures += 1
        else:
            errors.append({"pathway_id":pid,"step":None,"field":"target","structure":target_inchi})

        produced=set()
        consumed=set()
        converted={}
        rxns=[]

        for row in rows:
            subs_inchi=split_structures(row.get("substrate_structure"))
            prod_inchi=split_structures(row.get("product_structure"))
            subs_smiles=[]
            prod_smiles=[]
            for x in subs_inchi:
                total_structures += 1
                smi=inchi_to_smiles(x)
                if smi: converted_structures += 1
                else: errors.append({"pathway_id":pid,"step":row["step"],"field":"substrate","structure":x})
                converted[x]=smi
                if smi: subs_smiles.append(smi)
            for x in prod_inchi:
                total_structures += 1
                smi=inchi_to_smiles(x)
                if smi: converted_structures += 1
                else: errors.append({"pathway_id":pid,"step":row["step"],"field":"product","structure":x})
                converted[x]=smi
                if smi: prod_smiles.append(smi)

            consumed.update(subs_smiles)
            produced.update(prod_smiles)

            reaction_smiles=".".join(sorted(subs_smiles))+">>"+ ".".join(sorted(prod_smiles))
            rxns.append({
                "galaxy_step":int(row["step"]),
                "reaction_smiles":reaction_smiles,
                "substrates":split_field(row.get("substrate_name")),
                "products":split_field(row.get("product_name")),
                "substrate_inchi":subs_inchi,
                "product_inchi":prod_inchi,
                "substrate_smiles":subs_smiles,
                "product_smiles":prod_smiles,
                "ec_numbers":split_field(row.get("EC_number")),
                "enzymes":[x for x in [row.get("enzyme_identifier"),row.get("enzyme_name")] if x not in (None,"")],
                "uniprot":split_field(row.get("uniprot")),
                "evidence_note":str(row.get("comments") or "").strip(),
            })

        # Galaxy step 1 is closest to target, so reverse for biosynthetic forward order.
        rxns=sorted(rxns,key=lambda r:r["galaxy_step"],reverse=True)
        for i,rxn in enumerate(rxns,1):
            rxn["order"]=i

        roots=sorted(consumed-produced)
        match=match_by_pid.get(pid,{})
        records.append({
            "pathway_id":pid,
            "split":"development" if pid in dev_ids else "benchmark",
            "target_name":str(first["target_name"]).strip(),
            "target_inchi":target_inchi,
            "target_smiles":target_smiles,
            "chassis":{
                "organism":str(first["chassis"]).strip(),
                "strain":"",
                "source_metabolites":roots,
            },
            "literature":{
                "doi":str(first["reference"]).strip(),
                "pmid":"",
                "citation":"",
                "url":"https://doi.org/"+str(first["reference"]).strip(),
            },
            "experimentally_demonstrated":True,
            "reactions":rxns,
            "galaxy_reference":{
                "retropath_pathways_id":str(match.get("RetroPath_pathways_ID") or "").strip(),
                "matching_score":match.get("matching_score"),
                "pathway_similarity":match.get("pathway_similarity"),
            },
            "notes":"Normalized from Galaxy-SynBioCAD Supplementary Dataset 2; Galaxy step numbers preserved as galaxy_step.",
        })

    payload={
        "schema":"synbiocrow.literature_pathway_benchmark.v1",
        "benchmark_id":"synbiocrow_2_3_galaxy_literature_pathways",
        "source":{
            "doi":"10.1038/s41467-022-32661-x",
            "supplement":"Supplementary Dataset 2",
            "source_sha256":raw.get("source",{}).get("sha256"),
        },
        "truth_accessed":True,
        "development_policy":{
            "method":"stable SHA256 ordering of pathway_id",
            "development_count":len(dev_ids),
            "development_ids":sorted(dev_ids),
            "note":"Split selection is independent of SynBioCrow prediction performance."
        },
        "records":records,
    }

    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"galaxy_literature_benchmark_normalized.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    report={
        "schema":"synbiocrow.galaxy_normalization_report.v1",
        "pathway_count":len(records),
        "target_count":len({r["target_name"] for r in records}),
        "reaction_count":sum(len(r["reactions"]) for r in records),
        "development_count":sum(r["split"]=="development" for r in records),
        "benchmark_count":sum(r["split"]=="benchmark" for r in records),
        "inchi_structure_instances":total_structures,
        "inchi_to_smiles_successes":converted_structures,
        "conversion_failures":len(errors),
        "conversion_failure_examples":errors[:25],
        "chassis_counts":{},
        "path_length_counts":{},
        "truth_accessed":True,
        "prediction_scoring_performed":False,
    }
    for r in records:
        org=r["chassis"]["organism"]
        report["chassis_counts"][org]=report["chassis_counts"].get(org,0)+1
        n=str(len(r["reactions"]))
        report["path_length_counts"][n]=report["path_length_counts"].get(n,0)+1

    (out/"galaxy_literature_normalization_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
