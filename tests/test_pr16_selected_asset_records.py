"""整列2候補のrecord形/連続pointer窓に対する新規境界試験。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_asset_records as m

B=m.BASE


def blank(size=4096):
    return bytearray(size)


def put(raw,offset,*values):
    struct.pack_into('<'+'I'*len(values),raw,offset,*values)


class PointerRunTests(unittest.TestCase):
    def test_single(self):
        raw=blank();put(raw,128,B+512)
        row=m.pointer_run(raw,B+128)
        self.assertEqual((row['start'],row['end_exclusive'],row['origin_index']),(B+128,B+132,0))
        self.assertFalse(row['actual_table_extent_proven'])
    def test_both_directions(self):
        raw=blank();put(raw,120,B+500,B+504,B+508,B+512)
        row=m.pointer_run(raw,B+128)
        self.assertEqual((row['start'],row['end_exclusive'],row['origin_index']),(B+120,B+136,2))
    def test_low_window_flag(self):
        raw=blank();put(raw,124,B+500,B+504)
        self.assertTrue(m.pointer_run(raw,B+128,4)['lower_window_exhausted'])
    def test_high_window_flag(self):
        raw=blank();put(raw,128,B+500,B+504)
        self.assertTrue(m.pointer_run(raw,B+128,4)['upper_window_exhausted'])
    def test_input_boundary(self):
        raw=struct.pack('<II',B+512,B+516)
        row=m.pointer_run(raw,B)
        self.assertTrue(row['lower_window_exhausted']);self.assertTrue(row['upper_window_exhausted'])
    def test_unaligned_refused(self):
        with self.assertRaises(ValueError):m.pointer_run(blank(),B+1)
    def test_nonpointer_origin_refused(self):
        with self.assertRaises(ValueError):m.pointer_run(blank(),B+128)
    def test_window_limit_refused(self):
        with self.assertRaises(ValueError):m.pointer_run(blank(),B+128,1028)
    def test_mirror_canonical(self):
        raw=blank();put(raw,128,B+0x04000000+512)
        self.assertEqual(m.pointer_run(raw,B+128)['words'][0]['canonical_target'],B+512)
    def test_neighborhood_only_pointer_words(self):
        raw=blank();put(raw,128,B+512,6,0x0E000000,B+0x02000000+516)
        row=m.pointer_neighborhood(raw,B+128,16)
        self.assertEqual([r['address'] for r in row['pointer_words']],[B+128,B+140])


class RecordTests(unittest.TestCase):
    def tileset(self):
        raw=blank();struct.pack_into('<BBHIIIII',raw,128,1,0,0,B+512,B+1024,B+1280,0,B+1536)
        return raw
    def test_arm_tileset_offsets(self):
        rows=[r for r in m.record_shapes(self.tileset(),B+132) if r['kind']=='TILESET_DESCRIPTOR_SHAPE']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['pointer_field'],'tiles')
        self.assertEqual(rows[0]['descriptor']['attributes'],B+1536)
        self.assertFalse(rows[0]['actual_reader_proven'])
    def test_attributes_not_callback(self):
        rows=[r for r in m.record_shapes(self.tileset(),B+148) if r['kind']=='TILESET_DESCRIPTOR_SHAPE']
        self.assertEqual(rows[0]['pointer_field'],'attributes')
    def test_invalid_flag_rejected(self):
        raw=self.tileset();raw[128]=255
        self.assertFalse(any(r['kind']=='TILESET_DESCRIPTOR_SHAPE' for r in m.record_shapes(raw,B+132)))
    def test_invalid_data_pointer_rejected(self):
        raw=self.tileset();put(raw,140,0)
        self.assertFalse(any(r['kind']=='TILESET_DESCRIPTOR_SHAPE' for r in m.record_shapes(raw,B+132)))
    def test_callback_not_data(self):
        raw=self.tileset();put(raw,144,B+0x101)
        row=next(r for r in m.record_shapes(raw,B+132) if r['kind']=='TILESET_DESCRIPTOR_SHAPE')
        self.assertEqual(row['descriptor']['callback'],B+0x101)
    def test_sprite_extent_exact_end(self):
        raw=blank();struct.pack_into('<IHH',raw,128,B+512,64,33)
        row=next(r for r in m.record_shapes(raw,B+128,B+572) if r['kind']=='SPRITE_SHEET_SHAPE')
        self.assertTrue(row['hit_inside_declared_extent']);self.assertEqual(row['tag'],33)
    def test_sprite_partial_fourbyte_rejected(self):
        raw=blank();struct.pack_into('<IHH',raw,128,B+512,64,33)
        row=next(r for r in m.record_shapes(raw,B+128,B+573) if r['kind']=='SPRITE_SHEET_SHAPE')
        self.assertFalse(row['hit_inside_declared_extent'])
    def test_non_tile_size_rejected(self):
        raw=blank();struct.pack_into('<IHH',raw,128,B+512,63,33)
        self.assertFalse(any(r['kind']=='SPRITE_SHEET_SHAPE' for r in m.record_shapes(raw,B+128)))
    def test_wave_extent(self):
        raw=blank();put(raw,128,B+512);struct.pack_into('<HHIII',raw,512,0,0x4000,22050<<10,0,128)
        row=next(r for r in m.record_shapes(raw,B+128,B+640) if r['kind']=='WAVE_DATA_SHAPE')
        self.assertTrue(row['hit_inside_samples']);self.assertEqual(row['sample_count'],128)
    def test_wave_loop_bound_rejected(self):
        raw=blank();put(raw,128,B+512);struct.pack_into('<HHIII',raw,512,0,0x4000,22050<<10,129,128)
        self.assertFalse(any(r['kind']=='WAVE_DATA_SHAPE' for r in m.record_shapes(raw,B+128)))
    def test_shape_read_only(self):
        raw=self.tileset();before=bytes(raw)
        self.assertEqual(m.record_shapes(raw,B+132),m.record_shapes(raw,B+132));self.assertEqual(bytes(raw),before)
    def test_bad_candidate_refused(self):
        with self.assertRaises(ValueError):m.measure(b'1234',b'',{})


if __name__=='__main__':unittest.main()
