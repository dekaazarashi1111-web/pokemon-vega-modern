"""新PLR1読取境界の小さな合成fixture。受入済み原本/44試験は再実行しない。"""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from tools import pr16_learnset_runtime as r

ROOT = Path(__file__).resolve().parents[1]
U8P = c.POINTER(c.c_uint8)


class View(c.Structure):
    _fields_ = [('bytes', U8P), ('count', c.c_uint16), ('owner', c.c_uint16)]


def image():
    machine = 15084
    raw = bytearray(machine + 1483 * 16)
    raw[:32] = r.HEADER.pack(b'PLR1', 1, 1671, 32, 1704, 15072, machine, len(raw), 0)
    raw[32:1703] = bytes([2]) * 1671
    for sid in range(1671):
        r.ENTRY.pack_into(raw, 1704 + sid * 8, r.NONE, 0, 65535)
    raw[42] = 1
    r.ENTRY.pack_into(raw, 1784, 15072, 2, 0)
    raw[15072:15081] = struct.pack('<HBHBHB', 33, 1, 535, 9, 0, 255)
    for slot in (0, 31, 32, 63, 64, 95, 96, 127):
        raw[machine + slot // 8] |= 1 << (slot % 8)
    return raw


def library(destination):
    output = Path(destination) / 'runtime.so'
    subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    str(ROOT/'src/modernization/pr16_learnset_owner.c'),
                    str(ROOT/'src/modernization/pr16_learnset_runtime.c'), '-o', str(output)], check=True)
    dll = c.CDLL(str(output))
    dll.Pr16ReadLearnsetRuntime.argtypes = [U8P, c.c_uint32, c.c_uint16, c.c_uint8, c.POINTER(View)]
    dll.Pr16ReadLearnsetRuntime.restype = c.c_uint8
    dll.Pr16RuntimeLevelMoves.argtypes = [U8P, c.c_uint32, c.c_uint16, c.POINTER(c.c_uint16), c.c_uint16]
    dll.Pr16RuntimeLevelMoves.restype = c.c_uint8
    dll.Pr16RuntimeMachineAllowed.argtypes = [U8P, c.c_uint32, c.c_uint16, c.c_uint16]
    dll.Pr16RuntimeMachineAllowed.restype = c.c_uint8
    return dll


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.dll = library(cls.temp.name)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.raw = image()

    def call(self, sid=10, consumer=3, size=None):
        buf = (c.c_uint8 * len(self.raw)).from_buffer_copy(self.raw)
        view = View(); status = self.dll.Pr16ReadLearnsetRuntime(buf, len(buf) if size is None else size, sid, consumer, c.byref(view))
        return status, view, buf

    def invalid(self):
        status, view, _ = self.call()
        self.assertEqual(status, 0); self.assertFalse(view.bytes); self.assertEqual(view.count, 0)

    def test_explicit_level_span(self):
        status, view, buf = self.call()
        self.assertEqual((status, view.count, view.owner), (1, 2, 10))
        self.assertEqual(c.string_at(view.bytes, 6), self.raw[15072:15078])
        self.assertEqual(bytes(buf), self.raw)

    def test_machine_word_boundaries(self):
        buf = (c.c_uint8 * len(self.raw)).from_buffer_copy(self.raw)
        for slot in range(130):
            self.assertEqual(self.dll.Pr16RuntimeMachineAllowed(buf, len(buf), 10, slot),
                             slot in (0, 31, 32, 63, 64, 95, 96, 127))
        self.assertEqual(self.dll.Pr16RuntimeMachineAllowed(buf, len(buf), 10, 65535), 0)

    def test_no_partial_copy(self):
        buf = (c.c_uint8 * len(self.raw)).from_buffer_copy(self.raw)
        out = (c.c_uint16 * 4)(*([0xDEAD]*4))
        self.assertEqual(self.dll.Pr16RuntimeLevelMoves(buf, len(buf), 10, out, 1), 0)
        self.assertEqual(list(out), [0xDEAD]*4)
        self.assertEqual(self.dll.Pr16RuntimeLevelMoves(buf, len(buf), 10, out, 2), 2)
        self.assertEqual(list(out), [33, 535, 0xDEAD, 0xDEAD])

    def test_non_learning_owners_no_span(self):
        for policy in range(2, 8):
            self.raw[43] = policy
            status, view, _ = self.call(11)
            self.assertEqual(status, 2 if policy < 5 else 3)
            self.assertFalse(view.bytes); self.assertEqual(view.owner, 11)

    def test_non_learning_payload_rejected(self):
        self.raw[42] = 5; self.invalid()

    def test_no_conditional_flattening(self):
        for consumer in (0, 1, 2, 5, 6, 7, 8):
            status, view, _ = self.call(consumer=consumer)
            self.assertEqual(status, 4 if consumer in (2, 5) else 5)
            self.assertFalse(view.bytes)

    def test_species_consumer_bounds(self):
        for sid, consumer in ((1671, 3), (65535, 3), (10, 9), (10, 255)):
            self.assertEqual(self.call(sid, consumer)[0], 0)

    def test_short_header_and_nulls(self):
        for size in (0, 1, 31, len(self.raw)-1):
            self.assertEqual(self.call(size=size)[0], 0)
        self.assertEqual(self.dll.Pr16ReadLearnsetRuntime(None, 65535, 10, 3, c.byref(View())), 0)
        self.assertEqual(self.dll.Pr16ReadLearnsetRuntime(None, 0, 10, 3, None), 0)

    def test_header_offsets_and_version(self):
        original = self.raw[:]
        for offset, val in ((0, 0), (4, 2), (6, 1670), (8, 0xFFFFFFFF), (12, 0xFFFFFFFF),
                            (16, 0xFFFFFFFE), (20, 0xFFFFFFFC), (24, 0), (28, 1)):
            self.raw = original[:]
            struct.pack_into('<I' if offset >= 8 or offset == 0 else '<H', self.raw, offset, val)
            self.invalid()

    def test_level_span_wrap_and_count(self):
        for at, count in ((0, 2), (0xFFFFFFFE, 2), (15072, 65535), (15072, 41), (15082, 2)):
            self.raw = image(); r.ENTRY.pack_into(self.raw, 1784, at, count, 0); self.invalid()

    def test_machine_index_bounds(self):
        for slot in (1483, 65535):
            self.raw = image(); struct.pack_into('<H', self.raw, 1790, slot); self.invalid()

    def test_invalid_moves_and_levels(self):
        for move, lv in ((0, 1), (1063, 1), (65535, 1), (33, 0), (33, 101), (33, 255)):
            self.raw = image(); struct.pack_into('<HB', self.raw, 15072, move, lv); self.invalid()

    def test_bad_terminal(self):
        for pos in (15078, 15079, 15080):
            self.raw = image(); self.raw[pos] ^= 1; self.invalid()

    def test_empty_explicit_level_not_identity(self):
        struct.pack_into('<H', self.raw, 1788, 0); self.raw[15072:15075] = b'\0\0\xff'
        status, view, _ = self.call()
        self.assertEqual((status, view.owner, view.count), (1, 10, 0))
        self.assertTrue(view.bytes)

    def test_invalid_policy(self):
        for policy in (0, 8, 255):
            self.raw = image(); self.raw[42] = policy; self.invalid()

    def test_unaligned_image(self):
        buffer = (c.c_uint8 * (len(self.raw) + 1))()
        c.memmove(c.addressof(buffer) + 1, bytes(self.raw), len(self.raw))
        view = View(); ptr = c.cast(c.addressof(buffer) + 1, U8P)
        self.assertEqual(self.dll.Pr16ReadLearnsetRuntime(ptr, len(self.raw), 10, 3, c.byref(view)), 1)


class AllocationTests(unittest.TestCase):
    def fixture(self):
        return {'regions': [{'name':'x','kind':'allocatable','start':0,'end_exclusive':128}],
                'allocations':[{'region':'x','start':0,'end_exclusive':65}]}

    def test_alignment_and_no_reuse(self):
        self.assertEqual(r.free_span(self.fixture(), 60), (68, 'x'))

    def test_capacity_fail_closed(self):
        with self.assertRaises(ValueError): r.free_span(self.fixture(), 61)
        with self.assertRaises(ValueError): r.free_span(self.fixture(), True)

    def test_reserved_region_not_used(self):
        a = self.fixture(); a['regions'][0]['kind']='reserved'
        with self.assertRaises(ValueError): r.free_span(a, 1)


if __name__ == '__main__':
    unittest.main()
