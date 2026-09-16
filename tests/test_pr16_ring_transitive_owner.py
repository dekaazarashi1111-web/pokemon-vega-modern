"""Synthetic bytes only: no private ROM, native emulator, or accepted replay."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_transitive_owner as m


def image():
    return bytearray(8192)


def put(raw, offset, *halfwords):
    raw[offset:offset + 2 * len(halfwords)] = struct.pack('<' + 'H' * len(halfwords), *halfwords)


class StandardScriptTests(unittest.TestCase):
    def setUp(self):
        self.raw = image()
        self.table = m.BASE + 32
        # Odd script roots must not be normalized as Thumb entrypoints.
        self.root = m.BASE + 101
        struct.pack_into('<I', self.raw, 32 + 16, self.root)
        self.raw[101:109] = bytes.fromhex('6700000000666d03')

    def audit(self, **kw):
        return m.standard_script(bytes(self.raw), self.table, **kw)

    def test_message_wait_return(self):
        r = self.audit()
        self.assertEqual(r['target'], self.root)
        self.assertEqual([n['opcode'] for n in r['nodes']], [0x67, 0x66, 0x6D, 3])
        self.assertEqual(r['script_layer_gift_or_native_commands'], [])
        self.assertIn('ENGINE_HANDLERS_NOT_EXCLUDED', r['scope'])

    def test_unknown_not_resynchronized(self):
        self.raw[101] = 0xFE
        with self.assertRaisesRegex(ValueError, 'unreviewed'):
            self.audit()

    def test_native_command_rejected(self):
        self.raw[107] = 0x23
        with self.assertRaises(ValueError): self.audit()

    def test_jump_not_silently_followed(self):
        self.raw[107] = 5
        with self.assertRaises(ValueError): self.audit()

    def test_immediate_item_command_rejected(self):
        self.raw[107] = 0x44
        with self.assertRaises(ValueError): self.audit()

    def test_nonzero_message_pointer_rejected(self):
        self.raw[102] = 1
        with self.assertRaises(ValueError): self.audit()

    def test_missing_wait_rejected(self):
        self.raw[106] = 3
        with self.assertRaises(ValueError): self.audit()

    def test_missing_message_rejected(self):
        self.raw[101] = 3
        with self.assertRaises(ValueError): self.audit()

    def test_missing_return_hits_bound(self):
        self.raw[108:165] = b'\x6d' * 57
        with self.assertRaisesRegex(ValueError, 'bound'): self.audit(limit=10)

    def test_table_alignment(self):
        with self.assertRaises(ValueError): m.standard_script(bytes(self.raw), self.table + 1)

    def test_pointer_outside_rom(self):
        struct.pack_into('<I', self.raw, 48, m.BASE + len(self.raw))
        with self.assertRaises(ValueError): self.audit()

    def test_bad_limits(self):
        for value in (0, -1, 65, True):
            with self.subTest(value=value), self.assertRaises(ValueError): self.audit(limit=value)


class ThumbTests(unittest.TestCase):
    def graph(self, *halfwords, **kw):
        raw = image()
        put(raw, 64, *halfwords)
        return m.native_graph(bytes(raw), m.BASE + 65, **kw)

    def test_bx_lr_return(self):
        self.assertEqual(len(self.graph(0x4770)['nodes']), 1)

    def test_pop_pc_return(self):
        self.assertEqual(self.graph(0xBD10)['nodes'][0]['kind'], 'return')

    def test_direct_bl_target_and_fallthrough(self):
        r = self.graph(0xF000, 0xF810, 0x4770)
        self.assertEqual(r['external_edges'][0]['target'], m.BASE + 101)
        self.assertEqual(len(r['nodes']), 2)
        self.assertFalse(r['side_effects_excluded'])

    def test_negative_bl_displacement(self):
        raw=image();put(raw, 4096, 0xF7FF, 0xFFFE)
        self.assertEqual(m.thumb_instruction(bytes(raw), m.BASE + 4096)['target'], m.BASE + 4096)

    def test_backward_loop_is_finite(self):
        self.assertEqual(len(self.graph(0xE7FE)['nodes']), 1)

    def test_conditional_keeps_both_paths(self):
        r = self.graph(0xD000, 0x4770, 0x4770)
        self.assertEqual(len(r['nodes']), 3)

    def test_indirect_register_stays_unresolved(self):
        r = self.graph(0x4718)  # bx r3
        self.assertEqual(r['external_edges'][0]['register'], 3)
        self.assertIsNone(r['external_edges'][0]['target'])

    def test_add_pc_and_mov_pc_not_fallthrough(self):
        for half in (0x4487, 0x4687):
            r = self.graph(half)
            self.assertEqual(r['nodes'][0]['kind'], 'indirect')

    def test_literal_is_data_not_code(self):
        raw = image();put(raw, 64, 0x4800, 0x4770)
        struct.pack_into('<I', raw, 68, 0x0806DEC5)
        r = m.native_graph(bytes(raw), m.BASE + 65)
        self.assertEqual(r['nodes'][0]['literal_value'], 0x0806DEC5)
        self.assertEqual(len(r['nodes']), 2)

    def test_store_does_not_become_no_side_effect_proof(self):
        for half in (0x5000, 0x5200, 0x5400, 0x6000, 0x7000, 0x8000, 0x9000, 0xC001, 0xB401):
            r = self.graph(half, 0x4770)
            self.assertEqual(r['memory_write_sites'], [m.BASE + 64])
            self.assertFalse(r['side_effects_excluded'])

    def test_load_not_store(self):
        for half in (0x5800, 0x5A00, 0x5C00, 0x6800, 0x7800, 0x8800, 0x9800, 0xC801):
            self.assertEqual(self.graph(half, 0x4770)['memory_write_sites'], [])

    def test_unknown_and_non_arm7_encodings_rejected(self):
        for half in (0xB200, 0xBE00, 0xDE00, 0xDF00, 0x4780, 0xF800, 0xB400, 0xBC00, 0xC000, 0xC800):
            with self.subTest(half=half), self.assertRaises(ValueError): self.graph(half)

    def test_bad_bl_suffix(self):
        with self.assertRaises(ValueError): self.graph(0xF000, 0x4770)

    def test_branch_inside_bl_operand(self):
        # conditional target at +4, inside BL at +2..+5.
        with self.assertRaises(ValueError): self.graph(0xD000, 0xF000, 0xF810, 0x4770)

    def test_truncated_bl_at_window(self):
        with self.assertRaises(ValueError): self.graph(0xF000, 0xF810, window=2)

    def test_external_jump_not_scanned(self):
        r = self.graph(0xE010, window=8)
        self.assertEqual(len(r['nodes']), 1)
        self.assertEqual(r['external_edges'][0]['kind'], 'jump')

    def test_fallthrough_bound_reported_not_excluded(self):
        r = self.graph(0x2000, window=2)
        self.assertEqual(r['external_edges'][0]['kind'], 'window_fallthrough')

    def test_native_limits(self):
        with self.assertRaises(ValueError): self.graph(0x2000, 0x4770, limit=1)
        for window in (0, -1, 3, 2048, True):
            with self.subTest(window=window), self.assertRaises(ValueError): self.graph(0x4770, window=window)
        with self.assertRaises(ValueError): m.native_graph(bytes(image()), m.BASE + 64)


class BindingTests(unittest.TestCase):
    def header(self):
        fields = {k: m.BASE + 101 for k in m.MACROS}
        fields.update(EVENT_DESIGN_STATE_DAYCARE_COMPLETE=12,
                      EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR=74,
                      EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED=79)
        return ''.join(f'#define {k} {v}u\n' for k,v in fields.items()).encode()

    def test_header_exact_identity(self):
        data = self.header()
        self.assertEqual(m.header_values(data,m.identity(data))['EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED'],79)
        with self.assertRaises(ValueError): m.header_values(data+b'\n',m.identity(data))

    def test_header_duplicate_and_non_thumb_rejected(self):
        data = self.header()
        for changed in (data+data, data.replace(b'134217829u', b'134217828u')):
            with self.assertRaises(ValueError): m.header_values(changed,m.identity(changed))

    def test_stale_receipt_cannot_be_reaccepted(self):
        r = {'task':m.prior.TASK, 'classification':'COMPILED_OWNER_BOUNDARY_NOT_NATIVE_ACCEPTANCE',
             'candidate':m.prior.CANDIDATE, 'compiled_event_runtime_verified':True,
             'candidate_bytes_checked':True, 'ring_acquisition_accepted':True}
        with self.assertRaises(ValueError): m.reuse(r)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_text('x');link=Path(d)/'link';link.symlink_to(p)
            with self.assertRaises(ValueError): m.safe(link)


if __name__ == '__main__': unittest.main()
