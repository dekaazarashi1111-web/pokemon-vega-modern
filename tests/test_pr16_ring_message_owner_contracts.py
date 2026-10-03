"""実callerの結合だけを検証。先行受入suite/nativeや採取は呼ばない。"""
import copy
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_owner_contracts as t

class JoinedCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=t.evaluated();cls.p=cls.r['producer']
    def test_391_distinct_conditions(self):self.assertEqual(sum(len(v)for k,v in self.r.items()if k!='executed_sites'),391)
    def test_364_producer_conditions(self):self.assertEqual(len(self.p),364)
    def test_256_configuration_bytes(self):self.assertEqual([r['speed_byte']for r in self.p[:256]],list(range(256)))
    def test_speed_zero_maps_127(self):self.assertEqual(self.p[0]['builder_speed'],127)
    def test_speed_one_maps_one(self):self.assertEqual(self.p[1]['builder_speed'],1)
    def test_other_speed_maps_two(self):self.assertEqual({r['builder_speed']for r in self.p[2:256]},{2})
    def test_no_immediate_render_mode(self):self.assertFalse({r['builder_speed']for r in self.p}&{0,255})
    def test_three_fonts(self):self.assertEqual({r['font']for r in self.p},{2,4,5})
    def test_chooser_truncation(self):
        for r in self.p:self.assertEqual(r['font'],4 if r['chooser']&255==0 else 5 if r['chooser']&255==1 else 2)
    def test_invalid_config_falls_back(self):self.assertEqual({r['builder_speed']for r in self.p if r['config_kind']!='valid'},{1})
    def test_no_false_native(self):self.assertTrue(all(r['native_observation']is False for r in self.p))
    def test_return_is_saved_lr_not_status(self):self.assertEqual({r['return_value']for r in self.p},{t.b.vm.RETURN})
    def test_abi_return(self):self.assertTrue(all(r['return_sp_r4_r11_proven']for r in self.p))
    def test_stack_bound(self):self.assertEqual(max(r['maximum_stack_bytes']for r in self.p),140)
    def test_residue_from_validator_lr(self):
        for r in self.p:self.assertEqual(r['residue_provenance'],dict(site=0x093bd9a8,address=t.b.vm.SP-60,size=4,value=t.SAVED_LR))
    def test_residue_not_zeroed(self):
        for r in self.p:
            if not r['null_fonts']:self.assertEqual(bytes.fromhex(r['pool0_bytes'])[14:16],b'\x37\x09')
    def test_flags_upper_bytes_preserved(self):
        for r in self.p:self.assertEqual(r['flags_word'],0x78654300|((r['input_flags']|1)&~2))
    def test_slot_zero_only(self):
        for r in self.p:
            if not r['null_fonts']:self.assertEqual(bytes.fromhex(r['pool0_bytes'])[4],0)
    def test_slot_callback_pointer_is_null(self):
        for r in self.p:
            if not r['null_fonts']:self.assertEqual(bytes.fromhex(r['pool0_bytes'])[16:20],bytes(4))
    def test_slot_font_is_caller_selected(self):
        for r in self.p:
            if not r['null_fonts']:self.assertEqual(bytes.fromhex(r['pool0_bytes'])[5],r['font'])
    def test_slot_mode_normalized(self):
        for r in self.p:
            if not r['null_fonts']:self.assertEqual(bytes.fromhex(r['pool0_bytes'])[29],int(r['builder_speed']==2))
    def test_full_task_does_not_allocate(self):
        rows=[r for r in self.p if r['task_layout']=='full'];self.assertTrue(rows)
        self.assertTrue(all(not r['task']['allocated']and r['task']['slot']is None for r in rows))
    def test_full_task_still_writes_text(self):
        rows=[r for r in self.p if r['task_layout']=='full' and not r['null_fonts']]
        self.assertTrue(rows);self.assertTrue(all(r['text_slot_written']for r in rows))
    def test_last_task_slot(self):self.assertEqual({r['task']['slot']for r in self.p if r['task_layout']=='last'},{15})
    def test_priority_middle_links(self):self.assertEqual({tuple(r['task']['order'])for r in self.p if r['task_layout']=='middle'},{(5,2,0,9)})
    def test_task_callback_and_priority(self):
        for r in self.p:self.assertEqual((r['task']['task_callback'],r['task']['priority']),(0x08068c31,80))
    def test_null_font_no_slot_write(self):self.assertTrue(all(not r['text_slot_written']for r in self.p if r['null_fonts']))
    def test_null_font_still_allocates_task(self):self.assertTrue(all(r['task']['allocated']for r in self.p if r['null_fonts']and r['task_layout']=='empty'))
    def test_9_joined_drains(self):self.assertEqual(len(self.r['drain']),9)
    def test_drain_inherits_exact_producer(self):
        parents={r['case']:r for r in self.p}
        for row in self.r['drain']:self.assertEqual(row['input_pool0'],parents[row['parent_producer']]['pool0'])
    def test_all_selected_callbacks_executed(self):self.assertEqual({r['callback']for r in self.r['drain']},{0x080053b5,0x08005425,0x0800545d})
    def test_fast_queue_not_dma(self):
        self.assertEqual(sum(r['resource_queue_requests']for r in self.r['drain']),3)
        self.assertFalse(any(r['actual_dma_execution']for r in self.r['drain']))
    def test_10_producer_bounds(self):self.assertEqual(len(self.r['negative_producer']),10)
    def test_6_drain_bounds(self):self.assertEqual(len(self.r['negative_drain']),6)
    def test_failure_never_marked_return(self):
        self.assertTrue(all(not r['returned']and not r['return_sp_r4_r11_proven']for k in ('negative_producer','negative_drain','pending_task')for r in self.r[k]))
    def test_partial_slot_before_pool_fault(self):
        row=next(r for r in self.r['negative_drain']if r['case']=='drain-short-only-slot0')
        self.assertEqual((row['nonstack_write_count'],row['read_fault']['address']),(12,t.prior.POOL+59))
    def test_missing_callback_word_no_write(self):
        row=next(r for r in self.r['negative_drain']if r['case']=='drain-short-callback-word');self.assertEqual(row['nonstack_write_count'],0)
    def test_task_prefix_not_rolled_back(self):
        row=next(r for r in self.r['negative_producer']if r['case']=='producer-short-task-table');self.assertEqual(row['nonstack_write_count'],2167)
    def test_pending_task_registration_not_execution(self):
        self.assertEqual(len(self.r['pending_task']),2)
        for r in self.r['pending_task']:self.assertEqual((r['stop'],r['nonstack_write_count']),(['保存node境界で停止',0x08068c30],0))
    def test_evaluation_once(self):self.assertEqual(t.evaluated.cache_info().misses,1)

class InputAndMutationTests(unittest.TestCase):
    def test_case_duplicates_rejected_by_construction(self):self.assertEqual(len(t.configurations()),len(set(t.configurations())))
    def test_speed_bool_rejected(self):
        with self.assertRaises(ValueError):t.Case(speed=True).validate()
    def test_chooser_fallback_not_synthesized(self):
        with self.assertRaises(ValueError):t.Case(chooser=255).validate()
    def test_missing_terminator_rejected(self):
        with self.assertRaises(ValueError):t.Case(source=b'abc').validate()
    def test_unbounded_control_rejected(self):
        with self.assertRaises(ValueError):t.Case(source=b'\xfd\x01\xff').validate()
    def test_table_mutation_rejected(self):
        _,a,_,_=t.saved_inputs();row=copy.deepcopy(a['tables'][0]);row['hex']='00'+row['hex'][2:]
        with self.assertRaises(ValueError):t.table(row,192)
    def test_saved_speed_opcode_mutation_rejected(self):
        nodes,a,context,owner=t.saved_inputs();nodes=copy.deepcopy(nodes)
        next(n for n in nodes if n['address']==0x0937856c)['hex']='7d32'
        with self.assertRaises(ValueError):t.validate_saved(nodes,a,context,owner)
    def test_speed_mutation_breaks_join_oracle(self):
        nodes,a,context,_=t.saved_inputs();nodes=copy.deepcopy(nodes)
        next(n for n in nodes if n['address']==0x0937856c)['hex']='7d32'
        case=t.Case(speed=0);seg=t.fixture(case,a,context);m,stop=t.invoke(nodes,seg)
        self.assertIsNone(stop);e,allocation=t.expected(case,seg)
        with self.assertRaises(ValueError):t.check_result(case,m,e,allocation,a['selected_fonts'])
    def test_extra_write_is_rejected(self):
        # 実行済みcaseを再実行せず、観測write列の改変を拒否させる。
        _,a,context,_=t.saved_inputs();case=t.Case();seg=t.fixture(case,a,context);e,allocation=t.expected(case,seg)
        corrupted=SimpleNamespace(nonstack_writes=lambda:[*e.writes,(t.FLAGS,1,0)])
        with self.assertRaises(ValueError):t.check_result(case,corrupted,e,allocation,a['selected_fonts'])
    def test_trim_target_must_be_unique(self):
        with self.assertRaises(ValueError):t.trim([(1,b'x',False),(1,b'y',False)],1,0)

if __name__=='__main__':unittest.main()
