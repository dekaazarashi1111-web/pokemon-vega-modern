"""Semantic Stage70 relocation and an exact, separately identified Stage80 repair.

No runtime probe patches its ROM. Stage78 is an immutable parent; the three
reviewed literal words below produce a new candidate before validation starts.
"""
from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any, Mapping, Sequence

ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
PARENT_PATH = "build/stages/78_modernization_p05_eelevate_switch_ai.gba"
PARENT_SHA256 = "98fde60231175492032f0e28ca16549a73ca5b29e3f37438b77c6e3c80e9d06b"
OUTPUT_PATH = "build/stages/80_modernization_runtime_boundary_repair.gba"
REPORT_PATH = "build/stages/80_modernization_runtime_boundary_repair.json"
TASK = "USER-MODERNIZATION-STAGE80-RUNTIME-BOUNDARY-REPAIR"
COLLECTION_ROOT = 0x092D8530
COLLECTION_END = COLLECTION_ROOT + 1621 * 8
NEW_COLLECTION_ROOT = 0x0959D890
NEW_COLLECTION_END = NEW_COLLECTION_ROOT + 1670 * 8
ROOT_SITES = (0x12D12C4, 0x12D1CB0, 0x12D2068)
POLICY_END_SITE = 0x12D12CC
END_SITE = 0x12D12C0
POLICY_START_SITE = 0x12D12D0
UNRELATED_END_VALUE_SITES = (0x12D0E20, 0x12D27DC)
CANDY_ACCESSOR_SITE = 0x137AB5C
BOX_ACCESSOR = 0x0803F4B1
PARTY_ACCESSOR = 0x0803F355

# Pinned Thumb consumer instructions, not a value-only search/replace.
COLLECTION_CODE_GUARDS = {
    0x12D1210: "2b4b2c4d",  # ldr end / ldr start
    0x12D1240: "08359d42e7d1",  # stride 8 and end comparison
    0x12D1246: "214b214d",  # ldr policy end / ldr policy start
    0x12D12A0: "20359d42d2d1",  # policy stride 32 and end comparison
    0x12D1C32: "1f4dc600",  # collection row base and index * 8
    0x12D2026: "104be200",  # collection seen base and index * 8
}
CANDY_CODE_GUARDS = {
    0x137A9EC: "5b4b00f0d5f8",  # is_egg accessor, r3 veneer
    0x137A9F6: "594f00220b21019800f0cef8",  # species, r7 veneer
    0x137AA02: "002238210504019800f0c8f8",  # party level (56)
    0x137AA16: "002206001921019800f0bef8",  # EXP (25)
    0x137AB9C: "18473847",  # bx r3 / bx r7
    0x3F400: "201c5430007850e0",  # GetMonData(56) reads party level
    0x3F624: "50fa0308",  # GetBoxMonData(56) takes default (zero)
}
PATCHES = (
    (END_SITE, COLLECTION_END, NEW_COLLECTION_END, "collection_end"),
    (POLICY_END_SITE, NEW_COLLECTION_ROOT, COLLECTION_ROOT, "restore_policy_end"),
    (CANDY_ACCESSOR_SITE, BOX_ACCESSOR, PARTY_ACCESSOR, "party_candy_accessor"),
)


class BoundaryRepairError(RuntimeError):
    """Unexpected ROM or consumer identity; fail closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryRepairError(message)


def u32(rom: bytes, offset: int) -> int:
    require(0 <= offset <= len(rom) - 4, "literal outside ROM")
    return struct.unpack_from("<I", rom, offset)[0]


def occurrences(rom: bytes, value: int) -> list[int]:
    needle = struct.pack("<I", value)
    sites = []
    start = 0
    while (start := rom.find(needle, start)) >= 0:
        sites.append(start)
        start += 1
    return sites


def guard_code(rom: bytes, guards: Mapping[int, str]) -> None:
    for site, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        require(rom[site:site + len(expected)] == expected,
                f"consumer opcode mismatch at 0x{site:08X}")


def classify_collection_consumers(
    stage: bytes, rows: Sequence[Mapping[str, Any]], table: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Disambiguate equal-valued roots/endpoints on the pinned Stage69 ABI."""
    expected_table = {
        "current_address": COLLECTION_ROOT, "old_count": 1621,
        "new_count": 1670, "stride_bytes": 8,
        "old_size_bytes": 1621 * 8, "new_size_bytes": 1670 * 8,
    }
    require(all(table.get(k) == v for k, v in expected_table.items()),
            "collection table dimensions/identity mismatch")
    expected_sites = sorted((*ROOT_SITES, POLICY_END_SITE))
    require([row["site_offset"] for row in rows] == expected_sites,
            "unclassified, missing or duplicate collection root candidate")
    require(occurrences(stage, COLLECTION_ROOT) == expected_sites,
            "unclassified equal-valued collection root literal")
    require(occurrences(stage, COLLECTION_END) == sorted((*UNRELATED_END_VALUE_SITES, END_SITE)),
            "unclassified equal-valued collection end literal")
    guard_code(stage, COLLECTION_CODE_GUARDS)
    require(u32(stage, POLICY_START_SITE) == 0x092D6C10,
            "policy start identity mismatch")
    result = []
    for row in rows:
        require(row["old_pointer"] == COLLECTION_ROOT
                and u32(stage, row["site_offset"]) == COLLECTION_ROOT,
                "collection consumer preimage mismatch")
        role = "preserve_policy_end" if row["site_offset"] == POLICY_END_SITE else "root"
        result.append({**row, "reference_role": role})
    result.append({"site_offset": END_SITE, "site_address": ROM_BASE + END_SITE,
                   "old_pointer": COLLECTION_END, "reference_role": "collection_end"})
    return sorted(result, key=lambda row: row["site_offset"])


def reference_target(row: Mapping[str, Any], new_root: int, new_size: int) -> int:
    role = row.get("reference_role", "root")
    require(ROM_BASE <= new_root < ROM_BASE + ROM_SIZE
            and 0 < new_size <= ROM_BASE + ROM_SIZE - new_root,
            "relocated table bounds outside ROM")
    if role == "root":
        return new_root
    if role == "collection_end":
        require(row["site_offset"] == END_SITE and row["old_pointer"] == COLLECTION_END,
                "collection end classification mismatch")
        return new_root + new_size
    if role == "preserve_policy_end":
        require(row["site_offset"] == POLICY_END_SITE and row["old_pointer"] == COLLECTION_ROOT,
                "policy end classification mismatch")
        return COLLECTION_ROOT
    raise BoundaryRepairError(f"unknown reference role: {role}")


def validate_relocated_references(
    output: bytes, rows: Sequence[Mapping[str, Any]],
    new_root: int, new_size: int, old_root: int,
) -> None:
    preserved = []
    for row in rows:
        expected = reference_target(row, new_root, new_size)
        require(u32(output, int(row["site_offset"])) == expected,
                "relocated consumer readback mismatch")
        if expected == old_root:
            preserved.append(int(row["site_offset"]))
    require(occurrences(output, old_root) == sorted(preserved),
            "unclassified old root literal remains")


def repair_rom(parent: bytes) -> bytes:
    require(len(parent) == ROM_SIZE, "parent ROM size mismatch")
    require(hashlib.sha256(parent).hexdigest() == PARENT_SHA256,
            "parent ROM SHA-256 mismatch")
    guard_code(parent, COLLECTION_CODE_GUARDS)
    guard_code(parent, CANDY_CODE_GUARDS)
    require(all(u32(parent, site) == NEW_COLLECTION_ROOT for site in ROOT_SITES),
            "collection start consumer mismatch")
    require(u32(parent, POLICY_START_SITE) == 0x092D6C10,
            "policy start identity mismatch")
    require(all(u32(parent, site) == COLLECTION_END for site in UNRELATED_END_VALUE_SITES),
            "unrelated table identity mismatch")
    output = bytearray(parent)
    for site, old, new, role in PATCHES:
        require(u32(parent, site) == old, f"{role} literal preimage mismatch")
        struct.pack_into("<I", output, site, new)
    return bytes(output)


def rom_identity(path: str, rom: bytes) -> dict[str, Any]:
    return {"path": path, "size": len(rom),
            "sha256": hashlib.sha256(rom).hexdigest(),
            "crc32": f"{zlib.crc32(rom) & 0xFFFFFFFF:08X}"}


def make_report(parent: bytes, candidate: bytes) -> dict[str, Any]:
    require(candidate == repair_rom(parent), "candidate differs from exact repair recipe")
    patches = [{"file_offset": site, "address": ROM_BASE + site,
                "old_hex": struct.pack("<I", old).hex(),
                "new_hex": struct.pack("<I", new).hex(), "role": role,
                "changed_bytes": sum(a != b for a, b in zip(struct.pack("<I", old), struct.pack("<I", new)))}
               for site, old, new, role in PATCHES]
    return {"schema_version": 1, "stage": 80, "task": TASK,
            "status": "MATERIALIZED_RUNTIME_ACCEPTANCE_PENDING",
            "parent": rom_identity(PARENT_PATH, parent),
            "output": rom_identity(OUTPUT_PATH, candidate),
            "patches": patches, "changed_bytes": sum(row["changed_bytes"] for row in patches),
            "allocation_layout_unchanged": True,
            "parent_allocation_content_hashes_reused_as_candidate": False,
            "new_allocations": 0,
            "preserved_equal_valued_unrelated_table_sites": list(UNRELATED_END_VALUE_SITES),
            "collection_count": 1670, "collection_stride": 8,
            "active_play_baseline_stage": 62,
            "runtime_acceptance": False, "release_ready": False, "done": False}


def build(root: Path) -> dict[str, Any]:
    parent_path = root / PARENT_PATH
    require(parent_path.is_file() and not parent_path.is_symlink(), "unsafe parent ROM")
    parent = parent_path.read_bytes()
    candidate = repair_rom(parent)
    report = make_report(parent, candidate)
    for relative, data in ((OUTPUT_PATH, candidate), (REPORT_PATH, stable(report))):
        path = root / relative
        require(not path.is_symlink() and not path.parent.is_symlink(), "unsafe output path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    require(parent_path.read_bytes() == parent, "immutable Stage78 parent changed")
    return report


def stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
