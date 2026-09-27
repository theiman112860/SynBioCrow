from __future__ import annotations

import hashlib
import importlib
import importlib.util
import tempfile
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Mapping, Sequence

from synbiocrow.core.errors import BackendUnavailableError, ContractViolation
from synbiocrow.core.models import PathwayCandidate, ReactionStep
from .base import BackendInfo


def _mol_uid(mol: Any) -> str:
    value = getattr(mol, "uid", None)
    if value is None:
        value = getattr(mol, "smiles", None)
    if value is None:
        value = str(mol)
    return str(value)


def _operator_metadata(network: Any, operator_index: int) -> dict[str, Any]:
    """Best-effort read of DORAnet operator metadata across 0.5.x."""
    keys = ["name", "Name", "SMARTS", "Reaction_direction", "Reaction_type"]
    for requested in (keys, tuple(keys), None):
        try:
            if requested is None:
                value = network.ops.meta(operator_index)
            else:
                value = network.ops.meta(operator_index, requested)
            if isinstance(value, Mapping):
                return dict(value)
        except (TypeError, KeyError, AttributeError):
            pass

    result: dict[str, Any] = {}
    for key in keys:
        try:
            value = network.ops.meta(operator_index, key)
            if isinstance(value, Mapping):
                if key in value:
                    result[key] = value[key]
            elif value is not None:
                result[key] = value
        except (TypeError, KeyError, AttributeError):
            continue
    return result


def _network_to_candidates(
    network: Any,
    *,
    target_smiles: str,
    doranet_version: str,
    ruleset: str,
    direction: str,
) -> list[PathwayCandidate]:
    """Normalize one-generation DORAnet reactions into Candidate records."""
    candidates: list[PathwayCandidate] = []
    seen: set[str] = set()

    for rxn_index, rxn in enumerate(network.rxns):
        reactants = tuple(_mol_uid(network.mols[i]) for i in rxn.reactants)
        products = tuple(_mol_uid(network.mols[i]) for i in rxn.products)
        reaction = " + ".join(reactants) + " = " + " + ".join(products)
        op_meta = _operator_metadata(network, rxn.operator)
        rule_id = (
            op_meta.get("name")
            or op_meta.get("Name")
            or f"doranet_operator_{rxn.operator}"
        )
        rule_smarts = op_meta.get("SMARTS")

        fingerprint_payload = "\n".join(
            [target_smiles, direction, ruleset, str(rule_id), reaction]
        )
        digest = hashlib.sha256(fingerprint_payload.encode("utf-8")).hexdigest()[:16]
        candidate_id = f"DORANET-{digest}"
        if candidate_id in seen:
            continue
        seen.add(candidate_id)

        step = ReactionStep(
            reaction=reaction,
            rule_id=str(rule_id),
            source_backend="doranet",
            metadata={
                "doranet_operator_index": rxn.operator,
                "doranet_reaction_index": rxn_index,
                "rule_smarts": rule_smarts,
                "direction": direction,
                "ruleset": ruleset,
            },
        )
        candidates.append(
            PathwayCandidate(
                candidate_id=candidate_id,
                target_smiles=target_smiles,
                steps=(step,),
                source_backends=("doranet",),
                provenance={
                    "backend": "doranet",
                    "doranet_version": doranet_version,
                    "mode": "one_generation_direct_rule_probe",
                    "direction": direction,
                    "ruleset": ruleset,
                    "raw_reactant_indices": tuple(rxn.reactants),
                    "raw_product_indices": tuple(rxn.products),
                },
            )
        )

    return sorted(candidates, key=lambda x: x.candidate_id)


@dataclass
class DORAnetBackend:
    """Live, bounded DORAnet adapter.

    Phase-1 consolidation intentionally supports one generation only.
    Multi-generation DORAnet networks are not returned as pathways until
    reaction-graph path reconstruction is migrated and regression-tested.
    """

    info = BackendInfo(
        backend_id="doranet",
        family="reaction_network",
        role="general biosynthetic reaction-network generation",
        optional_dependency="doranet",
    )

    @property
    def backend_id(self) -> str:
        return self.info.backend_id

    def available(self) -> bool:
        return importlib.util.find_spec("doranet") is not None

    def runtime_info(self) -> dict[str, Any]:
        if not self.available():
            return {"available": False, "backend_id": self.backend_id}
        try:
            version = importlib_metadata.version("doranet")
        except importlib_metadata.PackageNotFoundError:
            version = "unknown"
        try:
            module = importlib.import_module("doranet.modules.enzymatic")
            callable_api = callable(getattr(module, "generate_network", None))
        except Exception:
            callable_api = False
        return {
            "available": True,
            "backend_id": self.backend_id,
            "version": version,
            "enzymatic_generate_network": callable_api,
        }

    def generate(
        self,
        target_smiles: str,
        *,
        options: Mapping[str, Any] | None = None,
    ) -> Sequence[PathwayCandidate]:
        options = dict(options or {})
        generations = int(options.pop("generations", 1))
        if generations != 1:
            raise ContractViolation(
                "DORAnet 2.2 consolidation currently supports generations=1 only; "
                "multi-generation path reconstruction has not yet been migrated."
            )
        if not self.available():
            raise BackendUnavailableError(
                "DORAnet is not installed. Install the optional 'doranet' extra "
                "or install doranet==0.5.7a1 in an isolated scientific runtime."
            )

        direction = str(options.pop("direction", "retro"))
        if direction not in {"retro", "forward"}:
            raise ValueError("direction must be 'retro' or 'forward'")
        ruleset = str(options.pop("ruleset", "JN3604IMT"))
        allow_multiple_reactants = bool(
            options.pop("allow_multiple_reactants", False)
        )
        max_atoms = options.pop("max_atoms", None)
        max_rxn_thermo_change = float(
            options.pop("max_rxn_thermo_change", 15)
        )
        if options:
            raise ValueError(
                "Unsupported DORAnet options: " + ", ".join(sorted(options))
            )

        try:
            module = importlib.import_module("doranet.modules.enzymatic")
            generate_network = module.generate_network
        except Exception as exc:
            raise BackendUnavailableError(
                f"DORAnet enzymatic API could not be imported: {exc!r}"
            ) from exc

        try:
            version = importlib_metadata.version("doranet")
        except importlib_metadata.PackageNotFoundError:
            version = "unknown"

        with tempfile.TemporaryDirectory(prefix="synbiocrow_doranet_") as tmp:
            job_name = str(Path(tmp) / "direct_rule_probe")
            network = generate_network(
                job_name=job_name,
                starters=[target_smiles],
                gen=1,
                direction=direction,
                rxn_thermo_calculator=None,
                max_rxn_thermo_change=max_rxn_thermo_change,
                max_atoms=max_atoms,
                allow_multiple_reactants=allow_multiple_reactants,
                targets=None,
                ruleset=ruleset,
            )

        return _network_to_candidates(
            network,
            target_smiles=target_smiles,
            doranet_version=version,
            ruleset=ruleset,
            direction=direction,
        )
