#!/usr/bin/env python3
"""compiled owner限定監査のsynthetic異常系。ROM/fixture受入を代用しない。"""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ring_compiled', ROOT / 'scripts/pr16_ring_compiled_owner.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
B = r.BASE


class RingCompiledOwnerTests(unittest.TestCase):
    def graph(self, data, limit=512):
        return r.graph(data, [B], B, B + len(data), limit)

    def test_end(self):
        self.assertEqual(len(self.graph(b'\x02')), 1)

    def test_unknown_stops_without_resync(self):
        with self.assertRaisesRegex(ValueError, 'unknown opcode'):
            self.graph(b'\xf0\x02')

    def test_truncated(self):
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.graph(b'\x16\0')

    def test_branch_outside(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.graph(b'\x05' + struct.pack('<I', B + 100))

    def test_branch_inside_operand(self):
        data = b'\x06\x01' + struct.pack('<I', B + 2) + b'\x02'
        with self.assertRaisesRegex(ValueError, 'inside operand'):
            self.graph(data)

    def test_overlapping_paths(self):
        data = b'\x06\x01' + struct.pack('<I', B + 8) + b'\x16\0\x02\0\0\x02'
        with self.assertRaises(ValueError):
            self.graph(data)

    def test_finite_cycle_without_end_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no reachable end'):
            self.graph(b'\x05' + struct.pack('<I', B))

    def test_both_conditional_paths_retained(self):
        data = b'\x06\x01' + struct.pack('<I', B + 7) + b'\x02\x02'
        self.assertEqual(len(self.graph(data)), 3)

    def test_bound_is_not_silent_truncation(self):
        with self.assertRaisesRegex(ValueError, 'bound exceeded'):
            self.graph(b'\x6a\x02', limit=1)

    def test_native_even_pointer_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-Thumb'):
            self.graph(b'\x23' + struct.pack('<I', B) + b'\x02')

    def test_native_is_external_not_executed(self):
        data = b'\x23' + struct.pack('<I', B + 1) + b'\x02'
        self.assertEqual(self.graph(data)[0]['native'], B + 1)

    def test_unreviewed_standard_rejected(self):
        with self.assertRaisesRegex(ValueError, 'standard'):
            self.graph(b'\x09\x00\x02')

    def test_standard_retained(self):
        self.assertEqual(self.graph(b'\x09\x04\x02')[0]['standard_script'], 4)

    def test_text_pointer_bounds(self):
        with self.assertRaisesRegex(ValueError, 'outside ROM'):
            self.graph(b'\x0f\0' + struct.pack('<I', B + 100) + b'\x02')

    def test_schedule_with_prior_native(self):
        d, n, old = B + 1234, B + 401, B + 81
        body = b'\x16' + struct.pack('<HH', 0x8000, d & 65535) + b'\x16' + struct.pack('<HH', 0x8001, d >> 16) + b'\x23' + struct.pack('<I', n) + b'\x02'
        value = r.schedule(b'\x23' + struct.pack('<I', old) + body, B, d, n)
        self.assertEqual(value['preexisting_transition_native'], old)
        with self.assertRaisesRegex(ValueError, 'schedule byte'):
            r.schedule(body, B, d + 1, n)

    def test_schedule_without_prior_native(self):
        d, n = B + 100, B + 51
        body = b'\x16' + struct.pack('<HH', 0x8000, d & 65535) + b'\x16' + struct.pack('<HH', 0x8001, d >> 16) + b'\x23' + struct.pack('<I', n) + b'\x02'
        self.assertIsNone(r.schedule(body, B, d, n)['preexisting_transition_native'])

    def test_negative_span_and_zero_size(self):
        for address, size in ((B - 1, 1), (B, 0), (B + 2, 1)):
            with self.assertRaises(ValueError):
                r.span(b'\0', address, size)

    def test_wrong_candidate_before_decode(self):
        with self.assertRaisesRegex(ValueError, 'candidate'):
            r.audit(b'\0', {}, b'')

    def test_event_header(self):
        data = bytearray(512)
        struct.pack_into('<8s16I', data, 0, b'VEGAED37', 1, 512, 256, 32, 288, 224,
                         80, 160, 76, 63, 326, 7, 7, B + 257, B + 259, B + 261)
        self.assertEqual(r.owner_header(bytes(data))['code_size'], 32)
        data[100:108] = b'VEGAED37'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            r.owner_header(bytes(data))

    def test_header_overlap(self):
        data = bytearray(512)
        struct.pack_into('<8s16I', data, 0, b'VEGAED37', 1, 512, 256, 32, 280, 224,
                         80, 160, 76, 63, 326, 7, 7, B + 257, B + 259, B + 261)
        with self.assertRaisesRegex(ValueError, 'overlap'):
            r.owner_header(bytes(data))

    def map_fixture(self):
        data = bytearray(0x55000)
        def put(at, val): struct.pack_into('<I', data, at, val)
        put(0x54B0C, B + 0x100); put(0x100 + 97 * 4, B + 0x400)
        put(0x400 + 80 * 4, B + 0x600); put(0x608, B + 0x700)
        data[0x700] = 3; put(0x701, B + 0x800)
        b = {'group_id': '97', 'map_id': '80', 'stage37_record_address': hex(B + 0x608),
             'stage37_script_pointer_address': hex(B + 0x800)}
        return data, b

    def test_map_pointer_field_means_script(self):
        data, b = self.map_fixture()
        data[0x800] = 0x16
        self.assertEqual(r.map_transition(bytes(data), b)['transition'], B + 0x800)

    def test_map_duplicate_transition(self):
        data, b = self.map_fixture()
        data[0x705] = 3; struct.pack_into('<I', data, 0x706, B + 0x800)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            r.map_transition(bytes(data), b)

    def test_map_wrong_header(self):
        data, b = self.map_fixture(); b['stage37_record_address'] = hex(B + 0x60c)
        with self.assertRaisesRegex(ValueError, 'record owner'):
            r.map_transition(bytes(data), b)


if __name__ == '__main__':
    unittest.main()
