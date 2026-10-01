import json
import zipfile

from synbiocrow.core.models import PathwayCandidate, ReactionStep
from synbiocrow.ensemble.graph import build_reaction_graph


def test_released_edge_id_algorithm_is_stable():
    c = PathwayCandidate(
        candidate_id="x",
        target_smiles="OCCCCO",
        source_backends=("retrobiocat2",),
        steps=(ReactionStep(
            reaction="OCCCCO = O=CCCCO",
            source_backend="retrobiocat2",
            metadata={},
        ),),
    )
    g = build_reaction_graph([c])
    assert list(g.edges) == ["rxn:5d08421cd957d457c203b145"]


def test_route_hashing_uses_graph_identity_not_reaction_text_hash():
    c1 = PathwayCandidate(
        candidate_id="a", target_smiles="CCO", source_backends=("retrobiocat2",),
        steps=(ReactionStep(reaction="CCO = CC=O", source_backend="retrobiocat2"),),
    )
    c2 = PathwayCandidate(
        candidate_id="b", target_smiles="CCO", source_backends=("retrobiocat2",),
        steps=(ReactionStep(reaction="CCO=CC=O", source_backend="retrobiocat2"),),
    )
    # Unsupported historical formatting without ' = ' must fail rather than
    # being normalized heuristically.
    build_reaction_graph([c1])
    try:
        build_reaction_graph([c2])
    except ValueError:
        pass
    else:
        raise AssertionError("expected fail-closed reaction parsing")
