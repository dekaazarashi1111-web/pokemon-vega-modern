from __future__ import annotations

import zlib
from collections.abc import Mapping

from scripts import build_stage61_display_npc_event_audit as builder


def build_stage61_save(
    *,
    map_group: int,
    map_number: int,
    x: int = 0,
    y: int = 0,
    warp_id: int = 0,
    flags: Mapping[int, bool] | None = None,
    variables: Mapping[int, int] | None = None,
    counter: int = 2,
    first_sector: int = 3,
    marker: int = 0,
    last_used_ball: int = 0,
    coins: int = 0,
) -> bytes:
    """Build a footer/checksum/CRC-correct synthetic Stage61 Flash image."""

    if not 0 <= map_group <= 0xFF or not 0 <= map_number <= 0xFF:
        raise ValueError("map identity outside u8")
    if not 0 <= first_sector < 14:
        raise ValueError("first sector outside slot")
    physical_base = (counter & 1) * 14
    raw = bytearray(b"\xFF" * (128 * 1024))
    sections = [bytearray(0x1000) for _ in range(14)]
    save1 = bytearray(0x3D40)
    save1[0:2] = x.to_bytes(2, "little")
    save1[2:4] = y.to_bytes(2, "little")
    save1[4] = map_group
    save1[5] = map_number
    save1[6] = warp_id
    save1[0x100] = marker & 0xFF
    payload = bytearray(0x606)

    for identifier, state in (flags or {}).items():
        if identifier < 0x0900:
            index = 0x0EE0 + (identifier >> 3)
            backing = save1
        elif identifier <= 0x18FF:
            index = (identifier - 0x0900) >> 3
            backing = payload
        else:
            raise ValueError(f"flag outside persistent namespace: {identifier:#x}")
        mask = 1 << (identifier & 7)
        if state:
            backing[index] |= mask
        else:
            backing[index] &= ~mask

    for identifier, value in (variables or {}).items():
        if 0x4000 <= identifier <= 0x40FF:
            index = 0x1000 + (identifier - 0x4000) * 2
            backing = save1
        elif 0x5000 <= identifier <= 0x51FF:
            index = 0x200 + (identifier - 0x5000) * 2
            backing = payload
        else:
            raise ValueError(f"var outside persistent namespace: {identifier:#x}")
        backing[index:index + 2] = int(value).to_bytes(2, "little")

    payload[0x600:0x602] = last_used_ball.to_bytes(2, "little")
    payload[0x602:0x606] = coins.to_bytes(4, "little")
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    record = (
        (0x45313653).to_bytes(4, "little")
        + (1).to_bytes(2, "little")
        + (0x606).to_bytes(2, "little")
        + crc.to_bytes(4, "little")
        + (~crc & 0xFFFFFFFF).to_bytes(4, "little")
        + payload
    )

    cursor = 0
    for identifier in range(1, 5):
        size = builder._MGBA_SAVE_SECTION_SIZES[identifier]
        sections[identifier][:size] = save1[cursor:cursor + size]
        cursor += size
    if cursor != len(save1):
        raise AssertionError("SaveBlock1 fixture partition drift")
    sections[13][0x7D0:0x7D0 + len(record)] = record

    for identifier, section in enumerate(sections):
        section[0xFF4:0xFF6] = identifier.to_bytes(2, "little")
        checksum = builder._mgba_save_checksum(bytes(section), identifier)
        section[0xFF6:0xFF8] = checksum.to_bytes(2, "little")
        section[0xFF8:0xFFC] = (0x08012025).to_bytes(4, "little")
        section[0xFFC:0x1000] = counter.to_bytes(4, "little")
        physical = physical_base + (first_sector + identifier) % 14
        start = physical * 0x1000
        raw[start:start + 0x1000] = section
    return bytes(raw)
