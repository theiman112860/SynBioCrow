#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, urllib.request
from collections import Counter
from pathlib import Path

HISTORICAL_URL = "https://raw.githubusercontent.com/brsynth/retropath2-wrapper/d9948aa1672873d1e3c1905a355f62f714946e67/tests/data/lycopene/out/r20220104/results.7325.csv"

def read_rows(path: Path):
    with path.open(newline="",encoding="utf-8",errors="replace") as fh:
        return list(csv.DictReader(fh))

def n(v): return " ".join(str(v or "").strip().split())

def key(row, cols):
    return tuple(n(row.get(c,"")) for c in cols)

def metric(a,b):
    ca, cb = Counter(a), Counter(b)
    inter=sum((ca & cb).values()); union=sum((ca | cb).values())
    return {
        "intersection":inter,
        "precision":inter/max(1,sum(ca.values())),
        "recall":inter/max(1,sum(cb.values())),
        "jaccard":inter/max(1,union),
        "missing":sum((cb-ca).values()),
        "novel":sum((ca-cb).values()),
        "exact":ca==cb,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--standalone-results",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    sfile=Path(args.standalone_results)
    hfile=sfile.parent/"historical_r20220104_results.7325.csv"
    if not hfile.exists():
        urllib.request.urlretrieve(HISTORICAL_URL,hfile)
    srows=read_rows(sfile); hrows=read_rows(hfile)

    projections={
      "compound_transition":["Substrate InChI","Product InChI","In Sink","Iteration"],
      "rule_transition":["Substrate InChI","Product InChI","Rule ID","Diameter","In Sink","Iteration"],
      "evidence_transition":["Substrate InChI","Product InChI","Rule ID","EC number","Score","Diameter","In Sink","Iteration"],
      "reaction_string":["Reaction SMILES","In Sink","Iteration"],
    }
    results={}
    for name,cols in projections.items():
        results[name]=metric([key(r,cols) for r in srows],[key(r,cols) for r in hrows])

    # Certification policy: require exact compound-transition multiset and exact
    # sink/iteration structure. This treats reaction-string formatting, rule/EC
    # aggregation, and score serialization as implementation details, but does
    # not tolerate chemistry/topology differences.
    cert = bool(results["compound_transition"]["exact"])
    payload={
      "status":"PASS" if cert else "FAIL",
      "certification_ready":cert,
      "policy":"EXACT_COMPOUND_TRANSITION_MULTISET",
      "standalone_rows":len(srows),
      "historical_rows":len(hrows),
      "results":results,
      "historical_source":HISTORICAL_URL,
    }
    Path(args.out).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True))
    if cert:
        print("RETROPATH STANDALONE CHEMICAL EQUIVALENCE PASS")
        return 0
    print("RETROPATH STANDALONE CHEMICAL EQUIVALENCE FAIL")
    return 2

if __name__=="__main__":
    raise SystemExit(main())
