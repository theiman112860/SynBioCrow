"""Fixed-candidate adapters for SynBioCrow 2.4.1.

This module reads already-generated route artifacts. It MUST NOT invoke a
generator. Parsing is conservative: missing evidence remains missing and an
unrecognizable reaction record fails closed.
"""
from __future__ import annotations
import csv, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

from .evidence import EvidenceLevel, ReactionEvidence, RankingFeatureVector, aggregate_route_evidence


_ROUTE_KEYS=("route_id","route","pathway_id","path_id","candidate_id")
_REACTION_LIST_KEYS=("reactions","steps","edges","reaction_steps")
_REACTION_ID_KEYS=("reaction_id","id","reaction","reaction_smiles","rxn_smiles","smarts")
_ENGINE_KEYS=("engine","backend","generator","source_engine")
_RHEA_KEYS=("rhea_id","rhea","rhea_ids")
_EC_KEYS=("ec","ec_number","ec_numbers")
_UNIPROT_KEYS=("uniprot","uniprot_id","uniprot_ids","protein_accessions")
_LIT_KEYS=("doi","pmid","literature_ids","references")
_MAP_KEYS=("mapping_confidence","map_confidence")
_SIM2D_KEYS=("similarity_2d","tanimoto","morgan_tanimoto","score_2d")
_SIM3D_KEYS=("similarity_3d","usrcat","usrcat_score","score_3d")


@dataclass(frozen=True)
class AdaptedRoute:
    route_id: str
    reactions: Tuple[ReactionEvidence,...]
    features: RankingFeatureVector
    source_format: str


def _first(d: Mapping[str,Any], keys: Sequence[str], default=None):
    for k in keys:
        if k in d and d[k] not in (None,""):
            return d[k]
    return default


def _tuple(v: Any) -> Tuple[str,...]:
    if v in (None,""): return ()
    if isinstance(v,(list,tuple,set)): return tuple(str(x) for x in v if x not in (None,""))
    if isinstance(v,str) and (";" in v or "|" in v):
        sep=";" if ";" in v else "|"
        return tuple(x.strip() for x in v.split(sep) if x.strip())
    return (str(v),)


def _float(v: Any) -> Optional[float]:
    if v in (None,""): return None
    try: return float(v)
    except (TypeError,ValueError): return None


def _bool(v: Any) -> Optional[bool]:
    if v is None or v=="": return None
    if isinstance(v,bool): return v
    s=str(v).strip().lower()
    if s in {"1","true","yes","y"}: return True
    if s in {"0","false","no","n"}: return False
    return None


def adapt_reaction(raw: Mapping[str,Any], ordinal: int) -> ReactionEvidence:
    rid=_first(raw,_REACTION_ID_KEYS)
    if rid is None:
        raise ValueError(f"reaction {ordinal} has no recognizable reaction identifier")
    engines=_tuple(_first(raw,_ENGINE_KEYS))
    rhea=_tuple(_first(raw,_RHEA_KEYS))
    exact=_bool(raw.get("rhea_exact"))
    connectivity=_bool(raw.get("rhea_connectivity"))
    if rhea and exact is None:
        connectivity=True if connectivity is None else connectivity
    reviewed=_tuple(_first(raw,_UNIPROT_KEYS))
    literature=_tuple(_first(raw,_LIT_KEYS))
    ec=_tuple(_first(raw,_EC_KEYS))
    level=EvidenceLevel.UNKNOWN
    if reviewed: level=EvidenceLevel.REVIEWED
    elif literature: level=EvidenceLevel.LITERATURE
    elif rhea or ec: level=EvidenceLevel.DATABASE
    elif raw.get("thermo_dg") not in (None,""): level=EvidenceLevel.CALCULATED
    provenance=[]
    for k,v in raw.items():
        if v not in (None,"",[],{}):
            provenance.append(f"source-field:{k}")
    return ReactionEvidence(
        reaction_id=str(rid), engines=engines, rhea_exact=exact,
        rhea_connectivity=connectivity, ec_numbers=ec,
        reviewed_uniprot=reviewed, literature_ids=literature,
        thermo_dg=_float(raw.get("thermo_dg")),
        thermo_units=raw.get("thermo_units"),
        cofactors=_tuple(raw.get("cofactors")),
        mapping_confidence=_float(_first(raw,_MAP_KEYS)),
        evidence_level=level, provenance=tuple(provenance),
    )


def adapt_route(raw: Mapping[str,Any], index: int=0, source_format: str="mapping") -> AdaptedRoute:
    route_id=str(_first(raw,_ROUTE_KEYS,f"route_{index:06d}"))
    rxns=_first(raw,_REACTION_LIST_KEYS)
    if rxns is None:
        # Flat row is permitted only when it itself contains a recognizable reaction.
        if _first(raw,_REACTION_ID_KEYS) is None:
            raise ValueError(f"{route_id}: no recognizable reactions")
        rxns=[raw]
    if not isinstance(rxns,list):
        raise ValueError(f"{route_id}: reaction collection must be a list")
    evidence=tuple(adapt_reaction(r,i) for i,r in enumerate(rxns) if isinstance(r,Mapping))
    if len(evidence)!=len(rxns):
        raise ValueError(f"{route_id}: non-mapping reaction entry")
    agg=aggregate_route_evidence(route_id,evidence)
    maps=[r.mapping_confidence for r in evidence if r.mapping_confidence is not None]
    n=max(1,len(evidence))
    features=RankingFeatureVector(
        route_id=route_id,
        structural_2d=_float(_first(raw,_SIM2D_KEYS)),
        structural_3d=_float(_first(raw,_SIM3D_KEYS)),
        reaction_evidence_fraction=agg.supported_reactions/n,
        reviewed_enzyme_fraction=agg.reviewed_enzyme_reactions/n,
        rhea_exact_fraction=agg.rhea_exact_reactions/n,
        thermo_coverage_fraction=agg.thermo_covered_reactions/n,
        engine_count=len(agg.independent_engines),
        route_length=len(evidence),
        unsupported_edge_count=len(evidence)-agg.supported_reactions,
        mapping_confidence_mean=(sum(maps)/len(maps) if maps else None),
    )
    return AdaptedRoute(route_id,evidence,features,source_format)


def load_fixed_candidates(path: str) -> List[AdaptedRoute]:
    p=Path(path); suffix=p.suffix.lower()
    if suffix==".json":
        obj=json.loads(p.read_text(encoding="utf-8"))
        if isinstance(obj,dict):
            rows=_first(obj,("routes","candidates","pathways"),[obj])
        elif isinstance(obj,list): rows=obj
        else: raise ValueError("JSON root must be object or list")
        return [adapt_route(x,i,"json") for i,x in enumerate(rows)]
    if suffix==".jsonl":
        rows=[json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
        return [adapt_route(x,i,"jsonl") for i,x in enumerate(rows)]
    if suffix==".csv":
        with p.open(newline="",encoding="utf-8-sig") as h: rows=list(csv.DictReader(h))
        grouped: Dict[str,List[Mapping[str,Any]]]={}
        for i,row in enumerate(rows):
            rid=str(_first(row,_ROUTE_KEYS,f"route_{i:06d}"))
            grouped.setdefault(rid,[]).append(row)
        return [adapt_route({"route_id":rid,"reactions":rxns},i,"csv") for i,(rid,rxns) in enumerate(grouped.items())]
    raise ValueError(f"unsupported fixed-candidate format: {suffix}")
