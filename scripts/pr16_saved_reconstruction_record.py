#!/usr/bin/env python3
"""保存byte再構成の成功原本と正本・両ログを検証して同branchへ記録する。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_saved_recipe as s
import pr16_resume as resume
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
TASK = 'USER-20260920-CIRCUS-SAVED-RECONSTRUCTION'
BASE = 'c2737e1b57ff28909d43c13ad4223d0380c0029a'
RUN, JOB, ARTIFACT = 35465528252, 105957035501, 10591650346
ZIP_ID = dict(size=263166, sha256='2794bdf353004a75754f2a4c20347822572bb252093688bcfbe283b96088bdc9')
SELF = 'scripts/pr16_saved_reconstruction_record.py'
TEST = 'tests/test_pr16_saved_reconstruction_record.py'
WORKFLOW = '.github/workflows/pr16-saved-reconstruction-record.yml'
NORMAL = 'content/modernization/pr16_saved_reconstruction_recipes.json'
REPORT = 'content/modernization/pr16_saved_reconstruction.json'
ORIGINAL = 'content/modernization/pr16_circus_rental_resume.json'
EVIDENCE = 'evidence/pr16_saved_reconstruction/'+str(RUN)+'/'
OUT = ROOT/'.local/pr16-saved-record'
LOGS = ('design/run_log.md', 'design/version_log.md')
TARGET = dict(size=33554432, sha256='2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183')
ANCHOR = dict(size=33554432, sha256='6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3')
NEXT = ('保存byte再構成は完了。scripts/pr16_saved_reconstruction.py reconstructを別processで使い、'
        '旧親builder/compile/Ring hostを起動せず同じ2b107e7eを復元する。24勝prefixを保持し、'
        '25戦目の通常レンタル/技選択だけを改善して真正30勝と通常Save/fresh Continueへ進む。'
        '25戦目の最初の入力変更より前のevent列を完全照合する。受入24勝の独立再実行、'
        '勝敗/連勝/効果/PC/LR/save注入は禁止。30勝後に正規特性抑制、影響範囲P08へ進む。')
SOURCE_PATHS = (SELF, TEST, WORKFLOW, 'scripts/pr16_saved_recipe.py',
    'scripts/pr16_saved_reconstruction.py', 'tests/test_pr16_saved_recipe.py',
    'tests/test_pr16_saved_reconstruction.py', 'tests/test_pr16_saved_object_bytes.py',
    'content/modernization/pr16_saved_reconstruction_seed.json',
    '.github/workflows/pr16-saved-reconstruction.yml',
    '.github/workflows/pr16-saved-reconstruction-source.yml')


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def api(path):
    return json.loads(command('gh', 'api', 'repos/'+REPO+'/'+path))


def scope():
    s.need(os.environ.get('GITHUB_REPOSITORY') == REPO and
           os.environ.get('GITHUB_REF') == 'refs/heads/'+BRANCH, 'write scope differs')
    head = command('git', 'rev-parse', 'HEAD')
    pr = api('pulls/16')
    s.need(pr['state'] == 'open' and pr['draft'] is True and not pr['merged'] and
           pr['head']['repo']['full_name'] == REPO and pr['head']['ref'] == BRANCH, 'PR scope differs')
    s.need(command('git', 'ls-remote', '--exit-code', 'origin', 'refs/heads/'+BRANCH).split() ==
           [head, 'refs/heads/'+BRANCH], 'remote branch advanced')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], cwd=ROOT, check=True)
    return head


def validate_receipt(report, recipe_bytes):
    s.need(report['classification'] == 'SAVED_BYTE_CHAIN_VERIFIED_NO_RECOMPILE' and
           report['tested_head'] == BASE and report['run_id'] == RUN, 'proof scope differs')
    s.need(report['candidate'] == TARGET and report['normalized_recipe'] == s.identity(recipe_bytes), 'recipe identity differs')
    for key in ('arm_compiles', 'arm_links', 'process_spawns', 'new_emulator_processes',
                'accepted_native_cases_replayed', 'accepted_host_tests_replayed', 'rom_changes'):
        s.need(type(report[key]) is int and report[key] == 0, 'unexpected execution: '+key)
    s.need(report['process_barrier_active'] is True, 'process barrier absent')
    for key in ('genuine_30_wins_verified', 'physical_admission_accepted', 'suppression_accepted', 'release_ready'):
        s.need(report[key] is False, 'unsupported acceptance: '+key)
    proof, model = report['reconstruction'], s.strict(recipe_bytes)
    s.need(proof['candidate'] == TARGET and proof['parent'] == ANCHOR and
           proof['whole_chain_rollback_matches_parent'] is True, 'whole chain proof absent')
    s.need(len(proof['layers']) == len(model['recipes']) == 20 and
           sum(row['patches'] for row in proof['layers']) == 425, 'layer boundary differs')
    current = ANCHOR
    for layer, recipe in zip(proof['layers'], model['recipes']):
        s.need(layer['parent'] == recipe['parent'] == current and layer['candidate'] == recipe['candidate'] and
               layer['whole_rom_rollback_matches_parent'] is True and layer['patches'] == len(recipe['patches']), 'layer proof differs')
        current = layer['candidate']
    s.need(current == TARGET and model['native_acceptance'] is False and model['release_ready'] is False, 'terminal scope differs')
    return model


def project(state, backlog, report):
    state, backlog = copy.deepcopy(state), copy.deepcopy(backlog)
    rows = [r for r in backlog['remaining_conditions'] if r['id'] == 'PHYSICAL_CIRCUS_ADMISSION']
    s.need(len(rows) == 1 and rows[0]['success_evidence'] is None and not rows[0].get('complete'), 'physical gap moved')
    s.need(state['latest_native_run'] == 34946969126 and not state['release_ready'], 'formal BP scope moved')
    rows[0]['reconstruction_checkpoint'] = REPORT
    rows[0]['resume'] = NEXT
    ref = dict(path=REPORT, classification=report['classification'], normalization_run=RUN,
               candidate=TARGET, arm_compiles=0, arm_links=0, physical_admission_accepted=False)
    state['saved_parent_reconstruction'] = ref
    stop = ('旧親20層425差分を保存byteのみで復元し、全層hash/allocation・全ROM逆適用と'
            'network/process禁止の固定JSON再開経路を検証済み。候補2b107e7eは不変、ARM compile/link/nativeは0。'
            '実24勝72BP・25戦目敗北・通常Save/fresh Continueは旧run35457636604の受入範囲を維持し、'
            '真正30勝・実受付から特性抑制の完了は主張しない。')
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = NEXT
    state['next_action']['id'] = 'CIRCUS_BATTLE25_ORDINARY_POLICY'
    state['next_action']['read_paths'] = [REPORT, 'scripts/pr16_saved_reconstruction.py',
        'content/modernization/pr16_circus_rental_closeout.json', ORIGINAL,
        'scripts/pr16_circus_rental_resume.py', resume.BACKLOG]
    note = ('run35465528252で旧親20層425差分の保存byte復元・全ROMrollbackを検証済み。'
            '保存レシピと核が不変ならnormalize/旧builder/compiler/既受入Ring hostを再実行しない。'
            '通常再開は固定JSONのreconstructのみ。履歴bootstrap全体のARM数unknownを0へ改作しない。')
    if note not in state['do_not_repeat']:
        state['do_not_repeat'].insert(0, note)
    # render()の単一段落契約を維持する。配列はjoin時にTypeErrorとなる。
    state['remaining_sequence_ja'] = ('同一2b107e7eの25戦目通常入力から真正30勝と保存 → '
        '正規実受付から特性抑制 → 変更影響範囲P08最終統合・release判断（公開操作は別指示）')
    return state, backlog


def write(name, raw):
    p = s.safe(ROOT, name)
    raw.decode('utf-8'); s.need(b'\0' not in raw, 'text only')
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)


def tests():
    import unittest
    name = 'test_pr16_saved_reconstruction_record.py'
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern=name)
    with (OUT/'record-tests.txt').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    s.need(result.wasSuccessful() and result.testsRun == 8 and not result.skipped, 'record contracts failed')
    return dict(tests_run=result.testsRun, success=True, skipped=0)


def main():
    head = scope(); OUT.mkdir(parents=True, exist_ok=True)
    s.need(not (ROOT/REPORT).exists(), 'already recorded; do not replay')
    state = resume.validate(ROOT)
    s.need(not command('git', 'status', '--porcelain', '--untracked-files=no'), 'dirty input')
    run, job, artifact = api('actions/runs/'+str(RUN)), api('actions/jobs/'+str(JOB)), api('actions/artifacts/'+str(ARTIFACT))
    s.need(run['head_sha'] == BASE and run['status'] == 'completed' and run['conclusion'] == 'success', 'normalization run not successful')
    s.need(job['run_id'] == RUN and job['status'] == 'completed' and job['conclusion'] == 'success', 'normalization job not successful')
    s.need(artifact['workflow_run']['id'] == RUN and artifact['workflow_run']['head_sha'] == BASE and
           artifact['digest'] == 'sha256:'+ZIP_ID['sha256'] and not artifact['expired'], 'artifact binding differs')
    raw = subprocess.check_output(['gh', 'api', 'repos/'+REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'], cwd=ROOT)
    s.need(s.identity(raw) == ZIP_ID, 'artifact archive differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        expected = {'reconstruction.json', 'normalized-recipes.json', 'tests.txt', 'tested-head.txt', 'normalize.stdout', 'normalize.stderr'}
        s.need(set(archive.namelist()) == expected and len(archive.namelist()) == len(expected), 'artifact members differ')
        contents = {name:archive.read(name) for name in expected}
    original = s.strict(contents['reconstruction.json'])
    model = validate_receipt(original, contents['normalized-recipes.json'])
    s.need(contents['tested-head.txt'].decode().strip() == BASE and not contents['normalize.stderr'], 'artifact boundary differs')
    s.need(model['runtime_metadata'] == resume.load(ROOT, ORIGINAL)['build'], 'runtime metadata changed')
    for name, binding in original['source_bindings'].items():
        s.need(s.identity(s.safe(ROOT, name).read_bytes()) == binding, 'normalization source changed: '+name)
    write(NORMAL, contents['normalized-recipes.json'])
    evidence = {}
    for name, data in contents.items():
        if name == 'normalized-recipes.json':
            continue
        path = EVIDENCE+name; write(path, data); evidence[path] = s.identity(data)
    program = """import sys,json
from pathlib import Path
sys.path.insert(0,'scripts')
import pr16_saved_reconstruction as r
def offline(event,args):
    if event.startswith('socket.') or event in ('urllib.Request','http.client.connect'):
        raise RuntimeError('保存JSON再開中のnetworkは禁止')
sys.addaudithook(offline)
result=r.reconstruct(r.ROOT/'.local/pr16-saved-record/runtime')
assert r._guard_active and result['whole_chain_rollback_matches_parent']
assert not any(name.startswith(('pr16_circus_','pr16_ring_','tools.')) for name in sys.modules)
result['network_barrier_active']=True
result['process_barrier_active']=True
result['legacy_modules_loaded']=False
print(json.dumps(result))
"""
    execution = subprocess.run([sys.executable, '-c', program], cwd=ROOT, capture_output=True, timeout=120)
    write(EVIDENCE+'runtime.stderr', execution.stderr)
    s.need(execution.returncode == 0 and not execution.stderr, 'offline runtime reconstruction failed')
    runtime = s.strict(execution.stdout)
    s.need(runtime['candidate'] == TARGET and runtime['layers'] == original['reconstruction']['layers'] and
           runtime['network_barrier_active'] is True and runtime['legacy_modules_loaded'] is False, 'runtime route differs')
    write(EVIDENCE+'runtime.json', s.stable(runtime))
    evidence[EVIDENCE+'runtime.json'] = s.identity(s.stable(runtime))
    evidence[EVIDENCE+'runtime.stderr'] = s.identity(execution.stderr)
    report = dict(schema_version=1, task=TASK, classification='SAVED_PARENT_RECONSTRUCTION_COMPLETE_NATIVE_30_OPEN',
        source_head=head, normalization_source_head=BASE, candidate=TARGET, anchor=ANCHOR,
        normalized_recipe=dict(path=NORMAL, **s.identity(contents['normalized-recipes.json'])),
        normalization=dict(run_id=RUN, job_id=JOB, artifact_id=ARTIFACT, archive=ZIP_ID, conclusion='success'),
        layer_count=20, patch_count=425, whole_rom_reverse_verified=True, offline_runtime_verified=True,
        reconstruction_child_processes=0, new_python_runtime_verifications=1, arm_compiles=0, arm_links=0,
        new_emulator_processes=0, accepted_native_cases_replayed=0, accepted_host_tests_replayed=0,
        raw_evidence=evidence, rom_changes=0, genuine_30_wins_verified=False, physical_admission_accepted=False,
        suppression_accepted=False, release_ready=False, historical_bootstrap_arm_count=None,
        old_native_boundary=dict(run_id=35457636604, genuine_wins=24, bp=72, loss_battle=25,
                                 candidate=TARGET, original_conclusion='failure'),
        failure_history=[dict(run_id=35464893016, conclusion='failure', diagnosis='受付adapterの明示padding未継承'),
                         dict(run_id=35465115956, conclusion='failure', diagnosis='objdump OBJECT定数8byteを見落とした'),
                         dict(run_id=35465795453, job_id=105957767914, conclusion='failure',
                              artifact_id=10591186356,
                              archive=dict(size=980, sha256='5f93d37f43902618f1e03de3500793dab13096ac1286f429bdb7ef099efabd73'),
                              diagnosis='投影したremaining_sequence_jaが配列で、固定MD生成時にTypeError。文字列契約と実render回帰を追加。')],
        correction_ja='コード284byte（OBJECT定数8byteを含む）と元ADAPTER_SIZE304の明示FF padding20byteで元payload hash一致。',
        next_action_ja=NEXT)
    report['record_tests'] = tests()
    state, backlog = project(state, resume.load(ROOT, resume.BACKLOG), report)
    state['observed_head'] = head
    state['observed_date_jst'] = '2026-09-20'
    state['observed_head_semantics'] = '保存byte正本の記録source HEAD。native最終試行は35457636604、正式BP checkpointは不変。'
    observed = [{k:run[k] for k in ('id','head_sha','status','conclusion')}]
    for item in report['failure_history']:
        prior = api('actions/runs/'+str(item['run_id']))
        s.need(prior['status'] == 'completed' and prior['conclusion'] == 'failure', 'failure history changed')
        observed.append({k:prior[k] for k in ('id','head_sha','status','conclusion')})
    state['observed_head_checks'] = dict(scope_head=head, runs=observed,
        reason_ja='復元run35465528252は成功。先行3失敗とnative30未達は維持。記録run自身はsnapshot外で、全CI greenは主張しない。')
    state['pending_runs'] = []
    state['recording_workflow'] = dict(run_id=int(os.environ['GITHUB_RUN_ID']), source_head=head,
                                      status_at_snapshot='in_progress', native_work=False)
    state['session_execution_summary'] = dict(scope_ja='保存byte復元と正本記録。旧20層compile/Ring host/nativeを呼ばない。',
        layer_count=20, patch_count=425, new_emulator_processes=0, arm_compiles=0, arm_links=0,
        accepted_standalone_replays=0, new_python_runtime_verifications=1)
    state['logs_synchronized'] = state['p08_resume_synchronized'] = True
    write(REPORT, s.stable(report)); write(resume.BACKLOG, s.stable(backlog))
    bindings = (*SOURCE_PATHS, NORMAL, REPORT, *evidence)
    for name in bindings:
        state['source_bindings'][name] = s.identity(s.safe(ROOT,name).read_bytes())
    if resume.BACKLOG in state['source_bindings']:
        state['source_bindings'][resume.BACKLOG] = s.identity((ROOT/resume.BACKLOG).read_bytes())
    write(resume.STATE, s.stable(state)); write(resume.DOC, resume.render(state).encode())
    resume.validate(ROOT)
    with (OUT/'resume-tests.txt').open('w') as stream:
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_pr16_resume.py', '-v'],
                       cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    with (OUT/'task-graph.txt').open('w') as stream:
        subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    paths = [NORMAL, REPORT, resume.STATE, resume.DOC, resume.BACKLOG, *evidence, *LOGS]
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 旧親を再compileしない保存byte再構成\n'
        '- Status: DONE（再構成経路。真正30勝・正規特性抑制・P08統合は未完）\n'
        '- Version: pr16-saved-byte-chain-20\n'
        '- Summary: 固定Stage80から20層425差分を保存BPS・原本byteのみで正規化し、候補2b107e7eへ全hash一致。全層allocationと全ROM逆適用を確認。'
        '通常再開は保存JSONと純粋核だけで、旧builder・network・子processは禁止。\n'
        '- Summary: 受付adapterのOBJECT定数8byteと明示20byte FF paddingを原本から回復。先行失敗35464893016/35465115956と記録型不整合35465795453は失敗のまま保存。単一段落契約と実render回帰を追加。\n'
        '- Files changed: '+', '.join((*SOURCE_PATHS,*paths))+'\n'
        '- Verify: run35465528252/job105957035501成功、artifact10591650346 sha256='+ZIP_ID['sha256']+'。'
        '核13契約の未影響12件と原本IO9契約の証跡継承、影響decoder3件PASS。記録8契約（投影後render/JSON往復を含む）、固定JSONのoffline実ROM再開、'
        'resume tests、pr16_resume.validate、task graph PASS。commit前index差分private guardで新規違反0、diff check必須。\n'
        '- Native: 今回0。候補byte変更0、ARM compile/link0、受入単体再実行0。履歴bootstrap全体ARM数はunknownを維持。\n'
        '- Commit: この記録を含む同branch非force commit。自己SHAはremote ref/receiptを参照。\n'
        '- Network: GitHub connector/Actionsの固定run/artifact照合と固定CFRU charmapのみ。private入力取得なし、ROM/save/credential追加追跡なし。\n'
        '- Next: '+NEXT+'\n')
    for name in LOGS:
        p = ROOT/name; s.need(TASK not in p.read_text(), 'duplicate completion log')
        with p.open('a') as stream:
            stream.write(entry)
    subprocess.run(['git','add','--',*paths], cwd=ROOT, check=True)
    changed = set(command('git','diff','--cached','--name-only',head).splitlines())
    s.need(changed == set(paths), 'recording path boundary differs')
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT, guard.ALLOWED = head, OUT, changed
    guard.guard()
    subprocess.run(['git','diff','--cached','--check'], cwd=ROOT, check=True)
    scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'], cwd=ROOT, check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'], cwd=ROOT, check=True)
    subprocess.run(['git','commit','-m',TASK+': 保存20層復元とoffline再開を受入・固定引継ぎと両ログ同期'], cwd=ROOT, check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH], cwd=ROOT, check=True)
    commit = scope()
    s.need(not command('git','status','--porcelain','--untracked-files=no'), 'dirty after push')
    receipt = dict(task=TASK, source_head=head, commit=commit, run_id=int(os.environ['GITHUB_RUN_ID']),
                   normalization_run=RUN, native_acceptance=False, non_force_push=True)
    (OUT/'receipt.json').write_bytes(s.stable(receipt))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__ == '__main__':
    main()
