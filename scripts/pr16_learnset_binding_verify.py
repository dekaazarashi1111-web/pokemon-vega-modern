#!/usr/bin/env python3
"""後継artifactを再利用し新adapter境界だけ検証・記録する。原本生成/nativeは呼ばない。"""
from __future__ import annotations
from collections import Counter
import csv
import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_binding as b
from pr16_resume import STATE, DOC, render

START = 'ec13a632dec95e8fd512618d9f1d1dbca604e7de'
TASK = 'USER-20260921-LEARNSET-BASELINE-RESET'
CHECKPOINT = s.BASE + 'pr16_learnset_binding_checkpoint.json'
EVIDENCE = s.BASE + 'pr16_learnset_binding_evidence'
GUIDE = 'docs/PR16_LEARNSET_BINDING_JA.md'
WORK = ROOT / '.local/pr16-learnset-binding'
FILES = ('unselected.jsonl', 'hatch_decisions.csv', 'summary.json', 'source-actions.json', 'unit.txt')
CODE = ('tools/pr16_learnset_binding.py', 'tests/test_pr16_learnset_binding.py',
        'scripts/pr16_learnset_binding_verify.py', '.github/workflows/pr16-learnset-binding.yml')
OWNED = {CHECKPOINT, GUIDE, STATE, DOC, 'design/run_log.md', 'design/version_log.md'} | {EVIDENCE + '/' + p for p in FILES}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def restore():
    from pr16_wiki_reconcile import fetch
    cp = s.read_json(ROOT / (s.BASE + 'pr16_learnset_successor_checkpoint.json'))
    b.require(cp['status'] == 'ACCEPTED_SUCCESSOR_TABLES_ONLY_RUNTIME_PENDING', '後継表受入不一致')
    receipt_path = ROOT / (s.BASE + 'pr16_learnset_successor_evidence/receipt.json')
    s.bound(receipt_path, cp['proof_bindings']['receipt.json'])
    receipt = s.read_json(receipt_path)
    b.require(cp['files'] == receipt['files'], 'checkpoint/receipt不一致')
    for name, ident in receipt['inputs'].items():
        if '/' in name:
            s.bound(ROOT / name, ident)
    run = fetch(f"actions/runs/{cp['run_id']}")
    jobs = fetch(f"actions/runs/{cp['run_id']}/jobs?per_page=100")
    b.require(run['status'] == 'completed' and run['conclusion'] == 'success'
              and run['head_sha'] == cp['source_head'], '受入run未完/HEAD不一致')
    b.require(jobs['total_count'] == len(jobs['jobs']) == 1 and all(j['conclusion'] == 'success'
              and j['head_sha'] == cp['source_head'] and all(t['conclusion'] == 'success' for t in j['steps'])
              for j in jobs['jobs']), '受入job/step未成功')
    artifact = fetch(f"actions/artifacts/{cp['table_artifact']['id']}")
    for key in ('id', 'name', 'digest', 'size_in_bytes', 'workflow_run'):
        b.require(artifact[key] == cp['table_artifact'][key], '表artifact binding不一致: ' + key)
    b.require(artifact['expired'] is False, '受入artifact期限切れ・自動再生成禁止')
    tables = b.restore_archive(ROOT, WORK / 'tables', fetch(f"actions/artifacts/{artifact['id']}/zip", binary=True), artifact, receipt)
    actions = {'reused_run_id': run['id'], 'source_head': run['head_sha'],
               'conclusion': run['conclusion'], 'job_ids': [j['id'] for j in jobs['jobs']],
               'artifact': cp['table_artifact'], 'source_generation_reruns': 0, 'accepted_tests_rerun': 0}
    return tables, receipt, actions


def inventory(tables):
    cp = s.read_json(ROOT / (s.BASE + 'pr16_learnset_successor_checkpoint.json'))
    review_path = ROOT / (s.BASE + 'pr16_learnset_successor_evidence/compact-review.json')
    s.bound(review_path, cp['proof_bindings']['compact-review.json'])
    review = s.read_json(review_path)
    coverage = list(s.rows(tables / 'species_coverage.jsonl'))
    missing = [r for r in coverage if r['selection'] in ('SOURCE_NOT_SELECTED', 'RUNTIME_EXTENSION_NOT_SELECTED')]
    b.require(missing == review['unselected_species'] and len(missing) == 191, '未選択集合不一致')
    manifest = s.manifest(ROOT / 'manifests/species_ids.csv', 'species_key')
    result = [dict(row, manifest=manifest.get(row['species_id'])) for row in missing]
    links = list(s.rows(tables / 'vega_hatch_links.jsonl'))
    plan = b.hatch_plan(links)
    gaps = [r for r in plan if not r['hatch_selected_direct_egg_membership']]
    expected = [{k: r[k] for k in ('row_key', 'receiver_species_id', 'hatch_species_id', 'move_id')} for r in gaps]
    b.require(expected == review['hatch_baseline_membership_gaps'] and len(gaps) == 531 and len(plan) == 2394,
              '原本裁定/孵化差分全数不一致')
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=list(plan[0]))
    writer.writeheader(); writer.writerows(plan)
    summary = {'unselected_species': len(result), 'unselected_states': dict(Counter(r['selection'] for r in result)),
               'hatch_rows': len(plan), 'hatch_dispositions': dict(Counter(r['disposition'] for r in plan)),
               'direct_grants': 0, 'shared_grants': 0, 'owner_overlay_grants': 0,
               'existing_move_carry_policy_changed': False, 'acquisition_impossible_claimed': False,
               'runtime_applied': False, 'rom_changes': 0, 'new_native_runs': 0,
               'issue19_complete': False, 'release_ready': False}
    return {'unselected.jsonl': b''.join(b.encode(r) for r in result),
            'hatch_decisions.csv': out.getvalue().encode(), 'summary.json': b.encode(summary)}, summary


def verify():
    from pr16_wiki_reconcile import fetch
    WORK.mkdir(parents=True, exist_ok=False)
    head = git('rev-parse', 'HEAD').decode().strip()
    b.require(head == os.environ['GITHUB_SHA'], 'HEAD不一致')
    pr = fetch('pulls/16')
    b.require(pr['state'] == 'open' and pr['draft'] is True and not pr['merged']
              and pr['head']['ref'] == 'codex/modernization-followup-20260908'
              and pr['head']['sha'] == head, 'PR状態/remote競合')
    unit = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests',
                           '-p', 'test_pr16_learnset_binding.py', '-v'], cwd=ROOT, capture_output=True, text=True)
    log = unit.stdout + unit.stderr
    (WORK / 'unit.txt').write_text(log)
    b.require(unit.returncode == 0 and '\nOK\n' in log and 'Ran 24 tests' in log, '新24試験未成功')
    tables, receipt, actions = restore()
    watched = [ROOT / name for name in receipt['inputs'] if '/' in name] + list(tables.iterdir())
    before = {str(p): (s.identity(p), p.stat().st_mtime_ns) for p in watched}
    outputs, summary = inventory(tables)
    b.require(before == {str(p): (s.identity(p), p.stat().st_mtime_ns) for p in watched}, '原本byte/mtime変化')
    outputs['source-actions.json'] = b.encode(actions)
    outputs['unit.txt'] = log.encode()
    checkpoint = dict(summary, task=TASK, status='HATCH_DISPOSITIONS_VERIFIED_SPECIES_BINDING_PENDING',
                      source_head=head, run_id=int(os.environ['GITHUB_RUN_ID']), actions_completion_confirmed=False,
                      focused_tests=24, accepted_tests_rerun=0, source_generation_reruns=0,
                      input_tables_reused=True, readonly_byte_mtime_unchanged=True,
                      code={name:s.identity(ROOT/name) for name in CODE},
                      outputs={name:b.identity(raw) for name,raw in outputs.items()})
    location = ROOT / EVIDENCE
    b.require(not location.exists() and not (ROOT/CHECKPOINT).exists(), '同工程を重複記録しない')
    location.mkdir()
    for name, raw in outputs.items():
        raw.decode('utf-8'); b.require(b'\0' not in raw, 'binary記録禁止')
        (location/name).write_bytes(raw)
    (ROOT/CHECKPOINT).write_bytes(b.encode(checkpoint))
    state = s.read_json(ROOT/STATE)
    b.require(not state['pr_merged'] and not state['release_ready'] and not state['active_baseline_changed'], '受入境界違反')
    state['learnset_binding'] = checkpoint
    goal = 'Issue19: 新規binding台帳の未選択191枠をSpecies/Formの正本へ明示対応させ、検証済み孵化531差分の非付与処理とともにbinary consumerへ接続する。後継ROM・別Wiki・影響nativeはその後。'
    state['next_action'] = dict(state['next_action'], id='LEARNSET_EXPLICIT_SPECIES_BINDING', goal_ja=goal,
                               read_paths=[GUIDE, CHECKPOINT, EVIDENCE+'/unselected.jsonl', EVIDENCE+'/summary.json',
                                           'tools/pr16_learnset_binding.py', 'config/move_port.json'])
    state['bp']['next_step'] = goal
    state['bp']['current_stop'] = '後継受入artifactをhash固定で再利用。非直接egg2394行のうち531差分を履歴参照・新規付与なしとして実装/全行照合し、新24境界試験PASS。191未選択枠はmanifest付き台帳へ分離。Species/Form裁定とbinary接続は未完。'
    state['do_not_repeat'].append('learnset binding: 受入9consumer表はartifact10653200020を再利用。531孵化差分は非付与として全行照合済み。旧原本/39受入試験/nativeを再実行せず、未選択191枠の明示bindingから続行。')
    (ROOT/STATE).write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    (ROOT/DOC).write_text(render(state))
    (ROOT/GUIDE).write_text('# Issue19 後継consumerの明示binding\n\n'
        '正本は `'+CHECKPOINT+'`。原本・旧候補・Wikiは不変。\n\n'
        '受入後継artifactを外側digest/全member hash/size/receiptで照合し、安全な.localへ復元する。'
        '未知member、symlink、既存出力、path traversalは拒否。公式/Vega原本の再生成は呼ばない。\n\n'
        '孵化2394行のうち新孵化先direct eggにない531行は `HISTORICAL_HATCH_REFERENCE_NO_NEW_GRANT`。'
        '進化時付与、direct/shared egg、owner overlayへ追加しない。現在保持している技の持越し規則は変更しない。'
        'この分類は全習得方法での取得不能を意味しない。全原本行keyとSHAをCSVへ保存する。\n\n'
        '未選択191枠はunselected.jsonlにmanifestと原本targetを保存した。旧表fallback/一括削除は未実装であり禁止。'
        '次はこの対応を解決し、binary adapter、後継ROM、別Wiki、影響nativeへ進む。\n\n'
        '24新試験と実データ全行照合まで。Actionsの最後のpush/artifact完了はrun APIで別途照合する。'
        'Issue19全体、release、merge、active baseline切替は未完/未実施。\n')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 後継binding入力と孵化非付与処理\n- Version: learnset-binding-v1\n- Status: DONE（入力復元/孵化処理のみ。Species binding/binary未完）\n- Summary: 受入表artifact再利用、2394行を照合し531差分の非付与を実装。191枠はmanifest付き台帳化。\n- Files changed: binding実装/新24試験/限定Actions、checkpoint/証拠/guide、固定MD/JSON、両ログ。\n- Verify: 新24試験PASS、artifact外側/全member hash、原本byte/mtime不変、孵化全行/531差分一致。原本生成/受入試験/native再実行0。run={checkpoint["run_id"]} input={head}。\n- Commit: 本記録を含む同branch非force commit。最終push完了はrun APIで別照合。\n- Network: GitHub connector/Actions、受入artifact10653200020再利用。Wiki再採取なし。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a') as stream: stream.write(entry)
    print(json.dumps(summary, ensure_ascii=False))


def guard():
    import guard_private_files as private
    subprocess.run(['git','merge-base','--is-ancestor',START,'HEAD'], cwd=ROOT, check=True)
    paths = {p for p in git('diff','--cached','--name-only','-z',START).decode().split('\0') if p}
    b.require(paths == OWNED | set(CODE), '変更path集合不一致: '+str(paths ^ (OWNED | set(CODE))))
    for name in sorted(paths):
        raw = git('show', ':'+name); raw.decode('utf-8'); b.require(b'\0' not in raw, 'binary stage禁止')
        previous = subprocess.run(['git','show',START+':'+name], cwd=ROOT, capture_output=True).stdout
        def bad(data):
            lines = data.decode('utf-8', errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(data))
        b.require(not bad(raw)-bad(previous), '新規private path違反: '+name)
        if name.startswith('design/'):
            b.require(raw.startswith(previous), 'append-only違反')
    subprocess.run(['git','diff','--exit-code',START,'--','tasks/task_graph.json','design/tasks_next.md','state/task_status.json'],cwd=ROOT,check=True)
    print(json.dumps({'status':'PASS_CHANGED_FINAL_INDEX','paths':len(paths),'new_violations':0,'full_historical_guard_pass_claimed':False}))


if __name__ == '__main__':
    if sys.argv[1:] == ['guard']: guard()
    elif not sys.argv[1:]: verify()
    else: raise SystemExit('usage: pr16_learnset_binding_verify.py [guard]')
