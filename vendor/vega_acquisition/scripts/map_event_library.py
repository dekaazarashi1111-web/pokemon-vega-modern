#!/usr/bin/env python3
"""Shared exact-ROM locator/patcher for Gen-3 object, coord, and bg event scripts."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import MutableSequence, Sequence

GBA_BASE = 0x08000000


class MapEventError(ValueError):
    pass


@dataclass(frozen=True)
class LocatedMapEvent:
    kind: str
    record_address: int
    script_pointer_address: int
    script_pointer: int
    x: int
    y: int
    elevation: int
    object_count: int
    coord_count: int
    bg_count: int


def _offset(rom: Sequence[int], address: int, size: int) -> int:
    value = address - GBA_BASE
    if value < 0 or value + size > len(rom):
        raise MapEventError(f"address outside ROM: 0x{address:08X}+{size}")
    return value


def u8(rom: Sequence[int], address: int) -> int:
    return int(rom[_offset(rom, address, 1)])


def u16(rom: Sequence[int], address: int) -> int:
    return struct.unpack_from("<H", bytes(rom), _offset(rom, address, 2))[0]


def u32(rom: Sequence[int], address: int) -> int:
    return struct.unpack_from("<I", bytes(rom), _offset(rom, address, 4))[0]


def pointer(rom: Sequence[int], address: int) -> int:
    value = u32(rom, address)
    if not (GBA_BASE <= value < GBA_BASE + len(rom)):
        raise MapEventError(f"invalid pointer 0x{value:08X} at 0x{address:08X}")
    return value


def set_u32(rom: MutableSequence[int], address: int, value: int) -> None:
    raw = struct.pack("<I", value)
    start = _offset(rom, address, 4)
    rom[start:start + 4] = raw


def map_event_header(rom: Sequence[int], map_groups_root: int,
                     group_id: int, map_id: int) -> tuple[int, int]:
    group_table = pointer(rom, map_groups_root + group_id * 4)
    map_header = pointer(rom, group_table + map_id * 4)
    event_header = pointer(rom, map_header + 4)
    return map_header, event_header


def locate(rom: Sequence[int], map_groups_root: int, group_id: int, map_id: int,
           kind: str, selector: int) -> LocatedMapEvent:
    _, event_header = map_event_header(rom, map_groups_root, group_id, map_id)
    object_count = u8(rom, event_header)
    coord_count = u8(rom, event_header + 2)
    bg_count = u8(rom, event_header + 3)
    if kind == "OBJECT_REUSE":
        table = pointer(rom, event_header + 4)
        matches = [table + index * 0x18 for index in range(object_count)
                   if u8(rom, table + index * 0x18) == selector]
        if len(matches) != 1:
            raise MapEventError(f"object local_id {selector} appears {len(matches)} times")
        record = matches[0]
        script_site = record + 0x10
        return LocatedMapEvent(kind, record, script_site, u32(rom, script_site),
                               u16(rom, record + 4), u16(rom, record + 6),
                               u8(rom, record + 8), object_count, coord_count, bg_count)
    if kind == "COORD_REUSE":
        if not (0 <= selector < coord_count):
            raise MapEventError(f"coord index {selector} outside {coord_count}")
        table = pointer(rom, event_header + 0x0C)
        record = table + selector * 0x10
        script_site = record + 0x0C
        return LocatedMapEvent(kind, record, script_site, u32(rom, script_site),
                               u16(rom, record), u16(rom, record + 2),
                               u8(rom, record + 4), object_count, coord_count, bg_count)
    if kind == "BG_REUSE":
        if not (0 <= selector < bg_count):
            raise MapEventError(f"bg index {selector} outside {bg_count}")
        table = pointer(rom, event_header + 0x10)
        record = table + selector * 0x0C
        script_site = record + 8
        return LocatedMapEvent(kind, record, script_site, u32(rom, script_site),
                               u16(rom, record), u16(rom, record + 2),
                               u8(rom, record + 4), object_count, coord_count, bg_count)
    raise MapEventError(f"unsupported event kind {kind}")


def patch_script_pointer(rom: MutableSequence[int], located: LocatedMapEvent,
                         expected_before: int, script_after: int) -> None:
    if located.script_pointer != expected_before:
        raise MapEventError(
            f"current script 0x{located.script_pointer:08X} != expected 0x{expected_before:08X}"
        )
    set_u32(rom, located.script_pointer_address, script_after)
