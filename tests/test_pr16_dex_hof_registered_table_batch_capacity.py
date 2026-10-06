"""新registered-table境界の766親保存容量と現owner束縛だけを検査する。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import pr16_dex_hof_registered_table_batch_chain as chain
import pr16_dex_hof_registered_table_batch_capacity as m
from test_pr16_dex_hof_registered_table_batch_chain import recorded_parents, registered_module_regions


class GuardCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.parents = recorded_parents()
        cls.parent = cls.parents['parent_audit']
        cls.inputs = m.read_inputs()
        cls.delta = chain.build(cls.parent, [], {'registered_table_guard_only': True})
        cls.full = chain.materialize(cls.parent, cls.delta)
        cls.result = m.current_report(cls.full, **cls.parents)

    def evaluate(self, full=None, **overrides):
        parents = dict(self.parents, **overrides)
        return m.current_report(self.full if full is None else full, **parents)

    def test_guard_keeps766_parent108_unknown_and_whole_donor_protection(self):
        plan = self.result['successor_plan']
        self.assertEqual((plan['parent_unknown_count'], plan['current_unknown_count'], plan['newly_classified_count']), (108, 108, 0))
        self.assertEqual(plan['protected'], [{'address': self.result['donor']['address'], 'size': 15118}])
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertEqual(plan['largest_aligned_gap_bytes'], 0)
        self.assertIs(plan['lease_eligible'], False)
        self.assertIs(plan['lease_authorized'], False)
        self.assertIs(plan['rom_mutation_performed'], False)
        self.assertEqual(self.full['hits'], self.parent['hits'])

    def test_latest_actual115_owner_and52_save_owner_bound_separately(self):
        binding = self.result['current_owner_binding']
        path = 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
        raw = (ROOT / path).read_bytes()
        placement = json.loads(raw)
        self.assertEqual(binding['path'], path)
        self.assertEqual(binding['checkpoint_identity'], chain.identity(raw))
        self.assertEqual(binding['actual_owner_rows_identity'], chain.identity(chain.canonical(placement['placement']['owner_byte_audit'])))
        self.assertEqual((binding['actual_owner_count'], binding['save_owner_count'], binding['save_free_bytes']), (115, 52, 804))
        self.assertIs(binding['donor_lease_or_owner_transfer_performed'], False)
        self.assertEqual(self.result['controller']['total_allocated_bytes'], 6528)
        self.assertEqual(self.result['other_known_capacity']['sum_upper_bound_bytes'], 1315)

    def test_entire_saved766_capacity_plan_is_preserved_with_independent_identity(self):
        _, cp, recorded = self.inputs
        self.assertEqual(cp['capacity_identity'], m.INPUTS[m.PARENT_PLAN])
        self.assertEqual(self.result['immediate_parent_recorded_successor_plan'], recorded['successor_plan'])
        self.assertEqual(self.result['fixed766_registered_callback_batch_successor_plan'], recorded['successor_plan'])
        self.assertEqual(self.result['immediate_parent_capacity_identity'], m.INPUTS[m.PARENT_PLAN])
        self.assertEqual(self.result['immediate_parent_checkpoint'], chain.PARENT_CHECKPOINT)
        self.assertEqual(self.result['successor_plan']['parent_frontier_identity'], m.INPUTS[m.FRONTIER])
        self.assertEqual(self.result['current_owner_binding'], recorded['current_owner_binding'])

    def test_runtime_boundary_heap13352_stock53300_release0804b85c_unchanged(self):
        boundary = self.result['registered_table_batch_runtime_boundary']
        self.assertEqual((boundary['controller_measured_bytes'], boundary['heap_scratch_bytes'],
                          boundary['stock_save_backup_bytes'], boundary['release_before_stock_save_entry']),
                         (6528, 13352, 53300, 0x0804B85C))
        for key in ('controller_runtime_wired', 'heap_lifetime_proven', 'stock_save_boundary_crossing_allowed',
                    'all_save_entry_heap_ready_proven', 'synchronous_nonreentrant_use_proven',
                    'indirect_reference_completeness_proven', 'target_retirement_proven',
                    'explicit_owner_transfer_proven', 'natural_play_universal_reachability_claimed'):
            self.assertIs(boundary[key], False)
        self.assertEqual(boundary['donor_safe_bytes'], 0)
        self.assertEqual(boundary, m.prior.runtime_boundary())

    def test_all49_historical_capacity_file_identities_match_without_remeasurement(self):
        bindings = m.all_input_bindings()
        self.assertEqual(len(bindings), 49)
        self.assertEqual(list(bindings), sorted(bindings))
        for path, expected in bindings.items():
            with self.subTest(path=path):
                self.assertEqual(chain.identity((ROOT / path).read_bytes()), expected)
        for path, expected in m.INPUTS.items():
            self.assertEqual(bindings[path], expected)
        bindings[m.FRONTIER]['size'] += 1
        self.assertNotEqual(bindings[m.FRONTIER], m.INPUTS[m.FRONTIER])

    def test_duplicate_or_cyclic_capacity_lineage_fails_closed(self):
        with patch.dict(m.prior.INPUTS, {m.FRONTIER: {'size': 1, 'sha256': 'bad'}}):
            with self.assertRaises(ValueError):
                m.all_input_bindings()
        with patch.object(m.prior, 'prior', m.prior):
            with self.assertRaises(ValueError):
                m.all_input_bindings()

    def test_all_immediate_capacity_bytes_and_symlinks_are_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in m.INPUTS:
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes((ROOT / path).read_bytes())
            for path in m.INPUTS:
                file = root / path
                raw = file.read_bytes()
                file.write_bytes(raw + b'\n')
                with self.subTest(path=path), self.assertRaises(ValueError):
                    m.read_inputs(root)
                file.write_bytes(raw)
            file = root / m.PARENT_PLAN
            file.unlink()
            file.symlink_to(ROOT / m.PARENT_PLAN)
            with self.assertRaises(ValueError):
                m.read_inputs(root)

    def test_old_root_validator_receives_only_exact766_parent_not_new_guard(self):
        original = m.prior.current_report
        with patch.object(m.prior, 'current_report', wraps=original) as old:
            result = self.evaluate()
        self.assertEqual(old.call_args.args[0], self.parent)
        self.assertEqual(old.call_args.kwargs['parent_audit'], self.parents['registered_callback_batch_parent'])
        self.assertNotIn(chain.NAMESPACE, old.call_args.args[0])
        self.assertEqual(result['successor_plan']['current_unknown_count'], 108)

    def test_every_field_of_prior_capacity_report_is_bound_before_successor_planning(self):
        _, _, recorded = self.inputs
        for mutate in (lambda report: report.update(unrecorded_permission=True),
                       lambda report: report['fixed761_registered_text_batch_successor_plan'].update(owner_count=114),
                       lambda report: report['current_owner_binding'].update(save_free_bytes=805)):
            altered = copy.deepcopy(recorded)
            mutate(altered)
            with self.subTest(mutate=mutate), patch.object(m.prior, 'current_report', return_value=altered):
                with self.assertRaisesRegex(ValueError, 'entire independently recorded766 capacity report'):
                    self.evaluate()

    def test_altered_accepted_unknown_or_proof_family_is_not_capacity_input(self):
        for accepted in (False, True):
            full = copy.deepcopy(self.full)
            next(h for h in full['hits'] if h['accepted'] is accepted)['sha256'] = 'changed'
            with self.subTest(accepted=accepted), self.assertRaises(ValueError):
                self.evaluate(full=full)
        full = copy.deepcopy(self.full)
        full['root_batch_reference_chain']['proof'] = {}
        with self.assertRaises(ValueError):
            self.evaluate(full=full)

    def test_historical743_or741_parent_cannot_replace_current766(self):
        for name in ('root_batch_parent', 'help_batch_parent'):
            with self.subTest(parent=name), self.assertRaises(ValueError):
                self.evaluate(parent_audit=self.parents[name])
        with self.assertRaises(ValueError):
            self.evaluate(root_batch_parent=self.parents['help_batch_parent'])

    def test_owner_rows_save_count_or_free_bytes_cannot_be_substituted(self):
        placement = json.loads((ROOT / 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json').read_bytes())
        for mutate in (lambda p: p['placement']['owner_byte_audit'].pop(),
                       lambda p: p['link']['sections'].pop(),
                       lambda p: p['link'].update(free_bytes=805),
                       lambda p: p['placement']['owner_byte_audit'][0].update(after_sha256='old nominal hash')):
            changed = copy.deepcopy(placement)
            mutate(changed)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.current_owner_binding(changed)

    def test_point_projection_and_zero_unknown_do_not_authorize_safety(self):
        self.assertIs(self.result['successor_point_only_projection']['safe_to_lease'], False)
        self.assertGreater(self.result['successor_point_only_projection']['largest_gap_bytes'], 0)
        full = copy.deepcopy(self.full)
        full['classified'], full['unclassified'] = 874, 0
        with self.assertRaises(ValueError):
            self.evaluate(full=full)
        self.assertEqual(self.result['successor_plan']['total_unprotected_bytes'], 0)


    def synthetic_classification(self, selected):
        """容量式の受入だけを合成型で検査する。実consumer測定とは別。"""
        kind, module_name = 'synthetic_registered_table_capacity_only', 'synthetic_registered_table_capacity_validator'
        module = SimpleNamespace(KIND=kind, witness_geometry=lambda e: (e['address'], e['size']))
        regions = [chain.d.TypedRegion(row['address'], row['address'] + row['size'], kind,
            {'address': row['address'], 'size': row['size'], 'synthetic_protocol_only': True}) for row in selected]
        with patch.dict(sys.modules, {module_name: module}), patch.dict(chain.NEW_KIND_MODULES, {kind: module_name}, clear=True):
            delta = chain.build(self.parent, regions, {'new_data': len(selected), 'synthetic_protocol_only': True})
            full = chain.materialize(self.parent, delta)
            result = self.evaluate(full=full)
        return delta, full, result

    def test_synthetic_classification_of_five_candidates_does_not_retire_any_current_owner(self):
        addresses = {0x090405A9,0x0917E399,0x0918BDD3,0x0918FBA2,0x0918FFDE}
        selected = [row for row in self.parent['hits'] if row['address'] in addresses]
        self.assertEqual(len(selected), 5)
        self.assertTrue(all(row['accepted'] is False for row in selected))
        delta, full, result = self.synthetic_classification(selected)
        self.assertEqual((full['classified'], full['unclassified']), (771, 103))
        self.assertEqual((len(delta['changes']), len(delta['witnesses'])), (5, 5))
        self.assertEqual(sum(len(full[name]['changes']) for name in (*chain.INHERITED_NAMES, chain.NAMESPACE)), 152)
        self.assertEqual(sum(len(full[name]['witnesses']) for name in (*chain.INHERITED_NAMES, chain.NAMESPACE)), 142)
        self.assertEqual(result['current_owner_binding'], self.result['current_owner_binding'])
        plan = result['successor_plan']
        self.assertEqual((plan['parent_unknown_count'], plan['current_unknown_count'], plan['newly_classified_count']), (108, 103, 5))
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertEqual(plan['owner_count'], 115)
        self.assertIs(plan['lease_authorized'], False)
        for before, after in zip(self.parent['hits'], full['hits']):
            if before['address'] not in addresses:
                self.assertEqual(before, after)

    def test_dedicated_five_hit_protocol_still_has_zero_safe_bytes_and_exact_owner_binding(self):
        delta = chain.build(self.parent, registered_module_regions(), {
            'dedicated_evidence_protocol_only': True, 'new_code': 0, 'new_data': 5})
        full = chain.materialize(self.parent, delta)
        result = self.evaluate(full=full)
        plan = result['successor_plan']
        self.assertEqual((full['classified'], full['unclassified']), (771, 103))
        self.assertEqual((plan['parent_unknown_count'], plan['current_unknown_count'],
                          plan['newly_classified_count']), (108, 103, 5))
        self.assertEqual(plan['protected'], [{'address': result['donor']['address'], 'size': 15118}])
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertIs(plan['lease_eligible'], False)
        self.assertIs(plan['lease_authorized'], False)
        self.assertEqual(result['current_owner_binding'], self.result['current_owner_binding'])
        self.assertEqual(result['registered_table_batch_runtime_boundary'], m.runtime_boundary())

    def test_current_frontier_is_additive_for_synthetic_subsets_of_five_candidates(self):
        addresses = {0x090405A9,0x0917E399,0x0918BDD3,0x0918FBA2,0x0918FFDE}
        rows = [row for row in self.parent['hits'] if row['address'] in addresses]
        for count in (1, 2):
            with self.subTest(classified=count):
                delta, full, result = self.synthetic_classification(rows[:count])
                self.assertEqual((full['classified'], full['unclassified']), (766 + count, 108 - count))
                self.assertEqual((len(delta['changes']), len(delta['witnesses'])), (count, count))
                self.assertEqual(result['successor_plan']['newly_classified_count'], count)
                self.assertEqual(result['successor_plan']['total_unprotected_bytes'], 0)
                self.assertEqual(result['current_owner_binding'], self.result['current_owner_binding'])
                for name in chain.INHERITED_NAMES:
                    self.assertEqual(full[name], self.parent[name])

    def test_saved_healing_veil_runtime_and_earlier_projection_remain_exact(self):
        _, _, recorded = self.inputs
        for key in ('healing_veil_batch_runtime_boundary',
                    'fixed753_script_producer_batch_successor_plan',
                    'fixed753_script_producer_batch_point_only_projection'):
            self.assertEqual(self.result[key], recorded[key])
        self.assertEqual(self.result['fixed766_registered_callback_batch_point_only_projection'],
                         recorded['successor_point_only_projection'])

    def test_even_zero_unknown_cannot_promote_indirect_completeness_or_retirement(self):
        _, _, result = self.synthetic_classification([row for row in self.parent['hits'] if not row['accepted']])
        plan = result['successor_plan']
        self.assertEqual((plan['current_unknown_count'], plan['newly_classified_count']), (0, 108))
        self.assertEqual(plan['protected'], [{'address': result['donor']['address'], 'size': 15118}])
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertIs(plan['lease_eligible'], False)
        self.assertIs(plan['lease_authorized'], False)
        self.assertEqual(plan['unresolved_obligations'], [
            'indirect_reference_completeness_unproven',
            'partial_retirement_and_explicit_owner_transfer_unproven'])
        self.assertEqual(result['successor_point_only_projection']['largest_gap_bytes'], 15118)
        self.assertIs(result['successor_point_only_projection']['safe_to_lease'], False)


if __name__ == '__main__':
    unittest.main()
