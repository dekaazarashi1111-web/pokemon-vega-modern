#!/usr/bin/env python3
"""候補限定load/newgame境界の新規検証。通常Saveの受入にはしない。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_lifecycle as lifecycle
s=lifecycle.scheduler;p=s.placement;need,identity=s.need,s.identity
BASE='d2dfe7a3402c5f87e6c3afdb6d2e711fcef8cc0c'
CODE={*lifecycle.SOURCES,'scripts/pr16_dex_lifecycle.py','scripts/pr16_dex_lifecycle_actions.py','tests/test_pr16_dex_lifecycle.py','tools/mgba_pr16_dex_lifecycle.c','.github/workflows/pr16-dex-lifecycle.yml',lifecycle.STATUS}
OUT=ROOT/'.local/pr16-dex-lifecycle';PUBLIC=ROOT/'public-dex-lifecycle'
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def guard():
 import pr16_story_live_probe as transport
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized branch attempt')
 pr=transport.api('pulls/16');need(pr['state']=='open'and pr['draft']and not pr['merged']and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'new lifecycle scope only')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'prior record terminal')
 for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'accepted source remains exact '+path)
def run():
 import pr16_story_live_probe as transport
 need(not OUT.exists()and not PUBLIC.exists(),'fresh lifecycle run');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_lifecycle.py','-v'],cwd=ROOT,capture_output=True)
  need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==6 and b'\nOK\n'in unit.stderr,'six lifecycle tests including50 host boundary cases');(PUBLIC/'host-tests.txt').write_bytes(unit.stderr)
  # 固定scheduler候補を再構成。既受入の隔離ARM19caseを再実行しない。
  z,_=transport.archive(transport.SAVE24)
  with z:formal=z.read('candidate.gba')
  need(identity(formal)==p.lease.CANDIDATE,'formal ROM source exact')
  payload,codec=p.link(OUT/'codec');need(codec['payload']==dict(size=5022,sha256='0541f69c476c5d4faf8fb62fcfa923395d7ba70925844d928a9594869feaeda9'),'codec reconstruction exact')
  placed,old=p.place(formal,payload,codec['symbols']);patches,scheduler=s.link(OUT/'scheduler');parent=s.apply(placed,patches,scheduler['extra_lease_size'])
  allocation=s.update_allocation(placed,parent,old['allocation'],scheduler['extra_lease_size'])
  need(identity(parent)==lifecycle.checkpoint()['candidate']and allocation==lifecycle.checkpoint()['allocation'],'accepted scheduler bytes and allocation reconstructed exactly')
  payload,linked=lifecycle.link(OUT/'lifecycle');after,applied=lifecycle.apply(parent,payload,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after)
  package=subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip();need(package=='0.10.2+dfsg-1.1build3','fixed mGBA package')
  need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA binary')
  header=OUT/'native-entries.h';header.write_text(lifecycle.abi_header()+''.join('#define '+n+' '+hex(a)+'\n'for n,a in linked['exports'].items()))
  exe=OUT/'native';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-DDEX_LIFECYCLE_ENTRIES="'+str(header)+'"',str(ROOT/'tools/mgba_pr16_dex_lifecycle.c'),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  built=subprocess.run(cmd,capture_output=True,text=True);need(built.returncode==0 and not built.stdout and not built.stderr,'strict native build: '+built.stderr[-2000:])
  write(PUBLIC/'native-attempt.json',dict(native_processes=1,status='ATTEMPT_STARTED_NOT_ACCEPTED'))
  tested=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300)
  need(tested.returncode==0 and not tested.stderr,'native rc='+str(tested.returncode)+' '+tested.stdout[-500:]+' '+tested.stderr[-1000:])
  rows=[json.loads(x)for x in tested.stdout.splitlines()];native=rows[-1];need(rows[:-1]==[dict(case=i)for i in range(1,53)]and native['status']=='PASS_ISOLATED_ARM_LOAD_NEWGAME_BOUNDARIES'and native['cases']==52,'all52 new isolated cases')
  need(candidate.read_bytes()==after,'private candidate unchanged');write(PUBLIC/'native.json',native)
  write(PUBLIC/'build.json',dict(status='PASS_ISOLATED_LOAD_NEWGAME_BOUNDARY_CANDIDATE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_candidate=identity(parent),formal_candidate=identity(formal),link=linked,placement=applied,generator_tests=6,host_load_cases=50,native=native,old_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,ordinary_save_continue_accepted=False,all_consumers_wired=False,all_save_modes_accepted=False,source_bindings={path:identity((ROOT/path).read_bytes())for path in sorted(CODE)}))
 except Exception as e:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists()),formal_rom_changed=False,formal_save_changed=False));raise
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and path.name in {'host-tests.txt','build.json','native.json','native-attempt.json','failure.json'},'explicit regular text only')
  raw=path.read_bytes();need(0<len(raw)<150000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete text');raw.decode('utf-8')
  if path.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'bounded action');globals()[sys.argv[1]]()
