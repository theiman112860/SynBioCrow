from __future__ import annotations
from dataclasses import asdict
from typing import Callable, Any

from synbiocrow.core.models import LifecycleState, PathwayCandidate, ReactionStep
from synbiocrow.ensemble import resolve_compound
from synbiocrow.execution.models import DesignRequest, DesignResult
from synbiocrow.execution.state import RunStateStore, stable_hash
from synbiocrow.engine import SynBioCrowEngine

ProgressCallback = Callable[[float,str],None]
VALID_MODES={"biosynthesis","hybrid","non-biosynthesis"}

def _emit(cb:ProgressCallback|None, pct:float, msg:str)->None:
    if cb is not None:
        cb(float(pct),str(msg))

def _candidate_from_dict(d:dict)->PathwayCandidate:
    steps=tuple(
        ReactionStep(
            reaction=s["reaction"],
            rule_id=s.get("rule_id"),
            source_backend=s.get("source_backend"),
            feasibility=s.get("feasibility"),
            metadata=s.get("metadata") or {},
        )
        for s in d.get("steps",[])
    )
    return PathwayCandidate(
        candidate_id=d["candidate_id"],
        target_smiles=d["target_smiles"],
        steps=steps,
        source_backends=tuple(d.get("source_backends") or ()),
        lifecycle=LifecycleState(d.get("lifecycle","CANDIDATE")),
        provenance=d.get("provenance") or {},
        evidence=d.get("evidence") or {},
    )

def _run_id(request:DesignRequest)->str:
    return "run-"+stable_hash(asdict(request))[:16]

def _mode_diagnostics(mode:str)->dict[str,Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")
    if mode=="non-biosynthesis":
        raise ValueError(
            "non-biosynthesis mode is not yet available in the consolidated 2.2 engine; "
            "no standalone chemical-synthesis backend has been migrated."
        )
    if mode=="hybrid":
        return {
            "mode":"hybrid",
            "mode_note":"Hybrid orchestration is enabled, but the currently registered generators are biosynthetic/specialized. Chemical backend migration remains future work.",
        }
    return {"mode":"biosynthesis","mode_note":"Biosynthetic/specialized generator ensemble."}

def design(
    request: DesignRequest,
    *,
    engine: SynBioCrowEngine|None=None,
    state_root: str|None=None,
    resume: bool=True,
    progress: ProgressCallback|None=None,
)->DesignResult:
    engine=engine or SynBioCrowEngine()
    mode_info=_mode_diagnostics(request.mode)
    run_id=_run_id(request)
    store=RunStateStore(state_root) if state_root else None

    _emit(progress,2,"backend readiness")
    readiness=engine.backend_readiness()
    selected=tuple(request.backend_ids or engine.backend_ids())

    unknown=[b for b in selected if b not in engine.backend_ids()]
    if unknown:
        raise ValueError(f"Unknown backends: {unknown}")

    candidates:list[PathwayCandidate]=[]
    backend_status:dict[str,dict[str,Any]]={}
    cached=store.read_stage(run_id,"candidates") if (store and resume) else None
    if cached is not None:
        candidates=[_candidate_from_dict(x) for x in cached.get("candidates",[])]
        backend_status=dict(cached.get("backend_status") or {})
        _emit(progress,35,"restored candidate generation checkpoint")
    else:
        total=max(1,len(selected))
        for i,bid in enumerate(selected):
            backend=engine.backends.get(bid)
            r=readiness.get(bid,{})
            if not r.get("available",False):
                backend_status[bid]={"status":"SKIPPED_UNAVAILABLE","readiness":r}
                _emit(progress,5+30*(i+1)/total,f"{bid}: unavailable/configuration missing")
                continue
            try:
                found=list(backend.generate(
                    request.target_smiles,
                    options=dict(request.backend_options.get(bid,{}) or {}),
                ))
                candidates.extend(found)
                backend_status[bid]={"status":"COMPLETE","candidate_count":len(found)}
            except Exception as exc:
                backend_status[bid]={
                    "status":"ERROR",
                    "error_type":type(exc).__name__,
                    "error":str(exc),
                }
            _emit(progress,5+30*(i+1)/total,f"{bid}: {backend_status[bid]['status']}")
        if store:
            store.write_stage(run_id,"candidates",{
                "request":asdict(request),
                "candidates":candidates,
                "backend_status":backend_status,
            })

    _emit(progress,45,"build cross-engine reaction graph")
    graph=engine.build_ensemble(candidates)
    graph_summary={
        "compound_count":len(graph.compounds),
        "edge_count":len(graph.edges),
        "backends":list(graph.backend_set()),
        "composite_edge_count":graph.composite_edge_count(),
    }
    if store:
        store.write_stage(run_id,"graph_summary",graph_summary)

    _emit(progress,65,"bounded route reconstruction")
    routes:list[list[str]]=[]
    if request.sink_smiles:
        target_key=resolve_compound(request.target_smiles,source="request").key
        sink_keys={resolve_compound(x,source="request").key for x in request.sink_smiles}
        routes=graph.find_routes(
            target_key,sink_keys,
            max_steps=request.max_route_steps,
            max_routes=request.max_routes,
        )
    if store:
        store.write_stage(run_id,"routes",{"routes":routes})

    diagnostics={
        **mode_info,
        "selected_backends":list(selected),
        "available_backends":[k for k,v in readiness.items() if v.get("available")],
        "resume_enabled":bool(resume),
        "state_root":state_root,
        "scientific_state":"CANDIDATE_ONLY",
    }
    result=DesignResult(
        request=request,
        candidates=candidates,
        routes=routes,
        backend_status=backend_status,
        graph_summary=graph_summary,
        diagnostics=diagnostics,
        run_id=run_id,
    )
    if store:
        store.write_stage(run_id,"result",result)
        store.write_stage(run_id,"manifest",store.latest_manifest(run_id))
    _emit(progress,100,"complete")
    return result
