"""Ring誤入口とevent宣言/native境界、受入済みBP保全の回帰検査。"""
from __future__ import annotations

import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_ring_owner as target
import pr16_p05_native_supply_evidence_map as mapper


class RingOwnerTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/target.PLAN).read_text())
        with (ROOT/target.BINDINGS).open(newline='') as stream:
            self.bindings = list(csv.DictReader(stream))
        self.event = target.one(self.plan['events'], 'event_key', target.EVENT)

    def test_authored_event_is_not_a_ring_reward(self):
        result = target.analyze_event(self.plan, self.bindings)
        self.assertEqual((result['map_group'], result['map_id']), (97, 80))
        self.assertEqual(result['declared_reward_key'], 'NONE')
        self.assertEqual(len(result['reachable_step_keys']), 6)
        self.assertEqual(result['reachable_give_reward_step_keys'], [])
        for key in ('ring_acquisition_accepted', 'candidate_bytes_checked', 'all_runtime_owners_excluded'):
            self.assertIs(result[key], False)

    def test_missing_or_duplicate_event_is_rejected(self):
        for duplicate in (False, True):
            plan = copy.deepcopy(self.plan)
            if duplicate:
                plan['events'].append(copy.deepcopy(self.event))
            else:
                plan['events'].remove(self.event)
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                target.analyze_event(plan, self.bindings)

    def test_dangling_or_duplicate_step_is_rejected(self):
        self.event['steps'][0]['next_step_key'] = 'MISSING'
        with self.assertRaises(ValueError):
            target.analyze_event(self.plan, self.bindings)
        self.event['steps'][0]['next_step_key'] = self.event['steps'][-1]['step_key']
        self.event['steps'].append(copy.deepcopy(self.event['steps'][0]))
        with self.assertRaises(ValueError):
            target.analyze_event(self.plan, self.bindings)

    def test_unknown_operation_does_not_become_no_giver_proof(self):
        self.event['steps'][1]['op'] = 'CALL_UNAUDITED_NATIVE'
        with self.assertRaises(ValueError):
            target.analyze_event(self.plan, self.bindings)

    def test_unreachable_reward_is_not_counted_as_acquisition(self):
        reward = self.plan['rewards'][0]['reward_key']
        self.event['steps'].append({'step_key': 'UNREACHABLE_GIFT', 'op': 'GIVE_REWARD',
            'arg_key': reward, 'next_step_key': 'NONE', 'alt_step_key': 'NONE'})
        result = target.analyze_event(self.plan, self.bindings)
        self.assertEqual(result['reachable_give_reward_step_keys'], [])
        self.assertNotIn('UNREACHABLE_GIFT', result['reachable_step_keys'])

    def test_reachable_generic_reward_is_still_not_native_ring_acceptance(self):
        self.event['steps'][1]['op'] = 'GIVE_REWARD'
        self.event['steps'][1]['arg_key'] = self.plan['rewards'][0]['reward_key']
        result = target.analyze_event(self.plan, self.bindings)
        self.assertEqual(len(result['reachable_give_reward_step_keys']), 1)
        self.assertIs(result['ring_acquisition_accepted'], False)
        self.assertIs(result['candidate_bytes_checked'], False)

    def test_missing_reward_owner_is_rejected(self):
        self.event['steps'][1]['op'] = 'GIVE_REWARD'
        self.event['steps'][1]['arg_key'] = 'UNBOUND_REWARD'
        with self.assertRaises(ValueError):
            target.analyze_event(self.plan, self.bindings)

    def test_binding_map_trigger_and_owner_must_match(self):
        for key, bad in (('map_key', 'OTHER_MAP'), ('trigger_type', 'OBJECT'),
                         ('event_keys', 'OTHER_EVENT'), ('status', 'FAIL'), ('script_owner', 'FIXTURE')):
            bindings = copy.deepcopy(self.bindings)
            row = target.one(bindings, 'placement_key', self.event['placement_key'])
            row[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                target.analyze_event(self.plan, bindings)

    def test_unterminated_cycle_is_rejected(self):
        first = self.event['steps'][0]
        first['next_step_key'] = first['alt_step_key'] = first['step_key']
        with self.assertRaises(ValueError):
            target.analyze_event(self.plan, self.bindings)

    def test_textual_nonfixture_diagnostic_does_not_become_ring_entry(self):
        report = mapper.build_map()
        ring = report['bindings'][target.GAP]
        self.assertGreater(ring['nonfixture_candidate_count'], 0)
        self.assertIsNone(ring['preferred_entry_candidate'])
        self.assertIs(ring['runtime_owner_verified'], False)
        self.assertIn('未解決', mapper.render_doc(report))

    def test_generic_projection_cannot_reopen_bp_or_drop_other_gaps(self):
        original = json.loads((ROOT/mapper.REMAINING).read_text())
        value = mapper.project_remaining_work(copy.deepcopy(original), mapper.build_map())
        before = target.one(original['remaining_conditions'], 'id', 'NATURAL_CAPTURE_GEAR')
        after = target.one(value['remaining_conditions'], 'id', 'NATURAL_CAPTURE_GEAR')
        self.assertEqual(before['remaining_supply_gap_ids'], after['remaining_supply_gap_ids'])
        self.assertNotIn('P05_NATIVE_BP_EARNING_PHYSICAL', after['remaining_supply_gap_ids'])
        self.assertEqual(before['status'], after['status'])
        for key in ('p05_native_bp_control_checkpoint', 'next_integration_candidate'):
            self.assertEqual(value[key], original[key])
        before_other = [r for r in original['remaining_conditions'] if r['id'] != 'NATURAL_CAPTURE_GEAR']
        after_other = [r for r in value['remaining_conditions'] if r['id'] != 'NATURAL_CAPTURE_GEAR']
        self.assertEqual(before_other, after_other)

    def test_ring_only_projection_is_idempotent_and_does_not_touch_policy(self):
        original = json.loads((ROOT/mapper.REMAINING).read_text())
        report = {'preferred_entry_candidate': None, 'ring_acquisition_accepted': False}
        value = target.project_ring_only(original, report)
        self.assertEqual(value, target.project_ring_only(value, report))
        expected = copy.deepcopy(original)
        row = target.one(expected['remaining_conditions'], 'id', 'NATURAL_CAPTURE_GEAR')
        row['selected_supply_entrypoints'][target.GAP] = None
        row['ring_owner_resolution'] = target.REPORT
        self.assertEqual(value, expected)
        self.assertEqual(original, json.loads((ROOT/mapper.REMAINING).read_text()))

    def test_closed_ring_is_not_reopened_and_false_acceptance_is_rejected(self):
        original = json.loads((ROOT/mapper.REMAINING).read_text())
        row = target.one(original['remaining_conditions'], 'id', 'NATURAL_CAPTURE_GEAR')
        row['remaining_supply_gap_ids'].remove(target.GAP)
        with self.assertRaises(ValueError):
            target.project_ring_only(original, {'preferred_entry_candidate': None, 'ring_acquisition_accepted': False})
        original = json.loads((ROOT/mapper.REMAINING).read_text())
        with self.assertRaises(ValueError):
            target.project_ring_only(original, {'preferred_entry_candidate': None, 'ring_acquisition_accepted': True})

    def test_live_gap_validation_fails_without_partial_mutation(self):
        original = json.loads((ROOT/mapper.REMAINING).read_text())
        row = target.one(original['remaining_conditions'], 'id', 'NATURAL_CAPTURE_GEAR')
        row['remaining_supply_gap_ids'].append('UNKNOWN_GAP')
        unchanged = copy.deepcopy(original)
        with self.assertRaises(ValueError):
            mapper.project_remaining_work(original, mapper.build_map())
        self.assertEqual(original, unchanged)

    def test_new_check_is_read_only_and_binds_source_bytes(self):
        names = (target.REPORT, target.resume.STATE, target.resume.DOC, target.resume.BACKLOG)
        before = {name: (ROOT/name).read_bytes() for name in names}
        target.check()
        self.assertEqual(before, {name: (ROOT/name).read_bytes() for name in names})
        with mock.patch.object(target, 'identity', return_value={'size': 0, 'sha256': '0'*64}):
            with self.assertRaises(ValueError):
                target.check()


def focused():
    """既存pytest形式9件も収集し、外部依存なしで対象48件を実行する。"""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RingOwnerTests)
    suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_pr16_resume.py'))
    spec = importlib.util.spec_from_file_location('legacy_map_tests', ROOT/'tests/test_pr16_p05_native_supply_evidence_map.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    functions = [value for key, value in vars(module).items() if key.startswith('test_') and callable(value)]
    if len(functions) != 9:
        raise ValueError('旧mapper testsの件数が変更された')
    suite.addTests(unittest.FunctionTestCase(function) for function in functions)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    out = ROOT/'.local/pr16-ring-owner'
    out.mkdir(parents=True, exist_ok=True)
    (out/'tests.json').write_bytes(target.stable({'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
        'successful': result.wasSuccessful() and not result.skipped}))
    return result.wasSuccessful() and not result.skipped


if __name__ == '__main__':
    if '--focused' in sys.argv:
        raise SystemExit(0 if focused() else 1)
    unittest.main()
