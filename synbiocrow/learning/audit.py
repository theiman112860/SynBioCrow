from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from .models import LearningPolicy, PolicyUpdate, TestOutcome

class LearningAuditLog:
    """Append-only JSONL audit trail for learned policy updates."""
    def __init__(self,path:str|Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(
        self,
        *,
        policy_before: LearningPolicy,
        policy_after: LearningPolicy,
        update: PolicyUpdate,
        outcomes: tuple[TestOutcome,...],
    )->None:
        record={
            "policy_before":asdict(policy_before),
            "policy_after":asdict(policy_after),
            "update":asdict(update),
            "outcomes":[asdict(o) for o in outcomes],
            "lifecycle_effect":"NONE",
        }
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(record,sort_keys=True)+"\n")

    def read_all(self)->list[dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
