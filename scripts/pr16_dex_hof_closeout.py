#!/usr/bin/env python3
"""HOF受入recordの終端と固定text全byteを確認。追加native/ARM/host0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
from pr16_dex_hof_ui import need,identity,write
BASE='59b912e7d5b28bc75d5198c097d95b651d73fa47';SOURCE='8cf485c88fcd7fe961852f449c1cd51ffa56d6ed'
RUN=37255837504;JOB=111592593684;ARCHIVE=(11322388029,RUN,31710,'8696eb745737d4ab62b2a462ec6189bcc16a49a84c82b0c54ed51e5c811a075a')
WF='.github/workflows/pr16-dex-hof-record.yml'
CODE={WF,'scripts/pr16_dex_hof_closeout.py','.github/workflows/pr16-dex-hof-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_hof_checkpoint.json';GUIDE='docs/PR16_DEX_HOF_FAILURE_JA.md';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-hof-closeout';PUBLIC=ROOT/'public-dex-hof-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized closeout')
    p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    import pr16_dex_publication as publication
    current();publication.contract(ROOT,'.github/workflows/pr16-dex-hof-closeout.yml',PUBLIC,'pr16-dex-hof-closeout-receipts','scripts/pr16_dex_hof_closeout.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
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
    publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),'pr16-dex-hof-record-receipts',RUN)
    z,_=t.archive(ARCHIVE)
    with z:need(z.namelist()==['hof-record.json'],'one immutable receipt');raw=z.read('hof-record.json')
    need(raw==(ROOT/CP).read_bytes()==git('show',BASE+':'+CP),'whole checkpoint equals recorded original')
    cp=json.loads(raw)
    need(cp['candidate']['sha256']=='40ad82373b1e0f49283f59dce1e68a009b3e548d8f3ff080b72a134a228b0ac2'and cp['ui']['native_processes']==6 and cp['isolated']['isolated']['cases']==2880 and cp['isolated']['link']['payload']['size']==260 and cp['hof_failure_notification_accepted']and cp['hof_fixture_bytes']==9 and cp['cold_input_fixture_derived'],'exact HOF candidate limited scope')
    need(not any(cp[k]for k in('early_sector31_fault_accepted','sector31_atomicity_accepted','common_failure_all_callers_accepted','all_save_modes_accepted','all_consumers_wired','natural_entry_accepted','full_hof_species_abi_accepted','formal_rom_changed','formal_save_changed','all_cold_owners_preserved','hof_initial_save_atomicity_accepted','hof_automatic_retry')),'scope not promoted')
    need(cp['source_bindings'][GUIDE]==identity((ROOT/GUIDE).read_bytes())==state['source_bindings'][GUIDE],'whole final GUIDE and both current bindings agree')
    for p,b in cp['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'all original evidence whole bytes')
    need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only terminal record pending');state['pending_runs']=[]
    receipt=dict(status='PASS_TERMINAL_HOF_FAILURE_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all12_record_steps_success=True,record_artifact=ARCHIVE[0],record_archive_size=ARCHIVE[2],record_archive_sha256=ARCHIVE[3],record_receipt_equals_checkpoint=True,checkpoint=CP,checkpoint_identity=identity(raw),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
    state['story_dex_owner']['runtime_integration']['hof_failure']['recording']=receipt
    state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all12_record_steps_success=True,whole_receipt_equals_checkpoint=True)
    for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-FAILURE / HOF通知記録の終端\n- Version: dex-hof-closeout\n- Status: STOPPED（安全な限定候補受入点。初回mode3/全mode/共通残caller/typedconsumer未完）\n- Summary: record run{RUN}/job{JOB}全12step成功とartifact{ARCHIVE[0]}のcheckpoint全文一致を確認しpending解除。成功済native/recordはmanual-onlyへ。\n- Files changed: closeout source/workflow、record起動条件、固定MDJSONと両ログ。\n- Verify: 全source/evidence/fixed resume/index/task graph PASS、host再試験0/ARM0/native0。原本はHOF隔離2880条件/1process、9byte UI-only3条件/各cold6process15画像。候補40ad8237、既存113owner全byte保持/新114owner。正式ROM/Save101不変。\n- Boundary: HOF入口9byteは自然リーグ到達や正規transitionではない。初回mode3原子性/共通残caller・SaveFailed scratch/authority wipe、全mode/残typed consumer未完。主故障cold101のQOL ledger差は前Union/Mystery同caseと同一で、全coldowner保持を受入しない。早期sector31故障/原子性未受入。trainer131後半0。一般CI既知QOL不一致/Stage79cache/旧9月18日queueを別扱い。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActionsと既存text receiptのみ。ROM/入力save/runtime/runner/credentials追加公開0。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as out:out.write(entry)
    write(PUBLIC/'closeout.json',receipt)
    for n,p in [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]:(PUBLIC/n).write_bytes((ROOT/p).read_bytes())
    owned={STATE,*LOGS}
    if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
    write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole final committed source')
    receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
    for n,p in [('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]:
        b=git('show','HEAD:'+p);need(b==(PUBLIC/n).read_bytes(),'whole artifact versus final committed text including newline');receipt['final_blobs'][p]=dict(**identity(b),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=b.endswith(b'\n'))
    for p in sorted(LOGS):
        b=git('show','HEAD:'+p);need(b==(ROOT/p).read_bytes()and b.endswith(b'\n'),'complete append-only log identity');receipt['final_blobs'][p]=dict(**identity(b),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=True)
    write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-FAILURE VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
    import pr16_dex_publication as publication
    publication.output(PUBLIC,success='closeout.json',failure=None)
    if not PUBLIC.exists():return
    need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated source snapshots')
    for p in PUBLIC.iterdir():
        need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json','fixed-state.json','fixed-resume.md','fixed-checkpoint.json','fixed-guide.md','fixed-run-log.md','fixed-version-log.md'},'only explicit snapshots')
        b=p.read_bytes();need(0<len(b)<(3500000 if p.name in('fixed-state.json','fixed-run-log.md','fixed-version-log.md')else 1500000)and b.endswith(b'\n')and b'\0'not in b,'complete bounded UTF8');b.decode('utf8')
        if p.suffix=='.json':json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed closeout');globals()[sys.argv[1]]()
