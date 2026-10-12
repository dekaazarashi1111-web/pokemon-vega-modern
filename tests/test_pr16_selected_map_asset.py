"""後継Tileset ABIと有限lookupに対する人工境界試験。旧測定は再走しない。"""
import copy
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_map_asset as m


class SelectedMapAssetTests(unittest.TestCase):
    def setUp(self):
        self.raw = bytearray(8192)
        self.ts = m.BASE+0x480
        self.lo = m.BASE+0x400
        self.root = m.BASE+0x40
        self.bank = m.BASE+0x100
        self.header = m.BASE+0x300
        struct.pack_into('<I',self.raw,0x40,self.bank)
        struct.pack_into('<I',self.raw,0x100,self.header)
        struct.pack_into('<I',self.raw,0x300,self.lo)
        struct.pack_into('<ii4I2B',self.raw,0x400,2,3,m.BASE+0x580,m.BASE+0x600,self.ts,self.ts,2,2)
        struct.pack_into('<BB2x5I',self.raw,0x480,0,1,m.BASE+0x700,m.BASE+0x740,m.BASE+0x780,0,m.BASE+0x800)
        struct.pack_into('<6H',self.raw,0,0x0080,0x0089,0x4A02,0x5810,0x5840,0x4770)
        struct.pack_into('<I',self.raw,16,self.root)
        self.symbol=dict(address=m.BASE,following_distinct_address=m.BASE+20)

    def row(self):
        return m.tileset(self.raw,self.ts,m.LAYOUT)

    def test_correct_callback_offset(self):
        self.assertEqual(self.row()['callback'],0)

    def test_correct_attributes_offset(self):
        self.assertEqual(self.row()['attributes'],m.BASE+0x800)

    def test_null_callback_not_data_error(self):
        self.assertEqual(self.row()['invalid_data_fields'],[])

    def test_thumb_callback_not_data_error(self):
        struct.pack_into('<I',self.raw,0x490,m.BASE+1)
        self.assertEqual(self.row()['invalid_data_fields'],[])
        self.assertEqual(self.row()['callback'],m.BASE+1)

    def test_bad_attribute_not_hidden_by_callback(self):
        struct.pack_into('<II',self.raw,0x490,m.BASE+0x800,0)
        self.assertEqual(self.row()['invalid_data_fields'],['attributes'])

    def test_palette_allows_half_alignment(self):
        struct.pack_into('<I',self.raw,0x488,m.BASE+0x742)
        self.assertEqual(self.row()['invalid_data_fields'],[])

    def test_attribute_requires_word_alignment(self):
        struct.pack_into('<I',self.raw,0x494,m.BASE+0x802)
        self.assertEqual(self.row()['invalid_data_fields'],['attributes'])

    def test_nonboolean_secondary_preserved(self):
        self.raw[0x481]=2
        self.assertEqual(self.row()['palette_mode'],'compressed')
        self.assertEqual(self.row()['secondary_byte'],2)

    def test_nonzero_compressed_semantics(self):
        self.raw[0x480]=255
        self.assertTrue(self.row()['compressed'])

    def test_layout_swapped_fields_rejected(self):
        layout=dict(m.LAYOUT,callback=20,attributes=16)
        with self.assertRaises(ValueError):m.checked_layout(layout)

    def test_layout_boolean_integer_rejected(self):
        layout=dict(m.LAYOUT,secondary=True)
        with self.assertRaises(ValueError):m.checked_layout(layout)

    def test_layout_missing_key_rejected(self):
        layout=dict(m.LAYOUT);del layout['map']
        with self.assertRaises(ValueError):m.checked_layout(layout)

    def test_section_end_boundary(self):
        self.assertEqual(m.section(self.raw,m.BASE+len(self.raw)-1,1),b'\0')
        with self.assertRaises(ValueError):m.section(self.raw,m.BASE+len(self.raw),1)

    def test_section_negative_zero_rejected(self):
        for n in (-1,0):
            with self.assertRaises(ValueError):m.section(self.raw,m.BASE,n)

    def test_section_boolean_address_rejected(self):
        with self.assertRaises(ValueError):m.section(self.raw,True,1)

    def test_descriptor_truncated_rejected(self):
        with self.assertRaises(ValueError):m.tileset(self.raw,m.BASE+len(self.raw)-4,m.LAYOUT)

    def test_distance_not_extent(self):
        rows=m.distances(self.row(),m.BASE+0x800)
        self.assertEqual(len(rows),4)
        self.assertTrue(all(not r['extent_proven'] for r in rows))

    def test_distance_excludes_invalid_field(self):
        row=self.row();row['invalid_data_fields']=['tiles']
        self.assertNotIn('tiles',[r['field'] for r in m.distances(row,m.BASE+0x800)])

    def test_distance_radius_exclusive(self):
        row=self.row();row.update(tiles=m.BASE,invalid_data_fields=['palettes','metatiles','attributes'])
        self.assertEqual(m.distances(row,m.BASE+128,128),[])

    def test_map_geometry(self):
        self.assertEqual(m.map_layout(self.raw,self.lo)['width'],2)
        self.assertEqual(m.map_layout(self.raw,self.lo)['height'],3)

    def test_map_dimension_zero_rejected(self):
        struct.pack_into('<i',self.raw,0x400,0)
        with self.assertRaises(ValueError):m.map_layout(self.raw,self.lo)

    def test_map_dimension_limit_rejected(self):
        struct.pack_into('<i',self.raw,0x400,257)
        with self.assertRaises(ValueError):m.map_layout(self.raw,self.lo)

    def test_map_extent_truncated_rejected(self):
        struct.pack_into('<I',self.raw,0x40C,m.BASE+len(self.raw)-2)
        with self.assertRaises(ValueError):m.map_layout(self.raw,self.lo)

    def test_contains_all_four_bytes(self):
        self.assertTrue(m.contains(100,4,100))
        self.assertFalse(m.contains(100,4,101))
        self.assertFalse(m.contains(100,4,99))

    def test_contains_overflow_rejected(self):
        with self.assertRaises(ValueError):m.contains(2**32-1,2,2**32-1)

    def test_lookup_executes_actual_fixture_instructions(self):
        p=m.lookup_profile(self.raw,self.symbol,0,0)
        self.assertEqual(p['result'],self.header)
        self.assertEqual(p['instruction_count'],6)
        self.assertFalse(p['natural_map_validity_proven'])
        self.assertEqual(m.root_from_profile(self.raw,p)['root'],self.root)

    def test_lookup_second_index(self):
        struct.pack_into('<I',self.raw,0x104,self.header+28)
        self.assertEqual(m.lookup_profile(self.raw,self.symbol,0,1)['result'],self.header+28)

    def test_lookup_rejects_unknown_opcode(self):
        struct.pack_into('<H',self.raw,0,0xDF11)
        with self.assertRaises(ValueError):m.lookup_profile(self.raw,self.symbol,0,0)

    def test_lookup_rejects_out_of_bounds_input(self):
        for g,n in ((256,0),(0,-1),(True,0)):
            with self.assertRaises(ValueError):m.lookup_profile(self.raw,self.symbol,g,n)

    def test_root_requires_actual_reads(self):
        p=m.lookup_profile(self.raw,self.symbol,0,0)
        p['data_reads']=[r for r in p['data_reads'] if r['address']!=self.root]
        with self.assertRaises(ValueError):m.root_from_profile(self.raw,p)

    def test_probe_map_hit_and_limits(self):
        p=m.probe_maps(self.raw,self.root,m.BASE+0x604,1,1)
        self.assertEqual(p['unique_headers'],1)
        self.assertTrue(p['matches'][0]['target_in_map'])
        self.assertFalse(p['actual_asset_reader_proven'])
        self.assertFalse(p['whole_map_inventory_claimed'])
        self.assertEqual(p['donor_safe_bytes'],0)
        with self.assertRaises(ValueError):m.probe_maps(self.raw,self.root,groups=129)

    def test_probe_read_only_and_deterministic(self):
        before=bytes(self.raw)
        one=m.encode(m.probe_maps(self.raw,self.root,m.BASE+0x604,1,1))
        two=m.encode(m.probe_maps(self.raw,self.root,m.BASE+0x604,1,1))
        self.assertEqual(one,two)
        self.assertEqual(bytes(self.raw),before)


if __name__=='__main__':unittest.main()
