#!/usr/bin/env python3
"""Collection受付のBG原本を読み取り、通常A入力用の接近点を検証する。"""
from __future__ import annotations
import struct

BASE = 0x08000000
MAP_ROOT = 0x54B0C


def geometry(rom: bytes, config: dict) -> dict:
    """NPC/objectへフォールバックしない。ROM・設定への書き込みは行わない。"""
    def need(ok: bool, message: str) -> None:
        if not ok:
            raise ValueError(message)

    def span(at: int, size: int) -> int:
        need(type(at) is int and 0 <= at <= len(rom) - size, 'BG: 読取範囲')
        return at

    def ptr(at: int, size: int = 1) -> int:
        return span(struct.unpack_from('<I', rom, span(at, 4))[0] - BASE, size)

    hosts = config['physical_hosts']
    selected = [(i, h) for i, h in enumerate(hosts) if h['service'] == 'GIFT']
    need(bool(selected), 'BG: GIFT定義なし')
    index, host = selected[0]
    group, number, x, y, elevation = (host[k] for k in ('map_group', 'map_num', 'x', 'y', 'elevation'))
    need(all(type(v) is int for v in (group, number, x, y, elevation)), 'BG: 整数設定')
    need(0 <= group < 256 and 0 <= number < 256 and 0 <= index < 256
         and 0 <= x < 65536 and 0 <= y < 65533 and 0 <= elevation < 16, 'BG: 設定境界')
    header = ptr(ptr(ptr(MAP_ROOT) + 4 * group) + 4 * number, 8)
    events = ptr(header + 4, 20)
    count = rom[events + 3]
    need(count > 0, 'BG: 受付イベントなし')
    table = ptr(events + 16, count * 12)
    found = [(i, bytes(rom[table + 12*i:table + 12*(i+1)])) for i in range(count)
             if struct.unpack_from('<HH', rom, table + 12*i) == (x, y)]
    need(len(found) == 1, 'BG: 一意の設定受付が必要')
    event_index, record = found[0]
    rx, ry, re, kind, padding, script = struct.unpack('<HHBBHI', record)
    need((rx, ry, re, kind, padding) == (x, y, elevation, 0, 0), 'BG: 通常A/elevation/予約領域')
    at = span(script - BASE, 32)
    need(rom[at:at+7] == bytes((0x6A, 0x16, 4, 0x80, index, 0, 0x23)), 'BG: lock/setvar host/callnative')
    native = struct.unpack_from('<I', rom, at + 7)[0]
    need(native & 1 == 1, 'BG: native Thumb')
    span((native & ~1) - BASE, 2)

    layout = ptr(header, 16)
    width, height = struct.unpack_from('<II', rom, layout)
    need(0 < width <= 512 and 0 < height <= 512 and x < width and y+2 < height, 'BG: 接近点map境界')
    blocks = ptr(layout + 12, width * height * 2)
    cells = []
    for py in (y, y+1, y+2):
        value = struct.unpack_from('<H', rom, blocks + 2*(py*width+x))[0]
        collision, ze = (value >> 10) & 3, value >> 12
        need(collision == 0 and ze == elevation, 'BG: 同高度の歩行可能な受付/接近点')
        cells.append(dict(x=x, y=py, metatile=value & 1023, collision=collision, elevation=ze))
    # 最初の上移動をfixture区間に限定。接近点上の別イベントで誤起動しない。
    for slot, stride, offset in ((0, 24, 4), (1, 8, 0), (2, 16, 0), (3, 12, 0)):
        n = rom[events + slot]
        if not n:
            continue
        rows = ptr(events + 4 + 4*slot, n*stride)
        for i in range(n):
            xy = struct.unpack_from('<HH', rom, rows + i*stride + offset)
            allowed = slot == 3 and i == event_index
            need(allowed or xy not in ((x, y), (x, y+1), (x, y+2)), 'BG: 受付/接近点イベント衝突')
    return dict(host_index=index, group=group, number=number, x=x, y=y+1,
                local_id=0, npc_y=y, script=script, native=native,
                script_hex=bytes(rom[at:at+32]).hex(), object_hex='',
                event_kind='BG_NORMAL_FIELD_A', bg_event_index=event_index,
                bg_record_hex=record.hex(), cells=cells,
                approach='PRE_BARRIER_ONE_TILE_UP_THEN_A_ONLY',
                legacy_npc_fields_are_not_object_identity=True)
