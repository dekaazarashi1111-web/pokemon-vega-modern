"""実保存byteで新しいdispatch契約だけを検証。既受入nativeは起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_dispatch_contracts as x


class StoryDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=x.payload('saved-context.json')
        cls.groups=x.verified_groups()
        cls.rows={r['case']:r for g in cls.groups.values()for r in g.rows}
        cls.slots=cls.c['story_dispatch_frontier']['command_slots']

    def test_01_exact_case_count(self):self.assertEqual(len(self.rows),1037)
    def test_02_group_counts(self):self.assertEqual([len(self.groups[g].rows)for g in x.GROUPS],[4,256,257,6,258,256])
    def test_03_modes_full_u8(self):self.assertTrue(all('mode-'+str(i)in self.rows for i in range(256)))
    def test_04_unknown_modes_keep_running(self):self.assertTrue(all(self.rows['mode-'+str(i)]['return_value']==1 and self.rows['mode-'+str(i)]['nonstack_write_count']==0 for i in range(3,256)))
    def test_05_null_native_falls_through(self):self.assertEqual(self.rows['mode-2']['nonstack_write_count'],2)
    def test_06_invalid_opcodes_advance_before_stop(self):self.assertTrue(all(self.rows['opcode-'+str(i)]['returned'] and self.rows['opcode-'+str(i)]['nonstack_write_count']==2 for i in range(211,256)))
    def test_07_missing_slots_fail_closed(self):self.assertEqual(sum(not self.rows['opcode-'+str(i)]['returned']for i in range(211)),209)
    def test_08_wait_actual_slot_sets_native_mode(self):self.assertEqual((self.rows['opcode-102']['return_value'],self.rows['opcode-102']['nonstack_write_count']),(1,3))
    def test_09_message_busy_does_not_render(self):self.assertEqual((self.rows['opcode-103']['return_value'],self.rows['opcode-103']['nonstack_write_count']),(0,7))
    def test_10_null_sentinel_not_success(self):self.assertFalse(self.rows['null-script-sentinel']['returned'])
    def test_11_real_wait_callback_not_stubbed(self):self.assertEqual(self.rows['real-wait-callback-unread']['stop'][1],x.WAIT&~1)
    def test_12_native_arm_rejected(self):self.assertEqual(self.rows['native-arm-pointer-rejected']['stop'][0],'ARM state未対応')
    def test_13_getter_is_conditional(self):self.assertEqual([self.rows['conditional-saved-getter-'+str(i)]['nonstack_write_count']for i in (0,1,2,255)],[0,1,0,0])
    def test_14_global_waiting_shutdown_no_writes(self):self.assertTrue(all(self.rows['global-status-'+str(i)]['nonstack_write_count']==0 for i in (1,2)))
    def test_15_global_other_status_closes_lock(self):self.assertTrue(all(self.rows['global-status-'+str(i)]['nonstack_write_count']==3 for i in range(256)if i not in (1,2)))
    def test_16_global_wait_keeps_lock(self):self.assertEqual(self.rows['global-real-wait']['nonstack_write_count'],4)
    def test_17_field_five_slots_missing(self):self.assertEqual([self.rows['field-state-'+str(i)]['read_fault']['address']for i in range(5)],[x.FIELD_TABLE+4*i for i in range(5)])
    def test_18_field_outside_states_return_without_write(self):self.assertTrue(all(self.rows['field-state-'+str(i)]['returned']and self.rows['field-state-'+str(i)]['nonstack_write_count']==0 for i in range(5,256)))
    def test_19_field_void_wrapper_not_boolean(self):self.assertEqual(self.rows['field-state-5']['return_value'],x.vm.b.vm.RETURN)
    def test_20_return_contracts_preserve_frame(self):self.assertTrue(all(r['return_sp_r4_r11_proven']for r in self.rows.values()if r['returned']))
    def test_21_init_exact_writes(self):self.assertEqual(self.rows['init-context']['nonstack_write_count'],30)
    def test_22_setup_reset_order(self):self.assertEqual(self.rows['setup-'+str(x.SCRIPT)]['nonstack_write_count'],37)
    def test_23_slot_target_mutation_rejected(self):
        slots=copy.deepcopy(self.slots);slots[0]['target']+=2
        with self.assertRaises(ValueError):x.slot_segments(slots)
    def test_24_slot_byte_mutation_rejected(self):
        slots=copy.deepcopy(self.slots);slots[1]['hex']='00000000'
        with self.assertRaises(ValueError):x.slot_segments(slots)
    def test_25_slot_order_rejected(self):
        with self.assertRaises(ValueError):x.slot_segments(self.slots[::-1])
    def test_26_mode_width_type_rejected(self):
        for v in (-1,256,True,'1'):
            with self.subTest(v=v),self.assertRaises(ValueError):x.context(v)
    def test_27_unmapped_ram_rejected(self):
        m=x.vm.Machine(self.c['nodes'],[],(x.C,))
        with self.assertRaisesRegex(ValueError,'未map read'):m.run(0x080690c5)
    def test_28_group_rejected(self):
        with self.assertRaises(ValueError):x.contracts([],self.slots,'all-native')
    def test_29_call_target_mutation_rejected(self):
        ns=copy.deepcopy(self.c['nodes'])
        next(n for n in ns if n['address']==0x0806912e)['target']+=4
        with self.assertRaises(ValueError):x.contracts(ns,self.slots,'opcode')
    def test_30_export_scope_rejected(self):
        with self.assertRaises(ValueError):x.payload('candidate.gba')


if __name__=='__main__':unittest.main()
