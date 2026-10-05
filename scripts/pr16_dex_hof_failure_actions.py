#!/usr/bin/env python3
"""HOFの新規隔離縦切りだけ。過去の受入nativeを重ねない。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_failure as f
import pr16_dex_union_formatter_actions as prior
need,identity=f.need,f.identity
BASE='83d45ede769c70b37d718e70fa3a8326ba66e2df'
HEADER='tools/mgba_pr16_dex_hof_failure.h';GUIDE='docs/PR16_DEX_HOF_FAILURE_JA.md';WF='.github/workflows/pr16-dex-hof-failure.yml'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_hof_failure.py','scripts/pr16_dex_hof_failure_actions.py','scripts/pr16_dex_hof_tail_lease.py','content/modernization/pr16_dex_hof_tail_lease.json','tests/test_pr16_dex_hof_failure.py',HEADER,GUIDE,WF}
OUT=ROOT/'.local/pr16-dex-hof-failure';PUBLIC=ROOT/'public-dex-hof-failure';ARTIFACT='pr16-dex-hof-failure-text-only'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_failure_actions.py')
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized HOF first current run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'exact new HOF sources')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'all prior records terminal')
 for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'every previously bound source retained '+path)
 j=t.api('actions/jobs/111583091182');need(j['run_id']==37252588731 and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'prior closeout terminal success')
def reconstruct():
 prior.OUT=OUT/'parent';prior.OUT.mkdir();_,_,before,_,_=prior.reconstruct();need(identity(before)==f.checkpoint()['candidate'],'whole current Union reconstruction')
 payload,linked=f.link(OUT/'hof',before);after,placed=f.apply(before,payload,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after);return candidate,before,after,linked,placed
def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh HOF run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_hof_failure.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==8,'eight new HOF host tests');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  candidate,before,after,linked,placed=reconstruct();ci=identity(after);write(PUBLIC/'build.json',dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'same fixed runtime')
  entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in prior.parent.prior.f.b.lifecycle.checkpoint()['link']['exports'].items())+'#define HOF_WAIT '+hex(linked['exports']['VegaDexHofSaveFailureWait'])+'u\n')
  src=OUT/'hof.c';src.write_text((ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text().replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')+'\n'+(ROOT/HEADER).read_text());exe=OUT/'hof'
  r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict HOF compile '+r.stderr[-1800:])
  attempts.append('hof-isolated');write(PUBLIC/'attempts.json',dict(native_processes=1,cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=600);(PUBLIC/'isolated-stdout.txt').write_text(r.stdout);(PUBLIC/'isolated-stderr.txt').write_text(r.stderr);need(r.returncode==0 and not r.stderr,'isolated rc='+str(r.returncode)+' '+r.stderr[-1400:]);native=json.loads(r.stdout);need(native['status']=='PASS_ISOLATED_HOF_FAILURE_NOTIFICATION_NO_RETRY'and native['cases']==2880,'all new HOF conditions');need(candidate.read_bytes()==after,'private candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_ISOLATED_HOF_FAILURE_NOTIFICATION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,isolated=native,native_processes=1,host_tests=8,unaffected_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,all_save_modes_accepted=False,common_failure_all_callers_accepted=False,hof_real_ui_accepted=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC)
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated HOF publication')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in{'host-tests.txt','build.json','measurement.json','attempts.json','failure.json','isolated-stdout.txt','isolated-stderr.txt'},'closed regular text only');b=p.read_bytes();need(len(b)<1500000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed HOF action');globals()[sys.argv[1]]()
