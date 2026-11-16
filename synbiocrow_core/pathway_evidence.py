"""Dependency-complete reaction-hypergraph pathway evidence validation.

No chemistry is invented; graph feasibility is distinct from biochemical feasibility.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Reaction:
    reaction_id: str
    reactants: tuple[str, ...]
    products: tuple[str, ...]
    engine: str
    evidence_ref: str

    def __post_init__(self) -> None:
        if not self.reaction_id or not self.reactants or not self.products:
            raise ValueError("reaction_id, reactants and products required")
        if not self.engine or not self.evidence_ref:
            raise ValueError("engine and evidence_ref required")
        if any(not s for s in (*self.reactants, *self.products)):
            raise ValueError("empty molecule identifier")


def trace_pathway(
    reactions: Iterable[Reaction],
    seeds: Iterable[str],
    target: str,
    *,
    max_rounds: int = 1000,
) -> dict:
    """Find a finite forward dependency proof for a target.

    All reactants are required. Input direction is never reversed. One
    witness reaction is retained per newly reachable product.
    """
    if not target:
        raise ValueError("target required")
    if max_rounds < 1:
        raise ValueError("max_rounds must be positive")
    rxns = tuple(reactions)
    ids = [r.reaction_id for r in rxns]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate reaction_id")
    reachable = set(seeds)
    if any(not x for x in reachable):
        raise ValueError("empty seed identifier")
    initial = set(reachable)
    witness: dict[str, Reaction] = {}
    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        changed = False
        for reaction in rxns:
            if not set(reaction.reactants).issubset(reachable):
                continue
            for product in reaction.products:
                if product not in reachable:
                    reachable.add(product)
                    witness[product] = reaction
                    changed = True
        if not changed:
            break
    complete = target in reachable
    used: dict[str, Reaction] = {}
    def collect(molecule: str) -> None:
        if molecule in initial:
            return
        reaction = witness.get(molecule)
        if reaction is None or reaction.reaction_id in used:
            return
        used[reaction.reaction_id] = reaction
        for precursor in reaction.reactants:
            collect(precursor)
    if complete:
        collect(target)
    else:
        # A missing precursor is not proof that no pathway exists in chemistry.
        pass
    blockers = []
    if not complete:
        for r in rxns:
            if target in r.products:
                missing = sorted(set(r.reactants) - reachable)
                blockers.append({"reaction_id": r.reaction_id, "missing_reactants": missing})
    return {
        "target": target,
        "graph_reachable": complete,
        "biochemically_validated": False,
        "seed_molecules": sorted(initial),
        "reachable_molecule_count": len(reachable),
        "reaction_evidence": [
            {"reaction_id": r.reaction_id, "engine": r.engine,
             "evidence_ref": r.evidence_ref, "reactants": list(r.reactants),
             "products": list(r.products)}
            for r in used.values()
        ],
        "target_producing_reaction_gaps": blockers,
        "search_exhausted": rounds < max_rounds or not changed,
    }
