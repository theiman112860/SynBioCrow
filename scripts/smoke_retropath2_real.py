from __future__ import annotations
import csv, json, os
from pathlib import Path
from rdkit import Chem
from synbiocrow.generators.retropath import RetroPathBackend, RetroPathSettings

rules=os.environ.get("SYNBIOCROW_RETROPATH_RULES")
sink=os.environ.get("SYNBIOCROW_RETROPATH_SINK")
knime=os.environ.get("SYNBIOCROW_RETROPATH_KNIME")
source=os.environ.get("SYNBIOCROW_RETROPATH_SMOKE_SOURCE")
if not all([rules,sink,knime,source]):
    raise SystemExit("RetroPath smoke requires SYNBIOCROW_RETROPATH_RULES/SINK/KNIME/SMOKE_SOURCE")

with Path(source).open(newline="",encoding="utf-8") as f:
    row=next(csv.DictReader(f))
inchi=row["InChI"]
mol=Chem.MolFromInchi(inchi)
if mol is None:
    raise SystemExit("Could not parse upstream RetroPath smoke-source InChI")
smiles=Chem.MolToSmiles(mol)

backend=RetroPathBackend(settings=RetroPathSettings(
    rules_file=rules,
    sink_file=sink,
    knime_install=knime,
    max_steps=3,
    topx=50,
    timeout_minutes=10,
))
print(json.dumps(backend.runtime_info(),indent=2,sort_keys=True))
out=backend.generate(smiles,options={"max_steps":3,"topx":50,"timeout_minutes":10})
print(json.dumps(backend.last_run_stats,indent=2,sort_keys=True))
print(f"RETROPATH SMOKE PASS candidates={len(out)} target={smiles}")
