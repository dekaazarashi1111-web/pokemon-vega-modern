"""Diploma chainの57保存親と閉じた4byte差分を検証。旧suite/ROM/nativeは呼ばない。"""
import copy
import sys
import unittest
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts')]
import pr16_dex_hof_diploma_chain as m

EXPECTED_HIT = 0x083DCAED
EXPECTED_KIND = 'rooted_diploma_lz10_minimum_asset'
EXPECTED_PARENT_ID = dict(size=5374525,
    sha256='3a311d6757418050acbbb2dc71ad93d9dfcc8fd63d7a52ba8782ad44d59ec3b7')
EXPECTED_CANDIDATE = dict(size=33554432,
    sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')

# chain単体のdependency contract。実ROM/source/decoderの受入fixtureではない。
# 独立consumerの実意味論はconsumer専用suiteで検証する。
CONTRACT_EVIDENCE = {
    'classified_window': {'address': EXPECTED_HIT, 'size': 4},
    'conditional_finite_type_only': True,
    'complete_asset_consumed': True,
    'actual_runtime_execution_observed': False,
    'donor_eligible': False,
    'donor_leased': False,
    'formal_rom_changed': False,
    'formal_save_changed': False,
}
CONTRACT_PROOF = {
    'status': 'CHAIN_DEPENDENCY_CONTRACT_FIXTURE_ONLY',
    'hit': EXPECTED_HIT,
    'newly_classified': 1,
    'donor_safe_bytes': 0,
    'native_processes': 0,
    'old_full_rom_scan_runs': 0,
    'conditional_finite_type_only': True,
    'actual_runtime_execution_observed': False,
}


def contract_consumer():
    def geometry(evidence):
        m.need(m.exact(evidence, CONTRACT_EVIDENCE), '独立fixture evidence全field')
        return EXPECTED_HIT, 4

    def scope(proof):
        m.need(m.exact(proof, CONTRACT_PROOF), '独立fixture scope全field')
        return True

    return SimpleNamespace(KIND=EXPECTED_KIND, HIT=EXPECTED_HIT,
        evidence_template=Mock(side_effect=lambda: copy.deepcopy(CONTRACT_EVIDENCE)),
        witness_geometry=Mock(side_effect=geometry), validate_scope_proof=Mock(side_effect=scope))


def fixture():
    return [m.d.TypedRegion(EXPECTED_HIT, EXPECTED_HIT + 4, EXPECTED_KIND,
                           copy.deepcopy(CONTRACT_EVIDENCE))], copy.deepcopy(CONTRACT_PROOF)


@lru_cache(maxsize=1)
def recorded_parent():
    args = tuple((ROOT / path).read_bytes() for path in m.PARENT_INPUTS)
    with patch('subprocess.Popen', side_effect=AssertionError('native禁止')), \
         patch.object(m.d, 'inventory', side_effect=AssertionError('全ROM scan禁止')), \
         patch.object(m.d, 'audit', side_effect=AssertionError('旧ROM audit禁止')), \
         patch.object(m.previous.consumer, 'compose_selected', side_effect=AssertionError('旧consumer再走禁止')), \
         patch.object(m, '_consumer', side_effect=AssertionError('新consumerも親読取では禁止')):
        parent = m.parent(*args)
    return args, parent


class DiplomaChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args, cls.parent = recorded_parent()
        cls.regions, cls.proof = fixture()
        with patch.object(m, '_consumer', return_value=contract_consumer()):
            cls.delta = m.build(cls.parent, cls.regions, cls.proof)
            cls.full = m.materialize(cls.parent, cls.delta)
            cls.zero = m.build(cls.parent, [], m.zero_proof_template())

    def setUp(self):
        self.consumer = contract_consumer()
        self.patcher = patch.object(m, '_consumer', return_value=self.consumer)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def reject(self, delta):
        with self.assertRaises(ValueError):
            m.validate(self.parent, delta)

    def changed(self, section, key, value):
        delta = copy.deepcopy(self.delta)
        target = delta if section is None else delta[section][0]
        target[key] = value
        return delta

    def test_exact_parent_identity_candidate_and_all_counts(self):
        self.assertEqual(m.PARENT_AUDIT_ID, EXPECTED_PARENT_ID)
        self.assertEqual(m.identity(m.canonical(self.parent)), EXPECTED_PARENT_ID)
        self.assertEqual(self.parent['candidate'], EXPECTED_CANDIDATE)
        self.assertEqual((self.parent['classified'], self.parent['unclassified'], len(self.parent['hits'])), (782, 92, 874))
        self.assertEqual((len(m.INHERITED_NAMES), sum(len(self.parent[n]['changes']) for n in m.INHERITED_NAMES),
                          sum(len(self.parent[n]['witnesses']) for n in m.INHERITED_NAMES)), (29, 163, 153))

    def test_parent_identity_registry_cannot_drift(self):
        changed = copy.deepcopy(self.parent)
        changed['candidate']['sha256'] = 'a' * 64
        with patch.object(m.credits, 'FULL_PARENT_ID', m.identity(m.canonical(changed))):
            with self.assertRaises(ValueError):
                m.validate_parent_state(changed)

    def test_all57_original_identities_and_order(self):
        self.assertEqual(len(m.PARENT_INPUTS), 57)
        self.assertEqual(m.PARENT_INPUTS, m.credits.INPUTS)
        self.assertEqual(tuple(m.PARENT_INPUT_IDENTITIES), m.PARENT_INPUTS)
        self.assertEqual(m.PARENT_INPUT_IDENTITIES, m.credits.INPUT_IDS)
        for path, raw in zip(m.PARENT_INPUTS, self.args):
            self.assertEqual(m.identity(raw), m.PARENT_INPUT_IDENTITIES[path])

    def test_parent_calls_saved57_restorer(self):
        with patch.object(m.credits, 'restore_parent', return_value=self.parent) as restore:
            self.assertIs(m.parent(*self.args), self.parent)
        restore.assert_called_once_with(*self.args)
        self.consumer.evidence_template.assert_not_called()
        self.consumer.validate_scope_proof.assert_not_called()

    def test_each_original_mutation_rejected_before_old_parent(self):
        for i in range(57):
            args = list(self.args)
            args[i] += b'\n'
            with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
                with self.assertRaises(ValueError):
                    m.parent(*args)

    def test_every_parent_input_lf_type_and_count(self):
        for i in range(57):
            for raw in (self.args[i].rstrip(b'\n'), self.args[i].replace(b'\n', b'\r\n'), bytearray(self.args[i])):
                args = list(self.args)
                args[i] = raw
                with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
                    with self.assertRaises(ValueError):
                        m.parent(*args)
        for args in (self.args[:-1], self.args + (b'{}\n',)):
            with self.assertRaises(ValueError):
                m.parent(*args)

    def test_swapped_parent_inputs_rejected(self):
        args = list(self.args)
        args[-2], args[-1] = args[-1], args[-2]
        with patch.object(m.previous, 'parent', side_effect=AssertionError('旧API到達禁止')):
            with self.assertRaises(ValueError):
                m.parent(*args)

    def test_unique_target_moves_782_92_to_783_91(self):
        self.assertEqual((m.HIT, m.KIND), (EXPECTED_HIT, EXPECTED_KIND))
        self.assertEqual(m.validate(self.parent, self.delta), 1)
        self.assertEqual((self.delta['classified'], self.delta['unclassified'], self.delta['newly_classified']), (783, 91, 1))
        self.assertEqual([r['address'] for r in self.delta['changes']], [EXPECTED_HIT])
        self.assertEqual([(r['address'], r['size'], r['kind']) for r in self.delta['witnesses']], [(EXPECTED_HIT, 4, EXPECTED_KIND)])
        self.assertEqual(m.witness_geometry(self.delta['witnesses'][0]), (EXPECTED_HIT, 4))

    def test_positive_binds_consumer_scope_and_independent_template(self):
        m.validate(self.parent, self.delta)
        self.consumer.validate_scope_proof.assert_called_once_with(self.proof)
        self.consumer.evidence_template.assert_called_once_with()
        self.consumer.witness_geometry.assert_called_once_with(CONTRACT_EVIDENCE)

    def test_scope_validator_cannot_silently_return_false_or_alias(self):
        for result in (False, None, 1, 1.0, {}, []):
            self.consumer.validate_scope_proof = Mock(return_value=result)
            with self.subTest(result=result):
                self.reject(self.delta)

    def test_positive_cannot_use_zero_or_self_declared_proof(self):
        for proof in (m.zero_proof_template(), {}, {'root_verified': True}, {'newly_classified': 1},
                      dict(self.proof, unknown_field=True)):
            delta = copy.deepcopy(self.delta)
            delta.update(proof=proof, proof_identity=m.identity(m.canonical(proof)))
            with self.subTest(proof=proof):
                self.reject(delta)

    def test_zero_preserves_every_original_field_without_consumer(self):
        with patch.object(m, '_consumer', side_effect=AssertionError('0件はconsumer不要')):
            full = m.materialize(self.parent, self.zero)
            self.assertEqual(m.validate(self.parent, self.zero), 0)
        self.assertEqual({k: v for k, v in full.items() if k != m.NAMESPACE}, self.parent)
        self.assertEqual((self.zero['changes'], self.zero['witnesses']), ([], []))
        self.assertEqual((self.zero['classified'], self.zero['unclassified'], self.zero['newly_classified']), (782, 92, 0))

    def test_zero_proof_is_closed_and_strict(self):
        for key in m.zero_proof_template():
            proof = m.zero_proof_template()
            del proof[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.build(self.parent, [], proof)
        for proof in ({}, self.proof, dict(m.zero_proof_template(), extra=False),
                      dict(m.zero_proof_template(), newly_classified=False)):
            with self.subTest(proof=proof), self.assertRaises(ValueError):
                m.build(self.parent, [], proof)

    def test_all29_namespaces_and_other873_rows_preserved(self):
        for name in m.INHERITED_NAMES:
            self.assertEqual(self.full[name], self.parent[name])
            self.assertIsNot(self.full[name], self.parent[name])
        other = [(old, new) for old, new in zip(self.parent['hits'], self.full['hits']) if old['address'] != EXPECTED_HIT]
        self.assertEqual(len(other), 873)
        self.assertTrue(all(m.exact(old, new) for old, new in other))
        self.assertTrue(m.d.compare_inventory(self.full['hits'], self.parent)['same_inventory'])

    def test_every_unaffected_top_field_preserved(self):
        for key, value in self.parent.items():
            if key not in ('hits', 'classified', 'unclassified', 'classifications'):
                self.assertTrue(m.exact(value, self.full[key]), key)
        self.assertEqual(self.full[m.NAMESPACE], self.delta)
        self.assertIsNot(self.full[m.NAMESPACE], self.delta)
        self.assertEqual(sum(self.full['classifications'].values()), 874)

    def test_build_and_materialize_never_mutate_inputs(self):
        args = m.canonical(self.parent), copy.deepcopy(self.regions), copy.deepcopy(self.proof), copy.deepcopy(self.delta)
        delta = m.build(self.parent, self.regions, self.proof)
        full = m.materialize(self.parent, delta)
        full[m.NAMESPACE]['proof']['status'] = 'changed'
        full['hits'][0]['accepted'] = not full['hits'][0]['accepted']
        self.assertEqual(m.canonical(self.parent), args[0])
        self.assertEqual((self.regions, self.proof, self.delta), args[1:])

    def test_tampered_parent_count_source_namespace_and_target_rejected(self):
        for modify in (
            lambda p: p.update(classified=783),
            lambda p: p['candidate'].update(sha256='0' * 64),
            lambda p: p[m.INHERITED_NAMES[-1]].update(extra=True),
            lambda p: p['hits'][0].update(accepted=not p['hits'][0]['accepted']),
            lambda p: p.update(donor_leased=True),
            lambda p: p.update({m.NAMESPACE: {}}),
        ):
            parent = copy.deepcopy(self.parent)
            modify(parent)
            with self.assertRaises(ValueError):
                m.build(parent, self.regions, self.proof)

    def test_parent_container_aliases_rejected_even_with_same_canonical_bytes(self):
        class MappingAlias(dict):
            pass
        for parent in (MappingAlias(self.parent), dict(self.parent, hits=tuple(self.parent['hits']))):
            self.assertEqual(m.canonical(parent), m.canonical(self.parent))
            with self.assertRaises(ValueError):
                m.validate_parent_state(parent)

    def test_top_schema_no_missing_or_extra(self):
        for key in self.delta:
            delta = copy.deepcopy(self.delta)
            del delta[key]
            with self.subTest(key=key):
                self.reject(delta)
        self.reject(dict(self.delta, extra=True))

    def test_status_version_and_integer_counters(self):
        for key, values in (
            ('status', ['PASS', 1]), ('schema_version', [True, 1.0, 0, 2]),
            ('inherited_candidates', [True, 874.0, 873]), ('inherited_classified', [781, 783]),
            ('inherited_unclassified', [91, 93]), ('classified', [782, 784, 783.0]),
            ('unclassified', [90, 92, 91.0]), ('newly_classified', [True, 1.0, 0, 2]),
            ('native_processes', [True, 0.0, 1]), ('old_full_rom_scan_runs', [False, 0.0, 1]),
            ('donor_safe_bytes', [False, 0.0, -1, 4]),
        ):
            for value in values:
                with self.subTest(key=key, value=value):
                    self.reject(dict(self.delta, **{key: value}))

    def test_all_flags_must_stay_boolean_false(self):
        for key in (*m.FLAGS, *m.BATCH_FLAGS):
            for value in (True, 0, 0.0, None):
                with self.subTest(key=key, value=value):
                    self.reject(dict(self.delta, **{key: value}))

    def test_baseline_parent_candidate_exact_identity(self):
        for key in ('baseline', 'parent', 'candidate'):
            for value in ({}, dict(self.delta[key], extra=True), dict(self.delta[key], size=True),
                          dict(self.delta[key], sha256='a' * 64)):
                with self.subTest(key=key):
                    self.reject(dict(self.delta, **{key: value}))

    def test_changes_witnesses_strict_lists_same_length_and_at_most_one(self):
        for key in ('changes', 'witnesses'):
            for value in ((), {}, None, self.delta[key] * 2, []):
                with self.subTest(key=key):
                    self.reject(dict(self.delta, **{key: value}))

    def test_every_change_and_witness_field_required_no_extra(self):
        for section in ('changes', 'witnesses'):
            for key in self.delta[section][0]:
                delta = copy.deepcopy(self.delta)
                del delta[section][0][key]
                with self.subTest(section=section, key=key):
                    self.reject(delta)
            self.reject(self.changed(section, 'extra', True))

    def test_existing_hit_identity_cannot_change(self):
        for key in m.FIELDS:
            for value in (None, True, 0.0, 'changed'):
                with self.subTest(key=key, value=value):
                    self.reject(self.changed('changes', key, value))

    def test_other_unknown_and_accepted_cannot_be_promoted(self):
        for accepted in (False, True):
            old = next(h for h in self.parent['hits'] if h['accepted'] is accepted and h['address'] != EXPECTED_HIT)
            delta = copy.deepcopy(self.delta)
            delta['changes'][0].update({k: old[k] for k in m.FIELDS})
            self.reject(delta)

    def test_change_classification_and_witness_reference_strict(self):
        for key, value in (('accepted', 1), ('accepted', False), ('classification', 'DATA'),
                           ('witness_ids', [True]), ('witness_ids', [0.0]), ('witness_ids', []),
                           ('witness_ids', [1]), ('witness_ids', [0, 0]), ('witness_ids', (0,))):
            with self.subTest(key=key, value=value):
                self.reject(self.changed('changes', key, value))

    def test_witness_id_address_size_kind_strict(self):
        for key, values in (('id', [True, 0.0, 1]), ('address', [EXPECTED_HIT - 1, EXPECTED_HIT + 1, float(EXPECTED_HIT)]),
                            ('size', [True, 4.0, 0, 3, 5, 3366]), ('kind', ['invented', m.previous.KIND])):
            for value in values:
                with self.subTest(key=key, value=value):
                    self.reject(self.changed('witnesses', key, value))

    def test_each_evidence_field_required_and_no_extra_after_reseal(self):
        for key in CONTRACT_EVIDENCE:
            delta = copy.deepcopy(self.delta)
            row = delta['witnesses'][0]
            del row['evidence'][key]
            row['evidence_identity'] = m.identity(m.canonical(row['evidence']))
            with self.subTest(key=key):
                self.reject(delta)
        delta = copy.deepcopy(self.delta)
        row = delta['witnesses'][0]
        row['evidence']['extra'] = True
        row['evidence_identity'] = m.identity(m.canonical(row['evidence']))
        self.reject(delta)

    def test_independent_template_check_even_if_consumer_geometry_lies(self):
        delta = copy.deepcopy(self.delta)
        row = delta['witnesses'][0]
        row['evidence'] = {'classified_window': {'address': EXPECTED_HIT, 'size': 4}, 'root_verified': True}
        row['evidence_identity'] = m.identity(m.canonical(row['evidence']))
        self.consumer.witness_geometry = Mock(return_value=(EXPECTED_HIT, 4))
        self.reject(delta)
        self.consumer.witness_geometry.assert_not_called()

    def test_consumer_geometry_cannot_be_partial_wider_shifted_or_alias(self):
        for geometry in ((EXPECTED_HIT, 4.0), (EXPECTED_HIT, True), (EXPECTED_HIT, 3), (EXPECTED_HIT, 5),
                         (EXPECTED_HIT - 1, 4), (EXPECTED_HIT,), None):
            self.consumer.witness_geometry = Mock(return_value=geometry)
            with self.subTest(geometry=geometry):
                self.reject(self.delta)

    def test_unregistered_kind_and_registry_drift_rejected(self):
        for kind in ('invented', m.previous.KIND, 'rooted_diploma_lz10'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                m.witness_geometry({'kind': kind, 'evidence': CONTRACT_EVIDENCE})
        for attr, value in (('KIND', 'changed'), ('HIT', EXPECTED_HIT + 1), ('HIT', float(EXPECTED_HIT)), ('HIT', True)):
            with patch.object(self.consumer, attr, value), self.assertRaises(ValueError):
                m.witness_geometry(self.delta['witnesses'][0])

    def test_build_rejects_duplicate_partial_wider_and_foreign_regions(self):
        for regions in (self.regions * 2, [m.d.TypedRegion(EXPECTED_HIT, EXPECTED_HIT + 3, EXPECTED_KIND, CONTRACT_EVIDENCE)],
                        [m.d.TypedRegion(EXPECTED_HIT, EXPECTED_HIT + 5, EXPECTED_KIND, CONTRACT_EVIDENCE)],
                        [m.d.TypedRegion(EXPECTED_HIT - 1, EXPECTED_HIT + 4, EXPECTED_KIND, CONTRACT_EVIDENCE)],
                        [m.d.TypedRegion(EXPECTED_HIT, EXPECTED_HIT + 4, 'invented', CONTRACT_EVIDENCE)],
                        [m.d.TypedRegion(float(EXPECTED_HIT), EXPECTED_HIT + 4, EXPECTED_KIND, CONTRACT_EVIDENCE)],
                        [m.d.TypedRegion(EXPECTED_HIT, float(EXPECTED_HIT + 4), EXPECTED_KIND, CONTRACT_EVIDENCE)], None):
            with self.subTest(regions=regions), self.assertRaises(ValueError):
                m.build(self.parent, regions, self.proof)

    def test_proof_and_witness_identity_must_match(self):
        for section, name in ((None, 'proof'), ('witnesses', 'evidence')):
            delta = copy.deepcopy(self.delta)
            target = delta if section is None else delta[section][0]
            target[name]['extra'] = True
            self.reject(delta)

    def test_identity_schema_integer_size_lowercase_hash_and_no_extra(self):
        for value in ({'size': True, 'sha256': 'a' * 64}, {'size': 1.0, 'sha256': 'a' * 64},
                      {'size': 1, 'sha256': 'A' * 64}, {'size': 1, 'sha256': 'a' * 64, 'extra': 1},
                      {'size': -1, 'sha256': 'a' * 64}, {'size': 1, 'sha256': 'z' * 64}):
            self.assertFalse(m.valid_identity(value))
            self.reject(dict(self.delta, proof_identity=value))
            self.reject(self.changed('witnesses', 'evidence_identity', value))

    def test_no_nested_safety_execution_or_donor_promotion(self):
        for key in ('release_ready', 'donor_leased', 'donor_eligible', 'formal_rom_changed', 'formal_save_changed',
                    'indirect_reference_completeness_claimed', 'opaque_callee_effects_proven',
                    'natural_play_universal_reachability_claimed', 'universal_irq_or_heap_lifetime_claimed',
                    'existing_execution_replayed', 'effects_discharged', 'irq_noninterference_proven'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_restricted_proof({'nested': [{key: True}]})
        for key in ('donor_safe_bytes', 'safe_donor_bytes', 'old_full_rom_scan_runs', 'native_processes', 'rom_writes', 'save_writes'):
            for value in (1, True, 0.0):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    m.validate_restricted_proof({'nested': {key: value}})

    def test_no_parent_namespace_or_inventory_copy(self):
        for key in (*m.INHERITED_NAMES, m.NAMESPACE, 'baseline_audit', 'parent_audit', 'inherited_audit'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_restricted_proof({'nested': {key: {}}})
        with self.assertRaises(ValueError):
            m.validate_restricted_proof({'nested': {'hits': [], 'candidate': {}}})

    def test_nested_container_aliases_integer_keys_and_nonfinite_rejected(self):
        class MappingAlias(dict):
            pass
        class ListAlias(list):
            pass
        class IntAlias(int):
            pass
        for value in (MappingAlias(release_ready=False), ListAlias([1]), (1,), {1: 'key'}, set(),
                      IntAlias(0), float('nan'), float('inf'), float('-inf'), 0.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.validate_restricted_proof({'nested': value})

    def test_resealed_evidence_boolean_and_integer_alias_rejected(self):
        for key, value in (('conditional_finite_type_only', 1), ('actual_runtime_execution_observed', 0),
                           ('classified_window', {'address': EXPECTED_HIT, 'size': 4.0})):
            delta = copy.deepcopy(self.delta)
            row = delta['witnesses'][0]
            row['evidence'][key] = value
            row['evidence_identity'] = m.identity(m.canonical(row['evidence']))
            self.reject(delta)

    def test_measured_roundtrip_binds_external_full_byte_identity(self):
        raw = m.canonical(self.delta)
        measured = m.read_measured(raw, m.identity(raw), self.parent)
        self.assertEqual(measured, self.delta)
        self.assertEqual(m.canonical(measured), raw)
        for changed in (raw + b'\n', raw.rstrip(b'\n'), raw.replace(b'\n', b'\r\n'), bytearray(raw)):
            with self.assertRaises(ValueError):
                m.read_measured(changed, m.identity(raw), self.parent)
        with self.assertRaises(ValueError):
            m.read_measured(raw, dict(m.identity(raw), extra=True), self.parent)

    def test_measured_duplicate_top_and_nested_keys_rejected_after_reseal(self):
        raw = m.canonical(self.delta)
        nested = b'"conditional_finite_type_only":true'
        self.assertIn(nested, raw)
        for changed in (raw.replace(b'{', b'{"schema_version":1,', 1),
                        raw.replace(nested, nested + b',' + nested, 1)):
            with self.assertRaises(ValueError):
                m.read_measured(changed, m.identity(changed), self.parent)

    def test_measured_json_nonfinite_constants_rejected_after_reseal(self):
        raw = m.canonical(self.delta)
        for token in (b'NaN', b'Infinity', b'-Infinity'):
            changed = raw.replace(b'"native_processes":0', b'"native_processes":' + token, 1)
            with self.subTest(token=token), self.assertRaises(ValueError):
                m.read_measured(changed, m.identity(changed), self.parent)

    def test_measured_unknown_fields_still_rejected_with_new_full_identity(self):
        raw = m.canonical(dict(self.delta, extra=1))
        with self.assertRaises(ValueError):
            m.read_measured(raw, m.identity(raw), self.parent)

    def test_bounded_delta_before_materialization(self):
        raw = m.canonical(self.delta)
        with patch.object(m, 'MAX_DELTA_BYTES', len(raw) - 1):
            self.reject(self.delta)
            with self.assertRaises(ValueError):
                m.read_measured(raw, m.identity(raw), self.parent)

    def test_parent_original_files_remain_identical(self):
        for path, original in zip(m.PARENT_INPUTS, self.args):
            self.assertEqual((ROOT / path).read_bytes(), original)


class DiplomaConsumerBindingTests(unittest.TestCase):
    def test_saved_independent_proof_and_real_consumer_roundtrip(self):
        """保存source証明の再照合だけ。consumer/ROM/nativeを再実行しない。"""
        import pr16_dex_hof_diploma_asset as consumer
        _, parent = recorded_parent()
        raw = (ROOT / consumer.PROOF_PATH).read_bytes()
        self.assertEqual(m.identity(raw), consumer.PROOF_ID)
        proof = m.credits.load(raw)
        region = m.d.TypedRegion(EXPECTED_HIT, EXPECTED_HIT + 4, EXPECTED_KIND,
                                 consumer.evidence_template())
        with patch.object(consumer, 'compose', side_effect=AssertionError('consumer再走禁止')), \
             patch.object(consumer, 'regions', side_effect=AssertionError('ROM計測禁止')), \
             patch('subprocess.Popen', side_effect=AssertionError('native禁止')):
            delta = m.build(parent, [region], proof)
            measured = m.read_measured(m.canonical(delta), m.identity(m.canonical(delta)), parent)
            full = m.materialize(parent, measured)
        self.assertEqual(delta, measured)
        self.assertEqual((full['classified'], full['unclassified'], len(full['hits'])), (783, 91, 874))
        self.assertEqual(delta['proof_identity'], consumer.PROOF_ID)
        self.assertEqual([h['address'] for h, old in zip(full['hits'], parent['hits']) if h != old], [EXPECTED_HIT])
        self.assertTrue(all(m.exact(full[n], parent[n]) for n in m.INHERITED_NAMES))
        self.__class__.measured_delta_identity = m.identity(m.canonical(delta))
        self.__class__.materialized_identity = m.identity(m.canonical(full))


if __name__ == '__main__':
    unittest.main()
