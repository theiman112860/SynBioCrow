#!/usr/bin/env python3
"""Bootstrap and verify the pinned RetroBioCat2 source-molecule database."""
import argparse, hashlib, json, os, sqlite3, time, shutil
from pathlib import Path
import requests

def file_sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def inspect(db):
    con=sqlite3.connect(str(db))
    try:
        tables={r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        counts={}
        for t in ("building_blocks","metabolites"):
            if t in tables:
                counts[t]=con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        return sorted(tables),counts
    finally: con.close()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    ap.add_argument("--candidate-db",action="append",default=[])
    a=ap.parse_args()
    from rbc2.configs.data_path import path_to_data_folder
    db=Path(path_to_data_folder)/"buyability"/"source_mols.db"
    before={}
    if db.exists():
        try:
            tables,counts=inspect(db); before={"bytes":db.stat().st_size,"tables":tables,"counts":counts}
        except Exception as e:
            before={"bytes":db.stat().st_size,"error":f"{type(e).__name__}: {e}"}
    valid=bool(before.get("counts",{}).get("building_blocks",0))
    reused_from=None
    if not valid:
        for candidate in a.candidate_db:
            cp=Path(candidate)
            if not cp.is_file():
                continue
            try:
                ctables,ccounts=inspect(cp)
            except Exception as exc:
                print(f"[RBC2 DATA] reject candidate {cp}: {type(exc).__name__}: {exc}",flush=True)
                continue
            if ccounts.get("building_blocks",0)>0:
                db.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(cp,db)
                reused_from=str(cp)
                print(f"[RBC2 DATA] reused validated Drive cache {cp} rows={ccounts.get('building_blocks')}",flush=True)
                valid=True
                break
    if not valid:
        if db.exists(): db.unlink()
        db.parent.mkdir(parents=True,exist_ok=True)
        url="https://figshare.com/ndownloader/files/43860240"
        tmp=db.with_suffix(".db.part")
        if tmp.exists(): tmp.unlink()
        last_status=None
        last_headers={}
        for attempt in range(1,9):
            resp=requests.get(url,allow_redirects=True,timeout=120,stream=True)
            last_status=resp.status_code
            last_headers=dict(resp.headers)
            print(f"[RBC2 DATA] attempt={attempt} status={resp.status_code} final_url={resp.url}",flush=True)
            if resp.status_code==202:
                retry=resp.headers.get("Retry-After")
                try: delay=max(2,int(retry)) if retry else min(5*attempt,30)
                except Exception: delay=min(5*attempt,30)
                time.sleep(delay)
                continue
            resp.raise_for_status()
            with tmp.open("wb") as out:
                for chunk in resp.iter_content(1024*1024):
                    if chunk: out.write(chunk)
            magic=tmp.read_bytes()[:16]
            if magic!=b"SQLite format 3\x00":
                preview=tmp.read_bytes()[:200]
                raise RuntimeError(
                    f"Figshare payload is not SQLite: bytes={tmp.stat().st_size} "
                    f"magic={magic!r} preview={preview!r}"
                )
            shutil.move(str(tmp),str(db))
            break
        else:
            raise RuntimeError(
                f"Figshare download never produced a file; "
                f"last_status={last_status} headers={last_headers}"
            )
    tables,counts=inspect(db)
    if "building_blocks" not in tables:
        raise RuntimeError(f"RBC2 database missing building_blocks table: {tables}")
    if counts.get("building_blocks",0)<=0:
        raise RuntimeError("RBC2 building_blocks table is empty")
    report={"schema":"synbiocrow.v24.rbc2-data-readiness.v1","database":str(db),
      "bytes":db.stat().st_size,"sha256":file_sha(db),"tables":tables,"row_counts":counts,
      "prebootstrap":before,"reused_from":reused_from,"execution_ready":True}
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
