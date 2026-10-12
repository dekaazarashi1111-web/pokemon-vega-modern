#!/usr/bin/env python3
"""HOF世代contractの新host実装だけを検証・記録。実ROM/native/ARMは0。"""
import datetime, io, json, os, subprocess, sys, unittest
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests'), str(ROOT)]
import pr16_dex_hof_capacity as capacity
import pr16_dex_publication as publication
need, identity = capacity.need, capacity.identity
BASE = 'e7bf7ff1ab85c37744d1cffe86fa2d67fe32486a'
WF = '.github/workflows/pr16-dex-hof-generation.yml'
GUIDE = 'docs/PR16_DEX_HOF_GENERATION_CONTRACT_JA.md'
CODE = {WF, GUIDE, 'scripts/pr16_dex_hof_transaction.py', 'scripts/pr16_dex_hof_capacity.py', 'scripts/pr16_dex_hof_generation_actions.py', 'tests/test_pr16_dex_hof_transaction.py'}
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP = 'content/modernization/pr16_dex_hof_generation_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_dex_hof_generation_evidence'
LOGS = {'design/run_log.md','design/version_log.md'}
OUT = ROOT/'.local/pr16-dex-hof-generation'; PUBLIC = ROOT/'public-dex-hof-generation'
ARTIFACT = 'pr16-dex-hof-generation-text-only'
SNAPSHOTS = [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]

def write(path, value):
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)

def bindings(paths): return {p:identity((ROOT/p).read_bytes()) for p in sorted(paths)}

def current():
 import pr16_story_live_probe as t
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','exact first authorized branch run')
 p=t.api('pulls/16'); need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft source')

def source_guard():
 import pr16_learnset_runtime_record as g
 current(); publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_generation_actions.py')
 g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[],'all predecessor runs terminal')
 need(bindings(state['source_bindings'])==state['source_bindings'],'every previously bound byte unchanged')
 capacity.audit()

def run():
 import test_pr16_dex_hof_transaction as tests
 current();need(not OUT.exists() and not PUBLIC.exists(),'fresh host-only observation');OUT.mkdir(parents=True);PUBLIC.mkdir()
 stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
 (PUBLIC/'host-tests.txt').write_text(stream.getvalue())
 need(result.wasSuccessful() and result.testsRun==21,'21 new host source contracts')
 audit=capacity.audit();write(PUBLIC/'capacity.json',audit)
 metrics=tests.MEASUREMENTS
 need(set(metrics)=={'blank_shadow_durable_boundaries','reused_valid_bank_durable_boundaries','normal_save_wrap_durable_boundaries','program_fault_cases','erase_fault_cases','reused_partial_erase_and_restart_cases','power_loss_restart_cases'},'all exact new measurement groups')
 need(metrics['program_fault_cases']==28 and metrics['erase_fault_cases']==8 and metrics['reused_partial_erase_and_restart_cases']==96 and metrics['power_loss_restart_cases']==8,'bounded new fault conditions')
 for name in ('blank_shadow_durable_boundaries','reused_valid_bank_durable_boundaries','normal_save_wrap_durable_boundaries'):need(metrics[name]['new']==1 and metrics[name]['old']>57000,'exact old/new commit boundary')
 write(PUBLIC/'measurement.json',dict(status='PASS_HOST_REFERENCE_HOF_TRANSACTION_AND_CAPACITY_REFUSAL',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),host_tests=result.testsRun,measurements=metrics,capacity=audit,synthetic_flash_sectors=34,actual_flash_sectors=32,actual_layout_refused_before_write=True,runtime_generation_binding=False,runtime_cross_store_atomicity=False,candidate=audit['candidate'],candidate_changed=False,formal_rom_changed=False,formal_save_changed=False,rom_reads=0,save_reads=0,arm_compiles=0,native_processes=0,source_bindings=bindings(CODE)))

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and not (ROOT/CP).exists(),'prior originals retained and one new checkpoint')
 measurement=json.loads((PUBLIC/'measurement.json').read_bytes());need(measurement['source_bindings']==bindings(CODE) and not measurement['runtime_cross_store_atomicity'],'host evidence exact; no runtime promotion')
 paths=set()
 for name in ('measurement.json','capacity.json','host-tests.txt'):
  p=EVIDENCE+'/'+name;need(not (ROOT/p).exists(),'one immutable new text evidence');(ROOT/p).parent.mkdir(parents=True,exist_ok=True);(ROOT/p).write_bytes((PUBLIC/name).read_bytes());paths.add(p)
 checkpoint=dict(schema_version=1,**measurement,guide=GUIDE,evidence_bindings=bindings(paths),previous_runtime_checkpoint=capacity.CP,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],runtime_integration_accepted=False)
 write(ROOT/CP,checkpoint)
 summary='HOF/mainの正確epoch＋全payload SHA256結合、normal Save継承、二重shadowからmain COWへ確定するhost参照実装と容量validatorを追加。21host契約・blank/再利用bank/normal wrapの全durable byte境界・故障/電源断を検証。現32sectorは独立shadow追加に8192byte不足としてwrite前拒否。候補88be8811と全115owner/43subowner/実残186byteは不変。実ROM世代結合・跨領域原子性は未受入。'
 goal='正式ROM/Save101と候補88be8811を保持し、永続HOF表現の容量/ownerを先に閉じる。host参照coreは34sector合成形式で現ROMへ未接続。現main片bank1740byteはzero/readback管理下、sector31残578byteもQOL管理下で無断借用不可。HOF不変base＋bounded team log等の実schema/容量満了処理を検討し、現ROM ABI・全mode/normal/link clone/HOF-only load/migration/coldを接続する。その後共通SaveFailed/早期31/全cold owner/typedconsumer、正式切替とtrainer131後半、最終シオウ通常回復・保存・独立cold Continueへ。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_generation_contract']=dict(checkpoint=CP,guide=GUIDE,status=measurement['status'],candidate=measurement['candidate'],host_tests=21,synthetic_only=True,runtime_generation_binding=False,runtime_cross_store_atomicity=False,record_run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='PROVE_DURABLE_HOF_LAYOUT_BEFORE_ROM_INTEGRATION',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_HOF_MAIN_COW_JA.md',capacity.CP,'docs/PR16_DEX_FALLBACK_QOL_JA.md'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='host参照transactionと容量拒否の実装検証source。実ROM/native/正式候補の原子性受入ではない。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(CODE|paths|{CP}))
 state['do_not_repeat'].append('HOF世代contractのhost参照実装21suiteは専用checkpointを再利用。34sector合成形式を32sector実Saveへ適用しない。現候補88be8811、全115owner/43subowner/186byte、正式ROM/Save101は不変。旧HOF/main/nativeを変更影響なしに再走せず、次は実永続表現の容量・ABI・ownerと全consumerへの接続。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],host_tests=21,native_processes=0,arm_compiles=0,candidate_changed=False,runtime_generation_binding=False,runtime_cross_store_atomicity=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();m=measurement['measurements']
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-GENERATION / HOF世代transaction参照実装と容量拒否\n- Version: dex-hof-generation-contract-v1\n- Status: DONE（host参照実装・容量validatorのみ。実ROM接続は未完）\n- Summary: {summary}\n- Files changed: transaction/capacity/source tests/Actions、専用guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: host21suite PASS。観測値={json.dumps(m,ensure_ascii=False,sort_keys=True)}。現32sector配置は書込前に拒否。\n- Boundary: 単一writer・同期readback・NOR model・CRC/SHA非衝突前提。実Flash/ARM/実Save parser/通常UI/cold受入0。合成34sector fixtureのみ、ROM/save読取0・ARM0/native0。実HOF/main原子性false。\n- Capacity: main片bank1740byteは現zero/readback管理下、logical13空き0、sector31候補残578byteもQOL管理下。sector30未使用認定禁止。現在115owner/43subowner/186byte、候補88be8811、正式ROM/Save101は不変。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repo Actions/正本text、source-lock固定CFRU save.c/pret hall_of_fame.c読取。公開はsource・最小address-size-SHA/textのみ。ROM断片/rawhex/ROM/入力save/runtime/runner/credential追加公開0。\n'
 for path in LOGS:
  with (ROOT/path).open('a') as out:out.write(entry)
 need(bindings(protected)==protected,'all prior accepted sources retained')
 owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')

def snapshot():
 receipt=dict(status='PASS_COMMITTED_HOST_CONTRACT_RECORD',source_head=os.environ['GITHUB_SHA'],final_head=git('rev-parse','HEAD').decode().strip(),record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=0,arm_compiles=0,final_blobs={})
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed source bytes')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes() and raw.endswith(b'\n'),'full snapshot with newline');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for p in LOGS:need(git('show','HEAD:'+p).startswith(git('show',BASE+':'+p)),'entire old log prefix preserved')
 write(PUBLIC/'record.json',receipt);print('RESULT=DONE TASK=USER-20261005-DEX-HOF-GENERATION VERIFY=PASS COMMIT='+receipt['final_head'])

def export():
 publication.output(PUBLIC)
 allowed={'host-tests.txt','capacity.json','measurement.json','record.json',*(n for n,_ in SNAPSHOTS)}
 for p in PUBLIC.iterdir():
  need(p.is_file() and not p.is_symlink() and p.name in allowed and not p.name.startswith('.'),'only explicit regular text snapshots')
  raw=p.read_bytes();need(0<len(raw)<3500000 and raw.endswith(b'\n') and b'\0'not in raw,'bounded complete text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)

if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed host-contract workflow')
 globals()[sys.argv[1]]()
