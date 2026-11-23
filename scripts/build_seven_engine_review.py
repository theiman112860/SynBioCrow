"""Build the deterministic SOURCE ZIP and manifest for the seven-engine review."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "ACCEPTANCE.md", "AGENTS.md", "FAILURE_LEDGER.md", "LICENSE.txt", "README.md",
    "pyproject.toml", "synbiocrow", "synbiocrow_core", "tests",
    "RELEASE_NOTES_2_2_RC1.md", "notebooks/SynBioCrow_2_2_RC1_ALL_GENERATORS.ipynb",
    "docs/M9_RELEASE_CANDIDATE.md", "paper/2.2", "scripts",
    "notebooks/SynBioCrow_SEVEN_ENGINE_REVIEW.ipynb", "notebooks/seven_engine",
    "docs/SEVEN_ENGINE_REVIEW.md", "release/2.1.0", "core_certification",
)
BASENAME = "SynBioCrow_M1_20_7"


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write_member(archive, name, contents):
    entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, contents, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD").decode().strip()
    paths = git("ls-tree", "-r", "--name-only", "-z", commit, "--", *SOURCES).decode()
    files = {}
    for name in sorted(filter(None, paths.split("\0"))):
        contents = git("show", f"{commit}:{name}")
        if name.endswith(".ipynb"):
            cells = json.loads(contents)["cells"]
            if any(cell.get("outputs") or cell.get("execution_count") for cell in cells):
                raise ValueError(f"Notebook contains execution output: {name}")
        files[name] = contents
    manifest = {
        "schema": "synbiocrow.seven-engine-review.v1",
        "git_commit": commit,
        "acceptance": "NOT_VERIFIED",
        "package_kind": "draft_review_source",
        "files": {name: {"sha256": sha256(contents), "bytes": len(contents)}
                  for name, contents in files.items()},
    }
    archive_path = out / f"{BASENAME}_SOURCE.zip"
    manifest_name = f"{BASENAME}_MANIFEST.json"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, contents in files.items():
            write_member(archive, name, contents)
        write_member(archive, "SOURCE_MANIFEST.json", json_bytes(manifest))
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("SOURCE archive failed integrity validation")
    manifest["source_zip_sha256"] = sha256(archive_path.read_bytes())
    (out / manifest_name).write_bytes(json_bytes(manifest))
    print(f"{archive_path.name} {manifest['source_zip_sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    build(parser.parse_args().output_dir)
