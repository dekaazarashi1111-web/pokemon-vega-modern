"""未map・未知opcode・書込/stack破壊・未読継続を拒否する保存契約検査。"""
from pathlib import Path
import copy
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_ring_saved_contracts as m


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frontier=json.loads((ROOT/m.FRONTIER).read_text())['analysis']
        patch=json.loads((ROOT/m.PATCH).read_text())
        cls.nodes=m.saved_nodes(frontier,patch)
    def vm(self,segments=(),args=()):return m.Machine(self.nodes,list(segments),args)
    def data_vm(self,data,args=None):return self.vm([(m.BUFFER,data,True)],args or (m.BUFFER,))
    def test_01_callback(self):
        vm=self.data_vm(bytes(16),(m.BUFFER,0x8068ddd)).run(m.CALLBACK)
        self.assertEqual(vm.data(m.BUFFER+4,4),(0x8068ddd).to_bytes(4,'little'))
        self.assertEqual(vm.nonstack_writes(),[(m.BUFFER+1,1,2),(m.BUFFER+4,4,0x8068ddd)])
    def test_02_callback_alignment(self):
        with self.assertRaisesRegex(ValueError,'整列'):self.data_vm(bytes(16),(m.BUFFER+1,1)).run(m.CALLBACK)
    def test_03_readonly_write_rejected(self):
        with self.assertRaisesRegex(ValueError,'未許可'):self.vm([(m.BUFFER,bytes(16),False)],(m.BUFFER,1)).run(m.CALLBACK)
    def test_04_le32(self):
        for word in (0,1,255,256,65535,65536,0x80000000,0xffffffff):
            vm=self.data_vm(bytes(8),(m.BUFFER,word)).run(m.WRITE)
            self.assertEqual(vm.data(m.BUFFER,4),word.to_bytes(4,'little'))
            self.assertEqual(len(vm.nonstack_writes()),4)
    def test_05_cursor(self):
        ctx=bytearray(16);ctx[8:12]=(m.BACKUP).to_bytes(4,'little')
        vm=self.vm([(m.BUFFER,bytes(ctx),True),(m.BACKUP,b'\x04\x03\x02\x01',False)],(m.BUFFER,)).run(m.CURSOR)
        self.assertEqual(vm.r[0],0x01020304);self.assertEqual(vm.read(m.BUFFER+8,4),m.BACKUP+4)
        self.assertEqual(m.SP-vm.low_sp,16)
    def test_06_cursor_unmapped(self):
        with self.assertRaisesRegex(ValueError,'未map'):self.data_vm(bytes(16)).run(m.CURSOR)
    def test_07_copy_one(self):
        vm=self.vm([(m.BUFFER,b'\0',True),(m.BACKUP,b'Z',False)],(m.BUFFER,m.BACKUP,1)).run(m.COPY)
        self.assertEqual(vm.data(m.BUFFER,1),b'Z');self.assertEqual(m.SP-vm.low_sp,8)
    def test_08_copy_exact_2048(self):
        raw=bytes(range(256))*8
        vm=self.vm([(m.BUFFER,bytes(2048),True),(m.BACKUP,raw,False)],(m.BUFFER,m.BACKUP,2048)).run(m.COPY)
        self.assertEqual(vm.data(m.BUFFER,2048),raw);self.assertEqual(len(vm.nonstack_writes()),2048)
    def test_09_zero_copy_is_not_empty(self):
        vm=self.vm([(m.BUFFER,bytes(1),True),(m.BACKUP,b'X',False)],(m.BUFFER,m.BACKUP,0))
        with self.assertRaises(ValueError):vm.run(m.COPY)
        self.assertEqual(vm.nonstack_writes(),[(m.BUFFER,1,ord('X'))])
    def test_10_hash_null(self):
        vm=self.vm(args=(0,)).run(m.HASH);self.assertEqual(vm.r[0],0);self.assertEqual(vm.nonstack_writes(),[])
    def test_11_hash_oracle(self):
        data=bytes((i*19+23)&255 for i in range(2048))
        vm=self.data_vm(data).run(m.HASH);self.assertEqual(vm.r[0],m.checksum(data));self.assertEqual(vm.nonstack_writes(),[])
    def test_12_checksum_excluded_slot(self):
        data=bytearray(bytes(range(256))*8);a=self.data_vm(bytes(data)).run(m.HASH).r[0]
        data[8:12]=b'\xff'*4;b=self.data_vm(bytes(data)).run(m.HASH).r[0]
        self.assertEqual(a,b)
    def test_13_checksum_nonexcluded_byte(self):
        data=bytearray(2048);a=self.data_vm(bytes(data)).run(m.HASH).r[0]
        data[12]=1;b=self.data_vm(bytes(data)).run(m.HASH).r[0]
        self.assertNotEqual(a,b)
    def test_14_metadata_init(self):
        vm=self.vm([(m.META,b'\xa5'*96,True)]).run(m.INIT)
        self.assertEqual(vm.data(m.META,96),m.metadata_expected());self.assertEqual(len(vm.nonstack_writes()),101)
    def test_15_ensure_valid_unchanged(self):
        raw=bytearray(b'\xa5'*96);raw[:4]=(0x31564552).to_bytes(4,'little')
        vm=self.vm([(m.META,bytes(raw),True)]).run(m.ENSURE)
        self.assertEqual(vm.data(m.META,96),bytes(raw));self.assertEqual(vm.nonstack_writes(),[])
    def test_16_ensure_invalid_nested_frame(self):
        vm=self.vm([(m.META,bytes(96),True)]).run(m.ENSURE)
        self.assertEqual(vm.data(m.META,96),m.metadata_expected());self.assertEqual(m.SP-vm.low_sp,16)
    def test_17_validator_null(self):self.assertEqual(self.vm(args=(0,0)).run(m.VALIDATE).r[0],6)
    def test_18_validator_short(self):self.assertEqual(self.vm([(0x02001000,b'\1'*2048,True)],(0x02001000,2047)).run(m.VALIDATE).r[0],4)
    def test_19_validator_empty(self):self.assertEqual(self.vm([(0x02001000,bytes(2048),True)],(0x02001000,2048)).run(m.VALIDATE).r[0],1)
    def test_20_validator_erased(self):self.assertEqual(self.vm([(0x02001000,b'\xff'*2048,True)],(0x02001000,2048)).run(m.VALIDATE).r[0],1)
    def test_21_validator_bad_magic(self):self.assertEqual(self.vm([(0x02001000,b'\1'*2048,True)],(0x02001000,2048)).run(m.VALIDATE).r[0],2)
    def test_22_validator_success_remains_boundary(self):
        data=bytearray(b'\1'*2048);data[:4]=(0x31534756).to_bytes(4,'little')
        vm=self.vm([(0x02001000,bytes(data),True)],(0x02001000,2048))
        with self.assertRaisesRegex(ValueError,'保存node境界'):vm.run(m.VALIDATE)
        self.assertEqual(vm.last_pc,0x093bda28)
    def test_23_global_validator_initialization(self):
        vm=self.vm([(m.BUFFER,bytes(2048),True),(m.META,bytes(96),True)],(m.BUFFER,2048)).run(m.VALIDATE)
        self.assertEqual(vm.r[0],1);self.assertEqual(vm.data(m.META,96),m.metadata_expected())
        self.assertEqual(len(vm.nonstack_writes()),102)
    def test_24_segment_stack_alias_rejected(self):
        with self.assertRaisesRegex(ValueError,'重複'):self.vm([(m.SP,bytes(4),True)])
    def test_25_segment_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,'重複'):self.vm([(10,bytes(2),True),(11,bytes(2),False)])
    def test_26_step_limit(self):
        with self.assertRaisesRegex(ValueError,'step上限'):self.data_vm(bytes(2048)).run(m.HASH,10)
    def test_27_missing_saved_node(self):
        nodes=[n for n in self.nodes if n['address']!=0x80690ba]
        with self.assertRaisesRegex(ValueError,'保存node境界'):m.Machine(nodes,[(m.BUFFER,bytes(16),True)],(m.BUFFER,1)).run(m.CALLBACK)
    def test_28_bad_return_state(self):
        vm=self.data_vm(bytes(16),(m.BUFFER,1));vm.r[14]=m.RETURN&~1
        with self.assertRaisesRegex(ValueError,'ARM state'):vm.run(m.CALLBACK)
    def test_29_stack_pop_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x9378ba2)['hex']='00bc'
        with self.assertRaises(ValueError):m.Machine(nodes,[(m.BUFFER,bytes(1),True),(m.BACKUP,b'Z',False)],(m.BUFFER,m.BACKUP,1)).run(m.COPY)
    def test_30_branch_target_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x9378ba0)['target']+=2
        with self.assertRaisesRegex(ValueError,'branch結合'):m.Machine(nodes,[(m.BUFFER,bytes(1),True),(m.BACKUP,b'Z',False)],(m.BUFFER,m.BACKUP,1)).run(m.COPY)
    def test_31_unknown_effect_rejected(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x80690b4)['hex']='00de'
        with self.assertRaises(ValueError):m.Machine(nodes,[(m.BUFFER,bytes(16),True)],(m.BUFFER,1)).run(m.CALLBACK)
    def test_32_u32_oracle_length(self):
        with self.assertRaises(ValueError):m.checksum(bytes(2047))


if __name__=='__main__':unittest.main()
