"""Synthetic static-reader boundaries, not native P05 acceptance."""
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_p05_root_diagnostics as m
from tools.t02.rom_inventory import RomImage, ScriptRoot
BASE=0x08000000


class P05RootDiagnosticsTests(unittest.TestCase):
    def test_invalid_root_does_not_erase_valid_reachable_evidence(self):
        raw=b'\x16\x3a\x40\x03\x00\x02'
        graph=m.rooted_graph(RomImage('synthetic',raw),[ScriptRoot(BASE,'map:1:2:object:0','object'),ScriptRoot(0x110A0000,'map:12:7:object:0','object')])
        self.assertEqual(graph['root_count'],1);self.assertFalse(graph['all_roots_decoded'])
        self.assertEqual(graph['invalid_roots'],[{'address':0x110A0000,'label':'map:12:7:object:0','kind':'object'}])
        self.assertEqual(graph['references'][0]['value'],0x403A)

    def test_unknown_opcode_cannot_be_skipped_to_a_later_match(self):
        graph=m.rooted_graph(RomImage('synthetic',b'\xfe\x16\x3a\x40\x03\x00\x02'),[ScriptRoot(BASE,'map:1:2:object:0','object')])
        self.assertEqual(graph['references'],[]);self.assertFalse(graph['all_roots_decoded'])
        self.assertEqual(graph['diagnostics'][0]['kind'],'unknown_opcode')

    def test_native_pointer_is_recorded_not_reinterpreted_as_an_event(self):
        raw=b'\x23'+struct.pack('<I',BASE+6)+b'\x02\x16\x3a\x40\x03\x00\x02'
        graph=m.rooted_graph(RomImage('synthetic',raw),[ScriptRoot(BASE,'map:1:2:object:0','object')])
        self.assertEqual(len(graph['references']),1);self.assertEqual(graph['references'][0]['category'],'native')
        self.assertEqual(graph['visited_script_count'],1)

    def wild(self):
        raw=bytearray(0x82600)
        struct.pack_into('<I',raw,0x8257C,BASE+0x101)
        raw[0x100:0x102]=b'\x01\x02'
        struct.pack_into('<I',raw,0x104,BASE+0x201)
        raw[0x200]=20;struct.pack_into('<I',raw,0x204,BASE+0x301)
        for i in range(12):struct.pack_into('<BBH',raw,0x300+4*i,10,10,503)
        return raw

    def test_tagged_pointer_levels_and_exact_species_are_preserved(self):
        report=m.wild_catalogue(bytes(self.wild()),count=1)
        self.assertEqual(report['root'],BASE+0x100);self.assertTrue(report['complete_valid_catalogue'])
        self.assertEqual(len(report['target_candidates']),12)
        self.assertIs(report['natural_acquisition_accepted'],False)
        self.assertEqual(report['target_candidates'][0]['species'],503)

    def test_bad_method_stays_invalid_without_erasing_valid_modes(self):
        raw=self.wild();struct.pack_into('<I',raw,0x108,0x110A0000)
        report=m.wild_catalogue(bytes(raw),count=1)
        self.assertFalse(report['complete_valid_catalogue']);self.assertEqual(len(report['target_candidates']),12)
        self.assertEqual(report['diagnostics'][0]['method'],'water')
        self.assertEqual(report['headers'][0]['tables']['water']['status'],'INVALID')

    def test_unknown_or_zero_slot_is_not_a_target_candidate(self):
        for field,value in ((0,0),(1,101)):
            raw=self.wild();raw[0x300+field]=value
            report=m.wild_catalogue(bytes(raw),count=1)
            self.assertFalse(report['complete_valid_catalogue']);self.assertEqual(report['target_candidates'],[])
        raw=self.wild();struct.pack_into('<H',raw,0x302,0)
        self.assertEqual(m.wild_catalogue(bytes(raw),count=1)['target_candidates'],[])

    def test_duplicate_coordinate_cannot_look_like_a_second_accessible_owner(self):
        raw=self.wild();raw[0x114:0x128]=raw[0x100:0x114]
        report=m.wild_catalogue(bytes(raw),count=2)
        self.assertTrue(report['headers'][0]['first_coordinate_owner'])
        self.assertFalse(report['headers'][1]['first_coordinate_owner'])
        self.assertTrue(all(not row['first_coordinate_owner'] for row in report['target_candidates'][12:]))

    def test_out_of_range_header_and_slots_are_explicit(self):
        raw=self.wild();struct.pack_into('<I',raw,0x8257C,BASE+len(raw)-8)
        report=m.wild_catalogue(bytes(raw),count=1)
        self.assertEqual(report['inspected_headers'],0);self.assertFalse(report['complete_valid_catalogue'])
        raw=self.wild();struct.pack_into('<I',raw,0x204,0x110A0000)
        report=m.wild_catalogue(bytes(raw),count=1)
        self.assertEqual(report['diagnostics'][0]['error'],'slots pointer outside ROM')

if __name__=='__main__':unittest.main()
