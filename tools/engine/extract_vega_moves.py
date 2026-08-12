#!/usr/bin/env python3
"""Vega参照ROMから、pointer-rootedな技関連表を決定的に抽出する。

ROMハッシュに加え、実際のrepoint word、隣接表の境界、各pointerを
失敗閉塞で検証する。成功時の戻り値はJSON-compatibleで、時刻や
絶対pathを含まない。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
import sys
import tomllib
import unicodedata
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROM_BASE = 0x08000000
MOVE_COUNT = 512
EFFECT_COUNT = 256


class VegaMoveExtractionError(ValueError):
    """ROM、policy、table ABIのいずれかが固定条件に合わない。"""


_DEFAULT_POLICY: dict[str, Any] = {
    "policy_id": "fixed_vega_move_tables_v1",
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
        "move_names": {
            "address": 0x08E0BBB0,
            "count": MOVE_COUNT,
            "record_size": 8,
            "pointer_sites": [0x08000148, 0x0804E7B4],
            "sha256": "cc18482c20e9783525786a2b224987ccc1175a2617a133d32de4a99966dd01c4",
        },
        "battle_moves": {
            "address": 0x08E0CBB0,
            "count": MOVE_COUNT,
            "record_size": 12,
            "pointer_sites": [0x080001CC, 0x08015B7C],
            "sha256": "269e3fc9803b3edbec8d6b78cfa457d7d8c9c8e307c11a647b9031bdf01b1708",
        },
        "descriptions": {
            "address": 0x08E0E3B0,
            "count": MOVE_COUNT,
            "record_size": 60,
            "pointer_sites": [0x080E63F0, 0x081383A4],
            "sha256": "a60e869d5041a0f0fd2f2adea3640a771f34a156019f7445757e81f9acc7ef14",
        },
        "animations": {
            "address": 0x08E15BB0,
            "count": MOVE_COUNT,
            "record_size": 4,
            "pointer_sites": [0x08071D74],
            "sha256": "a40a92b18005209d68902ec5f0ce31e95af9bcfc6707aac895e5d156ed8387bd",
        },
        "effects": {
            "address": 0x08E165D0,
            "count": EFFECT_COUNT,
            "record_size": 4,
            "pointer_sites": [
                0x08015B78,
                0x08022B28,
                0x080254E0,
                0x08026C40,
                0x08028FC8,
                0x0802B658,
            ],
            "sha256": "ac4e17870e1dec846dce36e6ff8266ffb3e6fab8a5b018004e8c9ea3209ec58c",
            "end_guard_size": 16,
            "end_guard_hex": "ff" * 16,
        },
    },
}


def default_policy() -> dict[str, Any]:
    """固定Vega reference用policyの独立コピーを返す。"""

    return copy.deepcopy(_DEFAULT_POLICY)


def _fail(message: str) -> NoReturn:
    raise VegaMoveExtractionError(message)


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
    if value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        _fail(f"{label} must be a 64-character lowercase SHA-256")
    return value


def _merge_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Allow deliberate partial overrides while rejecting misspelled keys."""

    supplied: Mapping[str, Any]
    if "vega_moves" in policy:
        supplied = _as_mapping(policy["vega_moves"], "policy.vega_moves")
        extra_outer = set(policy) - {"vega_moves"}
        if extra_outer:
            _fail(f"unknown policy keys: {sorted(extra_outer)}")
    else:
        supplied = policy

    result = default_policy()

    def merge(dst: dict[str, Any], src: Mapping[str, Any], path: str) -> None:
        unknown = set(src) - set(dst)
        if unknown:
            _fail(f"unknown {path} keys: {sorted(unknown)}")
        for key, value in src.items():
            if isinstance(dst[key], dict):
                merge(dst[key], _as_mapping(value, f"{path}.{key}"), f"{path}.{key}")
            else:
                dst[key] = copy.deepcopy(value)

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

    def require_rom_pointer(self, pointer: int, label: str) -> None:
        # Battle scripts and animation bytecode do not require word alignment.
        if pointer < ROM_BASE or pointer >= self.end_address:
            _fail(f"{label} is not a ROM pointer: 0x{pointer:08X}")


def _read_charmap(root: Path, policy: Mapping[str, Any]) -> tuple[dict[int, str], dict[str, Any]]:
    logical = policy.get("logical_path")
    if not isinstance(logical, str) or not logical or Path(logical).is_absolute():
        _fail("policy.charmap.logical_path must be a non-empty relative path")
    root_resolved = root.resolve()
    path = (root_resolved / logical).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError:
        _fail("policy.charmap.logical_path escapes root")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail(f"cannot read fixed charmap: {exc}")
    expected_sha = _as_sha256(policy.get("sha256"), "policy.charmap.sha256")
    actual_sha = _sha256(raw)
    if actual_sha != expected_sha:
        _fail(f"charmap sha256 mismatch: expected {expected_sha}, got {actual_sha}")

    mapping: dict[int, str] = {}
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        _fail(f"charmap is not UTF-8: {exc}")
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
        value = line[3:]
        mapping[key] = escapes.get(value, value)
    if mapping.get(0xFF) != "$" or mapping.get(0xFE) != "\n":
        _fail("charmap terminator/newline ABI mismatch")
    return mapping, {"logical_path": logical, "sha256": actual_sha, "encoding": "CFRU-JP/charmap.tbl"}


def _decode_fixed(raw: bytes, charmap: Mapping[int, str], label: str) -> tuple[str, int]:
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


def normalize_move_name(name: str) -> str:
    """V3などのUTF-8技名列とjoinできる最小正規形を返す。

    言語的な別名変換はせず、Unicode互換正規化と表示用空白の
    除去のみとする。これによりROM証拠の技名は失われない。
    """

    if not isinstance(name, str):
        _fail("move name must be a string")
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
    cfg = _table_config(policy, name)
    address = _as_int(cfg.get("address"), f"policy.tables.{name}.address")
    count = _as_int(cfg.get("count"), f"policy.tables.{name}.count")
    record_size = _as_int(cfg.get("record_size"), f"policy.tables.{name}.record_size")
    if count != required_count or record_size != required_record_size:
        _fail(
            f"{name} ABI mismatch: expected {required_count} x {required_record_size}, "
            f"got {count} x {record_size}"
        )
    if address & 3:
        _fail(f"{name} table is not 4-byte aligned")
    sites_value = cfg.get("pointer_sites")
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
    expected_sha = _as_sha256(cfg.get("sha256"), f"policy.tables.{name}.sha256")
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


def extract_vega_moves(root: Path, rom: bytes, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Extract all 512 frozen Vega move IDs from a fixed reference ROM."""

    if not isinstance(root, Path):
        _fail("root must be pathlib.Path")
    if not isinstance(policy, Mapping):
        _fail("policy must be a mapping")
    merged = _merge_policy(policy)
    rom_cfg = _as_mapping(merged.get("rom"), "policy.rom")
    expected_size = _as_int(rom_cfg.get("size"), "policy.rom.size")
    expected_rom_sha = _as_sha256(rom_cfg.get("sha256"), "policy.rom.sha256")
    logical_rom = rom_cfg.get("logical_path")
    if not isinstance(logical_rom, str) or not logical_rom or Path(logical_rom).is_absolute():
        _fail("policy.rom.logical_path must be a non-empty relative path")
    image = _Rom(rom)
    if len(rom) != expected_size:
        _fail(f"Vega ROM size mismatch: expected {expected_size}, got {len(rom)}")
    actual_rom_sha = _sha256(rom)
    if actual_rom_sha != expected_rom_sha:
        _fail(f"Vega ROM sha256 mismatch: expected {expected_rom_sha}, got {actual_rom_sha}")

    charmap, charmap_provenance = _read_charmap(root, _as_mapping(merged.get("charmap"), "policy.charmap"))
    names, names_info = _validate_table(image, merged, "move_names", required_count=512, required_record_size=8)
    battles, battles_info = _validate_table(image, merged, "battle_moves", required_count=512, required_record_size=12)
    descriptions, descriptions_info = _validate_table(image, merged, "descriptions", required_count=512, required_record_size=60)
    animations, animations_info = _validate_table(image, merged, "animations", required_count=512, required_record_size=4)
    effects, effects_info = _validate_table(image, merged, "effects", required_count=256, required_record_size=4)

    if names_info["end_address_exclusive"] != battles_info["address"]:
        _fail("move_names end does not equal battle_moves start")
    if battles_info["end_address_exclusive"] != descriptions_info["address"]:
        _fail("battle_moves end does not equal descriptions start")
    if descriptions_info["end_address_exclusive"] != animations_info["address"]:
        _fail("descriptions end does not equal animations start")

    effect_cfg = _table_config(merged, "effects")
    guard_size = _as_int(effect_cfg.get("end_guard_size"), "policy.tables.effects.end_guard_size")
    guard_hex = effect_cfg.get("end_guard_hex")
    if not isinstance(guard_hex, str):
        _fail("policy.tables.effects.end_guard_hex must be a hex string")
    try:
        expected_guard = bytes.fromhex(guard_hex)
    except ValueError:
        _fail("policy.tables.effects.end_guard_hex must be a hex string")
    if len(expected_guard) != guard_size or guard_size <= 0:
        _fail("effects end guard size mismatch")
    guard_address = effects_info["end_address_exclusive"]
    actual_guard = image.read(guard_address, guard_size, "effects end guard")
    if actual_guard != expected_guard:
        _fail("effects table end guard mismatch")
    effects_info["boundary_evidence"] = {
        "domain": "u8 move.effect",
        "entry_count": EFFECT_COUNT,
        "end_guard_address": guard_address,
        "end_guard_hex": actual_guard.hex(),
    }

    effect_pointers = [struct.unpack_from("<I", effects, index * 4)[0] for index in range(EFFECT_COUNT)]
    for index, pointer in enumerate(effect_pointers):
        image.require_rom_pointer(pointer, f"effect script {index}")
    animation_pointers = [struct.unpack_from("<I", animations, index * 4)[0] for index in range(MOVE_COUNT)]
    for index, pointer in enumerate(animation_pointers):
        image.require_rom_pointer(pointer, f"move animation {index}")

    rows: list[dict[str, Any]] = []
    name_lengths: list[int] = []
    description_lengths: list[int] = []
    used_effects: set[int] = set()
    for move_id in range(MOVE_COUNT):
        name_raw = names[move_id * 8 : (move_id + 1) * 8]
        battle_raw = battles[move_id * 12 : (move_id + 1) * 12]
        description_raw = descriptions[move_id * 60 : (move_id + 1) * 60]
        name_decoded, name_terminator = _decode_fixed(name_raw, charmap, f"move {move_id} name")
        description_decoded, description_terminator = _decode_fixed(
            description_raw, charmap, f"move {move_id} description"
        )
        effect, power, move_type, accuracy, pp, secondary, target = battle_raw[:7]
        priority = struct.unpack_from("<b", battle_raw, 7)[0]
        flags = struct.unpack_from("<I", battle_raw, 8)[0]
        used_effects.add(effect)
        name_lengths.append(name_terminator)
        description_lengths.append(description_terminator)
        rows.append(
            {
                "id": move_id,
                "name_raw": name_raw.hex(),
                "name_decoded": name_decoded,
                "normalized_name": normalize_move_name(name_decoded),
                "effect": effect,
                "power": power,
                "type": move_type,
                "accuracy": accuracy,
                "pp": pp,
                "secondary": secondary,
                "target": target,
                "priority": priority,
                "flags": flags,
                "raw_hex": battle_raw.hex(),
                "description_raw": description_raw.hex(),
                "description_decoded": description_decoded,
                "animation_pointer": animation_pointers[move_id],
                "effect_script_pointer": effect_pointers[effect],
                "evidence": {
                    "name_address": names_info["address"] + move_id * 8,
                    "battle_address": battles_info["address"] + move_id * 12,
                    "description_address": descriptions_info["address"] + move_id * 60,
                    "animation_entry_address": animations_info["address"] + move_id * 4,
                    "effect_entry_address": effects_info["address"] + effect * 4,
                    "name_terminator_offset": name_terminator,
                    "description_terminator_offset": description_terminator,
                },
            }
        )

    if len(rows) != MOVE_COUNT or [row["id"] for row in rows] != list(range(MOVE_COUNT)):
        _fail("move IDs are not the exact contiguous range 0..511")
    if max(used_effects) >= EFFECT_COUNT:
        _fail("a battle move effect is outside the effect script table")

    return {
        "schema_version": 1,
        "provenance": {
            "policy_id": merged["policy_id"],
            "rom": {"logical_path": logical_rom, "size": len(rom), "sha256": actual_rom_sha},
            "charmap": charmap_provenance,
            "method": "fixed pointer sites + adjacent table boundaries + per-table SHA-256",
        },
        "tables": {
            "move_names": names_info,
            "battle_moves": battles_info,
            "descriptions": descriptions_info,
            "animations": animations_info,
            "effects": effects_info,
        },
        "moves": rows,
        "summaries": {
            "move_count": len(rows),
            "first_move_id": rows[0]["id"],
            "last_move_id": rows[-1]["id"],
            "contiguous_ids": True,
            "used_effect_count": len(used_effects),
            "maximum_effect_id": max(used_effects),
            "name_decoded_bytes_min": min(name_lengths),
            "name_decoded_bytes_max": max(name_lengths),
            "description_decoded_bytes_min": min(description_lengths),
            "description_decoded_bytes_max": max(description_lengths),
            "animation_pointer_count": len(animation_pointers),
            "effect_script_pointer_count": len(effect_pointers),
        },
    }


def _load_cli_policy(root: Path) -> dict[str, Any]:
    config_path = root / "config/project.toml"
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        _fail(f"cannot read fixed config/project.toml: {exc}")
    expected = _as_mapping(config.get("expected"), "config.expected")
    policy = default_policy()
    policy["rom"]["size"] = _as_int(expected.get("vega_output_size"), "expected.vega_output_size")
    policy["rom"]["sha256"] = _as_sha256(
        expected.get("vega_output_sha256"), "expected.vega_output_sha256"
    )
    return policy


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract fixed Vega move tables as sanitized JSON")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (only fixed config/reference paths are read)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        policy = _load_cli_policy(root)
        logical_rom = policy["rom"]["logical_path"]
        rom_path = (root / logical_rom).resolve()
        try:
            rom_path.relative_to(root)
        except ValueError:
            _fail("fixed ROM path escapes root")
        rom = rom_path.read_bytes()
        result = extract_vega_moves(root, rom, policy)
    except (OSError, VegaMoveExtractionError) as exc:
        print(f"extract-vega-moves: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
