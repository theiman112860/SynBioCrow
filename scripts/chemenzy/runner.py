"""Restore the M1.20.6 native planner without changing SynBioCrow's environment."""
import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from trees import reaction_records


HERE = Path(__file__).resolve().parent
ASSETS = json.loads((HERE / "assets.json").read_text())
LOCK = HERE / "scientific-linux-cp38.lock"
STOCK = "Zinc_Fix-stock"
MODEL = "onmt_models.bionav_one_step"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--upstream", required=True, type=Path, help="Dedicated upstream checkout")
    parser.add_argument("--out", required=True, type=Path, help="New evidence directory")
    parser.add_argument("--fetch", action="store_true", help="Populate missing cache entries")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--stock", default=STOCK)
    parser.add_argument("--gpu", type=int, default=-1)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=5400)
    args = parser.parse_args()
    if not args.probe_only and not args.target:
        parser.error("provide at least one --target for native inference")
    cache, repo, out = (path.resolve() for path in (args.cache, args.upstream, args.out))
    out.mkdir(parents=True)
    cache.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "FAIL", "stage": "source", "assets": {},
        "upstream_git": ASSETS["upstream_git"], "scientific_lock_sha256": digest(LOCK),
    }

    with (out / "execution.log").open("w") as log:
        def run(command, *, cwd=None, env=None, timeout=900):
            command = [str(part) for part in command]
            print(command, file=log, flush=True)
            subprocess.run(
                command, cwd=cwd, env=env, check=True, timeout=timeout,
                stdout=log, stderr=subprocess.STDOUT,
            )

        def checked_asset(name):
            expected = ASSETS["files"][name]
            path = cache / name
            if not path.is_file():
                if not args.fetch:
                    raise FileNotFoundError(f"Missing pinned cache entry: {path}")
                partial = path.with_suffix(path.suffix + ".partial")
                url = ("https://huggingface.co/xiaoruiwang/ChemEnzyRetroPlanner_metadata/"
                       f"resolve/{ASSETS['metadata_revision']}/{name}?download=true")
                run(["curl", "--fail", "--location", "--silent", "--show-error", "--continue-at",
                     "-", "--max-time", "900", "--output", partial, url], timeout=920)
                if digest(partial) != expected:
                    raise ValueError(f"Downloaded asset SHA256 mismatch: {partial}")
                partial.replace(path)
            elif digest(path) != expected:
                raise ValueError(f"Cached asset SHA256 mismatch: {path}")
            status["assets"][name] = expected
            return path

        try:
            if not repo.exists() and args.fetch:
                run(["git", "clone", "--no-checkout",
                     "https://github.com/wangxr0526/ChemEnzyRetroPlanner.git", repo])
                run(["git", "checkout", "--detach", ASSETS["upstream_git"]], cwd=repo)
            actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            if actual != ASSETS["upstream_git"]:
                raise ValueError(f"Upstream checkout mismatch: {actual}")
            run(["git", "diff", "--exit-code", "HEAD", "--", "retro_planner"], cwd=repo)

            status["stage"] = "runtime"
            archive = checked_asset("retro_planner_env.tar.gz")
            runtime = cache / ("native-" + ASSETS["files"][archive.name][:16])
            marker = runtime / ".restored"
            if not marker.is_file():
                runtime.mkdir()
                with tarfile.open(archive) as packed:
                    packed.extractall(runtime, filter="data")
                run([runtime / "bin/python", runtime / "bin/conda-unpack"], cwd=runtime)
                marker.write_text(ASSETS["files"][archive.name] + "\n")
            if marker.read_text().strip() != ASSETS["files"][archive.name]:
                raise ValueError("Native runtime marker does not match the archive")
            python = runtime / "bin/python"
            status["stage"] = "scientific_overlay"
            overlay = cache / ("scientific-" + digest(LOCK)[:16])
            if not overlay.is_dir():
                wheels = cache / "wheels"
                wheels.mkdir(exist_ok=True)
                if args.fetch:
                    run([python, "-m", "pip", "download", "--require-hashes", "--only-binary=:all:",
                         "--dest", wheels, "-r", LOCK])
                with tempfile.TemporaryDirectory(dir=cache) as tmp:
                    pending = Path(tmp) / overlay.name
                    run([python, "-m", "pip", "install", "--no-index", "--find-links", wheels,
                         "--only-binary=:all:", "--require-hashes", "--target", pending, "-r", LOCK])
                    pending.rename(overlay)
            vendored = repo / "retro_planner/packages"
            roots = [overlay, repo, *sorted(path for path in vendored.iterdir() if path.is_dir()), vendored]
            env = dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, roots)), PYTHONNOUSERSITE="1",
                       PYTHONHASHSEED="0", DGLBACKEND="pytorch", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
            if args.gpu < 0:
                env["CUDA_VISIBLE_DEVICES"] = ""
            write_json(out / "import_roots.json", [str(path) for path in roots])
            status["stage"] = "native_api"
            run([python, "-W", "error:.*size changed:RuntimeWarning", "-c",
                 "import numpy, scipy, sklearn; from sklearn.neighbors import NearestNeighbors; "
                 "from retro_planner.api import RSPlanner; "
                 "print(numpy.__version__, scipy.__version__, sklearn.__version__, RSPlanner)"],
                cwd=repo, env=env, timeout=300)
            if args.probe_only:
                status.update(status="NOT_VERIFIED", stage="native_api_loaded")
                return 0

            status["stage"] = "model_and_stock"
            for name in ASSETS["files"]:
                if not name.endswith(".zip"):
                    continue
                archive = checked_asset(name)
                sentinel = repo / (".synbiocrow-" + ASSETS["files"][name])
                if not sentinel.is_file():
                    with zipfile.ZipFile(archive) as packed:
                        packed.extractall(repo)
                    sentinel.touch()
            config_path = repo / "retro_planner/config/config.yaml"
            config = json.loads(subprocess.check_output(
                [str(python), "-c", "import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))",
                 str(config_path)], cwd=repo, env=env, timeout=30,
            ))
            config["stocks"] = {args.stock: config["stocks"][args.stock]}
            config.update(iterations=args.iterations, gpu=args.gpu, pred_condition=False,
                          organic_enzyme_rxn_classification=False, enzyme_assign=False, viz=False)
            write_json(out / "effective_config.json", config)
            write_json(out / "targets.json", args.target)
            status.update(stock=args.stock, model=MODEL, stage="native_inference",
                          config_sha256=digest(out / "effective_config.json"))
            run([python, HERE / "worker.py", out / "effective_config.json", args.stock, MODEL,
                 out / "targets.json", out / "routes.json"], cwd=repo, env=env, timeout=args.timeout)
            routes = json.loads((out / "routes.json").read_text())
            counts = {row["target"]: len(row["routes"]) for row in routes}
            records = list(reaction_records(routes))
            write_json(out / "reactions.json", records)
            status["reactions_sha256"] = digest(out / "reactions.json")
            errors = {row["target"]: row["error"] for row in routes if "error" in row}
            if errors:
                status["target_errors"] = errors
                return 1
            status.update(stage="native_output", route_counts=counts,
                          routes_sha256=digest(out / "routes.json"))
            status["status"] = "NATIVE_OUTPUT" if all(counts.values()) else "NO_ROUTE"
            return 0 if all(counts.values()) else 2
        except Exception as exc:
            status["error"] = str(exc)
            print(f"Failed at {status['stage']}: {exc}", file=log)
            return 1
        finally:
            write_json(out / "status.json", status)
            print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
