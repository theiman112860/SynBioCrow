from __future__ import annotations
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from synbiocrow import SynBioCrowEngine
from synbiocrow.execution import DesignRequest, design, json_safe
from synbiocrow.bootstrap import bootstrap_advice
from synbiocrow.learning import LearningPolicy, load_policy, load_outcomes

def _progress(pct:float,msg:str)->None:
    print(f"[SynBioCrow] {pct:5.1f}% | {msg}",flush=True)

def build_parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="synbiocrow",description="SynBioCrow 2.4 Candidate-stage CLI")
    sub=p.add_subparsers(dest="command",required=True)

    ready=sub.add_parser("readiness",help="report backend readiness/configuration")
    ready.add_argument("--json",action="store_true",dest="as_json")

    boot=sub.add_parser("bootstrap",help="show backend installation/configuration guidance")
    boot.add_argument("--json",action="store_true",dest="as_json")

    des=sub.add_parser("design",help="run bounded pathway design")
    des.add_argument("target_smiles")
    des.add_argument("--mode",choices=["biosynthesis","hybrid","non-biosynthesis"],default="biosynthesis")
    des.add_argument("--backend",action="append",dest="backends",default=[])
    des.add_argument("--sink",action="append",dest="sinks",default=[])
    des.add_argument("--state-dir",default=".synbiocrow_runs")
    des.add_argument("--no-resume",action="store_true")
    des.add_argument("--max-route-steps",type=int,default=8)
    des.add_argument("--max-routes",type=int,default=100)
    des.add_argument("--output",default=None)

    learn=sub.add_parser("learn",help="apply structured Test outcomes to a bounded ranking policy")
    learn.add_argument("--outcomes",required=True)
    learn.add_argument("--policy",default=None)
    learn.add_argument("--learning-rate",type=float,default=0.10)
    learn.add_argument("--output",required=True)
    learn.add_argument("--audit-log",default=None)
    return p

def main(argv=None)->int:
    args=build_parser().parse_args(argv)
    engine=SynBioCrowEngine()

    if args.command=="readiness":
        data=engine.backend_readiness()
        if args.as_json:
            print(json.dumps(data,indent=2,sort_keys=True))
        else:
            for bid in engine.backend_ids():
                row=data.get(bid,{})
                state="READY" if row.get("available") else "NOT_READY"
                print(f"{bid:20s} {state:10s} {json.dumps(row,sort_keys=True)}")
        return 0

    if args.command=="bootstrap":
        data=bootstrap_advice(engine)
        if args.as_json:
            print(json.dumps(json_safe(data),indent=2,sort_keys=True))
        else:
            for row in data:
                state="READY" if row.ready else "NOT_READY"
                print(f"{row.backend_id:20s} {state:10s} {row.install_hint}")
                if row.external_requirements:
                    print("  external:",", ".join(row.external_requirements))
        return 0

    if args.command=="learn":
        policy=load_policy(args.policy) if args.policy else LearningPolicy()
        outcomes=load_outcomes(args.outcomes)
        new_policy,update=engine.learn(
            policy,
            outcomes,
            learning_rate=args.learning_rate,
            audit_log=args.audit_log,
        )
        payload={"policy":asdict(new_policy),"update":asdict(update)}
        Path(args.output).write_text(
            json.dumps(payload,indent=2,sort_keys=True)+"
",
            encoding="utf-8",
        )
        print(f"[SynBioCrow] learned policy v{new_policy.version}: {args.output}")
        print(f"[SynBioCrow] audit digest: {update.audit_digest}")
        return 0

    request=DesignRequest(
        target_smiles=args.target_smiles,
        mode=args.mode,
        backend_ids=tuple(args.backends) if args.backends else None,
        sink_smiles=tuple(args.sinks),
        max_route_steps=args.max_route_steps,
        max_routes=args.max_routes,
    )
    result=design(
        request,
        engine=engine,
        state_root=args.state_dir,
        resume=not args.no_resume,
        progress=_progress,
    )
    payload=json_safe(result)
    text=json.dumps(payload,indent=2,sort_keys=True)
    if args.output:
        Path(args.output).write_text(text+"
",encoding="utf-8")
        print(f"[SynBioCrow] result: {args.output}")
    else:
        print(text)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
