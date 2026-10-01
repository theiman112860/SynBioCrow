"""Deterministic feature-matrix export for fixed-candidate ranking."""
from __future__ import annotations
import csv
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List
from .adapters import AdaptedRoute

_COLUMNS=[
"route_id","structural_2d","structural_3d","reaction_evidence_fraction",
"reviewed_enzyme_fraction","rhea_exact_fraction","thermo_coverage_fraction",
"engine_count","route_length","unsupported_edge_count","mapping_confidence_mean",
]

def feature_rows(routes: Iterable[AdaptedRoute]) -> List[dict]:
    out=[]
    for route in routes:
        d=asdict(route.features)
        out.append({k:d.get(k) for k in _COLUMNS})
    return out

def write_feature_csv(routes: Iterable[AdaptedRoute], path: str) -> str:
    rows=feature_rows(routes)
    p=Path(path)
    with p.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=_COLUMNS)
        w.writeheader(); w.writerows(rows)
    return str(p)
