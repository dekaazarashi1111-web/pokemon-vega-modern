"""実中継literalの固定と未知辺の非昇格。既受入のnative/契約は起動しない。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_delegates as m


def original():
    p=os.environ.get('PR16_UI_CONTEXT')
    if p:return json.loads(Path(p).read_bytes())
    import pr16_ring_followup_v2 as s
    nodes,_,_=m.saved_inputs();return {'nodes':nodes,'analysis':s.load(m.PRIOR)['analysis']}


def tail(target=m.HOOK,register=3):
    return [{'address':0x08010000,'size':2,'hex':((0x4800|(register<<8)|1).to_bytes(2,'little')).hex(),
        'kind':'ordinary','literal_value':target},
        {'address':0x08010002,'size':2,'hex':((0x4700|(register<<3)).to_bytes(2,'little')).hex(),'kind':'indirect'}]


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.raw=original()
    def test_plan(self):self.assertEqual(m.plan(self.raw['analysis'],self.raw['nodes']),sorted((*m.CALLEES,m.HOOK)))
    def test_hook(self):self.assertEqual(m.hook_target(self.raw['nodes']),m.HOOK)
    def test_bad_hook(self):
        p=copy.deepcopy(self.raw['nodes']);next(n for n in p if n['address']==0x08002dd2)['literal_value']+=2
        with self.assertRaises(ValueError):m.hook_target(p)
    def test_hook_opcode(self):
        p=copy.deepcopy(self.raw['nodes']);next(n for n in p if n['address']==0x08002dd4)['hex']='0047'
        with self.assertRaises(ValueError):m.hook_target(p)
    def test_hook_pool(self):
        p=copy.deepcopy(self.raw['nodes']);next(n for n in p if n['address']==0x08002dd2)['literal_address']+=4
        with self.assertRaises(ValueError):m.hook_target(p)
    def test_hook_register(self):
        p=copy.deepcopy(self.raw['nodes']);next(n for n in p if n['address']==0x08002dd4)['register']=0
        with self.assertRaises(ValueError):m.hook_target(p)
    def test_node_count(self):
        with self.assertRaises(ValueError):m.plan(self.raw['analysis'],self.raw['nodes'][:-1])
    def test_duplicate(self):
        p=self.raw['nodes'][:-1]+[self.raw['nodes'][0]]
        with self.assertRaises(ValueError):m.plan(self.raw['analysis'],p)
    def test_scope(self):
        p=copy.deepcopy(self.raw['analysis']);p['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.plan(p,self.raw['nodes'])
    def test_pending(self):
        p=copy.deepcopy(self.raw['analysis']);p['pending_direct_callees']=[]
        with self.assertRaises(ValueError):m.plan(p,self.raw['nodes'])
    def test_continuation(self):
        p=copy.deepcopy(self.raw['analysis']);p['pending_continuations']=[m.HOOK]
        with self.assertRaises(ValueError):m.plan(p,self.raw['nodes'])


class TailTests(unittest.TestCase):
    def test_literal_tail(self):self.assertEqual(m.literal_tails(tail())[0]['target'],m.HOOK)
    def test_all_low_registers(self):
        for reg in range(8):self.assertTrue(m.literal_tails(tail(register=reg))[0]['thumb_rom_target'])
    def test_register_mismatch(self):
        p=tail();p[1]['hex']='0047';self.assertEqual(m.literal_tails(p),[])
    def test_no_preceding_load(self):self.assertEqual(m.literal_tails(tail()[1:]),[])
    def test_even_arm(self):self.assertFalse(m.literal_tails(tail(m.HOOK&~1))[0]['thumb_rom_target'])
    def test_null(self):self.assertFalse(m.literal_tails(tail(0))[0]['thumb_rom_target'])
    def test_ram_not_followed(self):self.assertFalse(m.literal_tails(tail(0x02001001))[0]['thumb_rom_target'])
    def test_return_not_all_callers(self):self.assertIn('NOT_ALL_ENTRY_PATHS',m.literal_tails(tail())[0]['binding'])
    def test_literal_u32(self):
        with self.assertRaises(ValueError):m.literal_tails(tail(-1))
    def test_not_load_opcode(self):
        p=tail();p[0]['hex']='0023';self.assertEqual(m.literal_tails(p),[])


if __name__=='__main__':unittest.main()
