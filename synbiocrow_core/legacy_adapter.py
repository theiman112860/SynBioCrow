"""Strict adapter for the historical SynBioCrow normalized reaction archives."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pathway_evidence import Reaction, trace_pathway


def adapt_legacy_reactions(records: list[dict[str, Any]]) -> tuple[list[Reaction], list[dict]]:
    """Preserve forward direction and provenance; quarantine incomplete records.

    Historical fields: id, engine, substrates, products, source_file,
    source_sha256, direction, status. Do not infer absent provenance.
    """
    reactions = []
    quarantine = []
    seen = set()
    for index, record in enumerate(records):
        try:
            rid = str(record["id"])
            engine = str(record["engine"])
            substrates = record["substrates"]
            products = record["products"]
            source = record["source_file"]
            digest = record["source_sha256"]
            if not isinstance(substrates, list) or not isinstance(products, list):
                raise ValueError("substrates/products must be lists")
            if not isinstance(source, str) or not source or not isinstance(digest, str) or len(digest) != 64:
                raise ValueError("source file and SHA256 required")
            if not isinstance(record.get("direction"), str) or not record["direction"]:
                raise ValueError("explicit native direction required")
            if rid in seen:
                raise ValueError("duplicate reaction id")
            seen.add(rid)
            reactions.append(Reaction(rid, tuple(substrates), tuple(products), engine, f"{source}#sha256={digest}"))
        except (KeyError, TypeError, ValueError) as exc:
            quarantine.append({"index": index, "id": record.get("id"), "reason": str(exc)})
    return reactions, quarantine


def report_from_legacy_archive(path: str | Path, seeds: list[str], target: str) -> dict:
    """Read a plain JSON list or one of the two previously inspected ZIP layouts."""
    import zipfile
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            choices = ("synbiocrow_target_integration/combined_reactions.json",
                       "combined_reaction_candidates.json")
            member = next((name for name in choices if name in archive.namelist()), None)
            if member is None:
                raise ValueError("no recognized normalized reaction member in archive")
            records = json.loads(archive.read(member))
    else:
        records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("normalized reaction archive must contain a JSON list")
    reactions, quarantine = adapt_legacy_reactions(records)
    result = trace_pathway(reactions, seeds, target)
    result["input_reaction_count"] = len(records)
    result["accepted_reaction_count"] = len(reactions)
    result["quarantined_reaction_count"] = len(quarantine)
    result["quarantine"] = quarantine
    result["scientific_status"] = "UNCERTIFIED_GRAPH_CANDIDATE"
    return result
