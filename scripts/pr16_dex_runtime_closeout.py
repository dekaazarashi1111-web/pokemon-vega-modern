#!/usr/bin/env python3
"""5UI寿命/host adapter記録runの終端を閉じる。試験・ARM・nativeは再実行しない。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as api
import pr16_story_route_probe as publication
from pr16_story_after_maori import need,identity,write
BASE='7e6451eec10b7cdf76aadac524ce28bdf8bf7665'
SOURCE='ada18f7e1fb9da89bb737517b8c2cc29b28ac24c'
RUN=37218128470;JOB=111482743441
CODE={'scripts/pr16_dex_runtime_closeout.py','.github/workflows/pr16-dex-runtime-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-runtime-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'
         and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'
         and os.environ['GITHUB_RUN_ATTEMPT']=='1','single authorized closeout')
    p=api.api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole exact draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists(),'one terminal closeout');OUT.mkdir();state=json.loads((ROOT/STATE).read_bytes())
    protected=dict(state['source_bindings']);need(all(identity((ROOT/p).read_bytes())==b for p,b in protected.items()),'all accepted source hashes')
    r=api.api('actions/runs/'+str(RUN));j=api.api('actions/jobs/'+str(JOB))
    need(r['head_sha']==SOURCE and r['status']=='completed' and r['conclusion']=='success' and r['run_attempt']==1,'terminal exact runtime record run')
    need(j['run_id']==RUN and j['conclusion']=='success' and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'all12 record steps')
    z,metadata=api.archive((11309133222,RUN,2952,'ca3a615a08dede4d9878cb4d71239e0cc347bd718a85334b2d910dfa4a6984f2'))
    with z:
        need(z.namelist()==['runtime-record.json'],'only public text receipt')
        raw=z.read('runtime-record.json');need(raw==(ROOT/'content/modernization/pr16_dex_runtime_checkpoint.json').read_bytes(),'whole receipt equals immutable checkpoint')
    need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only completed runtime record run pending')
    state['pending_runs']=[]
    receipt=dict(run=RUN,job=JOB,source=SOURCE,completion=BASE,all12_steps_success=True,
        artifact=11309133222,archive_size=2952,archive_sha256='ca3a615a08dede4d9878cb4d71239e0cc347bd718a85334b2d910dfa4a6984f2',
        receipt_whole_bytes_verified=True,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),
        host_tests_rerun=0,arm_compiles=0,native_processes=0,rom_changed=False,save_changed=False)
    state['story_dex_owner']['runtime_integration']['recording']=receipt
    state['observed_head_checks']=dict(scope_head=SOURCE,runtime_record_run=RUN,all12_steps_success=True,host_tests=102,
        general_ci_known_source_mismatch_not_resolved=True,runtime_wired=False,
        reason_ja='図鑑runtime専用run37218128470/job111482743441は全12step成功。102host試験、native5UI寿命の原本、Stage75 SID1670→owner925、ROM空き3151byteの監査を記録。receipt全byte一致。記録ARM0/native0/ROM変更0/Save変更0。全save/consumer接続とシオウ回復は未完。Stage79 cacheは新nativeではなく、一般CI QOL source不一致は未解決。')
    state['source_bindings'].update({p:identity((ROOT/p).read_bytes())for p in CODE});publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-RUNTIME / 5UI寿命とhost adapter記録の終端確認\n- Version: dex-runtime-foundation-v2-closeout\n- Status: DONE（記録終端のみ。保存ABIのROM接続/native受入は未完）\n- Summary: run{RUN}/job{JOB}全12step成功、102host試験と5UI寿命の記録commit{BASE}を照合。artifact11309133222の外側hashとreceipt全byteを確認しpendingを解除。\n- Files changed: 専用closeout、固定resumeMD/JSON、両ログ。\n- Verify: terminal/source bindings/resume/task graph/index guard PASS。host再試験0/ARM0/native0/ROM変更0/Save変更0。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions終端・小さい公開text receiptの読取。旧9月18日queueを操作しない。一般CI既知QOL source不一致は残件。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as f:f.write(entry)
    need(all(identity((ROOT/p).read_bytes())==b for p,b in protected.items()),'all previously accepted sources unchanged')
    owned={STATE,DOC,*LOGS};write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/closeout.json',receipt);git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def export():
    if (OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',ROOT/'public-dex-runtime-closeout-receipts')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed closeout text')
    print('RESULT=STOPPED TASK=USER-20261004-DEX-RUNTIME VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(source_guard=source_guard,close=close,guard=guard,export=export,snapshot=snapshot)
    need(len(sys.argv)==2 and sys.argv[1]in actions,'bounded terminal record action');actions[sys.argv[1]]()
