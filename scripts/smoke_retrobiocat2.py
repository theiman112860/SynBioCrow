"""Optional native RetroBioCat2 API smoke.

This validates the upstream API without launching a search or downloading
starting-material data.

Install the proven pinned source revision first, then run:
    python scripts/smoke_retrobiocat2.py
"""
from synbiocrow.generators.retrobiocat import RetroBioCatBackend

backend = RetroBioCatBackend()
info = backend.runtime_info()
print("RetroBioCat2 runtime:", info)
if not info.get("available"):
    raise SystemExit("RetroBioCat2 (rbc2) is not installed")
if not info.get("native_mcts_api"):
    raise SystemExit("RetroBioCat2 native MCTS/get_expanders API is unavailable")
print("SMOKE PASS: native RetroBioCat2 API contract is available")
