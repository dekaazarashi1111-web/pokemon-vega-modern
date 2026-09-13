#!/usr/bin/env python3
"""Stage68へフラエッテ（えいえんのはな）一回限りgiftを決定的に結合する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT"
CONFIG = Path("config/modernization_floette_gift.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "modernization_floette_gift_stage69_payload"
MAP_GROUPS_POINTER_SITE = 0x00054B0C
SPECIES_ID = 1029
BASE_SPECIES_ID = 959
NATIONAL_DEX = 670
COLLECTION_BIT = 850
CLAIM_FLAG = 0x14CD
KEY_STONE_ITEM = 580

REQUIRED_ENTRYPOINTS = {
    "FloetteGift_Probe",
    "FloetteGift_Claim",
    "FloetteGift_IsFormObtained",
    "FloetteGift_IsNationalDexSeen",
    "FloetteGift_IsNationalDexCaught",
}

TEXTS = {
    "text_floette_gift_success": "フラエッテを あずかりました！",
    "text_floette_gift_already": "もう あずかっています",
    "text_floette_gift_locked": "メガリングが ひつようです",
    "text_floette_gift_full": "てもちも パソコンも いっぱいです",
    "text_floette_gift_persist": "セーブに しっぱいしました",
    "text_floette_gift_busy": "ほかの うけとりを かんりちゅうです",
    "text_floette_gift_error": "フラエッテを あずかれませんでした",
}


class FloetteGiftBuildError(ValueError):
    """入力、Species surface、save、map、配置contractの違反。"""


def _fail(message: str) -> NoReturn:
    raise FloetteGiftBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    except OSError as error:
        _fail(f"CSVを読めません: {path}: {error}")


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}が整数ではありません")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label}失敗 ({completed.returncode}): {detail}")
    return completed.stdout.strip()


def _u16(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(raw):
        _fail(f"{label}: ROM範囲外 offset=0x{offset:X}")
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: ROM範囲外 offset=0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, size: int, label: str) -> int:
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"{label}: ROM address範囲外 0x{address:08X}+{size}")
    return offset


def _input_file(
    root: Path, spec: Mapping[str, Any], label: str,
) -> tuple[Path, bytes]:
    path = root / str(spec.get("path", ""))
    if not path.is_file():
        _fail(f"{label}がありません: {path}")
    raw = path.read_bytes()
    if "size" in spec and len(raw) != _integer(spec["size"], f"{label}.size"):
        _fail(f"{label} size不一致: {len(raw)}")
    expected = spec.get("sha256")
    if expected is not None and _sha(raw) != expected:
        _fail(f"{label} SHA-256不一致: expected={expected} actual={_sha(raw)}")
    return path, raw


def _decode_lz77(rom: bytes, pointer: int, label: str) -> tuple[bytes, int]:
    start = _rom_offset(pointer, 4, label)
    if rom[start] != 0x10:
        _fail(f"{label}: GBA LZ77 0x10 headerではありません")
    decoded_size = rom[start + 1] | rom[start + 2] << 8 | rom[start + 3] << 16
    if decoded_size <= 0 or decoded_size > 0x10000:
        _fail(f"{label}: decoded size不一致 {decoded_size}")
    cursor = start + 4
    output = bytearray()
    while len(output) < decoded_size:
        if cursor >= len(rom):
            _fail(f"{label}: flagsがROM範囲外です")
        flags = rom[cursor]
        cursor += 1
        for bit in range(7, -1, -1):
            if len(output) >= decoded_size:
                break
            if flags & (1 << bit):
                if cursor + 2 > len(rom):
                    _fail(f"{label}: compressed pairがROM範囲外です")
                first, second = rom[cursor:cursor + 2]
                cursor += 2
                length = (first >> 4) + 3
                distance = ((first & 0x0F) << 8 | second) + 1
                if distance > len(output):
                    _fail(f"{label}: invalid back-reference distance={distance}")
                for _ in range(length):
                    output.append(output[-distance])
                    if len(output) == decoded_size:
                        break
            else:
                if cursor >= len(rom):
                    _fail(f"{label}: literalがROM範囲外です")
                output.append(rom[cursor])
                cursor += 1
    return bytes(output), cursor - start


def _manifest_audit(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    spec = config["inputs"]["species_manifest"]
    path, raw = _input_file(root, spec, "Species manifest")
    matches = [row for row in _rows(path) if row.get("id") == str(SPECIES_ID)]
    if len(matches) != 1:
        _fail("Species 1029をmanifestから一意に解決できません")
    row = matches[0]
    expected = {
        "species_key": "SPECIES_KEY_FLOETTE_ETERNAL",
        "dpe_id": "848",
        "dpe_symbol": "SPECIES_FLOETTE_ETERNAL",
        "form_key": "FORM_KEY_FLOETTE_ETERNAL",
        "is_official": "true",
        "canonical_national_dex": str(NATIONAL_DEX),
        "status": "APPENDED",
    }
    mismatches = {key: row.get(key) for key, value in expected.items() if row.get(key) != value}
    if mismatches:
        _fail(f"Species 1029 manifest contract不一致: {mismatches}")
    return {
        "path": str(path.relative_to(root)),
        "size": len(raw),
        "sha256": _sha(raw),
        "row": {key: row.get(key) for key in (
            "species_key", "id", "dpe_id", "dpe_symbol", "classification",
            "display_name", "form_key", "is_official", "canonical_national_dex",
            "review_state", "status",
        )},
    }


def _row_bytes(
    rom: bytes, root_address: int, stride: int, species_id: int, label: str,
) -> tuple[int, bytes]:
    row_address = root_address + species_id * stride
    offset = _rom_offset(row_address, stride, label)
    return row_address, rom[offset:offset + stride]


def _surface_expected(spec: Mapping[str, Any], key: str, actual: object) -> None:
    expected = spec.get(key)
    if isinstance(expected, str) and key in {"root", "row_address", "pointer", "root_pointer_site", "catalog_pointer_site", "catalog_root"}:
        expected = _integer(expected, key)
    if actual != expected:
        _fail(f"Species 1029 {key}不一致: expected={expected!r} actual={actual!r}")


def _audit_species_runtime_one(
    root: Path, rom: bytes, config: Mapping[str, Any], label: str,
) -> dict[str, Any]:
    if len(rom) != ROM_SIZE:
        _fail(f"{label}: ROMが32 MiBではありません")
    contract = config["species_runtime_contract"]
    if _integer(contract["canonical_species_count"], "canonical species count") != 1621:
        _fail("canonical Species count contract不一致")
    evidence: dict[str, Any] = {}

    base = contract["base_stats"]
    base_root = _integer(base["root"], "base stats root")
    base_stride = _integer(base["stride"], "base stats stride")
    row_address, row = _row_bytes(rom, base_root, base_stride, SPECIES_ID, "base stats")
    for key, value in (("row_address", row_address), ("row_sha256", _sha(row))):
        _surface_expected(base, key, value)
    stats = list(row[:6])
    types = list(row[6:8])
    abilities = [row[0x16], row[0x1A], row[0x1C]]
    for key, value in (("stats", stats), ("types", types), ("abilities", abilities)):
        _surface_expected(base, key, value)
    evidence["base_stats"] = {
        "root": base_root, "stride": base_stride, "row_address": row_address,
        "row_size": len(row), "row_sha256": _sha(row), "raw_hex": row.hex(),
        "stats": stats, "types": types, "type_names": ["FAIRY", "FAIRY"],
        "abilities": abilities,
    }

    for key in ("front_sprite", "back_sprite", "normal_palette", "shiny_palette"):
        spec = contract[key]
        table_root = _integer(spec["root"], f"{key} root")
        stride = _integer(spec["stride"], f"{key} stride")
        row_address, row = _row_bytes(rom, table_root, stride, SPECIES_ID, key)
        pointer = _u32(row, 0, f"{key} pointer")
        decoded, consumed = _decode_lz77(rom, pointer, key)
        observed = {
            "row_address": row_address, "row_sha256": _sha(row),
            "pointer": pointer, "decoded_size": len(decoded),
            "decoded_sha256": _sha(decoded),
        }
        for field, value in observed.items():
            _surface_expected(spec, field, value)
        if not any(decoded):
            _fail(f"{key}: decoded streamが全zeroです")
        evidence[key] = {
            "root": table_root, "stride": stride, "row_address": row_address,
            "row_size": len(row), "row_sha256": _sha(row), "raw_hex": row.hex(),
            "pointer": pointer, "pointer_non_null": pointer != 0,
            "pointer_in_rom": True, "compression": "GBA_LZ77_0x10",
            "compressed_size_consumed": consumed, "decoded_size": len(decoded),
            "decoded_sha256": _sha(decoded),
            "decoded_nonzero_bytes": sum(value != 0 for value in decoded),
        }

    icon = contract["icon"]
    icon_root = _integer(icon["root"], "icon root")
    icon_stride = _integer(icon["stride"], "icon stride")
    icon_row_address, icon_row = _row_bytes(rom, icon_root, icon_stride, SPECIES_ID, "icon")
    icon_pointer = _u32(icon_row, 0, "icon pointer")
    icon_size = _integer(icon["decoded_size"], "icon size")
    icon_offset = _rom_offset(icon_pointer, icon_size, "icon data")
    icon_raw = rom[icon_offset:icon_offset + icon_size]
    for field, value in {
        "row_address": icon_row_address, "row_sha256": _sha(icon_row),
        "pointer": icon_pointer, "decoded_size": len(icon_raw),
        "decoded_sha256": _sha(icon_raw),
    }.items():
        _surface_expected(icon, field, value)
    if not any(icon_raw):
        _fail("icon dataが全zeroです")
    evidence["icon"] = {
        "root": icon_root, "stride": icon_stride,
        "row_address": icon_row_address, "row_sha256": _sha(icon_row),
        "raw_hex": icon_row.hex(), "pointer": icon_pointer,
        "pointer_non_null": icon_pointer != 0, "pointer_in_rom": True,
        "decoded_size": len(icon_raw), "decoded_sha256": _sha(icon_raw),
        "decoded_nonzero_bytes": sum(value != 0 for value in icon_raw),
    }

    icon_palette = contract["icon_palette"]
    palette_root = _integer(icon_palette["root"], "icon palette root")
    palette_stride = _integer(icon_palette["stride"], "icon palette stride")
    palette_address, palette_row = _row_bytes(
        rom, palette_root, palette_stride, SPECIES_ID, "icon palette",
    )
    for field, value in {
        "row_address": palette_address, "row_sha256": _sha(palette_row),
        "palette_index": palette_row[0],
    }.items():
        _surface_expected(icon_palette, field, value)
    evidence["icon_palette"] = {
        "root": palette_root, "stride": palette_stride,
        "row_address": palette_address, "row_sha256": _sha(palette_row),
        "palette_index": palette_row[0], "row_non_null": True,
    }

    name = contract["name"]
    name_root = _integer(name["root"], "name root")
    name_stride = _integer(name["stride"], "name stride")
    name_address, name_row = _row_bytes(rom, name_root, name_stride, SPECIES_ID, "name")
    mapping, tokens = _charmap(root)
    encoded = _encode_text(str(name["decoded"]), mapping, tokens)
    for field, value in {
        "row_address": name_address, "row_sha256": _sha(name_row),
        "encoded_hex": encoded.hex(),
    }.items():
        _surface_expected(name, field, value)
    if name_row[:len(encoded)] != encoded or any(value != 0xFF for value in name_row[len(encoded):]):
        _fail("Species 1029 name row padding不一致")
    evidence["name"] = {
        "root": name_root, "stride": name_stride, "row_address": name_address,
        "row_sha256": _sha(name_row), "raw_hex": name_row.hex(),
        "terminated_encoded_hex": encoded.hex(), "decoded": name["decoded"],
        "terminator_present": encoded[-1] == 0xFF,
    }

    level = contract["level_up"]
    level_site = _integer(level["root_pointer_site"], "level root pointer site")
    level_root = _u32(rom, level_site, "level root pointer")
    _surface_expected(level, "root", level_root)
    level_stride = _integer(level["stride"], "level stride")
    level_address, level_row = _row_bytes(rom, level_root, level_stride, SPECIES_ID, "level row")
    level_pointer = _u32(level_row, 0, "level data pointer")
    for field, value in {
        "row_address": level_address, "row_sha256": _sha(level_row),
        "pointer": level_pointer,
    }.items():
        _surface_expected(level, field, value)
    cursor = _rom_offset(level_pointer, 3, "level data")
    level_raw = bytearray()
    level_rows: list[dict[str, int]] = []
    for _ in range(256):
        move = _u16(rom, cursor, "level move")
        learned_at = rom[cursor + 2]
        level_raw.extend(rom[cursor:cursor + 3])
        level_rows.append({"move_id": move, "level": learned_at})
        cursor += 3
        if learned_at == 0xFF:
            break
    else:
        _fail("level-up learnsetにterminatorがありません")
    for field, value in {
        "decoded_size": len(level_raw), "decoded_sha256": _sha(level_raw),
    }.items():
        _surface_expected(level, field, value)
    if len(level_rows) < 2 or level_rows[-1] != {"move_id": 0, "level": 255}:
        _fail("level-up learnset終端不一致")
    evidence["level_up"] = {
        "root_pointer_site": level_site, "root": level_root, "stride": level_stride,
        "row_address": level_address, "row_sha256": _sha(level_row),
        "row_raw_hex": level_row.hex(), "pointer": level_pointer,
        "pointer_non_null": level_pointer != 0, "pointer_in_rom": True,
        "decoded_size": len(level_raw), "decoded_sha256": _sha(level_raw),
        "entry_count_including_terminator": len(level_rows), "rows": level_rows,
    }

    for key in ("tm_compatibility", "tutor_compatibility"):
        spec = contract[key]
        pointer_site = _integer(spec["root_pointer_site"], f"{key} pointer site")
        table_root = _u32(rom, pointer_site, f"{key} root")
        _surface_expected(spec, "root", table_root)
        stride = _integer(spec["stride"], f"{key} stride")
        row_address, row = _row_bytes(rom, table_root, stride, SPECIES_ID, key)
        for field, value in (("row_address", row_address), ("row_sha256", _sha(row))):
            _surface_expected(spec, field, value)
        if not any(row):
            _fail(f"{key} rowが全zeroです")
        record: dict[str, Any] = {
            "root_pointer_site": pointer_site, "root": table_root,
            "root_pointer_non_null": table_root != 0, "root_pointer_in_rom": True,
            "stride": stride, "row_address": row_address, "row_size": len(row),
            "row_sha256": _sha(row), "raw_hex": row.hex(),
            "nonzero_bytes": sum(value != 0 for value in row),
        }
        if key == "tutor_compatibility":
            catalog_site = _integer(spec["catalog_pointer_site"], "tutor catalog site")
            catalog_root = _u32(rom, catalog_site, "tutor catalog root")
            _surface_expected(spec, "catalog_root", catalog_root)
            _rom_offset(catalog_root, 2, "tutor catalog")
            record.update({
                "catalog_pointer_site": catalog_site,
                "catalog_root": catalog_root,
                "catalog_pointer_non_null": catalog_root != 0,
                "catalog_pointer_in_rom": True,
            })
        evidence[key] = record

    return {
        "status": "PASS_FULLY_RUNTIME_ADDRESSABLE",
        "rom_label": label,
        "rom_size": len(rom),
        "rom_sha256": _sha(rom),
        "species_id": SPECIES_ID,
        "evidence": evidence,
    }


def _species_runtime_audit(
    root: Path, stage67: bytes, parent: bytes, config: Mapping[str, Any],
) -> dict[str, Any]:
    canonical = _audit_species_runtime_one(root, stage67, config, "Stage67")
    inherited = _audit_species_runtime_one(root, parent, config, "Stage68")
    if canonical["evidence"] != inherited["evidence"]:
        _fail("Stage68がStage67 Species 1029 surfaceを変更しています")
    return {
        "status": "PASS_STAGE67_PROVEN_AND_STAGE68_BYTE_IDENTICAL",
        "stage67": canonical,
        "stage68_inheritance": inherited,
        "all_required_roles": [
            "base_stats", "front_sprite", "back_sprite", "normal_palette",
            "shiny_palette", "icon", "icon_palette", "name", "level_up",
            "tm_compatibility", "tutor_compatibility",
        ],
        "required_role_count": 11,
        "missing_role_count": 0,
    }


def _legacy_override_audit(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    _, raw = _input_file(
        root, config["inputs"]["legacy_collection_model"], "legacy collection model",
    )
    model = json.loads(raw)
    forms = model.get("forms")
    matches = [row for row in forms if isinstance(row, dict) and row.get("target_species") == SPECIES_ID] if isinstance(forms, list) else []
    if len(matches) != 1:
        _fail("legacy collection modelのSpecies 1029を一意に解決できません")
    legacy = matches[0]
    expected = {
        "species_key": "SPECIES_KEY_FLOETTE_ETERNAL",
        "base_species": BASE_SPECIES_ID,
        "status": "UNOBTAINABLE_EVENT_FORM_EXCLUDED",
        "collection_policy": "UNOBTAINABLE_CANON_EXCLUDED",
        "distributable": False,
    }
    if any(legacy.get(key) != value for key, value in expected.items()):
        _fail(f"legacy Species 1029 classification不一致: {legacy}")
    ledger_path = root / config["inputs"]["collection_ledger_manifest"]["path"]
    rows = _rows(ledger_path)
    ledger = [row for row in rows if row.get("canonical_id") == str(BASE_SPECIES_ID)]
    if len(ledger) != 1 or ledger[0].get("ledger_bit_index") != str(COLLECTION_BIT):
        _fail("Floette National 670 canonical collection bit不一致")
    return {
        "status": "PASS_STAGE69_EXPLICIT_OVERRIDE_WITHOUT_REWRITE",
        "legacy_model": {
            "path": config["inputs"]["legacy_collection_model"]["path"],
            "size": len(raw), "sha256": _sha(raw), "row": legacy,
            "mutated": False,
        },
        "stage69_override": {
            "species_id": SPECIES_ID,
            "status": "OBTAINABLE_ONE_TIME_GIFT",
            "claim_owner": "expanded event flag 0x14CD",
            "legacy_history_preserved": True,
        },
        "national_dex_registration": {
            "national_dex": NATIONAL_DEX,
            "base_species_id": BASE_SPECIES_ID,
            "collection_bit": COLLECTION_BIT,
            "collection_key": ledger[0].get("collection_key"),
            "ledger_manifest_path": str(ledger_path.relative_to(root)),
            "legacy_52_byte_pokedex_bitmaps_indexed": False,
            "reason": "National 670 exceeds the legacy 416-bit FireRed bitmap; canonical acquisition ledger is the existing safe owner",
        },
    }


def _flag_namespace_audit(
    root: Path, config: Mapping[str, Any], parent_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    flag_spec = config["inputs"]["flags_manifest"]
    path, raw = _input_file(root, flag_spec, "flags manifest")
    rows = _rows(path)
    used: dict[int, str] = {}
    for row in rows:
        try:
            flag = int(row.get("id", ""), 0)
        except ValueError:
            continue
        used[flag] = row.get("flag_key", "")
    if CLAIM_FLAG in used:
        _fail(f"0x14CDがglobal flags manifestと衝突しています: {used[CLAIM_FLAG]}")
    mega = parent_metadata.get("flag_namespace", {})
    first = _integer(mega.get("first"), "Stage68 claim first")
    last = _integer(mega.get("last"), "Stage68 claim last")
    if (first, last, mega.get("count"), mega.get("collision_count")) != (0x14A0, 0x14CC, 45, 0):
        _fail("Stage68 dedicated claim flag contract不一致")
    if CLAIM_FLAG != last + 1 or CLAIM_FLAG >= 0x1500:
        _fail("Stage69 claim flagがStage68直後/0x1500未満ではありません")
    overlap = [flag for flag in range(first, CLAIM_FLAG + 1) if flag in used]
    if overlap:
        _fail(f"Stage68/69 dedicated flag範囲がglobal manifestと衝突: {overlap}")
    if max((flag for flag in used if flag < first), default=-1) != 0x149D:
        _fail("global manifest predecessorが0x149Dではありません")
    return {
        "status": "PASS_DEDICATED_STAGE69_ALLOCATION",
        "claim_flag_key": config["gift"]["claim_flag_key"],
        "claim_flag": CLAIM_FLAG,
        "claim_flag_hex": "0x14CD",
        "source_of_truth": config["gift"]["claim_flag_source_of_truth"],
        "global_manifest": {
            "path": str(path.relative_to(root)), "size": len(raw),
            "sha256": _sha(raw), "data_row_count": len(rows),
            "claim_row_present": False, "mutated": False,
        },
        "stage68_reserved": {"first": first, "last": last, "count": 45},
        "collision_count": 0,
        "contiguous_after_stage68": True,
        "next_owner_boundary": "0x1500",
        "below_next_owner_boundary": True,
        "migration": "expanded event flag zero-default on legacy saves",
    }


def _acquisition_abi_audit(root: Path, config: Mapping[str, Any], parent: bytes) -> dict[str, Any]:
    _, raw = _input_file(
        root, config["inputs"]["stage26_acquisition_metadata"],
        "Stage26 acquisition metadata",
    )
    metadata = json.loads(raw)
    runtime = metadata.get("runtime", {})
    symbols = runtime.get("symbols", {})
    linked = runtime.get("linked_abi", {})
    expected = {
        "VegaAcqEngine_GetPending": (symbols, 153951456),
        "VegaAcqEngine_FinalizeInMemory": (symbols, 153953568),
        "GiveMonToPlayer": (linked, 151905848),
        "GetBoxedMonPtr": (linked, 152189664),
        "GetBoxMonDataAt": (linked, 152189924),
        "ZeroBoxMonAt": (linked, 152189384),
    }
    result: dict[str, Any] = {}
    for name, (owner, address) in expected.items():
        if owner.get(name) != address:
            _fail(f"Stage26 acquisition ABI {name}不一致: {owner.get(name)}")
        offset = _rom_offset(address, 16, name)
        code = parent[offset:offset + 16]
        if code in (bytes(16), b"\xFF" * 16):
            _fail(f"Stage68上の{name} entrypointが空です")
        result[name] = {
            "address": address, "thumb_entrypoint": address | 1,
            "stage68_first_16_sha256": _sha(code),
            "stage68_first_16_hex": code.hex(),
        }
    return {
        "status": "PASS_EXISTING_PROVEN_ABI_REUSED",
        "metadata_path": config["inputs"]["stage26_acquisition_metadata"]["path"],
        "metadata_sha256": _sha(raw),
        "entrypoints": result,
        "save_finalize_semantics": "VegaAcqEngine_FinalizeInMemory finalizes acquisition CRC and outer Vega ledger checksum",
    }


def _entry_header(rom: bytes, group_id: int, map_id: int) -> tuple[int, int]:
    root_pointer = _u32(rom, MAP_GROUPS_POINTER_SITE, "gMapGroups root")
    root = _rom_offset(root_pointer, 99 * 4, "gMapGroups root")
    group_pointer = _u32(rom, root + group_id * 4, "Factory map group")
    group = _rom_offset(group_pointer, (map_id + 1) * 4, "Factory map group")
    header_pointer = _u32(rom, group + map_id * 4, "Factory map header")
    header = _rom_offset(header_pointer, 0x1C, "Factory map header")
    return header, header_pointer


def _map_cell_audit(rom: bytes, config: Mapping[str, Any], header: int) -> dict[str, Any]:
    layout_pointer = _u32(rom, header, "Factory map layout")
    layout = _rom_offset(layout_pointer, 0x18, "Factory map layout")
    width = _u32(rom, layout, "Factory width")
    height = _u32(rom, layout + 4, "Factory height")
    block_pointer = _u32(rom, layout + 12, "Factory blockmap")
    blockmap = _rom_offset(block_pointer, width * height * 2, "Factory blockmap")
    x = _integer(config["map"]["x"], "map x")
    y = _integer(config["map"]["y"], "map y")
    if x >= width or y >= height:
        _fail("Stage69 NPC座標がmap範囲外です")
    entry_offset = blockmap + 2 * (y * width + x)
    entry = _u16(rom, entry_offset, "NPC metatile entry")
    collision = (entry >> 10) & 3
    expected_entry = _integer(config["map"]["expected_metatile_entry"], "metatile")
    expected_collision = _integer(config["map"]["expected_collision"], "collision")
    if entry != expected_entry or collision != expected_collision:
        _fail(f"Stage69 NPC cell不一致 entry=0x{entry:04X} collision={collision}")
    return {
        "layout_address": layout_pointer, "width": width, "height": height,
        "blockmap_address": block_pointer, "x": x, "y": y,
        "metatile_entry": entry, "metatile_entry_hex": f"0x{entry:04X}",
        "metatile_id": entry & 0x03FF, "collision": collision,
        "elevation": (entry >> 12) & 0x0F, "walkable_collision_zero": True,
    }


def _compile_runtime(
    root: Path, load_address: int, acquisition: Mapping[str, Any],
) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchainが必要です")
    abi = acquisition["entrypoints"]
    definitions = {
        "VEGA_FLOETTE_ACQ_GET_PENDING_ADDRESS": abi["VegaAcqEngine_GetPending"]["thumb_entrypoint"],
        "VEGA_FLOETTE_ACQ_FINALIZE_ADDRESS": abi["VegaAcqEngine_FinalizeInMemory"]["thumb_entrypoint"],
        "VEGA_FLOETTE_GIVE_MON_ADDRESS": abi["GiveMonToPlayer"]["thumb_entrypoint"],
        "VEGA_FLOETTE_GET_BOX_MON_DATA_ADDRESS": abi["GetBoxMonDataAt"]["thumb_entrypoint"],
        "VEGA_FLOETTE_ZERO_BOX_MON_AT_ADDRESS": abi["ZeroBoxMonAt"]["thumb_entrypoint"],
    }
    source = root / "overlays/modernization_floette_gift/modernization_floette_gift.c"
    with tempfile.TemporaryDirectory(prefix="vega-modernization-floette-gift-") as temporary:
        directory = Path(temporary)
        obj = directory / "floette_gift.o"
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", f"-I{root}",
            f"-I{root / 'overlays/modernization_floette_gift'}",
            *[f"-D{key}=0x{value:08X}u" for key, value in definitions.items()],
        ]
        _run([*common, "-c", str(source), "-o", str(obj)], "compile Floette gift runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.FloetteGift_*))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n",
            encoding="ascii",
        )
        elf = directory / "floette_gift.elf"
        binary = directory / "floette_gift.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,FloetteGift_Probe", f"-Wl,-T,{linker}", str(obj),
            "-lgcc", "-o", str(elf),
        ], "link Floette gift runtime")
        undefined = _run([nm, "-u", str(elf)], "Floette gift undefined-symbol audit")
        if undefined:
            _fail("Floette gift runtimeにundefined symbolがあります: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Floette gift objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Floette gift nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing:
            _fail(f"Floette gift export不足: {missing}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 16 * 1024:
            _fail(f"Floette gift runtime size不一致: {len(payload)}")
        return payload, symbols


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str, bool]]

    def __init__(self) -> None:
        self.data = bytearray()
        self.fixups = []

    def emit(self, *values: int) -> "_Script":
        self.data.extend(values)
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def pointer(self, label: str, *, thumb: bool = False) -> "_Script":
        self.fixups.append((len(self.data), label, thumb))
        self.data.extend(bytes(4))
        return self

    def callnative(self, name: str) -> "_Script":
        return self.emit(0x23).pointer(f"native::{name}", thumb=True)

    def msgbox(self, label: str) -> "_Script":
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, 4)

    def compare_result(self, value: int) -> "_Script":
        return self.emit(0x21).half(0x800D).half(value)

    def if_equal(self, label: str) -> "_Script":
        return self.emit(0x06, 0x01).pointer(label)

    def goto(self, label: str) -> "_Script":
        return self.emit(0x05).pointer(label)


def _add_script(blob: _Blob, label: str, script: _Script) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)


def _build_scripts(root: Path, blob: _Blob) -> dict[str, Any]:
    mapping, tokens = _charmap(root)
    texts: dict[str, Any] = {}
    for label, text in TEXTS.items():
        encoded = _encode_text(text, mapping, tokens)
        blob.add(label, encoded, 1)
        texts[label] = {"text": text, "size": len(encoded), "sha256": _sha(encoded)}
    _add_script(
        blob, "script_floette_gift_npc",
        _Script().emit(0x6A, 0x5A).callnative("FloetteGift_Claim")
        .goto("script_floette_gift_result"),
    )
    result = _Script()
    for value, label in (
        (0, "script_floette_gift_success"),
        (1, "script_floette_gift_already"),
        (3, "script_floette_gift_locked"),
        (4, "script_floette_gift_full"),
        (5, "script_floette_gift_persist"),
        (6, "script_floette_gift_busy"),
        (8, "script_floette_gift_persist"),
    ):
        result.compare_result(value).if_equal(label)
    result.goto("script_floette_gift_error")
    _add_script(blob, "script_floette_gift_result", result)
    for label, text_label in (
        ("script_floette_gift_success", "text_floette_gift_success"),
        ("script_floette_gift_already", "text_floette_gift_already"),
        ("script_floette_gift_locked", "text_floette_gift_locked"),
        ("script_floette_gift_full", "text_floette_gift_full"),
        ("script_floette_gift_persist", "text_floette_gift_persist"),
        ("script_floette_gift_busy", "text_floette_gift_busy"),
        ("script_floette_gift_error", "text_floette_gift_error"),
    ):
        _add_script(blob, label, _Script().msgbox(text_label).goto("script_floette_gift_end"))
    _add_script(blob, "script_floette_gift_end", _Script().emit(0x6C, 0x02))
    return {
        "texts": texts,
        "result_routes": {
            "0": "SUCCESS", "1": "ALREADY_CLAIMED", "3": "LOCKED",
            "4": "PARTY_AND_PC_FULL", "5": "PERSIST_FAILED",
            "6": "ACQUISITION_BUSY", "7": "ENGINE_REJECTED",
            "8": "ROLLBACK_PERSIST_FAILED",
        },
        "synchronous": True,
    }


def _add_map_runtime(
    parent: bytes, config: Mapping[str, Any], parent_metadata: Mapping[str, Any], blob: _Blob,
) -> dict[str, Any]:
    map_config = config["map"]
    group_id = _integer(map_config["group"], "map group")
    map_id = _integer(map_config["map"], "map id")
    local_id = _integer(map_config["local_id"], "local id")
    clone_id = _integer(map_config["clone_local_id"], "clone local id")
    header, header_pointer = _entry_header(parent, group_id, map_id)
    events_pointer = _u32(parent, header + 4, "Factory events root")
    scripts_pointer = _u32(parent, header + 8, "Factory scripts root")
    parent_map = parent_metadata.get("map", {})
    if (
        parent_map.get("group_id") != group_id
        or parent_map.get("map_id") != map_id
        or parent_map.get("events_after_address") != events_pointer
        or parent_map.get("object_count_after") != 14
    ):
        _fail("Stage68 map metadata/ROM identity不一致")
    events = _rom_offset(events_pointer, 0x14, "Factory events")
    old_events = bytearray(parent[events:events + 0x14])
    old_count = old_events[0]
    objects_pointer = _u32(parent, events + 4, "Factory object table")
    objects = _rom_offset(objects_pointer, old_count * 0x18, "Factory objects")
    old_objects = parent[objects:objects + old_count * 0x18]
    ids = [old_objects[index * 0x18] for index in range(old_count)]
    if old_count != 14 or ids != list(range(1, 15)):
        _fail(f"Stage68 Factory object ID contract不一致: {ids}")
    if objects_pointer != parent_map.get("objects_after_address"):
        _fail("Stage68 object table pointerがmetadataと不一致です")
    matches = [
        old_objects[index * 0x18:(index + 1) * 0x18]
        for index in range(old_count) if ids[index] == clone_id
    ]
    if len(matches) != 1 or local_id != old_count + 1:
        _fail("Stage69 clone/local ID contract不一致")
    x = _integer(map_config["x"], "map x")
    y = _integer(map_config["y"], "map y")
    occupied = [
        (struct.unpack_from("<H", old_objects, index * 0x18 + 4)[0],
         struct.unpack_from("<H", old_objects, index * 0x18 + 6)[0])
        for index in range(old_count)
    ]
    if (x, y) in occupied:
        _fail(f"Stage69 NPC座標が既存objectと衝突しています: {(x, y)}")
    cell = _map_cell_audit(parent, config, header)
    gift = bytearray(matches[0])
    gift[0] = local_id
    struct.pack_into("<HH", gift, 4, x, y)
    struct.pack_into("<I", gift, 0x10, 0)
    object_offset = blob.add("floette_gift_factory_objects", old_objects + bytes(gift), 4)
    blob.pointer(object_offset + old_count * 0x18 + 0x10, "script_floette_gift_npc")
    old_events[0] = old_count + 1
    struct.pack_into("<I", old_events, 4, 0)
    event_offset = blob.add("floette_gift_factory_events", bytes(old_events), 4)
    blob.pointer(event_offset + 4, "floette_gift_factory_objects")
    return {
        "group_id": group_id, "map_id": map_id,
        "header_offset": header, "header_address": header_pointer,
        "old_events_pointer": events_pointer, "old_scripts_pointer": scripts_pointer,
        "old_event_counts": list(parent[events:events + 4]),
        "old_objects_pointer": objects_pointer,
        "old_objects_sha256": _sha(old_objects),
        "object_count_before": old_count, "object_count_after": old_count + 1,
        "gift_object": {
            "local_id": local_id, "graphics_id": gift[1],
            "movement_type": gift[9], "x": x, "y": y,
            "source_clone_local_id": clone_id,
        },
        "cell_audit": cell,
        "existing_14_objects_preserved": True,
        "stage68_shop_local14_preserved": old_objects[13 * 0x18:(14 * 0x18)] == matches[0],
        "map_scripts_preserved": True,
    }


def _build_payload(
    root: Path, parent: bytes, config: Mapping[str, Any],
    parent_metadata: Mapping[str, Any], acquisition: Mapping[str, Any],
    payload_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    header_offset = blob.reserve("floette_gift_payload_header", PAYLOAD_HEADER_SIZE, 16)
    code_load = GBA_ROM_BASE + payload_offset + ((len(blob.data) + 3) & ~3)
    code, code_symbols = _compile_runtime(root, code_load, acquisition)
    code_offset = blob.add("floette_gift_runtime_code", code, 4)
    if GBA_ROM_BASE + payload_offset + code_offset != code_load:
        _fail("Floette gift linker/payload address不一致")
    for name, address in code_symbols.items():
        relative = address - code_load
        if 0 <= relative < len(code):
            blob.labels[f"native::{name}"] = code_offset + relative
    script_meta = _build_scripts(root, blob)
    map_meta = _add_map_runtime(parent, config, parent_metadata, blob)
    runtime_size = len(blob.data)
    struct.pack_into(
        "<8sIIIIIIIIIII", blob.data, header_offset,
        b"VEGAFG69", 1, runtime_size, len(code), SPECIES_ID,
        _integer(config["gift"]["level"], "gift level"), CLAIM_FLAG,
        KEY_STONE_ITEM, NATIONAL_DEX, COLLECTION_BIT,
        map_meta["object_count_after"], 0,
    )
    for offset, label, thumb in (
        (52, "native::FloetteGift_Probe", True),
        (56, "native::FloetteGift_Claim", True),
        (60, "native::FloetteGift_IsFormObtained", True),
        (64, "native::FloetteGift_IsNationalDexSeen", True),
        (68, "native::FloetteGift_IsNationalDexCaught", True),
        (72, "script_floette_gift_npc", False),
        (76, "floette_gift_factory_events", False),
    ):
        blob.pointer(header_offset + offset, label, thumb=thumb)
    payload = blob.finish(payload_offset)
    base = GBA_ROM_BASE + payload_offset
    labels = {name: base + relative for name, relative in sorted(blob.labels.items())}
    map_meta.update({
        "events_after_address": labels["floette_gift_factory_events"],
        "objects_after_address": labels["floette_gift_factory_objects"],
        "gift_script_address": labels["script_floette_gift_npc"],
    })
    return payload, {
        "payload": {
            "magic": "VEGAFG69", "offset": payload_offset, "address": base,
            "size": len(payload), "sha256": _sha(payload),
            "code_offset": payload_offset + code_offset,
            "code_address": code_load, "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": {name: code_symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)},
        "scripts": {**script_meta, "npc_address": labels["script_floette_gift_npc"]},
        "map": map_meta,
        "labels": labels,
    }


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, object]]:
    rows = allocation.get("allocations")
    if not isinstance(rows, list):
        _fail("Stage68 allocation rows不一致")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"],
        "owner": row["owner"], "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in rows]


def _allocation(
    root: Path, previous: Mapping[str, Any], size: int, digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "Floette Eternal one-time gift runtime, scripts, and Factory NPC",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage69 allocator overlapを検出しました")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage69 allocationを一意に解決できません")
    return matches[0], report


def _load_contract(root: Path) -> tuple[
    dict[str, Any], bytes, dict[str, Any], dict[str, Any], bytes,
]:
    config = _read_json(root / CONFIG)
    if config.get("schema_version") != 1 or config.get("task") != TASK or config.get("stage") != 69:
        _fail("Floette gift config schema/task/stage不一致")
    inputs = config.get("inputs")
    if not isinstance(inputs, dict):
        _fail("inputs contractがobjectではありません")
    _, parent = _input_file(root, inputs["parent_rom"], "Stage68 parent ROM")
    _, parent_meta_raw = _input_file(root, inputs["parent_metadata"], "Stage68 metadata")
    _, parent_alloc_raw = _input_file(root, inputs["parent_allocation"], "Stage68 allocation")
    _, parent_gate_raw = _input_file(root, inputs["parent_runtime_gate"], "Stage68 runtime gate")
    _, stage67 = _input_file(root, inputs["stage67_species_rom"], "Stage67 Species ROM")
    parent_meta = json.loads(parent_meta_raw)
    parent_alloc = json.loads(parent_alloc_raw)
    parent_gate = json.loads(parent_gate_raw)
    if parent_meta.get("stage") != 68 or parent_meta.get("output", {}).get("sha256") != _sha(parent):
        _fail("Stage68 metadata/ROM identity不一致")
    if parent_alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage68 allocation overlap contract不一致")
    if (
        parent_gate.get("status") != "PASS"
        or parent_gate.get("stage") != 68
        or parent_gate.get("inputs", {}).get("rom", {}).get("sha256") != _sha(parent)
        or parent_gate.get("runtime_result", {}).get("status") != "PASS"
    ):
        _fail("Stage68 exact-ROM runtime gate不一致")
    parent_meta["_stage69_parent_runtime_gate"] = {
        "path": inputs["parent_runtime_gate"]["path"],
        "size": len(parent_gate_raw),
        "sha256": _sha(parent_gate_raw),
        "status": "PASS",
    }
    return config, parent, parent_meta, parent_alloc, stage67


def run_host_test(root: Path = ROOT) -> dict[str, Any]:
    compiler = shutil.which("cc")
    if not compiler:
        _fail("host C compilerが必要です")
    with tempfile.TemporaryDirectory(prefix="vega-floette-gift-host-") as temporary:
        executable = Path(temporary) / "floette_gift_host_test"
        output = _run([
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-DMODERNIZATION_FLOETTE_GIFT_HOST_TEST=1", f"-I{root}",
            str(root / "overlays/modernization_floette_gift/modernization_floette_gift.c"),
            str(root / "overlays/modernization_floette_gift/modernization_floette_gift_host_test.c"),
            "-o", str(executable),
        ], "Floette gift host compile")
        if output:
            _fail(f"host compile stdoutが空ではありません: {output}")
        result = _run([str(executable)], "Floette gift host test")
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError as error:
        _fail(f"host test JSON不一致: {error}: {result}")
    if parsed.get("status") != "PASS" or parsed.get("scenario_count") != 13:
        _fail(f"host test結果不一致: {parsed}")
    return parsed


def _runtime_gate(
    root: Path, config: Mapping[str, Any], rom: bytes,
) -> dict[str, Any] | None:
    path = root / config["outputs"]["runtime_gate"]
    if not path.is_file():
        return None
    gate = _read_json(path)
    source = root / "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c"
    harness = root / "tools/mgba_regression_smoke.c"
    checks = gate.get("checks")
    valid = (
        gate.get("schema_version") == 1
        and gate.get("task") == TASK
        and gate.get("stage") == 69
        and gate.get("status") == "PASS"
        and gate.get("rom_sha256") == _sha(rom)
        and gate.get("rom_size") == len(rom)
        and gate.get("runner_source_sha256") == _sha(source.read_bytes())
        and gate.get("embedded_harness_sha256") == _sha(harness.read_bytes())
        and gate.get("process_runs") == 1
        and gate.get("core_instances") == 2
        and gate.get("warnings_errors") == 0
        and isinstance(checks, dict)
        and len(checks) == 10
        and all(checks.values())
        and gate.get("attempt_count") == 3
        and gate.get("execution_attempts") == 3
        and gate.get("retry_count") == 2
    )
    return gate if valid else None


def _partial_runtime_gate(
    root: Path, config: Mapping[str, Any], rom: bytes,
) -> dict[str, Any] | None:
    path = root / config["outputs"]["runtime_gate"]
    if not path.is_file():
        return None
    gate = _read_json(path)
    source = root / "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c"
    exact = gate.get("exact_rom_confirmed")
    host_only = gate.get("host_confirmed_pending_exact_rom")
    pending = gate.get("not_yet_executed_exact_rom")
    corrected = gate.get("corrected_runner", {})
    valid = (
        gate.get("schema_version") == 1
        and gate.get("task") == TASK
        and gate.get("stage") == 69
        and gate.get("status") == "PARTIAL_PASS_HARNESS_FIXTURE_BLOCKED"
        and gate.get("release_gate") == "PENDING_EXACT_PARTY_PC_FULL_AND_FRESH_RELOAD"
        and gate.get("rom_sha256") == _sha(rom)
        and gate.get("rom_size") == len(rom)
        and gate.get("attempt_count") == 3
        and gate.get("retry_count") == 2
        and isinstance(exact, dict)
        and len(exact) == 7
        and all(exact.values())
        and isinstance(host_only, dict)
        and len(host_only) == 4
        and all(host_only.values())
        and isinstance(pending, dict)
        and len(pending) == 2
        and set(pending.values()) == {"PENDING"}
        and corrected.get("status") == "COMPILE_PASS_NOT_EXECUTED_PER_THREE_ATTEMPT_LIMIT"
        and corrected.get("source_size") == source.stat().st_size
        and corrected.get("source_sha256") == _sha(source.read_bytes())
    )
    return gate if valid else None


def run_mgba_smoke(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    outputs = build_outputs(root)
    config = _read_json(root / CONFIG)
    output_paths = config["outputs"]
    rom_relative = output_paths["rom"]
    rom = outputs[rom_relative]
    if _partial_runtime_gate(root, config, rom) is not None:
        _fail("3回の記録済みmGBA上限に到達しています。追加実行には新しい明示承認が必要です")
    _write_outputs(root, outputs)
    metadata = json.loads(outputs[output_paths["metadata"]])
    source = root / "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c"
    harness = root / "tools/mgba_regression_smoke.c"
    compiler = shutil.which("cc")
    if not compiler:
        _fail("mGBA smoke用host C compilerが必要です")
    with tempfile.TemporaryDirectory(prefix="vega-floette-gift-mgba-") as temporary:
        directory = Path(temporary)
        runner = directory / "mgba_modernization_floette_gift_smoke"
        save = directory / "stage69-runtime.sav"
        _run([
            compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-Wl,--build-id=none", f"-I{root / 'tools'}", str(source),
            "-o", str(runner), "-lmgba",
        ], "compile Stage69 mGBA runner")
        entrypoints = metadata["entrypoints"]
        map_meta = metadata["map"]
        acquisition = json.loads(outputs[output_paths["contract"]])["acquisition_abi"]
        command = [
            str(runner), str(root / rom_relative), str(save),
            hex(entrypoints["FloetteGift_Probe"]),
            hex(entrypoints["FloetteGift_Claim"]),
            hex(entrypoints["FloetteGift_IsFormObtained"]),
            hex(entrypoints["FloetteGift_IsNationalDexSeen"]),
            hex(entrypoints["FloetteGift_IsNationalDexCaught"]),
            hex(map_meta["gift_script_address"]),
            hex(map_meta["events_after_address"]),
            hex(map_meta["old_scripts_pointer"]),
            hex(acquisition["entrypoints"]["VegaAcqEngine_GetPending"]["thumb_entrypoint"]),
            hex(acquisition["entrypoints"]["GetBoxMonDataAt"]["thumb_entrypoint"]),
            hex(acquisition["entrypoints"]["GetBoxedMonPtr"]["thumb_entrypoint"]),
            hex(acquisition["entrypoints"]["ZeroBoxMonAt"]["thumb_entrypoint"]),
        ]
        try:
            completed = subprocess.run(
                command, cwd=root, text=True, capture_output=True,
                check=False, timeout=300,
            )
        except subprocess.TimeoutExpired as error:
            _fail(f"Stage69 exact-ROM mGBA smoke timeout: {error}")
        if completed.returncode:
            detail = "\n".join(
                part.strip() for part in (completed.stderr, completed.stdout)
                if part.strip()
            )
            _fail(f"Stage69 exact-ROM mGBA smoke失敗 ({completed.returncode}): {detail}")
        try:
            observed = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            _fail(f"Stage69 mGBA stdout JSON不一致: {error}: {completed.stdout}")
        if observed.get("status") != "PASS" or not all(observed.get("checks", {}).values()):
            _fail(f"Stage69 mGBA assertions不一致: {observed}")
        gate = {
            **observed,
            "attempt_count": 3,
            "execution_attempts": 3,
            "successful_process_runs": 1,
            "retry_count": 2,
            "prior_attempts": [
                {
                    "attempt": 1,
                    "status": "FAIL_HARNESS_ASSERTION",
                    "last_completed_phase": "party-delivery",
                    "failed_phase": "pc-delivery",
                    "supplemental_assertion": "stock GetBoxMonDataAt plus legacy Codex box-level adapter",
                    "rom_claim_result": "SUCCESS",
                    "rom_species1029_postcondition": "PASS_INSIDE_GIFT_RUNTIME_USING_DPE_ABI",
                    "rom_transaction_failure": False,
                },
                {
                    "attempt": 2,
                    "status": "FAIL_HARNESS_ASSERTION",
                    "last_completed_phase": "party-delivery",
                    "failed_phase": "pc-delivery",
                    "supplemental_assertion": "CreateMon(1029,50) EXP identity still read through obsolete stock GetBoxMonDataAt 0x0808B4B5",
                    "rom_claim_result": "SUCCESS",
                    "rom_species1029_postcondition": "PASS_INSIDE_GIFT_RUNTIME_USING_DPE_ABI",
                    "rom_transaction_failure": False,
                },
            ],
            "retry_correction": {
                "validation_api_before": "stock GetBoxMonDataAt 0x0808B4B5",
                "validation_api_after": "Stage26 linked DPE GetBoxMonDataAt 0x09123BE5",
                "level50_proof": "production CreateMon(1029,50) EXP identity equals DPE GetBoxMonDataAt(EXP)",
            },
            "rom_path": rom_relative,
            "rom_size": len(rom),
            "rom_sha256": _sha(rom),
            "runner_source_path": str(source.relative_to(root)),
            "runner_source_size": source.stat().st_size,
            "runner_source_sha256": _sha(source.read_bytes()),
            "embedded_harness_path": str(harness.relative_to(root)),
            "embedded_harness_sha256": _sha(harness.read_bytes()),
            "runner_binary_size": runner.stat().st_size,
            "runner_binary_sha256": _sha(runner.read_bytes()),
            "compiler": {
                "path": compiler,
                "version": _run([compiler, "--version"], "host compiler version").splitlines()[0],
                "flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Wl,--build-id=none", "-lmgba"],
            },
            "stderr_phases": [
                line for line in completed.stderr.splitlines()
                if line.startswith("mgba-modernization-floette-gift: phase=")
            ],
            "temporary_save_retained": False,
        }
    path = root / output_paths["runtime_gate"]
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _stable(gate)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        stream.write(raw)
        temporary_path = Path(stream.name)
    os.replace(temporary_path, path)
    final_outputs = build_outputs(root)
    if _runtime_gate(root, config, final_outputs[rom_relative]) is None:
        _fail("生成したStage69 mGBA gateのidentity再検証に失敗しました")
    _write_outputs(root, final_outputs)
    return gate


def build_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    config, parent, parent_meta, previous_alloc, stage67 = _load_contract(root)
    manifest = _manifest_audit(root, config)
    species = _species_runtime_audit(root, stage67, parent, config)
    legacy = _legacy_override_audit(root, config)
    flags = _flag_namespace_audit(root, config, parent_meta)
    acquisition = _acquisition_abi_audit(root, config, parent)
    host = run_host_test(root)

    gift = config["gift"]
    exact = {
        "species_id": SPECIES_ID,
        "base_species_id": BASE_SPECIES_ID,
        "canonical_national_dex": NATIONAL_DEX,
        "canonical_collection_bit": COLLECTION_BIT,
        "level": 50,
        "unlock_item_id": KEY_STONE_ITEM,
        "claim_flag": CLAIM_FLAG,
    }
    for key, value in exact.items():
        if _integer(gift[key], f"gift.{key}") != value:
            _fail(f"gift contract {key}不一致")

    preliminary, _ = _build_payload(
        root, parent, config, parent_meta, acquisition, 0,
    )
    allocation, _ = _allocation(root, previous_alloc, len(preliminary), "0" * 64)
    payload_offset = _integer(allocation["start"], "payload start")
    payload, runtime = _build_payload(
        root, parent, config, parent_meta, acquisition, payload_offset,
    )
    if len(payload) != len(preliminary):
        _fail("load addressによりStage69 payload sizeが変化しました")
    allocation, allocation_report = _allocation(
        root, previous_alloc, len(payload), _sha(payload),
    )
    if _integer(allocation["start"], "final payload start") != payload_offset:
        _fail("final Stage69 payload allocationが変化しました")
    payload_end = _integer(allocation["end_exclusive"], "payload end")
    if parent[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage69 payload配置先がerased FFではありません")

    output = bytearray(parent)
    output[payload_offset:payload_end] = payload
    map_meta = runtime["map"]
    map_site = _integer(map_meta["header_offset"], "map header offset") + 4
    if _u32(parent, map_site, "Factory event root") != map_meta["old_events_pointer"]:
        _fail("Factory event root expected pointer不一致")
    struct.pack_into("<I", output, map_site, map_meta["events_after_address"])
    if _u32(output, map_site + 4, "Factory scripts root") != map_meta["old_scripts_pointer"]:
        _fail("Factory map scripts rootを変更しました")
    allowed = [(payload_offset, payload_end), (map_site, map_site + 4)]
    outside = [
        index for index, (before, after) in enumerate(zip(parent, output))
        if before != after and not any(start <= index < end for start, end in allowed)
    ]
    if outside:
        _fail(f"宣言span外を変更しました: {outside[:8]}")
    output_raw = bytes(output)
    patch_raw = create_bps(parent, output_raw)
    if apply_bps(parent, patch_raw) != output_raw:
        _fail("Stage68→69 BPS round-trip不一致")

    outputs = config["outputs"]
    runtime_gate = _runtime_gate(root, config, output_raw)
    partial_runtime_gate = (
        None if runtime_gate is not None
        else _partial_runtime_gate(root, config, output_raw)
    )
    if runtime_gate is not None:
        exact_runtime_status = "PASS"
        overall_status = "PASS_HOST_STATIC_EXACT_RUNTIME"
        runtime_evidence = runtime_gate
    elif partial_runtime_gate is not None:
        exact_runtime_status = "PARTIAL_PASS_FULL_AND_RELOAD_PENDING"
        overall_status = "PASS_HOST_AND_EXACT_PARTIAL_RUNTIME_FULL_RELOAD_PENDING"
        runtime_evidence = partial_runtime_gate
    else:
        exact_runtime_status = "PENDING"
        overall_status = "PASS_HOST_STATIC_EXACT_RUNTIME_SMOKE_PENDING"
        runtime_evidence = None
    contract = {
        "schema_version": 1,
        "task": TASK,
        "stage": 69,
        "status": "PASS_STATIC_CONTRACT",
        "identity": {
            "species_key": gift["species_key"], "species_id": SPECIES_ID,
            "base_species_key": gift["base_species_key"], "base_species_id": BASE_SPECIES_ID,
            "canonical_national_dex": NATIONAL_DEX,
            "level": gift["level"],
        },
        "species_manifest": manifest,
        "species_runtime": species,
        "legacy_collection_override": legacy,
        "claim_flag_namespace": flags,
        "acquisition_abi": acquisition,
        "delivery_contract": {
            "unlock": {"item_key": gift["unlock_item_key"], "item_id": KEY_STONE_ITEM},
            "destination_order": ["party", "PC"],
            "party_and_pc_full": "NO_DELIVERY_NO_CLAIM_NO_SAVE",
            "publication_order": [
                "CreateMon(Species1029,Lv50)", "GiveMon(party-or-PC)",
                "FlagSet(0x14CD)", "set collection_bits[850]",
                "VegaAcqEngine_FinalizeInMemory", "TrySavingData(0)",
                "TryWriteSector(31)",
            ],
            "save_failure_rollback": [
                "FlagClear(0x14CD)", "remove exact delivered party/PC slot",
                "restore exact pre-transaction modern ledger",
                "VegaAcqEngine_FinalizeInMemory", "compensating TrySavingData(0)",
                "compensating TryWriteSector(31)",
            ],
            "form_specific_source_of_truth": "expanded flag 0x14CD",
            "national_670_seen_caught_source_of_truth": "canonical collection ledger bit 850",
            "legacy_fire_red_pokedex_bitmap_write": False,
        },
    }
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "stage": 69,
        "status": overall_status,
        "parent": {
            "stage": 68, "task": parent_meta.get("task"),
            "path": config["inputs"]["parent_rom"]["path"],
            "size": len(parent), "sha256": _sha(parent),
            "metadata_sha256": config["inputs"]["parent_metadata"]["sha256"],
            "allocation_sha256": config["inputs"]["parent_allocation"]["sha256"],
            "runtime_gate": parent_meta["_stage69_parent_runtime_gate"],
        },
        "output": {"path": outputs["rom"], "size": len(output_raw), "sha256": _sha(output_raw)},
        **runtime,
        "contract": {
            "path": outputs["contract"], "sha256": _sha(_stable(contract)),
            "species_runtime_status": species["status"],
            "missing_species_roles": 0,
        },
        "gift": {
            "species_id": SPECIES_ID, "level": 50,
            "unlock_item_id": KEY_STONE_ITEM, "claim_flag": CLAIM_FLAG,
            "claim_flag_hex": "0x14CD", "canonical_national_dex": NATIONAL_DEX,
            "canonical_collection_bit": COLLECTION_BIT,
            "repeatability": "ONCE_PER_SAVE",
        },
        "transaction": contract["delivery_contract"],
        "flag_namespace": flags,
        "legacy_collection_override": legacy["stage69_override"],
        "allocation": {
            "path": outputs["allocation"], "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patch_round_trip": {
            "format": "BPS1", "source_sha256": _sha(parent),
            "target_sha256": _sha(output_raw), "size": len(patch_raw),
            "sha256": _sha(patch_raw), "exact": True,
        },
        "validation": {
            "host": host,
            "stage67_species_exact_audit": "PASS",
            "stage68_species_inheritance": "BYTE_IDENTICAL",
            "exact_rom_runtime_smoke": exact_runtime_status,
            "runtime_gate": runtime_evidence,
            "heavy_test_runs": (
                runtime_evidence.get("execution_attempts", runtime_evidence.get("attempt_count", 0))
                if runtime_evidence is not None else 0
            ),
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "species_1029_level50": gift["species_id"] == SPECIES_ID and gift["level"] == 50,
            "mega_ring_item580_gate": gift["unlock_item_id"] == KEY_STONE_ITEM,
            "one_time_claim_flag_14cd": _integer(gift["claim_flag"], "claim flag") == CLAIM_FLAG,
            "national670_collection_bit850": gift["canonical_collection_bit"] == COLLECTION_BIT,
            "physical_npc_local15": map_meta["gift_object"]["local_id"] == 15,
            "stage68_local14_preserved": map_meta["stage68_shop_local14_preserved"],
            "existing_14_objects_preserved": map_meta["existing_14_objects_preserved"],
            "walkable_unoccupied_cell": map_meta["cell_audit"]["collision"] == 0,
            "object_count_15": map_meta["object_count_after"] == 15,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "declared_spans_only": True,
            "bps_exact": True,
            "legacy_model_unmodified": not legacy["legacy_model"]["mutated"],
            "global_flags_manifest_unmodified": not flags["global_manifest"]["mutated"],
            "full_species_surface_proven": species["missing_role_count"] == 0,
        },
    }
    if not all(metadata["invariants"].values()):
        failed = [key for key, value in metadata["invariants"].items() if not value]
        _fail(f"Stage69 invariant失敗: {failed}")
    symbols = {
        "schema_version": 1, "task": TASK,
        "payload": runtime["payload"], "entrypoints": runtime["entrypoints"],
        "scripts": runtime["scripts"], "map": runtime["map"],
        "linked_acquisition_abi": acquisition["entrypoints"],
    }
    checkpoint = {
        "schema_version": 1, "task": TASK, "stage": 69,
        "status": metadata["status"], "rom": metadata["output"],
        "parent": metadata["parent"], "gift": metadata["gift"],
        "payload": metadata["payload"], "entrypoints": metadata["entrypoints"],
        "map": metadata["map"], "claim_flag_namespace": flags,
        "species_runtime_evidence": species,
        "legacy_collection_override": legacy,
        "transaction": metadata["transaction"], "validation": metadata["validation"],
        "release_patch_round_trip": metadata["release_patch_round_trip"],
    }
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["runtime_bin"]: payload,
        outputs["runtime_symbols"]: _stable(symbols),
        outputs["contract"]: _stable(contract),
        outputs["checkpoint"]: _stable(checkpoint),
        outputs["bps"]: patch_raw,
    }


def _write_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    differences = [
        relative for relative, raw in outputs.items()
        if not (root / relative).is_file() or (root / relative).read_bytes() != raw
    ]
    if differences:
        _fail("Stage69生成物が不一致です: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "host-test", "runtime-smoke"))
    args = parser.parse_args()
    try:
        if args.mode == "host-test":
            host = run_host_test(ROOT)
            print(json.dumps(host, ensure_ascii=False, sort_keys=True))
            return 0
        if args.mode == "runtime-smoke":
            gate = run_mgba_smoke(ROOT)
            print(json.dumps(gate, ensure_ascii=False, sort_keys=True))
            return 0
        outputs = build_outputs(ROOT)
        repeated = build_outputs(ROOT)
        if outputs != repeated:
            _fail("Stage69 buildがbyte deterministicではありません")
        if args.mode == "build":
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, KeyError, TypeError, ValueError, FloetteGiftBuildError) as error:
        print(f"Modernization Floette gift {args.mode} failed: {error}", file=sys.stderr)
        return 1
    config = _read_json(ROOT / CONFIG)
    rom = outputs[config["outputs"]["rom"]]
    print(
        f"Modernization Floette gift {args.mode}: PASS "
        f"rom={_sha(rom)} outputs={len(outputs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
