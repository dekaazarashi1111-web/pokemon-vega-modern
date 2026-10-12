#!/usr/bin/env python3
"""Record terminal scheduler evidence without rebuilding or rerunning native."""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
import pr16_dex_scheduler_actions as measured
need,identity,write=measured.need,measured.identity,measured.write
BASE=SOURCE='52c24cb0c2104edc2e07e259db7340d35ebc2342'
RUN=37228557062;JOB=111513197041;ARCHIVE=(11313181929,RUN,19026,'ea22ead56b59b5df7c6d2d90bfb5f13189c147fc078cccdb226b3ea7d4ea5e16')
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_scheduler_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_scheduler_evidence'
GUIDE='docs/PR16_DEX_SAVE_SCHEDULER_JA.md';CHAIN='content/modernization/pr16_dex_loadchain_audit.json'
CODE={'scripts/pr16_dex_scheduler_record.py','.github/workflows/pr16-dex-scheduler-record.yml',GUIDE,CHAIN,'content/modernization/pr16_dex_save_body_references.json'}
LOGS={'design/run_log.md','design/version_log.md'};OUT=ROOT/'.local/pr16-dex-scheduler-record';PUBLIC=ROOT/'public-dex-scheduler-record'
FAILURES=[
 dict(run=37225490072,job=111504163826,source='a2b15ba9ef3c4076aa5e3460ca312241e9ba2e28',native_processes=0,reason='元save専用窓に最大1320byte関数が収まらず停止'),
 dict(run=37226054728,job=111505814163,source='01acd19a11066a683632cebfc156f428429fa53f',native_processes=0,reason='共通化後も元窓の容量・分割制約で停止'),
 dict(run=37226341026,job=111506656698,source='79b2f2c3410c2e675a0338f1d629f6b88bb3c836',native_processes=0,reason='予約suffix併用後のfar-call stub実測で停止'),
 dict(run=37226687299,job=111507674387,source='d6f76379231eb39c08534b365c60b382c346633b',native_processes=0,reason='直接pointer呼出し案でも分割容量不足、採用しない'),
 dict(run=37227008304,job=111508629289,source='f3464a10c2d54825794ae61c5319e48f65dafa88',native_processes=0,reason='元save helper再配置後もstubを含む8220byteが断片窓へ収まらず停止'),
 dict(run=37228052395,job=111511709070,source='62c8e5b939f634438410dded8cad1da486717e3b',native_processes=0,reason='追加leaseと実link通過後、local veneer同名symbolの検査で停止'),
 dict(run=37228277111,job=111512377165,source='b60d6603dca643f0d424a753518c40fd61a99324',native_processes=0,reason='ARM interworkingのlocal thunkも同名になり得るためsymbol suffix条件で停止'),
 dict(run=37228400286,job=111512739968,source='84bad2c244640119b2f8c5d4853efdb33f52aa21',native_processes=0,reason='実候補生成とallocator検証通過後、runner関数accessがPOSIX宣言と衝突してcompile停止')]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized record branch')
 p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable scheduler record');OUT.mkdir(parents=True);PUBLIC.mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'all accepted sources retained and prior runs terminal')
 r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
 need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'exact successful scheduler run')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==10 and all(x['conclusion']=='success'for x in j['steps']),'all10 scheduler steps success')
 for f in FAILURES:
  old=transport.api('actions/runs/'+str(f['run']));need(old['head_sha']==f['source']and old['status']=='completed'and old['conclusion']=='failure','retained failed diagnostic')
 z,_=transport.archive(ARCHIVE)
 with z:
  need(set(z.namelist())=={'build.json','host-tests.txt','host-runtime.json','native.json','native-attempt.json'},'exact text-only evidence set');files={p:z.read(p)for p in z.namelist()}
 report=json.loads(files['build.json']);native=json.loads(files['native.json']);host=json.loads(files['host-runtime.json'])
 need(report['source_head']==SOURCE and report['run_id']==RUN and report['native']==native and report['status']=='PASS_ISOLATED_SAVE_SCHEDULER_CANDIDATE','exact accepted report')
 need(native['calls']==36 and native['steps']==126124517 and native['cases']==19 and native['native_processes']==1 and native['game_boots']==native['ordinary_saves']==0 and native['ewram_bytes_checked_per_call']==262144,'isolated native scope, no gameplay claim')
 need(host['cases']==20 and host['native_game_runs']==0 and files['host-tests.txt'].count(b' ... ok\n')==18,'20 host runtime plus18 generator cases')
 need(report['candidate']==dict(size=33554432,sha256='6066f9ede35ea2e244221b7a99219eee6dc239df00559311ec8feb20ee74c72c') and report['link']['actual_payload_bytes']==8264 and report['link']['extra_lease_size']==1084 and report['allocation']['summaries']['allocation_count']==108 and report['allocation']['summaries']['overlap_count']==0,'exact measured candidate and allocator')
 need(report['formal_rom_changed']is False and report['formal_save_changed']is False and report['gameplay_accepted']is False,'formal input remains unchanged')
 for p,b in report['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b and identity(git('show',SOURCE+':'+p))==b,'measured source whole-byte binding '+p)
 z,_=transport.archive(transport.SAVE24)
 with z:original=z.read('candidate.gba')
 need(identity(original)==report['formal_candidate'],'same immutable ROM for record-only audits')
 def windows(value):
  if isinstance(value,dict):
   if {'address','size','sha256'}<=set(value)and isinstance(value['address'],str):
    at=int(value['address'],16)-0x08000000
    need(identity(original[at:at+value['size']])==dict(size=value['size'],sha256=value['sha256']),'whole signed static audit window')
   for child in value.values():windows(child)
  elif isinstance(value,list):
   for child in value:windows(child)
 for path in (CHAIN,'content/modernization/pr16_dex_save_body_references.json'):windows(json.loads((ROOT/path).read_bytes()))
 e=ROOT/EVIDENCE;e.mkdir()
 for name,raw in files.items():(e/name).write_bytes(raw)
 evidence={p.relative_to(ROOT).as_posix()for p in e.iterdir()}
 checkpoint=dict(schema_version=1,status=report['status'],source_head=SOURCE,run=RUN,job=JOB,all10_steps_success=True,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],candidate=report['candidate'],formal_candidate=report['formal_candidate'],link=report['link'],allocation=report['allocation'],generator_tests=18,synthetic_host_cases=20,isolated_arm=native,failed_build_attempts=FAILURES,accepted_native_processes=1,record_arm_compiles=0,record_native_processes=0,formal_save_changed=False,formal_save=101,gameplay_accepted=False,all_save_modes_accepted=False,all_consumers_wired=False,newgame_wired=False,outer_load_guard_wired=False,release_ready=False,source_bindings=bindings(CODE|measured.CODE),evidence_bindings=bindings(evidence),record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']))
 write(ROOT/CP,checkpoint)
 goal=('正式ROM/Save101は不変。PR16_DEX_SAVE_SCHEDULER_JA.mdとpr16_dex_scheduler_checkpoint.jsonから再開。'
       'Stage61保存8入口の固定veneerと全44export/元non-save保持、同世代MDX、LinkFull署名前再読、CRC fallback/clone/record-onlyを候補内へ接続し隔離ARM19caseを受入。'
       '次はloadchain監査のMirage literal0x09391114にpost-QOL MDX gateを、CFRU literal0x09097178にwipe後InitNew tail wrapperを接続。'
       '現sector31復元はlegacy2048byteでMDXに重ならないがstockは内側load返値を捨てる。HOF-only load=3を除外し、復旧Save前に失敗遮断する。'
       'authority不明のinvalid-liveでは仮damaged sectorを付けず、上位の非破壊的失敗伝播を実装。全save mode固有副作用、全SID喪失前consumer/Bag count/reward clear/Factory-Codex rollback、'
       '候補限定通常Save/独立cold Continueを受入後だけ正式進行。最終はシオウPokecenter通常回復/Save/coldContinue。雑魚戦ごとのSaveは作らない。')
 state['story_dex_owner']['runtime_integration']['save_scheduler']=dict(checkpoint=CP,guide=GUIDE,status=report['status'],source=SOURCE,run=RUN,isolated_arm_cases=19,synthetic_host_cases=20,formal_save_changed=False,gameplay_accepted=False,outer_load_guard_wired=False,newgame_wired=False,consumer_wired=False,record_run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']='正式ROM/Save101保持。Stage61保存schedulerの候補配置と隔離ARM19caseまで受入。newgame、外側load失敗gate、全consumer、通常Save/coldContinueは未完。'
 state['bp']['next_step']=goal;state['next_action'].update(id='WIRE_DEX_LOAD_NEWGAME_AND_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,CHAIN,'docs/PR16_DEX_CONSUMERS_JA.md'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='図鑑保存scheduler候補の隔離ARM受入を記録したsource。正式ROM/Save101不変。記録ARM0/native0。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(CODE|measured.CODE|evidence|{CP}));state['do_not_repeat'].append(f'図鑑保存scheduler run{RUN}の隔離ARM19caseはsource/配置不変なら再実行しない。通常game Save/ContinueとHOF/overwrite受入へ昇格しない。8つのbuild診断failureはnative0のまま保持。')
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-SCHEDULER / Stage61同世代図鑑保存候補\n- Version: dex-save-scheduler-v1\n- Status: STOPPED（隔離ARM受入。通常保存・全consumerは未完）\n- Summary: 44export/非保存code/data/隣hotfixを保持し、元保存ownerを再配置。既存codec予約と署名済allocatable窓の最小leaseを正規allocatorで使用。MDX検証/注入/load/clone/record-onlyとLinkFull署名前再読を接続。\n- Files changed: scheduler source/harness/workflow、追加leaseとloadchain監査、checkpoint/evidence、固定MDJSON、両ログ。\n- Verify: run{RUN}/job{JOB}全10step成功。generator18、synthetic host20、隔離ARM19case/各EWRAM全262144byteのnon-owner対照。build診断8runはnative0 failure保持。記録では再compile/native0。\n- Next: {goal}\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存candidate、source根拠のみ。一般CI QOL source不一致、Stage79 cacheを別記。公開はsource/address/size/hashと検査済textのみ。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 need(bindings(protected)==protected,'all old accepted sources remain exact')
 owned={STATE,DOC,CP,*LOGS}|evidence;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'scheduler-record.json',checkpoint);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed text readback')
 print('RESULT=STOPPED TASK=USER-20261004-DEX-SCHEDULER VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated record public directory')
 for p in PUBLIC.iterdir():
  need(p.name=='scheduler-record.json'and p.is_file()and not p.is_symlink(),'only one regular receipt');raw=p.read_bytes();need(0<len(raw)<200000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete JSON');json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'bounded record action');globals()[sys.argv[1]]()
