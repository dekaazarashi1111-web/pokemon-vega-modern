#!/usr/bin/env python3
"""START限定gate。旧受入nativeを再走しない。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_valid_failure as f
import pr16_dex_save_failure_actions as prior
need,identity,write=prior.need,prior.identity,prior.write
BASE='a40e92f38f0e57792ee3535bffc359a9b9bdf767'
HEADER='tools/mgba_pr16_dex_start_failure.h'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_valid_failure.py','scripts/pr16_dex_start_failure_actions.py',HEADER,'tests/test_pr16_dex_start_failure.py','.github/workflows/pr16-dex-start-failure.yml'}
OUT=ROOT/'.local/pr16-dex-start-failure';PUBLIC=ROOT/'public-dex-start-failure'
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first run')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'bounded new START sources only')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'previous recording terminal')
 for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'all accepted source retained '+path)
def reconstruct():
 prior.OUT=OUT/'old';prior.OUT.mkdir();_,battle,accepted,_,_=prior.reconstruct();payload,linked=f.link(OUT/'new');after,placed=f.apply(battle,accepted,payload,linked);path=OUT/'candidate.gba';path.write_bytes(after);return path,accepted,after,linked,placed
def generate():
 source=(ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text();need(source.count('int main(int argc,char**argv)')==1,'one old main');return(source.replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')+'\n'+(ROOT/HEADER).read_text()).encode()
def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh START run');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_start_failure.py','-v'],cwd=ROOT,capture_output=True);need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==3,'three focused host suites');(PUBLIC/'host-tests.txt').write_bytes(unit.stderr)
  candidate,before,after,linked,placed=reconstruct();need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3','fixed mGBA package');need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
  entries=prior.f.b.lifecycle.checkpoint()['link']['exports'];header=OUT/'entries.h';header.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in entries.items()));source=OUT/'native.c';source.write_bytes(generate());exe=OUT/'native'
  cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(header)+'"',str(source),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)];r=subprocess.run(cmd,capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict gate build '+r.stderr[-1200:]);write(PUBLIC/'native-attempt.json',dict(status='ATTEMPT_STARTED_NOT_ACCEPTED',native_processes=1))
  r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300);need(r.returncode==0 and not r.stderr,'gate rc='+str(r.returncode)+' '+r.stdout[-300:]+' '+r.stderr[-1000:]);rows=[json.loads(v)for v in r.stdout.splitlines()];native=rows[-1];need(rows[:-1]==[dict(case=i)for i in range(1,1121)]and native['cases']==1120 and native['status']=='PASS_START_ONLY_VALID_FAILURE_GATE','all1120 cases');need(candidate.read_bytes()==after,'candidate unchanged');write(PUBLIC/'native.json',native)
  write(PUBLIC/'measurement.json',dict(status='PASS_START_ONLY_VALID_FAILURE_GATE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_candidate=identity(before),link=linked,placement=placed,native=native,host_suites=3,old_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,all_save_modes_accepted=False,all_consumers_wired=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists())));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in {'measurement.json','native.json','native-attempt.json','failure.json','host-tests.txt'},'exact regular text only');r=p.read_bytes();need(0<len(r)<200000 and r.endswith(b'\n')and b'\0'not in r,'bounded complete UTF8');r.decode('utf8')
  if p.suffix=='.json':json.loads(r)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed command');globals()[sys.argv[1]]()
