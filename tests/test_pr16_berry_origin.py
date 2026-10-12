"""人工byteだけで境界と過剰主張の拒否を確認。私有ROM/旧受入を再走しない。"""
import copy
import json
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_berry_origin as m


class BerryOriginTests(unittest.TestCase):
    def test_section_exact_end(self):
        self.assertEqual(m.section(b'abcdef', 100, 104, 2), b'ef')

    def test_section_negative_zero_overflow_and_bool(self):
        for args in [(100,99,1),(100,100,0),(100,105,2),(100,100,-1),(100,True,1),(100,100,True)]:
            with self.subTest(args=args), self.assertRaises(ValueError): m.section(b'abcdef',*args)

    def test_comparison_identity_and_no_consumer(self):
        raw=bytes(range(64));v=m.compare_regions(raw,raw,20)
        self.assertTrue(v['whole_asset_equal']);self.assertEqual(v['equal_prefix_bytes'],64)
        self.assertEqual(v['equal_suffix_bytes'],0);self.assertFalse(v['actual_consumer_proven'])

    def test_different_sizes_never_equated(self):
        v=m.compare_regions(bytes(range(64)),bytes(range(65)),20)
        self.assertFalse(v['same_size']);self.assertFalse(v['whole_asset_equal'])

    def test_locale_mismatch_and_unique_context(self):
        raw=bytes(range(64));other=b'zz'+raw+b'zzz'
        v=m.compare_regions(raw,other,20)
        self.assertEqual(v['public_exact_context_offsets'],[14])
        self.assertFalse(v['context_match_is_owner_proof'])

    def test_duplicate_context_retained(self):
        raw=bytes(range(64));v=m.compare_regions(raw,raw+raw,20)
        self.assertEqual(v['public_exact_context_offsets'],[12,76])

    def test_no_context_match(self):
        self.assertEqual(m.compare_regions(bytes(range(64)),b'X'*64,20)['public_exact_context_offsets'],[])

    def test_prefix_suffix_nonoverlap(self):
        raw=bytes(range(64));other=raw[:30]+b'X'+raw[31:]
        v=m.compare_regions(raw,other,20)
        self.assertEqual((v['equal_prefix_bytes'],v['equal_suffix_bytes']),(30,33))
        self.assertEqual(v['equal_bytes_at_same_offsets'],63)

    def test_compare_fails_closed_on_ranges(self):
        for raw,ref,hit in [(b'x'*15,b'x'*32,8),(b'x'*32,b'x'*15,8),(b'x'*32,b'x'*32,7),(b'x'*32,b'x'*32,21),(b'x'*32,b'x'*32,True)]:
            with self.subTest(hit=hit),self.assertRaises(ValueError):m.compare_regions(raw,ref,hit)

    def test_arm_header_branch(self):
        raw=struct.pack('<I',0xEA00002E)+b'\0'*252
        v=m.arm_header(raw);self.assertEqual(v['relative_entry_if_arm'],192)
        self.assertTrue(v['entry_inside_region']);self.assertFalse(v['runtime_mapping_proven'])

    def test_arm_negative_and_outside(self):
        raw=struct.pack('<I',0xEAFFFFFC)+b'\0'*252
        v=m.arm_header(raw);self.assertEqual(v['relative_entry_if_arm'],-8);self.assertFalse(v['entry_inside_region'])

    def test_arm_nonbranch_and_truncation(self):
        self.assertFalse(m.arm_header(b'\0'*192)['unconditional_arm_branch_shape'])
        with self.assertRaises(ValueError):m.arm_header(b'\0'*191)

    def test_thumb_bl_positive_and_hit_split(self):
        raw=b'\0'*4+struct.pack('<HH',0xF000,0xF802)+b'\0'*8
        v=m.thumb_shapes(raw,0x1000,0x1005)
        self.assertEqual(len(v),1);self.assertEqual(v[0]['hit_overlap_size'],3)
        self.assertEqual(v[0]['conditional_target_if_executed_at_rom_address'],0x100C)
        self.assertFalse(v[0]['actual_instruction_fetch_proven'])

    def test_thumb_bl_negative(self):
        raw=struct.pack('<HH',0xF7FF,0xFFFE)+b'\0'*4
        v=m.thumb_shapes(raw,0x1000,0x1001)
        self.assertEqual(v[0]['conditional_target_if_executed_at_rom_address'],0x1000)

    def test_thumb_bad_prefix_suffix_and_truncated(self):
        for hi,lo in [(0xE000,0xF800),(0xF000,0xE800),(0xF800,0xF000)]:
            self.assertEqual(m.thumb_shapes(struct.pack('<HH',hi,lo)+b'\0'*4,0x1000,0x1001),[])
        self.assertEqual(m.thumb_shapes(b'\0'*4,0x1000,0x1000),[])
        with self.assertRaises(ValueError):m.thumb_shapes(b'\0'*8,0x1001,0x1001)

    def test_literal_only_aligned_and_bounded(self):
        raw=struct.pack('<IIII',1,2,1,3)
        rows=m.literal_occurrences(raw,0x1000,{'first':1,'alias':1})
        self.assertEqual([v['address'] for v in rows],[0x1000,0x1008])
        self.assertEqual(rows[0]['value_labels'],['alias','first'])
        self.assertFalse(rows[0]['actual_ldr_consumer_proven'])
        for base,values in [(0x1001,{'x':1}),(0x1000,{'x':True}),(0x1000,{'x':2**32})]:
            with self.assertRaises(ValueError):m.literal_occurrences(raw,base,values)

    def test_symbols_only_required_unique(self):
        def row(addr,name):return '\t'.join(['x',addr,'x','x',name,'x','x','x'])
        raw='\n'.join([row('08001001','wanted'),row('08001010','local'),row('08001020','local')]).encode()
        v=m.parse_symbols(raw,{'wanted','missing'})
        self.assertEqual(v['missing'],['missing']);self.assertEqual(v['found']['wanted']['following_distinct_address'],0x08001010)
        with self.assertRaises(ValueError):m.parse_symbols(raw+b'\n'+row('08001030','wanted').encode(),{'wanted'})

    def test_symbols_bad_rows_and_nonrom_ignored(self):
        v=m.parse_symbols(b'bad\nx\t02000000\tx\tx\twanted\tx\tx\tx',{'wanted'})
        self.assertEqual(v,{'found':{},'missing':['wanted']})

    def test_deterministic_read_only_projection(self):
        raw=bytes(range(64));a=m.compare_regions(raw,raw,20);before=copy.deepcopy(a)
        self.assertEqual(m.encode(a),m.encode(json.loads(m.encode(a))))
        self.assertEqual(a,before);self.assertEqual(raw,bytes(range(64)))

    def test_exact_candidate_required(self):
        with self.assertRaises(ValueError):m.bind_hit(b'\0'*256)


if __name__ == '__main__':unittest.main()
