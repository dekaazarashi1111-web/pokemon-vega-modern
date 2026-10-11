#!/usr/bin/env python3
"""固定公開PNGからbubble64byteを独立生成する。既受入検証・ROM探索なし。"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from pr16_dex_hof_blastoise_sources import png_pixels

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local/weather-bubble-sources'
LOCK = 'content/modernization/pr16_weather_bubble_sources.json'
PNG = 'graphics/weather/bubble.png'
ASSET_ID = {'size': 64, 'sha256': 'fbf6491632f1aa7b1b2c827a23cb77c22e1e675976be827b443d64992acdb1e7'}
COMMIT = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
HEADER = {'repository': 'pret/pokefirered', 'commit': COMMIT,
          'path': 'include/field_weather.h', 'git_blob': 'c3c07d10d70b2f8b46dee954ab6428ffab076ca8'}
SYMBOLS = {'AllocSpriteTiles': 0x08006FB0, 'LoadSpriteSheet': 0x08008258,
           'AllocSpriteTileRange': 0x08008424, 'FogHorizontal_InitVars': 0x0807C060,
           'Bubbles_InitVars': 0x0807D034, 'CpuSet': 0x081C7A88,
           'gWeatherPtr': 0x08389940, 'gWeatherBubbleTiles': 0x0838B304,
           'sWeatherBubbleSpriteSheet': 0x0838D5F4}
TOKENS = {
 'src/field_weather.c': ('const u8 gWeatherBubbleTiles[] = INCBIN_U8("graphics/weather/bubble.4bpp");',),
 'src/field_weather_effects.c': ('static const struct SpriteSheet sWeatherBubbleSpriteSheet =',
    '.data = gWeatherBubbleTiles,', '.size = 0x0040,', '.tag = GFXTAG_BUBBLE,',
    'void Bubbles_InitVars(void)', 'FogHorizontal_InitVars();',
    'if (!gWeatherPtr->bubblesSpritesCreated)', 'LoadSpriteSheet(&sWeatherBubbleSpriteSheet);'),
 'src/sprite.c': ('u16 LoadSpriteSheet(const struct SpriteSheet *sheet)',
    's16 tileStart = AllocSpriteTiles(sheet->size / TILE_SIZE_4BPP);',
    'if (tileStart < 0)', 'AllocSpriteTileRange(sheet->tag, (u16)tileStart, sheet->size / TILE_SIZE_4BPP);',
    'CpuCopy16(sheet->data, (u8 *)OBJ_VRAM0 + TILE_SIZE_4BPP * tileStart, sheet->size);'),
 'src/libagbsyscall.s': ('CpuSet:\n\tsvc 0xB\n\tbx lr',),
 'include/gba/syscall.h': ('#define CPU_SET_16BIT     0x00000000', '#define CPU_SET_32BIT     0x04000000'),
}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def source_ids():
    result = {}
    for path, (size, sha256, blob) in json.loads((ROOT / LOCK).read_bytes()).items():
        repo, commit = ('ComplexRobot/frlg-sym', 'c04a31542086b20d8c6ee641eaa70b8db6713fd3') if path.startswith('diagnostics/') else ('pret/pokefirered', COMMIT)
        result[path] = dict(size=size, sha256=sha256, git_blob=blob, path=path, repository=repo,
            commit=commit, cache_name=repo.replace('/', '_')+'__'+path.replace('/', '_'),
            url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+path)
    return result

def tiles(png):
    width, height, pixels = png_pixels(png)
    need((width, height) == (8, 16), 'bubble全画像8x16のみ')
    # GBA tile順: 上下8x8、左pixelはlow nibble。圧縮・paddingは存在しない。
    return bytes(pixels[(ty+y)*width+tx+x] | pixels[(ty+y)*width+tx+x+1] << 4
                 for ty in range(0, height, 8) for tx in range(0, width, 8)
                 for y in range(8) for x in range(0, 8, 2))

def bind_sources(sources):
    ids = source_ids()
    need(type(sources) is dict and set(sources) == set(ids), '公開sourceの閉集合')
    for path, row in ids.items():
        raw = sources[path]
        need(type(raw) is bytes and identity(raw) == {k: row[k] for k in ('size', 'sha256')}
             and git_blob(raw) == row['git_blob'], '独立固定source全体identity: ' + path)
    for path, tokens in TOKENS.items():
        text = sources[path].decode('utf-8')
        need(all(token in text for token in tokens), 'source意味束縛: ' + path)
    rows = sources['diagnostics/pokefirered_jp.sym.audit.tsv'].decode().splitlines()
    for name, address in SYMBOLS.items():
        found = [line.split('\t') for line in rows if '\t' + name + '\t' in line]
        need(len(found) == 1 and int(found[0][1], 16) == address, 'JP symbol候補の固定: ' + name)
    need(identity(tiles(sources[PNG])) == ASSET_ID, 'PNG独立生成64byte全体')
    return copy.deepcopy(ids)

def load_sources(directory=CACHE):
    directory = Path(directory).absolute()
    result = {}
    for path, row in source_ids().items():
        local = directory / row['cache_name']
        need(all(not part.is_symlink() for part in (local, *local.parents)), 'source symlink拒否')
        need(local.is_file() and local.stat().st_size == row['size'], 'source欠落/size不一致: ' + path)
        result[path] = local.read_bytes()
    bind_sources(result)
    return result

def download_sources():
    import urllib.request
    CACHE.mkdir(parents=True, exist_ok=True)
    for row in source_ids().values():
        path = CACHE / row['cache_name']
        if not path.exists():
            with urllib.request.urlopen(row['url'], timeout=90) as response:
                raw = response.read(row['size'] + 1)
            need(identity(raw) == {k: row[k] for k in ('size', 'sha256')} and git_blob(raw) == row['git_blob'],
                 '固定公開source取得identity')
            path.write_bytes(raw)
    source = load_sources()
    # struct/enumの追加一次資料は固定Git blobで独立認証。可変HEADを使わない。
    url = 'https://raw.githubusercontent.com/' + HEADER['repository'] + '/' + HEADER['commit'] + '/' + HEADER['path']
    with urllib.request.urlopen(url, timeout=90) as response:
        header = response.read(20001)
    need(len(header) <= 20000 and git_blob(header) == HEADER['git_blob'], 'Weather header完全Git blob')
    text = header.decode('utf-8')
    need('#define TAG_WEATHER_START 0x1200' in text and 'GFXTAG_BUBBLE,' in text and
         'bool8 bubblesSpritesCreated;' in text, 'tag/flagの一次source')
    return source, dict(HEADER, **identity(header), url=url)
