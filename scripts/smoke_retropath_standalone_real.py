from __future__ import annotations
import csv, json, os
from pathlib import Path
from rdkit import Chem
from synbiocrow.generators.retropath_standalone import RetroPathStandaloneBackend, RetroPathStandaloneSettings

manifest_path=Path(os.environ["SYNBIOCROW_RETROPATH_STANDALONE_MANIFEST"])
manifest=json.loads(manifest_path.read_text())
source=Path(manifest["source_file"])
with source.open(newline="",encoding="utf-8") as fh:
    row=next(csv.DictReader(fh))
inchi=row.get("InChI") or row.get("inchi")
mol=Chem.MolFromInchi(inchi)
if mol is None:
    raise SystemExit("Could not parse standalone smoke-source InChI")
smiles=Chem.MolToSmiles(mol)

backend=RetroPathStandaloneBackend(settings=RetroPathStandaloneSettings(
    executable=manifest["executable"],
    rules_file=manifest["rules_file"],
    sink_file=manifest["sink_file"],
    max_steps=3,
    topx=50,
    timeout_minutes=10,
))
print(json.dumps(backend.runtime_info(),indent=2,sort_keys=True))
out=backend.generate(smiles,options={"max_steps":3,"topx":50,"timeout_minutes":10})
print(json.dumps(backend.last_run_stats,indent=2,sort_keys=True))
for c in out[:5]:
    print(json.dumps({
        "candidate_id":c.candidate_id,
        "steps":len(c.steps),
        "sink_reached":c.provenance.get("sink_reached"),
        "equivalence_status":c.provenance.get("equivalence_status"),
    },sort_keys=True))
print(f"RETROPATH STANDALONE SYNBIOCROW SMOKE PASS candidates={len(out)} target={smiles}")
