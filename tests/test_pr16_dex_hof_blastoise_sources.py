"""Blastoise公開source serializer専用。ROM・network・旧suiteを呼ばない。"""
import copy
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import zlib

import pr16_dex_hof_blastoise_sources as v
import pr16_dex_tail_lease as decoder


def chunk(tag, data):
    return len(data).to_bytes(4, 'big') + tag + data + (zlib.crc32(tag + data) & 0xFFFFFFFF).to_bytes(4, 'big')


def png(width=8, height=8, pixels=None, filters=None, palette=16, packed=None,
        tail=b'', depth=4, color=3, compression=0, filtering=0, interlace=0, odd_tail=0):
    if pixels is None:
        pixels = bytes((x + y * 3) % min(palette or 16, 16) for y in range(height) for x in range(width))
    if filters is None:
        filters = [0] * height
    raw, previous = bytearray(), bytes((width + 1) // 2)
    for y in range(height):
        values = pixels[y * width:(y + 1) * width]
        row = bytes((values[x] << 4) | (values[x + 1] if x + 1 < width else odd_tail)
                    for x in range(0, width, 2))
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
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, color, compression, filtering, interlace))
            + chunk(b'PLTE', bytes(i % 256 for i in range(palette * 3)))
            + chunk(b'IDAT', packed) + chunk(b'IEND', b'') + tail)


def split_chunks(raw):
    result, at = [], 8
    while at < len(raw):
        size = int.from_bytes(raw[at:at + 4], 'big')
        result.append((raw[at + 4:at + 8], raw[at + 8:at + 8 + size]))
        at += size + 12
    return result


def assemble(items):
    return b'\x89PNG\r\n\x1a\n' + b''.join(chunk(tag, data) for tag, data in items)


class SyntheticBlastoiseSourcesTests(unittest.TestCase):
    def test_01_all_png_filters_on_packed_bytes(self):
        expected = bytes((x * 5 + y * 7) % 16 for y in range(8) for x in range(8))
        for mode in range(5):
            with self.subTest(filter=mode):
                self.assertEqual(v.png_pixels(png(pixels=expected, filters=[mode] * 8)), (8, 8, expected))

    def test_02_mixed_filters_and_nibble_order(self):
        expected = bytes(range(16)) * 4
        self.assertEqual(v.png_pixels(png(pixels=expected, filters=[0, 1, 2, 3, 4, 1, 3, 4]))[2], expected)

    def test_03_odd_width_excludes_unused_low_nibble(self):
        expected = bytes((x + y) % 8 for y in range(8) for x in range(7))
        for mode in range(5):
            self.assertEqual(v.png_pixels(png(7, 8, expected, [mode] * 8, palette=8, odd_tail=15)), (7, 8, expected))

    def test_04_crc_every_chunk(self):
        good, at = png(), 8
        while at < len(good):
            size = int.from_bytes(good[at:at + 4], 'big')
            damaged = bytearray(good)
            damaged[at + 8 + size] ^= 1
            with self.subTest(chunk=good[at + 4:at + 8]), self.assertRaisesRegex(ValueError, 'CRC'):
                v.png_pixels(bytes(damaged))
            at += size + 12

    def test_05_every_truncation(self):
        good = png()
        for cut in range(len(good)):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                v.png_pixels(good[:cut])

    def test_06_extra_suffix(self):
        with self.assertRaises(ValueError):
            v.png_pixels(png(tail=b'\0'))

    def test_07_palette_index_bounds(self):
        for index in (8, 15):
            with self.assertRaisesRegex(ValueError, 'pixel outside'):
                v.png_pixels(png(pixels=bytes([index]) * 64, palette=8))

    def test_08_palette_geometry(self):
        for count in (0, 17, 256):
            with self.assertRaises(ValueError):
                v.png_pixels(png(palette=count))
        parts = split_chunks(png())
        parts[1] = (b'PLTE', b'1234')
        with self.assertRaises(ValueError):
            v.png_pixels(assemble(parts))

    def test_09_unsupported_header_modes(self):
        for args in ({'depth': 8}, {'depth': 2}, {'depth': 16}, {'color': 2}, {'color': 0},
                     {'compression': 1}, {'filtering': 1}, {'interlace': 1}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                v.png_pixels(png(**args))

    def test_10_dimensions_bound(self):
        for width, height in ((0, 8), (8, 0), (129, 8), (8, 129)):
            with self.assertRaises(ValueError):
                v.png_pixels(png(width, height))

    def test_11_invalid_filter(self):
        for mode in (5, 255):
            with self.assertRaises(ValueError):
                v.png_pixels(png(filters=[mode] * 8))

    def test_12_zlib_complete_bounded_single_stream(self):
        packed = zlib.compress(b'\0' * 40)
        for value in (packed[:-1], packed + b'X', packed + packed, b'bad',
                      zlib.compress(b'\0' * 41), zlib.compress(b'\0' * 39), zlib.compress(b'\0' * 200000)):
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                v.png_pixels(png(packed=value))

    def test_13_first_header_and_duplicate_header(self):
        p = split_chunks(png())
        for parts in (p[1:], [p[1], p[0], *p[2:]], [p[0], p[0], *p[1:]]):
            with self.assertRaises(ValueError):
                v.png_pixels(assemble(parts))

    def test_14_palette_before_idat_single(self):
        p = split_chunks(png())
        for parts in ([p[0], *p[2:]], [p[0], p[2], p[1], p[3]], [p[0], p[1], p[1], *p[2:]]):
            with self.assertRaises(ValueError):
                v.png_pixels(assemble(parts))

    def test_15_unknown_critical_invalid_type_reserved_bit(self):
        p = split_chunks(png())
        for tag in (b'ABCD', b'aBCD', b'tExt', b'tEX1'):
            # aBCDは正規ancillaryなので別に受入を確かめる。
            if tag == b'aBCD':
                self.assertEqual(v.png_pixels(assemble([p[0], (tag, b'x'), *p[1:]])), v.png_pixels(png()))
            else:
                with self.assertRaises(ValueError):
                    v.png_pixels(assemble([p[0], (tag, b'x'), *p[1:]]))

    def test_16_discontiguous_idat_rejected(self):
        h, palette, data, end = split_chunks(png())
        bad = assemble([h, palette, (b'IDAT', data[1][:2]), (b'tEXt', b'x'), (b'IDAT', data[1][2:]), end])
        with self.assertRaises(ValueError):
            v.png_pixels(bad)

    def test_17_consecutive_idat_accepted(self):
        h, palette, data, end = split_chunks(png())
        split = assemble([h, palette, (b'IDAT', b''), (b'IDAT', data[1][:2]), (b'IDAT', data[1][2:]), end])
        self.assertEqual(v.png_pixels(split), v.png_pixels(png()))

    def test_18_terminal_iend_required_empty_final(self):
        p = split_chunks(png())
        for parts in (p[:-1], [*p[:-1], (b'IEND', b'X')], [*p, p[-1]], [p[0], p[1], p[-1]]):
            with self.assertRaises(ValueError):
                v.png_pixels(assemble(parts))

    def test_19_input_type_signature_size(self):
        for value in (b'', bytearray(png()), 'PNG', b'X' + png()[1:], png() + b'\0' * 100000):
            with self.assertRaises(ValueError):
                v.png_pixels(value)

    def test_20_all_6400_pixels_tile_order_nibble_swap(self):
        pixels = bytes((x * 7 + y * 3) % 16 for y in range(80) for x in range(80))
        tiles = v.encode_blastoise_tiles(png(80, 80, pixels, [y % 5 for y in range(80)]))
        self.assertEqual(len(tiles), 3200)
        for y in range(80):
            for x in range(80):
                at = ((y // 8) * 10 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2
                self.assertEqual((tiles[at] >> (4 * (x % 2))) & 15, pixels[y * 80 + x])

    def test_21_asset_requires_full_geometry(self):
        for w, h in ((8, 8), (80, 72), (72, 80), (128, 128)):
            with self.assertRaises(ValueError):
                v.encode_blastoise_tiles(png(w, h))

    def test_22_closed_set_shape(self):
        for value in ({}, {'extra': b''}, [], None):
            with self.assertRaises(ValueError):
                v.bind_sources(value)

    def test_23_missing_cache_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, 'cache missing'):
            v.load_sources(directory)

    def test_24_cache_size_checked_before_read(self):
        first = next(iter(v.SOURCE_IDS.values()))
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory) / first['cache_name']
            local.write_bytes(b'X' * (first['size'] + 1))
            with mock.patch.object(Path, 'open', side_effect=AssertionError('must reject before read')):
                with self.assertRaisesRegex(ValueError, 'size before read'):
                    v.load_sources(directory)

    def test_25_cache_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            real = Path(directory) / 'real'
            (real / 'cache').mkdir(parents=True)
            linked = Path(directory) / 'linked'
            linked.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink rejected'):
                v.load_sources(linked / 'cache')

    def test_26_cache_directory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            linked = Path(directory) / 'linked'
            linked.symlink_to(v.CACHE, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink rejected'):
                v.load_sources(linked)


class FixedPublicBlastoiseSourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [r['cache_name'] for r in v.SOURCE_IDS.values() if not (v.CACHE / r['cache_name']).is_file()]
        if missing:
            raise unittest.SkipTest('固定公開source cacheなし。全byte検査未実施: ' + ', '.join(missing))
        cls.sources = v.load_sources()
        cls.asset = v.blastoise_asset(cls.sources)

    def test_27_whole_sources_and_defensive_copy(self):
        before = copy.deepcopy(v.SOURCE_IDS)
        result = v.bind_sources(self.sources)
        result[next(iter(result))]['size'] += 1
        self.assertEqual(v.SOURCE_IDS, before)
        self.assertEqual(len(self.sources), 14)

    def test_28_all_source_identity_mutations(self):
        for path, raw in self.sources.items():
            for damaged in (raw[:-1], raw + b'\0', bytes([raw[0] ^ 1]) + raw[1:]):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    v.bind_sources({**self.sources, path: damaged})

    def test_29_source_missing_and_extra(self):
        for path in self.sources:
            with self.subTest(path=path), self.assertRaises(ValueError):
                v.bind_sources({k: b for k, b in self.sources.items() if k != path})
        with self.assertRaises(ValueError):
            v.bind_sources({**self.sources, 'extra': b''})

    def test_30_source_immutable_bytes_only(self):
        path = next(iter(self.sources))
        with self.assertRaises(ValueError):
            v.bind_sources({**self.sources, path: bytearray(self.sources[path])})

    def test_31_png_complete_identity_and_geometry(self):
        self.assertEqual(self.asset['decoded_identity'], v.DECODED)
        self.assertEqual(v.png_pixels(self.sources[v.PNG])[:2], (80, 80))
        self.assertEqual(len(v.png_pixels(self.sources[v.PNG])[2]), 6400)

    def test_32_all_3200_bytes_equal_independent_lz_decoder(self):
        self.assertEqual(decoder.lz(self.asset['consumed']), self.asset['tiles'])
        self.assertEqual(self.asset['consumed'][:4], bytes.fromhex('10800c00'))

    def test_33_exact_consumed_and_excluded_padding(self):
        self.assertEqual(self.asset['consumed_identity'], v.CONSUMED)
        self.assertEqual(self.asset['padded_identity'], v.PADDED)
        self.assertEqual(self.asset['padded'], self.asset['consumed'] + b'\0\0')
        with self.assertRaises(ValueError):
            decoder.lz(self.asset['padded'])

    def test_34_target_four_bytes_are_inside_source_consumed(self):
        offset = 0x083D6B61 - 0x083D655C
        self.assertEqual(offset, 0x605)
        self.assertEqual(self.asset['consumed'][offset:offset + 4], bytes.fromhex('df06ff0b'))
        self.assertLessEqual(offset + 4, len(self.asset['consumed']))
        self.assertEqual(0x083D655C + len(self.asset['consumed']), 0x083D6C5E)

    def test_35_cached_file_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for expected in v.SOURCE_IDS.values():
                (Path(directory) / expected['cache_name']).symlink_to(v.CACHE / expected['cache_name'])
            with self.assertRaisesRegex(ValueError, 'symlink rejected'):
                v.load_sources(directory)

    def test_36_fixed_source_commits_and_semantic_chain(self):
        for path, record in v.SOURCE_IDS.items():
            self.assertEqual(record['commit'], 'c04a31542086b20d8c6ee641eaa70b8db6713fd3' if path.startswith('diagnostics/') else v.COMMIT)
            for token in v.SOURCE_TOKENS.get(path, ()):
                self.assertIn(token, self.sources[path].decode())
        rows = {row.split('\t')[4]: row.split('\t')[1] for row in v.JP_ROWS}
        self.assertEqual(rows['sBlastoise1_Tiles'], '083d655c')
        self.assertEqual(rows['LoadCreditsMonPic'], '080f5208')
        self.assertEqual(rows['CopyToWindowPixelBuffer'], '080043d0')
        self.assertEqual(rows['gWindows'], '02020430')

    def test_37_no_blind_extent_from_audit_reference_size(self):
        metadata = self.sources[v.JP_METADATA].decode()
        self.assertIn('size_policy\treference size retained; not a verified localized extent', metadata)
        self.assertEqual(len(self.asset['consumed']), 1794)
        self.assertNotEqual(len(self.asset['consumed']), int(next(row for row in v.JP_ROWS if '\tsBlastoise1_Tiles\t' in row).split('\t')[3], 16))

    def test_38_semantic_token_is_checked_even_if_hash_function_is_mocked(self):
        path = 'src/window.c'
        damaged = self.sources[path].replace(b'LZ77UnCompWram(src,', b'LZ77UnCompVram(src,')
        original_identity, original_blob = v.identity, v.git_blob
        with mock.patch.object(v, 'identity', side_effect=lambda raw: original_identity(self.sources[path] if raw == damaged else raw)), \
             mock.patch.object(v, 'git_blob', side_effect=lambda raw: original_blob(self.sources[path] if raw == damaged else raw)):
            with self.assertRaisesRegex(ValueError, 'semantic token'):
                v.bind_sources({**self.sources, path: damaged})

    def test_39_asset_checks_generated_tiles_identity(self):
        with mock.patch.object(v, 'encode_blastoise_tiles', return_value=b'\0' * 3200):
            with self.assertRaisesRegex(ValueError, 'whole Blastoise tiles'):
                v.blastoise_asset(self.sources)

    def test_40_asset_checks_generated_consumed_identity(self):
        with mock.patch.object(v, 'encode_lz10', return_value=(self.asset['consumed'][:-1], self.asset['padded'])):
            with self.assertRaisesRegex(ValueError, 'exact consumed'):
                v.blastoise_asset(self.sources)

    def test_41_asset_checks_terminal_padding(self):
        with mock.patch.object(v, 'encode_lz10', return_value=(self.asset['consumed'], self.asset['padded'][:-1] + b'X')):
            with self.assertRaisesRegex(ValueError, 'padding'):
                v.blastoise_asset(self.sources)


if __name__ == '__main__':
    unittest.main()
