# SynBioCrow Alpha90.1.2.3 canonical benchmark acquisition/certification repair
from __future__ import annotations
from pathlib import Path
import csv, hashlib, io, json, os, re, tarfile, time, zipfile
from typing import Iterable

VERSION='Alpha90.1.2.3'
FROZEN_ENGINE='Alpha87.11'
EXPECTED={'LASER':152,'Golden':20,'building_blocks_437':437}
ACS_DOI='10.1021/acssynbio.9b00447'
BIONAVI_DOI='10.1038/s41467-022-30970-9'


def sha256_path(p: Path, chunk=1024*1024):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()


def progress(label, frac, t0, extra=''):
    frac=max(0,min(1,float(frac))); elapsed=time.time()-t0
    eta=(elapsed/frac-elapsed) if frac>0.01 else None
    eta_s='estimating' if eta is None else f'{eta/60:.1f}m'
    print(f'[ALPHA90.1.2.3] {frac*100:5.1f}% elapsed={elapsed/60:.1f}m ETA={eta_s} | {label}' + (f' | {extra}' if extra else ''), flush=True)


def suppress_rdkit_warnings():
    try:
        from rdkit import RDLogger
        RDLogger.DisableLog('rdApp.warning')
        RDLogger.DisableLog('rdApp.info')
    except Exception:
        pass


def bounded_drive_discovery(roots: Iterable[Path], name_terms=(), max_files=5000, max_depth=6, max_bytes=3_000_000_000):
    out=[]
    terms=[t.lower() for t in name_terms]
    for root in roots:
        root=Path(root)
        if not root.exists(): continue
        base_parts=len(root.parts)
        try:
            iterator=root.rglob('*')
        except Exception:
            continue
        for p in iterator:
            if len(out)>=max_files: break
            try:
                if len(p.parts)-base_parts>max_depth or not p.is_file(): continue
                st=p.stat()
                if st.st_size>max_bytes: continue
                nm=p.name.lower()
                if terms and not any(t in nm for t in terms): continue
                out.append(p)
            except OSError: continue
    out.sort(key=lambda p:(-(p.stat().st_mtime if p.exists() else 0), str(p)))
    return out


def _archive_members(p: Path):
    suf=p.name.lower()
    if suf.endswith('.zip'):
        with zipfile.ZipFile(p) as z:
            for i in z.infolist():
                if i.is_dir() or i.file_size>100_000_000: continue
                try: yield i.filename, z.read(i)
                except Exception: continue
    elif suf.endswith(('.tar.gz','.tgz','.tar')):
        mode='r:gz' if suf.endswith(('.tar.gz','.tgz')) else 'r:'
        with tarfile.open(p,mode) as t:
            for m in t.getmembers():
                if not m.isfile() or m.size>100_000_000: continue
                try:
                    f=t.extractfile(m)
                    if f: yield m.name, f.read()
                except Exception: continue


def recursive_members(p: Path, max_nested=2):
    for name,b in _archive_members(p):
        yield str(p),name,b
        low=name.lower()
        if max_nested>0 and low.endswith(('.zip','.tar.gz','.tgz','.tar')) and len(b)<150_000_000:
            tmp=Path('/tmp')/('a90123_'+hashlib.sha256((str(p)+name).encode()).hexdigest()[:16]+Path(name).suffix)
            try:
                tmp.write_bytes(b)
                for a,n,b2 in recursive_members(tmp,max_nested-1):
                    yield f'{p}!{name}',n,b2
            except Exception: pass
            finally:
                try: tmp.unlink()
                except Exception: pass


def _text(b):
    for enc in ('utf-8','latin-1'):
        try: return b.decode(enc,errors='ignore')
        except Exception: pass
    return ''


def _structure_tokens(txt):
    inchis=set(re.findall(r'InChI=1S?/[A-Za-z0-9+\-(),./\\;?]+',txt))
    smis=set()
    for line in txt.splitlines():
        if len(line)>2000: continue
        fields=re.split(r'[,\t;]',line)
        for s in fields:
            s=s.strip().strip('"\'')
            if 2<=len(s)<=350 and re.fullmatch(r'[A-Za-z0-9@+\-\[\]\(\)=#$\\/.:%]+',s or '') and any(c in s for c in 'CONPSFIBrcnop[]=#'):
                if '/' not in s or s.startswith(('InChI=','C','N','O','c','n','[')):
                    smis.add(s)
    return inchis,smis


def acquire_original_retropathrl_supporting_data(dest: Path):
    """Best-effort download of original ACS Figshare supporting artifacts."""
    dest=Path(dest); dest.mkdir(parents=True,exist_ok=True)
    try:
        import requests
    except Exception:
        return []
    article_ids={11477925}
    for url in ['https://api.figshare.com/v2/collections/4800855/articles','https://api.figshare.com/v2/collections/4800855']:
        try:
            r=requests.get(url,timeout=20); r.raise_for_status(); obj=r.json()
            if isinstance(obj,list):
                for x in obj:
                    if isinstance(x,dict) and x.get('id'): article_ids.add(int(x['id']))
            elif isinstance(obj,dict):
                for x in obj.get('articles',[]) or []:
                    if isinstance(x,dict) and x.get('id'): article_ids.add(int(x['id']))
        except Exception:
            pass
    out=[]
    for aid in sorted(article_ids):
        meta=None
        try:
            r=requests.get('https://api.figshare.com/v2/articles/'+str(aid),timeout=20); r.raise_for_status(); meta=r.json()
        except Exception: pass
        if not isinstance(meta,dict): continue
        for f in meta.get('files',[]) or []:
            name=f.get('name') or f'figshare_{aid}_{f.get("id","file")}'
            dl=f.get('download_url') or f.get('url_private_api')
            if not dl: continue
            low=name.lower()
            if not any(k in low for k in ['supp','sifile','data','golden','laser']): continue
            q=dest/name
            if q.exists() and q.stat().st_size>0: out.append(q); continue
            try:
                with requests.get(dl,stream=True,timeout=60) as rr:
                    rr.raise_for_status()
                    with q.open('wb') as h:
                        for chunk in rr.iter_content(1024*1024):
                            if chunk: h.write(chunk)
                if q.stat().st_size>0: out.append(q)
            except Exception:
                try: q.unlink()
                except Exception: pass
    return out

def scan_candidate_files(files):
    rows=[]
    for p in files:
        p=Path(p); lowp=str(p).lower()
        provenance=('acssynbio.9b00447' in lowp or 'supplementary_data' in lowp or 'sifile' in lowp or 'retropath' in lowp or 'bionavi' in lowp)
        if p.suffix.lower() in ('.zip','.tar','.gz','.tgz') or p.name.lower().endswith('.tar.gz'):
            members=recursive_members(p)
        else:
            try: members=[(str(p),p.name,p.read_bytes())]
            except Exception: members=[]
        for archive,member,b in members:
            low=(archive+' '+member).lower(); txt=_text(b); ich,sm=_structure_tokens(txt)
            rows.append({'archive':archive,'member':member,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'provenance_signal':provenance or any(k in low for k in ['supplementary','sifile','acs','figshare']),'laser_signal':('laser' in low or 'laser' in txt[:20000].lower()),'golden_signal':('golden' in low or 'golden' in txt[:20000].lower()),'building_signal':(any(k in low for k in ['building','sink','iml1515','extended']) or any(k in txt[:20000].lower() for k in ['building block','iml1515','extended library'])),'pathway_signal':any(k in low or k in txt[:20000].lower() for k in ['pathway','sbml','reaction','ec number']),'structure_count':len(ich|sm),'inchi_count':len(ich),'smiles_token_count':len(sm)})
    return rows


def certify(rows):
    result={}; evidence={}
    for kind,expected in EXPECTED.items():
        hits=[]
        for r in rows:
            sig = r['laser_signal'] if kind=='LASER' else r['golden_signal'] if kind=='Golden' else r['building_signal']
            if not (r['provenance_signal'] and sig): continue
            count=r['structure_count']
            if count==expected and (kind!='Golden' or r['pathway_signal']): hits.append((r,count,'exact_structure_count'))
        if hits:
            r,c,method=hits[0]; result[kind]={'status':'PASS','count':c,'sha256':r['sha256'],'source_archive':r['archive'],'source_member':r['member'],'method':method}; evidence[kind]=[h[0] for h in hits[:10]]
        else:
            result[kind]={'status':'BLOCK','count':None,'sha256':None,'reason':f'No provenance-qualified artifact independently satisfied exact frozen count {expected}'}; evidence[kind]=[]
    return result,evidence


def write_csv(path, rows):
    path=Path(path)
    if not rows: path.write_text(''); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)


def run(workdir: Path, candidate_files, prior_summary: Path|None=None):
    suppress_rdkit_warnings(); t0=time.time(); workdir=Path(workdir); workdir.mkdir(parents=True,exist_ok=True)
    progress('validate frozen contract',.05,t0)
    prior={}
    if prior_summary and Path(prior_summary).exists(): prior=json.loads(Path(prior_summary).read_text())
    if prior and prior.get('alpha90_2_allowed') is True:
        raise RuntimeError('Prior artifact unexpectedly says Alpha90.2 allowed; this repair expects a blocked Alpha90.1.2.x input.')
    progress('scan provenance-qualified candidate artifacts',.25,t0,f'n={len(candidate_files)}')
    rows=scan_candidate_files(candidate_files); write_csv(workdir/'alpha90_1_2_3_candidate_audit.csv',rows)
    progress('independently certify exact populations',.62,t0); cert,evidence=certify(rows)
    semantic=[{'check':'Frozen engine preserved','status':'PASS','detail':'Alpha87.11 is not executed or modified.'},{'check':'No external benchmark tuning','status':'PASS','detail':'No model/search thresholds are adjusted from benchmark outcomes.'},{'check':'No prose reconstruction','status':'PASS','detail':'Counts must come from provenance-qualified artifact bytes, never publication prose.'},{'check':'LASER exact scored population','status':cert['LASER']['status'],'detail':'Requires exactly 152 provenance-qualified benchmark structures.'},{'check':'Golden exact reference population','status':cert['Golden']['status'],'detail':'Requires exactly 20 provenance-qualified targets with pathway semantics.'},{'check':'437 building-block library','status':cert['building_blocks_437']['status'],'detail':'Requires exactly 437 provenance-qualified structures tied to the extended/iML1515 library.'}]
    write_csv(workdir/'alpha90_1_2_3_semantic_audit.csv',semantic)
    allpass=all(v['status']=='PASS' for v in cert.values())
    summary={'version':VERSION,'frozen_engine':FROZEN_ENGINE,'state':'CERTIFIED_READY_FOR_ALPHA90_2' if allpass else 'BLOCKED_PENDING_CANONICAL_BENCHMARK_ARTIFACTS','alpha90_2_allowed':allpass,'run_synbiocrow':False,'external_benchmark_tuning':False,'certification':cert,'candidate_files':[str(x) for x in candidate_files]}
    (workdir/'alpha90_1_2_3_summary.json').write_text(json.dumps(summary,indent=2))
    report=['# Alpha90.1.2.3 Original Supporting-Data Acquisition & Canonical Certification Repair','',f"**State:** `{summary['state']}`",'', '## Gates']
    for k,v in cert.items(): report.append(f"- **{k}**: {v['status']}" + (f" — count={v.get('count')}" if v['status']=='PASS' else f" — {v.get('reason')}"))
    report += ['', '## Frozen-contract guarantees','- Alpha87.11 is not executed.','- No benchmark scores are produced.','- No thresholds are tuned against external benchmark outcomes.','- No canonical benchmark is reconstructed from publication prose.','- Alpha90.2 is permitted only if all three gates pass independently.']
    (workdir/'ALPHA90_1_2_3_CERTIFICATION_REPORT.md').write_text('\n'.join(report)+'\n')
    progress('package certification outputs',.90,t0)
    outzip=workdir.parent/(workdir.name+'_ALL_OUTPUTS.zip')
    with zipfile.ZipFile(outzip,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(workdir.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(workdir.parent))
    progress('done',1,t0,outzip.name)
    return summary,outzip
