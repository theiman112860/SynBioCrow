from __future__ import annotations
import platform
import sys
from dataclasses import dataclass
from typing import Any

from synbiocrow.engine import SynBioCrowEngine

@dataclass(frozen=True)
class RuntimeMatrixReport:
    python: str
    platform: str
    backends: dict[str,dict[str,Any]]
    core_ready: bool
    ready_backends: tuple[str,...]
    unavailable_backends: tuple[str,...]

def runtime_matrix(engine:SynBioCrowEngine|None=None)->RuntimeMatrixReport:
    engine=engine or SynBioCrowEngine()
    backends=engine.backend_readiness()
    ready=tuple(sorted(k for k,v in backends.items() if v.get("available")))
    unavailable=tuple(sorted(k for k,v in backends.items() if not v.get("available")))
    return RuntimeMatrixReport(
        python=sys.version.split()[0],
        platform=platform.platform(),
        backends=backends,
        core_ready=True,
        ready_backends=ready,
        unavailable_backends=unavailable,
    )
