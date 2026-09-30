from __future__ import annotations

import argparse, importlib, json, time
from pathlib import Path
from collections import Counter

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdChemReactions

def atom_bounds(precursor,target,extra=1):
    def counts(s):
        m=Chem.MolFromSmiles(s)
        if m is None:
            raise ValueError(f"Invalid SMILES: {s}")
        return Counter(a.GetSymbol() for a in m.GetAtoms())
    pc=counts(precursor); tc=counts(target)
    keys=set(pc)|set(tc)
    return {k:max(pc.get(k,0),tc.get(k,0))+extra for k in sorted(keys)}

def canon_no_stereo(s):
    m=Chem.MolFromSmiles(s)
    if m is None:
        raise ValueError(f"Invalid SMILES: {s}")
    Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m), m

def precursor_compatible_rules(src_tsv:Path, precursor_mol, out_tsv:Path):
    df=pd.read_csv(src_tsv,sep="\t")
    keep=[]
    reasons=[]
    for idx,row in df.iterrows():
        smarts=str(row["SMARTS"])
        try:
            rxn=rdChemReactions.ReactionFromSmarts(smarts)
            if rxn is None:
                continue
            matched=False
            matched_slots=[]
            for i in range(rxn.GetNumReactantTemplates()):
                templ=rxn.GetReactantTemplate(i)
                try:
                    if precursor_mol.HasSubstructMatch(templ):
                        matched=True
                        matched_slots.append(i)
                except Exception:
                    pass
            if matched:
                keep.append(idx)
                reasons.append(",".join(map(str,matched_slots)))
        except Exception:
            continue
    filtered=df.loc[keep].copy()
    filtered["SynBioCrow_precursor_match_slots"]=reasons
    filtered.to_csv(out_tsv,sep="\t",index=False)
    return len(df),len(filtered)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--base-ruleset",default="JN1224MIN")
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    enz_mod=importlib.import_module("doranet.modules.enzymatic.generate_network")
    import doranet
    import doranet.modules.post_processing as post_processing

    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)
    precursor,precursor_mol=canon_no_stereo(args.precursor)
    target,target_mol=canon_no_stereo(args.target)
    bounds=atom_bounds(precursor,target,extra=1)

    src=enz_mod.AVAILABLE_RULESETS[args.base_ruleset]
    filtered_path=outdir/f"{args.target_name}.{args.base_ruleset}.precursor_filtered.tsv"
    total_rules,filtered_rules=precursor_compatible_rules(Path(src),precursor_mol,filtered_path)
    if filtered_rules==0:
        raise RuntimeError("Precursor-compatibility filter removed every enzymatic rule")

    synthetic_ruleset=f"SYNBIOCROW_{args.target_name}"
    enz_mod.AVAILABLE_RULESETS[synthetic_ruleset]=filtered_path

    result={
        "schema":"synbiocrow.biopks_prefiltered_rules.v1",
        "doranet_version":getattr(doranet,"__version__","UNKNOWN"),
        "base_ruleset":args.base_ruleset,
        "total_base_rules":total_rules,
        "precursor_compatible_rules":filtered_rules,
        "precursor":precursor,
        "target":target,
        "max_atoms":bounds,
        "status":"STARTED",
        "timings":{},
    }
    print("[PREFILTER] RULES",total_rules,"->",filtered_rules,flush=True)

    job=f"{args.target_name}_PREFILTER"
    t=time.time()
    network=enz_mod.generate_network(
        job_name=job,
        starters={precursor},
        gen=1,
        direction="forward",
        max_atoms=bounds,
        targets={target},
        ruleset=synthetic_ruleset,
    )
    result["timings"]["network_seconds"]=time.time()-t
    result["network_molecule_count"]=len(network.mols)
    result["network_reaction_count"]=len(network.rxns)

    target_c=Chem.MolToSmiles(target_mol)
    result["target_in_network"]=any(
        (lambda m: (Chem.RemoveStereochemistry(m),Chem.MolToSmiles(m))[1])(Chem.MolFromSmiles(x.uid))
        == target_c
        for x in network.mols if Chem.MolFromSmiles(x.uid) is not None
    )

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
    report=outdir/f"{args.target_name}.prefiltered.json"
    report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
