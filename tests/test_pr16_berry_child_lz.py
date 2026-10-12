"""新しいLZ境界とnative証拠改変への人工試験。受入済みentryは再走しない。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_berry_child_lz as m


def stream(size, tail):
    return bytes([0x10]) + size.to_bytes(3, 'little') + tail


class LzTests(unittest.TestCase):
    def test_literal(self):
        out, p = m.decode_lz(stream(4, b'\0abcd'), source=0, target=5)
        self.assertEqual(out, b'abcd'); self.assertEqual(p['target_byte_indexes'], [0, 1, 2, 3])
    def test_overlap(self):
        out, p = m.decode_lz(stream(7, b'\x40a\x30\0'), source=0, target=4)
        self.assertEqual(out, b'a' * 7); self.assertEqual(p['consumed_bytes'], 8)
        self.assertEqual([x['kind'] for x in p['target_roles']], ['flags', 'literal', 'backreference'])
    def test_header_target(self):
        self.assertEqual(m.decode_lz(stream(1, b'\0a'), source=0, target=0)[1]['target_bytes_consumed'], 4)
    def test_trailing_not_consumed(self):
        _, p = m.decode_lz(stream(1, b'\0aXYZ'), source=0, target=6)
        self.assertEqual(p['target_bytes_consumed'], 0); self.assertEqual(p['trailing_bytes'], 3)
    def test_eight_literals_next_flags(self):
        out, _ = m.decode_lz(stream(9, b'\0abcdefgh\0i'))
        self.assertEqual(out, b'abcdefghi')
    def test_bad_signature(self):
        with self.assertRaises(ValueError): m.decode_lz(b'\x11\1\0\0\0a')
    def test_short_header(self):
        with self.assertRaises(ValueError): m.decode_lz(b'\x10\0')
    def test_empty_output(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(0, b''))
    def test_output_budget(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(4, b'\0abcd'), max_output=3)
    def test_missing_flags(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(1, b''))
    def test_missing_literal(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(1, b'\0'))
    def test_missing_reference(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(3, b'\x80\0'))
    def test_reference_before_output(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(3, b'\x80\0\0'))
    def test_overrun_not_clipped(self):
        with self.assertRaises(ValueError): m.decode_lz(stream(3, b'\x40a\0\0'))
    def test_deterministic(self):
        raw = stream(7, b'\x40a\x30\0')
        self.assertEqual(m.decode_lz(raw), m.decode_lz(raw))


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.p = {'source_end_exclusive': m.STREAM + 20, 'consumed_bytes': 20,
                  'output': {'size': 50}, 'target_byte_indexes': [0, 1, 2, 3]}
        self.n = dict(schema_version=1, native_processes=1, child_header_boots=0,
            entry=m.CHILD+0x120, stop_pc=m.CHILD+0x1D8, swi11_count=1,
            sio_fixture_transactions=8, sio_fixture_reads=32, host_write_guards=7,
            host_writes_after_entry=0, target_read_mask=15, mapped_bytes=m.SIZE,
            payload_read_first=m.STREAM, payload_read_end_exclusive=m.STREAM+20,
            payload_read_bytes=20, payload_read_unique=20, payload_read_max_count=1,
            output_write_bytes=50, output_size=50, steps=123,
            status='CONDITIONAL_LZ_READER_OBSERVED', stop_reason='RETURNED_FROM_SWI11',
            natural_link_transfer_proven=False, original_bios_cpu_execution_claimed=False,
            formal_rom_changed=False, formal_save_changed=False, full_emulator_checkpoint_restored=False,
            sio_reads_are_fixture=True, all_issued_code_equal_source=True,
            all_payload_reads_equal_source=True, output_writes_sequential=True,
            issued_spans=[{'address': m.CHILD+x, 'visits': 1} for x in (0x120,0x144,0x1CC,0x1D0,0x1D4)])
    def test_valid(self): self.assertTrue(m.validate_native(self.n, self.p))
    def test_reject_counter_mutations(self):
        for key in (k for k,v in self.n.items() if type(v) is int and k != 'steps'):
            with self.subTest(key=key):
                value=copy.deepcopy(self.n);value[key]+=1
                with self.assertRaises(ValueError): m.validate_native(value, self.p)
    def test_reject_boolean_as_integer(self):
        self.n['native_processes']=True
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)
    def test_reject_claim_mutations(self):
        for key in (k for k,v in self.n.items() if type(v) is bool):
            with self.subTest(key=key):
                value=copy.deepcopy(self.n);value[key]=not value[key]
                with self.assertRaises(ValueError): m.validate_native(value, self.p)
    def test_reject_duplicate_span(self):
        self.n['issued_spans'].append(self.n['issued_spans'][0])
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)
    def test_reject_header_replay(self):
        self.n['issued_spans'][0]['address']=m.CHILD
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)
    def test_reject_missing_swi(self):
        self.n['issued_spans'].pop()
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)
    def test_reject_partial_target(self):
        self.p['target_byte_indexes']=[0,1,2]
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)
    def test_reject_unbounded(self):
        self.n['steps']=500001
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)
    def test_reject_unreturned(self):
        self.n['stop_reason']='BUDGET'
        with self.assertRaises(ValueError): m.validate_native(self.n, self.p)


if __name__ == '__main__': unittest.main()
