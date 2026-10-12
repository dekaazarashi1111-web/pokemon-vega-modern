"""Bag並替えの局所producerと、未結合2hitの誤分類を拒否する新scope反証。"""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import pr16_dex_hof_bag_sort_roots as v
FIXTURE = None

class Overlay:
    def __init__(self, raw, address, size, value):
        self.raw, self.address = raw, address - 0x08000000
        self.value = value.to_bytes(size, 'little')
    def __len__(self):
        return len(self.raw)
    def __getitem__(self, index):
        if isinstance(index, int):
            return self[index:index + 1][0]
        low, high = index.start, index.stop
        data = bytearray(self.raw[index])
        left, right = max(low, self.address), min(high, self.address + len(self.value))
        if left < right:
            data[left - low:right - low] = self.value[left - self.address:right - self.address]
        return bytes(data)

def reseal(obj, raw):
    if isinstance(obj, dict):
        if {'address', 'size', 'sha256'} <= obj.keys():
            obj['sha256'] = hashlib.sha256(v.chunk(raw, obj['address'], obj['size'])).hexdigest()
        for value in obj.values():
            reseal(value, raw)
    elif isinstance(obj, list):
        for value in obj:
            reseal(value, raw)

class BagSortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURE is None:
            raise RuntimeError('必要窓だけの明示FIXTUREが必要')
        cls.raw, cls.inherited, cls.review, cls.sources = FIXTURE
        cls.regions, cls.proof = v._regions(*FIXTURE)
    def check(self, raw=None, inherited=None, review=None, sources=None):
        return v._regions(self.raw if raw is None else raw,
                          self.inherited if inherited is None else inherited,
                          self.review if review is None else review,
                          self.sources if sources is None else sources)
    def reject_review(self, edit):
        review = copy.deepcopy(self.review)
        edit(review)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.check(review=review)
    def reject_proof(self, edit):
        proof = copy.deepcopy(self.proof)
        edit(proof)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            v.validate_held_proof(proof)
    def mutate(self, address, size, value):
        raw = Overlay(self.raw, address, size, value)
        review, inherited = copy.deepcopy(self.review), copy.deepcopy(self.inherited)
        reseal(review, raw)
        reseal(inherited, raw)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.check(raw=raw, review=review, inherited=inherited)
    def test_01_no_classification_and_no_inherited_changes(self):
        before = copy.deepcopy(self.inherited)
        self.assertEqual(self.regions, [])
        self.assertEqual(self.proof['held_hits'], list(v.HITS))
        self.assertEqual(self.proof['count'], 0)
        self.assertEqual(self.inherited, before)
    def test_02_three_actual_producer_cases(self):
        self.assertEqual([p['actions'] for p in self.proof['producer_cases']], [[12, 13, 16, 4], [12, 4], [12, 16, 4]])
        self.assertTrue(all(p['opaque_boundaries'] == 0 for p in self.proof['producer_cases']))
    def test_03_actual_mode_writers_keep_two_excluded(self):
        self.assertEqual({p['action']: p['mode'] for p in self.proof['callback_mode_prefixes']}, v.MODES)
        generated = {a for p in self.proof['producer_cases'] for a in p['actions']} - {4}
        self.assertEqual({v.MODES[a] for a in generated}, {0, 1, 4})
    def test_04_independent_encoder_every_semantic_halfword(self):
        count = 0
        for ins in v.INS.values():
            self.assertEqual(v.chunk(self.raw, ins.address, ins.size), v.encoded(ins))
            for offset in range(0, ins.size, 2):
                address = ins.address + offset
                value = int.from_bytes(v.chunk(self.raw, address, 2), 'little') ^ 1
                with self.subTest(address=address), self.assertRaises(ValueError):
                    v.bind_semantics(Overlay(self.raw, address, 2, value))
                count += 1
        self.assertEqual(count, 65)
    def test_05_every_literal_reseal_fails(self):
        for address, value in v.LITERALS.items():
            with self.subTest(address=address):
                self.mutate(address, 4, value ^ 1)
    def test_06_all_protected_bytes_reseal_fails(self):
        for row in v.FIXED_WINDOWS:
            for offset in range(row['size']):
                address = row['address'] + offset
                with self.subTest(address=address):
                    self.mutate(address, 1, v.chunk(self.raw, address, 1)[0] ^ 1)
    def test_07_all_four_texts_and_both_boundaries_fixed(self):
        self.assertEqual(sum(t['size'] for t in v.TEXTS), 18)
        for row in v.TEXTS:
            self.assertEqual(v.chunk(self.raw, row['address'] + row['size'] - 1, 1), b'\xff')
        for hit in v.HITS:
            self.assertTrue(all(any(t['address'] <= a < t['address'] + t['size'] for t in v.TEXTS) for a in range(hit, hit + 4)))
    def test_08_injecting_most_into_actual_action_array_rejected(self):
        self.mutate(0x09167806, 1, 14)
    def test_09_injecting_least_into_actual_action_array_rejected(self):
        self.mutate(0x09167806, 1, 15)
    def test_10_extending_actual_count_rejected(self):
        self.mutate(0x09111978, 2, 0x2206)
    def test_11_table_text_redirect_rejected(self):
        self.mutate(v.TABLE + 16 * 8, 4, 0x0914926F)
    def test_12_callback_redirect_rejected(self):
        self.mutate(v.TABLE + 16 * 8 + 4, 4, 0x0910FC51)
    def test_13_mode_writer_redirect_rejected(self):
        self.mutate(0x0910FBF2, 2, 0x2203)
    def test_14_actual_all_u16_pocket_values_same_three_classes(self):
        for pocket in range(65536):
            result = v._compose_selected(self.raw, pocket)
            self.assertNotIn(14, result['actions'])
            self.assertNotIn(15, result['actions'])
    def test_15_invalid_pocket_inputs_rejected(self):
        for pocket in (-1, 65536, True, 0.0, '0', None):
            with self.subTest(pocket=pocket), self.assertRaises(ValueError):
                v.compose_selected(self.raw, pocket)
    def test_16_callback_all_valid_task_slots(self):
        for task_id in range(16):
            for action in v.CALLBACKS:
                self.assertEqual(v.callback_mode_prefix(self.raw, action, task_id)['mode'], v.MODES[action])
    def test_17_callback_invalid_slot_rejected(self):
        for slot in (-1, 16, True, '0'):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                v.callback_mode_prefix(self.raw, 14, slot)
    def test_18_callback_unknown_action_rejected(self):
        for action in (4, 11, 17, True, '14'):
            with self.subTest(action=action), self.assertRaises(ValueError):
                v.callback_mode_prefix(self.raw, action)
    def test_19_no_host_output_fixture_injection(self):
        with self.assertRaises(ValueError):
            v.compose_selected(self.raw, 0, initial_fields=[(v.POCKET, 2, 0), (v.COUNT, 1, 6)])
    def test_20_no_extra_ram_preservation(self):
        for row in self.proof['producer_cases']:
            self.assertEqual(row['required_initial_fields'], [dict(address=v.POCKET, size=2)])
    def test_21_guard_cannot_issue_evidence(self):
        for hit in (*v.HITS, 0x083DD7E7):
            with self.subTest(hit=hit), self.assertRaises(ValueError):
                v.evidence_template(hit)
    def test_22_guard_cannot_issue_geometry(self):
        for evidence in ({}, {'address': v.HITS[0], 'size': 4}, {'root_verified': True}):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                v.witness_geometry(evidence)
    def test_23_diagnostic_cannot_enter_current_wrapper(self):
        with patch.object(v, 'identity', return_value=v.DIAGNOSTIC), patch.object(v, '_regions') as run:
            with self.assertRaises(ValueError):
                v.regions(*FIXTURE)
            run.assert_not_called()
    def test_24_current_wrapper_sets_measured_flag(self):
        original_identity = v.identity
        with patch.object(v, 'identity', side_effect=lambda value: v.CANDIDATE if value is self.raw else original_identity(value)):
            rows, proof = v.regions(*FIXTURE)
        self.assertEqual(rows, [])
        self.assertTrue(proof['current_candidate_measured'])
        v.validate_held_proof(proof, True)
    def test_25_bad_inherited_candidate_rejected(self):
        inherited = copy.deepcopy(self.inherited)
        inherited['candidate']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.check(inherited=inherited)
    def test_26_owner_or_accepted_cannot_be_reclassified(self):
        for key, value in [('accepted', True), ('owner_candidates', ['fabricated']), ('classification', 'DATA')]:
            inherited, review = copy.deepcopy(self.inherited), copy.deepcopy(self.review)
            inherited['hits'][0][key] = review['hits'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(inherited=inherited, review=review)
    def test_27_missing_duplicate_reordered_hit_rejected(self):
        for hits in (self.inherited['hits'][:1], self.inherited['hits'] * 2, list(reversed(self.inherited['hits']))):
            inherited = copy.deepcopy(self.inherited)
            inherited['hits'] = hits
            with self.subTest(hits=hits), self.assertRaises(ValueError):
                self.check(inherited=inherited)
    def test_28_unrelated_hit_is_unchanged(self):
        inherited = copy.deepcopy(self.inherited)
        inherited['hits'].append(dict(address=0x08000000, sentinel='unchanged'))
        before = copy.deepcopy(inherited)
        self.check(inherited=inherited)
        self.assertEqual(inherited, before)
    def test_29_hit_geometry_types_and_size_rejected(self):
        for key, value in [('size', True), ('size', 5), ('kind', 'TEXT')]:
            inherited, review = copy.deepcopy(self.inherited), copy.deepcopy(self.review)
            inherited['hits'][0][key] = review['hits'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(inherited=inherited, review=review)
    def test_30_review_json_roundtrip_required(self):
        review = json.loads(json.dumps(self.review, ensure_ascii=False))
        self.assertEqual(self.check(review=review)[0], [])
    def test_31_closed_review_no_extra_field(self):
        self.reject_review(lambda r: r.update(trusted=True))
    def test_32_no_window_extension_reduction_or_reorder(self):
        for edit in (lambda r: r['windows'].pop(), lambda r: r['windows'].append(r['windows'][0]), lambda r: r['windows'].reverse()):
            self.reject_review(edit)
    def test_33_source_full_bytes_not_names(self):
        sources = dict(self.sources)
        sources['cfru-item.c'] += b'\n'
        with self.assertRaises(ValueError):
            self.check(sources=sources)
    def test_34_source_manifest_and_key_set_closed(self):
        self.reject_review(lambda r: r['source_bindings']['cfru-item.c'].update(git_blob_sha='0' * 40))
        with self.assertRaises(ValueError):
            self.check(sources={})
    def test_35_unbound_hook_not_a_root(self):
        self.reject_review(lambda r: r['root'].update(hook_caller_bound=True))
        self.reject_review(lambda r: r['root'].update(entry=0x091118EC))
    def test_36_table_existence_not_dispatch(self):
        self.reject_review(lambda r: r['root'].update(extended_table_dispatch_bound=True))
    def test_37_no_natural_reachability_claim(self):
        self.reject_review(lambda r: r['claims'].update(full_story_reachability_claimed=True))
    def test_38_no_global_dead_code_claim(self):
        self.reject_review(lambda r: r['claims'].update(global_unreachability_proven=True))
    def test_39_no_all_writers_claim(self):
        self.reject_review(lambda r: r['claims'].update(all_other_writers_excluded=True))
    def test_40_no_retirement_or_donor_claim(self):
        for key in ('retired_or_reusable_proven', 'donor_eligible', 'donor_leased'):
            self.reject_review(lambda r, k=key: r['claims'].update({k: True}))
    def test_41_no_hit_consumption_claim(self):
        self.reject_review(lambda r: r['claims'].update(all_hit_bytes_consumed=True))
    def test_42_no_native_or_universal_epoch_claim(self):
        for key in ('actual_runtime_execution_observed', 'universal_heap_or_irq_lifetime_proven'):
            self.reject_review(lambda r, k=key: r['claims'].update({k: True}))
    def test_43_no_classified_hit_in_guard_review(self):
        self.reject_review(lambda r: r['classified_hits'].append(v.HITS[0]))
    def test_44_no_omitted_obligation(self):
        self.reject_review(lambda r: r['required_obligations'].pop())
    def test_45_proof_cannot_promote_classification(self):
        self.reject_proof(lambda p: p.update(count=2, hits=list(v.HITS), held_hits=[]))
    def test_46_proof_cannot_promote_local_prefix_or_widen_actions(self):
        self.reject_proof(lambda p: p['callback_mode_prefixes'][2].update(registered_root_bound=True))
        self.reject_proof(lambda p: p['producer_cases'][0]['actions'].append(14))
    def test_47_boolean_current_flag_not_numeric(self):
        with self.assertRaises(ValueError):
            v.held_proof_template(1)
        self.reject_proof(lambda p: p.update(current_candidate_measured=0))
    def test_48_public_composition_rebinds_instruction_bytes(self):
        raw = Overlay(self.raw, 0x09111978, 2, 0x2206)
        with self.assertRaises(ValueError):
            v.compose_selected(raw, 0)
        with self.assertRaises(ValueError):
            v.callback_mode_prefix(raw, 14)
    def test_49_compact_proof_no_trace_payload(self):
        blob = json.dumps(self.proof, ensure_ascii=False)
        self.assertLess(len(blob.encode()), 18000)
        self.assertNotIn('raw_trace', blob)
        self.assertNotIn('private-inputs', blob)

if __name__ == '__main__':
    unittest.main()
