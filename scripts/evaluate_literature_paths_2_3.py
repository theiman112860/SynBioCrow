from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from synbiocrow.ensemble import resolve_compound

def canonical_key(smiles:str)->str:
    return resolve_compound(smiles,source='benchmark').key

def normalize_reaction_smiles(reaction:str):
    if '>>' in reaction:
        left,right=reaction.split('>>',1)
        lhs=tuple(sorted(canonical_key(x) for x in left.split('.') if x.strip()))
        rhs=tuple(sorted(canonical_key(x) for x in right.split('.') if x.strip()))
        return lhs,rhs
    if ' = ' in reaction:
        left,right=reaction.split(' = ',1)
        lhs=tuple(sorted(canonical_key(x) for x in left.split(' + ') if x.strip()))
        rhs=tuple(sorted(canonical_key(x) for x in right.split(' + ') if x.strip()))
        return lhs,rhs
    raise ValueError(f'Unsupported reaction format: {reaction!r}')

def reaction_signature(reaction:str):
    return normalize_reaction_smiles(reaction)

def ordered_lcs(a:list,b:list)->int:
    if not a or not b:
        return 0
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b,1):
            cur.append(prev[j-1]+1 if x==y else max(prev[j],cur[-1]))
        prev=cur
    return prev[-1]

def compare_routes(predicted:Iterable[str],truth:Iterable[str])->dict:
    p=[reaction_signature(x) for x in predicted]
    t=[reaction_signature(x) for x in truth]
    ps=set(p); ts=set(t)
    inter=len(ps & ts)
    precision=inter/len(ps) if ps else 0.0
    recall=inter/len(ts) if ts else 0.0
    f1=(2*precision*recall/(precision+recall)) if precision+recall else 0.0
    lcs=ordered_lcs(p,t)
    return {
        'predicted_reactions':len(p),
        'truth_reactions':len(t),
        'exact_reaction_overlap':inter,
        'reaction_precision':precision,
        'reaction_recall':recall,
        'reaction_f1':f1,
        'ordered_lcs_count':lcs,
        'ordered_lcs_fraction':lcs/max(1,len(t)),
        'exact_route_match':p==t,
        'length_difference':len(p)-len(t),
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--benchmark',required=True)
    ap.add_argument('--predictions',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    bench=json.loads(Path(args.benchmark).read_text(encoding='utf-8'))
    preds=json.loads(Path(args.predictions).read_text(encoding='utf-8'))
    out=[]
    for rec in bench.get('records',[]):
        pid=rec['pathway_id']
        if pid.startswith('EXAMPLE_ONLY'):
            continue
        truth=[x['reaction_smiles'] for x in rec.get('reactions',[])]
        ranked=preds.get(pid,[])
        rows=[]
        for rank,route in enumerate(ranked,1):
            metrics=compare_routes(route,truth)
            metrics['rank']=rank
            rows.append(metrics)
        best=max(rows,key=lambda x:(x['reaction_recall'],x['ordered_lcs_fraction'],-x['rank'])) if rows else None
        topk={}
        for k in (1,5,10,25,50):
            topk[str(k)]=any(x['exact_route_match'] for x in rows[:k])
        out.append({
            'pathway_id':pid,
            'target_name':rec.get('target_name'),
            'prediction_count':len(ranked),
            'best':best,
            'exact_recovery_topk':topk,
        })
    payload={
        'schema':'synbiocrow.literature_pathway_evaluation.v1',
        'records':out,
        'truth_accessed':True,
        'note':'This evaluator accesses benchmark truth and must not be used during sealed prediction generation.'
    }
    Path(args.output).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
