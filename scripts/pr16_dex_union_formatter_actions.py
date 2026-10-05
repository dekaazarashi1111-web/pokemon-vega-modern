#!/usr/bin/env python3
"""Union formatterの新規32byte owner leaseだけ検証。既存920+835条件はbyte一致で再利用。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_union_failure_actions as parent
f=parent.f;need,identity,write=parent.need,parent.identity,parent.write
BASE='38a8b1df37b4c211dfe8e8850226a7d68ff662e1'
ORIGINAL_RUN=37247511968;ORIGINAL_ARCHIVE=(11319413359,ORIGINAL_RUN,54317,'f6ec079006433fc2ffccd0b3b36c7287ff493a847600dbd5785d5a2a65ff7fd7')
HEADER='tools/mgba_pr16_dex_union_formatter.h';WF='.github/workflows/pr16-dex-union-formatter.yml';OLDWF='.github/workflows/pr16-dex-union-ui.yml'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_union_failure.py','scripts/pr16_dex_tail_lease.py','content/modernization/pr16_dex_union_tail_lease.json','tests/test_pr16_dex_union_failure.py','scripts/pr16_dex_union_formatter_actions.py',HEADER,WF,OLDWF,parent.GUIDE}
OUT=ROOT/'.local/pr16-dex-union-formatter';PUBLIC=ROOT/'public-dex-union-formatter'
def guard():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current formatter run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'only declared formatter correction sources')
 old=subprocess.check_output(['git','show',BASE+':'+OLDWF],cwd=ROOT);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+OLDWF+']\n').encode();need(old.count(trigger)==1 and(ROOT/OLDWF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'failed UI trigger manual during correction')
def reconstruct():
 parent.OUT=OUT/'parent';parent.OUT.mkdir();return parent.reconstruct()
def run():
 import pr16_story_live_probe as t
 need(not OUT.exists()and not PUBLIC.exists(),'fresh scoped formatter run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_union_failure.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==8,'eight host guards');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  z,_=t.archive(ORIGINAL_ARCHIVE)
  with z:accepted=json.loads(z.read('measurement.json'))
  candidate,before,after,linked,placed=reconstruct();ci=identity(after);size=linked['payload']['size'];need(size==408 and linked['exports']['VegaDexUnionResultDisplayGuard']==f.BASE+361,'one appended48byte formatter wrapper')
  reverted=bytearray(after);lo=f.BASE-0x08000000;reverted[lo+360:lo+size]=before[lo+360:lo+size];reverted[0x41A774:0x41A778]=before[0x41A774:0x41A778];need(identity(reverted)==accepted['candidate'],'whole exact rollback to previously isolated1ec42a50; all earlier gates and scheduler unchanged')
  write(PUBLIC/'build.json',dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,previous_isolated_candidate=accepted['candidate'],previous_isolated_run=ORIGINAL_RUN,delta_rollback_exact=True))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'same fixed runtime')
  entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in parent.prior.f.b.lifecycle.checkpoint()['link']['exports'].items())+'#define UNION_FORMATTER '+hex(linked['exports']['VegaDexUnionResultDisplayGuard'])+'u\n')
  src=OUT/'formatter.c';src.write_text((ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text().replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')+'\n'+(ROOT/HEADER).read_text());exe=OUT/'formatter';r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict formatter compile '+r.stderr[-1800:]);attempts.append('formatter');write(PUBLIC/'attempts.json',dict(native_processes=1,cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300);(PUBLIC/'formatter-stdout.txt').write_text(r.stdout);(PUBLIC/'formatter-stderr.txt').write_text(r.stderr);need(r.returncode==0 and not r.stderr,'formatter rc='+str(r.returncode)+' '+r.stderr[-1200:]);native=json.loads(r.stdout);need(native['status']=='PASS_UNION_FORMATTER_FULL_OWNER_PRESERVATION'and native['cases']==168,'all new72 and changed96 cases');need(candidate.read_bytes()==after,'private ROM unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_ISOLATED_UNION_FORMATTER_PRESERVATION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,isolated=native,native_processes=1,host_tests=8,previous_isolated=accepted,previous_isolated_run=ORIGINAL_RUN,delta_rollback_exact=True,unaffected_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,all_save_modes_accepted=False,all_nonstart_notifications_accepted=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated formatter publication')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'host-tests.txt','build.json','measurement.json','attempts.json','failure.json','formatter-stdout.txt','formatter-stderr.txt'},'closed text only');b=p.read_bytes();need(len(b)<1500000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed formatter action');globals()[sys.argv[1]]()
