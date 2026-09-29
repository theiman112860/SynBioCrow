from __future__ import annotations

import argparse, json, time
from pathlib import Path
from collections import Counter

def atom_counts(smiles):
    from rdkit import Chem
    mol=Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    return Counter(a.GetSymbol() for a in mol.GetAtoms())

def merged_bounds(precursor,target,margin):
    pc=atom_counts(precursor); tc=atom_counts(target)
    keys=set(pc)|set(tc)
    return {k:max(pc.get(k,0),tc.get(k,0))+int(margin.get(k,0)) for k in sorted(keys)}

def run_network(precursor,target_name,target,max_atoms,generations):
    import doranet.modules.enzymatic as enzymatic
    t=time.time()
    network=enzymatic.generate_network(
        job_name=f"{target_name}_BOUNDED",
        starters={precursor},
        gen=generations,
        direction="forward",
        max_atoms=max_atoms,
    )
    return {
        "status":"PASS",
        "elapsed_seconds":time.time()-t,
        "molecule_count":len(getattr(network,"mols",[]) or []),
        "reaction_count":len(getattr(network,"rxns",[]) or []),
        "max_atoms":max_atoms,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--margin-json",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    margin=json.loads(args.margin_json)
    bounds=merged_bounds(args.precursor,args.target,margin)
    result=run_network(args.precursor,args.target_name,args.target,bounds,1)
    result.update({
        "schema":"synbiocrow.biopks_bounded_postpks.v1",
        "precursor":args.precursor,
        "target":args.target,
        "margin":margin,
    })
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
