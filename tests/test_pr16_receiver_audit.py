"""Synthetic decoder boundaries, not a physical facility acceptance result."""
import struct
import sys
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_receiver_audit as audit
from tools.t02.rom_inventory import RomImage, ScriptRoot
BASE = 0x08000000


class ReceiverAuditTests(unittest.TestCase):
    def graph(self, raw):
        walker = audit.ReceiverWalker(RomImage('synthetic', raw))
        walker.add_root(ScriptRoot(BASE, 'map:1:2:object:0', 'object'))
        return walker.walk()

    def test_unrooted_bytes_do_not_establish_a_receiver(self):
        graph = self.graph(b'\x02\x16\x3a\x40\x03\x00\x25\x72\x00\x02')
        self.assertEqual(graph['references'], [])
        self.assertEqual(graph['diagnostics'], [])

    def test_reachable_facility_variable_preserves_operand_and_map_origin(self):
        graph = self.graph(b'\x16\x3a\x40\x03\x00\x02')
        self.assertEqual(len(graph['references']), 1)
        ref = graph['references'][0]
        self.assertEqual((ref['category'], ref['value'], ref['operand']), ('var', 0x403A, 3))
        self.assertEqual(ref['roots'], ['map:1:2:object:0'])

    def test_unknown_opcode_stops_without_resynchronization(self):
        graph = self.graph(b'\xfe\x16\x3a\x40\x03\x00\x02')
        self.assertEqual(graph['references'], [])
        self.assertEqual(graph['diagnostics'][0]['kind'], 'unknown_opcode')

    def test_truncated_native_pointer_is_not_a_match(self):
        graph = self.graph(b'\x23\x01')
        self.assertEqual(graph['references'], [])
        self.assertEqual(graph['diagnostics'][0]['kind'], 'invalid_instruction')

    def test_native_pointer_is_recorded_without_following_machine_code_as_script(self):
        target = BASE + 6
        graph = self.graph(b'\x23' + struct.pack('<I', target) + b'\x02\x16\x3a\x40\x03\x00\x02')
        self.assertEqual(len(graph['references']), 1)
        self.assertEqual((graph['references'][0]['category'], graph['references'][0]['value']), ('native', target))
        self.assertEqual(graph['visited_script_count'], 1)

    def test_gotonative_is_a_terminal_edge(self):
        graph = self.graph(b'\x24' + struct.pack('<I', BASE+5) + b'\x16\x3a\x40\x03\x00\x02')
        self.assertEqual(len(graph['references']), 1)
        self.assertEqual(graph['nodes'][0]['end_reason'], 'opcode_24')

    def test_script_call_carries_root_to_child(self):
        graph = self.graph(b'\x04' + struct.pack('<I', BASE+6) + b'\x02\x25\x72\x00\x03')
        ref = graph['references'][0]
        self.assertEqual((ref['category'], ref['value']), ('special', 0x72))
        self.assertEqual(ref['roots'], ['map:1:2:object:0'])

    def test_wild_reader_requires_a_rooted_terminator(self):
        raw = bytearray(0x82600)
        struct.pack_into('<I', raw, 0x8257C, BASE+0x100)
        raw[0x100:0x102] = b'\xff\xff'
        self.assertEqual(audit.wild(bytes(raw)), {'root': BASE+0x100, 'headers': []})
        raw[0x100:0x102] = b'\x01\x01'
        # A nonterminated all-zero tail cannot silently become a completed scan.
        with self.assertRaises(ValueError):
            audit.wild(bytes(raw))

if __name__ == '__main__':
    unittest.main()
