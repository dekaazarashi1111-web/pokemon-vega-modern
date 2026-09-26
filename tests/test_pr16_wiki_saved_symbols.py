"""新規保存ELF読取の異常境界。既存受入suite・ROM・ARMを使わない。"""
from __future__ import annotations
import copy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_wiki_elf_symbols import Elf
from pr16_candidate_wiki_inputs import BASE


def fixture():
    raw = bytearray(512)
    raw[:7] = b'\x7fELF\x01\x01\x01'
    struct.pack_into('<HHI', raw, 16, 2, 40, 1)
    struct.pack_into('<I', raw, 32, 52)
    struct.pack_into('<H', raw, 40, 52)
    struct.pack_into('<HH', raw, 46, 40, 4)
    struct.pack_into('<10I', raw, 92, 0, 1, 6, BASE, 240, 8, 0, 0, 2, 0)
    struct.pack_into('<10I', raw, 132, 0, 3, 0, 0, 260, 9, 0, 0, 1, 0)
    struct.pack_into('<10I', raw, 172, 0, 2, 0, 0, 280, 32, 2, 0, 4, 16)
    raw[240:248] = b'\x00\xb5\x01\x20\x00\xbd\x00\x00'
    raw[260:269] = b'\0Caller\0\0'
    struct.pack_into('<IIIBBH', raw, 296, 1, BASE|1, 6, 0x12, 0, 1)
    return raw


class SavedSymbolsTests(unittest.TestCase):
    def elf(self, edit=None):
        raw = fixture()
        if edit: edit(raw)
        return Elf(bytes(raw))
    def rejection(self, edit):
        with self.assertRaises((ValueError, UnicodeDecodeError)): self.elf(edit)
    def test_thumb_address(self): self.assertEqual(self.elf().symbols['Caller'][0]['address'], BASE|1)
    def test_exact_body(self): self.assertEqual(self.elf().bind('Caller',bytes(fixture()[240:248]))['status'],'EXACT_CANDIDATE_SYMBOL_BODY')
    def test_body_hashes_equal(self):
        r=self.elf().bind('Caller',bytes(fixture()[240:248]));self.assertEqual(r['saved_sha256'],r['candidate_sha256'])
    def test_changed_body(self): self.assertEqual(self.elf().bind('Caller',b'\0'*8)['status'],'CANDIDATE_BODY_DIFFERS')
    def test_small_candidate(self): self.assertEqual(self.elf().bind('Caller',b'\0')['status'],'SYMBOL_OUTSIDE_CANDIDATE')
    def test_missing(self): self.assertEqual(self.elf().bind('Absent',b'\0'*8)['status'],'MISSING_SAVED_SYMBOL')
    def test_ambiguous(self):
        e=self.elf();e.symbols['Caller'].append(dict(e.symbols['Caller'][0],address=BASE+3));self.assertEqual(e.bind('Caller',b'\0'*8)['status'],'AMBIGUOUS_SAVED_SYMBOL')
    def test_zero_extent(self):
        e=self.elf(lambda b:struct.pack_into('<I',b,304,0));self.assertEqual(e.bind('Caller',b'\0'*8)['status'],'SYMBOL_WITHOUT_PROVEN_EXTENT')
    def test_absolute_symbol(self):
        e=self.elf(lambda b:struct.pack_into('<H',b,310,0xFFF1));self.assertEqual(e.bind('Caller',b'\0'*8)['status'],'SYMBOL_WITHOUT_ALLOCATED_BODY')
    def test_other_type(self):
        e=self.elf(lambda b:b.__setitem__(308,0x10));self.assertEqual(e.bind('Caller',b'\0'*8)['status'],'UNSUPPORTED_SYMBOL_TYPE')
    def test_no_native_claim(self):
        r=self.elf().bind('Caller',bytes(fixture()[240:248]));self.assertEqual(r['native_acceptance'],'DEFERRED_AUDIT');self.assertFalse(r['source_equivalence_proven'])
    def test_invalid_magic(self): self.rejection(lambda b:b.__setitem__(0,0))
    def test_big_endian(self): self.rejection(lambda b:b.__setitem__(5,2))
    def test_elf64(self): self.rejection(lambda b:b.__setitem__(4,2))
    def test_bad_ident_version(self): self.rejection(lambda b:b.__setitem__(6,2))
    def test_bad_machine(self): self.rejection(lambda b:struct.pack_into('<H',b,18,3))
    def test_bad_type(self): self.rejection(lambda b:struct.pack_into('<H',b,16,3))
    def test_bad_version(self): self.rejection(lambda b:struct.pack_into('<I',b,20,2))
    def test_bad_header_size(self): self.rejection(lambda b:struct.pack_into('<H',b,40,64))
    def test_bad_section_stride(self): self.rejection(lambda b:struct.pack_into('<H',b,46,32))
    def test_zero_sections(self): self.rejection(lambda b:struct.pack_into('<H',b,48,0))
    def test_section_table_overflow(self): self.rejection(lambda b:struct.pack_into('<I',b,32,500))
    def test_section_file_overflow(self): self.rejection(lambda b:struct.pack_into('<I',b,112,1000))
    def test_address_overflow(self): self.rejection(lambda b:struct.pack_into('<I',b,104,0xFFFFFFFC))
    def test_symbol_stride(self): self.rejection(lambda b:struct.pack_into('<I',b,208,8))
    def test_symbol_size_multiple(self): self.rejection(lambda b:struct.pack_into('<I',b,192,31))
    def test_strtab_link_range(self): self.rejection(lambda b:struct.pack_into('<I',b,196,6))
    def test_strtab_type(self): self.rejection(lambda b:struct.pack_into('<I',b,136,1))
    def test_string_offset(self): self.rejection(lambda b:struct.pack_into('<I',b,296,10))
    def test_string_termination(self): self.rejection(lambda b:b.__setitem__(slice(267,269),b'xx'))
    def test_invalid_symbol_section(self): self.rejection(lambda b:struct.pack_into('<H',b,310,17))
    def test_symbol_outside_own_section(self):
        e=self.elf(lambda b:struct.pack_into('<I',b,304,10))
        with self.assertRaises(ValueError): e.span(e.symbols['Caller'][0])
    def test_nobits(self):
        e=self.elf(lambda b:struct.pack_into('<I',b,96,8))
        with self.assertRaises(ValueError): e.span(e.symbols['Caller'][0])
    def test_non_alloc(self):
        e=self.elf(lambda b:struct.pack_into('<I',b,100,0))
        with self.assertRaises(ValueError): e.span(e.symbols['Caller'][0])
    def test_explicit_bounded_span(self): self.assertEqual(len(self.elf().span(self.elf().symbols['Caller'][0],2)),2)
    def test_bool_size_rejected(self):
        with self.assertRaises(ValueError): self.elf().span(self.elf().symbols['Caller'][0],True)
    def test_stable_read(self): self.assertEqual(self.elf().symbols,self.elf().symbols)
    def test_no_mutation(self):
        raw=fixture();before=bytes(raw);Elf(raw).bind('Caller',b'\0'*8);self.assertEqual(raw,before)

if __name__=='__main__': unittest.main()
