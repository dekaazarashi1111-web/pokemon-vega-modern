#!/usr/bin/env python3
"""完了済み原本だけからCircus実受付を受入。ROM生成・native起動は行わない。"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TASK = 'USER-20260920-CIRCUS-ACCEPTANCE'
BASE = '17ad82cc7d8b8fe8de82ab3c886fb776d86dc1f3'
SHA = '46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38'
REPORT = 'content/modernization/pr16_circus_acceptance.json'
REVIEW = 'content/modernization/pr16_circus_visual_review.json'
OLD = 'content/modernization/pr16_circus_getter_followup.json'
LIFE = 'content/modernization/pr16_circus_suppression_lifecycle.json'
SELF = 'scripts/pr16_circus_acceptance.py'
TEST = 'tests/test_pr16_circus_acceptance.py'
WORKFLOW = '.github/workflows/pr16-circus-acceptance.yml'
RESUME_TEST = 'tests/test_pr16_resume.py'
RESUME_IMPL = 'scripts/pr16_resume.py'
FILES = (SELF, TEST, REVIEW, WORKFLOW, RESUME_TEST, RESUME_IMPL)
OUT = ROOT / '.local/pr16-circus-acceptance'
SOURCES = (
    dict(run=35503514936, artifact=10602823295, head='5618a38f6854aa4551e5c518509f5f97cf2a79b0',
         conclusion='failure', size=332538, sha256='c16ef7c1e05e5dad1ba4169016a9bbd863c97098eae9c2cb6c7d94d71d905eba'),
    dict(run=35504302893, artifact=10603527226, head='cc5d6822266a9663b0e368c9cff2c94d2ede3435',
         conclusion='success', size=299507, sha256='39481869e73b6685b964d58c8a24143f90c6650ee7e2c444f14207c11c8865e0'),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs)


def validate_actions(run, artifact, spec):
    need(run['id'] == spec['run'] and run['head_sha'] == spec['head']
         and run['head_branch'] == 'codex/modernization-followup-20260908'
         and run['status'] == 'completed' and run['conclusion'] == spec['conclusion'], 'Actions identity/status')
    need(artifact['id'] == spec['artifact'] and artifact['workflow_run']['id'] == spec['run']
         and artifact['workflow_run']['head_sha'] == spec['head'] and not artifact['expired']
         and artifact['digest'] == 'sha256:' + spec['sha256'], 'artifact identity/status')


def archive(raw, spec):
    need(identity(raw) == {k: spec[k] for k in ('size', 'sha256')}, 'archive byte identity')
    z = zipfile.ZipFile(io.BytesIO(raw))
    names = z.namelist()
    need(len(names) == len(set(names)), 'duplicate ZIP member')
    need(sum(x.file_size for x in z.infolist()) < 32 * 1024 * 1024, 'archive too large')
    for name in names:
        p = Path(name)
        need(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'unsafe ZIP member')
    return z


def verify_screens(z, review):
    need(review['schema_version'] == 1 and review['source_run'] == 35504302893
         and review['source_head'] == SOURCES[1]['head'] and review['completed'] is True, 'visual review provenance')
    names = {x for x in z.namelist() if x.startswith('screens/') and x.endswith('.ppm')}
    need(len(names) == 29 and set(review['screens']) == names, 'visual coverage incomplete')
    for name in sorted(names):
        row = review['screens'][name]
        need(identity(z.read(name)) == row['identity'] and bool(row['observation_ja']), 'reviewed pixels differ')
    return dict(completed=True, screen_count=len(names), source=REVIEW,
                archive_sha256=SOURCES[1]['sha256'], pixels_not_inferred_from_filename=True)


def verify_pair(old, new):
    need(old['candidate'] == new['candidate'] == dict(size=33554432, sha256=SHA), 'candidate mismatch')
    need(old['native_verified'] is False and old['process']['returncode'] == 1 and old['failures'], 'old failure relabelled')
    need(new['native_verified'] is True and new['failures'] == [] and new['process'] ==
         dict(schema_version=1, returncode=0, timed_out=False, spawn_error=None), 'lifecycle process failed')
    getter = old['getter_calls']
    need(len(getter) == 1 and getter[0]['result'] == getter[0]['owner_current'] == 30
         and getter[0]['args'][0] == 0 and getter[0]['host_writes'] == getter[0]['host_calls'] == 0, 'natural getter missing')
    need(len(old['natural_calls']) == 20 and all(x['host_writes'] == x['host_calls'] == 0
         for x in old['natural_calls']), 'natural suppression missing')
    result = new['analysis']['result']
    expected = dict(candidate_sha256=SHA, status='PASS_CIRCUS_SUPPRESSION_LIFECYCLE',
                    new_battles=3, new_wins=3, new_losses=0, bp_after=99, fresh_cores=2,
                    prefix_wins_reexecuted=0, save_counter_before=3, save_counter_after=4,
                    owner_bytes_verified=64, party_bytes_verified=600, input_only_after_guard=True,
                    host_write_barriers=7, warnings_errors=0, release_ready=False)
    for key, value in expected.items():
        need(type(result.get(key)) is type(value) and result[key] == value, 'result: ' + key)
    for value in (old, new):
        need(value['physical_admission_accepted'] is False and value['suppression_accepted'] is False
             and value['release_ready'] is False, 'original acceptance boundary relabelled')
    need(new['cache']['host_state_injection'] is False and new['cache']['prefix_wins_reexecuted'] == 0,
         'Save30 not genuine')
    return dict(physical_admission_accepted=True, suppression_accepted=True,
                scope='SCOPED_CIRCUS_ACTUAL_RECEPTION_SUPPRESSION_RETURN_SAVE_CONTINUE',
                prefix_candidate=old['original_failure']['normal_save30']['candidate'],
                prefix_not_relabelled_to_successor=True, native_battles_inherited=3,
                bp_before=90, bp_after=99, best_streak_after=33, party_bytes=600, owner_bytes=64,
                save_counter_before=3, save_counter_after=4,
                normal_battle_after_exit_newly_tested=False, final_candidate_transfer_complete=False,
                release_ready=False, new_emulator_processes=0, new_fresh_cores=0,
                arm_compiles=0, arm_links=0, rom_changes=0, accepted_standalone_replays=0)


def execute():
    import copy
    import os
    import subprocess
    import sys
    from datetime import datetime, timezone
    import pr16_circus_fairy_lock as fl
    _, b, c = fl.pipeline()
    b.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    head = b.scope()
    need(set(b.command('git', 'diff', '--name-only', BASE, head).splitlines()) == set(FILES), 'unreviewed source delta')
    state = b.load(b.resume.STATE)
    # 検査fixtureの修復だけ。前回bindingをBASE原本と照合してから限定更新する。
    for path in (RESUME_TEST, RESUME_IMPL):
        prior = subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        need(state['source_bindings'].get(path, identity(prior)) == identity(prior), 'unexpected prior resume binding')
        state['source_bindings'][path] = identity((ROOT/path).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode())
    b.resume.validate(ROOT)
    backlog = b.load(b.resume.BACKLOG)
    checkpoint = b.load(b.resume.CHECKPOINT)
    protected = {p: identity((ROOT / p).read_bytes()) for p in (OLD, LIFE, 'config/active_play_baseline.json')}
    row = next(x for x in backlog['remaining_conditions'] if x['id'] == 'PHYSICAL_CIRCUS_ADMISSION')
    need(not row.get('complete') and row['success_evidence'] is None, 'already accepted; do not duplicate')
    originals, checks, zips = [], [], []
    for spec in SOURCES:
        run = b.api('actions/runs/' + str(spec['run']))
        art = b.api('actions/artifacts/' + str(spec['artifact']))
        validate_actions(run, art, spec)
        raw = subprocess.check_output(['gh', 'api', 'repos/' + b.REPO + '/actions/artifacts/' + str(spec['artifact']) + '/zip'], cwd=ROOT)
        z = archive(raw, spec)
        zips.append(z)
        originals.append(strict(z.read('native-result.json')))
        jobs = b.api('actions/runs/' + str(spec['run']) + '/jobs')['jobs']
        need(jobs and all(j['status'] == 'completed' for j in jobs), 'jobs incomplete')
        checks.append(dict(run_id=run['id'], tested_head=run['head_sha'], status=run['status'],
                           conclusion=run['conclusion'], artifact_id=art['id'], archive=identity(raw),
                           jobs=[{k: j[k] for k in ('id', 'name', 'status', 'conclusion')} for j in jobs]))
    old, new = originals
    for path, original, keys in ((OLD, old, ('candidate', 'draws', 'getter_calls', 'natural_calls', 'build', 'failures')),
                                 (LIFE, new, ('candidate', 'draws', 'events', 'analysis', 'cache', 'generated', 'failures'))):
        tracked = b.load(path)
        need(all(tracked[k] == original[k] for k in keys), 'tracked original drift: ' + path)
    need(strict(zips[1].read('receipt-FINISH.json'))['commit'] == BASE, 'wrong lifecycle finish commit')
    failed = b.api('actions/runs/35505906219')
    need(failed['status']=='completed' and failed['conclusion']=='failure'
         and failed['head_sha']=='82b9f723fa9ed4a6dc8ba0e1eaf64e55b1a825f6','prior receipt failure changed')
    value = verify_pair(old, new)
    value['prior_receipt_failure'] = dict(run_id=failed['id'],head_sha=failed['head_sha'],conclusion='failure',
        artifact_id=10604105487,archive_sha256='11b1846a8419dfac44b7f5c691a1cead39245ddab85562090a1c33a6d2594ba2',
        cause_ja='原本照合後、合成resume fixtureがCircus未完を固定し0件を拒否。checkpoint/backlogの合成bindingと独立した未完/閉鎖fixtureへ修復。',
        new_emulator_processes=0)
    failed2 = b.api('actions/runs/35506191441')
    need(failed2['status']=='completed' and failed2['conclusion']=='failure'
         and failed2['head_sha']=='4a5de6198200589dc5a9685b3e8e598ecf534b93','second receipt failure changed')
    value['prior_routing_failure'] = dict(run_id=failed2['id'],conclusion='failure',artifact_id=10604040930,
        archive_sha256='81e5934d96a8faa8fd685f9c2fcde86828cac59faafd3df4fd7afe99b4c91802',
        cause_ja='26検査中24成功、installがP08を更新してもbindingを同期しない既存不具合で2失敗。事前照合と変更対象限定同期を修復。',
        new_emulator_processes=0)
    value['prior_unbound_source_failure'] = dict(run_id=35506544430,conclusion='failure',
        artifact_id=10603743757,archive_sha256='26d0eb3e4c9009df148c31fe3e79db3e92ff4b05e8290fdb5ee951eb43dca33b',
        cause_ja='新たにbindingへ追加するresume実装を既登録と仮定したKeyError。既登録はBASE照合、未登録は固定BASEの親を保持して新規登録に修復。',
        new_emulator_processes=0)
    value['visual_review'] = verify_screens(zips[1], b.load(REVIEW))
    need(c.validate_calls(old['natural_calls']) == new['analysis']['inherited_suppression'], 'suppression trace differs')
    analysis = fl.validate_lifecycle(zips[1].read('execution/' + c.CASE + '.stdout'),
                                    zips[1].read('execution/' + c.CASE + '.stderr'), 0, old)
    need(analysis == new['analysis'], 'lifecycle revalidation differs')
    trace = zips[0].read('execution/' + c.CASE + '.stderr')
    need(c.rows(trace, b'CIRCUS_GETTER_ABI ') == old['getter_calls']
         and c.rows(trace, b'CIRCUS_SUPPRESSION_CALL ') == old['natural_calls'], 'raw trace projection differs')
    # fl.pipeline resets helper output paths; only this receipt owns subsequent captures.
    b.OUT = OUT
    recent = b.api('actions/runs?branch=' + b.BRANCH + '&per_page=30')['workflow_runs']
    active_native = [r for r in recent if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
                     and ('circus' in r['path'].lower())]
    need(not active_native, 'newer Circus execution still pending')
    newer_native = [r for r in recent if r['id'] > SOURCES[1]['run'] and r['path'] in
                    ('.github/workflows/pr16-circus-fairy-lock.yml', '.github/workflows/pr16-circus-getter.yml')]
    need(not newer_native, 'newer native result requires reconciliation first')
    observed = [{k: r[k] for k in ('id', 'head_sha', 'path', 'status', 'conclusion')} for r in recent]
    prefix = 'evidence/pr16_circus_acceptance/' + str(os.environ['GITHUB_RUN_ID']) + '/'
    value.update(schema_version=1, task=TASK, classification='SCOPED_ACCEPTANCE', candidate=new['candidate'],
                 source_head=head, recording_run=int(os.environ['GITHUB_RUN_ID']), source_runs=checks,
                 originals_unchanged=True, native_revalidation_passed=True,
                 inherited_suppression=new['analysis']['inherited_suppression'],
                 source_bindings={p: identity((ROOT/p).read_bytes()) for p in (*FILES, OLD, LIFE)})
    evidence = prefix + 'acceptance.json'
    checks_path = prefix + 'actions.json'
    b.write(REPORT, b.stable(value)); b.write(evidence, b.stable(value)); b.write(checks_path, b.stable(observed))
    row.update(complete=True, physical_acceptance_complete=True, status='PASS_SCOPED_CANDIDATE_PENDING_P08_TRANSFER',
               accepted_candidate_sha256=SHA, success_evidence=REPORT, successor_transfer_condition_id='FINAL_NATIVE_ACCEPTANCE',
               reason_ja='実受付→自然getter30→正規抑制predicate8/delegate12を旧failure内の成功範囲として保持。別完了runの追加3勝、party600/owner64復元、通常Save/fresh Continueと29画面を原本再照合してscoped受入。旧30勝は旧候補のまま。',
               resume='Circusを再実行せずP08変更影響台帳へ。退出後通常戦闘を新規受入したとは主張しない。')
    physical, gates = b.resume.pending_ids(backlog)
    need(physical == [] and gates == ['FINAL_NATIVE_ACCEPTANCE', 'RELEASE_DECISION'], 'unexpected remaining gates')
    before_checkpoint = copy.deepcopy(checkpoint)
    checkpoint['physical_gap_count'] = len(physical)
    need({k:v for k,v in checkpoint.items() if k != 'physical_gap_count'} ==
         {k:v for k,v in before_checkpoint.items() if k != 'physical_gap_count'}, 'BP acceptance mutated')
    nxt = 'P08の変更ROM範囲/owner/runner/fixture/契約を保存レシピから照合し、46487d98候補への既受入移送と必要な最小代表回帰を確定する。旧ARM/30勝/受入単体は再実行しない。'
    stop = 'Circus実受付・正規抑制・通常帰還/保存再開を完了Actions・原本・29画面から正式scoped受入。physical残件0。新native0/ROM変更0。P08最終候補の変更影響移送とrelease判断は未完。'
    state['circus_physical_acceptance'] = dict(path=REPORT, candidate=new['candidate'], source_runs=[x['run'] for x in SOURCES], complete=True)
    state['remaining_physical_gap_ids'] = physical; state['remaining_p08_gate_ids'] = gates
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = nxt
    state['next_action'].update(id='P08_CHANGE_IMPACT_TRANSFER',
        read_paths=[REPORT, 'content/modernization/pr16_saved_reconstruction.json', 'scripts/pr16_saved_reconstruction.py', OLD, b.resume.BACKLOG],
        stop_rule_ja='影響台帳と必要最小回帰を区切りごとに保存する。merge/release/active baseline変更は別途明示指示が必要。')
    state['remaining_sequence_ja'] = 'Circus scoped受入完了 → P08変更影響移送/必要最小回帰 → 配布準備判定（公開操作は別指示）'
    state['candidate_scope_ja'] = 'この欄は正式BP親候補ceddbe91のidentityを維持。Ring/policyは4ea33fb8、Circusは46487d98でscoped受入済み。P08最終候補への移送/回帰・製品SHA固定は未完。'
    state['observed_head'] = head; state['observed_date_jst'] = '2026-09-20'
    state['observed_head_semantics'] = '受入集約直前remote。BP旧原本とCircus旧failureを変更せず新receiptで意味を接続。'
    state['observed_head_checks'] = dict(scope_head=head, runs=observed, reason_ja='完了native run35504302893はsuccess、getter run35503514936はfailureのまま。最新source CIのaction_required等をnative成功と混同しない。詳細は'+checks_path)
    state['pending_runs'] = [dict(run_id=r['id'], tested_head=r['head_sha'], status=r['status']) for r in recent
                             if r['status'] in ('queued','in_progress') and r['id'] != int(os.environ['GITHUB_RUN_ID'])]
    state['session_execution_summary'] = dict(new_emulator_processes=0, arm_compiles=0, arm_links=0, accepted_standalone_replays=0,
                                               prefix_wins_reexecuted=0, scope_ja='完了原本・画面・Actionsの照合のみ。nativeの再実行なし。')
    note = 'Circus正式scoped受入はpr16_circus_acceptance.json。35504302893の29画面/3勝/Save、35503514936の自然getter/抑制を再実行しない。旧failureの意味は維持。'
    state['do_not_repeat'].insert(0, note)
    final = next(x for x in backlog['remaining_conditions'] if x['id']=='FINAL_NATIVE_ACCEPTANCE')
    final['resume'] = nxt; final['circus_success_evidence'] = REPORT
    state['logs_synchronized'] = state['p08_resume_synchronized'] = True
    b.write(b.resume.BACKLOG, b.stable(backlog)); b.write(b.resume.CHECKPOINT, b.stable(checkpoint))
    tracked_paths = [*FILES, REPORT, evidence, checks_path, b.resume.BACKLOG, b.resume.CHECKPOINT]
    for name in tracked_paths:
        state['source_bindings'][name] = identity((ROOT/name).read_bytes())
    b.write(b.resume.STATE, b.stable(state)); b.write(b.resume.DOC, b.resume.render(state).encode())
    b.resume.validate(ROOT)
    for label, args in (
        ('receipt-contracts', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', Path(TEST).name, '-v']),
        ('resume', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_pr16_resume.py', '-v']),
        ('task-graph', [sys.executable, 'scripts/validate_task_graph.py'])):
        _, _, proc = b.capture(args, label)
        need(b.exited(proc) == 0, label + ' failed')
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths = [*tracked_paths, b.resume.STATE, b.resume.DOC, *b.LOGS]
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / Circus正式scoped受入\n'
             '- Status: DONE（P08最終移送・releaseは未完）\n- Version: pr16-circus-acceptance-v1\n'
             '- Summary: '+stop+'\n- Files changed: '+', '.join(paths)+'\n'
             '- Verify: 新規receipt契約・resume・task graph PASS。旧原本のgetter/predicate/delegate、lifecycle原本、29画面hash/目視と完了Actions再照合。新native/ARM/旧30勝再実行0。\n'
             '- Prior failure: run35505906219はresume合成fixtureのCircus未完固定でfailure。原本成功を変更せず検査を修復。run35506191441はinstallのP08 hash同期漏れ2検査でfailure。変更前照合/限定同期を修復、新native0。\n'
             '- Commit: 同branch非force commit/push、remote/HEADを読戻し。\n'
             '- Network: GitHub RESTの固定native2run/2artifact、記録失敗2runと最新30Actionsの照合のみ。\n- Next: '+nxt+'\n')
    for name in b.LOGS:
        need(TASK+'\n' not in (ROOT/name).read_text(), 'duplicate receipt log')
        with (ROOT/name).open('a') as stream: stream.write(entry)
    need(all(identity((ROOT/p).read_bytes()) == v for p,v in protected.items()), 'protected original changed')
    subprocess.run(['git','add','--',*paths], cwd=ROOT, check=True)
    changed = set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed <= set(paths), 'index scope')
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT, guard.ALLOWED = head, OUT, changed
    guard.guard()
    subprocess.run(['git','diff','--cached','--check'], cwd=ROOT, check=True)
    b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'], cwd=ROOT, check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'], cwd=ROOT, check=True)
    subprocess.run(['git','commit','-m',TASK+': 実受付・抑制・保存の正式受入、physical0とP08移送入口'], cwd=ROOT, check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH], cwd=ROOT, check=True)
    committed = b.scope()
    need(not b.command('git','status','--porcelain','--untracked-files=no'), 'dirty after push')
    (OUT/'receipt.json').write_bytes(b.stable(dict(task=TASK, commit=committed, run_id=int(os.environ['GITHUB_RUN_ID']), non_force_push=True)))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+committed)


def pack():
    """後続の限定ソース調査用。既存tracked UTF-8のみ、ROM/save/ZIPは含めない。"""
    import subprocess
    OUT.mkdir(parents=True, exist_ok=True)
    names = subprocess.check_output(['git','ls-files'], cwd=ROOT, text=True).splitlines()
    with zipfile.ZipFile(OUT/'next-sources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in names:
            p = Path(name)
            selected = ((name.startswith('scripts/pr16_') and p.suffix == '.py')
                        or (name.startswith('tests/test_pr16_') and p.suffix == '.py')
                        or (p.parent == Path('content/modernization') and p.suffix == '.json')
                        or name in ('AGENTS.md','design/active_play_baseline.md','config/active_play_baseline.json',
                                    'scripts/validate_task_graph.py'))
            if selected:
                raw = (ROOT/name).read_bytes(); raw.decode('utf-8')
                need(len(raw) < 16*1024*1024, 'oversized context source')
                z.writestr(name, raw)


if __name__ == '__main__':
    import sys
    need(len(sys.argv)==2, 'command required')
    if sys.argv[1]=='execute': execute()
    elif sys.argv[1]=='pack': pack()
    else: raise ValueError('unknown command')
