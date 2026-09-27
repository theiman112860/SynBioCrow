from __future__ import annotations
import importlib.util
from dataclasses import dataclass
from typing import Any

from synbiocrow.ensemble.graph import ReactionEdge
from .gates import GateDecision, GateResult

@dataclass(frozen=True)
class ThermodynamicResult:
    standard_dg_prime_kj_per_mol: float | None
    uncertainty_kj_per_mol: float | None
    p_h: float
    ionic_strength_m: float
    temperature_k: float
    formula: str

class EquilibratorThermoClient:
    """Lazy eQuilibrator ComponentContribution adapter.

    SynBioCrow only computes thermodynamics when an edge carries an explicit
    database-accession formula in provenance under equilibrator_formula.
    It does not guess accession mappings from names/SMILES.
    """
    def __init__(
        self,
        *,
        p_h: float = 7.0,
        ionic_strength_m: float = 0.25,
        temperature_k: float = 298.15,
    ):
        self.p_h = float(p_h)
        self.ionic_strength_m = float(ionic_strength_m)
        self.temperature_k = float(temperature_k)

    def available(self) -> bool:
        return importlib.util.find_spec("equilibrator_api") is not None

    def compute(self, formula: str) -> ThermodynamicResult:
        if not self.available():
            raise RuntimeError("equilibrator_api is not installed")

        from equilibrator_api import ComponentContribution, Q_
        cc = ComponentContribution()
        cc.p_h = Q_(self.p_h)
        cc.ionic_strength = Q_(f"{self.ionic_strength_m} M")
        cc.temperature = Q_(f"{self.temperature_k} K")

        reaction = cc.parse_reaction_formula(formula)
        if hasattr(reaction, "is_balanced") and not reaction.is_balanced():
            raise ValueError("eQuilibrator reaction is not atomically balanced")

        value = cc.standard_dg_prime(reaction)
        nominal = getattr(value, "value", value)
        uncertainty = getattr(value, "error", None)

        def to_kj_per_mol(x: Any) -> float | None:
            if x is None:
                return None
            if hasattr(x, "to"):
                x = x.to("kJ/mol")
            if hasattr(x, "magnitude"):
                return float(x.magnitude)
            if hasattr(x, "m_as"):
                return float(x.m_as("kJ/mol"))
            try:
                return float(x)
            except Exception:
                return None

        return ThermodynamicResult(
            standard_dg_prime_kj_per_mol=to_kj_per_mol(nominal),
            uncertainty_kj_per_mol=to_kj_per_mol(uncertainty),
            p_h=self.p_h,
            ionic_strength_m=self.ionic_strength_m,
            temperature_k=self.temperature_k,
            formula=formula,
        )

def _edge_equilibrator_formula(edge: ReactionEdge) -> str | None:
    formulas = []
    for item in edge.provenance:
        value = item.get("equilibrator_formula")
        if value:
            formulas.append(str(value).strip())
    formulas = sorted(set(x for x in formulas if x))
    if len(formulas) == 1:
        return formulas[0]
    return None

def thermodynamic_evidence_for_edge(
    edge: ReactionEdge,
    client: EquilibratorThermoClient,
) -> tuple[GateResult, ThermodynamicResult | None]:
    formula = _edge_equilibrator_formula(edge)
    if not formula:
        return (
            GateResult(
                "quantitative_thermodynamics",
                GateDecision.ABSTAIN,
                "No unique explicit eQuilibrator accession formula is attached to this edge.",
            ),
            None,
        )

    try:
        result = client.compute(formula)
    except Exception as exc:
        return (
            GateResult(
                "quantitative_thermodynamics",
                GateDecision.ABSTAIN,
                f"Quantitative thermodynamics unavailable: {type(exc).__name__}: {exc}",
            ),
            None,
        )

    dg = result.standard_dg_prime_kj_per_mol
    if dg is None:
        return (
            GateResult(
                "quantitative_thermodynamics",
                GateDecision.ABSTAIN,
                "eQuilibrator returned no usable standard transformed Gibbs energy.",
            ),
            result,
        )

    unc = result.uncertainty_kj_per_mol
    suffix = f" ± {unc:.3g}" if unc is not None else ""
    return (
        GateResult(
            "quantitative_thermodynamics",
            GateDecision.PASS,
            f"Quantified dG0-prime = {dg:.3g}{suffix} kJ/mol at pH {result.p_h:g}.",
            (formula,),
        ),
        result,
    )
