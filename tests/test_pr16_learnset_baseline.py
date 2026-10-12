"""Issue19の新規隔離境界だけを検証する。native/旧P03受入は再実行しない。"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools import pr16_learnset_baseline as b
from tools.modernization_learnsets import REQUIRED_ROUTE_FIELDS


def route(**overrides):
    r = {key: None for key in REQUIRED_ROUTE_FIELDS}
    r.update(route_id='a' * 24, route_kind='direct', method='level_up',
             official_move_id=1, project_move_id=1, existing_vega_move_id=1,
             level=0, target_learning_level=0, source_game='TEST_GAME',
             source_file='test.txt', source_line=1, source_raw_token='1:0',
             learning_species_key='TEST:1', learning_form_index=0)
    r.update(overrides)
    return r


def target():
    return dict(species_key='SPECIES_KEY_TEST', canonical_id=1, form_key='',
                reference_id='test:0001.00', input={'apply': True})


def crosswalk():
    return {1: dict(project_move_id=1, existing_vega_move_id=1,
                    project_move_key='MOVE_KEY_TEST')}


def compiled(r=None, t=None, catalog=None):
    return b.baseline_row(t or target(), r or route(), crosswalk(), catalog or {},
                          {'size': 1, 'sha256': '0' * 64})


class BaselineRows(unittest.TestCase):
    def test_zero_level_is_not_null(self):
        self.assertEqual(compiled()['source_route']['level'], 0)

    def test_source_route_is_lossless(self):
        r = route(extra_condition={'a': [None, 0, False]})
        old = copy.deepcopy(r)
        self.assertEqual(compiled(r)['source_route'], old)
        self.assertEqual(r, old)

    def test_spec_is_not_runtime_acceptance(self):
        self.assertEqual(compiled()['runtime_adoption'], 'NOT_ACTIVATED')

    def test_exact_layer(self):
        self.assertEqual(compiled()['layer'], 'official_baseline')

    def test_preserved_target_cannot_leak(self):
        t = target(); t['input']['apply'] = False
        with self.assertRaises(b.BaselineError): compiled(t=t)

    def test_truthy_string_is_not_adoption(self):
        t = target(); t['input']['apply'] = 'True'
        with self.assertRaises(b.BaselineError): compiled(t=t)

    def test_pre_evolution_donor_level_kept(self):
        r = route(route_kind='pre_evolution', level=17, donor_learning_level=17,
                  target_learning_level=None)
        out = compiled(r)
        self.assertEqual(out['consumer'], 'pre_evolution_carry')
        self.assertEqual(out['source_route']['donor_learning_level'], 17)
        self.assertEqual(out['runtime_supply']['status'], 'CARRY_ONLY_NO_TARGET_DIRECT_BIT')

    def test_pre_evolution_target_level_rejected(self):
        with self.assertRaises(ValueError): compiled(route(route_kind='pre_evolution'))

    def test_shared_egg_is_not_direct_egg(self):
        r = route(route_kind='shared_egg', method='shared_egg', acquisition_condition_ja='TEST条件')
        self.assertEqual(compiled(r)['consumer'], 'shared_egg')

    def test_shared_egg_needs_condition(self):
        with self.assertRaises(ValueError):
            compiled(route(route_kind='shared_egg', method='shared_egg'))

    def test_form_carry_is_not_direct_level(self):
        r = route(route_kind='form_change', form_change_condition_ja='TEST条件')
        self.assertEqual(compiled(r)['consumer'], 'form_change')

    def test_battle_only_not_permanent_level(self):
        self.assertEqual(compiled(route(method='battle_transform'))['consumer'], 'form_change')

    def test_source_tm_not_current_slot(self):
        r = route(method='tm', machine_item='技99')
        out = compiled(r, catalog={('machine', 1): 7})['runtime_supply']
        self.assertEqual(out['source_machine_item'], '技99')
        self.assertEqual(out['runtime_slot_zero_based'], 7)
        self.assertEqual(out['source_machine_namespace'], 'ORIGINAL_GAME_NOT_RUNTIME_SLOT')

    def test_missing_slot_not_created(self):
        self.assertEqual(compiled(route(method='tutor'))['runtime_supply']['status'], 'SUPPLY_REQUIRED')

    def test_unknown_move_rejected(self):
        with self.assertRaises(ValueError): compiled(route(project_move_id=99999))

    def test_unknown_route_rejected(self):
        with self.assertRaises(ValueError): compiled(route(route_kind='CURRENT_PRESERVED'))

    def test_missing_field_rejected(self):
        r = route(); del r['source_line']
        with self.assertRaises(ValueError): compiled(r)

    def test_spec_extension_remains_unimplemented(self):
        r = route(official_move_id=502, project_move_id=1063, existing_vega_move_id=None)
        m = {502: dict(project_move_id=1063, existing_vega_move_id=None,
                       project_move_key='MOVE_KEY_ALLYSWITCH')}
        out = b.baseline_row(target(), r, m, {}, {})
        self.assertIs(out['runtime_move_ready'], False)


class CsvValidation(unittest.TestCase):
    def setUp(self):
        self.row = dict(route_id='a' * 24, route_kind='direct', level='0')
        self.columns = list(self.row)
        self.expected = {'a' * 24: (b.sha(b.encode(self.row)), 'direct')}

    def test_full_match(self):
        self.assertEqual(b.consume_csv([self.row], self.columns, self.expected), 1)

    def test_duplicate_rejected(self):
        with self.assertRaises(b.BaselineError):
            b.consume_csv([self.row, self.row], self.columns, self.expected)

    def test_missing_row_rejected(self):
        with self.assertRaises(b.BaselineError): b.consume_csv([], self.columns, self.expected)

    def test_method_or_level_change_rejected(self):
        row = dict(self.row, level='1')
        with self.assertRaises(b.BaselineError): b.consume_csv([row], self.columns, self.expected)

    def test_wrong_partition_rejected(self):
        with self.assertRaises(b.BaselineError):
            b.consume_csv([self.row], self.columns, self.expected, kind='form_change')

    def test_unknown_route_rejected(self):
        row = dict(self.row, route_id='b' * 24)
        with self.assertRaises(b.BaselineError): b.consume_csv([row], self.columns, self.expected)

    def test_null_differs_from_zero(self):
        self.assertNotEqual(b.csv_value(None), b.csv_value(0))

    def test_array_order_preserved(self):
        self.assertNotEqual(b.csv_value([1, 2]), b.csv_value([2, 1]))

    def test_json_container_formatting_not_semantic_difference(self):
        row = {'inheritance_chain': '[1,  2]'}
        self.assertEqual(b.normalize_csv_row(row, list(row)), {'inheritance_chain': '[1,2]'})

    def test_extra_columns_rejected(self):
        with self.assertRaises(b.BaselineError):
            b.normalize_csv_row(dict(self.row, extra='1'), self.columns)

    def test_missing_values_rejected(self):
        with self.assertRaises(b.BaselineError):
            b.normalize_csv_row(dict(self.row, level=None), self.columns)

    def test_reference_metadata_not_donor_metadata(self):
        ref = dict(reference_id='test:1', national_no=3, source_form=0,
                   species_name_ja='TEST', selected_game='TEST_GAME')
        r = dict(source_species=1)
        cols = list(b.META_COLUMNS) + ['source_species']
        got = b.project_csv(ref, r, cols)
        self.assertEqual(got['target_national_no'], '3')
        self.assertEqual(got['source_species'], '1')


class OutputAndGate(unittest.TestCase):
    def test_output_cannot_target_tracked(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(b.BaselineError): b.ensure_output(Path(d), Path(d) / 'content/out')

    def test_output_cannot_be_local_root(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(b.BaselineError): b.ensure_output(Path(d), Path(d) / '.local')

    def test_output_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p / '.local').symlink_to(p)
            with self.assertRaises(b.BaselineError): b.ensure_output(p, p / '.local/out')

    def test_check_does_not_repair_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p / 'a.json').write_text('{}')
            expected = {'a.json': b.file_identity(p / 'a.json')}
            (p / 'a.json').write_text('{"bad":true}')
            before = (p / 'a.json').read_bytes()
            with self.assertRaises(b.BaselineError): b.compare_outputs(p, expected)
            self.assertEqual((p / 'a.json').read_bytes(), before)

    def test_unexpected_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p / 'extra').write_text('x')
            with self.assertRaises(b.BaselineError): b.compare_outputs(p, {})

    def test_unexpected_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p / 'extra').mkdir()
            with self.assertRaises(b.BaselineError): b.compare_outputs(p, {})

    def test_gate_keeps_three_independent_blockers(self):
        gate = b.source_gate(vega_complete=False, exceptions_resolved=False, runtime_complete=False)
        self.assertFalse(gate['ready']); self.assertEqual(len(gate['blockers']), 3)

    def test_csv_pass_cannot_close_native_gap(self):
        gate = b.source_gate(vega_complete=True, exceptions_resolved=True, runtime_complete=False)
        self.assertFalse(gate['ready'])

    def test_encoding_is_deterministic(self):
        self.assertEqual(b.encode({'b': 1, 'a': 2}), b.encode({'a': 2, 'b': 1}))


if __name__ == '__main__': unittest.main()
