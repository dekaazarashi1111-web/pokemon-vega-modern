#!/usr/bin/env python3
"""Serialize READY_TO_SERIALIZE acquisition host scripts into an exact ROM stage."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any

GBA_BASE = 0x08000000
ROM_LIMIT = 32 * 1024 * 1024
SCRIPT_ALIGNMENT = 4


class SerializeError(ValueError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise SerializeError(f"expected integer, got {value!r}")


def allocation(contract: dict[str, Any], name: str) -> tuple[int, int, int]:
    matches: list[dict[str, Any]] = []
    value = contract.get("allocations")
    if isinstance(value, dict) and isinstance(value.get(name), dict):
        matches.append({"name": name, **value[name]})
    elif isinstance(value, list):
        matches += [row for row in value if isinstance(row, dict) and row.get("name", row.get("allocation_name")) == name]
    for key in ("regions", "rows", "entries"):
        value = contract.get(key)
        if isinstance(value, list):
            matches += [row for row in value if isinstance(row, dict) and row.get("name", row.get("allocation_name")) == name]
    if len(matches) != 1:
        raise SerializeError(f"allocation {name!r} absent or ambiguous")
    row = matches[0]
    address = integer(row.get("address", row.get("start")))
    size = integer(row.get("size", row.get("capacity", row.get("length"))))
    if "fill_byte" not in row:
        raise SerializeError(f"allocation {name!r} must declare fill_byte for exact-ROM verification")
    fill = integer(row["fill_byte"])
    if not (0 <= fill <= 0xFF):
        raise SerializeError("fill_byte outside byte range")
    return address, size, fill


def symbol_table(*documents: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for document in documents:
        for key in ("symbols", "runtime_symbols", "script_symbols"):
            value = document.get(key)
            if isinstance(value, dict):
                for name, address in value.items():
                    try:
                        result[str(name)] = integer(address)
                    except (ValueError, TypeError):
                        pass
    return result


def expected_sha(metadata: dict[str, Any]) -> str:
    for key in ("sha256", "output_sha256", "rom_sha256", "stage_sha256"):
        value = metadata.get(key)
        if isinstance(value, str) and len(value) == 64:
            return value.lower()
    raise SerializeError("stage metadata lacks exact input ROM SHA-256")


def offset(address: int, size: int, rom_size: int) -> int:
    value = address - GBA_BASE
    if value < 0 or size < 0 or value + size > rom_size:
        raise SerializeError(f"ROM address outside image: 0x{address:08X}+{size}")
    return value


def read_u8(rom: bytes | bytearray, address: int) -> int:
    return rom[offset(address, 1, len(rom))]


def read_u16(rom: bytes | bytearray, address: int) -> int:
    return struct.unpack_from("<H", rom, offset(address, 2, len(rom)))[0]


def read_u32(rom: bytes | bytearray, address: int) -> int:
    return struct.unpack_from("<I", rom, offset(address, 4, len(rom)))[0]


def read_pointer(rom: bytes | bytearray, address: int) -> int:
    value = read_u32(rom, address)
    if not (GBA_BASE <= value < GBA_BASE + len(rom)):
        raise SerializeError(f"invalid ROM pointer 0x{value:08X} at 0x{address:08X}")
    return value


def write_u32(rom: bytearray, address: int, value: int) -> None:
    struct.pack_into("<I", rom, offset(address, 4, len(rom)), value)


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def host_script(wrapper_address: int) -> bytes:
    if not (GBA_BASE <= wrapper_address < GBA_BASE + ROM_LIMIT):
        raise SerializeError(f"wrapper address outside GBA ROM: 0x{wrapper_address:08X}")
    # FireRed field script: lock; faceplayer; callnative thumb; waitstate; release; end.
    return b"\x6A\x5A\x23" + struct.pack("<I", wrapper_address | 1) + b"\x27\x6C\x02"


def locate_object(rom: bytearray, map_groups_root: int, host: dict[str, Any]) -> dict[str, int]:
    group_id = integer(host["group_id"])
    map_id = integer(host["map_id"])
    local_id = integer(host["local_id"])
    group_table = read_pointer(rom, map_groups_root + group_id * 4)
    map_header = read_pointer(rom, group_table + map_id * 4)
    event_header = read_pointer(rom, map_header + 4)
    object_count = read_u8(rom, event_header)
    expected_count = integer(host["object_count"])
    if object_count != expected_count:
        raise SerializeError(f"{host['host_key']}: object count {object_count} != {expected_count}")
    objects = read_pointer(rom, event_header + 4)
    matches: list[int] = []
    for index in range(object_count):
        record = objects + index * 0x18
        if read_u8(rom, record) == local_id:
            matches.append(record)
    if len(matches) != 1:
        raise SerializeError(f"{host['host_key']}: local_id {local_id} appears {len(matches)} times")
    record = matches[0]
    observed = {
        "x": read_u16(rom, record + 4),
        "y": read_u16(rom, record + 6),
        "elevation": read_u8(rom, record + 8),
        "script_pointer": read_u32(rom, record + 0x10),
    }
    for key in ("x", "y", "elevation"):
        expected = integer(host[key])
        if observed[key] != expected:
            raise SerializeError(f"{host['host_key']}: {key} {observed[key]} != {expected}")
    return {"map_header": map_header, "event_header": event_header, "object_record": record, **observed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--stage-metadata", type=Path, required=True)
    parser.add_argument("--runtime-symbols", type=Path, required=True)
    parser.add_argument("--allocation-contract", type=Path, required=True)
    parser.add_argument("--patch-manifest", type=Path, required=True)
    parser.add_argument("--output-rom", type=Path, required=True)
    parser.add_argument("--output-metadata", type=Path, required=True)
    args = parser.parse_args()
    try:
        rom = bytearray(args.rom.read_bytes())
        if len(rom) != ROM_LIMIT:
            raise SerializeError(f"expected 32 MiB stage, got {len(rom)} bytes")
        stage = json.loads(args.stage_metadata.read_text(encoding="utf-8"))
        runtime = json.loads(args.runtime_symbols.read_text(encoding="utf-8"))
        contract = json.loads(args.allocation_contract.read_text(encoding="utf-8"))
        manifest = json.loads(args.patch_manifest.read_text(encoding="utf-8"))
        observed_input_sha = sha(rom)
        if observed_input_sha != expected_sha(stage):
            raise SerializeError(f"input ROM SHA differs: {observed_input_sha}")
        if manifest.get("release_policy") != "READY_TO_SERIALIZE_OBJECT_REUSE_ONLY":
            raise SerializeError("patch manifest release policy differs")
        symbols = symbol_table(stage, runtime)
        map_groups_root = symbols.get("map_groups_root", symbols.get("gMapGroups"))
        if map_groups_root is None:
            raise SerializeError("map_groups_root/gMapGroups symbol is required")
        allocation_address, allocation_size, fill = allocation(contract, "acquisition_map_scripts")
        allocation_offset = offset(allocation_address, allocation_size, len(rom))
        if any(value != fill for value in rom[allocation_offset:allocation_offset + allocation_size]):
            raise SerializeError("acquisition_map_scripts allocation is not uniformly declared fill_byte")

        cursor = allocation_address
        patches: list[dict[str, Any]] = []
        hosts = manifest.get("hosts")
        if not isinstance(hosts, list) or not hosts:
            raise SerializeError("patch manifest has no release hosts")
        for host in hosts:
            if host.get("event_kind") != "OBJECT_REUSE":
                raise SerializeError(f"unsupported release event kind: {host}")
            before_symbol = str(host["script_before_symbol"])
            wrapper_symbol = str(host["wrapper_symbol"])
            if before_symbol not in symbols:
                raise SerializeError(f"unresolved current script symbol {before_symbol}")
            if wrapper_symbol not in symbols:
                raise SerializeError(f"unresolved wrapper symbol {wrapper_symbol}")
            located = locate_object(rom, map_groups_root, host)
            expected_before = symbols[before_symbol]
            if located["script_pointer"] != expected_before:
                raise SerializeError(f"{host['host_key']}: script pointer 0x{located['script_pointer']:08X} != {before_symbol}=0x{expected_before:08X}")
            cursor = align(cursor, SCRIPT_ALIGNMENT)
            script = host_script(symbols[wrapper_symbol])
            if cursor + len(script) > allocation_address + allocation_size:
                raise SerializeError("acquisition map script allocation overflow")
            script_offset = offset(cursor, len(script), len(rom))
            if any(value != fill for value in rom[script_offset:script_offset + len(script)]):
                raise SerializeError(f"script write range for {host['host_key']} is not free")
            rom[script_offset:script_offset + len(script)] = script
            write_u32(rom, located["object_record"] + 0x10, cursor)
            patches.append({
                "host_key": host["host_key"],
                "group_id": integer(host["group_id"]), "map_id": integer(host["map_id"]),
                "local_id": integer(host["local_id"]),
                "object_record_address": located["object_record"],
                "pointer_patch_address": located["object_record"] + 0x10,
                "script_before_address": expected_before,
                "script_after_address": cursor,
                "script_size": len(script),
                "script_sha256": sha(script),
                "wrapper_symbol": wrapper_symbol,
                "wrapper_address": symbols[wrapper_symbol],
                "object_count": integer(host["object_count"]),
                "x": located["x"], "y": located["y"], "elevation": located["elevation"],
            })
            cursor += len(script)

        args.output_rom.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=args.output_rom.parent, delete=False) as temp:
            temp.write(rom)
            temp_path = Path(temp.name)
        os.replace(temp_path, args.output_rom)
        output_sha = sha(rom)
        metadata = {
            "schema_version": 1,
            "task": "VEGA_ACQUISITION_MAP_HOST_SERIALIZATION",
            "status": "SERIALIZED_REQUIRES_EXACT_ROM_ACCEPTANCE",
            "input_rom": str(args.rom), "input_sha256": observed_input_sha,
            "output_rom": str(args.output_rom), "output_sha256": output_sha,
            "map_groups_root": map_groups_root,
            "allocation_name": "acquisition_map_scripts",
            "allocation_address": allocation_address,
            "allocation_size": allocation_size,
            "allocation_used": cursor - allocation_address,
            "patches": patches,
        }
        args.output_metadata.parent.mkdir(parents=True, exist_ok=True)
        args.output_metadata.write_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, SerializeError) as error:
        print(f"acquisition serializer failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
