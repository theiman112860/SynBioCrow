"""Optional real-runtime smoke for the DORAnet adapter.

Run only in an environment with doranet installed:
    python scripts/smoke_doranet.py
"""
from synbiocrow.generators.doranet import DORAnetBackend

backend = DORAnetBackend()
info = backend.runtime_info()
print("DORAnet runtime:", info)
if not info.get("available"):
    raise SystemExit("DORAnet is not installed")
if not info.get("enzymatic_generate_network"):
    raise SystemExit("DORAnet enzymatic.generate_network API is unavailable")

# The real generation call is intentionally not automatic here because
# DORAnet loads thousands of enzymatic rules and writes a network artifact.
print("SMOKE PASS: live DORAnet API contract is available")
