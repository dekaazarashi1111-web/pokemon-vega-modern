"""実描画/heap採取の有限scopeと10要素分岐表を検査。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_runtime_bytes as m


def original():
    p=os.environ.get('PR16_UI_CONTEXT')
    if p:return json.loads(Path(p).read_bytes())
    import pr16_ring_followup_v2 as s
    nodes,_,_=m.saved_inputs();return {'nodes':nodes,'analysis':s.load(m.PRIOR)['analysis']}


def table(v=0x08001af0):return v.to_bytes(4,'little')*10


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.raw=original()
    def test_plan(self):self.assertEqual(m.plan(self.raw['analysis'],self.raw['nodes']),sorted((*m.DIRECT,*m.EFFECTIVE)))
    def reject_analysis(self,k,v):
        p=copy.deepcopy(self.raw['analysis']);p[k]=v
        with self.assertRaises(ValueError):m.plan(p,self.raw['nodes'])
    def test_count(self):self.reject_analysis('saved_node_count',3594)
    def test_direct(self):self.reject_analysis('pending_direct_callees',[])
    def test_effective(self):self.reject_analysis('pending_effective_targets',[])
    def test_continuations(self):self.reject_analysis('pending_continuations',[m.DIRECT[0]])
    def test_accepted(self):self.reject_analysis('ring_acquisition_accepted',True)
    def test_callback(self):self.reject_analysis('actual_callback_table_observed',True)
    def test_scope_type(self):self.reject_analysis('release_ready',0)
    def test_missing_nodes(self):
        with self.assertRaises(ValueError):m.plan(self.raw['analysis'],self.raw['nodes'][:-1])
    def test_selector_opcode(self):
        p=copy.deepcopy(self.raw['nodes']);next(n for n in p if n['address']==0x08001ab4)['hex']='0828'
        with self.assertRaises(ValueError):m.plan(self.raw['analysis'],p)
    def test_table_location(self):
        p=copy.deepcopy(self.raw['nodes']);next(n for n in p if n['address']==0x08001aba)['literal_value']+=4
        with self.assertRaises(ValueError):m.plan(self.raw['analysis'],p)


class TableTests(unittest.TestCase):
    def test_table(self):self.assertEqual(m.table_targets(table()),[0x08001af0]*10)
    def test_distinct(self):
        values=[0x08001af0+2*i for i in range(10)]
        self.assertEqual(m.table_targets(b''.join(v.to_bytes(4,'little')for v in values)),values)
    def test_short(self):
        with self.assertRaises(ValueError):m.table_targets(table()[:-1])
    def test_long(self):
        with self.assertRaises(ValueError):m.table_targets(table()+b'0')
    def test_ram(self):
        with self.assertRaises(ValueError):m.table_targets(table(0x02000000))
    def test_odd(self):
        with self.assertRaises(ValueError):m.table_targets(table(0x08001af1))
    def test_into_table(self):
        with self.assertRaises(ValueError):m.table_targets(table(m.TABLE))
    def test_rom_end(self):
        with self.assertRaises(ValueError):m.table_targets(table(0x0a000000))
    def test_null(self):
        with self.assertRaises(ValueError):m.table_targets(table(0))
    def test_type(self):
        with self.assertRaises(ValueError):m.table_targets(bytearray(table()))


if __name__=='__main__':unittest.main()
