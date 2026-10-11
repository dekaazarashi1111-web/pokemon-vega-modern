"""新fieldの型witness・guard0分類境界と746親lineageだけを検査。旧suiteは再走しない。"""
import copy
import json
import sys
import unittest
from pathlib import Path
from functools import lru_cache
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_field_consumer_batch_chain as m
@lru_cache(maxsize=1)
def recorded_parents():
    """この新suite内だけで再利用。読取専用の全親復元を重ねない。"""
    args = tuple((ROOT / path).read_bytes() for path in m.PARENT_INPUTS)
    return args, m.parent_audits(*args)


class GuardLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args, cls.parents = recorded_parents()
        cls.parent = cls.parents['parent_audit']
        cls.proof = {'finite_producer_guard_only': True, 'newly_classified': 0,
                     'all_callers_unreachable_claimed': False,
                     'all_writers_absent_claimed': False}
        cls.delta = m.build(cls.parent, [], cls.proof)

    def test_independent746_parent_has_all15_families127_changes117_witnesses(self):
        self.assertEqual(m.identity(m.canonical(self.parent)), m.PARENT_AUDIT_ID)
        self.assertEqual((self.parent['classified'], self.parent['unclassified']), (746, 128))
        self.assertEqual(len(self.parent['hits']), 874)
        self.assertEqual(len(m.INHERITED_NAMES), 15)
        self.assertEqual(sum(len(self.parent[n]['changes']) for n in m.INHERITED_NAMES), 127)
        self.assertEqual(sum(len(self.parent[n]['witnesses']) for n in m.INHERITED_NAMES), 117)
        self.assertEqual((self.parents['root_batch_parent']['classified'],
                          self.parents['root_batch_parent']['unclassified']), (743, 131))

    def test_all29_independent_inputs_are_whole_bound_before_old_api(self):
        self.assertEqual(len(m.PARENT_INPUTS), 29)
        self.assertEqual(m.PARENT_INPUTS[:-2], m.previous.PARENT_INPUTS)
        self.assertEqual(tuple(m.PARENT_INPUT_IDENTITIES), m.PARENT_INPUTS)
        for i in range(29):
            args = list(self.args)
            args[i] += b'\n'
            with self.subTest(index=i), patch.object(m.previous, 'parent', side_effect=AssertionError('old API must not run')):
                with self.assertRaisesRegex(ValueError, 'twenty-nine parent inputs'):
                    m.parent(*args)
        for args in (self.args[:-1], self.args + (b'extra\n',)):
            with self.assertRaises(ValueError):
                m.parent(*args)

    def test_current_checkpoint_and_delta_have_distinct_recorded_identities(self):
        cp = json.loads(self.args[-1])
        self.assertEqual(m.identity(self.args[-1]), m.PARENT_CHECKPOINT_ID)
        self.assertEqual(m.identity(self.args[-2]), cp['delta_identity'])
        self.assertEqual(cp['delta_identity'], m.PARENT_ID)
        self.assertEqual((cp['classified'], cp['unclassified'], cp['newly_classified']), (746, 128, 3))
        for i in (-1, -2):
            args = list(self.args)
            args[i] = args[i - 2]
            with self.subTest(index=i), self.assertRaises(ValueError):
                m.parent(*args)

    def test_all133_song_models50_assets_remain_in_root_namespace(self):
        song = self.parent[m.previous.NAMESPACE]['proof']['song']
        self.assertEqual((song['combined_song_models'], song['retained_sample_witnesses']), (133, 50))
        self.assertIs(song['all133_models_exact'], True)
        self.assertIs(song['all50_sample_identities_exact'], True)
        self.assertEqual(song['model_identity']['sha256'], '71f01cee0a344409445e17fdea268371269a3e622c6b93563d04b35677e0b975')
        self.assertEqual(song['sample_identity']['sha256'], '9f765e8eee8ad78eaac8902ccafbf9e14c7c694f842e9ae6b2002583181b70ee')

    def test_zero_delta_preserves_entire874_hits_and_every_parent_field(self):
        full = m.materialize(self.parent, self.delta)
        self.assertEqual(set(full) - set(self.parent), {m.NAMESPACE})
        self.assertEqual({k: v for k, v in full.items() if k != m.NAMESPACE}, self.parent)
        self.assertEqual(full['hits'], self.parent['hits'])
        self.assertEqual((full['classified'], full['unclassified']), (746, 128))
        self.assertEqual((self.delta['changes'], self.delta['witnesses'], self.delta['newly_classified']), ([], [], 0))
        self.assertEqual(self.delta['proof'], self.proof)

    def test_guard_registry_is_closed_and_never_interprets_old_witness(self):
        self.assertEqual(m.NEW_KIND_MODULES, {
            'rooted_event_adjacent_text_consumption': 'pr16_dex_hof_event_text_roots',
            'rooted_battle_script_minimum_cross_field': 'pr16_dex_hof_battle_script_roots'})
        for kind in ('rooted_extra_engine_minimum_thumb', 'rooted_bag_context_minimum_text_consumption', 'invented_guard'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                m.witness_geometry({'kind': kind, 'evidence': {}})
        with patch.object(m.importlib, 'import_module', side_effect=AssertionError('zero diagnostic must not import new validator')):
            m.validate(self.parent, self.delta)
        self.assertEqual(self.parent[m.previous.NAMESPACE]['newly_classified'], 3)

    def test_unregistered_guard_region_or_malformed_witness_is_rejected(self):
        old = next(h for h in self.parent['hits'] if not h['accepted'])
        region = m.d.TypedRegion(old['address'], old['address'] + old['size'], 'guard', {})
        with self.assertRaises(ValueError):
            m.build(self.parent, [region], {})
        for key in ('changes', 'witnesses'):
            delta = copy.deepcopy(self.delta)
            delta[key] = [{'fabricated': True}]
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate(self.parent, delta)

    def test_counter_edits_cannot_promote_diagnostics(self):
        for key in ('newly_classified', 'classified', 'unclassified', 'inherited_candidates',
                    'old_full_rom_scan_runs', 'native_processes', 'donor_safe_bytes'):
            for value in (False, float(self.delta[key]), self.delta[key] + 1):
                delta = copy.deepcopy(self.delta)
                delta[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    m.validate(self.parent, delta)

    def test_guard_cannot_claim_universal_unreachability_retirement_or_safe_capacity(self):
        names = (*m.FLAGS, *m.BATCH_FLAGS, 'universal_nonreachability_claimed',
                 'all_callers_unreachable_claimed', 'all_writers_absent_claimed',
                 'guard_promoted_to_classification', 'full_game_unreachability_claimed',
                 'all_game_contexts_unreachable', 'target_retirement_proven',
                 'explicit_owner_transfer_proven', 'all_save_entry_heap_ready_proven',
                 'synchronous_nonreentrant_use_proven', 'stock_save_boundary_crossing_allowed')
        for key in names:
            for value in (True, 0):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    m.validate_restricted_proof({'nested': ({key: value},)})
        for key in ('donor_safe_bytes', 'safe_donor_bytes'):
            for value in (1, False, 0.0):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    m.validate_restricted_proof({'nested': {key: value}})

    def test_proof_does_not_copy_parent_originals(self):
        for name in (*m.INHERITED_NAMES, 'parent_audit', 'inherited_audit', 'baseline_audit'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.validate_restricted_proof({'nested': {name: {}}})
        with self.assertRaises(ValueError):
            m.validate_restricted_proof({'copied': self.parent})

    def test_entire_parent_unknown_and_accepted_fields_are_immutable(self):
        for accepted in (False, True):
            audit = copy.deepcopy(self.parent)
            next(h for h in audit['hits'] if h['accepted'] is accepted)['reason'] = 'changed'
            with self.subTest(accepted=accepted), self.assertRaises(ValueError):
                m.build(audit, [], {})
        audit = copy.deepcopy(self.parent)
        audit[m.previous.NAMESPACE]['proof']['song']['retained_sample_witnesses'] = 49
        with self.assertRaises(ValueError):
            m.build(audit, [], {})

    def test_materialized_extra_claims_namespace_substitution_and_hidden_edit_rejected(self):
        for key, value in (('donor_safe_bytes', 15118), ('classified', 747), ('controller_runtime_wired', True)):
            full = m.materialize(self.parent, self.delta)
            full[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_materialized(self.parent, full)
        full = m.materialize(self.parent, self.delta)
        full[m.NAMESPACE] = copy.deepcopy(full[m.previous.NAMESPACE])
        with self.assertRaises(ValueError):
            m.validate_materialized(self.parent, full)

    def test_independent_measured_delta_identity_lf_and_closed_schema(self):
        raw = m.canonical(self.delta)
        self.assertEqual(m.read_measured(raw, m.identity(raw), self.parent), self.delta)
        for altered in (raw + b' ', raw.rstrip(b'\n'), raw.replace(b'\n', b'\r\n')):
            with self.subTest(suffix=altered[-2:]), self.assertRaises(ValueError):
                m.read_measured(altered, m.identity(altered), self.parent)
        changed = copy.deepcopy(self.delta)
        changed['extra'] = True
        with self.assertRaises(ValueError):
            m.validate(self.parent, changed)
        changed = copy.deepcopy(self.delta)
        changed['proof']['newly_classified'] = 1
        with self.assertRaises(ValueError):
            m.validate(self.parent, changed)

    def test_new_guard_data_and_parent_have_no_mutable_aliases(self):
        proof = {'guard': {'cases': []}}
        delta = m.build(self.parent, [], proof)
        proof['guard']['cases'].append('later')
        full = m.materialize(self.parent, delta)
        full[m.NAMESPACE]['proof']['guard']['cases'].append('later')
        self.assertEqual(delta['proof']['guard']['cases'], [])
        full['hits'][0]['evidence'] = []
        self.assertNotEqual(full['hits'][0], self.parent['hits'][0])


class TypedFieldProtocolTests(unittest.TestCase):
    """合成小fixtureで新chain接続だけを反証。現ROM根の代わりにはしない。"""
    KIND = 'synthetic_field_protocol_only'
    MODULE = 'synthetic_field_protocol_validator'

    def setUp(self):
        self.audit = dict(candidate={'size': 64, 'sha256': 'synthetic'},
            hits=[dict(address=100 + i * 4, target=200, kind='SYNTHETIC', size=4,
                sha256=str(i), accepted=i == 0, classification='ACCEPTED' if i == 0 else 'UNCLASSIFIED',
                evidence=['old'] if i == 0 else [], retained_extra=i) for i in range(5)],
            classified=1, unclassified=4, donor_leased=False, donor_eligible=False,
            indirect_reference_completeness_claimed=False,
            **{name: {'retained': name} for name in m.INHERITED_NAMES})
        self.module = SimpleNamespace(KIND=self.KIND, witness_geometry=lambda e: (e['address'], e['size']))
        for patcher in (patch.dict(m.PARENT_AUDIT_ID, m.identity(m.canonical(self.audit))),
                        patch.dict(m.NEW_KIND_MODULES, {self.KIND: self.MODULE}, clear=True),
                        patch.dict(sys.modules, {self.MODULE: self.module})):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.regions = [m.d.TypedRegion(104+i*4, 108+i*4, self.KIND,
            {'address': 104+i*4, 'size': 4, 'synthetic_protocol_only': True}) for i in range(3)]
        self.delta = m.build(self.audit, self.regions,
                             {'newly_classified': 3, 'new_data': 3, 'synthetic_protocol_only': True})

    def test_new_data_counts_are_not_mistaken_for_safety_claims(self):
        self.assertEqual((self.delta['newly_classified'], self.delta['classified'], self.delta['unclassified']), (3, 4, 1))
        self.assertEqual(len(self.delta['witnesses']), 3)
        self.assertEqual(self.delta['proof']['new_data'], 3)
        self.assertEqual(self.delta['donor_safe_bytes'], 0)
        self.assertIs(self.delta['natural_play_universal_reachability_claimed'], False)

    def test_all_accepted_remaining_unknown_and_inherited_families_remain_exact(self):
        full = m.materialize(self.audit, self.delta)
        self.assertEqual(full['hits'][0], self.audit['hits'][0])
        self.assertEqual(full['hits'][-1], self.audit['hits'][-1])
        for old, new in zip(self.audit['hits'], full['hits']):
            self.assertEqual({k: old[k] for k in m.FIELDS}, {k: new[k] for k in m.FIELDS})
        for name in m.INHERITED_NAMES:
            self.assertEqual(full[name], self.audit[name])
        self.assertEqual(full['hits'][1]['evidence'], [{'field_consumer_batch_reference_chain_witness': 0}])

    def test_witness_geometry_kind_module_and_import_failure_never_fall_back(self):
        for geometry in ((104.0, 4), (104, 4.0), (104, True), (103, 5), (104, 3)):
            self.module.witness_geometry = lambda e, v=geometry: v
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                m.validate(self.audit, self.delta)
        self.module.KIND = 'wrong_kind'
        with self.assertRaises(ValueError):
            m.validate(self.audit, self.delta)
        with patch.object(m.importlib, 'import_module', side_effect=ModuleNotFoundError('missing')):
            with self.assertRaises(ModuleNotFoundError):
                m.validate(self.audit, self.delta)

    def test_witness_evidence_cannot_hide_guard_promotion_or_lease_claim(self):
        for key in ('guard_promoted_to_classification', 'all_callers_unreachable_claimed',
                    'all_writers_absent_claimed', 'lease_authorized', 'target_retirement_proven'):
            evidence = dict(self.regions[0].evidence, nested={key: True})
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.build(self.audit, [m.d.TypedRegion(104, 108, self.KIND, evidence)], {})

    def test_no_partial_union_conflicting_type_or_unreferenced_witness(self):
        partial = [m.d.TypedRegion(104, 106, self.KIND, {'address': 104, 'size': 2}),
                   m.d.TypedRegion(106, 108, self.KIND, {'address': 106, 'size': 2})]
        self.assertEqual(m.build(self.audit, partial, {})['newly_classified'], 0)
        conflict = self.regions + [m.d.TypedRegion(104, 108, 'unregistered_guard', {})]
        self.assertEqual(m.build(self.audit, conflict, {})['newly_classified'], 2)
        delta = copy.deepcopy(self.delta)
        extra = copy.deepcopy(delta['witnesses'][-1])
        extra['id'] = 3
        delta['witnesses'].append(extra)
        with self.assertRaises(ValueError):
            m.validate(self.audit, delta)

    def test_change_and_witness_identities_order_counter_types_are_strict(self):
        mutations = (lambda x: x['changes'].reverse(),
                     lambda x: x['changes'][0].update(sha256='changed'),
                     lambda x: x['changes'][0].update(address=104.0),
                     lambda x: x['changes'][0].update(witness_ids=[True]),
                     lambda x: x['witnesses'][0].update(size=4.0),
                     lambda x: x['witnesses'][0]['evidence'].update(size=8),
                     lambda x: x.update(newly_classified=True))
        for mutate in mutations:
            delta = copy.deepcopy(self.delta)
            mutate(delta)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.validate(self.audit, delta)

    def test_zero_diagnostic_and_full_materialization_stay_independent(self):
        zero = m.build(self.audit, [], {'guard_only': True, 'newly_classified': 0})
        self.assertEqual(m.materialize(self.audit, zero)['hits'], self.audit['hits'])
        full = m.materialize(self.audit, self.delta)
        full['hits'][-1]['retained_extra'] = 'changed'
        with self.assertRaises(ValueError):
            m.validate_materialized(self.audit, full)
        self.assertEqual(self.audit['unclassified'], 4)


if __name__ == '__main__':
    unittest.main()
