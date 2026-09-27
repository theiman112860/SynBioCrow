from __future__ import annotations

import dataclasses
import hashlib
import importlib
import importlib.util
from dataclasses import dataclass, field
from importlib import metadata as importlib_metadata
from typing import Any, Mapping, Sequence

from synbiocrow.core.errors import BackendExecutionError, BackendUnavailableError
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from .base import BackendInfo


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if dataclasses.is_dataclass(value):
        return _json_safe(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def _ordered_reactions(pathway: Any) -> list[Any]:
    """Return RBC2 reactions target-first, preserving branch structure deterministically."""
    reactions = list(getattr(pathway, "reactions", ()) or ())
    if not reactions:
        return []

    by_product: dict[str, list[Any]] = {}
    for reaction in reactions:
        by_product.setdefault(str(reaction.product), []).append(reaction)

    target = str(getattr(pathway, "target_smi", "") or "")
    ordered: list[Any] = []
    seen: set[int] = set()

    def visit(product: str) -> None:
        candidates = by_product.get(product, [])
        candidates = sorted(
            candidates,
            key=lambda r: (
                str(getattr(r, "name", "")),
                tuple(str(x) for x in getattr(r, "substrates", ()) or ()),
            ),
        )
        for reaction in candidates:
            marker = id(reaction)
            if marker in seen:
                continue
            seen.add(marker)
            ordered.append(reaction)
            for substrate in sorted(str(x) for x in reaction.substrates):
                visit(substrate)

    if target:
        visit(target)

    # Defensive fallback for unusual RBC2 pathway objects.
    for reaction in reactions:
        if id(reaction) not in seen:
            ordered.append(reaction)
            seen.add(id(reaction))
    return ordered


def _precedent_summary(reaction: Any) -> list[dict[str, Any]]:
    out = []
    for precedent in list(getattr(reaction, "precedents", ()) or ()):
        data = _json_safe(precedent)
        if isinstance(data, Mapping):
            out.append(dict(data))
        else:
            out.append({"value": data})
    return out


def _pathway_to_candidate(
    pathway: Any,
    *,
    target_smiles: str,
    rbc2_version: str,
    search_stats: Mapping[str, Any] | None = None,
) -> PathwayCandidate:
    ordered = _ordered_reactions(pathway)
    steps: list[ReactionStep] = []
    signature_parts = [target_smiles]

    for index, reaction in enumerate(ordered):
        product = str(reaction.product)
        substrates = tuple(str(x) for x in reaction.substrates)
        rxn_text = product + " = " + " + ".join(substrates)
        name = str(getattr(reaction, "name", "unnamed_reaction"))
        score = getattr(reaction, "score", None)
        try:
            feasibility = float(score) if score is not None else None
        except (TypeError, ValueError):
            feasibility = None

        metadata = {
            "rbc2_step_index": index,
            "rxn_type": str(getattr(reaction, "rxn_type", "no_rxn_type")),
            "rxn_domain": str(getattr(reaction, "rxn_domain", "no_rxn_domain")),
            "template_metadata": _json_safe(getattr(reaction, "template_metadata", {})),
            "feasability_filter_scores": _json_safe(
                getattr(reaction, "feasability_filter_scores", {})
            ),
            "precedents": _precedent_summary(reaction),
            "rbc2_data": _json_safe(getattr(reaction, "data", {})),
        }
        steps.append(
            ReactionStep(
                reaction=rxn_text,
                rule_id=name,
                source_backend="retrobiocat2",
                feasibility=feasibility,
                metadata=metadata,
            )
        )
        # Do not include RBC2's random reaction UUID in the deterministic ID.
        signature_parts.extend([name, rxn_text])

    digest = hashlib.sha256("\n".join(signature_parts).encode("utf-8")).hexdigest()[:16]
    return PathwayCandidate(
        candidate_id=f"RBC2-{digest}",
        target_smiles=target_smiles,
        steps=tuple(steps),
        source_backends=("retrobiocat2",),
        provenance={
            "backend": "retrobiocat2",
            "rbc2_version": rbc2_version,
            "search_stats": _json_safe(dict(search_stats or {})),
            "pathway_length": int(getattr(pathway, "pathway_length", len(steps))),
            "end_smiles": sorted(str(x) for x in getattr(pathway, "end_smis", lambda: [])()),
        },
    )


@dataclass(frozen=True)
class RBC2Settings:
    max_search_time: float = 20.0
    max_iterations: int | None = 500
    max_length: int = 6
    chemistry_filter: str = "None"


@dataclass
class RetroBioCatBackend:
    """Native RetroBioCat2 MCTS adapter with explicit runtime/no-hit semantics."""

    settings: RBC2Settings = field(default_factory=RBC2Settings)
    last_run_stats: dict[str, Any] = field(default_factory=dict, init=False)

    info = BackendInfo(
        backend_id="retrobiocat2",
        family="biocatalysis",
        role="enzyme-centered biocatalytic retrosynthesis",
        optional_dependency="rbc2",
    )

    @property
    def backend_id(self) -> str:
        return self.info.backend_id

    def available(self) -> bool:
        return importlib.util.find_spec("rbc2") is not None

    def runtime_info(self) -> dict[str, Any]:
        if not self.available():
            return {"available": False, "backend_id": self.backend_id}
        try:
            version = importlib_metadata.version("rbc2")
        except importlib_metadata.PackageNotFoundError:
            version = "unknown"
        try:
            mcts_mod = importlib.import_module("rbc2.mcts.mcts")
            repo_mod = importlib.import_module("rbc2.expansion.expander_repository")
            native_api = callable(getattr(mcts_mod, "MCTS", None)) and callable(
                getattr(repo_mod, "get_expanders", None)
            )
        except Exception:
            native_api = False
        return {
            "available": True,
            "backend_id": self.backend_id,
            "version": version,
            "native_mcts_api": native_api,
        }

    def generate(
        self,
        target_smiles: str,
        *,
        options: Mapping[str, Any] | None = None,
    ) -> Sequence[PathwayCandidate]:
        if not self.available():
            raise BackendUnavailableError(
                "RetroBioCat2 (rbc2) is not installed. Use the pinned optional "
                "runtime described in docs/RETROBIOCAT2_ADAPTER.md."
            )

        options = dict(options or {})
        settings = RBC2Settings(
            max_search_time=float(options.pop("max_search_time", self.settings.max_search_time)),
            max_iterations=options.pop("max_iterations", self.settings.max_iterations),
            max_length=int(options.pop("max_length", self.settings.max_length)),
            chemistry_filter=str(options.pop("chemistry_filter", self.settings.chemistry_filter)),
        )
        starting_material_evaluator = options.pop("starting_material_evaluator", None)
        filters = options.pop("filters", None)
        if options:
            raise ValueError(
                "Unsupported RetroBioCat2 options: " + ", ".join(sorted(options))
            )

        try:
            mcts_mod = importlib.import_module("rbc2.mcts.mcts")
            config_mod = importlib.import_module("rbc2.configs.mcts_config")
            expander_mod = importlib.import_module("rbc2.expansion.expander_repository")
            MCTS = mcts_mod.MCTS
            config = config_mod.MCTS_Config()
            get_expanders = expander_mod.get_expanders
        except Exception as exc:
            raise BackendUnavailableError(
                f"RetroBioCat2 native API could not be imported: {exc!r}"
            ) from exc

        config.max_search_time = settings.max_search_time
        config.max_iterations = settings.max_iterations
        config.max_length = settings.max_length
        config.chemistry_filter = settings.chemistry_filter

        try:
            expanders = get_expanders(["retrobiocat"])
            kwargs = {
                "target_smi": target_smiles,
                "expanders": expanders,
                "config": config,
            }
            if starting_material_evaluator is not None:
                kwargs["starting_material_evaluator"] = starting_material_evaluator
            if filters is not None:
                kwargs["filters"] = filters
            mcts = MCTS(**kwargs)
            mcts.run()
            stats = dict(mcts.get_run_stats())
            solved = list(mcts.get_solved_pathways())
        except Exception as exc:
            self.last_run_stats = {
                "status": "ERROR",
                "target_smi": target_smiles,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            raise BackendExecutionError(
                f"RetroBioCat2 execution failed for target {target_smiles!r}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        try:
            version = importlib_metadata.version("rbc2")
        except importlib_metadata.PackageNotFoundError:
            version = "unknown"

        self.last_run_stats = {
            "status": "COMPLETE",
            **_json_safe(stats),
            "solved_pathways": len(solved),
        }

        # [] is a successful bounded no-hit, not an engine failure.
        candidates = [
            _pathway_to_candidate(
                pathway,
                target_smiles=target_smiles,
                rbc2_version=version,
                search_stats=self.last_run_stats,
            )
            for pathway in solved
        ]
        by_id = {c.candidate_id: c for c in candidates}
        return [by_id[k] for k in sorted(by_id)]
