from __future__ import annotations
import argparse, hashlib, json, os, subprocess, tempfile, zipfile
from pathlib import Path

from synbiocrow.execution import json_safe
from synbiocrow.verification import build_release_readiness_report

RELEASE="2.2.0"
REQUIRED=[
    "README.md",
    "pyproject.toml",
    "RELEASE_NOTES_2_2_0.md",
    "notebooks/SynBioCrow_2_2_RC1_ALL_GENERATORS.ipynb",
    "docs/M9_RELEASE_CANDIDATE.md",
    "docs/RETROPATH_STANDALONE_EQUIVALENCE.md",
    "paper/2.2/METHODS.md",
    "paper/2.2/RESULTS.md",
    "scripts/m7_release_readiness.py",
]
EXCLUDE_PREFIXES=(
    ".git/","dist/","build/","dist_m9/",".synbiocrow_runs/",
    "__pycache__/","development_history/",
)
PROTECTED_PATTERNS=("benchmark_v2_truth","holdout_truth","gold_truth","blind_truth")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def git_head(root:Path)->str:
    try:
        return subprocess.check_output(
            ["git","rev-parse","HEAD"],cwd=root,text=True
        ).strip()
    except Exception:
        return "UNKNOWN"

def tracked_files(root:Path)->list[Path]:
    try:
        raw=subprocess.check_output(
            ["git","ls-files"],cwd=root,text=True
        ).splitlines()
        paths=[root/x for x in raw]
    except Exception:
        paths=[p for p in root.rglob("*") if p.is_file()]
    selected=[]
    for p in paths:
        rel=p.relative_to(root).as_posix()
        low=rel.lower()
        if any(rel.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        if any(pattern in low for pattern in PROTECTED_PATTERNS):
            # Public sealed 2.1 manifests contain statements about truth isolation,
            # but no truth data; allow those exact release manifests.
            if not rel.startswith("release/2.1.0/"):
                continue
        if p.is_file():
            selected.append(p)
    return sorted(selected,key=lambda x:x.relative_to(root).as_posix())

def validate_required(root:Path)->None:
    missing=[x for x in REQUIRED if not (root/x).is_file()]
    if missing:
        raise SystemExit("Missing M9 required files: "+", ".join(missing))

def build(root:Path,outdir:Path,*,check_only:bool=False)->dict:
    validate_required(root)
    readiness=build_release_readiness_report(root)
    if not readiness.core_release_ready:
        raise SystemExit("M7 release-readiness blockers: "+", ".join(readiness.blockers))

    files=tracked_files(root)
    inventory=[]
    for p in files:
        rel=p.relative_to(root).as_posix()
        inventory.append({
            "path":rel,
            "bytes":p.stat().st_size,
            "sha256":sha256(p),
        })

    manifest={
        "schema":"synbiocrow.release_manifest.v2",
        "release":RELEASE,
        "release_kind":"final",
        "git_commit":git_head(root),
        "core_release_ready":readiness.core_release_ready,
        "m7_reproducibility_digest":readiness.reproducibility.digest,
        "frozen_2_1_policy_pass":readiness.frozen.passed,
        "benchmark_v2_truth_accessed":False,
        "paper1_baseline_modified":False,
        "scientific_lifecycle":"CANDIDATE_MATURE_CERTIFIED_SEPARATE",
        "retropath_primary_runtime":"retropath_standalone",
        "retropath_knime_required":False,
        "retropath_equivalence_policy":"EXACT_COMPOUND_TRANSITION_MULTISET",
        "retropath_equivalence_fixture":"brsynth/retropath2-wrapper r20220104 results.7325.csv",
        "file_count":len(inventory),
        "files":inventory,
    }

    if check_only:
        print(json.dumps({
            "status":"PASS",
            "release":RELEASE,
            "git_commit":manifest["git_commit"],
            "file_count":len(inventory),
            "m7_reproducibility_digest":manifest["m7_reproducibility_digest"],
        },indent=2,sort_keys=True))
        return manifest

    outdir.mkdir(parents=True,exist_ok=True)
    manifest_path=outdir/f"SynBioCrow_{RELEASE}_release_manifest.json"
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    zip_path=outdir/f"SynBioCrow_{RELEASE}_SOURCE_REPRODUCIBILITY.zip"
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p,p.relative_to(root).as_posix())
        z.write(manifest_path,manifest_path.name)

    zip_sha=sha256(zip_path)
    summary={
        "release":RELEASE,
        "git_commit":manifest["git_commit"],
        "source_zip":zip_path.name,
        "source_zip_bytes":zip_path.stat().st_size,
        "source_zip_sha256":zip_sha,
        "manifest":manifest_path.name,
        "file_count":len(inventory),
        "m7_reproducibility_digest":manifest["m7_reproducibility_digest"],
    }
    (outdir/f"SynBioCrow_{RELEASE}_PACKAGE_SUMMARY.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print(json.dumps(summary,indent=2,sort_keys=True))
    return manifest

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="dist_m9")
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    build(root,root/args.output_dir,check_only=args.check)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
