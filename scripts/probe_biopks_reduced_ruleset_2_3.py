from __future__ import annotations

import argparse, json, time
from pathlib import Path
from collections import Counter

def atom_bounds(precursor,target,extra=1):
    from rdkit import Chem
    def counts(s):
        m=Chem.MolFromSmiles(s)
        if m is None:
            raise ValueError(f"Invalid SMILES: {s}")
        c=Counter(a.GetSymbol() for a in m.GetAtoms())
        return c
    pc=counts(precursor); tc=counts(target)
    keys=set(pc)|set(tc)
    return {k:max(pc.get(k,0),tc.get(k,0))+extra for k in sorted(keys)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--ruleset",default="JN1224MIN")
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    import doranet.modules.enzymatic as enzymatic
    import doranet.modules.post_processing as post_processing
    from rdkit import Chem

    precursor_mol=Chem.MolFromSmiles(args.precursor)
    target_mol=Chem.MolFromSmiles(args.target)
    Chem.RemoveStereochemistry(precursor_mol)
    Chem.RemoveStereochemistry(target_mol)
    precursor=Chem.MolToSmiles(precursor_mol)
    target=Chem.MolToSmiles(target_mol)
    bounds=atom_bounds(precursor,target,extra=1)
    job=f"{args.target_name}_{args.ruleset}"

    result={
        "schema":"synbiocrow.biopks_reduced_ruleset_probe.v1",
        "precursor":precursor,
        "target":target,
        "ruleset":args.ruleset,
        "max_atoms":bounds,
        "status":"STARTED",
        "timings":{},
    }

    print("[REDUCED] NETWORK_START",args.ruleset,flush=True)
    t=time.time()
    network=enzymatic.generate_network(
        job_name=job,
        starters={precursor},
        gen=1,
        direction="forward",
        max_atoms=bounds,
        targets={target},
        ruleset=args.ruleset,
    )
    result["timings"]["network_seconds"]=time.time()-t
    result["network_molecule_count"]=len(network.mols)
    result["network_reaction_count"]=len(network.rxns)
    result["target_in_network"]=any(
        Chem.MolToSmiles(Chem.MolFromSmiles(m.uid))==target
        for m in network.mols if Chem.MolFromSmiles(m.uid) is not None
    )
    print("[REDUCED] NETWORK_DONE",json.dumps({
        "seconds":result["timings"]["network_seconds"],
        "molecules":result["network_molecule_count"],
        "reactions":result["network_reaction_count"],
        "target_in_network":result["target_in_network"],
    }),flush=True)

    # Only run pathway extraction when target is actually present.
    if result["target_in_network"]:
        print("[REDUCED] POSTPROCESS_START",flush=True)
        t=time.time()
        post_processing.one_step(
            networks={network},
            total_generations=1,
            starters={precursor},
            target=target,
            job_name=job,
            search_depth=1,
            max_num_rxns=1,
            min_rxn_atom_economy=0,
            num_process=1,
        )
        result["timings"]["postprocess_seconds"]=time.time()-t
        pf=Path(f"{job}_pathways.txt")
        result["pathways_file_exists"]=pf.is_file()
        result["pathways_file_bytes"]=pf.stat().st_size if pf.is_file() else 0
    else:
        result["pathways_file_exists"]=False
        result["pathways_file_bytes"]=0

    result["status"]="PASS"
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
