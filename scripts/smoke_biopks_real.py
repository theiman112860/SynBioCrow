from __future__ import annotations
import json, os
from synbiocrow.generators.biopks import BioPKSBackend

backend=BioPKSBackend()
info=backend.runtime_info()
print(json.dumps(info,indent=2,sort_keys=True))
if not info.get("available"):
    raise SystemExit("BioPKS backend is not configured/available")
out=backend.generate("CCO",options={"smoke_only":True})
if out != []:
    raise SystemExit("BioPKS smoke protocol expected zero candidates")
if backend.last_run_stats.get("status")!="COMPLETE":
    raise SystemExit(f"BioPKS smoke did not complete: {backend.last_run_stats}")
print("BIOPKS BRIDGE SMOKE PASS")
