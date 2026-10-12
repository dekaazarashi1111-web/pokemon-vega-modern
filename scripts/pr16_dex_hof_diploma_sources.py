#!/usr/bin/env python3
"""固定公開Diploma PNGから4bpp/LZ10を独立生成する。ROM入力・探索はない。"""
from __future__ import annotations

import copy
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local/jp-diploma-sources'
COMMIT = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
PNG = 'graphics/diploma/diploma.png'
DECODED = {'size': 8192, 'sha256': '1e3d4069b5ab9ebd09f28341597009aba99696b57290b89d3a6620b6914c7dfd'}
CONSUMED = {'size': 3366, 'sha256': 'cef35413656191513ea96f09a2f088f33fac4b579317567e7b4cf8875388490f'}
JP_AUDIT = 'diagnostics/pokefirered_jp.sym.audit.tsv'
JP_METADATA = 'diagnostics/pokefirered_jp.sym.metadata.tsv'
JP_ROWS = (
    '080017e4\t080017d0\tg\t000000b8\tLoadBgTiles\tunique_normalized_code\t98\t1',
    '080f5014\t080f6000\tl\t0000007c\tDiplomaLoadGfx\tunique_normalized_code\t98\t1',
    '080f6880\t080f7860\tg\t00000024\tResetTempTileDataBuffers\tunique_normalized_code\t98\t1',
    '080f68f0\t080f78d0\tg\t00000078\tDecompressAndCopyTileDataToVram\tunique_normalized_code\t98\t1',
    '080f6b18\t080f7af8\tg\t00000030\tMallocAndDecompress\tunique_normalized_code\t98\t1',
    '080f6b48\t080f7b28\tl\t00000036\tCopyDecompressedTileDataToVram\tunique_normalized_code\t98\t1',
    '081e3be0\t081c7a90\tg\t00000004\tLZ77UnCompWram\trelocated_pointer_or_call\t96\t1',
    '08414830\t083dbf7c\tl\t00000d28\tsDiplomaGfx\tunique_normalized_data\t98\t1',
)
SOURCE_TOKENS = {
    'src/diploma.c': (
        'static const u32 sDiplomaGfx[] = INCBIN_U32("graphics/diploma/diploma.4bpp.lz");',
        'CreateTask(Task_DiplomaInit, 0);', 'if (!DiplomaLoadGfx())',
        'switch (sDiploma->gfxState)', 'ResetTempTileDataBuffers();',
        'DecompressAndCopyTileDataToVram(BG_DIPLOMA, sDiplomaGfx, 0, 0, 0);'),
    'src/new_menu_helpers.c': (
        'void *sTempTileDataBuffers[0x20]', 'void *ptr = MallocAndDecompress(src, &sizeOut);',
        'if (!size)\n            size = sizeOut;', 'sizeAsBytes[0] = srcAsBytes[1];',
        'sizeAsBytes[1] = srcAsBytes[2];', 'sizeAsBytes[2] = srcAsBytes[3];',
        'sizeAsBytes[3] = 0;', 'ptr = Alloc(*size);', 'LZ77UnCompWram(src, ptr);',
        'return LoadBgTiles(bgId, src, size, offset);'),
    'src/libagbsyscall.s': ('LZ77UnCompWram:\n\tsvc 0x11\n\tbx lr',),
    'src/bg.c': ('u16 LoadBgTiles(u8 bg, const void *src, u16 size, u16 destOffset)',
                 'cursor = LoadBgVram(bg, src, size, tileOffset, DISPCNT_MODE_1);'),
    'tools/gbagfx/main.c': ('int minDistance = 2;',),
    'tools/gbagfx/convert_png.c': ('% (1 << destBitDepth)',),
    'tools/gbagfx/gfx.c': ('*dest++ = (rightPixel << 4) | leftPixel;',),
    'tools/gbagfx/lz.c': ('dest[0] = 0x10;', 'if (blockSize > bestBlockSize)',
                         'while (blockDistance <= srcPos && blockDistance <= 0x1000)'),
}
# 下記は固定公開source全文から得たidentity。可変cache manifestを信頼根にしない。
SOURCE_IDS = {'Makefile': {'cache_name': 'pret-Makefile',
              'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
              'git_blob': '8b454dbd18eb0069fa5851d788697190890a5b37',
              'path': 'Makefile',
              'repository': 'pret/pokefirered',
              'sha256': '51960ea72311e53c272ebcc5b481021efba52fcc7db7f0ded4bfcebaf8bbdf47',
              'size': 14605,
              'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/Makefile'},
 'diagnostics/pokefirered_jp.sym.audit.tsv': {'cache_name': 'frlg-diagnostics_pokefirered_jp.sym.audit.tsv',
                                              'commit': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
                                              'git_blob': '53316c0d61da2c6cc22acf3d79f68c61c64c65be',
                                              'path': 'diagnostics/pokefirered_jp.sym.audit.tsv',
                                              'repository': 'ComplexRobot/frlg-sym',
                                              'sha256': 'fc1e4b579b21a592b8e09fa3c36f242833837190401128cd6866c945eff2f44e',
                                              'size': 4147002,
                                              'url': 'https://github.com/ComplexRobot/frlg-sym/blob/c04a31542086b20d8c6ee641eaa70b8db6713fd3/diagnostics/pokefirered_jp.sym.audit.tsv'},
 'diagnostics/pokefirered_jp.sym.metadata.tsv': {'cache_name': 'frlg-diagnostics_pokefirered_jp.sym.metadata.tsv',
                                                 'commit': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
                                                 'git_blob': '2550c490a130f22dfd59725a200152a607c969fd',
                                                 'path': 'diagnostics/pokefirered_jp.sym.metadata.tsv',
                                                 'repository': 'ComplexRobot/frlg-sym',
                                                 'sha256': 'aa387f052a694890c3de8104f93b885cd0091d401a59cddf8ab067a6869bb774',
                                                 'size': 464,
                                                 'url': 'https://github.com/ComplexRobot/frlg-sym/blob/c04a31542086b20d8c6ee641eaa70b8db6713fd3/diagnostics/pokefirered_jp.sym.metadata.tsv'},
 'graphics/diploma/diploma.png': {'cache_name': 'pret-graphics_diploma_diploma.png',
                                  'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                  'git_blob': '5f7003dddfa4a0c3eff02ab03d82f861e0776b8b',
                                  'path': 'graphics/diploma/diploma.png',
                                  'repository': 'pret/pokefirered',
                                  'sha256': 'bb4d57325225bdade4efcf6838676c83c190cbffdb0defcca9dd982029eb5f12',
                                  'size': 3172,
                                  'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/graphics/diploma/diploma.png'},
 'graphics_file_rules.mk': {'cache_name': 'pret-graphics_file_rules.mk',
                            'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                            'git_blob': '39b952cd45b6a34eb98318a76aa531fcafff134d',
                            'path': 'graphics_file_rules.mk',
                            'repository': 'pret/pokefirered',
                            'sha256': 'bd56e518ab9527f844642230673ce27a5bae73c7208d917d3288b073859fb685',
                            'size': 14859,
                            'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/graphics_file_rules.mk'},
 'src/bg.c': {'cache_name': 'pret-src_bg.c',
              'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
              'git_blob': 'aa11ae01f87242edecc5656bb6649b04e319357a',
              'path': 'src/bg.c',
              'repository': 'pret/pokefirered',
              'sha256': '4813ff7fb1b9bcc952d3973d05a46d31c9fee57342c7957165a76a136ccd57da',
              'size': 31836,
              'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/bg.c'},
 'src/diploma.c': {'cache_name': 'pret-src_diploma.c',
                   'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'git_blob': 'b10c4d75c746f236755cb6dc49531eba195c0ec8',
                   'path': 'src/diploma.c',
                   'repository': 'pret/pokefirered',
                   'sha256': 'a5bffa1c9c09e14c3a38493234803c79f56a663a8de0459f4375a43c32adafa2',
                   'size': 7805,
                   'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/diploma.c'},
 'src/libagbsyscall.s': {'cache_name': 'pret-src_libagbsyscall.s',
                         'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                         'git_blob': '61c23feb497ade0742be6845be7d5716574f54cc',
                         'path': 'src/libagbsyscall.s',
                         'repository': 'pret/pokefirered',
                         'sha256': '6d183afe7a31976b1e301dac4f2926df9e251a636cd2a197f56bc8296dc46e78',
                         'size': 1358,
                         'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/libagbsyscall.s'},
 'src/new_menu_helpers.c': {'cache_name': 'pret-src_new_menu_helpers.c',
                            'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                            'git_blob': '08c032027cda2c34bf0dded37458adeb250aa553',
                            'path': 'src/new_menu_helpers.c',
                            'repository': 'pret/pokefirered',
                            'sha256': 'd115f81a76f93ba1a34894acd58f266a1920215784176f94188e4bad8ba51b1c',
                            'size': 27834,
                            'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/new_menu_helpers.c'},
 'tools/gbagfx/convert_png.c': {'cache_name': 'pret-tools_gbagfx_convert_png.c',
                                'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                'git_blob': '58371229c06d0c036a23d55ffcbf5761d0089800',
                                'path': 'tools/gbagfx/convert_png.c',
                                'repository': 'pret/pokefirered',
                                'sha256': 'c542d1cffe83516d8b644ec04be507d3fa376231083f03f2001be15152da2965',
                                'size': 7511,
                                'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/tools/gbagfx/convert_png.c'},
 'tools/gbagfx/gfx.c': {'cache_name': 'pret-tools_gbagfx_gfx.c',
                        'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                        'git_blob': '1dfc38e2d0362cb8224f67f057f68ee7120dce9f',
                        'path': 'tools/gbagfx/gfx.c',
                        'repository': 'pret/pokefirered',
                        'sha256': '3cd8346e273b76d74324af0c3aecfeda6607af5757503f3a973bf6be0faaccf2',
                        'size': 18570,
                        'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/tools/gbagfx/gfx.c'},
 'tools/gbagfx/lz.c': {'cache_name': 'pret-tools_gbagfx_lz.c',
                       'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                       'git_blob': '97434ce506dec319f0a76c54494fa2e60894be7d',
                       'path': 'tools/gbagfx/lz.c',
                       'repository': 'pret/pokefirered',
                       'sha256': '57c38f288de241b2490697af96673cde506f3adc97def0fec679745e4be5360c',
                       'size': 3297,
                       'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/tools/gbagfx/lz.c'},
 'tools/gbagfx/main.c': {'cache_name': 'pret-tools_gbagfx_main.c',
                         'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                         'git_blob': '0dba4c8aea0bec7a3f407ae3aee570e8e88a6834',
                         'path': 'tools/gbagfx/main.c',
                         'repository': 'pret/pokefirered',
                         'sha256': '3d263018fd669800dfe3dc5b5e62a013b8433769e4d5dc7c9aad2280980b9c0b',
                         'size': 21495,
                         'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/tools/gbagfx/main.c'}}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def bind_sources(sources):
    """全13source identity・登録/caller・JP exact対応行を固定する。"""
    need(type(sources) is dict and set(sources) == set(SOURCE_IDS), 'closed Diploma source set')
    for path, expected in SOURCE_IDS.items():
        raw = sources[path]
        need(type(raw) is bytes, 'source must be immutable bytes: ' + path)
        need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')}, 'whole source identity: ' + path)
        need(git_blob(raw) == expected['git_blob'], 'source Git blob: ' + path)
    for path, tokens in SOURCE_TOKENS.items():
        text = sources[path].decode('utf-8')
        for token in tokens:
            need(token in text, 'fixed source semantic token: ' + path + ': ' + token)
    audit = [line.split('\t') for line in sources[JP_AUDIT].decode('utf-8').splitlines()]
    for expected in JP_ROWS:
        row = expected.split('\t')
        need([fields for fields in audit if len(fields) >= 5 and fields[4] == row[4]] == [row],
             'unique exact JP correspondence: ' + row[4])
    metadata_lines = [line.split('\t') for line in sources[JP_METADATA].decode('utf-8').splitlines()]
    need(all(len(row) == 2 for row in metadata_lines), 'JP metadata key/value rows')
    metadata = dict(metadata_lines)
    need(len(metadata) == len(metadata_lines), 'unique JP metadata keys')
    for key, value in {'game_code': 'BPRJ', 'revision': '0',
                       'rom_sha256': '1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486',
                       'size_policy': 'reference size retained; not a verified localized extent'}.items():
        need(metadata.get(key) == value, 'JP metadata binding: ' + key)
    return copy.deepcopy(SOURCE_IDS)


def load_sources(cache_dir=CACHE):
    """Git管理外cacheを読むだけ。取得・生成・ROMへのfallbackはしない。"""
    cache_dir = Path(cache_dir).absolute()
    sources = {}
    for path, expected in SOURCE_IDS.items():
        local = cache_dir / expected['cache_name']
        need(all(not part.is_symlink() for part in (local, *local.parents)), 'source cache symlink rejected: ' + path)
        need(local.is_file(), 'fixed source cache missing: ' + path)
        need(local.stat().st_size == expected['size'], 'source cache size before read: ' + path)
        with local.open('rb') as handle:
            sources[path] = handle.read(expected['size'] + 1)
    bind_sources(sources)
    return sources


def paeth(a, b, c):
    value = a + b - c
    left, above, diagonal = abs(value - a), abs(value - b), abs(value - c)
    return a if left <= above and left <= diagonal else (b if above <= diagonal else c)


def png_pixels(raw):
    """bounded indexed8 PNG。CRC・chunk順・全zlib終端・全scanlineを検査。"""
    need(type(raw) is bytes and 0 < len(raw) <= 100000, 'bounded PNG bytes')
    need(raw[:8] == b'\x89PNG\r\n\x1a\n', 'PNG signature')
    at, width, height, palette = 8, None, None, None
    pieces, seen_idat, ended_idat, ended = [], False, False, False
    while at < len(raw):
        need(at + 12 <= len(raw), 'whole PNG chunk header')
        length = int.from_bytes(raw[at:at + 4], 'big')
        tag = raw[at + 4:at + 8]
        end = at + 12 + length
        need(end <= len(raw), 'whole PNG chunk')
        need(all(65 <= x <= 90 or 97 <= x <= 122 for x in tag) and not tag[2] & 32, 'PNG chunk type')
        data = raw[at + 8:at + 8 + length]
        crc = int.from_bytes(raw[at + 8 + length:end], 'big')
        need(zlib.crc32(tag + data) & 0xFFFFFFFF == crc, 'PNG chunk CRC')
        if width is None:
            need(tag == b'IHDR' and length == 13, 'IHDR first and unique')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            need(0 < width <= 128 and 0 < height <= 128, 'bounded PNG dimensions')
            need((depth, color, compression, filtering, interlace) == (8, 3, 0, 0, 0), 'indexed8 noninterlaced PNG')
        elif tag == b'IHDR':
            raise ValueError('duplicate IHDR')
        elif tag == b'PLTE':
            need(palette is None and not seen_idat and 3 <= length <= 768 and length % 3 == 0, 'single indexed palette before IDAT')
            palette = length // 3
        elif tag == b'IDAT':
            need(palette is not None and not ended_idat, 'consecutive IDAT after PLTE')
            seen_idat = True
            pieces.append(data)
        elif tag == b'IEND':
            need(length == 0 and seen_idat and end == len(raw), 'exact terminal IEND')
            ended = True
        else:
            need(tag[0] & 32, 'unsupported critical PNG chunk')
            if seen_idat:
                ended_idat = True
        at = end
        if ended:
            break
    need(ended and at == len(raw), 'complete PNG extent')
    expected_size = height * (width + 1)
    stream = zlib.decompressobj()
    try:
        scanlines = stream.decompress(b''.join(pieces), expected_size + 1)
    except zlib.error as exc:
        raise ValueError('invalid PNG zlib stream') from exc
    need(stream.eof and not stream.unused_data and not stream.unconsumed_tail and len(scanlines) == expected_size,
         'one bounded complete PNG zlib stream')
    pixels = bytearray()
    previous = bytearray(width)
    for y in range(height):
        row_at = y * (width + 1)
        filter_type = scanlines[row_at]
        need(filter_type <= 4, 'PNG filter type')
        row = bytearray(scanlines[row_at + 1:row_at + 1 + width])
        for x in range(width):
            left, above = row[x - 1] if x else 0, previous[x]
            upper_left = previous[x - 1] if x else 0
            predictor = (0, left, above, (left + above) // 2, paeth(left, above, upper_left))[filter_type]
            row[x] = (row[x] + predictor) & 255
        need(all(index < palette for index in row), 'pixel outside indexed palette')
        pixels.extend(row)
        previous = row
    return width, height, bytes(pixels)


def encode_diploma_tiles(png):
    """gbagfxのindex%16とdefault 1×1 metatile順を独立に再現。"""
    width, height, pixels = png_pixels(png)
    need((width, height) == (128, 128), 'whole Diploma PNG geometry')
    return bytes((pixels[(ty + y) * width + tx + x] & 15)
                 | ((pixels[(ty + y) * width + tx + x + 1] & 15) << 4)
                 for ty in range(0, height, 8) for tx in range(0, width, 8)
                 for y in range(8) for x in range(0, 8, 2))


def encode_lz10(raw, min_distance=2):
    """固定gbagfx LZCompressのgreedy順を再現し、最小消費prefixとpadding付きを返す。"""
    need(type(raw) is bytes and 0 < len(raw) <= 100000, 'bounded source LZ bytes')
    need(type(min_distance) is int and 1 <= min_distance <= 4096, 'LZ minimum search distance')
    size, pos = len(raw), 0
    out = bytearray(b'\x10' + len(raw).to_bytes(3, 'little'))
    while pos < size:
        flag_at = len(out)
        out.append(0)
        for bit in range(7, -1, -1):
            if pos == size:
                break
            best_distance, best_size = 0, 0
            for distance in range(min_distance, min(pos, 4096) + 1):
                length = 0
                while length < 18 and pos + length < size and raw[pos - distance + length] == raw[pos + length]:
                    length += 1
                if length > best_size:
                    best_distance, best_size = distance, length
                    if length == 18:
                        break
            if best_size >= 3:
                out[flag_at] |= 1 << bit
                out.extend((((best_size - 3) << 4) | ((best_distance - 1) >> 8), (best_distance - 1) & 255))
                pos += best_size
            else:
                out.append(raw[pos])
                pos += 1
    consumed = bytes(out)
    return consumed, consumed + b'\0' * (-len(consumed) % 4)


def diploma_asset(sources):
    """sourceだけで完全assetを生成し、独立identityへ束縛。ROMは一切参照しない。"""
    bindings = bind_sources(sources)
    tiles = encode_diploma_tiles(sources[PNG])
    need(identity(tiles) == DECODED, 'source-derived whole Diploma tiles')
    consumed, padded = encode_lz10(tiles)
    need(identity(consumed) == CONSUMED, 'source-derived exact consumed Diploma LZ')
    need(len(padded) == 3368 and padded[len(consumed):] == b'\0\0', 'two excluded terminal padding bytes')
    return {'tiles': tiles, 'consumed': consumed, 'padded': padded,
            'decoded_identity': identity(tiles), 'consumed_identity': identity(consumed),
            'padded_identity': identity(padded), 'source_bindings': bindings}


if __name__ == '__main__':
    result = diploma_asset(load_sources())
    print(json.dumps({k: result[k] for k in ('decoded_identity', 'consumed_identity', 'padded_identity')},
                     ensure_ascii=False, sort_keys=True))
