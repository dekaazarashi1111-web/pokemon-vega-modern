"""初期化を省略しない同一RAM経路と省略対照を検査する。"""
from contextlib import ExitStack
from pathlib import Path
import copy
import hashlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_bootstrap_lifecycle_contracts as m


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ExitStack() as stack:
            guards=[stack.enter_context(patch.object(owner,name,side_effect=AssertionError('旧suite再実行')))
                for owner,name in((m.prior,'verify'),(m.prior.prior,'verify'),(m.prior.h,'verify'),
                    (m.p,'evaluated'),(m.prior.glyph,'evaluated'),(m.w.task,'evaluated'))]
            cls.rows=m.verify();cls.old_calls=sum(g.call_count for g in guards)
        cls.good=[r for r in cls.rows if r['terminated']];cls.stopped=[r for r in cls.rows if r['stop']]

    def test_fourteen_new_sequences(self):self.assertEqual(len(self.rows),14)
    def test_twelve_endings_two_stops(self):self.assertEqual((len(self.good),len(self.stopped)),(12,2))
    def test_no_old_suite(self):self.assertEqual(self.old_calls,0)
    def test_null_and_poison_initial_pointer(self):self.assertEqual({r['initial_pointer']for r in self.good},{0,0xdeadbeef})
    def test_nonzero_initial_pool(self):self.assertTrue(all(r['initial_pool_byte']==0xa5 for r in self.rows))
    def test_exact_33_initialization_writes(self):self.assertTrue(all(r['initialization_writes']==33 for r in self.good))
    def test_only_font_write_in_reset_omission_control(self):self.assertTrue(all(r['initialization_writes']==1 for r in self.stopped))
    def test_font_pointer_from_saved_literal(self):self.assertTrue(all(r['font_pointer_written_by_initializer']for r in self.rows))
    def test_other_printer_reset_changes_only_active_byte(self):
        data=bytes(0 if i%32==27 else 0xa5 for i in range(992));digest=hashlib.sha256(data).hexdigest()
        self.assertTrue(all(r['final_other_printer_bytes']['sha256']==digest for r in self.good))
    def test_omitted_reset_keeps_other_printers_dirty(self):
        digest=hashlib.sha256(bytes([0xa5])*992).hexdigest()
        self.assertTrue(all(r['final_other_printer_bytes']['sha256']==digest for r in self.stopped))
    def test_five_characters_finish(self):self.assertTrue(all(r['characters']==list(m.prior.CHARS)for r in self.good))
    def test_null_poison_and_speed_same_final_pixels(self):
        for font in(2,4,5):self.assertEqual(len({r['final_pixels']['sha256']for r in self.good if r['font']==font}),1)
    def test_success_busy_and_task_cleared(self):self.assertTrue(all(r['busy_cleared']and r['task_deleted']for r in self.good))
    def test_omission_never_clears_busy_or_task(self):
        self.assertTrue(all(not r['busy_cleared']and not r['task_deleted']and r['polls'][-1]['busy']==2 and r['polls'][-1]['task_active']==1 for r in self.stopped))
    def test_omission_exact_slot1_font_failure(self):
        self.assertTrue(all(r['stop']=={'error':'未map read','read_fault':{'address':m.FONT_TABLE+0xa5*12,'size':4,'site':0x08002e5e}}for r in self.stopped))
    def test_omission_preserves_first_slot_draw(self):
        for r in self.stopped:
            self.assertEqual(r['characters'],list(m.prior.CHARS)if r['speed']==0 else[1])
            self.assertGreater(r['polls'][0]['write_count'],100)
    def test_no_host_change_between_phases(self):self.assertTrue(all(r['host_ram_mutations_between_phases']==0 for r in self.rows))
    def test_exact_phase_count(self):
        for r in self.rows:self.assertEqual(len(r['phase_object_sha256']),len(r['polls'])+(4 if r['skip_reset_control']else 5))
    def test_bounded_independent_stack_frames(self):
        self.assertTrue(all(0<min(r['callback_stack_bytes'])<=max(r['callback_stack_bytes'])<=512 and r['return_sp_r4_r11_proven_when_returned']for r in self.rows))
    def test_explicit_entries_not_native_story(self):
        self.assertTrue(all(r['explicit_entry_invocations_not_story_scheduler']and not any(r[k]for k in('native_scheduler_observed','normal_story_observed','ring_acquisition_accepted','bios_execution_observed','dma_execution_observed'))for r in self.rows))


class InputTests(unittest.TestCase):
    def base(self):return [(m.GFONTS,m.p.b.word(m.FONT_TABLE),False),(m.POOL,bytes(1024),True)]
    def test_strict_initial_types(self):
        for value in(True,-1,1<<32):
            with self.assertRaises(ValueError):m.uninitialized(self.base(),value)
    def test_bad_pool_width_rejected(self):
        seg=self.base();seg[1]=(m.POOL,bytes(32),True)
        with self.assertRaises(ValueError):m.uninitialized(seg,0)
    def test_missing_pointer_region_rejected(self):
        with self.assertRaises(ValueError):m.uninitialized(self.base()[1:],0)
    def test_signature_target_mutation_rejected(self):
        c=m.inputs()[0];nodes=[dict(n)for n in c['nodes']]
        next(n for n in nodes if n['address']==0x080f8a2c)['target']+=2
        with self.assertRaises(ValueError):m.bootstrap_signature({'nodes':nodes})


if __name__=='__main__':unittest.main()
