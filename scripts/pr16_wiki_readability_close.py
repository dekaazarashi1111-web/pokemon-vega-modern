#!/usr/bin/env python3
"""成功版を再走せず、旧方針の混在記録と完了Actionsを最終照合する。"""
from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
import unittest
import pr16_wiki_readability as w
import pr16_wiki_readability_publish as p

BASE = '7ac96b2103ed1ef002a0d1795ea7c62012aeda9a'
TASK = 'USER-20261011-WIKI-READABILITY-CLOSE'
CLOSE = 'content/modernization/pr16_wiki_readability_closure.json'
CODE = {'scripts/pr16_wiki_readability_close.py', '.github/workflows/pr16-wiki-readability-close.yml'}
HISTORY_KEYS = ('blocked_method_ja', 'local_verification', 'mode', 'owner_instruction_at', 'source_head', 'task', 'project_resume_check_executed')


def reconcile(original, source, completed):
    state = copy.deepcopy(original)
    wk = state['owner_execution_plan']['wiki_readability']
    w.need(wk['ready'] and wk['presented_to_owner'] and wk['completion_gates'] and all(wk['completion_gates'].values()), '未完Wikiを閉じない')
    w.need(state['next_action']['id'] == 'SAVE_CAPACITY_BERRY_ORIGIN_ACTUAL_OWNER_READER', '復帰先が変わった')
    rec = state['recording']
    w.need('historical_unscoped_recording' not in rec and 'closure_receipt_path' not in wk, '閉鎖照合済み・再走禁止')
    w.need(rec['wiki_readability_priority_update']['legacy_log_append']['status'] == 'DONE', '優先ログ追記未完')
    rec['historical_unscoped_recording'] = {'observed_at_commit': BASE, 'scope_ja': '旧方針/R0時代から混在していた値を原文のまま保存。現状の禁止・停止理由ではない。', 'values': {k: rec.pop(k) for k in HISTORY_KEYS if k in rec}}
    prior = rec['wiki_readability_priority_update']
    prior['status_before_log_reconciliation'] = prior['status']
    prior['status'] = 'ROUTING_RECORDED_LEGACY_LOG_APPEND_COMPLETED'
    prior['scope_ja'] = '方針変更時の検証履歴。wiki_fixed/generated=false等は当時の記録で、現在の完了判定はowner_execution_plan.wiki_readabilityとreceiptを読む。'
    rec['wiki_readability_receipt_execution'] = rec['wiki_readability_execution']
    rec['wiki_readability_execution'] = {'task': TASK, 'source_head': source, 'generated_again': False, 'accepted_test_reruns': 0, 'native_processes': 0, 'all_ci_green_claimed': False}
    rec.update(mode='READ_ONLY_RECEIPTS_AND_STATE_RECONCILIATION', source_head=source, task=TASK, owner_instruction_at='2026-10-11T01:44:48Z', status='R0_1_CLOSED_BERRY_OWNER_READER_NEXT', completed_wiki_actions=copy.deepcopy(completed))
    wk['closure_receipt_path'] = CLOSE
    state['authority_ja'] = 'このJSONが作業選択の正本。R0.1の全gateと実物提示は完了し、閲覧改善優先条件を充足。現在はnext_actionのBerry現owner/reader未完scopeへ戻る。旧R0のreadyだけで解除したのではない。旧方針・旧解析の記録は履歴として保持する。'
    for key in ('technical_lanes', 'owner_review', 'wiki'):
        w.need(state['owner_execution_plan'][key] == original['owner_execution_plan'][key], '受入/承認/技術停止点の変更')
    w.need(state['next_action'] == original['next_action'], 'next actionの意味変更')
    return state


def state_tests(original):
    class ClosureTests(unittest.TestCase):
        def test_history_is_preserved(self):
            result = reconcile(original, 'a'*40, [])
            self.assertEqual(result['recording']['historical_unscoped_recording']['values'], {k: original['recording'][k] for k in HISTORY_KEYS if k in original['recording']})
            self.assertNotIn('blocked_method_ja', result['recording'])
        def test_input_and_technical_frontier_unchanged(self):
            before = copy.deepcopy(original)
            result = reconcile(original, 'a'*40, [])
            self.assertEqual(original, before)
            self.assertEqual(result['next_action'], before['next_action'])
            self.assertEqual(result['owner_execution_plan']['technical_lanes'], before['owner_execution_plan']['technical_lanes'])
        def test_not_ready_rejected(self):
            for field in ('ready', 'presented_to_owner'):
                bad = copy.deepcopy(original); bad['owner_execution_plan']['wiki_readability'][field] = False
                with self.subTest(field=field), self.assertRaises(ValueError): reconcile(bad, 'a'*40, [])
        def test_incomplete_gate_rejected(self):
            bad = copy.deepcopy(original); gates = bad['owner_execution_plan']['wiki_readability']['completion_gates']; gates[next(iter(gates))] = False
            with self.assertRaises(ValueError): reconcile(bad, 'a'*40, [])
            bad['owner_execution_plan']['wiki_readability']['completion_gates'] = {}
            with self.assertRaises(ValueError): reconcile(bad, 'a'*40, [])
        def test_changed_next_rejected(self):
            bad = copy.deepcopy(original); bad['next_action']['id'] = 'OTHER'
            with self.assertRaises(ValueError): reconcile(bad, 'a'*40, [])
        def test_duplicate_rejected(self):
            closed = reconcile(original, 'a'*40, [])
            with self.assertRaises(ValueError): reconcile(closed, 'a'*40, [])
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ClosureTests))
    w.need(result.wasSuccessful() and not result.skipped, '新規状態照合試験失敗')
    return {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)}


def main():
    (p.WORK/'proof').mkdir(parents=True, exist_ok=True)
    raw = w.read(w.ROOT, p.STATE)
    original = json.loads(raw)
    if sys.argv[1:] == ['--self-test']:
        before = (raw, (w.ROOT/p.STATE).stat().st_mtime_ns)
        result = state_tests(original)
        w.need(before == (w.read(w.ROOT, p.STATE), (w.ROOT/p.STATE).stat().st_mtime_ns), '状態試験に副作用')
        (p.WORK/'proof/state-tests.json').write_bytes(w.encode(result))
        return
    w.need(not sys.argv[1:], '未知引数')
    source = os.environ['GITHUB_SHA']
    observed = p.preflight(source)
    p.git('merge-base', '--is-ancestor', BASE, source)
    receipt = json.loads(w.read(w.ROOT, p.RECEIPT))
    proof = json.loads(w.read(w.ROOT, p.PROOF))
    w.need(receipt['status'] == 'PASS_PUBLISHED_PRESENTED_R0_1', '提示受領の未完')
    p.git('diff', '--exit-code', receipt['presentation']['wiki_commit'], 'HEAD', '--', w.OUT)
    completed = []
    expected = [(proof['actions_run_id'], proof['source_head']), (original['recording']['wiki_readability_execution']['actions_run_id'], receipt['source_head'])]
    for run_id, head in expected:
        run = p.api('actions/runs/'+str(run_id))
        jobs = p.api('actions/runs/'+str(run_id)+'/jobs?per_page=100')
        w.need(run['head_sha'] == head and run['status'] == 'completed' and run['conclusion'] == 'success', '完了Actions identity')
        w.need(jobs['total_count'] == len(jobs['jobs']) > 0 and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in jobs['jobs']), '完了job集合')
        completed.append({'id': run_id, 'source_head': head, 'status': run['status'], 'conclusion': run['conclusion'], 'jobs': [{'id': j['id'], 'name': j['name'], 'conclusion': j['conclusion']} for j in jobs['jobs']]})
    state = reconcile(original, source, completed)
    state['recording']['wiki_readability_execution']['actions_run_id'] = int(os.environ['GITHUB_RUN_ID'])
    state['observed_head_checks'] = observed
    test_result = json.loads((p.WORK/'proof/state-tests.json').read_bytes())
    w.need(test_result == {'tests': 6, 'failures': 0, 'errors': 0, 'skipped': 0}, '状態試験の未完')
    graph = subprocess.run(['python3', '-B', 'scripts/validate_task_graph.py'], cwd=w.ROOT, check=True, capture_output=True)
    (p.WORK/'proof/task-graph.txt').write_bytes(graph.stdout)
    value = {'schema_version': 1, 'status': 'PASS_CLOSED_RECORDS_ALIGNED', 'source_head': source, 'base_receipt_commit': BASE, 'published_wiki_commit': receipt['presentation']['wiki_commit'], 'completed_actions': completed, 'new_state_tests': test_result, 'history_fields_preserved': list(HISTORY_KEYS), 'wiki_tree_unchanged': True, 'generated_again': False, 'accepted_test_reruns': 0, 'native_processes': 0, 'rom_reconstructions': 0, 'task_graph_passed': True, 'all_ci_green_claimed': False, 'next_action': state['next_action']['id']}
    extra = '\n## 完了Actionsと現在状態の照合\n\n生成run 38104885843 と提示受領run 38105312765 は、source HEADと全jobを照合して completed/success を確認。[最終照合記録](../'+CLOSE+')に保存。旧方針時の拒否理由/古い検証値は状態JSONのhistorical_unscoped_recordingへ原文保持し、追記済みログのpending表示を解消した。成功版・28試験・nativeは再走していない。新規6状態回帰とtask graphのみ実行。現在のnext_action・788/86・選定残7・安全容量0・未承認状態は不変。\n'
    p.write(p.GUIDE, w.read(w.ROOT, p.GUIDE)+extra.encode())
    p.bind_entry(state)
    p.append(TASK, '旧方針/R0から混在した未着手・拒否・ログpending表示を履歴へ分離し、完了Actions2件と現在のBerry復帰状態を整合。自己SHAだけの追記ではない。', '新規状態回帰6件/task graph、完了runと全jobのidentity、Wiki Git tree不変、技術停止点/承認/元履歴の意味不変。成功済み生成/28試験/native再走0。')
    p.write(p.STATE, w.encode(state)); p.write(CLOSE, w.encode(value))
    allowed = CODE | p.LOGS | {p.STATE, p.GUIDE, CLOSE}
    p.final_index(BASE, allowed, state, value, CLOSE)
    p.publish(source, TASK)
    for name, target in ((CLOSE, 'closure.json'), (p.STATE, 'state.json'), (p.GUIDE, 'guide.md')):
        (p.WORK/'proof'/target).write_bytes(w.read(w.ROOT, name))


if __name__ == '__main__':
    main()
