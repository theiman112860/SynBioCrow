from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping
from synbiocrow.core.models import PathwayCandidate

@dataclass(frozen=True)
class DesignRequest:
    target_smiles: str
    mode: str = "biosynthesis"
    backend_ids: tuple[str,...] | None = None
    sink_smiles: tuple[str,...] = ()
    max_route_steps: int = 8
    max_routes: int = 100
    backend_options: Mapping[str,Mapping[str,Any]] = field(default_factory=dict)

@dataclass
class DesignResult:
    request: DesignRequest
    candidates: list[PathwayCandidate]
    routes: list[list[str]]
    backend_status: dict[str,dict[str,Any]]
    graph_summary: dict[str,Any]
    diagnostics: dict[str,Any]
    run_id: str
