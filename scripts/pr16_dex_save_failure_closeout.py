#!/usr/bin/env python3
"""終端record/全byte読戻し。host/ARM/nativeは再実行しない。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
from pr16_dex_save_failure_actions import need,identity,write
BASE='57dedac5b94b9cb6a17282265e61c523530467c8';SOURCE='4ede9c47c6bf8dc9b5ff9441b3daeeff5656e20e'
RUN=37237246747;JOB=111538731599;ARCHIVE=(11316201657,RUN,38484,'80ca6e47fa0f6511b692cb643197a9b86d4b687510be1d410482c40ec4590100')
WFS={'.github/workflows/pr16-dex-battle-record.yml','.github/workflows/pr16-dex-save-failure-record.yml'}
CODE=WFS|{'scripts/pr16_dex_save_failure_closeout.py','.github/workflows/pr16-dex-save-failure-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_save_failure_checkpoint.json';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-save-failure-closeout';PUBLIC=ROOT/'public-dex-save-failure-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized one closeout')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists(),'one closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 for p,b in protected.items():
  if p not in WFS:need(identity((ROOT/p).read_bytes())==b,'every retained source '+p)
 for p in WFS:
  old=git('show',BASE+':'+p);new=(ROOT/p).read_bytes();trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+p+']\n').encode();need(identity(old)==protected[p]and old.count(trigger)==1 and new==old.replace(trigger,b'  workflow_dispatch:\n'),'only completed record trigger becomes manual')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'exact terminal record')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'all12 record steps success')
 z,_=t.archive(ARCHIVE)
 with z:need(z.namelist()==['save-failure-record.json'],'one exact record receipt');raw=z.read('save-failure-record.json')
 need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole receipt equals committed CP including newline')
 cp=json.loads(raw);need(cp['candidate']['sha256']=='d3dcb55ad09a509fa247e65a3ca3db1de4bdd5b5534288b2b03ddbacca65b314'and cp['updated_gates']['measurement']['native']['cases']==108 and cp['ordinary_error_ui']['spec']['run']==37236898977 and cp['invalid_live_save_error_accepted']and cp['valid_live_save_failed_owner_collision_unresolved']and not cp['all_consumers_wired']and not cp['all_save_modes_accepted'],'bounded accepted/remaining scope unchanged')
 for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'whole retained native evidence '+p)
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only finished record pending');state['pending_runs']=[]
 receipt=dict(status='PASS_TERMINAL_DEX_CONSUMER_AND_INVALID_SAVE_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all12_record_steps_success=True,record_artifact=ARCHIVE[0],record_archive_size=ARCHIVE[2],record_archive_sha256=ARCHIVE[3],record_receipt_equals_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['save_failure']['recording']=receipt
 state['observed_head_checks']=dict(scope_head=SOURCE,consumer_run=37233960024,isolated_save_failure_run=37234821383,updated_gates_run=37235903199,ordinary_error_ui_run=37236898977,record_run=RUN,all12_record_steps_success=True,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,all_consumers_wired=False,all_save_modes_accepted=False,reason_ja='candidate-only battle seen5/公式countとinvalid-live非破壊通常エラーを限定受入。旧SaveFailedのtiles/video-state衝突を原本保持し、valid-live失敗/全mode/残consumerは未完。UIの第一頁画像だけ同候補先行原本を再利用、最終頁/fieldは成功原本。全FlashRTC不変、record12step/receiptCP全byte一致。正式ROM/Save101保持。')
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-CONSUMERS / 図鑑consumerと保存拒否記録終端\n- Version: dex-consumers-save-failure-closeout\n- Status: STOPPED（安全な候補限定受入点、全consumer/全modeは未完）\n- Summary: 保存失敗record run{RUN}/job{JOB}全12stepとartifact{ARCHIVE[0]}のCP全byte一致を確認しpending解除。完了したconsumer/failure recordをmanual-onlyへ。\n- Files changed: closeout source/workflow、2record起動条件、固定MDJSON、両ログ。\n- Verify: 固定state/source binding/全evidence/index/task graph PASS、host再試験0/ARM0/native0。source差分ごとのconsumer180/初期失敗152/変更gate＋oracle108/実UI1を記録済み。画像第一頁は同候補先行原本を再利用し追加native0。\n- Boundary: 正式ROM/Save101不変。次はvalid-live専用SaveFailedのtiles/video-state owner衝突、全mode固有副作用/実retryと残typed consumer。通常story/trainer131後半はまだ進めない。一般CI既知QOL source不一致、Stage79cache、旧9月18日queue非操作を保持。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存text artifactとcommitのみ。ROM/save/runtime/runner/credentials追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 for p,b in protected.items():
  if p not in WFS:need(identity((ROOT/p).read_bytes())==b,'all unaffected accepted sources remain exact')
 write(PUBLIC/'closeout.json',receipt);(PUBLIC/'fixed-checkpoint.json').write_bytes(raw);(PUBLIC/'fixed-state.json').write_bytes((ROOT/STATE).read_bytes());(PUBLIC/'fixed-resume.md').write_bytes((ROOT/DOC).read_bytes())
 owned={STATE,*LOGS}
 if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole final committed text')
 receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for short,p in [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP)]:
  raw=git('show','HEAD:'+p);need(raw==(PUBLIC/short).read_bytes(),'whole artifact fixed snapshot equals HEAD including newline');receipt['final_blobs'][p]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=raw.endswith(b'\n'))
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261004-DEX-CONSUMERS VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public text snapshot directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json','fixed-state.json','fixed-checkpoint.json','fixed-resume.md'},'only explicit regular committed text or receipt')
  raw=p.read_bytes();limit=3500000 if p.name=='fixed-state.json'else 500000;need(0<len(raw)<limit and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete UTF8 source text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed action');globals()[sys.argv[1]]()
