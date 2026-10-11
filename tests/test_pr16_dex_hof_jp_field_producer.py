"""新Flash scopeだけを意味operand由来の疎fixtureで検査する。ROMは不要。"""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_dex_hof_jp_field_producer as v


class SourceSparse:
    def __init__(self):
        self.cells = {}
        for mod, instructions in v.ALL_BLOCKS.values():
            for ins in instructions:
                self.put(ins.address, mod.encoded(ins))
        for address, value in v.ALL_WORDS.items():
            self.put(address, value.to_bytes(4, 'little'))
        for address, size, value in v.FIELDS.values():
            self.put(address, value.to_bytes(size, 'little'))

    def put(self, address, value):
        for offset, byte in enumerate(value):
            where = address+offset
            if where in self.cells and self.cells[where] != byte:
                raise ValueError('意味fixtureの重複不一致')
            self.cells[where] = byte

    def __len__(self):
        return v.CANDIDATE['size']

    def __getitem__(self, part):
        if not isinstance(part, slice) or part.step not in (None, 1):
            raise ValueError('疎fixtureは有限連続sliceのみ')
        addresses = range(0x08000000+part.start, 0x08000000+part.stop)
        if any(address not in self.cells for address in addresses):
            raise ValueError('未束縛byteを読まない')
        return bytes(self.cells[address] for address in addresses)


class ProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SourceSparse()
        cls.proof, cls.machine = v.compose_selected(cls.raw, return_machine=True)

    def test_one_flash_action_produced(self):
        self.assertEqual(self.proof['outer_actions'], [0,18,3,2])
        self.assertEqual(self.proof['outer_count'], 4)
        events = [r for r in self.proof['events'] if r['role']=='field_move_append']
        self.assertEqual(len(events), 1)
        self.assertEqual((events[0]['action'], events[0]['move']), (18,148))

    def test_same_task_actual_callback_cell(self):
        events = [r for r in self.proof['events'] if r['role']=='selector_callback']
        self.assertEqual(events, [dict(role='selector_callback', callback_cell=0x08419E3C,
                                       callback=0x08124F09, task_id=0)])
        self.assertEqual(self.machine.pc, 0x08124F08)
        self.assertEqual(self.machine.reg[0], self.proof['selected_task'])

    def test_stop_before_callback_body(self):
        self.assertNotIn(v.CALLBACK, v.INS)
        self.assertFalse(self.proof['callback_body_executed'])
        self.assertFalse(self.proof['badge_branch_proven'])
        self.assertFalse(self.proof['complete_text_reads_proven'])
        self.assertEqual(self.proof['newly_classified'], 0)

    def test_claims_are_conditional(self):
        self.assertTrue(self.proof['synthetic_contract_execution'])
        for field in ('actual_runtime_execution_observed', 'full_story_reachability_claimed',
                      'all_opaque_effects_proven', 'universal_allocation_epoch_proven',
                      'irq_noninterference_proven', 'indirect_reference_completeness_claimed', 'donor_eligible'):
            self.assertIs(self.proof[field], False)

    def test_new_count4_selection_outputs(self):
        rows = [r for r in self.proof['conditional_calls'] if r['target']==0x08122628]
        self.assertEqual(len(rows), 1)
        self.assertEqual([(f['address'],f['size'],f['value']) for f in rows[0]['conditional_outputs']],
                         [(v.CURSOR+2,1,0),(v.CURSOR+3,1,0),(v.CURSOR+4,1,3),
                          (v.CURSOR+11,1,1),(v.runtime.ROOT+16+12,1,0)])
        self.assertFalse(rows[0]['effects_discharged'])

    def test_count4_uses_actual_wrap_input(self):
        self.assertEqual(self.proof['selected_input_function'],0x081105B8)
        self.assertIs(self.proof['selection_wrap'],True)
        self.assertIs(self.proof['legacy_no_wrap_result_reused'],False)
        rows = [r for r in self.proof['events'] if r['role']=='count4_wrap_input']
        self.assertEqual(rows,[dict(role='count4_wrap_input',address=0x0812347C,
                                   input_function=0x081105B8,task_id=0)]*2)
        self.assertNotIn(0x08110624,v.INS)

    def test_profile_closed_and_type_strict(self):
        for key, value in (('held_item',True),('task_id',True),('held_item',2),
                           ('move_slots',[0,0,0,0]),('outer_actions',[0,3,2]),
                           ('normal_returns',1),('fields_preserved',False),('stack_nonalias',None)):
            profile = copy.deepcopy(v.PROFILE)
            profile[key] = value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                v.selected_profile(profile)
        profile = copy.deepcopy(v.PROFILE)
        profile['extra'] = True
        with self.assertRaises(ValueError): v.selected_profile(profile)

    def test_selection_count3_not_reused(self):
        for count in (3,True,4.0,None):
            with self.subTest(count=count), self.assertRaises(ValueError):
                v.selection_initialization(v.runtime.ROOT+16,count)

    def test_selection_five_outputs_not_weakened(self):
        for index in range(5):
            spec = copy.deepcopy(v.SELECTION_OUTPUT_SPEC)
            spec[index]['value'] ^= 1
            with self.subTest(index=index), self.assertRaises(ValueError):
                v.selection_initialization(v.runtime.ROOT+16,4,spec)

    def test_each_new_match_instruction_mutation_rejected(self):
        for ins in v.BLOCKS['field_match_append']:
            raw = SourceSparse()
            raw.cells[ins.address] ^= 1
            with self.subTest(address=ins.address), self.assertRaises(ValueError):
                v.bind_semantics(raw)

    def test_callback_pointer_mutation_rejected(self):
        for offset in range(4):
            raw = SourceSparse()
            raw.cells[v.CALLBACK_CELL+offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                v.compose_selected(raw)

    def test_each_move_table_field_mutation_rejected(self):
        for address, size, value in v.FIELDS.values():
            raw = SourceSparse()
            raw.cells[address] ^= 1
            with self.subTest(address=address), self.assertRaises(ValueError):
                v.bind_semantics(raw)

    def test_every_common_root_semantic_mutation_rejected(self):
        for address in sorted(v.INS):
            raw = copy.copy(self.raw)
            raw.cells = dict(self.raw.cells)
            raw.cells[address] ^= 1
            with self.subTest(address=address), self.assertRaises(ValueError):
                v.bind_semantics(raw)

    def test_no_sparse_zero_fallback(self):
        with self.assertRaises(ValueError): v.chunk(self.raw,0x08000000,2)

    def test_no_field_move_function_execution(self):
        self.assertFalse(any(r['target']==v.CALLBACK for r in self.proof['conditional_calls']))
        self.assertFalse(any(r['site']>=v.CALLBACK and r['site']<v.CALLBACK+0x300
                             for r in self.proof['conditional_calls']))

    def test_getter_move_conditions_exact(self):
        rows = [r for r in self.proof['conditional_calls'] if r['site']==0x0812322C]
        self.assertEqual(sum(r['return_value']==148 for r in rows), 1)
        self.assertEqual(sum(r['return_value']==0 for r in rows), 36)
        self.assertTrue(all(r['effects_discharged'] is False for r in rows))

    def test_same_setup_admission_retained(self):
        rows = [r for r in self.proof['events'] if r['role']=='admitted_same_task']
        self.assertEqual(rows, [dict(role='admitted_same_task',address=0x0811F5C4,task_id=0)])

    def test_normal_abi_and_live_fields_explicit(self):
        self.assertTrue(self.proof['conditional_calls'])
        self.assertTrue(all(r['normal_abi_return_required'] is True and r['required_fields']
                            and r['effects_discharged'] is False for r in self.proof['conditional_calls']))

    def test_live_fields_and_epoch_counterexamples(self):
        pointer = v.runtime.ROOT+16
        for phase in v.PHASE_FIELDS:
            for field in v.live_projection(pointer,phase):
                with self.subTest(phase=phase,field=field['role']), self.assertRaises(ValueError):
                    v.preservation_contract(pointer,phase,[(field['address'],1)])
            with self.assertRaises(ValueError): v.preservation_contract(pointer,phase,[],freed=(pointer,))
            with self.assertRaises(ValueError): v.preservation_contract(pointer,phase,[],heap_reinitialized=True)

    def test_unrelated_ram_not_frozen(self):
        for phase in v.PHASE_FIELDS:
            self.assertTrue(v.preservation_contract(v.runtime.ROOT+16,phase,[(0x0203E000,12)]))

    def test_opaque_caller_registers_not_assumed_preserved(self):
        self.assertIsInstance(self.machine.reg[12], v.runtime.Unknown)
        self.assertEqual(self.machine.read(v.CURSOR+2,1),1)

    def test_proof_has_no_payload_or_private_path(self):
        def visit(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&{'raw','rawhex','bytes','private_path','member_path'})
                for child in value.values(): visit(child)
            elif isinstance(value,list):
                for child in value: visit(child)
        visit(self.proof)

    def test_profile_and_proof_do_not_mutate_inputs(self):
        before = copy.deepcopy(v.PROFILE)
        profile = v.selected_profile()
        profile['move_slots'][0] = 0
        self.assertEqual(v.PROFILE,before)
        self.assertEqual(self.proof['profile'],before)

    def test_all_new_windows_are_bound_in_sparse(self):
        for address,size in v.WINDOWS.values():
            self.assertEqual(len(v.chunk(self.raw,address,size)),size)


if __name__ == '__main__':
    unittest.main()
