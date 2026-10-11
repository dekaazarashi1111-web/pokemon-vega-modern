"""新741親の容量束縛と不変性だけを検査する。旧suiteは再走しない。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_dex_hof_help_batch_capacity as m
import pr16_dex_hof_help_batch_chain as chain


class CapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        args = [(m.ROOT / p).read_bytes() for p in chain.PARENT_INPUTS]
        cls.parents = chain.parent_audits(*args)
        cls.parent = cls.parents['parent_audit']

    def evaluate(self, full=None, **overrides):
        parents = dict(self.parents)
        parents.update(overrides)
        return m.current_report(self.parent if full is None else full, **parents)

    def test_exact_741_parent_no_synthetic_extra_classification(self):
        result = self.evaluate()
        plan = result['successor_plan']
        self.assertEqual(plan['parent_unknown_count'], 133)
        self.assertEqual(plan['current_unknown_count'], 133)
        self.assertEqual(plan['newly_classified_count'], 0)
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertFalse(plan['lease_eligible'])
        self.assertFalse(plan['lease_authorized'])

    def test_all115_owners_controller6528_known1315_unchanged(self):
        result = self.evaluate()
        self.assertEqual(result['successor_plan']['owner_count'], 115)
        self.assertEqual(result['controller']['total_allocated_bytes'], 6528)
        self.assertEqual(result['other_known_capacity']['sum_upper_bound_bytes'], 1315)
        self.assertEqual(result['donor']['size'], 15118)

    def test_parent_whole_candidate(self):
        parent = copy.deepcopy(self.parent)
        parent['candidate'] = {}
        with self.assertRaises(ValueError):
            self.evaluate(parent_audit=parent)

    def test_parent_unknown_fields(self):
        for key, value in [('target', 1), ('sha256', 'bad'), ('reason', 'changed')]:
            parent = copy.deepcopy(self.parent)
            next(h for h in parent['hits'] if not h['accepted'])[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.evaluate(parent_audit=parent)

    def test_parent_accepted_evidence_cannot_be_replaced(self):
        parent = copy.deepcopy(self.parent)
        next(h for h in parent['hits'] if h['accepted'])['evidence'] = []
        with self.assertRaises(ValueError):
            self.evaluate(full=parent, parent_audit=parent)

    def test_parent_counter(self):
        parent = copy.deepcopy(self.parent)
        parent['unclassified'] = 138
        with self.assertRaises(ValueError):
            self.evaluate(parent_audit=parent)

    def test_each_historical_parent_still_exact(self):
        for name in ('remaining_consumers_parent', 'summary_parent', 'party_parent', 'boundary_parent', 'runtime_parent', 'lifetime_parent', 'callback_parent', 'baseline_audit'):
            changed = copy.deepcopy(self.parents[name])
            changed['classified'] -= 1
            with self.subTest(parent=name), self.assertRaises(ValueError):
                self.evaluate(**{name: changed})

    def test_same_count729_ancestors_cannot_substitute(self):
        with self.assertRaises(ValueError):
            self.evaluate(runtime_parent=self.parents['lifetime_parent'])
        with self.assertRaises(ValueError):
            self.evaluate(lifetime_parent=self.parents['runtime_parent'])

    def test_retained_accepted_cannot_change(self):
        full = copy.deepcopy(self.parent)
        next(h for h in full['hits'] if h['accepted'])['sha256'] = 'changed'
        with self.assertRaises(ValueError):
            self.evaluate(full=full)

    def test_each_no_lease_flag_cannot_promote(self):
        for flag in chain.FLAGS:
            full = copy.deepcopy(self.parent)
            full[flag] = True
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                self.evaluate(full=full)

    def test_every_inherited_proof_family_remains_exact(self):
        for name in chain.INHERITED_NAMES:
            full = copy.deepcopy(self.parent)
            full[name]['proof'] = {'replaced': True}
            with self.subTest(namespace=name), self.assertRaises(ValueError):
                self.evaluate(full=full)

    def test_inherited_namespace_cannot_disappear(self):
        full = copy.deepcopy(self.parent)
        del full['runtime_reference_chain']
        with self.assertRaises(ValueError):
            self.evaluate(full=full)

    def test_parent_input_full_hash(self):
        with patch.dict(m.INPUTS, {m.FRONTIER: dict(size=1, sha256='bad')}):
            with self.assertRaises(ValueError):
                self.evaluate()

    def test_parent_input_lf_and_not_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in m.INPUTS:
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.symlink_to(m.ROOT / path)
            with self.assertRaises(ValueError):
                m.read_inputs(root)

    def test_each_immediate_capacity_file_is_whole_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in m.INPUTS:
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes((m.ROOT / path).read_bytes())
            for path in m.INPUTS:
                file = root / path
                original = file.read_bytes()
                file.write_bytes(original + b' ')
                with self.subTest(path=path), self.assertRaises(ValueError):
                    m.read_inputs(root)
                file.write_bytes(original)

    def test_point_projection_is_not_safe_capacity(self):
        result = self.evaluate()
        self.assertEqual(result['successor_point_only_projection']['largest_gap_bytes'], 1553)
        self.assertFalse(result['successor_point_only_projection']['safe_to_lease'])
        self.assertEqual(result['successor_plan']['total_unprotected_bytes'], 0)

    def test_newly_classified_hit_does_not_retire_owner_or_make_lease(self):
        # 容量計算専用の合成分類。実ROM consumer証明の代替にはしない。
        hit = next(h for h in self.parent['hits'] if not h['accepted'])
        region = chain.d.TypedRegion(hit['address'], hit['address'] + hit['size'],
            'rooted_help_context_topic_minimum_ids', {'address': hit['address'], 'size': hit['size'], 'synthetic_protocol_only': True})
        with patch.dict(sys.modules, {'pr16_dex_hof_help_roots': SimpleNamespace(KIND=region.kind, witness_geometry=lambda e: (e['address'], e['size']))}):
            delta = chain.build(self.parent, [region], {'capacity_test_only': True})
            full = chain.materialize(self.parent, delta)
            result = self.evaluate(full=full)
        plan = result['successor_plan']
        self.assertEqual((plan['parent_unknown_count'], plan['current_unknown_count'],
                          plan['newly_classified_count']), (133, 132, 1))
        self.assertEqual(plan['protected'], [{'address': result['donor']['address'], 'size': 15118}])
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertFalse(plan['lease_authorized'])
        self.assertFalse(plan['rom_mutation_performed'])

    def test_immediate_parent_identity_and_prior_plan_retained(self):
        result = self.evaluate()
        self.assertEqual(result['successor_plan']['parent_frontier_identity'], m.INPUTS[m.FRONTIER])
        self.assertEqual(result['immediate_parent_input_bindings'], m.INPUTS)
        self.assertEqual(result['immediate_parent_checkpoint'], m.CHECKPOINT)
        self.assertEqual(result['fixed733_party_parent_successor_plan']['parent_unknown_count'], 141)

    def test_full_inventory_and_unknown_fields_are_immutable(self):
        full = copy.deepcopy(self.parent)
        next(h for h in full['hits'] if not h['accepted'])['reason'] = 'new assertion'
        with self.assertRaises(ValueError):
            self.evaluate(full=full)
        full = copy.deepcopy(self.parent)
        full['hits'].reverse()
        with self.assertRaises(ValueError):
            self.evaluate(full=full)

    def test_report_does_not_mutate_any_input(self):
        before = copy.deepcopy(self.parents)
        self.evaluate()
        self.assertEqual(self.parents, before)

    def test_all_capacity_bindings_include_every_historical_input(self):
        bindings = m.all_input_bindings()
        self.assertEqual(list(bindings), sorted(bindings))
        self.assertEqual(len(bindings), 22)
        for path, expected in bindings.items():
            with self.subTest(path=path):
                self.assertEqual(chain.identity((m.ROOT / path).read_bytes()), expected)
        for path, expected in m.base_capacity.INPUTS.items():
            self.assertEqual(bindings[path], dict(zip(('size', 'sha256'), expected)))
        self.assertEqual(bindings[m.FRONTIER], m.INPUTS[m.FRONTIER])

    def test_duplicate_capacity_bindings_must_agree(self):
        with patch.dict(m.prior.INPUTS, {m.FRONTIER: {'size': 1, 'sha256': 'bad'}}):
            with self.assertRaises(ValueError):
                m.all_input_bindings()
        with patch.dict(m.prior.INPUTS, {m.FRONTIER: copy.deepcopy(m.INPUTS[m.FRONTIER])}):
            self.assertEqual(m.all_input_bindings()[m.FRONTIER], m.INPUTS[m.FRONTIER])

    def test_merged_capacity_bindings_are_not_aliases(self):
        values = m.all_input_bindings()
        values[m.FRONTIER]['sha256'] = 'changed'
        self.assertNotEqual(values[m.FRONTIER], m.INPUTS[m.FRONTIER])

    def test_capacity_lineage_cycle_fails_closed(self):
        with patch.object(m.prior, 'prior', m.prior):
            with self.assertRaises(ValueError):
                m.all_input_bindings()


    def test_saved_current_plan_is_bound_separately_from_historical_plan(self):
        frontier, checkpoint, saved = m.read_inputs()
        self.assertEqual(checkpoint['capacity_identity'], m.INPUTS[m.PARENT_PLAN])
        self.assertEqual(saved['current_plan']['unbounded_access_count'], 148)
        self.assertEqual(saved['successor_plan']['current_unknown_count'], 133)
        result = self.evaluate()
        self.assertEqual(result['immediate_parent_capacity_identity'], m.INPUTS[m.PARENT_PLAN])
        self.assertEqual(result['immediate_parent_recorded_successor_plan'], saved['successor_plan'])
        self.assertEqual(result['fixed735_summary_parent_successor_plan']['parent_unknown_count'], 139)

    def test_parent_plan_recalculation_must_match_saved_measurement(self):
        inputs = m.read_inputs()
        saved = copy.deepcopy(inputs[2])
        saved['successor_plan']['protected'] = []
        with patch.object(m, 'read_inputs', return_value=(inputs[0], inputs[1], saved)):
            with self.assertRaisesRegex(ValueError, 'saved current741 plan'):
                self.evaluate()

    def test_saved_capacity_quantities_cannot_be_silently_recomputed(self):
        inputs = m.read_inputs()
        for key in ('donor', 'controller', 'current_plan', 'other_known_capacity', 'execution'):
            saved = copy.deepcopy(inputs[2])
            saved[key] = {'altered': True}
            with self.subTest(key=key), patch.object(m, 'read_inputs', return_value=(inputs[0], inputs[1], saved)):
                with self.assertRaisesRegex(ValueError, 'fixed capacity quantities'):
                    self.evaluate()

    def test_zero_diagnostic_preserves_all_parent_capacity_and_hit_rows(self):
        delta = chain.build(self.parent, [], {'diagnostic_only': True})
        full = chain.materialize(self.parent, delta)
        result = self.evaluate(full=full)
        self.assertEqual(result['successor_plan']['current_unknown_count'], 133)
        self.assertEqual(result['successor_plan']['newly_classified_count'], 0)
        self.assertEqual(result['successor_plan']['total_unprotected_bytes'], 0)
        self.assertEqual(full['hits'], self.parent['hits'])
        for name in chain.INHERITED_NAMES:
            self.assertEqual(full[name], self.parent[name])

    def test_capacity_input_lf_requirement_is_independent_of_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in m.INPUTS:
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes((m.ROOT / path).read_bytes())
            for suffix in (b'', b'\r\n'):
                path = root / m.PARENT_PLAN
                raw = (m.ROOT / m.PARENT_PLAN).read_bytes().rstrip(b'\n') + suffix
                path.write_bytes(raw)
                with self.subTest(suffix=suffix), patch.dict(m.INPUTS, {m.PARENT_PLAN: chain.identity(raw)}):
                    with self.assertRaisesRegex(ValueError, 'independent741 capacity input'):
                        m.read_inputs(root)

    def test_all_thirteen_namespaces_and874_rows_retained(self):
        self.assertEqual(len(chain.INHERITED_NAMES), 13)
        self.assertEqual(len(self.parent['hits']), 874)
        self.assertEqual(sum(len(self.parent[name]['changes']) for name in chain.INHERITED_NAMES), 122)
        self.assertEqual(sum(len(self.parent[name]['witnesses']) for name in chain.INHERITED_NAMES), 112)


    def test_runtime_heap_and_stock_save_boundary_remains_unproved(self):
        result = self.evaluate()
        boundary = result['help_batch_runtime_boundary']
        self.assertEqual(boundary['controller_measured_bytes'], 6528)
        self.assertEqual(boundary['heap_scratch_bytes'], 13352)
        self.assertEqual(boundary['stock_save_backup_bytes'], 53300)
        self.assertEqual(boundary['release_before_stock_save_entry'], 0x0804B85C)
        for key in ('heap_lifetime_proven', 'controller_runtime_wired',
                    'universal_irq_or_heap_lifetime_claimed', 'stock_save_boundary_crossing_allowed',
                    'all_save_entry_heap_ready_proven', 'synchronous_nonreentrant_use_proven',
                    'donor_leased', 'formal_rom_changed', 'formal_save_changed'):
            self.assertIs(boundary[key], False)
        self.assertEqual(boundary['donor_safe_bytes'], 0)

    def test_runtime_boundary_return_has_no_shared_mutable_state(self):
        first = m.runtime_boundary()
        first['heap_lifetime_proven'] = True
        self.assertIs(m.runtime_boundary()['heap_lifetime_proven'], False)

    def test_classification_counters_alone_never_authorize_capacity(self):
        full = copy.deepcopy(self.parent)
        hit = next(row for row in full['hits'] if not row['accepted'])
        hit['accepted'] = True
        full['classified'] += 1
        full['unclassified'] -= 1
        with self.assertRaisesRegex(ValueError, 'without a new delta'):
            self.evaluate(full=full)

    def test_materialized_classifications_and_runtime_claims_are_bound(self):
        delta = chain.build(self.parent, [], {})
        for key, value in (('classifications', {'SAFE_DONOR': 874}),
                           ('controller_runtime_wired', True), ('donor_safe_bytes', 15118),
                           ('universal_heap_or_irq_lifetime_proven', True),
                           ('classified', float(self.parent['classified']))):
            full = chain.materialize(self.parent, delta)
            full[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.evaluate(full=full)

    def test_unknown_zero_still_requires_indirect_completeness_and_retirement(self):
        # 合成validatorで容量式の極限だけを検査。実Help分類の証明ではない。
        kind = 'rooted_help_context_topic_minimum_ids'
        regions = [chain.d.TypedRegion(row['address'], row['address'] + row['size'], kind,
            {'address': row['address'], 'size': row['size'], 'synthetic_protocol_only': True})
            for row in self.parent['hits'] if not row['accepted']]
        module = SimpleNamespace(KIND=kind, witness_geometry=lambda e: (e['address'], e['size']))
        with patch.dict(sys.modules, {'pr16_dex_hof_help_roots': module}):
            delta = chain.build(self.parent, regions, {'capacity_limit_test_only': True})
            full = chain.materialize(self.parent, delta)
            result = self.evaluate(full=full)
        plan = result['successor_plan']
        self.assertEqual((plan['current_unknown_count'], plan['newly_classified_count']), (0, 133))
        self.assertEqual(plan['protected'], [{'address': result['donor']['address'], 'size': 15118}])
        self.assertEqual(plan['unresolved_obligations'], [
            'indirect_reference_completeness_unproven', 'partial_retirement_and_explicit_owner_transfer_unproven'])
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertFalse(plan['lease_eligible'])
        self.assertFalse(plan['lease_authorized'])

    def test_new_delta_cannot_be_replaced_with_old_namespace(self):
        full = copy.deepcopy(self.parent)
        full[chain.NAMESPACE] = full['remaining_consumers_reference_chain']
        with self.assertRaises(ValueError):
            self.evaluate(full=full)

    def test_parent_exact_remaining_consumers_successor_is_separately_retained(self):
        result = self.evaluate()
        saved = m.read_inputs()[2]
        self.assertEqual(result['immediate_parent_recorded_successor_plan'], saved['successor_plan'])
        self.assertEqual(result['fixed737_remaining_consumers_parent_successor_plan']['parent_unknown_count'], 137)
        self.assertEqual(result['immediate_parent_capacity_identity'], m.INPUTS[m.PARENT_PLAN])


if __name__ == '__main__':
    unittest.main()
