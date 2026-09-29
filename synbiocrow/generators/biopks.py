from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from synbiocrow.core.errors import BackendExecutionError, BackendUnavailableError
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from .base import BackendInfo


def _step_reaction(step: Mapping[str, Any]) -> str | None:
    for key in ("reaction", "reaction_smiles", "reaction_string"):
        value = step.get(key)
        if value and "=" in str(value):
            return str(value).strip()

    product = step.get("product_smiles") or step.get("product")
    precursors = (
        step.get("precursor_smiles")
        or step.get("precursors")
        or step.get("substrates")
        or step.get("reactants")
    )
    if product and precursors:
        if isinstance(precursors, str):
            precursors = [precursors]
        vals = [str(x).strip() for x in precursors if str(x).strip()]
        if vals:
            return str(product).strip() + " = " + " + ".join(vals)
    return None


def normalize_biopks_payload(
    payload: Mapping[str, Any],
    *,
    target_smiles: str,
    source: str = "biopks_external",
) -> list[PathwayCandidate]:
    routes = payload.get("routes")
    if routes is None:
        routes = payload.get("pathways")
    if routes is None:
        routes = payload.get("candidates")
    if routes is None:
        routes = []
    if not isinstance(routes, list):
        raise BackendExecutionError("BioPKS bridge output must contain a list of routes/pathways/candidates")

    out: list[PathwayCandidate] = []
    for route_index, route in enumerate(routes):
        if not isinstance(route, Mapping):
            raise BackendExecutionError(f"BioPKS route {route_index} is not an object")
        steps_raw = route.get("steps") or route.get("reactions") or []
        if not isinstance(steps_raw, list):
            raise BackendExecutionError(f"BioPKS route {route_index} steps are not a list")

        steps: list[ReactionStep] = []
        signature = [target_smiles]
        for step_index, raw in enumerate(steps_raw):
            if not isinstance(raw, Mapping):
                continue
            reaction = _step_reaction(raw)
            if reaction is None:
                # PKS architecture/design-only steps remain provenance, not
                # invented reaction edges.
                continue
            rule_id = (
                raw.get("rule_id")
                or raw.get("rule")
                or raw.get("name")
                or raw.get("step_type")
                or "biopks_step"
            )
            score = raw.get("score")
            try:
                feasibility = float(score) if score is not None else None
            except (TypeError, ValueError):
                feasibility = None
            metadata = {
                "specialized_generator": True,
                "route_class": route.get("route_class", "PKS_SPECIALIST"),
                "biopks_step_index": step_index,
                "step_type": raw.get("step_type"),
                "module_architecture": raw.get("module_architecture"),
                "pks_design": raw.get("pks_design"),
                "retrosynthetic_parent_side": raw.get("retrosynthetic_parent_side", "left"),
                "external_source": source,
            }
            for key in (
                "rhea_id", "rhea_equation", "equilibrator_formula",
                "enzyme_accession", "ec_number"
            ):
                if raw.get(key) is not None:
                    metadata[key] = raw.get(key)

            step = ReactionStep(
                reaction=reaction,
                rule_id=str(rule_id),
                source_backend="biopks_retrotide",
                feasibility=feasibility,
                metadata=metadata,
            )
            steps.append(step)
            signature.extend([str(rule_id), reaction])

        route_id = route.get("candidate_id") or route.get("route_id")
        if route_id:
            candidate_id = str(route_id)
        else:
            digest = hashlib.sha256("\n".join(signature).encode("utf-8")).hexdigest()[:16]
            candidate_id = f"BIOPKS-{digest}"

        provenance = {
            "backend": "biopks_retrotide",
            "source": source,
            "route_class": route.get("route_class", "PKS_SPECIALIST"),
            "score": route.get("score"),
            "predicted_product_smiles": route.get("predicted_product_smiles"),
            "pks_design": route.get("pks_design"),
            "module_architecture": route.get("module_architecture"),
            "sequence_assets": route.get("sequence_assets", []),
            "specialist_sequence_complete": bool(route.get("specialist_sequence_complete", False)),
            "experimental_validation_claimed": bool(route.get("experimental_validation_claimed", False)),
            "candidate_default_state": "CANDIDATE",
            "raw_route_index": route_index,
        }
        out.append(
            PathwayCandidate(
                candidate_id=candidate_id,
                target_smiles=target_smiles,
                steps=tuple(steps),
                source_backends=("biopks_retrotide",),
                provenance=provenance,
            )
        )

    by_id = {c.candidate_id: c for c in out}
    return [by_id[k] for k in sorted(by_id)]


@dataclass
class BioPKSBackend:
    """External BioPKS/RetroTide specialist adapter.

    BioPKS Pipeline is not vendored. SynBioCrow communicates with a separately
    installed/authorized runtime through a JSON subprocess bridge.
    """

    runner: str | None = None
    python_executable: str | None = None
    timeout_s: float = 600.0
    last_run_stats: dict[str, Any] = field(default_factory=dict, init=False)

    info = BackendInfo(
        backend_id="biopks_retrotide",
        family="pks",
        role="bounded specialized PKS generation and post-PKS search",
        optional_dependency="external BioPKS-Pipeline / RetroTide runtime",
    )

    @property
    def backend_id(self) -> str:
        return self.info.backend_id

    def _runner_path(self) -> Path | None:
        raw = self.runner or os.getenv("SYNBIOCROW_BIOPKS_RUNNER")
        if not raw:
            return None
        p = Path(raw).expanduser()
        return p.resolve() if p.exists() else p

    def available(self) -> bool:
        p = self._runner_path()
        return p is not None and p.exists() and p.is_file()

    def runtime_info(self) -> dict[str, Any]:
        p = self._runner_path()
        return {
            "available": self.available(),
            "configured": p is not None,
            "backend_id": self.backend_id,
            "runner": str(p) if p is not None else None,
            "license_acknowledged": os.getenv("SYNBIOCROW_BIOPKS_ACK_LICENSE") == "1",
            "upstream": "https://github.com/JBEI/BioPKS-Pipeline",
            "retrotide_upstream": "https://github.com/JBEI/RetroTide",
        }

    def generate(
        self,
        target_smiles: str,
        *,
        options: Mapping[str, Any] | None = None,
    ) -> Sequence[PathwayCandidate]:
        runner = self._runner_path()
        if runner is None or not runner.exists():
            raise BackendUnavailableError(
                "BioPKS external bridge is not configured. Set SYNBIOCROW_BIOPKS_RUNNER "
                "to a bridge script in a separately installed BioPKS runtime."
            )
        if os.getenv("SYNBIOCROW_BIOPKS_ACK_LICENSE") != "1":
            raise BackendUnavailableError(
                "BioPKS external runtime requires explicit license acknowledgement: "
                "set SYNBIOCROW_BIOPKS_ACK_LICENSE=1 after reviewing the upstream license."
            )

        request = {
            "schema": "synbiocrow.biopks.external.v1",
            "target_smiles": target_smiles,
            "options": dict(options or {}),
        }
        python = (
            self.python_executable
            or os.getenv("SYNBIOCROW_BIOPKS_PYTHON")
            or sys.executable
        )
        try:
            proc = subprocess.run(
                [python, str(runner)],
                input=json.dumps(request),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_s,
            )
        except Exception as exc:
            self.last_run_stats = {
                "status": "ERROR",
                "stage": "BRIDGE_EXECUTION",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            raise BackendExecutionError(
                f"BioPKS bridge execution failed: {type(exc).__name__}: {exc}"
            ) from exc

        if proc.returncode != 0:
            self.last_run_stats = {
                "status": "ERROR",
                "stage": "BRIDGE_RETURN_CODE",
                "return_code": proc.returncode,
                "stderr_tail": proc.stderr[-4000:],
            }
            raise BackendExecutionError(
                f"BioPKS bridge returned rc={proc.returncode}"
            )

        try:
            response = json.loads(proc.stdout)
        except Exception as exc:
            raise BackendExecutionError(
                f"BioPKS bridge stdout is not valid JSON: {exc}"
            ) from exc

        if response.get("schema") not in (None, "synbiocrow.biopks.external.v1"):
            raise BackendExecutionError(
                f"Unsupported BioPKS bridge schema: {response.get('schema')!r}"
            )
        status = str(response.get("status", "COMPLETE")).upper()
        if status not in ("COMPLETE", "PASS", "NO_HIT"):
            raise BackendExecutionError(
                f"BioPKS bridge reported non-success status {status!r}"
            )

        candidates = normalize_biopks_payload(
            response,
            target_smiles=target_smiles,
            source=str(runner),
        )
        self.last_run_stats = {
            "status": "COMPLETE",
            "bridge_status": status,
            "candidate_pathways": len(candidates),
            "no_hit": len(candidates) == 0,
        }
        return candidates
