"""新規結合の回帰・境界mutation。既読nativeや単独checksumテストは再実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_ring_effective_contracts as m


class EffectiveContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=json.loads((ROOT/m.frontier.OLD).read_text())['analysis']
        cls.patch=json.loads((ROOT/m.vm.PATCH).read_text())
        cls.new=json.loads((ROOT/m.PRIOR).read_text())['analysis']
        cls.nodes=m.joined_nodes(cls.old,cls.patch,cls.new)
    def changed_new(self,at,**change):
        value=copy.deepcopy(self.new);next(n for n in value['new_nodes'] if n['address']==at).update(change);return value
    def test_01_mode_complete_byte_domain(self):
        rows=m.selector_results(self.new,self.old)
        self.assertEqual(len(rows),256)
        self.assertEqual([r['return_r0'] for r in rows[:6]],[0,1,2,1,2,0])
        self.assertTrue(all(r['return_r0']==0 for r in rows[5:]))
    def test_02_mode_return_mutation(self):
        with self.assertRaises(ValueError):m.selector_results(self.changed_new(0x08113828,hex='0320'),self.old)
    def test_03_mode_jump_mutation(self):
        with self.assertRaises(ValueError):m.selector_results(self.changed_new(0x0811382a,target=0x08113830),self.old)
    def test_04_mode_missing_case(self):
        new=copy.deepcopy(self.new);new['new_nodes']=[n for n in new['new_nodes'] if n['address']!=0x0811382c]
        with self.assertRaises(ValueError):m.selector_results(new,self.old)
    def test_05_mode_table_order_mutation(self):
        new=copy.deepcopy(self.new);new['table_entries'].reverse()
        with self.assertRaises(ValueError):m.selector_results(new,self.old)
    def test_06_mode_table_target_mutation(self):
        new=copy.deepcopy(self.new);new['table_entries'][1]['raw_target']=0x08113824
        new['table_entries'][1]['thumb_entry']=0x08113825
        with self.assertRaises(ValueError):m.selector_results(new,self.old)
    def test_07_mode_suffix_mutation(self):
        old=copy.deepcopy(self.old);next(n for n in old['new_nodes'] if n['address']==0x0811382e)['hex']='01bc'
        with self.assertRaises(ValueError):m.selector_results(self.new,old)
    def test_08_mode_no_stores(self):
        self.assertTrue(all(r['nonstack_writes']==0 for r in m.selector_results(self.new,self.old)))
    def test_09_veneer_exact_targets(self):
        self.assertEqual([r['target'] for r in m.veneer_links(self.nodes)],[0x093bd9a9,0x093bde81])
    def test_10_veneer_target_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x092d12e0)['literal_value']+=2
        with self.assertRaises(ValueError):m.veneer_links(nodes)
    def test_11_veneer_bx_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x092d297a)['hex']='0047'
        with self.assertRaises(ValueError):m.veneer_links(nodes)
    def test_12_veneer_not_callee_abi(self):
        self.assertTrue(all(not r['callee_return_proven'] and not r['native_reachability_proven'] for r in m.veneer_links(self.nodes)))
    def test_13_pop_zero(self):
        row=m.pop_case(self.nodes,0);self.assertEqual(row['writes'],[]);self.assertEqual(row['selected_script_pointer'],0)
    def test_14_pop_all_depths(self):
        for depth in range(1,256):
            row=m.pop_case(self.nodes,depth);self.assertEqual(row['writes'],[[m.CTX,1,depth-1]])
    def test_15_composed_return_all_depths(self):
        for depth in range(256):
            row=m.pop_case(self.nodes,depth,True);self.assertEqual(row['writes'][-1],[m.CTX+8,4,row['selected_script_pointer']])
            self.assertEqual(row['maximum_stack_bytes'],12)
    def test_16_depth_range(self):
        with self.assertRaises(ValueError):m.pop_case(self.nodes,256)
    def test_17_pop_incomplete_allocation(self):
        raw=bytearray(16);raw[0]=2
        machine=m.vm.Machine(self.nodes,[(m.CTX,bytes(raw),True)],(m.CTX,))
        with self.assertRaisesRegex(ValueError,'未map'):machine.run(m.POP)
    def test_18_pop_requires_write_permission(self):
        raw=bytearray(16);raw[0]=1
        with self.assertRaisesRegex(ValueError,'未許可'):m.vm.Machine(self.nodes,[(m.CTX,bytes(raw),False)],(m.CTX,)).run(m.POP)
    def test_19_pop_caller_capacity_not_proven(self):self.assertFalse(m.pop_case(self.nodes,255)['caller_capacity_proven'])
    def test_20_pop_nested_missing_node(self):
        nodes=[n for n in self.nodes if n['address']!=0x08069170]
        with self.assertRaisesRegex(ValueError,'保存node境界'):m.pop_case(nodes,2,True)
    def test_21_bad_version_returns_3(self):
        for version in (0,3,255,256,65535):self.assertEqual(m.validator_case(self.nodes,m.validator_buffer(version),3)['return_code'],3)
    def test_22_declared_size_returns_4(self):
        for size in (0,1,2047,2049,32768,65535):m.validator_case(self.nodes,m.validator_buffer(size=size),4)
    def test_23_checksum_mismatch_returns_5(self):
        for version in (1,2):self.assertEqual(m.validator_case(self.nodes,m.validator_buffer(version,good_hash=False),5)['maximum_stack_bytes'],48)
    def test_24_reserved_byte_returns_15(self):
        for version in (1,2):
            for offset in (65,66,67):m.validator_case(self.nodes,m.validator_buffer(version,reserved_offset=offset),15)
    def test_25_valid_header_not_promoted(self):
        for version in (1,2):
            machine=m.vm.Machine(self.nodes,[(m.CTX,m.validator_buffer(version),False)],(m.CTX,2048))
            with self.assertRaisesRegex(ValueError,'保存node境界'):machine.run(m.vm.VALIDATE)
            self.assertEqual(machine.last_pc,{1:0x093bdaa8,2:0x093bdb3e}[version])
    def test_26_missing_checksum_node_fails(self):
        nodes=[n for n in self.nodes if n['address']!=0x093bd970]
        with self.assertRaisesRegex(ValueError,'保存node境界'):m.validator_case(nodes,m.validator_buffer(good_hash=False),5)
    def test_27_wrong_checksum_branch_target(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x093bda5a)['target']+=2
        with self.assertRaisesRegex(ValueError,'branch結合'):m.validator_case(nodes,m.validator_buffer(good_hash=False),5)
    def test_28_wrong_error_oracle_rejected(self):
        with self.assertRaises(ValueError):m.validator_case(self.nodes,m.validator_buffer(3),0)
    def test_29_bad_header_arguments(self):
        with self.assertRaises(ValueError):m.validator_buffer(65536)
    def test_30_known_callee_edges_reused(self):
        links=m.boundary_links(self.new,self.nodes)
        self.assertEqual(links['pending_direct_callees'],[0x08008b49,0x08068ccd,0x080f7dbd,0x081c27dd])
        self.assertTrue(any(r.get('target')==0x093bd971 for r in links['saved_boundary_links']))
    def test_31_continuations_not_closed(self):
        self.assertEqual(m.boundary_links(self.new,self.nodes)['pending_continuations'],[0x081c2ad5,0x093bdaa9,0x093bdaaf,0x093bdb2b,0x093bdb3f])
    def test_32_covered_indirect_remains_scoped(self):
        label='SYNTHETIC_POP_RETURN_NOT_LIVE_FRAME'
        links=m.boundary_links(self.new,self.nodes,{0x0806918c:label})
        self.assertFalse(any(r['site']==0x0806918c for r in links['pending_boundaries']))
        self.assertTrue(any(r['binding']==label for r in links['saved_boundary_links']))


if __name__=='__main__':unittest.main()
