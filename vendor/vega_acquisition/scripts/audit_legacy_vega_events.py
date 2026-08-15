#!/usr/bin/env python3
"""Extract exact Tohoku event hosts and verify explicit legacy Vega bindings."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

GBA_BASE = 0x08000000


class AuditError(ValueError):
    pass


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise AuditError(f"not integer: {value!r}")


def offset(rom: bytes, address: int, size: int) -> int:
    value = address - GBA_BASE
    if value < 0 or value + size > len(rom):
        raise AuditError(f"address outside ROM: 0x{address:08X}+{size}")
    return value


def u8(rom: bytes, address: int) -> int:
    return rom[offset(rom, address, 1)]


def u16(rom: bytes, address: int) -> int:
    return struct.unpack_from("<H", rom, offset(rom, address, 2))[0]


def u32(rom: bytes, address: int) -> int:
    return struct.unpack_from("<I", rom, offset(rom, address, 4))[0]


def pointer(rom: bytes, address: int) -> int:
    value = u32(rom, address)
    if not (GBA_BASE <= value < GBA_BASE + len(rom)):
        raise AuditError(f"invalid pointer 0x{value:08X} at 0x{address:08X}")
    return value


def symbols(metadata: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key in ("symbols", "runtime_symbols", "script_symbols"):
        value = metadata.get(key)
        if isinstance(value, dict):
            for name, address in value.items():
                try:
                    result[str(name)] = integer(address)
                except ValueError:
                    pass
    return result


def metadata_sha(metadata: dict[str, Any]) -> str:
    for key in ("sha256", "output_sha256", "rom_sha256", "stage_sha256"):
        value = metadata.get(key)
        if isinstance(value, str) and len(value) == 64:
            return value.lower()
    raise AuditError("metadata lacks ROM SHA")


def event_rows_for_map(rom: bytes, root: int, group: int, map_id: int) -> list[dict[str, object]]:
    group_table = pointer(rom, root + group * 4)
    map_header = pointer(rom, group_table + map_id * 4)
    event_header = pointer(rom, map_header + 4)
    object_count = u8(rom, event_header)
    coord_count = u8(rom, event_header + 2)
    bg_count = u8(rom, event_header + 3)
    result: list[dict[str, object]] = []
    if object_count:
        table = pointer(rom, event_header + 4)
        for index in range(object_count):
            record = table + index * 0x18
            result.append({"event_kind": "OBJECT_REUSE", "selector": u8(rom, record),
                           "x": u16(rom, record + 4), "y": u16(rom, record + 6),
                           "elevation": u8(rom, record + 8), "record_address": record,
                           "script_pointer": u32(rom, record + 0x10)})
    if coord_count:
        table = pointer(rom, event_header + 0x0C)
        for index in range(coord_count):
            record = table + index * 0x10
            result.append({"event_kind": "COORD_REUSE", "selector": index,
                           "x": u16(rom, record), "y": u16(rom, record + 2),
                           "elevation": u8(rom, record + 4), "record_address": record,
                           "script_pointer": u32(rom, record + 0x0C)})
    if bg_count:
        table = pointer(rom, event_header + 0x10)
        for index in range(bg_count):
            record = table + index * 0x0C
            result.append({"event_kind": "BG_REUSE", "selector": index,
                           "x": u16(rom, record), "y": u16(rom, record + 2),
                           "elevation": u8(rom, record + 4), "record_address": record,
                           "script_pointer": u32(rom, record + 8)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--stage-metadata", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, help="explicit analyst-confirmed binding JSON")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    try:
        rom = args.rom.read_bytes()
        metadata = json.loads(args.stage_metadata.read_text(encoding="utf-8"))
        if hashlib.sha256(rom).hexdigest() != metadata_sha(metadata):
            raise AuditError("ROM SHA differs from stage metadata")
        table = symbols(metadata)
        root = table.get("map_groups_root", table.get("gMapGroups"))
        if root is None:
            raise AuditError("map_groups_root/gMapGroups symbol required")
        maps = rows(package / "inputs/map_ids.csv")
        targets = {int(row["vega_id"]): row for row in rows(package / "content/legacy_vega_event_audit_14.csv")}
        inventory: list[dict[str, object]] = []
        target_bytes = {vega_id: struct.pack("<H", vega_id) for vega_id in targets}
        for map_row in maps:
            group = int(map_row["group_id"]); map_id = int(map_row["map_id"])
            # Kanto namespace is already physically proven; this audit is Tohoku-only.
            if group >= 96:
                continue
            try:
                events = event_rows_for_map(rom, root, group, map_id)
            except AuditError:
                continue
            for event in events:
                script = int(event["script_pointer"])
                if not (GBA_BASE <= script < GBA_BASE + len(rom)):
                    continue
                window = rom[offset(rom, script, min(256, GBA_BASE + len(rom) - script)):
                             offset(rom, script, min(256, GBA_BASE + len(rom) - script)) + min(256, GBA_BASE + len(rom) - script)]
                hits = [vega_id for vega_id, pattern in target_bytes.items() if pattern in window]
                if hits:
                    inventory.append({**event, "group_id": group, "map_id": map_id,
                                      "map_key": map_row["map_key"],
                                      "candidate_vega_ids": hits,
                                      "candidate_only": True})

        verified: list[dict[str, object]] = []
        if args.bindings:
            binding_doc = json.loads(args.bindings.read_text(encoding="utf-8"))
            for binding in binding_doc.get("bindings", []):
                vega_id = integer(binding["vega_id"])
                if vega_id not in targets:
                    raise AuditError(f"binding target outside 14-row audit: {vega_id}")
                events = event_rows_for_map(rom, root, integer(binding["group_id"]), integer(binding["map_id"]))
                matches = [row for row in events if row["event_kind"] == binding["event_kind"] and row["selector"] == integer(binding["selector"])]
                if len(matches) != 1:
                    raise AuditError(f"binding host is absent/ambiguous: {binding}")
                event = matches[0]
                if integer(binding["script_pointer"]) != event["script_pointer"]:
                    raise AuditError(f"binding script pointer differs for Vega {vega_id}")
                operand = integer(binding["species_operand_address"])
                if u16(rom, operand) != vega_id:
                    raise AuditError(f"species operand is not canonical Vega ID {vega_id}")
                verified.append({**binding, **event, "status": "EXACT_ROM_BINDING_VERIFIED"})

        result = {
            "schema_version": 1,
            "status": "VERIFIED_BINDINGS_PRESENT" if verified else "CANDIDATE_SCAN_ONLY_PHYSICAL_AUDIT_REQUIRED",
            "rom_sha256": hashlib.sha256(rom).hexdigest(),
            "target_vega_ids": sorted(targets),
            "candidate_hosts": inventory,
            "verified_bindings": verified,
            "warning": "16-bit operand scan is heuristic and never promotes a row. Promotion requires explicit binding with exact operand address.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, AuditError) as error:
        print(f"legacy Vega event audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
