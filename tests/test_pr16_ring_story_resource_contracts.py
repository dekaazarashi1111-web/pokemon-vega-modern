"""実byteと独立期待値を結合し、部分書込・偽の通常取得受入を防ぐ。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_resource_contracts as x

class ResourceContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=x.payload('saved-context.json');cls.groups=x.verified_groups()
    def bad(self,change):
        c=copy.deepcopy(self.c);change(c)
        with self.assertRaises(ValueError):x.binding(c)
    def rows(self,group):return self.groups[group].rows
    def test_01_groups(self):self.assertEqual(set(self.groups),set(x.GROUPS))
    def test_02_count(self):self.assertEqual(sum(len(g.rows)for g in self.groups.values()),351)
    def test_03_copy_176(self):self.assertEqual(len(self.rows('memcpy')),176)
    def test_04_copy_returns(self):self.assertTrue(all(r['returned']and r['return_sp_r4_r11_proven']for r in self.rows('memcpy')))
    def test_05_copy_bounds(self):self.assertTrue(all(r['maximum_stack_bytes']==12 for r in self.rows('memcpy')))
    def test_06_copy_partial(self):self.assertEqual([r['nonstack_write_count']for r in self.rows('copy_faults')],[4,0])
    def test_07_copy_fault_sites(self):self.assertEqual([r['stop'][1]for r in self.rows('copy_faults')],[0x081c9dcc,0x081c9db4])
    def test_08_heap_returns(self):self.assertTrue(all(r['returned']and r['nonstack_write_count']==7 for r in self.rows('heap')))
    def test_09_heap_underflow_not_sanitized(self):
        e=x.Expected([(x.HP,bytes(8),True),(x.HEAP,bytes(16),True)]);e.heap_init(x.HEAP,0);self.assertEqual(e.read(x.HEAP+4,4),0xfffffff0)
    def test_10_bg_reset_returns(self):self.assertEqual(len(self.rows('bg_reset')),12);self.assertTrue(all(r['returned']for r in self.rows('bg_reset')))
    def test_11_bg_reset_effective_writes(self):self.assertTrue(all(r['nonstack_write_count']in (268,270)for r in self.rows('bg_reset')))
    def test_12_attributes_108(self):self.assertEqual(len(self.rows('attributes')),108)
    def test_13_invalid_bg_no_write(self):self.assertTrue(all(r['nonstack_write_count']==0 for r in self.rows('attributes')if r['case'].startswith('attr-4-')))
    def test_14_invalid_selector_no_write(self):self.assertTrue(all(r['nonstack_write_count']==0 for r in self.rows('attributes')if r['case'].split('-')[2]in ('0','8')))
    def test_15_pipeline_32_returns(self):self.assertEqual(len(self.rows('pipeline')),32);self.assertTrue(all(r['returned']for r in self.rows('pipeline')))
    def test_16_pipeline_continuity(self):
        for i,row in enumerate(self.rows('pipeline')):
            if i%8:self.assertEqual(row['incoming_object_sha256'],self.rows('pipeline')[i-1]['final_object_sha256'])
            else:self.assertIsNone(row['previous_final_object_sha256'])
    def test_17_no_host_writes(self):self.assertTrue(all(r['host_memory_writes_between_ticks']==0 for r in self.rows('pipeline')))
    def test_18_standard_windows_real_calls(self):
        for r in self.rows('pipeline'):
            if r['case'].endswith('-window'):
                self.assertIn(0x08003af1,[k['target']for k in r['calls']]);self.assertEqual(r['nonstack_write_count'],2179)
    def test_19_font_setter_is_not_caller_proof(self):
        for r in self.rows('pipeline'):
            if r['case'].endswith('-fonts'):self.assertEqual([k['target']for k in r['calls']],[0x08002c1d]);self.assertEqual(r['nonstack_write_count'],1)
    def test_20_save_random_stop(self):self.assertTrue(all(r['stop']==['保存node境界で停止',0x0804448c]for r in self.rows('save_prefix')))
    def test_21_save_all_three_copies(self):
        for r in self.rows('save_prefix'):
            calls=[k for k in r['calls']if k['target']==0x081c9d99];self.assertEqual([k['args'][2]for k in calls],[0xf24,0x3d40,0x83d0])
            self.assertEqual(r['nonstack_write_count'],3+(0xf24+0x3d40+0x83d0)//4)
    def test_22_save_did_not_return(self):self.assertTrue(all(not r['returned']and not r['return_sp_r4_r11_proven']for r in self.rows('save_prefix')))
    def test_23_calloc_unread_bios(self):self.assertTrue(all(r['stop']==['保存node境界で停止',0x081c7a88]for r in self.rows('calloc')))
    def test_24_calloc_does_not_zero_payload(self):self.assertTrue(all(r['nonstack_write_count']==11 for r in self.rows('calloc')))
    def test_25_resource_partial_before_read(self):self.assertEqual(self.rows('resource_faults')[0]['nonstack_write_count'],1)
    def test_26_bg_readonly_zero_writes(self):self.assertEqual(self.rows('resource_faults')[1]['nonstack_write_count'],0)
    def test_27_missing_default(self):self.assertEqual(self.rows('resource_faults')[2]['read_fault']['address'],0x081cde84)
    def test_28_candidate_mutation(self):self.bad(lambda c:c['story_resource_suppliers']['candidate'].update(size=0))
    def test_29_byte_mutation(self):self.bad(lambda c:next(n for n in c['nodes']if n['address']==min(x.vm.LDM)).update(hex='01c3'))
    def test_30_duplicate_node(self):self.bad(lambda c:c['nodes'].append(c['nodes'][0]))
    def test_31_table_hash_mutation(self):self.bad(lambda c:c['story_resource_suppliers']['data_tables'][0].update(hex='01000000'))
    def test_32_pointer_mutation(self):self.bad(lambda c:next(n for n in c['nodes']if n['address']==0x08055b84).update(literal_value=0))
    def test_33_false_acceptance(self):self.bad(lambda c:c['story_resource_suppliers'].update(ring_acquisition_accepted=True))
    def test_34_unmapped_not_zero_filled(self):
        m=x.vm.Machine(self.c['nodes'],[],(0x02010000,0x02020000,16))
        with self.assertRaisesRegex(ValueError,'未map read'):m.run(0x081c9d99)
    def test_35_extension_alignment(self):
        m=x.vm.Machine(self.c['nodes'],[(0x02010001,bytes(4),False)])
        m.r[3]=0x02010001
        with self.assertRaisesRegex(ValueError,'alignment'):m.run(min(x.vm.LDM)|1)
    def test_36_reject_wrong_expected_write(self):
        cases=x.vm.Cases(self.c['nodes']);seg=[(x.FONTS,bytes(4),True)]
        with self.assertRaisesRegex(ValueError,'正確順序write差分'):cases.run('bad',0x080f8a29,seg,writes=[(x.FONTS,4,0)])
    def test_37_map_segment_alias(self):
        with self.assertRaisesRegex(ValueError,'重複'):x.vm.Machine(self.c['nodes'],[(x.BG,bytes(4),True),(x.BG,bytes(1),False)])
    def test_38_stack_is_not_general_ram(self):
        with self.assertRaisesRegex(ValueError,'stack重複'):x.vm.Machine(self.c['nodes'],[(x.vm.prior.STACK_START,bytes(4),True)])
    def test_39_payload_allowlist(self):
        with self.assertRaises(ValueError):x.payload('candidate.gba')
    def test_40_groups_unknown(self):
        with self.assertRaises(ValueError):x.contracts(self.c,'accepted-native')

if __name__=='__main__':unittest.main()
