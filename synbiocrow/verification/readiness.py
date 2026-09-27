from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .frozen import verify_frozen_2_1, FrozenPolicyReport
from .reproducibility import run_reproducibility_panel, ReproducibilityPanelReport
from .runtime import runtime_matrix, RuntimeMatrixReport

@dataclass(frozen=True)
class ReleaseReadinessReport:
    core_release_ready: bool
    frozen: FrozenPolicyReport
    reproducibility: ReproducibilityPanelReport
    runtime: RuntimeMatrixReport
    blockers: tuple[str,...]
    warnings: tuple[str,...]

def build_release_readiness_report(
    repo_root: str|Path=".",
    *,
    engine=None,
)->ReleaseReadinessReport:
    frozen=verify_frozen_2_1(repo_root)
    reproducibility=run_reproducibility_panel()
    runtime=runtime_matrix(engine)

    blockers=[]
    if not frozen.passed:
        blockers.append("FROZEN_2_1_POLICY_REGRESSION")
    if not reproducibility.passed:
        blockers.append("HERMETIC_REPRODUCIBILITY_PANEL_FAILED")

    warnings=[]
    for backend in runtime.unavailable_backends:
        warnings.append(f"OPTIONAL_BACKEND_NOT_READY:{backend}")

    return ReleaseReadinessReport(
        core_release_ready=not blockers,
        frozen=frozen,
        reproducibility=reproducibility,
        runtime=runtime,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )
