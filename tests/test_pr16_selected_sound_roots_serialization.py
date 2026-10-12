"""保存境界の修正に直結する試験。前回32試験やROM測定は再走しない。"""
import json
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_sound_roots as m

class SoundSerializationTests(unittest.TestCase):
    def make(self, kind=0x40, matched=True):
        raw=bytearray(65536); bank=m.BASE+0x1000;child=m.BASE+0x2000;wave=m.BASE+0x3000
        struct.pack_into('<BBBBII',raw,0x1000,kind,0,0,0,child,m.BASE+0x4000)
        struct.pack_into('<BBBBI4B',raw,0x2000,0,60,0,0,wave,255,0,255,0)
        struct.pack_into('<HHIII',raw,0x3000,0,0,22579200,0,64)
        target=wave+(20 if matched else 100)
        proof=m.inspect_banks(raw,[dict(base=bank,indices=[0])],targets=(target,))
        return proof
    def test_split_roundtrip(self):
        p=self.make();self.assertEqual(json.loads(m.encode(p)),p)
    def test_rhythm_roundtrip(self):
        p=self.make(0x80);self.assertEqual(json.loads(m.encode(p)),p)
    def test_zero_match_roundtrip(self):
        p=self.make(matched=False);self.assertEqual(p['matches'],[]);self.assertEqual(json.loads(m.encode(p)),p)
    def test_nested_indices_are_lists(self):
        p=self.make();self.assertIsInstance(p['banks'][1]['root']['indices'],list)
    def test_matched_root_is_lossless(self):
        p=self.make();self.assertEqual(len(p['matches']),1)
        self.assertEqual(json.loads(m.encode(p))['matches'][0]['root'],p['matches'][0]['root'])
    def test_no_reader_promotion(self):
        p=json.loads(m.encode(self.make()));self.assertFalse(p['actual_reader_proven'])
        self.assertFalse(p['matches'][0]['actual_reader_proven']);self.assertFalse(p['global_sound_owner_absence_proven'])

if __name__=='__main__':unittest.main()
