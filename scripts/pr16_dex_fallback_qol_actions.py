#!/usr/bin/env python3
"""fallback専用新sourceをcompile。容量・純粋validator監査前には配置/実行しない。"""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_fallback_qol as f
need,identity=f.need,f.identity
BASE='f7a70dfa1f037f1824aeb4fc18a62f10fe11f0db'
WF='.github/workflows/pr16-dex-fallback-qol.yml';GUIDE='docs/PR16_DEX_FALLBACK_QOL_JA.md'
CODE={f.SOURCE,'scripts/pr16_dex_fallback_qol.py','scripts/pr16_dex_fallback_qol_actions.py','tools/mgba_pr16_dex_fallback_qol.h','tests/test_pr16_dex_fallback_qol.py',WF,GUIDE}
OUT=ROOT/'.local/pr16-dex-fallback-qol';PUBLIC=ROOT/'public-dex-fallback-qol';ARTIFACT='pr16-dex-fallback-qol-text-only'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def guard():
 import pr16_story_live_probe as t,pr16_dex_publication as publication
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_fallback_qol_actions.py')
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current first run');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
 need(set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())==CODE,'exact new fallback sources')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'prior native terminal')
 for p,b in state['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'every previously bound source retained '+p)
def run():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh compile-only run');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_fallback_qol.py','-v'],cwd=ROOT,capture_output=True);need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==1,'new fallback host matrix');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
  payload,linked=f.link(OUT/'link');write(PUBLIC/'measurement.json',dict(status='COMPILED_FALLBACK_NOT_PLACED_NOT_ACCEPTED',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),link=linked,host_cases=327693,native_processes=0,rom_writes=0,save_writes=0,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=0));raise
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'host-tests.txt','measurement.json','failure.json'},'closed regular text only');b=p.read_bytes();need(len(b)<100000 and b'\0'not in b and(not b or b.endswith(b'\n')),'bounded UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed fallback action');globals()[sys.argv[1]]()
