"""特殊野生診断の結果境界。旧native/旧unitを呼ばない。"""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('special_wild',Path(__file__).resolve().parents[1]/'scripts/pr16_special_wild.py')
s=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(s)


def party(last=92):
    raw=bytearray(100);struct.pack_into('<I',raw,0,123);struct.pack_into('<H',raw,32,1);raw[84]=25
    struct.pack_into('<4H',raw,44,10,39,33,last);raw[52:56]=bytes([35,30,35,10]);return raw.hex()


def fixture(method='fishing'):
    entries=[0x08082750,0x093BEA68,0x09392714] if method=='fishing' else [0x09220198,0x093BEA98,0x0939273C]
    rows=[dict(event='fixture',method=method,dispatch_status=0,profile=1,transitions=1000,normal_unlock_claimed=False),dict(event='call',attempt=1,seed=1,entry=entries[0]+1,map=[11,3])]
    rows += [dict(event='entry',attempt=1,step=i+1,pc=pc,lr=1) for i,pc in enumerate(entries)]
    rows += [dict(event='special_setter',attempt=1,step=10,pc=0x09114698,lr=0x09320001,move=92,slot=3),dict(event='before_apply',attempt=1,step=20,party=party()),dict(event='after_return',attempt=1,step=30,party=party(45)),dict(event='result',attempt=1,returned=1,species=1,special_setters=1,apply_calls=1),dict(event='summary',status='OBSERVED',method=method,calls=1,host_write_violations=0,direct_call_fixture=True,gameplay_accepted=False,save_continue_accepted=False)]
    return rows


def raw(rows):return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()


class Boundary(unittest.TestCase):
    def test_both_methods_detect_overwrite(self):
        for name in s.METHODS:
            v=s.validate(raw(fixture(name)),name);self.assertEqual(v['classification'],'SPECIAL_SLOT_OVERWRITTEN');self.assertFalse(v['runtime_accepted'])
    def test_preserved_is_not_overwrite(self):
        rows=fixture();rows[-3]['party']=party();self.assertEqual(s.validate(raw(rows),'fishing')['classification'],'SPECIAL_SLOT_PRESERVED')
    def test_cannot_promote_direct_call(self):
        for key in ('gameplay_accepted','save_continue_accepted'):
            rows=fixture();rows[-1][key]=True
            with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_write_violation_rejected(self):
        rows=fixture();rows[-1]['host_write_violations']=1
        with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_missing_and_duplicate_events(self):
        for index in (5,6,7,8):
            for mode in ('drop','duplicate'):
                rows=fixture()
                if mode=='drop':rows.pop(index)
                else:rows.insert(index,copy.deepcopy(rows[index]))
                with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_wrong_order_rejected(self):
        rows=fixture();rows[5]['step']=25
        with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_different_individual_rejected(self):
        rows=fixture();p=bytearray.fromhex(rows[-3]['party']);p[0]^=1;rows[-3]['party']=p.hex()
        with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_unobserved_special_rejected(self):
        rows=fixture();rows[5]['move']=99
        with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_changed_delegate_rejected(self):
        rows=fixture();rows[3]['pc']=0x09392714
        with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_no_success_and_bad_counts_rejected(self):
        for count in (0,True,9,2):
            rows=fixture();rows[-1]['calls']=count
            with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
        rows=fixture();rows[-1]['status']='NO_SPECIAL_WITNESS'
        with self.assertRaises(ValueError):s.validate(raw(rows),'fishing')
    def test_duplicate_json_and_invalid_party(self):
        for r in (b'{"event":"summary","event":"result"}',b''):
            with self.assertRaises(ValueError):s.decode_lines(r)
        for p in ('00'*100,'gg'*100,party()+'00'):
            with self.assertRaises(ValueError):s.mon(p)
    def test_exact_candidate_hash_gate(self):
        with self.assertRaises(ValueError):s.anchors(b'VEGAQP36')
    def test_anchor_byte_contract(self):
        rom=bytearray(33554432);q=0x1200000;rom[q:q+8]=b'VEGAQP36'
        struct.pack_into('<12I',rom,q+8,1,0x2000,0x1000,35,1,846,1,0x09200101,0x09200121,0x09200141,0x0203B5E8,0x0203B6E8)
        for off in (0x82750,0x1220198,0x13925F4):rom[off:off+8]=bytes.fromhex('004b184781f85f09')
        with patch.object(s,'CANDIDATE',s.identity(rom)):
            self.assertEqual(s.anchors(rom)['dispatch'],0x09200121)
        rom[0x82750]=1
        with patch.object(s,'CANDIDATE',s.identity(rom)):
            with self.assertRaises(ValueError):s.anchors(rom)


if __name__=='__main__':unittest.main()
