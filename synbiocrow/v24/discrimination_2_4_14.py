"""SynBioCrow 2.4.14 evidence-aware route discrimination.

Generation-free ranking over persisted development artifacts.  This module
never invokes a generator and never accesses validation/evaluation truth.

Missing evidence remains missing.  Scores are normalized over observed
features and multiplied by an evidence-coverage ceiling so sparse routes do
not outrank well-supported routes merely because unknown fields were ignored.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import hashlib
import json
import math

from rdkit import Chem

from synbiocrow.core.models import PathwayCandidate, ReactionStep
from synbiocrow.ensemble.graph import build_reaction_graph
from synbiocrow.ensemble.identity import resolve_compound


DEVELOPMENT_ONLY_ERROR = (
    "2.4.14 calibration is development-only; validation/evaluation records are sealed"
)

FEATURE_NAMES = (
    "reaction_evidence_fraction",
    "reviewed_enzyme_fraction",
    "ec_evidence_fraction",
    "rhea_exact_fraction",
    "rhea_connectivity_fraction",
    "thermo_coverage_fraction",
    "mapping_confidence_mean",
    "engine_count_scaled",
    "cross_engine_edge_fraction",
    "route_length_scaled",
    "unsupported_edge_fraction",
    "currency_burden_fraction",
)

DEFAULT_WEIGHTS = {
    "reaction_evidence_fraction": 0.80,
    "reviewed_enzyme_fraction": 1.00,
    "ec_evidence_fraction": 0.60,
    "rhea_exact_fraction": 0.90,
    "rhea_connectivity_fraction": 0.45,
    "thermo_coverage_fraction": 0.35,
    "mapping_confidence_mean": 0.40,
    "engine_count_scaled": 0.15,
    "cross_engine_edge_fraction": 0.10,
    "route_length_scaled": -0.20,
    "unsupported_edge_fraction": -0.55,
    "currency_burden_fraction": -0.25,
}


@dataclass(frozen=True)
class RouteFeatureRow:
    record_id: str
    target_name: str
    route_id: str
    split: str
    route_length: int
    engine_count: int
    component_values: Mapping[str, float | None]
    observed_feature_count: int
    total_feature_count: int
    evidence_coverage: float
    source_artifact: str


@dataclass(frozen=True)
class RankedRoute:
    record_id: str
    target_name: str
    route_id: str
    rank: int
    raw_observed_score: float | None
    coverage_adjusted_score: float | None
    evidence_coverage: float
    observed_feature_count: int
    route_length: int
    engine_count: int
    component_values: Mapping[str, float | None]


def _candidate_from_dict(d: Mapping[str, Any]) -> PathwayCandidate:
    steps=[]
    for row in d.get("steps") or ():
        if not isinstance(row, Mapping):
            continue
        steps.append(ReactionStep(
            reaction=str(row.get("reaction") or ""),
            rule_id=row.get("rule_id"),
            source_backend=row.get("source_backend"),
            feasibility=row.get("feasibility"),
            metadata=dict(row.get("metadata") or {}),
        ))
    return PathwayCandidate(
        candidate_id=str(d.get("candidate_id") or d.get("id") or "candidate"),
        target_smiles=str(d.get("target_smiles") or ""),
        steps=tuple(steps),
        source_backends=tuple(str(x) for x in (d.get("source_backends") or ())),
        provenance=dict(d.get("provenance") or {}),
        evidence=dict(d.get("evidence") or {}),
    )


def load_development_artifact(path: str | Path) -> tuple[dict, list[PathwayCandidate]]:
    p=Path(path)
    obj=json.loads(p.read_text(encoding="utf-8"))
    split=str(obj.get("split") or "")
    if split != "development":
        raise ValueError(f"{DEVELOPMENT_ONLY_ERROR}; refused split={split!r}")
    result=obj.get("result")
    if not isinstance(result, Mapping):
        raise ValueError(f"{p}: missing result object")
    raw=result.get("candidates") or []
    candidates=[_candidate_from_dict(x) for x in raw if isinstance(x, Mapping)]
    return obj,candidates


def _num(v: Any) -> float | None:
    try:
        if v is None or v == "": return None
        x=float(v)
        if math.isfinite(x): return x
    except Exception:
        pass
    return None


def _truthy(v: Any) -> bool:
    if v is True: return True
    if isinstance(v,(int,float)) and v == 1: return True
    if isinstance(v,str) and v.strip().lower() in {"true","yes","1","reviewed","exact","supported"}:
        return True
    if isinstance(v,(list,tuple,set,dict)) and len(v)>0:
        return True
    return False


def _meta_values(edge) -> list[Mapping[str,Any]]:
    return [x for x in (edge.provenance or ()) if isinstance(x,Mapping)]


def _edge_evidence(edge) -> dict[str, float | None]:
    metas=_meta_values(edge)
    explicit=False
    reviewed=False
    ec=False
    rhea_exact=False
    rhea_conn=False
    thermo=False
    mappings=[]
    for m in metas:
        reviewed = reviewed or any(_truthy(m.get(k)) for k in (
            "reviewed_uniprot","reviewed_enzyme","uniprot","uniprot_id","uniprot_ids"
        ))
        ec = ec or any(_truthy(m.get(k)) for k in ("ec","ec_number","ec_numbers"))
        rhea_exact = rhea_exact or _truthy(m.get("rhea_exact"))
        rhea_conn = rhea_conn or _truthy(m.get("rhea_connectivity")) or any(
            _truthy(m.get(k)) for k in ("rhea","rhea_id","rhea_ids")
        )
        thermo = thermo or any(_num(m.get(k)) is not None for k in (
            "thermo_dg","delta_g","dg_prime","dG"
        ))
        for k in ("mapping_confidence","map_confidence"):
            x=_num(m.get(k))
            if x is not None and 0 <= x <= 1: mappings.append(x)
        explicit = explicit or reviewed or ec or rhea_exact or rhea_conn or thermo
    return {
        "supported": 1.0 if explicit else 0.0,
        "reviewed": 1.0 if reviewed else 0.0,
        "ec": 1.0 if ec else 0.0,
        "rhea_exact": 1.0 if rhea_exact else 0.0,
        "rhea_connectivity": 1.0 if rhea_conn else 0.0,
        "thermo": 1.0 if thermo else 0.0,
        "mapping": (sum(mappings)/len(mappings) if mappings else None),
    }


def _compound_smiles(graph,key: str) -> str | None:
    ci=graph.compounds.get(key)
    if ci is None: return None
    return (
        getattr(ci,"canonical_smiles",None)
        or getattr(ci,"smiles",None)
        or getattr(ci,"raw",None)
    )


def _is_currency_like_smiles(smi: str | None) -> bool:
    if not smi: return False
    mol=Chem.MolFromSmiles(str(smi))
    if mol is None: return False
    atoms=[a.GetSymbol() for a in mol.GetAtoms()]
    heavy=mol.GetNumHeavyAtoms()
    p=atoms.count("P"); n=atoms.count("N")
    if Chem.MolToSmiles(mol,canonical=True) == "O":
        return True
    if heavy <= 2 and set(atoms).issubset({"H","O","N","P","S","C"}):
        return True
    if p >= 2 and n >= 3 and heavy >= 20:
        return True
    return False


def _route_feature_row(
    *,
    record_id: str,
    target_name: str,
    split: str,
    route: Sequence[str],
    graph,
    source_artifact: str,
) -> RouteFeatureRow:
    edges=[graph.edges[e] for e in route if e in graph.edges]
    n=max(1,len(edges))
    ev=[_edge_evidence(e) for e in edges]
    engines=sorted({b for e in edges for b in e.source_backends})
    cross=sum(len(e.source_backends)>1 for e in edges)/n
    supported=sum(x["supported"] for x in ev)/n
    reviewed=sum(x["reviewed"] for x in ev)/n
    ec=sum(x["ec"] for x in ev)/n
    rhea_exact=sum(x["rhea_exact"] for x in ev)/n
    rhea_conn=sum(x["rhea_connectivity"] for x in ev)/n
    thermo=sum(x["thermo"] for x in ev)/n
    maps=[x["mapping"] for x in ev if x["mapping"] is not None]
    mapping=(sum(maps)/len(maps)) if maps else None

    currency_precursors=0
    precursor_count=0
    for e in edges:
        for key in e.precursor_keys:
            precursor_count += 1
            currency_precursors += int(_is_currency_like_smiles(_compound_smiles(graph,key)))
    currency=(currency_precursors/precursor_count) if precursor_count else 0.0

    components={
        "reaction_evidence_fraction": supported,
        "reviewed_enzyme_fraction": reviewed,
        "ec_evidence_fraction": ec,
        "rhea_exact_fraction": rhea_exact,
        "rhea_connectivity_fraction": rhea_conn,
        "thermo_coverage_fraction": thermo,
        "mapping_confidence_mean": mapping,
        "engine_count_scaled": min(len(engines),4)/4.0,
        "cross_engine_edge_fraction": cross,
        "route_length_scaled": min(len(edges),12)/12.0,
        "unsupported_edge_fraction": 1.0-supported,
        "currency_burden_fraction": currency,
    }
    observed=sum(v is not None for v in components.values())
    return RouteFeatureRow(
        record_id=record_id,
        target_name=target_name,
        route_id="route:"+hashlib.sha256(
            (record_id+"|"+"|".join(route)).encode()
        ).hexdigest()[:20],
        split=split,
        route_length=len(edges),
        engine_count=len(engines),
        component_values=components,
        observed_feature_count=observed,
        total_feature_count=len(FEATURE_NAMES),
        evidence_coverage=observed/len(FEATURE_NAMES),
        source_artifact=source_artifact,
    )


def extract_development_features(path: str | Path) -> list[RouteFeatureRow]:
    """Extract fixed candidates plus any strict ensemble routes.

    Candidate pathways are always included because 2.4 development artifacts
    may contain many generated candidates even when strict sink closure is zero.
    """
    obj,candidates=load_development_artifact(path)
    result=obj["result"]
    record_id=str(obj.get("record_id") or "")
    target_name=str(obj.get("target_name") or "")
    out=[]

    # Rank each persisted candidate independently. This preserves proposal
    # provenance and does not require strict sink closure.
    for cand in candidates:
        cgraph=build_reaction_graph([cand])
        edge_ids=sorted(cgraph.edges)
        if not edge_ids:
            continue
        row=_route_feature_row(
            record_id=record_id,
            target_name=target_name,
            split="development",
            route=edge_ids,
            graph=cgraph,
            source_artifact=str(path),
        )
        out.append(RouteFeatureRow(
            record_id=row.record_id,
            target_name=row.target_name,
            route_id="candidate:"+cand.candidate_id,
            split=row.split,
            route_length=row.route_length,
            engine_count=row.engine_count,
            component_values=row.component_values,
            observed_feature_count=row.observed_feature_count,
            total_feature_count=row.total_feature_count,
            evidence_coverage=row.evidence_coverage,
            source_artifact=row.source_artifact,
        ))

    # Also include strict ensemble routes when present.
    graph=build_reaction_graph(candidates)
    for route in result.get("routes") or []:
        if not isinstance(route,list):
            continue
        out.append(_route_feature_row(
            record_id=record_id,
            target_name=target_name,
            split="development",
            route=[str(x) for x in route],
            graph=graph,
            source_artifact=str(path),
        ))

    # Deterministic de-duplication by route_id.
    dedup={}
    for row in out:
        dedup.setdefault(row.route_id,row)
    return [dedup[k] for k in sorted(dedup)]


def score_feature_row(
    row: RouteFeatureRow,
    weights: Mapping[str,float] | None=None,
) -> tuple[float | None,float | None]:
    w=dict(DEFAULT_WEIGHTS if weights is None else weights)
    numerator=0.0
    denom=0.0
    observed=0
    for name,weight in w.items():
        value=row.component_values.get(name)
        if value is None:
            continue
        numerator += float(weight)*float(value)
        denom += abs(float(weight))
        observed += 1
    if not observed or denom == 0:
        return None,None
    raw=numerator/denom
    # Conservative ceiling: evidence quality cannot outrun observed coverage.
    adjusted=raw*row.evidence_coverage
    return raw,adjusted


def rank_feature_rows(
    rows: Sequence[RouteFeatureRow],
    weights: Mapping[str,float] | None=None,
) -> list[RankedRoute]:
    grouped={}
    for row in rows:
        if row.split != "development":
            raise ValueError(f"{DEVELOPMENT_ONLY_ERROR}; refused split={row.split!r}")
        grouped.setdefault(row.record_id,[]).append(row)
    out=[]
    for record_id,items in sorted(grouped.items()):
        scored=[]
        for row in items:
            raw,adj=score_feature_row(row,weights)
            scored.append((row,raw,adj))
        scored.sort(key=lambda x:(
            -(x[2] if x[2] is not None else -1e9),
            -x[0].evidence_coverage,
            x[0].route_length,
            x[0].route_id,
        ))
        for rank,(row,raw,adj) in enumerate(scored,1):
            out.append(RankedRoute(
                record_id=row.record_id,
                target_name=row.target_name,
                route_id=row.route_id,
                rank=rank,
                raw_observed_score=raw,
                coverage_adjusted_score=adj,
                evidence_coverage=row.evidence_coverage,
                observed_feature_count=row.observed_feature_count,
                route_length=row.route_length,
                engine_count=row.engine_count,
                component_values=row.component_values,
            ))
    return out


def fit_development_weights(
    rows: Sequence[RouteFeatureRow],
    labels: Mapping[str,float],
) -> dict:
    """Deterministic small-grid development-only calibration.

    labels maps route_id -> relevance in [0,1].  At least two differently
    labelled routes are required.  No validation/evaluation rows are accepted.
    The objective is pairwise concordance over labelled route pairs.
    """
    rows=[r for r in rows if r.route_id in labels]
    if any(r.split != "development" for r in rows):
        raise ValueError(DEVELOPMENT_ONLY_ERROR)
    ys=[float(labels[r.route_id]) for r in rows]
    if len(rows)<2 or len(set(ys))<2:
        raise ValueError("development calibration requires >=2 labelled routes with differing relevance")

    base=dict(DEFAULT_WEIGHTS)
    tunable=(
        "reaction_evidence_fraction",
        "reviewed_enzyme_fraction",
        "rhea_exact_fraction",
        "thermo_coverage_fraction",
        "unsupported_edge_fraction",
        "currency_burden_fraction",
    )
    scales=(0.5,1.0,1.5)
    best=None
    for s0 in scales:
      for s1 in scales:
       for s2 in scales:
        for s3 in scales:
         for s4 in scales:
          for s5 in scales:
            ws=dict(base)
            for k,s in zip(tunable,(s0,s1,s2,s3,s4,s5)):
                ws[k]=base[k]*s
            values={}
            for r in rows:
                values[r.route_id]=score_feature_row(r,ws)[1]
            good=total=0
            for i,a in enumerate(rows):
                for b in rows[i+1:]:
                    ya=float(labels[a.route_id]); yb=float(labels[b.route_id])
                    if ya==yb: continue
                    total+=1
                    sa=values[a.route_id]; sb=values[b.route_id]
                    if sa is None or sb is None: continue
                    good += int((sa>sb)==(ya>yb))
            concordance=(good/total) if total else 0.0
            complexity=sum(abs(ws[k]-base[k]) for k in tunable)
            key=(concordance,-complexity,json.dumps(ws,sort_keys=True))
            if best is None or key>best[0]:
                best=(key,ws)
    return {
        "schema":"synbiocrow.v24.discrimination-policy.v1",
        "version":"2.4.14",
        "fit_split":"development",
        "validation_truth_accessed":False,
        "evaluation_truth_accessed":False,
        "label_count":len(rows),
        "pairwise_concordance":best[0][0],
        "weights":best[1],
    }


def rows_to_dicts(rows: Iterable[RouteFeatureRow]) -> list[dict]:
    return [asdict(x) for x in rows]


def ranked_to_dicts(rows: Iterable[RankedRoute]) -> list[dict]:
    return [asdict(x) for x in rows]
