from __future__ import annotations

import argparse, json, urllib.parse, urllib.request
from pathlib import Path

from synbiocrow.sequence import UniProtSequenceClient, optimize_protein_sequence, sequence_qc

PREFERRED_TARGETS=("sabinene","valencene")
UNIPROT_SEARCH="https://rest.uniprot.org/uniprotkb/search"

def preferred_records(payload):
    found=[]
    for rec in payload.get("records",[]):
        name=str(rec.get("target_name") or "").strip().lower()
        if name in PREFERRED_TARGETS:
            found.append(rec)
    found.sort(key=lambda r:PREFERRED_TARGETS.index(str(r.get("target_name")).strip().lower()))
    if not found:
        raise RuntimeError("Neither sabinene nor valencene found in normalized Galaxy benchmark")
    return found

def collect_uniprot(rec):
    out=[]
    for rxn in rec.get("reactions",[]):
        for acc in rxn.get("uniprot",[]) or []:
            acc=str(acc).strip()
            if acc and acc not in out:
                out.append(acc)
    return out

def collect_ecs(rec):
    out=[]
    for rxn in rec.get("reactions",[]):
        for ec in rxn.get("ec_numbers",[]) or []:
            ec=str(ec).strip()
            if ec and ec not in out:
                out.append(ec)
    return out

def search_reviewed_uniprot_by_ec(ec, *, timeout=30.0, size=10):
    query=f"ec:{ec} AND reviewed:true"
    params=urllib.parse.urlencode({
        "query":query,
        "fields":"accession,protein_name,organism_name,length",
        "format":"json",
        "size":int(size),
    })
    req=urllib.request.Request(
        UNIPROT_SEARCH+"?"+params,
        headers={"User-Agent":"SynBioCrow/2.3 DBTL case study"},
    )
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        data=json.loads(resp.read().decode("utf-8"))
    hits=[]
    for row in data.get("results",[]) or []:
        acc=str(row.get("primaryAccession") or "").strip()
        if acc:
            hits.append(acc)
    return hits

def resolve_protein_for_record(rec, client):
    explicit=collect_uniprot(rec)
    tried=[]
    for acc in explicit:
        tried.append({"mode":"galaxy_uniprot","accession":acc})
        try:
            p=client.fetch(acc)
            if p.sequence:
                return p,{
                    "resolution_mode":"galaxy_uniprot",
                    "galaxy_uniprot_accessions":explicit,
                    "ec_numbers":collect_ecs(rec),
                    "selected_accession":acc,
                    "tried":tried,
                }
        except Exception as exc:
            tried[-1]["error"]=f"{type(exc).__name__}: {exc}"

    # Provenance-safe fallback: use literature EC annotations to find reviewed UniProt entries.
    ecs=collect_ecs(rec)
    for ec in ecs:
        try:
            accessions=search_reviewed_uniprot_by_ec(ec)
        except Exception as exc:
            tried.append({"mode":"ec_reviewed_search","ec":ec,"error":f"{type(exc).__name__}: {exc}"})
            continue
        tried.append({"mode":"ec_reviewed_search","ec":ec,"accessions":accessions})
        for acc in accessions:
            try:
                p=client.fetch(acc)
                if p.sequence:
                    return p,{
                        "resolution_mode":"reviewed_uniprot_by_literature_ec",
                        "galaxy_uniprot_accessions":explicit,
                        "ec_numbers":ecs,
                        "selected_ec":ec,
                        "selected_accession":acc,
                        "tried":tried,
                    }
            except Exception as exc:
                tried.append({"mode":"ec_reviewed_fetch","ec":ec,"accession":acc,
                              "error":f"{type(exc).__name__}: {exc}"})
    return None,{
        "resolution_mode":"ABSTAIN_NO_PROVENANCE_BACKED_PROTEIN",
        "galaxy_uniprot_accessions":explicit,
        "ec_numbers":ecs,
        "tried":tried,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--normalized-benchmark",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    payload=json.loads(Path(args.normalized_benchmark).read_text())
    client=UniProtSequenceClient(timeout=30.0,user_agent="SynBioCrow/2.3 DBTL case study")

    chosen=None
    protein=None
    resolution=None
    attempts=[]
    for rec in preferred_records(payload):
        print("TRY_PATHWAY",rec.get("pathway_id"),rec.get("target_name"),flush=True)
        p,res=resolve_protein_for_record(rec,client)
        attempts.append({
            "pathway_id":rec.get("pathway_id"),
            "target_name":rec.get("target_name"),
            "resolution":res,
        })
        if p is not None:
            chosen=rec; protein=p; resolution=res
            break

    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    if protein is None:
        result={
            "schema":"synbiocrow.dbtl_sequence_backed_build.v2",
            "status":"ABSTAIN_NO_PROVENANCE_BACKED_PROTEIN",
            "attempts":attempts,
            "note":"Neither preferred Galaxy pathway yielded an explicit UniProt sequence or a reviewed UniProt protein resolvable from its literature EC annotations.",
        }
        (out/"dbtl_sequence_backed_build.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0

    optimized=optimize_protein_sequence(
        protein.sequence,
        profile_name="ecoli_k12_simple_preferred",
        include_stop=True,
    )
    qc=sequence_qc(optimized.dna_sequence)

    result={
        "schema":"synbiocrow.dbtl_sequence_backed_build.v2",
        "status":"COMPLETE_SYNTHETIC_CDS_DESIGN",
        "pathway_id":chosen.get("pathway_id"),
        "target_name":chosen.get("target_name"),
        "literature_doi":(chosen.get("literature") or {}).get("doi"),
        "protein_resolution":resolution,
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
            "sequence_qc":{
                "pass_qc":qc.pass_qc,
                "length":qc.length,
                "gc_fraction":qc.gc_fraction,
                "forbidden_motifs":list(qc.forbidden_motifs),
            },
            "cassette_status":"ABSTAIN_MISSING_VERIFIED_REGULATORY_SEQUENCES",
            "note":"The CDS is newly designed from a provenance-backed protein sequence; it is not represented as a native CDS accession. Full cassette assembly remains blocked until verified regulatory-part sequences are supplied."
        },
        "pathway_attempts":attempts,
    }

    (out/"dbtl_sequence_backed_build.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
