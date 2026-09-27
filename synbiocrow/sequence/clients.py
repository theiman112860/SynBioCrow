from __future__ import annotations
import json
import urllib.parse
import urllib.request

from .models import ProteinEvidence, CDSEvidence

UNIPROT_ENTRY = "https://rest.uniprot.org/uniprotkb/{accession}.json"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

class UniProtSequenceClient:
    def __init__(self, *, timeout: float = 20.0, user_agent: str = "SynBioCrow/2.2"):
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch(self, accession: str) -> ProteinEvidence:
        url = UNIPROT_ENTRY.format(accession=urllib.parse.quote(accession))
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        seq = (data.get("sequence") or {}).get("value")
        entry_type = str(data.get("entryType", ""))
        org = (data.get("organism") or {}).get("scientificName")
        return ProteinEvidence(
            accession=accession,
            source="UniProtKB",
            sequence=seq,
            reviewed=("reviewed" in entry_type.lower()),
            organism=org,
            provenance={"entry_type": entry_type, "primary_accession": data.get("primaryAccession")},
        )

class NCBIRefSeqClient:
    """Fetch an explicitly bounded CDS from a nucleotide accession.

    SynBioCrow requires upstream provenance to supply CDS coordinates and
    strand. A whole nucleotide record is never silently relabeled as a CDS.
    """
    def __init__(self, *, timeout: float = 30.0, user_agent: str = "SynBioCrow/2.2"):
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch_subsequence(
        self,
        nucleotide_accession: str,
        *,
        start: int,
        end: int,
        strand: int = 1,
    ) -> str:
        if start < 1 or end < start:
            raise ValueError("NCBI subsequence coordinates must satisfy 1 <= start <= end")
        if strand not in (1, 2):
            raise ValueError("NCBI strand must be 1 (plus) or 2 (minus)")
        params = urllib.parse.urlencode({
            "db": "nuccore",
            "id": nucleotide_accession,
            "rettype": "fasta",
            "retmode": "text",
            "seq_start": int(start),
            "seq_stop": int(end),
            "strand": int(strand),
        })
        req = urllib.request.Request(
            NCBI_EFETCH + "?" + params,
            headers={"User-Agent": self.user_agent},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        lines = [x.strip() for x in text.splitlines() if x.strip() and not x.startswith(">")]
        seq = "".join(lines).upper()
        if not seq:
            raise ValueError(
                f"No nucleotide sequence returned for {nucleotide_accession}:{start}-{end}"
            )
        return seq

    def cds_evidence(
        self,
        nucleotide_accession: str,
        *,
        start: int,
        end: int,
        strand: int = 1,
        protein_accession: str | None = None,
        protein_sequence: str | None = None,
        organism: str | None = None,
    ) -> CDSEvidence:
        seq=self.fetch_subsequence(
            nucleotide_accession,
            start=start,
            end=end,
            strand=strand,
        )
        return CDSEvidence(
            nucleotide_accession=nucleotide_accession,
            source="NCBI RefSeq/GenBank EFetch bounded CDS",
            cds_sequence=seq,
            protein_accession=protein_accession,
            protein_sequence=protein_sequence,
            organism=organism,
            start=start,
            end=end,
            strand=strand,
            provenance={
                "fetch_mode":"explicit_accession_coordinates",
                "coordinate_system":"NCBI 1-based inclusive",
            },
        )
