#!/usr/bin/env python3
"""Bounded save scheduler candidate build. No gameplay or formal save changes."""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_scheduler as scheduler
import pr16_dex_placement as placement
need,identity=scheduler.need,scheduler.identity
BASE='a4463621e8f8374f74c85d90056cc64e17720d6d'
CODE={'scripts/pr16_dex_scheduler.py','scripts/pr16_dex_scheduler_actions.py',
 'overlays/dex_owner/dex_stage61_scheduler.h','tests/test_pr16_dex_scheduler.py',
 '.github/workflows/pr16-dex-scheduler.yml','scripts/pr16_dex_scheduler_host.py','tools/pr16_dex_scheduler_host.c','tools/mgba_pr16_dex_scheduler.c'}
OUT=ROOT/'.local/pr16-dex-scheduler';PUBLIC=ROOT/'public-dex-scheduler'
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def guard():
 import pr16_story_live_probe as transport
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized branch and attempt')
 p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'current draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only scheduler implementation scope')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'previous runs terminal')
 for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'accepted source unchanged '+path)
def run():
 import pr16_story_live_probe as transport
 need(not OUT.exists()and not PUBLIC.exists(),'fresh isolated build');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_scheduler.py','-v'],cwd=ROOT,capture_output=True)
  need(test.returncode==0 and not test.stdout and b'\nOK\n'in test.stderr,'new scheduler generator tests');(PUBLIC/'host-tests.txt').write_bytes(test.stderr)
  host=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/pr16_dex_scheduler_host.py'),str(OUT/'host')],cwd=ROOT,capture_output=True,text=True)
  need(host.returncode==0 and not host.stderr,'synthetic host scheduler matrix: '+host.stderr[-1000:]);write(PUBLIC/'host-runtime.json',json.loads(host.stdout))
  patches,linked=scheduler.link(OUT/'scheduler')
  z,_=transport.archive(transport.SAVE24)
  with z:before=z.read('candidate.gba')
  need(identity(before)==placement.lease.CANDIDATE,'exact formal ROM source')
  payload,codec=placement.link(OUT/'codec');need(codec['payload']==dict(size=5022,sha256='0541f69c476c5d4faf8fb62fcfa923395d7ba70925844d928a9594869feaeda9'),'unchanged accepted codec reconstruction')
  placed,old=placement.place(before,payload,codec['symbols']);after=scheduler.apply(placed,patches)
  candidate=OUT/'scheduler-candidate.gba';candidate.write_bytes(after)
  package=subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()
  need(package=='0.10.2+dfsg-1.1build3','fixed mGBA package')
  need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA binary')
  header=OUT/'scheduler-entries.h';header.write_text(''.join('#define '+name+' '+hex(address)+'u\n'for name,address in linked['exports'].items()))
  exe=OUT/'native-scheduler';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(header)+'"',str(ROOT/'tools/mgba_pr16_dex_scheduler.c'),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  built=subprocess.run(cmd,capture_output=True,text=True);need(built.returncode==0 and not built.stdout and not built.stderr,'strict scheduler native compile: '+built.stderr[-2000:])
  write(PUBLIC/'native-attempt.json',dict(native_processes=1,status='ATTEMPT_STARTED_NOT_ACCEPTED'))
  tested=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=480)
  need(tested.returncode==0 and not tested.stderr,'scheduler native rc='+str(tested.returncode)+' progress='+tested.stdout[-1000:]+' '+tested.stderr[-1000:])
  rows=[json.loads(x)for x in tested.stdout.splitlines()];native=rows[-1]
  need(rows[:-1]==[dict(case=i)for i in range(1,20)]and native['cases']==19 and native['status']=='PASS_ISOLATED_ARM_SCHEDULER_SYNTHETIC_FLASH','all19 native scheduler cases')
  need(candidate.read_bytes()==after,'private candidate unchanged by harness');write(PUBLIC/'native.json',native)
  write(PUBLIC/'build.json',dict(status='PASS_ISOLATED_SAVE_SCHEDULER_CANDIDATE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),link=linked,candidate=identity(after),formal_candidate=identity(before),codec_native_reruns=0,native_processes=1,native=native,formal_rom_changed=False,formal_save_changed=False,gameplay_accepted=False,remaining=['outer sector31 load ordering','newgame init','save mode fault matrix','all consumers'],source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:
  diagnostic=OUT/'scheduler/link-diagnostic.json'
  if diagnostic.exists():(PUBLIC/'link-diagnostic.json').write_bytes(diagnostic.read_bytes())
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists()),formal_rom_changed=False,formal_save_changed=False));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in {'host-tests.txt','build.json','failure.json','link-diagnostic.json','host-runtime.json','native.json','native-attempt.json'},'explicit regular text file')
  raw=p.read_bytes();need(0<len(raw)<100000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete text');raw.decode('utf-8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'bounded action');globals()[sys.argv[1]]()
