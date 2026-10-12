#!/usr/bin/env python3
"""外側QOL失敗の成功原本だけを再検証・記録。native/ARM再走はしない。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_outer_qol_actions as work
need,identity,write=work.need,work.identity,work.write
BASE='feb3e148244f7202ff69e3be90cbb8ed68c8dccc';RUN=37241791183;JOB=111551805055;ARCHIVE=(11317337794,RUN,83866,'e36da19aa3259abcde7bde8084d4a15c70ac68a0f90d023b1b3726a658999265')
RETRY_DIAGNOSTIC=(11317657676,37241264916,46809,'392e0d0b84d23d5a43095d3de4f4c5521e7b460ebafd6a1a4e9e288c8053a6f9')
DIAGNOSTIC=(11317647339,37241038917,601,'e6da8da54566db59f0e7609157e784ce6ccf430045a07856e3b4181eb1619e3d')
WF='.github/workflows/pr16-dex-outer-qol.yml'
CODE={'scripts/pr16_dex_outer_qol_record.py','.github/workflows/pr16-dex-outer-qol-record.yml',WF}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_outer_qol_checkpoint.json';GUIDE=work.GUIDE;EVIDENCE='content/modernization/pr16_dex_outer_qol_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-outer-qol-record';PUBLIC=ROOT/'public-dex-outer-qol-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized record')
    p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def record():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable record');OUT.mkdir(parents=True);PUBLIC.mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'prior accepted sources unchanged and terminal')
    r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB));need(r['status']=='completed'and r['conclusion']=='success'and r['head_sha']==BASE and j['run_id']==RUN and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'all10 measured steps terminal')
    z,_=t.archive(ARCHIVE)
    with z:files={n:z.read(n)for n in z.namelist()}
    need('measurement.json'in files and 'failure.json'not in files,'complete successful original')
    m=json.loads(files['measurement.json']);need(m['status']=='PASS_OUTER_QOL_RESULT_AND_LAST_BYTE_FAULT_RETRY_COLD'and m['source_head']==BASE and m['run_id']==RUN and m['native_processes']==4,'isolated plus UI plus two cold only')
    for p,b in m['source_bindings'].items():need(identity(git('show',BASE+':'+p))==b and(p==WF or identity((ROOT/p).read_bytes())==b),'measured sources exact '+p)
    old=git('show',BASE+':'+WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+WF+']\n').encode()
    need(old.count(trigger)==1 and(ROOT/WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'completed native trigger manual only')
    folder=OUT/'original';folder.mkdir()
    for n,b in files.items():
        p=Path(n);need(not p.is_absolute()and '..'not in p.parts and len(p.parts)<=2,'bounded paths');dest=folder/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    oldpublic=work.PUBLIC
    try:work.PUBLIC=folder;work.export()
    finally:work.PUBLIC=oldpublic
    need(work.validate_ui(files['fault/stdout.txt'],folder/'fault',m['candidate'])==m['trace'],'all input/state/pixel trace revalidated without native')
    need(json.loads(files['isolated-stdout.txt'])==m['isolated']and m['isolated']['cases']==7984 and m['isolated']['real_saves']==0 and not files['isolated-stderr.txt'],'outer7680 retry288 relocated-wipe16 isolated cases')
    need(json.loads(files['build.json'])=={k:m[k]for k in ('candidate','parent_candidate','link','placement')},'whole immutable build proof')
    need(m['placement']['unchanged_owners']==109 and m['placement']['outer_qol_epilogue_bytes']==4 and m['placement']['modified_owners']==['qol_production_stage36_payload','pr16_dex_save_failure_gates'] and m['placement']['whole_rom_rollback_exact']and m['placement']['allocation']['summaries']['allocation_count']==112 and m['placement']['allocation']['summaries']['overlap_count']==0,'exact bounded layout')
    for c in m['cold']:
        rows=[json.loads(x)for x in files['cold-'+str(c['counter'])+'/stdout.txt'].splitlines()]
        need([x for x in rows if 'observe'in x]==[c['observation']]and [x for x in rows if 'mdx'in x]==[c['mdx']]and [x for x in rows if 'outer_qol_ledger'in x]==[c['qol']]and rows[-1]==c['end']and c['input']==c['output'],'whole cold originals')
        need(work.ui.screens(rows,folder/('cold-'+str(c['counter'])))==c['screens'],'cold all pixels')
    need([c['counter']for c in m['cold']]==[102,103]and m['cold'][0]['input']==m['failed_save']and m['cold'][1]['input']==m['retried_save'],'already committed102 versus retry103')
    need(not any(m[k]for k in ('formal_rom_changed','formal_save_changed','all_save_modes_accepted','non_start_notifications_accepted','early_sector31_fault_accepted','sector31_atomicity_accepted')),'no scope promotion')
    evidence=ROOT/EVIDENCE;evidence.mkdir();paths=set()
    for n,b in files.items():
        if Path(n).suffix not in{'.json','.txt'}:continue
        dest=evidence/'measured'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(dest.relative_to(ROOT).as_posix())
    z,_=t.archive(DIAGNOSTIC)
    with z:
        need(set(z.namelist())=={'host-tests.txt','failure.json'},'old diagnostic files only')
        for n in z.namelist():
            b=z.read(n);dest=evidence/'placement-diagnostic'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(dest.relative_to(ROOT).as_posix())
        failure=json.loads(z.read('failure.json'));need(failure==dict(status='DIAGNOSTIC_NOT_ACCEPTED',type='ValueError',message='QOL owner exact preimage',native_processes=0,attempts=[]),'old native0 failure preserved')
    z,_=t.archive(RETRY_DIAGNOSTIC)
    with z:retryfiles={n:z.read(n)for n in z.namelist()}
    oldpublic=work.PUBLIC;retryfolder=OUT/'retry-diagnostic';retryfolder.mkdir()
    for n,b in retryfiles.items():
        p=Path(n);need(not p.is_absolute()and '..'not in p.parts and len(p.parts)<=2,'safe retry diagnostic paths');d=retryfolder/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b)
        if p.suffix in{'.json','.txt'}:
            dest=evidence/'retry-diagnostic'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(dest.relative_to(ROOT).as_posix())
    try:work.PUBLIC=retryfolder;work.export()
    finally:work.PUBLIC=oldpublic
    failure=json.loads(retryfiles['failure.json']);need(failure['status']=='DIAGNOSTIC_NOT_ACCEPTED'and failure['native_processes']==2 and failure['attempts']==['isolated','fault'],'failed real retry kept distinct')
    need(json.loads(retryfiles['isolated-stdout.txt'])['cases']==7680,'old isolated success preserved without promoting UI failure')
    with(ROOT/GUIDE).open('a')as out:
        out.write('\n## 受入原本\n\nrun'+str(RUN)+' / job'+str(JOB)+' / source'+BASE+'は全10step成功。候補'+m['candidate']['sha256']+'。隔離outer7680＋retry288＋移設wipe16case、通常START last-byte故障→エラー2頁→field→キー再保存102→103と独立cold102/103、計4process/7画面。画面は同run原本を目視・全byte照合。MDX522/拡張RAM20248/QOL ledger2048/sector31 payload4080byteの保持を確認し、早期sector31故障・原子性・非START通知・全modeへ拡張しない。詳細は`content/modernization/pr16_dex_outer_qol_checkpoint.json`。\n')
    cp=dict(schema_version=1,status='PASS_CANDIDATE_OUTER_QOL_STATUS_AND_LAST_BYTE_UI',source_head=BASE,run_id=RUN,job_id=JOB,archive=ARCHIVE,candidate=m['candidate'],measurement=m,source_bindings=bindings(work.CODE|CODE),evidence_bindings=bindings(paths),diagnostics=[dict(run=DIAGNOSTIC[1],artifact=DIAGNOSTIC[0],native_processes=0,status='FAILURE_PRESERVED_NOT_ACCEPTED'),dict(run=RETRY_DIAGNOSTIC[1],artifact=RETRY_DIAGNOSTIC[0],native_processes=2,isolated_cases=7680,status='RETRY_FAILURE_PRESERVED_NOT_ACCEPTED')],visual_review=dict(run=RUN,screens=7,review_ja='同run原本の第一頁「レポートが かけませんでした」、最終故障案内、前/失敗後/再保存後fieldとcold102/103を目視。全7画像SHA照合。追加native0。'),outer_result_contract_accepted=True,start_mode0_last_byte_fault_accepted=True,early_sector31_fault_accepted=False,sector31_atomicity_accepted=False,non_start_notifications_accepted=False,global_save_failed_owner_collision_resolved=False,all_save_modes_accepted=False,all_consumers_wired=False,formal_rom_changed=False,formal_save_changed=False,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0)
    write(ROOT/CP,cp)
    goal=('正式ROM/Save101保持。外側QOLの全出口non1をreturn/attempt255へ整合し、ensure早期拒否も閉じた。START mode0/main成功/bit31単独だけinner成功からouter再writeへ渡し、mask自体は消さない。START mode0のsector31最終byte限定故障はmain102確定→通常エラー2頁→field→キー再Save103、独立cold102/103とQOL ledger2048保持まで候補受入。'
    '次は非START返値無視callerの失敗通知と、SaveFailedのtiles16KiB/video-state/gDecompressionBuffer退避、HOF payload/回数増分、mode4/5 erase再試行重複、stale selector時authority wipeを安全契約として修復する。sector31早期故障/原子性とmode1/2/default/LinkFull固有副作用も未完。'
    'その後active capture/SetMonPokedexFlags、native授受/孵化/進化、UI/native count、acquisition/research/reward、reward clear、Factory memorial/Codex rollback、DexNavをSID喪失前に接続。全consumer/必要modeと影響native前に正式ROM切替・trainer131後半へ進めない。最終はシオウPokecenter通常回復/Save/coldContinue、雑魚毎Saveなし。')
    state['story_dex_owner']['runtime_integration']['outer_qol_failure']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=m['candidate'],native_run=RUN,native_job=JOB,record_run=int(os.environ['GITHUB_RUN_ID']),outer_result_contract_accepted=True,start_mode0_last_byte_fault_accepted=True,all_save_modes_accepted=False,early_sector31_fault_accepted=False,non_start_notifications_accepted=False,formal_save_changed=False)
    state['bp']['current_stop']='正式ROM/Save101保持。候補outerQOL result/attempt整合、START mode0の末尾sector31故障・通常error・キー再Save102→103・cold102/103を受入。非START通知/破壊的SaveFailed/全mode/残consumer未完。';state['bp']['next_step']=goal
    state['next_action'].update(id='CLOSE_NONSTART_FAILURE_AND_SAVE_MODE_CONTRACTS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_START_FAILURE_JA.md','docs/PR16_DEX_SAVE_FAILURE_JA.md','docs/PR16_DEX_CONSUMERS_JA.md'])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='outerQOL末尾byte故障の限定候補記録source。正式ROM/Save101不変。'
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['source_bindings'].update(bindings(work.CODE|CODE|paths|{CP}))
    state['do_not_repeat'].append(f'outerQOL run{RUN}隔離outer7680＋retry288＋移設wipe16case、START末尾physical131071故障の5画面＋cold102/103の2画面、全4process原本は無変更再走しない。旧run37241038917はhistorical allocation hash誤仮定/native0でfailure保持。全mode sweepはABIだけ、末尾故障をearly位置/sector31原子性/非START通知へ昇格しない。')
    state['observed_head_checks']=dict(scope_head=BASE,native_run=RUN,native_job=JOB,all10_steps_success=True,native_processes=4,isolated_cases=7984,all_save_modes_accepted=False,all_consumers_wired=False,non_start_notifications_accepted=False,early_sector31_fault_accepted=False,sector31_atomicity_accepted=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=state['bp']['current_stop'])
    publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-OUTER-QOL / 外側sector31保存の失敗伝播\n- Version: dex-outer-qol-v1\n- Status: DONE（共通statusとSTART mode0末尾故障だけ。非START/全mode未完）\n- Summary: QOL共通epilogue4byteを特殊tailへ接続しnon1→return255/attempt255。ensure早期拒否も整合。START mode0/main0/bit31単独だけmaskを消さずouter再writeへ到達。既存8byte frame/calleeを保持、共有helper/transaction bypass全byte不変。\n- Files changed: outer ASM/generator/署名/native/host/workflow、guide/CP/evidence、固定MDJSON、両ログ。\n- Verify: run{RUN}/job{JOB}全10step、隔離outer7680＋retry288＋移設wipe16case、START last-byte故障と通常エラー2頁/field/キー再Save102→103/独立cold102/103、計4process7画像。MDX522/拡張RAM20248/QOL ledger2048/sector31payload4080保持。112owner/overlap0、他109ownerと全未宣言ROM byte保持/全逆変換。記録ARM0/native0。\n- Correction: run37241038917は旧Stage36 allocationcontent_shaと現QOL69440byteの混同でnative0停止。formal全ROMから現領域SHAを独立固定し旧台帳と区別、failure原本維持。未実行cold helperのframe前方参照も明示引数へ訂正。run37241264916はisolated7680成功/実error2頁からのretry未完でnative2のfailure維持。後継でinnerのstale bit31遮断を修復。\n- Boundary: 非START返値無視/HOF payload/回数/erase再試行とSaveFailed owner衝突、全mode/残consumer、sector31早期故障/単bank原子性は未完。正式ROM/Save101不変・trainer131後半0。\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存入力/公式Ubuntu compiler。公開source/address-size-SHA/text/screensのみ、ROM/runtime/入力save/runner/credentials追加公開0。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as out:out.write(entry)
    need(bindings(protected)==protected,'prior accepted sources retained')
    owned={STATE,DOC,CP,GUIDE,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'outer-qol-record.json',cp);git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed source readback')
    print('RESULT=DONE TASK=USER-20261004-DEX-OUTER-QOL VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
    if not PUBLIC.exists():return
    need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated record receipt')
    for p in PUBLIC.iterdir():
        need(p.is_file()and not p.is_symlink()and p.name=='outer-qol-record.json','only known receipt');b=p.read_bytes();need(0<len(b)<500000 and b.endswith(b'\n')and b'\0'not in b,'complete bounded JSON');json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed record');globals()[sys.argv[1]]()
