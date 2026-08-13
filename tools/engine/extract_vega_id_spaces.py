#!/usr/bin/env python3
"""固定Vega ROMからType/Ability/Itemの凍結snapshotを抽出する。

探索や推測ではなく、既知のpointer site、table ABI、table SHA-256、
ROM/charmap SHA-256をすべて検証してからJSON-compatibleな値を返す。
成功結果には時刻、絶対path、ROMの未解釈dumpを含めない。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
import sys
import unicodedata
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROM_BASE = 0x08000000
TYPE_COUNT = 18
ABILITY_COUNT = 78
ITEM_COUNT = 375
TYPE_EFFECTIVENESS_RAW_ENTRY_COUNT = 112
TYPE_DISPLAY_ICON_COUNT = 24
ITEM_ICON_COUNT = 376  # 0..374のitemに加え、bag UI用の1 entryを含む。


class VegaIdSpaceExtractionError(ValueError):
    """ROM、policy、または既存table ABIが固定条件に一致しない。"""


_DEFAULT_POLICY: dict[str, Any] = {
    "policy_id": "fixed_vega_type_ability_item_tables_v1",
    "rom": {
        "logical_path": "build/reference/vega.gba",
        "size": 16_777_216,
        "sha256": "f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5",
    },
    "charmap": {
        "logical_path": "vendor/upstream/CFRU-JP/charmap.tbl",
        "sha256": "35c1b978f7004129679751a79cf4b40d7edd2fcd678bc81a29483b64b75b7ed5",
    },
    "tables": {
        "type_effectiveness": {
            "address": 0x0820BF24,
            "count": TYPE_EFFECTIVENESS_RAW_ENTRY_COUNT,
            "record_size": 3,
            "pointer_sites": [
                0x0801E154,
                0x0801E294,
                0x0801E368,
                0x0801E6CC,
                0x0801E7D0,
                0x0801E8D0,
                0x080234D8,
                0x08029768,
                0x080395A4,
            ],
            "sha256": "41c4a8c8f45ae719ee04912c7ae3b6e5ae75a83ec9a270e7555bd6eefa4943da",
        },
        "type_names": {
            "address": 0x0820C074,
            "count": TYPE_COUNT,
            "record_size": 5,
            "pointer_sites": [
                0x08030134,
                0x080D9564,
                0x0811A028,
                0x0811A064,
                0x084172B0,
            ],
            "sha256": "fd4e05ee334070d8340ffb3bbcd76a721856fba0989e839dd4c430cf9ac3c31b",
        },
        "type_display_icons": {
            "address": 0x08411AFC,
            "count": TYPE_DISPLAY_ICON_COUNT,
            "record_size": 4,
            "pointer_sites": [0x081088B0],
            "sha256": "71e0f0e3cd892bab58f90ddd335541e951e06358adbb9e8714c0b559ebfd190b",
        },
        "ability_names": {
            "address": 0x0820C274,
            "count": ABILITY_COUNT,
            "record_size": 8,
            "pointer_sites": [0x080001C0, 0x080D9014, 0x080D9674, 0x08136F88],
            "sha256": "3883202b824720f2f6ad8d014fb1b4485b4e03c159e01bec13b6fce993e88a13",
        },
        "ability_descriptions": {
            "address": 0x0820C4E4,
            "count": ABILITY_COUNT,
            "record_size": 19,
            "pointer_sites": [0x080001C4, 0x08136F90],
            "sha256": "06e5765da56ac3b80c185b78144ae34b4a77aa55e7a49e26ba00baf6351f8969",
        },
        "items": {
            "address": 0x083A06F8,
            "count": ITEM_COUNT,
            "record_size": 40,
            "pointer_sites": [
                0x080001C8,
                0x0809A2E4,
                0x0809A308,
                0x0809A32C,
                0x0809A350,
                0x0809A374,
                0x0809A39C,
                0x0809A3C0,
                0x0809A3E4,
                0x0809A408,
                0x0809A42C,
                0x0809A454,
                0x0809A478,
                0x0809A4A0,
                0x0809A4C8,
            ],
            "sha256": "f56c68ce99fddcf6f191e96c5bd5fb470d25735f22bb21bf9caf08fd929119c5",
        },
        "item_icons": {
            "address": 0x0839C79C,
            "count": ITEM_ICON_COUNT,
            "record_size": 8,
            "pointer_sites": [0x080981FC, 0x080982DC, 0x080983A4],
            "sha256": "f4049fe0d890b0a226c45282657368b6e3e8329b95a8959a7d41a80eb5667552",
        },
    },
    "roots": {
        "type_display_palette": {
            "address": 0x08411B7C,
            "pointer_sites": [0x08108868],
        },
        "type_display_tiles": {
            "address": 0x08411B9C,
            "pointer_sites": [0x081088B4],
        },
    },
    "limits": {"item_description_bytes_including_terminator": 256},
}


def default_policy() -> dict[str, Any]:
    """固定Vega reference用policyの独立コピーを返す。"""

    return copy.deepcopy(_DEFAULT_POLICY)


def _fail(message: str) -> NoReturn:
    raise VegaIdSpaceExtractionError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _as_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} must be an object")
    return value


def _as_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{label} must be an integer")
    return value


def _as_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        _fail(f"{label} must be a 64-character lowercase SHA-256")
    if value.lower() != value or any(character not in "0123456789abcdef" for character in value):
        _fail(f"{label} must be a 64-character lowercase SHA-256")
    return value


def _merge_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    """部分overrideまたはconfigの``vega`` sectionを厳密にmergeする。"""

    if policy is None:
        return default_policy()
    supplied = _as_mapping(policy, "policy")
    if "vega" in supplied:
        # build側がconfig/id_spaces.json全体を渡してもよい。ほかのsectionは
        # 別domainだが、同configのcharmap固定値だけは取り込む。
        outer = supplied
        supplied = _as_mapping(outer["vega"], "policy.vega")
        outer_charmap = outer.get("charmap")
    else:
        outer_charmap = None

    flat_vega_keys = {
        "rom_path",
        "rom_size",
        "rom_sha256",
        "frozen_type_count",
        "frozen_ability_count",
        "frozen_item_count",
    }
    if set(supplied) & flat_vega_keys:
        unknown = set(supplied) - flat_vega_keys
        if unknown:
            _fail(f"unknown policy.vega keys: {sorted(unknown)}")
        required = flat_vega_keys
        missing = required - set(supplied)
        if missing:
            _fail(f"missing policy.vega keys: {sorted(missing)}")
        expected_counts = {
            "frozen_type_count": TYPE_COUNT,
            "frozen_ability_count": ABILITY_COUNT,
            "frozen_item_count": ITEM_COUNT,
        }
        for key, expected in expected_counts.items():
            actual = _as_int(supplied[key], f"policy.vega.{key}")
            if actual != expected:
                _fail(f"policy.vega.{key} must be {expected}, got {actual}")
        adapted: dict[str, Any] = {
            "rom": {
                "logical_path": supplied["rom_path"],
                "size": supplied["rom_size"],
                "sha256": supplied["rom_sha256"],
            }
        }
        if outer_charmap is not None:
            charmap_section = _as_mapping(outer_charmap, "policy.charmap")
            unknown_charmap = set(charmap_section) - {"path", "sha256"}
            if unknown_charmap:
                _fail(f"unknown policy.charmap keys: {sorted(unknown_charmap)}")
            if set(charmap_section) != {"path", "sha256"}:
                _fail("policy.charmap must contain exactly path and sha256")
            adapted["charmap"] = {
                "logical_path": charmap_section["path"],
                "sha256": charmap_section["sha256"],
            }
        supplied = adapted

    result = default_policy()

    def merge(destination: dict[str, Any], source: Mapping[str, Any], path: str) -> None:
        unknown = set(source) - set(destination)
        if unknown:
            _fail(f"unknown {path} keys: {sorted(unknown)}")
        for key, value in source.items():
            if isinstance(destination[key], dict):
                merge(destination[key], _as_mapping(value, f"{path}.{key}"), f"{path}.{key}")
            else:
                destination[key] = copy.deepcopy(value)

    merge(result, supplied, "policy")
    return result


class _Rom:
    def __init__(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            _fail("rom must be bytes")
        self.data = data

    @property
    def end_address(self) -> int:
        return ROM_BASE + len(self.data)

    def offset(self, address: int, size: int, label: str) -> int:
        if address < ROM_BASE or size < 0:
            _fail(f"{label} is outside the ROM")
        offset = address - ROM_BASE
        if offset > len(self.data) or size > len(self.data) - offset:
            _fail(f"{label} is outside the ROM")
        return offset

    def read(self, address: int, size: int, label: str) -> bytes:
        offset = self.offset(address, size, label)
        return self.data[offset : offset + size]

    def u32(self, address: int, label: str) -> int:
        if address & 3:
            _fail(f"{label} is not 4-byte aligned")
        return struct.unpack("<I", self.read(address, 4, label))[0]

    def require_rom_pointer(self, pointer: int, label: str, *, nullable: bool = False) -> None:
        if pointer == 0 and nullable:
            return
        # callbackはThumb bitを持ち得る。data pointerは偶数だが、この検査では
        # 範囲だけを共通に保証し、table固有のalignmentは呼出側で検査する。
        target = pointer & ~1
        if target < ROM_BASE or target >= self.end_address:
            _fail(f"{label} is not a ROM pointer: 0x{pointer:08X}")

    def read_terminated(self, address: int, limit: int, label: str) -> bytes:
        self.require_rom_pointer(address, label)
        if limit <= 0:
            _fail(f"{label} limit must be positive")
        available = min(limit, self.end_address - address)
        raw = self.read(address, available, label)
        try:
            end = raw.index(0xFF)
        except ValueError:
            _fail(f"{label} has no 0xFF terminator within {limit} bytes")
        return raw[: end + 1]


def _logical_path(root: Path, value: object, label: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        _fail(f"{label} must be a non-empty relative path")
    root_resolved = root.resolve()
    path = (root_resolved / value).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError:
        _fail(f"{label} escapes root")
    return value, path


def _read_charmap(root: Path, policy: Mapping[str, Any]) -> tuple[dict[int, str], dict[str, Any]]:
    logical, path = _logical_path(root, policy.get("logical_path"), "policy.charmap.logical_path")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail(f"cannot read fixed charmap: {exc}")
    expected_sha = _as_sha256(policy.get("sha256"), "policy.charmap.sha256")
    actual_sha = _sha256(raw)
    if actual_sha != expected_sha:
        _fail(f"charmap sha256 mismatch: expected {expected_sha}, got {actual_sha}")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        _fail(f"charmap is not UTF-8: {exc}")
    mapping: dict[int, str] = {}
    escapes = {r"\n": "\n", r"\l": "<SCROLL>", r"\p": "<PAGE>", r"\$": "$", r'\"': '"'}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("/"):
            continue
        if len(line) < 3 or line[2] != "=":
            _fail(f"unsupported charmap line {line_number}")
        try:
            key = int(line[:2], 16)
        except ValueError:
            _fail(f"invalid charmap byte on line {line_number}")
        mapping[key] = escapes.get(line[3:], line[3:])
    if mapping.get(0xFF) != "$" or mapping.get(0xFE) != "\n":
        _fail("charmap terminator/newline ABI mismatch")
    return mapping, {"logical_path": logical, "sha256": actual_sha, "encoding": "CFRU-JP/charmap.tbl"}


def _decode_terminated(raw: bytes, charmap: Mapping[int, str], label: str) -> tuple[str, int]:
    try:
        terminator = raw.index(0xFF)
    except ValueError:
        _fail(f"{label} has no 0xFF terminator")
    decoded: list[str] = []
    for index, byte in enumerate(raw[:terminator]):
        if byte not in charmap:
            _fail(f"{label} uses unmapped byte 0x{byte:02X} at +0x{index:X}")
        decoded.append(charmap[byte])
    return "".join(decoded), terminator


def _line_encoded_widths(raw: bytes) -> list[int]:
    """終端を除く1-byte encodingの各表示行長を返す。"""

    content = raw[: raw.index(0xFF)]
    return [len(line) for line in content.split(b"\xFE")]


def normalize_display_name(name: str) -> str:
    """join用にNFKC化し、表示上の空白だけを除く。"""

    if not isinstance(name, str):
        _fail("display name must be a string")
    return "".join(character for character in unicodedata.normalize("NFKC", name) if not character.isspace())


def _table_config(policy: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    tables = _as_mapping(policy.get("tables"), "policy.tables")
    return _as_mapping(tables.get(name), f"policy.tables.{name}")


def _validate_table(
    rom: _Rom,
    policy: Mapping[str, Any],
    name: str,
    *,
    required_count: int,
    required_record_size: int,
) -> tuple[bytes, dict[str, Any]]:
    config = _table_config(policy, name)
    address = _as_int(config.get("address"), f"policy.tables.{name}.address")
    count = _as_int(config.get("count"), f"policy.tables.{name}.count")
    record_size = _as_int(config.get("record_size"), f"policy.tables.{name}.record_size")
    if count != required_count or record_size != required_record_size:
        _fail(
            f"{name} ABI mismatch: expected {required_count} x {required_record_size}, "
            f"got {count} x {record_size}"
        )
    if address & 3:
        _fail(f"{name} table is not 4-byte aligned")
    sites_value = config.get("pointer_sites")
    if not isinstance(sites_value, Sequence) or isinstance(sites_value, (str, bytes)) or not sites_value:
        _fail(f"policy.tables.{name}.pointer_sites must be a non-empty array")
    sites = [_as_int(value, f"policy.tables.{name}.pointer_sites") for value in sites_value]
    if len(sites) != len(set(sites)):
        _fail(f"{name} pointer sites contain duplicates")
    pointer_rows: list[dict[str, int]] = []
    for site in sites:
        actual = rom.u32(site, f"{name} pointer site 0x{site:08X}")
        if actual != address:
            _fail(
                f"{name} pointer mismatch at 0x{site:08X}: "
                f"expected 0x{address:08X}, got 0x{actual:08X}"
            )
        pointer_rows.append({"site_address": site, "target_address": actual})
    size = count * record_size
    raw = rom.read(address, size, f"{name} table")
    expected_sha = _as_sha256(config.get("sha256"), f"policy.tables.{name}.sha256")
    actual_sha = _sha256(raw)
    if actual_sha != expected_sha:
        _fail(f"{name} table sha256 mismatch: expected {expected_sha}, got {actual_sha}")
    return raw, {
        "address": address,
        "end_address_exclusive": address + size,
        "count": count,
        "record_size": record_size,
        "sha256": actual_sha,
        "pointer_sites": pointer_rows,
    }


def _validate_pointer_root(rom: _Rom, policy: Mapping[str, Any], name: str) -> dict[str, Any]:
    roots = _as_mapping(policy.get("roots"), "policy.roots")
    config = _as_mapping(roots.get(name), f"policy.roots.{name}")
    address = _as_int(config.get("address"), f"policy.roots.{name}.address")
    rom.require_rom_pointer(address, f"{name} target")
    sites_value = config.get("pointer_sites")
    if not isinstance(sites_value, Sequence) or isinstance(sites_value, (str, bytes)) or not sites_value:
        _fail(f"policy.roots.{name}.pointer_sites must be a non-empty array")
    sites = [_as_int(value, f"policy.roots.{name}.pointer_sites") for value in sites_value]
    if len(sites) != len(set(sites)):
        _fail(f"{name} pointer sites contain duplicates")
    rows: list[dict[str, int]] = []
    for site in sites:
        actual = rom.u32(site, f"{name} pointer site 0x{site:08X}")
        if actual != address:
            _fail(
                f"{name} pointer mismatch at 0x{site:08X}: "
                f"expected 0x{address:08X}, got 0x{actual:08X}"
            )
        rows.append({"site_address": site, "target_address": actual})
    return {"address": address, "pointer_sites": rows}


def _extract_type_effectiveness(raw: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """sparse ABIからmarker/terminatorを除いた再構築可能な正規形を作る。"""

    marker_index: int | None = None
    terminator_index: int | None = None
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[int, int, bool]] = set()
    after_foresight_marker = False
    for raw_index in range(TYPE_EFFECTIVENESS_RAW_ENTRY_COUNT):
        entry = raw[raw_index * 3 : raw_index * 3 + 3]
        attacking, defending, multiplier = entry
        if attacking == 0xFE or defending == 0xFE:
            if entry != b"\xFE\xFE\x00" or marker_index is not None or terminator_index is not None:
                _fail(f"invalid or duplicate type effectiveness foresight marker at row {raw_index}")
            marker_index = raw_index
            after_foresight_marker = True
            continue
        if attacking == 0xFF or defending == 0xFF:
            if entry != b"\xFF\xFF\x00" or terminator_index is not None:
                _fail(f"invalid or duplicate type effectiveness terminator at row {raw_index}")
            terminator_index = raw_index
            if raw_index != TYPE_EFFECTIVENESS_RAW_ENTRY_COUNT - 1:
                _fail("type effectiveness terminator is not the last fixed entry")
            continue
        if terminator_index is not None:
            _fail("type effectiveness contains data after its terminator")
        if attacking >= TYPE_COUNT or defending >= TYPE_COUNT:
            _fail(f"type effectiveness row {raw_index} uses a non-frozen type ID")
        if multiplier not in (0, 5, 20):
            _fail(f"type effectiveness row {raw_index} has unsupported multiplier {multiplier}")
        key = (attacking, defending, after_foresight_marker)
        if key in seen:
            _fail(f"duplicate normalized type effectiveness row {key}")
        seen.add(key)
        normalized.append(
            {
                "attacking_type_id": attacking,
                "defending_type_id": defending,
                "multiplier_tenths": multiplier,
                "foresight_bypassable": after_foresight_marker,
                "raw_entry_index": raw_index,
                "raw_hex": entry.hex(),
            }
        )
    if marker_index is None or terminator_index is None:
        _fail("type effectiveness marker/terminator is missing")
    if not normalized or not any(row["foresight_bypassable"] for row in normalized):
        _fail("type effectiveness has no post-Foresight semantic entries")
    return normalized, {
        "raw_entry_count": TYPE_EFFECTIVENESS_RAW_ENTRY_COUNT,
        "semantic_entry_count": len(normalized),
        "foresight_marker_index": marker_index,
        "terminator_index": terminator_index,
        "default_multiplier_tenths": 10,
        "normalization": "marker and terminator removed; post-marker rows tagged foresight_bypassable",
    }


def extract_vega_id_spaces(root: Path, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """固定ROMからType/Ability/Itemの全既存IDを決定的に抽出する。"""

    if not isinstance(root, Path):
        _fail("root must be pathlib.Path")
    merged = _merge_policy(policy)
    rom_config = _as_mapping(merged.get("rom"), "policy.rom")
    logical_rom, rom_path = _logical_path(root, rom_config.get("logical_path"), "policy.rom.logical_path")
    try:
        rom_bytes = rom_path.read_bytes()
    except OSError as exc:
        _fail(f"cannot read fixed Vega ROM: {exc}")
    expected_size = _as_int(rom_config.get("size"), "policy.rom.size")
    if len(rom_bytes) != expected_size:
        _fail(f"Vega ROM size mismatch: expected {expected_size}, got {len(rom_bytes)}")
    expected_sha = _as_sha256(rom_config.get("sha256"), "policy.rom.sha256")
    actual_sha = _sha256(rom_bytes)
    if actual_sha != expected_sha:
        _fail(f"Vega ROM sha256 mismatch: expected {expected_sha}, got {actual_sha}")
    rom = _Rom(rom_bytes)
    charmap, charmap_metadata = _read_charmap(root, _as_mapping(merged.get("charmap"), "policy.charmap"))

    type_effectiveness_raw, type_effectiveness_info = _validate_table(
        rom,
        merged,
        "type_effectiveness",
        required_count=TYPE_EFFECTIVENESS_RAW_ENTRY_COUNT,
        required_record_size=3,
    )
    type_names_raw, type_names_info = _validate_table(
        rom, merged, "type_names", required_count=TYPE_COUNT, required_record_size=5
    )
    type_icons_raw, type_icons_info = _validate_table(
        rom,
        merged,
        "type_display_icons",
        required_count=TYPE_DISPLAY_ICON_COUNT,
        required_record_size=4,
    )
    ability_names_raw, ability_names_info = _validate_table(
        rom, merged, "ability_names", required_count=ABILITY_COUNT, required_record_size=8
    )
    ability_descriptions_raw, ability_descriptions_info = _validate_table(
        rom,
        merged,
        "ability_descriptions",
        required_count=ABILITY_COUNT,
        required_record_size=19,
    )
    items_raw, items_info = _validate_table(
        rom, merged, "items", required_count=ITEM_COUNT, required_record_size=40
    )
    item_icons_raw, item_icons_info = _validate_table(
        rom, merged, "item_icons", required_count=ITEM_ICON_COUNT, required_record_size=8
    )
    roots_info = {
        name: _validate_pointer_root(rom, merged, name)
        for name in ("type_display_palette", "type_display_tiles")
    }

    if type_effectiveness_info["end_address_exclusive"] != type_names_info["address"]:
        _fail("type_effectiveness end does not equal type_names start")
    if ability_names_info["end_address_exclusive"] != ability_descriptions_info["address"]:
        _fail("ability_names end does not equal ability_descriptions start")

    type_effectiveness, normalization_info = _extract_type_effectiveness(type_effectiveness_raw)
    type_effectiveness_info["boundary_evidence"] = normalization_info

    types: list[dict[str, Any]] = []
    type_name_lengths: list[int] = []
    for type_id in range(TYPE_COUNT):
        name_raw = type_names_raw[type_id * 5 : (type_id + 1) * 5]
        name_decoded, name_length = _decode_terminated(name_raw, charmap, f"type {type_id} name")
        # gMoveMenuInfoIcons[0]はunusedで、type ID nはicon index n+1を使う。
        icon_index = type_id + 1
        icon_raw = type_icons_raw[icon_index * 4 : (icon_index + 1) * 4]
        icon_width, icon_height, icon_tile_offset = struct.unpack("<BBH", icon_raw)
        if icon_width == 0 or icon_height == 0:
            _fail(f"type {type_id} display icon has a zero dimension")
        type_name_lengths.append(name_length)
        types.append(
            {
                "id": type_id,
                "name_raw": name_raw.hex(),
                "name_decoded": name_decoded,
                "normalized_name": normalize_display_name(name_decoded),
                "name_encoded_length": name_length,
                "name_line_encoded_widths": _line_encoded_widths(name_raw),
                "display_icon_index": icon_index,
                "display_icon_width": icon_width,
                "display_icon_height": icon_height,
                "display_icon_tile_offset": icon_tile_offset,
                "display_icon_raw": icon_raw.hex(),
                "evidence": {
                    "name_address": type_names_info["address"] + type_id * 5,
                    "display_icon_address": type_icons_info["address"] + icon_index * 4,
                    "name_terminator_offset": name_length,
                },
            }
        )

    abilities: list[dict[str, Any]] = []
    ability_name_lengths: list[int] = []
    ability_description_lengths: list[int] = []
    for ability_id in range(ABILITY_COUNT):
        name_raw = ability_names_raw[ability_id * 8 : (ability_id + 1) * 8]
        description_raw = ability_descriptions_raw[ability_id * 19 : (ability_id + 1) * 19]
        name_decoded, name_length = _decode_terminated(name_raw, charmap, f"ability {ability_id} name")
        description_decoded, description_length = _decode_terminated(
            description_raw, charmap, f"ability {ability_id} description"
        )
        ability_name_lengths.append(name_length)
        ability_description_lengths.append(description_length)
        abilities.append(
            {
                "id": ability_id,
                "name_raw": name_raw.hex(),
                "name_decoded": name_decoded,
                "normalized_name": normalize_display_name(name_decoded),
                "name_encoded_length": name_length,
                "name_line_encoded_widths": _line_encoded_widths(name_raw),
                "description_raw": description_raw.hex(),
                "description_decoded": description_decoded,
                "description_encoded_length": description_length,
                "description_line_encoded_widths": _line_encoded_widths(description_raw),
                "evidence": {
                    "name_address": ability_names_info["address"] + ability_id * 8,
                    "description_address": ability_descriptions_info["address"] + ability_id * 19,
                    "name_terminator_offset": name_length,
                    "description_terminator_offset": description_length,
                },
            }
        )

    limit_config = _as_mapping(merged.get("limits"), "policy.limits")
    description_limit = _as_int(
        limit_config.get("item_description_bytes_including_terminator"),
        "policy.limits.item_description_bytes_including_terminator",
    )
    items: list[dict[str, Any]] = []
    item_name_lengths: list[int] = []
    item_description_lengths: list[int] = []
    occupied_count = 0
    for item_index in range(ITEM_COUNT):
        raw = items_raw[item_index * 40 : (item_index + 1) * 40]
        (
            name_raw,
            item_id,
            price,
            hold_effect,
            hold_effect_param,
            description_pointer,
            importance,
            registrability,
            pocket,
            field_use_type,
            field_callback_pointer,
            battle_usage,
            battle_callback_pointer,
            secondary_id,
        ) = struct.unpack("<10sHHBBIBBBBIB3xIB3x", raw)
        if item_id not in (0, item_index):
            _fail(f"item table row {item_index} carries noncanonical itemId {item_id}")
        if raw[29:32] != b"\x00\x00\x00" or raw[37:40] != b"\x00\x00\x00":
            _fail(f"item table row {item_index} has nonzero ABI padding")
        rom.require_rom_pointer(description_pointer, f"item {item_index} description")
        rom.require_rom_pointer(field_callback_pointer, f"item {item_index} field callback", nullable=True)
        rom.require_rom_pointer(battle_callback_pointer, f"item {item_index} battle callback", nullable=True)
        description_raw = rom.read_terminated(
            description_pointer, description_limit, f"item {item_index} description"
        )
        name_decoded, name_length = _decode_terminated(name_raw, charmap, f"item {item_index} name")
        description_decoded, description_length = _decode_terminated(
            description_raw, charmap, f"item {item_index} description"
        )

        icon_raw = item_icons_raw[item_index * 8 : (item_index + 1) * 8]
        icon_pointer, palette_pointer = struct.unpack("<II", icon_raw)
        rom.require_rom_pointer(icon_pointer, f"item {item_index} icon")
        rom.require_rom_pointer(palette_pointer, f"item {item_index} palette")
        slot_state = "none" if item_index == 0 else ("unused" if item_id == 0 else "defined")
        if slot_state == "defined":
            occupied_count += 1
        item_name_lengths.append(name_length)
        item_description_lengths.append(description_length)
        items.append(
            {
                "id": item_index,
                "item_id": item_id,
                "slot_state": slot_state,
                "name_raw": name_raw.hex(),
                "name_decoded": name_decoded,
                "normalized_name": normalize_display_name(name_decoded),
                "name_encoded_length": name_length,
                "name_line_encoded_widths": _line_encoded_widths(name_raw),
                "price": price,
                "hold_effect": hold_effect,
                "hold_effect_param": hold_effect_param,
                "description_pointer": description_pointer,
                "description_raw": description_raw.hex(),
                "description_decoded": description_decoded,
                "description_encoded_length": description_length,
                "description_line_encoded_widths": _line_encoded_widths(description_raw),
                "importance": importance,
                "registrability": registrability,
                "pocket": pocket,
                "field_use_type": field_use_type,
                "field_callback_pointer": field_callback_pointer,
                "battle_usage": battle_usage,
                "battle_callback_pointer": battle_callback_pointer,
                "secondary_id": secondary_id,
                "icon_pointer": icon_pointer,
                "palette_pointer": palette_pointer,
                "icon_entry_raw": icon_raw.hex(),
                "raw_hex": raw.hex(),
                "evidence": {
                    "record_address": items_info["address"] + item_index * 40,
                    "icon_entry_address": item_icons_info["address"] + item_index * 8,
                    "name_terminator_offset": name_length,
                    "description_terminator_offset": description_length,
                },
            }
        )

    if [row["id"] for row in types] != list(range(TYPE_COUNT)):
        _fail("type IDs are not the exact contiguous range 0..17")
    if [row["id"] for row in abilities] != list(range(ABILITY_COUNT)):
        _fail("ability IDs are not the exact contiguous range 0..77")
    if [row["id"] for row in items] != list(range(ITEM_COUNT)):
        _fail("item IDs are not the exact contiguous range 0..374")

    type_icons_info["frozen_type_icon_indices"] = {"first": 1, "last": TYPE_COUNT}
    item_icons_info["frozen_item_icon_count"] = ITEM_COUNT
    item_icons_info["extra_ui_entry_count"] = ITEM_ICON_COUNT - ITEM_COUNT
    metadata = {
        "schema_version": 1,
        "policy_id": merged["policy_id"],
        "rom": {"logical_path": logical_rom, "size": len(rom_bytes), "sha256": actual_sha},
        "charmap": charmap_metadata,
        "method": "fixed pointer sites + table ABI/count + per-table SHA-256 + ROM SHA-256",
        "tables": {
            "type_effectiveness": type_effectiveness_info,
            "type_names": type_names_info,
            "type_display_icons": type_icons_info,
            "ability_names": ability_names_info,
            "ability_descriptions": ability_descriptions_info,
            "items": items_info,
            "item_icons": item_icons_info,
        },
        "roots": roots_info,
        "counts": {
            "types": len(types),
            "abilities": len(abilities),
            "item_slots": len(items),
            "defined_items_excluding_none": occupied_count,
            "unused_item_slots": sum(row["slot_state"] == "unused" for row in items),
            "type_effectiveness_semantic_entries": len(type_effectiveness),
        },
        "encoded_widths": {
            "type_name_record_bytes": 5,
            "type_name_min": min(type_name_lengths),
            "type_name_max": max(type_name_lengths),
            "ability_name_record_bytes": 8,
            "ability_name_min": min(ability_name_lengths),
            "ability_name_max": max(ability_name_lengths),
            "ability_description_record_bytes": 19,
            "ability_description_min": min(ability_description_lengths),
            "ability_description_max": max(ability_description_lengths),
            "item_name_record_bytes": 10,
            "item_name_min": min(item_name_lengths),
            "item_name_max": max(item_name_lengths),
            "item_description_min": min(item_description_lengths),
            "item_description_max": max(item_description_lengths),
            "item_description_line_max": max(
                max(row["description_line_encoded_widths"]) for row in items
            ),
            "item_description_line_count_max": max(
                len(row["description_line_encoded_widths"]) for row in items
            ),
        },
    }
    return {
        "metadata": metadata,
        "types": types,
        "abilities": abilities,
        "items": items,
        "type_effectiveness": type_effectiveness,
    }


def _load_json_policy(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"cannot read policy JSON: {exc}")
    return _as_mapping(value, "policy JSON")


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract fixed Vega Type/Ability/Item tables as JSON")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root",
    )
    parser.add_argument("--policy", type=Path, help="optional JSON policy (direct or top-level vega section)")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        policy = _load_json_policy(args.policy) if args.policy else None
        result = extract_vega_id_spaces(root, policy)
    except VegaIdSpaceExtractionError as exc:
        print(f"extract-vega-id-spaces: {exc}", file=sys.stderr)
        return 2
    json.dump(
        result,
        sys.stdout,
        ensure_ascii=False,
        sort_keys=True,
        indent=2 if args.pretty else None,
        separators=None if args.pretty else (",", ":"),
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
