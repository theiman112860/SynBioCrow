"""Optional RetroPath2/RP2paths API smoke.

This validates import-level readiness only. A real search additionally requires:
- KNIME
- a RetroRules RetroPath2-ready rules file
- a sink file
- RDKit
"""
import importlib

for name in ("retropath2_wrapper", "rp2paths"):
    mod = importlib.import_module(name)
    print(name, "OK", getattr(mod, "__file__", "?"))

from retropath2_wrapper import retropath2
assert callable(retropath2)
print("SMOKE PASS: RetroPath2 wrapper + rp2paths APIs are importable")
