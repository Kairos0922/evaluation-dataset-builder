#!/usr/bin/env python3
import argparse, hashlib, json, os, shutil, signal, socket, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

def now(): return datetime.now(timezone.utc).isoformat()
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tree_digest(root):
 h=hashlib.sha256()
 for p in sorted(x for x in root.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.suffix!='.pyc'):
  h.update(p.relative_to(root).as_posix().encode()+b'\0'+bytes.fromhex(digest(p)))
 return h.hexdigest()
def listening(host,port):
 with socket.socket() as s:
  s.settimeout(.2)
  try: s.connect((host,port)); return True
  except OSError: return False
def request(url,method='GET',payload=None):
 data=None if payload is None else json.dumps(payload).encode()
 req=urllib.request.Request(url,data=data,method=method,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=5) as r:
  raw=r.read()
  try: return r.status,json.loads(raw)
  except Exception: return r.status,raw.decode(errors='replace')
def wait_health(url):
 end=time.monotonic()+30; last='not ready'
 while time.monotonic()<end:
  try:
   status,data=request(url+'/api/health')
   if status==200 and data.get('status')=='ok': return data
  except Exception as e: last=str(e)
  time.sleep(.25)
 raise RuntimeError('health check timeout: '+last)
def stop(p):
 if p and p.poll() is None:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
def events(path):
 es=[]
 if path.exists():
  for line in path.read_text(errors='replace').splitlines():
   try:es.append(json.loads(line))
   except json.JSONDecodeError:pass
 calls=[e for e in es if e.get('type')=='tool_call' and e.get('tool')=='skill' and (e.get('input') or {}).get('name')=='webapp-testing']
 results={e.get('callId'):e for e in es if e.get('type')=='tool_result'}
 finals=[e for e in es if e.get('type')=='final']
 usage=[e.get('usage',{}) for e in es if e.get('type')=='status' and e.get('usage')]
 return {'event_count':len(es),'skill_calls':len(calls),'completed_skill_calls':sum(results.get(c.get('callId'),{}).get('status')=='completed' for c in calls),'final_reason':(finals[-1].get('reason') or {}).get('kind') if finals else None,'total_tokens':sum(int(u.get('totalTokens',0) or 0) for u in usage)}
def main():
 a=argparse.ArgumentParser()
 for n in ['dataset','dataset-id','fixture-source','public-assets','skill-source','work-root','output-dir','skill-commit']:a.add_argument('--'+n,required=True)
 a.add_argument('--limit',type=int,default=0);a.add_argument('--case-timeout',type=int,default=900);x=a.parse_args()
 ds=Path(x.dataset).resolve(); fixture=Path(x.fixture_source).resolve(); public=Path(x.public_assets).resolve(); skill=Path(x.skill_source).resolve(); workroot=Path(x.work_root).resolve(); out=Path(x.output_dir).resolve()
 workroot.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
 cases=[json.loads(l) for l in ds.read_text().splitlines() if l.strip()]
 if x.limit:cases=cases[:x.limit]
 key=os.environ.get('DEEPSEEK_API_KEY','')
 if not key:raise SystemExit('DEEPSEEK_API_KEY missing')
 results=[]
 for c in cases:
  cid=c['case_id'];
  if c.get('dataset_id')!=x.dataset_id:raise SystemExit('dataset mismatch: '+cid)
  er=c.get('execution_requirements') or {}; spec=er.get('environment') or {}; ui=c.get('user_input') or {}
  profile=spec.get('fixture_profile','clean'); mutations=spec.get('fixture_mutations') or []; state=spec.get('server_state_at_start','running')
  url=ui.get('target_url') or spec.get('app_url') or 'http://127.0.0.1:4173'; u=urlparse(url);host=u.hostname or '127.0.0.1';port=u.port or 4173
  if host not in ('127.0.0.1','localhost'):raise SystemExit('non-loopback target refused: '+url)
  co=out/cid;co.mkdir(parents=True,exist_ok=True);wd=workroot/cid
  if wd.exists():shutil.rmtree(wd)
  wd.mkdir(parents=True)
  shutil.copytree(public,wd/'assets'/'public',dirs_exist_ok=True);shutil.copytree(fixture,wd/'fixtures'/'workboard',dirs_exist_ok=True);shutil.copytree(skill,wd/'.dsh'/'skills'/'webapp-testing',dirs_exist_ok=True)
  wf=wd/'fixtures'/'workboard';before=tree_digest(wf);(wd/'artifacts'/cid).mkdir(parents=True,exist_ok=True)
  audit=co/'server-audit.jsonl';log=co/'server.log';lh=log.open('w');proc=None;pre=post=None;err=None;timed=False;exitcode=None;start=now()
  env=os.environ.copy()
  for k in ('APP_PROFILE','APP_MUTATIONS','APP_AUDIT_LOG','APP_PORT','APP_HOST'):env.pop(k,None)
  env.update({'DSH_TELEMETRY_MODE':'DISABLED','DSH_TELEMETRY_DISABLED':'1','DSH_HOME':os.environ['DSH_HOME']})
  if state=='stopped':env.update({'APP_HOST':host,'APP_PORT':str(port),'APP_PROFILE':profile,'APP_MUTATIONS':','.join(mutations),'APP_AUDIT_LOG':str(audit)})
  try:
   if listening(host,port):raise RuntimeError('port already occupied: '+str(port))
   if state!='stopped':
    se=os.environ.copy();se.update({'APP_HOST':host,'APP_PORT':str(port),'APP_PROQ’SHŽœ›Ùš[K	ÐTÓUUUSÓ”ÉÎ‰Ë	Ëš›Ú[Š]]][ÛœÊK	ÐTÐUQUÓÑÉÎœÝŠ]Y]
_JBˆ›ØÏ\ÝXœ›ØÙ\ÜË”Ü[ŠÜÞ\Ë™^XÝ]X›K	ÜÙ\™\‹œI×KÝÙ]Ù‹[\ÙKÝÝ][Ý\œ\ÝXœ›ØÙ\ÜË”ÕÕUÝ\Û™]×ÜÙ\ÜÚ[ÛUYJBˆØZ]ÚX[
\›
NÜ™\]Y\Ý
\›
ÉËØ\KÜ™\Ù]	Ë	ÔÔÕ	ËßJN×Ë™O\™\]Y\Ý
\›
ÉËØ\KÝ\ÚÜÉÊBˆ^[ØY^ÚÎZK™Ù]
ÊH›ÜˆÈ[ˆ
	Ý\ÚÉË	Ý\™Ù]Ý\›	Ë	Ü[\×ÜÛÝ\˜ÙIË	Ü[\×Ú[—ÜØÛÜIË	Ü™\ÜÜ™\]Z\™[Y[ÉË	ØÛÛœÝ˜Z[ÉÊ_Bˆ›Û\I×‰Ëš›Ú[ŠÉÈÈÙXˆ\XØ][Ûˆ\Ý[™È\ÚÉË	ÐØ\ÙHQˆ	ÊØÚY	Ñ]\Ù]Qˆ	ÊÞ™]\Ù]ÚY	Ô[›™YÚÚ[ÛÛ[Z]ˆ	ÊÞœÚÚ[ØÛÛ[Z]	ÉË	ÓØY[™›ÛÝÈHÙX˜\]\Ý[™ÈÚÚ[ˆ\ÙH™X[^]ÜšYÚœ›ÝÜÙ\ˆ[\˜XÝ[Û‹‰Ë	ÔX›XÈ[\È\™H[ˆ\ÜÙ]ËÜX›XËÎÈ\ÛÝ\˜ÙH\È[ˆš^\™\ËÝÛÜšØ›Ø\™È›ÜˆÝ\\[™Ù[XÝÜˆÛÛ^Û›KˆÈ›Ý™\XÙHœ›ÝÜÙ\ˆ\Ý[™ÈÚ]ÛÝ\˜ÙKÐTH[œÜXÝ[Û‹‰Ë	ÔØ]™HHÚ[™\ÙHX\šÙÝÛˆ™\Ü]šY[˜ÙKZ[™^”ÓÓ‹ØÜ™Y[œÚÝËØÜš\È[™ÙÜÈ[™\ˆ\Y˜XÝËÉÊØÚY+'/ .','Do not modify app source. Do not access external networks or hidden evaluation data. Do not search for other evaluation cases.','',json.dumps(payload,ensure_ascii=False,indent=2)])
   (co/'task-prompt.md').write_text(prompt)
   ev=co/'dsh-events.jsonl';se=co/'dsh-stderr.log'
   with ev.open('w') as stdout,se.open('w') as stderr:
    p=subprocess.Popen(['dsh','--profile','headless','--json','--permission-mode','workspace-write','-'],cwd=wd,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,start_new_session=True)
    try:
     p.communicate(prompt,timeout=x.case_timeout);exitcode=p.returncode
    except subprocess.TimeoutExpired:
     timed=True;exitcode=124
     try:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
     except Exception:
      try:os.killpg(p.pid,signal.SIGKILL)
      except ProcessLookupError:pass
      p.wait(timeout=5)
   if state!='stopped':
    try:_,post=request(url+'/api/tasks')
    except Exception as e:err='post-state capture: '+str(e)
  except Exception as e:err=type(e).__name__+': '+str(e)
  finally:
   stop(proc);lh.close();after_skill=listening(host,port)
   if after_skill:
    err=(err+'; ' if err else '')+'port remains open after Skill completion'
    f=shutil.which('fuser')
    if f:subpprocess.run([f,'-k',f'{port}/tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
   after_cleanup=listening(host,port)
  trace=events(co/'dsh-events.jsonl');after=tree_digest(wf)
  shutil.copytree(wd,co/'workspace',dirs_exist_ok=True)
  done=now();status='PASS' if exitcode==0 and trace['final_reason']=='completed' and trace['skill_calls']>0 and trace['completed_skill_calls']>0 and not err and not timed and before==after else 'BLOCKED'
  row={'case_id':cid,'dataset_id':x.dataset_id,'started_at':start,'finished_at':done,'fixture_profile_runner_only':profile,'fixture_mutations_runner_only':mutations,'server_state_at_start':state,'pre_state':pre,'post_state':post,'server_listener_after_skill':after_skill,'server_listener_after_cleanup':after_cleanup,'dsh_exit_code':exitcode,'timed_out':timed,'runner_error':err,'trace':trace,'fixture_tree_sha256_before':before,'fixture_tree_sha256_after':after,'fixture_modified_by_skill':before!=after,'status':status}
  (co/'runner-result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');results.append(row)
  print(json.dumps({'case_id':cid,'status':status,'dsh_exit_code':exitcode,'trace':trace,'runner_error':err},ensure_ascii=False),flush=True)
 leaked=[]
 for p in out.rglob('*'):
  if p.is_file():
   try:b=p.read_bytes()
   except OSError:continue
   if key.encode() in b:p.write_bytes(b.replace(key.encode(),b'[REDACTED_SECRET]'));leaked.append(str(p.relative_to(out)))
 summary={'dataset_id':x.dataset_id,'selected_cases':len(results),'runner_pass_count':sum(r['status']=='PASS' for r in results),'blocked_cases':[r['case_id'] for r in results if r['status']!='PASS'],'credential_leak_detected':bool(leaked),'redacted_files':leaked,'scope':'Skill invocation and execution completion only; not grading or Oracle adjudication','cases':[{'case_id':r['case_id'],'status':r['status'],'dsh_exit_code':r['dsh_exit_code'],'skill_calls':r['trace']['skill_calls'],'final_reason':r['trace']['final_reason']} for r in results]}
 out/'dataset-runner-summary.json'.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 return 0 if not summary['blocked_cases'] and not leaked else 1
if __name__=='__main__':raise SystemExit(main())
