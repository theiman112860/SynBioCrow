from __future__ import annotations
import csv, json, os, shutil, tempfile
from pathlib import Path
from rdkit import Chem
from synbiocrow.generators.retropath import RetroPathBackend, RetroPathSettings

rules=os.environ.get("SYNBIOCROW_RETROPATH_RULES")
sink=os.environ.get("SYNBIOCROW_RETROPATH_SINK")
knime=os.environ.get("SYNBIOCROW_RETROPATH_KNIME")
source=os.environ.get("SYNBIOCROW_RETROPATH_SMOKE_SOURCE")
if not all([rules,sink,knime,source]):
    raise SystemExit("RetroPath smoke requires SYNBIOCROW_RETROPATH_RULES/SINK/KNIME/SMOKE_SOURCE")

def dump_knime_logs(knime_install: str) -> None:
    roots=list(Path(knime_install).glob("knime_4.6.4/configuration/*.log"))
    roots=sorted(roots,key=lambda p:p.stat().st_mtime if p.exists() else 0,reverse=True)
    if not roots:
        print("[RETROPATH DIAGNOSTIC] no KNIME configuration log found",flush=True)
        return
    p=roots[0]
    print(f"[RETROPATH DIAGNOSTIC] latest KNIME log: {p}",flush=True)
    try:
        lines=p.read_text(encoding="utf-8",errors="replace").splitlines()
        print("\n".join(lines[-300:]),flush=True)
    except Exception as exc:
        print(f"[RETROPATH DIAGNOSTIC] could not read log: {exc}",flush=True)

# Stage A: exact upstream fixture through upstream wrapper, no SynBioCrow source rewriting.
print("[RETROPATH SMOKE A] exact upstream lycopene fixture through retropath2_wrapper",flush=True)
from retropath2_wrapper import retropath2
from retropath2_wrapper.knime import Knime
knime_obj=Knime(kinstall=knime)
with tempfile.TemporaryDirectory(prefix="synbiocrow_retropath_upstream_") as td:
    outdir=Path(td)/"scope"
    try:
        r_code, files=retropath2(
            sink_file=sink,
            source_file=source,
            rules_file=rules,
            outdir=str(outdir),
            max_steps=3,
            topx=50,
            dmin=0,
            dmax=1000,
            mwmax_source=1000,
            std_hydrogen="implicit",
            score_mode="maximize",
            msc_timeout=10,
            knime=knime_obj,
            rp2_version="r20220104",
        )
        print("[RETROPATH SMOKE A] return_code=",r_code,flush=True)
        print("[RETROPATH SMOKE A] files=",json.dumps(files,indent=2,sort_keys=True) if files else None,flush=True)
        produced=[]
        if outdir.exists():
            produced=[str(p.relative_to(outdir)) for p in sorted(outdir.rglob("*")) if p.is_file()]
        print("[RETROPATH SMOKE A] produced_files=",json.dumps(produced,indent=2),flush=True)
        if int(r_code) != 0:
            dump_knime_logs(knime)
            raise SystemExit(f"RETROPATH UPSTREAM FIXTURE SMOKE FAIL rc={r_code}")
    except Exception:
        dump_knime_logs(knime)
        raise
print("RETROPATH UPSTREAM FIXTURE SMOKE PASS",flush=True)

# Stage B: SynBioCrow adapter using the same upstream target chemistry.
print("[RETROPATH SMOKE B] SynBioCrow RetroPathBackend",flush=True)
with Path(source).open(newline="",encoding="utf-8") as fh:
    row=next(csv.DictReader(fh))
inchi=row.get("InChI") or row.get("inchi")
if not inchi:
    raise SystemExit("Upstream smoke source did not expose InChI column")
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
try:
    out=backend.generate(smiles,options={"max_steps":3,"topx":50,"timeout_minutes":10})
except Exception:
    dump_knime_logs(knime)
    raise
print(json.dumps(backend.last_run_stats,indent=2,sort_keys=True))
print(f"RETROPATH SMOKE PASS candidates={len(out)} target={smiles}")
