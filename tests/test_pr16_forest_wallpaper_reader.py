"""新Forest仕様モデルの拒否境界。既受入consumerやprivate ROMは使わない。"""
import copy
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_forest_wallpaper_reader as m


class Memory:
    def __init__(self, raw, src=0x1000, dst=0x2000, extent=32):
        self.mem = {src+i: v for i, v in enumerate(raw)}
        self.dst, self.extent = dst, extent
        self.reads, self.writes = [], []
    def read(self, address, size):
        m.need(size == 1 and address in self.mem, '未束縛read')
        self.reads.append(address)
        return self.mem[address]
    def write(self, address, size, value):
        m.need(size == 1 and self.dst <= address < self.dst+self.extent, '許可域外write')
        self.mem[address] = value
        self.writes.append(address)


def layout():
    return dict(object_size=8192, wallpaperOffset=0, wallpaperLoadState=1,
                wallpaperLoadBoxId=2, wallpaperLoadDir=3, wallpaperTilemap=4,
                wallpaperBgTilemapBuffer=724)


class ReaderModelTests(unittest.TestCase):
    def decode(self, raw, size, **kwargs):
        memory = Memory(raw, extent=size)
        result = m.lz10(memory, 0x1000, 0x2000, len(raw), size, **kwargs)
        return result, memory
    def reject(self, raw, size):
        with self.assertRaises(ValueError):
            self.decode(raw, size)
    def test_literals(self):
        result, mem = self.decode(b'\x10\x03\0\0\0ABC', 3)
        self.assertEqual(result, {'consumed': 8, 'output': m.identity(b'ABC')})
        self.assertEqual(mem.reads, list(range(0x1000, 0x1008)))
        self.assertEqual(mem.writes, list(range(0x2000, 0x2003)))
    def test_overlapping_backreference(self):
        result, mem = self.decode(b'\x10\x06\0\0\x40A\x20\0', 6)
        self.assertEqual(result['output'], m.identity(b'AAAAAA'))
        self.assertEqual(mem.writes, list(range(0x2000, 0x2006)))
        self.assertTrue(all(a in mem.reads for a in range(0x1000, 0x1008)))
    def test_second_flag_group(self):
        result, _ = self.decode(b'\x10\x09\0\0\0ABCDEFGH\0I', 9)
        self.assertEqual(result['output'], m.identity(b'ABCDEFGHI'))
    def test_maximum_reference_length(self):
        result, _ = self.decode(b'\x10\x13\0\0\x40Z\xf0\0', 19)
        self.assertEqual(result['output'], m.identity(b'Z'*19))
    def test_flags_after_declared_end_not_consumed(self):
        self.reject(b'\x10\x01\0\0\0A\0', 1)
    def test_nonzero_tail_rejected(self):
        self.reject(b'\x10\x01\0\0\0Ax', 1)
    def test_wrong_header(self):
        self.reject(b'\x11\x01\0\0\0A', 1)
    def test_wrong_declared_size(self):
        self.reject(b'\x10\x02\0\0\0A', 1)
    def test_zero_output(self):
        self.reject(b'\x10\0\0\0', 0)
    def test_huge_output(self):
        self.reject(b'\x10\0\0\1', 65536)
    def test_missing_flag(self):
        self.reject(b'\x10\x01\0\0', 1)
    def test_missing_literal(self):
        self.reject(b'\x10\x01\0\0\0', 1)
    def test_partial_reference(self):
        self.reject(b'\x10\x06\0\0\x40A\x20', 6)
    def test_reference_before_output(self):
        self.reject(b'\x10\x03\0\0\x80\0\0', 3)
    def test_reference_distance_outside_output(self):
        self.reject(b'\x10\x04\0\0\x40A\0\1', 4)
    def test_reference_output_overrun(self):
        self.reject(b'\x10\x02\0\0\x40A\0\0', 2)
    def test_source_bounds(self):
        for src in (-4, 2**32-4, 0x1001, True):
            with self.subTest(src=src), self.assertRaises(ValueError):
                m.lz10(Memory(b''), src, 0x2000, 8, 3)
    def test_destination_bounds(self):
        for dst in (-4, 2**32, 0x2001, False):
            with self.subTest(dst=dst), self.assertRaises(ValueError):
                m.lz10(Memory(b''), 0x1000, dst, 8, 3)
    def test_source_destination_alias(self):
        for dst in (0x1000, 0x1004):
            with self.subTest(dst=dst), self.assertRaises(ValueError):
                m.lz10(Memory(b''), 0x1000, dst, 8, 3)
    def test_invalid_extent_types(self):
        for packed, decoded in ((True, 1), (8, True), (3, 1), (16385, 1), (8, 8193)):
            with self.subTest(packed=packed, decoded=decoded), self.assertRaises(ValueError):
                m.lz10(Memory(b''), 0x1000, 0x2000, packed, decoded)
    def test_unbound_memory(self):
        with self.assertRaises(ValueError):
            m.lz10(Memory(b''), 0x1000, 0x2000, 8, 3)
    def test_write_frame(self):
        with self.assertRaises(ValueError):
            m.lz10(Memory(b'\x10\x03\0\0\0ABC', extent=2), 0x1000, 0x2000, 8, 3)
    def test_valid_layout_read_only(self):
        value=layout(); before=copy.deepcopy(value)
        self.assertEqual(m.validate_layout(value), before)
        self.assertEqual(value, before)
    def test_layout_missing_or_extra(self):
        for key in m.LAYOUT_FIELDS:
            value=layout();del value[key]
            with self.subTest(key=key), self.assertRaises(ValueError):m.validate_layout(value)
        value=layout();value['extra']=0
        with self.assertRaises(ValueError):m.validate_layout(value)
    def test_layout_type_and_size(self):
        for key in m.LAYOUT_FIELDS:
            value=layout();value[key]=True
            with self.subTest(key=key), self.assertRaises(ValueError):m.validate_layout(value)
        for size in (-1,0,0x8001):
            value=layout();value['object_size']=size
            with self.subTest(size=size), self.assertRaises(ValueError):m.validate_layout(value)
    def test_layout_outside_object(self):
        for key in m.WIDTHS:
            for offset in (-1,8192):
                value=layout();value[key]=offset
                with self.subTest(key=key,offset=offset), self.assertRaises(ValueError):m.validate_layout(value)
    def test_layout_alias(self):
        value=layout();value['wallpaperLoadBoxId']=value['wallpaperOffset']
        with self.assertRaises(ValueError):m.validate_layout(value)
    def test_layout_u16_alignment(self):
        value=layout();value['wallpaperTilemap']=5;value['wallpaperBgTilemapBuffer']=726
        with self.assertRaises(ValueError):m.validate_layout(value)
    def test_finite_options(self):
        for allocated in (False,True):
            for offset in (0,1):m.validate_options(allocated,offset)
    def test_invalid_options(self):
        for a,o in ((0,0),(1,0),(None,0),(True,-1),(True,2),(True,True),(False,'0')):
            with self.subTest(a=a,o=o), self.assertRaises(ValueError):m.validate_options(a,o)
    def test_identity_type_and_canonical(self):
        self.assertEqual(m.identity(b'abc')['sha256'], hashlib.sha256(b'abc').hexdigest())
        for v in ('abc',bytearray(b'abc'),None):
            with self.assertRaises(ValueError):m.identity(v)
        self.assertEqual(m.encode({'b':2,'a':1}),m.encode({'a':1,'b':2}))
        with self.assertRaises(ValueError):m.encode({'bad':float('nan')})
    def test_claims_do_not_grant_acceptance(self):
        for key in ('actual_runtime_execution_observed','actual_bios_cpu_executed',
                    'heap_free_proven','formal_classification_accepted','donor_eligible',
                    'formal_rom_changed','formal_save_changed'):
            self.assertIs(m.CLAIMS[key], False)
        for key in ('donor_safe_bytes','native_processes','accepted_test_reruns','accepted_reader_replays'):
            self.assertEqual(m.CLAIMS[key],0)
    def test_symbol_identity_and_missing(self):
        with self.assertRaises(ValueError):m.symbols(b'', {'size':1,'sha256':'0'*64})
        with self.assertRaises(ValueError):m.symbols(b'', m.identity(b''))


if __name__=='__main__':unittest.main()
