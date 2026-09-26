"""実callback、RAM連続tick、candidate field分岐の限定回帰。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_wait_lifecycle as x


class WaitLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=x.payload('saved-context.json');cls.groups=x.verified_groups()
        cls.rows={r['case']:r for g in cls.groups.values()for r in g.rows}
    def test_01_count(self):self.assertEqual(len(self.rows),786)
    def test_02_group_counts(self):self.assertEqual([len(self.groups[g].rows)for g in x.GROUPS],[256,256,256,6,12])
    def test_03_hidden_returns_true(self):self.assertEqual(self.rows['wait-0']['return_value'],1)
    def test_04_busy_returns_false(self):self.assertTrue(all(self.rows['wait-'+str(i)]['return_value']==0 for i in range(1,256)))
    def test_05_wait_read_only(self):self.assertTrue(all(r['nonstack_write_count']==0 for r in self.groups['wait'].rows))
    def test_06_dispatch_hidden_resumes(self):self.assertEqual(self.rows['dispatch-0']['nonstack_write_count'],1)
    def test_07_dispatch_busy_unchanged(self):self.assertTrue(all(self.rows['dispatch-'+str(i)]['nonstack_write_count']==0 for i in range(1,256)))
    def test_08_dispatch_defers_script(self):self.assertTrue(all(r['return_value']==1 for r in self.groups['dispatch'].rows))
    def test_09_global_hidden_retains_lock(self):self.assertEqual(self.rows['global-0']['nonstack_write_count'],2)
    def test_10_global_busy_retains_lock(self):self.assertTrue(all(self.rows['global-'+str(i)]['nonstack_write_count']==1 for i in range(1,256)))
    def test_11_sequence_hidden_three_ticks(self):self.assertEqual([self.rows['sequence-0-'+str(t)]['return_value']for t in range(3)],[1,1,0])
    def test_12_sequence_busy_not_falsely_complete(self):self.assertTrue(all(self.rows[f'sequence-{f}-{t}']['return_value']==1 for f in(1,2,255)for t in range(3)))
    def test_13_sequence_RAM_chain(self):
        for f in(0,1,2,255):
            for t in(1,2):self.assertEqual(self.rows[f'sequence-{f}-{t}']['incoming_object_sha256'],self.rows[f'sequence-{f}-{t-1}']['final_object_sha256'])
    def test_14_sequence_no_host_writes(self):self.assertTrue(all(r['host_memory_writes_between_ticks']==0 for r in self.groups['sequence'].rows))
    def test_15_field_first_initializer_pending(self):self.assertEqual(self.rows['field-0']['stop'][1],0x08055b70)
    def test_16_field_one_increments(self):self.assertEqual((self.rows['field-1']['return_value'],self.rows['field-1']['nonstack_write_count']),(0,1))
    def test_17_field_two_flash_pending(self):self.assertEqual(self.rows['field-2']['stop'][1],0x080555f0)
    def test_18_field_three_callback_pending(self):self.assertEqual(self.rows['field-3']['stop'][1],0x08055eac)
    def test_19_field_four_complete(self):self.assertEqual((self.rows['field-4']['return_value'],self.rows['field-4']['nonstack_write_count']),(1,0))
    def test_20_field_wrapper_not_boolean(self):self.assertEqual(self.rows['field-wrapper-one']['return_value'],x.vm.b.vm.RETURN)
    def test_21_return_frame_preserved(self):self.assertTrue(all(r['return_sp_r4_r11_proven']for r in self.rows.values()if r['returned']))
    def test_22_field_table_mutation_rejected(self):
        rows=copy.deepcopy(self.c['story_field_frontier']['field_slots']);rows[0]['target']+=2
        with self.assertRaises(ValueError):x.field_data(rows)
    def test_23_wait_branch_mutation_rejected(self):
        c=copy.deepcopy(self.c);next(n for n in c['nodes']if n['address']==0x08068de4)['target']+=2
        with self.assertRaises(ValueError):x.contracts(c,'wait')
    def test_24_missing_wait_node_not_stubbed(self):
        c=copy.deepcopy(self.c);c['nodes']=[n for n in c['nodes']if n['address']!=0x08068de0]
        with self.assertRaises(ValueError):x.contracts(c,'wait')
    def test_25_missing_busy_byte_not_defaulted(self):
        with self.assertRaisesRegex(ValueError,'未map read'):x.vm.Machine(self.c['nodes'],[]).run(x.d.WAIT)
    def test_26_tick_memory_tampering_rejected(self):
        original=x.carry_segments
        def corrupt(seg,m):return [(a,b'\x7f'if a==x.d.BUSY else data,w)for a,data,w in original(seg,m)]
        with patch.object(x,'carry_segments',side_effect=corrupt),self.assertRaisesRegex(ValueError,'RAM非連続'):x.contracts(self.c,'sequence')
    def test_27_group_rejected(self):
        with self.assertRaises(ValueError):x.contracts(self.c,'native')
    def test_28_payload_allowlist(self):
        with self.assertRaises(ValueError):x.payload('candidate.gba')


if __name__=='__main__':unittest.main()
