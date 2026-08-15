#!/usr/bin/env python3
"""Synthetic exact-layout test for the internal wild Species sanitizer."""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

GBA_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
ROOT = 0x092CAF0C
HEADER_SIZE = 20


def off(address: int) -> int:
    return address - GBA_BASE


def put_u32(rom: bytearray, address: int, value: int) -> None:
    struct.pack_into("<I", rom, off(address), value)


def put_slot(rom: bytearray, address: int, species: int, low: int = 10, high: int = 20) -> None:
    struct.pack_into("<BBH", rom, off(address), low, high, species)


def build_rom(uncovered_internal: bool) -> tuple[bytes, list[int]]:
    rom = bytearray([0xFF]) * ROM_SIZE
    # 265 unique map keys, explicitly including both audited correction maps and one
    # negative-fixture map.
    pairs = [(1, 64), (1, 111), (2, 2)]
    for group in range(16):
        for map_id in range(256):
            pair = (group, map_id)
            if pair not in pairs:
                pairs.append(pair)
            if len(pairs) == 265:
                break
        if len(pairs) == 265:
            break
    assert len(pairs) == 265 and len(set(pairs)) == 265
    # Zero pointer fields for all headers, then add land tables to three maps.
    for index, (group, map_id) in enumerate(pairs):
        header = ROOT + index * HEADER_SIZE
        rom[off(header):off(header) + HEADER_SIZE] = bytes(HEADER_SIZE)
        rom[off(header)] = group
        rom[off(header + 1)] = map_id
    terminator = ROOT + len(pairs) * HEADER_SIZE
    rom[off(terminator)] = 0xFF
    rom[off(terminator + 1)] = 0xFF

    species_addresses: list[int] = []
    base_info = 0x08010000
    base_slots = 0x08011000
    for table_index, pair in enumerate([(1, 64), (1, 111), (2, 2)]):
        header_index = pairs.index(pair)
        header = ROOT + header_index * HEADER_SIZE
        info = base_info + table_index * 0x20
        slots = base_slots + table_index * 0x80
        rom[off(info):off(info) + 8] = bytes(8)
        rom[off(info)] = 20
        put_u32(rom, info + 4, slots)
        put_u32(rom, header + 4, info)
        for slot_index in range(12):
            species = 1
            if slot_index == 0 and pair in {(1, 64), (1, 111)}:
                species = 282
                species_addresses.append(slots + 2)
            if slot_index == 1 and pair == (2, 2) and uncovered_internal:
                species = 253
            put_slot(rom, slots + slot_index * 4, species)
    return bytes(rom), species_addresses


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    tool = root / "scripts/sanitize_internal_wild_species.py"
    with tempfile.TemporaryDirectory() as temp_text:
        temp = Path(temp_text)
        raw, addresses = build_rom(False)
        input_rom = temp / "input.gba"
        input_rom.write_bytes(raw)
        metadata = temp / "stage.json"
        metadata.write_text(json.dumps({"sha256": hashlib.sha256(raw).hexdigest()}) + "\n", encoding="utf-8")
        output_rom = temp / "output.gba"
        output_meta = temp / "output.json"
        completed = run([sys.executable, str(tool), "--package", str(root), "--rom", str(input_rom), "--stage-metadata", str(metadata), "--output-rom", str(output_rom), "--output-metadata", str(output_meta)])
        if completed.returncode:
            print(completed.stderr or completed.stdout, file=sys.stderr)
            return 1
        result = json.loads(completed.stdout)
        if result.get("patch_count") != 2:
            print(f"unexpected patch count: {result}", file=sys.stderr)
            return 1
        patched = output_rom.read_bytes()
        for address in addresses:
            if struct.unpack_from("<H", patched, off(address))[0] != 255:
                print(f"Scyther slot not replaced at 0x{address:08X}", file=sys.stderr)
                return 1

        bad_raw, _ = build_rom(True)
        bad_rom = temp / "bad.gba"
        bad_rom.write_bytes(bad_raw)
        bad_meta = temp / "bad.json"
        bad_meta.write_text(json.dumps({"sha256": hashlib.sha256(bad_raw).hexdigest()}) + "\n", encoding="utf-8")
        completed = run([sys.executable, str(tool), "--package", str(root), "--rom", str(bad_rom), "--stage-metadata", str(bad_meta), "--output-rom", str(temp / "bad_out.gba"), "--output-metadata", str(temp / "bad_out.json")])
        detail = completed.stderr or completed.stdout
        if completed.returncode == 0 or "internal wild slots lack correction" not in detail:
            print(f"uncovered internal slot did not fail: {detail}", file=sys.stderr)
            return 1
    print("wild Species sanitizer synthetic tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
