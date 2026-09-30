from __future__ import annotations

import argparse, importlib, json, time
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdChemReactions, DataStructs
from rdkit.Chem import AllChem

def canon(s):
    m=Chem.MolFromSmiles(s)
    if m is None:
        return None
    Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m)

def fp_sim(a,b):
    ma=Chem.MolFromSmiles(a); mb=Chem.MolFromSmiles(b)
    if ma is None or mb is None:
        return None
    fa=AllChem.GetMorganFingerprintAsBitVect(ma,2,nBits=2048)
    fb=AllChem.GetMorganFingerprintAsBitVect(mb,2,nBits=2048)
    return float(DataStructs.TanimotoSimilarity(fa,fb))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--ruleset",default="JN1224MIN")
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    enz=importlib.import_module("doranet.modules.enzymatic.generate_network")
    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)

    precursor_s=canon(args.precursor); target_s=canon(args.target)
    precursor=Chem.MolFromSmiles(precursor_s)
    target=Chem.MolFromSmiles(target_s)
    if precursor is None or target is None:
        raise ValueError("Invalid precursor or target")

    rules_path=Path(enz.AVAILABLE_RULESETS[args.ruleset])
    df=pd.read_csv(rules_path,sep="\t")
    cofactors=getattr(enz,"cofactors_dict",{})

    exact=[]
    ranked=[]
    attempted=0
    skipped_multi_any=0
    parse_errors=0
    t0=time.time()

    for idx,row in df.iterrows():
        smarts=str(row["SMARTS"])
        reactant_types=str(row.get("Reactants","")).split(";")
        try:
            rxn=rdChemReactions.ReactionFromSmarts(smarts)
            if rxn is None:
                parse_errors += 1
                continue
        except Exception:
            parse_errors += 1
            continue

        # Identify slots the PKS precursor can occupy.
        precursor_slots=[]
        for i in range(rxn.GetNumReactantTemplates()):
            try:
                if precursor.HasSubstructMatch(rxn.GetReactantTemplate(i)):
                    precursor_slots.append(i)
            except Exception:
                pass
        if not precursor_slots:
            continue

        # Avoid open-ended bimolecular searches. For a direct one-step bridge,
        # every remaining slot must be a named DORAnet cofactor/helper.
        for pslot in precursor_slots:
            reactants=[]
            valid=True
            any_other=0
            for i in range(rxn.GetNumReactantTemplates()):
                if i==pslot:
                    reactants.append(precursor)
                    continue
                rtype=reactant_types[i] if i < len(reactant_types) else ""
                if rtype=="Any":
                    any_other += 1
                    valid=False
                    break
                smi=cofactors.get(rtype)
                if not smi:
                    valid=False
                    break
                m=Chem.MolFromSmiles(smi)
                if m is None:
                    valid=False
                    break
                reactants.append(m)

            if not valid:
                if any_other:
                    skipped_multi_any += 1
                continue

            attempted += 1
            try:
                outcomes=rxn.RunReactants(tuple(reactants))
            except Exception:
                continue

            for outcome in outcomes:
                for prod in outcome:
                    try:
                        Chem.SanitizeMol(prod)
                        ps=canon(Chem.MolToSmiles(prod))
                    except Exception:
                        continue
                    if not ps:
                        continue
                    sim=fp_sim(ps,target_s)
                    rec={
                        "rule_name":str(row.get("Name",f"rule_{idx}")),
                        "rule_index":int(idx),
                        "precursor_slot":int(pslot),
                        "product_smiles":ps,
                        "similarity_2d":sim,
                        "reactant_types":reactant_types,
                    }
                    ranked.append(rec)
                    if ps==target_s:
                        exact.append(rec)

    ranked=sorted(ranked,key=lambda r:(r["similarity_2d"] if r["similarity_2d"] is not None else -1),reverse=True)
    result={
        "schema":"synbiocrow.biopks_direct_one_step_screen.v1",
        "ruleset":args.ruleset,
        "target_name":args.target_name,
        "precursor":precursor_s,
        "target":target_s,
        "rules_total":len(df),
        "attempted_rule_slot_applications":attempted,
        "skipped_open_ended_multi_any":skipped_multi_any,
        "parse_errors":parse_errors,
        "unique_generated_products":len({r["product_smiles"] for r in ranked}),
        "exact_target_hits":exact,
        "exact_target_hit_count":len(exact),
        "top_products":ranked[:50],
        "elapsed_seconds":time.time()-t0,
        "status":"EXACT_HIT" if exact else "NO_EXACT_ONE_STEP_HIT",
    }
    out=outdir/f"{args.target_name}.direct_one_step.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "rules_total":result["rules_total"],
        "attempted":attempted,
        "products":result["unique_generated_products"],
        "exact_hits":result["exact_target_hit_count"],
        "elapsed_seconds":result["elapsed_seconds"],
        "best_similarity": ranked[0]["similarity_2d"] if ranked else None,
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
