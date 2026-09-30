from __future__ import annotations

import argparse, importlib, json, time
from pathlib import Path
from collections import Counter

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdChemReactions

def canon_mol(smiles):
    m=Chem.MolFromSmiles(smiles)
    if m is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m),m

def atom_bounds(precursor,target,extra=1):
    def counts(m):
        return Counter(a.GetSymbol() for a in m.GetAtoms())
    _,pm=canon_mol(precursor); _,tm=canon_mol(target)
    pc=counts(pm); tc=counts(tm)
    keys=set(pc)|set(tc)
    return {k:max(pc.get(k,0),tc.get(k,0))+extra for k in sorted(keys)}

def bidirectional_rules(src_tsv,precursor_mol,target_mol,out_tsv):
    df=pd.read_csv(src_tsv,sep="\t")
    rows=[]
    for idx,row in df.iterrows():
        smarts=str(row["SMARTS"])
        try:
            rxn=rdChemReactions.ReactionFromSmarts(smarts)
            if rxn is None:
                continue
            rslots=[]
            pslots=[]
            for i in range(rxn.GetNumReactantTemplates()):
                q=rxn.GetReactantTemplate(i)
                try:
                    if precursor_mol.HasSubstructMatch(q):
                        rslots.append(i)
                except Exception:
                    pass
            if not rslots:
                continue
            for i in range(rxn.GetNumProductTemplates()):
                q=rxn.GetProductTemplate(i)
                try:
                    if target_mol.HasSubstructMatch(q):
                        pslots.append(i)
                except Exception:
                    pass
            if not pslots:
                continue
            rec=row.to_dict()
            rec["SynBioCrow_precursor_match_slots"]=",".join(map(str,rslots))
            rec["SynBioCrow_target_product_match_slots"]=",".join(map(str,pslots))
            rows.append(rec)
        except Exception:
            continue
    out=pd.DataFrame(rows)
    out.to_csv(out_tsv,sep="\t",index=False)
    return len(df),len(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--base-ruleset",default="JN1224MIN")
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    import doranet
    enz_mod=importlib.import_module("doranet.modules.enzymatic.generate_network")
    import doranet.modules.post_processing as post_processing

    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)
    precursor,pm=canon_mol(args.precursor)
    target,tm=canon_mol(args.target)
    bounds=atom_bounds(precursor,target,1)
    src=Path(enz_mod.AVAILABLE_RULESETS[args.base_ruleset])
    filtered=outdir/f"{args.target_name}.{args.base_ruleset}.bidirectional.tsv"
    total,n=bidirectional_rules(src,pm,tm,filtered)

    result={
        "schema":"synbiocrow.biopks_bidirectional_rules.v1",
        "doranet_version":getattr(doranet,"__version__","UNKNOWN"),
        "base_ruleset":args.base_ruleset,
        "total_base_rules":total,
        "bidirectional_compatible_rules":n,
        "precursor":precursor,
        "target":target,
        "max_atoms":bounds,
        "timings":{},
    }

    print("[BIDIR] RULES",total,"->",n,flush=True)
    if n==0:
        result["status"]="NO_ONE_STEP_COMPATIBLE_RULE"
        report=outdir/f"{args.target_name}.bidirectional.json"
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0

    ruleset=f"SYNBIOCROW_BIDIR_{args.target_name}"
    enz_mod.AVAILABLE_RULESETS[ruleset]=filtered
    job=f"{args.target_name}_BIDIR"

    t=time.time()
    network=enz_mod.generate_network(
        job_name=job,starters={precursor},gen=1,direction="forward",
        max_atoms=bounds,targets={target},ruleset=ruleset
    )
    result["timings"]["network_seconds"]=time.time()-t
    result["network_molecule_count"]=len(network.mols)
    result["network_reaction_count"]=len(network.rxns)

    def c(s):
        m=Chem.MolFromSmiles(s)
        if m is None: return None
        Chem.RemoveStereochemistry(m)
        return Chem.MolToSmiles(m)

    result["target_in_network"]=any(c(x.uid)==target for x in network.mols)

    if result["target_in_network"]:
        t=time.time()
        post_processing.one_step(
            networks={network},total_generations=1,starters={precursor},target=target,
            job_name=job,search_depth=1,max_num_rxns=1,min_rxn_atom_economy=0,num_process=1
        )
        result["timings"]["postprocess_seconds"]=time.time()-t
        pf=Path(f"{job}_pathways.txt")
        result["pathways_file_exists"]=pf.is_file()
        result["pathways_file_bytes"]=pf.stat().st_size if pf.is_file() else 0
    else:
        result["pathways_file_exists"]=False
        result["pathways_file_bytes"]=0

    result["status"]="PASS"
    report=outdir/f"{args.target_name}.bidirectional.json"
    report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
