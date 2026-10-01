"""Source registry and snapshot metadata for SynBioCrow 2.4 benchmark curation."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SourceRegistryEntry:
    source_id: str
    name: str
    source_type: str
    homepage: str
    release: Optional[str] = None
    accessed_utc: Optional[str] = None
    license_note: Optional[str] = None
    role: str = "candidate-discovery"
    truth_eligible: bool = False
    notes: Optional[str] = None

    def validate(self) -> None:
        if not self.source_id or not self.name or not self.source_type:
            raise ValueError("source_id, name, and source_type are required")
        if self.role not in {
            "candidate-discovery",
            "reaction-evidence",
            "enzyme-evidence",
            "literature-provenance",
            "mapping",
        }:
            raise ValueError(f"unsupported source role: {self.role}")


@dataclass
class SourceRegistry:
    registry_id: str
    entries: List[SourceRegistryEntry]

    def validate(self) -> None:
        seen = set()
        for e in self.entries:
            e.validate()
            if e.source_id in seen:
                raise ValueError(f"duplicate source_id: {e.source_id}")
            seen.add(e.source_id)

    def canonical_json(self) -> str:
        self.validate()
        payload = {
            "registry_id": self.registry_id,
            "entries": [asdict(e) for e in sorted(self.entries, key=lambda x: x.source_id)],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def write_registry(registry: SourceRegistry, path: str) -> str:
    registry.validate()
    Path(path).write_text(
        json.dumps(
            {
                "registry_id": registry.registry_id,
                "registry_sha256": registry.sha256(),
                "entries": [asdict(e) for e in sorted(registry.entries, key=lambda x: x.source_id)],
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return path
