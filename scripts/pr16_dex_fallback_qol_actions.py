#!/usr/bin/env python3
"""fallback専用新sourceをcompile。容量・純粋validator監査前には配置/実行しない。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
import pr16_dex_hof_failure_actions as prior
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_fallback_qol as f
need,identity=f.need,f.identity
BASE='f7a70dfa1f037f1824aeb4fc18a62f10fe11f0db'
WF='.github/workflows/pr16-dex-fallback-qol.yml';GUIDE='docs/PR16_DEX_FALLBACK_QOL_JA.md'
CODE={f.SOURCE,f.HOST_REFERENCE,f.BINDINGS,'content/modernization/pr16_dex_fallback_tail_lease.json','scripts/pr16_dex_fallback_tail_lease.py','scripts/pr16_dex_fallback_qol.py','scripts/pr16_dex_fallback_qol_actions.py','tools/mgba_pr16_dex_fallback_qol.h','tests/test_pr16_dex_fallback_qol.py',WF,GUIDE}
OUT=ROOT/'.local/pr16-dex-fallback-qol';PUBLIC=ROOT/'public-dex-fallback-qol';ARTIFACT='pr16-dex-fallback-qol-text-only'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_fallback_qol_actions.py')
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current first run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'exact new fallback sources')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'prior native terminal')
 for p,b in state['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'every previously bound source retained '+p)
def reconstruct():
 prior.OUT=OUT/'parent';prior.OUT.mkdir();_,_,before,_,_=prior.reconstruct();need(identity(before)==f.checkpoint()['candidate'],'exact prior HOF whole ROM')
 payload,linked=f.link(OUT/'fallback-link');after,placed=f.apply(before,payload,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after);return candidate,before,after,linked,placed

def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh isolated fallback run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_fallback_qol.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==1,'new fallback host matrix');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  candidate,before,after,linked,placed=reconstruct();ci=identity(after);write(PUBLIC/'build.json',dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'same fixed runtime')
  exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in exports.items())+f.entries()+'#define FALLBACK_ENTRY '+hex(linked['entry'])+'u\n')
  src=OUT/'isolated.c';src.write_text((ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text().replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')+'\n'+(ROOT/'tools/mgba_pr16_dex_fallback_qol.h').read_text());exe=OUT/'isolated'
  r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/save_migration/save_migration.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict fallback native compile '+r.stderr[-1800:])
  attempts.append('isolated');write(PUBLIC/'attempts.json',dict(native_processes=1,cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=600);(PUBLIC/'isolated-stdout.txt').write_text(r.stdout);(PUBLIC/'isolated-stderr.txt').write_text(r.stderr);need(r.returncode==0 and not r.stderr,'isolated rc='+str(r.returncode)+' '+r.stderr[-1500:]);native=json.loads(r.stdout);need(native['status']=='PASS_ARM_FALLBACK_IDLE_LEDGER_RESTORE'and native['cases']==508,'all508 scoped ARM conditions');need(candidate.read_bytes()==after,'private candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_ISOLATED_FALLBACK_IDLE_QOL_LEDGER',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,host_cases=327907,isolated=native,native_processes=1,cold_accepted=False,all_cold_owners_preserved=False,initial_hof_atomicity=False,formal_rom_changed=False,formal_save_changed=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'host-tests.txt','measurement.json','failure.json','build.json','attempts.json','isolated-stdout.txt','isolated-stderr.txt'},'closed regular text only');b=p.read_bytes();need(len(b)<1500000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed fallback action');globals()[sys.argv[1]]()
