"""Forest新scopeだけのPNG/LZ/token境界試験。旧試験/ROM/PNG原本は使わない。"""
import sys, struct, zlib
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_forest_wallpaper_asset as m


def chunk(tag,data):
    return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)


def png(kind=0):
    rows=[];previous=bytes(64)
    for y in range(56):
        row=bytes((x+y)%32 for x in range(64));filtered=[]
        for x,v in enumerate(row):
            a=row[x-1] if x else 0;b=previous[x];c=previous[x-1] if x else 0
            filtered.append((v-(0,a,b,(a+b)//2,m.paeth(a,b,c))[kind])&255)
        rows.append(bytes([kind])+bytes(filtered));previous=row
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',64,56,8,3,0,0,0))+chunk(b'PLTE',bytes(96))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')


class PngTests(unittest.TestCase):
    def test_filter0(self):self.assertEqual(m.indexed8(png()),bytes((x+y)%32 for y in range(56) for x in range(64)))
    def test_filter1(self):self.assertEqual(m.indexed8(png(1)),m.indexed8(png()))
    def test_filter2(self):self.assertEqual(m.indexed8(png(2)),m.indexed8(png()))
    def test_filter3(self):self.assertEqual(m.indexed8(png(3)),m.indexed8(png()))
    def test_filter4(self):self.assertEqual(m.indexed8(png(4)),m.indexed8(png()))
    def test_crc(self):
        b=bytearray(png());b[29]^=1
        with self.assertRaises(ValueError):m.indexed8(bytes(b))
    def test_truncated(self):
        with self.assertRaises(ValueError):m.indexed8(png()[:-1])
    def test_trailing(self):
        with self.assertRaises(ValueError):m.indexed8(png()+b'\0')
    def test_wrong_geometry(self):
        b=png();b=b[:8]+chunk(b'IHDR',struct.pack('>IIBBBBB',56,64,8,3,0,0,0))+b[33:]
        with self.assertRaises(ValueError):m.indexed8(b)
    def test_wrong_depth(self):
        b=png();b=b[:8]+chunk(b'IHDR',struct.pack('>IIBBBBB',64,56,4,3,0,0,0))+b[33:]
        with self.assertRaises(ValueError):m.indexed8(b)
    def test_duplicate_header(self):
        b=png()
        with self.assertRaises(ValueError):m.indexed8(b[:33]+b[8:])
    def test_wrong_fixed_png(self):
        with self.assertRaises(ValueError):m.independent(png())
    def test_bank_nibble_order_and_tiles(self):
        pixels=bytes(range(32))*112;out=m.pack_tiles(pixels)
        self.assertEqual(out[:4],bytes.fromhex('10325476'))
        self.assertEqual(len(out),1792)
        self.assertEqual(out[:32],out[64:96])
    def test_53_tiles_not_56(self):
        self.assertEqual(len(m.forest_tiles(bytes(64*56))),1696)
    def test_nonblank_omitted_tile_rejected(self):
        pixels=bytearray(64*56);pixels[-1]=1
        with self.assertRaises(ValueError):m.forest_tiles(bytes(pixels))
    def test_incomplete_image(self):
        with self.assertRaises(ValueError):m.pack_tiles(bytes(100))


class LzTests(unittest.TestCase):
    def test_literals_and_alignment(self):
        consumed,padded=m.compress(b'abcde');out,used,tokens=m.decode(padded)
        self.assertEqual(out,b'abcde');self.assertEqual(used,len(consumed))
        self.assertEqual(len(padded)%4,0)
    def test_overlapping_copy(self):
        c,p=m.compress(b'ab'*64);out,used,t=m.decode(p)
        self.assertEqual(out,b'ab'*64)
        self.assertTrue(any(x['kind']=='backreference_length_distance' for x in t))
    def test_all_input_tokens_once(self):
        c,p=m.compress(bytes(range(256))*4);out,used,t=m.decode(p)
        positions=[i for row in t for i in range(row['offset'],row['offset']+row['size'])]
        self.assertEqual(positions,list(range(len(c))))
    def test_empty_source_rejected(self):
        with self.assertRaises(ValueError):m.compress(b'')
    def test_source_bound(self):
        with self.assertRaises(ValueError):m.compress(bytes(8193))
    def test_bad_type(self):
        with self.assertRaises(ValueError):m.decode(b'\x20\x01\0\0\0a')
    def test_zero_size(self):
        with self.assertRaises(ValueError):m.decode(b'\x10\0\0\0')
    def test_forward_reference(self):
        with self.assertRaises(ValueError):m.decode(b'\x10\x03\0\0\x80\0\0')
    def test_output_overrun(self):
        with self.assertRaises(ValueError):m.decode(b'\x10\x02\0\0\x40a\0\0')
    def test_incomplete_reference(self):
        with self.assertRaises(ValueError):m.decode(b'\x10\x04\0\0\x40a\0')
    def test_missing_flags(self):
        with self.assertRaises(ValueError):m.decode(b'\x10\x01\0\0')
    def test_nonzero_padding(self):
        c,p=m.compress(b'a')
        with self.assertRaises(ValueError):m.decode(p[:-1]+b'x')
    def test_extra_zero_word(self):
        c,p=m.compress(b'abcd')
        with self.assertRaises(ValueError):m.decode(p+bytes(4))
    def test_deterministic(self):self.assertEqual(m.compress(bytes(range(255))),m.compress(bytes(range(255))))
    def test_actual_rom_cannot_be_fixture(self):
        with self.assertRaises(ValueError):m.measure(bytes(100),png(),{})
    def test_no_promotion(self):
        self.assertFalse(m.CLAIMS['formal_classification_accepted']);self.assertEqual(m.CLAIMS['newly_classified'],0)
        self.assertFalse(m.CLAIMS['actual_entry_executed']);self.assertEqual(m.CLAIMS['donor_safe_bytes'],0)
    def test_closed_public_set(self):
        with self.assertRaises(ValueError):m.source_bindings({})


if __name__=='__main__':unittest.main()
