from __future__ import annotations
import csv
import io
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .gates import GateDecision, GateResult

UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/search"

@dataclass(frozen=True)
class UniProtEnzymeHit:
    accession: str
    entry_name: str
    protein_name: str
    organism_name: str
    length: int | None

class UniProtRheaClient:
    def __init__(self, *, timeout: float = 20.0, user_agent: str = "SynBioCrow/2.2"):
        self.timeout = timeout
        self.user_agent = user_agent

    def _search(self, query: str, *, size: int = 25) -> list[UniProtEnzymeHit]:
        params = urllib.parse.urlencode({
            "query": query,
            "fields": "accession,id,protein_name,organism_name,length",
            "format": "tsv",
            "size": int(size),
        })
        req = urllib.request.Request(
            UNIPROT_URL + "?" + params,
            headers={"User-Agent": self.user_agent},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
        hits = []
        for row in rows:
            length = row.get("Length") or row.get("length")
            try:
                length_i = int(length) if length else None
            except ValueError:
                length_i = None
            hits.append(UniProtEnzymeHit(
                accession=(row.get("Entry") or row.get("accession") or "").strip(),
                entry_name=(row.get("Entry Name") or row.get("id") or "").strip(),
                protein_name=(row.get("Protein names") or row.get("protein_name") or "").strip(),
                organism_name=(row.get("Organism") or row.get("organism_name") or "").strip(),
                length=length_i,
            ))
        return hits

    def reviewed_for_rhea(self, rhea_id: str, *, size: int = 25) -> list[UniProtEnzymeHit]:
        rid = str(rhea_id).upper()
        if not rid.startswith("RHEA:"):
            rid = "RHEA:" + rid
        return self._search(
            f'(cc_catalytic_activity:"{rid.lower()}" AND reviewed:true AND fragment:false)',
            size=size,
        )

    def reviewed_for_ec(self, ec_number: str, *, size: int = 25) -> list[UniProtEnzymeHit]:
        ec = str(ec_number).upper().replace("EC:", "")
        return self._search(
            f'(ec:{ec} AND reviewed:true AND fragment:false)',
            size=size,
        )

def enzyme_evidence_for_exact_rhea(rhea_ids: list[str], client: UniProtRheaClient) -> tuple[GateResult, list[UniProtEnzymeHit]]:
    if not rhea_ids:
        return (
            GateResult(
                "verified_enzyme_evidence",
                GateDecision.ABSTAIN,
                "No exact Rhea mapping is available, so enzyme evidence is not promoted from contextual matches.",
            ),
            [],
        )
    all_hits = []
    errors = []
    for rid in sorted(set(rhea_ids)):
        try:
            all_hits.extend(client.reviewed_for_rhea(rid))
        except Exception as exc:
            errors.append(f"{rid}: {type(exc).__name__}: {exc}")
    unique = {h.accession: h for h in all_hits if h.accession}
    hits = [unique[k] for k in sorted(unique)]
    if hits:
        return (
            GateResult(
                "verified_enzyme_evidence",
                GateDecision.PASS,
                "Reviewed UniProtKB entries are explicitly annotated to the exact Rhea reaction.",
                tuple(h.accession for h in hits),
            ),
            hits,
        )
    if errors:
        return (
            GateResult(
                "verified_enzyme_evidence",
                GateDecision.ABSTAIN,
                "UniProt exact-Rhea query was unavailable or incomplete: " + "; ".join(errors),
            ),
            [],
        )
    return (
        GateResult(
            "verified_enzyme_evidence",
            GateDecision.ABSTAIN,
            "No reviewed UniProtKB entries were found for the exact Rhea reaction.",
        ),
        [],
    )

def enzyme_context_for_ecs(ec_numbers: list[str], client: UniProtRheaClient) -> tuple[GateResult, list[UniProtEnzymeHit]]:
    ecs=sorted({str(x).upper().replace("EC:","") for x in ec_numbers if x})
    if not ecs:
        return (
            GateResult(
                "enzyme_context_evidence",
                GateDecision.ABSTAIN,
                "No EC classification is available for contextual enzyme-family evidence.",
            ),
            [],
        )
    hits=[]
    errors=[]
    for ec in ecs:
        try:
            hits.extend(client.reviewed_for_ec(ec))
        except Exception as exc:
            errors.append(f"EC:{ec}: {type(exc).__name__}: {exc}")
    unique={h.accession:h for h in hits if h.accession}
    hits=[unique[k] for k in sorted(unique)]
    if hits:
        return (
            GateResult(
                "enzyme_context_evidence",
                GateDecision.PASS,
                "Reviewed UniProtKB proteins exist for the associated EC class; this is family/context evidence, not exact reaction-enzyme proof.",
                tuple(h.accession for h in hits),
            ),
            hits,
        )
    if errors:
        return (
            GateResult(
                "enzyme_context_evidence",
                GateDecision.ABSTAIN,
                "Contextual EC query unavailable or incomplete: " + "; ".join(errors),
            ),
            [],
        )
    return (
        GateResult(
            "enzyme_context_evidence",
            GateDecision.ABSTAIN,
            "No reviewed UniProtKB proteins found for the associated EC class.",
        ),
        [],
    )
