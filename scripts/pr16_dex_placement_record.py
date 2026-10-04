#!/usr/bin/env python3
"""Record completed actual placement, recover original Stage61 inputs, retain scope."""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
import pr16_story_route_probe as publication
import pr16_dex_placement_actions as measured
import pr16_dex_placement as placement
import pr16_dex_stage61_inputs as stage61
need,identity,write=measured.need,measured.identity,measured.write
BASE=SOURCE='875ea6e86c462648548a5750f55baccfb9198d31'
RUN=37223181964;JOB=111497444702
ARCHIVE=(11310798064,RUN,19482,'a9de49054a20838d60d538de5789f05e3a0ca1b1af70198194ee75e3c41797ff')
CODE={'scripts/pr16_dex_placement_record.py','.github/workflows/pr16-dex-placement-record.yml',stage61.PROOF,'scripts/pr16_dex_stage61_inputs.py','tests/test_pr16_dex_stage61_inputs.py'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_placement_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_placement_evidence'
LOGS={'design/run_log.md','design/version_log.md'};OUT=ROOT/'.local/pr16-dex-placement-record'
FAILURES=[
    dict(run=37222498904,job=111495512598,source='1d7e1d9cd56afe626290529b30077911bc00a294',native_processes=0,reason='GNU-stack metadata warning rejected before native'),
    dict(run=37222659441,job=111495969860,source='a6055734ef35a64c475a0dc2af29864697d53bf5',native_processes=0,reason='Strict C11 harness missing POSIX PATH_MAX before native'),
    dict(run=37222833303,job=111496450744,source='bbd63b4a9d13afd380dad1dc3f30609992ed0c56',native_processes=1,reason='SIGSEGV with no flushed receipt; no API-stage completion inferred'),
    dict(run=37222998893,job=111496922202,source='d0c30d1e2de8a277da6ebb11fc7be268b526d416',native_processes=1,reason='All24 API receipt followed by cleanup SIGSEGV; mGBA deinit already frees core; run remains failure'),
]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','one authorized record attempt')
    p=transport.api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def record():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists() and not(ROOT/CP).exists(),'one new placement record');OUT.mkdir();(OUT/'receipts').mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'previous sources unchanged and prior runs closed')
    r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
    need(r['head_sha']==SOURCE and r['status']=='completed' and r['conclusion']=='success' and r['run_attempt']==1,'terminal exact placement run')
    need(j['run_id']==RUN and j['conclusion']=='success' and len(j['steps'])==10 and all(x['conclusion']=='success'for x in j['steps']),'all10 successful placement steps')
    for failed in FAILURES:
        old=transport.api('actions/runs/'+str(failed['run']));need(old['head_sha']==failed['source'] and old['status']=='completed' and old['conclusion']=='failure','retain original failed attempt')
    z,_=transport.archive(ARCHIVE)
    with z:
        need(set(z.namelist())=={'placement.json','native.json','host-tests.txt'},'only three placement text members')
        files={name:z.read(name)for name in z.namelist()}
    report=json.loads(files['placement.json']);native=json.loads(files['native.json'])
    need(report['source_head']==SOURCE and report['run_id']==RUN and report['status']=='PASS_ACTUAL_ALLOCATOR_LINK_AND_ISOLATED_NATIVE_ABI_GAME_UNWIRED','exact measured result')
    need(report['link']['payload']==dict(size=5022,sha256='0541f69c476c5d4faf8fb62fcfa923395d7ba70925844d928a9594869feaeda9') and report['link']['base']==placement.BASE and report['link']['reserved_suffix_bytes']==1462,'actual address complete linked payload identity')
    need(report['candidate']==dict(size=33554432,sha256='3cfbb21774c6a5bd695125d8f5a14d8d2872331a2f59cc6c7fb11c2b27a1c943') and report['formal_candidate']==placement.lease.CANDIDATE,'isolated candidate distinguished from formal')
    need(report['placement']['allocator_transferred'] and report['placement']['whole_rom_rollback_exact'] and report['placement']['diff']['changed_bytes']==4976,'actual transfer and complete bounded ROM diff')
    need(report['placement']['allocation']==placement.rebuild_allocation(report['placement']['allocation']) and len(report['placement']['allocation']['allocations'])==107,'canonical transferred allocator report')
    need(native==report['native'] and native['api_calls']==native['veneer_cases']==native['functional_cases']==24 and native['steps']==1613099 and native['native_processes']==native['fresh_cores']==1,'all24 actual API and veneer receipt')
    need(native['ewram_bytes_compared_per_case']==262144 and native['game_boots']==native['ordinary_saves']==0 and native['game_hooks_installed'] is False and native['story_progress_accepted'] is False,'isolated native boundary')
    need(report['host_tests']==26 and files['host-tests.txt'].count(b' ... ok\n')==26 and b'\nOK\n'in files['host-tests.txt'],'26 new placement tests evidence')
    for path,b in report['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b and identity(git('show',SOURCE+':'+path))==b,'whole measured source unchanged '+path)
    # Only new metadata validation. Do not recompile or repeat successful native APIs.
    folder=OUT/'metadata';folder.mkdir();proof=json.loads((ROOT/stage61.PROOF).read_bytes())
    metadata_raw=stage61.member(OUT,proof['archives'][0]);symbol_raw=stage61.member(OUT,proof['archives'][1])
    (folder/'61_critical_release_candidate_original.json').write_bytes(metadata_raw);(folder/'stage61_critical_release_candidate_symbols.json').write_bytes(symbol_raw)
    z,_=transport.archive(transport.SAVE24)
    with z:rom=z.read('candidate.gba')
    need(identity(rom)==placement.lease.CANDIDATE,'fixed private ROM metadata source');rom_path=OUT/'private-input.gba';rom_path.write_bytes(rom);rom_path.chmod(0o444)
    recovered=stage61.validate(proof,metadata_raw,symbol_raw,rom)
    env=dict(os.environ,VEGA_STAGE61_METADATA_DIR=str(folder),VEGA_DEX_ROM_PATH=str(rom_path))
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_stage61_inputs.py','-v'],cwd=ROOT,env=env,capture_output=True)
    need(test.returncode==0 and not test.stdout and test.stderr.count(b' ... ok\n')==12 and b'\nOK\n'in test.stderr,'12 new original metadata fail-closed tests')
    need(rom_path.read_bytes()==rom,'private fixed ROM remains exact')
    e=ROOT/EVIDENCE;e.mkdir()
    for name,raw in files.items():(e/name).write_bytes(raw)
    (e/'stage61-input-tests.txt').write_bytes(test.stderr);write(e/'stage61-input-validation.json',recovered)
    evidence={p.relative_to(ROOT).as_posix()for p in e.iterdir()}
    checkpoint=dict(schema_version=1,status=report['status'],source_head=SOURCE,run=RUN,job=JOB,all10_steps_success=True,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],actual_payload=report['link']['payload'],actual_address=placement.BASE,veneer_count=24,veneer_size=16,reserved_suffix_bytes=1462,isolated_candidate=report['candidate'],formal_candidate=report['formal_candidate'],allocator_transferred=True,allocator_owner_count=107,changed_bytes=4976,whole_rom_rollback_exact=True,host_tests=26,stage61_input_tests=12,stage61_recovered_inputs=stage61.PROOF,stage61_recovered=recovered,accepted_native_processes=1,native_attempt_processes=3,native_api_calls=24,failed_attempts=FAILURES,record_host_compiles=0,record_arm_compiles=0,record_native_processes=0,game_hooks_installed=False,save_scheduler_wired=False,consumer_wired=False,formal_save_changed=False,formal_save=101,release_ready=False,source_bindings=bindings(CODE|measured.CODE),evidence_bindings=bindings(evidence),record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']))
    write(ROOT/CP,checkpoint)
    goal=('正式ROM/Save101は不変。PR16_DEX_PLACEMENT_JA.mdとpr16_dex_placement_checkpoint.jsonから再開。'
        '退役T09 owner6484byteを実allocator移譲し0x09FC0998へ全API＋24veneer5022byteを配置、残1462byteを予約。'
        'run37223181964全10stepで26host/24API実ARM・各262144byte EWRAM対照を受入。ゲームhook/保存consumerは未接続。'
        'pr16_dex_stage61_relink_inputs.jsonに元assetから24macro/99sized symbol/4unsized aliasを回収し元code12568byteを全照合。'
        '次はStage61 existing-owner内の保存拡張。全44export位置・元data・次hotfix ownerを保ち、保存8入口だけを根拠に全codeを置換しない。'
        'validate_slot/inject_tail/expected_prepared_byte/tail_matches/load/clone/record-onlyを同世代MDXへ接続。'
        '署名前LinkFullを正規signature検査へ流さず、invalid liveはflash前拒否、復旧Save前にmain-bank MDX確定。'
        '全SID喪失前consumer/Bag count/reward clear/Factory-Codex rollback、候補限定Save/coldContinue・partial-write受入後だけ正式進行へ戻る。'
        '最終はシオウPokecenter通常回復/Save/coldContinue。雑魚戦ごとのSaveは作らない。')
    state['story_dex_owner']['runtime_integration']['placement']=dict(checkpoint=CP,guide='docs/PR16_DEX_PLACEMENT_JA.md',status=report['status'],run=RUN,source=SOURCE,allocator_transferred=True,actual_payload_bytes=5022,reserved_suffix_bytes=1462,isolated_native_accepted=True,save_scheduler_wired=False,consumer_wired=False,stage61_inputs=stage61.PROOF,record_run=int(os.environ['GITHUB_RUN_ID']))
    state['bp']['current_stop']='正式ROM/Save101保持。実allocator移譲と実アドレス全API/24veneer5022byteの隔離native ABI受入済み。Stage61全24macro/99symbol/4aliasを回収。ゲーム保存/consumer接続は未完。'
    state['bp']['next_step']=goal;state['next_action'].update(id='REPLACE_STAGE61_OWNER_AND_WIRE_DEX_CONSUMERS',goal_ja=goal,read_paths=['docs/PR16_DEX_PLACEMENT_JA.md',CP,stage61.PROOF,'docs/PR16_DEX_RUNTIME_INTEGRATION_JA.md','docs/PR16_DEX_CONSUMERS_JA.md'])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='図鑑実配置ABI受入と元Stage61入力の記録source。正式ROM/Save101不変、記録ARM0/native0。保存scheduler/全consumerは未接続。'
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['do_not_repeat'].append('図鑑実配置run37223181964の24API/24veneer隔離nativeを再実行しない。全107allocator中退役ownerだけ移管、payload5022/残1462。正式ROM/Save101不変。元Stage61 metadataはhash固定24macro/99sized symbol/4aliasを再利用し旧source再compile・元payload全体復元をしない。')
    state['source_bindings'].update(bindings(CODE|measured.CODE|evidence|{CP}));publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-PLACEMENT / 実allocator移管・24veneer・隔離ARM ABI\n- Version: dex-placement-v1\n- Status: STOPPED（実配置ABI受入済。ゲーム保存/全consumer接続は未完）\n- Summary: 旧T09 pointer owner6484byteのみ移管、全API/24固定veneerを0x09FC0998へ5022byte実配置、残1462byte予約。他106owner不変、4976変更byteはlease内、全ROMrollback一致。\n- Files changed: 専用placement source/harness/workflow、Stage61元macro/symbol復元proof/validator/12tests、checkpoint/evidence、固定MDJSON、両ログ。\n- Verify: run{RUN}/job{JOB}全10step成功。26host/1native core/24API/24veneer/各EWRAM262144bytes対照。4失敗runはfailure保持（初2native0、後2native1）、成功native1で計3attempt。記録では旧host再試験0/ARM0/native0。新Stage61 input12testsと元24macro/99sized symbol/4unsized alias/12568byte照合PASS。\n- Next: {goal}\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActionsと既存private-environment-v1 archive。mGBA0.10.2 core.cのdeinitがcoreをfreeする契約を一次sourceで確認。公開はsource/address/size/SHAと検査済textのみ。一般CI既知QOL source不一致、Stage79 cacheは新native扱いしない。\n'
    for path in LOGS:
        with(ROOT/path).open('a')as f:f.write(entry)
    need(bindings(protected)==protected,'all old accepted source bytes remain unchanged')
    owned={STATE,DOC,CP,*LOGS}|evidence;write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/placement-record.json',checkpoint);git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed text readback')
    print('RESULT=STOPPED TASK=USER-20261004-DEX-PLACEMENT VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
    if(OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',ROOT/'public-dex-placement-record')
if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'bounded record action');globals()[sys.argv[1]]()
