#!/usr/bin/env python3
"""新consumer縦切りの限定受入。既存native/ARMを再実行しない。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
import pr16_dex_battle_actions as measured
need,identity,write=measured.need,measured.identity,measured.write
BASE=SOURCE='63b1c819a9e84a1a8b1d0116320a908f26dec9e7'
RUN=37233960024;JOB=111529277202
ARCHIVE=(11315111220,RUN,17565,'aa3477701d2e425c7256df2d91fa3d83edf4733b613ab4f2ecb368694751e15f')
REJECTED=(11315031009,37233754843,17471,'a32f53170bbc0c3c61754f9c09cfc67fa478d81723a2a40a53b13169d947d346')
GUIDE='docs/PR16_DEX_BATTLE_CONSUMERS_JA.md'
CODE={GUIDE,'scripts/pr16_dex_battle_record.py','.github/workflows/pr16-dex-battle-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_battle_checkpoint.json'
EVIDENCE='content/modernization/pr16_dex_battle_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-battle-record';PUBLIC=ROOT/'public-dex-battle-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized branch')
 p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable consumer record');OUT.mkdir(parents=True);PUBLIC.mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'prior sources and terminal records')
 r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB));need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'exact successful source run')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==10 and all(x['conclusion']=='success'for x in j['steps']),'all10 steps successful')
 z,_=transport.archive(ARCHIVE)
 with z:
  need(set(z.namelist())=={'build.json','native.json','native-attempt.json','host-tests.txt'},'exact accepted text original');files={n:z.read(n)for n in z.namelist()}
 report=json.loads(files['build.json']);need(report['source_head']==SOURCE and report['run_id']==RUN and report['native']==json.loads(files['native.json']),'native report identity')
 need(report['host_suites']==6 and report['host_raw_species_cases']==1670 and report['native']['cases']==180 and report['native']['seen_cases']==140 and report['native']['count_cases']==40,'bounded host and native acceptance')
 need(report['link']['base']==0x095FFE50 and report['link']['payload']['size']==160 and report['placement']['allocation']['summaries']['allocation_count']==110 and report['placement']['changed_existing_owners']==[] and report['placement']['whole_rom_rollback_exact'],'correct new immutable allocation and all prior owners retained')
 need(report['all_consumers_wired']is False and report['all_save_modes_accepted']is False and report['ordinary_battle_accepted']is False and report['formal_save_changed']is False,'no overclaim')
 for p,b in report['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b and identity(git('show',SOURCE+':'+p))==b,'whole measured source retained')
 rz,_=transport.archive(REJECTED)
 with rz:
  prior=json.loads(rz.read('build.json'));need(prior['source_head']=='9217ffb215923e1794d064037f5c40fd86ac6538'and prior['run_id']==REJECTED[1]and prior['link']['base']==0x09FC1D38,'exact rejected placement original')
 reject=dict(run=REJECTED[1],source=prior['source_head'],artifact=REJECTED[0],archive_size=REJECTED[2],archive_sha256=REJECTED[3],candidate=prior['candidate'],native=prior['native'],actions_conclusion='success',candidate_accepted=False,reason_ja='隔離consumer180call成功だけでは保存配置を証明しない。codec suffixはscheduler clone等が使用済みで、同一owner内部の上書きを旧guardが見逃した。正式ROM/Save101不変。後継は監査済の別spanと全既存owner byte一致guardへ修正。')
 evidence=ROOT/EVIDENCE;evidence.mkdir()
 for name,raw in files.items():(evidence/name).write_bytes(raw)
 write(evidence/'rejected-placement-adjudication.json',reject)
 evidence_paths={p.relative_to(ROOT).as_posix()for p in evidence.iterdir()}
 cp=dict(schema_version=1,status='PASS_CANDIDATE_BATTLE_SEEN_AND_OFFICIAL_COUNT',candidate=report['candidate'],measurement=report,source=SOURCE,run=RUN,job=JOB,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],all10_steps_success=True,source_bindings=bindings(CODE|measured.CODE),evidence_bindings=bindings(evidence_paths),rejected_placement=reject,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0,formal_rom_changed=False,formal_save_changed=False,formal_save=101,all_consumers_wired=False,all_save_modes_accepted=False,ordinary_battle_accepted=False)
 write(ROOT/CP,cp)
 goal=('正式ROM/Save101は保持。battle seen5窓とCFRU公式countを新ownerへ接続し、host6suite/全1670SIDと新配置隔離ARM180callを限定受入。全109旧allocated owner、scheduler/codec/load/newgame不変。'
 '次はauthorityなしinvalid-liveの保存返値255がstock mask0で成功へ潰れる穴とSaveFailedのmask0誤成功を、共通TrySavingData後段とTryWipe非破壊guardでセット修復し、実失敗UI/A復帰/全FlashRTC不変を確認する。'
 'active capture/mon登録、native授受/孵化/進化、UI/native count、reward clear、Factory memorial/Codex rollback、DexNav、HOF/overwrite等全mode固有副作用は未完。全consumerと必要な影響native受入前に正式進行へ戻さない。最終はシオウPokecenter通常回復/Save/coldContinue、通常雑魚ごとのSaveなし。')
 state['story_dex_owner']['runtime_integration']['battle_consumers']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=cp['candidate'],run=RUN,source=SOURCE,record_run=int(os.environ['GITHUB_RUN_ID']),all_consumers_wired=False,formal_save_changed=False)
 state['bp']['current_stop']='正式ROM/Save101保持。battle seen5窓とCFRU公式countを候補限定受入。保存失敗誤成功2経路と残consumer/全save modeは未完。';state['bp']['next_step']=goal
 state['next_action'].update(id='CLOSE_DEX_SAVE_FAILURE_PROPAGATION_THEN_REMAINING_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_CONSUMERS_JA.md','docs/PR16_DEX_SAVE_SCHEDULER_JA.md'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='図鑑battle seen/公式countを候補限定受入した記録source。通常battle0、正式ROM/Save101不変。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(CODE|measured.CODE|evidence_paths|{CP}));state['do_not_repeat'].append(f'図鑑battle consumer run{RUN}のhost6suite/隔離ARM180callはsourceと候補不変で再実行しない。初回run37233754843はActions成功でもscheduler配置衝突により候補不受入。保存/通常battle/全consumerへ昇格しない。')
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-CONSUMERS / 図鑑battle seenと公式count\n- Version: dex-battle-consumers-v1\n- Status: DONE（候補consumer縦切り限定。残consumer/保存失敗は次工程）\n- Summary: raw SIDを失う前の5seen窓とCFRU公式1025countを接続。旧Bag誤読を停止。160byteを0x095FFE50へ新lease配置し全109旧owner/codec/scheduler/load/newgameを保持。\n- Files changed: consumer C/ASM、generator/native/host/workflow、署名窓、専用guide/CP/evidence、固定MDJSONと両ログ。\n- Verify: run{RUN}/job{JOB}全10step成功、host6suite/全1670SID、ARM180call/12101624instructions、全EWRAM/IWRAM非owner・SP/callee保持、allocator110owner/overlap0、全ROMrollback。通常battle0/Save0。\n- Correction: run37233754843は隔離180call成功でもcodec suffixへscheduler clone上書きのため候補不受入。正式入力不変。独立レビューで検出し配置変更＋既存owner全byte guardと回帰試験を追加。新配置の実アドレス変更を再検証し、旧successを保存健全性へ昇格しない。\n- Boundary: 全consumer/全save mode/実失敗UI未完。authorityなしinvalid-live返値255→stock mask0成功→QOL sector31保存の可能性、およびSaveFailed mask0成功を発見。次工程で両方を同時修復。\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存入力/公式Ubuntu toolchain。公開はsourceとaddress-size-SHA/textだけ。ROM/入力save/runtime/runner/credentials非公開。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 need(bindings(protected)==protected,'all older accepted sources retained')
 owned={STATE,DOC,CP,*LOGS}|evidence_paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'battle-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed readback')
 print('RESULT=DONE TASK=USER-20261004-DEX-CONSUMERS VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated record directory')
 for p in PUBLIC.iterdir():
  need(p.name=='battle-record.json'and p.is_file()and not p.is_symlink(),'one exact receipt');r=p.read_bytes();need(0<len(r)<250000 and r.endswith(b'\n')and b'\0'not in r,'bounded complete JSON');json.loads(r)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'bounded record action');globals()[sys.argv[1]]()
