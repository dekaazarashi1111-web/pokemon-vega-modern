#!/usr/bin/env python3
"""Validate the linked CFRU battle-script command dispatch tables.

The gate intentionally reads the final ROM bytes.  It does not trust a linker
map alone: the two adjacent table boundaries, every source-fixed entry target,
the five FireRed dispatcher roots, and the secondary-table dispatcher are all
checked against the linked image.
"""

from __future__ import annotations

import hashlib
import json
import struct
from typing import Any, Mapping, NoReturn, Sequence


ROM_BASE = 0x08000000
ROM_MAX_SIZE = 0x02000000
CFRU_PAYLOAD_START = 0x09000000
CFRU_PAYLOAD_END_EXCLUSIVE = 0x09200000

MAIN_SYMBOL = "gBattleScriptingCommandsTable"
SECONDARY_SYMBOL = "gBattleScriptingCommandsTable2"
SECONDARY_BOUNDARY_SYMBOL = "gNaturalGiftTable"
SECONDARY_DISPATCH_SYMBOL = "atkFF_callsecondarytable"

MAIN_ENTRY_COUNT = 0x100
SECONDARY_ENTRY_COUNT = 0x39
DEFAULT_ROOT_SITES = (0x1443C, 0x15240, 0x15480, 0x154AC, 0x1C864)
SECONDARY_NULL_INDICES = (0x00, 0x01, 0x04, 0x05, 0x0B, 0x0D)

# These commands deliberately keep the original FireRed implementation.  All
# remaining main-table commands must resolve through their unique ``atkXX_``
# linked symbol.  Values include the Thumb bit, exactly as emitted by .word.
_MAIN_LITERAL_TARGETS = {
    0x0A: 0x0801ED99,
    0x10: 0x0801F561,
    0x11: 0x0801F5A1,
    0x14: 0x0801F695,
    0x16: 0x08020A21,
    0x17: 0x08020A31,
    0x18: 0x08020A41,
    0x1A: 0x08020DB1,
    0x1C: 0x08020E51,
    0x21: 0x08021199,
    0x24: 0x08021BF9,
    0x25: 0x08021DD9,
    0x26: 0x08021DF1,
    0x28: 0x08021E51,
    0x29: 0x08021E71,
    0x2A: 0x08021F11,
    0x2B: 0x08021FB9,
    0x2C: 0x0802206D,
    0x2D: 0x080220F5,
    0x2E: 0x08022179,
    0x2F: 0x080221A1,
    0x30: 0x080221CD,
    0x31: 0x080221F9,
    0x32: 0x0802224D,
    0x33: 0x080222B9,
    0x34: 0x080222E5,
    0x35: 0x0802231D,
    0x36: 0x08022361,
    0x37: 0x0802238D,
    0x38: 0x080223C5,
    0x39: 0x08022409,
    0x3A: 0x08022449,
    0x3B: 0x08022469,
    0x3C: 0x080224C1,
    0x3D: 0x080224CD,
    0x3E: 0x080224ED,
    0x3F: 0x08022505,
    0x41: 0x08022541,
    0x44: 0x08022619,
    0x4B: 0x08023689,
    0x4C: 0x080236D9,
    0x4E: 0x080238D5,
    0x50: 0x08023BE1,
    0x54: 0x08024911,
    0x55: 0x0802494D,
    0x56: 0x08024989,
    0x57: 0x080249B9,
    0x58: 0x080249F1,
    0x59: 0x08024A25,
    0x5A: 0x08024B71,
    0x5B: 0x08024ED5,
    0x5D: 0x080250A1,
    0x5E: 0x08025259,
    0x5F: 0x0802530D,
    0x60: 0x0802535D,
    0x62: 0x08025455,
    0x65: 0x08025579,
    0x67: 0x080256B5,
    0x68: 0x08025791,
    0x6C: 0x080259F1,
    0x6D: 0x08025FB5,
    0x6E: 0x08025FCD,
    0x6F: 0x08025FED,
    0x71: 0x0802607D,
    0x72: 0x08026095,
    0x73: 0x080260D9,
    0x74: 0x08026185,
    0x75: 0x08026235,
    0x76: 0x0802628D,
    0x79: 0x0802699D,
    0x80: 0x08026E61,
    0x83: 0x08026FF9,
    0x85: 0x08027121,
    0x8B: 0x080278F9,
    0x8C: 0x08027969,
    0x8E: 0x080279F5,
    0x98: 0x08028821,
    0x9A: 0x08028A51,
    0x9C: 0x08028C4D,
    0x9F: 0x08028FD5,
    0xA7: 0x08029785,
    0xAB: 0x08029C31,
    0xAC: 0x08029C49,
    0xB6: 0x0802A5FD,
    0xBF: 0x0802AD19,
    0xC1: 0x0802AE51,
    0xC4: 0x0802B0E9,
    0xC7: 0x0802B40D,
    0xD5: 0x0802BCB5,
    0xD6: 0x0802BD0D,
    0xD9: 0x0802BE49,
    0xDC: 0x0802C04D,
    0xDD: 0x0802C0A5,
    0xDF: 0x0802C2BD,
    0xE0: 0x0802C341,
    0xE3: 0x0802C515,
    0xE6: 0x0802C709,
    0xE9: 0x0802C869,
    0xEC: 0x0802CA79,
    0xED: 0x0802CB3D,
    0xF2: 0x0802D1E9,
    0xF3: 0x0802D535,
    0xF4: 0x0802D7B9,
    0xF5: 0x0802D7E9,
    0xF6: 0x0802D811,
    0xF7: 0x0802D81D,
}
_SECONDARY_LITERAL_TARGETS = {0x11: 0x08028821}

# SHA-256 of the exact, source-order command labels/literals/NULL markers in
# assembly/data/battle_script_commands_table.s.  Prefix discovery below keeps
# this file compact while this digest prevents a renamed/unknown command from
# being silently accepted.
_SOURCE_CONTRACT_SHA256 = "8d8b3747a7eb119243c3b191a6b3388c780c11d397041de94968a4edba10c818"


class CFRUScriptTableGateError(ValueError):
    """The final-ROM script table does not match the frozen CFRU source ABI."""


def _fail(message: str) -> NoReturn:
    raise CFRUScriptTableGateError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _stable_digest(value: object) -> str:
    return _sha256(_stable_bytes(value))


def _validate_offsets(offsets: Mapping[str, int]) -> None:
    if not isinstance(offsets, Mapping):
        _fail("offsets must be a mapping")
    for name, value in offsets.items():
        if not isinstance(name, str) or not name:
            _fail("offset symbol names must be non-empty strings")
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
            _fail(f"offset symbol is not a u32: {name}")


def _symbol_address(offsets: Mapping[str, int], name: str, *, alignment: int) -> int:
    value = offsets.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"required linked symbol is missing: {name}")
    if value % alignment:
        _fail(f"linked symbol alignment mismatch: {name}={value:#010x}")
    return value


def _unique_command_symbol(offsets: Mapping[str, int], prefix: str) -> str:
    matches = sorted(name for name in offsets if name.startswith(prefix))
    if len(matches) != 1:
        _fail(f"source command symbol {prefix} must resolve exactly once, got {matches!r}")
    return matches[0]


def _resolve_source_contract(
    offsets: Mapping[str, int],
) -> tuple[list[int], list[int], list[str], list[str]]:
    main_pointers: list[int] = []
    main_tokens: list[str] = []
    for index in range(MAIN_ENTRY_COUNT):
        literal = _MAIN_LITERAL_TARGETS.get(index)
        if literal is not None:
            main_pointers.append(literal)
            main_tokens.append(f"0x{literal:08X}")
            continue
        name = _unique_command_symbol(offsets, f"atk{index:02X}_")
        address = _symbol_address(offsets, name, alignment=2)
        main_pointers.append(address | 1)
        main_tokens.append(name)

    nulls = set(SECONDARY_NULL_INDICES)
    secondary_pointers: list[int] = []
    secondary_tokens: list[str] = []
    for index in range(SECONDARY_ENTRY_COUNT):
        if index in nulls:
            secondary_pointers.append(0)
            secondary_tokens.append("NULL")
            continue
        literal = _SECONDARY_LITERAL_TARGETS.get(index)
        if literal is not None:
            secondary_pointers.append(literal)
            secondary_tokens.append(f"0x{literal:08X}")
            continue
        name = _unique_command_symbol(offsets, f"atkFF{index:02X}_")
        address = _symbol_address(offsets, name, alignment=2)
        secondary_pointers.append(address | 1)
        secondary_tokens.append(name)

    source_digest = _stable_digest({"main": main_tokens, "secondary": secondary_tokens})
    if source_digest != _SOURCE_CONTRACT_SHA256:
        _fail(
            "linked command symbol set does not match frozen source contract: "
            f"{source_digest} != {_SOURCE_CONTRACT_SHA256}"
        )
    return main_pointers, secondary_pointers, main_tokens, secondary_tokens


def _file_offset(address: int, image_size: int, label: str, size: int = 1) -> int:
    if address < ROM_BASE:
        _fail(f"{label} is below ROM: {address:#010x}")
    offset = address - ROM_BASE
    if offset < 0 or size < 0 or offset + size > image_size:
        _fail(f"{label} is outside linked image: {address:#010x}+{size:#x}")
    return offset


def _target_region(pointer: int, image_size: int, label: str) -> tuple[int, str]:
    if pointer == 0:
        _fail(f"{label} unexpectedly contains NULL")
    if pointer & 1 == 0:
        _fail(f"{label} is not a Thumb pointer: {pointer:#010x}")
    target = pointer & ~1
    image_end = ROM_BASE + image_size
    if ROM_BASE <= target < min(CFRU_PAYLOAD_START, image_end):
        return target, "base_image"
    if CFRU_PAYLOAD_START <= target < min(CFRU_PAYLOAD_END_EXCLUSIVE, image_end):
        return target, "cfru_payload"
    _fail(f"{label} target is outside base image/CFRU payload: {pointer:#010x}")


def _root_sites(value: Sequence[int] | None, image_size: int) -> tuple[int, ...]:
    if value is None:
        roots = DEFAULT_ROOT_SITES
    else:
        if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
            _fail("root_sites must be a sequence of five ROM offsets")
        roots = tuple(value)
    if len(roots) != len(DEFAULT_ROOT_SITES) or len(set(roots)) != len(roots):
        _fail("root_sites must contain exactly five unique ROM offsets")
    for site in roots:
        if isinstance(site, bool) or not isinstance(site, int) or site < 0 or site % 4:
            _fail(f"invalid root site: {site!r}")
        if site + 4 > image_size:
            _fail(f"root site is outside linked image: {site:#x}")
    return roots


def _validate_table(
    image: bytes,
    *,
    name: str,
    address: int,
    expected: Sequence[int],
    source_tokens: Sequence[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    size = len(expected) * 4
    offset = _file_offset(address, len(image), name, size)
    raw = image[offset : offset + size]
    actual = list(struct.unpack(f"<{len(expected)}I", raw))
    snapshots: list[dict[str, Any]] = []
    entry_digests: list[str] = []
    null_indices: list[int] = []
    regions = {"base_image": 0, "cfru_payload": 0, "null": 0}
    for index, (pointer, wanted, source) in enumerate(zip(actual, expected, source_tokens)):
        entry_raw = raw[index * 4 : index * 4 + 4]
        entry_digests.append(_sha256(entry_raw))
        if pointer != wanted:
            _fail(
                f"{name}[{index:#04x}] target mismatch: "
                f"{pointer:#010x} != {wanted:#010x} ({source})"
            )
        if pointer == 0:
            null_indices.append(index)
            regions["null"] += 1
            target: int | None = None
            region = "null"
        else:
            target, region = _target_region(pointer, len(image), f"{name}[{index:#04x}]")
            regions[region] += 1
        snapshots.append(
            {
                "index": index,
                "source_target": source,
                "pointer": pointer,
                "target": target,
                "region": region,
            }
        )
    record = {
        "symbol": name,
        "address": address,
        "rom_offset": offset,
        "entry_count": len(expected),
        "byte_size": size,
        "non_null_count": len(expected) - len(null_indices),
        "null_indices": null_indices,
        "region_counts": regions,
        "table_sha256": _sha256(raw),
        "entry_sha256": entry_digests,
        "target_snapshot_sha256": _stable_digest(snapshots),
    }
    return record, snapshots


def validate_script_command_tables(
    image: bytes,
    offsets: Mapping[str, int],
    root_sites: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Validate both linked command tables and return a metadata snapshot.

    ``offsets`` uses GBA ROM addresses (the format emitted by CFRU's
    ``offsets.ini``).  ``root_sites`` is an explicit five-site test seam; final
    builds should omit it so the frozen FireRed sites are used.
    """

    if not isinstance(image, bytes) or not 0 < len(image) <= ROM_MAX_SIZE:
        _fail("image must be non-empty bytes no larger than 32 MiB")
    _validate_offsets(offsets)
    roots = _root_sites(root_sites, len(image))

    main_address = _symbol_address(offsets, MAIN_SYMBOL, alignment=4)
    secondary_address = _symbol_address(offsets, SECONDARY_SYMBOL, alignment=4)
    boundary_address = _symbol_address(offsets, SECONDARY_BOUNDARY_SYMBOL, alignment=4)
    if secondary_address - main_address != MAIN_ENTRY_COUNT * 4:
        _fail("main table boundary is not exactly 256 entries")
    if boundary_address - secondary_address != SECONDARY_ENTRY_COUNT * 4:
        _fail("secondary table boundary is not exactly 57 entries")

    expected_main, expected_secondary, main_tokens, secondary_tokens = (
        _resolve_source_contract(offsets)
    )
    main_record, main_snapshot = _validate_table(
        image,
        name=MAIN_SYMBOL,
        address=main_address,
        expected=expected_main,
        source_tokens=main_tokens,
    )
    secondary_record, secondary_snapshot = _validate_table(
        image,
        name=SECONDARY_SYMBOL,
        address=secondary_address,
        expected=expected_secondary,
        source_tokens=secondary_tokens,
    )
    if main_record["null_indices"]:
        _fail("main command table must not contain NULL")
    if secondary_record["null_indices"] != list(SECONDARY_NULL_INDICES):
        _fail("secondary command table NULL bitmap changed")

    dispatch_address = _symbol_address(offsets, SECONDARY_DISPATCH_SYMBOL, alignment=2)
    dispatch_pointer = dispatch_address | 1
    if expected_main[0xFF] != dispatch_pointer:
        _fail("source contract main[0xFF] is not the secondary dispatcher")
    actual_dispatch = struct.unpack_from(
        "<I", image, main_record["rom_offset"] + 0xFF * 4
    )[0]
    if actual_dispatch != dispatch_pointer:
        _fail("linked main[0xFF] is not the secondary dispatcher")

    root_records: list[dict[str, int]] = []
    for site in roots:
        actual = struct.unpack_from("<I", image, site)[0]
        if actual != main_address:
            _fail(
                f"battle-script root {site:#x} does not target main table: "
                f"{actual:#010x} != {main_address:#010x}"
            )
        root_records.append({"rom_offset": site, "pointer": actual})

    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "PASS",
        "source_contract": {
            "sha256": _SOURCE_CONTRACT_SHA256,
            "main_entry_count": MAIN_ENTRY_COUNT,
            "secondary_entry_count": SECONDARY_ENTRY_COUNT,
            "secondary_null_indices": list(SECONDARY_NULL_INDICES),
            "secondary_boundary_symbol": SECONDARY_BOUNDARY_SYMBOL,
        },
        "image": {
            "size": len(image),
            "sha256": _sha256(image),
            "rom_base": ROM_BASE,
            "cfru_payload_start": CFRU_PAYLOAD_START,
            "cfru_payload_end_exclusive": CFRU_PAYLOAD_END_EXCLUSIVE,
        },
        "tables": {"main": main_record, "secondary": secondary_record},
        "dispatch": {
            "main_index": 0xFF,
            "symbol": SECONDARY_DISPATCH_SYMBOL,
            "symbol_address": dispatch_address,
            "pointer": actual_dispatch,
            "secondary_table_address": secondary_address,
        },
        "roots": {
            "uses_default_sites": root_sites is None,
            "count": len(root_records),
            "records": root_records,
            "sha256": _stable_digest(root_records),
        },
        "target_snapshot": {
            "main": main_snapshot,
            "secondary": secondary_snapshot,
        },
    }
    report["snapshot_sha256"] = _stable_digest(report)
    return report


__all__ = [
    "CFRUScriptTableGateError",
    "DEFAULT_ROOT_SITES",
    "MAIN_ENTRY_COUNT",
    "SECONDARY_ENTRY_COUNT",
    "SECONDARY_NULL_INDICES",
    "validate_script_command_tables",
]
