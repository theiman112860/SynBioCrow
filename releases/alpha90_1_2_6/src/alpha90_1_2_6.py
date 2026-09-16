from __future__ import annotations

from pathlib import Path
import csv, hashlib, io, json, re, shutil, time, zipfile
from collections import Counter
from typing import Iterable

VERSION = "Alpha90.1.2.6"
FROZEN_ENGINE = "Alpha87.11"
EXPECTED = {"LASER": 152, "Golden": 20, "building_blocks_437": 437}
GOLDEN_FROZEN_SHA256 = "98817792e44123eeb14840ba4c743f344eedefebdb1a5cde54a81ed157bb3096"
BIONAVI_COMMIT = "8350a4dc8ca262154787d6a3055ba75bd4e0c746"
RETROPATHRL_COMMIT = "7de91f0236cf3c3dfc2c0455bd7dbcee9f715d2f"
ACS_S2S4_URL = "https://acs.figshare.com/ndownloader/files/20493042"
BIONAVI_ARCHIVE_URL = f"https://codeload.github.com/prokia/BioNavi-NP/zip/{BIONAVI_COMMIT}"
RETROPATHRL_ARCHIVE_URL = f"https://codeload.github.com/brsynth/RetroPathRL/zip/{RETROPATHRL_COMMIT}"


def sha256_path(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def progress(label: str, frac: float, t0: float, extra: str = "") -> None:
    frac = max(0.0, min(1.0, float(frac)))
    elapsed = time.time() - t0
    eta = None if frac <= 0.01 else max(0.0, elapsed / frac - elapsed)
    eta_s = "estimating" if eta is None else f"{eta/60:.1f}m"
    suffix = f" | {extra}" if extra else ""
    print(f"[ALPHA90.1.2.6] {frac*100:5.1f}% elapsed={elapsed/60:.1f}m ETA={eta_s} | {label}{suffix}", flush=True)


def suppress_rdkit_warnings() -> None:
    try:
        from rdkit import RDLogger
        RDLogger.DisableLog("rdApp.warning")
        RDLogger.DisableLog("rdApp.info")
    except Exception:
        pass


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try: return data.decode(enc)
        except UnicodeDecodeError: pass
    return data.decode("utf-8", errors="ignore")


def _sniff(text: str) -> str:
    try: return csv.Sniffer().sniff(text[:10000], delimiters=",\t;").delimiter
    except Exception: return "\t" if "\t" in text[:10000] else ","


def read_table_bytes(data: bytes) -> tuple[list[str], list[dict]]:
    text = _decode(data)
    r = csv.DictReader(io.StringIO(text), delimiter=_sniff(text))
    fields = [str(x or "").strip() for x in (r.fieldnames or [])]
    rows = []
    for raw in r:
        row = {str(k or "").strip(): ("" if v is None else str(v).strip()) for k,v in raw.items()}
        if any(row.values()): rows.append(row)
    return fields, rows


def iter_tabular(path: Path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as zf:
            for info in zf.infolist():
                if info.is_dir() or info.file_size > 50_000_000: continue
                if info.filename.lower().endswith((".csv", ".tsv", ".txt")) and "__macosx" not in info.filename.lower():
                    try: yield info.filename, zf.read(info)
                    except Exception: pass
    elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
        yield p.name, p.read_bytes()


def load_prior_all_outputs(path: Path) -> tuple[dict, dict[str, bytes]]:
    p = Path(path)
    files: dict[str, bytes] = {}
    if p.is_dir():
        for f in p.rglob("*"):
            if f.is_file(): files[f.name] = f.read_bytes()
    elif p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as zf:
            for info in zf.infolist():
                if not info.is_dir(): files[Path(info.filename).name] = zf.read(info)
    else:
        raise RuntimeError("Prior Alpha90.1.2.5.1 output must be a ZIP or directory")
    candidates = [v for k,v in files.items() if k.endswith("summary.json")]
    if not candidates: raise RuntimeError("Prior 1.2.5.1 summary JSON not found")
    summary = json.loads(candidates[0].decode("utf-8"))
    if summary.get("version") != "Alpha90.1.2.5.1": raise RuntimeError("Expected Alpha90.1.2.5.1 prior outputs")
    g = summary.get("certification",{}).get("Golden",{})
    if g.get("status") != "PASS" or g.get("count") != 20 or g.get("sha256") != GOLDEN_FROZEN_SHA256:
        raise RuntimeError("Frozen Golden-20 contract failed")
    return summary, files


def frozen_golden(prior: dict) -> dict:
    g = dict(prior["certification"]["Golden"])
    g.update(status="PASS", count=20, sha256=GOLDEN_FROZEN_SHA256, method="frozen_from_alpha90_1_2_4")
    return g


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


def _truthy(v: str) -> bool:
    return str(v).strip().lower() in {"1","true","yes","y","t","pass","present"}


def _identity(row: dict) -> str:
    for k in ("inchikey","inchi","compound","name","filename","all_names"):
        if str(row.get(k,"")).strip(): return f"{k}:{row[k].strip()}"
    return "row:"+json.dumps(row, sort_keys=True)


def _laser_tables(s2s4_zip: Path) -> list[tuple[str,list[str],list[dict],str]]:
    out=[]
    for member,data in iter_tabular(s2s4_zip):
        if "supplementary_data_2" not in member.lower() and "supplementary_data_3" not in member.lower(): continue
        fields,rows=read_table_bytes(data)
        if "source" in fields and len(rows) >= 150:
            out.append((member,fields,rows,sha256_bytes(data)))
    return out


def laser_seven_exclusion_audit(s2s4_zip: Path, source_text_roots: Iterable[Path] = ()) -> tuple[dict,list[dict],list[dict]]:
    evidence=[]; candidates=[]; source_hints=[]
    tables=_laser_tables(Path(s2s4_zip))
    if not tables:
        return {"status":"BLOCK","count":None,"reason":"Authentic S2/S3 LASER table not found"}, evidence, source_hints
    for member,fields,rows,sha in tables:
        laser=[r for r in rows if str(r.get("source","")).strip().upper()=="LASER"]
        evidence.append({"kind":"population","member":member,"sha256":sha,"total_rows":len(rows),"laser_rows":len(laser),"mbe_legacy_rows":sum(str(r.get('source','')).strip().upper()=="MBE_LEGACY" for r in rows)})
        for f in fields:
            if f in {"source","name","inchi","inchikey","compound","all_names","filename"}: continue
            vals=[str(r.get(f,"")).strip() for r in laser]
            counts=Counter(vals)
            if 1 < len(counts) <= 12:
                for value,n in counts.items():
                    kept=len(laser)-n
                    if n==7 or kept==152:
                        excluded=[_identity(r) for r in laser if str(r.get(f,"")).strip()==value]
                        candidates.append({"member":member,"field":f,"rule":f"{f} != {value!r}","excluded_count":n,"kept_count":kept,"excluded":excluded,"basis":"single_source_value","certifying":False})
            present=[bool(v) for v in vals]
            n_absent=present.count(False)
            if n_absent==7 or len(laser)-n_absent==152:
                excluded=[_identity(r) for r in laser if not str(r.get(f,"")).strip()]
                candidates.append({"member":member,"field":f,"rule":f"nonempty({f})","excluded_count":n_absent,"kept_count":len(laser)-n_absent,"excluded":excluded,"basis":"field_presence","certifying":False})
        for f in ("in_sink","file_to_add"):
            if f in fields:
                tr=[r for r in laser if _truthy(r.get(f,""))]
                fa=[r for r in laser if not _truthy(r.get(f,""))]
                evidence.append({"kind":"boolean_profile","member":member,"field":f,"true_count":len(tr),"false_count":len(fa)})
    terms=("laser","in_sink","file_to_add","supplementary_data_2","supplementary_data_3","152")
    for root in map(Path,source_text_roots):
        if not root.exists(): continue
        files=[root] if root.is_file() else list(root.rglob("*"))
        for p in files:
            if not p.is_file() or p.suffix.lower() not in {".py",".md",".txt",".yaml",".yml",".json",".csv",".tsv"}: continue
            if p.stat().st_size > 2_000_000: continue
            text=p.read_text(encoding="utf-8",errors="ignore"); low=text.lower(); hits=[t for t in terms if t in low]
            if len(hits)>=2:
                lines=text.splitlines()
                for i,line in enumerate(lines):
                    if any(t in line.lower() for t in hits):
                        source_hints.append({"path":str(p),"line":i+1,"terms":hits,"excerpt":"\n".join(lines[max(0,i-2):min(len(lines),i+3)])[:1500]})
                        if len(source_hints)>=100: break
            if len(source_hints)>=100: break
        if len(source_hints)>=100: break
    rule_files=[]
    for root in map(Path,source_text_roots):
        if root.exists(): rule_files += ([root] if root.is_file() and root.name=="laser_152_source_rule.json" else list(root.rglob("laser_152_source_rule.json")) if root.is_dir() else [])
    valid=[]
    for rf in rule_files:
        try:
            rule=json.loads(rf.read_text())
            if rule.get("source_evidence") and rule.get("field") and "exclude_values" in rule:
                for member,fields,rows,sha in tables:
                    laser=[r for r in rows if str(r.get("source","")).strip().upper()=="LASER"]
                    f=rule["field"]; ex={str(x) for x in rule["exclude_values"]}; kept=[r for r in laser if str(r.get(f,"")).strip() not in ex]
                    if len(kept)==152: valid.append({"count":152,"method":"source_rule","field":f,"exclude_values":sorted(ex),"source_evidence":rule["source_evidence"],"source_member":member,"sha256":sha})
        except Exception: pass
    uniq={(v['field'],tuple(v['exclude_values']),v['source_evidence']) for v in valid}
    cert={"status":"PASS",**valid[0]} if len(uniq)==1 else {"status":"BLOCK","count":None,"observed_laser_rows":sorted({e.get('laser_rows') for e in evidence if e.get('kind')=='population'}),"candidate_seven_exclusion_rules":len(candidates),"reason":"159 LASER-labeled rows are confirmed, but no unique source-evidenced exclusion rule has yet certified the seven excluded projects. Diagnostic count matches are not accepted."}
    return cert,evidence,candidates+source_hints


def _canonical_members_from_file(path: Path) -> tuple[int,list[str]]:
    p=Path(path); data=p.read_bytes(); fields,rows=read_table_bytes(data)
    if fields and rows:
        ids=[]
        for r in rows:
            v=""
            for k in ("mol","smiles","inchi","inchikey","metabolite_id","compound_id","id","name"):
                if k in r and r[k].strip(): v=f"{k}:{r[k].strip()}"; break
            if not v: v=json.dumps(r,sort_keys=True)
            ids.append(v)
        return len(dict.fromkeys(ids)),ids
    lines=[x.strip() for x in _decode(data).splitlines() if x.strip()]
    if lines and lines[0].lower() in {"mol","smiles","inchi","name"}: lines=lines[1:]
    return len(dict.fromkeys(lines)),lines


def _text_references(root: Path, relative_path: str) -> list[dict]:
    out=[]; target=relative_path.replace('\\','/'); base=Path(target).name
    if not root.exists(): return out
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".py",".md",".yaml",".yml",".txt",".json"}: continue
        if p.stat().st_size>2_000_000: continue
        text=p.read_text(encoding="utf-8",errors="ignore")
        if target in text or base in text:
            for i,line in enumerate(text.splitlines()):
                if target in line or base in line:
                    out.append({"path":str(p),"line":i+1,"excerpt":line[:1200]})
                    if len(out)>=50: return out
    return out


def building_block_provenance_audit(source_roots: Iterable[Path]) -> tuple[dict,list[dict],list[dict]]:
    evidence=[]; exact=[]; hints=[]
    for root in map(Path,source_roots):
        if not root.exists(): continue
        files=[root] if root.is_file() else list(root.rglob("*"))
        for p in files:
            if not p.is_file() or p.suffix.lower() not in {".csv",".tsv",".txt"}: continue
            low=str(p).lower()
            if not any(x in low for x in ("building","precursor","sink","metabol","iml1515")): continue
            if p.stat().st_size>20_000_000: continue
            try: n,members=_canonical_members_from_file(p)
            except Exception: continue
            rel=str(p.relative_to(root)) if root.is_dir() else p.name; refs=_text_references(root,rel) if root.is_dir() else []
            role="bionavi_default_runtime_library" if "bio_building_blocks_all" in low else "full_iml1515_sink_control" if "iml1515" in low and "sink" in low else "building_or_precursor_candidate" if "building" in low or "precursor" in low else ""
            rec={"path":str(p),"relative_path":rel,"count":n,"sha256":sha256_path(p),"role":role,"source_references":len(refs)}; evidence.append(rec)
            if refs: hints.extend([{**r,"referenced_artifact":rel} for r in refs])
            if n==437 and role!="full_iml1515_sink_control" and refs: exact.append({"count":437,"path":str(p),"relative_path":rel,"sha256":sha256_path(p),"method":"source_referenced_exact_437_artifact","references":refs[:10]})
        terms=("iml1515","cytosol","precursor","building block","building_block","sink")
        for p in files:
            if not p.is_file() or p.suffix.lower() not in {".py",".md",".txt",".yaml",".yml"}: continue
            if p.stat().st_size>2_000_000: continue
            text=p.read_text(encoding="utf-8",errors="ignore"); low=text.lower()
            if sum(t in low for t in terms)>=2:
                for i,line in enumerate(text.splitlines()):
                    if any(t in line.lower() for t in terms):
                        hints.append({"path":str(p),"line":i+1,"excerpt":"\n".join(text.splitlines()[max(0,i-2):i+3])[:1500]})
                        if len(hints)>=150: break
            if len(hints)>=150: break
    unique={(x['sha256'],x['relative_path']) for x in exact}
    cert={"status":"PASS",**exact[0]} if len(unique)==1 else {"status":"BLOCK","count":None,"reason":"Multiple distinct source-referenced 437-member artifacts found; canonical identity is ambiguous.","candidates":exact} if len(unique)>1 else {"status":"BLOCK","count":None,"reason":"No source-referenced artifact or source-defined derivation independently certifies exactly 437 precursor metabolites. The full iML1515 sink and BioNavi default runtime library remain non-certifying controls."}
    return cert,evidence,hints


def write_csv(path: Path, rows: list[dict]) -> None:
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("status\nNO_RECORDS\n",encoding="utf-8"); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k:(json.dumps(v,sort_keys=True) if isinstance(v,(list,dict)) else v) for k,v in r.items()})


def run(outdir: Path, prior_outputs: Path, s2s4_zip: Path, source_roots: Iterable[Path]) -> tuple[dict,Path]:
    t0=time.time(); out=Path(outdir); out.mkdir(parents=True,exist_ok=True); suppress_rdkit_warnings(); progress("validate frozen prior certification",0.05,t0)
    prior,_=load_prior_all_outputs(prior_outputs); golden=frozen_golden(prior); progress("159 -> 152 LASER seven-exclusion audit",0.22,t0)
    laser,laser_ev,laser_diag=laser_seven_exclusion_audit(Path(s2s4_zip),source_roots); progress("437 precursor provenance reconstruction",0.62,t0)
    bb,bb_ev,bb_hints=building_block_provenance_audit(source_roots); progress("semantic certification",0.84,t0)
    allowed=golden.get("status")=="PASS" and laser.get("status")=="PASS" and bb.get("status")=="PASS"
    summary={"version":VERSION,"frozen_engine":FROZEN_ENGINE,"state":"READY_FOR_ALPHA90_2" if allowed else "BLOCKED_PENDING_PROVENANCE_CERTIFICATION","alpha90_2_allowed":allowed,"run_synbiocrow":False,"external_benchmark_tuning":False,"certification":{"Golden":golden,"LASER":laser,"building_blocks_437":bb},"contracts":{"alpha87_11_modified":False,"alpha87_11_executed":False,"benchmark_scoring_executed":False,"publication_prose_reconstruction":False,"count_fitting_allowed":False}}
    (out/"alpha90_1_2_6_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    write_csv(out/"alpha90_1_2_6_laser_population_evidence.csv",laser_ev); write_csv(out/"alpha90_1_2_6_laser_seven_exclusion_diagnostics.csv",laser_diag); write_csv(out/"alpha90_1_2_6_building_block_artifacts.csv",bb_ev); write_csv(out/"alpha90_1_2_6_building_block_provenance_hints.csv",bb_hints)
    write_csv(out/"alpha90_1_2_6_semantic_audit.csv",[{"check":"Golden 20 frozen SHA","status":"PASS"},{"check":"LASER 152 source-evidenced","status":laser.get("status")},{"check":"437 source-evidenced","status":bb.get("status")},{"check":"Alpha87.11 unchanged","status":"PASS"},{"check":"benchmark scoring not executed","status":"PASS"},{"check":"external benchmark tuning disabled","status":"PASS"},{"check":"count fitting forbidden","status":"PASS"}])
    (out/"ALPHA90_1_2_6_CERTIFICATION_REPORT.md").write_text("\n".join([f"# SynBioCrow {VERSION} certification report","",f"State: **{summary['state']}**",f"Alpha90.2 allowed: **{allowed}**","",f"- Golden 20: **{golden['status']}** (frozen)",f"- LASER 152: **{laser['status']}**",f"- Building blocks 437: **{bb['status']}**","","## LASER","```json",json.dumps(laser,indent=2),"```","","## 437 building blocks","```json",json.dumps(bb,indent=2),"```","","No Alpha87.11 execution, benchmark scoring, or benchmark tuning was performed."]),encoding="utf-8")
    progress("package ALL_OUTPUTS",0.94,t0); zpath=out.parent/(out.name+"_ALL_OUTPUTS.zip")
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(out.rglob("*")):
            if p.is_file(): zf.write(p,Path(out.name)/p.relative_to(out))
    progress("complete",1.0,t0,summary["state"]); return summary,zpath
