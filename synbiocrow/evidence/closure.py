from __future__ import annotations
from collections import Counter
from typing import Iterable

from synbiocrow.core.models import ReactionStep
from .gates import GateDecision, GateResult

def split_reaction_tokens(reaction: str) -> tuple[list[str], list[str]]:
    if " = " not in reaction:
        raise ValueError(f"reaction lacks explicit ' = ' separator: {reaction!r}")
    left, right = reaction.split(" = ", 1)
    # SynBioCrow normalizers emit ' + ' between compounds. Splitting only on
    # spaced separators avoids corrupting charged SMILES such as [NH4+].
    lhs = [x.strip() for x in left.split(" + ") if x.strip()]
    rhs = [x.strip() for x in right.split(" + ") if x.strip()]
    return lhs, rhs

def _side_inventory(tokens: Iterable[str]):
    try:
        from rdkit import Chem
    except Exception:
        return None
    atoms = Counter()
    charge = 0
    for token in tokens:
        mol = Chem.MolFromSmiles(token)
        if mol is None:
            return None
        for atom in mol.GetAtoms():
            atoms[atom.GetSymbol()] += 1
            charge += int(atom.GetFormalCharge())
    return atoms, charge

def stoichiometric_closure(step: ReactionStep) -> GateResult:
    try:
        lhs, rhs = split_reaction_tokens(step.reaction)
    except ValueError as exc:
        return GateResult("stoichiometric_closure", GateDecision.ABSTAIN, str(exc))

    li = _side_inventory(lhs)
    ri = _side_inventory(rhs)
    if li is None or ri is None:
        return GateResult(
            "stoichiometric_closure",
            GateDecision.ABSTAIN,
            "One or more reaction participants could not be parsed as molecular structures.",
        )

    latoms, lcharge = li
    ratoms, rcharge = ri
    if latoms == ratoms and lcharge == rcharge:
        return GateResult(
            "stoichiometric_closure",
            GateDecision.PASS,
            "Reaction is balanced for explicit atoms and formal charge.",
        )
    return GateResult(
        "stoichiometric_closure",
        GateDecision.FAIL,
        f"Reaction is not balanced: atoms {dict(latoms)} -> {dict(ratoms)}; charge {lcharge} -> {rcharge}.",
    )
