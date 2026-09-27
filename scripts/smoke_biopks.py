"""BioPKS external bridge smoke.

This does not install or vendor BioPKS Pipeline.
Configure a separately installed/authorized bridge first:

  export SYNBIOCROW_BIOPKS_RUNNER=/path/to/bridge.py
  export SYNBIOCROW_BIOPKS_ACK_LICENSE=1
  export SYNBIOCROW_BIOPKS_PYTHON=/path/to/python   # optional

Then:
  python scripts/smoke_biopks.py
"""
from synbiocrow.generators.biopks import BioPKSBackend

backend=BioPKSBackend()
print("BioPKS runtime:",backend.runtime_info())
if not backend.available():
    raise SystemExit("BioPKS bridge is not configured")
print("SMOKE PASS: external BioPKS bridge is configured")
