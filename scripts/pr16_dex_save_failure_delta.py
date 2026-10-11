#!/usr/bin/env python3
"""ROM不変。152原本を再走せず、新しい60個の不足oracleのみ追加。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_save_failure_actions as isolated
import pr16_dex_save_failure_ui as ui
need,identity,write=isolated.need,isolated.identity,isolated.write
BASE='4d55bf6856448eaebfec3bae93150f0bc8433c17'
HEADER='tools/mgba_pr16_dex_save_failure_delta.h'
CODE={HEADER,'scripts/pr16_dex_save_failure_delta.py','.github/workflows/pr16-dex-save-failure-delta.yml',isolated.f.SOURCE,isolated.f.BINDINGS,'tests/test_pr16_dex_save_failure.py','.github/workflows/pr16-dex-save-failure.yml'}
OUT=ROOT/'.local/pr16-dex-save-failure-delta';PUBLIC=ROOT/'public-dex-save-failure-delta'
def generate():
 source=(ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text()
 for old,new in [('static uint8_t all_flash_before','static unsigned sf_expected_dispatch;\nstatic uint8_t all_flash_before'),('need(dispatch<=1,"original wipe dispatch at most once")','need(dispatch==sf_expected_dispatch,"exact expected original wipe dispatch count")'),('pc==0x080DB368||pc==0x080DB384','pc==0x080DB368||pc==0x080DB384||pc==0x080DB36E'),('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')]:need(source.count(old)==1,'one bounded delta source transform');source=source.replace(old,new)
 return(source+'\n'+(ROOT/HEADER).read_text()).encode()
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first delta attempt')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'delta observer scope only')
 for path in (isolated.CODE|ui.CODE)-CODE:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'isolated and UI sources unchanged')
def run():
 import pr16_story_live_probe as t
 need(not OUT.exists()and not PUBLIC.exists(),'fresh delta');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_save_failure.py','-v'],cwd=ROOT,capture_output=True);need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==4,'four affected boundary suites');(PUBLIC/'host-tests.txt').write_bytes(unit.stderr)
  package=subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip();library=identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes());need(package=='0.10.2+dfsg-1.1build3'and library==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'same verified runtime')
  z,_=t.archive(ui.MEASURE)
  with z:proof=json.loads(z.read('build.json'))
  isolated.OUT=OUT;candidate,before,after,linked,placed=isolated.reconstruct();need(identity(before)==proof['parent_candidate']and proof['link']['payload']['size']==104,'same battle parent; change only new failure gates')
  header=OUT/'native.h';header.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in isolated.f.b.lifecycle.checkpoint()['link']['exports'].items()))
  source=OUT/'delta.c';source.write_bytes(generate());exe=OUT/'delta';args=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(header)+'"',str(source),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  compiled=subprocess.run(args,capture_output=True,text=True);need(compiled.returncode==0 and not compiled.stdout and not compiled.stderr,'strict delta compile: '+compiled.stderr[-1500:]);write(PUBLIC/'native-attempt.json',dict(status='ATTEMPT_STARTED_NOT_ACCEPTED',native_processes=1))
  r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300);need(r.returncode==0 and not r.stderr,'delta rc='+str(r.returncode)+' '+r.stdout[-400:]+' '+r.stderr[-1000:]);rows=[json.loads(v)for v in r.stdout.splitlines()];native=rows[-1];need(rows[:-1]==[dict(case=i)for i in range(1,109)]and native['status']=='PASS_SAVE_FAILURE_DELTA_ORACLES','new gate48 and oracle60 cases')
  need(candidate.read_bytes()==after,'candidate unchanged');write(PUBLIC/'native.json',native);write(PUBLIC/'measurement.json',dict(status='PASS_ADDITIONAL_SAVE_FAILURE_ORACLES',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),runtime=dict(package=package,library=library),candidate=identity(after),parent_candidate=identity(before),link=linked,placement=placed,native=native,isolated_parent_run=ui.MEASURE[1],old_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists())));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public delta directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'host-tests.txt','measurement.json','native.json','native-attempt.json','failure.json'},'exact regular JSON only');r=p.read_bytes();need(0<len(r)<100000 and r.endswith(b'\n')and b'\0'not in r,'bounded UTF8');r.decode('utf8')
  if p.suffix=='.json':json.loads(r)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed action');globals()[sys.argv[1]]()
