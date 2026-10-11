#!/usr/bin/env python3
"""fallback記録の終端と固定正本全byteを確認。native/ARM/host再走0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
from pr16_dex_fallback_cold import need,identity,write
BASE='953d6c3e967554f37f5e34c849faa4228ed73015';SOURCE='4ca18a66618571137d120091a45607937fcb6e67';RUN=37261371891;JOB=111609123964;ARCHIVE=(11325430266,RUN,56682,'6a883ef7029f9ea7d723a72c0f1b7eb4eb3e46a88675b20d5c70d64e2887d9a0')
WF='.github/workflows/pr16-dex-fallback-record.yml';CODE={WF,'scripts/pr16_dex_fallback_closeout.py','.github/workflows/pr16-dex-fallback-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_fallback_checkpoint.json';GUIDE='docs/PR16_DEX_FALLBACK_QOL_JA.md';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-fallback-closeout';PUBLIC=ROOT/'public-dex-fallback-closeout'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized closeout');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
def source_guard():
 import pr16_learnset_runtime_record as g,pr16_dex_publication as publication
 current();publication.contract(ROOT,'.github/workflows/pr16-dex-fallback-closeout.yml',PUBLIC,'pr16-dex-fallback-closeout-receipts','scripts/pr16_dex_fallback_closeout.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume,pr16_dex_publication as publication
 current();need(not OUT.exists(),'one closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 for p,b in protected.items():
  if p!=WF:need(identity((ROOT/p).read_bytes())==b,'every protected source retained '+p)
 old=git('show',BASE+':'+WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+WF+']\n').encode();need(identity(old)==protected[WF]and old.count(trigger)==1 and(ROOT/WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'completed record now manual-only')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1 and j['run_id']==RUN and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'record terminal all12 success')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),'pr16-dex-fallback-record-receipts',RUN);z,_=t.archive(ARCHIVE)
 with z:need(z.namelist()==['fallback-record.json'],'one exact receipt');raw=z.read('fallback-record.json')
 need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole checkpoint equals original record');cp=json.loads(raw)
 need(cp['candidate']['sha256']=='d773a1232c31fcb5629785278c2ad6e6d46208dbc62a55d66167fba7a2a38670'and cp['isolated']['isolated']['cases']==508 and cp['isolated']['link']['payload']['size']==296 and cp['all_previous_owners']==114 and cp['unchanged_previous_owners']==113 and cp['current_build']['placement']['allocation']['summaries']['allocation_count']==115,'exact limited candidate and whole prior lineage')
 need(cp['accepted_raw_native_processes']==4 and cp['diagnostic_native_processes']==2 and cp['intermediate_boot_title_native_processes']==2 and cp['total_native_processes']==8,'complete native accounting including intermediate title/intro')
 need(not any(cp[k]for k in('all_cold_owners_preserved','sector31_generation_binding','sector31_atomicity','initial_hof_atomicity','all_save_modes','common_failure_all_callers','all_typed_consumers','formal_rom_changed','formal_save_changed')),'no scope promotion')
 need(cp['source_bindings'][GUIDE]==identity((ROOT/GUIDE).read_bytes())==state['source_bindings'][GUIDE],'final GUIDE matches CP and current state')
 for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'every immutable raw evidence byte')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only record pending');state['pending_runs']=[]
 receipt=dict(status='PASS_TERMINAL_FALLBACK_QOL_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all12_record_steps_success=True,record_archive=ARCHIVE,record_receipt_equals_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['fallback_qol']['recording']=receipt;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all12_record_steps_success=True,whole_receipt_equals_checkpoint=True)
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-FALLBACK-QOL / fallback台帳記録の終端\n- Version: dex-fallback-qol-closeout\n- Status: STOPPED（安全なidle台帳限定受入点。初回mode3/全mode/共通残caller/全cold owner未完）\n- Summary: record run{RUN}/job{JOB}全12stepとartifact{ARCHIVE[0]}のcheckpoint全byte一致を確認しpending解除。新native/recordはmanual-onlyへ。\n- Files changed: closeout source/workflow、record起動条件、固定MDJSONと両ログ。\n- Verify: 全source/evidence/fixed resume/index/task graph PASS。追加host0/ARM0/native0。原本はARM508/host327907、正常/片bank故障/破損cold3case、3画像。acceptedraw4＋diagnostic2＋intro/title中間2＝native総8。\n- Lineage: HOF40ad8237からd773a123へ。既存114owner全部継承、113全byte不変、Mirage参照4byteのみ変更、新296byte追加で115/overlap0。残tailは0x09FFFEEC以降276byte。古い572byte空き表示を使わない。\n- Boundary: fallback255の有効v2/idle durable QOL2048byteのみ。全cold owner・main世代binding/sector31原子性/初回HOF保存/全mode/共通残caller/typedconsumerは未完。正式ROM/Save101不変、trainer131後半0。一般CI既知QOL source不一致/Stage79cache/旧9月18日queueは別扱い。\n- Next: 初回mode3 HOF28/29とmainの保存契約へ。最新115ownerと実sectionを先に再照合。最終はシオウ通常回復/保存/cold Continue、雑魚毎Saveなし。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repo Actions/既存text receiptだけ。ROM/入力save/runtime/runner/credentials追加公開0。\n'
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
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-FALLBACK-QOL VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC,success='closeout.json',failure=None)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json',*(n for n,_ in SNAPSHOTS)},'only explicit whole-source snapshots');b=p.read_bytes();need(0<len(b)<(3500000 if p.name in('fixed-state.json','fixed-run-log.md','fixed-version-log.md')else 1500000)and b.endswith(b'\n')and b'\0'not in b,'bounded complete UTF8');b.decode('utf8')
  if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed closeout');globals()[sys.argv[1]]()
