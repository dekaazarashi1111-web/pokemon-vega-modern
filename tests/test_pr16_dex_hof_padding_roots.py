"""新Credits gap guard専用。固定窓fixtureのみを使い旧consumerは再実行しない。"""
import copy
import hashlib
import unittest
from unittest.mock import patch
import pr16_dex_hof_padding_roots as v

FIXTURE = None


class Overlay:
    def __init__(self, raw, address, size, value):
        self.raw, self.a, self.data = raw, address - 0x08000000, value.to_bytes(size, 'little')
    def __len__(self):
        return len(self.raw)
    def __getitem__(self, key):
        if isinstance(key, int):
            return self[key:key + 1][0]
        start, end = key.start, key.stop
        value = bytearray(self.raw[key])
        left, right = max(start, self.a), min(end, self.a + len(self.data))
        if left < right:
            value[left - start:right - start] = self.data[left - self.a:right - self.a]
        return bytes(value)


def reseal(obj, raw):
    if isinstance(obj, dict):
        if {'address', 'size', 'sha256'} <= obj.keys():
            obj['sha256'] = hashlib.sha256(v.chunk(raw, obj['address'], obj['size'])).hexdigest()
        for value in obj.values():
            reseal(value, raw)
    elif isinstance(obj, list):
        for value in obj:
            reseal(value, raw)


class PaddingRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURE is None:
            raise RuntimeError('explicit bounded in-memory FIXTURE required')
        cls.raw, cls.inherited, cls.review, cls.sources = FIXTURE
        cls.regions, cls.proof = v._regions(*FIXTURE)
    def check(self, raw=None, inherited=None, review=None, sources=None):
        return v._regions(self.raw if raw is None else raw,
                          self.inherited if inherited is None else inherited,
                          self.review if review is None else review,
                          self.sources if sources is None else sources)
    def reject_review(self, mutate):
        review = copy.deepcopy(self.review)
        mutate(review)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.check(review=review)
    def reject_both(self, mutate):
        inherited, review = copy.deepcopy(self.inherited), copy.deepcopy(self.review)
        mutate(inherited['hits'][0]); mutate(review['hits'][0])
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.check(inherited=inherited, review=review)
    def test_01_no_typed_region_or_new_bytes(self):
        self.assertEqual((self.regions, v.CLASSIFIED_HITS, self.proof['count'], self.proof['new_classified_bytes']),
                         ([], (), 0, 0))
    def test_02_exact_four_held_hits(self):
        self.assertEqual(self.proof['held_hits'], list(v.HELD_HITS))
    def test_03_actual_table_rows(self):
        self.assertEqual([r['table_index'] for r in self.proof['observations']], [1, 6, 10, 11])
    def test_04_exact_gap_sizes(self):
        self.assertEqual([r['gap']['size'] for r in self.proof['observations']], [1, 2, 1, 1])
    def test_05_each_hit_has_one_unproven_byte(self):
        for row in self.proof['observations']:
            self.assertEqual(row['split']['unproven_bytes'], [row['hit']])
            self.assertEqual(row['split']['text_extent_bytes'], list(range(row['hit'] + 1, row['hit'] + 4)))
            self.assertIs(row['split']['all_hit_bytes_in_text_extents'], False)
    def test_06_eight_english_declarations_do_not_match_rom(self):
        comparisons = [x for row in self.proof['observations'] for x in row['public_source_comparison']]
        self.assertEqual(len(comparisons), 8)
        self.assertTrue(all(x['exact_glyph_sequence_matches'] is False for x in comparisons))
    def test_07_all_inherited_fields_untouched(self):
        inherited = copy.deepcopy(self.inherited)
        inherited['other_proof_families'] = {'must': ['stay', 'identical']}
        before = copy.deepcopy(inherited)
        self.check(inherited=inherited)
        self.assertEqual(inherited, before)
    def test_08_diagnostic_not_current(self):
        with patch.object(v, 'identity', return_value=v.DIAGNOSTIC), patch.object(v, '_regions') as verify:
            with self.assertRaises(ValueError):
                v.regions(*FIXTURE)
            verify.assert_not_called()
    def test_09_current_wrapper_only_after_identity_gate(self):
        with patch.object(v, 'identity', return_value=v.CANDIDATE), patch.object(v, '_regions', return_value=([], v.held_proof_template())) as verify:
            regions, proof = v.regions(*FIXTURE)
            self.assertEqual(regions, [])
            self.assertIs(proof['current_candidate_measured'], True)
            verify.assert_called_once()
    def test_10_diagnostic_audit_flag_stays_false(self):
        self.assertIs(self.proof['current_candidate_measured'], False)
    def test_11_current_identity_cannot_be_replaced(self):
        inherited = copy.deepcopy(self.inherited); inherited['candidate'] = v.DIAGNOSTIC
        with self.assertRaises(ValueError): self.check(inherited=inherited)
    def test_12_accepted_hit_rejected(self):
        self.reject_both(lambda h: h.update(accepted=True))
    def test_13_owner_hit_rejected(self):
        self.reject_both(lambda h: h.update(owner_candidates=['owner']))
    def test_14_typed_classification_rejected(self):
        self.reject_both(lambda h: h.update(classification='TYPED'))
    def test_15_hit_size_rejected(self):
        self.reject_both(lambda h: h.update(size=3))
    def test_16_hit_size_bool_rejected(self):
        self.reject_both(lambda h: h.update(size=True))
    def test_17_hit_kind_rejected(self):
        self.reject_both(lambda h: h.update(kind='ROM_POINTER'))
    def test_18_duplicate_held_row_rejected(self):
        inherited = copy.deepcopy(self.inherited); inherited['hits'].append(inherited['hits'][0])
        with self.assertRaises(ValueError): self.check(inherited=inherited)
    def test_19_missing_held_row_rejected(self):
        inherited = copy.deepcopy(self.inherited); inherited['hits'].pop()
        with self.assertRaises(ValueError): self.check(inherited=inherited)
    def test_20_reordered_held_rows_rejected(self):
        inherited = copy.deepcopy(self.inherited); inherited['hits'].reverse()
        with self.assertRaises(ValueError): self.check(inherited=inherited)
    def test_21_new_classified_hit_rejected(self):
        self.reject_review(lambda r: r.update(classified_hits=[v.HELD_HITS[0]]))
    def test_22_every_stronger_claim_rejected(self):
        for key, value in v.CLAIMS.items():
            if value is False:
                with self.subTest(claim=key): self.reject_review(lambda r, k=key: r['claims'].update({k: True}))
    def test_23_missing_claim_rejected(self):
        self.reject_review(lambda r: r['claims'].pop('gap_unreferenced_proven'))
    def test_24_false_integer_claim_rejected(self):
        self.reject_review(lambda r: r['claims'].update(donor_leased=0))
    def test_25_source_only_layout_promotion_rejected(self):
        self.reject_review(lambda r: r['source_limitations'].update(japanese_object_build_available=True))
    def test_26_invented_linker_map_rejected(self):
        self.reject_review(lambda r: r['source_limitations'].update(exact_linker_map_available=True))
    def test_27_invented_reference_closure_rejected(self):
        self.reject_review(lambda r: r['source_limitations'].update(complete_reference_domain_available=True))
    def test_28_missing_obligation_rejected(self):
        self.reject_review(lambda r: r['required_obligations'].pop())
    def test_29_arbitrary_evidence_never_creates_witness(self):
        for evidence in ({}, self.review, self.proof, {'all_hit_bytes_consumed': True}, {'serializer_verified': True}):
            with self.subTest(evidence_type=type(evidence).__name__), self.assertRaises(ValueError):
                v.witness_geometry(evidence)
    def test_30_unknown_top_level_review_rejected(self):
        self.reject_review(lambda r: r.update(trusted=True))
    def test_31_review_schema_bool_rejected(self):
        self.reject_review(lambda r: r.update(schema_version=True))
    def test_32_missing_window_rejected(self):
        self.reject_review(lambda r: r['windows'].pop())
    def test_33_added_window_rejected(self):
        self.reject_review(lambda r: r['windows'].append(r['windows'][0]))
    def test_34_widened_gap_rejected(self):
        self.reject_review(lambda r: r['layout_rows'][0]['gap'].update(size=4))
    def test_35_moved_names_start_rejected(self):
        self.reject_review(lambda r: r['layout_rows'][0]['names'].update(address=v.HELD_HITS[0]))
    def test_36_modified_pinned_source_rejected(self):
        for key in self.sources:
            sources = dict(self.sources); sources[key] += b'\n'
            with self.subTest(source=key), self.assertRaises(ValueError): self.check(sources=sources)
    def test_37_resealed_source_cannot_replace_pinned_source(self):
        for key in self.sources:
            sources = dict(self.sources); sources[key] += b'\n'
            review = copy.deepcopy(self.review); review['source_bindings'][key].update(v.identity(sources[key]))
            with self.subTest(source=key), self.assertRaises(ValueError): self.check(review=review, sources=sources)
    def test_38_missing_source_rejected(self):
        sources = dict(self.sources); sources.pop('pret-defines.h')
        with self.assertRaises(ValueError): self.check(sources=sources)
    def test_39_extra_source_cannot_supply_serializer(self):
        sources = dict(self.sources); sources['alleged-japanese-object'] = b'ALIGNED(4)'
        with self.assertRaises(ValueError): self.check(sources=sources)
    def test_40_every_bounded_byte_mutation_resealed_rejected(self):
        for window in v.FIXED_WINDOWS:
            for offset in range(window['size']):
                address = window['address'] + offset
                raw = Overlay(self.raw, address, 1, v.chunk(self.raw, address, 1)[0] ^ 1)
                inherited, review = copy.deepcopy(self.inherited), copy.deepcopy(self.review)
                reseal(inherited, raw); reseal(review, raw)
                with self.subTest(address=address), self.assertRaises(ValueError):
                    self.check(raw=raw, inherited=inherited, review=review)
    def test_41_gap_not_eos_even_after_reseal(self):
        for row in v.LAYOUT_ROWS:
            raw = Overlay(self.raw, row['hit'], 1, 255)
            inherited, review = copy.deepcopy(self.inherited), copy.deepcopy(self.review)
            reseal(inherited, raw); reseal(review, raw)
            with self.subTest(hit=row['hit']), self.assertRaises(ValueError):
                self.check(raw=raw, inherited=inherited, review=review)
    def test_42_pointer_cannot_move_to_gap(self):
        for row in v.LAYOUT_ROWS:
            raw = Overlay(self.raw, row['pointer_pair']['address'] + 4, 4, row['hit'])
            review = copy.deepcopy(self.review); reseal(review, raw)
            with self.subTest(hit=row['hit']), self.assertRaises(ValueError): self.check(raw=raw, review=review)
    def test_43_split_detects_uncovered_leading_byte(self):
        self.assertEqual(v.split_hit(100, 4, [{'address': 101, 'size': 9}]),
                         dict(text_extent_bytes=[101, 102, 103], unproven_bytes=[100], all_hit_bytes_in_text_extents=False))
    def test_44_split_detects_interior_gap(self):
        self.assertEqual(v.split_hit(100, 4, [{'address': 100, 'size': 1}, {'address': 102, 'size': 2}])['unproven_bytes'], [101])
    def test_45_split_empty_text_does_not_create_coverage(self):
        self.assertEqual(v.split_hit(100, 4, [])['unproven_bytes'], [100, 101, 102, 103])
    def test_46_split_full_coverage_still_does_not_issue_witness(self):
        split = v.split_hit(100, 4, [{'address': 100, 'size': 4}])
        self.assertIs(split['all_hit_bytes_in_text_extents'], True)
        with self.assertRaises(ValueError): v.witness_geometry(split)
    def test_47_overlapping_extents_rejected(self):
        with self.assertRaises(ValueError): v.split_hit(100, 4, [{'address': 100, 'size': 4}, {'address': 103, 'size': 2}])
    def test_48_invalid_extent_geometry_rejected(self):
        for windows in ([{'address': 100, 'size': False}], [{'address': 100, 'size': 0}], [{'address': 100, 'size': 4, 'trusted': True}]):
            with self.subTest(windows=windows), self.assertRaises(ValueError): v.split_hit(100, 4, windows)
    def test_49_public_proof_is_small(self):
        self.assertLess(len(__import__('json').dumps(self.proof).encode()), 20000)
    def test_50_all_hold_obligations_remain_open(self):
        self.assertEqual(self.proof['required_obligations'], list(v.REQUIRED_OBLIGATIONS))
        self.assertTrue(all(r['real_consumer_recomposed'] is False and r['classified'] is False for r in self.proof['observations']))

    def test_51_closed_guard_proof_accepts_exact_observation(self):
        self.assertIs(v.validate_held_proof(self.proof), True)
        self.assertEqual(v.HITS, v.HELD_HITS)
    def test_52_empty_guard_proof_rejected(self):
        with self.assertRaises(ValueError): v.validate_held_proof({})
    def test_53_missing_guard_field_rejected(self):
        for key in self.proof:
            proof = copy.deepcopy(self.proof); proof.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_54_extra_guard_field_rejected(self):
        proof = copy.deepcopy(self.proof); proof['trusted'] = True
        with self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_55_every_guard_boolean_promotion_rejected(self):
        for key, value in self.proof.items():
            if type(value) is bool:
                proof = copy.deepcopy(self.proof); proof[key] = not value
                with self.subTest(key=key), self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_56_guard_zero_bool_rejected(self):
        proof = copy.deepcopy(self.proof); proof['count'] = False
        with self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_57_guard_partial_hit_list_rejected(self):
        proof = copy.deepcopy(self.proof); proof['held_hits'].pop()
        with self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_58_guard_text_membership_cannot_cover_gap(self):
        proof = copy.deepcopy(self.proof); proof['observations'][0]['split']['unproven_bytes'] = []
        with self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_59_guard_donor_safe_bytes_field_rejected(self):
        proof = copy.deepcopy(self.proof); proof['donor_safe_bytes'] = 15118
        with self.assertRaises(ValueError): v.validate_held_proof(proof)
    def test_60_explicit_measurement_bool_required(self):
        with self.assertRaises(ValueError): v.validate_held_proof(self.proof, current_candidate_measured=0)
        proof = v.held_proof_template(current_candidate_measured=True)
        self.assertIs(v.validate_held_proof(proof, current_candidate_measured=True), True)
        with self.assertRaises(ValueError): v.validate_held_proof(proof)
