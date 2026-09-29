#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, urllib.request
from collections import Counter
from pathlib import Path

HISTORICAL_URL = "https://raw.githubusercontent.com/brsynth/retropath2-wrapper/d9948aa1672873d1e3c1905a355f62f714946e67/tests/data/lycopene/out/r20220104/results.7325.csv"

KEYS = [
    "Initial source",
    "Reaction SMILES",
    "Substrate InChI",
    "Product InChI",
    "In Sink",
    "Diameter",
    "Rule ID",
    "EC number",
    "Score",
    "Iteration",
]

def norm(v: str) -> str:
    return " ".join(str(v or "").strip().split())

def row_key(row: dict[str,str]) -> tuple[str,...]:
    return tuple(norm(row.get(k,"")) for k in KEYS)

def read_rows(path: Path) -> list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8",errors="replace") as fh:
        return list(csv.DictReader(fh))

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--standalone-results",required=True)
    ap.add_argument("--out",default="retropath_standalone_equivalence.json")
    args=ap.parse_args()

    standalone=Path(args.standalone_results)
    historical=standalone.parent/"historical_r20220104_results.7325.csv"
    if not historical.exists():
        print(f"[EQUIVALENCE] download historical fixture {HISTORICAL_URL}",flush=True)
        urllib.request.urlretrieve(HISTORICAL_URL,historical)

    srows=read_rows(standalone)
    hrows=read_rows(historical)
    sc=Counter(row_key(r) for r in srows)
    hc=Counter(row_key(r) for r in hrows)

    intersection=sum((sc & hc).values())
    union=sum((sc | hc).values())
    exact=sc==hc
    recall=intersection/max(1,sum(hc.values()))
    precision=intersection/max(1,sum(sc.values()))
    jaccard=intersection/max(1,union)

    # Also compare exact full-row multisets as a stricter diagnostic. Transformation
    # IDs can differ between independent implementations, so certification is based
    # on the chemistry/evidence projection above, not internal generated IDs.
    all_cols=sorted(set().union(*(r.keys() for r in srows+hrows)))
    full_s=Counter(tuple(norm(r.get(k,"")) for k in all_cols) for r in srows)
    full_h=Counter(tuple(norm(r.get(k,"")) for k in all_cols) for r in hrows)

    payload={
        "status":"PASS" if exact else "FAIL",
        "certification_ready":bool(exact),
        "comparison":"EXACT_MULTISET_SEMANTIC_PROJECTION",
        "projection_columns":KEYS,
        "standalone_rows":len(srows),
        "historical_rows":len(hrows),
        "intersection_rows":intersection,
        "precision":precision,
        "recall":recall,
        "jaccard":jaccard,
        "full_row_exact":full_s==full_h,
        "standalone_sha256":sha256_file(standalone),
        "historical_sha256":sha256_file(historical),
        "historical_source":HISTORICAL_URL,
        "missing_from_standalone":sum((hc-sc).values()),
        "novel_in_standalone":sum((sc-hc).values()),
    }
    Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True),flush=True)
    if exact:
        print("RETROPATH STANDALONE EQUIVALENCE PASS",flush=True)
        return 0
    print("RETROPATH STANDALONE EQUIVALENCE FAIL (certification remains fail-closed)",flush=True)
    return 2

if __name__=="__main__":
    raise SystemExit(main())
