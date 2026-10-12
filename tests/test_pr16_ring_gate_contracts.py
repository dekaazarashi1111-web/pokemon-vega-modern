"""81要素/帰還context/12byte recordの境界と追加3転送命令。旧単独契約は実行しない。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_gate_contracts as c


class ExpansionTests(unittest.TestCase):
    def test_image_size(self):self.assertEqual(len(c.expansion((0,1,2))[0]),168)
    def test_write_count(self):self.assertEqual(len(c.expansion((0,1,2))[1]),84)
    def test_metadata_order(self):self.assertEqual(c.expansion((0,1,2))[0][-6:],b'\x01\0\0\0\x02\0')
    def test_first_and_last(self):
        data,_=c.expansion((0,1,2));self.assertEqual((data[:2],data[160:162]),(b'\x11\x11',b'\x22\x22'))
    def test_dimension_stride(self):
        data,_=c.expansion((0,1,2));self.assertEqual([int.from_bytes(data[i*2:i*2+2],'little')for i in (1,3,9,27)],[0x0111,0x1011,0x1101,0x1110])
    def test_81_distinct_for_distinct_nibbles(self):
        data,_=c.expansion((0,1,15));self.assertEqual(len({data[i:i+2]for i in range(0,162,2)}),81)
    def test_eight_bit_normalization(self):self.assertEqual(c.expansion((256,257,511)),c.expansion((0,1,255)))
    def test_output_16bit_truncation(self):
        data,_=c.expansion((255,255,255));self.assertEqual(data[:162],b'\xff'*162)
    def test_metadata_written_before_table(self):
        _,w=c.expansion((0,1,2));self.assertEqual(w[:3],[(c.COMBINATIONS+162,2,1),(c.COMBINATIONS+164,2,0),(c.COMBINATIONS+166,2,2)])
        self.assertEqual([p for p,_,_ in w[3:]],list(range(c.COMBINATIONS,c.COMBINATIONS+162,2)))
    def test_length_rejected(self):
        with self.assertRaises(ValueError):c.expansion((1,2))
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):c.expansion((True,1,2))
    def test_negative_rejected(self):
        with self.assertRaises(ValueError):c.expansion((-1,1,2))
    def test_wrap_rejected(self):
        with self.assertRaises(ValueError):c.expansion((0x100000000,1,2))


class ContextTests(unittest.TestCase):
    def test_32_bytes(self):self.assertEqual(len(c.context_image(bytes(16),1,0)),32)
    def test_descriptor_and_pointer(self):
        src=bytes(range(16));x=c.context_image(src,1,0x08012345)
        self.assertEqual(x[:20],src+b'E#\x01\x08');self.assertEqual(x[20:],bytes(7)+bytes([1,0,1,0,0]))
    def test_127_normalized(self):self.assertEqual(c.context_image(bytes(16),127,0),c.context_image(bytes(16),1,0))
    def test_383_normalized(self):self.assertEqual(c.context_image(bytes(16),383,0),c.context_image(bytes(16),1,0))
    def test_dispatch_modes_not_decremented(self):
        self.assertEqual(c.context_image(bytes(16),0,0)[29],0);self.assertEqual(c.context_image(bytes(16),255,0)[29],255)
    def test_short_descriptor(self):
        with self.assertRaises(ValueError):c.context_image(bytes(15),1,0)
    def test_pointer_overflow(self):
        with self.assertRaises(ValueError):c.context_image(bytes(16),1,0x100000000)
    def test_bool_mode(self):
        with self.assertRaises(ValueError):c.context_image(bytes(16),True,0)
    def test_record_exact(self):
        self.assertEqual(c.record_args(bytes([7,0,0,5,9,0,0x34,0x12,0x78,0x56,0x34,0x12])),[7,0x12345678,1440,0x1234])
    def test_record_product_truncation(self):
        raw=bytes([0,0,0,255,255,0,0,0,0,0,0,0]);self.assertEqual(c.record_args(raw)[2],(255*255*32)&65535)
    def test_record_short(self):
        with self.assertRaises(ValueError):c.record_args(bytes(11))


class TransferTests(unittest.TestCase):
    def machine(self,pc):
        n={'address':pc,'size':2,'hex':c.TRANSFERS[pc],'kind':'ordinary'}
        m=c.Machine([n],[(c.caller.CTX,bytes(range(16)),True)])
        m.r[0]=m.r[1]=m.r[5]=c.caller.CTX;return m
    def test_stack_word_load(self):
        pc=0x08002ed4;m=self.machine(pc);m.r[5]=c.vm.SP-16;m.write(m.r[5],4,0x12345678)
        m.transfer_new(pc,f'未対応保存命令 {pc:08X}');self.assertEqual((m.r[1],m.r[5]),(0x12345678,c.vm.SP-12))
    def test_resource_three_word_load(self):
        pc=0x08003f06;m=self.machine(pc);m.transfer_new(pc,f'未対応保存命令 {pc:08X}')
        self.assertEqual([m.r[i]for i in (2,4,6)],[0x03020100,0x07060504,0x0b0a0908]);self.assertEqual(m.r[1],c.caller.CTX+12)
    def test_resource_three_word_store(self):
        pc=0x08003f08;m=self.machine(pc);m.r[2],m.r[4],m.r[6]=1,2,3;m.transfer_new(pc,f'未対応保存命令 {pc:08X}')
        self.assertEqual(m.writes,[(c.caller.CTX,4,1),(c.caller.CTX+4,4,2),(c.caller.CTX+8,4,3)])
    def test_flags_preserved(self):
        pc=0x08002ed4;m=self.machine(pc);m.flags=(True,False,True,False);m.transfer_new(pc,f'未対応保存命令 {pc:08X}')
        self.assertEqual(m.flags,(True,False,True,False))
    def test_opcode_tamper(self):
        pc=0x08002ed4;m=self.machine(pc);m.nodes[pc]['hex']='03cd'
        with self.assertRaises(ValueError):m.transfer_new(pc,f'未対応保存命令 {pc:08X}')
    def test_unknown_error(self):
        pc=0x08002ed4;m=self.machine(pc)
        with self.assertRaises(ValueError):m.transfer_new(pc,'未map read')
    def test_read_boundary(self):
        pc=0x08003f06;m=self.machine(pc);m.r[1]+=8
        with self.assertRaises(ValueError):m.transfer_new(pc,f'未対応保存命令 {pc:08X}')
    def test_write_boundary(self):
        pc=0x08003f08;m=self.machine(pc);m.r[0]+=8
        with self.assertRaises(ValueError):m.transfer_new(pc,f'未対応保存命令 {pc:08X}')
    def test_unaligned(self):
        pc=0x08002ed4;m=self.machine(pc);m.r[5]+=1
        with self.assertRaises(ValueError):m.transfer_new(pc,f'未対応保存命令 {pc:08X}')


class ArchiveTests(unittest.TestCase):
    def test_bound_archive_not_discarded(self):
        original={'contracts':[{'writes':[(1,1,2)]}],'limited_stops':[{'writes':[]}]}
        result,raw=c.archive_effects(original)
        self.assertEqual(result['raw_effects_identity'],c.identity(raw));self.assertEqual(result['contracts'][0]['nonstack_write_count'],1)
        self.assertNotIn('writes',result['contracts'][0]);self.assertIn('writes',original['contracts'][0])
    def test_distinct_write_changes_binding(self):
        a={'contracts':[{'writes':[(1,1,2)]}],'limited_stops':[]}
        b={'contracts':[{'writes':[(1,1,3)]}],'limited_stops':[]}
        self.assertNotEqual(c.archive_effects(a)[0]['raw_effects_identity'],c.archive_effects(b)[0]['raw_effects_identity'])


if __name__=='__main__':unittest.main()
