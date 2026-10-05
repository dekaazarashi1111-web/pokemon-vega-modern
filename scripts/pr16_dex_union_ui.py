#!/usr/bin/env python3
"""Union Chatの21byte限定入口から真の表示・音・field帰還・独立coldを確認。"""
from __future__ import annotations
import json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_union_failure as f
need,identity=f.need,f.identity
BASE='168d827d6004fa5df75883273427cfc43c62275b';RUN=37247511968;JOB=111568210062;ARCHIVE=(11319413359,RUN,54317,'f6ec079006433fc2ffccd0b3b36c7287ff493a847600dbd5785d5a2a65ff7fd7')
HEADER='tools/mgba_pr16_dex_union_ui.h';BINDINGS='content/modernization/pr16_dex_union_ui_bindings.json'
OLDWF='.github/workflows/pr16-dex-union-failure.yml';WF='.github/workflows/pr16-dex-union-ui.yml'
CODE={HEADER,BINDINGS,'scripts/pr16_dex_union_ui.py','tests/test_pr16_dex_union_ui.py',OLDWF,WF}
OUT=ROOT/'.local/pr16-dex-union-ui';PUBLIC=ROOT/'public-dex-union-ui'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def validate_header(source):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
 for bad in ('rawWrite','writeRegister','si_call(','si_restore(','si_open(','loadState(','loadTemporarySave('):need(bad not in s,'no register/general fixture '+bad)
 need(s.count('uu_write8(c,addresses[i],values[i]);')==1 and s.count('uu_fixture(c,0);')==1 and s.count('uu_fixture(c,1);')==1,'two exact closed fixture callsites')
 need('addresses[count]=sb+0x14+i'in s and 'read16(c,sb)==53&&read16(c,sb+2)==13'in s,'eight-byte current-field dynamic return metadata only')
 need('addresses[count]=uu_task+4+i'in s and 'values[count++]=i==0?9:i==2?6:0'in s,'only four Union state bytes')
 need(s.count('cpu->memory.store8=uu_store8;')==1 and 'uu_target=131071'in s and 'FLASH_COMMAND_PROGRAM'in s and 'at==uu_target'in s and 'v^1u'in s,'one data-only Flash fault')
 need('c->frameCounter(c)==frame'in s and 'c->step(c);'in s and 'cpu->gprs['in s and not re.search(r'cpu->gprs\[[^\]]+\]\s*=(?!=)',s),'CPU register read only observation')
 main=s.split('int main(int argc,char**argv)',1)[1];need(main.index('si_guard(c);')<main.index('st_keys(c,'),'barriers before first game frame');return identity(s.encode())
def generate(candidate):
 import pr16_dex_gameplay as game
 s=(ROOT/HEADER).read_text();validate_header(s);old=game.CANDIDATE
 try:game.CANDIDATE=candidate;source=game.generate().decode()
 finally:game.CANDIDATE=old
 need(source.count('int main(int argc,char**argv){')==1,'one key-only parent main');return(source.replace('int main(int argc,char**argv){','int accepted_story_main_not_called(int argc,char**argv){')+'\n'+s).encode()
def guard():
 import pr16_story_live_probe as t
 import pr16_dex_union_failure_actions as prior
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first UI run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only new UI source and completed prior trigger')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==BASE and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'isolated all10 terminal')
 for path in prior.CODE-{OLDWF}:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'accepted isolation retained '+path)
 old=subprocess.check_output(['git','show',BASE+':'+OLDWF],cwd=ROOT);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+OLDWF+']\n').encode();need(old.count(trigger)==1 and(ROOT/OLDWF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'completed isolated manual only')
def validate_trace(raw,folder,candidate,mode):
 import pr16_dex_start_fault_ui as ui
 rows=[json.loads(x)for x in raw.splitlines()];need(rows[0]==dict(begin='UNION_CHAT_UI_ONLY_FIXTURE',candidate_sha256=candidate['sha256'],mode=mode,host_write_barriers=7,register_writes=0,allowed_fixture_bytes=21),'closed fixture begin')
 end=rows[-1];need(end['end']=='PASS_UNION_CHAT_UI_FAILURE_SUCCESS_AND_FIELD_RETURN'and end['mode']==mode and end['fixture_phases']==2 and end['fixture_bytes_written']==21 and end['register_writes']==0 and end['host_write_barriers']==7 and end['counter']==(101 if mode==1 else 102)and end['attempt']==(255 if mode else 1),'complete actual UI result')
 need(end['result_printers']==1 and end['save_sounds']==int(mode==0)and end['clear_calls']==1,'one truthful result and appropriate audio/clear')
 need(not any(end[k]for k in('old_save_failed_entered','natural_chat_entry_accepted','link_transaction_accepted','formal_save_changed')),'no scope promotion')
 if mode:need(0<end['fault_writes']<=16 and end['extension_bytes_preserved_after_fault']==20248 and(end['fault_physical_address']<14*4096 if mode==1 else end['fault_physical_address']==131071),'real physical failure')
 else:need(end['fault_writes']==end['extension_bytes_preserved_after_fault']==0,'healthy counterpart')
 frame=inputs=screen=0;pending=False;stages=[];fixtures=[];setups=[];printers=[];returns=[];last_input=None
 for r in rows[1:-1]:
  if 'input'in r:need(not pending and r['input']==inputs and r['frame']==frame and r['key']in(0,1,2,8,16,32,64,128)and 0<r['frames']<=600,'ordered inputs');last_input=r;frame+=r['frames'];inputs+=1
  elif 'union_stage'in r:need(not pending and r['frame']==frame,'same-frame stage');stages.append(r);pending=True
  elif 'screen'in r:need(pending and r['frame']==frame and r['screen']==screen,'exact stage screen');pending=False;screen+=1
  elif 'dynamic_return_fixture'in r:need(not pending and r['frame']==frame and r['size']==8 and r['current_map']==[3,24]and r['current_xy']==[53,13]and r['source_unset']and not r['natural_link_entry_accepted']and 0x02000014<=r['address']<0x02040000-8,'only rooted same-position dynamic return metadata');returns.append(r)
  elif 'ui_fixture'in r:need(not pending and r['ui_fixture']==len(fixtures)and r['frame']==frame and r['all_other_ewram_unchanged']and r['all_other_iwram_unchanged'],'full nonfixture RAM unchanged');fixtures.append(r)
  elif 'native_ui_setup'in r:need(not pending and r['frame']==frame and(r['chat_size'],r['display_size'],r['sprite_size'],r['windows'])==(440,8552,24,4)and r['all_heap_extents_valid']and not r['natural_link_transition_accepted'],'real native owner setup');setups.append(r)
  elif 'result_printer'in r:
   need(not pending and last_input and last_input['frames']==1 and r['frame']==last_input['frame']==frame-1 and 0<r['size']<=128 and 0<=r['window']<32,'instruction observation inside exact ordinary frame')
   if mode:need({k:r[k]for k in('address','size','sha256')}=={k:f.proof()['error_text'][k]for k in('address','size','sha256')},'whole actual error printer argument')
   printers.append(r)
  else:raise ValueError('unknown UI trace row')
 need(not pending and screen==end['screens']==4 and frame==end['frames']and inputs==end['inputs']and len(setups)==len(printers)==len(returns)==1 and[f['bytes_written']for f in fixtures]==[17,4],'whole trace complete')
 need([r['union_stage']for r in stages]==['before_ui_fixture','native_chat_initialized','failure_waiting'if mode else'success_rendered','returned_to_field'],'all observed screen stages')
 need(stages[2]['callback']==0x08128F05 and stages[2]['routine']==9 and stages[2]['state']==(9 if mode else 11) and stages[-1]['callback']==0x08055E75 and stages[-1]['routine']==0 and stages[-1]['state']==0,'actual result and stable original field')
 return dict(end=end,stages=stages,fixtures=fixtures,setups=setups,printers=printers,return_metadata=returns,screens=ui.screens(rows,folder))
def run():
 import pr16_story_live_probe as t
 import pr16_dex_union_failure_actions as prior
 import pr16_dex_start_fault_ui as cold
 import pr16_dex_gameplay as game
 import pr16_dex_mystery_ui as mg
 need(not OUT.exists()and not PUBLIC.exists(),'fresh UI run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_union_ui.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==3,'three new UI confinement tests');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  z,_=t.archive(ARCHIVE)
  with z:isolated=json.loads(z.read('measurement.json'))
  prior.OUT=OUT/'build';prior.OUT.mkdir();candidate,before,after,linked,placed=prior.reconstruct();ci=identity(after)
  need({k:isolated[k]for k in('candidate','parent_candidate','link','placement')}==dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed),'exact unchanged isolated candidate reconstructed')
  for w in json.loads((ROOT/BINDINGS).read_bytes())['windows']:
   at=w['address']-0x08000000;need(identity(after[at:at+w['size']])==dict(size=w['size'],sha256=w['sha256']),'signed UI entry '+w['id'])
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
  old=game.CANDIDATE
  try:game.CANDIDATE=ci;coldsource=game.generate()
  finally:game.CANDIDATE=old
  exes={}
  for name,source in [('ui',generate(ci)),('mystery',mg.generate(ci)),('cold',coldsource)]:
   src=OUT/(name+'.c');src.write_bytes(source);exe=OUT/name;r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict '+name+' compile '+r.stderr[-1800:]);exes[name]=exe
  z,_=t.archive(t.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==t.SEED,'original Save101');expected=game.record(game.physical(seed,101)['legacy']);cases=[]
  for mode,name in [(1,'main-fault'),(2,'outer-fault'),(0,'healthy')]:
   folder=OUT/name;folder.mkdir();public=PUBLIC/name;public.mkdir();copy=folder/'copy.srm';copy.write_bytes(seed);captured=folder/'captured.srm';attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
   with(public/'stdout.txt').open('wb')as out,(public/'stderr.txt').open('wb')as err:r=subprocess.run([str(exes['ui']),str(candidate),str(copy),str(captured),str(mode)],cwd=public,stdout=out,stderr=err,timeout=300)
   need(r.returncode==0 and not(public/'stderr.txt').read_bytes(),name+' rc='+str(r.returncode)+' '+(public/'stderr.txt').read_text()[-1800:]);trace=validate_trace((public/'stdout.txt').read_bytes(),public,ci,mode);data=captured.read_bytes();need(len(data)==131088 and data[131072:]==seed[131072:]and copy.read_bytes()==data,'complete private save/RTC identity')
   counter=101 if mode==1 else 102;p=game.physical(data,counter);need(p['party']==game.physical(seed,101)['party']and p['mdx']==(bytes(522)if mode==1 else expected),'exact old or new generation payload')
   cf=OUT/(name+'-cold');cf.mkdir();cp=PUBLIC/(name+'-cold');cp.mkdir();cold.OUT=cf;cold.PUBLIC=cp;attempts.append(name+'-cold');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));continued=cold.cold(exes['cold'],candidate,data,counter,expected,0 if mode==1 else 1)
   cases.append(dict(name=name,mode=mode,trace=trace,save=identity(data),cold=continued))
  regression_cases=[]
  for mode,name0 in [(1,'main-fault'),(2,'outer-fault'),(0,'healthy')]:
   name='mystery-'+name0;folder=OUT/name;folder.mkdir();public=PUBLIC/name;public.mkdir();copy=folder/'copy.srm';copy.write_bytes(seed);captured=folder/'captured.srm';attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
   with(public/'stdout.txt').open('wb')as out,(public/'stderr.txt').open('wb')as err:r=subprocess.run([str(exes['mystery']),str(candidate),str(copy),str(captured),str(mode)],cwd=public,stdout=out,stderr=err,timeout=300)
   need(r.returncode==0 and not(public/'stderr.txt').read_bytes(),name+' rc='+str(r.returncode)+' '+(public/'stderr.txt').read_text()[-1800:]);trace=mg.validate_trace((public/'stdout.txt').read_bytes(),public,ci,mode);data=captured.read_bytes();need(len(data)==131088 and data[131072:]==seed[131072:]and copy.read_bytes()==data,'relocated MG complete private save')
   counter=101 if mode==1 else 102;p=game.physical(data,counter);need(p['party']==game.physical(seed,101)['party']and p['mdx']==(bytes(522)if mode==1 else expected),'relocated MG generation/MDX')
   cf=OUT/(name+'-cold');cf.mkdir();cp=PUBLIC/(name+'-cold');cp.mkdir();cold.OUT=cf;cold.PUBLIC=cp;attempts.append(name+'-cold');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));continued=cold.cold(exes['cold'],candidate,data,counter,expected,0 if mode==1 else 1)
   regression_cases.append(dict(name=name,mode=mode,trace=trace,save=identity(data),cold=continued))
  need(candidate.read_bytes()==after,'candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_UNION_CHAT_UI_ONLY_FAILURE_SUCCESS_AND_COLD',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,isolated_run=RUN,isolated_candidate=isolated['candidate'],cases=cases,relocated_mystery_cases=regression_cases,native_processes=len(attempts),host_tests=3,ram_fixture_bytes_per_ui_process=21,register_writes=0,mystery_fixture_bytes_per_process=11,natural_entry_accepted=False,all_nonstart_notifications_accepted=False,link_transaction_accepted=False,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated publication')
 dirs={'main-fault','outer-fault','healthy','main-fault-cold','outer-fault-cold','healthy-cold','main-fault-cold/cold-101','outer-fault-cold/cold-102','healthy-cold/cold-102'}
 dirs|={'mystery-'+d for d in list(dirs)}
 for p in PUBLIC.rglob('*'):
  rel=p.relative_to(PUBLIC);need(not p.is_symlink()and not any(x.startswith('.')for x in rel.parts),'no hidden/symlink')
  if p.is_dir():need(str(rel)in dirs,'known directory');continue
  need(p.is_file(),'regular only')
  if len(rel.parts)==1:need(p.name in{'host-tests.txt','measurement.json','failure.json','attempts.json'},'closed root text')
  else:need(str(rel.parent)in dirs and(p.name in{'stdout.txt','stderr.txt'}or re.fullmatch(r'screen-000[0-3]\.ppm',p.name)),'closed text/screens')
  b=p.read_bytes()
  if p.suffix=='.ppm':need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'complete screenshot');continue
  need(len(b)<2000000 and b'\0'not in b and(not b or b.endswith(b'\n')),'complete bounded UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed UI action');globals()[sys.argv[1]]()
