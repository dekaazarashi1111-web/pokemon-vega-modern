#!/usr/bin/env python3
"""新5UI寿命と新host adapterを記録。旧nativeを再実行せず正式Save101を保持。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path,PurePosixPath
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as transport
import pr16_story_route_probe as publication
import pr16_dex_adapter_tables as tables
import pr16_dex_lifetime as lifetime
from pr16_story_after_maori import need,identity,write
BASE='587736739708b82178f2ada891cc837aea7c653a'
SOURCE='32fc3bb382598065978696618ea314363fda2e25';RUN=37217077790;JOB=111479655834
ARTIFACT=(11307919413,RUN,147409,'e6562a97c2f2731a39459a84dde7c07b52e9d717f5872422ae76baddd0fe1ed3')
TASK='USER-20261004-DEX-RUNTIME'
STATE='content/modernization/pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_runtime_checkpoint.json'
UNIT='content/modernization/pr16_dex_runtime_unit.json'
GUIDE='docs/PR16_DEX_RUNTIME_INTEGRATION_JA.md'
PLACEMENT='content/modernization/pr16_dex_placement_audit.json'
LOGS={'design/run_log.md','design/version_log.md'}
CODE={'tools/mgba_pr16_dex_lifetime.c','scripts/pr16_dex_lifetime.py','tests/test_pr16_dex_lifetime.py','.github/workflows/pr16-dex-lifetime.yml',
 'overlays/dex_owner/dex_adapter.c','overlays/dex_owner/dex_adapter.h','overlays/dex_owner/dex_adapter_tables.h',
 'overlays/dex_owner/dex_save_bridge.c','overlays/dex_owner/dex_save_bridge.h','scripts/pr16_dex_adapter_tables.py',
 'tests/test_pr16_dex_adapter.py','tests/test_pr16_dex_save_bridge.py',GUIDE,PLACEMENT,'scripts/pr16_dex_runtime_record.py','.github/workflows/pr16-dex-runtime-record.yml'}
REFERENCES=set(tables.REFERENCES)
OUT=ROOT/'.local/pr16-dex-runtime-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','single authorized record attempt')
    p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole exact draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def native_evidence():
    r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
    need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'exact terminal lifetime run')
    need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==9 and all(x['conclusion']=='success'for x in j['steps']),'all9 steps successful')
    z,meta=transport.archive(ARTIFACT);proof=OUT/'proof';proof.mkdir()
    with z:
        for name in z.namelist():
            path=PurePosixPath(name);need(not path.is_absolute()and '..'not in path.parts and all(not x.startswith('.')for x in path.parts)and path.suffix in {'.json','.txt','.ppm'},'safe known text/screens archive')
            f=proof/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(name))
    measurement=json.loads((proof/'measurement.json').read_bytes())
    need(measurement['source_head']==SOURCE and measurement['run_id']==RUN and measurement['status']=='PASS_FIVE_UI_UNSAVED_MDX_LIFETIME_ONLY'and measurement['native_processes']==4 and measurement['reused_native_cases']==1,'four new and one retained exact lifetime scope')
    lifetime.OUT=proof;results=[]
    for case in lifetime.CASES:
        value,_=lifetime.validate((proof/case/'stdout.txt').read_bytes(),case)
        need(value==json.loads((proof/case/'result.json').read_bytes()),'whole native result '+case)
        execution=json.loads((proof/case/'execution.json').read_bytes());need(execution['returncode']==0 and execution['save_unchanged']is True,'full input Save101 equality '+case)
        results.append(value)
    need(results==measurement['results'],'all five case results')
    return dict(run=RUN,job=JOB,source=SOURCE,artifact=ARTIFACT[0],archive_size=ARTIFACT[2],archive_sha256=ARTIFACT[3],all9_steps_success=True,accepted_ui_cases=5,new_native_processes_in_terminal_run=4,reused_bag_native_cases=1,total_attempt_native_processes=7,failed_compile_native_processes=0,failed_summary_attempts=2,whole_owner_bytes=522,whole_party_bytes=600,whole_pc_bytes=0x83D0,tail_alignment_guard_bytes=2,owner_store_calls=0,ordinary_saves=0,formal_save_changed=False,rom_changed=False,visual_review_completed=True,results=results)
def record():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists()and not(ROOT/CP).exists(),'new runtime checkpoint only');OUT.mkdir();(OUT/'receipts').mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'accepted source frozen and no old pending run')
    placement=json.loads((ROOT/PLACEMENT).read_bytes());need(placement['candidate']==dict(size=33554432,sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')and placement['free_window_count']==40 and sum(x['size']for x in placement['unallocated_windows'])==3151 and max(x['size']for x in placement['unallocated_windows'])==1704 and placement['sid1670']['stable_owner']==925 and placement['sid1670']['rom_count']==1671 and placement['rom_fragments_or_raw_hex_included']is False,'bound low-disclosure placement and final SID evidence')
    native=native_evidence();need((ROOT/tables.OUTPUT).read_bytes()==tables.build(),'all1671 adapter mapping exact generated bytes')
    cases={};test_ids=[]
    for pattern,count in [('test_pr16_dex_lifetime.py',30),('test_pr16_dex_save_bridge.py',34),('test_pr16_dex_adapter.py',38)]:
        test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True)
        need(test.returncode==0 and test.stderr.count(' ... ok\n')==count and '\nOK\n'in test.stderr,'focused final host tests '+pattern)
        cases[pattern]=dict(tests=count,passed=count,stderr_sha256=identity(test.stderr.encode())['sha256'])
        test_ids.extend(line.split(' ... ok')[0]for line in test.stderr.splitlines()if line.endswith(' ... ok'))
    unit=dict(schema_version=1,tests=102,passed=102,host_c_compiles=2,arm_compiles=0,native_processes=0,test_ids=test_ids,groups=cases,source_bindings=bindings(CODE|REFERENCES),scope='HOST_ADAPTER_BRIDGE_AND_NEW_UI_EVIDENCE_VALIDATOR')
    write(ROOT/UNIT,unit)
    checkpoint=dict(schema_version=1,task=TASK,status='PASS_FIVE_UI_LIFETIME_AND_HOST_ADAPTER_RUNTIME_UNWIRED',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),source_bindings=bindings(CODE|REFERENCES|{UNIT}),native_lifetime=native,host_tests=102,host_c_compiles=2,placement_audit=PLACEMENT,namespace_version=1,stable_owner_count=1206,foundation_runtime_slots=1670,adapter_runtime_slots=1671,stage75_form=dict(species_id=1670,base_species_id=1142,owner=925,namespace_owner_semantics_changed=False),serialized_bytes=522,legacy_snapshot_bytes=208,ram_lifetime_scoped_accepted=True,save_scheduler_wired=False,consumer_callsites_wired=False,repair_native_accepted=False,arm_compiles=0,rom_changed=False,formal_story_save=101,formal_save_changed=False,milestone_reached=False,release_ready=False,
        unresolved=['宣言済ROM空き3151byteの容量制約とowner lease/compact mapping','Stage61全save modeとCRC fallback/partial write接続','外側load復旧Saveより前のMDX復元とsector31 shadow無効化','全SID/official/nativeUI consumer署名付き接続','旧履歴の根拠付き昇格','候補normal Save/独立cold Continue限定native','シオウPokecenter通常回復milestone'],
        review_fixes=['store前unknown差分検知','同値の未所有store拒否','末尾2byte/再配置PC全体guard','metadata/path/fixture validator厳格化','Stage75 OwnTempo1670をbase1142 owner925へ明示拡張'])
    write(ROOT/CP,checkpoint)
    goal=('正式Save101は不変。PR16_DEX_RUNTIME_INTEGRATION_JA.mdとpr16_dex_runtime_checkpoint.jsonから再開。'
          'MDX522の5UI寿命はnative受入、SID/公式count/Factory-Codex rollback/companion bridgeは102host検査済みだがROM未接続。'
          '固定候補の未割当は3151byteのみで大窓1704/1240byte。Stage61全体再リンクを押し込まず、compact namespace/既存owner内置換を署名・到達性・allocationで設計する。'
          'Stage75 SID1670→base1142/owner925を含む1671slotを使い、旧1670slot上限をruntime全体へ誤適用しない。'
          '全save mode/CRC bank fallback/partial-write、外側復旧Saveより前のMDX load、全SID喪失前consumer/direct count-clear/transactionを接続。'
          '保存ABI限定nativeと通常Save/独立cold Continue受入まではtrainer戦闘・候補基準切替をしない。'
          '受入後だけSave101からtrainer131/128/1065経由でシオウPokecenter回復・Save・cold Continueへ。雑魚戦ごとのSaveは作らない。')
    state['story_dex_owner']['runtime_integration']=dict(checkpoint=CP,guide=GUIDE,status=checkpoint['status'],source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),host_tests=102,native_lifetime_run=RUN,accepted_ui_cases=5,adapter_runtime_slots=1671,runtime_wired=False,formal_story_save=101)
    state['next_action'].update(id='WIRE_COMPACT_DEX_SAVE_AND_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,PLACEMENT,'docs/PR16_DEX_CONSUMERS_JA.md','content/modernization/pr16_dex_storage_audit.json'])
    state['bp']['current_stop']='正式Save101保持。MDX522の5UI寿命をnative確認。SID/公式/rollback/保存bridgeは102host検査済み、ROM未接続。未割当3151byteの容量設計が次。';state['bp']['next_step']=goal
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='5UI寿命の原本を受入しhost接続APIを記録したsource。新ROM/ARM/通常Saveなし。全保存/consumer nativeとシオウ到達は未完。'
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['do_not_repeat'].append('MDX候補RAMの5UI寿命はrun37217077790の原本から再利用（Bagは37216583954から再利用）。正式Save101不変。Stage75 internal1670は明示adapterでbase1142/owner925へ結合し、namespace owner数1206は不変。全save/consumer未接続とROM空き容量3151byteを隠さず先に解決。')
    state['source_bindings'].update(bindings(CODE|REFERENCES|{CP,UNIT}));publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 図鑑未保存RAM寿命とtyped consumer・companion bridge\n- Version: dex-runtime-foundation-v2\n- Status: STOPPED（5UI寿命とhost実装受入。ROM保存/consumer接続未完）\n- Summary: Bag/summary/図鑑/PC/box-nameで522byte保持、CPU/DMA/STM未所有write0、party/PC/全Save101保持を実証。新SID/公式count・Factory/Codex rollback・sector bridge実装。独立レビューでStage75 SID1670漏れを補いowner925へ束縛。\n- Files changed: 専用fixture/adapter/bridge/102検査、checkpoint/guide、固定resumeMD/JSON、両ログ。\n- Verify: 新102host PASS（C compile2）、native run{RUN}/job{JOB}全9step成功の原本5UI/27画面を再照合。失敗compile native0、失敗Summary2を履歴として保持。今回記録ARM0/native0/ROM変更0/通常Save0。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoGitHub source/Actions原本、mGBA0.10.2公式ARM memory/DMA sourceを参照。公開はsourceと検査済text/screensのみ、ROM断片/runtime/inputSaveを含めない。一般CI QOL source不一致は未解決、Stage79はcache再利用。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as f:f.write(entry)
    need(bindings(protected)==protected,'old accepted source remains byte-identical');owned={STATE,DOC,CP,UNIT,*LOGS};write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/runtime-record.json',checkpoint);git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed bytes')
    print('RESULT=STOPPED TASK='+TASK+' VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
    if(OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',ROOT/'public-dex-runtime-receipts')
if __name__=='__main__':
    actions=dict(source_guard=source_guard,record=record,guard=guard,snapshot=snapshot,export=export);need(len(sys.argv)==2 and sys.argv[1]in actions,'closed source-only record action');actions[sys.argv[1]]()
