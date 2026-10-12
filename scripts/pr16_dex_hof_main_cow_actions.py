#!/usr/bin/env python3
"""mode3 mainの新規変更だけ。既存受入nativeを再走しない。"""
from __future__ import annotations
import json,os,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_main_cow as f
import pr16_dex_fallback_qol_actions as prior
need,identity=f.need,f.identity
BASE='faba7fde12a0aca9892c0e137edda4e8d727a0f5'
WF='.github/workflows/pr16-dex-hof-main-cow.yml';GUIDE='docs/PR16_DEX_HOF_MAIN_COW_JA.md';HEADER='tools/mgba_pr16_dex_hof_main_cow.h'
HOST='content/modernization/pr16_dex_hof_main_cow_host.json'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_hof_main_cow.py','scripts/pr16_dex_hof_main_cow_actions.py','tests/test_pr16_dex_hof_main_cow.py',HEADER,GUIDE,WF,HOST}
OUT=ROOT/'.local/pr16-dex-hof-main-cow';PUBLIC=ROOT/'public-dex-hof-main-cow';ARTIFACT='pr16-dex-hof-main-cow-text-only'
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_main_cow_actions.py')
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current first mode3 run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'only nine new mode3 files')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'all prior scoped work terminal')
 for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'all previously bound source bytes retained '+path)
 j=t.api('actions/jobs/111609876395');need(j['run_id']==37261623547 and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'fallback closeout complete')
def reconstruct():
 prior.OUT=OUT/'parent';prior.OUT.mkdir();_,_,before,old_link,old_place=prior.reconstruct();need(identity(before)==f.checkpoint()['candidate'],'exact current115owner parent')
 need(old_place==f.checkpoint()['current_build']['placement'],'entire current parent allocation and retention receipt')
 f.signed(before);patches,linked=f.link(OUT/'hof-cow-link');after,placed=f.apply(before,patches,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after);return candidate,before,after,linked,placed
def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh mode3 measurement');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  host=json.loads((ROOT/HOST).read_bytes());need(host['status']=='PASS_NEW_MODE3_SOURCE_CONTRACTS'and host['tests']==7 and host['exit_code']==0,'seven previously measured new host tests')
  for path,b in host['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'reuse exact measured host inputs '+path)
  write(PUBLIC/'host-tests.json',host)
  candidate,before,after,linked,placed=reconstruct();ci=identity(after);write(PUBLIC/'build.json',dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed accepted runtime')
  exports=json.loads((ROOT/f.SCHED).read_bytes())['link']['exports'];entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in exports.items())+'#define HOF_COW_ENTRY '+hex(linked['entry'])+'u\nstatic const unsigned hc_dispatch_targets[]={'+','.join(hex(struct.unpack_from('<I',before,0xDB258+4*i)[0])+'u'for i in range(6))+'};\n')
  source=(ROOT/'tools/mgba_pr16_dex_scheduler.c').read_text();need(source.count('int main(int argc,char **argv)')==1,'one accepted scheduler entry renamed only');src=OUT/'isolated.c';src.write_text(source.replace('int main(int argc,char **argv)','int accepted_scheduler_main_not_called(int argc,char **argv)')+'\n'+(ROOT/HEADER).read_text());exe=OUT/'isolated'
  r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict mode3 isolated compile '+r.stderr[-1800:])
  attempts.append('mode3-isolated');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=720);(PUBLIC/'isolated-stdout.txt').write_text(r.stdout);(PUBLIC/'isolated-stderr.txt').write_text(r.stderr);need(r.returncode==0 and not r.stderr,'isolated rc='+str(r.returncode)+' '+r.stderr[-1800:]);native=json.loads(r.stdout);need(native['status']=='PASS_ARM_MODE3_MAIN_COW_SOURCE_AUTHORITY'and native['cases']==554 and native['mode3_cases']==42 and native['dispatch_cases']==512,'all changed scope conditions');need(candidate.read_bytes()==after,'private candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_ISOLATED_MODE3_MAIN_COW_SOURCE_AUTHORITY',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,isolated=native,native_processes=1,host_tests=7,unaffected_native_reruns=0,initial_hof_atomicity=False,all_save_modes=False,gameplay_accepted=False,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC)
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in{'host-tests.json','build.json','measurement.json','attempts.json','failure.json','isolated-stdout.txt','isolated-stderr.txt'},'only explicit regular public text');b=path.read_bytes();need(len(b)<2000000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded complete UTF8');b.decode('utf8')
  if path.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed mode3 actions');globals()[sys.argv[1]]()
