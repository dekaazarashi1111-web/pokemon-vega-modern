"""741親・十三旧namespaceの保持とHelp専用delta境界だけを反証する。"""
import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_dex_hof_help_batch_chain as m

ROOT = Path(__file__).resolve().parents[1]
KIND = 'rooted_help_context_topic_minimum_ids'
MODULE = 'pr16_dex_hof_help_roots'
HELP = (0x0841B41A, 0x0841B44C)
PADDING = (0x083E239B, 0x083E24C3, 0x083E2563, 0x083E258F)


class SyntheticChainTests(unittest.TestCase):
    """型validatorの中身でなくchain接続を合成fixtureで検査する。"""
    def setUp(self):
        self.audit = dict(candidate=dict(size=64, sha256='synthetic'),
            hits=[dict(address=100 + i * 4, target=200, kind='SYNTHETIC', size=4,
                       sha256=str(i), accepted=i == 0,
                       classification='ACCEPTED' if i == 0 else 'UNCLASSIFIED',
                       evidence=['keep'] if i == 0 else [], extra={'keep': i}) for i in range(4)],
            classified=1, unclassified=3, candidates=4,
            donor_leased=False, donor_eligible=False, indirect_reference_completeness_claimed=False,
            **{name: {'retained': name} for name in m.INHERITED_NAMES})
        self.start_patch = patch.dict(m.PARENT_AUDIT_ID, m.identity(m.canonical(self.audit)))
        self.start_patch.start()
        self.addCleanup(self.start_patch.stop)
        self.geometry = Mock(side_effect=lambda evidence: (evidence['address'], evidence['size']))
        module = SimpleNamespace(KIND=KIND, witness_geometry=self.geometry)
        self.module_patch = patch.dict(sys.modules, {MODULE: module})
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)
        self.evidence = {'address': 104, 'size': 8, 'synthetic_protocol_only': True}
        self.regions = [m.d.TypedRegion(104, 112, KIND, self.evidence)]
        self.delta = m.build(self.audit, self.regions, {})

    def reject(self, mutate):
        delta = copy.deepcopy(self.delta)
        mutate(delta)
        with self.assertRaises(ValueError):
            m.validate(self.audit, delta)

    def test_complete_old_namespaces_and_new_namespace(self):
        full = m.materialize(self.audit, self.delta)
        for name in m.INHERITED_NAMES:
            self.assertEqual(full[name], self.audit[name])
        self.assertEqual(full[m.NAMESPACE], self.delta)
        self.assertEqual(set(full) - set(self.audit), {m.NAMESPACE, 'classifications'})

    def test_accepted_and_remaining_unknown_all_fields(self):
        before = copy.deepcopy(self.audit)
        full = m.materialize(self.audit, self.delta)
        self.assertEqual(self.audit, before)
        self.assertEqual(full['hits'][0], before['hits'][0])
        self.assertEqual(full['hits'][3], before['hits'][3])
        self.assertEqual(full['hits'][1]['evidence'], [{'help_batch_reference_chain_witness': 0}])

    def test_shared_complete_witness_is_not_duplicated(self):
        self.assertEqual(len(self.delta['witnesses']), 1)
        self.assertEqual(self.delta['newly_classified'], 2)
        self.assertNotIn('hits', self.delta)
        self.assertNotIn('inherited_audit', self.delta)

    def test_no_fixed_new_classification_count(self):
        for regions, count in (([], 0), ([m.d.TypedRegion(104, 108, KIND, {'address': 104, 'size': 4})], 1), (self.regions, 2)):
            delta = m.build(self.audit, regions, {})
            self.assertEqual(delta['newly_classified'], count)
            self.assertEqual(delta['unclassified'], 3 - count)

    def test_zero_delta_keeps_every_old_row(self):
        delta = m.build(self.audit, [], {'diagnostic_only': True})
        self.assertEqual(m.materialize(self.audit, delta)['hits'], self.audit['hits'])
        self.assertEqual(delta['witnesses'], [])

    def test_every_parent_field_is_bound_before_build(self):
        for mutate in (lambda a: a['hits'][0].update(evidence=[]),
                       lambda a: a['hits'][-1].update(extra={}),
                       lambda a: a.update(classified=0),
                       lambda a: a.update(classifications={'fabricated': 4}),
                       lambda a: a.update(controller_runtime_wired=True),
                       lambda a: a['reference_delta'].update(retained='changed')):
            audit = copy.deepcopy(self.audit)
            mutate(audit)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.build(audit, [], {})

    def test_every_parent_field_is_bound_before_validate(self):
        audit = copy.deepcopy(self.audit)
        audit['hits'][0]['evidence'] = []
        with self.assertRaises(ValueError):
            m.validate(audit, self.delta)

    def test_parent_path_and_hash(self):
        for key, value in (('path', m.EARLIER), ('sha256', 'bad'), ('size', 1)):
            self.reject(lambda delta, k=key, v=value: delta['parent'].update({k: v}))

    def test_baseline_identity(self):
        self.reject(lambda delta: delta['baseline'].update(sha256='bad'))

    def test_identity_envelopes_reject_numeric_aliases(self):
        for container in ('baseline', 'parent', 'candidate', 'proof_identity'):
            self.reject(lambda delta, key=container: delta[key].update(size=float(delta[key]['size'])))
        self.reject(lambda delta: delta['witnesses'][0]['evidence_identity'].update(size=float(delta['witnesses'][0]['evidence_identity']['size'])))
        raw = m.canonical(self.delta)
        measured = m.identity(raw)
        measured['size'] = float(measured['size'])
        with self.assertRaises(ValueError):
            m.read_measured(raw, measured, self.audit)

    def test_malformed_change_or_witness_mapping_is_rejected(self):
        for field in ('changes', 'witnesses'):
            for value in (None, {}, {'address': 104}):
                self.reject(lambda delta, key=field, row=value: delta.update({key: [row]}))

    def test_candidate_identity(self):
        self.reject(lambda delta: delta.update(candidate={}))

    def test_closed_delta_schema(self):
        self.reject(lambda delta: delta.update(inherited_audit=self.audit))
        self.reject(lambda delta: delta.pop('proof_identity'))

    def test_old_delta_status_cannot_substitute(self):
        self.reject(lambda delta: delta.update(status='PASS_737_PARENT_BOUND_REMAINING_CONSUMERS_REFERENCE_CHAIN'))

    def test_lease_runtime_and_universal_claims_cannot_promote(self):
        for flag in (*m.FLAGS, *m.BATCH_FLAGS):
            for value in (True, 0, None):
                with self.subTest(flag=flag, value=value):
                    self.reject(lambda delta, k=flag, v=value: delta.update({k: v}))

    def test_execution_and_safe_capacity_counters_stay_zero(self):
        for key in ('old_full_rom_scan_runs', 'native_processes', 'donor_safe_bytes'):
            self.reject(lambda delta, k=key: delta.update({k: 1}))

    def test_all_counter_types_are_strict(self):
        for key in ('inherited_candidates', 'inherited_classified', 'inherited_unclassified', 'classified',
                    'unclassified', 'newly_classified', 'old_full_rom_scan_runs', 'native_processes', 'donor_safe_bytes'):
            for value in (False, float(self.delta[key]), -1):
                with self.subTest(key=key, value=value):
                    self.reject(lambda delta, k=key, v=value: delta.update({k: v}))

    def test_nested_proof_cannot_promote_universal_claims(self):
        for key in (*m.FLAGS, *m.BATCH_FLAGS, 'universal_heap_or_irq_lifetime_claimed',
                    'natural_gameplay_reachability_claimed', 'full_story_reachability_claimed',
                    'natural_screen_context_invocation_proven', 'actual_runtime_execution_observed',
                    'independent_old_final_source_review_completed', 'maximum_target_access_width_proven',
                    'whole_id_tables_classified', 'padding_classified', 'source_pointer_interpretation',
                    'universal_heap_or_irq_lifetime_proven',
                    'universal_irq_or_heap_lifetime_proven', 'full_lifetime_proven', 'heap_lifetime_proven',
                    'stock_save_boundary_crossing_allowed', 'safe_to_lease', 'lease_authorized', 'lease_eligible'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.build(self.audit, [], {'nested': [{'proof': {key: True}}]})

    def test_nested_proof_cannot_promote_safe_bytes(self):
        for key in ('donor_safe_bytes', 'safe_donor_bytes'):
            for value in (1, False, 0.0):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    m.build(self.audit, [], {'nested': {key: value}})

    def test_old_originals_are_referenced_not_duplicated(self):
        for key in (*m.INHERITED_NAMES, 'baseline_audit', 'parent_audit', 'inherited_audit'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.build(self.audit, [], {'nested': {key: {'copied': True}}})
        with self.assertRaises(ValueError):
            m.build(self.audit, [], {'copied': self.audit})

    def test_proof_must_be_mapping_and_finite(self):
        for proof in (None, [], {'value': float('nan')}, {'value': float('inf')}):
            with self.subTest(proof=proof), self.assertRaises(ValueError):
                m.build(self.audit, [], proof)

    def test_unknown_and_legacy_kinds_cannot_classify_new_batch(self):
        for kind in ('invented', 'zlib_serialized_archive', 'rooted_rfu_parent_disconnect_minimum_thumb'):
            self.reject(lambda delta, k=kind: delta['witnesses'][0].update(kind=k))

    def test_registered_dedicated_geometry_and_kind_contract(self):
        self.assertEqual(m.NEW_KIND_MODULES, {KIND: MODULE})
        module = SimpleNamespace(KIND='another', witness_geometry=Mock())
        with patch.dict(sys.modules, {MODULE: module}), self.assertRaises(ValueError):
            m.witness_geometry({'kind': KIND, 'evidence': {}})
        module.witness_geometry.assert_not_called()

    def test_declared_kind_collection_cannot_be_string(self):
        module = SimpleNamespace(KINDS=KIND + '_suffix', witness_geometry=Mock())
        with patch.dict(sys.modules, {MODULE: module}), self.assertRaises(ValueError):
            m.witness_geometry({'kind': KIND, 'evidence': {}})

    def test_validator_failure_and_missing_import_never_fall_back(self):
        with patch.object(m.importlib, 'import_module', side_effect=ModuleNotFoundError('missing')), self.assertRaises(ModuleNotFoundError):
            m.witness_geometry({'kind': KIND, 'evidence': {}})
        self.geometry.side_effect = ValueError('incomplete root')
        with self.assertRaisesRegex(ValueError, 'incomplete root'):
            m.validate(self.audit, self.delta)

    def test_zero_diagnostic_does_not_import_new_module(self):
        with patch.object(m.importlib, 'import_module', side_effect=AssertionError('unexpected import')):
            m.build(self.audit, [], {})

    def test_whole_hit_containment_not_partial_union(self):
        regions = [m.d.TypedRegion(104, 106, KIND, {}), m.d.TypedRegion(106, 108, KIND, {})]
        self.assertEqual(m.build(self.audit, regions, {})['newly_classified'], 0)

    def test_conflicting_types_stay_unknown(self):
        delta = m.build(self.audit, self.regions + [m.d.TypedRegion(108, 112, 'conflict', {})], {})
        self.assertEqual(delta['newly_classified'], 1)

    def test_geometry_cannot_shrink_or_expand(self):
        for address, size in ((104, 4), (102, 10)):
            region = m.d.TypedRegion(address, address + size, KIND, self.evidence)
            with self.subTest(address=address), self.assertRaises(ValueError):
                m.build(self.audit, [region], {})

    def test_witness_and_change_identities_are_strict(self):
        for key in ('address', 'target', 'size'):
            self.reject(lambda delta, k=key: delta['changes'][0].update({k: float(delta['changes'][0][k])}))
        for key in ('address', 'size', 'id'):
            self.reject(lambda delta, k=key: delta['witnesses'][0].update({k: float(delta['witnesses'][0][k])}))
        self.reject(lambda delta: delta['changes'][0].update(sha256='changed'))
        self.reject(lambda delta: delta['witnesses'][0]['evidence'].update(size=9))

    def test_accepted_row_cannot_rewrite(self):
        self.reject(lambda delta: delta['changes'][0].update(**{k: self.audit['hits'][0][k] for k in m.FIELDS}))

    def test_inventory_change_order_is_fixed(self):
        self.reject(lambda delta: delta['changes'].reverse())
        self.reject(lambda delta: delta['changes'].append(copy.deepcopy(delta['changes'][0])))

    def test_witness_references_are_canonical(self):
        for ids in ([], [True], [0, 0], [1], '0'):
            self.reject(lambda delta, value=ids: delta['changes'][0].update(witness_ids=value))

    def test_classification_is_derived_from_kind(self):
        self.reject(lambda delta: delta['changes'][0].update(classification='SAFE_DONOR'))

    def test_no_unused_duplicate_witness(self):
        def mutate(delta):
            row = copy.deepcopy(delta['witnesses'][0])
            row['id'] = 1
            delta['witnesses'].append(row)
        self.reject(mutate)

    def test_zero_changes_cannot_claim_new_rows(self):
        delta = m.build(self.audit, [], {})
        delta['newly_classified'] = 2
        with self.assertRaises(ValueError):
            m.validate(self.audit, delta)

    def test_entire_measured_envelope_and_lf(self):
        raw = m.canonical(self.delta)
        self.assertEqual(m.read_measured(raw, m.identity(raw), self.audit), self.delta)
        for changed in (raw + b' ', raw[:-1], raw.replace(b'\n', b'\r\n'), raw.replace(b'{', b'{\r', 1)):
            with self.subTest(identity=m.identity(changed)), self.assertRaises(ValueError):
                m.read_measured(changed, m.identity(changed), self.audit)

    def test_independent_measurement_is_not_self_hash(self):
        raw = m.canonical(self.delta)
        changed = copy.deepcopy(self.delta)
        changed['proof'] = {'changed': True}
        changed['proof_identity'] = m.identity(m.canonical(changed['proof']))
        with self.assertRaises(ValueError):
            m.read_measured(m.canonical(changed), m.identity(raw), self.audit)

    def test_delta_is_bounded(self):
        with self.assertRaises(ValueError):
            m.build(self.audit, [], {'diagnostic': 'x' * m.MAX_DELTA_BYTES})

    def test_build_and_materialize_have_no_mutable_aliases(self):
        proof = {'nested': []}
        delta = m.build(self.audit, self.regions, proof)
        proof['nested'].append('later')
        self.evidence['later'] = True
        self.assertEqual(delta['proof'], {'nested': []})
        self.assertNotIn('later', delta['witnesses'][0]['evidence'])
        full = m.materialize(self.audit, delta)
        full[m.NAMESPACE]['proof']['nested'].append('changed')
        self.assertEqual(delta['proof'], {'nested': []})

    def test_full_materialization_rejects_changed_classifications_or_extras(self):
        for mutate in (lambda full: full['classifications'].update(SAFE_DONOR=1),
                       lambda full: full.update(controller_runtime_wired=True),
                       lambda full: full.update(donor_safe_bytes=15118),
                       lambda full: full['hits'][0].update(evidence=[]),
                       lambda full: full.update(classified=float(full['classified']))):
            full = m.materialize(self.audit, self.delta)
            mutate(full)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.validate_materialized(self.audit, full)

    def test_full_materialization_requires_delta(self):
        full = m.materialize(self.audit, self.delta)
        del full[m.NAMESPACE]
        with self.assertRaises(ValueError):
            m.validate_materialized(self.audit, full)
        self.assertEqual(m.validate_materialized(self.audit, self.audit), self.audit)


class RecordedParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = [(ROOT / path).read_bytes() for path in m.PARENT_INPUTS]
        cls.parents = m.parent_audits(*cls.args)
        cls.parent = cls.parents['parent_audit']

    def test_exact741_independent_parent_identity(self):
        self.assertEqual(m.identity(m.canonical(self.parent)), m.PARENT_AUDIT_ID)
        self.assertEqual((self.parent['classified'], self.parent['unclassified']), (741, 133))
        self.assertEqual(len(self.parent['hits']), 874)

    def test_twenty_five_full_parent_inputs_and_no_count_alias(self):
        self.assertEqual(len(m.PARENT_INPUTS), 25)
        for args in (self.args[:-1], self.args + [b'extra\n']):
            with self.assertRaises(ValueError):
                m.parent(*args)

    def test_every_parent_input_is_whole_bound(self):
        for index in range(len(self.args)):
            args = self.args.copy()
            args[index] += b'\n'
            with self.subTest(index=index), self.assertRaises(ValueError):
                m.parent(*args)

    def test_parent_checkpoint_is_independent(self):
        args = self.args.copy()
        checkpoint = json.loads(args[-1])
        checkpoint['delta_identity'] = m.identity(args[2])
        args[-1] = m.canonical(checkpoint)
        with self.assertRaises(ValueError):
            m.parent(*args)

    def test_parent_cannot_substitute_earlier_delta(self):
        args = self.args.copy()
        args[-2] = args[-4]
        with self.assertRaises(ValueError):
            m.parent(*args)

    def test_all13_namespaces_122_changes112_witnesses(self):
        self.assertEqual(len(m.INHERITED_NAMES), 13)
        self.assertEqual(sum(len(self.parent[name]['changes']) for name in m.INHERITED_NAMES), 122)
        self.assertEqual(sum(len(self.parent[name]['witnesses']) for name in m.INHERITED_NAMES), 112)
        old = self.parents['remaining_consumers_parent']
        for name in m.previous.INHERITED_NAMES:
            self.assertEqual(self.parent[name], old[name])
        for before, after in zip(old['hits'], self.parent['hits']):
            self.assertEqual({k: before[k] for k in m.FIELDS}, {k: after[k] for k in m.FIELDS})
            if before['accepted'] or not after['accepted']:
                self.assertEqual(before, after)

    def test_all133_song_models_and50_assets_retained(self):
        song = self.parent['remaining_consumers_reference_chain']['proof']['song']
        self.assertEqual((song['combined_song_models'], song['retained_sample_witnesses']), (133, 50))
        self.assertTrue(song['all133_models_exact'])
        self.assertTrue(song['all50_sample_identities_exact'])

    def test_explicit_parent_names_preserve_equal_counter_ancestors(self):
        expected = {'parent_audit': (741, 133), 'remaining_consumers_parent': (737, 137),
            'summary_parent': (735, 139), 'party_parent': (733, 141), 'boundary_parent': (732, 142),
            'runtime_parent': (729, 145), 'lifetime_parent': (729, 145),
            'callback_parent': (728, 146), 'baseline_audit': (726, 148)}
        self.assertEqual({k: (v['classified'], v['unclassified']) for k, v in self.parents.items()}, expected)
        self.assertNotEqual(self.parents['runtime_parent'], self.parents['lifetime_parent'])

    def test_help_and_padding_start_as_exact_four_byte_unknowns(self):
        by_address = {row['address']: row for row in self.parent['hits']}
        for address in (*HELP, *PADDING):
            self.assertFalse(by_address[address]['accepted'])
            self.assertEqual(by_address[address]['size'], 4)

    def test_two_help_protocols_preserve_padding_allfields_and_741accepted(self):
        geometry = Mock(side_effect=lambda evidence: (evidence['address'], 4))
        module = SimpleNamespace(KIND=KIND, witness_geometry=geometry)
        regions = [m.d.TypedRegion(address, address + 4, KIND, {'address': address, 'synthetic_protocol_only': True}) for address in HELP]
        with patch.dict(sys.modules, {MODULE: module}):
            delta = m.build(self.parent, regions, {'synthetic_protocol_only': True})
            full = m.materialize(self.parent, delta)
        self.assertEqual((full['classified'], full['unclassified']), (743, 131))
        for old, new in zip(self.parent['hits'], full['hits']):
            self.assertEqual({k: old[k] for k in m.FIELDS}, {k: new[k] for k in m.FIELDS})
            if old['address'] not in HELP:
                self.assertEqual(old, new)
        for name in m.INHERITED_NAMES:
            self.assertEqual(self.parent[name], full[name])


if __name__ == '__main__':
    unittest.main()
