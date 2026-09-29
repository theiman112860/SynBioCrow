from __future__ import annotations

import argparse, json, time, traceback
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--precursor",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--target-name",required=True)
    ap.add_argument("--stage",choices=["network","full"],default="full")
    ap.add_argument("--generations",type=int,default=1)
    ap.add_argument("--cores",type=int,default=1)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    from rdkit import Chem
    import doranet.modules.enzymatic as enzymatic
    import doranet.modules.post_processing as post_processing

    out={"schema":"synbiocrow.biopks_post_pks_probe.v1","stage":args.stage,
         "precursor":args.precursor,"target":args.target,"timings":{},"status":"STARTED"}

    precursor_mol=Chem.MolFromSmiles(args.precursor)
    target_mol=Chem.MolFromSmiles(args.target)
    if precursor_mol is None or target_mol is None:
        raise ValueError("Invalid precursor or target SMILES")
    Chem.RemoveStereochemistry(precursor_mol)
    Chem.RemoveStereochemistry(target_mol)
    precursor=Chem.MolToSmiles(precursor_mol)
    target=Chem.MolToSmiles(target_mol)
    job=f"{args.target_name}_POSTPKS_PROBE"

    print("[POSTPKS] NETWORK_START",flush=True)
    t=time.time()
    network=enzymatic.generate_network(
        job_name=job, starters={precursor}, gen=args.generations,
        direction="forward", max_atoms=None
    )
    out["timings"]["network_seconds"]=time.time()-t
    out["network_molecule_count"]=len(getattr(network,"mols",[]) or [])
    out["network_reaction_count"]=len(getattr(network,"rxns",[]) or [])
    print("[POSTPKS] NETWORK_DONE",json.dumps({
        "seconds":out["timings"]["network_seconds"],
        "molecules":out["network_molecule_count"],
        "reactions":out["network_reaction_count"]
    }),flush=True)

    if args.stage=="network":
        out["status"]="PASS_NETWORK"
        Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        return 0

    print("[POSTPKS] POSTPROCESS_START",flush=True)
    t=time.time()
    post_processing.one_step(
        networks={network}, total_generations=args.generations,
        starters={precursor}, target=target, job_name=job,
        search_depth=args.generations, max_num_rxns=args.generations,
        min_rxn_atom_economy=0, num_process=args.cores
    )
    out["timings"]["postprocess_seconds"]=time.time()-t
    pathfile=Path(f"{job}_pathways.txt")
    out["pathways_file_exists"]=pathfile.is_file()
    out["pathways_file_bytes"]=pathfile.stat().st_size if pathfile.is_file() else 0
    out["status"]="PASS_FULL"
    print("[POSTPKS] POSTPROCESS_DONE",json.dumps({
        "seconds":out["timings"]["postprocess_seconds"],
        "pathways_file_exists":out["pathways_file_exists"],
        "pathways_file_bytes":out["pathways_file_bytes"]
    }),flush=True)
    Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("[POSTPKS] ERROR",type(exc).__name__,str(exc),flush=True)
        traceback.print_exc()
        raise
