"""VarGet値域、POP継続、未証明allocation境界の新規単体検証。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_dispatch_contracts as c


class HelperTests(unittest.TestCase):
    def test_zero(self):self.assertEqual(c.helper_result(0),0)
    def test_immediate_upper(self):self.assertEqual(c.helper_result(0x3fff),0)
    def test_ordinary_lower(self):self.assertEqual(c.helper_result(0x4000),0)
    def test_ordinary_upper(self):self.assertEqual(c.helper_result(0x40ff),0)
    def test_suppressed_lower(self):self.assertEqual(c.helper_result(0x4100),1)
    def test_before_extended(self):self.assertEqual(c.helper_result(0x4fff),1)
    def test_extended_lower(self):self.assertEqual(c.helper_result(0x5000),0x0203b2e8)
    def test_extended_upper(self):self.assertEqual(c.helper_result(0x51ff),0x0203b6e6)
    def test_after_extended(self):self.assertEqual(c.helper_result(0x5200),1)
    def test_suppressed_upper(self):self.assertEqual(c.helper_result(0x7fff),1)
    def test_special_lower(self):self.assertEqual(c.helper_result(0x8000),0)
    def test_special_upper(self):self.assertEqual(c.helper_result(0xffff),0)
    def test_reject_non_u16(self):
        for v in (-1,65536,True,None,'1'):
            with self.subTest(v=v),self.assertRaises(ValueError):c.helper_result(v)
    def test_partition(self):
        counts={0:0,1:0,'pointer':0}
        for v in range(65536):
            out=c.helper_result(v);counts[out if out<2 else'pointer']+=1
        self.assertEqual(counts,{0:49408,1:15616,'pointer':512})


class RouteTests(unittest.TestCase):
    def test_immediate_identity(self):self.assertEqual(c.route(0x3fff),{'kind':'immediate','value':0x3fff})
    def test_suppressed_identity(self):self.assertEqual(c.route(0x4100),{'kind':'immediate','value':0x4100})
    def test_saveblock_lower(self):self.assertEqual(c.route(0x4000)['offset'],0x1000)
    def test_saveblock_upper(self):self.assertEqual(c.route(0x40ff)['offset'],0x11fe)
    def test_extended_lower(self):self.assertEqual(c.route(0x5000)['address'],0x0203b2e8)
    def test_extended_upper(self):self.assertEqual(c.route(0x51ff)['address'],0x0203b6e6)
    def test_special_lower(self):self.assertEqual(c.route(0x8000)['table_slot'],0x08163014)
    def test_special_upper(self):self.assertEqual(c.route(0xffff)['table_slot'],0x08183010)
    def test_u32_truncation(self):
        for v in (0,0x4000,0x4100,0x5000,0x8000,0xffff):self.assertEqual(c.route(0xabcd0000|v),c.route(v))
    def test_reject_non_u32(self):
        for v in (-1,0x100000000,True,None,'1'):
            with self.subTest(v=v),self.assertRaises(ValueError):c.route(v)
    def test_no_map_for_immediate(self):self.assertEqual(c.var_segments(0x5200),([],0x5200,None))
    def test_null_special_returns_input(self):
        seg,value,target=c.var_segments(0x8000,pointer=0)
        self.assertEqual(value,0x8000);self.assertIsNone(target);self.assertEqual(seg,[(0x08163014,bytes(4),False)])
    def test_short_halfword_is_one_byte(self):
        segments,_,_=c.var_segments(0x5000,short=True);self.assertEqual(len(segments[-1][1]),1)
    def test_missing_halfword_not_stubbed(self):self.assertEqual(c.var_segments(0x5000,present=False)[0],[])
    def test_selector_and_data_readonly(self):
        segments,_,_=c.var_segments(0x4000,2)
        self.assertEqual(segments[0],(c.SELECTOR,b'\2',False));self.assertTrue(all(not s[2]for s in segments))


class PopTests(unittest.TestCase):
    def machine(self):
        n={'address':c.POP_SITE,'hex':'70bd','size':2,'kind':'return','memory_write':False}
        m=c.Machine([n],[]);m.r[13]=c.vm.SP-16
        for i,value in enumerate([*m.original[4:7],c.vm.RETURN]):m.write(m.r[13]+i*4,4,value)
        m.r[4:7]=[0,0,0];return m
    def test_exact_return_restores_registers_sp(self):
        m=self.machine().run(c.POP_SITE|1);self.assertEqual(m.r[13],c.vm.SP);self.assertEqual(m.r[4:7],list(m.original[4:7]))
    def test_pop_ignores_bit_zero(self):
        m=self.machine();m.write(c.vm.SP-4,4,c.vm.RETURN&~1);m.run(c.POP_SITE|1);self.assertEqual(m.r[13],c.vm.SP)
    def test_reject_opcode_mutation(self):
        m=self.machine();m.nodes[c.POP_SITE]['hex']='30bd'
        with self.assertRaises(ValueError):m.pop_return(c.POP_SITE,'未対応間接命令')
    def test_reject_kind_mutation(self):
        m=self.machine();m.nodes[c.POP_SITE]['kind']='ordinary'
        with self.assertRaises(ValueError):m.pop_return(c.POP_SITE,'未対応間接命令')
    def test_reject_size_mutation(self):
        m=self.machine();m.nodes[c.POP_SITE]['size']=4
        with self.assertRaises(ValueError):m.pop_return(c.POP_SITE,'未対応間接命令')
    def test_reject_exception_mismatch(self):
        with self.assertRaises(ValueError):self.machine().pop_return(c.POP_SITE,'未対応間接命令ではない')
    def test_reject_stack_high(self):
        m=self.machine();m.r[13]=c.vm.STACK_HI-12
        with self.assertRaises(ValueError):m.pop_return(c.POP_SITE,'未対応間接命令')
    def test_reject_stack_low(self):
        m=self.machine();m.r[13]=c.vm.STACK_LO-4
        with self.assertRaises(ValueError):m.pop_return(c.POP_SITE,'未対応間接命令')
    def test_reject_unaligned_stack(self):
        m=self.machine();m.r[13]-=1
        with self.assertRaises(ValueError):m.pop_return(c.POP_SITE,'未対応間接命令')


if __name__=='__main__':unittest.main()
