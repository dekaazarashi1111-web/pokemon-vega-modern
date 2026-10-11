#!/usr/bin/env python3
"""選定originの後継ABI/現map参照を限定検証する。旧探索原本は改作しない。"""
from __future__ import annotations
import hashlib
import json
import struct

BASE_HEAD = 'c0bbe4e2c1ada632a9de62aef42907be2edb6c28'
BASE = 0x08000000
HIT = 0x0880FA64
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
HIT_ID = dict(size=4, sha256='b12945a9395fea471444b59c0a9e33507a82af3be4b8d0a17ffbf5077f926c37')
LAYOUT = dict(tileset_size=24, compressed=0, secondary=1, tiles=4, palettes=8,
              metatiles=12, callback=16, attributes=20, map_layout_size=28,
              width=0, height=4, border=8, map=12, primary=16, secondary_tileset=20,
              border_width=24, border_height=25)
LOOKUP = 'Overworld_GetMapHeaderByGroupAndId'
NAMES = {LOOKUP, 'gMapGroups', 'gMapHeader', 'gBackupMapLayout',
         'CopyMapGridData', 'InitMap', 'MapGridGetMetatileIdAt',
         'MapGridGetMetatileAttributeAt', 'GetMetatileAttributesById',
         'GetMetatileAttributesByIdAndMapLayout', 'GetMapHeaderFromConnection'}
DATA_FIELDS = ('tiles', 'palettes', 'metatiles', 'attributes')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def section(raw, address, size, alignment=1):
    need(type(address) is int and type(size) is int and type(alignment) is int and
         alignment in (1, 2, 4) and size > 0 and address % alignment == 0 and
         BASE <= address and address+size <= BASE+len(raw), '有限ROM範囲/整列')
    return raw[address-BASE:address-BASE+size]


def u32(raw, address):
    return struct.unpack('<I', section(raw, address, 4, 4))[0]


def checked_layout(layout):
    need(type(layout) is dict and set(layout) == set(LAYOUT) and
         all(type(v) is int for v in layout.values()) and layout == LAYOUT, '固定ARM構造体ABI')
    return dict(layout)


def tileset(raw, address, layout):
    checked_layout(layout)
    data = section(raw, address, layout['tileset_size'], 4)
    values = {key: struct.unpack_from('<I', data, layout[key])[0]
              for key in (*DATA_FIELDS, 'callback')}
    # callbackをdata pointerとして検査しない。NULL/Thumb/ARMの記録と実行証明は別。
    errors = []
    for key in DATA_FIELDS:
        align = 2 if key in ('palettes', 'metatiles') else 4
        try:
            section(raw, values[key], align, align)
        except ValueError:
            errors.append(key)
    return dict(address=address, identity=identity(data),
                compression_byte=data[layout['compressed']],
                secondary_byte=data[layout['secondary']],
                compressed=data[layout['compressed']] != 0,
                palette_mode=('primary' if data[layout['secondary']] == 0 else
                              'secondary' if data[layout['secondary']] == 1 else 'compressed'),
                **values, invalid_data_fields=errors, actual_consumer_proven=False)


def distances(row, hit=HIT, radius=131072):
    need(type(hit) is int and type(radius) is int and 0 < radius <= 131072, '限定距離上限')
    return [dict(field=key, pointer=row[key], offset=hit-row[key], extent_proven=False)
            for key in DATA_FIELDS if key not in row['invalid_data_fields'] and
            0 <= hit-row[key] < radius]


def map_layout(raw, address):
    data = section(raw, address, LAYOUT['map_layout_size'], 4)
    width, height = struct.unpack_from('<ii', data)
    need(0 < width <= 256 and 0 < height <= 256, '限定map寸法')
    values = dict(zip(('border', 'map', 'primary', 'secondary_tileset'), struct.unpack_from('<4I', data, 8)))
    section(raw, values['map'], width*height*2, 2)
    return dict(address=address, identity=identity(data), width=width, height=height,
                border_width=data[24], border_height=data[25], **values)


def contains(start, size, hit, width=4):
    need(all(type(n) is int for n in (start, size, hit, width)) and
         size > 0 and width > 0 and 0 <= start < start+size <= 2**32 and
         0 <= hit < hit+width <= 2**32, '有限包含範囲')
    return start <= hit and hit+width <= start+size


def lookup_profile(raw, symbol, group, number):
    """現候補の実命令を直接ABI入力で解釈。game boot/自然map有効性は非主張。"""
    import pr16_dex_hof_runtime_sprite as thumb
    need(type(group) is int and type(number) is int and 0 <= group < 256 and 0 <= number < 256, 'u8 lookup入力')
    start = symbol['address'] & ~1
    end = symbol['following_distinct_address']
    need(type(end) is int and 0 < end-start <= 256, '有限lookup code')
    machine = thumb.Machine(raw, ((start, end),), ((0x03007800, 0x03007F00),))
    machine.r[:2] = [group, number]
    saved = machine.r[4:12]+machine.r[13:15]
    machine.run(start, 0x01000000, limit=128)
    need(machine.r[4:12]+machine.r[13:15] == saved and not machine.calls, 'lookup単一leaf/ABI帰還')
    data_reads = [dict(row) for (address, size), row in machine.reads.items()
                  if size == 4]
    return dict(group=group, number=number, result=machine.r[0],
                code=dict(start=start, end_exclusive=end, **identity(section(raw,start,end-start))),
                trace=machine.trace, data_reads=data_reads,
                instruction_count=len(machine.trace), writes=[{k:w[k] for k in ('address','size')} for w in machine.writes],
                conditional_actual_thumb_interpretation=True, natural_map_validity_proven=False)


def root_from_profile(raw, profile):
    """実LDRしたliteral→bank→headerの一意連鎖だけを採用する。"""
    need(profile['group'] == profile['number'] == 0, 'root抽出入力0/0')
    addresses = {r['address'] for r in profile['data_reads'] if r['size'] == 4}
    lo, hi = profile['code']['start'], profile['code']['end_exclusive']
    roots = []
    for at in sorted(addresses):
        if not lo <= at < hi:
            continue
        root = u32(raw, at)
        try:
            bank = u32(raw, root)
            header = u32(raw, bank)
        except ValueError:
            continue
        if root in addresses and bank in addresses and header == profile['result']:
            roots.append(dict(literal_address=at, root=root, first_bank=bank, first_header=header))
    need(len(roots) == 1, '一意の実lookup連鎖')
    return roots[0]


def probe_maps(raw, root, hit=HIT, groups=128, maps=128):
    """明示した有限入力矩形。全map数/自然到達性/owner完全性を推測しない。"""
    need(type(groups) is int and type(maps) is int and 1 <= groups <= 128 and 1 <= maps <= 128, '有限lookup件数')
    section(raw, root, groups*4, 4)
    layouts, descriptors, matches, table_ids = {}, {}, [], {}
    seen_headers = set()
    for group in range(groups):
        bank = u32(raw, root+group*4)
        try:
            table = section(raw, bank, maps*4, 4)
        except ValueError:
            continue
        table_ids[bank] = identity(table)
        for number in range(maps):
            header = u32(raw, bank+number*4)
            try:
                section(raw, header, 28, 4)
                layout_address = u32(raw, header)
                layout = map_layout(raw, layout_address)
            except ValueError:
                continue
            seen_headers.add(header)
            layouts.setdefault(layout_address, layout)
            owners = []
            for field in ('primary', 'secondary_tileset'):
                address = layout[field]
                if address not in descriptors:
                    try:
                        row = tileset(raw, address, LAYOUT)
                        descriptors[address] = row
                    except ValueError:
                        continue
                row = descriptors[address]
                near = distances(row, hit)
                if near:
                    owners.append(dict(role=field, descriptor=address, bounded_distances=near))
            map_size = layout['width']*layout['height']*2
            map_hit = contains(layout['map'], map_size, hit)
            bw,bh = layout['border_width'],layout['border_height']
            border_hit = 0 < bw <= 16 and 0 < bh <= 16 and contains(layout['border'], bw*bh*2, hit)
            if owners or map_hit or border_hit:
                matches.append(dict(group=group, number=number, header=header,
                    layout=layout_address, owners=owners, target_in_map=map_hit,
                    target_in_border=bool(border_hit), natural_map_validity_proven=False))
    return dict(input_bounds=dict(groups=groups, maps_per_group=maps, total_probes=groups*maps),
                root=dict(address=root, **identity(section(raw,root,groups*4))),
                bank_tables=[dict(address=k, **v) for k,v in sorted(table_ids.items())],
                unique_headers=len(seen_headers), layouts=list(layouts.values()),
                descriptors=list(descriptors.values()), matches=matches,
                whole_map_inventory_claimed=False, all_rom_scan=False,
                actual_asset_reader_proven=False, donor_safe_bytes=0)


def measure(raw, saved, symbols, layout):
    checked_layout(layout)
    need(identity(raw) == CANDIDATE and identity(section(raw,HIT,4)) == HIT_ID, '現候補/対象identity')
    rows = []
    for name, symbol in sorted(saved['selected_symbols']['found'].items()):
        if name.startswith('gTileset_'):
            row = tileset(raw, symbol['address'], layout)
            rows.append(dict(symbol=name, **row, bounded_distances=distances(row)))
    need(len(rows) == saved['tileset_descriptors']['checked_descriptors'], '旧descriptor候補集合保持')
    lookup = lookup_profile(raw, symbols['found'][LOOKUP], 0, 0)
    chain = root_from_profile(raw, lookup)
    maps = probe_maps(raw, chain['root'])
    # 有限probeで見つかったlayoutを実lookup結果へ再照合。asset readとは区別する。
    selected = []
    seen = set()
    for row in maps['matches']:
        if row['layout'] in seen:
            continue
        seen.add(row['layout'])
        profile = lookup_profile(raw, symbols['found'][LOOKUP], row['group'], row['number'])
        need(profile['result'] == row['header'], '実lookupと選定header一致')
        selected.append(profile)
    return dict(schema_version=1, candidate=CANDIDATE, origin=dict(address=HIT, **HIT_ID),
                corrected_arm_layout=layout, prior_descriptor_decoder_abi_mismatch=True,
                prior_zero_lz_search_replayed=False, prior_measurement_rewritten=False,
                descriptor_candidates=rows, valid_descriptor_candidates=sum(not r['invalid_data_fields'] for r in rows),
                actual_lookup=lookup, actual_root=chain, map_probe=maps, selected_lookup_profiles=selected,
                formal_classification_changes=0, actual_asset_reader_proven=False, donor_safe_bytes=0,
                limitations_ja=['旧callback/属性offset逆転を後継で修正。旧0件結果は履歴のまま保持する。',
                    '固定公開ARM layoutと現ROMの実lookupは束縛。有限入力/距離候補を自然map・asset extent・実readへ昇格しない。'])
