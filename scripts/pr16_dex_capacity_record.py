#!/usr/bin/env python3
"""完了したcompact ARM測定と新lease検証を記録。既存native/保存受入を再実行しない。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as transport
import pr16_story_route_probe as publication
import pr16_dex_capacity as measured
import pr16_dex_lease as lease
from pr16_story_after_maori import need,identity,write
BASE=SOURCE='8822a20ba6233bce79d23c54c499461ec0e8fd44'
RUN=37219630045;JOB=111487163702
ARCHIVE=(11309287135,RUN,3630,'998a5b66cdb2c4c788350c23e8d4a926f5e0d9f942d40dfa0e5643c0a6f34817')
CODE={lease.PROOF,'scripts/pr16_dex_lease.py','tests/test_pr16_dex_lease.py','scripts/pr16_dex_capacity_record.py','.github/workflows/pr16-dex-capacity-record.yml','docs/PR16_DEX_COMPACT_CAPACITY_JA.md','.github/workflows/pr16-dex-capacity.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_capacity_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_capacity_evidence'
GUIDE='docs/PR16_DEX_COMPACT_CAPACITY_JA.md';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-capacity-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','single authorized record attempt')
 p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'new capacity record only');OUT.mkdir();(OUT/'receipts').mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'old accepted sources and closed runs')
 r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
 need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'terminal exact ARM measurement')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==10 and all(x['conclusion']=='success'for x in j['steps']),'all10 measurement steps')
 z,meta=transport.archive(ARCHIVE)
 with z:
  need(set(z.namelist())=={'measurement.json','host-tests.txt'},'only two bounded text files')
  raw=z.read('measurement.json');host=z.read('host-tests.txt');report=json.loads(raw)
 need(report['source_head']==SOURCE and report['run_id']==RUN and report['status']=='PASS_COMPACT_C_AND_ARM_FOOTPRINT_ROM_UNWIRED','measurement identity')
 need(report['host_tests']==51 and report['c_mapping_comparisons']==262144 and report['arm_translation_units']==4 and report['arm_links']==1,'exact test/compiler scope')
 need(report['footprint']==dict(size=4638,sha256='2276f459265b5cf79523e411660cbee3cddcd806343f6bb8d35de15f8d41d05f'),'bound full API footprint')
 need(host.count(b' ... ok\n')==51 and b'\nOK\n'in host,'all51 compact tests evidence reused')
 for p,b in report['source_bindings'].items():
  need(identity(git('show',SOURCE+':'+p))==b,'all original measured source bytes '+p)
  if p not in{GUIDE,'.github/workflows/pr16-dex-capacity.yml'}:need(identity((ROOT/p).read_bytes())==b,'actual ARM code unchanged '+p)
 need(all(report[k]is False for k in('rom_changed','save_changed','runtime_wired','lease_accepted','public_binary_included'))and report['native_processes']==0,'strict measure scope')
 proof=lease.proof();need(proof['source_commit']==SOURCE and proof['typing_blockers']==[]and proof['unresolved_pointer_candidates']==[],'all35 donor candidates classified at current source')
 for row in proof['source_bindings']:
  if row['repository']!='dekaazarashi1111-web/pokemon-vega-modern':continue
  b=(ROOT/row['path']).read_bytes();need(identity(b)=={k:row[k]for k in('size','sha256')},'lease source still unchanged '+row['path'])
 z,_=transport.archive(transport.SAVE24)
 with z:
  manifest=json.loads(z.read('manifest.json'));need(set(z.namelist())==set(manifest)|{'manifest.json'},'fixed existing ROM donor archive')
  for n,b in manifest.items():need(identity(z.read(n))==b,'fixed donor artifact member '+n)
  rom=z.read('candidate.gba')
 need(identity(rom)==lease.CANDIDATE,'private fixed candidate');private=OUT/'private-candidate.gba';private.write_bytes(rom);private.chmod(0o444)
 validated=lease.validate_preimage(rom);plan=lease.plan_payload(report['footprint']['size'])
 env=dict(os.environ,VEGA_DEX_ROM_PATH=str(private));test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_lease.py','-v'],cwd=ROOT,env=env,capture_output=True)
 need(test.returncode==0 and not test.stdout and test.stderr.count(b' ... ok\n')==25 and b'\nOK\n'in test.stderr,'25 new lease and fail-closed publication tests')
 need(private.read_bytes()==rom,'private source ROM remains exact');e=ROOT/EVIDENCE;e.mkdir()
 for n,b in{'measurement.json':raw,'compact-host-tests.txt':host,'lease-host-tests.txt':test.stderr}.items():(e/n).write_bytes(b)
 write(e/'lease-validation.json',validated);write(e/'placement-plan.json',plan)
 evidence={p.relative_to(ROOT).as_posix()for p in e.iterdir()};new_sources=measured.CODE|CODE
 checkpoint=dict(schema_version=1,status='PASS_COMPACT_ARM_AND_HASH_BOUND_RETIRED_OWNER_CONTRACT_PLACEMENT_PENDING',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),measurement_source=SOURCE,measurement_run=RUN,measurement_job=JOB,measurement_artifact=ARCHIVE[0],measurement_all10_steps_success=True,compact_tests=51,lease_tests=25,c_mapping_comparisons=262144,arm_translation_units=4,arm_links=1,compact_data_bytes=1801,previous_data_bytes=7597,full_api_arm_footprint_bytes=4638,donor_bytes=6484,remaining_within_donor_bytes=1846,lease_validation=validated,placement_plan=plan,source_bindings=bindings(new_sources),evidence_bindings=bindings(evidence),rom_changed=False,formal_save_changed=False,native_processes=0,record_arm_compiles=0,old_compact_tests_rerun=0,allocator_transferred=False,actual_placement_linked=False,save_scheduler_wired=False,consumer_callsites_wired=False,repair_native_accepted=False,formal_story_save=101,release_ready=False,public_artifacts='validated text only',unresolved=['実配置addressでのrelink/stub/veneerとallocator owner移管','候補全diff監査と影響learnset回帰','Stage61既存owner内置換と全保存mode接続','全SID/official/direct consumer接続','通常Save/独立cold Continue限定native','シオウPokecenter回復milestone'])
 write(ROOT/CP,checkpoint)
 goal=('正式Save101は不変。PR16_DEX_COMPACT_CAPACITY_JA.mdとpr16_dex_capacity_checkpoint.jsonから再開。'
 'compact mapping1801byte、新codec/typed adapter/lookup/save bridgeの全API ARMv4T footprint4638byteを51host/262144入力比較/4compileで確認。'
 'Stage39退役T09 pointer owner6484byteは全35疑似pointer型・5root・8間接参照・旧DATA/6sentinel参照・全1621終端と20sourceを照合し、25lease試験PASS。'
 '実allocator移譲/実配置addressでの再link/stub/veneer/ROM patch/nativeは未実施。Stage61全12568byteを空きへcloneする容量証明ではない。'
 '既存owner内置換・export/callsite到達性を固定し全save mode/CRC bank fallback/partial-write/復旧Save前MDX load、全SID喪失前consumer/Bag count/reward clear/Factory-Codex rollbackへ接続。'
 '候補全diff/影響learnsetと保存ABI限定native・通常Save/独立cold Continue受入まで正式基準/trainer戦闘を変えない。受入後Save101からシオウPokecenter通常回復へ。雑魚戦ごとのSaveは作らない。')
 state['story_dex_owner']['runtime_integration']['capacity']=dict(checkpoint=CP,guide=GUIDE,status=checkpoint['status'],source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),measurement_source=SOURCE,measurement_run=RUN,compact_tests=51,lease_tests=25,arm_translation_units=4,full_api_arm_footprint_bytes=4638,donor_bytes=6484,allocator_transferred=False,runtime_wired=False)
 state['next_action'].update(id='PLACE_HASH_BOUND_DEX_AND_WIRE_SAVE_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,lease.PROOF,'docs/PR16_DEX_RUNTIME_INTEGRATION_JA.md','content/modernization/pr16_dex_runtime_checkpoint.json','docs/PR16_DEX_CONSUMERS_JA.md'])
 state['bp']['current_stop']='正式Save101保持。compact1801byte/ARM全API4638byte、Stage39退役owner6484byteのhash-bound leaseを検証。実配置と全save/consumer接続は未完。';state['bp']['next_step']=goal
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='図鑑compact ARM容量と退役owner契約の記録source。正式ROM/Save101不変、記録ARM0/native0。実配置/全save/consumer受入は未完。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['do_not_repeat'].append('図鑑compact51host/262144比較/ARM4compileはrun37219630045の原本を再利用。旧T09 pointer表6484byteはStage39退役のhash-bound契約のみ。元DATA81885byte/sentinel6参照保持、実owner移管/ROM配置/Stage61全clone/nativeを完了扱いしない。')
 state['source_bindings'].update(bindings(new_sources|evidence|{CP}));publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-CAPACITY / 図鑑lookup圧縮・ARM容量・退役owner契約\n- Version: dex-capacity-v1\n- Status: STOPPED（容量工程PASS。実配置と全保存/consumer接続は未完）\n- Summary: mapping7597→1801byte、元adapterを保全してcompact版生成。全API ARM4638byteを実測。Stage39退役T09 pointer表6484byteを全候補35件/新5root/間接8/旧DATA・6sentinel/1621終端/20sourceからhash固定。公開guard失敗時upload可能だった経路を閉じた。\n- Files changed: compact専用source/51tests、ARM測定workflow、lease契約/validator/25tests、checkpoint/evidence、固定MDJSON、両ログ。\n- Verify: run{RUN}/job{JOB}全10step成功の51host・262144入力比較・ARM4compile/1linkを再利用。新25lease試験PASS。今回記録compact再試験0/ARM0/native0/ROM・Save変更0。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/source、採用pinのpret/CFRU型定義。公開はhash/address/size/sourceと検査済textのみ。一般CI既知QOL source不一致、Stage79 cacheは別扱い。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as f:f.write(entry)
 need(bindings(protected)==protected,'previously accepted source bytes remain unchanged');owned={STATE,DOC,CP,*LOGS}|evidence;write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/capacity-record.json',checkpoint);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed text readback')
 print('RESULT=STOPPED TASK=USER-20261004-DEX-CAPACITY VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if(OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',ROOT/'public-dex-capacity-record')
if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'bounded record action');globals()[sys.argv[1]]()
