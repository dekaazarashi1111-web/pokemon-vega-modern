"""旧単独suiteを再実行せず、新しいproducer→state012連続経路を検査する。"""
from contextlib import ExitStack
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_lifecycle_contracts as m


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ExitStack() as stack:
            guards=[stack.enter_context(patch.object(owner,name,side_effect=AssertionError('旧単独suite再実行')))
                for owner,name in ((m.prior,'verify'),(m.prior.prior,'completion_contracts'),
                    (m.prior.prior,'option_contracts'),(m.prior.state1,'verify'),
                    (m.p,'evaluated'),(m.w.task,'evaluated'))]
            cls.rows=m.verify();cls.old_calls=sum(g.call_count for g in guards)
        cls.by={r['case']:r for r in cls.rows}

    def test_32_new_sequences(self):self.assertEqual(len(self.rows),32)
    def test_no_old_suite(self):self.assertEqual(self.old_calls,0)
    def test_three_fonts(self):self.assertEqual({r['parameters']['font']for r in self.rows},{2,4,5})
    def test_three_speeds(self):self.assertEqual({r['parameters']['speed']for r in self.rows},{0,1,2})
    def test_script_immediate_and_fallback(self):
        for font in range(3):
            for speed in range(3):
                a=self.by[f'font{font}-speed{speed}-fallback0'];b=self.by[f'font{font}-speed{speed}-fallback1']
                self.assertEqual(a['phase_write_counts'],b['phase_write_counts'])
                self.assertEqual(a['script_operand_bytes_consumed'],4)
                self.assertEqual(b['script_operand_bytes_consumed'],4)
    def test_generated_task_states(self):self.assertTrue(all(r['states']==[0,1,2]for r in self.rows))
    def test_busy_only_clears_after_state2(self):
        self.assertTrue(all([p['busy_after']for p in r['phases']]==[2,2,0]for r in self.rows))
    def test_active_only_clears_after_state2(self):
        self.assertTrue(all([p['task_active_after']for p in r['phases']]==[1,1,0]for r in self.rows))
    def test_all_ended(self):self.assertTrue(all(r['task_deleted']and r['busy_cleared']and r['printer_inactive']for r in self.rows))
    def test_no_host_mutation(self):self.assertTrue(all(r['host_ram_mutations_between_phases']==0 for r in self.rows))
    def test_four_real_returns(self):
        self.assertTrue(all(r['return_values']==[0]+[m.w.b.vm.RETURN]*3 and r['return_sp_r4_r11_proven']for r in self.rows))
    def test_four_independent_stack_frames(self):
        self.assertTrue(all(len(r['callback_stack_bytes'])==4 and 0<min(r['callback_stack_bytes'])<=max(r['callback_stack_bytes'])<=512 for r in self.rows))
    def test_unchanged_old_task_links(self):self.assertTrue(all(r['initial_task_chain']==r['final_task_chain']for r in self.rows))
    def test_last_free_task(self):self.assertEqual(self.by['task-last']['task_id'],15)
    def test_insert_middle_delete_links(self):self.assertEqual(self.by['task-middle']['final_task_chain'],[5,2,9])
    def test_invalid_config_does_not_claim_valid_config(self):
        for kind in ('bad_crc','bad_magic'):
            r=self.by['config-'+kind];self.assertEqual(r['parameters']['config_kind'],kind)
            self.assertLess(r['phase_write_counts'][0],self.by['font0-speed2-fallback0']['phase_write_counts'][0])
    def test_fast_fifth_reservation(self):self.assertEqual(self.by['font0-speed0-fallback0']['reserved_slots'],[0,1,2,3,4])
    def test_normal_four_reservations(self):self.assertEqual(self.by['font0-speed2-fallback0']['reserved_slots'],[0,1,2,3])
    def test_capacity_boundaries(self):
        for n in range(5):
            r=self.by[f'capacity-{n}'];self.assertEqual(r['reserved_slots'],list(range(n)))
            self.assertEqual(r['queue_plan'],list(range(n))+[None]*(5-n))
    def test_queue_wrap(self):self.assertEqual(self.by['wrap127']['reserved_slots'],[127,0,1,2,3])
    def test_seven_hle_not_bios_execution(self):
        self.assertTrue(all(r['bios_service_count']==7 and not r['bios_execution_observed']for r in self.rows))
    def test_not_native_story_dma_or_ring(self):
        self.assertTrue(all(not any(r[k]for k in ('normal_story_observed','native_scheduler_observed','dma_execution_observed','ring_acquisition_accepted'))for r in self.rows))
    def test_full_phase_image_coverage(self):
        for r in self.rows:
            self.assertEqual(len(r['phase_object_sha256']),4)
            self.assertEqual(len(set(r['phase_object_sha256'])),4)
            self.assertEqual(len(r['combined_write_identity']['sha256']),64)
    def test_unique_rows(self):self.assertEqual(len(self.by),len(self.rows))


class BoundaryTests(unittest.TestCase):
    def fixture(self):
        old=[(m.p.tasks.TASKS,b'A'*640,True),(m.p.FLAGS,b'aaaa',True)]
        new=[(m.p.tasks.TASKS,b'B'*640,True),(m.p.FLAGS,b'bbbb',True)]
        return old,new
    def test_producer_owns_both_shared_regions(self):
        old,new=self.fixture();self.assertEqual(m.merge_initial(old,new),new)
    def test_alias_outside_shared_regions_rejected(self):
        old,new=self.fixture();old.append((0x02000000,b'AB',False));new.append((0x02000001,b'B',False))
        with self.assertRaisesRegex(ValueError,'alias'):m.merge_initial(old,new)
    def test_shared_width_rejected(self):
        old,new=self.fixture();new[1]=(m.p.FLAGS,b'A',True)
        with self.assertRaises(ValueError):m.merge_initial(old,new)
    def test_shared_readonly_rejected(self):
        old,new=self.fixture();new[1]=(m.p.FLAGS,b'bbbb',False)
        with self.assertRaises(ValueError):m.merge_initial(old,new)
    def test_shared_missing_rejected(self):
        old,new=self.fixture()
        with self.assertRaises(ValueError):m.merge_initial(old,new[:1])
    def test_stack_alias_rejected(self):
        old,new=self.fixture();new.append((m.w.strict.STACK_START,b'A',True))
        with self.assertRaises(ValueError):m.merge_initial(old,new)
    def test_queue_plan_rejects_types_and_bounds(self):
        for args in ((True,(),4),(128,(),4),(0,(),6),(0,(128,),4),(0,(True,),4)):
            with self.assertRaises(ValueError):m.reservations(*args)
    def test_nonterminator_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError,'終端text'):m.one('invalid',m.p.Case(full_pool=True,source=b'\1\xff'))
    def test_incomplete_pool_is_not_silently_padded(self):
        with self.assertRaisesRegex(ValueError,'終端text'):m.one('invalid',m.p.Case())
    def test_unallocated_task_is_not_dispatched(self):
        with self.assertRaisesRegex(ValueError,'終端text'):m.one('invalid',m.p.Case(full_pool=True,task_layout='full'))

if __name__=='__main__':unittest.main()
