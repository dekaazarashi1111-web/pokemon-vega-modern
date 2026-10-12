"""新規除算・周波数契約の検査。既読の独立audio/renderer/native工程は実行しない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_audio_tail_contracts as t

class AudioTailContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis'];cls.cases,cls.groups=t.evaluated()
    def rows(self,prefix):return [r for r in self.cases.rows if r['case'].startswith(prefix)]
    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a,self.context)
    def test_counts(self):self.assertEqual(self.groups,dict(zip(t.GROUPS,(304,6,24,90,8,2,3,2))))
    def test_unique_cases(self):self.assertEqual(len({r['case']for r in self.cases.rows}),439)
    def test_return_count(self):self.assertEqual(sum(r['returned']for r in self.cases.rows),418)
    def test_stop_count(self):self.assertEqual(sum(not r['returned']for r in self.cases.rows),21)
    def test_stack_bound(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in self.cases.rows),512)
    def test_return_abi(self):
        for r in self.cases.rows:self.assertEqual(r['return_sp_r4_r11_proven'],r['returned'])
    def test_new_division_sites_used(self):self.assertTrue({t.DIV&~1,0x081c7fbe}<=self.cases.sites)
    def test_new_restart_used(self):self.assertIn(t.ON&~1,self.cases.sites)
    def test_exception_not_executed(self):self.assertNotIn(t.ZERO,self.cases.sites)
    def test_bios_not_executed(self):self.assertTrue({t.audio.BIOS,t.prior.BIOS}.isdisjoint(self.cases.sites))
    def test_signed_truncation(self):self.assertEqual(t.quotient((-7)&t.MASK,3),(-2)&t.MASK)
    def test_negative_divisor(self):self.assertEqual(t.quotient(7,(-3)&t.MASK),(-2)&t.MASK)
    def test_double_negative(self):self.assertEqual(t.quotient((-7)&t.MASK,(-3)&t.MASK),2)
    def test_minimum_word_wrap(self):self.assertEqual(t.quotient(0x80000000,0xffffffff),0x80000000)
    def test_zero_numerator(self):self.assertEqual(t.quotient(0,0x80000000),0)
    def test_bool_word_rejected(self):
        with self.assertRaises(ValueError):t.signed(True)
    def test_negative_word_rejected(self):
        with self.assertRaises(ValueError):t.signed(-1)
    def test_word_overflow_rejected(self):
        with self.assertRaises(ValueError):t.quotient(1<<32,1)
    def test_zero_oracle_rejected(self):
        with self.assertRaises(ValueError):t.quotient(1,0)
    def test_exception_preserves_no_ram_write(self):
        for r in self.rows('division_zero-'):self.assertEqual(r['nonstack_write_count'],0);self.assertFalse(r['returned'])
    def test_restart_magic_noop(self):
        e=t.b.Expected(t.fixture(self.a));t.on_writes(e);self.assertEqual(e.writes,[])
    def test_restart_lock_restored(self):
        e=t.b.Expected(t.fixture(self.a,t.audio.MAGIC+10));t.on_writes(e)
        self.assertEqual(e.read(t.audio.SOUND,4),t.audio.MAGIC);self.assertEqual(e.read(t.audio.SOUND+4,1),0)
        self.assertEqual(e.read(t.current.IO_BASE+2,2),0xb600)
    def test_invalid_magic_not_silently_guarded(self):
        e=t.b.Expected(t.fixture(self.a,0));t.on_writes(e);self.assertEqual(e.read(t.audio.SOUND,4),(-10)&t.MASK)
    def test_wait_finite_return(self):self.assertEqual(t.wait_events((158,159)),(None,[(0x081c15b8,158),(0x081c15c0,159)]))
    def test_wait_two_loop_order(self):
        self.assertEqual(t.wait_events((159,0,0,159))[1],[(0x081c15b8,159),(0x081c15b8,0),(0x081c15c0,0),(0x081c15c0,159)])
    def test_wait_first_loop_exhaustion(self):self.assertEqual(t.wait_events((159,159))[0],('VCOUNT入力列不足',0x081c15b8))
    def test_wait_second_loop_exhaustion(self):self.assertEqual(t.wait_events((0,0))[0],('VCOUNT入力列不足',0x081c15c0))
    def test_wait_empty(self):self.assertEqual(t.wait_events(())[0],('VCOUNT入力列不足',0x081c15b8))
    def test_wait_byte_type(self):
        with self.assertRaises(ValueError):t.wait_events((True,))
    def test_wait_overflow(self):
        with self.assertRaises(ValueError):t.wait_events((256,))
    def test_wait_length_bound(self):
        with self.assertRaises(ValueError):t.wait_events((0,)*65)
    def test_frequency_timer_enable_only_after_wait(self):
        e=t.b.Expected(t.fixture(self.a,t.audio.MAGIC+10));stop,events=t.frequency_writes(e,1<<16,(0,0))
        self.assertIsNotNone(stop);self.assertEqual(e.read(t.TIMER+2,2),0)
        self.assertNotIn((t.TIMER+2,2,128),e.writes)
    def test_frequency_timer_program(self):
        e=t.b.Expected(t.fixture(self.a,t.audio.MAGIC+10));stop,events=t.frequency_writes(e,1<<16,(158,159))
        self.assertIsNone(stop);self.assertEqual(e.read(t.TIMER+2,2),128)
        self.assertEqual(e.read(t.TIMER,2),(-0x44940//96)&65535)
    def test_frequency_fields(self):
        e=t.b.Expected(t.fixture(self.a));t.frequency_writes(e,1<<16,(158,159))
        self.assertEqual(e.read(t.audio.SOUND+16,4),96);self.assertEqual(e.read(t.audio.SOUND+11,1),16)
        self.assertEqual(e.read(t.audio.SOUND+20,4),(96*0x91d1b+5000)//10000)
    def test_window_indices_not_legal_mode_claim(self):
        for r in self.rows('frequency-'):self.assertFalse(r['legal_mode_claimed']);self.assertTrue(r['vcount_input_is_fixture'])
    def test_missing_index_zero_address(self):
        r=self.rows('frequency_missing-0')[0];self.assertEqual(r['read_fault']['address'],t.TABLE-2)
    def test_truncated_tail_halfword(self):
        r=self.rows('frequency_missing-15')[0];self.assertEqual(r['read_fault']['size'],2);self.assertEqual(r['nonstack_write_count'],1)
    def test_zero_frequency_partial_writes(self):
        for r in self.rows('frequency_zero-'):
            self.assertEqual(r['nonstack_write_count'],2);self.assertEqual(r['stop'],['保存node境界で停止',t.ZERO])
            self.assertTrue(r['zero_table_is_fault_fixture'])
    def test_known_bios_classified_not_unread(self):
        for r in self.rows('bios_entry-'):self.assertEqual(r['stop'][0],'既知BIOS SWI未実行');self.assertFalse(r['returned'])
    def test_machine_input_type(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[],sequence=[0])
    def test_machine_bios_allowlist(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[],bios=(t.ZERO,))
    def test_machine_bios_duplicates(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[],bios=(t.audio.BIOS,t.audio.BIOS))
    def test_mode_bool_rejected(self):
        with self.assertRaises(ValueError):t.frequency_writes(t.b.Expected(t.fixture(self.a)),True,())
    def test_mode_overflow_rejected(self):
        with self.assertRaises(ValueError):t.frequency_writes(t.b.Expected(t.fixture(self.a)),1<<32,())
    def test_candidate_mutation(self):self.reject(lambda a:a['candidate'].update(crc32='00000000'))
    def test_native_not_promoted(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_not_promoted(self):self.reject(lambda a:a.update(release_ready=True))
    def test_dma_not_promoted(self):self.reject(lambda a:a.update(dma_execution_observed=True))
    def test_bios_not_promoted(self):self.reject(lambda a:a['audio_bios_prefix'].update(executed=True))
    def test_bios_encoding_mutation(self):self.reject(lambda a:a['audio_bios_prefix'].update(hex='0cdf7047'))
    def test_pending_mutation(self):self.reject(lambda a:a.update(pending_direct_callees=[]))
    def test_table_bytes_mutation(self):self.reject(lambda a:a['frequency_window'].update(hex='00'*30))
    def test_table_values_mutation(self):self.reject(lambda a:a['frequency_window']['values'].__setitem__(0,0))
    def test_table_length_not_promoted(self):self.reject(lambda a:a['frequency_window'].update(actual_table_length_proven=True))
    def test_all_mode_validity_not_promoted(self):self.reject(lambda a:a['frequency_window'].update(all_selected_indices_valid_proven=True))
    def test_index_zero_not_promoted(self):self.reject(lambda a:a['frequency_window'].update(index_zero_sampled=True))
    def test_entry_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==t.DIV&~1)['hex']='7047'
        with self.assertRaises(ValueError):t.validate_inputs(nodes,self.a,self.context)
    def test_input_preserved(self):
        a=copy.deepcopy(self.a);t.validate_inputs(self.nodes,a,self.context);self.assertEqual(a,self.a)

if __name__=='__main__':unittest.main()
