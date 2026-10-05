#!/usr/bin/env python3
"""d773a123候補のcold loadだけ追加。主故障生成・旧HOF/Union入力を再走しない。"""
from __future__ import annotations
import json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_fallback_qol_actions as prior
need,identity,write=prior.need,prior.identity,prior.write
BASE='06ff1e48ae0dd1dcaa5e49e803bd2df7c777dd3e';RUN=37258786462;JOB=111601363009;ARCHIVE=(11324225759,RUN,49949,'ef08914791b96041206d9904a0daa831a84a0109f45e907d626e4e31164206a7')
HEADER='tools/mgba_pr16_dex_fallback_cold.h';OLDWF=prior.WF;WF='.github/workflows/pr16-dex-fallback-cold.yml';ARTIFACT='pr16-dex-fallback-cold-text-only'
CODE={HEADER,'scripts/pr16_dex_fallback_cold.py','tests/test_pr16_dex_fallback_cold.py',OLDWF,WF}
OUT=ROOT/'.local/pr16-dex-fallback-cold';PUBLIC=ROOT/'public-dex-fallback-cold'
def validate_header(s):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for bad in('busWrite','rawWrite','writeRegister','si_call(','si_restore(','si_open(','loadState(','loadTemporarySave('):need(bad not in s,'no direct state write '+bad)
 need(not re.search(r'cpu->gprs\[[^\]]+\]\s*=(?!=)',s),'CPU register observations read only')
 need(s.count('c->runFrame=fb_frame;')==1 and s.count('si_guard(c);')==1 and s.index('si_guard(c);')<s.index('st_keys(c,0,600)'),'all seven barriers before first frame')
 need('memcmp(flash,fb_flash,131072)'in s and '!fb_save_calls'in s,'all Flash and recovery writes guarded');return identity(s.encode())
def generate(candidate,entry):
 import pr16_dex_gameplay as game
 s=(ROOT/HEADER).read_text();validate_header(s);old=game.CANDIDATE
 try:game.CANDIDATE=candidate;source=game.generate().decode()
 finally:game.CANDIDATE=old
 token='int main(int argc,char**argv){';need(source.count(token)==1,'one inherited main');return(source.replace(token,'int accepted_story_main_not_called(int argc,char**argv){')+'\n#define FALLBACK_ENTRY '+hex(entry)+'u\n'+s).encode()
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_fallback_cold.py');need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first current cold');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'only new cold sources and retired isolated trigger')
 for path in prior.CODE-{OLDWF}:need((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'all isolated implementation unchanged '+path)
 old=subprocess.check_output(['git','show',BASE+':'+OLDWF],cwd=ROOT);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+OLDWF+']\n').encode();need(old.count(trigger)==1 and(ROOT/OLDWF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'accepted native manual-only')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==BASE and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'complete isolated all10 success')
def trace(raw,folder,candidate,source,blocked):
 import pr16_dex_start_fault_ui as images
 rows=[json.loads(x)for x in raw.splitlines()];need(rows[0]==dict(begin='FALLBACK_QOL_COLD_KEYS_ONLY',candidate_sha256=candidate['sha256'],input_sha256=identity(source)['sha256'],blocked=blocked,host_write_barriers=7,ram_fixture_writes=0,register_writes=0),'closed cold begin');end=rows[-1]
 frame=inputs=0;meta=[];obs=[];mdx=[];screens=[];phase=0
 for row in rows[1:-1]:
  if'input'in row:need(phase==0 and row['input']==inputs and row['frame']==frame and row['key']in(0,1,2,8,16,32,64,128)and 0<row['frames']<=600,'ordered bounded keys');inputs+=1;frame+=row['frames']
  elif'fallback_cold'in row:need(phase==0 and row['frame']==frame,'single final metadata');meta.append(row);phase=1
  elif'observe'in row:need(phase==1 and row['frame']==frame,'same-frame observation');obs.append(row);phase=2
  elif'mdx'in row:need(phase==2 and row['frame']==frame,'same-frame MDX');mdx.append(row);phase=3
  elif'screen'in row:need(phase==3 and row['frame']==frame,'same-frame screen');screens.append(row);phase=4
  else:raise ValueError('unknown cold trace row')
 need(phase==4 and len(meta)==len(obs)==len(mdx)==len(screens)==1,'one complete final observation');need(end==dict(end='PASS_FALLBACK_QOL_COLD',frames=frame,inputs=inputs,blocked=blocked,host_write_barriers=7,ram_fixture_writes=0,register_writes=0,native_processes=1),'complete cold end')
 m,o,d=meta[0],obs[0],mdx[0];need(m['save_calls']==0 and m['flash_all_bytes_unchanged']and m['counter']==101 and m['ledger_sha256']==o['ledger_sha256']and m['status']==d['save_file_status'],'full coherent cold metadata');need(m['blocked']==blocked and o['field']==(not blocked),'field only valid idle ledger')
 if not blocked:need(m['ledger_physical_exact']and m['ledger_sha256']==identity(source[0x1F064:0x1F864])['sha256']and d['valid']and o['map']==[3,24]and o['xy']==[53,13]and o['party_count']==4 and o['lock']==0,'full durable ledger and selected formal location')
 else:need(m['status']==2 and not d['valid'],'invalid durable blocks Continue without initialization')
 need(images.screens(rows,folder)==screens,'complete original screen bytes');return dict(metadata=m,observation=o,mdx=d,screens=screens,end=end)
def fixture(seed,kind):
 need(len(seed)==131088,'whole FlashRTC');out=bytearray(seed);offsets=[]
 if kind!='healthy':out[0xFF8]^=1;offsets.append(0xFF8)
 if kind=='corrupt-ledger':out[0x1F06C]^=1;offsets.append(0x1F06C)
 need(kind in('healthy','fallback','corrupt-ledger'),'closed copied Flash fixture');need([i for i,(a,b)in enumerate(zip(seed,out))if a!=b]==offsets,'only declared copied Flash bytes');return bytes(out),dict(kind=kind,changed_byte_offsets=offsets,changed_bytes=len(offsets),input=identity(seed),output=identity(out),selected_bank1_aux_and_RTC_unchanged=kind!='corrupt-ledger',ram_fixture_writes=0)
def run():
 import pr16_story_live_probe as t,pr16_dex_publication as publication,pr16_dex_gameplay as game
 need(not OUT.exists()and not PUBLIC.exists(),'fresh cold-only run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_fallback_cold.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==3,'three new cold confinement tests');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),prior.ARTIFACT,RUN);z,_=t.archive(ARCHIVE)
  with z:isolated=json.loads(z.read('measurement.json'))
  prior.OUT=OUT/'build';prior.OUT.mkdir();candidate,before,after,linked,placed=prior.reconstruct();ci=identity(after);need({k:isolated[k]for k in('candidate','parent_candidate','link','placement')}==dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed),'exact previously isolated build')
  src=OUT/'cold.c';src.write_bytes(generate(ci,linked['entry']));exe=OUT/'cold-native';r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict key-only compile '+r.stderr[-1800:])
  z,_=t.archive(t.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==t.SEED,'formal Save101 original exact');selected=game.physical(seed,101);expected=game.record(selected['legacy']);cases=[]
  for name in('healthy','fallback','corrupt-ledger'):
   data,declared=fixture(seed,name);need(game.physical(data,101)==selected,'every selected101 byte identical to formal');private=OUT/name;private.mkdir();public=PUBLIC/name;public.mkdir();save=private/'copy.srm';save.write_bytes(data);blocked=int(name=='corrupt-ledger');attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
   r=subprocess.run([str(exe),str(candidate),str(save),'blocked'if blocked else'valid',identity(data)['sha256']],cwd=public,capture_output=True,text=True,timeout=300);(public/'stdout.txt').write_text(r.stdout);(public/'stderr.txt').write_text(r.stderr);need(r.returncode==0 and not r.stderr,name+' rc='+str(r.returncode)+' '+r.stderr[-1500:]);parsed=trace(r.stdout,public,ci,data,blocked);need(save.read_bytes()==data,'all FlashRTC file bytes unchanged by cold');need(parsed['metadata']['status']==(1 if name=='healthy' else 255 if name=='fallback' else 2),'exact healthy/fallback/rejected status')
   if not blocked:need(parsed['mdx']['live_sha256']==identity(expected)['sha256'],'whole selected101 migrated MDX')
   cases.append(dict(name=name,fixture=declared,trace=parsed,save=identity(data),output=identity(save.read_bytes())))
  for key in('party_sha256','map','xy','party_count'):need(cases[0]['trace']['observation'][key]==cases[1]['trace']['observation'][key],'fallback preserves '+key)
  need(cases[0]['trace']['mdx']['bag_sha256']==cases[1]['trace']['mdx']['bag_sha256'],'normalized Bag unchanged');need(candidate.read_bytes()==after,'private ROM unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_FALLBACK_IDLE_LEDGER_COLD_AND_INVALID_BLOCK',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,isolated_run=RUN,isolated_candidate=isolated['candidate'],formal_seed=identity(seed),physical_ledger=identity(seed[0x1F064:0x1F864]),cases=cases,native_processes=len(attempts),host_tests=3,old_native_reruns=0,ram_fixture_writes=0,register_writes=0,physical_copy_fixture=True,all_cold_owners_preserved=False,sector31_atomicity=False,hof_initial_atomicity=False,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC)
 for p in PUBLIC.rglob('*'):
  rel=p.relative_to(PUBLIC);need(not p.is_symlink()and not any(x.startswith('.')for x in rel.parts),'no hidden/symlink')
  if p.is_dir():need(str(rel)in('healthy','fallback','corrupt-ledger'),'closed directory');continue
  need(p.is_file(),'regular only')
  if len(rel.parts)==1:need(p.name in('host-tests.txt','measurement.json','failure.json','attempts.json'),'closed root text')
  else:need(len(rel.parts)==2 and rel.parts[0]in('healthy','fallback','corrupt-ledger')and p.name in('stdout.txt','stderr.txt','screen-0000.ppm'),'closed trace/screens')
  b=p.read_bytes()
  if p.suffix=='.ppm':need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'complete screen');continue
  need(len(b)<1500000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed cold action');globals()[sys.argv[1]]()
