#!/usr/bin/env python3
"""新しい保存Continue区間だけを独立測定・記録する。旧受入は起動しない。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_research_story_continue as m
import pr16_research_story_actions as old
import pr16_research_lifecycle_actions as d

TASK = 'USER-20260927-RESEARCH-STORY-CONTINUE'
SELF = 'scripts/pr16_research_story_continue_actions.py'
WF = '.github/workflows/pr16-research-story-continue.yml'
GUIDE = 'docs/PR16_RESEARCH_STORY_CONTINUE_JA.md'
CP = 'content/modernization/pr16_research_story_continue_checkpoint.json'
OUT = ROOT/'.local/pr16-story-continue-run'
PUBLIC = OUT/'public'
ART = OUT/'checkpoint'
ARTNAME = 'pr16-research-story-continue-checkpoint'
CODE = {SELF, WF, m.SOURCE, m.TEST}


def put(path, value):d.write(path, value)


def starter(parent):
    """固定原本をread-only復元。全ZIPの安全性を調べ必要memberだけを展開。"""
    m.checkpoint(parent)
    expected = parent['retained_artifact'];number = expected['id']
    meta = d.inputs.api('actions/artifacts/'+str(number))
    m.need(not meta['expired'] and all(meta[k] == expected[k] for k in
           ('id','name','size_in_bytes','digest','workflow_run')), '固定starter artifact metadata')
    raw = d.inputs.api('actions/artifacts/'+str(number)+'/zip', True)
    m.need(m.identity(raw) == dict(size=expected['size_in_bytes'],sha256=expected['digest'].split(':')[1]),
           '固定starter archive bytes')
    dest = OUT/'starter';dest.mkdir()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        m.need(len(z.namelist()) == len(set(z.namelist())) and
               sum(i.file_size for i in z.infolist()) < 12000000, 'bounded unique starter members')
        for i in z.infolist():
            p = PurePosixPath(i.filename)
            m.need(not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename and
                   i.external_attr >> 28 != 10, 'safe original member')
        for name in ('checkpoint.json','starter.srm','runner'):
            (dest/name).write_bytes(z.read(name))
    saved = d.read(dest/'checkpoint.json')
    m.need(saved == parent['checkpoint'] and m.identity((dest/'starter.srm').read_bytes()) == m.STARTER and
           m.identity((dest/'runner').read_bytes()) == saved['executable'], 'original Save/runner identity')
    put(PUBLIC/'starter-artifact.json', {k:meta[k] for k in
        ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    return dest


def invoke(runtime, candidate, executable, name, saved, sha, commands):
    """作業Save以外は入力を変更しない。実行直後の原本は検査失敗時も保持。"""
    where = OUT/name;where.mkdir();working = where/'story.srm';working.write_bytes(saved)
    m.need(m.identity(saved)['sha256'] == sha, 'exact whole input save')
    argv = [str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(executable),
            str(candidate),str(working),'continue-story',sha]
    p = subprocess.run(argv,cwd=where,input=commands,capture_output=True,timeout=240)
    (PUBLIC/(name+'.stdout.txt')).write_bytes(p.stdout)
    (PUBLIC/(name+'.stderr.txt')).write_bytes(p.stderr)
    put(PUBLIC/(name+'.execution.json'),dict(returncode=p.returncode,input_save=m.identity(saved),
        output_save=m.identity(working.read_bytes()),stdout=m.identity(p.stdout),stderr=m.identity(p.stderr)))
    dest = ART/name;dest.mkdir()
    for path in where.iterdir():
        if path.is_file() and path.suffix in ('.srm','.ppm'):shutil.copy2(path,dest/path.name)
    m.need(p.returncode == 0 and not p.stderr, name+' process failed; preserve partial, never blind replay')
    return p.stdout, working, where


def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/CP).exists(),
           '一度の新規測定だけ。原本があれば回収し再実行しない')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    state = d.read(ROOT/d.STATE);protected = dict(state['source_bindings'])
    m.need(d.bindings(set(protected)) == protected, 'accepted original source bindings')
    parent = d.read(ROOT/m.PARENT);m.checkpoint(parent)
    dev = ROOT/m.DEV;local = d.read(dev/'verification.json')
    m.need(d.bindings(set(local['source_bindings'])) == local['source_bindings'] and
           d.bindings(set(local['evidence_bindings'])) == local['evidence_bindings'],
           'exact local new test/source/evidence bindings')
    unit = (dev/'unit.stderr.txt').read_bytes()
    m.need(local['unit_tests'] == 59 and unit.count(b' ... ok\n') == 59 and b'\nOK\n' in unit and
           b'FAILED' not in unit and not (dev/'unit.stdout.txt').read_bytes(), '59 original new oracle tests')
    command = (dev/'commands.txt').read_text();m.commands(command)
    baseline = m.verify((dev/'progress.stdout.txt').read_bytes(),(dev/'continue.stdout.txt').read_bytes(),
                        parent,local['output_save'])
    source = starter(parent)
    # 既存の固定recipe復元だけ。old.measure/new-game-story/compileは呼ばない。
    old.OUT = OUT;old.PUBLIC = PUBLIC;runtime,data = old.restore()
    candidate = data/'candidate.gba';m.need(m.identity(candidate.read_bytes()) == m.CANDIDATE, 'whole fixed candidate')
    executable = OUT/'runner';shutil.copy2(source/'runner',executable);executable.chmod(0o755)
    shutil.copy2(executable,ART/'runner')
    raw, saved, where = invoke(runtime,candidate,executable,'progress',(source/'starter.srm').read_bytes(),
                               m.STARTER['sha256'],command.encode())
    shutil.copy2(saved,ART/'route.srm')
    first = m.read_trace(raw,where)
    m.need(first == m.read_trace((dev/'progress.stdout.txt').read_bytes()),
           'independent new progress reproduces all inputs/observations/21 screen hashes')
    save_identity = m.identity(saved.read_bytes());m.need(save_identity == m.ROUTE_SAVE, 'normally generated successor save')
    cold_raw,cold_save,cold_where = invoke(runtime,candidate,executable,'continue',saved.read_bytes(),
                                          save_identity['sha256'],b'quit\n')
    second = m.read_trace(cold_raw,cold_where)
    m.need(second == m.read_trace((dev/'continue.stdout.txt').read_bytes()),
           'independent new cold Continue reproduces local real screen/state')
    result = m.retained(first,second,parent,save_identity)
    m.need(result == baseline and m.identity(cold_save.read_bytes()) == save_identity and
           m.identity(saved.read_bytes()) == save_identity and
           m.identity((source/'starter.srm').read_bytes()) == m.STARTER and
           m.identity(executable.read_bytes()) == parent['checkpoint']['executable'] and
           m.identity(candidate.read_bytes()) == m.CANDIDATE, 'all input and new save identities unchanged')
    m.need(d.bindings(set(protected)) == protected, 'accepted source unchanged after two new native processes')
    saved_checkpoint = dict(schema_version=1,candidate=m.CANDIDATE,save=save_identity,
        executable=parent['checkpoint']['executable'],runtime_artifact=10898620034,data_artifact=10898510128,
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),parent_artifact=10932059074,
        frame=12012,map=[3,19],xy=[1,14],party_count=1,rp=0,save_counter=2,mode='continue-story',
        commands='quit\n',new_game_replay_required=False,starter_story_replay_required=False,
        completed_route_segment_replay_required=False,natural_research_arrival_accepted=False)
    put(ART/'checkpoint.json',saved_checkpoint)
    devpaths = {str(p.relative_to(ROOT)) for p in dev.iterdir() if p.is_file()}
    put(PUBLIC/'measurement.json',dict(**result,checkpoint=saved_checkpoint,
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=d.bindings(CODE|devpaths),protected_bindings=protected,
        fresh_cores=2,native_processes=2,local_development_native_processes=2,
        host_compiles=0,arm_compiles=0,rom_changes=0,accepted_case_reruns=0,new_game_replays=0,
        new_guard_processes=0,reused_fixed_runner_barriers=7,reused_new_oracle_tests=59,new_unit_test_runs=0))
    print('PASS: new rival loss recovery / road / ordinary Save / independent Continue only')


def record():
    os.chdir(ROOT);d.current();m.need(not (ROOT/CP).exists(),'one immutable continuation receipt')
    measured = d.read(PUBLIC/'measurement.json');state = d.read(ROOT/d.STATE)
    m.need(d.bindings(set(measured['protected_bindings'])) == measured['protected_bindings'] and
           d.bindings(set(measured['source_bindings'])) == measured['source_bindings'], 'exact measured source before record')
    base = 'content/modernization/pr16_research_story_continue_evidence/'+os.environ['GITHUB_RUN_ID']
    evidence = ROOT/base;evidence.mkdir(parents=True)
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw = p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text evidence only');shutil.copy2(p,evidence/p.name)
    evidence_paths = {str(p.relative_to(ROOT)) for p in evidence.iterdir()}
    put(evidence/'manifest.json',d.bindings(evidence_paths));evidence_paths.add(base+'/manifest.json')
    cp = dict(measured,actions_completion_confirmed=False,status='PASS_NATURAL_STORY_ROUTE_SAVE_PENDING_TERMINAL',
        manifest=base+'/manifest.json',retained_artifact_name=ARTNAME,retained_artifact_id=None,
        development=m.DEV+'/verification.json',visual_review=m.DEV+'/visual-review.json',
        next_input='continue-story from route.srm; never replay starter or completed route segment')
    put(ROOT/CP,cp)
    goal='保存starter以後のライバル敗北復帰→研究所退出→517番道路の木の拒否→東側道路map3/19→Save counter1→2→独立Continueを限定実測。次は後継artifactのroute.srmから未完ストーリーへ。研究活動施設への自然到達は未完。初期化/スターター/完了区間/旧RP/UI/BP/P08を再実行しない。'
    text='# PR16 保存スターター以後の通常進行\n\n## 今回の限定受入\n\n'+goal+'\n\n正本: `'+CP+'`。正式source `'+os.environ['GITHUB_SHA']+'`、run `'+os.environ['GITHUB_RUN_ID']+'`。専用Actionsの成功終端とartifact IDは外部API確認待ち。全体完成ではない。\n\n## 実装と検証\n\n新continuation oracleは保存前提をstarter artifact10932059074に限定し、通常ライバル戦での敗北・正常復帰を勝利へ読み替えない。517番道路の切れる木は会話だけで通過せず、町へ戻って東側道路map3/19へ進んだ。114入力/12012frames、実画面21枚、通常Save1回。別coreのContinueは12入力/1390frames・実画面1枚、party600bytes/Flash128KiB/研究ledger/位置/RP0/counter2を保持。戦闘flags/outcomeは一時状態として0へ初期化。\n\n新59oracle/拒否試験は成功原本とsource一致を再利用。最初のContinue入力件数誤記(17→実測12)は失敗receiptを保持し、そこでの負例okを受入しない。ローカル開発native2、正式native2は別会計。旧受入ケースの再実行0、NewGame再生0、guard再起動0、host/ARM compile0、ROM変更0。固定runnerの7禁止barrierと候補全体SHAを維持。\n\n## 重複防止と後継保存\n\n通常生成route.srmは131088bytes / SHA-256 '+m.ROUTE_SAVE['sha256']+'。map3/19 (1,14)、party1/RP0/counter2。固定runtime10898620034・data10898510128とrunner identityをcheckpoint.jsonで照合する。保存原本を保全し作業コピーだけに continue-story と全Save SHAを渡す。次回の入力はこの地点より先だけで、既存commands.txtは再生しない。\n\n研究活動施設(map96/0→98/3)への通常到達、全体ストーリー、releaseは未受入。merge/active baseline変更なし。一般CI action_required/失敗と歴史的全体private guardを成功へ読み替えない。ROM/save/runner/画面はartifactだけに保持しGit trackedには入れない。\n'
    (ROOT/GUIDE).write_text(text)
    state['research_story_continue'] = dict(path=CP,status=cp['status'],candidate=m.CANDIDATE,
        run_id=cp['run_id'],source_head=cp['source_head'],natural_research_arrival_accepted=False,
        actions_completion_confirmed=False,retained_artifact_name=ARTNAME)
    state['bp']['current_stop'] = cp['status'];state['bp']['next_step'] = goal
    state['next_action'] = dict(state['next_action'],id='NATURAL_STORY_FROM_ROUTE_CONTINUE_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,m.DEV+'/visual-review.json','scripts/pr16_research_story_continue.py'],
        stop_rule_ja='まず新runの全step終端とcheckpoint artifactを照合。成功済み114入力を再実行せずroute.srmをContinue。研究施設到達/勝利/切断の受入へ昇格しない。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'新規道路保存は '+CP+'。次はroute.srmからContinueだけ。旧starterと今回完走114入力/12012framesを再生しない。RP0の研究活動施設未到達。')
    state['observed_head'] = os.environ['GITHUB_SHA']
    state['observed_head_semantics'] = '通常starter保存以後の新規道路保存を測定したsource HEAD。終端は外部API確認待ちで、自己記録commitや最終製品SHAではない。'
    runs = d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    m.need(runs['total_count'] == len(runs['workflow_runs']) <= 50,'complete source Actions list')
    state['observed_head_checks'] = dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs['workflow_runs']],reason_ja='新規道路保存の限定測定と一般CIは別。未完/action_required/失敗をsuccessへ読み替えない。')
    state['pending_runs'] = [dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]
    for p in CODE|evidence_paths|{GUIDE,CP}:state['source_bindings'][p] = m.identity((ROOT/p).read_bytes())
    state['logs_synchronized'] = True
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / スターター以後の道路保存と独立Continue\n- Version: research-story-continue-v1\n- Status: DONE（新規道路保存限定、研究活動施設到達未完）\n- Summary: 通常ライバル戦の敗北復帰、517番道路の木の会話と帰還、東側道路map3/19への退出、通常Save counter1→2を114入力/12012framesで独立再現。別core Continueで全party/Flash/研究ledger/位置/RP0を保持し、新22実画面のhashを開発原本と照合。\n- Files changed: 専用継続oracle/59検査/Actions、開発と正式のUTF8原本、checkpoint、引継ぎMD/JSON、両ログ。save/runner/画面は非tracked artifactへ。\n- Verify: 新59oracle成功原本/source一致再利用、正式native2core、host/ARM compile0、ROM変更0、旧受入再実行0。固定runner7禁止barrierは再起動せず同一実装を再利用。task graph/resume/scoped index/diff検査後にcommit。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push。成功終端/保存artifact IDは外部確認待ち。\n- Network: GitHub固定artifact/Actions/APIのみ。merge/release/baseline変更0、歴史的private guard/一般CI未完を成功扱いしない。次は後継route.srmだけから未完ストーリーへ進む。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a') as f:f.write(entry)
    put(OUT/'owned.json',sorted(evidence_paths|{GUIDE,CP,d.STATE,d.DOC}|d.LOGS))
    print('PASS: new scoped progress recorded, old accepted originals intact')


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    m.need(d.bindings(set(d.read(ROOT/CP)['protected_bindings'])-g.OWNED) ==
           {p:v for p,v in d.read(ROOT/CP)['protected_bindings'].items() if p not in g.OWNED},
           'all unmodified accepted sources retained')
    subprocess.run(['git','diff','--cached','--check'],check=True)


def preserve():
    """成功後のrecord失敗でも、nativeを重複しないため生の進行をartifactに残す。"""
    ART.mkdir(parents=True,exist_ok=True)
    for mode in ('progress','continue'):
        src=OUT/mode
        if src.is_dir():
            dst=ART/mode;dst.mkdir(exist_ok=True)
            for p in src.iterdir():
                if p.is_file() and p.suffix in ('.ppm','.srm'):shutil.copy2(p,dst/p.name)
    for p in list(PUBLIC.glob('*'))+list(OUT.glob('*.txt')):
        if p.is_file():shutil.copy2(p,ART/p.name)
    if (OUT/'runner').is_file():shutil.copy2(OUT/'runner',ART/'runner')


def snapshot():
    paths=d.read(OUT/'owned.json')
    with zipfile.ZipFile(ART/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            raw=d.git('show','HEAD:'+p);m.need(raw==(ROOT/p).read_bytes(),'committed readback '+p);raw.decode('utf-8');z.writestr(p,raw)
        z.writestr('record-head.txt',d.git('rev-parse','HEAD'))
    preserve()


if __name__=='__main__':
    operations={'measure':measure,'record':record,'guard':guard,'snapshot':snapshot,'preserve':preserve,
                'paths':lambda:print('\n'.join(d.read(OUT/'owned.json')))}
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|guard|snapshot|preserve|paths')
    operations[sys.argv[1]]()
