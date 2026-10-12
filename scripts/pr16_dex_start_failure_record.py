#!/usr/bin/env python3
"""通常STARTのvalid失敗/手動retry/cold原本を、native再走せず記録。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_start_fault_ui as ui
import pr16_dex_start_failure_actions as gates
need,identity,write=ui.need,ui.identity,ui.write
BASE='78b6af2fd055f492fc28f264f5b3f6bfb7cda498';RUN=37239138134;JOB=111544115505
ARCHIVE=(11315944185,RUN,79269,'9b4906932b3e89f784195bd46fd3c13bebe14c9f15e00882cd6c1e3b5b1d7d9d')
GUIDE='docs/PR16_DEX_START_FAILURE_JA.md';CODE={GUIDE,'scripts/pr16_dex_start_failure_record.py','.github/workflows/pr16-dex-start-failure-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_start_failure_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_start_failure_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-start-failure-record';PUBLIC=ROOT/'public-dex-start-failure-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first record')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable START record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'previous sources unchanged and record terminal')
 r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['status']=='completed'and r['conclusion']=='success'and r['head_sha']==BASE and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'all10 native workflow steps')
 z,_=t.archive(ARCHIVE)
 with z:files={n:z.read(n)for n in z.namelist()}
 need('measurement.json'in files and 'failure.json'not in files,'complete actual UI result');m=json.loads(files['measurement.json']);need(m['status']=='PASS_VALID_START_FAILURE_UI_RETRY_AND_TWO_COLD'and m['source_head']==BASE and m['run_id']==RUN and m['native_processes']==3 and m['ram_fixture_writes']==m['register_writes']==0,'three actual no-RAM-fixture processes')
 for p,b in m['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'exact measured UI sources')
 folder=OUT/'original';folder.mkdir()
 for n,b in files.items():
  p=Path(n);need(not p.is_absolute()and '..'not in p.parts and len(p.parts)<=2,'safe known evidence path');dest=folder/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 previous=ui.PUBLIC
 try:ui.PUBLIC=folder;ui.export()
 finally:ui.PUBLIC=previous
 need(ui.validate_ui(files['fault/stdout.txt'],folder/'fault',m['candidate'])==m['trace'],'independent all-input/state/pixel validation without native')
 need(m['candidate']['sha256']=='d69a1d3c2b2d929ee94523eae00a7e6ce51a11e9a759c179b63f25b5abd7890c'and m['reconstructed_gate']['link']['payload']['size']==192 and m['reconstructed_gate']['placement']['all110_other_owners_byte_identical']and m['reconstructed_gate']['placement']['allocation']['summaries']['overlap_count']==0,'exact candidate and all prior owners')
 need(m['trace']['end']['fault_writes']==1 and m['trace']['end']['fault_physical_address']==16384 and m['trace']['end']['all_extension_bytes_retained_after_fault']==20248,'bounded real program-data fault')
 for c in m['cold']:
  rows=[json.loads(x)for x in files['cold-'+str(c['counter'])+'/stdout.txt'].splitlines()];need([x for x in rows if 'observe'in x]==[c['observation']]and [x for x in rows if 'mdx'in x]==[c['mdx']]and rows[-1]==c['end']and c['input']==c['output'],'whole cold original and FlashRTC identity');need(ui.screens(rows,folder/('cold-'+str(c['counter'])))==c['screens'],'cold pixels exact')
 need([c['counter']for c in m['cold']]==[101,102]and m['cold'][0]['input']==m['failed_save']and m['cold'][1]['input']==m['retried_save'],'failure bank fallback and retry independent cold')
 evidence=ROOT/EVIDENCE;evidence.mkdir();paths=set()
 for n,b in files.items():
  if Path(n).suffix not in{'.json','.txt'}:continue
  dest=evidence/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(dest.relative_to(ROOT).as_posix())
 code=CODE|gates.CODE|ui.CODE
 cp=dict(schema_version=1,status='PASS_CANDIDATE_SAME_SAVE_START_FAULT_KEY_RETRY_COLD',source_head=BASE,run_id=RUN,job_id=JOB,archive=ARCHIVE,candidate=m['candidate'],measurement=m,source_bindings=bindings(code),evidence_bindings=bindings(paths),visual_review=dict(run=RUN,screens=7,first_page='fault/screen-0001.ppm',final_page='fault/screen-0002.ppm',review_ja='同run原本で「レポートが かけませんでした」と最終故障案内、失敗後field/再保存後field/cold101/cold102を目視。全7画像のSHA照合、追加native0。'),same_save_mode0_failure_retry_accepted=True,mode4_actual_retry_accepted=False,outer_qol_sector31_failure_accepted=False,global_save_failed_owner_collision_resolved=False,all_save_modes_accepted=False,all_consumers_wired=False,formal_rom_changed=False,formal_save_changed=False,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0)
 write(ROOT/CP,cp)
 goal=('正式ROM/Save101保持。候補d69a1d3cはSTART実callback限定のvalid-live main Flash故障→通常エラー2頁→field→通常キー再Save101→102と失敗cold101/再保存cold102を受入。'
 '次は外側QOL sector31失敗のgSaveAttemptStatus伝播と、START以外のSaveFailedでtiles16KiB/video-state/gDecompressionBufferを破壊せず失敗を通知する契約。HOF payload/回数増分、mode4/5の28..31erase、stale selector時authority wipe、mode1/2/default/LinkFullを別々に受入する。'
 '続いてactive capture/SetMonPokedexFlags、native授受/孵化/進化、UI/native count、acquisition/research/reward、reward clear、Factory memorial/Codex rollback、DexNavをSID喪失前に接続。'
 '全consumer/必要な全modeと影響native前に正式ROM切替・trainer131後半へ進めない。最終はシオウPokecenter通常回復/Save/coldContinue、雑魚毎Saveなし。')
 state['story_dex_owner']['runtime_integration']['start_save_failure']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=m['candidate'],ui_run=RUN,ui_job=JOB,record_run=int(os.environ['GITHUB_RUN_ID']),same_save_mode0_accepted=True,all_save_modes_accepted=False,outer_qol_failure_unresolved=True,global_save_failed_collision_unresolved=True,formal_save_changed=False)
 state['bp']['current_stop']='正式ROM/Save101保持。candidate-only START mode0のvalid Flash故障・非破壊error・通常キー再保存・両coldを受入。outerQOL/非START専用画面/全mode/残consumerは未完。';state['bp']['next_step']=goal
 state['next_action'].update(id='CLOSE_OUTER_QOL_AND_NONSTART_FAILURE_CONTRACTS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_SAVE_FAILURE_JA.md','docs/PR16_DEX_CONSUMERS_JA.md'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='candidate-only START valid Flash fault/retry/cold記録source。正式ROM/Save101不変。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(code|paths|{CP}));state['do_not_repeat'].append(f'START valid失敗: gate run37238699272は1120case必須assert成功だがupload path誤記によりraw measurementなし。原本欠落を隠さず再走0。run{RUN}の192byte gate全再構成/同candidate、1Flash故障/818入力/5画面とcold101の16入力/cold102の12入力、計3process7画面を無変更再走しない。全mode/outerQOL/非STARTへ受入拡張しない。')
 state['observed_head_checks']=dict(scope_head=BASE,native_run=RUN,native_job=JOB,all10_steps_success=True,native_processes=3,gate_prior_run=37238699272,gate_asserted_cases=1120,gate_raw_measurement_available=False,all_save_modes_accepted=False,all_consumers_wired=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=state['bp']['current_stop'])
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-START-FAILURE / valid START main保存故障と通常キー再試行\n- Version: dex-start-failure-v1\n- Status: DONE（same-save mode0限定。全mode/非START/outerQOL未完）\n- Summary: 実START callback＋mode0/4だけ通常errorへ返す192byte gate。元110owner全byte、111allocation/overlap0。valid MDXでFlash PROGRAM1address/XOR1故障をCPUが検出し、old SaveFailedを避ける。\n- Files changed: START gate/source/署名/native、fault driver、guide/CP/evidence、固定MDJSON、両ログ。\n- Verify: gate1120case必須assert成功、upload path誤記でraw原本なしを明記。run{RUN}/job{JOB}全10step・3process・7画像・RAM/register fixture0・20248byte拡張owner保持・source bank/aux保全・エラー2頁/別A復帰・キー再Save101→102・失敗cold101/再保存cold102のFlashRTC全byte保持。記録native0。\n- Boundary: HOF返値無視とdecompression payload衝突/重複副作用、mode4失敗後flag clear、valid MDXでもstale selectorによるauthority wipe、outerQOL sector31失敗status未伝播を独立未完として記録。正式ROM/Save101不変、trainer131後半0。\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions・既存入力・固定mGBA一次source・公式Ubuntu compiler。公開source/address-size-SHA/text/screensのみ。ROM/入力save/runtime/runner/credential追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'all prior accepted sources retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'start-failure-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'complete committed readback')
 print('RESULT=DONE TASK=USER-20261004-DEX-START-FAILURE VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated receipt')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name=='start-failure-record.json','exact JSON only');b=p.read_bytes();need(0<len(b)<500000 and b.endswith(b'\n')and b'\0'not in b,'complete UTF8');json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed record');globals()[sys.argv[1]]()
