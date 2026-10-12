"""JP itemの53保存親・4byte deltaを独立fixtureで検証。旧suite/ROM/nativeは呼ばない。"""
import copy
import json
import sys
import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import pr16_dex_hof_jp_item_chain as m

EXPECTED_HIT = 0x083DE02B
EXPECTED_KIND = 'rooted_jp_item_exchange_mail_minimum_text'
EXPECTED_PARENT_ID = {'size': 4594118, 'sha256': '0cca2c1d2d1ac7bb23c4d27727ed6470a54143bfa2908573be29455e62605c4f'}


# consumer実行を呼ばず、固定期待値から作る独立chain fixture。
EXPECTED_WITNESS = {'root_verified': True,
 'root_scope': 'two_separate_registered_conditional_item_roots',
 'classified_window': {'address': 138272811, 'size': 4},
 'boundary_parts': [{'address': 138272811, 'size': 3, 'role': '交換原文FC09とEOS'},
                    {'address': 138272814, 'size': 1, 'role': 'mailbox拒否文先頭glyph'}],
 'left_text': {'address': 138272790,
               'size': 24,
               'sha256': 'd5a7d3df2c8c59c7e85d5125c435550afc96daeb6b44b2cc5a22ea11a4ff3b49'},
 'right_text': {'address': 138272814,
                'size': 38,
                'sha256': '8bdd256110b1a1dd65ce82874e572d7e975f890595196fab3de96d77e2b678e9'},
 'exchange_entry': 135413976,
 'exchange_message': 135400776,
 'mailbox_entry': 135429392,
 'mailbox_callback': 135429436,
 'expand_entry': 134253384,
 'text_byte_reader': 134240270,
 'control_operand_reader': 134240374,
 'endpoint': 135400178,
 'input_contract': {'root_ja': '交換は登録前Task_SwitchItemsYesNoのtask0から実書込/RunTasks/Yes0/AddBagItem成功/新item2非mail。mailboxはChooseMonToGiveMailFromMailboxのaction7をconstructor/state20/同task/現hookで実選択する。自然到達は別義務。',
                    'names_ja': 'CopyItemNameの通常同期戻り条件はitem2→STR_VAR1のハイパーボール、item1→STR_VAR2のマスターボール。calleeの内部item '
                                'table読取は本scopeの証明外。これらを自動生成された名前と主張しない。',
                    'expansion_ja': '実DisplaySwitchedHeldItemMessageが原文083DE016とgStringVar4をBLへ渡す。FD03/FD02の実再帰、通常glyph/newline/FC09 '
                                    'copy/EOSを読み、原文と展開後RAMを別traceとする。',
                    'mailbox_ja': '非eggかつheld item1の条件。manager cursor0/itemsAbove0/saveblock1 '
                                  'pointerの有限有効値からmail位置を計算するが、拒否枝ではmail本体を読取/変更しない。',
                    'abi_ja': '各明示opaque siteは通常同期Thumb ABI復帰。r0-r3/r12/LR/flagsをUnknownへ破棄し、callee saved '
                              'register/SP/saved stackと必要future-live RAMだけを保持。効果全体とIRQは未証明。',
                    'printer_ja': '有効window6/font2/text '
                                  'speed255、printer開始時new/heldKeys0。FC09待機の正常戻り1を条件とし、展開後交換文とmailbox全38byteの実LDRBをEOSまで実行。',
                    'endpoint_ja': 'PartyMenuPrintTextからDisplayPartyMenuMessage内08120AF2へ戻った点で停止。API後半/各callback全体の正常復帰を主張しない。',
                    'lifetime_ja': '同party object '
                                   'epochが最後の参照まで有効、window6/font/展開先RAMは最終text読取まで有効。heap13352/保存退避/donor移管は別gate。'},
 'complete_original_and_expanded_reads': True,
 'pointer_host_seeded': False,
 'conditional_finite_type_only': True,
 'actual_runtime_execution_observed': False,
 'full_story_reachability_claimed': False,
 'opaque_callee_effects_proven': False,
 'universal_heap_or_irq_lifetime_proven': False,
 'indirect_reference_completeness_claimed': False,
 'donor_eligible': False,
 'donor_leased': False,
 'formal_rom_changed': False,
 'formal_save_changed': False}


def fixture():
    """chain層は型witnessを入力にする。旧/新consumerの実行を親読取へ混ぜない。"""
    region = m.d.TypedRegion(EXPECTED_HIT, EXPECTED_HIT + 4, EXPECTED_KIND,
                             copy.deepcopy(EXPECTED_WITNESS))
    proof = {'source_only_protocol': True, 'native_processes': 0,
             'old_full_rom_scan_runs': 0, 'donor_safe_bytes': 0,
             'actual_runtime_execution_observed': False,
             'formal_rom_changed': False, 'formal_save_changed': False}
    return [region], proof

@lru_cache(maxsize=1)
def recorded_parent():
    args = tuple((ROOT / path).read_bytes() for path in m.PARENT_INPUTS)
    # 保存JSON検証から外部processや旧caseへ逸脱しない。
    with patch('subprocess.Popen', side_effect=AssertionError('native禁止')), \
         patch.object(m.d, 'inventory', side_effect=AssertionError('全ROM scan禁止')), \
         patch.object(m.d, 'audit', side_effect=AssertionError('旧ROM audit禁止')), \
         patch.object(m.previous.consumer.stock, 'compose_selected', side_effect=AssertionError('旧max3禁止')), \
         patch.object(m.previous.consumer, 'compose_selected', side_effect=AssertionError('Flash再走禁止')), \
         patch.object(m.consumer, 'compose_selected', side_effect=AssertionError('新caseも親読取では禁止')):
        parent = m.parent(*args)
    return args, parent


class ItemChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args, cls.parent = recorded_parent()
        cls.regions, cls.proof = fixture()
        cls.delta = m.build(cls.parent, cls.regions, cls.proof)
        cls.full = m.materialize(cls.parent, cls.delta)
        cls.zero = m.build(cls.parent, [], {'source_only_protocol': True})

    def reject(self, delta):
        with self.assertRaises(ValueError):
            m.validate(self.parent, delta)

    def test_exact_parent_all_fields_and_counts(self):
        self.assertEqual(m.identity(m.canonical(self.parent)), m.PARENT_AUDIT_ID)
        self.assertEqual(m.PARENT_AUDIT_ID, EXPECTED_PARENT_ID)
        self.assertEqual((self.parent['classified'], self.parent['unclassified'], len(self.parent['hits'])), (780, 94, 874))
        self.assertEqual((len(m.INHERITED_NAMES), sum(len(self.parent[n]['changes']) for n in m.INHERITED_NAMES),
                          sum(len(self.parent[n]['witnesses']) for n in m.INHERITED_NAMES)), (27, 161, 151))

    def test_all53_input_identities_and_order(self):
        self.assertEqual(len(m.PARENT_INPUTS), 53)
        self.assertEqual(tuple(m.PARENT_INPUT_IDENTITIES), m.PARENT_INPUTS)
        self.assertEqual(m.PARENT_INPUTS[:-2], m.previous.PARENT_INPUTS)
        for path, raw in zip(m.PARENT_INPUTS, self.args):
            self.assertEqual(m.identity(raw), m.PARENT_INPUT_IDENTITIES[path])

    def test_each_input_mutation_fails_before_previous(self):
        for i in range(53):
            args = list(self.args)
            args[i] += b'\n'
            with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
                with self.assertRaises(ValueError):
                    m.parent(*args)

    def test_every_parent_lf_bytes_and_input_count(self):
        for i in range(53):
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
        prior = {'parent_audit': {'classified': 779}, 'baseline_audit': {'classified': 100}}
        with patch.object(m, 'parent', return_value=self.parent) as latest, \
             patch.object(m.previous, 'parent_audits', return_value=copy.deepcopy(prior)) as inherited:
            values = m.parent_audits(*self.args)
        latest.assert_called_once_with(*self.args)
        inherited.assert_called_once_with(*self.args[:-2])
        self.assertEqual(values['parent_audit'], self.parent)
        self.assertEqual(values['jp_field_parent'], prior['parent_audit'])
        self.assertEqual(values['baseline_audit'], prior['baseline_audit'])

    def test_only_one_hit_781_and93_with_closed_geometry(self):
        self.assertEqual(m.validate(self.parent, self.delta), 1)
        self.assertEqual((self.delta['classified'], self.delta['unclassified'], self.delta['newly_classified']), (781, 93, 1))
        self.assertEqual([r['address'] for r in self.delta['changes']], [EXPECTED_HIT])
        self.assertEqual([(r['address'], r['size'], r['kind']) for r in self.delta['witnesses']], [(m.HIT, 4, m.KIND)])
        self.assertEqual(m.witness_geometry(self.delta['witnesses'][0]), (m.HIT, 4))

    def test_independent_minimum_fixture_and_original_parent_identity(self):
        self.assertEqual((m.HIT, m.KIND), (EXPECTED_HIT, EXPECTED_KIND))
        self.assertEqual(m.PARENT_ID, {'size': 160664, 'sha256': '0539ee048ea49cf0f6b492f88325a89578c43182936d6910c19a7d3c9f5cf6cd'})
        self.assertEqual(m.PARENT_CHECKPOINT_ID, {'size': 4898, 'sha256': '664db2adae82b84cc23fef7965e5e301864c65dbee6a2186592a425772c1f113'})
        self.assertEqual(self.delta['proof'], self.proof)
        self.assertLess(len(m.canonical(self.delta)), m.MAX_DELTA_BYTES)

    def test_zero_delta_retains_every_original_field(self):
        full = m.materialize(self.parent, self.zero)
        self.assertEqual({k: v for k, v in full.items() if k != m.NAMESPACE}, self.parent)
        self.assertEqual((self.zero['changes'], self.zero['witnesses']), ([], []))
        self.assertEqual((self.zero['classified'], self.zero['unclassified'], self.zero['newly_classified']), (780, 94, 0))
        self.assertEqual(m.validate(self.parent, self.zero), 0)

    def test_old_accepted_and_remaining_unknown_rows_exact(self):
        for old, current in zip(self.parent['hits'], self.full['hits']):
            if old['address'] != m.HIT:
                self.assertEqual(old, current)
            else:
                self.assertFalse(old['accepted'])
                self.assertTrue(current['accepted'])
                self.assertEqual(current['evidence'], [{'jp_item_reference_chain_witness': 0}])
        self.assertEqual(len([h for h in self.full['hits'] if not h['accepted']]), 93)
        self.assertTrue(m.d.compare_inventory(self.full['hits'], self.parent)['same_inventory'])

    def test_all27_namespaces_and_source_fields_exact(self):
        for name in m.INHERITED_NAMES:
            self.assertEqual(self.full[name], self.parent[name])
        for key in self.parent:
            if key not in {'hits', 'classified', 'unclassified', 'classifications'}:
                self.assertEqual(self.full[key], self.parent[key])
        self.assertEqual(self.full['source_bindings'], self.parent['source_bindings'])

    def test_song133_models50_sample_identities_retained(self):
        song = self.parent[m.previous.previous.NAMESPACE]['proof']['song']
        self.assertEqual(song, self.full[m.previous.previous.NAMESPACE]['proof']['song'])
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
        for key, value in (('classified', 781), ('donor_leased', True), ('extra', 'invented'),
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
                'release_ready', 'formal_rom_changed', 'formal_save_changed',
                'source_pointer_host_seeded', 'actual_item_name_production_proven',
                'callee_effect_proven', 'effects_discharged', 'old_positive_profile_reexecuted',
                'universal_allocation_epoch_proven', 'all_opaque_effects_proven', 'irq_noninterference_proven')
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
                            ('size', [True, 4.0, 3, 5, 30]), ('kind', ['invented', m.previous.KIND])):
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

    def test_resealed_witness_container_aliases_rejected(self):
        class MappingAlias(dict):
            pass
        class ListAlias(list):
            pass
        values = (('boundary_parts', tuple(EXPECTED_WITNESS['boundary_parts'])),
                  ('boundary_parts', ListAlias(EXPECTED_WITNESS['boundary_parts'])),
                  ('classified_window', MappingAlias(EXPECTED_WITNESS['classified_window'])),
                  ('root_verified', 1))
        for key, value in values:
            delta = copy.deepcopy(self.delta)
            witness = delta['witnesses'][0]
            witness['evidence'][key] = value
            witness['evidence_identity'] = m.identity(m.canonical(witness['evidence']))
            with self.subTest(key=key, value=value):
                self.reject(delta)
        delta = copy.deepcopy(self.delta)
        delta['witnesses'][0]['evidence'] = MappingAlias(delta['witnesses'][0]['evidence'])
        self.reject(delta)

    def test_unregistered_old_kinds_and_registry_drift_rejected(self):
        for kind in ('invented', m.previous.KIND, 'registered_frontier_records_minimum_text_consumption'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                m.witness_geometry({'kind': kind, 'evidence': {}})
        with patch.object(m.consumer, 'KIND', 'changed'), self.assertRaises(ValueError):
            m.witness_geometry(self.delta['witnesses'][0])
        for hit in (m.HIT + 1, float(m.HIT), True):
            with self.subTest(hit=hit), patch.object(m.consumer, 'HIT', hit), self.assertRaises(ValueError):
                m.witness_geometry(self.delta['witnesses'][0])

    def test_build_rejects_duplicate_or_wider_regions(self):
        for regions in (self.regions * 2, [m.d.TypedRegion(m.HIT, m.HIT + 5, m.KIND, {})],
                        [m.d.TypedRegion(m.HIT - 1, m.HIT + 4, m.KIND, {})],
                        [m.d.TypedRegion(m.HIT, m.HIT + 4, 'invented', {})],
                        [m.d.TypedRegion(float(m.HIT), m.HIT + 4, m.KIND, {})],
                        [m.d.TypedRegion(m.HIT, float(m.HIT + 4), m.KIND, {})], None):
            with self.subTest(regions=regions), self.assertRaises(ValueError):
                m.build(self.parent, regions, self.proof)

    def test_parent_order_and_old779_substitution_rejected(self):
        swapped = list(self.args)
        swapped[-2], swapped[-1] = swapped[-1], swapped[-2]
        with patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
            with self.assertRaises(ValueError):
                m.parent(*swapped)
        with self.assertRaises(ValueError):
            m.build(m.previous.parent(*self.args[:-2]), self.regions, self.proof)

    def test_each_inherited_change_and_witness_count_exact(self):
        expected = ((25, 22), (17, 16), (33, 33), (29, 23), (3, 3), (2, 2), (1, 1),
                    (0, 0), (3, 3), (1, 1), (2, 2), (2, 2), (4, 4), (2, 2), (3, 3),
                    (3, 3), (2, 2), (2, 2), (3, 3), (5, 5), (2, 2), (3, 3), (5, 5),
                    (3, 3), (2, 2), (3, 3), (1, 1))
        self.assertEqual(tuple((len(self.parent[n]['changes']), len(self.parent[n]['witnesses']))
                               for n in m.INHERITED_NAMES), expected)

    def test_resealed_nested_safety_claim_and_evidence_identity_types(self):
        for container in ('proof', 'evidence'):
            delta = copy.deepcopy(self.delta)
            target = delta if container == 'proof' else delta['witnesses'][0]
            target[container]['nested'] = {'release_ready': True}
            target[container + '_identity'] = m.identity(m.canonical(target[container]))
            with self.subTest(container=container):
                self.reject(delta)
        for value in ({'size': True, 'sha256': 'a' * 64},
                      {'size': 1, 'sha256': 'A' * 64}, {'size': 1, 'sha256': 'a' * 64, 'extra': 1}):
            delta = copy.deepcopy(self.delta)
            delta['witnesses'][0]['evidence_identity'] = value
            self.reject(delta)

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
