"""新しいstate0帰還とoption境界だけを検査。旧単独検証は起動しない。"""
from pathlib import Path
import copy
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_state0_completion_contracts as t

ROW=t.w.b.word(0x0843d000)+t.w.b.word(0x0843e000)
DATA=bytes(range(32))

class State0CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c,cls.a,cls.old=t.inputs()
        cls.rows=t.completion_contracts(ROW.hex(),DATA.hex())
        cls.by={r['case']:r for r in cls.rows}
        cls.options=t.option_contracts()

    def test_inputs_preserve_prior_scope(self):
        self.assertFalse(self.a['state0_to1_proven']);self.assertTrue(self.a['palette32_two_copies_conditional_proven'])

    def test_option_count(self):self.assertEqual(len(self.options),263)
    def test_all_byte_values(self):self.assertEqual([r['option_byte']for r in self.options[:256]],list(range(256)))
    def test_exact_unsigned_shift(self):
        for v,r in enumerate(self.options[:256]):
            self.assertEqual(r['raw_index'],v>>3)
            self.assertEqual(r['read_fault'],dict(address=t.ROW+(v>>3)*8,size=4,site=0x081530b8))
    def test_short_global(self):
        for r in self.options[256:260]:self.assertEqual(r['read_fault'],dict(address=t.GLOBAL,size=4,site=0x081530f4))
    def test_null_is_not_valid_pointer(self):self.assertEqual(self.options[260]['read_fault']['address'],0x14)
    def test_unmapped_pointer(self):self.assertEqual(self.options[261]['read_fault']['address'],t.OBJECT+0x114)
    def test_missing_option(self):self.assertEqual(self.options[262]['read_fault'],dict(address=t.OPTION,size=1,site=0x081530f6))
    def test_option_no_effects_or_valid_table_claim(self):
        self.assertTrue(all(r['nonstack_writes']==0 and not r['valid_table_length_proven']for r in self.options))
    def test_invalid_option(self):
        for v in(-1,256,True):
            with self.assertRaises(ValueError):t.select_case(self.c,self.old,v)
    def test_row_identity(self):
        row=t.selected_row(ROW);self.assertEqual(row['identity'],t.s.identity(ROW));self.assertEqual(row['index'],0)
    def test_row_width(self):
        for data in(ROW[:-1],ROW+b'\0',bytearray(ROW)):
            with self.assertRaises(ValueError):t.selected_row(data)
    def test_row_bad_pointers(self):
        for address in(0,0x02000000,0x08000001,0x09fffff0):
            with self.assertRaises(ValueError):t.selected_row(t.w.b.word(address)+ROW[4:])
            with self.assertRaises(ValueError):t.selected_row(ROW[:4]+t.w.b.word(address))
    def test_75_returns_43_stops(self):
        self.assertEqual(len(self.rows),118);self.assertEqual(sum(r['returned']for r in self.rows),75)
    def test_saved_registers_all_returns(self):
        self.assertTrue(all(r['return_sp_r4_r11_proven']and r['state_after']==1 for r in self.rows if r['returned']))
    def test_all_task_slots(self):
        self.assertEqual({r['parameters']['task_id']for r in self.rows if r['returned']},set(range(16)))
    def test_bios_history_six_copies(self):
        for r in self.rows[:75]:self.assertEqual(r['bios_written_units'],[10,10,16,16,16,16])
    def test_full_queue_not_render_success(self):
        for i in range(16):
            r=self.by[f'task{i}-full'];self.assertTrue(r['returned']);self.assertEqual(r['queue_reservations'],[])
            self.assertFalse(r['dma_execution_observed'])
    def test_single_free_queue(self):
        r=self.by['one-free-queue'];self.assertEqual(len(r['queue_reservations']),1);self.assertTrue(r['returned'])
    def test_lower_option_bits_do_not_change_writes(self):
        for v in range(1,8):self.assertEqual(self.by[f'lower-bits-{v}']['write_identity'],self.by['task0-free']['write_identity'])
    def test_partial_row_first_word(self):
        for n in range(4):
            r=self.by[f'row-short-{n}'];self.assertEqual(r['write_count'],r['phase_ends']['prefix'])
            self.assertEqual(r['completed_bios_copies'],4)
    def test_partial_row_second_word_keeps_queue(self):
        for n in range(4,8):
            r=self.by[f'row-short-{n}'];self.assertEqual(r['write_count'],r['phase_ends']['queue'])
    def test_partial_palette(self):
        for n in range(32):
            r=self.by[f'palette-short-{n}'];self.assertEqual(r['write_count'],r['phase_ends']['queue']+n//2)
            self.assertEqual(r['state_after'],0)
    def test_readonly_tail_keeps_prior_copies(self):
        for dest,extra in((t.DEST1,10),(t.DEST2,26)):
            r=self.by[f'palette-readonly-{dest:x}'];self.assertEqual(r['write_count'],r['phase_ends']['queue']+extra)
    def test_state_write_failure_not_accepted(self):
        r=self.by['state-readonly'];self.assertEqual(r['completed_bios_copies'],6)
        self.assertFalse(r['returned']);self.assertEqual(r['state_after'],0)
    def test_seventh_bios_plan_rejected(self):
        with self.assertRaises(ValueError):t.Machine(self.c,[],(),self.old['new_nodes'],[(0,0,0)]*7)
    def test_unplanned_bios_rejected_before_writes(self):
        m=t.Machine(self.c,[],(t.b.SOURCE,t.DEST1,10),self.old['new_nodes'])
        with self.assertRaisesRegex(ValueError,'BIOS許可列/予算'):m.run(t.w.BIOS_COPY|1)
        self.assertEqual(m.bios_events,[]);self.assertEqual(m.nonstack_writes(),[])
    def test_invalid_options_and_data_rejected(self):
        row=t.selected_row(ROW)
        for kw in(dict(option=8),dict(mode=2),dict(task_id=16),dict(bg=4),dict(unknown=1)):
            with self.assertRaises(ValueError):t.segments(self.c,self.a,self.old,row,DATA,kw)
        with self.assertRaises(ValueError):t.segments(self.c,self.a,self.old,row,DATA[:-1],{})
    def test_mutated_write_detected(self):
        row=t.selected_row(ROW);seg,opt=t.segments(self.c,self.a,self.old,row,DATA,{})
        e,_=t.expected(seg,self.a,row,DATA,opt)
        writes=copy.deepcopy(e.writes);writes[-1]=(writes[-1][0],2,2)
        with patch.object(t,'expected',return_value=(type('Expected',(),{'writes':writes})(),{})):
            with self.assertRaises(ValueError):t.task_case(self.c,self.a,self.old,row,DATA,'mutation',{})
    def test_no_native_or_full_table_claim(self):
        self.assertTrue(all(not r['bios_execution_observed']and not r['native_observation']for r in self.rows))
        self.assertEqual(t.EXTRA_CODE,())

if __name__=='__main__':unittest.main()
