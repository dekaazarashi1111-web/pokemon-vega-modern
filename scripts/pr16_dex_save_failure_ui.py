#!/usr/bin/env python3
"""CRC1byte negative fixtureによる実保存失敗UI。正式入力は不変。"""
from __future__ import annotations
import json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_save_failure_actions as isolated
import pr16_dex_gameplay as game
need,identity,write=isolated.need,isolated.identity,isolated.write
BASE='2ea7577c8d4d02e88e91253dab9855bbc8d3eb3c'
MEASURE=(11315426394,37234821383,17512,'3f5dda8b3f7b70f1de4361ecb52efe55ce90018281e212ae19b1fbe3f508927d')
HEADER='tools/mgba_pr16_dex_save_failure_ui.h'
CODE={HEADER,'scripts/pr16_dex_save_failure_ui.py','tests/test_pr16_dex_save_failure_ui.py','.github/workflows/pr16-dex-save-failure-ui.yml'}
OUT=ROOT/'.local/pr16-dex-save-failure-ui';PUBLIC=ROOT/'public-dex-save-failure-ui'
def validate_header(source):
 stripped=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
 need(stripped.count('sf_fixture_write8(c,')==1 and stripped.count('sf_fixture_write8=c->busWrite8;')==1,'one declared saved write pointer and one byte exception')
 for bad in ('si_restore(','si_open(','si_call(','si_transaction(','write_register(','busWrite16(','busWrite32(','rawWrite8(','rawWrite16(','rawWrite32(','writeRegister('):need(bad not in stripped,'no extra fixture or barrier removal '+bad)
 main=stripped.split('int main(int argc,char**argv)',1)[1]
 need(main.index('si_guard(c);')<main.index('st_keys(c,'),'all seven barriers before first frame')
 need('VEGA_DEX_OWNER_RAM+4,(uint8_t)(old^1)'in stripped and 'sf_injected=1;'in stripped,'exact CRC byte only')
 return identity(source.encode())
def generate(candidate):
 source=(ROOT/HEADER).read_text();validate_header(source);old=game.CANDIDATE
 try:game.CANDIDATE=candidate;generated=game.generate().decode()
 finally:game.CANDIDATE=old
 token='int main(int argc,char**argv){';need(generated.count(token)==1,'one prior key-only main');return(generated.replace(token,'int accepted_story_main_not_called(int argc,char**argv){')+'\n'+source).encode()
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized UI attempt')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'negative UI source only')
 cp=isolated.f.checkpoint()
 for path,b in cp['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'accepted battle code retained')
 for path in isolated.CODE:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'isolated gates retained')
def validate(raw,folder):
 rows=[json.loads(x)for x in raw.splitlines()];end=rows[-1]
 need(end['end']=='PASS_EXPLICIT_CRC_FIXTURE_SAVE_FAILURE_UI'and end['fixture_calls']==1 and end['fixture_bytes']==1 and end['host_write_barriers']==7 and end['other_host_writes']==end['register_writes']==end['save_commits']==0 and end['counter']==101 and end['all_flash_unchanged']is True and end['authority_present']is True and end['story_progress_accepted']is False,'exact negative terminal')
 stages=[r for r in rows if 'failure_ui_stage'in r];need([r['failure_ui_stage']for r in stages]==['injected_at_field','save_failed_state6','ordinary_save_error','field_after_failure'],'four ordered real UI stages')
 need(stages[1]['state']==6 and stages[1]['active']!=0 and stages[1]['attempt']==255 and stages[2]['callback']==0x0806F21D and stages[2]['delay']==0 and stages[3]['active']==0 and stages[3]['state']==0,'failure and double-A ordinary recovery states')
 states=[r['save_failed_state']for r in rows if 'save_failed_state'in r];need(states==[5,6],'actual frame-state transition observed')
 fixtures=[r for r in rows if 'fixture_calls'in r and 'address'in r];need(len(fixtures)==1 and fixtures[0]['address']==0x0203DB44 and fixtures[0]['new']==fixtures[0]['old']^1,'exact one-byte CRC fixture')
 screens=[]
 for row in rows:
  if 'screen'not in row:continue
  image=(folder/('screen-'+str(row['screen']).zfill(4)+'.ppm')).read_bytes();need(len(image)==115215 and image.startswith(b'P6\n240 160\n255\n')and identity(image)['sha256']==row['sha256'],'complete original screen')
  px=image[15:];colors=len(set(px[i:i+3]for i in range(0,len(px),3)));need(colors>1,'nonblank actual renderer');screens.append(dict(**row,colors=colors))
 need(len(screens)==end['screens']==4,'all4 screens');return dict(end=end,stages=stages,fixture=fixtures[0],screens=screens)
def run():
 import pr16_story_live_probe as t
 need(not OUT.exists()and not PUBLIC.exists(),'fresh UI negative run');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_save_failure_ui.py','-v'],cwd=ROOT,capture_output=True);need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==3,'three new driver confinement suites');(PUBLIC/'host-tests.txt').write_bytes(unit.stderr)
  r=t.api('actions/runs/'+str(MEASURE[1]));need(r['head_sha']==BASE and r['status']=='completed'and r['conclusion']=='success','isolated source terminal success')
  z,_=t.archive(MEASURE)
  with z:proof=json.loads(z.read('build.json'))
  need(proof['native']['cases']==152 and proof['real_save_failure_ui_accepted']is False,'isolated only, no previous real UI')
  isolated.OUT=OUT;candidate,before,after,linked,placed=isolated.reconstruct();need(identity(after)==proof['candidate']and linked==proof['link']and placed==proof['placement'],'whole candidate matches isolated gates')
  source=OUT/'ui.c';source.write_bytes(generate(identity(after)));exe=OUT/'ui'
  cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(source),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  compiled=subprocess.run(cmd,capture_output=True,text=True);need(compiled.returncode==0 and not compiled.stdout and not compiled.stderr,'strict negative UI build: '+compiled.stderr[-2000:])
  z,_=t.archive(t.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==t.SEED,'exact unchanged formal Save101 input');save=OUT/'negative-copy.srm';save.write_bytes(seed)
  write(PUBLIC/'native-attempt.json',dict(status='ATTEMPT_STARTED_NOT_ACCEPTED',native_processes=1,fixture_bytes_authorized_for_test=1))
  with(PUBLIC/'stdout.txt').open('wb')as out,(PUBLIC/'stderr.txt').open('wb')as err:
   completed=subprocess.run([str(exe),str(candidate),str(save)],cwd=PUBLIC,stdout=out,stderr=err,timeout=300)
  need(completed.returncode==0 and not(PUBLIC/'stderr.txt').read_bytes(),'UI rc='+str(completed.returncode)+' '+(PUBLIC/'stderr.txt').read_text()[-1500:])
  trace=validate((PUBLIC/'stdout.txt').read_bytes(),PUBLIC);need(save.read_bytes()==seed,'full131088byte FlashRTC remains original after close/process exit');need(candidate.read_bytes()==after,'private candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_EXPLICIT_CRC_NEGATIVE_SAVE_FAILURE_UI',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_isolated_run=MEASURE[1],native_processes=1,save_attempts=1,save_commits=0,source_save=identity(seed),output_save=identity(save.read_bytes()),formal_save_changed=False,fixture_bytes=1,authority_present=True,authorityless_real_ui_accepted=False,all_consumers_wired=False,all_save_modes_accepted=False,trace=trace,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=int((PUBLIC/'native-attempt.json').exists()),formal_rom_changed=False,formal_save_changed=False));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public UI directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and(p.name in{'host-tests.txt','measurement.json','native-attempt.json','failure.json','stdout.txt','stderr.txt'}or re.fullmatch(r'screen-000[0-3]\.ppm',p.name)),'only explicit text/screens; never inputsave/ROM/runner')
  raw=p.read_bytes()
  if p.suffix=='.ppm':need(len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'fixed real PPM');continue
  need(len(raw)<1500000 and b'\0'not in raw and(not raw or raw.endswith(b'\n')),'bounded complete UTF8');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed action');globals()[sys.argv[1]]()
