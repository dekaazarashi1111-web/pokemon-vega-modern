#!/usr/bin/env python3
"""Save13の初回新区間測定と、native/test再実行なしの終端回収。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save13 as m
import pr16_story_save9_actions as transport
from pr16_learnset_compact_record import publish_resume
h,d=transport.h,transport.d
TASK='USER-20260928-STORY-SAVE13'
SELF='scripts/pr16_story_save13_actions.py'
WF='.github/workflows/pr16-story-save13.yml'
TWF='.github/workflows/pr16-story-save13-terminal.yml'
GUIDE='docs/PR16_STORY_SAVE13_JA.md'
WORK='content/modernization/pr16_story_save13_working.json'
OUT=ROOT/'.local/pr16-story-save13';PUBLIC=OUT/'public';ART=OUT/'checkpoint'
ARTNAME='pr16-story-save13-checkpoint'
CODE={SELF,WF,m.SOURCE,m.TEST,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt',m.DEV+'/verification.json'}
LOCAL_CODE={m.SOURCE:dict(size=13894,sha256='93660b11320a6f326099ddccb763686364e49e065d191694d7394253e7881de8'),m.TEST:dict(size=11272,sha256='b67129123da8b7fd191f1c2ef6ecb3a3c8a1a8b7ac5165d3e8044360513f8027')}
LOCAL_UNIT=dict(size=11337,sha256='eb9c7b56a9c7863e7befad82e71423e250e8989bf51ab7aa84ed2b6f184bec2b')
GOAL='Save13のtraining.srm作業コピーから先だけ進める。自宅map4/0(8,5)上向き、先頭ツツケラLv4/EXP80/HP17/17/PP35/40、2番目リープンLv9/EXP479/HP26/26/PP35/30/25。通常並替・戦闘中の通常交代でスバメLv4に1勝し、53/29EXPを獲得。母親で通常回復、Save12→13と独立Continue後の全Save/RTC保持を確認。手持ち2、ボール3、2776円、RP0。次は必要な通常育成を続けてマオリ/通常ストーリーへ。トレーナー勝利/研究施設自然到達/図鑑統合/全story/release未完。255/cold40、受入済みSave12の153/cold40、Save11の176/cold50等を再生しない。'
transport.m=m;transport.OUT=OUT;transport.PUBLIC=PUBLIC;transport.ART=ART
write,archive,invoke,preserve=transport.write,transport.archive,transport.invoke,transport.preserve
guard,snapshot=transport.guard,transport.snapshot

def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists(),'初回の新区間だけ')
    state=h.source_check();parent=d.read(ROOT/m.PARENT);m.parent_boundary(parent)
    m.need(d.bindings(LOCAL_CODE)==LOCAL_CODE,'ローカル95検査と同一source')
    review_raw=(ROOT/m.DEV/'verification.json').read_bytes();expected=m.review(review_raw)
    PUBLIC.mkdir(parents=True);ART.mkdir();(OUT/'private').mkdir()
    source=d.bindings(CODE);protected=d.bindings(d.PROTECTED)
    write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,accepted_case_reruns=0))
    command=(ROOT/m.DEV/'commands.txt').read_bytes();cold_command=(ROOT/m.DEV/'continue-commands.txt').read_bytes()
    for name,raw in (('commands.txt',command),('continue-commands.txt',cold_command)):
        m.commands(raw);m.need(m.identity(raw)==expected['files'][name],'固定した新入力だけ');(PUBLIC/name).write_bytes(raw)
    raw=archive(10975157558,36435307920,18553083,'e7d24ce43937d2f444db65eec1268a54da27d36b41380649855cff9814d2c75d')
    with h.safe_zip(raw,200000000) as z:
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.INPUT_SAVE)):
            value=z.read(name);m.need(m.identity(value)==binding,'Save12原本 '+name)
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
    m.need(m.identity(first)==expected['files']['progress.stdout.txt'] and m.identity(saved)==m.OUTPUT_SAVE,'開発255入力/全Save13の再現')
    second,cold=invoke(runtime,'continue',saved,cold_command)
    (OUT/'private/cold.srm').write_bytes(cold);(PUBLIC/'verification.json').write_bytes(review_raw);preserve()
    result=m.verify(first,second,command,cold_command,parent,review_raw,OUT/'progress',OUT/'continue')
    proof=m.saved_bytes(seed,saved,cold);write(PUBLIC/'save-byte-proof.json',proof)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save13.py','-v'],cwd=ROOT,env=dict(os.environ,PR16_SAVE13_ROOT=str(OUT)),capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==95 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新規95試験PASS/skip0')
    m.need(d.bindings(CODE)==source and d.bindings(set(state['source_bindings']))==state['source_bindings'] and d.bindings(d.PROTECTED)==protected,'受入原本とbaseline不変')
    for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('private/input.srm',m.INPUT_SAVE)):
        m.need(m.identity((OUT/name).read_bytes())==binding,'入力不変 '+name)
    write(PUBLIC/'measurement.json',dict(result=result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,focused_tests=95,new_native_processes=2,development_native_processes=2,development_focused_test_executions=95,development_unit_stderr=LOCAL_UNIT,development_source_bindings=LOCAL_CODE,accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,save_byte_proof=proof))
    preserve();print('PASS: 255/cold40新入力、76画面、95新検査、通常交代の育成1勝/Save13')


def checks(state,source):
    runs={}
    reply=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')
    for r in reply['workflow_runs']:runs[r['id']]=d.run_summary(r)
    for head in sorted({source,os.environ['GITHUB_SHA'],'5a2e188f4b6ec938b224b0c96fbaaaf0111cefd4'}):
        reply=d.inputs.api('actions/runs?head_sha='+head+'&per_page=100')
        m.need(reply['total_count']==len(reply['workflow_runs'])<=100,'対象HEADの全Actions取得')
        for r in reply['workflow_runs']:runs[r['id']]=d.run_summary(r)
    for item in state.get('pending_runs',[]):
        r=d.inputs.api('actions/runs/'+str(item['run_id']));runs[r['id']]=d.run_summary(r)
    state['observed_head_checks']=dict(scope_head=source,runs=[runs[k] for k in sorted(runs)],reason_ja='branch最新30件・開始/測定/記録HEAD全件と旧pendingをAPI照合。一般CIのcapacity原本failure/action_requiredを成功へ改作しない。自己run終端は別途確認。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs.values() if r['status'] in ('queued','in_progress')]
    write(PUBLIC/'observed-actions.json',state['observed_head_checks'])


def publish(state,cp,owned,terminal=False):
    keys=('status','source_head','run_id','candidate','output_save','retained_artifact_id','actions_completion_confirmed','poke_balls','experience','level','hp','moves_pp','party_count','party_species','wild_victories','experience_gained_by_species','captures','trainer_victories','natural_research_arrival_accepted')
    state['story_save13']={k:cp[k] for k in keys};state['story_save13']['path']=m.CP
    state['bp']['current_stop']=cp['status']
    goal=GOAL if terminal else 'native/95試験を再実行せず、今回Actionsの全step・76画面/Save原本artifact・記録commitを終端確認する。その後 '+GOAL
    state['next_action']=dict(state['next_action'],id='STORY_TRAINING_AND_MAORI_FROM_SAVE13_NEXT' if terminal else 'STORY_SAVE13_TERMINAL_COLLECTION_ONLY',goal_ja=goal,read_paths=[GUIDE,m.CP,WORK,m.SOURCE,m.TEST,SELF],stop_rule_ja='Save13原本の終端を先に照合。training.srmから先だけ。完走255/cold40と受入済み153/cold40・176/cold50等を再生しない。野生1勝をトレーナー/研究施設到達へ昇格しない。')
    state['bp']['next_step']=goal
    note='Save13の255/cold40入力と76画面・95検査は保存原本から照合するだけ。ツツケラ先頭Lv4/EXP80とリープンEXP479、全回復済み。勝利残留flags4/outcome1・wire field:falseを追加勝利や未復帰にしない。次はSave13から先だけ。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=cp['source_head'];state['observed_head_semantics']='Save12後の通常交代育成区間Save13の測定source HEAD。記録commit/active baselineではない。'
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    checks(state,cp['source_head']);state['logs_synchronized']=True;write(ROOT/m.CP,cp)
    for name in (owned|CODE|{m.CP}|({TWF} if terminal else set()))-{d.STATE,d.DOC}-d.LOGS:
        state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    verify='専用run全step・原本ZIP全76画面/Save/95検査/commitを照合。新native0/test0。' if terminal else '新255/cold40入力、76画面、7組の全画像一致、新95検査PASS。開発2process/95検査と正式2process/95検査を分離。'
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常交代の育成1勝・Save13'+('終端確認' if terminal else '限定受入')+f'\n- Version: story-save13-v1\n- Status: DONE（通常交代育成1勝/Save13限定。マオリ/研究施設/図鑑統合/全story/release未受入）\n- Summary: Save12から通常並替でツツケラ先頭、野生スバメLv4へ通常交代しリープンのひっかく3回で勝利。ツツケラ53EXPでLv3→4/EXP80、リープン29EXPでEXP479。母親でHP9→26/PP32→35へ回復し通常Save12→13。独立Continue後の全131088Save/RTC、7組全画像、前回bank57344bytes/未使用party400bytes保持。並替を整列したparty14bytes変更と回復2bytesを分離。全5bag pocket/ボール3/2776円/RP0保持。\n- Files changed: Save13後継検証器/95試験/入力目視原本/Actions/証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画面は非tracked artifactのみ。\n- Verify: {verify} 単一戦闘14→30観測、経験値途中と勝利残留を分離。保存完了lock1と解除lock0、進行末尾wire field:falseとcold trueを保持。探索セルのfield真値仮定をcallback/lock判定へ訂正、nativeの再起動/追加入力なし。急所被弾・帰宅迂回・バッグ誤選択・図鑑No???/レポート1匹を原本へ保持。旧受入再実行0、ROM/runner/compile変更0。resume/task graph/scoped final index確認後にcommit。全体private guard/一般CI成功は主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push。WIP 5bed135cで停止点、c07dd98bで検証sourceを先行保存。\n- Network: GitHub HEAD/Actions/artifactのみ。Save12正式run36435307920と終端run36435622530の原本/compact contextを使用。旧capacity failure/action_requiredを成功へ改作しない。merge/release/active baseline変更0。\n- Next: {goal}\n'
    for name in d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    write(OUT/'guard-base.json',os.environ['GITHUB_SHA']);write(OUT/'owned.json',sorted(owned|{m.CP,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();state=h.source_check();v=d.read(PUBLIC/'measurement.json')
    m.need(not (ROOT/m.CP).exists() and d.bindings(set(v['source_bindings']))==v['source_bindings'],'測定の一意な公開')
    checks(state,v['source_head'])
    base='content/modernization/pr16_story_save13_evidence/'+str(v['run_id']);dest=ROOT/base;dest.mkdir(parents=True);owned=set()
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text証拠だけ')
            target=dest/p.name;target.write_bytes(raw);owned.add(str(target.relative_to(ROOT)))
    write(dest/'manifest.json',d.bindings(owned));owned.add(base+'/manifest.json')
    cp=dict(v['result'],schema_version=1,status='PASS_STORY_SAVE13_PENDING_TERMINAL',source_head=v['source_head'],run_id=v['run_id'],source_bindings=v['source_bindings'],focused_tests=95,development_native_processes=2,development_focused_test_executions=95,actions_completion_confirmed=False,retained_artifact_name=ARTNAME,retained_artifact_id=None,parent_checkpoint=m.PARENT,parent_artifact=10975157558,runtime_artifact=10898620034,map=[4,0],xy=[8,5],rp=0,mode='continue-story',commands='quit\n',new_game_replay_required=False,evidence_manifest=base+'/manifest.json',host_compiles=0,arm_compiles=0,rom_changes=0,next_input='continue-story from Save13 training.srm; no replay of completed 255/cold40 inputs')
    guide='# Save13: 通常交代の育成1勝・保存再開\n\n'+GOAL+'\n\n## 今回の受入範囲\n\nSave12から通常手持ちメニューでツツケラを先頭へ。501番道路の野生スバメLv4でリープンへ通常交代し、ひっかく3回で勝利。相手のなきごえ・つつく・急所とHP26→20→9も保持。ツツケラ53EXP/Lv3→4/EXP80とリープン29EXP/EXP479を別々の実表示で確認する。均等な経験値分配を仮定しない。帰宅して母親が通常回復。保存前/独立Continue後の先頭順とHP17/17・26/26、PP35/40と35/30/25、両個体の経験値と全能力を7組の全画面一致で結合する。\n\n## 勝利とfieldの境界\n\n開始観測14から戦闘UI・通常交代・3攻撃・経験値/レベル表示を経て観測30のFIELD callback/lock0を1勝とする。倒れた表示や経験値途中はoutcome0のままで終端ではない。その後のflags4/outcome1残留とwire field:falseを追加勝利や未復帰と数えない。保存完了はlock1、次の観測でlock0。fresh Continueはflags/outcome0・field:true。探索セルのfield真値仮定だけを訂正し、runner/ROM/原本ログを変更しない。\n\n## 保存byte境界\n\n通常Save12→13。前回bank57344bytesと未使用party400bytesを保持。並替後の個体を整列して比較した変更は14bytes、母親回復はリープンのHP/PPの2bytesだけ。全5bag pocket/ボール3/2776円/RP0は不変。ledgerは時計/checksumの5bytesのみ。独立Continue後の全131088Save/RTCを保持。一般section checksum全種の受入は主張しない。帰宅迂回とバッグ誤選択も元入力のまま残す。\n\n## 未受入\n\n新規トレーナー勝利/捕獲/敗北/逃走0。マオリ勝利/研究施設自然到達/全story/release未完。図鑑No???・レポート1匹を保持し図鑑統合の受入へ転用しない。元Save10 run failureと旧敗北・一般CIの既存capacity failure/action_requiredは歴史のまま。\n\n## 実行会計\n\n開発2process/95検査、正式2process/95検査を別計上。旧受入の明示再実行0、ROM/runner/compile変更0。完走255/cold40入力/76画面は原本回収だけにして再生しない。Save12の153/cold40、Save11の176/cold50等も再生しない。\n\n'+'正式source `'+v['source_head']+'`、run '+str(v['run_id'])+'。全step/保存artifact/commit終端は別API照合で確定する。\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    work=d.read(ROOT/WORK);work.update(status='FORMAL_MEASUREMENT_COMPLETE_TERMINAL_PENDING',superseded_by=m.CP,formal_native_processes=2,formal_focused_tests=95,development_focused_tests=95,formal_run_id=v['run_id'],formal_source_head=v['source_head'],development_source_bindings=LOCAL_CODE,development_unit_stderr=LOCAL_UNIT)
    write(ROOT/WORK,work);publish(state,cp,owned|{GUIDE,WORK});write(ART/'checkpoint.json',cp)


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/m.CP)
    m.need(cp['actions_completion_confirmed'] is False,'終端は一度だけ。native/test起動なし')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['run_id']))
    m.need(run['head_sha']==cp['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'測定run全体の成功')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    m.need(reply['total_count']==len(reply['jobs'])==1,'1つの必須job');job=reply['jobs'][0]
    m.need(job['name']=='training' and job['conclusion']=='success' and len(job['steps'])>=10 and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'upload/postを含む全step成功')
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
        m.need(unit.count(b' ... ok\n')==95 and b'\nOK\n' in unit and not z.read('public/unit.stdout.txt'),'実95試験原本')
        with h.safe_zip(z.read('record.zip'),100000000) as r:
            for name in r.namelist():m.need(d.git('show',completion+':'+name)==r.read(name),'commit text読戻し '+name)
    receipt='content/modernization/pr16_story_save13_terminal.json'
    write(ROOT/receipt,dict(run=d.run_summary(run),job=job,artifact=meta,completion_head=completion,save_byte_proof=proof,new_native_processes=0,new_test_executions=0))
    cp.update(status='PASS_STORY_SAVE13_SCOPED',actions_completion_confirmed=True,retained_artifact_id=meta['id'],completion_head=completion,terminal_receipt=receipt)
    work=d.read(ROOT/WORK);work.update(status='FORMAL_TERMINAL_CONFIRMED',actions_completion_confirmed=True,retained_artifact_id=meta['id']);write(ROOT/WORK,work)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write('\n## 正式終端\n\nrun '+str(cp['run_id'])+' の全step成功、completion `'+completion+'`、原本artifact '+str(meta['id'])+'。次はこのartifactのtraining.srmのみ。終端回収native0/test0。\n')
    publish(state,cp,{receipt,WORK,GUIDE},True)


if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,snapshot=snapshot,preserve=preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
