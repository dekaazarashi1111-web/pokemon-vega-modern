#!/usr/bin/env python3
"""固定公開Blastoise画像の完全LZ10型。ROM入力・探索・既受入再走はない。"""
from __future__ import annotations

import copy
import json
import struct
import zlib
from pathlib import Path

# 既受入を呼ばず、ROM非依存の純関数だけを再利用する。
from pr16_dex_hof_diploma_sources import encode_lz10, git_blob, identity, need, paeth

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local/jp-blastoise-sources'
COMMIT = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
PNG = 'graphics/credits/blastoise_1.png'
DECODED = {'size': 3200, 'sha256': '53555d2564544f36b20a1100c372fd16e6a4eab1e62f58a2a87b02dae97ab068'}
CONSUMED = {'size': 1794, 'sha256': '795833f5dc50f7eeb6bc69b851d2ea3cdebe18ee6c8ec35e3b708ca1113dea01'}
PADDED = {'size': 1796, 'sha256': 'a183b4a4cc7e541e1d343f0e1d4f57ed0cece0471332b7a2ecafca2feae04d92'}
JP_AUDIT = 'diagnostics/pokefirered_jp.sym.audit.tsv'
JP_METADATA = 'diagnostics/pokefirered_jp.sym.metadata.tsv'
# auditのreference sizeはJP extentの根拠ではない。extentはPNGから独立生成する。
JP_ROWS = ('020204b4\t02020430\tg\t00000180\tgWindows\trelocated_pointer_or_call\t96\t0',
 '080017e4\t080017d0\tg\t000000b8\tLoadBgTiles\tunique_normalized_code\t98\t1',
 '08003b38\t08003af0\tg\t000001c0\tInitWindows\tunique_normalized_code\t98\t1',
 '08003f34\t08003eec\tg\t0000007e\tCopyWindowToVram\tunique_normalized_code\t98\t1',
 '08004418\t080043d0\tg\t00000058\tCopyToWindowPixelBuffer\tunique_normalized_code\t98\t1',
 '080f421c\t080f5208\tl\t0000014c\tLoadCreditsMonPic\tunique_normalized_code\t98\t1',
 '080f43a0\t080f538c\tl\t0000034a\tDoCreditsMonScene\tunique_normalized_code\t98\t1',
 '081e3be0\t081c7a90\tg\t00000004\tLZ77UnCompWram\trelocated_pointer_or_call\t96\t1',
 '0840c660\t083d27c8\tl\t00000020\tsWindowTemplates_Blastoise\tunique_normalized_data\t98\t1',
 '0840f2b0\t083d655c\tl\t00000704\tsBlastoise1_Tiles\tunique_normalized_data\t98\t1')

# 固定公開source全文identity。可変manifestやROMから採取しない。
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
 'graphics/credits/blastoise_1.png': {'cache_name': 'pret-graphics_credits_blastoise_1.png',
                                      'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                      'git_blob': 'b212fbcc1930bb066b1999bc4cb19de110befcbf',
                                      'path': 'graphics/credits/blastoise_1.png',
                                      'repository': 'pret/pokefirered',
                                      'sha256': '518f6637243fe88ac58e522a2e7b8133b49531d9faf64ad6ee78d63244f57673',
                                      'size': 1348,
                                      'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/graphics/credits/blastoise_1.png'},
 'graphics_file_rules.mk': {'cache_name': 'pret-graphics_file_rules.mk',
                            'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                            'git_blob': '39b952cd45b6a34eb98318a76aa531fcafff134d',
                            'path': 'graphics_file_rules.mk',
                            'repository': 'pret/pokefirered',
                            'sha256': 'bd56e518ab9527f844642230673ce27a5bae73c7208d917d3288b073859fb685',
                            'size': 14859,
                            'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/graphics_file_rules.mk'},
 'include/window.h': {'cache_name': 'pret-include_window.h',
                      'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                      'git_blob': 'f64adce251582e0752128ddc00891661b9207168',
                      'path': 'include/window.h',
                      'repository': 'pret/pokefirered',
                      'sha256': '86539c82ace8392589a5f80c137b5c4bd5ef710b90cedcb1726ea9dc8ada9edf',
                      'size': 2989,
                      'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/include/window.h'},
 'src/bg.c': {'cache_name': 'pret-src_bg.c',
              'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
              'git_blob': 'aa11ae01f87242edecc5656bb6649b04e319357a',
              'path': 'src/bg.c',
              'repository': 'pret/pokefirered',
              'sha256': '4813ff7fb1b9bcc952d3973d05a46d31c9fee57342c7957165a76a136ccd57da',
              'size': 31836,
              'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/bg.c'},
 'src/credits.c': {'cache_name': 'pret-src_credits.c',
                   'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                   'git_blob': '8f89652a0f864ae4fcacd67cccff3a4d3441f350',
                   'path': 'src/credits.c',
                   'repository': 'pret/pokefirered',
                   'sha256': '96690b500af63cc588b2ca8060f4af5b1a69a99797870099831d77a32027af25',
                   'size': 50032,
                   'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/credits.c'},
 'src/libagbsyscall.s': {'cache_name': 'pret-src_libagbsyscall.s',
                         'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                         'git_blob': '61c23feb497ade0742be6845be7d5716574f54cc',
                         'path': 'src/libagbsyscall.s',
                         'repository': 'pret/pokefirered',
                         'sha256': '6d183afe7a31976b1e301dac4f2926df9e251a636cd2a197f56bc8296dc46e78',
                         'size': 1358,
                         'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/libagbsyscall.s'},
 'src/window.c': {'cache_name': 'pret-src_window.c',
                  'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                  'git_blob': '834f13a8c9f4b5dbf5f5c278004f5fe5d9ff0ca2',
                  'path': 'src/window.c',
                  'repository': 'pret/pokefirered',
                  'sha256': '223a0ff33a3d4c92dc25d18ab2022d32e7e06d8c0e2fbf02c3cc111cbb0a2352',
                  'size': 15783,
                  'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/window.c'},
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

SOURCE_TOKENS = {
    'src/credits.c': (
        'enum CreditsMon\n{\n    CREDITSMON_CHARIZARD = 0,\n    CREDITSMON_VENUSAUR,\n    CREDITSMON_BLASTOISE,\n    CREDITSMON_PIKACHU\n};',
        'static const u32 sBlastoise1_Tiles[] = INCBIN_U32("graphics/credits/blastoise_1.4bpp.lz");',
        'static const struct WindowTemplate sWindowTemplates_Blastoise[] = {\n    {\n        .bg = 0,\n        .tilemapLeft = 11,\n        .tilemapTop = 6,\n        .width = 8,\n        .height = 8,\n        .paletteNum = 10,\n        .baseBlock = 0x0008\n    }, {\n        .bg = 0,\n        .tilemapLeft = 10,\n        .tilemapTop = 5,\n        .width = 10,\n        .height = 10,\n        .paletteNum = 10,\n        .baseBlock = 0x0048',
        'case CREDITSMON_BLASTOISE:\n        InitWindows(sWindowTemplates_Blastoise);\n        FillWindowPixelBuffer(0, PIXEL_FILL(0));\n        LoadMonPicInWindow(SPECIES_BLASTOISE, SHINY_ODDS, 0, TRUE, 10, 0);\n        CopyToWindowPixelBuffer(1, (const void *)sBlastoise1_Tiles, 0, 0);',
        'LoadCreditsMonPic(sCreditsMgr->whichMon);',
        'CopyWindowToVram(1, COPYWIN_GFX);'),
    'src/window.c': (
        'EWRAM_DATA struct Window gWindows[WINDOWS_MAX] = {0};',
        'allocatedTilemapBuffer = Alloc((u16)(0x20 * (templates[i].width * templates[i].height)));',
        'gWindows[i].tileData = allocatedTilemapBuffer;',
        'gWindows[i].window = templates[i];',
        'void CopyToWindowPixelBuffer(u8 windowId, const void *src, u16 size, u16 tileOffset)\n{\n    if (size != 0)\n        CpuCopy16(src, gWindows[windowId].tileData + (0x20 * tileOffset), size);\n    else\n        LZ77UnCompWram(src, gWindows[windowId].tileData + (0x20 * tileOffset));\n}',
        'u16 windowSize = 32 * (windowLocal.window.width * windowLocal.window.height);',
        'case COPYWIN_GFX:\n            LoadBgTiles(windowLocal.window.bg, windowLocal.tileData, windowSize, windowLocal.window.baseBlock);'),
    'include/window.h': (
        'struct WindowTemplate\n{\n    u8 bg;\n    u8 tilemapLeft;\n    u8 tilemapTop;\n    u8 width;\n    u8 height;\n    u8 paletteNum;\n    u16 baseBlock;\n};',
        'struct Window\n{\n    struct WindowTemplate window;\n    u8 *tileData;\n};',
        '#define WINDOWS_MAX 32',
        'COPYWIN_NONE,\n    COPYWIN_MAP,\n    COPYWIN_GFX,\n    COPYWIN_FULL,'),
    'src/libagbsyscall.s': ('LZ77UnCompWram:\n\tsvc 0x11\n\tbx lr',),
    'src/bg.c': ('u16 LoadBgTiles(u8 bg, const void *src, u16 size, u16 destOffset)',
                 'cursor = LoadBgVram(bg, src, size, tileOffset, DISPCNT_MODE_1);'),
    'Makefile': ('%.4bpp:   %.png  ; $(GFX) $< $@', '%.lz:     %      ; $(GFX) $< $@'),
    'tools/gbagfx/main.c': ('int minDistance = 2;', 'options.metatileWidth = 1;',
                           'options.metatileHeight = 1;', 'options.numTilesMode = NUM_TILES_IGNORE;',
                           'WriteTileImage(outputPath, options->numTilesMode, options->numTiles, options->metatileWidth, options->metatileHeight, &image, !image.hasPalette);'),
    'tools/gbagfx/convert_png.c': ('image->hasPalette = (color_type == PNG_COLOR_TYPE_PALETTE);',
                                  'png_read_image(png_ptr, row_pointers);',
                                  'if (bit_depth != image->bitDepth && image->tilemap.data.affine == NULL)'),
    'tools/gbagfx/gfx.c': ('unsigned char leftPixel = srcPixelPair >> 4;',
                         'unsigned char rightPixel = srcPixelPair & 0xF;',
                         '*dest++ = (rightPixel << 4) | leftPixel;'),
    'tools/gbagfx/lz.c': ('dest[0] = 0x10;', 'if (blockSize > bestBlockSize)',
                         'while (blockDistance <= srcPos && blockDistance <= 0x1000)'),
}


def bind_sources(sources):
    """閉じた14sourceとJP対応行・実sourceのcaller/ABIを固定する。"""
    need(type(sources) is dict and set(sources) == set(SOURCE_IDS), 'closed Blastoise source set')
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
                       'size_policy': 'reference size retained; not a verified localized extent',
                       'confidence_policy': 'evidence ranks, not statistical probabilities'}.items():
        need(metadata.get(key) == value, 'JP metadata binding: ' + key)
    return copy.deepcopy(SOURCE_IDS)


def load_sources(cache_dir=CACHE):
    """cacheを読むだけ。network/生成/ROMへのfallbackはしない。"""
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


def png_pixels(raw):
    """bounded indexed4 PNG。packed byte上で全filter復元後、左の高nibbleから展開。"""
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
            need((depth, color, compression, filtering, interlace) == (4, 3, 0, 0, 0), 'indexed4 noninterlaced PNG')
        elif tag == b'IHDR':
            raise ValueError('duplicate IHDR')
        elif tag == b'PLTE':
            need(palette is None and not seen_idat and 3 <= length <= 48 and length % 3 == 0,
                 'single indexed4 palette before IDAT')
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
    row_bytes = (width + 1) // 2
    expected_size = height * (row_bytes + 1)
    stream = zlib.decompressobj()
    try:
        scanlines = stream.decompress(b''.join(pieces), expected_size + 1)
    except zlib.error as exc:
        raise ValueError('invalid PNG zlib stream') from exc
    need(stream.eof and not stream.unused_data and not stream.unconsumed_tail and len(scanlines) == expected_size,
         'one bounded complete PNG zlib stream')
    pixels = bytearray()
    previous = bytearray(row_bytes)
    for y in range(height):
        row_at = y * (row_bytes + 1)
        filter_type = scanlines[row_at]
        need(filter_type <= 4, 'PNG filter type')
        row = bytearray(scanlines[row_at + 1:row_at + 1 + row_bytes])
        for x in range(row_bytes):
            left, above = row[x - 1] if x else 0, previous[x]
            upper_left = previous[x - 1] if x else 0
            predictor = (0, left, above, (left + above) // 2, paeth(left, above, upper_left))[filter_type]
            row[x] = (row[x] + predictor) & 255
        indices = bytes((row[x // 2] >> (4 if x % 2 == 0 else 0)) & 15 for x in range(width))
        need(all(index < palette for index in indices), 'pixel outside indexed palette')
        pixels.extend(indices)
        previous = row
    return width, height, bytes(pixels)


def encode_blastoise_tiles(png):
    """80×80の全100tileを1×1 metatile順、GBAの左low/right highで復元する。"""
    width, height, pixels = png_pixels(png)
    need((width, height) == (80, 80), 'whole Blastoise PNG geometry')
    return bytes(pixels[(ty + y) * width + tx + x]
                 | (pixels[(ty + y) * width + tx + x + 1] << 4)
                 for ty in range(0, height, 8) for tx in range(0, width, 8)
                 for y in range(8) for x in range(0, 8, 2))


def blastoise_asset(sources):
    """公開sourceだけから完全assetを生成。現candidate一致は別gate。"""
    bindings = bind_sources(sources)
    tiles = encode_blastoise_tiles(sources[PNG])
    need(identity(tiles) == DECODED, 'source-derived whole Blastoise tiles')
    consumed, padded = encode_lz10(tiles)
    need(identity(consumed) == CONSUMED, 'source-derived exact consumed Blastoise LZ')
    need(identity(padded) == PADDED and padded[len(consumed):] == b'\0\0', 'two excluded terminal padding bytes')
    return {'tiles': tiles, 'consumed': consumed, 'padded': padded,
            'decoded_identity': identity(tiles), 'consumed_identity': identity(consumed),
            'padded_identity': identity(padded), 'source_bindings': bindings}


if __name__ == '__main__':
    result = blastoise_asset(load_sources())
    print(json.dumps({k: result[k] for k in ('decoded_identity', 'consumed_identity', 'padded_identity')},
                     ensure_ascii=False, sort_keys=True))
