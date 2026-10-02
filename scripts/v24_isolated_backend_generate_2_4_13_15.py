#!/usr/bin/env python3
import argparse,json,pickle,resource
from pathlib import Path
from synbiocrow import SynBioCrowEngine
from synbiocrow.execution import json_safe
from rdkit import Chem

class FrozenSinkEvaluator:
    def __init__(self,sinks):
        self.target_always_not_buyable=True
        self._sink_canon={self._canon(x) for x in sinks}
    def _canon(self,smi):
        mol=Chem.MolFromSmiles(str(smi))
        if mol is None: return str(smi)
        return Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True)
    def eval(self,smi):
        c=self._canon(smi)
        return (c in self._sink_canon,{"source":"synbiocrow_frozen_sink_panel","canonical_smiles":c})
    def is_mol_chiral(self,smi):
        mol=Chem.MolFromSmiles(str(smi))
        return False if mol is None else bool(Chem.FindMolChiralCenters(mol,includeUnassigned=True))

ap=argparse.ArgumentParser()
ap.add_argument("--backend",required=True,choices=["doranet","retrobiocat2"])
ap.add_argument("--target",required=True)
ap.add_argument("--sink-panel",required=True)
ap.add_argument("--pickle-out",required=True)
ap.add_argument("--summary-out",required=True)
ap.add_argument("--quick",action="store_true")
a=ap.parse_args()

panel=json.loads(Path(a.sink_panel).read_text())
sinks=[x["smiles"] for x in panel["sinks"]]
engine=SynBioCrowEngine()
backend=engine.backends.get(a.backend)
if backend is None:
    raise RuntimeError("backend unavailable: "+a.backend)
readiness=backend.readiness() if hasattr(backend,"readiness") else {"available":True}
if isinstance(readiness,dict) and not readiness.get("available",True):
    raise RuntimeError("backend not ready: "+json.dumps(readiness,sort_keys=True))

opts={}
if a.backend=="retrobiocat2":
    opts={
        "max_search_time":15.0 if a.quick else 30.0,
        "max_iterations":300 if a.quick else 750,
        "max_length":4 if a.quick else 6,
        "starting_material_evaluator":FrozenSinkEvaluator(sinks),
        "include_explored_pathways":True,
    }
found=list(backend.generate(a.target,options=opts))
Path(a.pickle_out).parent.mkdir(parents=True,exist_ok=True)
with open(a.pickle_out,"wb") as fh:
    pickle.dump(found,fh,pickle.HIGHEST_PROTOCOL)
stats=json_safe(getattr(backend,"last_run_stats",{}))
rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
summary={
    "backend":a.backend,"target":a.target,"quick":bool(a.quick),
    "candidate_count":len(found),"run_stats":stats,
    "max_rss_kb":rss_kb,"pickle_path":str(a.pickle_out),
    "validation_truth_accessed":False,
}
Path(a.summary_out).write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,sort_keys=True),flush=True)
