"""新732親の容量束縛と不変性だけを検査する。旧suiteは再走しない。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_dex_hof_boundary_capacity as m
import pr16_dex_hof_boundary_chain as chain


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

    def test_exact_732_parent_no_synthetic_extra_classification(self):
        result = self.evaluate()
        plan = result['successor_plan']
        self.assertEqual(plan['parent_unknown_count'], 142)
        self.assertEqual(plan['current_unknown_count'], 142)
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
        parent['unclassified'] = 141
        with self.assertRaises(ValueError):
            self.evaluate(parent_audit=parent)

    def test_each_historical_parent_still_exact(self):
        for name in ('runtime_parent', 'lifetime_parent', 'callback_parent', 'baseline_audit'):
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
        hit = next(h for h in self.parent['hits'] if h['address'] == 0x08142F5D)
        region = chain.d.TypedRegion(hit['address'], hit['address'] + hit['size'],
            'zlib_serialized_archive', {'stream': {'address': hit['address'], 'size': hit['size']}})
        delta = chain.build(self.parent, [region], {'capacity_test_only': True})
        full = chain.materialize(self.parent, delta)
        result = self.evaluate(full=full)
        plan = result['successor_plan']
        self.assertEqual((plan['parent_unknown_count'], plan['current_unknown_count'],
                          plan['newly_classified_count']), (142, 141, 1))
        self.assertEqual(plan['protected'], [{'address': result['donor']['address'], 'size': 15118}])
        self.assertEqual(plan['total_unprotected_bytes'], 0)
        self.assertFalse(plan['lease_authorized'])
        self.assertFalse(plan['rom_mutation_performed'])

    def test_immediate_parent_identity_and_prior_plan_retained(self):
        result = self.evaluate()
        self.assertEqual(result['successor_plan']['parent_frontier_identity'], m.INPUTS[m.FRONTIER])
        self.assertEqual(result['immediate_parent_input_bindings'], m.INPUTS)
        self.assertEqual(result['immediate_parent_checkpoint'], m.CHECKPOINT)
        self.assertEqual(result['fixed729_runtime_parent_successor_plan']['parent_unknown_count'], 145)

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
        self.assertEqual(len(bindings), 12)
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


if __name__ == '__main__':
    unittest.main()
