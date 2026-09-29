from __future__ import annotations
import json
from pathlib import Path
from synbiocrow.execution import json_safe
from synbiocrow.verification import build_release_readiness_report

root=Path(__file__).resolve().parents[1]
report=build_release_readiness_report(root)
payload=json_safe(report)
out=root/"m7_release_readiness_report.json"
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(payload,indent=2,sort_keys=True))
print(f"[M7] report={out}")
raise SystemExit(0 if report.core_release_ready else 1)
