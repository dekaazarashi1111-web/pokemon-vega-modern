"""新しい音声root/PCM宣言境界だけの人工試験。実ROM測定の再走ではない。"""
import copy
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_sound_roots as m

B=m.BASE

class SoundRootsTests(unittest.TestCase):
    def setUp(self):
        self.raw=bytearray(b'\xff'*65536)
        self.bank=B+0x1000; self.sample=B+0x3000; self.hit=self.sample+20
        self.raw[0x1000:0x1000+1536]=bytes(1536)
        struct.pack_into('<BBBBI4B',self.raw,0x1000,0,60,0,0,self.sample,255,0,255,0)
        struct.pack_into('<HHIII',self.raw,0x3000,0,0,22050*1024,0,64)
        self.raw[0x3010:0x3050]=bytes(range(64))
    def roots(self,indices=(0,)):
        return [dict(base=self.bank,indices=indices)]
    def inspect(self,**kw):
        return m.inspect_banks(self.raw,self.roots(),targets=(self.hit,),**kw)
    def test_pcm_extent(self):
        p=m.wave(self.raw,self.sample); self.assertEqual((p['data_start'],p['end_exclusive']),(self.sample+16,self.sample+80))
        self.assertFalse(p['actual_reader_proven'])
    def test_loop(self):
        struct.pack_into('<H',self.raw,0x3002,0x4000)
        struct.pack_into('<I',self.raw,0x3008,63)
        self.assertEqual(m.wave(self.raw,self.sample)['loop_start'],63)
    def test_loop_end_rejected(self):
        struct.pack_into('<I',self.raw,0x3008,64)
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample)
    def test_compressed_rejected(self):
        struct.pack_into('<H',self.raw,0x3000,1)
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample)
    def test_unknown_status(self):
        struct.pack_into('<H',self.raw,0x3002,1)
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample)
    def test_zero_frequency(self):
        struct.pack_into('<I',self.raw,0x3004,0)
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample)
    def test_zero_samples(self):
        struct.pack_into('<I',self.raw,0x300c,0)
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample)
    def test_oversize_samples(self):
        struct.pack_into('<I',self.raw,0x300c,0x200001)
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample)
    def test_truncated_sample(self):
        with self.assertRaises(ValueError): m.wave(self.raw[:0x304f],self.sample)
    def test_unaligned_header(self):
        with self.assertRaises(ValueError): m.wave(self.raw,self.sample+1)
    def test_mirror(self):
        self.assertEqual(m.wave(self.raw,self.sample+0x2000000),m.wave(self.raw,self.sample))
    def test_four_bytes_covered(self):
        p=self.inspect(); self.assertEqual(len(p['matches']),1)
        self.assertEqual(p['matches'][0]['covered_targets'],[self.hit]); self.assertFalse(p['actual_reader_proven'])
    def test_header_not_sample(self):
        p=m.inspect_banks(self.raw,self.roots(),targets=(self.sample+12,));self.assertEqual(p['matches'],[])
    def test_last_four_bytes(self):
        p=m.inspect_banks(self.raw,self.roots(),targets=(self.sample+76,));self.assertEqual(len(p['matches']),1)
    def test_partial_overlap_not_match(self):
        p=m.inspect_banks(self.raw,self.roots(),targets=(self.sample+77,));self.assertEqual(p['matches'],[])
    def test_fixed_pitch(self):
        self.raw[0x1000]=8;self.assertEqual(len(self.inspect()['matches']),1)
    def test_cgb_not_pcm(self):
        self.raw[0x1000]=3;self.assertEqual(self.inspect()['matches'],[])
    def test_compressed_not_pcm(self):
        struct.pack_into('<H',self.raw,0x3000,1);self.assertEqual(self.inspect()['matches'],[])
    def test_nested_keysplit(self):
        child=B+0x2000;keymap=B+0x4000
        self.raw[0x2000:0x200c]=self.raw[0x1000:0x100c]
        struct.pack_into('<BBBBII',self.raw,0x1000,0x40,0,0,0,child,keymap)
        self.raw[0x4000:0x4080]=bytes(128)
        p=self.inspect();self.assertEqual(len(p['matches']),1);self.assertEqual(p['counts']['banks'],2)
    def test_bad_keysplit(self):
        struct.pack_into('<BBBBII',self.raw,0x1000,0x40,0,0,0,B+0x2000,B+0x4000)
        self.raw[0x4000:0x4080]=bytes([128])*128
        self.assertEqual(self.inspect()['matches'],[])
    def test_cycle_bounded(self):
        struct.pack_into('<BBBBII',self.raw,0x1000,0x80,0,0,0,self.bank,0)
        p=self.inspect();self.assertEqual(p['counts']['banks'],2)
    def test_bank_limit_rejects_partial(self):
        struct.pack_into('<BBBBII',self.raw,0x1000,0x80,0,0,0,self.bank,0)
        with self.assertRaises(ValueError):self.inspect(max_banks=1)
    def test_invalid_index(self):
        with self.assertRaises(ValueError):m.inspect_banks(self.raw,self.roots((512,)),targets=(self.hit,))
    def test_dedup(self):
        p=m.inspect_banks(self.raw,self.roots()*2,targets=(self.hit,));self.assertEqual(len(p['matches']),1)
    def test_song_root(self):
        struct.pack_into('<IHH',self.raw,0x100,B+0x200,0,0)
        struct.pack_into('<BBBBII',self.raw,0x200,1,0,0,0,self.bank,B+0x500)
        p=m.song_banks(self.raw,B+0x100,1);self.assertEqual(p['entries'][0]['bank'],self.bank)
    def test_bad_song_track(self):
        struct.pack_into('<IHH',self.raw,0x100,B+0x200,0,0)
        struct.pack_into('<BBBBII',self.raw,0x200,1,0,0,0,self.bank,0)
        p=m.song_banks(self.raw,B+0x100,1);self.assertEqual(p['rejected'],1)
    def test_song_count_limit(self):
        with self.assertRaises(ValueError):m.song_banks(self.raw,B+0x100,513)
    def test_literals_are_not_execution(self):
        struct.pack_into('<H',self.raw,0x100,0x4800)
        struct.pack_into('<I',self.raw,0x104,self.bank)
        p=m.literal_facts(self.raw,dict(address=B+0x100,next_address=B+0x102))
        self.assertEqual(p['literal_shapes'][0]['canonical_target'],self.bank)
        self.assertFalse(p['literal_shapes'][0]['instruction_fetch_proven'])
    def test_invalid_window(self):
        with self.assertRaises(ValueError):m.literal_facts(self.raw,dict(address=B,next_address=None))
    def test_deterministic_no_write(self):
        before=bytes(self.raw);a=m.encode(self.inspect());self.assertEqual(a,m.encode(self.inspect()));self.assertEqual(before,bytes(self.raw))
    def test_saved_zero_is_not_reader(self):
        p=dict(candidate=m.CANDIDATE,origin=dict(address=m.HIT,**m.x.HIT_ID),base_reference_count=0,literal_shape_count=0,
               formal_classification_changes=0,inspections=[dict(origin=n,record_shapes=[]) for n in m.TARGETS[1:]])
        m.validate_parent(p);q=copy.deepcopy(p);q['inspections'][0]['record_shapes']=[{}]
        with self.assertRaises(ValueError):m.validate_parent(q)
    def test_targets_required(self):
        with self.assertRaises(ValueError):m.inspect_banks(self.raw,self.roots(),targets=())

if __name__=='__main__':unittest.main()
