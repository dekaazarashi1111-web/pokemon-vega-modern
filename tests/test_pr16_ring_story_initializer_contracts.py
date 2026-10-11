"""通常callback登録を主張せず、実保存calleeの新しい契約だけ検証する。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_initializer_contracts as x


class InitializerContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=x.payload('saved-context.json');cls.groups=x.verified_groups()
        cls.rows={r['case']:r for g in cls.groups.values()for r in g.rows}
    def test_01_count(self):self.assertEqual(len(self.rows),540)
    def test_02_group_counts(self):self.assertEqual([len(self.groups[g].rows)for g in x.GROUPS],[256,256,4,10,4,10])
    def test_03_flash_all_u8(self):self.assertTrue(all(self.rows['flash-'+str(i)]['return_value']==i for i in range(256)))
    def test_04_flash_read_only(self):self.assertTrue(all(r['nonstack_write_count']==0 for r in self.groups['flash'].rows))
    def test_05_callback2_zero_waits(self):self.assertEqual((self.rows['callback2-0']['return_value'],self.rows['callback2-0']['nonstack_write_count']),(0,0))
    def test_06_callback2_nonzero_clears_both(self):self.assertTrue(all(self.rows['callback2-'+str(i)]['return_value']==1 and self.rows['callback2-'+str(i)]['nonstack_write_count']==2 for i in range(1,256)))
    def test_07_callback1_ignores_return(self):self.assertTrue(all(r['return_value']==1 and r['nonstack_write_count']==1 for r in self.groups['callback1'].rows))
    def test_08_callback2_priority_does_not_read_callback1(self):self.assertTrue(self.rows['priority-false-no-cb1-read']['returned'])
    def test_09_default_callback_is_not_stubbed(self):self.assertEqual(self.rows['default-callback-unread']['stop'][1],0x0807d694)
    def test_10_unknown_callback_stops(self):self.assertTrue(all(self.rows[k]['stop'][1]==x.UNKNOWN&~1 for k in('unknown1','unknown2')))
    def test_11_arm_callback_rejected(self):self.assertTrue(all(self.rows[k]['stop']==['ARM state未対応',0x081c7ac8]for k in('arm1','arm2')))
    def test_12_partial_clear_preserved(self):self.assertEqual((self.rows['partial-clear-before-cb1-denied']['stop'][1],self.rows['partial-clear-before-cb1-denied']['nonstack_write_count']),(0x08055ece,1))
    def test_13_readonly_clear_rejected(self):self.assertEqual(self.rows['readonly-cb2-clear-denied']['nonstack_write_count'],0)
    def test_14_globals_not_defaulted(self):self.assertEqual(self.rows['missing-cb2-object']['read_fault']['address'],x.CB2)
    def test_15_save_pointer_not_defaulted(self):self.assertEqual(self.rows['missing-save-pointer']['read_fault']['address'],x.SAVE_PTR)
    def test_16_initializer_heap_first(self):self.assertEqual(self.rows['initializer-heap-reset-unread']['stop'][1],0x0804b85c)
    def test_17_gpu_register_boundary(self):self.assertEqual(self.rows['screen-gpu-register-unread']['stop'][1],0x08000a38)
    def test_18_window_actual_template_argument(self):self.assertEqual(self.rows['windows-bg-supplier-unmapped']['calls'][0]['args'][0],0x083e30d0)
    def test_19_window_bg_unmapped(self):self.assertEqual(self.rows['windows-bg-supplier-unmapped']['read_fault'],{'address':0x030008d0,'size':1,'site':0x08001200})
    def test_20_printer_bg_x_before_reset(self):self.assertEqual(self.rows['printer-bg-x-unread']['stop'][1],0x08001b90)
    def test_21_resource_no_synthetic_success(self):self.assertTrue(all(not r['returned']and r['nonstack_write_count']==0 for r in self.groups['resources'].rows))
    def test_22_field0_actual_heap_callee(self):self.assertEqual(self.rows['field0-heap-boundary']['stop'][1],0x0804b85c)
    def test_23_field2_split_stops(self):self.assertEqual([self.rows['field2-flash-'+str(i)]['stop'][1]for i in(0,1,255)],[0x080f77e8,0x0807e7a4,0x0807e7a4])
    def test_24_field3_true_reaches_done_next_tick(self):self.assertTrue(all(self.rows[f'field3-sequence-{i}-0']['return_value']==0 and self.rows[f'field3-sequence-{i}-1']['return_value']==1 for i in(1,255)))
    def test_25_field3_false_keeps_waiting(self):self.assertTrue(all(self.rows[f'field3-sequence-0-{t}']['return_value']==0 for t in(0,1)))
    def test_26_field_tick_memory_chain(self):
        for i in(0,1,255):self.assertEqual(self.rows[f'field3-sequence-{i}-1']['incoming_object_sha256'],self.rows[f'field3-sequence-{i}-0']['final_object_sha256'])
    def test_27_frames_preserved_on_return(self):self.assertTrue(all(r['return_sp_r4_r11_proven']for r in self.rows.values()if r['returned']))
    def test_28_callback_branch_mutation_rejected(self):
        c=copy.deepcopy(self.c);next(n for n in c['nodes']if n['address']==0x08055ebe)['target']+=2
        with self.assertRaises(ValueError):x.contracts(c,'callback2')
    def test_29_flash_segment_type(self):
        for value in(-1,256,True):
            with self.subTest(value=value),self.assertRaises(ValueError):x.flash(value)
    def test_30_between_tick_tampering_rejected(self):
        original=x.life.carry_segments
        def corrupt(seg,m):return [(at,b'\0'if at==x.d.FIELD_STATE else data,w)for at,data,w in original(seg,m)]
        with patch.object(x.life,'carry_segments',side_effect=corrupt),self.assertRaisesRegex(ValueError,'field連続RAM不一致'):x.contracts(self.c,'field')
    def test_31_group_rejected(self):
        with self.assertRaises(ValueError):x.contracts(self.c,'native')
    def test_32_payload_allowlist(self):
        with self.assertRaises(ValueError):x.payload('candidate.gba')


if __name__=='__main__':unittest.main()
