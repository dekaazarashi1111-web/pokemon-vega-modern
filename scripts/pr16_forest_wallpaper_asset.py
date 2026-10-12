#!/usr/bin/env python3
"""固定公開Forest PNGとLZ10全体の証明。実entry/heap/BIOS受入とは分離する。"""
from __future__ import annotations
import hashlib
import struct
import zlib
import pr16_capacity_08397492 as binding

need, identity, encode, exact = binding.need, binding.identity, binding.encode, binding.exact
BASE, ASSET, HIT = 0x08000000, 0x08397188, binding.TARGET
PNG = 'graphics/pokemon_storage/wallpapers/forest/tiles.png'
COMMIT = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
PNG_ID = {'size':721,'sha256':'fc8f20243a1dd2fbcbd86647e77395c84a428689c2c25918152d6c9525969aed'}
TILES_ID = {'size': 1696, 'sha256': '004a48f42202841373162e9732de13007725da29ad997429386cbccf0461a2ea'}
BLOBS = {PNG:'e305ce6079ded5576600ecc7c70fe919fdc6c297',
 'src/pokemon_storage_system_graphics.c':'046f82d9c6178d9457ee2e63c8952310fc96b93a',
 'tools/gbagfx/lz.c':'97434ce506dec319f0a76c54494fa2e60894be7d',
 'tools/gbagfx/main.c':'0dba4c8aea0bec7a3f407ae3aee570e8e88a6834',
 'tools/gbagfx/gfx.c':'1dfc38e2d0362cb8224f67f057f68ee7120dce9f',
 'tools/gbagfx/convert_png.c':'58371229c06d0c036a23d55ffcbf5761d0089800',
 'Makefile':'8b454dbd18eb0069fa5851d788697190890a5b37',
 'graphics_file_rules.mk':'39b952cd45b6a34eb98318a76aa531fcafff134d'}
CLAIMS = {'formal_classification_accepted':False,'actual_entry_executed':False,
 'actual_heap_allocation_observed':False,'actual_bios_executed':False,
 'actual_dma_or_screen_observed':False,'indirect_reference_completeness_claimed':False,
 'donor_eligible':False,'donor_leased':False,'donor_safe_bytes':0,'newly_classified':0,
 'accepted_reader_replays':0,'accepted_test_reruns':0,'native_processes':0,
 'formal_rom_changed':False,'formal_save_changed':False}


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def paeth(a,b,c):
    p=a+b-c; d=(abs(p-a),abs(p-b),abs(p-c))
    return (a,b,c)[d.index(min(d))]


def indexed8(raw):
    """この新assetに必要なindexed8だけ。CRC/全filter/展開上限/余剰を閉じる。"""
    need(type(raw) is bytes and len(raw)<=100000 and raw[:8]==b'\x89PNG\r\n\x1a\n','PNG signature/size')
    at=8; header=None; palette=None; parts=[]; ended=False; after_idat=False
    while at<len(raw):
        need(at+12<=len(raw),'PNG chunk header')
        n=int.from_bytes(raw[at:at+4],'big');tag=raw[at+4:at+8];end=at+12+n
        need(end<=len(raw),'PNG whole chunk')
        data=raw[at+8:at+8+n]
        need(zlib.crc32(tag+data)&0xffffffff==int.from_bytes(raw[at+8+n:end],'big'),'PNG CRC')
        if header is None:
            need(tag==b'IHDR' and n==13,'IHDR first')
            header=struct.unpack('>IIBBBBB',data)
            need(header==(64,56,8,3,0,0,0),'Forest geometry/indexed8')
        elif tag==b'IHDR':raise ValueError('duplicate IHDR')
        elif tag==b'PLTE':
            need(palette is None and not parts and 3<=n<=768 and n%3==0,'palette extent/order')
            palette=n//3
        elif tag==b'IDAT':
            need(palette is not None and not after_idat,'contiguous IDAT after palette')
            parts.append(data)
        elif tag==b'IEND':
            need(n==0 and parts and end==len(raw),'terminal IEND')
            ended=True
        else:
            need(len(tag)==4 and all(65<=x<=90 or 97<=x<=122 for x in tag)
                 and tag[0]&32 and not tag[2]&32,'supported ancillary chunk')
            if parts:after_idat=True
        at=end
        if ended:break
    need(ended,'complete PNG')
    stream=zlib.decompressobj()
    try:scan=stream.decompress(b''.join(parts),65*56+1)
    except zlib.error as exc:raise ValueError('PNG zlib') from exc
    need(stream.eof and not stream.unused_data and not stream.unconsumed_tail and len(scan)==65*56,'one bounded PNG stream')
    pixels=bytearray();prev=bytes(64)
    for y in range(56):
        f=scan[y*65];need(f<=4,'PNG filter')
        row=bytearray(scan[y*65+1:(y+1)*65])
        for x in range(64):
            left=row[x-1] if x else 0;above=prev[x];corner=prev[x-1] if x else 0
            row[x]=(row[x]+(0,left,above,(left+above)//2,paeth(left,above,corner))[f])&255
        need(all(p<palette for p in row),'palette index')
        pixels.extend(row);prev=row
    return bytes(pixels)


def pack_tiles(pixels):
    need(type(pixels) is bytes and len(pixels)==64*56,'whole Forest pixels')
    # Public convert_png.c truncates each 8-bit palette index to its low nibble for 4bpp.
    return bytes((pixels[(ty+y)*64+tx+x]&15)|((pixels[(ty+y)*64+tx+x+1]&15)<<4)
        for ty in range(0,56,8) for tx in range(0,64,8) for y in range(8) for x in range(0,8,2))


def forest_tiles(pixels):
    whole=pack_tiles(pixels)
    need(not any(whole[53*32:]), "public build rule truncates only three blank tiles")
    return whole[:53*32]


def compress(raw):
    """gbagfx LZCompressの既定minDistance=2、最長一致/近距離優先を独立実装。"""
    need(type(raw) is bytes and 0<len(raw)<=8192,'bounded tiles')
    out=bytearray(b'\x10'+len(raw).to_bytes(3,'little'));pos=0
    while pos<len(raw):
        flag=len(out);out.append(0)
        for bit in range(8):
            if pos==len(raw):break
            best=0;distance=0
            for d in range(2,min(pos,4096)+1):
                size=0
                while size<18 and pos+size<len(raw) and raw[pos-d+size]==raw[pos+size]:size+=1
                if size>best:best,distance=size,d
                if size==18:break
            if best>=3:
                out[flag]|=128>>bit;d=distance-1
                out.extend((((best-3)<<4)|(d>>8),d&255));pos+=best
            else:out.append(raw[pos]);pos+=1
    consumed=bytes(out);out.extend(bytes((-len(out))%4))
    return consumed,bytes(out)


def decode(raw):
    """全消費tokenと展開を返す。BIOS実行ではない。過剰出力/前方参照を拒否。"""
    need(type(raw) is bytes and 4<=len(raw)<=16384 and raw[0]==16,'LZ10 header')
    size=int.from_bytes(raw[1:4],'little');need(0<size<=8192,'LZ output bound')
    out=bytearray();at=4;tokens=[{'offset':0,'size':4,'kind':'header','output_start':0,'output_size':0}]
    while len(out)<size:
        need(at<len(raw),'LZ flags');flags=raw[at]
        tokens.append({'offset':at,'size':1,'kind':'flags','output_start':len(out),'output_size':0});at+=1
        for bit in range(8):
            if len(out)==size:break
            begin=at;start=len(out)
            if flags&(128>>bit):
                need(at+2<=len(raw),'LZ complete reference')
                count=(raw[at]>>4)+3;distance=((raw[at]&15)<<8|raw[at+1])+1;at+=2
                need(distance<=len(out) and len(out)+count<=size,'LZ reference/overrun')
                for _ in range(count):out.append(out[-distance])
                kind='backreference_length_distance'
            else:
                need(at<len(raw),'LZ literal');out.append(raw[at]);at+=1;kind='literal_palette_indices'
            tokens.append({'offset':begin,'size':at-begin,'kind':kind,'output_start':start,'output_size':len(out)-start})
    need(len(raw)==at or len(raw)==((at+3)&~3),'LZ only alignment tail')
    need(not any(raw[at:]),'LZ nonzero alignment tail')
    return bytes(out),at,tokens


def independent(png):
    need(exact(identity(png),PNG_ID) and blob(png)==BLOBS[PNG],'fixed whole Forest PNG')
    pixels=indexed8(png);tiles=forest_tiles(pixels)
    need(exact(identity(tiles),TILES_ID),'source-derived whole tiles')
    consumed,padded=compress(tiles);decoded,used,tokens=decode(padded)
    need(decoded==tiles and used==len(consumed),'LZ round trip/extent')
    return pixels,tiles,consumed,padded,tokens


def source_bindings(sources):
    need(type(sources) is dict and set(sources)==set(BLOBS),'closed public sources')
    for name,expected in BLOBS.items():need(blob(sources[name])==expected,'fixed public blob: '+name)
    text=sources['src/pokemon_storage_system_graphics.c'].decode()
    for token in ('sWallpaperTiles_Forest[] = INCBIN_U32("graphics/pokemon_storage/wallpapers/forest/tiles.4bpp.lz")',
        '{sWallpaperTiles_Forest,     sWallpaperTilemap_Forest,     *sWallpaperPalettes_Forest',
        'wallpaper = &sWallpapers[wallpaperId];',
        'DecompressAndLoadBgGfxUsingHeap(2, wallpaper->tiles, 0, 256 * gStorage->wallpaperOffset, 0);'):
        need(token in text,'source declaration/consumer changed')
    need('$(WALLPAPERGFXDIR)/forest/tiles.4bpp: %.4bpp: %.png\n\t$(GFX) $< $@ -num_tiles 53 -Wnum_tiles' in sources['graphics_file_rules.mk'].decode(),'exact Forest 53 tiles build rule')
    need('int minDistance = 2;' in sources['tools/gbagfx/main.c'].decode(),'LZ default')
    return {name:{'repository':'pret/pokefirered','commit':COMMIT,'path':name,'git_blob':BLOBS[name],**identity(raw)} for name,raw in sorted(sources.items())}


def symbol_rows(raw):
    binding.bind_symbols(raw)
    wanted={'sWallpapers','sWallpaperTiles_Forest','sWallpaperTilemap_Forest','sWallpaperPalettes_Forest',
        'LoadWallpaperGfx','DecompressAndLoadBgGfxUsingHeap','LZ77UnCompWram'}
    found={}
    for line in raw.decode().splitlines():
        row=line.split('\t')
        if len(row)==8 and row[4] in wanted:
            need(row[4] not in found,'unique public symbol');found[row[4]]=row
    need(set(found)==wanted,'whole named JP symbol set')
    need(int(found['sWallpaperTiles_Forest'][1],16)==ASSET,'fixed JP tiles start')
    return found


def measure(raw, png, rows):
    need(exact(identity(raw),binding.CANDIDATE),'exact whole capacity candidate')
    _,tiles,consumed,padded,tokens=independent(png)
    start=ASSET-BASE
    need(raw[start:start+len(padded)]==padded,'whole independent compressed asset equals current ROM')
    target=HIT-ASSET
    need(4<=target and target+4<=len(consumed),'all target bytes consumed, not alignment')
    need(exact(identity(consumed[target:target+4]),{'size':4,'sha256':binding.HIT['sha256']}),'saved target hash')
    table=int(rows['sWallpapers'][1],16)
    need(BASE<=table<=BASE+len(raw)-12 and table%4==0,'JP table range')
    expected=tuple(int(rows[name][1],16) for name in ('sWallpaperTiles_Forest','sWallpaperTilemap_Forest','sWallpaperPalettes_Forest'))
    need(struct.unpack_from('<III',raw,table-BASE)==expected,'actual complete Forest table tuple')
    selected=[dict(t,address=ASSET+t['offset'],sha256=identity(consumed[t['offset']:t['offset']+t['size']])['sha256'])
              for t in tokens if t['offset']<target+4 and target<t['offset']+t['size']]
    covered={x for t in selected for x in range(t['offset'],t['offset']+t['size'])}
    need(set(range(target,target+4))<=covered,'four bytes have complete LZ token coverage')
    actual=raw[start:start+len(padded)];decoded,used,_=decode(actual)
    need(decoded==tiles and used==len(consumed),'actual candidate stream decodes whole independently fixed tiles')
    return {'status':'PASS_FOREST_WHOLE_ASSET_TABLE_AND_LZ_TOKENS_ONLY',
        'candidate':dict(binding.CANDIDATE),'asset':{'address':ASSET,**identity(padded)},
        'consumed':{'address':ASSET,**identity(consumed)},'decoded':identity(decoded),
        'target':dict(binding.HIT),'target_tokens':selected,'table':{'address':table,**identity(raw[table-BASE:table-BASE+12])},
        'table_entry_index':0,'alignment_bytes':len(padded)-len(consumed),'claims':dict(CLAIMS),
        'entry_to_heap_to_bios_contract':'NOT_PROVEN; source calls and actual tuple do not prove actual entry/control/lifetime',
        'inherited_classified':784,'inherited_unclassified':90}
