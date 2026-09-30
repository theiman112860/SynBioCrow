from __future__ import annotations

import argparse, json
from pathlib import Path

from synbiocrow.sequence import UniProtSequenceClient, optimize_protein_sequence, sequence_qc

PREFERRED_TARGETS=("sabinene","valencene")

def pick_record(payload):
    candidates=[]
    for rec in payload.get("records",[]):
        name=str(rec.get("target_name") or "").strip().lower()
        if name in PREFERRED_TARGETS:
            candidates.append(rec)
    if not candidates:
        raise RuntimeError("Neither sabinene nor valencene found in normalized Galaxy benchmark")
    candidates.sort(key=lambda r:PREFERRED_TARGETS.index(str(r.get("target_name")).strip().lower()))
    return candidates[0]

def collect_uniprot(rec):
    out=[]
    for rxn in rec.get("reactions",[]):
        for acc in rxn.get("uniprot",[]) or []:
            acc=str(acc).strip()
            if acc and acc not in out:
                out.append(acc)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--normalized-benchmark",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    payload=json.loads(Path(args.normalized_benchmark).read_text())
    rec=pick_record(payload)
    accessions=collect_uniprot(rec)
    if not accessions:
        raise RuntimeError(f"No UniProt accessions in literature pathway {rec.get('pathway_id')}")

    client=UniProtSequenceClient(timeout=30.0,user_agent="SynBioCrow/2.3 DBTL case study")
    fetched=[]
    for acc in accessions:
        try:
            p=client.fetch(acc)
            if p.sequence:
                fetched.append(p)
        except Exception as exc:
            print("UNIPROT_FETCH_FAIL",acc,type(exc).__name__,exc,flush=True)

    if not fetched:
        raise RuntimeError("No provenance-backed UniProt protein sequence could be fetched")

    # Prefer reviewed protein evidence, then deterministic accession order.
    fetched.sort(key=lambda p:(not bool(p.reviewed),p.accession))
    protein=fetched[0]
    optimized=optimize_protein_sequence(
        protein.sequence,
        profile_name="ecoli_k12_simple_preferred",
        include_stop=True,
    )
    qc=sequence_qc(optimized.dna_sequence)

    result={
        "schema":"synbiocrow.dbtl_sequence_backed_build.v1",
        "pathway_id":rec.get("pathway_id"),
        "target_name":rec.get("target_name"),
        "literature_doi":(rec.get("literature") or {}).get("doi"),
        "galaxy_uniprot_accessions":accessions,
        "selected_protein":{
            "accession":protein.accession,
            "source":protein.source,
            "reviewed":protein.reviewed,
            "organism":protein.organism,
            "protein_length":len(protein.sequence or ""),
            "provenance":dict(protein.provenance or {}),
        },
        "build":{
            "status":"SYNTHETIC_CDS_DESIGNED_FROM_PROVENANCE_BACKED_PROTEIN",
            "profile_name":optimized.profile_name,
            "cds_length_nt":len(optimized.dna_sequence),
            "protein_length_aa":len(optimized.protein_sequence),
            "translation_preserved":True,
            "sequence_qc": {
                "pass_qc":qc.pass_qc,
                "length":qc.length,
                "gc_fraction":qc.gc_fraction,
                "forbidden_motifs":list(qc.forbidden_motifs),
            },
            "cassette_status":"ABSTAIN_MISSING_VERIFIED_REGULATORY_SEQUENCES",
            "note":"CDS is a newly designed synthetic coding sequence derived from the selected UniProt protein; it is not represented as a native CDS accession."
        }
    }

    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"dbtl_sequence_backed_build.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
