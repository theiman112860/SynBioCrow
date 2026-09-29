from __future__ import annotations

import argparse, json, os, subprocess, time
from pathlib import Path

SCHEMA='synbiocrow.biopks.external.v1'

def run_trial(python,runner,target_smiles,options,timeout_s):
    req={'schema':SCHEMA,'target_smiles':target_smiles,'options':options}
    t0=time.time()
    try:
        p=subprocess.run([python,runner],input=json.dumps(req),text=True,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout_s)
        elapsed=time.time()-t0
        try:
            payload=json.loads(p.stdout)
        except Exception:
            payload={'schema':SCHEMA,'status':'ERROR','routes':[],
                     'error_type':'InvalidJSON','error':p.stdout[-2000:]}
        return {
            'execution_status':'RETURNED',
            'return_code':p.returncode,
            'elapsed_seconds':elapsed,
            'response':payload,
            'stderr_tail':p.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            'execution_status':'TIMEOUT',
            'elapsed_seconds':time.time()-t0,
            'timeout_seconds':timeout_s,
            'stdout_tail':(exc.stdout or '')[-2000:] if isinstance(exc.stdout,str) else '',
            'stderr_tail':(exc.stderr or '')[-4000:] if isinstance(exc.stderr,str) else '',
        }
    except Exception as exc:
        return {
            'execution_status':'ERROR',
            'elapsed_seconds':time.time()-t0,
            'error_type':type(exc).__name__,
            'error':str(exc),
        }

def passed(result):
    if result.get('execution_status')!='RETURNED':
        return False
    resp=result.get('response') or {}
    return resp.get('status') in {'COMPLETE','PASS','NO_HIT'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--python',required=True)
    ap.add_argument('--runner',required=True)
    ap.add_argument('--panel',required=True)
    ap.add_argument('--output-dir',required=True)
    ap.add_argument('--timeout-smoke',type=int,default=60)
    ap.add_argument('--timeout-pks',type=int,default=240)
    ap.add_argument('--timeout-combined',type=int,default=360)
    args=ap.parse_args()

    panel=json.loads(Path(args.panel).read_text())
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    report={'schema':'synbiocrow.biopks_reentry_gate.v1','targets':{},'gate':{},'truth_accessed':False}

    # Stage 0: import/configuration smoke. One target is enough.
    t0=panel['targets'][0]
    smoke=run_trial(args.python,args.runner,t0['target_smiles'],{'smoke_only':True},args.timeout_smoke)
    report['gate']['stage_0_smoke']=smoke
    (out/'stage_0_smoke.json').write_text(json.dumps(smoke,indent=2,sort_keys=True)+'\n')
    if not passed(smoke):
        report['gate']['status']='BLOCKED_STAGE_0'
        (out/'biopks_reentry_report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(json.dumps(report['gate'],indent=2)); return 2

    stage1_pass=False
    stage2_pass=False
    for target in panel['targets']:
        tid=target['target_id']; report['targets'][tid]={}
        pks=run_trial(args.python,args.runner,target['target_smiles'],
                      {'pathway_sequence':['pks'],'max_designs':1,'target_name':tid},args.timeout_pks)
        report['targets'][tid]['pks_only']=pks
        (out/f'{tid}.pks_only.json').write_text(json.dumps(pks,indent=2,sort_keys=True)+'\n')
        if passed(pks):
            stage1_pass=True
        else:
            continue

        combined=run_trial(args.python,args.runner,target['target_smiles'],
                           {'pathway_sequence':['pks','bio'],'max_designs':1,'target_name':tid},args.timeout_combined)
        report['targets'][tid]['combined']=combined
        (out/f'{tid}.combined.json').write_text(json.dumps(combined,indent=2,sort_keys=True)+'\n')
        if passed(combined):
            stage2_pass=True

    report['gate']['stage_1_pks_only_pass']=stage1_pass
    report['gate']['stage_2_combined_pass']=stage2_pass
    report['gate']['status']='PASS_REENTRY' if stage2_pass else ('PARTIAL_STAGE_1' if stage1_pass else 'BLOCKED_STAGE_1')
    report['gate']['manuscript_reentry_allowed']=bool(stage2_pass)
    (out/'biopks_reentry_report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['gate'],indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
