#!/usr/bin/env python3
"""Close terminal placement record and export its already committed text receipt."""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as api
import pr16_story_route_probe as publication
from pr16_story_after_maori import need,identity,write
BASE='f6e00fa3d556fd5930ecc517a55174da5be44b33';SOURCE='8db8f096d4bdbec6c4f2388e78121e45a390ab56'
RUN=37223939077;JOB=111499616811
WF='.github/workflows/pr16-dex-placement-record.yml'
CODE={'scripts/pr16_dex_placement_closeout.py','.github/workflows/pr16-dex-placement-closeout.yml',WF}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_placement_checkpoint.json';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-placement-closeout';PUBLIC=ROOT/'public-dex-placement-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','single authorized closeout')
    p=api.api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole exact draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as g
    current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists(),'one terminal closeout');(OUT/'receipts').mkdir(parents=True)
    state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
    for p,b in protected.items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==b,'accepted source unchanged '+p)
    old=git('show',BASE+':'+WF);new=(ROOT/WF).read_bytes()
    need(identity(old)==protected[WF] and old.count(b'path: public-dex-capacity-record')==1 and new==old.replace(b'path: public-dex-capacity-record',b'path: public-dex-placement-record').replace(b'  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: [.github/workflows/pr16-dex-placement-record.yml]\n',b'  workflow_dispatch:\n'),'only receipt upload path corrected and finished record made manual-only')
    r=api.api('actions/runs/'+str(RUN));j=api.api('actions/jobs/'+str(JOB))
    need(r['head_sha']==SOURCE and r['status']=='completed' and r['conclusion']=='success' and r['run_attempt']==1,'terminal exact record run')
    need(j['run_id']==RUN and j['conclusion']=='success' and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'all12 record steps success')
    artifacts=api.api('actions/runs/'+str(RUN)+'/artifacts');need(artifacts['total_count']==0,'record receipt artifact absent due to preserved wrong path')
    cp=(ROOT/CP).read_bytes();need(cp==git('show',BASE+':'+CP),'whole immutable committed checkpoint readback');checkpoint=json.loads(cp)
    need(checkpoint['record_source']==SOURCE and checkpoint['record_run']==RUN and checkpoint['stage61_input_tests']==12 and checkpoint['accepted_native_processes']==1 and checkpoint['native_attempt_processes']==3,'committed measured record scope')
    for p,b in checkpoint['evidence_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'whole original evidence '+p)
    need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only finished record pending');state['pending_runs']=[]
    receipt=dict(run=RUN,job=JOB,source=SOURCE,completion=BASE,all12_steps_success=True,checkpoint=CP,checkpoint_identity=identity(cp),record_artifact_missing_reason='export/upload path mismatch; committed checkpoint/evidence retained',receipt_recovered_by_closeout=True,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,formal_rom_changed=False,formal_save_changed=False)
    state['story_dex_owner']['runtime_integration']['placement']['recording']=receipt
    state['observed_head_checks']=dict(scope_head=SOURCE,placement_run=37223181964,record_run=RUN,all12_record_steps_success=True,general_ci_known_source_mismatch_not_resolved=True,game_hooks_installed=False,reason_ja='図鑑実配置run37223181964は全10step成功。24entry・24API ARM/EWRAM対照を受入、正式ROM/Save101は不変。記録run37223939077全12stepと固定MDJSON/両ログを読戻し、元24macro/99sized symbol/4aliasの12testsを照合。record upload path不一致でartifact0だったため、既存commitのcheckpointをcloseoutで再公開。旧host/ARM/native再実行0。一般CI既知QOL source不一致とStage79 cacheは別扱い。')
    for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-PLACEMENT / 実配置記録の終端とreceipt公開\n- Version: dex-placement-v1-closeout\n- Status: DONE（実配置ABIの記録終端。保存scheduler/全consumer接続は未完）\n- Summary: record run{RUN}/job{JOB}全12step、固定MDJSON/両ログ・原本evidenceを全byte/hash照合。upload pathがexport先と不一致でartifact0件だったため訂正し、完了済記録の自動再実行を止めて、既存commit checkpointを再公開。pending解除。\n- Files changed: closeout source/workflow、record upload pathと完了済記録のmanual-only化、固定MDJSON、両ログ。\n- Verify: terminal/source bindings/resume/task graph/index guard PASS。host再試験0/ARM0/native0/正式ROM・Save変更0。初回nativeのsignal位置は未採取、次回は全24完了後のcore二重freeと確定して修正、失敗原本を成功へ改作しない。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActionsとcommitのみ。cleanup一次source https://raw.githubusercontent.com/mgba-emu/mgba/0.10.2/src/gba/core.c 。旧9月18日queueは非操作、一般CIのQOL source不一致は残件。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as f:f.write(entry)
    for p,b in protected.items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==b,'all unaffected accepted source unchanged '+p)
    (OUT/'receipts/placement-record.json').write_bytes(cp);write(OUT/'receipts/placement-closeout.json',receipt)
    owned={STATE,*LOGS}
    if(ROOT/DOC).read_bytes()!=git('show','HEAD:'+DOC):owned.add(DOC)
    write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def export():
    if(OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',PUBLIC)
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole closeout committed text')
    print('RESULT=STOPPED TASK=USER-20261004-DEX-PLACEMENT VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','export','snapshot'),'bounded closeout action');globals()[sys.argv[1]]()
