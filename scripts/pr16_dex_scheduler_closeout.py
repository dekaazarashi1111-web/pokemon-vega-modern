#!/usr/bin/env python3
"""Close the terminal scheduler record; no rebuild, host test or native rerun."""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
from pr16_dex_scheduler_actions import need,identity,write
BASE='5674f6e89d099eafa8938d7dd04fee27451fcdb0';SOURCE='b65b53e70895c124e9d00709f47fc0c66a7b07d5'
RUN=37228900963;JOB=111514202531;ARCHIVE=(11312448019,RUN,19454,'974a8914a71ec3b2a15bc7ec3d8daacb6613658a3d8697e1cc6302da7b8511b2')
WF='.github/workflows/pr16-dex-scheduler-record.yml'
CODE={'scripts/pr16_dex_scheduler_closeout.py','.github/workflows/pr16-dex-scheduler-closeout.yml',WF}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_scheduler_checkpoint.json'
LOGS={'design/run_log.md','design/version_log.md'};OUT=ROOT/'.local/pr16-dex-scheduler-closeout';PUBLIC=ROOT/'public-dex-scheduler-closeout'
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
 trigger=b'  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: [.github/workflows/pr16-dex-scheduler-record.yml]\n'
 need(identity(old)==protected[WF]and old.count(trigger)==1 and new==old.replace(trigger,b'  workflow_dispatch:\n'),'completed record made manual-only, nothing else changed')
 r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
 need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'terminal exact record run')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'all12 record steps successful')
 z,_=transport.archive(ARCHIVE)
 with z:need(z.namelist()==['scheduler-record.json'],'one exact public record receipt');raw=z.read('scheduler-record.json')
 need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole record artifact equals committed checkpoint')
 cp=json.loads(raw);need(cp['run']==37228557062 and cp['accepted_native_processes']==1 and cp['isolated_arm']['cases']==19,'unchanged measured acceptance')
 for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'whole original scheduler evidence')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only finished record pending');state['pending_runs']=[]
 receipt=dict(status='PASS_TERMINAL_RECORD_AND_WHOLE_ARTIFACT_READBACK',run=RUN,job=JOB,source=SOURCE,completion=BASE,all12_steps_success=True,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],artifact_equals_committed_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['save_scheduler']['recording']=receipt
 state['observed_head_checks']=dict(scope_head=SOURCE,scheduler_run=37228557062,record_run=RUN,all12_record_steps_success=True,general_ci_known_source_mismatch_not_resolved=True,gameplay_accepted=False,reason_ja='保存scheduler候補は全10step、18generator/20host/19隔離ARM/36calls、EWRAM non-ownerとSP/r4-r11を限定受入。record全12stepとartifact/commit checkpointの全byteを照合。正式ROM/Save101不変。通常保存・新規ゲーム・外側load gate・全consumerは未完。一般CI既知QOL source不一致、Stage79 cacheは新nativeではない。')
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-SCHEDULER / 保存scheduler記録終端\n- Version: dex-save-scheduler-v1-closeout\n- Status: DONE（候補の隔離ARM記録終端。通常game受入は次工程）\n- Summary: record run{RUN}/job{JOB}全12step成功。artifact{ARCHIVE[0]}のreceiptとcommit checkpointを全byte照合し、pendingを解除。完了記録はmanual-onlyへ移す。\n- Files changed: closeout source/workflow、record起動条件、固定MDJSON、両ログ。\n- Verify: artifact/固定state/source binding/index/task graph PASS。host再試験0/ARM0/native0/正式ROM・Save変更0。元44export/非保存code/dataを保持、実配置8264byte、追加lease1084byte、allocator108owner/overlap0。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/commit/既存text artifactのみ。一般CI既知QOL不一致、Stage79 cache、旧9月18日queue非操作を保持。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 for p,b in protected.items():
  if p!=WF:need(identity((ROOT/p).read_bytes())==b,'all unaffected sources exact')
 (PUBLIC/'scheduler-record.json').write_bytes(raw);write(PUBLIC/'scheduler-closeout.json',receipt)
 owned={STATE,*LOGS}
 if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole final committed text readback')
 print('RESULT=STOPPED TASK=USER-20261004-DEX-SCHEDULER VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in {'scheduler-record.json','scheduler-closeout.json'},'only explicit regular receipts');raw=p.read_bytes();need(0<len(raw)<200000 and raw.endswith(b'\n')and b'\0'not in raw,'complete bounded JSON');json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'bounded action');globals()[sys.argv[1]]()
