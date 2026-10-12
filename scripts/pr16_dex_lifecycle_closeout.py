#!/usr/bin/env python3
"""Close the terminal lifecycle record; no rebuild, host test or native rerun."""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
from pr16_dex_lifecycle_actions import need,identity,write
BASE='b67ecf975da589f36f50943a14fb718058a88f20';SOURCE='5860c3d2c5fcd8edb98f999178fc690e9775140a'
RUN=37232613702;JOB=111525319786;ARCHIVE=(11313869049,RUN,21306,'7ed5885de00d2ca3dbd2b87975dd34b80dec45cc44517bd49796583a1d8060ae')
WF='.github/workflows/pr16-dex-lifecycle-record.yml'
CODE={'scripts/pr16_dex_lifecycle_closeout.py','.github/workflows/pr16-dex-lifecycle-closeout.yml',WF}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_lifecycle_checkpoint.json'
LOGS={'design/run_log.md','design/version_log.md'};OUT=ROOT/'.local/pr16-dex-lifecycle-closeout';PUBLIC=ROOT/'public-dex-lifecycle-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized closeout branch')
 p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists(),'one closeout');OUT.mkdir(parents=True);PUBLIC.mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 for p,b in protected.items():
  if p!=WF:need(identity((ROOT/p).read_bytes())==b,'retained source '+p)
 old=git('show',BASE+':'+WF);new=(ROOT/WF).read_bytes()
 trigger=b'  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: [.github/workflows/pr16-dex-lifecycle-record.yml]\n'
 need(identity(old)==protected[WF]and old.count(trigger)==1 and new==old.replace(trigger,b'  workflow_dispatch:\n'),'completed record made manual-only, nothing else changed')
 r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
 need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'terminal exact record run')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'all12 record steps successful')
 z,_=transport.archive(ARCHIVE)
 with z:need(z.namelist()==['lifecycle-record.json'],'one exact public record receipt');raw=z.read('lifecycle-record.json')
 need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole record artifact equals committed checkpoint')
 cp=json.loads(raw);need(cp['isolated']['run']==37230810454 and cp['isolated']['native']['cases']==52 and cp['gameplay']['run']==37231996230 and cp['gameplay']['measurement']['accepted_native_processes']==4 and cp['ordinary_save_continue_accepted']is True,'unchanged scoped lifecycle acceptance')
 for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'whole original lifecycle evidence')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only finished record pending');state['pending_runs']=[]
 receipt=dict(status='PASS_TERMINAL_RECORD_AND_WHOLE_ARTIFACT_READBACK',run=RUN,job=JOB,source=SOURCE,completion=BASE,all12_steps_success=True,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],artifact_equals_committed_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['load_newgame']['recording']=receipt
 state['observed_head_checks']=dict(scope_head=SOURCE,lifecycle_run=37231996230,record_run=RUN,all12_record_steps_success=True,general_ci_known_source_mismatch_not_resolved=True,gameplay_accepted=True,all_consumers_wired=False,reason_ja='候補限定のload/newgame接続、隔離ARM52case、通常Save101移行とNewGame初回Save/独立coldを受入。受入4processのうち原本3再利用＋新cold1、記録native0。画像6枚正常と追加無入力4画面、全SaveRTC保持を確認。record全12stepとartifact/commit checkpointを全byte照合。正式ROM/Save101不変。全consumer、全mode固有副作用、実失敗UIは未完。一般CI既知QOL source不一致、Stage79 cacheは新nativeではない。')
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-LIFECYCLE / 図鑑load/newgame保存記録終端\n- Version: dex-lifecycle-v1-closeout\n- Status: DONE（候補通常lifecycleの記録終端。全consumer等は次工程）\n- Summary: record run{RUN}/job{JOB}全12step成功。artifact{ARCHIVE[0]}のreceiptとcommit checkpointを全byte照合し、pendingを解除。完了記録はmanual-onlyへ移す。\n- Files changed: closeout source/workflow、record起動条件、固定MDJSON、両ログ。\n- Verify: artifact/固定state/source binding/index/task graph PASS。host再試験0/ARM0/native0/正式ROM・Save変更0。元scheduler/codec/44export保持、追加wrapper188byte、allocator109owner/overlap0。正常fallback維持/無効MDXはglobal2でContinue遮断、newgame tailを接続。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/commit/既存text artifactのみ。一般CI既知QOL不一致、Stage79 cache、旧9月18日queue非操作を保持。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 for p,b in protected.items():
  if p!=WF:need(identity((ROOT/p).read_bytes())==b,'all unaffected sources exact')
 (PUBLIC/'lifecycle-record.json').write_bytes(raw);write(PUBLIC/'lifecycle-closeout.json',receipt)
 owned={STATE,*LOGS}
 if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole final committed text readback')
 print('RESULT=STOPPED TASK=USER-20261004-DEX-LIFECYCLE VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in {'lifecycle-record.json','lifecycle-closeout.json'},'only explicit regular receipts');raw=p.read_bytes();need(0<len(raw)<200000 and raw.endswith(b'\n')and b'\0'not in raw,'complete bounded JSON');json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'bounded action');globals()[sys.argv[1]]()
