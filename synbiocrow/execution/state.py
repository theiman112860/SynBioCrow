from __future__ import annotations
import json
import hashlib
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

def json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k:json_safe(v) for k,v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,set)):
        return [json_safe(v) for v in value]
    return value

def stable_hash(data: Any) -> str:
    raw=json.dumps(json_safe(data),sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class RunStateStore:
    """Atomic, stage-based JSON persistence for resumable design runs."""
    def __init__(self, root: str|Path):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)

    def run_dir(self, run_id: str)->Path:
        p=self.root/run_id
        p.mkdir(parents=True,exist_ok=True)
        return p

    def write_stage(self, run_id: str, stage: str, payload: Any)->Path:
        d=self.run_dir(run_id)
        target=d/f"{stage}.json"
        tmp=d/f".{stage}.json.tmp"
        tmp.write_text(json.dumps(json_safe(payload),indent=2,sort_keys=True)+"\n",encoding="utf-8")
        tmp.replace(target)
        return target

    def read_stage(self, run_id: str, stage: str)->Any|None:
        p=self.run_dir(run_id)/f"{stage}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def completed_stages(self, run_id: str)->tuple[str,...]:
        d=self.run_dir(run_id)
        return tuple(sorted(p.stem for p in d.glob("*.json")))

    def latest_manifest(self, run_id: str)->dict[str,Any]:
        return {
            "run_id":run_id,
            "completed_stages":list(self.completed_stages(run_id)),
        }
