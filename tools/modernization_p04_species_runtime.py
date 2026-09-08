#!/usr/bin/env python3
"""Stage70: P04 Mega 49形態とAbility固定表をStage69 ROMへmaterializeする。"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text
from tools.release.bps import apply_bps, create_bps
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


TASK = "USER-MODERNIZATION-P04-SPECIES-RUNTIME-STAGE70"
CONFIG_PATH = Path("config/modernization_p04_species_runtime.json")
ROM_SIZE = 32 * 1024 * 1024
HEADER_MAGIC = b"P04SP70\0"
SPECIES_TABLE_KEYS = (
    "species_front", "species_back", "species_palette", "species_shiny_palette",
    "species_icon", "species_icon_palette", "species_front_coords",
    "species_back_coords", "species_elevation", "species_footprint", "species_cry",
    "species_cry2", "species_dex_entries", "species_national_dex",
    "species_national_dex_runtime", "species_base_stats", "species_species_names",
    "species_species_names_legacy", "species_level_up_pointers", "species_tmhm",
    "species_tutor", "species_wild_table", "acquisition_collection_defs", "evolution",
)
ABILITY_TABLE_KEYS = (
    "ability_names", "ability_descriptions", "ability_ratings",
    "ability_mold_breaker_ignored",
)
TABLE_KEYS = ABILITY_TABLE_KEYS + SPECIES_TABLE_KEYS
POINTER_ROW_ASSETS = {
    "species_front": "front_lz",
    "species_back": "back_lz",
    "species_palette": "normal_palette_lz",
    "species_shiny_palette": "shiny_palette_lz",
    "species_icon": "icon_raw",
}


class SpeciesRuntimeError(RuntimeError):
    """入力契約またはROM ABIが一致しない場合。"""


def _fail(message: str) -> None:
    raise SpeciesRuntimeError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpeciesRuntimeError(f"JSONを読めません: {path}: {exc}") from exc


def _read_pinned(root: Path, spec: Mapping[str, Any], label: str) -> tuple[Path, bytes, Any]:
    path = root / str(spec["path"])
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SpeciesRuntimeError(f"{label}を読めません: {path}: {exc}") from exc
    _require(_sha(raw) == spec["sha256"], f"{label} SHA-256がconfig pinと不一致です")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpeciesRuntimeError(f"{label} JSON不正: {exc}") from exc
    return path, raw, parsed


def _read_csv_pinned(root: Path, spec: Mapping[str, Any], label: str) -> list[dict[str, str]]:
    path = root / str(spec["path"])
    raw = path.read_bytes()
    _require(_sha(raw) == spec["sha256"], f"{label} SHA-256がconfig pinと不一致です")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _all_offsets(raw: bytes, needle: bytes) -> list[int]:
    result: list[int] = []
    cursor = 0
    while True:
        cursor = raw.find(needle, cursor)
        if cursor < 0:
            return result
        result.append(cursor)
        cursor += 1


def _lz77_literal(raw: bytes) -> bytes:
    _require(0 < len(raw) < (1 << 24), "LZ77入力size不一致")
    output = bytearray((0x10, len(raw) & 0xFF, (len(raw) >> 8) & 0xFF, (len(raw) >> 16) & 0xFF))
    for start in range(0, len(raw), 8):
        output.append(0)
        output.extend(raw[start:start + 8])
    while len(output) & 3:
        output.append(0)
    return bytes(output)


def _lz77_decompress(raw: bytes) -> bytes:
    _require(len(raw) >= 4 and raw[0] == 0x10, "LZ77 header不一致")
    size = raw[1] | raw[2] << 8 | raw[3] << 16
    cursor = 4
    result = bytearray()
    while len(result) < size:
        _require(cursor < len(raw), "LZ77 flagsが途中で終わりました")
        flags = raw[cursor]
        cursor += 1
        for bit in range(8):
            if len(result) >= size:
                break
            _require(cursor < len(raw), "LZ77 streamが途中で終わりました")
            if flags & (0x80 >> bit):
                _require(cursor + 1 < len(raw), "LZ77 backrefが途中で終わりました")
                pair = raw[cursor] << 8 | raw[cursor + 1]
                cursor += 2
                count = (pair >> 12) + 3
                distance = (pair & 0xFFF) + 1
                _require(distance <= len(result), "LZ77 backref距離不正")
                for _ in range(count):
                    result.append(result[-distance])
                    if len(result) == size:
                        break
            else:
                result.append(raw[cursor])
                cursor += 1
    return bytes(result)


def _fixed_text(text: str, size: int, mapping: Mapping[str, int], tokens: Sequence[str]) -> bytes:
    encoded = _encode_text(text, mapping, tokens)
    _require(len(encoded) <= size, f"固定長textが{size} bytesを超えます: {text!r}")
    return encoded + b"\xFF" * (size - len(encoded))


def _table_definitions(capacity: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = capacity["table_capacity"]["fixed_tables"]
    by_key = {row["table_key"]: dict(row) for row in rows}
    _require(len(by_key) == len(rows), "P04 fixed table keyが重複しています")
    _require(set(TABLE_KEYS) <= set(by_key), "Stage70必須fixed tableがcapacity manifestに不足しています")
    selected = {key: by_key[key] for key in TABLE_KEYS}
    for key, row in selected.items():
        old_count = int(row["old_count"])
        new_count = int(row["new_count"])
        stride = int(row["stride_bytes"])
        _require(int(row["old_size_bytes"]) == old_count * stride, f"{key}: old size不一致")
        _require(int(row["new_size_bytes"]) == new_count * stride, f"{key}: new size不一致")
        _require(bool(row["relocation_required"]), f"{key}: relocation_requiredではありません")
    return selected


def _species_source_ids(rows: Sequence[Mapping[str, str]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        key = row.get("species_key", "")
        if key:
            result[key] = int(row["id"])
    return result


def _id_map(rows: Sequence[Mapping[str, str]], key_field: str) -> dict[str, int]:
    return {row[key_field]: int(row["id"]) for row in rows if row.get(key_field)}


def _extract_initializer(text: str, symbol: str) -> str:
    match = re.search(r"\[\s*" + re.escape(symbol) + r"\s*\]\s*=\s*\{", text)
    _require(match is not None, f"upstream species initializerがありません: {symbol}")
    start = match.end() - 1
    depth = 0
    in_string = False
    escaped = False
    for cursor in range(start, len(text)):
        char = text[cursor]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:cursor + 1]
    _fail(f"upstream species initializerが閉じていません: {symbol}")
    raise AssertionError


def _number(block: str, field: str, *, default: int | None = None) -> int:
    match = re.search(r"\." + re.escape(field) + r"\s*=\s*(-?\d+)", block)
    if match is None:
        if default is not None:
            return default
        _fail(f"upstream fieldがありません: {field}")
    return int(match.group(1))


def _coords(block: str, field: str) -> tuple[int, int]:
    match = re.search(r"\." + re.escape(field) + r"\s*=\s*MON_COORDS_SIZE\(\s*(\d+)\s*,\s*(\d+)\s*\)", block)
    _require(match is not None, f"upstream coordsがありません: {field}")
    return int(match.group(1)), int(match.group(2))


def _type_symbols(block: str) -> list[str]:
    match = re.search(r"\.types\s*=\s*MON_TYPES\(([^)]*)\)", block)
    _require(match is not None, "upstream typesがありません")
    values = [part.strip() for part in match.group(1).split(",") if part.strip()]
    _require(len(values) in (1, 2), "upstream type数が1/2ではありません")
    return values if len(values) == 2 else [values[0], values[0]]


def _upstream_text(root: Path, expected_commit: str) -> tuple[str, list[dict[str, str]]]:
    checkout = root
    _require(checkout.is_dir(), f"upstream checkoutがありません: {checkout}")
    actual = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], check=True,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()
    _require(actual == expected_commit, "upstream checkout commitがpinと不一致です")
    files = sorted((checkout / "src/data/pokemon/species_info").glob("*.h"))
    _require(files, "upstream species_info headersがありません")
    inventory = [{"path": str(path.relative_to(checkout)), "sha256": _sha(path.read_bytes())} for path in files]
    return "\n".join(path.read_text(encoding="utf-8") for path in files), inventory


def _asset_by_role(asset: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    pools = list(asset.get("png_assets", [])) + list(asset.get("palette_assets", []))
    matches = [row for row in pools if row.get("role") == role]
    _require(len(matches) == 1, f"{asset.get('record_key')}: asset role {role}が一意ではありません")
    return matches[0]


def _read_asset(root: Path, asset: Mapping[str, Any], role: str, expected_size: int) -> tuple[bytes, dict[str, Any]]:
    row = _asset_by_role(asset, role)
    conversion = row["gba_conversion"]
    relative = str(conversion["relative_path"])
    path = root / relative
    raw = path.read_bytes()
    _require(len(raw) == expected_size == int(conversion["size"]), f"{relative}: asset size不一致")
    _require(_sha(raw) == conversion["sha256"], f"{relative}: asset SHA-256不一致")
    return raw, {"path": relative, "size": len(raw), "sha256": _sha(raw), "role": role}


@dataclass(frozen=True)
class PreparedSpecies:
    reservation: Mapping[str, Any]
    candidate: Mapping[str, Any]
    source_id: int
    stats: tuple[int, int, int, int, int, int]
    type_ids: tuple[int, int]
    ability_id: int
    front_coords: tuple[int, int, int]
    back_coords: tuple[int, int, int]
    elevation: int
    icon_palette: int
    assets: Mapping[str, bytes]
    asset_evidence: Sequence[Mapping[str, Any]]
    upstream_block_sha256: str


def _prepare_species(
    reservations: Sequence[Mapping[str, Any]], candidates: Mapping[str, Mapping[str, Any]],
    assets: Mapping[str, Mapping[str, Any]], source_ids: Mapping[str, int],
    type_ids: Mapping[str, int], type_symbols: Mapping[str, str], ability_ids: Mapping[str, int],
    upstream: str, asset_root: Path,
) -> list[PreparedSpecies]:
    prepared: list[PreparedSpecies] = []
    for reservation in reservations:
        key = str(reservation["source_record_key"])
        _require(key in candidates and key in assets, f"{key}: candidate/asset manifest行不足")
        candidate = candidates[key]
        _require(candidate["implementation_scope"] == "ADOPT_CANDIDATE", f"{key}: 非採用candidateです")
        _require(candidate["classification"] == "BATTLE_ONLY_MEGA", f"{key}: Mega形態ではありません")
        _require(candidate["source_species_key"] == reservation["source_species_key"], f"{key}: source key不一致")
        source_key = str(reservation["source_species_key"])
        _require(source_key in source_ids, f"{key}: source species ID不明")
        source_id = source_ids[source_key]
        _require(0 <= source_id < 1621, f"{key}: source species ID範囲外")
        symbol = str(candidate["upstream_species_symbol"])
        block = _extract_initializer(upstream, symbol)
        stats = tuple(_number(block, field) for field in (
            "baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense",
        ))
        _require(all(0 < value <= 255 for value in stats), f"{key}: base stat u8範囲外")
        candidate_types = list(candidate["type_keys"])
        if len(candidate_types) == 1:
            candidate_types.append(candidate_types[0])
        _require(len(candidate_types) == 2, f"{key}: candidate type数不正")
        _require(all(type_key in type_ids for type_key in candidate_types), f"{key}: type ID不明")
        expected_symbols = [type_symbols[type_key] for type_key in candidate_types]
        _require(_type_symbols(block) == expected_symbols, f"{key}: candidate/upstream type不一致")
        ability_key = str(reservation["ability_key"])
        _require(ability_key == candidate["ability_key"], f"{key}: ability key不一致")
        _require(ability_key in ability_ids, f"{key}: ability ID不明: {ability_key}")
        fw, fh = _coords(block, "frontPicSize")
        bw, bh = _coords(block, "backPicSize")
        _require(all(value in range(8, 65, 8) for value in (fw, fh, bw, bh)),
                 f"{key}: GBA画像座標は8刻みの8..64必須")
        front_y = _number(block, "frontPicYOffset")
        back_y = _number(block, "backPicYOffset")
        icon_palette = _number(block, "iconPalIndex")
        elevation = _number(block, "enemyMonElevation", default=0)
        _require(all(0 <= value <= 255 for value in (front_y, back_y, icon_palette, elevation)), f"{key}: graphics metadata u8範囲外")
        asset_row = assets[key]
        front, e_front = _read_asset(asset_root, asset_row, "FRONT", 2048)
        back, e_back = _read_asset(asset_root, asset_row, "BACK", 2048)
        icon, e_icon = _read_asset(asset_root, asset_row, "ICON", 1024)
        normal, e_normal = _read_asset(asset_root, asset_row, "NORMAL_PALETTE", 32)
        shiny, e_shiny = _read_asset(asset_root, asset_row, "SHINY_PALETTE", 32)
        converted = {
            "front_raw": front, "front_lz": _lz77_literal(front),
            "back_raw": back, "back_lz": _lz77_literal(back),
            "icon_raw": icon, "normal_palette_raw": normal,
            "normal_palette_lz": _lz77_literal(normal),
            "shiny_palette_raw": shiny, "shiny_palette_lz": _lz77_literal(shiny),
        }
        _require(_lz77_decompress(converted["front_lz"]) == front, f"{key}: front LZ roundtrip失敗")
        _require(_lz77_decompress(converted["back_lz"]) == back, f"{key}: back LZ roundtrip失敗")
        _require(_lz77_decompress(converted["normal_palette_lz"]) == normal, f"{key}: palette LZ roundtrip失敗")
        _require(_lz77_decompress(converted["shiny_palette_lz"]) == shiny, f"{key}: shiny palette LZ roundtrip失敗")
        prepared.append(PreparedSpecies(
            reservation=reservation, candidate=candidate, source_id=source_id,
            stats=stats, type_ids=(type_ids[candidate_types[0]], type_ids[candidate_types[1]]),
            ability_id=ability_ids[ability_key],
            front_coords=((fw + 7) // 8 << 4 | (fh + 7) // 8, front_y, 0),
            back_coords=((bw + 7) // 8 << 4 | (bh + 7) // 8, back_y, 0),
            elevation=elevation, icon_palette=icon_palette, assets=converted,
            asset_evidence=(e_front, e_back, e_icon, e_normal, e_shiny),
            upstream_block_sha256=_sha(block.encode("utf-8")),
        ))
    return prepared


def _slice(stage: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - GBA_ROM_BASE
    _require(0 <= offset <= len(stage) - size, f"{label}: ROM外slice")
    return stage[offset:offset + size]


def _source_row(stage: bytes, table: Mapping[str, Any], source_id: int, *, runtime_index: bool = False) -> bytes:
    index = source_id - 1 if runtime_index else source_id
    _require(index >= 0, "national dex runtime source indexが負です")
    stride = int(table["stride_bytes"])
    return _slice(stage, int(table["current_address"]) + index * stride, stride, str(table["table_key"]))


def _new_species_row(key: str, item: PreparedSpecies, stage: bytes, tables: Mapping[str, Mapping[str, Any]]) -> bytes:
    species_id = int(item.reservation["id"])
    if key in POINTER_ROW_ASSETS:
        if key in ("species_front", "species_back"):
            return struct.pack("<IHH", 0, 2048, species_id)
        if key == "species_palette":
            return struct.pack("<IHH", 0, species_id, 0)
        if key == "species_shiny_palette":
            return struct.pack("<IHH", 0, species_id + 1621, 0)
        return bytes(4)
    if key == "species_icon_palette":
        return bytes((item.icon_palette,))
    if key == "species_front_coords":
        return bytes((item.front_coords[0], item.front_coords[1], 0, 0))
    if key == "species_back_coords":
        return bytes((item.back_coords[0], item.back_coords[1], 0, 0))
    if key == "species_elevation":
        return bytes((item.elevation,))
    if key == "species_national_dex":
        return struct.pack("<H", int(item.candidate["national_dex"]))
    if key == "species_national_dex_runtime":
        return struct.pack("<H", int(item.candidate["national_dex"]))
    if key == "species_base_stats":
        row = bytearray(_source_row(stage, tables[key], item.source_id))
        row[0:6] = bytes(item.stats)
        row[6:8] = bytes(item.type_ids)
        for offset in (22, 26, 28):
            struct.pack_into("<H", row, offset, item.ability_id)
        return bytes(row)
    if key == "acquisition_collection_defs":
        return struct.pack("<HHBBBB", species_id, 0xFFFF, 0, 0, 5, 0)
    if key == "evolution":
        return bytes(int(tables[key]["stride_bytes"]))
    return _source_row(stage, tables[key], item.source_id)


def _header() -> bytes:
    raw = bytearray(64)
    raw[:8] = HEADER_MAGIC
    struct.pack_into("<IIII", raw, 8, 70, 1621, 1670, 318)
    raw[24:56] = bytes.fromhex("6532002dabd3197ee6b8ded8b153a495d3241acf062fc931210987093172cb95")
    return bytes(raw)


def _build_blob(
    root: Path, stage: bytes, tables: Mapping[str, Mapping[str, Any]],
    prepared: Sequence[PreparedSpecies], ability_rows: Sequence[Mapping[str, Any]],
) -> tuple[_Blob, dict[str, Any]]:
    mapping, tokens = _charmap(root)
    blob = _Blob()
    blob.add("stage70_header", _header(), 16)
    for item in prepared:
        record = str(item.reservation["source_record_key"]).lower()
        for asset_key in ("front_lz", "back_lz", "normal_palette_lz", "shiny_palette_lz", "icon_raw"):
            blob.add(f"asset_{record}_{asset_key}", item.assets[asset_key], 4)
    for row in ability_rows:
        blob.add(f"ability_desc_{int(row['id'])}", _encode_text(str(row["description_ja"]), mapping, tokens), 1)

    table_meta: dict[str, Any] = {}
    for key in TABLE_KEYS:
        table = tables[key]
        old_count = int(table["old_count"])
        new_count = int(table["new_count"])
        stride = int(table["stride_bytes"])
        old_prefix = _slice(stage, int(table["current_address"]), old_count * stride, key)
        rows = bytearray(old_prefix)
        if key == "ability_names":
            for row in ability_rows:
                rows.extend(_fixed_text(str(row["name_ja"]), stride, mapping, tokens))
        elif key == "ability_descriptions":
            rows.extend(bytes(len(ability_rows) * stride))
        elif key == "ability_ratings":
            rows.extend(bytes(int(row["rating"]) for row in ability_rows))
        elif key == "ability_mold_breaker_ignored":
            rows.extend(bytes(int(row["mold_breaker_ignored"]) for row in ability_rows))
        else:
            for item in prepared:
                rows.extend(_new_species_row(key, item, stage, tables))
        _require(len(rows) == new_count * stride, f"{key}: generated table size不一致")
        table_offset = blob.add(f"table_{key}", bytes(rows), int(table["alignment"]))
        if key == "ability_descriptions":
            for position, row in enumerate(ability_rows):
                blob.pointer(table_offset + (old_count + position) * stride, f"ability_desc_{int(row['id'])}")
        elif key in POINTER_ROW_ASSETS:
            asset_key = POINTER_ROW_ASSETS[key]
            for position, item in enumerate(prepared):
                record = str(item.reservation["source_record_key"]).lower()
                blob.pointer(table_offset + (old_count + position) * stride, f"asset_{record}_{asset_key}")
        table_meta[key] = {
            "label": f"table_{key}", "payload_relative_offset": table_offset,
            "old_address": int(table["current_address"]), "old_count": old_count,
            "new_count": new_count, "stride": stride,
            "old_size": old_count * stride, "new_size": new_count * stride,
            "old_sha256": _sha(old_prefix),
            "capacity_stage65_old_sha256": table["stage65_old_slice_sha256"],
            "parent_matches_capacity_stage65": _sha(old_prefix) == table["stage65_old_slice_sha256"],
            "appended_unlinked_sha256": _sha(bytes(rows[old_count * stride:])),
        }
    return blob, table_meta


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"], "owner": row["owner"],
        "purpose": row["purpose"], "content_sha256": row["content_sha256"],
    } for row in allocation["allocations"]]


def _allocate(root: Path, previous: Mapping[str, Any], config: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    request = dict(config["allocation"])
    requests = _previous_requests(previous)
    requests.append({
        "name": request["name"], "region": request["region"], "size": size,
        "alignment": int(request["alignment"]), "owner": TASK,
        "purpose": "P04 Mega 49 species fixed tables/assets and Ability 312..317 UI-safe rows",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    _require(report["summaries"]["overlap_count"] == 0, "Stage70 allocator overlapを検出しました")
    matches = [row for row in report["allocations"] if row["name"] == request["name"]]
    _require(len(matches) == 1, "Stage70 allocationを一意に解決できません")
    return matches[0], report


def _semantic_owner(site: int, previous: Mapping[str, Any]) -> dict[str, Any]:
    for row in previous["allocations"]:
        if int(row["start"]) <= site and site + 4 <= int(row["end_exclusive"]):
            return {
                "owner_class": "ALLOCATED_OWNER", "semantic_owner": str(row["owner"]),
                "allocation_name": str(row["name"]), "allocation_region": str(row["region"]),
                "semantic_evidence": "PINNED_STAGE69_ALLOCATION_CONTAINS_EXACT_POINTER_SITE",
            }
    if 0 <= site < 0x1000000:
        return {"owner_class": "VEGA_BASE", "semantic_owner": "VEGA_BASE_ROM", "allocation_name": None,
                "allocation_region": "base", "semantic_evidence": "FILE_OFFSET_BELOW_CFRU_BOUNDARY"}
    if 0x1000000 <= site < 0x1200000:
        return {"owner_class": "CFRU_PAYLOAD", "semantic_owner": "CFRU_LINKED_PAYLOAD", "allocation_name": None,
                "allocation_region": "cfru", "semantic_evidence": "PINNED_CFRU_FILE_OFFSET_RANGE"}
    if 0x1600000 <= site < 0x1F50000:
        return {"owner_class": "DPE_PAYLOAD", "semantic_owner": "DPE_LINKED_PAYLOAD", "allocation_name": None,
                "allocation_region": "dpe", "semantic_evidence": "PINNED_DPE_FILE_OFFSET_RANGE"}
    _fail(f"pointer siteのsemantic ownerを解決できません: 0x{site:X}")
    raise AssertionError


def _context(stage: bytes, site: int, width: int, context_bytes: int) -> dict[str, Any]:
    start = max(0, min(site - 8, len(stage) - context_bytes))
    raw = stage[start:start + context_bytes]
    _require(start <= site and site + width <= start + len(raw), "pointer context内にsiteがありません")
    return {
        "parent_context_start": start, "site_offset_in_context": site - start,
        "parent_context_hex": raw.hex(), "parent_context_sha256": _sha(raw),
    }


def _literal_load_references(stage: bytes, site: int) -> dict[str, list[int]]:
    """ARM7TDMIのThumb/ARM PC-relative literal loadがsiteを参照する候補を返す。"""
    thumb: list[int] = []
    for instruction in range(max(0, site - 1024) & ~1, site, 2):
        halfword = struct.unpack_from("<H", stage, instruction)[0]
        if halfword & 0xF800 == 0x4800:
            target = ((instruction + 4) & ~3) + ((halfword & 0xFF) << 2)
            if target == site:
                thumb.append(instruction)
    arm: list[int] = []
    for instruction in range(max(0, site - 4096) & ~3, site, 4):
        word = struct.unpack_from("<I", stage, instruction)[0]
        if word & 0x0F7F0000 == 0x051F0000:
            displacement = word & 0xFFF
            target = instruction + 8 + (displacement if word & (1 << 23) else -displacement)
            if target == site:
                arm.append(instruction)
    return {"thumb16": thumb, "arm32": arm}


def _shifted_root_audit(
    stage: bytes, tables: Mapping[str, Mapping[str, Any]],
    derived_plan: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    confirmed = {int(row["site_offset"]) for row in derived_plan}
    hit_rows: list[dict[str, Any]] = []
    referenced: set[int] = set()
    for key in TABLE_KEYS:
        root = int(tables[key]["current_address"])
        for shift in range(1, 5):
            value = root >> shift
            sites = _all_offsets(stage, struct.pack("<I", value))
            if not sites:
                continue
            references = {site: _literal_load_references(stage, site) for site in sites}
            referenced_sites = [site for site, refs in references.items() if refs["thumb16"] or refs["arm32"]]
            referenced.update(referenced_sites)
            hit_rows.append({
                "table_key": key, "old_root": root, "shift": shift, "shifted_value": value,
                "exact_u32_occurrence_count": len(sites), "word_aligned_occurrence_count": sum(site % 4 == 0 for site in sites),
                "literal_referenced_site_offsets": referenced_sites,
                "literal_load_instruction_offsets": {
                    str(site): references[site] for site in referenced_sites
                },
            })
    _require(referenced == confirmed,
             f"shifted root literal参照集合がsemantic allowlistと不一致: observed={sorted(referenced)}, confirmed={sorted(confirmed)}")
    return {
        "scope": "ALL_28_RELOCATED_ROOTS_FULL_U32_UNALIGNED_RIGHT_SHIFT_1_THROUGH_4",
        "instruction_reference_scan": "THUMB16_LDR_LITERAL_PREVIOUS_1024_BYTES_AND_ARM32_LDR_LITERAL_PREVIOUS_4096_BYTES",
        "tables_with_exact_shift_hits": sorted({row["table_key"] for row in hit_rows}),
        "confirmed_semantic_site_offsets": sorted(confirmed),
        "unallowlisted_literal_referenced_sites": [], "rows": hit_rows,
        "conclusion": "ONLY_ABILITY_DESCRIPTIONS_RIGHT_SHIFT_2_THREE_CODEX_REWARD_CONSUMERS_CONFIRMED",
    }


def _species_count_literal_audit(stage: bytes, count_plan: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    allowed_by_old = {
        value: {int(row["site_offset"]) for row in count_plan if int(row["old"]) == value}
        for value in (1620, 1621)
    }
    rejected_data = {
        1620: set(),
        1621: {0x1A5CA8C, 0x1F77F70},
    }
    rows: list[dict[str, Any]] = []
    for value in (1620, 1621):
        sites = _all_offsets(stage, struct.pack("<I", value))
        references = {site: _literal_load_references(stage, site) for site in sites}
        referenced = {site for site, refs in references.items() if refs["thumb16"] or refs["arm32"]}
        _require(referenced == (allowed_by_old[value] - ({0x144BAA8} if value == 1621 else set())) | rejected_data[value],
                 f"Species count/max literal参照集合が監査allowlistと不一致: {value}")
        rows.append({
            "value": value, "exact_u32_occurrence_count": len(sites),
            "literal_referenced_site_offsets": sorted(referenced),
            "patched_semantic_site_offsets": sorted(allowed_by_old[value]),
            "rejected_data_site_offsets": sorted(rejected_data[value]),
        })
    return {
        "scope": "FULL_ROM_U32_EXACT_1620_MAX_AND_1621_COUNT_PLUS_THUMB_ARM_LITERAL_REFERENCE",
        "rejected_data_evidence": {
            "0x1A5CA8C": "DPE_STRUCTURED_POINTER_TAG_TABLE_ROW_NOT_EXECUTABLE",
            "0x1F77F70": "SPECIES_DEX_ENTRIES_ROW_1562_DATA_NOT_EXECUTABLE",
        },
        "rows": rows, "unresolved_executable_candidates": [],
    }


def _pointer_plan(
    stage: bytes, capacity: Mapping[str, Any], tables: Mapping[str, Mapping[str, Any]],
    previous: Mapping[str, Any], policy: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    inventory = capacity["consumer_audit"]["stage65_exact_literal_candidates"]
    old_spans = [(int(row["current_address"]) - GBA_ROM_BASE,
                  int(row["current_address"]) - GBA_ROM_BASE + int(row["old_size_bytes"]), key)
                 for key, row in tables.items()]
    allowed = set(policy["allow_owner_classes"])
    context_bytes = int(policy["context_bytes"])
    result: dict[str, list[dict[str, Any]]] = {}
    for key in TABLE_KEYS:
        table = tables[key]
        old_address = int(table["current_address"])
        expected = inventory[key]
        _require(int(expected["target_address"]) == old_address, f"{key}: pointer target address不一致")
        observed = _all_offsets(stage, struct.pack("<I", old_address))
        sites = [int(value) for value in expected["site_offsets"]]
        _require(observed == sites, f"{key}: Stage69 exact literal site集合がcapacity pinと不一致")
        rows: list[dict[str, Any]] = []
        for site in sites:
            enclosing = [span_key for start, end, span_key in old_spans if start <= site < end]
            _require(not enclosing, f"{key}: pointer siteがrelocated table内部です: 0x{site:X} ({enclosing})")
            owner = _semantic_owner(site, previous)
            _require(owner["owner_class"] in allowed, f"{key}: semantic owner class非許可")
            rows.append({
                "site_offset": site, "site_address": GBA_ROM_BASE + site,
                "old_pointer": old_address, **owner, **_context(stage, site, 4, context_bytes),
            })
        calculated = _sha(_json_bytes(sites))
        _require(calculated == expected["site_set_sha256"], f"{key}: site set SHA-256不一致")
        result[key] = rows
    return result


def _count_plan(stage: bytes, config: Mapping[str, Any], previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for spec in config["count_consumers"]["sites"]:
        site = int(spec["site"])
        width = int(spec["width"])
        _require(width in (1, 2, 4), "count patch width不正")
        old = int(spec["old"])
        new = int(spec["new"])
        _require(stage[site:site + width] == old.to_bytes(width, "little"), f"count site旧値不一致: 0x{site:X}")
        result.append({
            "site_offset": site, "site_address": GBA_ROM_BASE + site, "width": width,
            "old": old, "new": new, "consumer_semantic_owner": str(spec["owner"]),
            **_semantic_owner(site, previous), **_context(stage, site, width, 20),
        })
    _require(len({row["site_offset"] for row in result}) == len(result), "count consumer site重複")
    return result


def _derived_pointer_plan(stage: bytes, config: Mapping[str, Any], previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    section = config["derived_pointer_consumers"]
    _require(section["policy"] == "EXPLICIT_PARENT_CONTEXT_SEMANTIC_ALLOWLIST",
             "derived pointer policy不一致")
    result: list[dict[str, Any]] = []
    for spec in section["sites"]:
        site = int(spec["site"])
        width = int(spec["width"])
        old = int(spec["old"])
        key = str(spec["table_key"])
        _require(key in TABLE_KEYS and width == 4, "derived pointer table/width不一致")
        _require(spec["transform"] == "ADDRESS_RIGHT_SHIFT_2", "derived pointer transform不一致")
        _require(stage[site:site + width] == old.to_bytes(width, "little"),
                 f"derived pointer旧値不一致: 0x{site:X}")
        result.append({
            "table_key": key, "site_offset": site, "site_address": GBA_ROM_BASE + site,
            "width": width, "transform": spec["transform"], "old": old,
            "consumer_semantic_owner": str(spec["owner"]),
            **_semantic_owner(site, previous), **_context(stage, site, width, 20),
        })
    _require(len({row["site_offset"] for row in result}) == len(result), "derived pointer site重複")
    for key in {row["table_key"] for row in result}:
        rows = [row for row in result if row["table_key"] == key]
        old_values = {int(row["old"]) for row in rows}
        _require(len(old_values) == 1, f"{key}: derived old valueが一意ではありません")
        observed = _all_offsets(stage, struct.pack("<I", next(iter(old_values))))
        expected = [int(row["site_offset"]) for row in rows]
        _require(observed == expected, f"{key}: derived pointer exact site集合がallowlistと不一致")
    return result


def _ability_count_plan(stage: bytes, config: Mapping[str, Any], previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    section = config["ability_count_consumers"]
    _require(section["policy"] == "EXPLICIT_THUMB_MOVS_HALF_COUNT_THEN_LSLS_ONE_CONTEXT_ALLOWLIST",
             "ability count policy不一致")
    _require((int(section["old_count"]), int(section["new_count"])) == (312, 318),
             "ability count契約不一致")
    result: list[dict[str, Any]] = []
    for spec in section["sites"]:
        site = int(spec["site"])
        old = bytes.fromhex(str(spec["old_hex"]))
        new = bytes.fromhex(str(spec["new_hex"]))
        _require(len(old) == len(new) == 2, "ability count Thumb patch size不一致")
        _require(stage[site:site + 4] == old + b"\x5B\x00",
                 f"ability count Thumb MOVS/LSLS context不一致: 0x{site:X}")
        _require(int.from_bytes(old, "little") == 0x239C and int.from_bytes(new, "little") == 0x239F,
                 "ability count Thumb immediateが312/318契約ではありません")
        result.append({
            "site_offset": site, "site_address": GBA_ROM_BASE + site, "width": 2,
            "old_hex": old.hex(), "new_hex": new.hex(),
            "decoded_old": "movs r3,#156; lsls r3,#1 => 312",
            "decoded_new": "movs r3,#159; lsls r3,#1 => 318",
            "consumer_semantic_owner": str(spec["owner"]),
            **_semantic_owner(site, previous), **_context(stage, site, 2, 20),
        })
    _require(len({row["site_offset"] for row in result}) == len(result), "ability count site重複")
    signature = b"\x9C\x23\x5B\x00\x98\x42"
    _require(_all_offsets(stage, signature) == [int(row["site_offset"]) for row in result],
             "ability count Thumb signature集合がallowlistと不一致")
    return result


def _apply_and_audit(
    stage: bytes, payload: bytes, allocation: Mapping[str, Any], table_meta: Mapping[str, Any],
    pointer_plan: Mapping[str, Sequence[Mapping[str, Any]]], count_plan: Sequence[Mapping[str, Any]],
    derived_pointer_plan: Sequence[Mapping[str, Any]], ability_count_plan: Sequence[Mapping[str, Any]],
) -> tuple[bytes, list[dict[str, int]]]:
    output = bytearray(stage)
    payload_start = int(allocation["start"])
    payload_end = payload_start + len(payload)
    _require(payload_end == int(allocation["end_exclusive"]), "payload allocation end不一致")
    _require(stage[payload_start:payload_end] == b"\xFF" * len(payload), "Stage70 allocation先がerased FFではありません")
    output[payload_start:payload_end] = payload
    allowed_spans: list[tuple[int, int]] = [(payload_start, payload_end)]
    for key, rows in pointer_plan.items():
        new_address = GBA_ROM_BASE + payload_start + int(table_meta[key]["payload_relative_offset"])
        for row in rows:
            site = int(row["site_offset"])
            _require(output[site:site + 4] == struct.pack("<I", int(row["old_pointer"])), f"{key}: pointer patch旧値不一致")
            output[site:site + 4] = struct.pack("<I", new_address)
            allowed_spans.append((site, site + 4))
    for row in derived_pointer_plan:
        key = str(row["table_key"])
        site = int(row["site_offset"])
        new_address = GBA_ROM_BASE + payload_start + int(table_meta[key]["payload_relative_offset"])
        _require(new_address & 3 == 0, f"{key}: >>2 derived root用4-byte alignment不足")
        _require(output[site:site + 4] == int(row["old"]).to_bytes(4, "little"),
                 f"{key}: derived pointer patch旧値不一致")
        output[site:site + 4] = (new_address >> 2).to_bytes(4, "little")
        allowed_spans.append((site, site + 4))
    for row in count_plan:
        site = int(row["site_offset"])
        width = int(row["width"])
        _require(output[site:site + width] == int(row["old"]).to_bytes(width, "little"), f"count patch競合: 0x{site:X}")
        output[site:site + width] = int(row["new"]).to_bytes(width, "little")
        allowed_spans.append((site, site + width))
    for row in ability_count_plan:
        site = int(row["site_offset"])
        old = bytes.fromhex(str(row["old_hex"]))
        new = bytes.fromhex(str(row["new_hex"]))
        _require(output[site:site + 2] == old, f"ability count patch競合: 0x{site:X}")
        output[site:site + 2] = new
        allowed_spans.append((site, site + 2))
    for index, (before, after) in enumerate(zip(stage, output)):
        if before != after:
            _require(any(start <= index < end for start, end in allowed_spans), f"許可span外ROM変更: 0x{index:X}")
    merged: list[list[int]] = []
    for start, end in sorted(allowed_spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return bytes(output), [{"start": start, "end_exclusive": end, "size": end - start} for start, end in merged]


def _record_metadata(item: PreparedSpecies) -> dict[str, Any]:
    return {
        "id": int(item.reservation["id"]), "record_key": item.reservation["source_record_key"],
        "species_key": item.reservation["species_key"], "source_species_key": item.reservation["source_species_key"],
        "source_species_id": item.source_id, "classification": item.reservation["classification"],
        "national_dex": int(item.candidate["national_dex"]), "name_en": item.candidate["name_en"],
        "upstream_species_symbol": item.candidate["upstream_species_symbol"],
        "stats": list(item.stats), "type_ids": list(item.type_ids), "ability_key": item.reservation["ability_key"],
        "ability_id": item.ability_id, "ability_status": item.reservation["ability_status"],
        "ability_replacement_key": item.reservation.get("ability_replacement_key"),
        "front_coords": list(item.front_coords), "back_coords": list(item.back_coords),
        "elevation": item.elevation, "icon_palette": item.icon_palette,
        "asset_evidence": list(item.asset_evidence), "upstream_block_sha256": item.upstream_block_sha256,
        "clone_policy": {
            "source_rows": ["footprint", "cry", "cry2", "dex_entry", "name", "legacy_name", "level_up_pointer", "tmhm", "tutor", "wild"],
            "base_stats": "CLONE_SOURCE_THEN_PATCH_STATS_TYPES_ALL_ABILITY_SLOTS",
            "new_assets": ["front", "back", "normal_palette", "shiny_palette", "icon"],
            "evolution": "ZERO_STAGE71_OWNS_MEGA_LINKS",
        },
    }


def build_artifacts(root: Path) -> dict[str, bytes]:
    root = root.resolve()
    config_raw = (root / CONFIG_PATH).read_bytes()
    config = json.loads(config_raw)
    _require(config["task"] == TASK and int(config["stage"]) == 70, "Stage70 config identity不一致")
    inputs = config["inputs"]
    rom_path = root / inputs["rom"]["path"]
    stage = rom_path.read_bytes()
    _require(len(stage) == ROM_SIZE == int(inputs["rom"]["size"]), "Stage69 ROM size不一致")
    _require(_sha(stage) == inputs["rom"]["sha256"], "Stage69 ROM SHA-256不一致")
    _, allocation_raw, previous = _read_pinned(root, inputs["allocation"], "Stage69 allocation")
    _, candidate_raw, candidate_manifest = _read_pinned(root, inputs["candidate_manifest"], "P04 candidate manifest")
    _, capacity_raw, capacity = _read_pinned(root, inputs["capacity_manifest"], "P04 capacity manifest")
    _, asset_manifest_raw, asset_manifest = _read_pinned(root, inputs["asset_manifest"], "P04 asset manifest")
    _, asset_sources_raw, _ = _read_pinned(root, inputs["asset_sources"], "P04 asset sources")
    _, p05_config_raw, p05_config = _read_pinned(root, inputs["p05_ability_runtime_config"], "P05 config")
    _, p05_checkpoint_raw, _ = _read_pinned(root, inputs["p05_ability_runtime_checkpoint"], "P05 checkpoint")
    species_rows = _read_csv_pinned(root, inputs["species_manifest"], "species manifest")
    type_rows = _read_csv_pinned(root, inputs["type_manifest"], "type manifest")
    ability_manifest_rows = _read_csv_pinned(root, inputs["ability_manifest"], "ability manifest")
    tables = _table_definitions(capacity)

    reservations = list(capacity["id_reservations"]["species_form"]["rows"])
    _require([int(row["id"]) for row in reservations] == list(range(1621, 1670)), "P04 species reservation IDs不連続")
    excluded = set(config["species_ids"]["excluded_record_keys"])
    _require(excluded.isdisjoint({row["source_record_key"] for row in reservations}), "Browt/Pombon/Gecquaが予約に混入")
    candidates = {row["record_key"]: row for row in candidate_manifest["records"]}
    asset_rows = {row["record_key"]: row for row in asset_manifest["species_assets"]}
    _require({row["source_record_key"] for row in reservations} == set(asset_rows), "49形態とasset manifest集合が不一致")
    source_ids = _species_source_ids(species_rows)
    _require(source_ids.get("SPECIES_KEY_FLOETTE_ETERNAL") == 1029,
             "既存Floette Eternalのcanonical ID 1029が維持されていません")
    type_ids = _id_map(type_rows, "type_key")
    type_symbols = {row["type_key"]: row["dpe_symbol"] for row in type_rows}
    ability_ids = _id_map(ability_manifest_rows, "ability_key")
    ability_rows = list(config["ability_rows"])
    _require([int(row["id"]) for row in ability_rows] == list(range(312, 318)), "Stage70 ability IDs不連続")
    _require(p05_config["ability_allocation"]["new_count"] == 318, "P05 ability count pin不一致")
    _require([row["ability_key"] for row in ability_rows] == [row["ability_key"] for row in p05_config["ability_allocation"]["rows"]], "Stage70/P05 ability順不一致")
    ability_ids.update({str(row["ability_key"]): int(row["id"]) for row in ability_rows})
    upstream_root = root / str(inputs["upstream_checkout"])
    upstream_text, upstream_inventory = _upstream_text(upstream_root, str(inputs["upstream_commit"]))
    asset_root = root / str(inputs["asset_root"])

    vertical = _prepare_species(
        reservations[:1], candidates, asset_rows, source_ids, type_ids, type_symbols,
        ability_ids, upstream_text, asset_root,
    )
    _require(len(vertical) == 1 and int(vertical[0].reservation["id"]) == 1621, "1形態vertical slice失敗")
    prepared = _prepare_species(
        reservations, candidates, asset_rows, source_ids, type_ids, type_symbols,
        ability_ids, upstream_text, asset_root,
    )
    _require(_record_metadata(vertical[0]) == _record_metadata(prepared[0]), "縦切りと49形態展開の先頭行が不一致")

    pointer_plan = _pointer_plan(stage, capacity, tables, previous, config["pointer_consumers"])
    count_plan = _count_plan(stage, config, previous)
    derived_pointer_plan = _derived_pointer_plan(stage, config, previous)
    ability_count_plan = _ability_count_plan(stage, config, previous)
    shifted_root_audit = _shifted_root_audit(stage, tables, derived_pointer_plan)
    species_count_literal_audit = _species_count_literal_audit(stage, count_plan)
    blob, preliminary_tables = _build_blob(root, stage, tables, prepared, ability_rows)
    preliminary_payload = blob.finish(0)
    allocation, _ = _allocate(root, previous, config, len(preliminary_payload), _sha(preliminary_payload))
    payload = blob.finish(int(allocation["start"]))
    allocation, allocation_report = _allocate(root, previous, config, len(payload), _sha(payload))
    _require(allocation["content_sha256"] == _sha(payload), "allocation content identity不一致")
    output, changed_spans = _apply_and_audit(
        stage, payload, allocation, preliminary_tables, pointer_plan, count_plan,
        derived_pointer_plan, ability_count_plan,
    )

    tables_meta: dict[str, Any] = {}
    for key in TABLE_KEYS:
        table = preliminary_tables[key]
        new_offset = int(allocation["start"]) + int(table["payload_relative_offset"])
        new_raw = output[new_offset:new_offset + int(table["new_size"])]
        prefix = new_raw[:int(table["old_size"])]
        appended = new_raw[int(table["old_size"]):]
        _require(prefix == _slice(stage, int(table["old_address"]), int(table["old_size"]), key), f"{key}: 既存行byte保持失敗")
        sites = [int(row["site_offset"]) for row in pointer_plan[key]]
        for site in sites:
            _require(output[site:site + 4] == struct.pack("<I", GBA_ROM_BASE + new_offset), f"{key}: repoint検証失敗")
        _require(not _all_offsets(output, struct.pack("<I", int(table["old_address"]))), f"{key}: old root literalが残っています")
        derived_rows = [dict(row) for row in derived_pointer_plan if row["table_key"] == key]
        for row in derived_rows:
            site = int(row["site_offset"])
            _require(output[site:site + 4] == struct.pack("<I", (GBA_ROM_BASE + new_offset) >> 2),
                     f"{key}: derived pointer readback失敗")
        tables_meta[key] = {
            "old_address": int(table["old_address"]), "old_file_offset": int(table["old_address"]) - GBA_ROM_BASE,
            "old_count": int(table["old_count"]), "old_size": int(table["old_size"]), "old_sha256": table["old_sha256"],
            "capacity_stage65_old_sha256": table["capacity_stage65_old_sha256"],
            "parent_matches_capacity_stage65": table["parent_matches_capacity_stage65"],
            "new_address": GBA_ROM_BASE + new_offset, "new_file_offset": new_offset,
            "new_count": int(table["new_count"]), "new_size": int(table["new_size"]), "stride": int(table["stride"]),
            "new_sha256": _sha(new_raw), "existing_prefix_sha256": _sha(prefix), "appended_sha256": _sha(appended),
            "allocation_identity": {
                "name": allocation["name"], "owner": allocation["owner"], "region": allocation["region"],
                "start": allocation["start"], "end_exclusive": allocation["end_exclusive"],
                "content_sha256": allocation["content_sha256"],
            },
            "pointer_consumers": {
                "site_offsets": sites,
                "site_set_sha256": _sha(_json_bytes(sites)),
                "count": len(sites), "rows": pointer_plan[key],
                "derived_count": len(derived_rows),
                "derived_site_offsets": [row["site_offset"] for row in derived_rows],
                "derived_rows": derived_rows, "all_consumer_count": len(sites) + len(derived_rows),
            },
        }

    evolution_append = output[
        tables_meta["evolution"]["new_file_offset"] + tables_meta["evolution"]["old_size"]:
        tables_meta["evolution"]["new_file_offset"] + tables_meta["evolution"]["new_size"]
    ]
    _require(evolution_append == bytes(49 * 128), "evolution新49行がzeroではありません")
    _require(not _all_offsets(output, struct.pack("<I", int(tables["ability_descriptions"]["current_address"]) >> 2)),
             "ability_descriptions旧root>>2 consumerが残っています")
    for row in ability_count_plan:
        site = int(row["site_offset"])
        _require(output[site:site + 2] == bytes.fromhex(str(row["new_hex"])),
                 f"ability count readback失敗: 0x{site:X}")
    _require(not _all_offsets(output, b"\x9C\x23\x5B\x00\x98\x42"),
             "ability count 312 Thumb signatureが残っています")
    for item in prepared:
        index = int(item.reservation["id"])
        base = tables_meta["species_base_stats"]["new_file_offset"] + index * 32
        row = output[base:base + 32]
        _require(tuple(row[:6]) == item.stats and tuple(row[6:8]) == item.type_ids, f"{item.reservation['source_record_key']}: base stats readback失敗")
        _require(all(struct.unpack_from("<H", row, offset)[0] == item.ability_id for offset in (22, 26, 28)), f"{item.reservation['source_record_key']}: ability readback失敗")

    patch = create_bps(stage, output)
    _require(apply_bps(stage, patch) == output, "Stage70 BPS roundtrip失敗")
    records = [_record_metadata(item) for item in prepared]
    ability_runtime = {
        "old_count": 312, "new_count": 318,
        "stable_keys": [row["ability_key"] for row in ability_rows],
        "localization_status": config["ability_content_policy"]["localization_status"],
        "localization_replacement_contract": "STABLE_ABILITY_KEY_AND_CANONICAL_ID_REPLACEABLE",
        "description_replacement_trigger": "STAGE72_EFFECT_HOOK_CONNECTED_THEN_REPLACE_PENDING_NOTICE_WITH_REVIEWED_JAPANESE_SEMANTICS",
        "effect_runtime_status": "EFFECT_RUNTIME_PENDING_STAGE72",
        "rating_and_mold_breaker_status": "STAGE70_UI_OOB_SAFE_DEFAULT_MANDATORY_STAGE72_REVIEW_NOT_OFFICIAL",
        "ui_rows_safe": True,
        "fixed_table_keys": list(ABILITY_TABLE_KEYS),
        "facility_team_builder_boundary": "ABILITY_ON_TEAM_312_BYTE_ARRAY_UNCHANGED_NEW_MEGA_BATTLE_ONLY_NOT_IN_FACILITY_GENERATION_POOL_STAGE72_REVIEW",
        "consumer_audit": {
            "exact_root_policy": "PINNED_CAPACITY_ALL_U32_LITERAL_OCCURRENCES",
            "shift_search_scope": "FULL_U32_UNALIGNED_EXACT_ROOT_RIGHT_SHIFT_1_THROUGH_4_ON_PINNED_STAGE69",
            "confirmed_derived_consumers": 3,
            "confirmed_derived_table": "ability_descriptions",
            "confirmed_reconstruction": "(LITERAL_0x0241330A + ABILITY_ID) << 2 = 0x0904CC28 + ABILITY_ID*4",
            "confirmed_thumb_sequence": "LDR_LITERAL; ADDS_ABILITY; LSLS_2; CALL_TEXT_COPY",
            "confirmed_source_owner": "CodexBattleRewards_FillSummaryAbility T28/T29/T30",
            "other_exact_shifted_root_hits": 0,
            "broader_row_address_or_low_width_hits": "REJECTED_NON_WORD_ALIGNED_GRAPHICS_OR_PACKED_DATA_WITHOUT_EXECUTABLE_SOURCE_OWNER",
        },
        "rows": [{**row, "localization_status": "PROVISIONAL_LOCALIZATION_REPLACEABLE", "effect_runtime_status": "EFFECT_RUNTIME_PENDING_STAGE72",
                  "technical_runtime_profile": p05_config["runtime_profile"]["abilities"][row["ability_key"]],
                  "rating_semantics": "SAFETY_DEFAULT_NOT_OFFICIAL", "mold_breaker_semantics": "SAFETY_DEFAULT_NOT_OFFICIAL"} for row in ability_rows],
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": 70, "status": "ROM_MATERIALIZED_CHECKPOINT",
        "parent_rom": {"path": inputs["rom"]["path"], "size": len(stage), "sha256": _sha(stage)},
        "output_rom": {"path": config["outputs"]["rom"], "size": len(output), "sha256": _sha(output)},
        "allocation": allocation, "allocation_report_sha256": _sha(_json_bytes(allocation_report)),
        "payload": {"size": len(payload), "sha256": _sha(payload), "header_magic_hex": HEADER_MAGIC.hex()},
        "tables": tables_meta, "count_consumers": {"policy": config["count_consumers"]["policy"], "rows": count_plan},
        "ability_count_consumers": {"policy": config["ability_count_consumers"]["policy"], "rows": ability_count_plan},
        "consumer_audits": {
            "shifted_roots": shifted_root_audit,
            "species_count_literals": species_count_literal_audit,
        },
        "species": {"old_count": 1621, "new_count": 1670, "new_ids": [1621, 1669], "records": records,
                    "excluded_record_keys": sorted(excluded)},
        "ability_runtime": ability_runtime,
        "vertical_slice": {"record_key": records[0]["record_key"], "species_id": 1621,
                           "status": "PASS_BEFORE_BULK_EXPANSION", "record_sha256": _sha(_json_bytes(records[0]))},
        "scope": {
            "battle_mega_change_hooks": "OUT_OF_SCOPE_STAGE71", "ability_effect_hooks": "EFFECT_RUNTIME_PENDING_STAGE72",
            "side_change": "NOT_REFERENCED", "existing_species_rows_0_1620": "BYTE_EXACT_PREFIX_ALL_TABLES",
            "actual_hardware_or_mgba": "PENDING_SEPARATE_REPRESENTATIVE_RUNTIME_READ",
        },
        "changed_spans": changed_spans,
        "source_evidence": {
            "config_sha256": _sha(config_raw), "candidate_manifest_sha256": _sha(candidate_raw),
            "capacity_manifest_sha256": _sha(capacity_raw), "asset_manifest_sha256": _sha(asset_manifest_raw),
            "asset_sources_sha256": _sha(asset_sources_raw), "stage69_allocation_sha256": _sha(allocation_raw),
            "p05_config_sha256": _sha(p05_config_raw), "p05_checkpoint_sha256": _sha(p05_checkpoint_raw),
            "upstream_commit": inputs["upstream_commit"], "upstream_species_headers": upstream_inventory,
            "private_asset_root": inputs["asset_root"], "private_assets_tracked": False,
        },
        "checks": {
            "one_form_vertical_slice_before_bulk": "PASS", "all_49_rows_materialized": "PASS",
            "all_28_fixed_tables_relocated": "PASS", "existing_prefixes_byte_exact": "PASS",
            "pointer_consumers_exact_context_fail_closed": "PASS", "count_consumers_explicit_context": "PASS",
            "allocation_overlap_count": allocation_report["summaries"]["overlap_count"],
            "rom_outside_declared_spans_unchanged": "PASS", "evolution_new_rows_zero": "PASS",
            "ability_ui_rows_318_safe": "PASS", "bps_roundtrip": "PASS",
            "floette_eternal_species_id_1029_preserved": "PASS",
            "ability_derived_description_consumers_rebound": "PASS",
            "ability_runtime_count_consumers_318": "PASS",
            "all_species_and_ability_shifted_roots_audited": "PASS",
            "species_count_max_executable_literals_allowlisted": "PASS",
        },
    }
    contract = {
        "schema_version": 1, "task": TASK, "status": "STAGE70_RUNTIME_CONTRACT",
        "parent_rom_sha256": _sha(stage), "output_rom_sha256": _sha(output),
        "species_id_range": [1621, 1669], "species_count": 1670,
        "excluded_record_keys": sorted(excluded), "tables": tables_meta,
        "ability_runtime": ability_runtime,
        "ability_count_consumers": {"policy": config["ability_count_consumers"]["policy"], "rows": ability_count_plan},
        "consumer_audits": metadata["consumer_audits"],
        "records": records,
        "clone_and_asset_policy": {
            "clone_source_table_rows": ["footprint", "cry", "cry2", "dex_entries", "names", "level_up", "tmhm", "tutor", "wild"],
            "new_private_assets": ["front", "back", "normal_palette", "shiny_palette", "icon"],
            "assets_are_from_pinned_external_repository": True,
            "evolution_rows": "ALL_ZERO_STAGE71_EXCLUSIVE_SEMANTIC_OWNER",
        },
        "pending": ["STAGE71_MEGA_FORWARD_REVERSE_EVOLUTION_ROWS_AND_BATTLE_CHANGE", "STAGE72_ABILITY_EFFECT_HOOKS_AND_DEFAULT_REVIEW", "STAGE72_FACILITY_TEAMBUILDER_ABILITY_ON_TEAM_312_ARRAY_REVIEW_BEFORE_NEW_ABILITIES_ENTER_POOL", "REPRESENTATIVE_MGBA_CREATE_MON_RENDER_READ"],
    }
    rows_output = {
        "schema_version": 1, "task": TASK, "vertical_slice": metadata["vertical_slice"],
        "species_records": records, "ability_rows": ability_runtime["rows"],
    }
    checkpoint = {
        "schema_version": 1, "task": TASK, "stage": 70, "status": "ROM_MATERIALIZED_CHECKPOINT",
        "parent_rom_sha256": _sha(stage), "output_rom_sha256": _sha(output), "payload_sha256": _sha(payload),
        "allocation_identity": tables_meta["evolution"]["allocation_identity"],
        "evolution_table": tables_meta["evolution"],
        "ability_tables": {key: tables_meta[key] for key in ABILITY_TABLE_KEYS},
        "ability_count_consumers": ability_count_plan,
        "consumer_audits": metadata["consumer_audits"],
        "species_table_count": len(SPECIES_TABLE_KEYS), "ability_table_count": len(ABILITY_TABLE_KEYS),
        "checks": metadata["checks"], "pending": contract["pending"],
    }
    return {
        config["outputs"]["rom"]: output,
        config["outputs"]["metadata"]: _json_bytes(metadata),
        config["outputs"]["allocation"]: _json_bytes(allocation_report),
        config["outputs"]["bps"]: patch,
        config["outputs"]["contract"]: _json_bytes(contract),
        config["outputs"]["checkpoint"]: _json_bytes(checkpoint),
        config["outputs"]["generated_payload"]: payload,
        config["outputs"]["generated_rows"]: _json_bytes(rows_output),
    }


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def materialize(root: Path, *, check: bool = False) -> dict[str, Any]:
    artifacts = build_artifacts(root)
    differences: list[str] = []
    for relative, raw in artifacts.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_bytes() != raw:
                differences.append(relative)
        else:
            _atomic_write(path, raw)
    if check and differences:
        _fail("生成物が再現結果と不一致です: " + ", ".join(differences))
    config = _read_json(root / CONFIG_PATH)
    metadata = json.loads(artifacts[config["outputs"]["metadata"]])
    return {
        "status": "PASS", "mode": "CHECK" if check else "WRITE",
        "output_rom_sha256": metadata["output_rom"]["sha256"],
        "payload_sha256": metadata["payload"]["sha256"],
        "species_count": metadata["species"]["new_count"],
        "new_species_rows": len(metadata["species"]["records"]),
        "ability_count": metadata["ability_runtime"]["new_count"],
        "evolution_address": metadata["tables"]["evolution"]["new_address"],
        "evolution_stride": metadata["tables"]["evolution"]["stride"],
        "evolution_pointer_sites": metadata["tables"]["evolution"]["pointer_consumers"]["count"],
    }


__all__ = [
    "ABILITY_TABLE_KEYS", "CONFIG_PATH", "HEADER_MAGIC", "SPECIES_TABLE_KEYS",
    "SpeciesRuntimeError", "TABLE_KEYS", "build_artifacts", "materialize",
    "_all_offsets", "_lz77_decompress", "_lz77_literal",
]
