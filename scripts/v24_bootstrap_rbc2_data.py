#!/usr/bin/env python3
"""Bootstrap and verify the pinned RetroBioCat2 source-molecule database."""
import argparse, hashlib, json, os, sqlite3
from pathlib import Path

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
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); a=ap.parse_args()
    from rbc2.configs.data_path import path_to_data_folder
    from rbc2.configs.download_data_files.download_source_mols import download_source_mols_db
    db=Path(path_to_data_folder)/"buyability"/"source_mols.db"
    before={}
    if db.exists():
        try:
            tables,counts=inspect(db); before={"bytes":db.stat().st_size,"tables":tables,"counts":counts}
        except Exception as e:
            before={"bytes":db.stat().st_size,"error":f"{type(e).__name__}: {e}"}
    valid=bool(before.get("counts",{}).get("building_blocks",0))
    if not valid:
        if db.exists(): db.unlink()
        download_source_mols_db()
    tables,counts=inspect(db)
    if "building_blocks" not in tables:
        raise RuntimeError(f"RBC2 database missing building_blocks table: {tables}")
    if counts.get("building_blocks",0)<=0:
        raise RuntimeError("RBC2 building_blocks table is empty")
    report={"schema":"synbiocrow.v24.rbc2-data-readiness.v1","database":str(db),
      "bytes":db.stat().st_size,"sha256":file_sha(db),"tables":tables,"row_counts":counts,
      "prebootstrap":before,"execution_ready":True}
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
