#!/usr/bin/env python3
"""Seven distinct operational adapter slots, each isolated and attempted in a fresh run.
Native outputs are never replaced by historical evidence; errors remain visible.
"""
import argparse,csv,hashlib,json,os,pathlib,subprocess,sys,time,traceback,zipfile,signal,shutil
ROOT=pathlib.Path(__file__).resolve().parent
ENGINES=['DORAnet','AiZynthFinder','ChemEnzyRetroPlanner','RetroTide','BioPKS','RetroBioCat2','RetroPath2']
TARGETS={'3_hydroxypropionic_acid':'O=C(O)CCO','butanal':'CCCC=O','hexanoic_acid':'CCCCCC(=O)O'}
def execute(name,cmd,out,timeout):
 log=out/'logs'/(name+'.log');log.parent.mkdir(parents=True,exist_ok=True)
 print('[MASTER V2]',name,'START',flush=True);start=time.monotonic()
 with log.open('w') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=str(ROOT),start_new_session=True,env={**os.environ,'PYTHONUNBUFFERED':'1','PYTHONHASHSEED':'0','PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')})
  last=0
  while p.poll() is None:
   elapsed=time.monotonic()-start
   if elapsed>timeout:
    os.killpg(p.pid,signal.SIGKILL);p.wait();return {'status':'TIMEOUT','seconds':round(elapsed),'log':str(log.relative_to(out))}
   if elapsed-last>=30:
    last=elapsed;print('[MASTER V2]',name,'elapsed',round(elapsed),'s',flush=True)
   time.sleep(1)
 return {'status':'PROCESS_PASS' if p.returncode==0 else 'PROCESS_FAILED','exit_code':p.returncode,'seconds':round(time.monotonic()-start,1),'log':str(log.relative_to(out))}
def collect_external(engine, out, started_ns):
 """Explicitly parse native evidence. Never count a route count or template as a reaction."""
 import csv,json,pathlib,shutil
 roots={
  'DORAnet':pathlib.Path('/content/synbiocrow_doranet_native'),
  'AiZynthFinder':pathlib.Path('/content/synbiocrow_aizynth/outputs'),
  'RetroPath2':pathlib.Path('/content/retropath2_standalone'),
  'RetroBioCat2':pathlib.Path('/content/rbc2_native_verified/results')}
 root=roots.get(engine)
 if not root or not root.exists():return [],{'root':str(root),'status':'NOT_FOUND'}
 dest=out/'native'/engine/'external_evidence';dest.mkdir(parents=True,exist_ok=True)
 if engine=='DORAnet':paths=[root/'results.json']
 elif engine=='AiZynthFinder':paths=list(root.glob('*_native_routes.json'))
 elif engine=='RetroPath2':paths=list(root.glob('runs/*/results/results.csv'))
 elif engine=='RetroBioCat2':paths=[root/'results.json']
 else:paths=[]
 records=[];selected=[];diagnostics=[]
 def emit(a,b,f,**extra):
  if not isinstance(a,str) or not isinstance(b,str) or not a or not b:return
  records.append({'engine':engine,'reactants':a,'products':b,'reaction_smiles':a+'>>'+b,
                  'native_file':str(f.relative_to(out)), 'fresh_native':True,'candidate_only':True,
                  **extra})
 for f in paths[:40]:
  if not f.is_file() or f.stat().st_size>30_000_000 or f.stat().st_mtime_ns < started_ns:continue
  copy=dest/(str(len(selected))+'_'+f.name);shutil.copy2(f,copy);selected.append(str(f))
  try:
   if engine=='RetroPath2':
    with f.open(newline='') as h:
     reader=csv.DictReader(h)
     for row_index,r in enumerate(reader,1):
      rxn=r.get('Reaction SMILES') or r.get('reaction_smiles') or ''
      if '>>' in rxn:
       a,b=rxn.split('>>',1);emit(a,b,copy,direction='native_source_expansion',native_pointer=f'csv:{row_index}',
            native_template=r.get('Rule ID'))
   else:
    obj=json.loads(f.read_text())
    if engine=='DORAnet':
     for target_index,target in enumerate(obj.get('targets',[])):
      for reaction_index,r in enumerate(target.get('reactions',[])):
       # DORAnet uses human-readable `a + b = c + d`, not reaction SMILES.
       raw=r.get('reaction','')
       if ' = ' in raw:
        left,right=raw.split(' = ',1)
        # Plus-separated species are joined by dot, preserving original raw reaction.
        direction=r.get('metadata',{}).get('direction',obj.get('direction'))
        if direction not in ('retro','forward'):
         raise ValueError('DORAnet reaction direction missing from native report')
        a,b=(right,left) if direction=='retro' else (left,right)
        emit('.'.join(x.strip() for x in a.split(' + ')),'.'.join(x.strip() for x in b.split(' + ')),
             copy,direction='precursors_to_target',native_direction=direction,native_reaction=raw,
             target_smiles=target.get('smiles'),native_template=r.get('rule_id'),
             native_pointer=f'/targets/{target_index}/reactions/{reaction_index}')
    elif engine=='RetroBioCat2':
     for target_index,t in enumerate(obj.get('targets',[])):
      for reaction_index,r in enumerate(t.get('reactions',[])):
       rx=r.get('reaction_smiles','')
       if '>>' in rx:
        a,b=rx.split('>>',1)
        emit(a,b,copy,direction='precursors_to_target',target_smiles=t.get('smiles'),
             native_template=r.get('reaction_name'),native_pointer=f'/targets/{target_index}/reactions/{reaction_index}')
    elif engine=='AiZynthFinder':
     def walk(node,path,parent=None):
      if not isinstance(node,dict):return
      if node.get('type')=='reaction':
       precursors=[c.get('smiles') for c in node.get('children',[]) if isinstance(c,dict) and c.get('type')=='mol' and c.get('smiles')]
       if parent and precursors:
        emit('.'.join(precursors),parent,copy,direction='precursors_to_target',
             target_smiles=obj.get('target_smiles'),native_pointer=path,
             native_template=node.get('metadata',{}).get('template_hash'))
      for i,child in enumerate(node.get('children',[])):
       walk(child,f'{path}/children/{i}',node.get('smiles') if node.get('type')=='mol' else None)
     for i,route in enumerate(obj.get('routes',[])):walk(route.get('tree',{}),f'/routes/{i}/tree')
  except Exception as exc:diagnostics.append(str(f)+': '+repr(exc))
 digests={name:hashlib.sha256((out/name).read_bytes()).hexdigest()
          for name in {row["native_file"] for row in records}}
 for row in records:
  row["native_sha256"]=digests[row["native_file"]]
 return records,{'root':str(root),'files':selected,'diagnostics':diagnostics,'collected':len(records)}

def collect_retrotide_design_evidence(out, started_ns):
 """Collect actual specialist design/TE evidence without inventing separate reactions.

 The packaged RetroTide adapter currently invokes the shared BioPKS implementation.
 The design records demonstrate execution, not a distinct algorithm or extra chemistry.
 """
 import pathlib,shutil,json
 root=pathlib.Path('/content/synbiocrow_retrotide_native/outputs')
 dest=out/'native'/'RetroTide'/'external_evidence'
 candidates=list(root.glob('**/native_design_release_records.json')) if root.exists() else []
 if not candidates:return {'status':'NO_DESIGN_EVIDENCE','native_designs':0,'native_te_calls':0,'exact_target_matches':0}
 dest.mkdir(parents=True,exist_ok=True)
 candidates=[path for path in candidates if path.stat().st_mtime_ns >= started_ns]
 if not candidates:return {'status':'NO_FRESH_DESIGN_EVIDENCE'}
 src=max(candidates,key=lambda p:p.stat().st_mtime)
 dst=dest/src.name;shutil.copy2(src,dst)
 try: records=json.loads(dst.read_text())
 except Exception as exc:return {'status':'INVALID_DESIGN_EVIDENCE','error':repr(exc)}
 if not isinstance(records,list):return {'status':'UNEXPECTED_DESIGN_SCHEMA','record_type':type(records).__name__}
 return {'status':'RETROTIDE_NATIVE_DESIGN_API_EVIDENCE','native_designs':len(records),
         'native_te_calls':sum(bool(r.get('native_release_product_smiles')) for r in records if isinstance(r,dict)),
         'exact_target_matches':sum(bool(r.get('exact_target_match')) for r in records if isinstance(r,dict)),
         'evidence_file':str(dst.relative_to(out)),
         'evidence_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
         'independent_retrotide_api_verified':bool(records) and all(bool(r.get('native_retrotide_designPKS_called')) for r in records if isinstance(r,dict)),
         'additional_unique_reactions_counted':0}

def collect_biopks_design_evidence(out, started_ns):
 src=pathlib.Path('/content/synbiocrow_m2412/outputs/native_design_release_records.json')
 if not src.is_file() or src.stat().st_mtime_ns < started_ns:
  return {'status':'NO_FRESH_DESIGN_EVIDENCE'}
 data=src.read_bytes()
 records=json.loads(data)
 if not isinstance(records,list) or not records or not all(
     isinstance(record,dict) and record.get('native_bound_smiles') for record in records):
  raise ValueError('Unexpected BioPKS design schema')
 dest=out/'native'/'BioPKS'/'external_evidence'/src.name
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(data)
 return {'status':'BIOPKS_NATIVE_DESIGN_API_EVIDENCE','native_designs':len(records),
         'exact_target_matches':sum(bool(record.get('exact_target_match')) for record in records),
         'evidence_file':str(dest.relative_to(out)),'evidence_sha256':hashlib.sha256(data).hexdigest()}

def build_runner(engine,source,target):
 """Execute proven notebook source as isolated script; strip Colab-only UI and notebook magic.
Each script runs in its own process to prevent global-state collisions.
"""
 nb=json.loads((ROOT/(engine+'.ipynb')).read_text());chunks=[]
 for c in nb['cells']:
  if c['cell_type']!='code':continue
  s=''.join(c['source']);lines=s.splitlines()
  if any('files.download(' in x for x in lines):continue
  if any(x.strip().startswith(('%%','!')) for x in lines):continue
  cleaned=[]
  for line in lines:
   if line.lstrip().startswith('%pip '):
    cleaned.append('import subprocess,sys; subprocess.run([sys.executable,"-m","pip"]+'+repr(line.strip()[5:].split())+',check=True)')
   elif line.lstrip().startswith('%'):continue
   else:cleaned.append(line)
  code='\n'.join(cleaned)
  try:compile(code,'cell','exec')
  except SyntaxError:continue
  chunks.append(code)
 return '\n\n'.join(chunks)
def run_chemenzy(args, out, folder):
 cache = os.environ.get("CHEMENZY_CACHE")
 if not cache:
  return {"run":{"status":"SKIPPED_UNAVAILABLE","error":"Set CHEMENZY_CACHE"}}, [], [], {}
 runner = ROOT.parents[1] / "scripts/chemenzy/runner.py"
 upstream = os.environ.get("CHEMENZY_UPSTREAM", "/content/ChemEnzyRetroPlanner")
 native_out = folder / "local_native"
 command = [sys.executable, runner, "--cache", cache, "--upstream", upstream, "--out", native_out,
            "--timeout", str(args.timeout),
            "--stock", os.environ.get("CHEMENZY_STOCK", "BioNav-stock"),
            "--iterations", os.environ.get("CHEMENZY_ITERATIONS", "12"),
            "--gpu", os.environ.get("CHEMENZY_GPU", "-1")]
 if os.environ.get("CHEMENZY_FETCH") == "1":
  command.append("--fetch")
 for name in args.targets:
  command.extend(["--target", TARGETS[name]])
 state = {"run": execute("ChemEnzyRetroPlanner_native", list(map(str, command)), out, args.timeout)}
 status_file = native_out / "status.json"
 if not status_file.is_file():
  return state, [], [], {}
 status = json.loads(status_file.read_text())
 state["native_status"] = status
 if status["status"] not in ("NATIVE_OUTPUT", "NO_ROUTE"):
  return state, [], [], {}
 raw = native_out / "routes.json"
 digest = hashlib.sha256(raw.read_bytes()).hexdigest()
 normalized = native_out / "reactions.json"
 if digest != status["routes_sha256"] or hashlib.sha256(normalized.read_bytes()).hexdigest() != status["reactions_sha256"]:
  raise ValueError("ChemEnzy native evidence hash mismatch")
 rows = [dict(record, engine="ChemEnzyRetroPlanner", native_file=str(raw.relative_to(out)),
              native_sha256=digest, fresh_native=True, candidate_only=True)
         for record in json.loads(normalized.read_text())]
 return state, rows, [str(raw.relative_to(out))], {"config_sha256":status["config_sha256"]}


def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--targets',nargs='+',default=list(TARGETS));p.add_argument('--timeout',type=int,default=3600);p.add_argument('--engines',nargs='+',default=ENGINES);a=p.parse_args()
 out=pathlib.Path(a.output).resolve();out.mkdir(parents=True)
 report={'version':'M1_20_7_REVIEW','targets':a.targets,'engine_states':{},'fresh_native_records':0,'replayed_records':0,'seven_engine_live_gate':'NOT_PASSED','limitations':['Separate operational adapters do not imply independent algorithms','ChemEnzyRetroPlanner local routes require a verified native artifact hash','Raw template hits and designs are not certified reactions','Automated hybrid candidates are structural only']}
 def checkpoint(): (out/'summary.json').write_text(json.dumps(report,indent=2))
 allrows=[]
 for engine in a.engines:
  print('\n[MASTER V2]',engine,flush=True);folder=out/'native'/engine;folder.mkdir(parents=True,exist_ok=True)
  started_ns=time.time_ns()
  try:
   if engine=='ChemEnzyRetroPlanner':
    state,rows,files,ev=run_chemenzy(a,out,folder)
   elif engine=='RetroBioCat2':
    code=build_runner(engine,ROOT/(engine+'.ipynb'),a.targets)
    script=folder/'native_notebook.py';script.write_text(code)
    state={'syntax':'PASS','run':execute(engine+'_native',[sys.executable,'-u',str(script)],out,a.timeout)}
   elif engine=='RetroTide':
    # RetroTide/RetroTide-derived PKS specialist shares the BioPKS implementation in this source package.
    # Run its native design-and-release path, but do not double-count BioPKS chemistry.
    code=build_runner(engine,ROOT/(engine+'.ipynb'),a.targets)
    script=folder/'native_notebook.py';script.write_text(code)
    state={'syntax':'PASS','run':execute(engine+'_native',[sys.executable,'-u',str(script)],out,a.timeout),
           'implementation_note':'Direct RetroTide designPKS invocation; shared upstream package with BioPKS',
           'acceptance_override':'RETROTIDE_DESIGN_API_VERIFICATION_PENDING'}
   else:
    code=build_runner(engine,ROOT/(engine+'.ipynb'),a.targets)
    script=folder/'native_notebook.py';script.write_text(code)
    try:compile(code,str(script),'exec');syntax='PASS'
    except Exception as exc:syntax=repr(exc)
    state={'syntax':syntax,'run':execute(engine+'_native',[sys.executable,'-u',str(script)],out,a.timeout) if syntax=='PASS' else {'status':'SCRIPT_ERROR'}}
   if engine in ('DORAnet','AiZynthFinder','RetroBioCat2','RetroPath2'):
    rows,ev=collect_external(engine,out,started_ns)
    files=sorted({row['native_file'] for row in rows})
   if engine in ('BioPKS','RetroTide'):
    rows,files,ev=[],[],{}
   if engine=='BioPKS':
    state['specialist_evidence']=collect_biopks_design_evidence(out,started_ns)
    state['acceptance_override']=state['specialist_evidence']['status']
   if engine=='RetroTide':
    state['specialist_evidence']=collect_retrotide_design_evidence(out,started_ns)
    state['acceptance_override']='RETROTIDE_NATIVE_DESIGN_API_PASS' if state['specialist_evidence'].get('independent_retrotide_api_verified') else 'RETROTIDE_DESIGN_API_NOT_VERIFIED'
    rows=[] # shared BioPKS source; never double-count
   allrows+=rows;state['parsed_reaction_records']=len(rows);state['native_json_files']=files;state['external_evidence']=ev;state['acceptance']=state.get('acceptance_override') or ('NATIVE_REACTIONS_EXPORTED' if rows else 'NATIVE_REACTION_GATE_OPEN')
  except Exception as exc:state={'status':'EXCEPTION','error':repr(exc),'traceback':traceback.format_exc()[-3000:]}
  report['engine_states'][engine]=state;report['fresh_native_records']=sum(bool(r.get('fresh_native')) for r in allrows);report['historical_hosted_reactions']=sum(not bool(r.get('fresh_native')) for r in allrows);checkpoint()
 # No fabricated edges: only forward exact product->reactant identity across different engines.
 edges=[]
 for i,x in enumerate(allrows):
  for j,y in enumerate(allrows):
   if i!=j and x['engine']!=y['engine'] and x['products']==y['reactants']:
    edges.append({'upstream_index':i,'downstream_index':j,'shared_molecule':x['products'],'status':'STRUCTURAL_CANDIDATE_NOT_CERTIFIED'})
 (out/'fresh_native_reactions.json').write_text(json.dumps(allrows,indent=2))
 with (out/'fresh_native_reactions.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['engine','reactants','products','reaction_smiles','native_file','native_sha256','native_pointer','native_template','target_smiles','direction','native_direction','native_reaction','fresh_native','candidate_only']);w.writeheader();w.writerows(allrows)
 (out/'hybrid_candidates.json').write_text(json.dumps(edges,indent=2))
 report['hybrid_candidates']=len(edges)
 report['seven_engine_execution_gate']='PASSED' if all(report['engine_states'].get(e,{}).get('run',{}).get('status')=='PROCESS_PASS' and (report['engine_states'][e].get('acceptance')=='NATIVE_REACTIONS_EXPORTED' or (e=='RetroTide' and report['engine_states'][e].get('acceptance')=='RETROTIDE_NATIVE_DESIGN_API_PASS') or (e=='BioPKS' and report['engine_states'][e].get('acceptance')=='BIOPKS_NATIVE_DESIGN_API_EVIDENCE')) for e in ENGINES) and report['historical_hosted_reactions']==0 else 'NOT_PASSED'
 report['seven_engine_reaction_export_gate']='PASSED' if all(report['engine_states'].get(e,{}).get('parsed_reaction_records',0)>0 for e in ENGINES) else 'NOT_PASSED'
 report['seven_engine_live_gate']='NOT_VERIFIED'
 report['retro_tide_output_type']='Native PKS designs, not reaction records'
 checkpoint();print(json.dumps(report,indent=2))
if __name__=='__main__':main()
