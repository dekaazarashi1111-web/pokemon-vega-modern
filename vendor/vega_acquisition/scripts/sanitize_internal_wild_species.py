#!/usr/bin/env python3
"""Audit and replace internal compatibility Species IDs in exact wild tables.

The correction rows are manifest-derived and map-scoped. The tool fails if an internal
Species appears outside an explicit correction, if a correction matches zero slots, or if
any internal Species remains after patching.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any

GBA_BASE = 0x08000000
HEADER_SIZE = 20
INFO_POINTER_OFFSET = 4
SLOT_KINDS = {
    "LAND": (4, 12),
    "WATER": (8, 5),
    "ROCK_SMASH": (12, 5),
    "FISHING": (16, 10),
}


class WildSanitizeError(ValueError):
    pass


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def digest(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise WildSanitizeError(f"not an integer: {value!r}")


def expected_sha(metadata: dict[str, Any]) -> str:
    for key in ("sha256", "output_sha256", "rom_sha256", "stage_sha256"):
        value = metadata.get(key)
        if isinstance(value, str) and len(value) == 64:
            return value.lower()
    for parent_key in ("final_rom", "output", "stage"):
        parent = metadata.get(parent_key)
        if isinstance(parent, dict):
            for key in ("sha256", "output_sha256", "rom_sha256", "stage_sha256"):
                value = parent.get(key)
                if isinstance(value, str) and len(value) == 64:
                    return value.lower()
    raise WildSanitizeError("stage metadata lacks exact ROM SHA-256")


def offset(address: int, size: int, rom_size: int) -> int:
    value = address - GBA_BASE
    if value < 0 or size < 0 or value + size > rom_size:
        raise WildSanitizeError(f"address outside ROM: 0x{address:08X}+{size}")
    return value


def u8(rom: bytes | bytearray, address: int) -> int:
    return rom[offset(address, 1, len(rom))]


def u16(rom: bytes | bytearray, address: int) -> int:
    return struct.unpack_from("<H", rom, offset(address, 2, len(rom)))[0]


def u32(rom: bytes | bytearray, address: int) -> int:
    return struct.unpack_from("<I", rom, offset(address, 4, len(rom)))[0]


def pointer_or_zero(rom: bytes | bytearray, address: int) -> int:
    value = u32(rom, address)
    if value == 0:
        return 0
    if not (GBA_BASE <= value < GBA_BASE + len(rom)):
        raise WildSanitizeError(f"bad ROM pointer 0x{value:08X} at 0x{address:08X}")
    return value


def set_u16(rom: bytearray, address: int, value: int) -> None:
    struct.pack_into("<H", rom, offset(address, 2, len(rom)), value)


def scan_slots(rom: bytes | bytearray, root: int, header_count: int) -> list[dict[str, int | str]]:
    found: list[dict[str, int | str]] = []
    seen_maps: set[tuple[int, int]] = set()
    for header_index in range(header_count):
        header = root + header_index * HEADER_SIZE
        group = u8(rom, header)
        map_id = u8(rom, header + 1)
        if group == 0xFF and map_id == 0xFF:
            raise WildSanitizeError(f"wild header terminator reached before declared count at index {header_index}")
        key = (group, map_id)
        # FireRed/Vegaの補助headerにはmap 0/0の反復行が正規に存在する。
        # それ以外の重複だけを構造異常として扱う。
        if key in seen_maps and key != (0, 0):
            raise WildSanitizeError(f"duplicate wild header map {group}/{map_id}")
        seen_maps.add(key)
        for kind, (pointer_field, slot_count) in SLOT_KINDS.items():
            info = pointer_or_zero(rom, header + pointer_field)
            if info == 0:
                continue
            slots = pointer_or_zero(rom, info + INFO_POINTER_OFFSET)
            if slots == 0:
                raise WildSanitizeError(f"{group}/{map_id} {kind}: info has null slot pointer")
            for slot_index in range(slot_count):
                record = slots + slot_index * 4
                found.append({
                    "header_index": header_index,
                    "map_group": group,
                    "map_id": map_id,
                    "encounter_kind": kind,
                    "slot_index": slot_index,
                    "min_level": u8(rom, record),
                    "max_level": u8(rom, record + 1),
                    "species_id": u16(rom, record + 2),
                    "species_address": record + 2,
                })
    terminator = root + header_count * HEADER_SIZE
    if not (u8(rom, terminator) == 0xFF and u8(rom, terminator + 1) == 0xFF):
        raise WildSanitizeError("wild header count/root differs: expected terminator after declared count")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--stage-metadata", type=Path, required=True)
    parser.add_argument("--output-rom", type=Path, required=True)
    parser.add_argument("--output-metadata", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    try:
        stage = json.loads(args.stage_metadata.read_text(encoding="utf-8"))
        pin = json.loads((package / "manifests/source_stage_pin.json").read_text(encoding="utf-8"))
        correction_rows = rows(package / "content/wild_source_corrections.csv")
        block_rows = rows(package / "content/internal_species_blocklist_25.csv")
        rom = bytearray(args.rom.read_bytes())
        input_sha = digest(rom)
        if input_sha != expected_sha(stage):
            raise WildSanitizeError(f"input ROM SHA differs: {input_sha}")
        root = integer(pin["wild_header_root"])
        header_count = integer(pin["wild_header_count"])
        internal_ids = {int(row["canonical_id"]) for row in block_rows}
        rules: dict[tuple[int, int, str, int], dict[str, str]] = {}
        for row in correction_rows:
            key = (int(row["map_group"]), int(row["map_id"]), row["encounter_kind"], int(row["from_canonical_id"]))
            if key in rules:
                raise WildSanitizeError(f"duplicate correction selector: {key}")
            if int(row["from_canonical_id"]) not in internal_ids:
                raise WildSanitizeError(f"correction source is not internal: {row['correction_key']}")
            if int(row["to_canonical_id"]) in internal_ids:
                raise WildSanitizeError(f"correction target is internal: {row['correction_key']}")
            rules[key] = row

        slots = scan_slots(rom, root, header_count)
        internal_slots = [row for row in slots if int(row["species_id"]) in internal_ids]
        uncovered = [row for row in internal_slots if (int(row["map_group"]), int(row["map_id"]), str(row["encounter_kind"]), int(row["species_id"])) not in rules]
        if uncovered:
            raise WildSanitizeError(f"internal wild slots lack correction: {uncovered[:10]}")

        patches: list[dict[str, object]] = []
        match_counts = {key: 0 for key in rules}
        for slot in internal_slots:
            key = (int(slot["map_group"]), int(slot["map_id"]), str(slot["encounter_kind"]), int(slot["species_id"]))
            rule = rules[key]
            match_counts[key] += 1
            old_id = int(slot["species_id"])
            new_id = int(rule["to_canonical_id"])
            address = int(slot["species_address"])
            set_u16(rom, address, new_id)
            patches.append({
                "correction_key": rule["correction_key"],
                "map_group": int(slot["map_group"]),
                "map_id": int(slot["map_id"]),
                "encounter_kind": slot["encounter_kind"],
                "slot_index": int(slot["slot_index"]),
                "min_level": int(slot["min_level"]),
                "max_level": int(slot["max_level"]),
                "species_address": address,
                "from_canonical_id": old_id,
                "to_canonical_id": new_id,
            })
        zero = [rules[key]["correction_key"] for key, count in match_counts.items() if count == 0]
        if zero:
            raise WildSanitizeError(f"wild corrections matched zero exact slots: {zero}")
        remaining = [row for row in scan_slots(rom, root, header_count) if int(row["species_id"]) in internal_ids]
        if remaining:
            raise WildSanitizeError(f"internal wild slots remain after patch: {remaining[:10]}")

        args.output_rom.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=args.output_rom.parent, delete=False) as temp:
            temp.write(rom)
            temp_path = Path(temp.name)
        os.replace(temp_path, args.output_rom)
        output_sha = digest(rom)
        metadata = dict(stage)
        metadata.update({
            "sha256": output_sha,
            "output_sha256": output_sha,
            "input_sha256": input_sha,
            "wild_sanitization": {
                "status": "PASS",
                "wild_header_root": root,
                "wild_header_count": header_count,
                "patch_count": len(patches),
                "patches": patches,
            },
        })
        args.output_metadata.parent.mkdir(parents=True, exist_ok=True)
        args.output_metadata.write_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        report = {
            "schema_version": 1,
            "status": "PASS",
            "input_sha256": input_sha,
            "output_sha256": output_sha,
            "patch_count": len(patches),
            "patches": patches,
        }
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, WildSanitizeError) as error:
        print(f"wild Species sanitization failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
