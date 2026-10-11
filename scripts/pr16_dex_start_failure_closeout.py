#!/usr/bin/env python3
"""START限定の終端record・固定MDJSON全byte照合。native/ARM/host再走0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
from pr16_dex_start_failure_actions import need,identity,write
BASE='4d6243ea1863f8e15990dc9b6d0ac95552837a04';SOURCE='01aa0c98cd4ba0367d9200bb2cbf62fc3968f4aa'
RUN=37239484032;JOB=111545113352;ARCHIVE=[11317305248,37239484032,20500,"fdde0ddc81734c2312f5b389fb1b0827aea38205dce849c73f20c44e58017d3f"]
WFS={'.github/workflows/pr16-dex-start-fault-ui.yml','.github/workflows/pr16-dex-start-failure-record.yml'}
CODE=WFS|{'scripts/pr16_dex_start_failure_closeout.py','.github/workflows/pr16-dex-start-failure-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_start_failure_checkpoint.json';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-start-failure-closeout';PUBLIC=ROOT/'public-dex-start-failure-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized closeout')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists(),'one closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 for p,b in protected.items():
  if p not in WFS:need(identity((ROOT/p).read_bytes())==b,'all accepted sources retained '+p)
 for p in WFS:
  old=git('show',BASE+':'+p);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+p+']\n').encode();need(identity(old)==protected[p]and old.count(trigger)==1 and(ROOT/p).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'only completed triggers made manual')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1 and j['run_id']==RUN and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'record all12 steps terminal')
 z,_=t.archive(ARCHIVE)
 with z:need(z.namelist()==['start-failure-record.json'],'one record receipt');raw=z.read('start-failure-record.json')
 need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'complete record artifact equals committed checkpoint')
 cp=json.loads(raw);need(cp['candidate']['sha256']=='d69a1d3c2b2d929ee94523eae00a7e6ce51a11e9a759c179b63f25b5abd7890c'and cp['measurement']['native_processes']==3 and cp['same_save_mode0_failure_retry_accepted']and not cp['all_save_modes_accepted']and not cp['all_consumers_wired']and not cp['global_save_failed_owner_collision_resolved'],'scope preserved')
 for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'all evidence whole bytes')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'one actually completed record pending');state['pending_runs']=[]
 receipt=dict(status='PASS_TERMINAL_START_FAULT_RETRY_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all12_record_steps_success=True,record_artifact=ARCHIVE[0],record_archive_size=ARCHIVE[2],record_archive_sha256=ARCHIVE[3],record_receipt_equals_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['start_save_failure']['recording']=receipt
 state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all12_record_steps_success=True,whole_receipt_equals_checkpoint=True)
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-START-FAILURE / valid START故障記録の終端\n- Version: dex-start-failure-closeout\n- Status: STOPPED（安全な候補限定受入点。非START/outerQOL/全mode/残consumer未完）\n- Summary: record run{RUN}/job{JOB}全12stepとartifact{ARCHIVE[0]}のcheckpoint全byte一致を確認しpending解除。成功したUI/recordの自動triggerをmanual-onlyへ。\n- Files changed: closeout source/workflow、2workflow起動条件、固定MDJSON、両ログ。\n- Verify: 全evidence/source/fixed resume/index/task graph PASS、host再試験0/ARM0/native0。前runのfault1/818入力/5画面＋cold16/12入力/2画面、3process原本を再利用。正式ROM/Save101不変。\n- Boundary: 次はouterQOL sector31失敗attempt伝播と非START保存失敗通知/退避/副作用契約、全modeと残typed consumer。trainer131後半は未実行。既知一般CI QOL不一致・Stage79cache・旧9月18日queueは区別。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActionsと既存text receiptのみ。ROM/入力save/runtime/runner/credential追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 write(PUBLIC/'closeout.json',receipt);(PUBLIC/'fixed-checkpoint.json').write_bytes(raw);(PUBLIC/'fixed-state.json').write_bytes((ROOT/STATE).read_bytes());(PUBLIC/'fixed-resume.md').write_bytes((ROOT/DOC).read_bytes());owned={STATE,*LOGS}
 if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole final committed text')
 receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for n,p in [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP)]:
  b=git('show','HEAD:'+p);need(b==(PUBLIC/n).read_bytes(),'whole artifact and remote-bound HEAD exact including newline');receipt['final_blobs'][p]=dict(**identity(b),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=b.endswith(b'\n'))
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261004-DEX-START-FAILURE VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated source-only snapshots')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json','fixed-state.json','fixed-checkpoint.json','fixed-resume.md'},'explicit source snapshots only');b=p.read_bytes();need(0<len(b)<(3500000 if p.name=='fixed-state.json'else 500000)and b.endswith(b'\n')and b'\0'not in b,'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed action');globals()[sys.argv[1]]()
