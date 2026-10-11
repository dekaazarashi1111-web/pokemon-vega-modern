#!/usr/bin/env python3
"""候補限定battle seen/公式count。既受入nativeは再走しない。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_battle_consumers as b
import pr16_dex_gameplay_actions as parent
need,identity,write=parent.need,parent.identity,parent.write
BASE='35d77de29f7d28e89d6445fefc99c81b8707ce01'
CODE={*b.SOURCES,b.BINDINGS,'scripts/pr16_dex_battle_consumers.py','scripts/pr16_dex_battle_actions.py','tests/test_pr16_dex_battle_consumers.py','tools/mgba_pr16_dex_battle_consumers.c','.github/workflows/pr16-dex-battle-consumers.yml'}
OUT=ROOT/'.local/pr16-dex-battle';PUBLIC=ROOT/'public-dex-battle'
def guard():
 import pr16_story_live_probe as transport
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized branch and first attempt')
 pr=transport.api('pulls/16');need(pr['state']=='open'and pr['draft']and not pr['merged']and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only signed consumer slice sources')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'previous recording terminal')
 for path,binding in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'previous accepted source retained '+path)
def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh consumer attempt');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_battle_consumers.py','-v'],cwd=ROOT,capture_output=True)
  need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==6 and b'\nOK\n'in unit.stderr,'six new host suites with full1670 namespace sweep');(PUBLIC/'host-tests.txt').write_bytes(unit.stderr)
  # unchanged parent source reconstruction; its accepted native tests are not run.
  parent.OUT=OUT/'parent';parent.OUT.mkdir();before_path=parent.reconstruct();before=before_path.read_bytes()
  payload,linked=b.link(OUT/'consumer');after,placed=b.apply(before,payload,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after)
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3','fixed mGBA package')
  need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA library')
  namespace=json.loads((ROOT/'content/modernization/pr16_dex_namespace.json').read_bytes());owners={row['species_id']:row['owner']for row in namespace['species']};owners[1670]=925
  samples=[0,1,129,481,253,255,649,650,1620,1669,1670,1671,65535]
  header=OUT/'native-entries.h';header.write_text(b.lifecycle.abi_header()+'#define DEX_SAMPLE_OWNERS {'+','.join(str(owners.get(sid,0))for sid in samples)+'}\n')
  exe=OUT/'native';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-DDEX_CONSUMER_NATIVE="'+str(header)+'"',str(ROOT/'tools/mgba_pr16_dex_battle_consumers.c'),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  compiled=subprocess.run(cmd,capture_output=True,text=True);need(compiled.returncode==0 and not compiled.stdout and not compiled.stderr,'strict new native build: '+compiled.stderr[-2000:])
  write(PUBLIC/'native-attempt.json',dict(status='ATTEMPT_STARTED_NOT_ACCEPTED',native_processes=1))
  result=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300)
  need(result.returncode==0 and not result.stderr,'native rc='+str(result.returncode)+' '+result.stdout[-500:]+' '+result.stderr[-1000:])
  rows=[json.loads(x)for x in result.stdout.splitlines()];native=rows[-1];need(rows[:-1]==[dict(case=i)for i in range(1,181)]and native['status']=='PASS_ISOLATED_ARM_BATTLE_SEEN_AND_OFFICIAL_COUNT'and native['cases']==180,'all180 consumer ARM cases')
  need(candidate.read_bytes()==after and before_path.read_bytes()==before,'candidate and parent unchanged');write(PUBLIC/'native.json',native)
  write(PUBLIC/'build.json',dict(status='PASS_BATTLE_SEEN_AND_OFFICIAL_COUNT_CANDIDATE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_candidate=identity(before),link=linked,placement=placed,host_suites=6,host_raw_species_cases=1670,native=native,old_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,ordinary_battle_accepted=False,all_consumers_wired=False,all_save_modes_accepted=False,source_bindings={path:identity((ROOT/path).read_bytes())for path in sorted(CODE)}))
 except Exception as e:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists()),formal_rom_changed=False,formal_save_changed=False));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and path.name in{'host-tests.txt','build.json','native.json','native-attempt.json','failure.json'},'exact regular text files only')
  raw=path.read_bytes();need(0<len(raw)<200000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete UTF8');raw.decode('utf-8')
  if path.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'bounded action');globals()[sys.argv[1]]()
