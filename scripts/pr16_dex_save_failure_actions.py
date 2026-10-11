#!/usr/bin/env python3
"""保存失敗2gateとauthorityなし全writerの新規隔離測定。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_save_failure as f
import pr16_dex_battle_actions as prior
parent=prior.parent;need,identity,write=prior.need,prior.identity,prior.write
BASE='00566a7ea4c05b32ae2b323f34858711e8dac14a'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_save_failure.py','scripts/pr16_dex_save_failure_actions.py','tests/test_pr16_dex_save_failure.py','tools/mgba_pr16_dex_save_failure.c','.github/workflows/pr16-dex-save-failure.yml'}
OUT=ROOT/'.local/pr16-dex-save-failure';PUBLIC=ROOT/'public-dex-save-failure'
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current first attempt')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'bounded save failure source only')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[dict(run_id=37234348310,tested_head='51506e34ea552cd55a52ac311b92f47218f008fd',status='in_progress')],'only preceding record pending')
 r=t.api('actions/runs/37234348310');j=t.api('actions/jobs/111530381334');need(r['status']=='completed'and r['conclusion']=='success'and j['run_id']==37234348310 and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'preceding record actually terminal12success')
 z,_=t.archive((11315196473,37234348310,18170,'e4b4a476af39b2ba319017092b3db5c660112b4166780bd9b9b57888ca5f5129'))
 with z:need(z.read('battle-record.json')==(ROOT/f.CP).read_bytes(),'whole record artifact and committed CP exact')
 for path,binding in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'all prior source bindings retained '+path)
def reconstruct():
 parent.OUT=OUT/'parent';parent.OUT.mkdir();base_path=parent.reconstruct();before=base_path.read_bytes()
 payload,linked=f.b.link(OUT/'battle');before,placed=f.b.apply(before,payload,linked);cp=f.checkpoint();need(identity(before)==cp['candidate']and linked==cp['measurement']['link']and placed==cp['measurement']['placement'],'accepted battle source/bytes/allocation reconstructed without native rerun')
 payload,linked=f.link(OUT/'failure');after,placed=f.apply(before,payload,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after)
 return candidate,before,after,linked,placed

def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh failure-only attempt');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_save_failure.py','-v'],cwd=ROOT,capture_output=True)
  need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==4,'four new boundary host suites');(PUBLIC/'host-tests.txt').write_bytes(unit.stderr)
  candidate,before,after,linked,placed=reconstruct()
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3','fixed mGBA package');need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA library')
  entries=f.b.lifecycle.checkpoint()['link']['exports'];header=OUT/'native.h';header.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in entries.items()))
  exe=OUT/'native';args=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(header)+'"',str(ROOT/'tools/mgba_pr16_dex_save_failure.c'),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  compiled=subprocess.run(args,capture_output=True,text=True);need(compiled.returncode==0 and not compiled.stdout and not compiled.stderr,'strict negative native build: '+compiled.stderr[-2000:])
  write(PUBLIC/'native-attempt.json',dict(status='ATTEMPT_STARTED_NOT_ACCEPTED',native_processes=1))
  tested=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300);need(tested.returncode==0 and not tested.stderr,'native rc='+str(tested.returncode)+' '+tested.stdout[-400:]+' '+tested.stderr[-1000:])
  rows=[json.loads(x)for x in tested.stdout.splitlines()];native=rows[-1];need(rows[:-1]==[dict(case=i)for i in range(1,153)]and native['cases']==152 and native['status']=='PASS_ISOLATED_SAVE_FAILURE_GATES_AND_AUTHORITYLESS_WRITERS','all152 new cases')
  need(candidate.read_bytes()==after,'private candidate unchanged');write(PUBLIC/'native.json',native)
  write(PUBLIC/'build.json',dict(status='PASS_CANDIDATE_SAVE_FAILURE_GATES_ISOLATED',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_candidate=identity(before),link=linked,placement=placed,host_suites=4,native=native,old_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,real_save_failure_ui_accepted=False,all_consumers_wired=False,all_save_modes_accepted=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists()),formal_rom_changed=False,formal_save_changed=False));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'host-tests.txt','build.json','native.json','native-attempt.json','failure.json'},'explicit regular text only');r=p.read_bytes();need(0<len(r)<200000 and r.endswith(b'\n')and b'\0'not in r,'bounded complete UTF8');r.decode('utf-8')
  if p.suffix=='.json':json.loads(r)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'bounded action');globals()[sys.argv[1]]()
