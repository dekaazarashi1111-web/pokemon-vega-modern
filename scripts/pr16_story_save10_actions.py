#!/usr/bin/env python3
"""Save10新区間の初回正式測定と、nativeを再実行しない終端回収。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save10 as m
import pr16_story_save9_actions as transport
from pr16_learnset_compact_record import publish_resume
h,d=transport.h,transport.d
TASK='USER-20260928-STORY-SAVE10'
SELF='scripts/pr16_story_save10_actions.py'
WF='.github/workflows/pr16-story-save10.yml'
TWF='.github/workflows/pr16-story-save10-terminal.yml'
GUIDE='docs/PR16_STORY_SAVE10_JA.md'
WORK='content/modernization/pr16_story_save10_working.json'
BCP='content/modernization/pr16_story_journey_sequence_checkpoint.json'
OUT=ROOT/'.local/pr16-story-save10';PUBLIC=OUT/'public';ART=OUT/'checkpoint'
ARTNAME='pr16-story-save10-checkpoint'
CODE={SELF,WF,m.SOURCE,m.TEST,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt',m.DEV+'/verification.json'}
LOCAL_CODE={m.SOURCE:dict(size=12028,sha256='7bf533e53a8ea4c61860a0684a680d81889cf26540f92c625991c6bd68062928'),m.TEST:dict(size=9491,sha256='7a6a5b33b004f49b7d323985f880d97c949162c82bfb6babb2524bc55227cdde')}
LOCAL_UNIT=dict(size=4185,sha256='20b5fdce3fc337cbd198f9ccfa700876a37567b713951226fe1e2efeee7103f8')
GOAL='Save10のtraining.srm作業コピーから先だけ進める。501番道路の民家map32/2(4,3)下向き、モンスターボール5個。女性の通常贈与0→5、再会話の二重受取防止、通常Save9→10、独立Continue後の5個/再受取防止を確認。リープンLv9/EXP450/HP26/26/PP35/30/25、手持ち1、RP0、2776円。次は自然捕獲で手持ち拡充または追加育成を経てマオリ/通常ストーリーへ。捕獲/トレーナー勝利/研究活動施設自然到達/全story/releaseは未完。218/cold62と旧363/cold34等の受入区間を再生しない。'
# 保存/転送だけの既存関数を再利用。旧measure/record/terminalは呼ばない。
transport.m=m;transport.OUT=OUT;transport.PUBLIC=PUBLIC;transport.ART=ART
write,archive,invoke,preserve=transport.write,transport.archive,transport.invoke,transport.preserve
guard,snapshot=transport.guard,transport.snapshot


def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists(),'one new interval only')
    state=h.source_check();parent=d.read(ROOT/m.PARENT);m.parent_boundary(parent)
    m.need(d.bindings(LOCAL_CODE)==LOCAL_CODE,'exact locally tested source')
    review_raw=(ROOT/m.DEV/'verification.json').read_bytes();expected=m.review(review_raw)
    PUBLIC.mkdir(parents=True);ART.mkdir();(OUT/'private').mkdir()
    source=d.bindings(CODE);protected=d.bindings(d.PROTECTED)
    write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,accepted_case_reruns=0))
    command=(ROOT/m.DEV/'commands.txt').read_bytes();cold_command=(ROOT/m.DEV/'continue-commands.txt').read_bytes()
    for name,raw in (('commands.txt',command),('continue-commands.txt',cold_command)):
        m.commands(raw);m.need(m.identity(raw)==expected['files'][name],'fixed new input only');(PUBLIC/name).write_bytes(raw)
    raw=archive(10963436148,36408354430,18606567,'4cca4769455a8e0f5791c1bc38ef264332931fb8a71a0f5d99f8f3d94a9f789b')
    with h.safe_zip(raw,200000000) as z:
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.INPUT_SAVE)):
            value=z.read(name);m.need(m.identity(value)==binding,'Save9 member '+name)
            target=OUT/'private/input.srm' if name=='training.srm' else OUT/name
            target.write_bytes(value);target.chmod(0o555 if name=='runner' else 0o444)
    raw=archive(10898620034,36218655601,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')
    runtime=OUT/'runtime';runtime.mkdir()
    with h.safe_zip(raw,300000000) as z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
    seed=(OUT/'private/input.srm').read_bytes()
    first,saved=invoke(runtime,'progress',seed,command)
    (OUT/'private/training.srm').write_bytes(saved);preserve()
    m.need(m.identity(first)==expected['files']['progress.stdout.txt'] and m.identity(saved)==m.OUTPUT_SAVE,'developed progress/Save10 all bytes')
    second,cold=invoke(runtime,'continue',saved,cold_command)
    (OUT/'private/cold.srm').write_bytes(cold);(PUBLIC/'verification.json').write_bytes(review_raw);preserve()
    result=m.verify(first,second,command,cold_command,parent,review_raw,OUT/'progress',OUT/'continue')
    proof=m.saved_bytes(seed,saved,cold);write(PUBLIC/'save-byte-proof.json',proof)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save10.py','-v'],cwd=ROOT,env=dict(os.environ,PR16_SAVE10_ROOT=str(OUT)),capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==32 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'32 new actual tests')
    m.need(d.bindings(CODE)==source and d.bindings(set(state['source_bindings']))==state['source_bindings'] and d.bindings(d.PROTECTED)==protected,'accepted evidence/source and baseline unchanged')
    for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('private/input.srm',m.INPUT_SAVE)):
        m.need(m.identity((OUT/name).read_bytes())==binding,'immutable original '+name)
    write(PUBLIC/'measurement.json',dict(result=result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,focused_tests=32,new_native_processes=2,development_native_processes=2,development_focused_test_executions=32,development_unit_stderr=LOCAL_UNIT,development_source_bindings=LOCAL_CODE,accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,save_byte_proof=proof))
    preserve();print('PASS: new 218/cold62 inputs, 32 tests, 77 screens, ordinary balls5/Save10')


def checks(state,source):
    runs={}
    for head in sorted({source,os.environ['GITHUB_SHA'],'0912af7e71b89f48698256a1d0c2ec8fc084892c'}):
        reply=d.inputs.api('actions/runs?head_sha='+head+'&per_page=100')
        m.need(reply['total_count']==len(reply['workflow_runs'])<=100,'complete scoped Actions list')
        for r in reply['workflow_runs']:runs[r['id']]=d.run_summary(r)
    for item in state.get('pending_runs',[]):
        r=d.inputs.api('actions/runs/'+str(item['run_id']));runs[r['id']]=d.run_summary(r)
    state['observed_head_checks']=dict(scope_head=source,runs=[runs[k] for k in sorted(runs)],reason_ja='開始HEAD/今回source/記録sourceとpendingの実API。既存capacity原本の一般CI failureをsuccessへ改作せず、自己run終端は別途回収。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs.values() if r['status'] in ('queued','in_progress')]
    write(PUBLIC/'observed-actions.json',state['observed_head_checks'])


def boundary_terminal():
    cp=d.read(ROOT/BCP);m.need(cp['run_id']==36420363480 and cp['focused_tests']==28 and cp['actions_completion_confirmed'] is False,'boundary terminal not yet collected')
    run=d.inputs.api('actions/runs/36420363480');reply=d.inputs.api('actions/runs/36420363480/jobs?per_page=100')
    m.need(run['head_sha']==cp['source_head'] and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'boundary run success')
    m.need(reply['total_count']==len(reply['jobs'])==1,'one boundary job');job=reply['jobs'][0]
    m.need(job['name']=='boundary' and job['conclusion']=='success' and all(x['status']=='completed' and x['conclusion']=='success' for x in job['steps']),'all boundary steps')
    raw=archive(10969625772,36420363480,809496,'e36742829c0b1f1d1424a26aeffd0c03d3cb651da0bf72882db2520c717e9560')
    with h.safe_zip(raw,100000000) as z:
        completion=z.read('completion-head.txt').decode().strip();m.need(completion=='6bbab5cb0c70b53b9a8fd3e3d1e764e83bab06fc','boundary commit')
        m.need(m.identity(z.read('unit.txt'))==cp['unit'],'28-test immutable output')
        with h.safe_zip(z.read('record.zip'),100000000) as r:
            for name in r.namelist():m.need(d.git('show',completion+':'+name)==r.read(name),'boundary committed readback')
    receipt='content/modernization/pr16_story_journey_sequence_terminal.json'
    write(ROOT/receipt,dict(run=d.run_summary(run),job=job,artifact=d.read(PUBLIC/'artifact-10969625772.json'),completion_head=completion,new_native_processes=0,new_test_executions=0))
    cp.update(actions_completion_confirmed=True,completion_head=completion,terminal_receipt=receipt,retained_artifact_id=10969625772);write(ROOT/BCP,cp)
    return {BCP,receipt}


def publish(state,cp,owned,terminal=False):
    state['story_save10']={k:cp[k] for k in ('status','source_head','run_id','candidate','output_save','retained_artifact_id','actions_completion_confirmed','poke_balls','experience','level','trainer_victories','natural_research_arrival_accepted')}
    state['story_save10']['path']=m.CP
    if terminal:state['story_journey_sequence'].update(actions_completion_confirmed=True,retained_artifact_id=10969625772)
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='STORY_PARTY_EXPANSION_FROM_SAVE10_NEXT' if terminal else 'STORY_SAVE10_TERMINAL_COLLECTION_ONLY',goal_ja=GOAL if terminal else 'native/test再実行せず今回Actionsの全step・保存artifact・commitを先に終端確認。その後 '+GOAL,read_paths=[GUIDE,m.CP,WORK,m.SOURCE,m.TEST,SELF,BCP],stop_rule_ja='専用run/artifact終端を先に照合。後継Save10 training.srmのみ。218/cold62も旧Save9の363/cold34も再生しない。用品供給を捕獲/トレーナー勝利/研究施設到達へ昇格しない。')
    state['bp']['next_step']=state['next_action']['goal_ja']
    note='Save10の218/cold62と77画面・32検査は保存原本から照合し、通常進行の再開時に再実行しない。28境界検査も影響なしに再実行しない。前回未保存WIPの敗北は保持。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=cp['source_head'];state['observed_head_semantics']='新区間Save10の測定source HEAD。記録commit/active baselineではない。'
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    checks(state,cp['source_head']);state['logs_synchronized']=True;write(ROOT/m.CP,cp)
    for name in (owned|CODE|{m.CP}|({TWF} if terminal else set()))-{d.STATE,d.DOC}-d.LOGS:
        state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    verify='終端全step/保存ZIP全77画面/Save/32検査原本/commit照合。新規native0/test0。28境界原本の終端も回収。' if terminal else '新区間218/cold62入力・77画面・新規32検査PASS、開発2process/32検査と正式2process/32検査は別会計。'
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常用品供給・Save10'+('終端確認' if terminal else '限定受入')+f'\n- Version: story-save10-v1\n- Status: DONE（通常ボール5個/二重受取防止/Save10のみ。捕獲/トレーナー/全story/release未受入）\n- Summary: 501番道路の女性から通常0→5、再会話/独立Continue後も5。Save9→10、全Save/RTC131088bytes保持、旧bank57344bytes保持。徒歩友情+2以外599partybytes、他4bag pocket/2776円不変。12全画面一致、一覧358pixelはsprite animationのみ。\n- Files changed: Save10検証器/32検査/入力目視原本、専用Actions、証拠/checkpoint、固定引継ぎMD/JSON、専用guide、両ログ。\n- Verify: {verify} resume/task graph/scoped index/diff確認。既存一般CIのcapacity原本failureは保持、全体private guard PASSを主張しない。\n- Commit: source={cp["source_head"]}、measurement run={cp["run_id"]}、record run={os.environ["GITHUB_RUN_ID"]}。同branch非force commit/push。\n- Network: GitHub原本再利用。accepted native再実行/ROM変更/host/ARM compile/merge/release/baseline切替0。\n'
    for name in d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    write(OUT/'guard-base.json',os.environ['GITHUB_SHA']);write(OUT/'owned.json',sorted(owned|{m.CP,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();state=h.source_check();v=d.read(PUBLIC/'measurement.json')
    m.need(not (ROOT/m.CP).exists() and d.bindings(set(v['source_bindings']))==v['source_bindings'],'one measured publication')
    checks(state,v['source_head']);base='content/modernization/pr16_story_save10_evidence/'+str(v['run_id']);dest=ROOT/base;dest.mkdir(parents=True);owned=set()
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text only evidence');(dest/p.name).write_bytes(raw);owned.add(base+'/'+p.name)
    write(dest/'manifest.json',d.bindings(owned));owned.add(base+'/manifest.json')
    cp=dict(v['result'],schema_version=1,status='PASS_STORY_SAVE10_PENDING_TERMINAL',source_head=v['source_head'],run_id=v['run_id'],source_bindings=v['source_bindings'],focused_tests=32,development_native_processes=2,development_focused_test_executions=32,actions_completion_confirmed=False,retained_artifact_name=ARTNAME,retained_artifact_id=None,parent_checkpoint=m.PARENT,parent_artifact=10963436148,runtime_artifact=10898620034,map=[32,2],xy=[4,3],rp=0,party_count=1,mode='continue-story',commands='quit\n',new_game_replay_required=False,completed_segment_replay_required=False,evidence_manifest=base+'/manifest.json',host_compiles=0,arm_compiles=0,rom_changes=0,next_input='continue-story from Save10 training.srm; do not replay 218/cold62')
    write(ART/'checkpoint.json',cp)
    (ROOT/GUIDE).write_text('# Save10: 通常用品供給・保存再開\n\n'+GOAL+'\n\n## 受入原本\n\nsource `'+v['source_head']+'` / run '+str(v['run_id'])+'。新区間218/cold62、77画面、正式32検査PASS。開発2process/32検査とは別。終端は次のAPI回収で確認する。Save10 SHA-256 `'+m.OUTPUT_SAVE['sha256']+'`、131088bytes。\n\nバッグは再暗号化keyを解いてitem4×5のみ差分、他4pocket/残12ボール枠/2776円不変。Save9 bank57344bytesと徒歩友情104→106以外599partybytesを保持。Save10/coldの600partybytesと131088Save/RTCは一致。12組は全pixel一致、手持ち一覧の358pixel差はsprite animation矩形に限定し一覧全画面一致とはしない。Save完了画面の501番道路を正とし、502という開発時の呼称は訂正。贈与中の空画面に道具名を創作しない。初期研究室の図鑑評価を研究活動施設到達へ昇格しない。\n\n前回未保存WIPは docs/PR16_STORY_SAVE10_WIP_JA.md に保持。ROM/受入済み原本/基準は不変。終了済み区間を対話的に再生せず、測定後の記録回復はnative0で行う。一般CIの既存capacity原本failureは別途未解決。\n',encoding='utf-8')
    write(ROOT/WORK,dict(schema_version=1,status='FORMAL_MEASUREMENT_COMPLETE_TERMINAL_PENDING',superseded_by=m.CP,development_native_processes=2,development_focused_tests=32,development_unit_stderr=LOCAL_UNIT,development_source_bindings=LOCAL_CODE,formal_run_id=v['run_id'],formal_source_head=v['source_head'],prior_wip='docs/PR16_STORY_SAVE10_WIP_JA.md',prior_wip_accepted=False,result=v['result'],save_byte_proof=v['save_byte_proof']))
    publish(state,cp,owned|{GUIDE,WORK});preserve()


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/m.CP)
    m.need(cp['actions_completion_confirmed'] is False,'terminal once only');PUBLIC.mkdir(parents=True);ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['run_id']));reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    m.need(run['head_sha']==cp['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'successful measurement terminal')
    m.need(reply['total_count']==len(reply['jobs'])==1,'one supply job');job=reply['jobs'][0]
    m.need(job['name']=='supply' and job['conclusion']=='success' and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'all job steps including artifact/push')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    m.need(reply['total_count']==len(reply['artifacts'])==1,'one complete retained checkpoint');meta=reply['artifacts'][0]
    m.need(meta['name']==ARTNAME and not meta['expired'] and meta['workflow_run']['head_sha']==cp['source_head'],'retained source')
    raw=archive(meta['id'],cp['run_id'],meta['size_in_bytes'],meta['digest'].removeprefix('sha256:'))
    expected=m.review((ROOT/m.DEV/'verification.json').read_bytes())
    with h.safe_zip(raw,200000000) as z:
        completion=z.read('completion-head.txt').decode().strip()
        m.need(len(completion)==40 and all(c in '0123456789abcdef' for c in completion),'completion SHA')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        m.need(m.load(z.read('checkpoint.json'))==cp,'immutable measurement checkpoint')
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER)):
            m.need(m.identity(z.read(name))==binding,'retained immutable '+name)
        proof=m.saved_bytes(z.read('input.srm'),z.read('training.srm'),z.read('cold.srm'))
        for name,binding in expected['files'].items():m.need(m.identity(z.read('public/'+name))==binding,'retained input/trace '+name)
        for name,command,seed in (('progress','commands.txt',m.INPUT_SAVE),('continue','continue-commands.txt',m.OUTPUT_SAVE)):
            parsed=m.trace(z.read('public/'+name+'.stdout.txt'),z.read('public/'+command),seed)
            for s in parsed['screens']:m.screen_bytes(z.read(name+f'/screen-{s["screen"]:04d}.ppm'),s)
        unit=z.read('public/unit.stderr.txt');m.need(unit.count(b' ... ok\n')==32 and b'\nOK\n' in unit and not z.read('public/unit.stdout.txt'),'actual 32-test original')
        with h.safe_zip(z.read('record.zip'),100000000) as r:
            for name in r.namelist():m.need(d.git('show',completion+':'+name)==r.read(name),'committed text readback')
    receipt=dict(source_head=cp['source_head'],run_id=cp['run_id'],completion_head=completion,run=d.run_summary(run),job=job,artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},save_byte_proof=proof,new_native_processes=0,new_test_executions=0)
    name='content/modernization/pr16_story_save10_terminal.json';write(ROOT/name,receipt)
    cp.update(status='PASS_STORY_SAVE10_SCOPED',actions_completion_confirmed=True,retained_artifact_id=meta['id'],retained_artifact=receipt['artifact'],completion_head=completion,terminal_receipt=name)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write('\n## Actions終端確認済み\n\n全'+str(len(job['steps']))+'step成功、artifact '+str(meta['id'])+'、completion `'+completion+'`。全77画面/Save/32検査原本/commit text照合、native/test再実行0。正式再開はこのSave10だけ。\n')
    work=d.read(ROOT/WORK);work.update(status='FORMAL_TERMINAL_CONFIRMED',retained_artifact_id=meta['id'],actions_completion_confirmed=True);write(ROOT/WORK,work)
    owned=boundary_terminal();write(ART/'terminal.json',receipt);publish(state,cp,owned|{name,GUIDE,WORK},True)


if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,snapshot=snapshot,preserve=preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
