#!/usr/bin/env python3
"""HOFの9byte入口から実表示/音/一回保存/独立coldだけを追加する。"""
from __future__ import annotations
import json,os,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_failure_actions as prior
need,identity,write=prior.need,prior.identity,prior.write
BASE='98870aa4841bb2ccf25e143c8d685004f764b618';RUN=37254891427;JOB=111589743264;ARCHIVE=(11322336994,RUN,48093,'4ec434ee2ea1cfb094f001b35d47c0b2dc3171a5dac82e4f5282f6f9a03729cc')
HEADER='tools/mgba_pr16_dex_hof_ui.h';BINDINGS='content/modernization/pr16_dex_hof_ui_bindings.json';OLDWF=prior.WF;WF='.github/workflows/pr16-dex-hof-ui.yml';ARTIFACT='pr16-dex-hof-ui-text-only'
CODE={HEADER,BINDINGS,'scripts/pr16_dex_hof_ui.py','tests/test_pr16_dex_hof_ui.py',OLDWF,WF}
OUT=ROOT/'.local/pr16-dex-hof-ui';PUBLIC=ROOT/'public-dex-hof-ui'
def validate_header(source):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
 for bad in('rawWrite','writeRegister','si_call(','si_restore(','si_open(','loadState(','loadTemporarySave('):need(bad not in s,'no general fixture '+bad)
 need(s.count('hu_write8(c,addresses[i],values[i]);')==1 and s.count('hu_fixture(c);')==1 and 'allowed_fixture_bytes\\\":9'in s,'one9byte fixture callsite')
 need('0x080F2E5Du'in s and 'addresses[8]=0x03003568'in s and 'c->frameCounter(c)==frame'in s,'closed current callback entry and no frame during writes')
 need(s.count('cpu->memory.store8=hu_store8;')==1 and 'FLASH_COMMAND_PROGRAM'in s and 'at==hu_target'in s and 'v^1u'in s,'one bounded Flash data fault')
 need(not re.search(r'cpu->gprs\[[^\]]+\]\s*=(?!=)',s),'all CPU register observations read only')
 main=s.split('int main(int argc,char**argv)',1)[1];need(main.index('si_guard(c);')<main.index('st_keys(c,'),'barriers before first frame');return identity(s.encode())
def generate(candidate,linked,cold=False):
 import pr16_dex_gameplay as game
 old=game.CANDIDATE
 try:game.CANDIDATE=candidate;source=game.generate().decode()
 finally:game.CANDIDATE=old
 if not cold:
  s=(ROOT/HEADER).read_text();validate_header(s);token='int main(int argc,char**argv){';need(source.count(token)==1,'one parent main');return(source.replace(token,'int accepted_story_main_not_called(int argc,char**argv){')+'\n#define HOF_UI_WAIT '+hex(linked['exports']['VegaDexHofSaveFailureWait'])+'u\n'+s).encode()
 helper='''static void hc_metadata(struct mCore*c,unsigned frame){uint8_t q[2048];char sha[65];for(unsigned i=0;i<2048;i++)q[i]=read8(c,0x0203D000+i);si_digest(q,2048,sha);unsigned stat=read32(c,read32(c,QOL_SAVE_BLOCK1_SLOT)+0x1228)^read32(c,read32(c,0x0300504C)+0xF20);printf("{\\"hof_cold_metadata\\":true,\\"frame\\":%u,\\"stat10\\":%u,\\"ledger_sha256\\":\\"%s\\"}\\n",frame,stat,sha);}\n'''
 token='static struct mCore *st_open(';need(source.count(token)==1,'one metadata insertion');source=source.replace(token,helper+token);token='dx_observe(c,n,st_frames);st_screen(n);';need(source.count(token)==1,'one cold observation');return source.replace(token,'dx_observe(c,n,st_frames);hc_metadata(c,st_frames);st_screen(n);').encode()
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_ui.py');need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized HOF UI first run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'only new HOF UI sources')
 for path in prior.CODE-{OLDWF}:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'all isolated implementation bytes retained')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==BASE and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'complete isolated all10steps')
 old=subprocess.check_output(['git','show',BASE+':'+OLDWF],cwd=ROOT);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+OLDWF+']\n').encode();need(old.count(trigger)==1 and(ROOT/OLDWF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'retire old native trigger without source changes')
def validate_trace(raw,folder,candidate,mode):
 import pr16_dex_start_fault_ui as image
 rows=[json.loads(x)for x in raw.splitlines()];need(rows[0]==dict(begin='HOF_UI_ONLY_FIXTURE',candidate_sha256=candidate['sha256'],mode=mode,host_write_barriers=7,register_writes=0,allowed_fixture_bytes=9),'exact UI begin');end=rows[-1]
 need(end['end']=='PASS_HOF_UI_FAILURE_SUCCESS_AND_NO_RETRY'and end['mode']==mode and end['fixture_bytes_written']==9 and end['register_writes']==0 and end['host_write_barriers']==7 and end['native_hof_saves']==end['stock_save_calls']==end['stat10_increment_calls']==1,'one physical HOF attempt')
 need(end['stat10_after']==end['stat10_before']+1 and end['attempt']==(255 if mode else 1)and end['counter']==(101 if mode==1 else 102)and end['save_sounds']==int(mode==0)and end['result_printers']==int(mode!=0),'truthful result and single initial increment')
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
 need(not OUT.exists()and not PUBLIC.exists(),'fresh HOF UI');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_hof_ui.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==4,'four new UI guards');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),prior.ARTIFACT,RUN);z,_=t.archive(ARCHIVE)
  with z:isolated=json.loads(z.read('measurement.json'))
  prior.OUT=OUT/'build';prior.OUT.mkdir();candidate,before,after,linked,placed=prior.reconstruct();ci=identity(after);need({k:isolated[k]for k in('candidate','parent_candidate','link','placement')}==dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed),'exact complete previously isolated reconstruction')
  for w in json.loads((ROOT/BINDINGS).read_bytes())['windows']:
   a=w['address']-0x08000000;need(identity(after[a:a+w['size']])=={k:w[k]for k in('size','sha256')},'signed HOF UI entry '+w['id'])
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
  exes={}
  for name,is_cold in [('ui',False),('cold',True)]:
   src=OUT/(name+'.c');src.write_bytes(generate(ci,linked,is_cold));exe=OUT/(name+'-native');r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict '+name+' compile '+r.stderr[-1800:]);exes[name]=exe
  z,_=t.archive(t.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==t.SEED,'formal Save101 original');seeddata=game.physical(seed,101);expected=game.record(seeddata['legacy']);cases=[];initial_stat=struct.unpack_from('<I',seeddata['save1'],0x1228)[0]^struct.unpack_from('<I',seeddata['save2'],0xF20)[0]
  for mode,name in[(1,'main-fault'),(2,'outer-fault'),(0,'healthy')]:
   folder=OUT/name;folder.mkdir();public=PUBLIC/name;public.mkdir();copy=folder/'copy.srm';copy.write_bytes(seed);captured=folder/'captured.srm';attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
   with(public/'stdout.txt').open('wb')as out,(public/'stderr.txt').open('wb')as err:r=subprocess.run([str(exes['ui']),str(candidate),str(copy),str(captured),str(mode)],cwd=public,stdout=out,stderr=err,timeout=420)
   need(r.returncode==0 and not(public/'stderr.txt').read_bytes(),name+' rc='+str(r.returncode)+' '+(public/'stderr.txt').read_text()[-1800:]);trace=validate_trace((public/'stdout.txt').read_bytes(),public,ci,mode);data=captured.read_bytes();need(len(data)==131088 and data[131072:]==seed[131072:]and copy.read_bytes()==data,'complete copied FlashRTC capture')
   counter=101 if mode==1 else 102;p=game.physical(data,counter);stat=struct.unpack_from('<I',p['save1'],0x1228)[0]^struct.unpack_from('<I',p['save2'],0xF20)[0];need(p['party']==seeddata['party']and p['mdx']==(bytes(522)if mode==1 else expected)and stat==initial_stat+int(mode!=1),'selected generation party/MDX/HOF count coherent')
   cf=OUT/(name+'-cold');cf.mkdir();cp=PUBLIC/(name+'-cold');cp.mkdir();cold.OUT=cf;cold.PUBLIC=cp;attempts.append(name+'-cold');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));continued=cold.cold(exes['cold'],candidate,data,counter,expected,int(mode!=1));rows=[json.loads(x)for x in(cp/('cold-'+str(counter))/'stdout.txt').read_bytes().splitlines()];meta=[x for x in rows if'hof_cold_metadata'in x];need(len(meta)==1 and meta[0]['stat10']==stat,'cold live HOF count from selected generation');continued['hof_metadata']=meta[0]
   cases.append(dict(name=name,mode=mode,trace=trace,save=identity(data),physical_stat10=stat,cold=continued))
  need(candidate.read_bytes()==after,'candidate unchanged');write(PUBLIC/'measurement.json',dict(status='PASS_HOF_UI_ONLY_FAILURE_SUCCESS_AND_COLD',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,isolated_run=RUN,isolated_candidate=isolated['candidate'],cases=cases,native_processes=len(attempts),host_tests=4,ram_fixture_bytes_per_ui_process=9,register_writes=0,natural_entry_accepted=False,all_nonstart_notifications_accepted=False,all_save_modes_accepted=False,hof_atomicity_accepted=False,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC);dirs={'main-fault','outer-fault','healthy','main-fault-cold','outer-fault-cold','healthy-cold','main-fault-cold/cold-101','outer-fault-cold/cold-102','healthy-cold/cold-102'}
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
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed HOF UI action');globals()[sys.argv[1]]()
