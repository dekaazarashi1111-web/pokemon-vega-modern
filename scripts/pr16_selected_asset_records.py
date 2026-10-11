#!/usr/bin/env python3
"""保存逆参照の整列2起点だけを構造体/table候補へ接続する。"""
from __future__ import annotations
import struct
import pr16_selected_asset_xrefs as x
import pr16_selected_map_asset as abi

BASE_HEAD = 'b804c42ea8556d9f76931802d30254dc801b7edc'
ORIGINS = (0x095FE848, 0x09673660)
TARGETS = (0x0880F004, 0x0880EFD0)
CANDIDATE, HIT = x.CANDIDATE, x.HIT
identity, encode, need = x.identity, x.encode, x.need
BASE = x.ROM_BASE


def word(raw, address):
    return struct.unpack('<I', x.section(raw, BASE, address, 4))[0]


def rom_pointer(value):
    return type(value) is int and BASE <= value < 0x0E000000


def pointer_run(raw, origin, half_window=256):
    """ROM pointerの連続形。非pointer境界もABI/table終端とは断定しない。"""
    need(origin % 4 == 0 and type(half_window) is int and 4 <= half_window <= 1024 and half_window % 4 == 0, 'pointer窓/整列')
    need(rom_pointer(word(raw, origin)), '起点pointer形')
    low, high = max(BASE, origin-half_window), min(BASE+len(raw), origin+half_window+4)
    start, end = origin, origin+4
    while start > low and rom_pointer(word(raw, start-4)):
        start -= 4
    while end+4 <= high and rom_pointer(word(raw, end)):
        end += 4
    return dict(start=start,end_exclusive=end,origin_index=(origin-start)//4,
        lower_window_exhausted=start==low,upper_window_exhausted=end==high,
        identity=identity(x.section(raw,BASE,start,end-start)),
        words=[dict(address=at,target=word(raw,at),canonical_target=x.canonical(word(raw,at))) for at in range(start,end,4)],
        actual_table_extent_proven=False)


def pointer_neighborhood(raw, origin, radius=64):
    need(origin%4==0 and type(radius) is int and 0<radius<=256 and radius%4==0, '周辺窓')
    low, high = max(BASE,origin-radius), min(BASE+len(raw),origin+radius+4)
    return dict(start=low,end_exclusive=high,identity=identity(x.section(raw,BASE,low,high-low)),
        pointer_words=[dict(address=at,target=word(raw,at),canonical_target=x.canonical(word(raw,at)))
            for at in range(low,high-3,4) if rom_pointer(word(raw,at))])


def record_shapes(raw, origin, hit=HIT):
    need(type(origin) is int and origin%4==0, '構造体pointer整列')
    target=word(raw,origin); need(rom_pointer(target), '構造体pointer範囲')
    result=[]
    for field,offset in ((key,abi.LAYOUT[key]) for key in abi.DATA_FIELDS):
        start=origin-offset
        try:
            row=abi.tileset(raw,start,abi.LAYOUT)
        except ValueError:
            continue
        callback=row['callback']
        if not row['invalid_data_fields'] and row['compression_byte'] in (0,1) and row['secondary_byte'] in (0,1,2) and (callback==0 or rom_pointer(callback)):
            result.append(dict(kind='TILESET_DESCRIPTOR_SHAPE',start=start,pointer_field=field,
                descriptor=row,actual_reader_proven=False,asset_extent_proven=False))
    for field,offset in (('border',8),('map',12),('primary',16),('secondary_tileset',20)):
        start=origin-offset
        try:
            row=abi.map_layout(raw,start)
            x.section(raw,BASE,row['border'],2)
            for key in ('primary','secondary_tileset'):
                if abi.tileset(raw,row[key],abi.LAYOUT)['invalid_data_fields']:
                    raise ValueError('descriptor')
        except ValueError:
            continue
        result.append(dict(kind='MAP_LAYOUT_SHAPE',start=start,pointer_field=field,layout=row,
            hit_inside_map_extent=abi.contains(row['map'],row['width']*row['height']*2,hit),actual_reader_proven=False))
    # SpriteSheet / SpritePaletteは同じ8byte外形。size/tag値だけで採用せず候補として残す。
    data=x.section(raw,BASE,origin,8)
    size,tag=struct.unpack_from('<HH',data,4)
    if 0<size<=32768 and size%32==0:
        try:
            x.section(raw,BASE,x.canonical(target),size)
            result.append(dict(kind='SPRITE_SHEET_SHAPE',start=origin,pointer=target,size=size,tag=tag,
                identity=identity(data),hit_inside_declared_extent=abi.contains(x.canonical(target),size,hit),actual_reader_proven=False))
        except ValueError:
            pass
    # WaveDataのフィールドを宣言順で読む。PCM byte列は公開せずextent条件だけを保存する。
    normalized=x.canonical(target)
    try:
        wave=x.section(raw,BASE,normalized,16)
        type_flags,status,freq,loop_start,sample_count=struct.unpack('<HHIII',wave)
        if type_flags in (0,1) and 0<freq<=0x4000000 and 0<sample_count<=0x200000 and loop_start<sample_count:
            x.section(raw,BASE,normalized+16,sample_count)
            result.append(dict(kind='WAVE_DATA_SHAPE',start=normalized,type_flags=type_flags,status=status,
                frequency=freq,loop_start=loop_start,sample_count=sample_count,header_identity=identity(wave),
                hit_inside_samples=abi.contains(normalized+16,sample_count,hit),actual_reader_proven=False))
    except ValueError:
        pass
    return result


def validate_saved(saved):
    need(type(saved) is dict and saved['candidate']==CANDIDATE and saved['origin']==dict(address=HIT,**x.HIT_ID), '逆参照候補identity')
    need(saved['first_level_count']==len(saved['first_level'])==11 and saved['second_level_count']==1 and
         saved['literal_shape_count']==0 and saved['formal_classification_changes']==0, '保存逆参照閉集合')
    rows=[r for r in saved['first_level'] if r['address']%4==0]
    need(tuple(r['address'] for r in rows)==ORIGINS and tuple(r['canonical_target'] for r in rows)==TARGETS, '保存整列2件だけ')
    return rows


def measure(raw, symbols, saved):
    need(identity(raw)==CANDIDATE and identity(x.section(raw,BASE,HIT,4))==x.HIT_ID, '候補全SHA/選定4byte')
    rows=validate_saved(saved); index=x.symbol_index(symbols)
    inspections=[]; bases=set()
    excluded={r['address'] for r in saved['first_level']}
    for row in rows:
        origin=row['address']
        need(identity(x.section(raw,BASE,origin,4))==dict(size=4,sha256=row['sha256']) and word(raw,origin)==row['target'], '保存pointer全4byte')
        run=pointer_run(raw,origin);shapes=record_shapes(raw,origin)
        nearby=pointer_neighborhood(raw,origin)
        # 実record strideが未確定なので、前64byteの整列した各baseを有限候補にする。
        starts=set(range(origin-64,origin+1,4))|{run['start']}|{r['start'] for r in shapes}
        starts={n for n in starts if BASE<=n<BASE+len(raw)}
        bases.update(starts-excluded)
        inspections.append(dict(origin=origin,target=row['canonical_target'],pointer_run=run,record_shapes=shapes,
            neighborhood=nearby,base_candidates=sorted(starts),owner_identified=False))
    refs=[]
    for start in sorted(bases):
        hits=x.inverse_pointers(raw,BASE,start,start+1)
        for row in hits:
            row['public_neighborhood']=x.neighborhood(index,row['address'])
            row['thumb_literal_shapes']=x.literal_shapes(raw,BASE,row['address'])
            for shape in row['thumb_literal_shapes']:
                shape['public_neighborhood']=x.neighborhood(index,shape['address'])
        if hits:refs.append(dict(base_candidate=start,references=hits))
    return dict(schema_version=1,candidate=CANDIDATE,origin=dict(address=HIT,**x.HIT_ID),
        saved_xrefs_identity=identity(encode(saved)),inspections=inspections,base_references=refs,
        new_base_candidates=sorted(bases),new_base_reference_passes=len(bases),
        base_reference_count=sum(len(r['references']) for r in refs),
        literal_shape_count=sum(len(h['thumb_literal_shapes']) for r in refs for h in r['references']),
        accepted_xref_passes_replayed=0,accepted_test_reruns=0,map_probe_reruns=0,prior_lz_search_reruns=0,
        formal_classification_changes=0,formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        owner_identified=False,actual_asset_reader_proven=False,
        limitations_ja=['2起点の前64byte整列baseと連続pointer形開始だけの有限探索。全table基点の網羅ではない。',
            '構造体/命令の形は実readerの証明ではない。外形だけで正式型や安全容量を変更しない。',
            '新規baseへの逆参照だけを全ROM入力から検索。旧11起点の第2段検索、map、LZ、Wikiは再走しない。'])
