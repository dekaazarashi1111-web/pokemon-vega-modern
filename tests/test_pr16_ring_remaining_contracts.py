"""新規SP/NZCVモデル境界と新規fixture構成だけ。受入済みABI/nativeは呼ばない。"""
from pathlib import Path
import sys
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_contract_machine as model
import pr16_ring_remaining_contracts as m
import pr16_ring_saved_contracts as vm
A=0x08000400


def program(words):
    nodes=[]
    for i,h in enumerate(words):
        at=A+2*i;kind='ordinary';extra={}
        if h&0xff87==0x4700:kind='return' if h==0x4770 else 'indirect'
        elif h&0xff87==0x4687:kind='indirect'
        elif h&0xf000==0xd000 and (h>>8)&15<14:
            kind='conditional';d=h&255;extra['target']=at+4+2*(d-256 if d&128 else d)
        nodes.append({'address':at,'size':2,'hex':h.to_bytes(2,'little').hex(),'kind':kind,**extra})
    return nodes


class ModelTests(unittest.TestCase):
    def machine(self,words=(),args=(),segments=()):return model.Machine(program([*words,0x4770]),segments,args)
    def run_words(self,words,args=()):return self.machine(words,args).run(A|1)
    def test_mov_updates_nz(self):
        x=self.run_words([0x2000],(1,));self.assertEqual(x.flags[:2],(False,True))
    def test_and_updates_nz(self):self.assertTrue(self.run_words([0x4008],(1,2)).flags[1])
    def test_eor_updates_nz(self):self.assertTrue(self.run_words([0x4048],(7,7)).flags[1])
    def test_bic_updates_nz(self):self.assertTrue(self.run_words([0x4388],(7,7)).flags[1])
    def test_mvn_updates_nz(self):self.assertTrue(self.run_words([0x43c8],(0,0)).flags[0])
    def test_tst_preserves_register(self):
        x=self.run_words([0x4208],(1,2));self.assertEqual(x.r[0],1);self.assertTrue(x.flags[1])
    def test_lsl_zero_preserves_carry(self):
        x=self.machine();x.flags=(False,False,True,False);self.assertEqual(x.shift(7,0,0),7);self.assertTrue(x.flags[2])
    def test_lsl32(self):
        x=self.machine();self.assertEqual(x.shift(1,32,0),0);self.assertTrue(x.flags[2])
    def test_lsl33(self):
        x=self.machine();self.assertEqual(x.shift(1,33,0),0);self.assertFalse(x.flags[2])
    def test_lsr32(self):
        x=self.machine();self.assertEqual(x.shift(0x80000000,32,1),0);self.assertTrue(x.flags[2])
    def test_asr32_negative(self):self.assertEqual(self.machine().shift(0x80000000,32,2),0xffffffff)
    def test_asr255_positive(self):self.assertEqual(self.machine().shift(0x7fffffff,255,2),0)
    def test_ror32(self):
        x=self.machine();self.assertEqual(x.shift(0x80000001,32,3),0x80000001);self.assertTrue(x.flags[2])
    def test_register_shift_low_byte(self):self.assertEqual(self.run_words([0x4088],(1,0x101)).r[0],2)
    def test_lsr_immediate_zero_means32(self):self.assertEqual(self.run_words([0x0808],(0,0x80000000)).r[0],0)
    def test_mov_nz_branch(self):
        x=self.run_words([0x2000,0xd000,0x2001]);self.assertEqual(x.r[0],0)
    def test_or_nz_branch(self):
        x=self.run_words([0x4308,0xd000,0x2009],(0,0));self.assertEqual(x.r[0],0)
    def test_add_signed_overflow(self):
        x=self.machine();self.assertEqual(x.add_carry(0x7fffffff,0,1),0x80000000);self.assertTrue(x.flags[3])
    def test_add_unsigned_carry(self):
        x=self.machine();self.assertEqual(x.add_carry(0xffffffff,0,1),0);self.assertTrue(x.flags[2])
    def test_sbc_full_borrow(self):
        x=self.machine([0x4188],(0,0xffffffff));x.flags=(False,False,False,False);x.run(A|1)
        self.assertEqual(x.r[0],0);self.assertFalse(x.flags[2])
    def test_adc_undefined_carry_rejected(self):
        x=self.machine([0x4148],(0,0));x.flags=(False,False,None,None)
        with self.assertRaisesRegex(ValueError,'carry'):x.run(A|1)
    def test_mul_carry_unknown(self):
        x=self.run_words([0x4348],(3,4));self.assertEqual(x.r[0],12);self.assertEqual(x.flags[2:],(None,None))
    def test_mul_then_carry_branch_rejected(self):
        with self.assertRaisesRegex(ValueError,'未定義flag'):self.run_words([0x4348,0xd200],(3,4))
    def test_mul_then_cmp_restores_flags(self):self.run_words([0x4348,0x280c,0xd000,0x2009],(3,4))
    def test_sp_relative_roundtrip(self):
        x=self.run_words([0xb500,0xb082,0x9001,0x2000,0x9801,0xb002,0xbc02,0x4708],(0x12345678,))
        self.assertEqual(x.r[0],0x12345678);self.assertEqual(vm.SP-x.low_sp,12)
    def test_sp_address_preserves_flags(self):
        x=self.machine([0xa803]);x.flags=(True,False,True,False);x.run(A|1)
        self.assertEqual(x.r[0],vm.SP+12);self.assertEqual(x.flags,(True,False,True,False))
    def test_sp_underflow_rejected(self):
        with self.assertRaisesRegex(ValueError,'SP境界'):self.run_words([0xb0ff]*9)
    def test_sp_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError,'SP境界'):self.run_words([0xb001])
    def test_missing_data_read_is_recorded(self):
        x=self.machine([0x6800],(0x02000000,))
        with self.assertRaisesRegex(ValueError,'未map'):x.run(A|1)
        self.assertEqual(x.read_fault,{'address':0x02000000,'size':4,'site':A})
    def test_readonly_write_rejected(self):
        x=self.machine([0x6001],(0x02000000,7),[(0x02000000,bytes(4),False)])
        with self.assertRaisesRegex(ValueError,'未許可'):x.run(A|1)
    def test_mov_pc_requires_saved_target(self):
        with self.assertRaisesRegex(ValueError,'保存node'):self.run_words([0x4687],(A+100,))
    def test_bx_even_state_rejected(self):
        with self.assertRaisesRegex(ValueError,'ARM state'):self.run_words([0x4700],(A+2,))
    def test_unknown_opcode_rejected(self):
        with self.assertRaisesRegex(ValueError,'未対応'):self.run_words([0xdf00])
    def test_data_segment_alias_rejected(self):
        with self.assertRaisesRegex(ValueError,'重複'):self.machine(segments=[(vm.SP,bytes(4),True)])


class FixtureTests(unittest.TestCase):
    def test_vgs_length_rejected(self):
        with self.assertRaises(ValueError):m.seal(bytes(2047))
    def test_vacq_length_rejected(self):
        with self.assertRaises(ValueError):m.validator_data(bytes(239))
    def test_crc_matches_zeroed_slot(self):
        data=bytearray(m.acquisition(17));saved=int.from_bytes(data[8:12],'little');data[8:12]=bytes(4)
        self.assertEqual(saved,zlib.crc32(data))
    def test_initial_boolean_normalization(self):self.assertEqual(m.initialized_data(1),m.initialized_data(0xffffffff))
    def test_initial_false_differs(self):self.assertNotEqual(m.initialized_data(0),m.initialized_data(1))
    def test_checksum_slot(self):
        data=m.initialized_data(1);self.assertEqual(int.from_bytes(data[8:12],'little'),vm.checksum(data))
    def test_three_finite_data_ranges(self):self.assertEqual(sum(row['length'] for row in m.TABLES),440)
    def test_seed_bool_rejected(self):
        with self.assertRaises(ValueError):m.acquisition(True)

if __name__=='__main__':unittest.main()
