from __future__ import annotations
import csv
import io
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from synbiocrow.ensemble.graph import ReactionEdge, EnsembleGraph
from .gates import GateDecision, GateResult

RHEA_SEARCH_URL = "https://www.rhea-db.org/rhea/"

@dataclass(frozen=True)
class RheaHit:
    rhea_id: str
    equation: str
    ec: tuple[str, ...] = ()
    uniprot_count: str | None = None
    pubmed: tuple[str, ...] = ()

class RheaClient:
    """Small stdlib REST client for Rhea search.

    Rhea participant searches are contextual by default. They become exact
    evidence only when the edge already carries an explicit Rhea identifier
    that is confirmed by the query result.
    """
    def __init__(self, *, timeout: float = 20.0, user_agent: str = "SynBioCrow/2.2"):
        self.timeout = timeout
        self.user_agent = user_agent

    def _get_tsv(self, query: str, limit: int = 50) -> list[dict[str, str]]:
        params = urllib.parse.urlencode({
            "query": query,
            "columns": "rhea-id,equation,ec,uniprot,pubmed",
            "format": "tsv",
            "limit": int(limit),
        })
        req = urllib.request.Request(
            RHEA_SEARCH_URL + "?" + params,
            headers={"User-Agent": self.user_agent},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        return list(csv.DictReader(io.StringIO(text), delimiter="\t"))

    def search_inchikeys(self, inchikeys: Iterable[str], *, limit: int = 50) -> list[RheaHit]:
        keys = sorted({k for k in inchikeys if k})
        if not keys:
            return []
        query = " AND ".join(f"inchikey:{k}" for k in keys)
        rows = self._get_tsv(query, limit=limit)
        hits = []
        for row in rows:
            hits.append(RheaHit(
                rhea_id=(row.get("Reaction identifier") or row.get("rhea-id") or "").strip(),
                equation=(row.get("Equation") or row.get("equation") or "").strip(),
                ec=tuple(x.strip() for x in (row.get("EC number") or row.get("ec") or "").split(";") if x.strip()),
                uniprot_count=(row.get("Enzymes") or row.get("uniprot") or "").strip() or None,
                pubmed=tuple(x.strip() for x in (row.get("PubMed") or row.get("pubmed") or "").split(";") if x.strip()),
            ))
        return hits

def _explicit_rhea_ids(edge: ReactionEdge) -> set[str]:
    ids = set()
    for item in edge.provenance:
        for key in ("rhea_id", "rhea", "RHEA"):
            value = item.get(key)
            if value:
                s = str(value).upper().replace("RHEA:", "")
                ids.add("RHEA:" + s)
    return ids

def rhea_evidence_for_edge(graph: EnsembleGraph, edge: ReactionEdge, client: RheaClient) -> tuple[GateResult, list[RheaHit]]:
    compound_keys = [edge.parent_key, *edge.precursor_keys]
    identities = [graph.compounds[k] for k in compound_keys if k in graph.compounds]
    inchikeys = [c.inchikey for c in identities if c.inchikey]
    if len(inchikeys) != len(compound_keys):
        return (
            GateResult(
                "rhea_reaction_evidence",
                GateDecision.ABSTAIN,
                "Not all reaction participants have canonical InChIKeys; exact Rhea lookup is unavailable.",
            ),
            [],
        )

    try:
        hits = client.search_inchikeys(inchikeys)
    except Exception as exc:
        return (
            GateResult(
                "rhea_reaction_evidence",
                GateDecision.ABSTAIN,
                f"Rhea query unavailable: {type(exc).__name__}: {exc}",
            ),
            [],
        )

    if not hits:
        return (
            GateResult(
                "rhea_reaction_evidence",
                GateDecision.ABSTAIN,
                "No Rhea reaction contained all canonical participants.",
            ),
            [],
        )

    explicit = _explicit_rhea_ids(edge)
    exact = [h for h in hits if h.rhea_id in explicit]
    if exact:
        return (
            GateResult(
                "rhea_reaction_evidence",
                GateDecision.PASS,
                "Explicit Rhea mapping confirmed by Rhea participant search.",
                tuple(h.rhea_id for h in exact),
            ),
            exact,
        )

    return (
        GateResult(
            "rhea_reaction_evidence",
            GateDecision.ABSTAIN,
            "Rhea contains reactions with all participants, but participant co-occurrence alone is not treated as exact reaction evidence.",
            tuple(h.rhea_id for h in hits),
        ),
        hits,
    )
