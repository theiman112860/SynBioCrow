#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, json, shutil, subprocess, sys, tarfile, tempfile, urllib.request
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
    ap.add_argument("--knime-version",default="4.6.4",choices=["4.6.4"])
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

    compatibility_aliases={}
    if args.smoke_resources:
        # Older RetroPath KNIME components can retain absolute /content defaults
        # even when workflow variables are supplied. Provide auditable aliases to
        # the exact same upstream fixtures; explicit workflow variables remain authoritative.
        for alias,target in (
            (Path("/content/rules.csv"),rules_csv),
            (Path("/content/source.csv"),source),
            (Path("/content/sink.csv"),sink),
        ):
            if alias.exists() or alias.is_symlink():
                alias.unlink()
            alias.symlink_to(target)
            compatibility_aliases[str(alias)]=str(target)
            print(f"[RetroPath bootstrap] compatibility alias {alias} -> {target}",flush=True)

    print("[RetroPath bootstrap] install Colab native libraries required by KNIME headless runtime",flush=True)
    subprocess.run(["apt-get","update","-qq"],check=True)
    subprocess.run([
        "apt-get","install","-y","-qq",
        "libatk1.0-0","libatk-bridge2.0-0","libgtk-3-0","libnss3",
        "libx11-xcb1","libxcomposite1","libxdamage1","libxrandr2",
        "libgbm1","libasound2t64"
    ],check=True)

    # RetroPath's archived KNIME 4.6.4 record was created specifically to
    # preserve the contemporaneous KNIME + extension stack. Do not resolve
    # plugins against today's live update site: that can install newer RDKit
    # nodes into the old KNIME runtime and break the historical workflow.
    print(f"[RetroPath bootstrap] install archived KNIME {args.knime_version} stack from upstream Zenodo record 7515771",flush=True)
    from retropath2_wrapper.knime import Knime
    archive_dir=root/"knime_archive"
    archive_dir.mkdir(parents=True,exist_ok=True)
    meta_url="https://zenodo.org/api/records/7515771"
    with urllib.request.urlopen(meta_url,timeout=60) as fh:
        meta=json.load(fh)
    selected=[]
    for item in meta.get("files",[]):
        key=item.get("key","")
        low=key.lower()
        if (
            ("linux" in low and ("4.6.4" in low or "knime" in low))
            or "updatesite_latest46" in low
            or "trustedcommunitycontributions_4.6" in low
            or ("chemistry" in low and "4.6" in low)
        ):
            selected.append(item)
    if not any("linux" in x.get("key","").lower() for x in selected):
        raise RuntimeError("Zenodo 7515771 did not expose a KNIME 4.6.4 Linux archive")
    if not any("trustedcommunitycontributions_4.6" in x.get("key","").lower() for x in selected):
        raise RuntimeError("Zenodo 7515771 did not expose the frozen KNIME 4.6 trusted-community repository")
    print("[RetroPath bootstrap] archived files: "+", ".join(x.get("key","") for x in selected),flush=True)
    local=[]
    linux_archive=None
    for item in selected:
        key=item["key"]
        dest=archive_dir/Path(key).name
        if not dest.exists():
            download(item["links"]["self"],dest)
        low=key.lower()
        if "linux" in low and linux_archive is None:
            linux_archive=dest
        elif dest.suffix.lower()==".zip":
            local.append(dest)
    if knime.exists():
        shutil.rmtree(knime)
    knime.mkdir(parents=True,exist_ok=True)
    if linux_archive is None:
        raise RuntimeError("No Linux KNIME archive selected")
    print(f"[RetroPath bootstrap] extract frozen KNIME base {linux_archive}",flush=True)
    if tarfile.is_tarfile(linux_archive):
        with tarfile.open(linux_archive,"r:*") as tf:
            tf.extractall(knime)
    else:
        shutil.unpack_archive(str(linux_archive),str(knime))
    kexec=Knime.find_executable(path=str(knime))
    p2_dir=Knime.find_p2_dir(path=str(knime))
    if not kexec or not p2_dir:
        raise RuntimeError("Frozen KNIME base extracted but executable/p2 directory was not found")
    knime_root=str(Path(kexec).parent)
    repos=["jar:file:"+str(p.resolve())+"!/" for p in local]
    if not repos:
        raise RuntimeError("No frozen KNIME update repositories were selected")
    print("[RetroPath bootstrap] install extensions ONLY from archived repositories",flush=True)
    subprocess.run([
        str(kexec),"-nosplash","-consoleLog",
        "-application","org.eclipse.equinox.p2.director",
        "-repository",",".join(repos),
        "-bundlepool",str(p2_dir),"-destination",knime_root,
        "-i",",".join(Knime.PLUGINS)
    ],check=True)
    kexec=Knime.find_executable(path=str(knime))
    if not kexec:
        raise RuntimeError("Archived KNIME install returned but no executable was found")

    payload={
        "knime_install":str(knime),
        "knime_version":args.knime_version,
        "knime_executable":str(kexec),
        "bootstrap_complete":True,
        "rules_file":str(rules_csv) if rules_csv else None,
        "sink_file":str(sink) if sink else None,
        "source_file":str(source) if source else None,
        "resource_kind":"UPSTREAM_FUNCTIONAL_TEST_FIXTURES" if args.smoke_resources else "NONE",
        "workflow_compatibility_aliases":compatibility_aliases,
        "knime_provenance":"ZENODO_7515771_FROZEN_REPOSITORIES",
        "knime_archive_files":[x.get("key","") for x in selected],
    }
    out=root/"synbiocrow_retropath_bootstrap.json"
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True))
    print(f"[RetroPath bootstrap] manifest={out}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
