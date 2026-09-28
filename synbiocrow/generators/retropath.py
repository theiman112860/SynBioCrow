from __future__ import annotations

import csv
import hashlib
import importlib
import os
import importlib.util
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from synbiocrow.core.errors import BackendExecutionError, BackendUnavailableError
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from .base import BackendInfo

RETROPATH_OK = 0
RETROPATH_SOURCE_IN_SINK = 10
RETROPATH_NO_SOLUTION = 11


def _require_file(path: str | Path, label: str) -> Path:
    p = Path(path)
    if not p.exists() or not p.is_file() or p.stat().st_size == 0:
        raise BackendExecutionError(f"RetroPath2 {label} file is missing/empty: {p}")
    return p.resolve()


def _smiles_to_inchi(smiles: str) -> str:
    try:
        from rdkit import Chem
    except Exception as exc:
        raise BackendUnavailableError(
            "RetroPath2 source preparation requires RDKit to convert target SMILES to InChI."
        ) from exc
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid target SMILES: {smiles!r}")
    inchi = Chem.MolToInchi(mol)
    if not inchi.startswith("InChI=1"):
        raise BackendExecutionError(f"RDKit could not produce a valid InChI for {smiles!r}")
    return inchi


def _write_source_csv(path: Path, target_smiles: str) -> str:
    inchi = _smiles_to_inchi(target_smiles)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "inchi"])
        w.writerow(["synbiocrow_target", inchi])
    return inchi


def _parse_out_paths(path: Path, *, target_smiles: str, provenance: Mapping[str, Any]) -> list[PathwayCandidate]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    grouped: dict[str, list[dict[str, str]]] = {}
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pid = str(row.get("Path ID", "")).strip()
            if pid:
                grouped.setdefault(pid, []).append(row)

    out: list[PathwayCandidate] = []
    for pid in sorted(grouped, key=lambda x: (len(x), x)):
        steps: list[ReactionStep] = []
        sig = [target_smiles, pid]
        for index, row in enumerate(grouped[pid]):
            left = str(row.get("Left", "")).strip()
            right = str(row.get("Right", "")).strip()
            rule = str(row.get("Rule ID", "")).strip() or None
            unique_id = str(row.get("Unique ID", "")).strip() or None
            lhs = " + ".join([x for x in left.split(":") if x])
            rhs = " + ".join([x for x in right.split(":") if x])
            reaction = f"{lhs} = {rhs}"
            sig.extend([str(rule or ""), reaction])
            steps.append(ReactionStep(
                reaction=reaction,
                rule_id=rule,
                source_backend="retropath2",
                metadata={
                    "retropath_path_id": pid,
                    "retropath_step_index": index,
                    "retropath_unique_id": unique_id,
                    "raw_left": left,
                    "raw_right": right,
                    "compound_identity_state": "RETROPATH_IDENTIFIER_PENDING_GRAPH_RESOLUTION",
                },
            ))
        digest = hashlib.sha256("\n".join(sig).encode("utf-8")).hexdigest()[:16]
        out.append(PathwayCandidate(
            candidate_id=f"RETROPATH2-{digest}",
            target_smiles=target_smiles,
            steps=tuple(steps),
            source_backends=("retropath2",),
            provenance={**dict(provenance), "retropath_path_id": pid},
        ))
    return out


@dataclass(frozen=True)
class RetroPathSettings:
    rules_file: str
    sink_file: str
    knime_install: str | None = None
    max_steps: int = 5
    topx: int = 50
    dmin: int = 0
    dmax: int = 1000
    mwmax_source: int = 1000
    timeout_minutes: int = 5
    std_hydrogen: str = "implicit"
    score_mode: str = "maximize"


@dataclass
class RetroPathBackend:
    """RetroPath2 scope generation + rp2paths pathway enumeration adapter."""

    settings: RetroPathSettings | None = None
    last_run_stats: dict[str, Any] = field(default_factory=dict, init=False)

    info = BackendInfo(
        backend_id="retropath2",
        family="reaction_rules",
        role="RetroRules/RetroPath pathway generation",
        optional_dependency="retropath2_wrapper + rp2paths + RDKit + KNIME",
    )

    @property
    def backend_id(self) -> str:
        return self.info.backend_id

    def available(self) -> bool:
        return (
            importlib.util.find_spec("retropath2_wrapper") is not None
            and importlib.util.find_spec("rp2paths") is not None
        )

    def configured(self) -> bool:
        return self.settings is not None

    def runtime_info(self) -> dict[str, Any]:
        knime_exec = None
        if self.settings is not None and self.settings.knime_install:
            try:
                knime_mod = importlib.import_module("retropath2_wrapper.knime")
                knime_exec = knime_mod.Knime.find_executable(str(self.settings.knime_install))
            except Exception:
                knime_exec = None
        return {
            "available": self.available(),
            "configured": self.configured(),
            "execution_ready": bool(
                self.available()
                and self.settings is not None
                and Path(self.settings.rules_file).is_file()
                and Path(self.settings.sink_file).is_file()
                and knime_exec
                and os.getenv("SYNBIOCROW_RETROPATH_SMOKE_PASS") == "1"
            ),
            "backend_id": self.backend_id,
            "retropath2_wrapper": importlib.util.find_spec("retropath2_wrapper") is not None,
            "rp2paths": importlib.util.find_spec("rp2paths") is not None,
            "rules_file": None if self.settings is None else str(self.settings.rules_file),
            "sink_file": None if self.settings is None else str(self.settings.sink_file),
            "knime_install": None if self.settings is None else self.settings.knime_install,
            "knime_executable": knime_exec,
        }

    def generate(self, target_smiles: str, *, options: Mapping[str, Any] | None = None) -> Sequence[PathwayCandidate]:
        if self.settings is None:
            raise BackendUnavailableError(
                "RetroPath2 backend is known but not configured. Provide RetroPathSettings(rules_file=..., sink_file=...)."
            )
        if not self.available():
            raise BackendUnavailableError(
                "RetroPath2 runtime is incomplete. Both retropath2_wrapper and rp2paths "
                "must be installed, with RDKit/KNIME available to the scientific runtime."
            )

        rules = _require_file(self.settings.rules_file, "rules")
        sink = _require_file(self.settings.sink_file, "sink")
        options = dict(options or {})
        max_steps = int(options.pop("max_steps", self.settings.max_steps))
        topx = int(options.pop("topx", self.settings.topx))
        timeout_minutes = int(options.pop("timeout_minutes", self.settings.timeout_minutes))
        if options:
            raise ValueError("Unsupported RetroPath2 options: " + ", ".join(sorted(options)))

        try:
            mod = importlib.import_module("retropath2_wrapper")
            retropath2 = getattr(mod, "retropath2")
            knime_obj = None
            if self.settings.knime_install:
                knime_mod = importlib.import_module("retropath2_wrapper.knime")
                knime_obj = knime_mod.Knime(kinstall=str(self.settings.knime_install))
        except Exception as exc:
            raise BackendUnavailableError(f"RetroPath2 Python API could not be imported: {exc!r}") from exc

        with tempfile.TemporaryDirectory(prefix="synbiocrow_retropath2_") as td:
            work = Path(td)
            source = work / "source.csv"
            inchi = _write_source_csv(source, target_smiles)
            scope_dir = work / "scope"
            paths_dir = work / "paths"

            try:
                r_code, files = retropath2(
                    sink_file=str(sink),
                    source_file=str(source),
                    rules_file=str(rules),
                    outdir=str(scope_dir),
                    max_steps=max_steps,
                    topx=topx,
                    dmin=self.settings.dmin,
                    dmax=self.settings.dmax,
                    mwmax_source=self.settings.mwmax_source,
                    std_hydrogen=self.settings.std_hydrogen,
                    score_mode=self.settings.score_mode,
                    msc_timeout=timeout_minutes,
                    knime=knime_obj,
                    rp2_version="r20220104",
                )
            except Exception as exc:
                self.last_run_stats = {"status":"ERROR","stage":"RETROPATH2_SCOPE","error_type":type(exc).__name__,"error":str(exc)}
                raise BackendExecutionError(
                    f"RetroPath2 scope generation failed: {type(exc).__name__}: {exc}"
                ) from exc

            try:
                r_code_int = int(r_code)
            except Exception:
                r_code_int = r_code

            if r_code_int in (RETROPATH_SOURCE_IN_SINK, RETROPATH_NO_SOLUTION):
                self.last_run_stats = {
                    "status":"COMPLETE","return_code":r_code_int,"no_hit":True,
                    "target_inchi":inchi,"max_steps":max_steps,"topx":topx,
                }
                return []

            if r_code_int != RETROPATH_OK:
                self.last_run_stats = {"status":"ERROR","stage":"RETROPATH2_SCOPE","return_code":r_code_int,"target_inchi":inchi}
                raise BackendExecutionError(f"RetroPath2 returned non-success code {r_code_int}")

            result_name = "results.csv"
            scope_root = scope_dir
            if isinstance(files, Mapping):
                result_name = str(files.get("results", result_name))
                scope_root = Path(str(files.get("outdir", scope_dir)))
            scope_csv = scope_root / result_name
            if not scope_csv.exists():
                raise BackendExecutionError(f"RetroPath2 completed but scope result was not found: {scope_csv}")

            paths_dir.mkdir(parents=True, exist_ok=True)
            cmd = [sys.executable, "-m", "rp2paths", "all", str(scope_csv), "--outdir", str(paths_dir)]
            try:
                proc = subprocess.run(
                    cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=max(60, timeout_minutes * 60),
                )
            except Exception as exc:
                raise BackendExecutionError(
                    f"rp2paths extraction failed to execute: {type(exc).__name__}: {exc}"
                ) from exc
            if proc.returncode != 0:
                self.last_run_stats = {
                    "status":"ERROR","stage":"RP2PATHS_ENUMERATION",
                    "return_code":proc.returncode,"output":proc.stdout[-4000:],
                }
                raise BackendExecutionError(f"rp2paths returned rc={proc.returncode}")

            provenance = {
                "backend":"retropath2",
                "mode":"retropath2_scope_plus_rp2paths",
                "rules_file":rules.name,
                "sink_file":sink.name,
                "max_steps":max_steps,
                "topx":topx,
                "target_inchi":inchi,
                "compound_identity_state":"RETROPATH_IDENTIFIER_PENDING_GRAPH_RESOLUTION",
            }
            candidates = _parse_out_paths(
                paths_dir / "out_paths.csv",
                target_smiles=target_smiles,
                provenance=provenance,
            )
            self.last_run_stats = {
                "status":"COMPLETE","return_code":r_code_int,
                "no_hit":len(candidates)==0,"pathways":len(candidates),
                "max_steps":max_steps,"topx":topx,"target_inchi":inchi,
            }
            return candidates
