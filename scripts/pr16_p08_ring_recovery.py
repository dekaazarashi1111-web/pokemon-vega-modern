#!/usr/bin/env python3
"""完了済みRing原本を再実行せず回収。末尾空行もJSON包絡でbyte保存する。"""
from __future__ import annotations
import base64
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TASK = 'USER-20260920-P08-RING-RECOVERY'
SELF = 'scripts/pr16_p08_ring_recovery.py'
TEST = 'tests/test_pr16_p08_ring_recovery.py'
WORKFLOW = '.github/workflows/pr16-p08-ring-recovery.yml'
FILES = (SELF, TEST, WORKFLOW)
REPORT = 'content/modernization/pr16_p08_ring_acceptance.json'
RUN = 35507654812
JOB = 106070069903
ARTIFACT = 10604711829
HEAD = '870e65e58fa34289daa6216ae41ed201e54b5e29'
ARCHIVE = {'size': 94066, 'sha256': 'a1a2b2ce1966b14ce895367a426c5d9f4db33b6adb94fc63176243de435e6795'}
OUT = ROOT / '.local/pr16-p08-ring-recovery'
SCREENS = (
    'bag-stone', 'battle-reloaded', 'equip-menus-closed', 'equipped-reloaded',
    'equipped', 'fixture', 'give-menu', 'give-party', 'mega-active',
    'mega-selection', 'native-turn', 'natural-equipped-battle', 'npc-dialogue', 'reverted-field',
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def strict(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def envelope(raw):
    raw.decode('utf-8')
    need(b'\0' not in raw, 'text evidence required')
    return {'encoding': 'base64', 'identity': identity(raw),
            'data': base64.b64encode(raw).decode('ascii')}


def unwrap(value):
    need(set(value) == {'encoding', 'identity', 'data'} and value['encoding'] == 'base64', 'envelope schema')
    raw = base64.b64decode(value['data'], validate=True)
    need(identity(raw) == value['identity'], 'evidence bytes changed')
    raw.decode('utf-8')
    need(b'\0' not in raw, 'text evidence required')
    return raw


def archive_members(raw, expected):
    need(identity(raw) == expected, 'archive digest mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        need(len(infos) <= 100 and len({p.filename for p in infos}) == len(infos), 'archive member count/duplicate')
        need(sum(p.file_size for p in infos) < 8 * 1024 * 1024, 'archive size limit')
        result = {}
        for info in infos:
            p = PurePosixPath(info.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                 and p.as_posix() == info.filename and not info.is_dir(), 'archive member path')
            need(not stat.S_ISLNK(info.external_attr >> 16), 'archive symlink')
            result[info.filename] = archive.read(info)
        return result


def require_native(value, proc):
    need(value['source_head'] == HEAD and value['workflow_source_head'] == HEAD
         and value['recording_run'] == RUN and value['case'] == 'ring-active', 'native provenance')
    need(value['native_verified'] is True and value['representative_accepted'] is False
         and value['visual_review_completed'] is False and value['failures'] == [], 'original native state')
    for name, count in [('new_emulator_processes', 1), ('fresh_cores', 3), ('host_compiles', 1),
                        ('arm_compiles', 0), ('arm_links', 0), ('accepted_standalone_replays', 0),
                        ('prefix_wins_reexecuted', 0), ('rom_changes', 0)]:
        need(type(value[name]) is int and value[name] == count, 'original count: ' + name)
    need(type(proc['returncode']) is int and proc['returncode'] == 0
         and proc['timed_out'] is False and proc['spawn_error'] is None, 'native process')
    need(value['release_ready'] is False, 'premature release')


def sources_snapshot():
    # 次の実装用のtracked textのみ。ROM/save/生成物/秘密設定は持ち出さない。
    dst = OUT / 'source-context.zip'
    prefixes = ('scripts/', 'tests/', 'tools/', 'overlays/', 'content/modernization/')
    suffixes = {'.py', '.c', '.h', '.json', '.md'}
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in paths:
            p = ROOT / name
            if not name.startswith(prefixes) or p.suffix not in suffixes or not p.is_file() or p.is_symlink():
                continue
            if '/evidence/' in name or '_evidence/' in name:
                continue
            raw = p.read_bytes()
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if b'\0' not in raw:
                archive.writestr(name, raw)


def main():
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
    import pr16_p08_ring_representative as m
    b = m.b
    b.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    head = b.scope()
    state = b.resume.validate(ROOT)
    need(not (ROOT / REPORT).exists(), 'already reconciled: do not replay')
    run = b.api('actions/runs/' + str(RUN))
    job = b.api('actions/jobs/' + str(JOB))
    art = b.api('actions/artifacts/' + str(ARTIFACT))
    need(run['status'] == 'completed' and run['conclusion'] == 'failure' and run['head_sha'] == HEAD, 'run boundary')
    need(job['run_id'] == RUN and job['status'] == 'completed' and job['conclusion'] == 'failure'
         and job['head_sha'] == HEAD, 'job boundary')
    steps = {x['number']: x for x in job['steps']}
    need(steps[5]['conclusion'] == 'success' and steps[6]['conclusion'] == 'failure'
         and steps[8]['conclusion'] == 'success', 'native/record/upload boundary')
    need(art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == HEAD
         and not art['expired'] and art['digest'] == 'sha256:' + ARCHIVE['sha256'], 'artifact boundary')
    raw = subprocess.check_output(['gh', 'api', 'repos/' + b.REPO + '/actions/artifacts/' + str(ARTIFACT) + '/zip'], cwd=ROOT)
    members = archive_members(raw, ARCHIVE)
    need(len(members) == 42, 'original member inventory')
    value = strict(members['native-result.json'])
    proc = strict(members['execution/ring-active.process.json'])
    require_native(value, proc)
    need(m.protected() == value['protected_originals'], 'protected original drift')
    for path, expected in {**value['source_bindings'], **value['original']['sources'], **value['transitive_compiled_sources']}.items():
        need(identity(b.resume.safe_path(ROOT, path).read_bytes()) == expected, 'source binding: ' + path)
    for name in m.FILES:
        need(members['source/' + name] == (ROOT / name).read_bytes(), 'archived source drift')
    row = m.validate_result(members['execution/ring-active.stdout'], members['execution/ring-active.stderr'], proc, value['oracle'])
    need(row == value['native_result'] and value['candidate'] == m.impact.TARGET, 'native result drift')
    names = {'ring-active-' + x + '.ppm' for x in SCREENS}
    need(set(value['screens']) == names, 'reviewed screen inventory')
    for name, expected in value['screens'].items():
        pixels = members['screens/' + name]
        need(identity(pixels) == expected and pixels.startswith(b'P6\n240 160\n255\n') and len(pixels) == 115215, 'reviewed pixels drift')
    test_out, test_err, test_proc = b.capture([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', Path(TEST).name, '-v'], 'recovery-tests')
    need(b.exited(test_proc) == 0 and b'\nOK\n' in test_err, 'recovery tests failed')
    bp_path = 'content/modernization/pr16_bp_chooser_checkpoint.json'
    bp_identity = identity((ROOT / bp_path).read_bytes())
    bp = b.load(bp_path)
    need(bp['accepted_case_count'] == 3 and bp['candidate']['sha256'].startswith('ceddbe91'), 'BP authority changed')
    evidence = 'evidence/pr16_p08_ring/' + str(RUN) + '/recovered/'
    saved_paths = []
    def save(name, obj):
        path = evidence + name
        b.write(path, stable(obj))
        saved_paths.append(path)
    # stdoutをtrimしない。検証済みのbyte列そのものをJSON包絡で保存し読戻す。
    text = {name: envelope(data) for name, data in members.items()
            if name.startswith('execution/') or name in ('native-result.json', 'guard.json', 'receipt-START.json')}
    for name, obj in text.items():
        need(unwrap(obj) == members[name], 'envelope roundtrip: ' + name)
    save('original-text.json', text)
    save('native-result.json', value)
    save('visual-review.json', dict(schema_version=1, artifact_id=ARTIFACT, archive=ARCHIVE,
         screens=value['screens'], reviewed_screen_count=14, visual_review_completed=True,
         reviewer='ChatGPT', reviewed_at_utc='2026-09-20',
         observations_ja=['NPC「メガリングを うけとった」を確認。', 'Bagのシビルドナイト、もたせるUI、装備確定を確認。',
                          '自然遭遇・技選択・実ターン・通常field帰還と再読込の14画面を確認。',
                          '隠れたMega状態・PP・保存counterは画像だけから推測せずnative原本と照合。'],
         initial_map_progress_party_stone_are_fixtures=True))
    save('workflow-boundary.json', dict(run_id=RUN, job_id=JOB, source_head=HEAD,
         original_conclusion='failure', native_step_conclusion='success', recording_step_conclusion='failure',
         failure_reason='git diff --cached --check: materialize.stdout new blank line at EOF',
         artifact_id=ARTIFACT, archive=ARCHIVE, member_identities={k: identity(v) for k,v in members.items()},
         failure_relabelled=False, new_emulator_processes=0, normalization_of_original_bytes=False))
    save('recovery-tests.json', dict(process=test_proc, stdout=envelope(test_out), stderr=envelope(test_err)))
    acceptance = dict(schema_version=1, task=TASK, classification='P08_RING_ORDINARY_REPRESENTATIVE_ACCEPTED',
         candidate=m.impact.TARGET, original_run_id=RUN, original_job_id=JOB, original_conclusion='failure',
         original_source_head=HEAD, artifact_id=ARTIFACT, archive=ARCHIVE,
         native_step_conclusion='success', native_verified=True, representative_accepted=True,
         visual_review_completed=True, reviewed_screen_count=14, native_result=row,
         original_native_processes=1, original_fresh_cores=3, new_emulator_processes=0,
         arm_compiles=0, arm_links=0, accepted_standalone_replays=0, prefix_wins_reexecuted=0,
         recording_source_head=head, recording_run=int(os.environ['GITHUB_RUN_ID']),
         required_regression_id='P08_RING_ORDINARY', evidence_paths=saved_paths,
         release_ready=False, final_product_sha_fixed=False, active_baseline_changed=False,
         next_required_ids=['P08_SHARED_SAVE_LOAD', 'P08_BP_RETURN_PARTY', 'P08_CIRCUS_POST_EXIT_ORDINARY'])
    b.write(REPORT, stable(acceptance))
    recovered = copy.deepcopy(value)
    recovered.update(phase='FINISH_RECOVERED', representative_accepted=True, visual_review_completed=True,
                     acceptance_path=REPORT, recovered_by_run=acceptance['recording_run'], original_run_conclusion='failure')
    b.write(m.REPORT, stable(recovered))
    backlog = b.load(b.resume.BACKLOG)
    final = next(x for x in backlog['remaining_conditions'] if x['id'] == 'FINAL_NATIVE_ACCEPTANCE')
    need(final['required_representative_regression_ids'] == ['P08_SHARED_SAVE_LOAD', 'P08_BP_RETURN_PARTY', 'P08_RING_ORDINARY', 'P08_CIRCUS_POST_EXIT_ORDINARY'], 'P08 scope drift')
    final.update(completed_representative_regression_ids=['P08_RING_ORDINARY'],
                 remaining_representative_regression_ids=acceptance['next_required_ids'],
                 ring_representative_acceptance=REPORT, status='RING_REPRESENTATIVE_ACCEPTED_THREE_BOUNDARIES_PENDING')
    stop = 'run35507654812のRing代表native成功1process/3fresh cores・14画面を原本照合しP08_RING_ORDINARYだけ受入。run全体の記録失敗は保持。末尾空行もJSON包絡でbyte保存、回収native0。'
    nxt = '同一46487d98のP08_BP_RETURN_PARTY（通常Factory復帰と元party）を次に実装。残るP03共有保存/読み込み・Circus退出後通常戦闘も影響境界だけ検証。Ring/旧5case/30勝は再実行しない。'
    final['reason_ja'] = 'BP/Ring/policy/Circusのscoped受入とbyte影響監査は保持。Ring代表境界を閉鎖し、最終候補移送は残る3代表境界で判定する。'
    final['resume'] = nxt
    b.write(b.resume.BACKLOG, stable(backlog))
    state['p08_ring_representative'].update(path=m.REPORT, phase='FINISH_RECOVERED', native_verified=True,
                                          representative_accepted=True, acceptance=REPORT)
    state['p08_ring_recovery'] = dict(path=REPORT, run_id=acceptance['recording_run'], original_run=RUN, original_conclusion='failure')
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = nxt
    state['next_action'].update(id='P08_BP_REPRESENTATIVE', read_paths=[REPORT, m.IMPACT, bp_path, 'content/modernization/pr16_bp_spending_verified.json', b.resume.BACKLOG], stop_rule_ja=nxt)
    state['pending_runs'] = [dict(run_id=acceptance['recording_run'], tested_head=head, status='in_progress', native_execution=False)]
    state['observed_head'] = head
    state['observed_date_jst'] = '2026-09-20'
    state['observed_head_semantics'] = 'Ring原本回収の記録直前remote。完了済みnativeの証拠と記録jobの完了は別。'
    state['observed_head_checks'] = dict(scope_head=head, run_id=acceptance['recording_run'], verified_prior_run=RUN,
        prior_conclusion='failure', native_step_conclusion='success', recording_step_conclusion='failure',
        reason_ja='前runのnative成功と記録失敗を区別。今回回収jobの完了は次に別照合。')
    state['session_execution_summary'] = dict(new_emulator_processes=0, arm_compiles=0, arm_links=0,
        accepted_standalone_replays=0, prefix_wins_reexecuted=0, scope_ja='保存済みRing原本の回収・14画面照合のみ。')
    state['remaining_sequence_ja'] = 'P08の残3代表境界（BP元party/共有保存/Circus退出後通常戦闘）→最終候補identity・配布準備判断'
    state['logs_synchronized'] = state['p08_resume_synchronized'] = True
    paths = [REPORT, m.REPORT, b.resume.BACKLOG, *saved_paths]
    for path in (*FILES, *paths):
        state['source_bindings'][path] = identity((ROOT / path).read_bytes())
    b.write(b.resume.STATE, stable(state))
    b.write(b.resume.DOC, b.resume.render(state).encode())
    b.resume.validate(ROOT)
    _, _, graph = b.capture([sys.executable, 'scripts/validate_task_graph.py'], 'task-graph')
    need(b.exited(graph) == 0, 'task graph failed')
    need(identity((ROOT / bp_path).read_bytes()) == bp_identity and m.protected() == value['protected_originals'], 'protected originals changed')
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths += [b.resume.STATE, b.resume.DOC, *b.LOGS]
    entry = ('\n\n## ' + stamp + ' — ' + TASK + '\n- Timestamp: ' + stamp + '\n- Task: ' + TASK +
        '\n- Status: DONE\n- Version: pr16-p08-ring-recovery-v1\n- Summary: ' + stop +
        '\n- Files changed: ' + ', '.join((*FILES, *paths)) +
        '\n- Verify: recovery unit tests PASS; 原本SHA/42member/25source・推移include/14画面/native validator/JSON byte往復/resume/task graph PASS。'+
        '\n- Boundary: 原run failure不変、今回native0/ARM0/旧受入再実行0。全体guard既存違反はbaseline差分照合し過大なPASSを主張しない。'+
        '\n- Commit: 同branchの本commit、非force push後remoteを照合。\n- Network: GitHub固定run/job/artifactを照合・取得。\n- Next: ' + nxt + '\n')
    for path in b.LOGS:
        need('— ' + TASK not in (ROOT / path).read_text(), 'duplicate recovery log')
        with (ROOT / path).open('a') as stream:
            stream.write(entry)
    subprocess.run(['git', 'add', '--', *paths], cwd=ROOT, check=True)
    changed = set(b.command('git', 'diff', '--cached', '--name-only', head).splitlines())
    need(changed and changed <= set(paths), 'staged scope')
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT, guard.ALLOWED = head, OUT, changed
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    for path in paths:
        need(subprocess.check_output(['git', 'show', ':' + path], cwd=ROOT) == (ROOT / path).read_bytes(), 'index readback')
    b.scope()
    subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], cwd=ROOT, check=True)
    subprocess.run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'], cwd=ROOT, check=True)
    subprocess.run(['git', 'commit', '-m', TASK + ': 原本byte回収・Ring代表受入・残3境界を同期'], cwd=ROOT, check=True)
    subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/' + b.BRANCH], cwd=ROOT, check=True)
    commit = b.scope()
    need(not b.command('git', 'status', '--porcelain', '--untracked-files=no'), 'dirty after push')
    (OUT / 'receipt.json').write_bytes(stable(dict(task=TASK, commit=commit, non_force_push=True,
        original_run_conclusion='failure', representative_accepted=True, new_emulator_processes=0)))
    print('RESULT=DONE TASK=' + TASK + ' VERIFY=PASS COMMIT=' + commit)
    sources_snapshot()


if __name__ == '__main__':
    main()
