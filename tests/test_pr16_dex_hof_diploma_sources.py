"""Diploma公開source serializerのみ。ROM・旧scope・networkを使わない反証。"""
import copy
import struct
import tempfile
import unittest
from unittest import mock
import zlib
from pathlib import Path

import pr16_dex_hof_diploma_sources as v
import pr16_dex_tail_lease as decoder


def chunk(tag, data):
    return len(data).to_bytes(4, 'big') + tag + data + (zlib.crc32(tag + data) & 0xFFFFFFFF).to_bytes(4, 'big')


def png(width=8, height=8, pixels=None, filters=None, palette=32, packed=None, tail=b'', depth=8, color=3):
    if pixels is None:
        pixels = bytes((x + y * 3) % palette for y in range(height) for x in range(width))
    if filters is None:
        filters = [0] * height
    raw, previous = bytearray(), bytes(width)
    for y in range(height):
        row = pixels[y * width:(y + 1) * width]
        raw.append(filters[y])
        for x, value in enumerate(row):
            a, b, c = row[x - 1] if x else 0, previous[x], previous[x - 1] if x else 0
            p = a + b - c
            paeth = min((a, b, c), key=lambda candidate: abs(p - candidate))
            predictor = (0, a, b, (a + b) // 2, paeth)[filters[y]] if filters[y] < 5 else 0
            raw.append((value - predictor) & 255)
        previous = row
    packed = zlib.compress(raw) if packed is None else packed
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, 0))
            + chunk(b'PLTE', bytes((i % 256 for i in range(palette * 3))))
            + chunk(b'IDAT', packed) + chunk(b'IEND', b'') + tail)


class SyntheticDiplomaSourcesTests(unittest.TestCase):
    def test_01_all_png_filters(self):
        expected = bytes((x * 5 + y * 7) % 32 for y in range(8) for x in range(8))
        for mode in range(5):
            with self.subTest(filter=mode):
                self.assertEqual(v.png_pixels(png(pixels=expected, filters=[mode] * 8)), (8, 8, expected))

    def test_02_mixed_png_filters(self):
        expected = bytes(range(32)) * 2
        self.assertEqual(v.png_pixels(png(pixels=expected, filters=[0, 1, 2, 3, 4, 1, 3, 4]))[2], expected)

    def test_03_png_crc_every_chunk(self):
        good = png()
        at = 8
        while at < len(good):
            size = int.from_bytes(good[at:at + 4], 'big')
            damaged = bytearray(good)
            damaged[at + 8 + size] ^= 1
            with self.subTest(chunk=good[at + 4:at + 8]), self.assertRaises(ValueError):
                v.png_pixels(bytes(damaged))
            at += size + 12

    def test_04_png_truncations(self):
        good = png()
        for cut in range(len(good)):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                v.png_pixels(good[:cut])

    def test_05_png_extra_suffix(self):
        with self.assertRaises(ValueError):
            v.png_pixels(png(tail=b'\0'))

    def test_06_png_bad_pixel_palette(self):
        with self.assertRaises(ValueError):
            v.png_pixels(png(pixels=bytes([32]) * 64))

    def test_07_png_unsupported_modes(self):
        for depth, color in ((4, 3), (8, 2), (16, 3)):
            with self.subTest(depth=depth, color=color), self.assertRaises(ValueError):
                v.png_pixels(png(depth=depth, color=color))

    def test_08_png_bad_filter(self):
        with self.assertRaises(ValueError):
            v.png_pixels(png(filters=[5] * 8))

    def test_09_png_zlib_incomplete_extra_stream_and_overflow(self):
        packed = zlib.compress(b'\0' * 72)
        for value in (packed[:-1], packed + b'X', packed + packed,
                      zlib.compress(b'\0' * 73), zlib.compress(b'\0' * 71), zlib.compress(b'\0' * 200000)):
            with self.subTest(size=len(value)), self.assertRaises(ValueError):
                v.png_pixels(png(packed=value))

    def test_10_png_bad_chunk_order(self):
        good = png()
        ihdr = good[8:33]
        cases = (good[:33] + ihdr + good[33:], good[:33] + chunk(b'ABCD', b'') + good[33:],
                 good[:33] + chunk(b'IDAT', b'') + good[33:])
        for value in cases:
            with self.assertRaises(ValueError):
                v.png_pixels(value)

    def test_11_png_discontiguous_idat(self):
        good = png()
        marker = good.index(b'IDAT') - 4
        size = int.from_bytes(good[marker:marker + 4], 'big')
        part = good[marker + 8:marker + 8 + size]
        bad = good[:marker] + chunk(b'IDAT', part[:2]) + chunk(b'tEXt', b'x') + chunk(b'IDAT', part[2:]) + chunk(b'IEND', b'')
        with self.assertRaises(ValueError):
            v.png_pixels(bad)

    def test_12_png_multiple_consecutive_idat(self):
        good = png()
        marker = good.index(b'IDAT') - 4
        size = int.from_bytes(good[marker:marker + 4], 'big')
        part = good[marker + 8:marker + 8 + size]
        split = good[:marker] + chunk(b'IDAT', part[:2]) + chunk(b'IDAT', part[2:]) + chunk(b'IEND', b'')
        self.assertEqual(v.png_pixels(split), v.png_pixels(good))

    def test_13_diploma_all_pixels_tile_order_and_bank_strip(self):
        pixels = bytes((x + y * 3) % 32 for y in range(128) for x in range(128))
        tiles = v.encode_diploma_tiles(png(128, 128, pixels))
        self.assertEqual(len(tiles), 8192)
        for y in range(128):
            for x in range(128):
                at = ((y // 8) * 16 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2
                self.assertEqual((tiles[at] >> (4 * (x % 2))) & 15, pixels[y * 128 + x] % 16)

    def test_14_diploma_extent_required(self):
        with self.assertRaises(ValueError):
            v.encode_diploma_tiles(png())

    def test_15_lz_exact_literals(self):
        consumed, padded = v.encode_lz10(b'ABCDEFGH')
        self.assertEqual(consumed, b'\x10\x08\x00\x00\x00ABCDEFGH')
        self.assertEqual(padded, consumed + b'\0\0\0')

    def test_16_lz_default_distance_two_and_overlap(self):
        consumed, padded = v.encode_lz10(b'A' * 20)
        self.assertEqual(consumed, bytes.fromhex('10140000204141f001'))
        self.assertEqual(decoder.lz(consumed), b'A' * 20)
        self.assertEqual(len(padded), 12)

    def test_17_lz_first_best_tie(self):
        # ABCABCXABCの最終ABCは距離4と7が同長で、sourceと同じ距離4を選ぶ。
        consumed, _ = v.encode_lz10(b'ABCABCXABC')
        self.assertEqual(consumed, bytes.fromhex('100a0000144142430002580003'))
        self.assertEqual(decoder.lz(consumed), b'ABCABCXABC')

    def test_18_lz_max_match_and_flag_groups(self):
        for data in (bytes(range(256)), b'AB' * 100, bytes(range(100)) * 50, b'A' * 37):
            with self.subTest(size=len(data)):
                consumed, padded = v.encode_lz10(data)
                self.assertEqual(decoder.lz(consumed), data)
                self.assertEqual(len(padded) % 4, 0)
                self.assertLess(len(padded) - len(consumed), 4)

    def test_19_lz_input_bounds(self):
        for value, distance in ((b'', 2), (b'A', 0), (b'A', True), (b'A', 4097), (bytearray(b'A'), 2)):
            with self.subTest(distance=distance), self.assertRaises(ValueError):
                v.encode_lz10(value, distance)

    def test_20_lz_padding_is_not_consumed(self):
        consumed, padded = v.encode_lz10(b'AB')
        self.assertNotEqual(consumed, padded)
        with self.assertRaises(ValueError):
            decoder.lz(padded)

    def test_21_source_set_missing_extra(self):
        for value in ({}, {'extra': b''}, []):
            with self.assertRaises(ValueError):
                v.bind_sources(value)

    def test_22_missing_cache_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, 'cache missing'):
            v.load_sources(directory)

    def test_30_cache_size_checked_before_read(self):
        first = next(iter(v.SOURCE_IDS.values()))
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory) / first['cache_name']
            local.write_bytes(b'X' * (first['size'] + 1))
            with mock.patch.object(Path, 'open', side_effect=AssertionError('must reject before read')):
                with self.assertRaisesRegex(ValueError, 'size before read'):
                    v.load_sources(directory)

    def test_31_cache_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            real = Path(directory) / 'real'
            (real / 'cache').mkdir(parents=True)
            linked = Path(directory) / 'linked'
            linked.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink rejected'):
                v.load_sources(linked / 'cache')

    def test_32_cache_directory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            linked = Path(directory) / 'linked'
            linked.symlink_to(v.CACHE, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink rejected'):
                v.load_sources(linked)


class FixedPublicDiplomaSourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [r['cache_name'] for r in v.SOURCE_IDS.values() if not (v.CACHE / r['cache_name']).is_file()]
        if missing:
            raise unittest.SkipTest('固定公開source cacheなし。全byte source検査は未実施、synthetic検査は別classで実施: ' + ', '.join(missing))
        cls.sources = v.load_sources()
        cls.asset = v.diploma_asset(cls.sources)

    def test_23_whole_sources_and_defensive_copy(self):
        before = copy.deepcopy(v.SOURCE_IDS)
        result = v.bind_sources(self.sources)
        result[next(iter(result))]['size'] += 1
        self.assertEqual(v.SOURCE_IDS, before)
        self.assertEqual(len(self.sources), 13)

    def test_24_all_source_identity_mutations(self):
        for path, raw in self.sources.items():
            for damaged in (raw[:-1], raw + b'\0', bytes([raw[0] ^ 1]) + raw[1:]):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    v.bind_sources({**self.sources, path: damaged})

    def test_25_source_missing_and_extra(self):
        for path in self.sources:
            with self.subTest(path=path), self.assertRaises(ValueError):
                v.bind_sources({k: b for k, b in self.sources.items() if k != path})
        with self.assertRaises(ValueError):
            v.bind_sources({**self.sources, 'extra': b''})

    def test_26_source_png_complete_identity(self):
        self.assertEqual(self.asset['decoded_identity'], v.DECODED)
        self.assertEqual(v.png_pixels(self.sources[v.PNG])[:2], (128, 128))

    def test_27_all_8192_decoded_bytes_equal_independent_decoder(self):
        self.assertEqual(decoder.lz(self.asset['consumed']), self.asset['tiles'])

    def test_28_exact_consumed_and_excluded_padding(self):
        self.assertEqual(self.asset['consumed_identity'], v.CONSUMED)
        self.assertEqual(self.asset['padded'], self.asset['consumed'] + b'\0\0')
        self.assertEqual(self.asset['padded_identity'], {'size': 3368, 'sha256': '0a0159f0e97592b16103a331a5a445ddca2db6ee4ab95b9e5ea8bbf48ebaf912'})
        with self.assertRaises(ValueError):
            decoder.lz(self.asset['padded'])

    def test_29_cached_file_not_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for path, expected in v.SOURCE_IDS.items():
                (base / expected['cache_name']).symlink_to(v.CACHE / expected['cache_name'])
            with self.assertRaises(ValueError):
                v.load_sources(base)


if __name__ == '__main__':
    unittest.main()
