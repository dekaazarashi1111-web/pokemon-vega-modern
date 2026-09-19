#!/usr/bin/env python3
"""構築済みREADY/6体候補のrunner契約を復元し、未実行nativeだけを再開する。"""
from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
import pr16_circus_rental_drought as inherited
need, identity, stable = inherited.need, inherited.identity, inherited.stable
SELF = 'scripts/pr16_circus_rental_resume.py'
TEST = 'tests/test_pr16_circus_rental_resume.py'
WORKFLOW = '.github/workflows/pr16-circus-rental-resume.yml'
REPORT = 'content/modernization/pr16_circus_rental_resume.json'
PREVIOUS = 'content/modernization/pr16_circus_rental_drought.json'
BASE = '7838f3f510fdf004a426b84cd75141c6dff8b207'
COMPILE_RUN = 35457143420
COMPILE_JOB = 105934337378
COMPILE_HEAD = '667ef6aee34f0e7dda25f6d94d8db5649a571fd7'
RUN = 35456028016
JOB = 105931324175
SHA = '2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183'
OUT = ROOT / '.local/pr16-circus-rental-resume'
FILES = (SELF, TEST, WORKFLOW)
NEXT = '候補2b107e7eを再linkせず、親から復元した受付/launch契約で未実行だった22戦目以降のnativeを検証する。旧21勝は同一continuation内のprefixだけとし、真正30勝・通常Save/fresh Continue後に正規特性抑制へ進む。'


def restore_contract(saved):
    """ROM差分レシピを変更せず、親の非ROM runner契約を継承する。"""
    need(saved['candidate'] == dict(size=33554432, sha256=SHA), 'saved candidate identity')
    need(saved['independent_arm_links'] == 2 and saved['whole_rom_rollback_matches_parent'] is True,
         'saved independent links/rollback absent')
    parent = saved['old']
    need(parent['candidate'] == saved['parent'], 'saved parent identity')
    need('reception' not in saved and 'launch_sites' not in saved, 'original missing-contract failure differs')
    need(set(parent['reception']) == {'bridge', 'circus', 'selector', 'sp072'}, 'reception contract keys')
    for address in parent['reception'].values():
        need(type(address) is int and 0x08000000 <= address < 0x0A000000, 'reception pointer bound')
    need(len(parent['launch_sites']) == 3, 'three native launch sites required')
    for row in parent['launch_sites']:
        need(type(row['new']) is int and 0x08000000 <= row['new'] < 0x0A000000, 'launch pointer bound')
    result = deepcopy(parent)
    result.update(deepcopy(saved))
    # 継承対象は親にしかないmetadata。今回のallocation/patches/identityは絶対に置換しない。
    for key in saved:
        need(result[key] == saved[key], 'saved recipe overwritten: ' + key)
    return result


def checked_patch(raw, recipe):
    from pr16_circus_streak import bounded_patch
    need(identity(raw) == recipe['parent'], 'reconstruction parent identity')
    result = bounded_patch(raw, recipe['patches'])
    need(identity(result) == recipe['candidate'], 'reconstruction candidate identity')
    for row in recipe['allocation']['allocations']:
        need(identity(result[row['start']:row['end_exclusive']])['sha256'] == row['content_sha256'],
             'reconstruction allocation differs: ' + row['name'])
    reverse = [dict(p, before=p['after'], after=p['before']) for p in recipe['patches']]
    need(bounded_patch(result, reverse) == raw, 'whole ROM rollback differs')
    return result


def configure():
    for key, value in dict(SELF=SELF, TEST=TEST, WORKFLOW=WORKFLOW, REPORT=REPORT, OUT=OUT,
                          NEXT=NEXT, NEW=tuple(dict.fromkeys((*inherited.NEW, *FILES)))).items():
        setattr(inherited, key, value)
    inherited.record = record
    d, b = inherited.configure()
    d.FILES = tuple(dict.fromkeys((*d.FILES, *FILES, PREVIOUS)))
    d.c.FILES = d.FILES
    return d, b


def record(value, phase, stop, next_step):
    import pr16_resume as resume
    d, b = configure()
    r = b.rec
    state = resume.load(ROOT, resume.STATE)
    loss = resume.load(ROOT, r.REPORT)
    (ROOT / REPORT).write_bytes(stable(value))
    ref = dict(path=REPORT, classification=value['classification'], run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_rental_contract_resume'] = loss['rental_contract_resume'] = ref
    state['circus_continuous_followup'] = dict(ref, target_wins=30)
    state['prior_actions_reconciled'] = value['actions_reconciled']
    note = ('run35456028016/job105931324175は候補2b107e7eの独立2link/rollback成功後、'
            "runner契約reception欠落でnative0停止。失敗原本と候補は不変。親の受付/launch metadataを継承して"
            '未実行nativeだけを再開し、旧ARM再link・旧境界診断・受入単体は再実行しない。')
    if note not in state['do_not_repeat']:
        state['do_not_repeat'].insert(0, note)
    compile_note = ('run35457143420/job105934337378は候補2b107e7eの受付/launch契約復元・再構築成功後、'
                    'policy includeがsc_events定義より先でC compile失敗/native0。旧失敗を保持し、'
                    'host counter前方定義だけを追加した後継で未実行nativeへ進む。旧ARM再link0。')
    if compile_note not in state['do_not_repeat']:
        state['do_not_repeat'].insert(0, compile_note)
    r.SELF, r.TEST, r.WORKFLOW, r.HEADER = SELF, TEST, WORKFLOW, inherited.HEADER
    r.TASK = 'USER-20260920-CIRCUS-RENTAL-CONTRACT-RUN' + os.environ['GITHUB_RUN_ID']
    r.checkpoint(state, loss, stop, next_step,
                 [REPORT, *FILES, PREVIOUS, *value.get('text_evidence', {})], phase,
                 value['classification'] + '。既存candidate2b107e7e/全allocation/rollback固定。'
                 '受付・launch metadata継承とhost counter前方定義のみ、ROM変更0/ARM再link0/受入単体再実行0。'
                 '100events prefix同一意味、実勝敗・owner64・元party600・通常Save/fresh Continueを別判定。')


def refresh_changed_bindings(state):
    """旧HEADで同一性を証明した意図した3ファイルだけを更新する。"""
    import pr16_resume as resume
    for path, bound in state['source_bindings'].items():
        current = identity((ROOT / path).read_bytes())
        if current != bound:
            need(path in FILES, 'unexpected source drift: ' + path)
            previous = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
            need(identity(previous) == bound, 'previous source binding differs: ' + path)
    # 生成MDを先に同期し、resumeの他の受入/候補/台帳検査は一切緩和しない。
    for path in FILES:
        state['source_bindings'][path] = identity((ROOT / path).read_bytes())
    (ROOT / resume.STATE).write_bytes(stable(state))
    (ROOT / resume.DOC).write_text(resume.render(state))
    return resume.validate(ROOT)


def policy_with_counter(text):
    """policy includeはcontrollerの定義より前。Cの同一内部リンケージを前方定義する。"""
    declaration = 'static unsigned sc_events;\n'
    need(declaration not in text, 'duplicate event counter declaration')
    return declaration + text



def prepare():
    import pr16_resume as resume
    d, b = configure()
    r = b.rec
    head = r.scope()
    state = resume.load(ROOT, resume.STATE)
    need(r.command('git', 'rev-parse', 'HEAD^') == BASE, 'resume base advanced')
    need(set(r.command('git', 'diff', '--name-only', BASE, head).splitlines()) == set(FILES), 'resume WIP scope')
    last = resume.load(ROOT, REPORT)
    need(last.get('recording_run') == COMPILE_RUN, 'resume already attempted; inspect original instead')
    need(last['native']['actual_new_processes'] == 0 and last['native']['failures'] ==
         [dict(stage='setup-or-execution', error='Circus native controller compile failed')],
         'previous controller compilation failure differs')
    for path, bound in last['text_evidence'].items():
        need(identity((ROOT / path).read_bytes()) == bound, 'previous runner evidence changed: ' + path)
    error_path = 'evidence/pr16_circus_rental_drought/' + str(COMPILE_RUN) + '/native/compile.stderr'
    errors = (ROOT / error_path).read_text()
    need('sc_events' in errors and 'undeclared' in errors, 'original counter declaration failure absent')
    state = refresh_changed_bindings(state)
    previous = resume.load(ROOT, PREVIOUS)
    need(previous['recording_run'] == RUN and previous['native']['actual_new_processes'] == 0,
         'previous native already executed')
    need(previous['native']['failures'] == [dict(stage='setup-or-execution', error="'reception'")],
         'previous failure differs')
    for path, bound in previous['text_evidence'].items():
        need(identity((ROOT / path).read_bytes()) == bound, 'previous evidence changed: ' + path)
    recipe = restore_contract(previous['build'])
    for path, bound in recipe['source_bindings'].items():
        need(identity((ROOT / path).read_bytes()) == bound, 'saved source binding: ' + path)
    run, job = r.api('actions/runs/' + str(RUN)), r.api('actions/jobs/' + str(JOB))
    need(run['status'] == 'completed' and run['conclusion'] == 'failure'
         and run['head_sha'] == 'd1af762472eb529b4fcad93bac65c4e44aa05db3', 'previous Actions differs')
    need(job['run_id'] == RUN and job['status'] == 'completed' and job['conclusion'] == 'failure', 'previous job differs')
    compile_run = r.api('actions/runs/' + str(COMPILE_RUN))
    compile_job = r.api('actions/jobs/' + str(COMPILE_JOB))
    need(compile_run['head_sha'] == COMPILE_HEAD and compile_run['conclusion'] == 'failure'
         and compile_run['status'] == 'completed', 'compilation run identity differs')
    need(compile_job['run_id'] == COMPILE_RUN and compile_job['conclusion'] == 'failure'
         and compile_job['status'] == 'completed', 'compilation job identity differs')
    # 保存済みin_progressを失敗完了として先に照合する。新しいrunはcheckpointが別に登録する。
    actions = [{k: run[k] for k in ('id', 'head_sha', 'status', 'conclusion')}]
    actions.append({k: compile_run[k] for k in ('id', 'head_sha', 'status', 'conclusion')})
    for item in r.api('actions/runs?head_sha=' + BASE + '&per_page=20')['workflow_runs']:
        actions.append({k: item[k] for k in ('id', 'head_sha', 'status', 'conclusion')})
    value = dict(schema_version=1, classification='CIRCUS_RENTAL_CONTROLLER_DECLARATION_REPAIRED_NATIVE_PENDING',
                 prior_runner_attempt=dict(run_id=COMPILE_RUN, job_id=COMPILE_JOB, original_conclusion='failure',
                                          native_processes=0, error_evidence=error_path,
                                          text_evidence=last['text_evidence']),
                 previous_run=RUN, previous_job=JOB, previous_original_conclusion='failure', previous_native_processes=0,
                 candidate=recipe['candidate'], actions_reconciled=actions,
                 inherited_recipe=identity(stable(previous['build'])),
                 restored_metadata_keys=sorted(set(recipe) - set(previous['build'])),
                 host_tests=r.tests([Path(TEST).name]), accepted_native_cases_replayed=0,
                 independent_old_arm_links_replayed=0, new_arm_links=0, rom_changes=0,
                 native_lifecycle_accepted=False, standard_save_fresh_continue=False,
                 genuine_30_wins_verified=False, physical_admission_accepted=False,
                 suppression_accepted=False, release_ready=False)
    record(value, 'PREPARED', '候補2b107e7eの受付/launch契約と再構築は成功。native0のcontroller include順序によるsc_events未宣言を前方定義で修復し、未実行continuationだけを開始。', NEXT)


def reconstruct():
    d, b = configure()
    d.c.f.reconstruct()
    import pr16_streak_native as n
    saved = json.loads((ROOT / PREVIOUS).read_bytes())['build']
    recipe = restore_contract(saved)
    raw = (n.INPUT / 'candidate.gba').read_bytes()
    parent = checked_patch(raw, saved['old'])
    candidate = checked_patch(parent, saved)
    for path, bound in recipe['source_bindings'].items():
        need(identity((ROOT / path).read_bytes()) == bound, 'saved source changed: ' + path)
    recipe['source_bindings'].update({p: identity((ROOT / p).read_bytes()) for p in FILES})
    OUT.mkdir(parents=True, exist_ok=True)
    for folder in (OUT, n.INPUT):
        (folder / 'candidate.gba').write_bytes(candidate)
        (folder / ('build.json' if folder == OUT else 'report.json')).write_bytes(stable(recipe))
    (OUT / 'reconstruction.json').write_bytes(stable(dict(candidate=identity(candidate),
        inherited_build_run=RUN, inherited_independent_links=2, new_arm_links=0, old_arm_links_replayed=0,
        rom_changes=0, all_allocations_verified=True, whole_rom_rollback_matches_parent=True,
        restored_metadata_keys=sorted(set(recipe) - set(saved)))))


def native():
    configure()
    import pr16_streak_native as n
    previous_policy = n.policy
    n.policy = lambda wx, br: policy_with_counter(previous_policy(wx, br))
    inherited.native()
    result = json.loads((OUT / 'rental-drought-result.json').read_bytes())
    need(result['genuine_30_wins_verified'], 'genuine 30-win target remains open; preserve scoped result')


def finish():
    configure()
    inherited.finish()


if __name__ == '__main__':
    need(len(sys.argv) == 2, 'command required')
    action = sys.argv[1]
    if action == 'pipeline':
        configure()[1].pipeline()
    elif action == 'pack':
        configure()[0].c.f.pack()
    elif action in {'prepare', 'reconstruct', 'native', 'finish'}:
        globals()[action]()
    else:
        raise SystemExit('unknown command')
