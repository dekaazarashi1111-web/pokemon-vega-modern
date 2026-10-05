#!/usr/bin/env python3
"""mode3 main記録の終端と固定正本全byteを確認。native/ARM/host再走0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
from pr16_dex_hof_main_ui import need,identity,write
BASE='c5282ebe037f11b5773cca458741dcc9533e6f53';SOURCE='3227331bb38b807822ed9f7da8ea197b09269418';RUN=37267010828;JOB=111625848719;ARCHIVE=(11327160720,RUN,58657,'3746c89741f98483a7e9270cd8c2b1cb766f2df5825856745dd6c56c4dfc0a76')
WF='.github/workflows/pr16-dex-hof-main-record.yml';CODE={WF,'scripts/pr16_dex_hof_main_closeout.py','.github/workflows/pr16-dex-hof-main-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_hof_main_checkpoint.json';GUIDE='docs/PR16_DEX_HOF_MAIN_COW_JA.md';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-hof-main-closeout';PUBLIC=ROOT/'public-dex-hof-main-closeout'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized closeout');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
def source_guard():
 import pr16_learnset_runtime_record as g,pr16_dex_publication as publication
 current();publication.contract(ROOT,'.github/workflows/pr16-dex-hof-main-closeout.yml',PUBLIC,'pr16-dex-hof-main-closeout-receipts','scripts/pr16_dex_hof_main_closeout.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume,pr16_dex_publication as publication
 current();need(not OUT.exists(),'one closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 for p,b in protected.items():
  if p!=WF:need(identity((ROOT/p).read_bytes())==b,'every protected source retained '+p)
 old=git('show',BASE+':'+WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+WF+']\n').encode();need(identity(old)==protected[WF]and old.count(trigger)==1 and(ROOT/WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'completed record now manual-only')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1 and j['run_id']==RUN and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'record terminal all12 success')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),'pr16-dex-hof-main-record-receipts',RUN);z,_=t.archive(ARCHIVE)
 with z:need(z.namelist()==['hof-main-record.json'],'one exact receipt');raw=z.read('hof-main-record.json')
 need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole checkpoint equals original record');cp=json.loads(raw)
 need(cp['candidate']['sha256']=='88be88116bd452bd70cffaf2a820d5c6c6b6b7410fa603a9a0228b694725d5de'and cp['isolated']['isolated']['cases']==554 and cp['isolated']['link']['payload_bytes']==180 and cp['all_previous_owners']==115 and cp['unchanged_previous_owners']==114 and cp['current_build']['placement']['allocation']['summaries']['allocation_count']==115,'exact limited mode3 candidate and whole previous lineage')
 need(cp['accepted_raw_native_processes']==11 and cp['diagnostic_native_processes']==0 and cp['ui']['native_processes']==10 and cp['visual_review']['screens']==25 and cp['current_scheduler_free_bytes']==186,'complete native and actual subowner accounting')
 need(not any(cp[k]for k in('all_cold_owners_preserved','sector31_atomicity','initial_hof_atomicity','hof_main_generation_binding','all_save_modes','common_failure_all_callers','all_typed_consumers','formal_rom_changed','formal_save_changed')),'no scope promotion')
 need(cp['source_bindings'][GUIDE]==identity((ROOT/GUIDE).read_bytes())==state['source_bindings'][GUIDE],'final GUIDE matches CP and current state')
 for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'every immutable raw evidence byte')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only record pending');state['pending_runs']=[]
 receipt=dict(status='PASS_TERMINAL_HOF_MAIN_COW_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all12_record_steps_success=True,record_archive=ARCHIVE,record_receipt_equals_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['hof_main_cow']['recording']=receipt;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all12_record_steps_success=True,whole_receipt_equals_checkpoint=True)
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-MAIN-COW / mode3記録の終端\n- Version: dex-hof-main-cow-closeout\n- Status: STOPPED（mode3 main保護とHOF失敗短絡の限定受入点。世代結合/全mode/共通残caller未完）\n- Summary: record run{RUN}/job{JOB}全12stepとartifact{ARCHIVE[0]}のcheckpoint全byte一致を確認しpending解除。新native/record workflowはmanual-onlyへ。\n- Files changed: closeout source/workflow、record起動条件、固定MDJSONと両ログ。\n- Verify: 全source/evidence/fixed resume/index/task graph PASS。追加host0/ARM0/native0。原本はARM554/host7suite＋影響1suite、UI4suite、5UI/各cold10process/25画像。受入native計11、診断0。\n- Lineage: d773a123から88be8811へ。既存115owner中114全byte不変、Stage61内の実空き5窓180byteとstock mode3 row4byteだけ。115/overlap0/全ROM逆変換。元scheduler再link0・新tail0、現subownerを除いた残186byte。旧366byteは履歴。\n- Boundary: HOF28故障は29/mainを呼ばず、29故障はmainを呼ばない。主故障も旧14sector/cold101を保護し、正常/outer末尾はcold102。5coldでQOL2048byteは物理一致。HOF/main世代bindingと全体原子性、全mode/共通残caller/early31/全cold owner/typedconsumerは未完。正式ROM/Save101不変、trainer131後半0。一般CI既知QOL不一致/Stage79cache/旧9月18日queueは別扱い。\n- Next: HOF28/29とmainの世代結合・原子性へ。最新115ownerとcurrent_scheduler_subownersを優先。最終はシオウ通常回復/保存/cold Continue、雑魚毎Saveなし。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repo Actions/既存text receiptだけ。ROM/入力save/runtime/runner/credential追加公開0。\n'

 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 write(PUBLIC/'closeout.json',receipt)
 for name,p in SNAPSHOTS:(PUBLIC/name).write_bytes((ROOT/p).read_bytes())
 owned={STATE,*LOGS}
 if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'complete committed source')
 receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for name,p in SNAPSHOTS:
  b=git('show','HEAD:'+p);need(b==(PUBLIC/name).read_bytes()and b.endswith(b'\n'),'complete artifact versus committed text including newline');receipt['final_blobs'][p]=dict(**identity(b),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=True)
 for p in LOGS:need(git('show','HEAD:'+p).startswith(git('show',BASE+':'+p)),'every old log byte preserved as prefix')
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-MAIN-COW VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC,success='closeout.json',failure=None)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json',*(n for n,_ in SNAPSHOTS)},'only explicit whole-source snapshots');b=p.read_bytes();need(0<len(b)<(3500000 if p.name in('fixed-state.json','fixed-run-log.md','fixed-version-log.md')else 1500000)and b.endswith(b'\n')and b'\0'not in b,'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed closeout');globals()[sys.argv[1]]()
