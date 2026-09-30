from __future__ import annotations

import argparse, importlib, json, math, time
from pathlib import Path

import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdChemReactions, AllChem

def canon(s):
    m=Chem.MolFromSmiles(s)
    if m is None:
        return None
    Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m)

def sim2d(a,b):
    ma=Chem.MolFromSmiles(a); mb=Chem.MolFromSmiles(b)
    if ma is None or mb is None:
        return -1.0
    fa=AllChem.GetMorganFingerprintAsBitVect(ma,2,nBits=2048)
    fb=AllChem.GetMorganFingerprintAsBitVect(mb,2,nBits=2048)
    return float(DataStructs.TanimotoSimilarity(fa,fb))

def prepare_rules(df, cofactors):
    prepared=[]
    for idx,row in df.iterrows():
        try:
            rxn=rdChemReactions.ReactionFromSmarts(str(row["SMARTS"]))
            if rxn is None:
                continue
        except Exception:
            continue
        rtypes=str(row.get("Reactants","")).split(";")
        prepared.append((int(idx),str(row.get("Name",f"rule_{idx}")),rxn,rtypes))
    return prepared

def expand_one(smiles, prepared, cofactors, target, max_products_per_rule=32):
    mol=Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    out=[]
    for idx,name,rxn,rtypes in prepared:
        slots=[]
        for i in range(rxn.GetNumReactantTemplates()):
            try:
                if mol.HasSubstructMatch(rxn.GetReactantTemplate(i)):
                    slots.append(i)
            except Exception:
                pass
        for slot in slots:
            reactants=[]
            valid=True
            for i in range(rxn.GetNumReactantTemplates()):
                if i==slot:
                    reactants.append(mol)
                    continue
                rtype=rtypes[i] if i < len(rtypes) else ""
                if rtype=="Any":
                    valid=False
                    break
                cs=cofactors.get(rtype)
                if not cs:
                    valid=False
                    break
                cm=Chem.MolFromSmiles(cs)
                if cm is None:
                    valid=False
                    break
                reactants.append(cm)
            if not valid:
                continue
            try:
                outcomes=rxn.RunReactants(tuple(reactants))
            except Exception:
                continue
            kept=0
            for tup in outcomes:
                for p in tup:
                    try:
                        Chem.SanitizeMol(p)
                        ps=canon(Chem.MolToSmiles(p))
                    except Exception:
                        continue
                    if not ps:
                        continue
                    out.append({
                        "product":ps,
                        "rule_index":idx,
                        "rule_name":name,
                        "similarity":sim2d(ps,target),
                    })
                    kept+=1
                    if kept>=max_products_per_rule:
                        break
                if kept>=max_products_per_rule:
                    break
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--ruleset",default="JN1224MIN")
    ap.add_argument("--max-depth",type=int,default=3)
    ap.add_argument("--beam-width",type=int,default=80)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    enz=importlib.import_module("doranet.modules.enzymatic.generate_network")
    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)
    precursor=canon(args.precursor); target=canon(args.target)
    if not precursor or not target:
        raise ValueError("Invalid precursor or target")

    df=pd.read_csv(Path(enz.AVAILABLE_RULESETS[args.ruleset]),sep="\t")
    cofactors=getattr(enz,"cofactors_dict",{})
    prepared=prepare_rules(df,cofactors)

    frontier=[{"smiles":precursor,"score":sim2d(precursor,target),"path":[]}]
    seen={precursor}
    best=frontier[0]
    exact=None
    levels=[]
    t0=time.time()

    for depth in range(1,args.max_depth+1):
        candidates={}
        expanded_nodes=0
        generated=0

        for node in frontier:
            expanded_nodes+=1
            products=expand_one(node["smiles"],prepared,cofactors,target)
            generated+=len(products)
            for rec in products:
                ps=rec["product"]
                path=node["path"]+[{
                    "from":node["smiles"],
                    "to":ps,
                    "rule_index":rec["rule_index"],
                    "rule_name":rec["rule_name"],
                    "similarity":rec["similarity"],
                }]
                if ps==target:
                    exact={"depth":depth,"path":path}
                    break
                if ps in seen:
                    continue
                old=candidates.get(ps)
                cand={"smiles":ps,"score":rec["similarity"],"path":path}
                if old is None or cand["score"]>old["score"]:
                    candidates[ps]=cand
                if cand["score"]>best["score"]:
                    best=cand
            if exact:
                break
        if exact:
            levels.append({
                "depth":depth,"expanded_nodes":expanded_nodes,
                "generated_products":generated,"unique_candidates":len(candidates),
                "exact_hit":True
            })
            break

        ranked=sorted(candidates.values(),key=lambda x:x["score"],reverse=True)
        frontier=ranked[:args.beam_width]
        seen.update(x["smiles"] for x in frontier)
        levels.append({
            "depth":depth,"expanded_nodes":expanded_nodes,
            "generated_products":generated,"unique_candidates":len(candidates),
            "beam_size":len(frontier),
            "best_similarity":frontier[0]["score"] if frontier else None,
            "exact_hit":False,
        })
        if not frontier:
            break

    result={
        "schema":"synbiocrow.biopks_direct_beam.v1",
        "target_name":args.target_name,
        "ruleset":args.ruleset,
        "precursor":precursor,
        "target":target,
        "max_depth":args.max_depth,
        "beam_width":args.beam_width,
        "levels":levels,
        "exact_hit":exact,
        "exact_hit_found":exact is not None,
        "best_similarity":best["score"],
        "best_path":best["path"],
        "elapsed_seconds":time.time()-t0,
        "status":"EXACT_HIT" if exact else "NO_EXACT_HIT_WITHIN_BOUNDS",
    }
    out=outdir/f"{args.target_name}.direct_beam.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "exact_hit_found":result["exact_hit_found"],
        "best_similarity":result["best_similarity"],
        "depths_completed":len(levels),
        "elapsed_seconds":result["elapsed_seconds"],
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
