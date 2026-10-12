#!/usr/bin/env python3
"""新規Save14の初回正式測定/記録と、原本だけを読む終端回収。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save14 as m
import pr16_story_save13_actions as inherited
import pr16_story_save9_actions as transport
from pr16_learnset_compact_record import publish_resume
h,d=transport.h,transport.d
TASK='USER-20260929-STORY-SAVE14'
SELF='scripts/pr16_story_save14_actions.py'
WF='.github/workflows/pr16-story-save14.yml'
TWF='.github/workflows/pr16-story-save14-terminal.yml'
PREP='.github/workflows/pr16-story-save14-prepare.yml'
GUIDE='docs/PR16_STORY_SAVE14_JA.md'
WORK='content/modernization/pr16_story_save14_working.json'
OUT=ROOT/'.local/pr16-story-save14';PUBLIC=OUT/'public';ART=OUT/'checkpoint'
ARTNAME='pr16-story-save14-checkpoint'
CODE={SELF,WF,PREP,m.SOURCE,m.TEST,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt',m.DEV+'/verification.json'}
LOCAL_CODE={m.SOURCE:dict(size=14794,sha256='2315c2e7b17d5f91798aa876c5e44c8e9c9eda7699eb0845332b14a4f2e358b6'),m.TEST:dict(size=11708,sha256='c221e816421477ac860f37f8806f103ab50ba414eb5600062fd300344cd45466')}
LOCAL_UNIT=dict(size=11924,sha256='1a75b29b57451398c9926159eb17c7ec0b511baa6cbcdadb57b4c795da2076e2')
GOAL='Save14のtraining.srm作業コピーから先だけ進める。自宅map4/0(8,5)上向き、ツツケラLv4/EXP80/HP17/17/PP35/40、リープンLv9/EXP516（次Lv44）/HP26/26/PP35/30/25。手持ち2、ボール3、2776円、RP0。野生ツツケラ雌Lv5へ1勝、味方ツツケラひんし1、全滅0。母親で回復し通常Save13→14と独立Continue全Save/RTC保持を確認。飛行技はリープンに効果抜群だったため、危険な育成交代を漫然と反復せず通常育成/用品・手持ちを整えてマオリ/通常storyへ進む。トレーナー勝利/研究施設自然到達/図鑑統合/全story/release未完。新303/cold40とSave13の255/cold40等の受入済み区間を再生しない。'
transport.m=m;transport.OUT=OUT;transport.PUBLIC=PUBLIC;transport.ART=ART
write,archive,invoke,preserve=transport.write,transport.archive,transport.invoke,transport.preserve
guard,snapshot=transport.guard,transport.snapshot
inherited.PUBLIC=PUBLIC
checks=inherited.checks


def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists(),'初回の未受入新区間だけ')
    state=h.source_check();parent=d.read(ROOT/m.PARENT);m.parent_boundary(parent)
    m.need(d.bindings(LOCAL_CODE)==LOCAL_CODE,'ローカル110検査と同一source')
    review_raw=(ROOT/m.DEV/'verification.json').read_bytes();expected=m.review(review_raw)
    PUBLIC.mkdir(parents=True);ART.mkdir();(OUT/'private').mkdir()
    source=d.bindings(CODE);protected=d.bindings(d.PROTECTED)
    write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,accepted_case_reruns=0))
    command=(ROOT/m.DEV/'commands.txt').read_bytes();cold_command=(ROOT/m.DEV/'continue-commands.txt').read_bytes()
    for name,raw in (('commands.txt',command),('continue-commands.txt',cold_command)):
        m.commands(raw);m.need(m.identity(raw)==expected['files'][name],'固定した新入力だけ');(PUBLIC/name).write_bytes(raw)
    raw=archive(10976693019,36439214540,18633620,'0ac72978a6c431989f793395976c8c4540d7f39fc4eafe690ca3e1b24a1f726b')
    with h.safe_zip(raw,200000000) as z:
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.INPUT_SAVE)):
            value=z.read(name);m.need(m.identity(value)==binding,'Save13原本 '+name)
            target=OUT/'private/input.srm' if name=='training.srm' else OUT/name
            target.write_bytes(value);target.chmod(0o555 if name=='runner' else 0o444)
    raw=archive(10898620034,36218655601,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')
    runtime=OUT/'runtime';runtime.mkdir()
    with h.safe_zip(raw,300000000) as z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定runtime、compileなし')
    seed=(OUT/'private/input.srm').read_bytes()
    first,saved=invoke(runtime,'progress',seed,command)
    (OUT/'private/training.srm').write_bytes(saved);preserve()
    m.need(m.identity(first)==expected['files']['progress.stdout.txt'] and m.identity(saved)==m.OUTPUT_SAVE,'開発303入力とSave14全byte再現')
    second,cold=invoke(runtime,'continue',saved,cold_command)
    (OUT/'private/cold.srm').write_bytes(cold);(PUBLIC/'verification.json').write_bytes(review_raw);preserve()
    result=m.verify(first,second,command,cold_command,parent,review_raw,OUT/'progress',OUT/'continue')
    proof=m.saved_bytes(seed,saved,cold);write(PUBLIC/'save-byte-proof.json',proof)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save14.py','-v'],cwd=ROOT,env=dict(os.environ,PR16_SAVE14_ROOT=str(OUT)),capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==110 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新110試験PASS/skip0')
    m.need(d.bindings(CODE)==source and d.bindings(set(state['source_bindings']))==state['source_bindings'] and d.bindings(d.PROTECTED)==protected,'既受入sourceとbaseline不変')
    for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('private/input.srm',m.INPUT_SAVE)):
        m.need(m.identity((OUT/name).read_bytes())==binding,'入力不変 '+name)
    write(PUBLIC/'measurement.json',dict(result=result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,focused_tests=110,new_native_processes=2,development_native_processes=2,development_focused_test_executions=110,development_unit_stderr=LOCAL_UNIT,development_source_bindings=LOCAL_CODE,accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,save_byte_proof=proof))
    preserve();print('PASS: 新303/cold40、97画面、110検査、味方ひんし1/全滅0/野生1勝/Save14')


def publish(state,cp,owned,terminal=False):
    keys=('status','source_head','run_id','candidate','output_save','retained_artifact_id','actions_completion_confirmed','poke_balls','experience','level','hp','moves_pp','party_count','party_species','wild_victories','experience_gained_by_species','captures','trainer_victories','natural_research_arrival_accepted','party_faints','losses','normal_battle_switches','forced_replacements')
    state['story_save14']={k:cp[k] for k in keys};state['story_save14']['path']=m.CP
    state['bp']['current_stop']=cp['status']
    goal=GOAL if terminal else 'native/110試験を再実行せず、今回Actionsの全step・97画面/Save原本artifact・記録commitを終端確認する。その後 '+GOAL
    state['next_action']=dict(state['next_action'],id='STORY_TRAINING_AND_MAORI_FROM_SAVE14_NEXT' if terminal else 'STORY_SAVE14_TERMINAL_COLLECTION_ONLY',goal_ja=goal,read_paths=[GUIDE,m.CP,WORK,m.SOURCE,m.TEST,SELF],stop_rule_ja='Save14原本の終端を先に照合しtraining.srmから先だけ。303/cold40と旧255/cold40等は再生しない。味方ひんし1を全滅や経験値獲得にしない。野生1勝をトレーナー/研究施設到達へ昇格しない。')
    state['bp']['next_step']=goal
    note='Save14の303/cold40入力・97画面・110試験は保存原本から照合するだけ。ひんしツツケラのEXP80は不変、リープンEXP516、両個体回復済み。勝利残留を再計上せず、coldのRAM時刻差と全Save/RTC不変を分離。次はSave14から先だけ。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=cp['source_head'];state['observed_head_semantics']='Save13後のひんし交代・野生1勝・Save14測定source HEAD。記録commit/active baselineではない。'
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['logs_synchronized']=True;write(ROOT/m.CP,cp)
    for name in (owned|CODE|{m.CP}|({TWF} if terminal else set()))-{d.STATE,d.DOC}-d.LOGS:
        state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    verification='専用run全step・ZIP全97画面/Save/110試験/commitを照合。新native0/test0。' if terminal else '新303/cold40入力・97画面・7組全画像一致・新110検査PASS。開発2process/110検査と正式2process/110検査を分離。'
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Save14'+('終端確認' if terminal else '限定測定')+f'\n- Version: story-save14-v1\n- Status: DONE（Save14限定。'+('終端原本確認済み' if terminal else '全step終端の別API照合待ち')+'。マオリ/研究施設/図鑑統合/全story/release未受入）\n- Summary: Save13から野生ツツケラ雌Lv5へ通常交代2回。味方ツツケラがひんし、リープンへ通常の強制交代1回で1勝。全滅/捕獲/逃走0。ツツケラEXP80不変、リープン479→516。母親回復4bytesと最終party変更3bytesを分離。Save13→14、前回bank57344bytes/未使用party400bytes、全5bag pocket/ボール3/2776円/RP0保持。独立Continue全131088Save/RTCと7画面一致。RAM時計12→13分だけの差も証明。\n- Files changed: Save14後継検証器/110試験/入力・97目視原本/Actions/証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画像は非tracked artifactのみ。\n'+f'- Verify: {verification} 味方ひんし35/相手ひんし41/EXP42を終端とせずfield43だけで1勝。保存中81..84と完了85/解除86を分離。図鑑誤選択No???/7-1/レポート1匹も保持。resume/task graph/scoped final indexを確認し、一般CI全体成功や一般sector checksum対応は主張しない。旧受入再実行0、ROM/runner/compile変更0。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push/readback。WIP984ed574で停止点、04d0ae01/e48ab93f/b0d8c9b4で検証器/試験/目視原本を先行保存。\n- Network: GitHub HEAD/Actions/artifactのみ。Save13正式run36439214540/終端run36484123426を継承。一般CIの既存capacity failure/action_requiredは改作しない。merge/release/active baseline変更0。\n- Next: {goal}\n'
    for name in d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    write(OUT/'guard-base.json',os.environ['GITHUB_SHA']);write(OUT/'owned.json',sorted(owned|{m.CP,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();state=h.source_check();v=d.read(PUBLIC/'measurement.json')
    m.need(not (ROOT/m.CP).exists() and d.bindings(set(v['source_bindings']))==v['source_bindings'],'測定の一意な公開')
    checks(state,v['source_head'])
    base='content/modernization/pr16_story_save14_evidence/'+str(v['run_id']);dest=ROOT/base;dest.mkdir(parents=True);owned=set()
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'trackedはtext証拠だけ')
            target=dest/p.name;target.write_bytes(raw);owned.add(str(target.relative_to(ROOT)))
    write(dest/'manifest.json',d.bindings(owned));owned.add(base+'/manifest.json')
    cp=dict(v['result'],schema_version=1,status='PASS_STORY_SAVE14_PENDING_TERMINAL',source_head=v['source_head'],run_id=v['run_id'],source_bindings=v['source_bindings'],focused_tests=110,development_native_processes=2,development_focused_test_executions=110,actions_completion_confirmed=False,retained_artifact_name=ARTNAME,retained_artifact_id=None,parent_checkpoint=m.PARENT,parent_artifact=10976693019,runtime_artifact=10898620034,map=[4,0],xy=[8,5],rp=0,mode='continue-story',commands='quit\n',new_game_replay_required=False,evidence_manifest=base+'/manifest.json',host_compiles=0,arm_compiles=0,rom_changes=0,next_input='continue-story from Save14 training.srm; no replay of completed 303/cold40 inputs')
    guide='# Save14: ひんし交代・野生1勝・回復・保存再開\n\n'+GOAL+'\n\n## 観測と限定受入\n\nSave13から通常キーのみで501番道路へ。野生ツツケラ雌Lv5に通常交代2回、途中の交代メニュー取消も保持。つつくに弱いリープンがHP26→15→5、ツツケラも17→9→0となった。味方ひんし後にリープンを通常UIで出し、ひっかくで相手を倒して37EXP。味方ひんし1・全滅0・野生1勝を区別する。ツツケラLv4/EXP80に経験値は加算されず、リープンLv9/EXP516（次Lv44）。固定dataは改変せず実測だけを採用。\n\n## field・保存・時計境界\n\n観測12→43が一戦。味方ひんし35、相手ひんし41、経験値42はoutcome0。field callback/lock0の43で初めて1勝。戦闘後flags4/outcome1とwire field:falseの残留を新勝利や未復帰にしない。母親で66から回復。最終party変更はEXP2bytesと歩行friendship1byte、回復はHP/PP4bytes。前回Save13 bank57344bytesと未使用party400bytes、全5pocket/ボール3/2776円/RP0は不変。通常レポートの書込中81..84、完了表示85、field解除86を分離。独立Continueで手持ち順と両個体情報/能力/技7組の全画像一致、全Save/RTC131088bytes保持。RAM ledger時計は保存時12分からcold13分へ進むが、保存byteは同一。時計/checksum以外のownerを保持。一般sector checksum全種対応は主張しない。\n\n## 原本と未完範囲\n\n97画面を直接目視、OCRなし。図鑑の誤選択、見つけた7/捕まえた1、No???とレポート1匹を保存し、図鑑統合受入にしない。新規トレーナー勝利/捕獲/逃走/全滅0。マオリ勝利・研究施設自然到達・全story・releaseは未完。次の育成では飛行技への不用意な交代を避け、実際の相手/HP/順序を見て通常操作する。\n\n## 実行会計\n\n開発2process/110検査、正式2process/110検査を別計上。新303/cold40入力、23105/3054frames、97画面。旧受入の明示再実行0、ROM/runner/compile変更0。終端回収は原本のみでnative/test0。Save13の255/cold40やそれ以前の受入区間を再生しない。\n\n'+f'正式source `{v["source_head"]}`、run `{v["run_id"]}`。全step/原本artifact/記録commitは別API照合で確定する。\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    work=d.read(ROOT/WORK);work.update(status='FORMAL_MEASUREMENT_COMPLETE_TERMINAL_PENDING',superseded_by=m.CP,formal_native_processes=2,formal_focused_tests=110,development_focused_tests=110,formal_run_id=v['run_id'],formal_source_head=v['source_head'],development_source_bindings=LOCAL_CODE,development_unit_stderr=LOCAL_UNIT)
    write(ROOT/WORK,work);publish(state,cp,owned|{GUIDE,WORK});write(ART/'checkpoint.json',cp)


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/m.CP)
    m.need(cp['actions_completion_confirmed'] is False,'終端回収一度だけ、native/test0')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['run_id']))
    m.need(run['head_sha']==cp['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'測定run全体成功')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    m.need(reply['total_count']==len(reply['jobs'])==1,'必須job全件');job=reply['jobs'][0]
    m.need(job['name']=='training' and job['status']=='completed' and job['conclusion']=='success' and len(job['steps'])>=10 and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'upload/postを含む全step成功')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    m.need(reply['total_count']==len(reply['artifacts'])==1,'artifact全件');meta=reply['artifacts'][0]
    m.need(meta['name']==ARTNAME and not meta['expired'] and meta['workflow_run']['head_sha']==cp['source_head'],'artifact source一致')
    raw=archive(meta['id'],cp['run_id'],meta['size_in_bytes'],meta['digest'].removeprefix('sha256:'))
    expected=m.review((ROOT/m.DEV/'verification.json').read_bytes())
    with h.safe_zip(raw,200000000) as z:
        completion=z.read('completion-head.txt').decode().strip()
        m.need(len(completion)==40 and all(c in '0123456789abcdef' for c in completion),'completion SHA')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        m.need(cp==m.load(z.read('checkpoint.json')),'保存測定checkpoint一致')
        m.need(m.identity(z.read('candidate.gba'))==m.CANDIDATE and m.identity(z.read('runner'))==m.RUNNER,'同一ROM/runner')
        proof=m.saved_bytes(z.read('input.srm'),z.read('training.srm'),z.read('cold.srm'))
        for name,binding in expected['files'].items():m.need(m.identity(z.read('public/'+name))==binding,'全byte原本 '+name)
        parsed=[]
        for name,command,seed in (('progress','commands.txt',m.INPUT_SAVE),('continue','continue-commands.txt',m.OUTPUT_SAVE)):
            value=m.trace(z.read('public/'+name+'.stdout.txt'),z.read('public/'+command),seed);parsed.append(value)
            for s in value['screens']:m.screen_bytes(z.read(name+f'/screen-{s["screen"]:04d}.ppm'),s)
        m.semantic(*parsed,d.read(ROOT/m.PARENT))
        for a,b in m.PAIRS:m.need(z.read(f'progress/screen-{a:04d}.ppm')==z.read(f'continue/screen-{b:04d}.ppm'),'7組全画面一致')
        unit=z.read('public/unit.stderr.txt')
        m.need(unit.count(b' ... ok\n')==110 and b'\nOK\n' in unit and not z.read('public/unit.stdout.txt') and b'skipped' not in unit,'110試験原本/skip0')
        manifest=d.read(ROOT/cp['evidence_manifest'])
        for name,binding in manifest.items():
            data=z.read('public/'+Path(name).name)
            m.need(m.identity(data)==binding and d.git('show',completion+':'+name)==data,'manifestと記録commitの全公開text一致 '+name)
        with h.safe_zip(z.read('record.zip'),100000000) as r:
            for name in r.namelist():m.need(d.git('show',completion+':'+name)==r.read(name),'記録commit全text読戻し '+name)
    receipt='content/modernization/pr16_story_save14_terminal.json'
    write(ROOT/receipt,dict(run=d.run_summary(run),job=dict(id=job['id'],name=job['name'],status=job['status'],conclusion=job['conclusion'],steps=job['steps']),artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},completion_head=completion,save_byte_proof=proof,screen_count=97,full_image_comparisons=7,focused_tests_reexecuted=0,new_native_processes=0,accepted_case_reruns=0,record_text_readback=True,all_required_steps_succeeded=True))
    cp.update(status='PASS_STORY_SAVE14_SCOPED',actions_completion_confirmed=True,retained_artifact_id=meta['id'],completion_head=completion,terminal_receipt=receipt)
    work=d.read(ROOT/WORK);work.update(status='FORMAL_SAVE14_TERMINAL_CONFIRMED',actions_completion_confirmed=True,retained_artifact_id=meta['id']);write(ROOT/WORK,work)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write(f'\n## 終端確認\n\nrun {cp["run_id"]} の全step成功、artifact {meta["id"]}、記録commit `{completion}` を原本から照合。97画面・全Save/RTC・110試験原本・全公開textを読戻し、新native/test0。次はSave14から先だけ。\n')
    checks(state,cp['source_head']);publish(state,cp,{GUIDE,WORK,receipt},True);write(ART/'terminal.json',d.read(ROOT/receipt));preserve()

if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,snapshot=snapshot,preserve=preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
