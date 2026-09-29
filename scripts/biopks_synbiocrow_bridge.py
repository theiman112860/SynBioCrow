#!/usr/bin/env python3
from __future__ import annotations
import contextlib
import hashlib
import json
import os
import sys
import traceback
import builtins
from pathlib import Path
from typing import Any

SCHEMA="synbiocrow.biopks.external.v1"

def _safe(value:Any)->Any:
    if value is None or isinstance(value,(str,int,float,bool)):
        return value
    if isinstance(value,dict):
        return {str(k):_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,set)):
        return [_safe(v) for v in value]
    if hasattr(value,"__dict__"):
        return {str(k):_safe(v) for k,v in vars(value).items() if not str(k).startswith("_")}
    return repr(value)

def _steps_from_non_pks(pathway:dict[str,Any])->list[dict[str,Any]]:
    reactions=pathway.get("reactions (SMILES)") or pathway.get("reactions") or []
    feas=pathway.get("feasibilities") or []
    out=[]
    for i,rxn in enumerate(reactions):
        if not isinstance(rxn,str) or "=" not in rxn:
            continue
        score=None
        if i < len(feas):
            try: score=float(feas[i])
            except Exception: score=None
        out.append({
            "step_type":"POST_PKS",
            "reaction":rxn,
            "rule_id":f"biopks_non_pks_{i}",
            "score":score,
            "retrosynthetic_parent_side":"left",
        })
    return out

def _normalize_results(obj,target_smiles:str)->list[dict[str,Any]]:
    routes=[]
    for result_index,raw in enumerate(getattr(obj,"results_logs",[]) or []):
        item=_safe(raw)
        if not isinstance(item,dict):
            continue
        base={
            "route_class":"PKS_SPECIALIST",
            "score":item.get("pks_product_similarity"),
            "predicted_product_smiles":item.get("non_pks_product") or item.get("pks_product"),
            "pks_design":item.get("pks_design"),
            "module_architecture":item.get("pks_design"),
            "specialist_sequence_complete":False,
            "experimental_validation_claimed":False,
        }
        non_pks=item.get("non_pks_pathways")
        if isinstance(non_pks,dict) and non_pks:
            for path_id,pathway in sorted(non_pks.items(),key=lambda kv:str(kv[0])):
                if not isinstance(pathway,dict):
                    continue
                payload=f"{target_smiles}\n{result_index}\n{path_id}"
                rid="BIOPKS-"+hashlib.sha256(payload.encode()).hexdigest()[:16]
                route=dict(base)
                route["route_id"]=rid
                route["steps"]=_steps_from_non_pks(pathway)
                route["biopks_path_id"]=str(path_id)
                routes.append(route)
        else:
            payload=f"{target_smiles}\n{result_index}\narchitecture"
            rid="BIOPKS-"+hashlib.sha256(payload.encode()).hexdigest()[:16]
            route=dict(base)
            route["route_id"]=rid
            route["steps"]=[]
            routes.append(route)
    return routes

def main()->int:
    protocol_out=sys.stdout
    try:
        request=json.load(sys.stdin)
        if request.get("schema")!=SCHEMA:
            raise ValueError(f"unsupported schema: {request.get('schema')!r}")
        target=str(request["target_smiles"])
        options=dict(request.get("options") or {})
        smoke_only=bool(options.pop("smoke_only",False))
        max_designs=int(options.pop("max_designs",4))
        if max_designs < 0 or max_designs > 20:
            raise ValueError("max_designs must be between 0 and 20")
        pathway_sequence=options.pop("pathway_sequence",["pks","bio"])
        target_name=str(options.pop("target_name","synbiocrow_target"))
        release=str(options.pop("pks_release_mechanism","thiolysis"))
        root=Path(os.environ.get("SYNBIOCROW_BIOPKS_ROOT","/content/BioPKS-Pipeline"))
        config=Path(options.pop("config_filepath",root/"scripts"/"input_config_file.json"))
        if options:
            raise ValueError("unsupported BioPKS bridge options: "+", ".join(sorted(options)))

        # BioPKS/RetroTide still uses legacy pkg_resources. Some modern
        # environments omit it from the runtime unless setuptools is explicitly
        # installed, and some vendored modules reference the name indirectly.
        # Import it once and expose it through builtins before BioPKS imports.
        try:
            import pkg_resources as _pkg_resources
            builtins.pkg_resources = _pkg_resources
        except Exception as exc:
            raise RuntimeError(
                "BioPKS requires legacy pkg_resources; install setuptools<81 "
                f"in the isolated runtime ({type(exc).__name__}: {exc})"
            ) from exc

        # BioPKS is verbose. Keep stdout exclusively for the JSON protocol.
        with contextlib.redirect_stdout(sys.stderr):
            from biopks_pipeline import biopks_pipeline as pipeline_module
            from DORA_XGB import DORA_XGB
            if smoke_only:
                response={
                    "schema":SCHEMA,
                    "status":"NO_HIT",
                    "routes":[],
                    "diagnostics":{
                        "bridge_import":"PASS",
                        "biopks_root":str(root),
                        "config_exists":config.is_file(),
                    },
                }
            else:
                classifier=DORA_XGB.feasibility_classifier(
                    cofactor_positioning="add_concat",
                    model_type="spare",
                )
                obj=pipeline_module.biopks_pipeline(
                    pathway_sequence=list(pathway_sequence),
                    target_smiles=target,
                    target_name=target_name,
                    feasibility_classifier=classifier,
                    pks_release_mechanism=release,
                    config_filepath=str(config),
                )
                obj.run_combined_synthesis(max_designs=max_designs)
                routes=_normalize_results(obj,target)
                response={
                    "schema":SCHEMA,
                    "status":"COMPLETE" if routes else "NO_HIT",
                    "routes":routes,
                    "diagnostics":{
                        "results_log_count":len(getattr(obj,"results_logs",[]) or []),
                        "bridge":"synbiocrow-biopks-v1",
                    },
                }
        protocol_out.write(json.dumps(response,sort_keys=True))
        protocol_out.write("\n")
        protocol_out.flush()
        return 0
    except Exception as exc:
        response={
            "schema":SCHEMA,
            "status":"ERROR",
            "routes":[],
            "error_type":type(exc).__name__,
            "error":str(exc),
            "traceback":traceback.format_exc(limit=8),
        }
        protocol_out.write(json.dumps(response,sort_keys=True))
        protocol_out.write("\n")
        protocol_out.flush()
        return 0

if __name__=="__main__":
    raise SystemExit(main())
