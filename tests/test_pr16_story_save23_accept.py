"""保存された新原本だけを変更検出に使用。nativeと旧caseは再実行しない。"""
import copy
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save23_accept as m


class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(os.environ['PR16_SAVE23_ORIGINAL'])
        cls.a=m.measured.trace(cls.folder/'progress',m.measured.plan.INPUT_SAVE)
        cls.b=m.measured.trace(cls.folder/'continue',m.OUTPUT)
        cls.before=(cls.folder/'input.srm').read_bytes();cls.after=(cls.folder/'story-fast.srm').read_bytes()
        cls.cold=(cls.folder/'cold.srm').read_bytes()
        s=m.parent.sectors;ta,_=s.bank(cls.before,0,22,s.LAYOUT);tb,_=s.bank(cls.after,0xe000,23,s.LAYOUT)
        cls.fa,cls.va=s.legacy_state(cls.before,ta);cls.fb,cls.vb=s.legacy_state(cls.after,tb)
    def test_original_full_verification(self):
        v,l=m.verify(self.folder);self.assertEqual((v['boundary']['changed_bytes'],len(l['ranges'])),(7000,1788))
    def test_original_native_accounting(self):self.assertEqual(m.semantics(self.a,self.b)['save_counter'],23)
    def test_observed_auxiliary_change(self):self.assertFalse(m.flag_vars(self.fa,self.va,self.fb,self.vb)['auxiliary_flag2056_runtime_owner_resolved'])
    def test_another_flag_rejected(self):
        fb=bytearray(self.fb);fb[0]^=1
        with self.assertRaises(ValueError):m.flag_vars(self.fa,self.va,bytes(fb),self.vb)
    def test_missing_flag_change_rejected(self):
        with self.assertRaises(ValueError):m.flag_vars(self.fa,self.va,self.fa,self.vb)
    def test_extra_var_rejected(self):
        vb=list(self.vb);vb[0x73]+=1
        with self.assertRaises(ValueError):m.flag_vars(self.fa,self.va,self.fb,vb)
    def test_wrong_auxiliary_var_rejected(self):
        vb=list(self.vb);vb[0x21]+=1
        with self.assertRaises(ValueError):m.flag_vars(self.fa,self.va,self.fb,vb)
    def test_national_unlock_rejected(self):
        vb=list(self.vb);vb[0x4e]=0x6258
        with self.assertRaises(ValueError):m.flag_vars(self.fa,self.va,self.fb,vb)
    def test_story_unlock_rejected(self):
        vb=list(self.vb);vb[0x72]=9
        with self.assertRaises(ValueError):m.flag_vars(self.fa,self.va,self.fb,vb)
    def test_cold_save_byte_change_rejected(self):
        cold=bytearray(self.cold);cold[-1]^=1
        with self.assertRaises(ValueError):m.boundary(self.before,self.after,bytes(cold))
    def test_wrong_parent_rejected(self):
        before=bytearray(self.before);before[0]^=1
        with self.assertRaises(ValueError):m.boundary(bytes(before),self.after,self.cold)
    def reject_observation(self,lane,index,key,value):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        (a if lane=='a' else b)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantics(a,b)
    def test_wrong_warp_rejected(self):self.reject_observation('a',7,'map',[1,72])
    def test_wrong_coordinate_rejected(self):self.reject_observation('a',7,'xy',[20,4])
    def test_party_change_rejected(self):self.reject_observation('a',7,'party_sha256','0'*64)
    def test_hidden_battle_rejected(self):self.reject_observation('a',7,'battle_flags',12)
    def test_hidden_rp_rejected(self):self.reject_observation('a',7,'rp',1)
    def test_partial_save_not_accepted(self):self.reject_observation('a',12,'save_counter',23)
    def test_no_success_wording_boundary(self):self.reject_observation('a',13,'flash_sha256',m.parent.FLASH)
    def test_menu_end_not_field(self):self.reject_observation('a',14,'field',False)
    def test_cold_requires_unlock(self):self.reject_observation('b',1,'lock',1)
    def test_cold_state_mismatch(self):self.reject_observation('b',1,'ledger_sha256','0'*64)
    def test_truncated_trace_rejected(self):
        raw=(self.folder/'progress/stdout.txt').read_bytes().splitlines(keepends=True)
        with self.assertRaises(ValueError):m.parent.parent.trace(b''.join(raw[:-1]),(self.folder/'progress/commands.txt').read_bytes(),m.measured.plan.INPUT_SAVE)
    def test_unapproved_input_rejected(self):
        with self.assertRaises(ValueError):m.parent.commands(b'write 0 1\nquit\n')
    def test_extra_input_rejected(self):
        command=(self.folder/'progress/commands.txt').read_bytes().replace(b'quit\n',b'key 1 1\nquit\n')
        with self.assertRaises(ValueError):m.parent.parent.trace((self.folder/'progress/stdout.txt').read_bytes(),command,m.measured.plan.INPUT_SAVE)


if __name__=='__main__':unittest.main()
