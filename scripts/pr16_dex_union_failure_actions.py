#!/usr/bin/env python3
"""Union Room Chatの新規caller通知縦切りだけ測定。旧受入native再走なし。"""
from __future__ import annotations
import json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_union_failure as f
import pr16_dex_outer_qol_actions as prior
need,identity,write=prior.need,prior.identity,prior.write
BASE='2fb796501cc834552f1e2beee0f588d96eac378d'
HEADER='tools/mgba_pr16_dex_union_failure.h'
GUIDE='docs/PR16_DEX_UNION_FAILURE_JA.md'
WF='.github/workflows/pr16-dex-union-failure.yml'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_union_failure.py','scripts/pr16_dex_union_failure_actions.py','tests/test_pr16_dex_union_failure.py','scripts/pr16_dex_subowners.py','scripts/pr16_dex_tail_lease.py','content/modernization/pr16_dex_union_tail_lease.json','scripts/pr16_dex_mystery_failure.py',HEADER,GUIDE,WF}
OUT=ROOT/'.local/pr16-dex-union-failure';PUBLIC=ROOT/'public-dex-union-failure'
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first current run')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'exact new Union Room Chat source paths')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'prior record terminal')
 for path,b in state['source_bindings'].items():
  if path=='scripts/pr16_dex_mystery_failure.py':
   old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT);needle=b'def apply(before,payload,linked):\n';insert=needle+b' import pr16_dex_subowners as current\n current.require_codec_lease(BASE,len(payload))\n';need(old.count(needle)==1 and(ROOT/path).read_bytes()==old.replace(needle,insert),'only fail-closed actual-subowner guard added to historical generator');continue
  need(identity((ROOT/path).read_bytes())==b,'all other accepted source retained '+path)
def reconstruct():
 prior.OUT=OUT/'parent';prior.OUT.mkdir();_,_,before,_,_=prior.reconstruct();need(identity(before)==f.checkpoint()['isolated']['parent_candidate'],'intact outer reconstruction')
 payload,linked=f.link(OUT/'union',before);after,placed=f.apply(before,payload,linked);path=OUT/'candidate.gba';path.write_bytes(after);return path,before,after,linked,placed
def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh Union Room Chat attempt');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_union_failure.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==8,'eight targeted host tests');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  candidate,before,after,linked,placed=reconstruct();ci=identity(after);write(PUBLIC/'build.json',dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
  entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in prior.f.b.lifecycle.checkpoint()['link']['exports'].items()))
  src=OUT/'isolated.c';src.write_text((ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text().replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')+'\n'+(ROOT/HEADER).read_text());exe=OUT/'isolated'
  r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict isolated compile '+r.stderr[-1800:])
  attempts.append('isolated');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300);(PUBLIC/'isolated-stdout.txt').write_text(r.stdout);(PUBLIC/'isolated-stderr.txt').write_text(r.stderr);need(r.returncode==0 and not r.stderr,'isolated rc='+str(r.returncode)+' '+r.stderr[-1200:]);native=json.loads(r.stdout)
  need(native['status']=='PASS_ISOLATED_UNION_SAVE_NOTIFICATION_AND_RETURN'and native['cases']==1016,'new caller96 scope720 text200 cases');need(candidate.read_bytes()==after,'private ROM unchanged')
  regressions={}
  common=(ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text().replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')
  mystery=(ROOT/'tools/mgba_pr16_dex_mystery_failure.h').read_text();needle='outers[]={0x08143287,0x08129A93,0x0806F147}';need(mystery.count(needle)==1,'one impacted negative caller updated');mystery=mystery.replace(needle,'outers[]={0x08143287,0x08129A91,0x0806F147}')
  sources=[('restored-scheduler',(ROOT/'tools/mgba_pr16_dex_scheduler.c').read_text(),'PASS_ISOLATED_ARM_SCHEDULER_SYNTHETIC_FLASH',19),('relocated-mystery',common+'\n'+mystery,'PASS_ISOLATED_MYSTERY_MENU_AND_EXACT_FAILURE_SCOPE',816)]
  for name,source,status,cases in sources:
   src=OUT/(name+'.c');src.write_text(source);exe=OUT/name;r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict impacted regression compile '+r.stderr[-1800:])
   attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300);(PUBLIC/(name+'-stdout.txt')).write_text(r.stdout);(PUBLIC/(name+'-stderr.txt')).write_text(r.stderr);need(r.returncode==0 and not r.stderr,name+' rc='+str(r.returncode)+' '+r.stderr[-1000:]);rows=[json.loads(x)for x in r.stdout.splitlines()];result=rows[-1];need(result['status']==status and result['cases']==cases,'complete impacted '+name);regressions[name]=result
  write(PUBLIC/'measurement.json',dict(status='PASS_ISOLATED_UNION_SAVE_FAILURE_NOTIFICATION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,isolated=native,regressions=regressions,native_processes=len(attempts),host_tests=8,old_unaffected_native_reruns=0,changed_impact_native_reruns=2,formal_rom_changed=False,formal_save_changed=False,union_physical_ui_accepted=False,all_nonstart_notifications_accepted=False,all_save_modes_accepted=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in{'host-tests.txt','build.json','measurement.json','attempts.json','failure.json','isolated-stdout.txt','isolated-stderr.txt','restored-scheduler-stdout.txt','restored-scheduler-stderr.txt','relocated-mystery-stdout.txt','relocated-mystery-stderr.txt'},'closed regular text only')
  raw=p.read_bytes();need(len(raw)<2000000 and b'\0'not in raw and(not raw or raw.endswith(b'\n')),'bounded complete UTF8');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed actions');globals()[sys.argv[1]]()
