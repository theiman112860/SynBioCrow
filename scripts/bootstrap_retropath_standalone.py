#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

RELEASE_URL="https://github.com/TraceLD/retropath/releases/download/v0.0.1-alpha/retropath_1.0.0-alpha_linux-x64.zip"
RELEASE_TAG="v0.0.1-alpha"
UPSTREAM_REPO="https://github.com/TraceLD/retropath"
UPSTREAM_COMMIT="a8fe50c8da283d99688462c6eb828a9b65a7e00f"

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def download(url:str,dest:Path)->None:
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size>0:
        print(f"[RetroPath standalone] cache hit {dest} bytes={dest.stat().st_size}",flush=True)
        return
    part=dest.with_suffix(dest.suffix+".part")
    offset=part.stat().st_size if part.exists() else 0
    req=urllib.request.Request(url)
    if offset:
        req.add_header("Range",f"bytes={offset}-")
    print(f"[RetroPath standalone] download {url} resume_from={offset}",flush=True)
    with urllib.request.urlopen(req,timeout=120) as resp:
        mode="ab" if offset and getattr(resp,"status",200)==206 else "wb"
        if mode=="wb" and part.exists():
            part.unlink()
        with part.open(mode) as out:
            shutil.copyfileobj(resp,out,length=8*1024*1024)
    part.replace(dest)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="/content/retropath_standalone")
    ap.add_argument("--cache-dir",default=None)
    ap.add_argument("--rules",required=True)
    ap.add_argument("--source",required=True)
    ap.add_argument("--sink",required=True)
    ap.add_argument("--smoke-max-steps",type=int,default=2)
    ap.add_argument("--smoke-max-structures",type=int,default=20)
    args=ap.parse_args()

    root=Path(args.root)
    cache=Path(args.cache_dir) if args.cache_dir else root/"cache"
    root.mkdir(parents=True,exist_ok=True)
    cache.mkdir(parents=True,exist_ok=True)
    archive=cache/"retropath_1.0.0-alpha_linux-x64.zip"
    download(RELEASE_URL,archive)
    digest=sha256_file(archive)
    print(f"[RetroPath standalone] archive bytes={archive.stat().st_size} sha256={digest}",flush=True)

    install=root/"runtime"
    if install.exists():
        shutil.rmtree(install)
    install.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(install)

    candidates=list(install.rglob("RetroPath.Cli"))
    if not candidates:
        raise RuntimeError("RetroPath.Cli not found in standalone Linux release")
    exe=candidates[0]
    exe.chmod(exe.stat().st_mode | 0o111)
    print(f"[RetroPath standalone] executable={exe}",flush=True)

    smoke_out=root/"smoke"
    if smoke_out.exists():
        shutil.rmtree(smoke_out)
    cmd=[
        str(exe),str(Path(args.rules).resolve()),str(Path(args.source).resolve()),
        str(Path(args.sink).resolve()),str(args.smoke_max_steps),
        "--source-mw","1000","--min-diameter","0","--max-diameter","1000",
        "--max-structures",str(args.smoke_max_structures),"--output-dir",str(smoke_out),
    ]
    print("[RetroPath standalone] smoke command: "+" ".join(cmd),flush=True)
    proc=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(proc.stdout,flush=True)
    if proc.returncode!=0:
        raise RuntimeError(f"RetroPath standalone smoke failed rc={proc.returncode}")
    result=smoke_out/"results.csv"
    if not result.is_file():
        raise RuntimeError("RetroPath standalone smoke did not produce results.csv")

    payload={
        "backend_id":"retropath_standalone",
        "bootstrap_complete":True,
        "execution_ready":True,
        "certification_ready":False,
        "equivalence_status":"PENDING_CANONICAL_FIXTURE_COMPARISON",
        "knime_required":False,
        "upstream_repo":UPSTREAM_REPO,
        "upstream_commit":UPSTREAM_COMMIT,
        "release_tag":RELEASE_TAG,
        "release_url":RELEASE_URL,
        "release_archive":str(archive),
        "release_archive_sha256":digest,
        "executable":str(exe),
        "smoke_results":str(result),
        "rules_file":str(Path(args.rules).resolve()),
        "source_file":str(Path(args.source).resolve()),
        "sink_file":str(Path(args.sink).resolve()),
        "smoke_max_steps":args.smoke_max_steps,
        "smoke_max_structures":args.smoke_max_structures,
    }
    out=root/"synbiocrow_retropath_standalone.json"
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True),flush=True)
    print(f"RETROPATH STANDALONE SMOKE PASS results={result}",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
