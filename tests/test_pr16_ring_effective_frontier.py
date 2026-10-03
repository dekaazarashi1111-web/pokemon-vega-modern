"""計算ジャンプ表の境界と保存済prefixの結合だけを検証する。ROM/native不要。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_ring_effective_frontier as m


def encoded(values):return b''.join(v.to_bytes(4,'little') for v in values)


class FrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes=json.loads((ROOT/m.OLD).read_text())['analysis']['new_nodes']
        cls.prior=json.loads((ROOT/m.PRIOR).read_text())['analysis']
        cls.context=json.loads((ROOT/m.CONTEXT).read_text())['analysis']
    def changed(self,at,**change):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==at).update(change);return nodes
    def table(self,values=None,occupied=None):
        return m.table_entries(encoded(values or [0x08113824]*5),occupied or set())
    def test_01_saved_prefix(self):
        result=m.bind_table_prefix(self.nodes)
        self.assertEqual(result['table'],0x08113810);self.assertEqual(result['mode_range'],[0,4])
    def test_02_prefix_missing(self):
        with self.assertRaises(ValueError):m.bind_table_prefix([n for n in self.nodes if n['address']!=0x081137fa])
    def test_03_wrong_mode_limit(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x081137fa,hex='0528'))
    def test_04_wrong_branch_relation(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x081137fc,hex='12d2'))
    def test_05_wrong_branch_target(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x081137fc,target=0x08113828))
    def test_06_wrong_mode_pointer(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x081137f6,literal_value=0x03005ed9))
    def test_07_wrong_table_pointer(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x08113800,literal_value=0x08113814))
    def test_08_wrong_table_stride(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x081137fe,hex='4000'))
    def test_09_wrong_pc_transfer(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x08113806,hex='0047'))
    def test_10_wrong_load_width(self):
        with self.assertRaises(ValueError):m.bind_table_prefix(self.changed(0x08113804,hex='0078'))
    def test_11_duplicate_nodes(self):
        with self.assertRaises(ValueError):m.bind_table_prefix([*self.nodes,self.nodes[0]])
    def test_12_table_entries(self):
        rows=self.table([0x08113824,0x08113828,0x0811382a,0x08113824,0x08113828])
        self.assertEqual([r['index'] for r in rows],[0,1,2,3,4])
        self.assertEqual([r['thumb_entry'] for r in rows],[0x08113825,0x08113829,0x0811382b,0x08113825,0x08113829])
    def test_13_short_table(self):
        with self.assertRaises(ValueError):m.table_entries(bytes(16),set())
    def test_14_long_table(self):
        with self.assertRaises(ValueError):m.table_entries(bytes(24),set())
    def test_15_odd_table_target(self):
        with self.assertRaises(ValueError):self.table([0x08113825]*5)
    def test_16_non_rom_target(self):
        with self.assertRaises(ValueError):self.table([0x02000000]*5)
    def test_17_out_of_rom_target(self):
        with self.assertRaises(ValueError):self.table([0x0a000000]*5)
    def test_18_table_self_branch(self):
        with self.assertRaises(ValueError):self.table([m.TABLE]*5)
    def test_19_table_overlaps_instruction(self):
        with self.assertRaises(ValueError):self.table(occupied={m.TABLE+19})
    def test_20_new_roots_include_five_rows_dedup(self):
        roots=m.requested_roots(self.prior,self.context,self.table())
        self.assertEqual(roots,sorted([*m.FIXED,0x08113825]));self.assertNotIn(0x0806dec5,roots)
    def test_21_changed_pending_callee(self):
        prior=copy.deepcopy(self.prior);prior['next_unread_boundaries']['direct_callees'][0]+=2
        with self.assertRaises(ValueError):m.requested_roots(prior,self.context,self.table())
    def test_22_changed_effective_target(self):
        context=copy.deepcopy(self.context);context['resolved_trampoline_targets'][1]+=2
        with self.assertRaises(ValueError):m.requested_roots(self.prior,context,self.table())
    def test_23_incomplete_table_rows(self):
        with self.assertRaises(ValueError):m.requested_roots(self.prior,self.context,self.table()[:4])
    def test_24_memory_merge_identical(self):
        mem={};m.put(mem,0x08000000,b'xy');m.put(mem,0x08000001,b'y')
        self.assertEqual(mem,{0x08000000:120,0x08000001:121})
    def test_25_memory_conflict(self):
        with self.assertRaises(ValueError):m.put({0x08000000:1},0x08000000,b'\x02')
    def test_26_memory_range(self):
        with self.assertRaises(ValueError):m.put({},0x09ffffff,b'xy')
    def test_27_saved_nodes_do_not_decode(self):
        mem={};occupied=m.nodes_to_memory(mem,self.nodes)
        self.assertEqual(len(occupied),sum(n['size'] for n in self.nodes))
        self.assertEqual(bytes(mem[0x0811380c+i] for i in range(4)),m.TABLE.to_bytes(4,'little'))
    def test_28_saved_operand_overlap(self):
        nodes=[{'address':0x08000000,'size':4,'hex':'00f000f8'},
               {'address':0x08000002,'size':2,'hex':'0020'}]
        with self.assertRaises(ValueError):m.nodes_to_memory({},nodes)


if __name__=='__main__':unittest.main()
