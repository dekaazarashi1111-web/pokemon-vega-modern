"""重複headerを実行対象に混ぜない。旧19unitは再実行しない。"""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_special_wild_header_binding as h


class HeaderBinding(unittest.TestCase):
    def source(self,pairs):
        rom=bytearray(0x90000)
        rows=[{'region':'TOHOKU','research_key':str(m),'fields':[3,m,41,2,5,2,5,5,2,0,1]} for m in (19,27,28,63)]
        packed=b''.join(struct.pack('<BBH8B',*r['fields']) for r in rows)
        rom[0x80000:0x80000+len(packed)]=packed
        struct.pack_into('<I',rom,0x8257C,0x08001000)
        for i,pair in enumerate(pairs):
            at=0x1000+20*i;rom[at:at+2]=bytes(pair)
            struct.pack_into('<I',rom,at+16,0x08004000)
        at=0x1000+20*len(pairs);rom[at:at+2]=b'\xff\xff'
        struct.pack_into('<I',rom,0x4004,0x08005000)
        return rom,{'qol_start':0x08080000,'qol_end':0x08080100},rows
    def test_unique_intersection_with_irrelevant_duplicates(self):
        rom,a,rows=self.source([(0,0),(0,0),(3,27)])
        result=h.select_fixture(bytes(rom),a,rows)
        self.assertEqual(result['fishing']['map'],[3,27])
        self.assertEqual(result['duplicate_maps_excluded'][0]['map'],[0,0])
        self.assertEqual(result['header_count'],3)
    def test_duplicate_candidate_skipped_even_if_same_bytes(self):
        rom,a,rows=self.source([(3,27),(3,27),(3,28)])
        result=h.select_fixture(bytes(rom),a,rows)
        self.assertEqual(result['fishing']['map'],[3,28])
        self.assertEqual(result['excluded_research_headers'][0]['reason'],'DUPLICATE_MAP')
    def test_all_candidates_ambiguous_fails(self):
        rom,a,rows=self.source([(3,27),(3,27)])
        with self.assertRaisesRegex(ValueError,'unique research'):h.select_fixture(bytes(rom),a,rows)
    def test_invalid_info_or_slots_excluded_without_dereference(self):
        for pointer,where in ((0x07FFFFFF,0x1010),(0x08090000-4,0x1010),(0x08090000-39,0x4004)):
            rom,a,rows=self.source([(3,27)])
            struct.pack_into('<I',rom,where,pointer)
            with self.assertRaisesRegex(ValueError,'unique research'):h.select_fixture(bytes(rom),a,rows)
    def test_no_terminator_fails_closed(self):
        rom,a,rows=self.source([(3,27)]);rom[0x1014:0x1016]=b'\0\0'
        with self.assertRaisesRegex(ValueError,'terminated wild'):h.select_fixture(bytes(rom),a,rows)
    def test_excluded_map_does_not_win_selection(self):
        rom,a,rows=self.source([(3,19),(3,27)])
        self.assertEqual(h.select_fixture(bytes(rom),a,rows)['fishing']['map'],[3,27])
    def test_table_drift_and_duplicate_table_fail(self):
        for duplicate in (False,True):
            rom,a,rows=self.source([(3,27)])
            if duplicate:rom[0x80040:0x80070]=rom[0x80000:0x80030]
            else:rom[0x80002]^=1
            with self.assertRaisesRegex(ValueError,'exact effective'):h.select_fixture(bytes(rom),a,rows)
    def test_negative_or_outside_root_fails(self):
        for pointer in (0,0x08090000):
            rom,a,rows=self.source([(3,27)]);struct.pack_into('<I',rom,0x8257C,pointer)
            with self.assertRaisesRegex(ValueError,'bounded wild header'):h.select_fixture(bytes(rom),a,rows)


if __name__=='__main__':unittest.main()
