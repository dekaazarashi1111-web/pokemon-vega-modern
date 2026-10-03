"""新規保存6siteだけの独立命令oracleと境界。旧契約/native再実行なし。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_string_contracts as c
import pr16_ring_string_machine as m
b=m.prior.base
AT=min(m.STM_SITES)
DEST=0x02001000


def node(at,raw,kind='ordinary'):
    return {'address':at,'size':len(bytes.fromhex(raw)),'hex':raw,'kind':kind,'memory_write':raw=='08c1'}


def stm(writable=True):
    machine=m.Machine([node(AT,'08c1'),node(AT+2,'7047','return')],[(DEST,bytes(8),writable)],(7,DEST,9,0x12345678))
    machine.flags=(True,False,True,False)
    return machine


def pop(ret=b.RETURN):
    machine=m.Machine([node(m.POP_SITE,'30bd','return')],[])
    machine.r[13]=b.SP-12
    for i,value in enumerate((machine.original[4],machine.original[5],ret)):
        machine.write(b.SP-12+i*4,4,value)
    machine.r[4]=0;machine.r[5]=0;machine.flags=(False,True,False,True)
    return machine


class ExtensionTests(unittest.TestCase):
    def test_stm_byte_order(self):
        machine=stm().run(AT|1);self.assertEqual(machine.data(DEST,8),bytes.fromhex('7856341200000000'))
    def test_stm_writeback(self):self.assertEqual(stm().run(AT|1).r[1],DEST+4)
    def test_stm_flags(self):self.assertEqual(stm().run(AT|1).flags,(True,False,True,False))
    def test_stm_other_registers(self):
        machine=stm();old=machine.r[:];machine.run(AT|1)
        self.assertEqual(machine.r[:1]+machine.r[2:],old[:1]+old[2:])
    def test_stm_steps(self):self.assertEqual(stm().run(AT|1).steps,2)
    def test_stm_write_event(self):self.assertEqual(stm().run(AT|1).nonstack_writes(),[(DEST,4,0x12345678)])
    def test_stm_readonly(self):
        machine=stm(False)
        with self.assertRaisesRegex(ValueError,'未許可 write'):machine.run(AT|1)
        self.assertEqual(machine.r[1],DEST);self.assertEqual(machine.data(DEST,8),bytes(8))
    def test_stm_unaligned(self):
        machine=stm();machine.r[1]+=1
        with self.assertRaisesRegex(ValueError,'write整列'):machine.run(AT|1)
        self.assertEqual(machine.r[1],DEST+1)
    def test_stm_unmapped(self):
        machine=stm();machine.r[1]=DEST+8
        with self.assertRaisesRegex(ValueError,'未許可 write'):machine.run(AT|1)
        self.assertEqual(machine.r[1],DEST+8)
    def test_stm_wrong_opcode(self):
        machine=stm();machine.nodes[AT]['hex']='10c1'
        with self.assertRaisesRegex(ValueError,'未対応保存命令'):machine.run(AT|1)
    def test_stm_wrong_site(self):
        machine=m.Machine([node(0x08010000,'08c1')],[])
        with self.assertRaisesRegex(ValueError,'未対応保存命令'):machine.run(0x08010001)
    def test_stm_wrong_kind(self):
        machine=stm();machine.nodes[AT]['kind']='indirect'
        with self.assertRaisesRegex(ValueError,'未対応間接命令'):machine.run(AT|1)
    def test_stm_wrong_error(self):
        with self.assertRaisesRegex(ValueError,'STM例外境界'):stm().extension(AT,'other')
    def test_stm_step_limit_not_reset(self):
        machine=stm()
        with self.assertRaisesRegex(ValueError,'step上限到達'):machine.run(AT|1,max_steps=1)
        self.assertEqual(machine.steps,1);self.assertEqual(machine.r[1],DEST+4)
    def test_unknown_node_not_swallowed(self):
        with self.assertRaisesRegex(ValueError,'保存node境界で停止'):stm().run(0x08010001)
    def test_pop_odd_return(self):self.assertEqual(pop().run(m.POP_SITE|1).r[13],b.SP)
    def test_pop_even_thumb_return(self):self.assertEqual(pop(b.RETURN&~1).run(m.POP_SITE|1).r[15],b.RETURN&~1)
    def test_pop_restores_registers(self):
        machine=pop().run(m.POP_SITE|1);self.assertEqual(machine.r[4:12],list(machine.original[4:12]))
    def test_pop_flags(self):self.assertEqual(pop().run(m.POP_SITE|1).flags,(False,True,False,True))
    def test_pop_no_external_writes(self):self.assertEqual(pop().run(m.POP_SITE|1).nonstack_writes(),[])
    def test_pop_corrupt_saved_register(self):
        machine=pop();machine.write(b.SP-12,4,0)
        with self.assertRaisesRegex(ValueError,'callee-saved差分'):machine.run(m.POP_SITE|1)
    def test_pop_stack_bounds(self):
        machine=pop();machine.r[13]=b.STACK_HI-8
        with self.assertRaisesRegex(ValueError,'POP stack境界'):machine.run(m.POP_SITE|1)
    def test_pop_unaligned(self):
        machine=pop();machine.r[13]+=1
        with self.assertRaisesRegex(ValueError,'read整列'):machine.run(m.POP_SITE|1)
    def test_pop_wrong_opcode(self):
        machine=pop();machine.nodes[m.POP_SITE]['hex']='10bd'
        with self.assertRaisesRegex(ValueError,'未対応間接命令'):machine.run(m.POP_SITE|1)
    def test_pop_wrong_error(self):
        with self.assertRaisesRegex(ValueError,'POP例外境界'):pop().extension(m.POP_SITE,'other')
    def test_pop_unmapped_pc_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'保存node境界で停止'):pop(0x08010001).run(m.POP_SITE|1)
    def test_extension_size_guard(self):
        machine=stm();machine.nodes[AT]['size']=4
        with self.assertRaisesRegex(ValueError,'拡張命令長'):machine.extension(AT,f'未対応保存命令 {AT:08X}')
    def test_all_five_stm_sites(self):
        for at in m.STM_SITES:
            machine=m.Machine([node(at,'08c1')],[(DEST,bytes(4),True)],(0,DEST,0,255))
            self.assertEqual(machine.extension(at,f'未対応保存命令 {at:08X}'),at+2)
            self.assertEqual(machine.data(DEST,4),b'\xff\0\0\0')


class OracleTests(unittest.TestCase):
    def test_fc_count_three(self):self.assertEqual(c.argument_count(4),3)
    def test_fc_count_two(self):self.assertEqual(c.argument_count(11),2)
    def test_fc_zero_cases(self):self.assertEqual([i for i in range(4,25) if c.argument_count(i)==0],[7,9,15,21,22,23,24])
    def test_fc_invalid(self):
        for value in (True,3,25,'4'):
            with self.assertRaises(ValueError):c.argument_count(value)
    def test_nibble_parity(self):
        self.assertEqual(c.nibble_expected(0,b'\xab'*76),11);self.assertEqual(c.nibble_expected(1,b'\xab'*76),10)
    def test_nibble_last_boundary(self):
        self.assertEqual(c.nibble_expected(151,b'\xfe'*76),15);self.assertEqual(c.nibble_expected(152,b'\xfe'*76),3)
    def test_nibble_low_halfword(self):self.assertEqual(c.nibble_expected(0x10001,b'\xab'*76),10)
    def test_nibble_bad_length(self):
        with self.assertRaises(ValueError):c.nibble_expected(0,bytes(75))
    def test_nibble_bad_arg(self):
        for value in (-1,0x100000000,True):
            with self.assertRaises(ValueError):c.nibble_expected(value,bytes(76))
    def test_fill_zero(self):self.assertEqual(c.fill_writes(DEST,0,0),[])
    def test_fill_word_and_tail(self):self.assertEqual(c.fill_writes(DEST,0x12345678,5),[(DEST,4,0x78787878),(DEST+4,1,0x78)])
    def test_fill_unaligned_is_bytes(self):self.assertEqual(c.fill_writes(DEST+1,255,5),[(DEST+1+i,1,255)for i in range(5)])
    def test_fill_invalid_length(self):
        with self.assertRaises(ValueError):c.fill_writes(DEST,0,-1)
    def test_pending_ranges(self):self.assertEqual(sum(r['length']for r in c.PENDING_DATA),133)
    def test_preflight_rejects_old_nodes(self):
        with self.assertRaisesRegex(ValueError,'保存命令件数'):c.verify([],{'cached_node_count':1576,'new_node_count':176})


if __name__=='__main__':unittest.main()
