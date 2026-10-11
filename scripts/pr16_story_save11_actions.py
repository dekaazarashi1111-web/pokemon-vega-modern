#!/usr/bin/env python3
"""Save11新区間の初回測定と、native/test再実行なしの記録終端回収。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save11 as m
import pr16_story_save9_actions as transport
from pr16_learnset_compact_record import publish_resume
h,d=transport.h,transport.d
TASK='USER-20260928-STORY-SAVE11'
SELF='scripts/pr16_story_save11_actions.py'
WF='.github/workflows/pr16-story-save11.yml'
TWF='.github/workflows/pr16-story-save11-terminal.yml'
GUIDE='docs/PR16_STORY_SAVE11_JA.md'
WORK='content/modernization/pr16_story_save11_working.json'
OUT=ROOT/'.local/pr16-story-save11';PUBLIC=OUT/'public';ART=OUT/'checkpoint'
ARTNAME='pr16-story-save11-checkpoint'
CODE={SELF,WF,m.SOURCE,m.TEST,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt',m.DEV+'/verification.json'}
LOCAL_CODE={m.SOURCE:dict(size=13973,sha256='8f93e95a14c012630222d447c5e362ba83ae2e20b0c0fdc54e460670174a1a53'),m.TEST:dict(size=9389,sha256='09245dab1ad5b0190f3cebaadba803e00c813964dd03f53e8b9c522c5ef3fa76')}
LOCAL_UNIT=dict(size=8143,sha256='cf86c328856fc6434bdbfdbc35a2533b0cfbc6b5a3dffd4f47e4a8b866428dba')
GOAL='Save11のtraining.srm作業コピーから先だけ進める。501番道路map3/19(15,10)左向き。通常捕獲で手持ち1→2、ボール5→3、初投失敗/二投目成功を分離、通常Save10→11と独立Continue後の全Save/RTC保持を確認。リープンLv9/EXP450/HP16/26/PP35/30/22、ツツケラLv3/EXP27/HP4/15/PP33/38、RP0、2776円。次は2体の通常回復と育成を経てマオリ/通常ストーリーへ。トレーナー勝利/研究施設自然到達/全story/releaseは未完。地域図鑑No???・レポート図鑑1匹も観測履歴として保持し、図鑑統合を受入にしない。176/cold50と旧218/cold62等を再生しない。'
transport.m=m;transport.OUT=OUT;transport.PUBLIC=PUBLIC;transport.ART=ART
write,archive,invoke,preserve=transport.write,transport.archive,transport.invoke,transport.preserve
guard,snapshot=transport.guard,transport.snapshot


def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists(),'初回の新区間だけ')
    state=h.source_check();parent=d.read(ROOT/m.PARENT);m.parent_boundary(parent)
    m.need(d.bindings(LOCAL_CODE)==LOCAL_CODE,'ローカル68検査と同一source')
    review_raw=(ROOT/m.DEV/'verification.json').read_bytes();expected=m.review(review_raw)
    PUBLIC.mkdir(parents=True);ART.mkdir();(OUT/'private').mkdir()
    source=d.bindings(CODE);protected=d.bindings(d.PROTECTED)
    write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,accepted_case_reruns=0))
    command=(ROOT/m.DEV/'commands.txt').read_bytes();cold_command=(ROOT/m.DEV/'continue-commands.txt').read_bytes()
    for name,raw in (('commands.txt',command),('continue-commands.txt',cold_command)):
        m.commands(raw);m.need(m.identity(raw)==expected['files'][name],'固定した新入力だけ');(PUBLIC/name).write_bytes(raw)
    raw=archive(10970079659,36423498952,17781137,'2d9b381ca9b4e162a784a621b7335f396e281e9b171a34d0892765e18fdeee63')
    with h.safe_zip(raw,200000000) as z:
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.INPUT_SAVE)):
            value=z.read(name);m.need(m.identity(value)==binding,'Save10原本 '+name)
            target=OUT/'private/input.srm' if name=='training.srm' else OUT/name
            target.write_bytes(value);target.chmod(0o555 if name=='runner' else 0o444)
    raw=archive(10898620034,36218655601,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')
    runtime=OUT/'runtime';runtime.mkdir()
    with h.safe_zip(raw,300000000) as z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定runtime')
    seed=(OUT/'private/input.srm').read_bytes()
    first,saved=invoke(runtime,'progress',seed,command)
    (OUT/'private/training.srm').write_bytes(saved);preserve()
    m.need(m.identity(first)==expected['files']['progress.stdout.txt'] and m.identity(saved)==m.OUTPUT_SAVE,'開発176入力/全Save11の再現')
    second,cold=invoke(runtime,'continue',saved,cold_command)
    (OUT/'private/cold.srm').write_bytes(cold);(PUBLIC/'verification.json').write_bytes(review_raw);preserve()
    result=m.verify(first,second,command,cold_command,parent,review_raw,OUT/'progress',OUT/'continue')
    proof=m.saved_bytes(seed,saved,cold);write(PUBLIC/'save-byte-proof.json',proof)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save11.py','-v'],cwd=ROOT,env=dict(os.environ,PR16_SAVE11_ROOT=str(OUT)),capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==68 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新規68試験PASS/skip0')
    m.need(d.bindings(CODE)==source and d.bindings(set(state['source_bindings']))==state['source_bindings'] and d.bindings(d.PROTECTED)==protected,'受入原本とbaseline不変')
    for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('private/input.srm',m.INPUT_SAVE)):
        m.need(m.identity((OUT/name).read_bytes())==binding,'入力不変 '+name)
    write(PUBLIC/'measurement.json',dict(result=result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,focused_tests=68,new_native_processes=2,development_native_processes=2,development_focused_test_executions=68,development_unit_stderr=LOCAL_UNIT,development_source_bindings=LOCAL_CODE,accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,save_byte_proof=proof))
    preserve();print('PASS: 176/cold50新入力、83画面、68新検査、自然捕獲/Save11')


def checks(state,source):
    runs={}
    reply=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')
    for r in reply['workflow_runs']:runs[r['id']]=d.run_summary(r)
    for head in sorted({source,os.environ['GITHUB_SHA'],'39d05cd01972f398138e6763db18f9465ff2866f'}):
        reply=d.inputs.api('actions/runs?head_sha='+head+'&per_page=100')
        m.need(reply['total_count']==len(reply['workflow_runs'])<=100,'対象HEADの全Actions取得')
        for r in reply['workflow_runs']:runs[r['id']]=d.run_summary(r)
    for item in state.get('pending_runs',[]):
        r=d.inputs.api('actions/runs/'+str(item['run_id']));runs[r['id']]=d.run_summary(r)
    state['observed_head_checks']=dict(scope_head=source,runs=[runs[k] for k in sorted(runs)],reason_ja='branch最新30件・開始/測定/記録HEAD全件と旧pendingをAPI照合。一般CIのcapacity原本failure/action_requiredを成功へ改作しない。自己run終端は別途確認。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs.values() if r['status'] in ('queued','in_progress')]
    write(PUBLIC/'observed-actions.json',state['observed_head_checks'])


def publish(state,cp,owned,terminal=False):
    state['story_save11']={k:cp[k] for k in ('status','source_head','run_id','candidate','output_save','retained_artifact_id','actions_completion_confirmed','poke_balls','experience','level','party_count','captures','trainer_victories','natural_research_arrival_accepted')}
    state['story_save11']['path']=m.CP
    state['bp']['current_stop']=cp['status']
    goal=GOAL if terminal else 'native/68試験を再実行せず、今回Actionsの全step・83画面/Save原本artifact・記録commitを終端確認する。その後 '+GOAL
    state['next_action']=dict(state['next_action'],id='STORY_RECOVERY_AND_TRAINING_FROM_SAVE11_NEXT' if terminal else 'STORY_SAVE11_TERMINAL_COLLECTION_ONLY',goal_ja=goal,read_paths=[GUIDE,m.CP,WORK,m.SOURCE,m.TEST,SELF],stop_rule_ja='Save11原本の終端を先に照合。training.srmから先だけ。176/cold50や既受入218/cold62等を再生しない。捕獲を勝利/研究施設到達/図鑑統合へ昇格しない。')
    state['bp']['next_step']=state['next_action']['goal_ja']
    note='Save11の176/cold50入力と83画面・68検査は保存原本から照合し、通常進行再開では再実行しない。初投失敗/名前UI/捕獲outcome7を区別。次はHP16/26と4/15の2体を通常回復してから先へ。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=cp['source_head'];state['observed_head_semantics']='Save10後の新捕獲区間Save11の測定source HEAD。記録commit/active baselineではない。'
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    checks(state,cp['source_head']);state['logs_synchronized']=True;write(ROOT/m.CP,cp)
    for name in (owned|CODE|{m.CP}|({TWF} if terminal else set()))-{d.STATE,d.DOC}-d.LOGS:
        state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    verify='専用run全step・原本ZIP全83画面/Save/68検査/commitを照合。新native0/test0。' if terminal else '新176/cold50入力、83画面、7組の全画像一致、新68検査PASS。開発2process/68検査と正式2process/68検査を分離。'
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 最初の自然捕獲・Save11'+('終端確認' if terminal else '限定受入')+f'\n- Version: story-save11-v1\n- Status: DONE（自然捕獲/Save11限定。トレーナー/研究施設/図鑑統合/全story/release未受入）\n- Summary: 501番道路でツツケラLv3へ初投失敗・すいとる3回・二投目成功。ボール5→3、手持ち1→2、Save10→11、独立Continue後の全Save/RTC131088bytes保持。親bank57344bytes/未使用party400bytes保持。先頭個体のHP26→16/PP25→22の2bytesだけ変更。名前入力の寄道/地域図鑑No???/図鑑1匹を保持。\n- Files changed: Save11後継検証器/68試験/入力目視原本/Actions/証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画面は非tracked artifactのみ。\n- Verify: {verify} 保存完了はlock1、coldでfield復帰。バッグ左端80pixel差を全一致にしない。初期実装の未使用slot全ゼロ仮定は既存FF sentinelを保持する条件へ修正してから68検査PASS。旧受入再実行0、ROM/compile変更0。resume/task graph/scoped final indexを確認後にcommit。全体private guard/一般CI成功は主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push。WIP c9a3fbe2で停止点、df3708a3で検証sourceを先行保存。\n- Network: GitHub HEAD/Actions/artifactのみ。元Save10 run failureを保持。直接cloneのDNS失敗はconnector/保存contextで代替。merge/release/active baseline変更0。\n- Next: {goal}\n'
    for name in d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    write(OUT/'guard-base.json',os.environ['GITHUB_SHA']);write(OUT/'owned.json',sorted(owned|{m.CP,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();state=h.source_check();v=d.read(PUBLIC/'measurement.json')
    m.need(not (ROOT/m.CP).exists() and d.bindings(set(v['source_bindings']))==v['source_bindings'],'測定の一意な公開')
    checks(state,v['source_head'])
    base='content/modernization/pr16_story_save11_evidence/'+str(v['run_id']);dest=ROOT/base;dest.mkdir(parents=True);owned=set()
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text証拠だけ')
            target=dest/p.name;target.write_bytes(raw);owned.add(str(target.relative_to(ROOT)))
    write(dest/'manifest.json',d.bindings(owned));owned.add(base+'/manifest.json')
    cp=dict(v['result'],schema_version=1,status='PASS_STORY_SAVE11_PENDING_TERMINAL',source_head=v['source_head'],run_id=v['run_id'],source_bindings=v['source_bindings'],focused_tests=68,development_native_processes=2,development_focused_test_executions=68,actions_completion_confirmed=False,retained_artifact_name=ARTNAME,retained_artifact_id=None,parent_checkpoint=m.PARENT,parent_artifact=10970079659,runtime_artifact=10898620034,map=[3,19],xy=[15,10],rp=0,mode='continue-story',commands='quit\n',new_game_replay_required=False,evidence_manifest=base+'/manifest.json',host_compiles=0,arm_compiles=0,rom_changes=0,next_input='continue-story from Save11 training.srm; no replay of completed 176/cold50 inputs')
    guide='# Save11: 最初の自然捕獲・保存再開\n\n'+GOAL+'\n\n## 今回の受入範囲\n\n通常5個のボールを持つSave10から開始。野生ツツケラLv3へ最初の投球は失敗し、バッグで4個と戦闘継続を確認。すいとる3回でHPを減らして二投目に捕獲。成功表示・名前確認後のfield復帰・party1→2/outcome7・バッグ3個を結合。勝利/逃走/研究到達は加算しない。名前入力を空のまま決定した寄道も原本に保持。\n\nSave11はリープンLv9/EXP450/HP16/26、ツツケラLv3/EXP27/HP4/15。通常レポートの確認/上書き/7つの途中Flash/完了表示/counter11を分離。完了画面はlock1でありfield復帰とはしない。独立Continueのfield、両個体情報/能力/技・手持ち7組全画像一致、全131088Save/RTC保持で受入。バッグ80pixelの左端表示差は全画面一致ではない。\n\n## 保存byte境界\n\n前回bank57344bytes、未使用400partybytes保持。未使用slotには既存FF sentinelがあり、全ゼロへ改作しない。先頭個体の変更はHPとPPの2bytesだけ。残12ball枠/他4bag pocket/2776円/EXP450は不変。ledgerは時計/checksumの6bytesだけ。一般section checksum全種の追加受入ではない。\n\n## 未受入\n\n地域図鑑No???・レポート図鑑1匹の表示をそのまま保持し、図鑑全統合の受入には使わない。トレーナー勝利/マオリ/研究施設自然到達/全story/release未完。元Save10測定runの全体failure、旧WIP敗北、一般CIの既存capacity原本failureを成功へ改作しない。次は2体の通常回復/育成から。\n\n## 実行会計\n\n開発2process/68検査、正式2process/68検査を別計上。旧受入の明示再実行0、ROM/runner/compile変更0。新区間176/cold50入力/83画面が完了したら保存原本を回収し、終端記録のために再生しない。\n\n正式source `'+v['source_head']+'`、run '+str(v['run_id'])+'。全step/保存artifact/commit終端は別のAPI照合で確定する。\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    work=d.read(ROOT/WORK);work.update(status='FORMAL_MEASUREMENT_COMPLETE_TERMINAL_PENDING',superseded_by=m.CP,formal_native_processes=2,formal_focused_tests=68,development_focused_tests=68,formal_run_id=v['run_id'],formal_source_head=v['source_head'],development_source_bindings=LOCAL_CODE,development_unit_stderr=LOCAL_UNIT)
    write(ROOT/WORK,work);publish(state,cp,owned|{GUIDE,WORK});write(ART/'checkpoint.json',cp)


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/m.CP)
    m.need(cp['actions_completion_confirmed'] is False,'終端は一度だけ。native/test起動なし')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['run_id']))
    m.need(run['head_sha']==cp['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'測定run全体の成功')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    m.need(reply['total_count']==len(reply['jobs'])==1,'1つの必須job');job=reply['jobs'][0]
    m.need(job['name']=='capture' and job['conclusion']=='success' and len(job['steps'])>=10 and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'upload/postを含む全step成功')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    m.need(reply['total_count']==len(reply['artifacts'])==1,'保存artifact全件');meta=reply['artifacts'][0]
    m.need(meta['name']==ARTNAME and not meta['expired'] and meta['workflow_run']['head_sha']==cp['source_head'],'保存artifact source')
    raw=archive(meta['id'],cp['run_id'],meta['size_in_bytes'],meta['digest'].removeprefix('sha256:'))
    expected=m.review((ROOT/m.DEV/'verification.json').read_bytes())
    with h.safe_zip(raw,200000000) as z:
        completion=z.read('completion-head.txt').decode().strip()
        m.need(len(completion)==40 and all(c in '0123456789abcdef' for c in completion),'completion commit')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        m.need(cp==m.load(z.read('checkpoint.json')),'保存された測定checkpoint')
        m.need(m.identity(z.read('candidate.gba'))==m.CANDIDATE and m.identity(z.read('runner'))==m.RUNNER,'同一ROM/runner')
        proof=m.saved_bytes(z.read('input.srm'),z.read('training.srm'),z.read('cold.srm'))
        for name,binding in expected['files'].items():m.need(m.identity(z.read('public/'+name))==binding,'原本 '+name)
        for name,command,seed in (('progress','commands.txt',m.INPUT_SAVE),('continue','continue-commands.txt',m.OUTPUT_SAVE)):
            parsed=m.trace(z.read('public/'+name+'.stdout.txt'),z.read('public/'+command),seed)
            for s in parsed['screens']:m.screen_bytes(z.read(name+f'/screen-{s["screen"]:04d}.ppm'),s)
        unit=z.read('public/unit.stderr.txt')
        m.need(unit.count(b' ... ok\n')==68 and b'\nOK\n' in unit and not z.read('public/unit.stdout.txt'),'実68試験原本')
        with h.safe_zip(z.read('record.zip'),100000000) as r:
            for name in r.namelist():m.need(d.git('show',completion+':'+name)==r.read(name),'commit text読戻し '+name)
    receipt='content/modernization/pr16_story_save11_terminal.json'
    write(ROOT/receipt,dict(run=d.run_summary(run),job=job,artifact=meta,completion_head=completion,save_byte_proof=proof,new_native_processes=0,new_test_executions=0))
    cp.update(status='PASS_STORY_SAVE11_SCOPED',actions_completion_confirmed=True,retained_artifact_id=meta['id'],completion_head=completion,terminal_receipt=receipt)
    work=d.read(ROOT/WORK);work.update(status='FORMAL_TERMINAL_CONFIRMED',actions_completion_confirmed=True,retained_artifact_id=meta['id']);write(ROOT/WORK,work)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write('\n## 正式終端\n\nrun '+str(cp['run_id'])+' の全step成功、completion `'+completion+'`、原本artifact '+str(meta['id'])+'。次はこのartifactのtraining.srmのみ。終端回収native0/test0。\n')
    publish(state,cp,{receipt,WORK,GUIDE},True)


if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,snapshot=snapshot,preserve=preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
