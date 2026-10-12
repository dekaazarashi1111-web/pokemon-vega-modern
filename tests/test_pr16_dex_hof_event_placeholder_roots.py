"""未接続event/FD03境界の未知維持、登録prefixと条件付き終端probeの新scope反証。"""
import copy, hashlib, unittest
from unittest.mock import patch
import pr16_dex_hof_event_placeholder_roots as v
FIXTURE = None


class Overlay:
    def __init__(self, raw, address, size, value):
        self.raw, self.address = raw, address - 0x08000000
        self.value = value.to_bytes(size, 'little')
    def __len__(self):
        return len(self.raw)
    def __getitem__(self, key):
        if isinstance(key, int):
            return self[key:key + 1][0]
        low, high = key.start, key.stop
        data = bytearray(self.raw[key]); left = max(low, self.address); right = min(high, self.address + len(self.value))
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


class EventPlaceholderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURE is None:
            raise RuntimeError('明示的な必要窓だけのFIXTUREが必要')
        cls.raw, cls.inherited, cls.review, cls.sources = FIXTURE
        cls.regions, cls.proof = v._regions(*FIXTURE)
    def check(self, raw=None, inherited=None, review=None, sources=None):
        return v._regions(self.raw if raw is None else raw, self.inherited if inherited is None else inherited,
                          self.review if review is None else review, self.sources if sources is None else sources)
    def reject_review(self, edit):
        review = copy.deepcopy(self.review); edit(review)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.check(review=review)
    def reject_proof(self, edit):
        proof = copy.deepcopy(self.proof); edit(proof)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            v.validate_held_proof(proof)
    def mutated(self, address, size=1, xor=1):
        return Overlay(self.raw, address, size, int.from_bytes(v.chunk(self.raw, address, size), 'little') ^ xor)
    def test_zero_regions(self): self.assertEqual(self.regions, [])
    def test_one_held_hit(self): self.assertEqual(self.proof['held_hits'], [0x0818DD5D])
    def test_zero_classified_bytes(self): self.assertEqual(self.proof['new_classified_bytes'], 0)
    def test_guard_api(self): self.assertEqual(v.TYPE_CATEGORY, 'guard'); self.assertEqual(v.CLASSIFIED_HITS, ())
    def test_registered_objects(self): self.assertEqual([p['owner_id'] for p in self.proof['registration_paths']], ['OBJECT:3/10:0', 'OBJECT:23/0:0'])
    def test_actual_other_text_pointers(self): self.assertEqual([r['text_pointer'] for r in v.ROOTS], [0x086A1E74, 0x086A20F9])
    def test_prefix_and_conditional_terminal_counts(self): self.assertEqual([(r['prefix_machine_instructions'], r['conditional_terminal_machine_instructions']) for r in self.proof['conditional_root_probes']], [(237, 50), (237, 50)])
    def test_standard2_no_runtime_claim(self): self.assertTrue(all(r['standard_handlers_executed'] is False for r in self.proof['conditional_root_probes']))
    def test_actual_end_writes(self): self.assertTrue(all(r['actual_end_dispatch_executed'] and r['terminal_mode'] == r['terminal_script_pointer'] == 0 for r in self.proof['conditional_root_probes']))
    def test_no_target_consumption(self): self.assertEqual([r['target_text_bytes_consumed'] for r in self.proof['conditional_root_probes']], [0, 0])
    def test_no_target_context(self): self.assertFalse(self.proof['selected_target_root_paths_bound']); self.assertFalse(self.proof['selected_target_consumer_executed'])
    def test_no_universal_unreachable(self): self.assertFalse(self.proof['all_roots_unreachable_claimed']); self.assertFalse(self.proof['whole_script_unreachable_claimed'])
    def test_no_lifetime_or_donor(self): self.assertFalse(self.proof['universal_heap_or_irq_lifetime_proven']); self.assertFalse(self.proof['donor_eligible']); self.assertFalse(self.proof['donor_leased'])
    def test_placeholder_source_only(self): self.assertEqual(self.proof['placeholder']['id'], 3); self.assertEqual(self.proof['placeholder']['source_meaning'], 'gStringVar2'); self.assertFalse(self.proof['placeholder']['actual_branch_bound'])
    def test_placeholder_extent_and_eos_unknown(self): self.assertFalse(self.proof['placeholder']['replacement_extent_bound']); self.assertFalse(self.proof['placeholder']['replacement_eos_bound'])
    def test_minimum_windows(self): self.assertEqual((len(v.FIXED_WINDOWS), sum(r['size'] for r in v.FIXED_WINDOWS)), (35, 619))
    def test_independent_thumb_encoder(self):
        for ins in v.INS.values(): self.assertEqual(v.chunk(self.raw, ins.address, ins.size), v.encoded(ins))
    def test_every_instruction_halfword_rejected_without_hash_guard(self):
        for ins in v.INS.values():
            for offset in range(0, ins.size, 2):
                with self.subTest(address=ins.address + offset), patch.object(v.d, 'signed', return_value=None), self.assertRaises(ValueError):
                    v.bind_semantics(self.mutated(ins.address + offset, 2))
    def test_every_evidence_byte_rejected(self):
        for row in v.FIXED_WINDOWS:
            for offset in range(row['size']):
                with self.subTest(address=row['address'] + offset), self.assertRaises(ValueError):
                    self.check(raw=self.mutated(row['address'] + offset))
    def test_every_literal_rejected_without_hash_guard(self):
        for address in v.LITERALS:
            with self.subTest(address=address), patch.object(v.d, 'signed', return_value=None), self.assertRaises(ValueError):
                v.bind_semantics(self.mutated(address, 4, 4))
    def test_every_script_byte_rejected_without_hash_guard(self):
        for address, size in [(r['script']['address'], 9) for r in v.ROOTS] + [(v.STANDARD2, 11)] + [(t['loadword_and_callstd']['address'], 8) for t in v.TEXTS]:
            for offset in range(size):
                with self.subTest(address=address + offset), patch.object(v.d, 'signed', return_value=None), self.assertRaises(ValueError):
                    v.bind_semantics(self.mutated(address + offset))
    def test_every_text_byte_reseal_rejected(self):
        for text in v.TEXTS:
            for offset in range(text['size']):
                raw = self.mutated(text['address'] + offset); review = copy.deepcopy(self.review); reseal(review, raw)
                with self.subTest(address=text['address'] + offset), self.assertRaises(ValueError): self.check(raw=raw, review=review)
    def test_root_chain_reseal_rejected(self):
        for root in v.ROOTS:
            for row in root['root_chain']:
                raw = self.mutated(row['address']); review = copy.deepcopy(self.review); reseal(review, raw)
                with self.subTest(role=row['role']), self.assertRaises(ValueError): self.check(raw=raw, review=review)
    def test_no_host_context_seed(self):
        with patch.object(v.rt, 'setmem', side_effect=AssertionError('host seed禁止')):
            v.compose_selected(self.raw, v.ROOTS[0])
    def test_explicit_initial_field_rejected(self):
        with self.assertRaises(ValueError): v.compose_selected(self.raw, v.ROOTS[0], initial_fields={v.CTX + 100: v.TEXTS[0]['address']})
    def test_incomplete_standard_rejected(self):
        with self.assertRaises(ValueError): v.compose_selected(self.raw, v.ROOTS[0], standard2_completed=False)
    def test_integer_completion_rejected(self):
        with self.assertRaises(ValueError): v.compose_selected(self.raw, v.ROOTS[0], standard2_completed=1)
    def test_root_substitution_direct_rejected(self):
        root = copy.deepcopy(v.ROOTS[0]); root['script']['address'] = 0x0818DB31
        with self.assertRaises(ValueError): v.compose_selected(self.raw, root)
    def test_standard_return_is_not_fallthrough(self): self.assertEqual([r['return_address'] for r in self.proof['conditional_root_probes']], [0x0818D832, 0x0818D7FA])
    def test_end_byte_mutation_rejected(self):
        for root in v.ROOTS:
            with self.assertRaises(ValueError): v.compose_selected(self.mutated(root['end_address']), root)
    def test_standard_slot_mutation_rejected(self):
        with self.assertRaises(ValueError): v.compose_selected(self.mutated(0x08163760, 4, 4), v.ROOTS[0])
    def test_stop_writer_mutation_rejected(self):
        with self.assertRaises(ValueError): v.compose_selected(self.mutated(0x080690C0, 2), v.ROOTS[0])
    def test_return_stack_pop_mutation_rejected(self):
        with self.assertRaises(ValueError): v.compose_selected(self.mutated(0x08069184, 2), v.ROOTS[0])
    def test_schema_boolean_rejected(self): self.reject_review(lambda r: r.update(schema_version=True))
    def test_review_extra_rejected(self): self.reject_review(lambda r: r.update(extra=True))
    def test_review_missing_rejected(self): self.reject_review(lambda r: r.pop('roots'))
    def test_review_classified_rejected(self): self.reject_review(lambda r: r.update(classified_hits=list(v.HITS)))
    def test_review_target_root_lift_rejected(self): self.reject_review(lambda r: r['claims'].update(selected_target_root_paths_bound=True))
    def test_review_consumer_lift_rejected(self): self.reject_review(lambda r: r['claims'].update(selected_target_consumer_executed=True))
    def test_review_natural_lift_rejected(self): self.reject_review(lambda r: r['claims'].update(actual_runtime_execution_observed=True))
    def test_review_unreachable_lift_rejected(self): self.reject_review(lambda r: r['claims'].update(all_roots_unreachable_claimed=True))
    def test_review_contract_lift_rejected(self): self.reject_review(lambda r: r['input_contract'].update(terminal='unconditional'))
    def test_review_root_object_rejected(self): self.reject_review(lambda r: r['roots'][0].update(object=1))
    def test_review_root_pointer_rejected(self): self.reject_review(lambda r: r['roots'][0].update(text_pointer=v.TEXTS[0]['address']))
    def test_review_root_end_rejected(self): self.reject_review(lambda r: r['roots'][0].update(end_address=0x0818DB31))
    def test_review_root_chain_drop_rejected(self): self.reject_review(lambda r: r['roots'][0]['root_chain'].pop())
    def test_review_text_extent_rejected(self): self.reject_review(lambda r: r['texts'][0].update(size=80))
    def test_review_placeholder_id_rejected(self): self.reject_review(lambda r: r['placeholder'].update(id=2))
    def test_review_placeholder_branch_rejected(self): self.reject_review(lambda r: r['placeholder'].update(actual_branch_bound=True))
    def test_review_placeholder_extent_rejected(self): self.reject_review(lambda r: r['placeholder'].update(replacement_extent_bound=True))
    def test_review_placeholder_eos_rejected(self): self.reject_review(lambda r: r['placeholder'].update(replacement_eos_bound=True))
    def test_review_placeholder_consumer_rejected(self): self.reject_review(lambda r: r['placeholder'].update(replacement_source_byte_consumer_executed=True))
    def test_review_dynamic_summary_substitution_rejected(self): self.reject_review(lambda r: r['placeholder'].update(source_meaning='DynamicPlaceholderTextUtil'))
    def test_review_window_drop_rejected(self): self.reject_review(lambda r: r['windows'].pop())
    def test_review_window_enlargement_rejected(self): self.reject_review(lambda r: r['windows'][0].update(size=4096))
    def test_current_identity_mismatch_rejected(self): self.reject_review(lambda r: r.update(required_candidate=v.DIAGNOSTIC))
    def test_diagnostic_identity_mismatch_rejected(self): self.reject_review(lambda r: r.update(diagnostic_input=v.CANDIDATE))
    def test_missing_hit_rejected(self):
        inherited = copy.deepcopy(self.inherited); inherited['hits'] = []
        with self.assertRaises(ValueError): self.check(inherited=inherited)
    def test_duplicate_hit_rejected(self):
        inherited = copy.deepcopy(self.inherited); inherited['hits'] *= 2
        with self.assertRaises(ValueError): self.check(inherited=inherited)
    def edit_hit_rejected(self, **kwargs):
        inherited = copy.deepcopy(self.inherited); inherited['hits'][0].update(**kwargs)
        review = v.make_review(None, inherited['hits'])
        with self.assertRaises(ValueError): self.check(inherited=inherited, review=review)
    def test_accepted_hit_rejected(self): self.edit_hit_rejected(accepted=True)
    def test_owned_hit_rejected(self): self.edit_hit_rejected(owner_candidates=['owner'])
    def test_hit_size_rejected(self): self.edit_hit_rejected(size=8)
    def test_hit_classification_rejected(self): self.edit_hit_rejected(classification='data')
    def test_hit_kind_rejected(self): self.edit_hit_rejected(kind='POINTER')
    def test_hit_sha_rejected(self): self.edit_hit_rejected(sha256='0' * 64)
    def test_hit_target_rejected(self): self.edit_hit_rejected(target=0)
    def test_all_input_fields_preserved(self):
        before = copy.deepcopy((self.inherited, self.review)); self.check(); self.assertEqual(before, (self.inherited, self.review))
    def test_source_each_mutation_rejected(self):
        for key in self.sources:
            sources = dict(self.sources); sources[key] += b'\n'
            with self.subTest(source=key), self.assertRaises(ValueError): self.check(sources=sources)
    def test_source_each_missing_rejected(self):
        for key in self.sources:
            sources = dict(self.sources); sources.pop(key)
            with self.subTest(source=key), self.assertRaises(ValueError): self.check(sources=sources)
    def test_source_extra_rejected(self):
        sources = dict(self.sources); sources['extra'] = b''
        with self.assertRaises(ValueError): self.check(sources=sources)
    def test_source_reseal_rejected(self): self.reject_review(lambda r: r['source_bindings']['pret-script.c'].update(sha256='0' * 64))
    def test_witness_always_rejected(self):
        for hit in [v.HITS[0], 0x0818034F, None]:
            with self.assertRaises(ValueError): v.evidence_template(hit)
    def test_geometry_always_rejected(self):
        for evidence in [self.proof, {'address': v.HITS[0], 'size': 4}, None]:
            with self.assertRaises(ValueError): v.witness_geometry(evidence)
    def test_proof_extra_rejected(self): self.reject_proof(lambda p: p.update(extra=True))
    def test_proof_missing_rejected(self): self.reject_proof(lambda p: p.pop('placeholder'))
    def test_proof_regions_lift_rejected(self): self.reject_proof(lambda p: p.update(count=1, hits=list(v.HITS)))
    def test_proof_byte_lift_rejected(self): self.reject_proof(lambda p: p.update(new_classified_bytes=4))
    def test_proof_unreachable_lift_rejected(self): self.reject_proof(lambda p: p.update(whole_script_unreachable_claimed=True))
    def test_proof_standard_effect_lift_rejected(self): self.reject_proof(lambda p: p.update(standard2_handler_runtime_effects_proven=True))
    def test_proof_conditional_requirement_drop_rejected(self): self.reject_proof(lambda p: p.update(conditional_return_probe_requires_standard2_completion_and_stack_preservation=False))
    def test_proof_consumer_lift_rejected(self): self.reject_proof(lambda p: p['conditional_root_probes'][0].update(target_text_bytes_consumed=60))
    def test_proof_eos_lift_rejected(self): self.reject_proof(lambda p: p['placeholder'].update(replacement_eos_bound=True))
    def test_proof_obligation_drop_rejected(self): self.reject_proof(lambda p: p['required_obligations'].pop())
    def test_proof_current_gate_lift_rejected(self): self.reject_proof(lambda p: p.update(current_candidate_measured=True))
    def test_proof_donor_lift_rejected(self): self.reject_proof(lambda p: p.update(donor_eligible=True))
    def test_proof_boolean_count_rejected(self): self.reject_proof(lambda p: p.update(count=False))
    def test_current_gate_boolean_only(self):
        with self.assertRaises(ValueError): v.validate_held_proof(self.proof, 0)
    def test_whole_current_gate(self):
        with patch.object(v, 'identity', return_value=v.DIAGNOSTIC), self.assertRaises(ValueError): v.regions(self.raw, self.inherited, self.review, self.sources)
    def test_whole_current_gate_enters_proof(self):
        with patch.object(v, 'identity', return_value=v.CANDIDATE), patch.object(v, '_regions', return_value=([], v.held_proof_template())) as call:
            rows, proof = v.regions(self.raw, self.inherited, self.review, self.sources)
            call.assert_called_once(); self.assertEqual(rows, []); self.assertTrue(v.validate_held_proof(proof, True))
    def test_review_roundtrip(self): self.assertEqual(v.make_review(None, self.inherited['hits']), self.review)
    def test_all_claims_unchanged(self):
        for key, value in v.CLAIMS.items(): self.assertEqual(self.proof[key], value)
    def test_invalid_loadword_type_rejected(self):
        with self.assertRaises(ValueError): v.script_encoded('loadword', True, v.TEXTS[0]['address'])
    def test_invalid_standard_type_rejected(self):
        with self.assertRaises(ValueError): v.script_encoded('callstd', True)
    def test_invalid_script_command_rejected(self):
        with self.assertRaises(ValueError): v.script_encoded('goto', 0x0818DB31)
