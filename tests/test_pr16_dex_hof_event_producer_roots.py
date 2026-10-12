"""新登録2根/追加grammar/FD03分岐だけの閉鎖契約と過大主張の反証。"""
import copy, hashlib, json, unittest
from unittest.mock import patch
import pr16_dex_hof_event_producer_roots as v
FIXTURE = None
class Overlay:
    def __init__(self, raw, address, size=1, xor=1):
        self.raw, self.address = raw, address - 0x08000000
        self.value = (int.from_bytes(v.chunk(raw, address, size), 'little') ^ xor).to_bytes(size, 'little')
    def __len__(self): return len(self.raw)
    def __getitem__(self, key):
        if isinstance(key, int): return self[key:key + 1][0]
        data = bytearray(self.raw[key]); left = max(key.start, self.address); right = min(key.stop, self.address + len(self.value))
        if left < right: data[left - key.start:right - key.start] = self.value[left - self.address:right - self.address]
        return bytes(data)

def reseal(obj, raw):
    if isinstance(obj, dict):
        if {'address', 'size', 'sha256'} <= obj.keys(): obj['sha256'] = hashlib.sha256(v.chunk(raw, obj['address'], obj['size'])).hexdigest()
        for value in obj.values(): reseal(value, raw)
    elif isinstance(obj, list):
        for value in obj: reseal(value, raw)

class EventProducerRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURE is None: raise RuntimeError('明示的な必要窓だけのFIXTUREが必要')
        cls.raw, cls.inherited, cls.review, cls.sources = FIXTURE
        cls.regions, cls.proof = v._regions(*FIXTURE)
    def check(self, raw=None, inherited=None, review=None, sources=None):
        return v._regions(self.raw if raw is None else raw, self.inherited if inherited is None else inherited, self.review if review is None else review, self.sources if sources is None else sources)
    def reject_review(self, edit):
        r=copy.deepcopy(self.review); edit(r)
        with self.assertRaises((ValueError, KeyError, TypeError)): self.check(review=r)
    def reject_proof(self, edit):
        p=copy.deepcopy(self.proof); edit(p)
        with self.assertRaises((ValueError, KeyError, TypeError)): v.validate_held_proof(p)
    def edit_hit(self, **kwargs):
        inherited=copy.deepcopy(self.inherited); inherited['hits'][0].update(**kwargs)
        with self.assertRaises((ValueError, TypeError)): self.check(inherited=inherited, review=v.make_review(None,inherited['hits']))
    def test_guard_api(self): self.assertEqual(v.TYPE_CATEGORY,'guard'); self.assertEqual(v.CLASSIFIED_HITS,()); self.assertEqual(v.KIND,'held_event_producer_registered_roots')
    def test_zero_regions(self): self.assertEqual(self.regions,[])
    def test_held_hit_only(self): self.assertEqual(self.proof['held_hits'],[0x0818DD5D]); self.assertEqual(self.proof['hits'],[])
    def test_zero_classified_bytes(self): self.assertEqual(self.proof['new_classified_bytes'],0)
    def test_registered_roots(self): self.assertEqual([r['script']for r in v.ROOTS],[0x0818D4F2,0x0818D143])
    def test_registered_owners(self): self.assertEqual([r['owner_id']for r in v.ROOTS],['OBJECT:10/2:0','OBJECT:21/0:0'])
    def test_direct_graph_57_67(self): self.assertEqual([g['state_count']for g in self.proof['direct_graphs']],[57,67])
    def test_standard_expanded_graph_77_83(self): self.assertEqual([g['state_count']for g in self.proof['graphs']],[77,83])
    def test_no_remaining_grammar_blocker(self): self.assertTrue(all(not g['unhandled_opcodes']and g['bounded_graph_complete']for g in self.proof['graphs']))
    def test_target_path_not_found(self): self.assertTrue(all(g['target_loadwords_found']==[]for g in self.proof['graphs']))
    def test_no_unreachable_lift(self): self.assertFalse(self.proof['all_roots_unreachable_claimed']); self.assertFalse(self.proof['whole_script_unreachable_claimed'])
    def test_old_stop_commands_present(self):
        nodes={r['address']:r for g in self.proof['graphs'] for r in g['nodes']}
        self.assertEqual(nodes[0x0818D52F]['command'],'compare_var_to_var'); self.assertEqual(nodes[0x08193E86]['command'],'incrementgamestat')
    def test_new_command_sizes(self): self.assertEqual({o:v.command_size(o)for o in (34,195,125,41,79,81,156,158)},{34:5,195:2,125:4,41:3,79:7,81:3,156:3,158:3})
    def test_new_handlers_8(self): self.assertEqual(len(v.NEW_HANDLERS),8)
    def test_no_handler_runtime_claim(self): self.assertFalse(self.proof['handler_effects_executed']); self.assertFalse(self.proof['registered_root_runtime_execution_proven'])
    def test_standard4_5_expanded(self):
        targets={s['address'] for g in self.proof['graphs']for r in g['nodes']if r['opcode']==9 for s in r['successors']}
        self.assertEqual(targets,{0x08192DA5,0x08192DAD})
    def test_actual_compare_hook_is_preserved(self): self.assertEqual(v.d.u32(self.raw,0x0806DC4C),0x090970DD)
    def test_placeholder_current_slot(self): self.assertEqual(self.proof['placeholder']['table_slot'],0x081F1370)
    def test_placeholder_current_callee(self): self.assertEqual(self.proof['placeholder']['callee'],0x08008CB0)
    def test_placeholder_pointer_only(self): self.assertEqual(self.proof['placeholder']['returned_address'],0x02021C60)
    def test_placeholder_steps_14(self): self.assertEqual(self.proof['placeholder']['machine_instructions'],14)
    def test_placeholder_reads_no_source(self): self.assertEqual(self.proof['placeholder']['source_bytes_read'],0); self.assertEqual(self.proof['placeholder']['text_bytes_read'],0)
    def test_placeholder_producer_still_unknown(self): self.assertFalse(self.proof['placeholder']['producer_bound']); self.assertFalse(self.proof['replacement_eos_bound'])
    def test_placeholder_extent_still_unknown(self): self.assertFalse(self.proof['replacement_extent_bound'])
    def test_placeholder_direct_argument_condition(self): self.assertTrue(self.proof['placeholder']['direct_id_argument_is_entry_condition']); self.assertFalse(self.proof['placeholder']['natural_text_consumer_call_proven'])
    def test_minimum_evidence(self): self.assertEqual((len(v.FIXED_WINDOWS),sum(w['size']for w in v.FIXED_WINDOWS)),(47,1162))
    def test_instruction_count_176(self): self.assertEqual(len(v.INS),176)
    def test_independent_thumb_encoder(self):
        for ins in v.INS.values(): self.assertEqual(v.chunk(self.raw,ins.address,ins.size),v.encoded(ins))
    def test_each_instruction_halfword_rejected_without_hash_guard(self):
        for ins in v.INS.values():
            for off in range(0,ins.size,2):
                with self.subTest(address=ins.address+off),patch.object(v.d,'signed',return_value=None),self.assertRaises(ValueError): v.bind_semantics(Overlay(self.raw,ins.address+off,2))
    def test_each_literal_rejected_without_hash_guard(self):
        for address in v.LITERALS:
            with self.subTest(address=address),patch.object(v.d,'signed',return_value=None),self.assertRaises(ValueError): v.bind_semantics(Overlay(self.raw,address,4,4))
    def test_each_evidence_byte_rejected(self):
        for w in v.FIXED_WINDOWS:
            for off in range(w['size']):
                with self.subTest(address=w['address']+off),self.assertRaises(ValueError): self.check(raw=Overlay(self.raw,w['address']+off))
    def test_every_graph_command_byte_rejected_without_hash_guard(self):
        commands={(n['address'],n['size'])for g in v.GRAPH_PROOFS for n in g['nodes']}
        for address,size in commands:
            for off in range(size):
                with self.subTest(address=address+off),patch.object(v.d,'signed',return_value=None),self.assertRaises(ValueError): self.check(raw=Overlay(self.raw,address+off))
    def test_all_root_chains_reseal_rejected(self):
        for r in v.ROOTS:
            for w in r['root_chain']:
                raw=Overlay(self.raw,w['address']);review=copy.deepcopy(self.review);reseal(review,raw)
                with self.subTest(address=w['address']),self.assertRaises(ValueError): self.check(raw=raw,review=review)
    def test_text_reseal_rejected(self):
        for t in v.TEXTS:
            for off in range(t['size']):
                raw=Overlay(self.raw,t['address']+off);review=copy.deepcopy(self.review);reseal(review,raw)
                with self.subTest(address=t['address']+off),self.assertRaises(ValueError): self.check(raw=raw,review=review)
    def test_bool_opcode_rejected(self):
        with self.assertRaises(ValueError):v.command_size(True)
    def test_unknown_grammar_rejected(self):
        with self.assertRaises(ValueError):v.command_size(255)
    def test_graph_integer_mode_rejected(self):
        with self.assertRaises(ValueError):v.trace_graph(self.raw,v.ROOTS[0],1)
    def test_root_substitution_rejected(self):
        r=copy.deepcopy(v.ROOTS[0]);r['script']=0x0818DB31
        with self.assertRaises(ValueError):v.trace_graph(self.raw,r)
    def test_placeholder_no_seed_api(self):
        with self.assertRaises(ValueError):v.placeholder_probe(self.raw,initial_fields={0x02021C60:255})
    def test_placeholder_no_setmem_used(self):
        with patch.object(v.rt,'setmem',side_effect=AssertionError('host seed禁止')): v.placeholder_probe(self.raw)
    def test_placeholder_different_id_rejected(self):
        for value in (0,2,4,14,True):
            with self.subTest(value=value),self.assertRaises(ValueError):v.placeholder_probe(self.raw,value)
    def test_source_each_mutation_rejected(self):
        for key in self.sources:
            sources=dict(self.sources);sources[key]+=b'\n'
            with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=sources)
    def test_source_each_missing_rejected(self):
        for key in self.sources:
            sources=dict(self.sources);sources.pop(key)
            with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=sources)
    def test_source_extra_rejected(self):
        sources=dict(self.sources);sources['extra']=b''
        with self.assertRaises(ValueError):self.check(sources=sources)
    def test_source_reseal_rejected(self): self.reject_review(lambda r:r['source_bindings']['pret-script_cmd_table.inc'].update(sha256='0'*64))
    def test_review_json_roundtrip(self): self.check(review=json.loads(json.dumps(self.review)))
    def test_review_extra_rejected(self): self.reject_review(lambda r:r.update(extra=True))
    def test_review_missing_rejected(self): self.reject_review(lambda r:r.pop('roots'))
    def test_review_boolean_schema_rejected(self): self.reject_review(lambda r:r.update(schema_version=True))
    def test_review_current_identity_rejected(self): self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC))
    def test_review_diagnostic_identity_rejected(self): self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
    def test_review_classified_lift_rejected(self): self.reject_review(lambda r:r.update(classified_hits=list(v.HITS)))
    def test_review_root_path_lift_rejected(self): self.reject_review(lambda r:r['claims'].update(selected_target_root_paths_bound=True))
    def test_review_consumer_lift_rejected(self): self.reject_review(lambda r:r['claims'].update(selected_target_consumer_executed=True))
    def test_review_graph_drop_rejected(self): self.reject_review(lambda r:r['graphs'][0]['nodes'].pop())
    def test_review_graph_extra_rejected(self): self.reject_review(lambda r:r['graphs'][0]['nodes'].append(dict(address=0x0818DB31)))
    def test_review_graph_edge_rejected(self): self.reject_review(lambda r:r['graphs'][0]['nodes'][0].update(successors=[]))
    def test_review_graph_stack_rejected(self): self.reject_review(lambda r:r['graphs'][0]['nodes'][0].update(stack=[0x0818DB31]))
    def test_review_graph_bool_count_rejected(self): self.reject_review(lambda r:r['graphs'][0].update(state_count=True))
    def test_review_direct_graph_claim_rejected(self): self.reject_review(lambda r:r['direct_graphs'][0].update(runtime_effects_proven=True))
    def test_review_grammar_extent_rejected(self): self.reject_review(lambda r:r['grammar'][0].update(operands='WW'))
    def test_review_handler_extent_rejected(self): self.reject_review(lambda r:r['new_handlers'][0].update(size=2))
    def test_review_hook_hidden_rejected(self): self.reject_review(lambda r:r['input_contract'].update(current_handlers='stock'))
    def test_review_placeholder_source_rejected(self): self.reject_review(lambda r:r['placeholder'].update(returned_address=0x02021C4C))
    def test_review_placeholder_producer_lift_rejected(self): self.reject_review(lambda r:r['placeholder'].update(producer_bound=True))
    def test_review_placeholder_extent_lift_rejected(self): self.reject_review(lambda r:r['placeholder'].update(replacement_extent_bound=True))
    def test_review_placeholder_eos_lift_rejected(self): self.reject_review(lambda r:r['placeholder'].update(replacement_eos_bound=True))
    def test_review_window_drop_rejected(self): self.reject_review(lambda r:r['windows'].pop())
    def test_review_window_enlargement_rejected(self): self.reject_review(lambda r:r['windows'][0].update(size=4096))
    def test_all_inherited_fields_preserved(self):
        before=copy.deepcopy((self.inherited,self.review));self.check();self.assertEqual(before,(self.inherited,self.review))
    def test_missing_hit_rejected(self):
        x=copy.deepcopy(self.inherited);x['hits']=[]
        with self.assertRaises(ValueError):self.check(inherited=x)
    def test_duplicate_hit_rejected(self):
        x=copy.deepcopy(self.inherited);x['hits']*=2
        with self.assertRaises(ValueError):self.check(inherited=x)
    def test_owned_hit_rejected(self):self.edit_hit(owner_candidates=['owner'])
    def test_accepted_hit_rejected(self):self.edit_hit(accepted=True)
    def test_hit_size_rejected(self):self.edit_hit(size=8)
    def test_hit_classification_rejected(self):self.edit_hit(classification='data')
    def test_hit_kind_rejected(self):self.edit_hit(kind='POINTER')
    def test_hit_sha_rejected(self):self.edit_hit(sha256='0'*64)
    def test_hit_target_rejected(self):self.edit_hit(target=0)
    def test_proof_extra_rejected(self):self.reject_proof(lambda p:p.update(extra=True))
    def test_proof_missing_rejected(self):self.reject_proof(lambda p:p.pop('placeholder'))
    def test_proof_type_lift_rejected(self):self.reject_proof(lambda p:p.update(count=1,hits=list(v.HITS),new_classified_bytes=4))
    def test_proof_unreachable_lift_rejected(self):self.reject_proof(lambda p:p.update(all_roots_unreachable_claimed=True))
    def test_proof_opaque_effect_lift_rejected(self):self.reject_proof(lambda p:p.update(opaque_callee_effects_proven=True))
    def test_proof_consumer_lift_rejected(self):self.reject_proof(lambda p:p.update(selected_target_consumer_executed=True))
    def test_proof_placeholder_consumption_lift_rejected(self):self.reject_proof(lambda p:p['placeholder'].update(source_bytes_read=20))
    def test_proof_natural_call_lift_rejected(self):self.reject_proof(lambda p:p['placeholder'].update(natural_text_consumer_call_proven=True))
    def test_proof_obligation_drop_rejected(self):self.reject_proof(lambda p:p['required_obligations'].pop())
    def test_proof_current_gate_lift_rejected(self):self.reject_proof(lambda p:p.update(current_candidate_measured=True))
    def test_proof_donor_lift_rejected(self):self.reject_proof(lambda p:p.update(donor_eligible=True))
    def test_proof_owner_lift_rejected(self):self.reject_proof(lambda p:p.update(owner_transferred=True))
    def test_proof_retirement_lift_rejected(self):self.reject_proof(lambda p:p.update(retired=True))
    def test_proof_boolean_count_rejected(self):self.reject_proof(lambda p:p.update(count=False))
    def test_current_gate_boolean_only(self):
        with self.assertRaises(ValueError):v.validate_held_proof(self.proof,0)
    def test_whole_current_identity_required(self):
        with patch.object(v,'identity',return_value=v.DIAGNOSTIC),self.assertRaises(ValueError):v.regions(*FIXTURE)
    def test_whole_current_gate_sets_true_only_after_identity(self):
        original=v.identity
        with patch.object(v,'identity',side_effect=lambda x:v.CANDIDATE if x is self.raw else original(x)):
            rows,p=v.regions(*FIXTURE);self.assertEqual(rows,[]);self.assertTrue(p['current_candidate_measured']);v.validate_held_proof(p,True)
    def test_evidence_template_never_promotes(self):
        for hit in (v.HITS[0],0,None):
            with self.assertRaises(ValueError):v.evidence_template(hit)
    def test_witness_geometry_never_promotes(self):
        with self.assertRaises(ValueError):v.witness_geometry(self.proof)
