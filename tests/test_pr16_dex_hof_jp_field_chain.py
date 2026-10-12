"""JP fieldの51親原本・1件delta・全field保存だけを検証。旧suite/nativeは呼ばない。"""
import copy
import json
import sys
import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import pr16_dex_hof_jp_field_chain as m
from test_pr16_dex_hof_jp_field_text import fixture


@lru_cache(maxsize=1)
def recorded_parent():
    args = tuple((ROOT / path).read_bytes() for path in m.PARENT_INPUTS)
    # 保存JSON検証から外部processや旧caseへ逸脱しない。
    with patch('subprocess.Popen', side_effect=AssertionError('native禁止')), \
         patch.object(m.consumer.stock, 'compose_selected', side_effect=AssertionError('旧case禁止')), \
         patch.object(m.consumer, 'compose_selected', side_effect=AssertionError('新caseも親読取では禁止')):
        parent = m.parent(*args)
    return args, parent


class FieldChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args, cls.parent = recorded_parent()
        cls.regions, cls.proof = m.consumer._regions(fixture(), cls.parent)
        cls.delta = m.build(cls.parent, cls.regions, cls.proof)
        cls.full = m.materialize(cls.parent, cls.delta)
        cls.zero = m.build(cls.parent, [], {'source_only_protocol': True})

    def reject(self, delta):
        with self.assertRaises(ValueError):
            m.validate(self.parent, delta)

    def test_exact_parent_all_fields_and_counts(self):
        self.assertEqual(m.identity(m.canonical(self.parent)), m.PARENT_AUDIT_ID)
        self.assertEqual(m.PARENT_AUDIT_ID, {'size': 4433327, 'sha256': '80bbcb126b5e4fe387624e7a8a0f081ff55df3a2a47bb1dc5f0217ede05149d4'})
        self.assertEqual((self.parent['classified'], self.parent['unclassified'], len(self.parent['hits'])), (779, 95, 874))
        self.assertEqual((len(m.INHERITED_NAMES), sum(len(self.parent[n]['changes']) for n in m.INHERITED_NAMES),
                          sum(len(self.parent[n]['witnesses']) for n in m.INHERITED_NAMES)), (26, 160, 150))

    def test_all51_input_identities_and_order(self):
        self.assertEqual(len(m.PARENT_INPUTS), 51)
        self.assertEqual(tuple(m.PARENT_INPUT_IDENTITIES), m.PARENT_INPUTS)
        self.assertEqual(m.PARENT_INPUTS[:-2], m.previous.PARENT_INPUTS)
        for path, raw in zip(m.PARENT_INPUTS, self.args):
            self.assertEqual(m.identity(raw), m.PARENT_INPUT_IDENTITIES[path])

    def test_each_input_mutation_fails_before_previous(self):
        for i in range(51):
            args = list(self.args)
            args[i] += b'\n'
            with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
                with self.assertRaises(ValueError):
                    m.parent(*args)

    def test_every_parent_lf_bytes_and_input_count(self):
        for i in range(51):
            for raw in (self.args[i].rstrip(b'\n'), self.args[i].replace(b'\n', b'\r\n'), bytearray(self.args[i])):
                args = list(self.args)
                args[i] = raw
                with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
                    with self.assertRaises(ValueError):
                        m.parent(*args)
        for args in (self.args[:-1], self.args + (b'{}\n',)):
            with self.assertRaises(ValueError):
                m.parent(*args)

    def test_parent_audits_names_only_and_no_second_latest(self):
        prior = {'parent_audit': {'classified': 776}, 'baseline_audit': {'classified': 100}}
        with patch.object(m, 'parent', return_value=self.parent) as latest, \
             patch.object(m.previous, 'parent_audits', return_value=copy.deepcopy(prior)) as inherited:
            values = m.parent_audits(*self.args)
        latest.assert_called_once_with(*self.args)
        inherited.assert_called_once_with(*self.args[:-2])
        self.assertEqual(values['parent_audit'], self.parent)
        self.assertEqual(values['registered_ui_batch_parent'], prior['parent_audit'])
        self.assertEqual(values['baseline_audit'], prior['baseline_audit'])

    def test_only_one_hit_780_and94_with_closed_geometry(self):
        self.assertEqual(m.validate(self.parent, self.delta), 1)
        self.assertEqual((self.delta['classified'], self.delta['unclassified'], self.delta['newly_classified']), (780, 94, 1))
        self.assertEqual([r['address'] for r in self.delta['changes']], [0x083DDEE1])
        self.assertEqual([(r['address'], r['size'], r['kind']) for r in self.delta['witnesses']], [(m.HIT, 4, m.KIND)])
        self.assertEqual(m.witness_geometry(self.delta['witnesses'][0]), (m.HIT, 4))

    def test_actual_new_composition_and_old_right_receipt(self):
        self.assertEqual(self.proof['composition']['text_read_bytes'], 30)
        self.assertEqual(self.proof['composition']['producer']['outer_actions'], [0, 18, 3, 2])
        self.assertEqual(self.proof['reused_right']['complete_consumed_bytes'], 27)
        self.assertFalse(self.proof['reused_right']['existing_execution_replayed'])
        self.assertEqual(self.delta['proof'], self.proof)
        self.assertLess(len(m.canonical(self.delta)), m.PARENT_ID['size'])

    def test_zero_delta_retains_every_original_field(self):
        full = m.materialize(self.parent, self.zero)
        self.assertEqual({k: v for k, v in full.items() if k != m.NAMESPACE}, self.parent)
        self.assertEqual((self.zero['changes'], self.zero['witnesses']), ([], []))
        self.assertEqual(m.validate(self.parent, self.zero), 0)

    def test_old_accepted_and_remaining_unknown_rows_exact(self):
        for old, current in zip(self.parent['hits'], self.full['hits']):
            if old['address'] != m.HIT:
                self.assertEqual(old, current)
            else:
                self.assertFalse(old['accepted'])
                self.assertTrue(current['accepted'])
                self.assertEqual(current['evidence'], [{'jp_field_reference_chain_witness': 0}])
        self.assertEqual(len([h for h in self.full['hits'] if not h['accepted']]), 94)
        self.assertTrue(m.d.compare_inventory(self.full['hits'], self.parent)['same_inventory'])

    def test_all26_namespaces_and_source_fields_exact(self):
        for name in m.INHERITED_NAMES:
            self.assertEqual(self.full[name], self.parent[name])
        for key in self.parent:
            if key not in {'hits', 'classified', 'unclassified', 'classifications'}:
                self.assertEqual(self.full[key], self.parent[key])
        self.assertEqual(self.full['source_bindings'], self.parent['source_bindings'])

    def test_song133_models50_sample_identities_retained(self):
        song = self.parent[m.previous.NAMESPACE]['proof']['song']
        self.assertEqual(song, self.full[m.previous.NAMESPACE]['proof']['song'])
        self.assertEqual((song['combined_song_models'], song['retained_sample_witnesses']), (133, 50))
        self.assertIs(song['all133_models_exact'], True)
        self.assertIs(song['all50_sample_identities_exact'], True)

    def test_independent_copy_of_parent_delta_and_evidence(self):
        parent = copy.deepcopy(self.parent)
        regions = copy.deepcopy(self.regions)
        proof = copy.deepcopy(self.proof)
        delta = m.build(parent, regions, proof)
        full = m.materialize(parent, delta)
        full[m.NAMESPACE]['proof']['extra'] = True
        full[m.previous.NAMESPACE]['proof']['extra'] = True
        full['hits'][0]['extra'] = True
        delta['witnesses'][0]['evidence']['extra'] = True
        self.assertEqual(parent, self.parent)
        self.assertEqual(regions, self.regions)
        self.assertEqual(proof, self.proof)

    def test_parent_all_field_mutation_rejected(self):
        for key, value in (('classified', 780), ('donor_leased', True), ('extra', 'invented'),
                           ('source_bindings', {}), ('candidate', {}), ('hits', [])):
            parent = copy.deepcopy(self.parent)
            parent[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                m.validate_parent_state(parent)

    def test_each_inherited_namespace_mutation_rejected(self):
        for name in m.INHERITED_NAMES:
            parent = copy.deepcopy(self.parent)
            parent[name]['extra'] = True
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.validate_parent_state(parent)

    def test_materialized_full_field_mutation_rejected(self):
        self.assertIs(m.validate_materialized(self.parent, self.full), self.full)
        self.assertIs(m.validate_materialized(self.parent, self.parent), self.parent)
        for key, value in (('source_bindings', {}), ('extra', True), ('classified', 779), ('donor_eligible', True)):
            full = copy.deepcopy(self.full)
            full[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                m.validate_materialized(self.parent, full)
        full = copy.deepcopy(self.full)
        full['hits'][0]['extra'] = True
        with self.assertRaises(ValueError):
            m.validate_materialized(self.parent, full)

    def test_each_top_schema_field_required_and_no_extra(self):
        for key in self.delta:
            delta = copy.deepcopy(self.delta)
            del delta[key]
            with self.subTest(field=key):
                self.reject(delta)
        self.reject(dict(self.delta, extra=True))

    def test_schema_status_and_every_counter_strict(self):
        for key in ('schema_version', 'inherited_candidates', 'inherited_classified', 'inherited_unclassified',
                    'classified', 'unclassified', 'newly_classified', 'native_processes', 'old_full_rom_scan_runs', 'donor_safe_bytes'):
            for value in (True, 0.0, -1):
                with self.subTest(field=key, value=value):
                    self.reject(dict(self.delta, **{key: value}))
        for value in ('PASS', m.previous.NAMESPACE, None):
            self.reject(dict(self.delta, status=value))

    def test_parent_baseline_candidate_envelopes_cannot_be_resealed(self):
        for key in ('parent', 'baseline', 'candidate'):
            for field, value in (('size', 1), ('sha256', 'a' * 64), ('extra', True)):
                delta = copy.deepcopy(self.delta)
                delta[key][field] = value
                with self.subTest(key=key, field=field):
                    self.reject(delta)

    def test_every_counter_correct_arithmetic(self):
        for key in ('inherited_candidates', 'inherited_classified', 'inherited_unclassified',
                    'classified', 'unclassified', 'newly_classified', 'native_processes', 'old_full_rom_scan_runs', 'donor_safe_bytes'):
            self.reject(dict(self.delta, **{key: self.delta[key] + 1}))

    def test_every_top_safety_flag_false_not_false_alias(self):
        for key in (*m.FLAGS, *m.BATCH_FLAGS):
            for value in (True, 0, None):
                with self.subTest(field=key, value=value):
                    self.reject(dict(self.delta, **{key: value}))

    def test_no_nested_unproved_claims(self):
        keys = ('donor_leased', 'donor_eligible', 'indirect_reference_completeness_claimed',
                'natural_play_universal_reachability_claimed', 'universal_irq_or_heap_lifetime_claimed',
                'all_save_entry_heap_ready_proven', 'synchronous_nonreentrant_use_proven',
                'target_retirement_proven', 'explicit_owner_transfer_proven',
                'independent_old_final_source_review_completed', 'opaque_callee_effects_proven',
                'field_move_function_called', 'pointer_host_seeded', 'existing_execution_replayed',
                'release_ready', 'formal_rom_changed', 'formal_save_changed')
        for key in keys:
            with self.subTest(field=key), self.assertRaises(ValueError):
                m.build(self.parent, [], {'nested': [{key: True}]})

    def test_no_nested_safety_bytes_or_execution_promotion(self):
        for key in ('donor_safe_bytes', 'safe_donor_bytes', 'old_full_rom_scan_runs', 'native_processes', 'rom_writes', 'save_writes'):
            for value in (1, True, 0.0):
                with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                    m.build(self.parent, [], {'nested': {key: value}})

    def test_no_any_parent_namespace_or_inventory_copy(self):
        for key in (*m.INHERITED_NAMES, 'baseline_audit', 'parent_audit', 'inherited_audit'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.build(self.parent, [], {'nested': {key: {}}})
        with self.assertRaises(ValueError):
            m.build(self.parent, [], {'nested': {'hits': [], 'candidate': {}}})

    def test_proof_and_evidence_identity_must_match(self):
        for field in ('proof', 'evidence'):
            delta = copy.deepcopy(self.delta)
            target = delta if field == 'proof' else delta['witnesses'][0]
            target[field]['extra'] = True
            self.reject(delta)

    def test_identity_schema_types_and_hash_case(self):
        for value in ({'size': True, 'sha256': 'a' * 64}, {'size': 1.0, 'sha256': 'a' * 64},
                      {'size': 1, 'sha256': 'A' * 64}, {'size': 1, 'sha256': 'a' * 64, 'extra': 1},
                      {'size': -1, 'sha256': 'a' * 64}, {'size': 1, 'sha256': 'z' * 64}):
            self.assertFalse(m.valid_identity(value))
            delta = copy.deepcopy(self.delta)
            delta['proof_identity'] = value
            self.reject(delta)

    def test_changes_witnesses_canonical_list_and_zero_or_one(self):
        for key in ('changes', 'witnesses'):
            for value in ((), {}, None, self.delta[key] * 2, []):
                with self.subTest(key=key):
                    self.reject(dict(self.delta, **{key: value}))

    def test_every_change_field_required_no_extra(self):
        for key in self.delta['changes'][0]:
            delta = copy.deepcopy(self.delta)
            del delta['changes'][0][key]
            with self.subTest(field=key):
                self.reject(delta)
        delta = copy.deepcopy(self.delta)
        delta['changes'][0]['extra'] = True
        self.reject(delta)

    def test_hit_original_identity_cannot_change(self):
        for key in m.FIELDS:
            for value in (None, True, 0.0, 'changed'):
                delta = copy.deepcopy(self.delta)
                delta['changes'][0][key] = value
                with self.subTest(field=key, value=value):
                    self.reject(delta)
        delta = copy.deepcopy(self.delta)
        old = next(h for h in self.parent['hits'] if h['accepted'])
        delta['changes'][0].update({k: old[k] for k in m.FIELDS})
        self.reject(delta)

    def test_other_unknown_cannot_gain_classification(self):
        delta = copy.deepcopy(self.delta)
        old = next(h for h in self.parent['hits'] if not h['accepted'] and h['address'] != m.HIT)
        delta['changes'][0].update({k: old[k] for k in m.FIELDS})
        self.reject(delta)

    def test_witness_references_and_classification_strict(self):
        for key, value in (('accepted', 1), ('accepted', False), ('classification', 'DATA'),
                           ('witness_ids', [True]), ('witness_ids', [0.0]), ('witness_ids', []),
                           ('witness_ids', [1]), ('witness_ids', [0, 0]), ('witness_ids', (0,))):
            delta = copy.deepcopy(self.delta)
            delta['changes'][0][key] = value
            with self.subTest(field=key, value=value):
                self.reject(delta)

    def test_every_witness_field_required_no_extra(self):
        for key in self.delta['witnesses'][0]:
            delta = copy.deepcopy(self.delta)
            del delta['witnesses'][0][key]
            with self.subTest(field=key):
                self.reject(delta)
        delta = copy.deepcopy(self.delta)
        delta['witnesses'][0]['extra'] = True
        self.reject(delta)

    def test_witness_geometry_address_size_and_type_strict(self):
        for key, values in (('id', [True, 0.0, 1]), ('address', [m.HIT - 1, m.HIT + 1, float(m.HIT)]),
                            ('size', [True, 4.0, 3, 5, 30]), ('kind', ['invented', m.consumer.stock.KIND])):
            for value in values:
                delta = copy.deepcopy(self.delta)
                delta['witnesses'][0][key] = value
                with self.subTest(field=key, value=value):
                    self.reject(delta)

    def test_resealed_witness_cannot_mutate_template(self):
        for key in self.delta['witnesses'][0]['evidence']:
            delta = copy.deepcopy(self.delta)
            row = delta['witnesses'][0]
            del row['evidence'][key]
            row['evidence_identity'] = m.identity(m.canonical(row['evidence']))
            with self.subTest(field=key):
                self.reject(delta)
        delta = copy.deepcopy(self.delta)
        row = delta['witnesses'][0]
        row['evidence']['extra'] = True
        row['evidence_identity'] = m.identity(m.canonical(row['evidence']))
        self.reject(delta)

    def test_consumer_cannot_return_different_geometry(self):
        for geometry in ((m.HIT, 4.0), (m.HIT, True), (m.HIT, 5), (m.HIT - 1, 4), (m.HIT,), None):
            with self.subTest(geometry=geometry), patch.object(m.consumer, 'witness_geometry', return_value=geometry):
                self.reject(self.delta)

    def test_unregistered_old_kinds_and_registry_drift_rejected(self):
        for kind in ('invented', m.consumer.stock.KIND, 'registered_frontier_records_minimum_text_consumption'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                m.witness_geometry({'kind': kind, 'evidence': {}})
        with patch.object(m.consumer, 'KIND', 'changed'), self.assertRaises(ValueError):
            m.witness_geometry(self.delta['witnesses'][0])

    def test_build_rejects_duplicate_or_wider_regions(self):
        for regions in (self.regions * 2, [m.d.TypedRegion(m.HIT, m.HIT + 5, m.KIND, {})],
                        [m.d.TypedRegion(m.HIT - 1, m.HIT + 4, m.KIND, {})],
                        [m.d.TypedRegion(m.HIT, m.HIT + 4, 'invented', {})], None):
            with self.subTest(regions=regions), self.assertRaises(ValueError):
                m.build(self.parent, regions, self.proof)

    def test_measured_roundtrip_and_external_identity(self):
        raw = m.canonical(self.delta)
        self.assertEqual(m.read_measured(raw, m.identity(raw), self.parent), self.delta)
        for changed in (raw + b'\n', raw.rstrip(b'\n'), raw.replace(b'\n', b'\r\n'), bytearray(raw)):
            with self.assertRaises(ValueError):
                m.read_measured(changed, m.identity(raw), self.parent)
        with self.assertRaises(ValueError):
            m.read_measured(raw, dict(m.identity(raw), extra=True), self.parent)

    def test_measured_duplicate_json_keys_and_nan_rejected(self):
        raw = m.canonical(self.delta)
        for changed in (raw.replace(b'{', b'{"schema_version":1,', 1),
                        raw.replace(b'"donor_safe_bytes":0', b'"donor_safe_bytes":NaN', 1)):
            with self.assertRaises(ValueError):
                m.read_measured(changed, m.identity(changed), self.parent)

    def test_bounded_delta_before_materialization(self):
        raw = m.canonical(self.delta)
        with patch.object(m, 'MAX_DELTA_BYTES', len(raw) - 1):
            self.reject(self.delta)
            with self.assertRaises(ValueError):
                m.read_measured(raw, m.identity(raw), self.parent)

    def test_parent_original_files_stay_unchanged(self):
        for path, original in zip(m.PARENT_INPUTS, self.args):
            self.assertEqual((ROOT / path).read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
