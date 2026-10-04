#!/usr/bin/env python3
"""記録runを閉じ、欠けたtext receiptだけを回復。native/既受入検証は再走しない。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as api
import pr16_story_route_probe as publication
from pr16_story_after_maori import need,identity,write
BASE='f79a3b5e32be3960d16c74f137d1d819b5c4a809'
CODE={'scripts/pr16_story_trainer_closeout.py','.github/workflows/pr16-story-trainer-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
LOGS={'design/run_log.md','design/version_log.md'};OUT=ROOT/'.local/pr16-story-trainer-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
    p=api.api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole live draft head')
def close():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists(),'one source-only closeout');OUT.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
    need(all(identity((ROOT/p).read_bytes())==b for p,b in protected.items()),'all accepted bytes preserved')
    r=api.api('actions/runs/37211680551');j=api.api('actions/jobs/111463968925')
    need(r['head_sha']=='96ae45bfc5e3297fe5071500f8822f0ab452606a' and r['status']=='completed' and r['conclusion']=='success' and r['run_attempt']==1,'completed exact recording run')
    need(j['run_id']==r['id'] and j['conclusion']=='success' and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'all12 record steps')
    need(api.api('actions/runs/37211680551/artifacts')['total_count']==0,'record receipt path warning has no artifact')
    need(state['pending_runs']==[dict(run_id=37211680551,status='in_progress',tested_head=r['head_sha'])],'only the completed run pending')
    state['pending_runs']=[]
    receipt=dict(record_run=37211680551,record_job=111463968925,record_source=r['head_sha'],record_completion=BASE,all12_steps_success=True,record_native_processes=0,record_compiles=0,original_receipt_artifact_missing=True,missing_reason='historical record workflow used public-story-route-record-receipts while export wrote public-story-trainer-record-receipts',recovery_source=os.environ['GITHUB_SHA'],recovery_run=int(os.environ['GITHUB_RUN_ID']),native_reruns=0,accepted_tests_reruns=0,rom_fragments_in_receipt=False)
    state['story_trainer_adapter']['recording']=receipt
    state['source_bindings'].update({p:identity((ROOT/p).read_bytes())for p in CODE});publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-STORY-TRAINER / 記録終端とreceipt回復\n- Status: DONE（記録終端・補助receipt回復。図鑑保存ABI本修復は未完）\n- Summary: record run37211680551/job111463968925の全12step成功とcommit{BASE}を確認。upload先の旧名残留により補助artifact0を記録し、正しい専用dirへhash/text receiptだけを別工程で出力。固定resume pending_runsを空へ。\n- Files changed: 専用closeout、固定resumeJSON/生成MD、両ログ。旧測定・記録sourceは凍結。\n- Verify: 固定source全hash/生成MD/task graph/index guard、正常terminal12step。native0/compile0/受入済み検証再走0。正式Save101不変、未保存trainer勝利0。\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非forcepush。\n- Network: 同repoActions終端読取と同branch更新のみ。ROM/Save/runtime/credential/ROM断片の再公開なし。一般CI既知QOL source不一致は未解決。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as f:f.write(entry)
    need(all(identity((ROOT/p).read_bytes())==b for p,b in protected.items()),'unchanged accepted sources after closeout')
    write(OUT/'receipt/record-completion.json',receipt);publication.export_evidence(OUT/'receipt',ROOT/'public-story-trainer-closeout-receipts');write(OUT/'owned.json',sorted({STATE,DOC,*LOGS}));git('add','--',STATE,DOC,*sorted(LOGS))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'exact committed closeout bytes')
    print('RESULT=STOPPED TASK=USER-20261004-STORY-TRAINER VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(close=close,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in actions,'bounded closeout action');actions[sys.argv[1]]()
