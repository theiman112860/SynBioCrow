#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, json, shutil, subprocess, sys, urllib.request
from pathlib import Path

BASE="https://raw.githubusercontent.com/brsynth/retropath2-wrapper/master/tests/data"

def download(url:str,path:Path)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    print(f"[RetroPath bootstrap] download {url}",flush=True)
    urllib.request.urlretrieve(url,path)
    print(f"[RetroPath bootstrap] {path} bytes={path.stat().st_size}",flush=True)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="/content/retropath2_runtime")
    ap.add_argument("--knime-version",default="4.7.0",choices=["4.6.4","4.7.0"])
    ap.add_argument("--smoke-resources",action="store_true")
    args=ap.parse_args()
    root=Path(args.root)
    root.mkdir(parents=True,exist_ok=True)
    knime=root/"knime"
    resources=root/"resources"

    if args.smoke_resources:
        rules_gz=resources/"rules_d12_7325.csv.gz"
        rules_csv=resources/"rules_d12_7325.csv"
        sink=resources/"sink.csv"
        source=resources/"lycopene_source.csv"
        if not rules_gz.exists():
            download(f"{BASE}/rules_d12_7325.csv.gz",rules_gz)
        if not rules_csv.exists():
            print(f"[RetroPath bootstrap] decompress {rules_gz}",flush=True)
            with gzip.open(rules_gz,"rb") as src, rules_csv.open("wb") as dst:
                shutil.copyfileobj(src,dst)
        if not sink.exists():
            download(f"{BASE}/lycopene/in/sink.csv",sink)
        if not source.exists():
            download(f"{BASE}/lycopene/in/source.csv",source)
    else:
        rules_csv=sink=source=None

    print(f"[RetroPath bootstrap] install/check KNIME {args.knime_version}",flush=True)
    subprocess.run([
        sys.executable,"-m","retropath2_wrapper.knime","online",
        "--kinstall",str(knime),"--kver",args.knime_version
    ],check=True)

    payload={
        "knime_install":str(knime),
        "rules_file":str(rules_csv) if rules_csv else None,
        "sink_file":str(sink) if sink else None,
        "source_file":str(source) if source else None,
        "resource_kind":"UPSTREAM_FUNCTIONAL_TEST_FIXTURES" if args.smoke_resources else "NONE",
    }
    out=root/"synbiocrow_retropath_bootstrap.json"
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True))
    print(f"[RetroPath bootstrap] manifest={out}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
