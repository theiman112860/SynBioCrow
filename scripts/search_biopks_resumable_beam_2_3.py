from __future__ import annotations

import argparse, importlib, json, time
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

def fp(m):
    return AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=2048)

def sim_fp(m,target_fp):
    return float(DataStructs.TanimotoSimilarity(fp(m),target_fp))

def prepare_rules(df, cofactors):
    prepared=[]
    cofactor_mols={}
    for k,s in cofactors.items():
        m=Chem.MolFromSmiles(s)
        if m is not None:
            cofactor_mols[k]=m
    for idx,row in df.iterrows():
        try:
            rxn=rdChemReactions.ReactionFromSmarts(str(row["SMARTS"]))
            if rxn is None:
                continue
        except Exception:
            continue
        rtypes=str(row.get("Reactants","")).split(";")
        prepared.append((int(idx),str(row.get("Name",f"rule_{idx}")),rxn,rtypes))
    return prepared,cofactor_mols

def expand_one(smiles, prepared, cofactor_mols, target_fp, max_products_per_rule):
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
                cm=cofactor_mols.get(rtype)
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
                    pm=Chem.MolFromSmiles(ps)
                    if pm is None:
                        continue
                    out.append({
                        "product":ps,
                        "rule_index":idx,
                        "rule_name":name,
                        "similarity":sim_fp(pm,target_fp),
                    })
                    kept+=1
                    if kept>=max_products_per_rule:
                        break
                if kept>=max_products_per_rule:
                    break
    return out

def save(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--ruleset",default="JN1224MIN")
    ap.add_argument("--max-depth",type=int,default=3)
    ap.add_argument("--beam-width",type=int,default=12)
    ap.add_argument("--max-products-per-rule",type=int,default=8)
    ap.add_argument("--time-budget",type=int,default=240)
    ap.add_argument("--state-file",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    enz=importlib.import_module("doranet.modules.enzymatic.generate_network")
    precursor=canon(args.precursor); target=canon(args.target)
    if not precursor or not target:
        raise ValueError("Invalid precursor or target")
    target_m=Chem.MolFromSmiles(target)
    target_fp=fp(target_m)

    df=pd.read_csv(Path(enz.AVAILABLE_RULESETS[args.ruleset]),sep="\t")
    prepared,cofactor_mols=prepare_rules(df,getattr(enz,"cofactors_dict",{}))

    state_path=Path(args.state_file)
    if state_path.is_file():
        state=json.loads(state_path.read_text())
    else:
        start_m=Chem.MolFromSmiles(precursor)
        state={
            "schema":"synbiocrow.biopks_resumable_beam_state.v1",
            "target_name":args.target_name,
            "precursor":precursor,
            "target":target,
            "ruleset":args.ruleset,
            "max_depth":args.max_depth,
            "beam_width":args.beam_width,
            "max_products_per_rule":args.max_products_per_rule,
            "depth":1,
            "frontier":[{"smiles":precursor,"score":sim_fp(start_m,target_fp),"path":[]}],
            "node_index":0,
            "current_candidates":{},
            "seen":[precursor],
            "levels":[],
            "best":{"smiles":precursor,"score":sim_fp(start_m,target_fp),"path":[]},
            "exact_hit":None,
            "status":"RUNNING",
        }
        save(state_path,state)

    started=time.time()
    seen=set(state["seen"])

    while state["status"]=="RUNNING":
        if time.time()-started >= args.time_budget:
            state["status"]="PAUSED_BUDGET"
            save(state_path,state)
            break

        depth=state["depth"]
        if depth>args.max_depth:
            state["status"]="NO_EXACT_HIT_WITHIN_BOUNDS"
            save(state_path,state)
            break

        frontier=state["frontier"]
        if state["node_index"] >= len(frontier):
            candidates=list(state["current_candidates"].values())
            candidates=sorted(candidates,key=lambda x:x["score"],reverse=True)
            next_frontier=candidates[:args.beam_width]
            state["levels"].append({
                "depth":depth,
                "expanded_nodes":len(frontier),
                "unique_candidates":len(candidates),
                "beam_size":len(next_frontier),
                "best_similarity":next_frontier[0]["score"] if next_frontier else None,
                "exact_hit":False,
            })
            if not next_frontier:
                state["status"]="NO_EXACT_HIT_WITHIN_BOUNDS"
                save(state_path,state)
                break
            state["frontier"]=next_frontier
            for n in next_frontier:
                seen.add(n["smiles"])
            state["seen"]=sorted(seen)
            state["depth"]=depth+1
            state["node_index"]=0
            state["current_candidates"]={}
            save(state_path,state)
            continue

        node=frontier[state["node_index"]]
        products=expand_one(
            node["smiles"],prepared,cofactor_mols,target_fp,args.max_products_per_rule
        )
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
                state["exact_hit"]={"depth":depth,"path":path}
                state["status"]="EXACT_HIT"
                state["levels"].append({
                    "depth":depth,
                    "expanded_nodes":state["node_index"]+1,
                    "exact_hit":True,
                })
                save(state_path,state)
                break
            if ps in seen:
                continue
            cand={"smiles":ps,"score":rec["similarity"],"path":path}
            old=state["current_candidates"].get(ps)
            if old is None or cand["score"]>old["score"]:
                state["current_candidates"][ps]=cand
            if cand["score"]>state["best"]["score"]:
                state["best"]=cand

        if state["status"]=="EXACT_HIT":
            break

        state["node_index"] += 1
        save(state_path,state)

    result={
        "schema":"synbiocrow.biopks_resumable_direct_beam.v1",
        "target_name":args.target_name,
        "status":state["status"],
        "depth":state["depth"],
        "node_index":state["node_index"],
        "frontier_size":len(state["frontier"]),
        "levels":state["levels"],
        "exact_hit":state["exact_hit"],
        "best_similarity":state["best"]["score"],
        "best_path":state["best"]["path"],
        "state_file":str(state_path),
    }
    save(args.output,result)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
