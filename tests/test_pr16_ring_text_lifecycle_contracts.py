"""非空producer/state012の連続性と不足入力を検査。旧単独suiteは呼ばない。"""
from contextlib import ExitStack
from pathlib import Path
import hashlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_text_lifecycle_contracts as m


class TextLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ExitStack() as stack:
            guards=[stack.enter_context(patch.object(owner,name,side_effect=AssertionError('旧単独suite再実行')))
                for owner,name in ((m.prior,'verify'),(m.h,'verify'),(m.q,'completion_contracts'),
                    (m.q,'option_contracts'),(m.h.state1,'verify'),(m.p,'evaluated'),
                    (m.glyph,'evaluated'),(m.w.task,'evaluated'))]
            cls.rows=m.verify();cls.old_calls=sum(g.call_count for g in guards)
        cls.by={r['case']:r for r in cls.rows};cls.good=[r for r in cls.rows if r['terminated']]
        cls.stopped=[r for r in cls.rows if r['stop']is not None]

    def test_31_new_paths(self):self.assertEqual(len(self.rows),31)
    def test_no_old_suite(self):self.assertEqual(self.old_calls,0)
    def test_27_endings_and_four_exact_stops(self):self.assertEqual((len(self.good),len(self.stopped)),(27,4))
    def test_five_saved_characters(self):self.assertTrue(all(r['characters']==list(m.CHARS)for r in self.good))
    def test_terminator_consumed(self):self.assertTrue(all(r['polls'][-1]['pointer']==m.TEXT+len(m.STREAM)for r in self.good))
    def test_normal_fast_pixel_and_glyph_equality(self):
        for font in range(3):
            rows=[self.by[f'font{font}-speed{speed}']for speed in(0,1,2)]
            self.assertEqual(len({r['final_pixels']['sha256']for r in rows}),1)
            self.assertEqual(len({r['final_glyph']['sha256']for r in rows}),1)
    def test_actual_pixels_changed(self):
        blank=hashlib.sha256(bytes([0x11])*3456).hexdigest()
        self.assertTrue(all(r['final_pixels']['sha256']!=blank for r in self.good))
    def test_default_background_unchanged_at_missing_glyph(self):
        blank=hashlib.sha256(bytes([0x11])*3456).hexdigest()
        self.assertTrue(all(r['final_pixels']['sha256']==blank for r in self.stopped))
    def test_speed0_single_poll(self):self.assertTrue(all(r['poll_calls']==1 for r in self.good if r['speed']==0))
    def test_speed1_six_polls(self):self.assertTrue(all(r['poll_calls']==6 for r in self.good if r['speed']==1))
    def test_speed2_eleven_polls(self):self.assertTrue(all(r['poll_calls']==11 for r in self.good if r['speed']==2))
    def test_delay_has_no_queue_request(self):
        waited=[p for r in self.good for p in r['polls']if p['waited']]
        self.assertTrue(waited)
        self.assertTrue(all(p['characters']==[]and p['queue_reservations']==[]and p['nonstack_write_count']==1 for p in waited))
    def test_counter_evolves_without_host_write(self):
        self.assertEqual([p['counter']for p in self.by['font0-speed2']['polls']],[1,0]*5+[1])
    def test_busy_active_until_actual_terminator(self):
        for r in self.good:
            self.assertTrue(all(p['busy']==2 and p['task_active']==1 for p in r['polls'][:-1]))
            self.assertEqual((r['polls'][-1]['busy'],r['polls'][-1]['task_active']),(0,0))
    def test_task15_can_finish(self):
        for speed in(0,2):self.assertEqual(self.by[f'lasttask-speed{speed}']['task_id'],15)
    def test_unrelated_task_chain_preserved(self):self.assertTrue(all(r['initial_task_chain']==r['final_task_chain']for r in self.good))
    def test_initial_four_queue_slots_preserved(self):
        self.assertEqual(self.by['font0-speed0']['text_reserved_slots'],[4])
        self.assertEqual(self.by['font0-speed1']['text_reserved_slots'],[4,5,6,7,8])
    def test_saturated_queue_not_overwritten(self):
        for free in(0,4):
            for speed in(0,2):self.assertEqual(self.by[f'capacity{free}-speed{speed}']['text_reserved_slots'],[])
    def test_partial_queue_allocation(self):
        self.assertEqual(self.by['capacity6-speed0']['text_reserved_slots'],[4])
        self.assertEqual(self.by['capacity6-speed2']['text_reserved_slots'],[4,5])
    def test_queue_wrap(self):
        self.assertEqual(self.by['wrap127-speed0']['text_reserved_slots'],[3])
        self.assertEqual(self.by['wrap127-speed2']['text_reserved_slots'],[3,4,5,6,7])
    def test_fallback_matches_immediate_pixels(self):
        for font in range(3):
            for speed in(0,2):self.assertEqual(self.by[f'font{font}-speed{speed}']['final_pixels'],self.by[f'font{font}-speed{speed}-fallback']['final_pixels'])
    def test_flag4_does_not_forge_completion(self):
        for speed in(0,2):self.assertEqual(self.by[f'flag4-speed{speed}']['final_pixels'],self.by[f'font0-speed{speed}']['final_pixels'])
    def test_missing_input_still_busy(self):
        for r in self.stopped:
            self.assertFalse(r['task_deleted']or r['busy_cleared'])
            self.assertEqual((r['polls'][0]['busy'],r['polls'][0]['task_active']),(2,1))
    def test_missing_input_preserves_partial_four_writes(self):
        self.assertTrue(all(r['polls'][0]['nonstack_write_count']==4 and r['polls'][0]['pointer']==m.TEXT+1 for r in self.stopped))
    def test_missing_input_is_not_success_return(self):self.assertTrue(all(not r['polls'][0]['returned']for r in self.stopped))
    def test_missing_input_exact_sites(self):self.assertEqual({r['stop']['site']for r in self.stopped},{0x08002f7c,0x08002f82})
    def test_no_host_mutation_between_any_phases(self):self.assertTrue(all(r['host_ram_mutations_between_phases']==0 for r in self.rows))
    def test_each_callback_has_independent_stack(self):
        for r in self.rows:
            self.assertEqual(len(r['callback_stack_bytes']),3+r['poll_calls'])
            self.assertTrue(0<min(r['callback_stack_bytes'])<=max(r['callback_stack_bytes'])<=512)
            self.assertTrue(r['successful_return_sp_r4_r11_proven'])
    def test_complete_memory_hashes(self):
        for r in self.rows:
            self.assertEqual(len(r['phase_object_sha256']),3+r['poll_calls'])
            self.assertTrue(all(len(h)==64 for h in r['phase_object_sha256']))
    def test_not_story_or_native_or_dma(self):
        self.assertTrue(all(not any(r[k]for k in('bios_execution_observed','dma_execution_observed','native_scheduler_observed','normal_story_observed','ring_acquisition_accepted'))for r in self.rows))
    def test_only_saved_seven_hle_services(self):self.assertTrue(all(r['bios_service_count']==7 for r in self.rows))


class InputBoundaryTests(unittest.TestCase):
    def test_unsupported_source_not_accepted(self):
        for source in(b'\xff',b'\1\xff',b'\x99\xff'):
            with self.assertRaisesRegex(ValueError,'限定非空'):m.one('unsupported',m.p.Case(full_pool=True,source=source))
    def test_bad_configuration_not_conflated_with_text_failure(self):
        with self.assertRaisesRegex(ValueError,'限定非空'):m.one('badconfig',m.p.Case(full_pool=True,source=m.STREAM,config_kind='bad_crc'))
    def test_missing_kind_rejected_before_input_read(self):
        with self.assertRaises(ValueError):m.output_segments({},4,'anything')
    def test_queue_plan_strict_types(self):
        for args in((True,(),4),(128,(),4),(0,(),11),(0,(128,),4),(0,(True,),4)):
            with self.assertRaises(ValueError):m.reservation_plan(*args)


if __name__=='__main__':unittest.main()
