"""New Save18 completion/S61E guards only; never run old native cases."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_ayame_accept as m


def fixture():
    last=dict(save_counter=18,map=[5,4],xy=[7,4],live_xy=[14,11],facing=2,party_count=4,rp=0,
              callback2=m.chain.FIELD,lock=0,party_sha256=m.PARTY,flash_sha256=m.FLASH,
              ledger_sha256='847e0b99bded52ce70fbcab4f13accf1ef41ab98a728f4679cff6baeb79aaebb',
              battle_flags=12,battle_outcome=1)
    cold=[dict(last,battle_flags=0,battle_outcome=0,lock=0 if i in (0,4) else 1,
               callback2=m.chain.PARTY_UI if i == 2 else m.chain.FIELD) for i in range(5)]
    return last,cold


def record(flag=3,extra=None):
    data=bytearray(0x606);data[0x100]=flag
    if extra is not None:data[extra]=1
    payload=bytes(data);crc=zlib.crc32(payload)
    return struct.pack('<4sHHII',b'S61E',1,0x606,crc,crc^0xffffffff)+payload


class CompletionTests(unittest.TestCase):
    def bad(self,key,value,cold=False):
        last,rows=fixture(); (rows[0] if cold else last)[key]=value
        with self.assertRaises(ValueError):m.completion(last,rows)
    def test_completed_save_and_cold(self):m.completion(*fixture())
    def test_partial_counter17_rejected(self):self.bad('save_counter',17)
    def test_counter18_still_locked_rejected(self):self.bad('lock',1)
    def test_partial_flash_with_counter18_rejected(self):self.bad('flash_sha256','0'*64)
    def test_cold_fallback17_rejected(self):self.bad('save_counter',17,True)
    def test_cold_flash_change_rejected(self):self.bad('flash_sha256','0'*64,True)
    def test_cold_party_change_rejected(self):self.bad('party_sha256','0'*64,True)
    def test_cold_ledger_change_rejected(self):self.bad('ledger_sha256','0'*64,True)
    def test_cold_map_change_rejected(self):self.bad('map',[3,1],True)
    def test_wrong_saved_coordinate_rejected(self):self.bad('xy',[7,5])
    def test_wrong_live_coordinate_rejected(self):self.bad('live_xy',[14,12])
    def test_boolean_lock_rejected(self):self.bad('lock',False)
    def test_missing_party_ui_rejected(self):
        last,rows=fixture();rows[2]['callback2']=m.chain.FIELD
        with self.assertRaises(ValueError):m.completion(last,rows)
    def test_missing_cold_terminal_rejected(self):
        last,rows=fixture()
        with self.assertRaises(ValueError):m.completion(last,rows[:-1])
    def test_cold_rematch_rejected(self):self.bad('battle_flags',12,True)
    def test_rp_injection_rejected(self):self.bad('rp',1)
    def test_actual_failed_development_rejected(self):
        r=json.loads((m.ROOT/m.DEV/'expected.json').read_text())['failure']
        last,rows=fixture();last.update(r['last_observation'])
        self.assertEqual(r['failed_cold_counter'],17)
        with self.assertRaises(ValueError):m.completion(last,rows)


class S61ETests(unittest.TestCase):
    def test_only_gym_bit_and_crc_change(self):
        self.assertEqual(m.s61e_boundary(record(3),record(11))['changed_flag'],4355)
    def test_other_flag_change_rejected(self):
        with self.assertRaises(ValueError):m.s61e_boundary(record(3),record(15))
    def test_missing_gate_bit_rejected(self):
        with self.assertRaises(ValueError):m.s61e_boundary(record(3),record(3))
    def test_other_flag_byte_rejected(self):
        with self.assertRaises(ValueError):m.s61e_boundary(record(),record(11,extra=0))
    def test_other_var_rejected(self):
        with self.assertRaises(ValueError):m.s61e_boundary(record(),record(11,extra=0x200))
    def test_last_ball_rejected(self):
        with self.assertRaises(ValueError):m.s61e_boundary(record(),record(11,extra=0x600))
    def test_coin_change_rejected(self):
        with self.assertRaises(ValueError):m.s61e_boundary(record(),record(11,extra=0x602))
    def test_bad_crc_rejected(self):
        raw=bytearray(record());raw[8]^=1
        with self.assertRaises(ValueError):m.s61e_record(bytes(raw))
    def test_bad_complement_rejected(self):
        raw=bytearray(record());raw[12]^=1
        with self.assertRaises(ValueError):m.s61e_record(bytes(raw))
    def test_truncated_record_rejected(self):
        with self.assertRaises(ValueError):m.s61e_record(record()[:-1])
    def test_extra_record_bytes_rejected(self):
        with self.assertRaises(ValueError):m.s61e_record(record()+b'\0')
    def test_wrong_magic_version_size_rejected(self):
        for index in (0,4,6):
            raw=bytearray(record());raw[index]^=1
            with self.subTest(index=index),self.assertRaises(ValueError):m.s61e_record(bytes(raw))
    def test_non_bytes_rejected(self):
        with self.assertRaises(ValueError):m.s61e_record(bytearray(record()))


if __name__=='__main__':unittest.main()
