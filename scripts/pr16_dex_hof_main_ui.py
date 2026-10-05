#!/usr/bin/env python3
"""新mode3 COWの実HOF表示/故障と独立cold。旧nativeは再走しない。"""
from __future__ import annotations
import json,os,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_main_cow_actions as prior
import pr16_dex_hof_ui as original
need,identity,write=prior.need,prior.identity,prior.write
BASE='64fb8049ef3edf71b11d17760247879ecd2812b7';RUN=37265656275;JOB=111621821031;ARCHIVE=(11326008565,RUN,52263,'136786ca226d82f28bd156577b7ae5a657cec91a17c7be7bf3ed33210dc4e18c')
HEADER='tools/mgba_pr16_dex_hof_main_ui.h';OLDWF=prior.WF;WF='.github/workflows/pr16-dex-hof-main-ui.yml';ARTIFACT='pr16-dex-hof-main-ui-text-only'
CODE={HEADER,'scripts/pr16_dex_hof_main_ui.py','tests/test_pr16_dex_hof_main_ui.py',OLDWF,WF}
OUT=ROOT/'.local/pr16-dex-hof-main-ui';PUBLIC=ROOT/'public-dex-hof-main-ui'
def validate_header(s):
 original.validate_header(s)
 for token in('hu_cow_entry==1','hu_hof_write==(hu_mode==3?1u:2u)','hu_cow_main==(hu_mode<3)','hu_target=28*4096','hu_target=29*4096','HOF28 failure preserves29','HOF failure prevents every main-sector write'):need(token in s,'closed new mode3 oracle '+token)
 return identity(s.encode())
def generate(candidate,cold=False):
 import pr16_dex_gameplay as game
 hof_link=json.loads((ROOT/'content/modernization/pr16_dex_hof_checkpoint.json').read_bytes())['isolated']['link']
 if cold:return original.generate(candidate,hof_link,True)
 s=(ROOT/HEADER).read_text();validate_header(s);old=game.CANDIDATE
 try:game.CANDIDATE=candidate;source=game.generate().decode()
 finally:game.CANDIDATE=old
 token='int main(int argc,char**argv){';need(source.count(token)==1,'one inherited main')
 return(source.replace(token,'int accepted_story_main_not_called(int argc,char**argv){')+'\n#define HOF_UI_WAIT '+hex(hof_link['exports']['VegaDexHofSaveFailureWait'])+'u\n'+s).encode()
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_main_ui.py');need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current first mode3 UI');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'only new affected UI source and retired isolated trigger')
 for path in prior.CODE-{OLDWF}:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'all accepted isolation bytes retained '+path)
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==BASE and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'isolated all10 steps complete')
 old=subprocess.check_output(['git','show',BASE+':'+OLDWF],cwd=ROOT);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+OLDWF+']\n').encode();need(old.count(trigger)==1 and(ROOT/OLDWF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'retire successful isolation without source change')
def validate_fault(end,mode):
 need(mode in(0,1,2,3,4),'only five fault modes');count=end['fault_writes'];address=end['fault_physical_address']
 if mode==0:need(count==0 and address==0xFFFFFFFF,'healthy has no fault target')
 else:
  need(1<=count<=16,'bounded actual Flash fault observed')
  if mode==1:need(0<=address<14*4096,'main fault remains inside target bank0')
  else:need(address=={2:131071,3:28*4096,4:29*4096}[mode],'exact requested auxiliary sector fault')
def validate_trace(raw,folder,candidate,mode):
 import pr16_dex_start_fault_ui as image
 rows=[json.loads(x)for x in raw.splitlines()];need(rows[0]==dict(begin='HOF_UI_ONLY_FIXTURE',candidate_sha256=candidate['sha256'],mode=mode,host_write_barriers=7,register_writes=0,allowed_fixture_bytes=9),'exact UI begin');end=rows[-1]
 need(end['end']=='PASS_HOF_UI_FAILURE_SUCCESS_AND_NO_RETRY'and end['mode']==mode and end['fixture_bytes_written']==9 and end['register_writes']==0 and end['host_write_barriers']==7 and end['native_hof_saves']==end['stock_save_calls']==end['stat10_increment_calls']==1,'one physical HOF attempt')
 need(end['stat10_after']==end['stat10_before']+1 and end['attempt']==(255 if mode else 1)and end['counter']==(102 if mode in(0,2)else 101)and end['save_sounds']==int(mode==0)and end['result_printers']==int(mode!=0),'truthful result and single initial increment')
 validate_fault(end,mode)
 need(end['cow_entry_calls']==1 and end['cow_main_calls']==end['cow_serializer_calls']==int(mode<3)and end['hof_writer_calls']==(1 if mode==3 else 2),'new main COW and exact HOF short-circuit counts')
 need(end['payload_bytes_preserved_through_ack']==8192 and end['extension_bytes_preserved']==20248 and not end['old_save_failed_entered'],'complete owners preserved')
 stages=[r for r in rows if'hof_stage'in r];fixtures=[r for r in rows if'ui_fixture'in r];payload=[r for r in rows if'hof_payload'in r]
 need([r['hof_stage']for r in stages]==['before_ui_fixture','save_returned','failure_waiting'if mode else'success_waiting','original_hof_display'],'all4 stage screens');need(len(fixtures)==len(payload)==1 and fixtures[0]['bytes_written']==9 and payload[0]['size']==8192,'complete entry and prepared payload evidence')
 frame=inputs=screen=0;pending=False
 for r in rows[1:-1]:
  if'input'in r:need(not pending and r['input']==inputs and r['frame']==frame and r['key']in(0,1,2,8,16,32,64,128)and 0<r['frames']<=600,'bounded ordered input');frame+=r['frames'];inputs+=1
  elif'hof_stage'in r:need(not pending and r['frame']==frame,'same-frame stage');pending=True
  elif'screen'in r:need(pending and r['screen']==screen and r['frame']==frame,'same-frame screenshot');pending=False;screen+=1
  elif'ui_fixture'in r:need(not pending and r['frame']==frame,'fixture between frames')
  elif'hof_payload'in r:need(not pending and frame-1<=r['frame']<=frame,'read-only prepared payload within ordinary frame')
  else:raise ValueError('unknown HOF trace row')
 need(not pending and screen==end['screens']==4 and inputs==end['inputs']and frame==end['frames'],'whole trace consumed');return dict(end=end,stages=stages,fixtures=fixtures,payload=payload,screens=image.screens(rows,folder))
def run():
 import pr16_story_live_probe as t,pr16_dex_publication as publication,pr16_dex_gameplay as game,pr16_dex_start_fault_ui as cold
 need(not OUT.exists()and not PUBLIC.exists(),'fresh affected UI');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_hof_main_ui.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==4,'four new changed UI source contracts');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),prior.ARTIFACT,RUN);z,_=t.archive(ARCHIVE)
  with z:isolated=json.loads(z.read('measurement.json'))
  prior.OUT=OUT/'build';prior.OUT.mkdir();candidate,before,after,linked,placed=prior.reconstruct();ci=identity(after);need({k:isolated[k]for k in('candidate','parent_candidate','link','placement')}==dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed),'whole accepted isolated build exact')
  for w in json.loads((ROOT/'content/modernization/pr16_dex_hof_ui_bindings.json').read_bytes())['windows']:
   at=w['address']-0x08000000;need(identity(after[at:at+w['size']])=={k:w[k]for k in('size','sha256')},'original UI callable retained '+w['id'])
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
  exes={}
  for name,is_cold in[('ui',False),('cold',True)]:
   src=OUT/(name+'.c');src.write_bytes(generate(ci,is_cold));exe=OUT/(name+'-native');r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict '+name+' compile '+r.stderr[-1800:]);exes[name]=exe
  z,_=t.archive(t.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==t.SEED,'formal Save101 original exact');seeddata=game.physical(seed,101);expected=game.record(seeddata['legacy']);initial_stat=struct.unpack_from('<I',seeddata['save1'],0x1228)[0]^struct.unpack_from('<I',seeddata['save2'],0xF20)[0];cases=[]
  for mode,name in[(3,'hof28-fault'),(4,'hof29-fault'),(1,'main-fault'),(2,'outer-fault'),(0,'healthy')]:
   folder=OUT/name;folder.mkdir();public=PUBLIC/name;public.mkdir();copy=folder/'copy.srm';copy.write_bytes(seed);captured=folder/'captured.srm';attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
   with(public/'stdout.txt').open('wb')as out,(public/'stderr.txt').open('wb')as err:r=subprocess.run([str(exes['ui']),str(candidate),str(copy),str(captured),str(mode)],cwd=public,stdout=out,stderr=err,timeout=420)
   need(r.returncode==0 and not(public/'stderr.txt').read_bytes(),name+' rc='+str(r.returncode)+' '+(public/'stderr.txt').read_text()[-1800:]);trace=validate_trace((public/'stdout.txt').read_bytes(),public,ci,mode);data=captured.read_bytes();need(len(data)==131088 and data[131072:]==seed[131072:]and copy.read_bytes()==data,'whole changed copy and original RTC')
   counter=102 if mode in(0,2)else 101;physical=game.physical(data,counter);stat=struct.unpack_from('<I',physical['save1'],0x1228)[0]^struct.unpack_from('<I',physical['save2'],0xF20)[0];need(physical['party']==seeddata['party']and physical['mdx']==(expected if counter==102 else bytes(522))and stat==initial_stat+int(counter==102),'selected whole generation party/MDX/stat')
   cf=OUT/(name+'-cold');cf.mkdir();cp=PUBLIC/(name+'-cold');cp.mkdir();cold.OUT=cf;cold.PUBLIC=cp;attempts.append(name+'-cold');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));continued=cold.cold(exes['cold'],candidate,data,counter,expected,int(counter==102));rows=[json.loads(x)for x in(cp/('cold-'+str(counter))/'stdout.txt').read_bytes().splitlines()];meta=[x for x in rows if'hof_cold_metadata'in x];need(len(meta)==1 and meta[0]['stat10']==stat and meta[0]['ledger_sha256']==continued['observation']['ledger_sha256']==identity(data[0x1F064:0x1F864])['sha256'],'cold selected stat and entire durable2048 QOL ledger exact');continued['hof_metadata']=meta[0]
   cases.append(dict(name=name,mode=mode,trace=trace,save=identity(data),physical_stat10=stat,cold=continued))
  need(candidate.read_bytes()==after,'candidate unchanged');write(PUBLIC/'measurement.json',dict(status='PASS_MODE3_COW_UI_ONLY_FAILURE_SUCCESS_AND_COLD',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,isolated_run=RUN,isolated_candidate=isolated['candidate'],cases=cases,native_processes=len(attempts),host_tests=4,ram_fixture_bytes_per_ui_process=9,register_writes=0,natural_entry_accepted=False,initial_hof_atomicity=False,all_save_modes=False,all_cold_owners_preserved=False,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC);names={'hof28-fault','hof29-fault','main-fault','outer-fault','healthy'};dirs=set(names)|{n+'-cold'for n in names}|{n+'-cold/cold-'+str(102 if n in('healthy','outer-fault')else 101)for n in names}
 for p in PUBLIC.rglob('*'):
  rel=p.relative_to(PUBLIC);need(not p.is_symlink()and not any(x.startswith('.')for x in rel.parts),'no hidden or symlink')
  if p.is_dir():need(str(rel)in dirs,'only declared directory');continue
  need(p.is_file(),'regular files only')
  if len(rel.parts)==1:need(p.name in{'host-tests.txt','measurement.json','failure.json','attempts.json'},'closed root text')
  else:need(str(rel.parent)in dirs and(p.name in{'stdout.txt','stderr.txt'}or re.fullmatch(r'screen-000[0-3]\.ppm',p.name)),'only declared original text/screens')
  b=p.read_bytes()
  if p.suffix=='.ppm':need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'complete original screenshot');continue
  need(len(b)<2000000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed changed mode3 UI');globals()[sys.argv[1]]()
