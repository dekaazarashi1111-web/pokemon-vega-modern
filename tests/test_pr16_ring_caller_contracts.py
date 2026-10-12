"""caller前提・有限容量・新規転送命令の反例。ROM/旧単独契約は実行しない。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_caller_contracts as c


class TaskTests(unittest.TestCase):
    def test_empty(self):self.assertEqual(c.task_chain(c.task_fixture([],[])),[])
    def test_full(self):self.assertEqual(len(c.task_chain(c.task_fixture(list(range(16)),[0]*16))),16)
    def test_scrambled(self):self.assertEqual(c.task_chain(c.task_fixture([9,1,14],[2,2,255])),[9,1,14])
    def test_short(self):
        with self.assertRaises(ValueError):c.task_chain(bytes(639))
    def test_mutable_rejected(self):
        with self.assertRaises(ValueError):c.task_chain(bytearray(640))
    def bad(self,offset,value):
        data=bytearray(c.task_fixture([1,4],[10,20]));data[offset]=value
        with self.assertRaises(ValueError):c.task_chain(bytes(data))
    def test_active_invalid(self):self.bad(2*40+4,2)
    def test_no_head(self):self.bad(40+5,255)
    def test_two_heads(self):self.bad(4*40+5,254)
    def test_cyclic(self):self.bad(4*40+6,4)
    def test_next_out_of_range(self):self.bad(4*40+6,16)
    def test_early_terminator(self):self.bad(40+6,255)
    def test_inactive_link(self):self.bad(40+6,3)
    def test_bad_inverse(self):self.bad(4*40+5,2)
    def test_descending_priority(self):self.bad(4*40+7,9)
    def test_unreachable_active(self):self.bad(3*40+4,1)
    def test_fixture_duplicate(self):
        with self.assertRaises(ValueError):c.task_fixture([1,1],[0,0])
    def test_fixture_bool(self):
        with self.assertRaises(ValueError):c.task_fixture([True],[0])
    def test_create_first_free(self):
        data=c.task_fixture([0,2],[10,20]);out,slot,writes,chain=c.created(data,0x08012345,15)
        self.assertEqual(slot,1);self.assertEqual(chain,[0,1,2]);self.assertEqual(c.task_chain(out),chain)
        self.assertEqual(writes[0],(c.TASKS+40,4,0x08012345));self.assertEqual(writes[-1],(c.TASKS+44,1,1))
        self.assertEqual(out[48:80],bytes(32))
    def test_create_tie_is_stable(self):
        data=c.task_fixture([9,1],[10,10]);self.assertEqual(c.created(data,1,10)[3],[9,1,0])
    def test_create_priority_normalized(self):
        data=c.task_fixture([1],[50]);self.assertEqual(c.created(data,1,0x12340032),c.created(data,1,50))
    def test_create_full_no_write(self):
        data=c.task_fixture(list(range(16)),list(range(16)));out,value,writes,_=c.created(data,1,0)
        self.assertEqual((out,value,writes),(data,0,[]))
    def test_full_and_slot0_return_ambiguity(self):
        empty=c.created(c.task_fixture([],[]),1,0);full=c.created(c.task_fixture(list(range(16)),[0]*16),1,0)
        self.assertEqual(empty[1],full[1]);self.assertNotEqual(bool(empty[2]),bool(full[2]))
    def test_invalid_callback(self):
        with self.assertRaises(ValueError):c.created(c.task_fixture([],[]),-1,0)


class TextTests(unittest.TestCase):
    def test_first_ff_only(self):self.assertEqual(c.text_body(b'AB\xfflater\xff'),b'AB\xff')
    def test_unterminated(self):
        with self.assertRaises(ValueError):c.text_body(b'ABC')
    def test_recursive_fd_rejected(self):
        with self.assertRaises(ValueError):c.text_body(b'\xfd\x01\xff')
    def test_control_fc_rejected(self):
        with self.assertRaises(ValueError):c.text_body(b'\xfc\x04\xff')
    def test_capacity_includes_ff(self):
        out,writes=c.fd_expected(c.CTX,[b'AB\xff']);self.assertEqual(out,b'PAB`\xff')
        self.assertEqual(writes,[(c.CTX,1,80),(c.CTX+1,1,65),(c.CTX+2,1,66),(c.CTX+3,1,255),(c.CTX+3,1,96),(c.CTX+4,1,255)])
    def test_repeated_fd_temporaries(self):
        out,writes=c.fd_expected(c.CTX,[b'A\xff',b'B\xff']);self.assertEqual(out,b'PA`B`\xff')
        self.assertEqual(sum(v==255 for _,_,v in writes),3)
    def test_empty_name(self):self.assertEqual(c.fd_expected(c.CTX,[b'\xff'])[0],b'P`\xff')
    def test_no_names(self):
        with self.assertRaises(ValueError):c.fd_expected(c.CTX,[])
    def test_capacity_wrap(self):
        with self.assertRaises(ValueError):c.fd_expected(0xfffffffe,[b'AB\xff'])


class TransferTests(unittest.TestCase):
    def machine(self,pc=0x08002d30,raw=None):
        n={'address':pc,'hex':raw or c.TRANSFERS[pc],'size':2,'kind':'ordinary'}
        m=c.Machine([n],[(c.CTX,bytes(range(32)),True)],());m.r[0]=m.r[1]=c.CTX;return m
    def apply(self,m,pc):return m.transfer(pc,f'未対応保存命令 {pc:08X}')
    def test_load_three_and_writeback(self):
        m=self.machine();original=m.r.copy();self.apply(m,0x08002d30)
        self.assertEqual([m.r[i]for i in (2,3,7)],[0x03020100,0x07060504,0x0b0a0908]);self.assertEqual(m.r[0],c.CTX+12)
        self.assertTrue(all(m.r[i]==original[i]for i in range(16)if i not in (0,2,3,7)))
    def test_store_order_and_writeback(self):
        pc=0x08002d32;m=self.machine(pc);m.r[2],m.r[3],m.r[7]=1,2,3;self.apply(m,pc)
        self.assertEqual(m.writes,[(c.CTX,4,1),(c.CTX+4,4,2),(c.CTX+8,4,3)]);self.assertEqual(m.r[1],c.CTX+12)
    def test_flags_unchanged(self):
        m=self.machine();m.flags=(True,False,True,False);self.apply(m,0x08002d30);self.assertEqual(m.flags,(True,False,True,False))
    def test_tamper_rejected(self):
        m=self.machine(raw='8dc8')
        with self.assertRaises(ValueError):self.apply(m,0x08002d30)
    def test_wrong_exception_rejected(self):
        m=self.machine()
        with self.assertRaises(ValueError):m.transfer(0x08002d30,'未map read')
    def test_unaligned_rejected(self):
        m=self.machine();m.r[0]+=1
        with self.assertRaises(ValueError):self.apply(m,0x08002d30)
    def test_unmapped_rejected(self):
        m=self.machine();m.r[0]=c.SRC
        with self.assertRaises(ValueError):self.apply(m,0x08002d30)
    def test_wrong_kind_rejected(self):
        m=self.machine();m.nodes[0x08002d30]['kind']='return'
        with self.assertRaises(ValueError):self.apply(m,0x08002d30)
    def test_outside_frame_diagnostic(self):
        m=self.machine();m.write(c.vm.SP+4,1,255)
        self.assertEqual(c.outside_writes(m,[(c.CTX,32)]),[[c.vm.SP+4,1,255]])
    def test_owned_frame_write_allowed(self):
        m=self.machine();m.low_sp=c.vm.SP-4;m.write(m.low_sp,4,1)
        self.assertFalse(c.outside_writes(m,[(c.CTX,32)]))
    def test_stack_object_alias_rejected(self):
        with self.assertRaises(ValueError):c.outside_writes(self.machine(),[(c.vm.SP,4)])
    def test_call_snapshot_is_copy(self):
        m=self.machine();m.nodes[0x8001000]={'kind':'call','target':c.INSERT-1}
        m.r[:4]=[1,2,3,4];m.nodes[0x8001000];m.r[0]=99
        self.assertEqual(m.call_arguments[0]['args'],[1,2,3,4])


if __name__=='__main__':unittest.main()
