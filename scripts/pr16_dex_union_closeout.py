#!/usr/bin/env python3
"""Union Chat受入recordの終端と固定text全byteを確認。追加native/ARM/host0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
from pr16_dex_union_ui import need,identity,write
BASE='4248b965930010167bdedb5b07986f90d01e3917';SOURCE='eecd1da4c9890304eb19222cc205e1ac2fa86b38'
RUN=37252355438;JOB=111582411166;ARCHIVE=(11321735909,RUN,91587,'b443a9b9e7bfb6779e2e2c7fed1a3c26df622df1deaf2cb3eda4934507c9216e')
WF='.github/workflows/pr16-dex-union-record.yml'
CODE={WF,'scripts/pr16_dex_union_closeout.py','.github/workflows/pr16-dex-union-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_union_checkpoint.json';GUIDE='docs/PR16_DEX_UNION_FAILURE_JA.md';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-union-closeout';PUBLIC=ROOT/'public-dex-union-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized closeout')
    p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    import pr16_dex_publication as publication
    current();publication.contract(ROOT,'.github/workflows/pr16-dex-union-closeout.yml',PUBLIC,'pr16-dex-union-closeout-receipts','scripts/pr16_dex_union_closeout.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists(),'one closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
    for p,b in protected.items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==b,'all prior accepted source retained '+p)
    old=git('show',BASE+':'+WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+WF+']\n').encode()
    need(identity(old)==protected[WF]and old.count(trigger)==1 and(ROOT/WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'completed record becomes manual only')
    r=t.api('actions/runs/'+str(RUN));j=t.api('actions/jobs/'+str(JOB))
    need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1 and j['run_id']==RUN and len(j['steps'])==12 and all(s['conclusion']=='success'for s in j['steps']),'record terminal all12success')
    import pr16_dex_publication as publication
    publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),'pr16-dex-union-record-receipts',RUN)
    z,_=t.archive(ARCHIVE)
    with z:need(z.namelist()==['union-record.json'],'one immutable receipt');raw=z.read('union-record.json')
    need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole checkpoint equals recorded original')
    cp=json.loads(raw)
    need(cp['candidate']['sha256']=='0180c1804cc368b30bc0ee63ec4f5743d46c707a9f88f45650c47edb375e5315'and cp['ui']['native_processes']==12 and cp['ancestor_isolated']['isolated']['cases']==1016 and cp['formatter_assertion_only']['raw_artifact_available']is False and cp['current_build']['link']['payload']['size']==408 and cp['union_failure_notification_accepted']and cp['union_fixture_bytes']==21 and cp['scheduler_subowners_restored']and cp['cold_input_fixture_derived']and not cp['old_mystery_candidate_allocation_accepted'],'exact accepted candidate only')
    need(not any(cp[k]for k in ('early_sector31_fault_accepted','sector31_atomicity_accepted','all_nonstart_notifications_accepted','hof_save_failed_repair_accepted','all_save_modes_accepted','all_consumers_wired','natural_entry_accepted','link_transaction_accepted','formal_rom_changed','formal_save_changed','normal_field_sprite_camera_accepted')),'scope not promoted')
    for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'all original evidence whole bytes')
    need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only terminal record pending');state['pending_runs']=[]
    receipt=dict(status='PASS_TERMINAL_UNION_FAILURE_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all12_record_steps_success=True,record_artifact=ARCHIVE[0],record_archive_size=ARCHIVE[2],record_archive_sha256=ARCHIVE[3],record_receipt_equals_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
    state['story_dex_owner']['runtime_integration']['union_failure']['recording']=receipt
    state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all12_record_steps_success=True,whole_receipt_equals_checkpoint=True)
    for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-UNION-FAILURE / Union Chat通知記録の終端\n- Version: dex-union-closeout\n- Status: STOPPED（安全な限定候補受入点。HOF/全非START/全mode/残consumer未完）\n- Summary: record run{RUN}/job{JOB}全12step成功とartifact{ARCHIVE[0]}のcheckpoint全文一致を確認しpending解除。成功済native/recordはmanual-onlyへ。\n- Files changed: closeout source/workflow、record起動条件、固定MDJSONと両ログ。\n- Verify: 全source/evidence/fixed resume/index/task graph PASS、host再試験0/ARM0/native0。前段原本はUnion1016/Mystery816/scheduler19、formatter168step成功はraw欠落/再走0、UI-only両caller各3条件/各cold12process30画像。候補0180c180、復元112owner/新113owner、正式ROM/Save101不変。\n- Boundary: Union21byte/Mystery11byte入口fixtureを自然通信/受信/削除/正規transitionやHOFへ昇格しない。cold入力もfixture由来。旧Mystery配置全体受入は撤回。次はHOF副作用/SaveFailed scratch/authority wipe、全mode/残typed consumer。早期sector31故障/原子性未受入。trainer131後半0。一般CI既知QOL不一致/Stage79cache/旧9月18日queueを別扱い。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActionsと既存text receiptのみ。ROM/入力save/runtime/runner/credentials追加公開0。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as out:out.write(entry)
    write(PUBLIC/'closeout.json',receipt)
    for n,p in [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE)]:(PUBLIC/n).write_bytes((ROOT/p).read_bytes())
    owned={STATE,*LOGS}
    if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
    write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole final committed source')
    receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
    for n,p in [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE)]:
        b=git('show','HEAD:'+p);need(b==(PUBLIC/n).read_bytes(),'whole artifact versus final committed text including newline');receipt['final_blobs'][p]=dict(**identity(b),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=b.endswith(b'\n'))
    for p in sorted(LOGS):
        b=git('show','HEAD:'+p);need(b==(ROOT/p).read_bytes()and b.endswith(b'\n'),'complete append-only log identity');receipt['final_blobs'][p]=dict(**identity(b),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=True)
    write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-UNION-FAILURE VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
    import pr16_dex_publication as publication
    publication.output(PUBLIC,success='closeout.json',failure=None)
    if not PUBLIC.exists():return
    need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated source snapshots')
    for p in PUBLIC.iterdir():
        need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json','fixed-state.json','fixed-resume.md','fixed-checkpoint.json','fixed-guide.md'},'only explicit snapshots')
        b=p.read_bytes();need(0<len(b)<(3500000 if p.name=='fixed-state.json'else 500000)and b.endswith(b'\n')and b'\0'not in b,'complete bounded UTF8');b.decode('utf8')
        if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed closeout');globals()[sys.argv[1]]()
