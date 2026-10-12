"""新しい逆参照器の人工境界。旧map/LZ/native試験は呼ばない。"""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_asset_xrefs as m


class InverseTests(unittest.TestCase):
    def scan(self, raw, low=0x0880FA64, high=0x0880FA68, **kw):
        return m.inverse_pointers(raw, 0x08000000, low, high, **kw)
    def test_no_match(self):
        self.assertEqual(self.scan(b'\x00'*16), [])
    def test_unaligned_start(self):
        raw=b'X'+struct.pack('<I',m.HIT)+b'Y'
        self.assertEqual(self.scan(raw)[0]['address'],0x08000001)
    def test_last_four_bytes(self):
        self.assertEqual(self.scan(b'X'*8+struct.pack('<I',m.HIT))[0]['address'],0x08000008)
    def test_first_four_bytes(self):
        self.assertEqual(self.scan(struct.pack('<I',m.HIT))[0]['address'],0x08000000)
    def test_three_mirrors(self):
        rows=self.scan(b''.join(struct.pack('<I',m.HIT+i*m.ROM_SIZE) for i in range(3)))
        self.assertEqual([r['mirror'] for r in rows],[0,1,2])
        self.assertEqual({r['canonical_target'] for r in rows},{m.HIT})
    def test_lower_included(self):
        self.assertEqual(len(self.scan(struct.pack('<I',m.HIT))),1)
    def test_upper_excluded(self):
        self.assertEqual(self.scan(struct.pack('<I',m.HIT+4)),[])
    def test_below_excluded(self):
        self.assertEqual(self.scan(struct.pack('<I',m.HIT-1)),[])
    def test_cross_high16_page(self):
        raw=struct.pack('<II',0x0880FFFF,0x08810000)
        self.assertEqual(len(self.scan(raw,0x0880FFFE,0x08810001)),2)
    def test_truncated_needle_start(self):
        self.assertEqual(self.scan(b'\x80\x08X'),[])
    def test_hash_binds_full_pointer(self):
        raw=struct.pack('<I',m.HIT)
        self.assertEqual(self.scan(raw)[0]['sha256'],hashlib.sha256(raw).hexdigest())
    def test_duplicate_occurrences_preserved(self):
        self.assertEqual(len(self.scan(struct.pack('<I',m.HIT)*3)),3)
    def test_limit_fails_not_truncates(self):
        with self.assertRaises(ValueError):self.scan(struct.pack('<I',m.HIT)*2,limit=1)
    def test_oversize_range_rejected(self):
        with self.assertRaises(ValueError):self.scan(b'1234',m.HIT-9000,m.HIT)
    def test_invalid_range_rejected(self):
        for lo,hi in ((m.HIT,m.HIT),(0x07000000,0x07000001),(0x09FFFFFF,0x0A000001)):
            with self.subTest(lo=lo),self.assertRaises(ValueError):self.scan(b'1234',lo,hi)
    def test_noninteger_rejected(self):
        with self.assertRaises(ValueError):self.scan(b'1234',True,m.HIT)
    def test_mirror_end_rejected(self):
        with self.assertRaises(ValueError):m.canonical(0x0E000000)
    def test_against_bruteforce(self):
        raw=bytearray(range(256))*6
        for at,value in ((1,m.HIT),(43,m.HIT-1),(199,m.HIT+3),(422,m.HIT+0x02000000),(981,m.HIT+0x04000000)):
            struct.pack_into('<I',raw,at,value)
        want=[]
        for at in range(len(raw)-3):
            value=struct.unpack_from('<I',raw,at)[0]
            if 0x08000000<=value<0x0E000000 and m.HIT<=m.canonical(value)<m.HIT+4:want.append(0x08000000+at)
        self.assertEqual([r['address'] for r in self.scan(raw)],want)
    def test_deterministic_read_only(self):
        raw=struct.pack('<I',m.HIT);before=raw[:]
        self.assertEqual(m.encode(self.scan(raw)),m.encode(self.scan(raw)))
        self.assertEqual(raw,before)


class LiteralTests(unittest.TestCase):
    def test_pc_alignment_and_register(self):
        raw=struct.pack('<HHI',0x4B00,0,0x12345678)
        row=m.literal_shapes(raw,0x08000000,0x08000004)[0]
        self.assertEqual((row['address'],row['register']),(0x08000000,3))
        self.assertFalse(row['actual_instruction_fetch_proven'])
    def test_halfword_pc_alignment(self):
        raw=struct.pack('<HHI',0,0x4800,0)
        self.assertEqual(m.literal_shapes(raw,0x08000000,0x08000004)[0]['address'],0x08000002)
    def test_unaligned_literal_not_shape(self):
        self.assertEqual(m.literal_shapes(b'\x00'*12,0x08000000,0x08000005),[])
    def test_wrong_literal_rejected(self):
        raw=struct.pack('<HHII',0x4801,0,0,0)
        self.assertEqual(m.literal_shapes(raw,0x08000000,0x08000004),[])
    def test_maximum_offset(self):
        raw=bytearray(1032);struct.pack_into('<H',raw,0,0x48FF)
        self.assertEqual(m.literal_shapes(raw,0x08000000,0x08000400)[0]['address'],0x08000000)
    def test_outside_input_rejected(self):
        with self.assertRaises(ValueError):m.literal_shapes(b'1234',0x08000000,0x08000004)


class SymbolTests(unittest.TestCase):
    @staticmethod
    def source():
        return b'x\t08000001\tx\tx\tAlpha\tx\tx\tx\nx\t08000020\tx\tx\tBeta\tx\tx\tx\n'
    def test_alias_thumb_and_following(self):
        n=m.neighborhood(m.symbol_index(self.source()),0x08000010)
        self.assertEqual(n['preceding']['address'],0x08000000)
        self.assertEqual(n['following']['address'],0x08000020)
        self.assertFalse(n['current_owner_proven'])
    def test_before_first_and_after_last(self):
        idx=m.symbol_index(self.source())
        self.assertIsNone(m.neighborhood(idx,0x07FFFFFF)['preceding'])
        self.assertIsNone(m.neighborhood(idx,0x08000020)['following'])
    def test_empty_symbols_rejected(self):
        with self.assertRaises(ValueError):m.symbol_index(b'header\n')
    def test_measure_requires_exact_candidate(self):
        with self.assertRaises(ValueError):m.measure(b'1234',self.source())
    def test_interval_overflow(self):
        with self.assertRaises(ValueError):m.interval(0xFFFFFFFF,2)


if __name__=='__main__':unittest.main()
