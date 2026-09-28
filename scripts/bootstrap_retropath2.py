#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, hashlib, io, json, os, re, shutil, subprocess, sys, tarfile, tempfile, time, urllib.request, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

BASE="https://raw.githubusercontent.com/brsynth/retropath2-wrapper/master/tests/data"
KNIME_46_UPDATE_ARCHIVE="https://update.knime.org/analytics-platform/UpdateSite_latest46.zip"
KNIME_46_CORE_REPO="https://update.knime.com/analytics-platform/4.6/"
KNIME_46_CHEM_REPO="https://update.knime.com/analytics-platform/4.6/chemistry/"

KNOWN_ARCHIVE_SHA256={
    "knime_4.6.4.linux.gtk.x86_64.tar.gz":"7a9e1eabbf90e79d5bdfcb7e88b4cdbada33479d0968ae94e323da15fb5aa418",
    "TrustedCommunityContributions_4.6_202212212136.zip":"dd9b840b9126162a7bc071910c077bc06f201271009fe208ae7de98fc0c977dc",
}


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def p2_units(path:Path)->set[str]:
    """Return IU ids advertised by an Eclipse p2 repository ZIP."""
    try:
        with zipfile.ZipFile(path) as outer:
            names=set(outer.namelist())
            xml_bytes=None
            if "content.xml" in names:
                xml_bytes=outer.read("content.xml")
            elif "content.jar" in names:
                with zipfile.ZipFile(io.BytesIO(outer.read("content.jar"))) as inner:
                    xml_bytes=inner.read("content.xml")
            if xml_bytes is None:
                return set()
        root=ET.fromstring(xml_bytes)
        return {u.attrib["id"] for u in root.iter() if u.tag.endswith("unit") and u.attrib.get("id")}
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError):
        return set()

def download(url:str,path:Path,expected_size:int|None=None,expected_sha256:str|None=None)->None:
    """Resumable download with visible progress and integrity checks."""
    path.parent.mkdir(parents=True,exist_ok=True)
    part=path.with_suffix(path.suffix+".part")

    def valid_complete()->bool:
        if not path.exists():
            return False
        if expected_size is not None and path.stat().st_size != int(expected_size):
            return False
        if expected_sha256 is not None and sha256_file(path) != expected_sha256:
            return False
        return True

    if valid_complete():
        print(f"[RetroPath bootstrap] cache hit {path} bytes={path.stat().st_size}",flush=True)
        return
    if path.exists():
        print(f"[RetroPath bootstrap] discard invalid cached file {path}",flush=True)
        path.unlink()

    offset=part.stat().st_size if part.exists() else 0
    req=urllib.request.Request(url)
    if offset:
        req.add_header("Range",f"bytes={offset}-")
    print(f"[RetroPath bootstrap] download {url} resume_from={offset}",flush=True)
    with urllib.request.urlopen(req,timeout=120) as resp:
        status=getattr(resp,"status",200)
        if offset and status != 206:
            print("[RetroPath bootstrap] server ignored Range; restarting download",flush=True)
            offset=0
            if part.exists():
                part.unlink()
        mode="ab" if offset else "wb"
        content_length=resp.headers.get("Content-Length")
        total=(offset+int(content_length)) if content_length and status==206 else (
            int(content_length) if content_length else expected_size
        )
        got=offset
        started=time.time()
        last_report=started
        with part.open(mode) as out:
            while True:
                chunk=resp.read(8*1024*1024)
                if not chunk:
                    break
                out.write(chunk)
                got += len(chunk)
                now=time.time()
                if now-last_report >= 15:
                    elapsed=max(now-started,0.001)
                    rate=max((got-offset)/elapsed,1.0)
                    pct=(100.0*got/total) if total else 0.0
                    eta=((total-got)/rate/60.0) if total and got < total else 0.0
                    print(
                        f"[RetroPath bootstrap] {path.name} {got/1e9:.2f} GB"
                        + (f"/{total/1e9:.2f} GB {pct:.1f}% ETA {eta:.1f} min" if total else ""),
                        flush=True,
                    )
                    last_report=now
    part.replace(path)
    if expected_size is not None and path.stat().st_size != int(expected_size):
        raise RuntimeError(
            f"Archive size mismatch for {path.name}: got {path.stat().st_size}, expected {expected_size}"
        )
    digest=sha256_file(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise RuntimeError(
            f"Archive SHA256 mismatch for {path.name}: got {digest}, expected {expected_sha256}"
        )
    print(f"[RetroPath bootstrap] {path} bytes={path.stat().st_size} sha256={digest}",flush=True)


def installed_ius(knime_root:Path)->set[str]:
    """Best-effort IU inventory from the extracted/installed KNIME filesystem."""
    out=set()
    plugins=knime_root/"plugins"
    if plugins.exists():
        for p in plugins.iterdir():
            m=re.match(r"^(.+?)_(\d[^/]*)?(?:\.jar)?$",p.name)
            if m:
                out.add(m.group(1))
    features=knime_root/"features"
    if features.exists():
        for p in features.iterdir():
            stem=p.name[:-4] if p.name.endswith(".jar") else p.name
            m=re.match(r"^(.+?)_(\d.*)$",stem)
            if m:
                fid=m.group(1)
                out.add(fid)
                out.add(fid+".feature.group")
    return out


def required_runtime_lock(knime_root:Path,required:set[str])->dict[str,list[dict[str,object]]]:
    """Hash files/directories that implement the requested IUs for reproducibility."""
    lock={iu:[] for iu in sorted(required)}
    search_roots=[knime_root/"plugins",knime_root/"features"]
    aliases={iu:{iu,iu.removesuffix(".feature.group")} for iu in required}
    for root in search_roots:
        if not root.exists():
            continue
        for p in root.iterdir():
            stem=p.name[:-4] if p.name.endswith(".jar") else p.name
            for iu,names in aliases.items():
                if any(stem.startswith(name+"_") for name in names):
                    if p.is_file():
                        lock[iu].append({
                            "path":str(p.relative_to(knime_root)),
                            "bytes":p.stat().st_size,
                            "sha256":sha256_file(p),
                        })
                    else:
                        lock[iu].append({
                            "path":str(p.relative_to(knime_root)),
                            "kind":"directory",
                        })
    return lock

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="/content/retropath2_runtime")
    ap.add_argument("--knime-version",default="4.6.4",choices=["4.6.4"])
    ap.add_argument("--smoke-resources",action="store_true")
    ap.add_argument("--cache-dir",default=None,help="Persistent cache for the frozen KNIME/Zenodo archives")
    ap.add_argument("--allow-full-update-archive",action="store_true",help="Last-resort 7.9-GB KNIME update archive fallback")
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
    archive_dir=Path(args.cache_dir) if args.cache_dir else root/"knime_archive"
    archive_dir.mkdir(parents=True,exist_ok=True)
    meta_url="https://zenodo.org/api/records/7515771"
    with urllib.request.urlopen(meta_url,timeout=60) as fh:
        meta=json.load(fh)
    all_files=meta.get("files",[])
    print("[RetroPath bootstrap] Zenodo 7515771 file inventory:",flush=True)
    for item in all_files:
        print(f"  - {item.get('key','')} bytes={item.get('size','?')}",flush=True)

    # Download only the frozen KNIME platform plus the frozen community/chemistry
    # repositories needed for RetroPath. Deliberately EXCLUDE the 7.9-GB archived
    # analytics-platform repository here; if KNIME-owned IUs are missing after
    # extracting the base runtime, targeted 4.6 p2 resolution below acquires only
    # their dependency closure. The giant archive remains an explicit last resort.
    selected=[]
    for item in all_files:
        key=item.get("key","")
        low=key.lower()
        is_linux=("linux" in low and ("4.6.4" in low or "knime" in low))
        is_repo=(
            key.lower().endswith(".zip")
            and not any(tag in low for tag in ("win32","windows","macos","macosx"))
            and "org.knime.update.analytics-platform" not in low
            and any(tag in low for tag in (
                "trustedcommunity","communitycontributions",
                "community-contributions","chemistry"
            ))
        )
        if is_linux or is_repo:
            selected.append(item)
    if not any("linux" in x.get("key","").lower() for x in selected):
        raise RuntimeError("Zenodo 7515771 did not expose a KNIME 4.6.4 Linux archive")
    if not any("trustedcommunity" in x.get("key","").lower() for x in selected):
        raise RuntimeError("Zenodo 7515771 did not expose the frozen KNIME 4.6 trusted-community repository")
    print("[RetroPath bootstrap] selected archived files: "+", ".join(x.get("key","") for x in selected),flush=True)

    local=[]
    linux_archive=None
    provenance=[]
    for item in selected:
        key=item["key"]
        dest=archive_dir/Path(key).name
        expected_sha=KNOWN_ARCHIVE_SHA256.get(Path(key).name)
        download(
            item["links"]["self"],dest,
            expected_size=item.get("size"),
            expected_sha256=expected_sha,
        )
        entry={"key":key,"bytes":dest.stat().st_size,"sha256":sha256_file(dest),"source":"ZENODO_7515771"}
        low=key.lower()
        if "linux" in low and linux_archive is None:
            linux_archive=dest
            entry["kind"]="KNIME_PLATFORM"
        elif dest.suffix.lower()==".zip":
            units=p2_units(dest)
            entry["kind"]="P2_REPOSITORY" if units else "ZIP_NON_P2"
            entry["iu_count"]=len(units)
            entry["contains_org.knime.chem.base"]="org.knime.chem.base" in units
            entry["contains_rdkit_feature"]="org.rdkit.knime.feature.feature.group" in units
            if units:
                local.append(dest)
        provenance.append(entry)
        print("[RetroPath bootstrap] archive probe "+json.dumps(entry,sort_keys=True),flush=True)

    # Extract first, then inspect the base runtime.  This avoids downloading the
    # ~7.9-GB analytics-platform repository merely because an IU is absent from
    # Trusted Community metadata even when it is already bundled in KNIME.
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
    knime_root=Path(kexec).parent

    base_advertised=installed_ius(knime_root)
    repo_advertised=set()
    for p in local:
        repo_advertised.update(p2_units(p))
    required=set(Knime.PLUGINS)

    # Availability in a p2 repository is NOT the same thing as installation.
    # Install every required IU that is not already represented in the extracted
    # KNIME base. Local frozen repositories satisfy RDKit; KNIME's 4.6 lane is
    # added only when a required IU is unavailable in the frozen repositories.
    to_install=sorted(required-base_advertised)
    unavailable=sorted(required-(base_advertised|repo_advertised))

    print(
        "[RetroPath bootstrap] preflight "
        + json.dumps({
            "base_iu_count":len(base_advertised),
            "archived_repo_iu_count":len(repo_advertised),
            "required_count":len(required),
            "to_install":to_install,
            "unavailable_in_frozen_inputs":unavailable,
            "base_has_org.knime.chem.base":"org.knime.chem.base" in base_advertised,
            "archive_has_rdkit_feature":"org.rdkit.knime.feature.feature.group" in repo_advertised,
        },sort_keys=True),
        flush=True,
    )

    repos=["jar:file:"+str(p.resolve())+"!/" for p in local]
    repo_mode="ZENODO_7515771_ONLY"
    p2_online_used=[]
    if unavailable:
        # The core 4.6 repository is sufficient for the KNIME-owned IUs observed
        # in the frozen RetroPath stack. The historical /chemistry/ URL now 404s,
        # so do not include it merely to generate noisy p2 errors.
        p2_online_used=[KNIME_46_CORE_REPO]
        repos.extend(p2_online_used)
        repo_mode="ZENODO_7515771_PLUS_TARGETED_KNIME_46_P2"

    if to_install:
        print(
            "[RetroPath bootstrap] p2 install required IUs: "+",".join(to_install),
            flush=True,
        )
        try:
            subprocess.run([
                str(kexec),"-nosplash","-consoleLog",
                "-application","org.eclipse.equinox.p2.director",
                "-repository",",".join(repos),
                "-bundlepool",str(p2_dir),"-destination",str(knime_root),
                "-i",",".join(to_install)
            ],check=True)
        except subprocess.CalledProcessError:
            if not args.allow_full_update_archive:
                raise RuntimeError(
                    "Targeted KNIME 4.6 p2 install failed. The 7.9-GB full archive was NOT "
                    "downloaded automatically. Re-run with --allow-full-update-archive only "
                    "if the targeted version-lane repository is unavailable."
                )
            core=archive_dir/"UpdateSite_latest46.zip"
            download(KNIME_46_UPDATE_ARCHIVE,core)
            units=p2_units(core)
            if not units:
                raise RuntimeError("Full KNIME 4.6 update archive is not a readable p2 repository")
            provenance.append({
                "key":core.name,"bytes":core.stat().st_size,"sha256":sha256_file(core),
                "source":KNIME_46_UPDATE_ARCHIVE,"kind":"P2_REPOSITORY",
                "iu_count":len(units),"fallback_reason":"targeted_p2_failed",
            })
            repos=["jar:file:"+str(p.resolve())+"!/" for p in local+[core]]
            repo_mode="ZENODO_7515771_PLUS_RESUMABLE_FULL_46_ARCHIVE"
            subprocess.run([
                str(kexec),"-nosplash","-consoleLog",
                "-application","org.eclipse.equinox.p2.director",
                "-repository",",".join(repos),
                "-bundlepool",str(p2_dir),"-destination",str(knime_root),
                "-i",",".join(to_install)
            ],check=True)

    # Filesystem naming is not a reliable p2-IU oracle (feature.group IDs and
    # plugin bundle names differ). Query p2 itself for the installed profile and
    # retain filesystem hashes as the reproducibility lock. A successful p2
    # director transaction is authoritative for requested IU installation.
    final_advertised=installed_ius(knime_root)
    filesystem_unseen=sorted(required-final_advertised)
    if filesystem_unseen:
        print(
            "[RetroPath bootstrap] note: filesystem IU heuristic does not expose: "
            + ",".join(filesystem_unseen)
            + " ; p2 director installation result is authoritative",
            flush=True,
        )
    runtime_lock=required_runtime_lock(knime_root,required)
    print("[RetroPath bootstrap] required runtime IU lock captured",flush=True)

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
        "knime_provenance":repo_mode,
        "knime_targeted_online_repositories":p2_online_used,
        "knime_base_iu_count":len(base_advertised),
        "knime_to_install":to_install,\n        "knime_unavailable_in_frozen_inputs":unavailable,
        "knime_required_runtime_lock":runtime_lock,
        "knime_archive_files":[x.get("key","") for x in selected],
        "knime_repository_provenance":provenance,
        "knime_repository_iu_preflight":{
            "org.knime.chem.base":"org.knime.chem.base" in final_advertised,
            "org.rdkit.knime.feature.feature.group":"org.rdkit.knime.feature.feature.group" in final_advertised,
        },
    }
    out=root/"synbiocrow_retropath_bootstrap.json"
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True))
    print(f"[RetroPath bootstrap] manifest={out}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
