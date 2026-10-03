"""PLC2の新規形式/decoderだけを検証。過去のhost/native受入は再実行しない。"""
from __future__ import annotations
import ctypes
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from tools import pr16_learnset_compact as c

ROOT = Path(__file__).resolve().parents[1]


class View(ctypes.Structure):
    _fields_ = [('bytes', ctypes.POINTER(ctypes.c_uint8)),
                ('count', ctypes.c_uint16), ('owner', ctypes.c_uint16)]


def load_library(folder: Path):
    target = folder / 'compact.so'
    subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-shared', '-fPIC', '-Isrc/modernization',
                    'src/modernization/pr16_learnset_compact.c',
                    'src/modernization/pr16_learnset_owner.c', '-o', str(target)],
                   cwd=ROOT, check=True, capture_output=True)
    lib = ctypes.CDLL(str(target))
    fn = lib.Pr16ReadCompactConditional
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint32,
                   ctypes.c_uint16, ctypes.c_uint8, ctypes.POINTER(View)]
    fn.restype = ctypes.c_uint8
    return fn


def read(fn, image, species=1, consumer=0):
    buffer = (ctypes.c_uint8 * len(image)).from_buffer_copy(image)
    view = View()
    result = fn(buffer, len(image), species, consumer, ctypes.byref(view))
    length = (16 if consumer == 8 else view.count * 2) if result == 1 else 0
    raw = ctypes.string_at(view.bytes, length) if length else b''
    return result, view.owner, view.count, raw, bool(view.bytes)


def audit_library(fn, source: bytes, packed: bytes) -> dict:
    rows = c.source_rows(source)
    queries = 0
    for sid in range(c.COUNT):
        policy = source[c.POLICY + sid]
        for consumer in range(9):
            action = 1 if policy == 1 else 2 if policy < 5 else 3
            if consumer not in c.CONSUMERS:
                expected = (4 if policy == 1 and consumer in (2, 5) else 5,
                            65535, 0, b'', False)
            elif action != 1:
                expected = (action, sid, 0, b'', False)
            else:
                row = rows[sid * 5 + c.CONSUMERS.index(consumer)]
                count = struct.unpack_from('<H', row)[0] & 0x7FFF
                expected = (1, sid, count, row[2:], True)
            actual = read(fn, packed, sid, consumer)
            if actual != expected:
                raise AssertionError(f'PLC2 semantic mismatch species={sid} consumer={consumer}')
            queries += 1
    return {'status': 'PASS', 'queries': queries, 'owner_consumer_pairs': len(rows),
            'owner_order_count_payload_actions_equal': True}


def fixture():
    image = bytearray(c.OLD_DATA)
    policies = bytearray([2] * c.COUNT)
    for sid in (1, 8, 9, 1029, 1621): policies[sid] = 1
    for sid in range(2, 8): policies[sid] = sid
    image[c.POLICY:c.POLICY + c.COUNT] = policies
    for sid in range(c.COUNT):
        for col, consumer in enumerate(c.CONSUMERS):
            key = (sid << 4) | consumer
            if policies[sid] != 1:
                entry = (0xFFFFFFFF, 0, key)
            else:
                if consumer == 8:
                    raw, count = bytes([5]) + bytes(15), 64
                else:
                    values = (1, 5, 1) if consumer == 0 else (7, 42)
                    if sid == 8: values = ()
                    if sid == 9: values = tuple(range(1, 51))
                    raw, count = b''.join(struct.pack('<H', x) for x in values), len(values)
                entry = (len(image), count, key)
                image.extend(raw)
            struct.pack_into('<IHH', image, c.INDEX + (sid * 5 + col) * 8, *entry)
    c.HEADER.pack_into(image, 0, b'PLC1', 1, c.COUNT, c.POLICY, c.INDEX,
                      c.OLD_DATA, len(image), c.MASK, 0)
    return bytes(image)


class CompactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.fn = staticmethod(load_library(Path(cls.folder.name)))
        cls.source = fixture()
        cls.image, cls.receipt = c.compact(cls.source)

    @classmethod
    def tearDownClass(cls): cls.folder.cleanup()

    def changed(self, offset, value, fmt='<H'):
        image = bytearray(self.image)
        struct.pack_into(fmt, image, offset, value)
        return image

    def offset(self, column=0):
        return struct.unpack_from('<H', self.image, c.INDEX + (5 + column) * 2)[0]

    def invalid(self, image, species=1, consumer=0):
        self.assertEqual(read(self.fn, image, species, consumer), (0, 65535, 0, b'', False))

    def test_roundtrip_all_rows(self):
        self.assertEqual(c.source_rows(self.source), c.compact_rows(self.image))

    def test_deterministic_without_source_mutation(self):
        source = bytearray(self.source)
        self.assertEqual(c.compact(source), (self.image, self.receipt))
        self.assertEqual(source, self.source)

    def test_actual_c_decoder_all_owners_and_consumers(self):
        self.assertEqual(audit_library(self.fn, self.source, self.image)['queries'], 15039)

    def test_duplicate_order_not_deduplicated_inside_row(self):
        self.assertEqual(read(self.fn, self.image)[3], struct.pack('<3H', 1, 5, 1))

    def test_empty_and_fifty_rows(self):
        self.assertEqual(read(self.fn, self.image, 8)[2], 0)
        self.assertEqual(read(self.fn, self.image, 9)[2], 50)

    def test_floette_and_own_tempo_keep_their_owner(self):
        for sid in (1029, 1621): self.assertEqual(read(self.fn, self.image, sid)[1], sid)

    def test_null_arguments(self):
        v = View()
        self.assertEqual(self.fn(None, len(self.image), 1, 0, ctypes.byref(v)), 0)
        self.assertEqual(self.fn(None, 0, 1, 0, None), 0)
        self.assertEqual(v.owner, 65535)

    def test_invalid_species_consumer_policy(self):
        self.invalid(self.image, 1671)
        self.invalid(self.image, 65535)
        self.invalid(self.image, 1, 9)
        self.invalid(self.changed(c.POLICY + 1, 0, '<B'))
        self.invalid(self.changed(c.POLICY + 1, 8, '<B'))

    def test_header_fields_fail_closed(self):
        for offset, fmt in ((0,'<I'),(4,'<H'),(6,'<H'),(8,'<I'),(12,'<I'),
                            (16,'<I'),(20,'<I'),(24,'<I'),(28,'<I')):
            with self.subTest(offset=offset):
                value = struct.unpack_from(fmt, self.image, offset)[0]
                self.invalid(self.changed(offset, value ^ 1, fmt))

    def test_alignment_padding(self):
        for offset in (1703, 18414, 18415):
            self.invalid(self.changed(offset, 1, '<B'))

    def test_truncation(self):
        for size in (0, 1, 31, 1704, c.DATA - 1, len(self.image) - 1):
            self.invalid(self.image[:size])

    def test_explicit_owner_requires_span(self):
        self.invalid(self.changed(c.INDEX + 10, 65535))

    def test_preserved_owner_forbids_span(self):
        self.invalid(self.changed(c.INDEX + 20, self.offset()), 2)

    def test_offset_bounds_and_alignment(self):
        for offset in (0, c.DATA - 2, self.offset() + 1, len(self.image), 65534):
            self.invalid(self.changed(c.INDEX + 10, offset))

    def test_tutor_and_list_types_cannot_cross(self):
        self.invalid(self.changed(c.INDEX + 10, self.offset(4)))
        self.invalid(self.changed(c.INDEX + 18, self.offset()), 1, 8)

    def test_overlong_list_and_invalid_tutor_tag(self):
        self.invalid(self.changed(self.offset(), 51))
        self.invalid(self.changed(self.offset(4), 0x8041), 1, 8)

    def test_side_change_and_zero_move_rejected(self):
        for value in (0, 1063, 65535): self.invalid(self.changed(self.offset() + 2, value))

    def test_tutor_high_bits_rejected(self):
        self.invalid(self.changed(self.offset(4) + 10, 1, '<B'), 1, 8)

    def test_form_and_carry_are_not_automatic_grants(self):
        for consumer in (2, 5): self.assertEqual(read(self.fn, self.image, 1, consumer)[0], 4)

    def test_plc1_bad_owner_key_rejected(self):
        source = bytearray(self.source)
        struct.pack_into('<H', source, c.INDEX + 5 * 8 + 6, 0)
        with self.assertRaises(ValueError): c.compact(source)

    def test_plc1_bad_policy_and_header_rejected(self):
        for offset in (0, c.POLICY):
            source = bytearray(self.source); source[offset] = 0
            with self.assertRaises(ValueError): c.compact(source)

    def test_plc1_nonlearning_span_rejected(self):
        source = bytearray(self.source)
        struct.pack_into('<I', source, c.INDEX, c.OLD_DATA)
        with self.assertRaises(ValueError): c.compact(source)

    def test_plc1_bad_move_and_tutor_rejected(self):
        for column, delta, value in ((0, 0, 1063), (4, 8, 1)):
            source = bytearray(self.source)
            offset = struct.unpack_from('<I', source, c.INDEX + (5 + column) * 8)[0]
            struct.pack_into('<H', source, offset + delta, value)
            with self.assertRaises(ValueError): c.compact(source)

    def test_offline_rejects_interior_record_pointer(self):
        with self.assertRaises(ValueError): c.compact_rows(self.changed(c.INDEX + 10, self.offset() + 2))

    def test_offline_rejects_unreferenced_record(self):
        image = bytearray(self.image); image.extend(b'\0\0')
        struct.pack_into('<I', image, 20, len(image))
        with self.assertRaises(ValueError): c.compact_rows(image)


if __name__ == '__main__': unittest.main()
