"""新Save17 oracle/600frame境界のみ。旧受入試験は呼ばない。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'scripts'), str(Path(__file__).resolve().parents[1])]
import pr16_story_after_maori_accept as m
from pr16_story_after_maori_session import key_command

class InputTests(unittest.TestCase):
    def test_600_boundary(self): self.assertEqual(key_command(0,600), 'key 0 600\n')
    def test_601_rejected(self):
        with self.assertRaises(ValueError): key_command(0,601)
    def test_original_900_rejected(self):
        with self.assertRaises(ValueError): key_command(0,900)
    def test_bool_frames(self):
        with self.assertRaises(ValueError): key_command(0,True)
    def test_bool_key(self):
        with self.assertRaises(ValueError): key_command(True,2)
    def test_combined_key(self):
        with self.assertRaises(ValueError): key_command(3,2)
    def test_zero_frames(self):
        with self.assertRaises(ValueError): key_command(0,0)
    def test_whole_stream_rejects_900_before_native(self):
        with self.assertRaises(ValueError): m.commands(b'key 0 900\nquit\n')
    def test_no_save_helper(self):
        with self.assertRaises(ValueError): m.commands(b'save\nquit\n')
    def test_no_missing_quit(self):
        with self.assertRaises(ValueError): m.commands(b'key 1 2\n')

class OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(os.environ.get('PR16_SAVE17_EVIDENCE', m.source.ART))
        cls.a=m.shared.trace((cls.folder/'progress/stdout.txt').read_bytes(),
            (cls.folder/'progress/commands.txt').read_bytes(),m.source.INPUT_SAVE)
        cls.b=m.shared.trace((cls.folder/'continue/stdout.txt').read_bytes(),
            (cls.folder/'continue/commands.txt').read_bytes(),m.OUTPUT_SAVE)
        cls.before=(cls.folder/'input.srm').read_bytes()
        cls.after=(cls.folder/'story-fast.srm').read_bytes()
    def mutate(self,index,key,value,cold=False):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        (b if cold else a)['observations'][index][key]=value
        with self.assertRaises(ValueError): m.semantic(a,b)
    def test_real_semantic(self): self.assertEqual(m.semantic(self.a,self.b)['trainer_victories'],3)
    def test_real_save(self): self.assertEqual(m.save_structure(self.before,self.after,self.after)['prize_money'],436)
    def test_real_whole_oracle(self): self.assertEqual(m.verify(self.folder)[0]['screens'],119)
    def test_missing_observation(self):
        a=copy.deepcopy(self.a); a['observations'].pop()
        with self.assertRaises(ValueError): m.semantic(a,self.b)
    def test_faint_not_victory(self): self.mutate(34,'battle_outcome',1)
    def test_no_field_unlock(self): self.mutate(39,'lock',1)
    def test_wrong_double_flags(self): self.mutate(14,'battle_flags',12)
    def test_old_outcome_not_new_battle(self): self.mutate(47,'battle_outcome',1)
    def test_field_tail_not_new_battle(self): self.mutate(40,'callback2',m.BATTLE)
    def test_wrong_route(self): self.mutate(64,'map',[4,3])
    def test_premature_save(self): self.mutate(113,'save_counter',17)
    def test_writing_not_anchor(self): self.mutate(113,'flash_sha256',m.FLASH)
    def test_party_injection(self): self.mutate(0,'party_count',6)
    def test_rp_injection(self): self.mutate(2,'rp',1)
    def test_bool_counter(self): self.mutate(0,'save_counter',True)
    def test_cold_wrong_location(self): self.mutate(0,'xy',[7,5],True)
    def test_cold_battle_state_leak(self): self.mutate(0,'battle_flags',12,True)
    def test_cold_party_ui_required(self): self.mutate(1,'callback2',m.FIELD,True)
    def test_cold_party_corruption(self): self.mutate(1,'party_sha256','0'*64,True)
    def test_cold_ledger_corruption(self): self.mutate(0,'ledger_sha256','0'*64,True)
    def test_host_write_rejected(self):
        a=copy.deepcopy(self.a);a['end']['guarded_host_writes']=1
        with self.assertRaises(ValueError): m.semantic(a,self.b)
    def test_save_cold_all_bytes(self):
        cold=bytearray(self.after);cold[-1]^=1
        with self.assertRaises(ValueError): m.save_structure(self.before,self.after,bytes(cold))
    def test_previous_bank_preserved(self):
        after=bytearray(self.after);after[0]^=1
        with self.assertRaises(ValueError): m.save_structure(self.before,bytes(after),bytes(after))
    def test_national_gate_not_relaxed(self):
        after=bytearray(self.after); sec=m.shared.sections(self.after,0xe000,17);after[sec[0]+0x1b]=0xb9
        with self.assertRaises(ValueError): m.save_structure(self.before,bytes(after),bytes(after))

if __name__=='__main__': unittest.main()
