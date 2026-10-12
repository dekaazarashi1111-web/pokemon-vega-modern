"""音声origin専用の人工境界試験。受入済みROM/readerは再走しない。"""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest

P = Path(__file__).resolve().parents[1] / 'scripts/pr16_sound_origin_asset.py'
SPEC = importlib.util.spec_from_file_location('sound_asset', P)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def chunk(tag, data):
    return tag + struct.pack('<I', len(data)) + data + b'\0' * (len(data) % 2)


def wav(data=b'\x00\x7f\x80\xff', bits=8, extra=b'', channels=1):
    fmt = struct.pack('<HHIIHH', 1, channels, 8000, 8000*(bits//8), bits//8, bits)
    body = b'WAVE' + chunk(b'fmt ', fmt) + chunk(b'data', data) + extra
    return b'RIFF' + struct.pack('<I', len(body)) + body


def smpl(start=1, end=2, kind=0):
    return chunk(b'smpl', struct.pack('<9I', 0,0,0,60,0,0,0,1,0) + struct.pack('<6I',0,kind,start,end,0,0))


class SoundAssetTests(unittest.TestCase):
    def test_pcm8_all_values(self):
        raw, facts = m.convert_pcm(wav(bytes(range(256))))
        self.assertEqual(raw[16:], bytes(range(128,256))+bytes(range(128)))
        self.assertEqual(facts['payload_samples'], 256)

    def test_pcm16_signed_floor(self):
        values = [-32768,-32767,-257,-256,-255,-1,0,1,255,256,32767]
        raw,_ = m.convert_pcm(wav(struct.pack('<11h', *values),16))
        self.assertEqual(raw[16:27], bytes([128,128,254,255,255,255,0,0,0,1,127]))

    def test_unlooped_header(self):
        raw,facts=m.convert_pcm(wav())
        self.assertEqual(struct.unpack('<4I',raw[:16]),(0,8192000,0,4))
        self.assertTrue(facts['header_and_payload_count_match'])

    def test_forward_loop(self):
        raw,facts=m.convert_pcm(wav(extra=smpl()))
        self.assertEqual(struct.unpack('<4I',raw[:16]),(0x40000000,8192000,1,3))
        self.assertEqual(facts['payload_samples'],3)
        self.assertEqual(raw[-1],0)

    def test_loop_clamps_to_input(self):
        self.assertEqual(m.convert_pcm(wav(extra=smpl(end=100)))[1]['payload_samples'],4)

    def test_exact_pitch(self):
        self.assertEqual(m.convert_pcm(wav(extra=chunk(b'agbp',struct.pack('<I',123))))[1]['pitch'],123)

    def test_header_override_preserved(self):
        _,facts=m.convert_pcm(wav(extra=chunk(b'agbl',struct.pack('<I',3))))
        self.assertEqual((facts['header_samples'],facts['payload_samples']),(3,4))
        self.assertFalse(facts['header_and_payload_count_match'])

    def test_zero_override_falls_back(self):
        _,facts=m.convert_pcm(wav(extra=chunk(b'agbl',bytes(4))+chunk(b'agbp',bytes(4))))
        self.assertEqual((facts['header_samples'],facts['pitch']),(4,8192000))

    def test_odd_chunks(self):
        self.assertEqual(len(m.chunks(wav(extra=chunk(b'JUNK',b'x')))),3)

    def test_deterministic_and_immutable(self):
        source=wav();before=copy.deepcopy(source)
        self.assertEqual(m.convert_pcm(source),m.convert_pcm(source))
        self.assertEqual(source,before)
        facts=m.convert_pcm(source)[1]
        self.assertEqual(m.encode(facts),m.encode(__import__('json').loads(m.encode(facts))))

    def test_reject_every_truncation(self):
        raw=wav(extra=smpl())
        for n in range(len(raw)):
            with self.subTest(n=n),self.assertRaises(ValueError):m.convert_pcm(raw[:n])

    def test_reject_bad_magic(self):
        with self.assertRaises(ValueError):m.convert_pcm(b'RIFX'+wav()[4:])

    def test_reject_riff_tail(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav()+b'xx')

    def test_reject_duplicate(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(extra=chunk(b'data',b'ab')))

    def test_reject_unknown_chunk(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(extra=chunk(b'evil',b'ab')))

    def test_reject_stereo(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(channels=2))

    def test_reject_unsupported_width(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(bits=24))

    def test_reject_partial_frame(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(b'abc',16))

    def test_reject_empty_data(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(b''))

    def test_reject_loop_direction(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(extra=smpl(kind=1)))

    def test_reject_loop_range(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(extra=smpl(start=3,end=2)))

    def test_reject_loop_overflow(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(extra=smpl(end=0xffffffff)))

    def test_reject_short_custom_chunks(self):
        for tag in (b'agbp',b'agbl'):
            with self.subTest(tag=tag),self.assertRaises(ValueError):m.convert_pcm(wav(extra=chunk(tag,b'x')))

    def test_reject_undeclared_smpl_tail(self):
        with self.assertRaises(ValueError):m.convert_pcm(wav(extra=chunk(b'smpl',bytes(37))))

    def bound(self):
        asset,_=m.convert_pcm(wav())
        return asset,m.compare_asset(asset,asset,0x08000010,0x08000000,0x08000014,m.identity(asset[16:20]))

    def test_bind_complete_asset_and_hit(self):
        asset,facts=self.bound()
        self.assertEqual(facts['sample_index'],0)
        self.assertEqual(facts['sample_count'],4)
        self.assertFalse(facts['actual_consumer_proven'])
        self.assertFalse(facts['unused_name_proves_unreachable'])
        self.assertEqual(facts['formal_classification_changes'],0)
        self.assertEqual(facts['donor_safe_bytes'],0)

    def test_reject_asset_mismatch_outside_hit(self):
        asset,_=self.bound();changed=bytearray(asset);changed[4]^=1
        with self.assertRaises(ValueError):m.compare_asset(bytes(changed),asset,0x08000010,0x08000000,0x08000014,m.identity(asset[16:]))

    def test_reject_hit_identity(self):
        asset,_=self.bound()
        with self.assertRaises(ValueError):m.compare_asset(asset,asset,0x08000010,0x08000000,0x08000014,m.identity(b'abcd'))

    def test_reject_extent(self):
        asset,_=self.bound()
        with self.assertRaises(ValueError):m.compare_asset(asset,asset,0x08000010,0x08000000,0x08000013,m.identity(asset[16:]))

    def test_reject_hit_header_and_overrun(self):
        asset,_=self.bound()
        for origin in (0x0800000F,0x08000011):
            with self.subTest(origin=origin),self.assertRaises(ValueError):m.compare_asset(asset,asset,origin,0x08000000,0x08000014,m.identity(asset[16:]))

    def test_reject_missing_source(self):
        with self.assertRaises(ValueError):m.source_contract({})

    def test_reject_tampered_source(self):
        with self.assertRaises(ValueError):m.source_contract({p:b'tampered' for p in m.BLOBS})

    def test_u32_bounds(self):
        for offset in (-1,1,True):
            with self.subTest(offset=offset),self.assertRaises(ValueError):m.u32(bytes(4),offset)


if __name__=='__main__':unittest.main()
