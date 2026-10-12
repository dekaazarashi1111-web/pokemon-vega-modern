#!/usr/bin/env python3
"""新区間の独立測定・再実行しない終端回収・同branchへの記録。"""
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
import pr16_research_story_route as m
import pr16_research_story_actions as old
import pr16_research_lifecycle_actions as d
from pr16_learnset_compact_record import publish_resume
TASK = 'USER-20260928-RESEARCH-STORY-ROUTE'
SELF = 'scripts/pr16_research_story_route_actions.py'
WF = '.github/workflows/pr16-research-story-route.yml'
GUIDE = 'docs/PR16_RESEARCH_STORY_ROUTE_JA.md'
CP = 'content/modernization/pr16_research_story_route_checkpoint.json'
TERMINAL = 'content/modernization/pr16_research_story_route_terminal.json'
OUT = ROOT/'.local/pr16-story-route-run'
PUBLIC = OUT/'public'
ART = OUT/'checkpoint'
ARTNAME = 'pr16-research-story-route-checkpoint'
CODE = {SELF, WF, m.SOURCE, m.TEST}
GOAL = '道路でのトレーナー敗北2回・母親の通常回復・草側迂回・キズぐすり1個の通常取得・Save counter2→3・独立Continueの所持保持を限定受入。次はpotion.srmのmap3/19 (26,17)から通常ストーリーへ。トレーナー勝利0、研究活動施設への自然到達は未完。旧starter/完走301入力/旧RP/UI/BP/P08を再実行しない。'


def put(path, value):
    d.write(path, value)


def source_check():
    state = d.read(ROOT/d.STATE)
    m.need(d.bindings(set(state['source_bindings'])) == state['source_bindings'],
           'accepted source/evidence unchanged')
    return state


def local_verified():
    dev = ROOT/m.DEV
    local = d.read(dev/'verification.json')
    for field in ('source_bindings', 'evidence_bindings'):
        m.need(d.bindings(set(local[field])) == local[field], 'exact local '+field)
    unit = (dev/'unit.stderr.txt').read_bytes()
    m.need(local['unit_tests'] == 74 and unit.count(b' ... ok\n') == 74 and
           b'\nOK\n' in unit and b'FAILED' not in unit and
           not (dev/'unit.stdout.txt').read_bytes(), '74 actual successful new oracle originals')
    for name, cold in (('commands.txt', False), ('continue-commands.txt', True)):
        m.commands((dev/name).read_text(), cold)
    result = m.verify((dev/'progress.stdout.txt').read_bytes(), (dev/'continue.stdout.txt').read_bytes(),
                      d.read(ROOT/m.PARENT), local['output_save'])
    m.need(result == local['result'], 'whole local positive oracle result')
    return local


def safe_zip(raw: bytes, max_size: int):
    z = zipfile.ZipFile(io.BytesIO(raw))
    m.need(0 < len(z.infolist()) < 1000 and len(z.namelist()) == len(set(z.namelist())) and
           sum(i.file_size for i in z.infolist()) < max_size, 'bounded unique archive members')
    for entry in z.infolist():
        path = PurePosixPath(entry.filename)
        m.need(not path.is_absolute() and '..' not in path.parts and '\\' not in entry.filename
               and entry.external_attr >> 28 != 10 and not entry.is_dir(), 'regular safe archive member')
    return z


def parent_input():
    parent = d.read(ROOT/m.PARENT)
    m.parent_boundary(parent)
    expected = parent['retained_artifact']
    meta = d.inputs.api('actions/artifacts/10933499471')
    m.need(not meta['expired'] and all(meta[k] == expected[k] for k in
           ('id', 'name', 'size_in_bytes', 'digest', 'workflow_run')), 'fixed parent artifact metadata')
    raw = d.inputs.api('actions/artifacts/10933499471/zip', True)
    m.need(m.identity(raw) == dict(size=1313382, sha256='55e88187f9dbc5ed2f075857506071a06789ae03c57004f8a0f4d54b0f251362'), 'fixed parent archive bytes')
    with safe_zip(raw, 12000000) as z:
        saved, runner = z.read('route.srm'), z.read('runner')
        m.need(m.load(z.read('checkpoint.json')) == parent['checkpoint'] and
               m.identity(saved) == m.INPUT_SAVE and m.identity(runner) == m.RUNNER, 'original Save and runner')
    put(PUBLIC/'parent-artifact.json', {k: meta[k] for k in
        ('id', 'name', 'size_in_bytes', 'digest', 'workflow_run', 'expires_at')})
    return parent, saved, runner


def invoke(runtime, candidate, executable, name, saved, command):
    where = OUT/name
    where.mkdir()
    working = where/'story.srm'
    working.write_bytes(saved)
    cmd = [str(runtime/'ld.so'), '--library-path', str(runtime/'lib'), str(executable),
           str(candidate), str(working), 'continue-story', m.identity(saved)['sha256']]
    # 中断時にも生stdout/Saveを失わず、完走区間の盲目的再測定を防ぐ。
    with (PUBLIC/(name+'.stdout.txt')).open('wb') as out, (PUBLIC/(name+'.stderr.txt')).open('wb') as err:
        result = subprocess.run(cmd, cwd=where, input=command, stdout=out, stderr=err, timeout=300)
    raw = (PUBLIC/(name+'.stdout.txt')).read_bytes()
    errors = (PUBLIC/(name+'.stderr.txt')).read_bytes()
    put(PUBLIC/(name+'.execution.json'), dict(returncode=result.returncode, input_save=m.identity(saved),
        output_save=m.identity(working.read_bytes()), stdout=m.identity(raw), stderr=m.identity(errors)))
    preserve()
    m.need(result.returncode == 0 and not errors, 'native failed; preserve without blind replay')
    return raw, working, where


def measure():
    os.chdir(ROOT)
    d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/CP).exists(), 'one new interval only')
    state = source_check()
    local = local_verified()
    PUBLIC.mkdir(parents=True)
    ART.mkdir()
    parent, saved, runner = parent_input()
    # 固定recipe復元だけ。旧measure/NewGame/compileを呼ばない。
    old.OUT, old.PUBLIC = OUT, PUBLIC
    runtime, data = old.restore()
    candidate = data/'candidate.gba'
    m.need(m.identity(candidate.read_bytes()) == m.CANDIDATE, 'whole fixed candidate')
    executable = OUT/'runner'
    executable.write_bytes(runner)
    executable.chmod(0o755)
    dev = ROOT/m.DEV
    first_raw, first_save, where = invoke(runtime, candidate, executable, 'progress', saved,
                                         (dev/'commands.txt').read_bytes())
    shutil.copy2(first_save, ART/'potion.srm')
    m.need(first_raw == (dev/'progress.stdout.txt').read_bytes(), 'all new progress input/state/screen bytes reproduce')
    m.need(m.identity(first_save.read_bytes()) == m.OUTPUT_SAVE, 'whole naturally generated successor')
    cold_raw, cold_save, cold_where = invoke(runtime, candidate, executable, 'continue', first_save.read_bytes(),
                                           (dev/'continue-commands.txt').read_bytes())
    m.need(cold_raw == (dev/'continue.stdout.txt').read_bytes(), 'all new cold input/state/screen bytes reproduce')
    result = m.verify(first_raw, cold_raw, parent, m.identity(first_save.read_bytes()), where, cold_where)
    m.need(result == local['result'] and m.identity(cold_save.read_bytes()) == m.OUTPUT_SAVE and
           m.identity(first_save.read_bytes()) == m.OUTPUT_SAVE and
           m.identity(candidate.read_bytes()) == m.CANDIDATE and
           m.identity(executable.read_bytes()) == m.RUNNER and m.identity(saved) == m.INPUT_SAVE,
           'all original and successor identities retained')
    m.need(d.bindings(set(state['source_bindings'])) == state['source_bindings'], 'accepted source unchanged after new native')
    checkpoint = dict(schema_version=1, candidate=m.CANDIDATE, save=m.OUTPUT_SAVE, executable=m.RUNNER,
        runtime_artifact=10898620034, data_artifact=10898510128, parent_artifact=10933499471,
        source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
        frame=31904, map=[3,19], xy=[26,17], party_count=1, rp=0, save_counter=3,
        mode='continue-story', commands='quit\n', native_bag_potion_count=1,
        new_game_replay_required=False, starter_story_replay_required=False,
        completed_route_segment_replay_required=False, natural_research_arrival_accepted=False)
    put(ART/'checkpoint.json', checkpoint)
    paths = CODE | {str(p.relative_to(ROOT)) for p in dev.iterdir() if p.is_file()}
    put(PUBLIC/'measurement.json', dict(**result, checkpoint=checkpoint,
        source_head=os.environ['GITHUB_SHA'], run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=d.bindings(paths), protected_bindings=state['source_bindings'],
        native_processes=2, fresh_cores=2, local_development_native_processes=2,
        host_compiles=0, arm_compiles=0, rom_changes=0, accepted_case_reruns=0,
        new_game_replays=0, new_guard_processes=0, reused_fixed_runner_barriers=7,
        reused_new_oracle_tests=74, new_unit_test_runs=0))
    print('PASS: new road loss/recovery/item pickup/Save/cold Bag only')


def append_logs(summary, verify, version, status='DONE（新区間限定、研究施設への通常到達未完）'):
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 道路通常進行・キズぐすり保存継続\n- Version: {version}\n- Status: {status}\n- Summary: {summary}\n- Files changed: 専用oracle/検査/入力原本/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画面は非tracked artifactのみ。\n- Verify: {verify}\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branchへ非force push。\n- Network: 固定GitHub HEAD/Actions/artifact/APIのみ。一般CI action_required・失敗と歴史的全体private guardを成功へ読み替えない。merge/release/active baseline変更0。\n'
    for name in d.LOGS:
        with (ROOT/name).open('a') as f:f.write(entry)


def observe_checks(state, source):
    runs = d.inputs.api('actions/runs?head_sha='+source+'&per_page=50')
    m.need(runs['total_count'] == len(runs['workflow_runs']) <= 50, 'complete measured-source Actions list')
    state['observed_head_checks'] = dict(scope_head=source, runs=[d.run_summary(r) for r in runs['workflow_runs']],
        reason_ja='新区間専用Actionsと一般CIを分離。未完/action_required/失敗を成功にしない。')
    state['pending_runs'] = [dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status'])
        for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]


def record():
    os.chdir(ROOT)
    d.current()
    m.need(not (ROOT/CP).exists(), 'immutable new checkpoint')
    state = source_check()
    measured = d.read(PUBLIC/'measurement.json')
    for field in ('source_bindings', 'protected_bindings'):
        m.need(d.bindings(set(measured[field])) == measured[field], 'exact measured '+field)
    base = 'content/modernization/pr16_research_story_route_evidence/'+os.environ['GITHUB_RUN_ID']
    dest = ROOT/base
    dest.mkdir(parents=True)
    for path in PUBLIC.iterdir():
        if path.is_file():
            raw = path.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw, 'text evidence only')
            shutil.copy2(path, dest/path.name)
    evidence = {str(p.relative_to(ROOT)) for p in dest.iterdir()}
    put(dest/'manifest.json', d.bindings(evidence));evidence.add(base+'/manifest.json')
    cp = dict(measured, status='PASS_NATURAL_STORY_POTION_SAVE_PENDING_TERMINAL', actions_completion_confirmed=False,
              manifest=base+'/manifest.json', retained_artifact_name=ARTNAME, retained_artifact_id=None,
              development=m.DEV+'/verification.json', visual_review=m.DEV+'/visual-review.json',
              next_input='continue-story from potion.srm; do not replay the completed 301 inputs')
    put(ROOT/CP, cp)
    with (ROOT/GUIDE).open('a') as f:
        f.write('\n## Actions独立測定（終端は外部照合待ち）\n\n'+GOAL+'\n\n正式source `'+os.environ['GITHUB_SHA']+'`、run `'+os.environ['GITHUB_RUN_ID']+'`。開発と独立測定の全stdout/53画面/Saveが一致。正式native2、開発native2は別会計。新74検査成功原本はsource一致で再利用し再起動0。\n')
    state['research_story_route'] = dict(path=CP, status=cp['status'], run_id=cp['run_id'],
        source_head=cp['source_head'], candidate=m.CANDIDATE, actions_completion_confirmed=False,
        natural_research_arrival_accepted=False, retained_artifact_name=ARTNAME)
    state['bp']['current_stop'] = cp['status'];state['bp']['next_step'] = GOAL
    state['next_action'] = dict(state['next_action'], id='NATURAL_STORY_FROM_POTION_SAVE_NEXT', goal_ja=GOAL,
        read_paths=[GUIDE, CP, m.SOURCE],
        stop_rule_ja='先に新runの全必須stepと後継Save artifactを照合。potion.srmから先だけ進め、成功301入力を再実行しない。勝利/研究施設到達へ昇格禁止。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0, '道路通常進行は '+CP+'。敗北2回/回復/キズぐすり1個/Save counter3まで完走301入力を保持し、次はpotion.srmだけ。旧受入区間を再生しない。')
    state['observed_head'] = os.environ['GITHUB_SHA']
    state['observed_head_semantics'] = '道路の新規道具取得とSave継続を独立測定したsource HEAD。成功終端は別途API照合する。自己commit/製品最終SHAではない。'
    observe_checks(state, os.environ['GITHUB_SHA'])
    for name in CODE | evidence | {GUIDE, CP}:state['source_bindings'][name] = m.identity((ROOT/name).read_bytes())
    state['research_story_route_development']['superseded_by'] = CP
    state['logs_synchronized'] = True
    publish_resume(state)
    append_logs(GOAL, '正式native2/301入力31904frames・cold24入力1942frames/53画面/全party600bytes・Flash128KiB・研究ledger・位置・RP0・Bagキズぐすり1個一致。新74oracle原本再利用、compile/ROM変更/旧受入再実行/guard再起動0。task graph/resume/scoped index/diff後にcommit。', 'research-story-route-v1')
    put(OUT/'owned.json', sorted(evidence | {GUIDE, CP, d.STATE, d.DOC} | d.LOGS))


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    d.current()
    pr16_resume.validate(ROOT)
    g.START = os.environ['GITHUB_SHA'];g.CODE = set();g.OWNED = set(d.read(OUT/'owned.json'))
    g.guard()
    if (ROOT/CP).exists():
        protected = d.read(ROOT/CP)['protected_bindings']
        m.need(d.bindings(set(protected)-g.OWNED) == {p:v for p,v in protected.items() if p not in g.OWNED}, 'unmodified accepted originals')
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)


def preserve():
    ART.mkdir(parents=True, exist_ok=True)
    for mode in ('progress', 'continue'):
        where = OUT/mode
        if where.is_dir():
            dest = ART/mode;dest.mkdir(exist_ok=True)
            for path in where.iterdir():
                if path.is_file() and path.suffix in ('.srm', '.ppm'):shutil.copy2(path, dest/path.name)
    for path in list(PUBLIC.glob('*')) + list(OUT.glob('*.txt')):
        if path.is_file():shutil.copy2(path, ART/path.name)
    if (OUT/'runner').is_file():shutil.copy2(OUT/'runner', ART/'runner')


def snapshot():
    paths = d.read(OUT/'owned.json')
    ART.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ART/'record.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for name in paths:
            raw = d.git('show', 'HEAD:'+name)
            m.need(raw == (ROOT/name).read_bytes(), 'committed text readback '+name)
            raw.decode('utf-8');z.writestr(name, raw)
        z.writestr('record-head.txt', d.git('rev-parse', 'HEAD'))
    preserve()


if __name__ == '__main__':
    operations = dict(measure=measure, record=record, guard=guard, snapshot=snapshot, preserve=preserve,
                      paths=lambda: print('\n'.join(d.read(OUT/'owned.json'))))
    if len(sys.argv) != 2 or sys.argv[1] not in operations:
        raise SystemExit('measure|record|guard|snapshot|preserve|paths')
    operations[sys.argv[1]]()
