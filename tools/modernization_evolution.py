#!/usr/bin/env python3
"""Modernization P02: evolution tableをstable keyで監査する決定的契約builder。"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

from scripts.build_species_surface import (
    EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
    EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
    MEGA_VARIANT_WISH,
    remap_evolution_parameters,
)
from tools.modernization_identity import (
    CheckedArchive,
    ManifestIndex,
    ModernizationIdentityError,
    load_manifests,
    stable_json,
)


SCHEMA_VERSION = 1
ROM_BASE = 0x08000000
SPECIES_COUNT = 1621
EVOLUTION_STRIDE = 128
EVOLUTION_SLOTS = 16
EVOLUTION_ENTRY_SIZE = 8

EVOLUTION_BINARY = Path("generated/engine/evolutions/evolutions.bin")
EVOLUTION_MODEL = Path("generated/engine/evolutions/evolutions.json")
IDENTITY_CONTRACT = Path("content/modernization/identity_contract.json")
STAGE09_METADATA = Path("build/stages/09_species_surface.json")
STAGE09_ROM = Path("build/stages/09_species_surface.gba")
LEVEL_POINTERS = Path("generated/engine/learnsets/level_up_pointers.bin")
LEVEL_DATA = Path("generated/engine/learnsets/level_up_data.bin")

RUNTIME_SOURCES = (
    Path("vendor/upstream/CFRU-JP/include/pokemon.h"),
    Path("vendor/upstream/CFRU-JP/src/config.h"),
    Path("vendor/upstream/CFRU-JP/src/evolution.c"),
    Path("vendor/upstream/CFRU-JP/src/mega.c"),
    Path("vendor/upstream/CFRU-JP/src/dynamax.c"),
    Path("vendor/upstream/CFRU-JP/src/terastal.c"),
)
GENERATOR_SOURCE = Path("scripts/build_species_surface.py")
DPE_EVOLUTION_SOURCE = Path("vendor/upstream/DPE-JP/src/Evolution Table.c")
DPE_LEARNSET_SOURCE = Path("vendor/upstream/DPE-JP/src/Learnsets.c")

ZIP_MEMBERS = {
    "official_existing": "05_\u65e2\u5b58\u539f\u4f5c205\u7a2e_\u9032\u5316\u5168\u884c_\u751f\u30c7\u30fc\u30bf\u3068\u8aac\u660e.csv",
    "vega_unique": "06_\u7dad\u6301\u5019\u88dc_\u539f\u4f5c\u304b\u3089\u30d9\u30ac\u72ec\u81ea\u3078\u306e26\u9032\u5316.csv",
    "description_mismatch": "07_\u9032\u5316\u8aac\u660e\u4e0d\u6574\u5408_\u78ba\u8a8d15\u7d4c\u8def.csv",
    "public_vega_diff": "08_\u516c\u958b\u30d9\u30ac\u3068\u306e\u5dee_\u9032\u531610\u7d4c\u8def.csv",
    "missing_branches": "09_\u4e0d\u8db3\u3059\u308b\u539f\u4f5c\u5206\u5c90_3\u7cfb\u7d71.csv",
}


class ModernizationEvolutionError(ValueError):
    """進化契約の入力またはruntime ABIが矛盾している。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationEvolutionError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file(root: Path, relative: Path) -> tuple[Path, bytes]:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"通常ファイルではありません: {relative.as_posix()}")
    return path, path.read_bytes()


def _identity(relative: Path, raw: bytes) -> dict[str, Any]:
    return {
        "path": relative.as_posix(),
        "size": len(raw),
        "sha256": _sha256(raw),
    }


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}が有効なJSONではありません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label}のrootがobjectではありません")
    return value


def _csv(raw: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        _fail(f"{label}がUTF-8 CSVではありません: {error}")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail(f"{label}のheaderがありません、または重複しています")
    rows = list(reader)
    if any(None in row for row in rows):
        _fail(f"{label}にheader外の列があります")
    return rows


def _integer(value: Any, label: str, *, maximum: int = 0xFFFF) -> int:
    raw = str(value)
    if re.fullmatch(r"0|[1-9][0-9]*", raw) is None:
        _fail(f"{label}が非負10進整数ではありません: {raw!r}")
    result = int(raw)
    if result > maximum:
        _fail(f"{label}が範囲外です: {result} > {maximum}")
    return result


@dataclass(frozen=True)
class MethodSpec:
    method_id: int
    key: str
    family: str
    parameter_role: str
    extra_role: str = "ZERO"
    runtime_supported: bool = True


_METHOD_ROWS = (
    (1, "EVO_FRIENDSHIP", "PERSISTENT", "ZERO"),
    (2, "EVO_FRIENDSHIP_DAY", "PERSISTENT", "ZERO"),
    (3, "EVO_FRIENDSHIP_NIGHT", "PERSISTENT", "ZERO"),
    (4, "EVO_LEVEL", "PERSISTENT", "LEVEL"),
    (5, "EVO_TRADE", "PERSISTENT", "ZERO"),
    (6, "EVO_TRADE_ITEM", "PERSISTENT", "ITEM"),
    (7, "EVO_ITEM", "PERSISTENT", "ITEM", "GENDER_OR_ZERO"),
    (8, "EVO_LEVEL_ATK_GT_DEF", "PERSISTENT", "LEVEL"),
    (9, "EVO_LEVEL_ATK_EQ_DEF", "PERSISTENT", "LEVEL"),
    (10, "EVO_LEVEL_ATK_LT_DEF", "PERSISTENT", "LEVEL"),
    (11, "EVO_LEVEL_SILCOON", "PERSISTENT", "LEVEL"),
    (12, "EVO_LEVEL_CASCOON", "PERSISTENT", "LEVEL"),
    (13, "EVO_LEVEL_NINJASK", "PERSISTENT", "LEVEL"),
    (14, "EVO_LEVEL_SHEDINJA", "PERSISTENT", "LEVEL"),
    (15, "EVO_BEAUTY", "PERSISTENT", "BEAUTY"),
    (16, "EVO_RAINY_FOGGY_OW", "PERSISTENT", "LEVEL"),
    (17, "EVO_MOVE_TYPE", "PERSISTENT", "TYPE", "FRIENDSHIP_FLAG"),
    (18, "EVO_TYPE_IN_PARTY", "PERSISTENT", "LEVEL", "TYPE"),
    (19, "EVO_MAP", "PERSISTENT", "MAP_SECTION"),
    (20, "EVO_MALE_LEVEL", "PERSISTENT", "LEVEL"),
    (21, "EVO_FEMALE_LEVEL", "PERSISTENT", "LEVEL"),
    (22, "EVO_LEVEL_NIGHT", "PERSISTENT", "LEVEL"),
    (23, "EVO_LEVEL_DAY", "PERSISTENT", "LEVEL"),
    (24, "EVO_HOLD_ITEM_NIGHT", "PERSISTENT", "ITEM"),
    (25, "EVO_HOLD_ITEM_DAY", "PERSISTENT", "ITEM"),
    (26, "EVO_MOVE", "PERSISTENT", "MOVE"),
    (27, "EVO_OTHER_PARTY_MON", "PERSISTENT", "SPECIES"),
    (28, "EVO_LEVEL_SPECIFIC_TIME_RANGE", "PERSISTENT", "LEVEL", "TIME_RANGE"),
    (29, "EVO_FLAG_SET", "PERSISTENT", "FLAG"),
    (30, "EVO_CRITICAL_HIT", "PERSISTENT", "ZERO"),
    (31, "EVO_NATURE_HIGH", "PERSISTENT", "LEVEL"),
    (32, "EVO_NATURE_LOW", "PERSISTENT", "LEVEL"),
    (33, "EVO_DAMAGE_LOCATION", "PERSISTENT", "ZERO", "ZERO", False),
    (34, "EVO_ITEM_LOCATION", "PERSISTENT", "ITEM", "TILE_BEHAVIOR"),
    (35, "EVO_LEVEL_HOLD_ITEM", "PERSISTENT", "LEVEL", "ITEM"),
    (36, "EVO_ITEM_HOLD_ITEM", "PERSISTENT", "ITEM", "ITEM"),
    (37, "EVO_MOVE_MALE", "PERSISTENT", "MOVE"),
    (38, "EVO_MOVE_FEMALE", "PERSISTENT", "MOVE"),
    (39, "EVO_ITEM_NIGHT", "PERSISTENT", "ITEM"),
    (40, "EVO_MAUSHOLD_THREE", "PERSISTENT", "LEVEL"),
    (41, "EVO_MAUSHOLD_FOUR", "PERSISTENT", "LEVEL"),
    (42, "EVO_DUDUNSPARCE_TWO", "PERSISTENT", "MOVE"),
    (43, "EVO_DUDUNSPARCE_THREE", "PERSISTENT", "MOVE"),
    (252, "EVO_TERASTAL", "BATTLE_TRANSFORM", "DIRECTION_FLAG"),
    (253, "EVO_GIGANTAMAX", "BATTLE_TRANSFORM", "DIRECTION_FLAG"),
    (254, "EVO_MEGA", "BATTLE_TRANSFORM", "MEGA_DYNAMIC", "MEGA_VARIANT"),
)
METHODS: dict[int, MethodSpec] = {
    row[0]: MethodSpec(*row) for row in _METHOD_ROWS
}


def parse_runtime_method_enum(raw: bytes) -> dict[str, int]:
    """C headerの暗黙incrementを展開し、進化method ABIを検証可能にする。"""

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        _fail(f"pokemon.hがUTF-8ではありません: {error}")
    match = re.search(r"enum\s+EvolutionMethods\s*\{(.*?)\};", text, re.S)
    if match is None:
        _fail("EvolutionMethods enumが見つかりません")
    body = re.sub(r"/\*.*?\*/", "", match.group(1), flags=re.S)
    body = re.sub(r"//[^\n]*", "", body)
    values: dict[str, int] = {}
    current = -1
    for token in body.split(","):
        token = token.strip()
        if not token:
            continue
        parsed = re.match(r"(EVO_[A-Z0-9_]+)(?:\s*=\s*(0x[0-9A-Fa-f]+|[0-9]+))?", token)
        if parsed is None:
            continue
        current = int(parsed.group(2), 0) if parsed.group(2) else current + 1
        values[parsed.group(1)] = current
    for key, literal in re.findall(
        r"#define\s+(EVO_(?:TERASTAL|GIGANTAMAX|MEGA))\s+(0x[0-9A-Fa-f]+|[0-9]+)",
        text,
    ):
        values[key] = int(literal, 0)
    expected = {"EVO_NONE": 0, **{spec.key: method_id for method_id, spec in METHODS.items()}}
    if values != expected:
        _fail(f"EvolutionMethods ABIが契約外です: actual={values} expected={expected}")
    return values


def parse_evolution_binary(
    raw: bytes,
    *,
    species_count: int = SPECIES_COUNT,
) -> list[dict[str, int]]:
    expected = species_count * EVOLUTION_STRIDE
    if len(raw) != expected:
        _fail(f"進化table size不一致: {len(raw)} != {expected}")
    rows: list[dict[str, int]] = []
    for source_id in range(species_count):
        seen_zero = False
        seen_entries: set[tuple[int, int, int, int]] = set()
        for slot in range(EVOLUTION_SLOTS):
            offset = source_id * EVOLUTION_STRIDE + slot * EVOLUTION_ENTRY_SIZE
            method, parameter, target_id, extra = struct.unpack_from("<HHHH", raw, offset)
            if method == 0:
                # T06由来の一部終端rowには、method/targetを0にした後のlevel値だけが
                # parameterへ残る。consumerはmethod==0を終端として扱うため進化行では
                # ない。target/extraを伴う曖昧なpayloadだけは拒否する。
                if target_id or extra:
                    _fail(
                        f"EVO_NONE rowにtarget/extra payloadがあります: species={source_id} slot={slot}"
                    )
                seen_zero = True
                continue
            if seen_zero:
                _fail(
                    f"進化rowがEVO_NONE後にあり、battle consumerから不可視です: "
                    f"species={source_id} slot={slot}"
                )
            entry = (method, parameter, target_id, extra)
            if entry in seen_entries:
                _fail(f"進化tupleが重複しています: species={source_id} slot={slot}")
            seen_entries.add(entry)
            rows.append({
                "source_id": source_id,
                "slot": slot,
                "method_id": method,
                "parameter": parameter,
                "target_id": target_id,
                "extra": extra,
                "table_offset": offset,
            })
    return rows


def _padding_residues(raw: bytes) -> list[dict[str, int]]:
    """method=0のため非行だが、旧prefixに残るparameter値を可視化する。"""

    output: list[dict[str, int]] = []
    for source_id in range(SPECIES_COUNT):
        for slot in range(EVOLUTION_SLOTS):
            offset = source_id * EVOLUTION_STRIDE + slot * EVOLUTION_ENTRY_SIZE
            method, parameter, target_id, extra = struct.unpack_from("<HHHH", raw, offset)
            if method == 0 and parameter:
                if target_id or extra:
                    _fail(f"EVO_NONE residueにtarget/extraがあります: species={source_id} slot={slot}")
                output.append({
                    "source_id": source_id,
                    "slot": slot,
                    "parameter_residue": parameter,
                    "table_relative_offset": offset,
                })
    return output


def _species_ref(index: ManifestIndex, species_id: int, label: str) -> dict[str, Any]:
    row = index.by_id.get(species_id)
    if row is None:
        _fail(f"{label} Species IDがcanonical範囲外です: {species_id}")
    return {
        "species_key": row["species_key"],
        "canonical_id": species_id,
        "display_name": row["display_name"],
        "form_key": row.get("form_key", ""),
        "national_dex": _integer(
            row.get("canonical_national_dex", "0") or "0",
            f"{label}:canonical_national_dex",
        ),
        "classification": row.get("classification", ""),
        "status": row.get("status", ""),
    }


def _entity_ref(index: ManifestIndex, entity_id: int, label: str) -> dict[str, Any]:
    row = index.by_id.get(entity_id)
    if row is None:
        _fail(f"{label} IDがcanonical範囲外です: {entity_id}")
    key = row[index.spec.key_field]
    result = {
        "key": key,
        "canonical_id": entity_id,
        "display_name": row["display_name"],
        "status": row.get("status", ""),
    }
    if index.spec.name == "items":
        result.update({
            "item_type_key": row.get("item_type_key", ""),
            "is_evolution_item": row.get("is_evolution_item", ""),
            "consume_policy": row.get("consume_policy", ""),
            "supply_key": row.get("supply_key", ""),
            "runtime_binding": row.get("runtime_binding", ""),
        })
    return result


def _value_contract(
    role: str,
    value: int,
    manifests: Mapping[str, ManifestIndex],
    label: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {"role": role, "value": value}
    if role == "ZERO":
        if value != 0:
            _fail(f"{label}は0でなければなりません: {value}")
    elif role == "LEVEL":
        if not 1 <= value <= 100:
            _fail(f"{label} levelが範囲外です: {value}")
    elif role == "BEAUTY":
        if not 1 <= value <= 255:
            _fail(f"{label} beauty thresholdが範囲外です: {value}")
    elif role == "ITEM":
        if value == 0:
            _fail(f"{label} Item IDが0です")
        result["reference"] = _entity_ref(manifests["items"], value, label)
    elif role == "MOVE":
        if value == 0:
            _fail(f"{label} Move IDが0です")
        result["reference"] = _entity_ref(manifests["moves"], value, label)
    elif role == "TYPE":
        result["reference"] = _entity_ref(manifests["types"], value, label)
    elif role == "SPECIES":
        if value == 0:
            _fail(f"{label} Species IDが0です")
        result["reference"] = _species_ref(manifests["species"], value, label)
    elif role in {"MAP_SECTION", "FLAG", "TILE_BEHAVIOR"}:
        if value == 0:
            _fail(f"{label} engine scalarが0です")
    elif role == "GENDER_OR_ZERO":
        if value not in {0, 0xFE}:
            _fail(f"{label} gender markerが契約外です: {value}")
        result["meaning"] = "MALE_OR_UNRESTRICTED" if value == 0 else "FEMALE"
    elif role == "FRIENDSHIP_FLAG":
        if value not in {0, 1}:
            _fail(f"{label} friendship flagが0/1ではありません: {value}")
        result["requires_friendship_220"] = bool(value)
    elif role == "TIME_RANGE":
        start, end = value >> 8, value & 0xFF
        if not (0 <= start <= 23 and 1 <= end <= 24 and start < end):
            _fail(f"{label} time rangeが不正です: {value:#06x}")
        result.update({"start_hour_inclusive": start, "end_hour_exclusive": end})
    elif role == "DIRECTION_FLAG":
        if value not in {0, 1}:
            _fail(f"{label} transform directionが0/1ではありません: {value}")
        result["direction"] = "FORWARD" if value else "REVERSE"
    elif role == "MEGA_VARIANT":
        if value not in {0, 1, 2, 3}:
            _fail(f"{label} Mega variantが契約外です: {value}")
        result["variant"] = {
            0: "STANDARD_ITEM", 1: "PRIMAL_ITEM", 2: "WISH_MOVE", 3: "ULTRA_ITEM",
        }[value]
    else:
        _fail(f"{label}の未定義value roleです: {role}")
    return result


def _condition_ja(spec: MethodSpec, parameter: dict[str, Any], extra: dict[str, Any]) -> str:
    value = parameter["value"]
    ref = parameter.get("reference", {})
    name = ref.get("display_name", ref.get("species_key", str(value)))
    by_method = {
        1: "なつき度220以上でレベルアップ",
        2: "昼、なつき度220以上でレベルアップ",
        3: "夜、なつき度220以上でレベルアップ",
        4: f"Lv.{value}以上でレベルアップ",
        5: "通信交換",
        6: f"{name}を持たせて通信交換",
        7: f"{name}を使用",
        8: f"Lv.{value}以上かつ攻撃>防御",
        9: f"Lv.{value}以上かつ攻撃=防御",
        10: f"Lv.{value}以上かつ攻撃<防御",
        11: f"Lv.{value}以上かつpersonality分岐(0-4)",
        12: f"Lv.{value}以上かつpersonality分岐(5-9)",
        13: f"Lv.{value}以上（ヌケニン派生元）",
        14: f"Lv.{value}以上（ヌケニン特殊生成）",
        15: f"うつくしさ{value}以上",
        16: f"Lv.{value}以上かつ雨または霧",
        17: f"{name}タイプの技を覚えている",
        18: f"Lv.{value}以上かつpartyに{extra.get('reference', {}).get('display_name', extra['value'])}タイプ",
        19: f"region map section {value}でレベルアップ",
        20: f"Lv.{value}以上かつ♂",
        21: f"Lv.{value}以上かつ♀",
        22: f"Lv.{value}以上かつ夜",
        23: f"Lv.{value}以上かつ昼",
        24: f"{name}を持たせて夜にレベルアップ",
        25: f"{name}を持たせて昼にレベルアップ",
        26: f"{name}を覚えてレベルアップ",
        27: f"partyに{name}がいる状態でレベルアップ",
        28: f"Lv.{value}以上かつ{extra.get('start_hour_inclusive')}時以上{extra.get('end_hour_exclusive')}時未満",
        29: f"flag {value}がONの状態でレベルアップ",
        30: "1戦中に急所を3回成功後",
        31: f"Lv.{value}以上かつhigh nature",
        32: f"Lv.{value}以上かつlow nature",
        33: "runtime未実装",
        34: f"tile behavior {extra['value']}上で{name}を使用",
        35: f"Lv.{value}以上かつ{extra.get('reference', {}).get('display_name', extra['value'])}を所持",
        36: f"{extra.get('reference', {}).get('display_name', extra['value'])}を所持して{name}を使用",
        37: f"{name}を覚えている♂",
        38: f"{name}を覚えている♀",
        39: f"夜に{name}を使用",
        40: f"Lv.{value}以上（イッカネズミ3びきpersonality分岐）",
        41: f"Lv.{value}以上（イッカネズミ4ひきpersonality分岐）",
        42: f"{name}を覚えている（ノココッチ2ふしpersonality分岐）",
        43: f"{name}を覚えている（ノココッチ3ふしpersonality分岐）",
        252: "テラスタル戦闘内変身" if value else "テラスタル解除",
        253: "キョダイマックス戦闘内変身" if value else "キョダイマックス解除",
    }
    if spec.method_id == 254:
        if value == 0:
            return "メガ・ゲンシ・ウルトラ変身解除"
        trigger_name = parameter.get("reference", {}).get("display_name", str(value))
        return f"{extra['variant']}条件: {trigger_name}"
    text = by_method[spec.method_id]
    if spec.method_id == 17 and extra.get("requires_friendship_220"):
        text += "、かつなつき度220以上"
    return text


def normalize_evolution_rows(
    binary_rows: Sequence[Mapping[str, int]],
    manifests: Mapping[str, ManifestIndex],
    *,
    runtime_address: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """全tupleをstable species_keyへ解決し、parameter namespaceも検査する。"""

    output: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    seen_row_keys: set[str] = set()
    for raw in binary_rows:
        source_id = int(raw["source_id"])
        target_id = int(raw["target_id"])
        slot = int(raw["slot"])
        method_id = int(raw["method_id"])
        parameter_value = int(raw["parameter"])
        extra_value = int(raw["extra"])
        source = _species_ref(manifests["species"], source_id, "evolution source")
        target = _species_ref(manifests["species"], target_id, "evolution target")
        spec = METHODS.get(method_id)
        if spec is None:
            _fail(f"未定義Evolution methodです: species={source_id} slot={slot} method={method_id}")
        if not spec.runtime_supported:
            _fail(f"runtime未実装methodがtableにあります: {spec.key} species={source_id}")

        if spec.parameter_role == "MEGA_DYNAMIC":
            extra = _value_contract("MEGA_VARIANT", extra_value, manifests, "Mega extra")
            if parameter_value == 0:
                parameter = {"role": "ZERO", "value": 0, "direction": "REVERSE"}
            else:
                role = "MOVE" if extra_value == 2 else "ITEM"
                parameter = _value_contract(role, parameter_value, manifests, "Mega parameter")
                parameter["direction"] = "FORWARD"
        else:
            parameter = _value_contract(
                spec.parameter_role, parameter_value, manifests, f"{spec.key} parameter",
            )
            extra = _value_contract(
                spec.extra_role, extra_value, manifests, f"{spec.key} extra",
            )

        row_key = f"{source['species_key']}#SLOT_{slot:02d}"
        if row_key in seen_row_keys:
            _fail(f"stable evolution row keyが重複しています: {row_key}")
        seen_row_keys.add(row_key)
        table_offset = int(raw["table_offset"])
        row = {
            "row_key": row_key,
            "source": source,
            "slot": slot,
            "target": target,
            "method": {
                "id": method_id,
                "key": spec.key,
                "family": spec.family,
                "runtime_supported": spec.runtime_supported,
            },
            "condition": {
                "parameter": parameter,
                "extra": extra,
                "normalized_ja": _condition_ja(spec, parameter, extra),
            },
            "layout": {
                "table_relative_offset": table_offset,
                "rom_file_offset": runtime_address - ROM_BASE + table_offset,
                "runtime_address": runtime_address + table_offset,
            },
            "baseline_policy": "ADOPT_CURRENT",
            "source_partition": "VEGA_PREFIX" if source_id < 412 else "DPE_APPEND",
        }

        if spec.family == "BATTLE_TRANSFORM" and source["national_dex"] != target["national_dex"]:
            _fail(f"戦闘内form変身が別National Dexを指しています: {row_key}")
        if method_id == 254 and parameter_value == 0 and not source["form_key"]:
            _fail(f"Mega reverse rowのsourceが変身formではありません: {row_key}")

        if method_id == 254 and parameter_value:
            if extra_value == 0:
                item_row = manifests["items"].by_id[parameter_value]
                if item_row.get("item_type_key") != "ITEM_TYPE_MEGA_STONE":
                    findings.append({
                        "finding_key": "P02-EVO-LEGACY-MEGA-PARAM",
                        "severity": "HIGH",
                        "classification": "CONFIRMED_RUNTIME_NO_OP_OR_WRONG_TRIGGER",
                        "row_key": row_key,
                        "summary_ja": "standard Mega行がMega Stoneでないcanonical Itemを参照しています。",
                        "current_parameter": parameter,
                        "layout": {
                            "entry_runtime_address": runtime_address + table_offset,
                            "entry_runtime_address_hex": f"0x{runtime_address + table_offset:08X}",
                            "entry_rom_file_offset": runtime_address - ROM_BASE + table_offset,
                            "entry_rom_file_offset_hex": f"0x{runtime_address - ROM_BASE + table_offset:08X}",
                        },
                        "disposition": "REVIEW_ONLY_NO_AUTOMATIC_REWRITE",
                    })
            elif extra_value == 1:
                item_row = manifests["items"].by_id[parameter_value]
                if item_row.get("item_type_key") != "ITEM_TYPE_PRIMAL_ORB":
                    _fail(f"Primal rowがPrimal OrbでないItemを参照しています: {row_key}")
            elif extra_value == 3:
                item_row = manifests["items"].by_id[parameter_value]
                if item_row.get("item_type_key") != "ITEM_TYPE_Z_CRYSTAL":
                    _fail(f"Ultra Burst rowがZ CrystalでないItemを参照しています: {row_key}")

        output.append(row)
    return output, findings


def _model_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "from_form_key": row["source"]["form_key"],
        "from_id": row["source"]["canonical_id"],
        "from_national_dex": row["source"]["national_dex"],
        "method": row["method"]["id"],
        "param": row["condition"]["parameter"]["value"],
        "target_form_key": row["target"]["form_key"],
        "target_id": row["target"]["canonical_id"],
        "target_national_dex": row["target"]["national_dex"],
        "unknown": row["condition"]["extra"]["value"],
    }


def _resolve_zip_edge(
    row: Mapping[str, str],
    species: ManifestIndex,
    label: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_id = _integer(row.get("\u5143ID", ""), f"{label}:\u5143ID", maximum=SPECIES_COUNT - 1)
    target_id = _integer(row.get("\u9032\u5316\u5148ID", ""), f"{label}:\u9032\u5316\u5148ID", maximum=SPECIES_COUNT - 1)
    source = _species_ref(species, source_id, f"{label}:source")
    target = _species_ref(species, target_id, f"{label}:target")
    if row.get("\u5143\u540d") != source["display_name"]:
        _fail(f"{label} source ID/name意味不一致: {source_id} {row.get('\u5143\u540d')!r}")
    if row.get("\u9032\u5316\u5148\u540d") != target["display_name"]:
        _fail(f"{label} target ID/name意味不一致: {target_id} {row.get('\u9032\u5316\u5148\u540d')!r}")
    return source, target


def _tuple_from_columns(row: Mapping[str, str], label: str) -> tuple[int, int, int]:
    return (
        _integer(row.get("method_id", ""), f"{label}:method_id"),
        _integer(row.get("parameter", ""), f"{label}:parameter"),
        _integer(row.get("extra", ""), f"{label}:extra"),
    )


def _raw_tuples(value: str, label: str) -> list[tuple[int, int, int]]:
    output: list[tuple[int, int, int]] = []
    for index, part in enumerate(value.split("||")):
        match = re.fullmatch(r"\s*([0-9]+)\s*/\s*([0-9]+)\s*/\s*([0-9]+)\s*", part)
        if match is None:
            _fail(f"{label} raw tupleが不正です: {part!r}")
        item = tuple(int(number) for number in match.groups())
        if item in output:
            _fail(f"{label} raw tupleが重複しています: {item}")
        output.append(item)
    return output


def _relation(reference: set[tuple[int, int, int]], current: set[tuple[int, int, int]]) -> str:
    if reference == current:
        return "EXACT_CURRENT_SET"
    if current < reference:
        return "REFERENCE_SUPERSET_OF_CURRENT"
    if reference < current:
        return "REFERENCE_SUBSET_OF_CURRENT"
    if reference & current:
        return "PARTIAL_OVERLAP"
    return "DISJOINT_OR_MISSING"


def _audit_zip_rows(
    archive: CheckedArchive,
    species: ManifestIndex,
    current_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], set[str], dict[str, Any]]:
    by_slot = {(r["source"]["canonical_id"], r["slot"]): r for r in current_rows}
    by_pair: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in current_rows:
        by_pair[(row["source"]["canonical_id"], row["target"]["canonical_id"])].append(row)

    member_meta: dict[str, Any] = {}
    source_rows: dict[str, list[dict[str, str]]] = {}
    for role, suffix in ZIP_MEMBERS.items():
        name, raw = archive.read(suffix)
        source_rows[role] = _csv(raw, suffix)
        member_meta[role] = {
            "path_below_archive_root": "/".join(Path(name).parts[1:]),
            "size": len(raw),
            "sha256": _sha256(raw),
            "rows": len(source_rows[role]),
        }
    expected_counts = {
        "official_existing": 128,
        "vega_unique": 26,
        "description_mismatch": 15,
        "public_vega_diff": 10,
        "missing_branches": 3,
    }
    actual_counts = {key: len(value) for key, value in source_rows.items()}
    if actual_counts != expected_counts:
        _fail(f"進化監査ZIP row count不一致: {actual_counts}")

    official: list[dict[str, Any]] = []
    for index, source_row in enumerate(source_rows["official_existing"], 1):
        label = f"official_existing:{index}"
        source, target = _resolve_zip_edge(source_row, species, label)
        if source_row.get("\u9032\u5316\u5148\u5206\u985e") != target["classification"]:
            _fail(f"{label} target classificationがmanifestと一致しません")
        slot = _integer(source_row.get("slot", ""), f"{label}:slot", maximum=15)
        triple = _tuple_from_columns(source_row, label)
        current = by_slot.get((source["canonical_id"], slot))
        exact = current is not None and (
            current["method"]["id"],
            current["condition"]["parameter"]["value"],
            current["condition"]["extra"]["value"],
        ) == triple and current["target"]["canonical_id"] == target["canonical_id"]
        official.append({
            "reference_key": f"ZIP05-{index:03d}",
            "source_species_key": source["species_key"],
            "source_form_key": source["form_key"],
            "target_species_key": target["species_key"],
            "target_form_key": target["form_key"],
            "slot": slot,
            "tuple": {"method_id": triple[0], "parameter": triple[1], "extra": triple[2]},
            "raw_interpretation_ja": source_row.get("\u751f\u30c7\u30fc\u30bf\u306e\u89e3\u91c8", ""),
            "wiki_description_ja": source_row.get("Wiki\u8aac\u660e\u6587", ""),
            "comparison": "EXACT_CURRENT_SLOT" if exact else "REVIEW_ONLY_NOT_CURRENT_SLOT",
            "current_row_key": current["row_key"] if current else None,
            "policy": "OBSERVATION_ONLY_NO_AUTOMATIC_APPLY",
        })

    preserve_keys: set[str] = set()
    preserve: list[dict[str, Any]] = []
    for index, source_row in enumerate(source_rows["vega_unique"], 1):
        label = f"vega_unique:{index}"
        source, target = _resolve_zip_edge(source_row, species, label)
        if source_row.get("\u9032\u5316\u5148\u5206\u985e") != "VEGA_ORIGINAL" or target["classification"] != "VEGA_ORIGINAL":
            _fail(f"{label}がVEGA_ORIGINAL targetではありません")
        slot = _integer(source_row.get("slot", ""), f"{label}:slot", maximum=15)
        triple = _tuple_from_columns(source_row, label)
        current = by_slot.get((source["canonical_id"], slot))
        if current is None or current["target"]["canonical_id"] != target["canonical_id"] or (
            current["method"]["id"],
            current["condition"]["parameter"]["value"],
            current["condition"]["extra"]["value"],
        ) != triple:
            _fail(f"維持必須のベガ独自進化が現行tableと一致しません: {label}")
        if current["row_key"] in preserve_keys:
            _fail(f"ベガ独自進化rowが重複しています: {current['row_key']}")
        preserve_keys.add(current["row_key"])
        preserve.append({
            "preservation_key": f"VEGA-UNIQUE-{index:02d}",
            "row_key": current["row_key"],
            "source_species_key": source["species_key"],
            "target_species_key": target["species_key"],
            "method_key": current["method"]["key"],
            "condition_ja": current["condition"]["normalized_ja"],
            "policy": "ADOPTED_PRESERVE_EXACT",
        })

    def mismatch_section(role: str) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for index, source_row in enumerate(source_rows[role], 1):
            label = f"{role}:{index}"
            source, target = _resolve_zip_edge(source_row, species, label)
            reference = set(_raw_tuples(source_row.get("raw_method_parameter_extra", ""), label))
            actual_rows = by_pair.get((source["canonical_id"], target["canonical_id"]), [])
            current = {
                (
                    row["method"]["id"],
                    row["condition"]["parameter"]["value"],
                    row["condition"]["extra"]["value"],
                )
                for row in actual_rows
            }
            output.append({
                "review_key": f"{'ZIP07' if role == 'description_mismatch' else 'ZIP08'}-{index:02d}",
                "source_species_key": source["species_key"],
                "target_species_key": target["species_key"],
                "reference_tuples": [
                    {"method_id": a, "parameter": b, "extra": c}
                    for a, b, c in sorted(reference)
                ],
                "current_row_keys": [row["row_key"] for row in actual_rows],
                "current_tuples": [
                    {"method_id": a, "parameter": b, "extra": c}
                    for a, b, c in sorted(current)
                ],
                "comparison": _relation(reference, current),
                "reference_description_ja": source_row.get("Wiki\u8aac\u660e\u6587", source_row.get("ZIP\u8a2d\u5b9a", "")),
                "recommendation_ja": source_row.get("\u5bfe\u5fdc\u65b9\u91dd", source_row.get("\u63a8\u5968", "")),
                "policy": "REVIEW_ONLY_NOT_ADOPTED",
            })
        return output

    sections = {
        "official_existing_observations": official,
        "adopted_vega_unique_preservation": preserve,
        "description_mismatch_candidates": mismatch_section("description_mismatch"),
        "public_vega_difference_candidates": mismatch_section("public_vega_diff"),
    }
    return sections, preserve_keys, {"members": member_meta, "rows": source_rows["missing_branches"]}


def _find_line(raw: bytes, needle: str, label: str) -> int:
    text = raw.decode("utf-8")
    hits = [index for index, line in enumerate(text.splitlines(), 1) if needle in line]
    if len(hits) != 1:
        _fail(f"{label} producer markerが一意ではありません: {needle!r} hits={hits}")
    return hits[0]


def _find_line_in_c_block(raw: bytes, block_marker: str, needle: str, label: str) -> int:
    lines = raw.decode("utf-8").splitlines()
    starts = [index for index, line in enumerate(lines) if block_marker in line]
    if len(starts) != 1:
        _fail(f"{label} C block markerが一意ではありません: {block_marker!r}")
    start = starts[0]
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip() == "};"), None)
    if end is None:
        _fail(f"{label} C blockが終端しません")
    hits = [index + 1 for index in range(start, end + 1) if needle in lines[index]]
    if len(hits) != 1:
        _fail(f"{label} C block内markerが一意ではありません: {needle!r} hits={hits}")
    return hits[0]


def _parse_level_moves(pointer_raw: bytes, data_raw: bytes, base: int, species_id: int) -> list[dict[str, int]]:
    if len(pointer_raw) != SPECIES_COUNT * 4:
        _fail("level-up pointer table sizeがSpecies ABIと一致しません")
    pointer = struct.unpack_from("<I", pointer_raw, species_id * 4)[0]
    offset = pointer - base
    if offset < 0 or offset >= len(data_raw):
        _fail(f"level-up pointerがdata外です: species={species_id} pointer={pointer:#x}")
    rows: list[dict[str, int]] = []
    for slot in range(256):
        if offset + slot * 3 + 3 > len(data_raw):
            _fail(f"level-up dataが終端前に範囲外です: species={species_id}")
        move_id, level = struct.unpack_from("<HB", data_raw, offset + slot * 3)
        if move_id == 0 and level == 0xFF:
            return rows
        rows.append({"level": level, "move_id": move_id})
    _fail(f"level-up dataが256行以内に終端しません: species={species_id}")


def _missing_branch_contract(
    raw_rows: Sequence[Mapping[str, str]],
    manifests: Mapping[str, ManifestIndex],
    current_rows: Sequence[Mapping[str, Any]],
    pointer_raw: bytes,
    level_raw: bytes,
    level_base: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current_pairs = {
        (row["source"]["canonical_id"], row["target"]["canonical_id"])
        for row in current_rows
    }
    proposals = {
        54: {
            "expected_existing": 55,
            "targets": [(1558, 26, "MOVE_KEY_TWINBEAM")],
            "decision": "EXCLUSIVE_BRANCH_PRIORITY_REQUIRED",
        },
        255: {
            "expected_existing": 283,
            "targets": [(1433, 7, "ITEM_KEY_BLACK_AUGURITE")],
            "decision": "PLA_BRANCH_ADOPTION_REQUIRED",
        },
        341: {
            "expected_existing": 342,
            "targets": [
                (1559, 42, "MOVE_KEY_HYPERDRILL"),
                (1560, 43, "MOVE_KEY_HYPERDRILL"),
            ],
            "decision": "FORM_AND_SLOT_PRIORITY_REQUIRED",
        },
    }
    if {int(row.get("\u5143ID", "-1")) for row in raw_rows} != set(proposals):
        _fail("不足分岐3系統のsource集合が契約外です")
    output: list[dict[str, Any]] = []
    p03: list[dict[str, Any]] = []
    for source_row in raw_rows:
        source_id = _integer(source_row.get("\u5143ID", ""), "missing branch source", maximum=SPECIES_COUNT - 1)
        spec = proposals[source_id]
        source = _species_ref(manifests["species"], source_id, "missing branch source")
        if source_row.get("\u5143\u540d") != source["display_name"]:
            _fail(f"不足分岐source ID/name不一致: {source_id}")
        existing_ids = [int(value) for value in re.findall(r"\b([0-9]{1,4})\b", source_row.get("\u65e2\u5b58\u30d9\u30ac\u5148", ""))]
        missing_ids = [int(value) for value in re.findall(r"\b([0-9]{1,4})\b", source_row.get("\u4e0d\u8db3\u3059\u308b\u539f\u4f5c\u5148", ""))]
        if not existing_ids or existing_ids[0] != spec["expected_existing"]:
            _fail(f"不足分岐の既存Vega targetが契約外です: {source_id}")
        if missing_ids != [target[0] for target in spec["targets"]]:
            _fail(f"不足分岐target集合が契約外です: {source_id} {missing_ids}")
        existing_edge_present = (source_id, spec["expected_existing"]) in current_pairs
        branches: list[dict[str, Any]] = []
        for target_id, method_id, requirement_key in spec["targets"]:
            if (source_id, target_id) in current_pairs:
                _fail(f"review-only不足分岐が既に現行tableへ混入しています: {source_id}->{target_id}")
            target = _species_ref(manifests["species"], target_id, "missing branch target")
            namespace = "moves" if requirement_key.startswith("MOVE_KEY_") else "items"
            requirement_row = manifests[namespace].by_key.get(requirement_key)
            if requirement_row is None:
                _fail(f"不足分岐requirement keyがmanifestにありません: {requirement_key}")
            requirement = _entity_ref(
                manifests[namespace], int(requirement_row["id"]), "missing branch requirement",
            )
            branch = {
                "target": target,
                "method": {"id": method_id, "key": METHODS[method_id].key},
                "requirement": requirement,
                "current_edge_present": False,
                "policy": "REVIEW_ONLY_NOT_ADOPTED",
            }
            branches.append(branch)
            if namespace == "moves":
                current_level = _parse_level_moves(pointer_raw, level_raw, level_base, source_id)
                move_id = int(requirement_row["id"])
                learned = [row["level"] for row in current_level if row["move_id"] == move_id]
                dependency = {
                    "dependency_key": (
                        f"P03-{source['species_key']}-{target['species_key']}-{requirement_key}"
                    ),
                    "source_species_key": source["species_key"],
                    "target_species_key": target["species_key"],
                    "required_move_key": requirement_key,
                    "required_move_id": move_id,
                    "move_manifest_status": requirement_row.get("status", ""),
                    "current_level_up_levels": learned,
                    "satisfied_by_current_level_up_table": bool(learned),
                    "gate": "P03_LEARNSET_PROOF_REQUIRED_BEFORE_BRANCH_ADOPTION",
                }
                p03.append(dependency)
        output.append({
            "review_key": f"ZIP09-{source_id}",
            "source": source,
            "existing_vega_target": _species_ref(
                manifests["species"], spec["expected_existing"], "existing Vega target",
            ),
            "existing_vega_edge_present": existing_edge_present,
            "proposed_official_branches": branches,
            "required_decision": spec["decision"],
            "source_note_ja": source_row.get("\u8ffd\u52a0\u6848", ""),
            "policy": "REVIEW_ONLY_PRESERVE_VEGA_BRANCH",
        })
    output.sort(key=lambda row: row["source"]["canonical_id"])
    p03.sort(key=lambda row: row["dependency_key"])
    if len(output) != 3 or len(p03) != 3:
        _fail(f"P03 dependency件数が契約外です: branches={len(output)} deps={len(p03)}")
    return output, p03


def _validate_identity_contract(
    raw: bytes,
    manifests: Mapping[str, ManifestIndex],
) -> dict[str, Any]:
    contract = _json(raw, IDENTITY_CONTRACT.as_posix())
    if contract.get("schema_version") != 1 or contract.get("status") != "PASS":
        _fail("P01 identity contractがPASS schema 1ではありません")
    policy = contract.get("policy", {})
    if policy.get("identity_join") != "CANONICAL_KEY_THEN_ASSERT_NUMERIC_ID":
        _fail("P01 identity join policyが変更されています")
    if policy.get("restoration_candidates") != "REVIEW_ONLY_NOT_AUTOMATICALLY_APPLIED":
        _fail("P01 restoration review-only policyが変更されています")
    for name, manifest in manifests.items():
        recorded = contract.get("manifests", {}).get(name, {})
        if recorded.get("sha256") != manifest.sha256 or recorded.get("rows") != len(manifest.rows):
            _fail(f"P01 identity contractと{name} manifestが一致しません")
    target_records = {
        row["species_key"]: row
        for row in contract.get("target_normalization", {}).get("records", [])
    }
    caterpie = target_records.get("SPECIES_KEY_CATERPIE", {})
    egg = target_records.get("SPECIES_KEY_EGG", {})
    if caterpie.get("canonical_id") != 649 or not caterpie.get("normalized", {}).get("apply"):
        _fail("P01 Caterpie=649通常対象契約がありません")
    if egg.get("canonical_id") != 412 or egg.get("normalized", {}).get("apply"):
        _fail("P01 Egg=412内部除外契約がありません")
    return contract


def _item_acquisition_contract(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in rows:
        for field in ("parameter", "extra"):
            reference = row["condition"][field].get("reference")
            if not reference or not str(reference.get("key", "")).startswith("ITEM_KEY_"):
                continue
            key = str(reference["key"])
            current = by_key.setdefault(
                key,
                {
                    **reference,
                    "used_by_row_keys": [],
                },
            )
            current["used_by_row_keys"].append(row["row_key"])
    items = []
    for key in sorted(by_key):
        item = by_key[key]
        item["used_by_row_keys"] = sorted(set(item["used_by_row_keys"]))
        supply = str(item.get("supply_key", ""))
        item["static_supply_state"] = (
            "PENDING_EXTERNAL_SUPPLY_PROOF" if "PENDING" in supply
            else "DECLARED_SUPPLY_KEY"
        )
        items.append(item)
    return {
        "item_count": len(items),
        "items": items,
        "pending_item_keys": [
            row["key"] for row in items
            if row["static_supply_state"] == "PENDING_EXTERNAL_SUPPLY_PROOF"
        ],
        "policy": "MANIFEST_DECLARATION_ONLY_RUNTIME_ACQUISITION_TEST_DEFERRED",
    }


def build_evolution_contract(root: Path, restoration_zip: Path) -> dict[str, Any]:
    manifests = load_manifests(root)
    inputs: dict[str, Any] = {}

    _, identity_raw = _file(root, IDENTITY_CONTRACT)
    _validate_identity_contract(identity_raw, manifests)
    inputs["identity_contract"] = _identity(IDENTITY_CONTRACT, identity_raw)

    _, binary_raw = _file(root, EVOLUTION_BINARY)
    _, model_raw = _file(root, EVOLUTION_MODEL)
    model = _json(model_raw, EVOLUTION_MODEL.as_posix())
    inputs["evolution_binary"] = _identity(EVOLUTION_BINARY, binary_raw)
    inputs["evolution_model"] = _identity(EVOLUTION_MODEL, model_raw)

    source_blobs: dict[Path, bytes] = {}
    for relative in (*RUNTIME_SOURCES, GENERATOR_SOURCE, DPE_EVOLUTION_SOURCE, DPE_LEARNSET_SOURCE):
        _, raw = _file(root, relative)
        source_blobs[relative] = raw
    inputs["producer_and_runtime_sources"] = [
        _identity(relative, source_blobs[relative])
        for relative in (*RUNTIME_SOURCES, GENERATOR_SOURCE, DPE_EVOLUTION_SOURCE, DPE_LEARNSET_SOURCE)
    ]
    method_abi = parse_runtime_method_enum(source_blobs[RUNTIME_SOURCES[0]])

    config_text = source_blobs[RUNTIME_SOURCES[1]].decode("utf-8")
    evolution_text = source_blobs[RUNTIME_SOURCES[2]].decode("utf-8")
    mega_text = source_blobs[RUNTIME_SOURCES[3]].decode("utf-8")
    if "#define TIME_ENABLED" not in config_text:
        _fail("TIME_ENABLEDが無効です。昼夜進化の現行契約を固定できません")
    if "#define EVO_HOLD_ITEM_REMOVAL" not in config_text:
        _fail("EVO_HOLD_ITEM_REMOVALが無効です。所持Item消費契約を固定できません")
    if evolution_text.count("friendship >= 220") < 3:
        _fail("friendship threshold 220のruntime実装を確認できません")
    if "evolutions[i].unknown == MEGA_VARIANT_WISH" not in mega_text or "evolutions[i].param == mon->moves[j]" not in mega_text:
        _fail("Mega WishのMove parameter runtimeを確認できません")

    _, metadata_raw = _file(root, STAGE09_METADATA)
    metadata = _json(metadata_raw, STAGE09_METADATA.as_posix())
    inputs["stage09_metadata"] = _identity(STAGE09_METADATA, metadata_raw)
    repoint = metadata.get("repoints", {}).get("evolution_runtime", {})
    runtime_address = int(repoint.get("new", -1))
    if runtime_address < ROM_BASE or repoint.get("count") != len(repoint.get("sites", [])):
        _fail("Stage09 evolution runtime repoint metadataが不正です")
    allocation = next(
        (row for row in metadata.get("allocation", {}).get("entries", []) if row.get("name") == "evolutions"),
        None,
    )
    if allocation is None or int(allocation.get("address", -1)) != runtime_address:
        _fail("Stage09 evolution allocation metadataが不一致です")
    if allocation.get("sha256") != _sha256(binary_raw) or int(allocation.get("size", -1)) != len(binary_raw):
        _fail("Stage09 evolution allocationと生成binaryが不一致です")

    _, rom_raw = _file(root, STAGE09_ROM)
    rom_offset = runtime_address - ROM_BASE
    if rom_raw[rom_offset:rom_offset + len(binary_raw)] != binary_raw:
        _fail("Stage09 ROM内のevolution tableが生成binaryと一致しません")
    if metadata.get("output", {}).get("sha256") != _sha256(rom_raw):
        _fail("Stage09 ROM hashがmetadataと一致しません")
    inputs["stage09_rom_read_only_verification"] = _identity(STAGE09_ROM, rom_raw)

    binary_rows = parse_evolution_binary(binary_raw)
    padding_residues = _padding_residues(binary_raw)
    normalized, findings = normalize_evolution_rows(
        binary_rows, manifests, runtime_address=runtime_address,
    )
    if model.get("schema_version") != 1 or model.get("status") != "PASS":
        _fail("現行evolution JSON modelがPASS schema 1ではありません")
    if model.get("species_count") != SPECIES_COUNT or model.get("stride") != EVOLUTION_STRIDE:
        _fail("現行evolution JSON layoutが契約外です")
    if model.get("nonzero_rows") != len(normalized) or model.get("semantic_duplicates_removed") != 0:
        _fail("現行evolution JSON集計がbinaryと一致しません")
    projections = [_model_projection(row) for row in normalized]
    if model.get("rows") != projections:
        _fail("現行evolution JSON rowsがbinary/canonical manifest照合結果と一致しません")

    with CheckedArchive(restoration_zip, "restoration_audit") as archive:
        zip_identity = archive.identity()
        audit_sections, preserve_keys, zip_private = _audit_zip_rows(
            archive, manifests["species"], normalized,
        )
    inputs["restoration_audit"] = zip_identity
    inputs["restoration_audit"]["evolution_members"] = zip_private["members"]

    for row in normalized:
        if row["row_key"] in preserve_keys:
            row["baseline_policy"] = "ADOPT_AND_PRESERVE_VEGA_UNIQUE"
    if len(preserve_keys) != 26:
        _fail(f"維持対象Vega独自進化が26件ではありません: {len(preserve_keys)}")

    _, pointer_raw = _file(root, LEVEL_POINTERS)
    _, level_raw = _file(root, LEVEL_DATA)
    inputs["level_up_pointers"] = _identity(LEVEL_POINTERS, pointer_raw)
    inputs["level_up_data"] = _identity(LEVEL_DATA, level_raw)
    level_allocation = next(
        (row for row in metadata.get("allocation", {}).get("entries", []) if row.get("name") == "level_up_data"),
        None,
    )
    if level_allocation is None or level_allocation.get("sha256") != _sha256(level_raw):
        _fail("level-up data allocationと生成物が一致しません")
    missing, p03 = _missing_branch_contract(
        zip_private["rows"], manifests, normalized, pointer_raw, level_raw,
        int(level_allocation["address"]),
    )
    evolution_markers = {
        "SPECIES_KEY_FARIGIRAF": "{EVO_MOVE, MOVE_TWINBEAM, SPECIES_FARIGIRAF, 0}",
        "SPECIES_KEY_KLEAVOR": "{EVO_ITEM, ITEM_BLACK_AUGURITE, SPECIES_KLEAVOR, 0}",
        "SPECIES_KEY_DUDUNSPARCE": "{EVO_DUDUNSPARCE_TWO, MOVE_HYPERDRILL, SPECIES_DUDUNSPARCE, 0}",
        "SPECIES_KEY_DUDUNSPARCE_THREE": "{EVO_DUDUNSPARCE_THREE, MOVE_HYPERDRILL, SPECIES_DUDUNSPARCE_THREE, 0}",
    }
    for family in missing:
        for branch in family["proposed_official_branches"]:
            target_key = branch["target"]["species_key"]
            marker = evolution_markers[target_key]
            branch["upstream_dpe_source"] = {
                "path": DPE_EVOLUTION_SOURCE.as_posix(),
                "line": _find_line(
                    source_blobs[DPE_EVOLUTION_SOURCE], marker,
                    f"{target_key} DPE evolution",
                ),
                "marker": marker,
            }
    learnset_evidence = {
        "MOVE_KEY_TWINBEAM": ("static const struct LevelUpMove sGirafarigLevelUpLearnset[]", "LEVEL_UP_MOVE(32, MOVE_TWINBEAM)"),
        "MOVE_KEY_HYPERDRILL": ("static const struct LevelUpMove sDunsparceLevelUpLearnset[]", "LEVEL_UP_MOVE(32, MOVE_HYPERDRILL)"),
    }
    for dependency in p03:
        block, marker = learnset_evidence[dependency["required_move_key"]]
        dependency["upstream_dpe_level_up"] = {
            "path": DPE_LEARNSET_SOURCE.as_posix(),
            "line": _find_line_in_c_block(
                source_blobs[DPE_LEARNSET_SOURCE], block, marker,
                f"{dependency['required_move_key']} DPE learnset",
            ),
            "level": 32,
        }
    audit_sections["missing_official_branch_candidates"] = missing

    # DPEのWish rowはMove ID 559。現行producerはEVO_MEGAをItemとして変換するため、
    # canonical Move 630ではなくcanonical Item 773と同じ数値へ化ける。
    dpe_evo_text = source_blobs[DPE_EVOLUTION_SOURCE].decode("utf-8")
    if "{EVO_MEGA, MOVE_DRAGONASCENT, SPECIES_RAYQUAZA_MEGA, MEGA_VARIANT_WISH}" not in dpe_evo_text:
        _fail("DPE Rayquaza Wish evolution source rowが変更されています")
    generator_text = source_blobs[GENERATOR_SOURCE].decode("utf-8")
    rayquaza = next(
        (row for row in normalized if row["source"]["species_key"] == "SPECIES_KEY_RAYQUAZA" and row["method"]["id"] == 254 and row["condition"]["extra"]["value"] == 2),
        None,
    )
    if rayquaza is None:
        _fail("Rayquaza Wish Mega rowが現行tableにありません")
    dragon_ascent = manifests["moves"].by_key["MOVE_KEY_DRAGONASCENT"]
    mawilite = manifests["items"].by_key["ITEM_KEY_MAWILITE"]
    ray_key = rayquaza["condition"]["parameter"]["reference"]["key"]
    if ray_key not in {"MOVE_KEY_OVERDRIVE", "MOVE_KEY_DRAGONASCENT"}:
        _fail(f"Rayquaza Wish Megaが予期しないMoveを参照しています: {ray_key}")
    legacy_mapping = remap_evolution_parameters(
        0xFE,
        559,
        MEGA_VARIANT_WISH,
        {},
        {559: int(dragon_ascent["id"])},
        {559: int(mawilite["id"])},
        policy=EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
    )
    modernization_mapping = remap_evolution_parameters(
        0xFE,
        559,
        MEGA_VARIANT_WISH,
        {},
        {559: int(dragon_ascent["id"])},
        {559: int(mawilite["id"])},
        policy=EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
    )
    expected_legacy = (int(mawilite["id"]), MEGA_VARIANT_WISH)
    expected_modernization = (int(dragon_ascent["id"]), MEGA_VARIANT_WISH)
    if legacy_mapping != expected_legacy:
        _fail("historical evolution parameter policyがT09のbyte互換を保持していません")
    if modernization_mapping != expected_modernization:
        _fail("modernization evolution parameter policyがWish MegaをMoveとして解決しません")
    root_fix = {
        "status": "PASS",
        "historical_default_policy": EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
        "historical_default_output_preserved": True,
        "modernization_policy": EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
        "wish_source_move_id": 559,
        "legacy_item_alias_key": "ITEM_KEY_MAWILITE",
        "legacy_resolved_parameter_id": legacy_mapping[0],
        "modernization_resolved_parameter_id": modernization_mapping[0],
        "required_modernization_parameter_key": "MOVE_KEY_DRAGONASCENT",
        "required_modernization_parameter_id": int(dragon_ascent["id"]),
    }
    if ray_key != "MOVE_KEY_DRAGONASCENT":
        findings.append({
            "finding_key": "P02-EVO-RAYQUAZA-MOVE-NAMESPACE",
            "severity": "CRITICAL",
            "classification": "CONFIRMED_HISTORICAL_ARTIFACT_NAMESPACE_ERROR",
            "row_key": rayquaza["row_key"],
            "summary_ja": "現行ROMのMEGA_VARIANT_WISH parameterはガリョウテンセイでなくオーバードライブIDです。producerのmodernization policyは修正済みですが、履歴成果物を上書きせず新Stageで再生成・修復する必要があります。",
            "current": {
                "parameter_key": ray_key,
                "parameter_id": rayquaza["condition"]["parameter"]["value"],
                "runtime_address": rayquaza["layout"]["runtime_address"] + 2,
                "runtime_address_hex": f"0x{rayquaza['layout']['runtime_address'] + 2:08X}",
                "rom_file_offset": rayquaza["layout"]["rom_file_offset"] + 2,
                "rom_file_offset_hex": f"0x{rayquaza['layout']['rom_file_offset'] + 2:08X}",
            },
            "required": {
                "parameter_key": "MOVE_KEY_DRAGONASCENT",
                "parameter_id": int(dragon_ascent["id"]),
                "producer_handles_wish_as_move": True,
            },
            "producer_cause": {
                "path": GENERATOR_SOURCE.as_posix(),
                "function": "merge_evolutions",
                "line": _find_line(source_blobs[GENERATOR_SOURCE], "def merge_evolutions(", "merge_evolutions"),
                "historical_cause": "T09 legacy policy maps EVO_MEGA(0xFE) through Item aliases; MEGA_VARIANT_WISH requires Move aliases",
                "root_fix_applied": True,
                "parameter_namespace_policy": root_fix,
            },
            "disposition": "REQUIRED_NEW_STAGE_ROM_REBUILD_OR_EXACT_PATCH",
        })
    findings.sort(key=lambda row: row["finding_key"])

    official_current = audit_sections["official_existing_observations"]
    method_counts = Counter(row["method"]["key"] for row in normalized)
    family_counts = Counter(row["method"]["family"] for row in normalized)
    generator_line = _find_line(source_blobs[GENERATOR_SOURCE], "def merge_evolutions(", "merge_evolutions")
    learnset_line = _find_line(source_blobs[GENERATOR_SOURCE], "def merge_learnsets(", "merge_learnsets")
    required_fixes = [row for row in findings if row["disposition"].startswith("REQUIRED_")]
    acquisition = _item_acquisition_contract(normalized)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": "MODERNIZATION_P02_STATIC_EVOLUTION_CONTRACT",
        "status": "PASS",
        "static_gate": "PASS",
        "release_gate": (
            "BLOCKED_BY_REQUIRED_FIXES_AND_DEFERRED_RUNTIME_ACCEPTANCE"
            if required_fixes else "BLOCKED_BY_DEFERRED_RUNTIME_ACCEPTANCE"
        ),
        "policy": {
            "identity_join": "STABLE_SPECIES_KEY_WITH_CANONICAL_ID_ASSERTION",
            "current_table": "ADOPTED_BASELINE_UNTIL_EXPLICIT_REVIEW_DECISION",
            "vega_unique_evolutions": "ADOPTED_AND_PRESERVED_EXACTLY",
            "zip_change_candidates": "REVIEW_ONLY_NOT_AUTOMATICALLY_APPLIED",
            "normal_vs_battle_transform": "SEPARATE_RUNTIME_FAMILIES",
            "self_target_or_item_like_value": "INTERPRET_WITH_METHOD_AND_RUNTIME_BEFORE_CLASSIFICATION",
            "communication_and_rtc": "DO_NOT_ADD_MANDATORY_DEPENDENCY_WITHOUT_REVIEW",
            "p03_dependency": "MOVE_BASED_BRANCH_REQUIRES_LIVE_LEARNSET_PROOF",
        },
        "inputs": inputs,
        "runtime_contract": {
            "method_abi": method_abi,
            "friendship_threshold": 220,
            "time_enabled": True,
            "hold_item_removal_enabled": True,
            "normal_selection": "ALL_16_SLOTS_SCANNED_LAST_MATCH_WINS",
            "battle_transform_selection": "CONTIGUOUS_ROWS_STOP_AT_FIRST_EVO_NONE",
            "unsupported_methods": ["EVO_DAMAGE_LOCATION"],
            "table": {
                "species_count": SPECIES_COUNT,
                "stride": EVOLUTION_STRIDE,
                "slots_per_species": EVOLUTION_SLOTS,
                "entry_size": EVOLUTION_ENTRY_SIZE,
                "entry_layout": ["u16 method", "u16 parameter", "u16 target_species", "u16 extra"],
                "entry_offset_formula": "rom_file_offset + species_id * 128 + slot * 8",
                "runtime_address": runtime_address,
                "runtime_address_hex": f"0x{runtime_address:08X}",
                "rom_file_offset": rom_offset,
                "rom_file_offset_hex": f"0x{rom_offset:08X}",
                "repoint_from": int(repoint["old"]),
                "repoint_sites": repoint["sites"],
                "read_only_rom_match": True,
                "evo_none_parameter_residues": {
                    "classification": "IGNORED_PADDING_NOT_EVOLUTION_ROWS",
                    "count": len(padding_residues),
                    "rows": padding_residues,
                },
            },
            "producer": {
                "path": GENERATOR_SOURCE.as_posix(),
                "function": "merge_evolutions",
                "line": generator_line,
                "vega_prefix_policy": "SPECIES_0_TO_411_COPIED_BYTE_FOR_BYTE_FROM_T06",
                "dpe_append_policy": "SPECIES_412_TO_1620_ALIAS_TRANSLATED",
                "rom_write": "allocator.put('evolutions', evolutions) then repoint old T06 root literals",
                "parameter_namespace_policy": root_fix,
            },
        },
        "current_table": {
            "summary": {
                "rows": len(normalized),
                "sources_with_rows": len({row["source"]["species_key"] for row in normalized}),
                "families": dict(sorted(family_counts.items())),
                "methods": dict(sorted(method_counts.items())),
                "vega_prefix_rows": sum(row["source_partition"] == "VEGA_PREFIX" for row in normalized),
                "dpe_append_rows": sum(row["source_partition"] == "DPE_APPEND" for row in normalized),
                "adopted_vega_unique_rows": len(preserve_keys),
            },
            "rows": normalized,
        },
        "adopted_specifications": {
            "vega_unique_preservation": audit_sections.pop("adopted_vega_unique_preservation"),
            "current_rows": "current_table.rows (850 stable row keys)",
        },
        "review_only": {
            **audit_sections,
            "summary": {
                "zip05_rows": len(official_current),
                "zip05_exact_current": sum(row["comparison"] == "EXACT_CURRENT_SLOT" for row in official_current),
                "zip05_not_current": sum(row["comparison"] != "EXACT_CURRENT_SLOT" for row in official_current),
                "description_mismatch_candidates": 15,
                "public_vega_difference_candidates": 10,
                "missing_official_branch_families": 3,
            },
        },
        "p03_dependencies": {
            "producer": {
                "path": GENERATOR_SOURCE.as_posix(),
                "function": "merge_learnsets",
                "line": learnset_line,
                "cause": "Species 0..411 use preserved Vega learnsets; DPE modern trigger moves are not inherited automatically",
            },
            "dependencies": p03,
            "all_satisfied_by_current_level_up_table": all(
                row["satisfied_by_current_level_up_table"] for row in p03
            ),
        },
        "acquisition_contract": acquisition,
        "deferred_runtime_acceptance": {
            "reason": "THIS_ARTIFACT_IS_THE_REQUESTED_STATIC_FOUNDATION; NO ROM WAS MODIFIED",
            "required_after_adopted_branch_changes": [
                "成立/不成立/level境界と複数分岐slot優先順位",
                "4技満杯時の進化時技とキャンセル後の個体保持",
                "所持道具・使用道具の消費/不消費と不足時",
                "通常/隠れ特性slot、form、個体ID、既存技の保持",
                "保存、終了、fresh reload後の同一性",
                "通信代替と昼夜条件の代表回帰",
            ],
            "must_not_be_reported_as_passed": True,
        },
        "findings": {
            "required_fix_count": len(required_fixes),
            "review_count": len(findings) - len(required_fixes),
            "rows": findings,
        },
    }


__all__ = [
    "METHODS",
    "ModernizationEvolutionError",
    "ModernizationIdentityError",
    "build_evolution_contract",
    "normalize_evolution_rows",
    "parse_evolution_binary",
    "parse_runtime_method_enum",
    "stable_json",
]
