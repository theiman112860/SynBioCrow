from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from rdkit import Chem

from synbiocrow.core.errors import BackendExecutionError, BackendUnavailableError
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from .base import BackendInfo


def _canon(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    return Chem.MolToSmiles(mol) if mol is not None else smiles.strip()


def _truthy_sink(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _write_source(path: Path, target_smiles: str) -> None:
    mol = Chem.MolFromSmiles(target_smiles)
    if mol is None:
        raise ValueError(f"Invalid target SMILES: {target_smiles!r}")
    inchi = Chem.MolToInchi(mol)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Name", "InChI"])
        w.writerow(["synbiocrow_target", inchi])


@dataclass(frozen=True)
class RetroPathStandaloneSettings:
    executable: str
    rules_file: str
    sink_file: str
    max_steps: int = 3
    topx: int = 50
    dmin: int = 0
    dmax: int = 1000
    mwmax_source: int = 1000
    timeout_minutes: int = 10


@dataclass
class RetroPathStandaloneBackend:
    """KNIME-free RetroPath2.0-compatible scope generator.

    This adapter targets TraceLD/retropath. It remains fail-closed for
    certification until equivalence testing against the canonical RetroPath2
    fixtures is complete.
    """

    settings: RetroPathStandaloneSettings | None = None
    last_run_stats: dict[str, Any] = field(default_factory=dict, init=False)

    info = BackendInfo(
        backend_id="retropath_standalone",
        family="reaction_rules",
        role="KNIME-free RetroPath2.0 standalone reaction-network generation",
        optional_dependency="TraceLD/retropath standalone CLI",
    )

    @property
    def backend_id(self) -> str:
        return self.info.backend_id

    def available(self) -> bool:
        return bool(
            self.settings
            and Path(self.settings.executable).is_file()
            and os.access(self.settings.executable, os.X_OK)
            and Path(self.settings.rules_file).is_file()
            and Path(self.settings.sink_file).is_file()
        )

    def runtime_info(self) -> dict[str, Any]:
        s = self.settings
        return {
            "backend_id": self.backend_id,
            "available": self.available(),
            "configured": s is not None,
            "execution_ready": bool(self.available() and os.getenv("SYNBIOCROW_RETROPATH_STANDALONE_SMOKE_PASS") == "1"),
            "certification_ready": False,
            "equivalence_status": "PENDING_CANONICAL_FIXTURE_COMPARISON",
            "knime_required": False,
            "executable": None if s is None else s.executable,
            "rules_file": None if s is None else s.rules_file,
            "sink_file": None if s is None else s.sink_file,
        }

    def _rows_to_candidates(
        self,
        rows: list[dict[str, str]],
        *,
        target_smiles: str,
        max_steps: int,
        topx: int,
    ) -> list[PathwayCandidate]:
        target = _canon(target_smiles)
        parsed = []
        for row in rows:
            substrate = _canon(row.get("Substrate SMILES", ""))
            product = _canon(row.get("Product SMILES", ""))
            if not substrate or not product:
                continue
            parsed.append((substrate, product, row))

        fwd_hits = sum(1 for a, _, _ in parsed if a == target)
        rev_hits = sum(1 for _, b, _ in parsed if b == target)
        reverse = rev_hits > fwd_hits

        adjacency: dict[str, list[tuple[str, dict[str, str]]]] = {}
        for a, b, row in parsed:
            left, right = (b, a) if reverse else (a, b)
            adjacency.setdefault(left, []).append((right, row))

        routes: list[tuple[list[dict[str, str]], bool]] = []
        stack: list[tuple[str, list[dict[str, str]], set[str]]] = [(target, [], {target})]
        while stack and len(routes) < max(topx, 1) * 4:
            node, path, seen = stack.pop()
            edges = adjacency.get(node, [])
            if not edges:
                if path:
                    routes.append((path, False))
                continue
            for nxt, row in edges[: max(topx, 1)]:
                if nxt in seen:
                    continue
                new_path = path + [row]
                solved = _truthy_sink(row.get("In Sink", "0"))
                if solved or len(new_path) >= max_steps:
                    routes.append((new_path, solved))
                else:
                    stack.append((nxt, new_path, seen | {nxt}))

        # If orientation/canonicalization prevents chaining, still expose the
        # generated reaction scope as one-step candidates rather than fabricating
        # connectivity.
        if not routes:
            routes = [([row], _truthy_sink(row.get("In Sink", "0"))) for _, _, row in parsed[:topx]]

        out: list[PathwayCandidate] = []
        for idx, (route, solved) in enumerate(routes[:topx]):
            steps = []
            sig = [target]
            for row in route:
                reaction = row.get("Reaction SMILES", "").strip()
                if not reaction:
                    reaction = f"{row.get('Substrate SMILES','')}>>{row.get('Product SMILES','')}"
                rule = row.get("Rule ID", "").strip() or None
                sig.extend([reaction, str(rule or "")])
                steps.append(
                    ReactionStep(
                        reaction=reaction,
                        rule_id=rule,
                        source_backend=self.backend_id,
                        feasibility=None,
                        metadata={
                            "transformation_id": row.get("Transformation ID"),
                            "substrate_smiles": row.get("Substrate SMILES"),
                            "product_smiles": row.get("Product SMILES"),
                            "substrate_inchi": row.get("Substrate InChI"),
                            "product_inchi": row.get("Product InChI"),
                            "in_sink": _truthy_sink(row.get("In Sink", "0")),
                            "sink_name": row.get("Sink name"),
                            "diameter": row.get("Diameter"),
                            "ec_number": row.get("EC number"),
                            "score": row.get("Score"),
                            "iteration": row.get("Iteration"),
                        },
                    )
                )
            digest = hashlib.sha256("\n".join(sig).encode("utf-8")).hexdigest()[:16]
            out.append(
                PathwayCandidate(
                    candidate_id=f"RETROPATH-STANDALONE-{digest}",
                    target_smiles=target_smiles,
                    steps=tuple(steps),
                    source_backends=(self.backend_id,),
                    provenance={
                        "backend": self.backend_id,
                        "engine": "TraceLD/retropath",
                        "knime_required": False,
                        "equivalence_status": "PENDING_CANONICAL_FIXTURE_COMPARISON",
                        "certification_ready": False,
                        "sink_reached": solved,
                        "graph_orientation": "product_to_substrate" if reverse else "substrate_to_product",
                        "scope_rows": len(rows),
                        "route_index": idx,
                    },
                )
            )
        return out

    def generate(self, target_smiles: str, *, options: Mapping[str, Any] | None = None) -> Sequence[PathwayCandidate]:
        if self.settings is None:
            raise BackendUnavailableError("RetroPath standalone backend is not configured.")
        if not self.available():
            raise BackendUnavailableError("RetroPath standalone executable/rules/sink are unavailable.")

        options = dict(options or {})
        max_steps = int(options.pop("max_steps", self.settings.max_steps))
        topx = int(options.pop("topx", self.settings.topx))
        timeout_minutes = int(options.pop("timeout_minutes", self.settings.timeout_minutes))
        if options:
            raise ValueError("Unsupported RetroPath standalone options: " + ", ".join(sorted(options)))

        with tempfile.TemporaryDirectory(prefix="synbiocrow_retropath_standalone_") as td:
            root = Path(td)
            source = root / "source.csv"
            output = root / "results"
            _write_source(source, target_smiles)
            cmd = [
                self.settings.executable,
                self.settings.rules_file,
                str(source),
                self.settings.sink_file,
                str(max_steps),
                "--source-mw", str(self.settings.mwmax_source),
                "--min-diameter", str(self.settings.dmin),
                "--max-diameter", str(self.settings.dmax),
                "--max-structures", str(topx),
                "--output-dir", str(output),
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=max(60, timeout_minutes * 60),
                )
            except Exception as exc:
                raise BackendExecutionError(
                    f"RetroPath standalone execution failed: {type(exc).__name__}: {exc}"
                ) from exc

            result_csv = output / "results.csv"
            if proc.returncode != 0:
                self.last_run_stats = {
                    "status": "ERROR",
                    "return_code": proc.returncode,
                    "output": proc.stdout[-8000:],
                }
                raise BackendExecutionError(
                    f"RetroPath standalone returned rc={proc.returncode}: {proc.stdout[-2000:]}"
                )
            if not result_csv.is_file():
                raise BackendExecutionError(
                    f"RetroPath standalone completed without results.csv. Output: {proc.stdout[-4000:]}"
                )

            with result_csv.open(newline="", encoding="utf-8", errors="replace") as fh:
                rows = list(csv.DictReader(fh))
            candidates = self._rows_to_candidates(
                rows,
                target_smiles=target_smiles,
                max_steps=max_steps,
                topx=topx,
            )
            self.last_run_stats = {
                "status": "COMPLETE",
                "return_code": proc.returncode,
                "scope_rows": len(rows),
                "pathways": len(candidates),
                "sink_reaching_pathways": sum(
                    1 for c in candidates if c.provenance.get("sink_reached")
                ),
                "equivalence_status": "PENDING_CANONICAL_FIXTURE_COMPARISON",
            }
            return candidates
