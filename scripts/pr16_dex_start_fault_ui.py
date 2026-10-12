#!/usr/bin/env python3
"""valid-liveの実CPU Flash故障モデル、通常error、キー再保存と2cold Continue。"""
from __future__ import annotations
import json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_start_failure_actions as prior
import pr16_dex_gameplay as game
need,identity,write=prior.need,prior.identity,prior.write
BASE='5a4822770ffd4543c4ad8a98b2a3d595b85c3bab';RUN=37238699272;JOB=111542850908
HEADER='tools/mgba_pr16_dex_start_fault_ui.h';WORKFLOW='.github/workflows/pr16-dex-start-failure.yml'
CODE={HEADER,'scripts/pr16_dex_start_fault_ui.py','tests/test_pr16_dex_start_fault_ui.py','.github/workflows/pr16-dex-start-fault-ui.yml',WORKFLOW}
OUT=ROOT/'.local/pr16-dex-start-fault-ui';PUBLIC=ROOT/'public-dex-start-fault-ui'
def validate_header(s):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for bad in ('busWrite','rawWrite','writeRegister','si_call(','si_restore(','si_open(','loadState(','loadTemporarySave('):need(bad not in s,'no CPU/RAM/writeback fixture '+bad)
 need(s.count('cpu->memory.store8=vf_store8;')==1 and 'FLASH_COMMAND_PROGRAM'in s and 'at==vf_target'in s and 'v^1u'in s,'one bounded Flash data fault hook')
 main=s.split('int main(int argc,char**argv)',1)[1];need(main.index('si_guard(c);')<main.index('st_keys(c,'),'all barriers before first frame');return identity(s.encode())
def generate(candidate):
 s=(ROOT/HEADER).read_text();validate_header(s);old=game.CANDIDATE
 try:game.CANDIDATE=candidate;src=game.generate().decode()
 finally:game.CANDIDATE=old
 token='int main(int argc,char**argv){';need(src.count(token)==1,'one key-only parent main');return(src.replace(token,'int accepted_story_main_not_called(int argc,char**argv){')+'\n'+s).encode()
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first run')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft current HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'bounded UI/closed prior trigger')
 for path in prior.CODE-{WORKFLOW}:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'gate source byte identical')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==BASE and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'gate all10 steps terminal1120 asserted; do not rerun')
 need(t.api('actions/runs/'+str(RUN)+'/artifacts')['total_count']==0,'prior raw measurement missing due upload path; explicit no raw receipt claim')
def screens(rows,folder):
 images=[]
 for r in rows:
  if 'screen'not in r:continue
  b=(folder/f"screen-{r['screen']:04}.ppm").read_bytes();need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n')and identity(b)['sha256']==r['sha256'],'whole original screen identity');need(len(set(b[i:i+3]for i in range(15,len(b),3)))>1,'nonblank rendered pixels');images.append(r)
 return images
def validate_ui(raw,folder,candidate):
 rows=[json.loads(x)for x in raw.splitlines()];need(rows[0]==dict(begin='VALID_MDX_START_FLASH_FAULT_AND_KEY_RETRY',candidate_sha256=candidate['sha256'],host_write_barriers=7,ram_fixture_writes=0,register_writes=0),'closed fault begin')
 end=rows[-1];need(end['end']=='PASS_VALID_START_FLASH_FAULT_KEY_RETRY'and end['failed_counter']==101 and end['retry_counter']==102 and end['ram_fixture_writes']==end['register_writes']==0 and end['host_write_barriers']==7 and not end['old_save_failed_entered']and end['source_bank_and_aux_retained_on_failure']and end['all_extension_bytes_retained_after_fault']==20248 and 0<end['fault_writes']<=16 and end['fault_physical_address']<14*4096,'closed complete fault/retry terminal')
 stages=[r for r in rows if 'start_failure_stage'in r];need([r['start_failure_stage']for r in stages]==['before_fault','error_first_page','error_final_page','field_after_failure','field_after_retry'],'all5 stages')
 need(all(r['counter']==101 for r in stages[:-1])and stages[-1]['counter']==102 and stages[-1]['attempt']==1 and all(r['attempt']==255 for r in stages[1:4]),'failure/error versus actual committed retry')
 frame=inputs=0;pending=False;si=0;saves=[]
 for row in rows[1:-1]:
  if 'input'in row:need(not pending and row['input']==inputs and row['frame']==frame and row['key']in(0,1,2,8,16,32,64,128)and 0<row['frames']<=600,'ordered bounded inputs');frame+=row['frames'];inputs+=1
  elif 'start_failure_stage'in row:need(not pending and row['frame']==frame,'same-frame stage');pending=True
  elif 'screen'in row:need(pending and row['screen']==si and row['frame']==frame,'same-frame screen');si+=1;pending=False
  elif 'ordinary_save'in row:need(not pending and row==dict(ordinary_save=True,before=101,after=102,frame=frame),'one ordinary retry');saves.append(row)
  else:raise ValueError('unknown fault trace row')
 need(not pending and len(saves)==1 and si==end['screens']==5 and frame==end['frames']and inputs==end['inputs'],'complete fault trace')
 return dict(end=end,stages=stages,saves=saves,screens=screens(rows,folder))
def cold(exe,candidate,source,counter,expected,physical_mdx):
 name='cold-'+str(counter);folder=OUT/name;folder.mkdir();public=PUBLIC/name;public.mkdir();save=folder/'cold.srm';save.write_bytes(source)
 args=[str(exe),str(candidate),str(save),'continue-story',identity(source)['sha256']];r=subprocess.run(args,cwd=folder,input='quit\n',capture_output=True,text=True,timeout=180)
 (public/'stdout.txt').write_text(r.stdout);(public/'stderr.txt').write_text(r.stderr)
 for p in folder.glob('*.ppm'):shutil.copyfile(p,public/p.name)
 need(r.returncode==0 and not r.stderr,'cold'+str(counter)+' rc='+str(r.returncode)+' '+r.stderr[-1000:]);rows=[json.loads(x)for x in r.stdout.splitlines()];end=rows[-1]
 need(end['end']=='STORY_INPUT_CHECKPOINT'and end['host_write_barriers']==7 and end['guarded_host_writes']==end['fixture_calls']==end['warnings_errors']==0,'key-only independent cold');need(save.read_bytes()==source,'full FlashRTC unchanged by cold');obs=[x for x in rows if 'observe'in x];mdx=[x for x in rows if 'mdx'in x]
 need(len(obs)==len(mdx)==1 and not any('ordinary_save'in x for x in rows),'one field no save');o=obs[0];d=mdx[0];need(o['save_counter']==counter and o['map']==[3,24]and o['xy']==[53,13]and o['party_count']==4 and o['field']and o['lock']==0,'correct cold generation and location');need(d['valid']and d['live_sha256']==identity(expected)['sha256']and d['physical_matches_current_generation']==physical_mdx,'same migrated or stored MDX');return dict(counter=counter,input=identity(source),output=identity(save.read_bytes()),observation=o,mdx=d,end=end,screens=screens(rows,public))
def run():
 import pr16_story_live_probe as t
 need(not OUT.exists()and not PUBLIC.exists(),'fresh fault-only run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_start_fault_ui.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==3,'three new driver confinement tests');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  prior.OUT=OUT/'build';prior.OUT.mkdir();candidate,before,after,linked,placed=prior.reconstruct();ci=identity(after)
  recovered=dict(status='PASS_SOURCE_IDENTICAL_GATE_RECONSTRUCTION',prior_run=RUN,prior_job=JOB,prior_source=BASE,prior_all10_steps_success=True,prior_asserted_gate_cases=1120,prior_raw_measurement_available=False,publication_error_ja='upload pathが旧public-dex-save-failureで原本JSON未保存。1120case完了はsourceの必須assertと成功stepが根拠。steps/callsの未回収数値は創作しない。',old_native_reruns=0,candidate=ci,parent_candidate=identity(before),link=linked,placement=placed);write(PUBLIC/'reconstructed-gate.json',recovered)
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'same fixed runtime')
  sources=[('fault',generate(ci))];old=game.CANDIDATE
  try:game.CANDIDATE=ci;sources.append(('cold',game.generate()))
  finally:game.CANDIDATE=old
  exes={}
  for name,raw in sources:
   src=OUT/(name+'.c');src.write_bytes(raw);exe=OUT/name;cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)];r=subprocess.run(cmd,capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict '+name+' build '+r.stderr[-2000:]);exes[name]=exe
  z,_=t.archive(t.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==t.SEED,'exact untouched input');expected=game.record(game.physical(seed,101)['legacy']);copy=OUT/'copy.srm';copy.write_bytes(seed);failed=OUT/'failed.srm';saved=OUT/'retry.srm';case=PUBLIC/'fault';case.mkdir();attempts.append('fault');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
  with(case/'stdout.txt').open('wb')as out,(case/'stderr.txt').open('wb')as err:r=subprocess.run([str(exes['fault']),str(candidate),str(copy),str(failed),str(saved)],cwd=case,stdout=out,stderr=err,timeout=300)
  need(r.returncode==0 and not(case/'stderr.txt').read_bytes(),'fault rc='+str(r.returncode)+' '+(case/'stderr.txt').read_text()[-1500:]);trace=validate_ui((case/'stdout.txt').read_bytes(),case,ci);bad=failed.read_bytes();good=saved.read_bytes();need(len(bad)==len(good)==len(seed)==131088 and bad[14*4096:]==seed[14*4096:]and bad!=seed,'whole original source bank/aux/RTC preserved during real torn target');need(game.physical(bad,101)['mdx']==bytes(522),'old101 selected bank remains legacy');physical=game.physical(good,102);need(physical['mdx']==expected and physical['party']==game.physical(seed,101)['party'],'same-session retry has full MDX and party');need(copy.read_bytes()==good,'final emulator file equals private captured whole retry FlashRTC')
  cs=[]
  for data,counter,physical_mdx in [(bad,101,0),(good,102,1)]:attempts.append('cold-'+str(counter));write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));cs.append(cold(exes['cold'],candidate,data,counter,expected,physical_mdx))
  for k in ('party_sha256','map','xy','party_count'):need(cs[0]['observation'][k]==cs[1]['observation'][k],'both cold retain '+k)
  need(cs[0]['mdx']['bag_sha256']==cs[1]['mdx']['bag_sha256'],'both cold retain normalized Bag');need(candidate.read_bytes()==after,'candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_VALID_START_FAILURE_UI_RETRY_AND_TWO_COLD',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,reconstructed_gate=recovered,trace=trace,cold=cs,failed_save=identity(bad),retried_save=identity(good),input_save=identity(seed),native_processes=len(attempts),host_suites=3,ram_fixture_writes=0,register_writes=0,formal_rom_changed=False,formal_save_changed=False,all_save_modes_accepted=False,all_consumers_wired=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=len(attempts),attempts=attempts));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated fault publication')
 for p in PUBLIC.rglob('*'):
  rel=p.relative_to(PUBLIC);need(not p.is_symlink()and not any(v.startswith('.')for v in rel.parts),'no hidden or symlink')
  if p.is_dir():need(str(rel)in('fault','cold-101','cold-102'),'known dirs');continue
  need(p.is_file(),'regular only')
  if len(rel.parts)==1:need(p.name in{'host-tests.txt','reconstructed-gate.json','measurement.json','attempts.json','failure.json'},'known root text')
  else:need(len(rel.parts)==2 and rel.parts[0]in('fault','cold-101','cold-102')and(p.name in('stdout.txt','stderr.txt')or re.fullmatch(r'screen-000[0-4]\.ppm',p.name)),'known text/screens only')
  b=p.read_bytes()
  if p.suffix=='.ppm':need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'whole screenshot');continue
  need(len(b)<2000000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed command');globals()[sys.argv[1]]()
