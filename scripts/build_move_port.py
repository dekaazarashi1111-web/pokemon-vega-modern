#!/usr/bin/env python3
"""T04: Vega固定IDとCFRU-JP技表を決定的に統合する。"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import re
import struct
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.engine.cfru_move_inventory import build_cfru_move_inventory  # noqa: E402
from tools.engine.extract_vega_moves import (  # noqa: E402
    default_policy,
    extract_vega_moves,
)


MOVE_FIELDS = (
    "effect",
    "power",
    "type",
    "accuracy",
    "pp",
    "secondary",
    "target",
    "priority",
    "flags",
    "z_move_power",
    "split",
    "z_move_effect",
)
ARTIFACT_ROOT = "generated/engine/moves"
MANIFEST_HEADER = (
    "move_key",
    "id",
    "vega_id",
    "cfru_symbol",
    "classification",
    "display_name",
    "status",
    "notes",
)


class MovePortError(ValueError):
    """入力、割当、または生成ABIが固定契約に一致しない。"""


def _fail(message: str) -> NoReturn:
    raise MovePortError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _normal(name: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKC", name)
        if not character.isspace()
    )


def _relative_file(root: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        _fail(f"{label} must be a non-empty relative path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        _fail(f"{label} escapes repository root")
    return path


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{label} must be an integer")
    return value


def _hex_integer(value: object, label: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if not isinstance(value, str):
        _fail(f"{label} must be an integer or hexadecimal string")
    try:
        return int(value, 0)
    except ValueError:
        _fail(f"{label} is not an integer")


def _read_csv(path: Path, expected_sha: str, expected_count: int) -> list[dict[str, str]]:
    raw = path.read_bytes()
    actual = _sha256(raw)
    if actual != expected_sha:
        _fail(f"V3 input hash mismatch for {path.name}: {actual}")
    with io.StringIO(raw.decode("utf-8-sig"), newline="") as stream:
        rows = [dict(row) for row in csv.DictReader(stream)]
    if len(rows) != expected_count:
        _fail(f"V3 row count mismatch for {path.name}: {len(rows)}")
    names = [row.get("move_name", "") for row in rows]
    if any(not name for name in names) or len(names) != len(set(names)):
        _fail(f"V3 move_name must be non-empty and unique: {path.name}")
    return rows


def _triple(spec: str) -> tuple[int, int, int] | None:
    match = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)(?=\D|$)", spec)
    if match is None:
        return None
    values = tuple(int(value) for value in match.groups())
    if any(value > 255 for value in values):
        _fail(f"V3 numeric triple is outside u8: {spec}")
    return values  # type: ignore[return-value]


_PROPOSAL_CLAUSE_OPS = {
    "相手全体": "TARGET_ALL_FOES",
    "特攻+1が20%": "USER_SP_ATTACK_UP_1_CHANCE_20",
    "麻痺30%": "TARGET_PARALYSIS_CHANCE_30",
    "自分混乱20%": "USER_CONFUSION_CHANCE_20",
    "連続強化": "ROLLING_POWER",
    "素早さ-1が20%": "TARGET_SPEED_DOWN_1_CHANCE_20",
    "優先度-1": "PRIORITY_MINUS_1",
    "4～5ターン拘束": "TRAP_TURNS_4_TO_5",
    "あくび同等": "YAWN_EQUIVALENT",
    "命中必中": "ALWAYS_HIT",
    "音技": "SOUND_MOVE",
    "特防-1が20%": "TARGET_SP_DEFENSE_DOWN_1_CHANCE_20",
    "命中低下20%": "TARGET_ACCURACY_DOWN_1_CHANCE_20",
    "自分の命中+1が30%": "USER_ACCURACY_UP_1_CHANCE_30",
    "猛毒20%": "TARGET_BAD_POISON_CHANCE_20",
    "自分防御-1が30%": "USER_DEFENSE_DOWN_1_CHANCE_30",
    "混乱20%": "TARGET_CONFUSION_CHANCE_20",
    "交代不可3ターン": "TRAP_TURNS_3",
    "反動1/3": "RECOIL_ONE_THIRD",
    "命中85": "ACCURACY_85",
    "混乱": "TARGET_CONFUSION_ALWAYS",
    "防御低下20%/凍り10%": "TARGET_DEFENSE_DOWN_20_OR_FREEZE_10",
    "睡眠20%": "TARGET_SLEEP_CHANCE_20",
    "自分特防+1が20%": "USER_SP_DEFENSE_UP_1_CHANCE_20",
    "自分特攻-1": "USER_SP_ATTACK_DOWN_1",
    "混乱10%": "TARGET_CONFUSION_CHANCE_10",
    "特防低下20%": "TARGET_SP_DEFENSE_DOWN_1_CHANCE_20",
    "自分防御/特防/素早さ-1": "USER_DEFENSE_SPDEF_SPEED_DOWN_1",
    "まもる貫通なし": "PROTECT_AFFECTED",
    "天候別状態異常20%": "WEATHER_STATUS_CHANCE_20",
    "体重依存特殊": "WEIGHT_BASED_SPECIAL_POWER",
    "攻撃または特攻の高い方を-1が30%": "TARGET_HIGHER_ATTACK_DOWN_1_CHANCE_30",
    "相手特攻+2": "TARGET_SP_ATTACK_UP_2",
    "麻痺10%": "TARGET_PARALYSIS_CHANCE_10",
    "素早さ+1が30%": "USER_SPEED_UP_1_CHANCE_30",
    "回避上昇なし": "NO_EVASION_BOOST",
    "HP依存": "USER_HP_SCALED_POWER",
    "特攻-2": "USER_SP_ATTACK_DOWN_2",
    "急所率+1": "CRITICAL_STAGE_UP_1",
    "命中+2、PP10": "USER_ACCURACY_UP_2",
    "素早さ+1/回避+1/命中-1": "USER_SPEED_EVASION_UP_1_ACCURACY_DOWN_1",
    "攻撃/特攻+1、雨で特攻のみ+2": "USER_ATTACK_SPATTACK_UP_1_RAIN_SPATTACK_UP_2",
    "自分猛毒": "USER_BAD_POISON",
    "優先度+1": "PRIORITY_PLUS_1",
    "自分特防-1が20%": "USER_SP_DEFENSE_DOWN_1_CHANCE_20",
    "追加効果なし": "NO_SECONDARY_EFFECT",
    "攻撃+1が10%": "USER_ATTACK_UP_1_CHANCE_10",
    "回避低下20%": "TARGET_EVASION_DOWN_1_CHANCE_20",
    "毒30%": "TARGET_POISON_CHANCE_30",
    "相手攻撃+1が30%": "TARGET_ATTACK_UP_1_CHANCE_30",
    "急所率+2": "CRITICAL_STAGE_UP_2",
    "自分のランダム能力+1が30%": "USER_RANDOM_STAT_UP_1_CHANCE_30",
    "自分素早さ-1が20%": "USER_SPEED_DOWN_1_CHANCE_20",
    "優先度-4": "PRIORITY_MINUS_4",
    "被弾時2倍": "DOUBLE_POWER_IF_HIT",
    "防御低下20%": "TARGET_DEFENSE_DOWN_1_CHANCE_20",
    "相手回避+1": "TARGET_EVASION_UP_1",
    "防御-1が30%": "TARGET_DEFENSE_DOWN_1_CHANCE_30",
    "素早さ-1が30%": "TARGET_SPEED_DOWN_1_CHANCE_30",
    "みねうち効果": "FALSE_SWIPE_DAMAGE_FLOOR",
    "自分防御+1が20%": "USER_DEFENSE_UP_1_CHANCE_20",
    "怯み10%": "TARGET_FLINCH_CHANCE_10",
    "三状態の合計発生率30%": "THREE_STATUS_TOTAL_CHANCE_30",
}


def _proposal_contract(spec: str, battle: dict[str, int]) -> dict[str, Any]:
    """V3独自技の自由記述をT06が消費できる固定operation列へ変換する。"""

    clauses = [part.strip() for part in spec.split("・") if part.strip()]
    if not clauses:
        _fail("V3 proposal is empty")
    head = clauses[0]
    tail = clauses[1:]
    power_rule: dict[str, Any]
    fixed = re.fullmatch(r"(\d+)/(\d+|必中)/(\d+)", head)
    multi = re.fullmatch(r"(\d+)×(\d+)/(\d+|必中)/(\d+)", head)
    ranged = re.fullmatch(r"(\d+)～(\d+)/(\d+|必中)/(\d+)", head)
    maximum = re.fullmatch(r"最大(\d+)/(\d+|必中)/(\d+)", head)
    operations: list[str] = []
    if fixed:
        power, accuracy, pp = fixed.groups()
        battle["power"] = int(power)
        battle["accuracy"] = 0 if accuracy == "必中" else int(accuracy)
        battle["pp"] = int(pp)
        power_rule = {"kind": "FIXED", "power": int(power)}
        if int(power):
            operations.append("DAMAGE")
    elif multi:
        power, hits, accuracy, pp = multi.groups()
        battle["power"] = int(power)
        battle["accuracy"] = 0 if accuracy == "必中" else int(accuracy)
        battle["pp"] = int(pp)
        power_rule = {"kind": "FIXED_MULTI_HIT", "power_per_hit": int(power), "hits": int(hits)}
        operations.extend(("DAMAGE", f"HIT_EXACTLY_{hits}"))
    elif ranged:
        minimum, maximum_value, accuracy, pp = ranged.groups()
        battle["accuracy"] = 0 if accuracy == "必中" else int(accuracy)
        battle["pp"] = int(pp)
        power_rule = {"kind": "RANGE", "minimum": int(minimum), "maximum": int(maximum_value)}
        operations.append("DYNAMIC_DAMAGE")
    elif maximum:
        maximum_value, accuracy, pp = maximum.groups()
        battle["accuracy"] = 0 if accuracy == "必中" else int(accuracy)
        battle["pp"] = int(pp)
        power_rule = {"kind": "MAXIMUM", "maximum": int(maximum_value)}
        operations.append("DYNAMIC_DAMAGE")
    else:
        tail = clauses
        power_rule = {"kind": "INHERIT_VEGA_BASE", "power": battle["power"]}
        if battle["power"]:
            operations.append("DAMAGE")

    for clause in tail:
        operation = _PROPOSAL_CLAUSE_OPS.get(clause)
        if operation is None:
            _fail(f"unparsed V3 exclusive proposal clause: {clause}")
        operations.append(operation)
        if clause == "相手全体":
            battle["target"] = 0x8
        elif clause == "命中必中":
            battle["accuracy"] = 0
        elif clause == "命中85":
            battle["accuracy"] = 85
        elif clause == "優先度-1":
            battle["priority"] = -1
        elif clause == "優先度-4":
            battle["priority"] = -4
        elif clause == "優先度+1":
            battle["priority"] = 1
        elif clause == "命中+2、PP10":
            battle["pp"] = 10
        elif clause == "まもる貫通なし":
            battle["flags"] |= 0x2

    chances = [int(value) for value in re.findall(r"(\d+)%", "・".join(tail))]
    if "追加効果なし" in tail:
        battle["secondary"] = 0
    elif chances:
        battle["secondary"] = max(chances)
    if not operations:
        operations.append("STATUS_OR_FIELD_EFFECT")
    return {
        "proposal": spec,
        "power_rule": power_rule,
        "accuracy": battle["accuracy"],
        "pp": battle["pp"],
        "secondary_chances": chances,
        "operations": operations,
        "runtime_binding": "T06_CFRU_EFFECT_DISPATCH",
    }


def _charmap(root: Path) -> tuple[dict[str, int], list[str]]:
    path = root / "vendor/upstream/CFRU-JP/charmap.tbl"
    result: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            byte = int(line[:2], 16)
        except ValueError:
            continue
        token = line[3:]
        if token == "$":
            continue
        result.setdefault(token, byte)
    tokens = sorted((token for token in result if token), key=lambda token: (-len(token), token))
    return result, tokens


def _encode_text(text: str, mapping: Mapping[str, int], tokens: Sequence[str]) -> bytes:
    output = bytearray()
    index = 0
    while index < len(text):
        for token in tokens:
            if text.startswith(token, index):
                output.append(mapping[token])
                index += len(token)
                break
        else:
            _fail(f"move name is not encodable at {text[index:]!r}: {text!r}")
    return bytes(output)


def _fixed_name(text: str, mapping: Mapping[str, int], tokens: Sequence[str]) -> bytes:
    encoded = _encode_text(text, mapping, tokens)
    if len(encoded) > 7:
        _fail(f"Vega bridge name exceeds 7 bytes: {text}")
    return encoded + bytes([0xFF]) * (8 - len(encoded))


def _terminated_game_text(text: str, mapping: Mapping[str, int], tokens: Sequence[str]) -> bytes:
    encoded = _encode_text(text, mapping, tokens)
    if not encoded or encoded[-1] != 0xFF:
        encoded += b"\xFF"
    return encoded


def _trim_game_text(raw: bytes, label: str) -> bytes:
    try:
        end = raw.index(0xFF)
    except ValueError:
        _fail(f"{label} has no game-text terminator")
    return raw[: end + 1]


def _decode_game_text(raw: bytes, mapping: Mapping[str, int]) -> str:
    reverse = {byte: token for token, byte in mapping.items()}
    output: list[str] = []
    for byte in _trim_game_text(raw, "game text")[:-1]:
        token = reverse.get(byte)
        if token is None:
            _fail(f"game text contains unmapped byte 0x{byte:02X}")
        output.append(token)
    return "".join(output)


def _cfru_description(
    row: Mapping[str, Any],
    reference_rom: bytes,
    mapping: Mapping[str, int],
    tokens: Sequence[str],
) -> dict[str, Any]:
    kind = str(row["description_mapping_kind"])
    if kind == "EXTERNAL_ROM_POINTER":
        pointer = int(str(row["description_symbol"]), 0)
        offset = pointer - 0x08000000
        if offset < 0 or offset + 60 > len(reference_rom):
            _fail(f"CFRU description pointer is outside reference ROM: 0x{pointer:08X}")
        raw = _trim_game_text(reference_rom[offset : offset + 60], f"description 0x{pointer:08X}")
        text = _decode_game_text(raw, mapping)
    elif kind == "SOURCE_SYMBOL":
        text = str(row["description_ja"] or "")
        if not text:
            _fail(f"CFRU source description is empty: {row['description_symbol']}")
        raw = _terminated_game_text(text, mapping, tokens)
    else:
        _fail(f"unknown CFRU description mapping kind: {kind}")
    return {
        "text": text,
        "raw_hex": raw.hex(),
        "symbol": row["description_symbol"],
        "mapping_kind": kind,
    }


def _z_effect_values(root: Path) -> dict[str, int]:
    result = {"0": 0}
    text = (root / "vendor/upstream/CFRU-JP/include/new/z_move_effects.h").read_text(
        encoding="utf-8"
    )
    for match in re.finditer(r"^#define\s+(Z_EFFECT_[A-Z0-9_]+)\s+(\d+)\b", text, re.MULTILINE):
        result[match.group(1)] = int(match.group(2))
    dynamax = (root / "vendor/upstream/CFRU-JP/include/new/dynamax.h").read_text(
        encoding="utf-8"
    )
    enum = re.search(r"enum\s+MaxMoveEffect\s*\{(.*?)\};", dynamax, re.DOTALL)
    if enum is None:
        _fail("CFRU MaxMoveEffect enum is missing")
    value = 0
    for raw in enum.group(1).split(","):
        symbol = re.sub(r"//.*", "", raw).strip()
        if not symbol:
            continue
        if "=" in symbol:
            symbol, literal = (part.strip() for part in symbol.split("=", 1))
            value = int(literal, 0)
        result[symbol] = value
        value += 1
    return result


def _vega_battle(row: Mapping[str, Any]) -> dict[str, int]:
    raw = bytes.fromhex(str(row["raw_hex"]))
    if len(raw) != 12:
        _fail(f"Vega move {row['id']} has a non-12-byte battle record")
    return {
        "effect": raw[0],
        "power": raw[1],
        "type": raw[2],
        "accuracy": raw[3],
        "pp": raw[4],
        "secondary": raw[5],
        "target": raw[6],
        "priority": struct.unpack("<b", raw[7:8])[0],
        "flags": raw[8],
        "z_move_power": raw[9],
        "split": raw[10],
        "z_move_effect": raw[11],
    }


def _cfru_battle(row: Mapping[str, Any], z_values: Mapping[str, int]) -> dict[str, int]:
    symbol = str(row["z_move_effect_symbol"])
    if symbol not in z_values:
        _fail(f"unresolved CFRU z/max effect: {symbol}")
    return {
        "effect": int(row["effect_id"]),
        "power": int(row["power"]),
        "type": int(row["type_id"]),
        "accuracy": int(row["accuracy"]),
        "pp": int(row["pp"]),
        "secondary": int(row["secondary_effect_chance"]),
        "target": int(row["target_id"]),
        "priority": int(row["priority"]),
        "flags": int(row["flags_mask"]),
        "z_move_power": int(row["z_move_power"]),
        "split": {"PHYSICAL": 0, "SPECIAL": 1, "STATUS": 2}[str(row["category"])],
        "z_move_effect": z_values[symbol],
    }


def _apply_triple(battle: dict[str, int], triple: tuple[int, int, int] | None) -> None:
    if triple is not None:
        battle["power"], battle["accuracy"], battle["pp"] = triple


def _crosscheck_config(config: Mapping[str, Any], vega: Mapping[str, Any], cfru: Mapping[str, Any]) -> None:
    if config.get("schema_version") != 1 or config.get("task") != "T04":
        _fail("move_port config schema/task mismatch")
    vcfg = config.get("vega")
    ccfg = config.get("cfru")
    if not isinstance(vcfg, Mapping) or not isinstance(ccfg, Mapping):
        _fail("move_port config requires vega and cfru objects")
    provenance = vega["provenance"]["rom"]
    for key, actual in (("rom_size", provenance["size"]), ("move_count", 512)):
        if _integer(vcfg.get(key), f"vega.{key}") != actual:
            _fail(f"vega.{key} differs from extracted evidence")
    if vcfg.get("rom_sha256") != provenance["sha256"]:
        _fail("vega.rom_sha256 differs from extracted evidence")
    table_names = {
        "names": "move_names",
        "battle": "battle_moves",
        "descriptions": "descriptions",
        "animations": "animations",
        "effects": "effects",
    }
    tables = vcfg.get("tables")
    if not isinstance(tables, Mapping):
        _fail("vega.tables must be an object")
    for config_name, extracted_name in table_names.items():
        cfg = tables.get(config_name)
        actual = vega["tables"][extracted_name]
        if not isinstance(cfg, Mapping):
            _fail(f"vega.tables.{config_name} missing")
        expected = (
            _hex_integer(cfg.get("address"), f"{config_name}.address"),
            _integer(cfg.get("count"), f"{config_name}.count"),
            _integer(cfg.get("stride"), f"{config_name}.stride"),
            cfg.get("sha256"),
        )
        observed = (actual["address"], actual["count"], actual["record_size"], actual["sha256"])
        if expected != observed:
            _fail(f"configured {config_name} table differs from extraction")
    if _integer(ccfg.get("move_count"), "cfru.move_count") != len(cfru["moves"]):
        _fail("configured CFRU move count differs from inventory")
    if ccfg.get("commit") != cfru["source_commit"]:
        _fail("configured CFRU commit differs from inventory")


def build_move_model(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """固定入力から、JSON-compatible情報とprivate bridge bytesを持つモデルを返す。"""

    if not isinstance(root, Path) or not isinstance(config, Mapping):
        _fail("root must be Path and config must be a mapping")
    root = root.resolve()
    vcfg = config.get("vega")
    ccfg = config.get("cfru")
    adjustments = config.get("adjustments")
    policy = config.get("mapping_policy")
    if not all(isinstance(value, Mapping) for value in (vcfg, ccfg, adjustments, policy)):
        _fail("move_port config is incomplete")

    rom_path = _relative_file(root, str(vcfg["rom_path"]), "vega.rom_path")
    rom_bytes = rom_path.read_bytes()
    vega = extract_vega_moves(root, rom_bytes, default_policy())
    source_root = _relative_file(root, str(ccfg["source_path"]), "cfru.source_path")
    cfru = build_cfru_move_inventory(root, source_root)
    _crosscheck_config(config, vega, cfru)

    adjustment_root = _relative_file(root, str(adjustments["root"]), "adjustments.root")
    v3_sets: dict[str, dict[str, Any]] = {}
    for key, spec_column in (
        ("modern_effects", "integrated_spec"),
        ("vega_exclusive", "integrated_proposal"),
    ):
        cfg = adjustments.get(key)
        if not isinstance(cfg, Mapping):
            _fail(f"adjustments.{key} missing")
        rows = _read_csv(
            _relative_file(adjustment_root, str(cfg["path"]), f"adjustments.{key}.path"),
            str(cfg["sha256"]),
            _integer(cfg["count"], f"adjustments.{key}.count"),
        )
        v3_sets[key] = {"rows": rows, "spec_column": spec_column, "sha256": cfg["sha256"]}

    mapping, tokens = _charmap(root)
    description_rom_path = _relative_file(
        root,
        str(ccfg["description_reference_rom"]),
        "cfru.description_reference_rom",
    )
    description_rom = description_rom_path.read_bytes()
    description_rom_sha256 = _sha256(description_rom)
    if description_rom_sha256 != ccfg.get("description_reference_sha256"):
        _fail("CFRU description reference ROM SHA-256 mismatch")
    z_values = _z_effect_values(root)
    vega_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cfru_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in vega["moves"]:
        vega_by_name[_normal(row["name_decoded"])].append(row)
    for row in cfru["moves"]:
        cfru_by_name[_normal(row["name_ja"])].append(row)

    exclusive_names = {_normal(row["move_name"]) for row in v3_sets["vega_exclusive"]["rows"]}
    adjustment_by_vega: dict[int, list[dict[str, Any]]] = defaultdict(list)
    v3_output: dict[str, Any] = {}
    for key, dataset in v3_sets.items():
        joins: list[dict[str, Any]] = []
        for source_row in dataset["rows"]:
            normalized = _normal(source_row["move_name"])
            matched = vega_by_name.get(normalized, [])
            if len(matched) != 1:
                _fail(f"V3 {key} name must resolve to one Vega move: {source_row['move_name']}")
            cfru_matches = cfru_by_name.get(normalized, [])
            if key == "modern_effects" and len(cfru_matches) != 1:
                _fail(f"modern V3 name must resolve to one CFRU move: {source_row['move_name']}")
            triple = _triple(source_row[dataset["spec_column"]])
            adjustment = {
                "dataset": key,
                "move_name": source_row["move_name"],
                "spec": source_row[dataset["spec_column"]],
                "numeric_triple": list(triple) if triple else None,
            }
            adjustment_by_vega[matched[0]["id"]].append(adjustment)
            joins.append(
                {
                    **adjustment,
                    "vega_id": matched[0]["id"],
                    "cfru_source_id": cfru_matches[0]["id"] if len(cfru_matches) == 1 else None,
                    "cfru_symbol": cfru_matches[0]["cfru_symbol"] if len(cfru_matches) == 1 else None,
                }
            )
        v3_output[key] = {
            "count": len(joins),
            "source_sha256": dataset["sha256"],
            "joins": joins,
        }

    overrides = policy.get("vega_name_overrides")
    if not isinstance(overrides, Mapping):
        _fail("mapping_policy.vega_name_overrides must be an object")
    duplicate_rules = policy.get("duplicate_name_resolution")
    if not isinstance(duplicate_rules, Mapping):
        _fail("mapping_policy.duplicate_name_resolution must be an object")
    pound_rule = duplicate_rules.get("1")
    if not isinstance(pound_rule, Mapping) or (
        pound_rule.get("duplicate_vega_ids") != [1, 511]
        or pound_rule.get("cfru_symbol") != "MOVE_POUND"
        or pound_rule.get("canonical_vega_id") != 1
        or pound_rule.get("policy") != "CFRU_ALIAS_TO_LOWEST_VEGA_ID_KEEP_ALL_FROZEN_ROWS"
    ):
        _fail("duplicate-name MOVE_POUND resolution contract differs")
    frozen: list[dict[str, Any]] = []
    mapped_symbols: set[str] = set()
    aliases: list[dict[str, Any]] = []
    bridge_names: list[bytes] = []
    bridge_battles: list[bytes] = []
    for vrow in vega["moves"]:
        move_id = int(vrow["id"])
        normalized = _normal(vrow["name_decoded"])
        exclusive = normalized in exclusive_names
        candidates = cfru_by_name.get(normalized, [])
        canonical_cfru: dict[str, Any] | None = None
        duplicate = False
        if not exclusive and len(candidates) == 1:
            siblings = sorted(row["id"] for row in vega_by_name[normalized])
            if move_id == siblings[0]:
                canonical_cfru = candidates[0]
                mapped_symbols.add(canonical_cfru["cfru_symbol"])
            else:
                duplicate = True
        elif not exclusive:
            _fail(f"non-exclusive Vega move has no unique CFRU identity: {move_id}")

        override = overrides.get(str(move_id))
        if override is not None and not isinstance(override, Mapping):
            _fail(f"name override {move_id} must be an object")
        display_name = str(override["display_name"]) if override else str(vrow["name_decoded"])
        if override and override.get("source_name") != vrow["name_decoded"]:
            _fail(f"name override source mismatch at Vega ID {move_id}")
        if override:
            move_key = str(override["move_key"])
        elif canonical_cfru:
            move_key = str(canonical_cfru["canonical_key"])
        else:
            move_key = f"MOVE_KEY_VEGA_{move_id:03d}"

        if exclusive:
            classification = "VEGA_EXCLUSIVE_V3"
        elif duplicate:
            classification = "VEGA_COMPAT_DUPLICATE"
        else:
            classification = "VEGA_CFRU_CANONICAL"
        source_for_data = canonical_cfru
        battle = (
            _cfru_battle(source_for_data, z_values)
            if source_for_data is not None
            else _vega_battle(vrow)
        )
        for adjustment in adjustment_by_vega.get(move_id, []):
            triple = adjustment["numeric_triple"]
            _apply_triple(battle, tuple(triple) if triple else None)
        effect_adapter: dict[str, Any] | None = None
        if exclusive:
            exclusive_adjustments = [
                adjustment
                for adjustment in adjustment_by_vega.get(move_id, [])
                if adjustment["dataset"] == "vega_exclusive"
            ]
            if len(exclusive_adjustments) != 1:
                _fail(f"Vega-exclusive move {move_id} must have one V3 proposal")
            plan = _proposal_contract(exclusive_adjustments[0]["spec"], battle)
            # CFRU table側では未知のVega numeric effectを流用しない。通常の
            # EFFECT_HIT(0)を安全なbaseにし、全意味はgenerated handlerが実行する。
            battle["effect"] = 0
            handler_symbol = f"MovePortAdapt_{move_key.removeprefix('MOVE_KEY_')}"
            effect_adapter = {
                "kind": "GENERATED_ADAPTER",
                "source_vega_effect_id": int(vrow["effect"]),
                "source_script_pointer": int(vrow["effect_script_pointer"]),
                "cfru_effect_id": 0,
                "cfru_script_symbol": None,
                "handler_symbol": handler_symbol,
                "adapter_source": f"{ARTIFACT_ROOT}/move_effect_adapters.c",
                "adapter_source_sha256": None,
                "effect_plan": plan,
                "evidence": "V3_EXCLUSIVE_PROPOSAL_AND_FIXED_VEGA_EFFECT_POINTER",
                "binding_status": "COMPILED_INTERFACE_T06_RUNTIME_BIND_PENDING",
            }
        bridge_record = bytearray(bytes.fromhex(vrow["raw_hex"]))
        for adjustment in adjustment_by_vega.get(move_id, []):
            triple = adjustment["numeric_triple"]
            if triple:
                bridge_record[1], bridge_record[3], bridge_record[4] = triple
        if effect_adapter is not None:
            bridge_record[1] = battle["power"]
            bridge_record[3] = battle["accuracy"]
            bridge_record[4] = battle["pp"]
            bridge_record[5] = battle["secondary"]
            bridge_record[6] = battle["target"]
            bridge_record[7] = battle["priority"] & 0xFF
            bridge_record[8] = battle["flags"]
        bridge_names.append(
            _fixed_name(display_name, mapping, tokens) if override else bytes.fromhex(vrow["name_raw"])
        )
        bridge_battles.append(bytes(bridge_record))

        if source_for_data:
            description = _cfru_description(
                source_for_data, description_rom, mapping, tokens
            )
            animation = {
                "symbol": source_for_data["animation_symbol"],
                "vega_pointer": 0,
                "mapping_kind": source_for_data["animation_mapping_kind"],
            }
            effect_map = {
                "id": source_for_data["effect_id"],
                "symbol": source_for_data["effect"],
                "script_symbol": source_for_data["effect_script_symbol"],
                "vega_pointer": 0,
                "mapping_kind": source_for_data["effect_script_mapping_kind"],
            }
        else:
            description = {
                "text": vrow["description_decoded"],
                "raw_hex": _trim_game_text(
                    bytes.fromhex(vrow["description_raw"]), f"Vega description {move_id}"
                ).hex(),
                "symbol": None,
                "mapping_kind": "VEGA_ROM_BYTES",
            }
            animation = {
                "symbol": None,
                "vega_pointer": vrow["animation_pointer"],
                "mapping_kind": "VEGA_ROM_POINTER",
            }
            effect_map = {
                "id": battle["effect"],
                "symbol": "GENERATED_VEGA_EXCLUSIVE_ADAPTER" if effect_adapter else None,
                "script_symbol": effect_adapter["handler_symbol"] if effect_adapter else None,
                "vega_pointer": vrow["effect_script_pointer"],
                "mapping_kind": "GENERATED_ADAPTER" if effect_adapter else "VEGA_ROM_POINTER",
            }
        frozen.append(
            {
                "id": move_id,
                "move_key": move_key,
                "vega_id": move_id,
                "cfru_symbol": source_for_data["cfru_symbol"] if source_for_data else None,
                "cfru_source_id": source_for_data["id"] if source_for_data else None,
                "classification": classification,
                "display_name": display_name,
                "source_name": vrow["name_decoded"],
                "battle": battle,
                "description": description,
                "animation": animation,
                "effect_map": effect_map,
                "effect_adapter": effect_adapter,
                "v3_adjustments": copy.deepcopy(adjustment_by_vega.get(move_id, [])),
            }
        )
        if source_for_data:
            aliases.append(
                {
                    "cfru_symbol": source_for_data["cfru_symbol"],
                    "cfru_source_id": source_for_data["id"],
                    "canonical_id": move_id,
                    "canonical_key": move_key,
                    "mapping": "VEGA_FROZEN_EXACT_NAME",
                }
            )

    append_start = _integer(policy.get("append_start"), "mapping_policy.append_start")
    if append_start != 512:
        _fail("append_start must remain 512")
    appended: list[dict[str, Any]] = []
    for cfru_row in cfru["moves"]:
        if cfru_row["cfru_symbol"] in mapped_symbols:
            continue
        canonical_id = append_start + len(appended)
        battle = _cfru_battle(cfru_row, z_values)
        row = {
            "id": canonical_id,
            "move_key": cfru_row["canonical_key"],
            "vega_id": None,
            "cfru_symbol": cfru_row["cfru_symbol"],
            "cfru_source_id": cfru_row["id"],
            "classification": "CFRU_APPEND",
            "display_name": cfru_row["name_ja"],
            "source_name": cfru_row["name_ja"],
            "battle": battle,
            "description": _cfru_description(
                cfru_row, description_rom, mapping, tokens
            ),
            "animation": {
                "symbol": cfru_row["animation_symbol"],
                "vega_pointer": 0,
                "mapping_kind": cfru_row["animation_mapping_kind"],
            },
            "effect_map": {
                "id": cfru_row["effect_id"],
                "symbol": cfru_row["effect"],
                "script_symbol": cfru_row["effect_script_symbol"],
                "vega_pointer": 0,
                "mapping_kind": cfru_row["effect_script_mapping_kind"],
            },
            "effect_adapter": None,
            "v3_adjustments": [],
        }
        appended.append(row)
        aliases.append(
            {
                "cfru_symbol": cfru_row["cfru_symbol"],
                "cfru_source_id": cfru_row["id"],
                "canonical_id": canonical_id,
                "canonical_key": cfru_row["canonical_key"],
                "mapping": "CFRU_APPEND",
            }
        )

    bridge_cfg = config.get("bridge")
    if not isinstance(bridge_cfg, Mapping):
        _fail("bridge config is missing")
    table_blobs = {
        "names": b"".join(bridge_names),
        "battle": b"".join(bridge_battles),
        "descriptions": b"".join(bytes.fromhex(row["description_raw"]) for row in vega["moves"]),
        "animations": b"".join(
            struct.pack("<I", row["animation_pointer"]) for row in vega["moves"]
        ),
        "effects": b"".join(
            struct.pack("<I", pointer)
            for pointer in [
                struct.unpack_from("<I", rom_bytes, vega["tables"]["effects"]["address"] - 0x08000000 + index * 4)[0]
                for index in range(256)
            ]
        ),
    }
    bridge_start = _hex_integer(bridge_cfg.get("start"), "bridge.start")
    bridge_blob = bytearray()
    layout_tables: dict[str, Any] = {}
    for name in ("names", "battle", "descriptions", "animations", "effects"):
        blob = table_blobs[name]
        offset = len(bridge_blob)
        bridge_blob.extend(blob)
        table_config = vcfg["tables"][name]
        layout_tables[name] = {
            "offset": offset,
            "size": len(blob),
            "file_offset": bridge_start + offset,
            "gba_address": 0x08000000 + bridge_start + offset,
            "old_gba_address": _hex_integer(table_config["address"], f"{name}.address"),
            "reference_count": _integer(table_config["reference_count"], f"{name}.reference_count"),
            "sha256": _sha256(blob),
        }
    bridge_bytes = bytes(bridge_blob)
    expected_bridge_size = _integer(bridge_cfg.get("expected_size"), "bridge.expected_size")
    if len(bridge_bytes) != expected_bridge_size:
        _fail(f"bridge size mismatch: {len(bridge_bytes)} != {expected_bridge_size}")

    moves = frozen + appended
    aliases.sort(key=lambda row: row["cfru_source_id"])
    model: dict[str, Any] = {
        "schema_version": 1,
        "task": "T04",
        "summary": {
            "frozen_count": len(frozen),
            "mapped_cfru_count": len(mapped_symbols),
            "appended_count": len(appended),
            "move_count": len(moves),
            "last_id": moves[-1]["id"],
            "cfru_alias_count": len(aliases),
            "v3_modern_count": v3_output["modern_effects"]["count"],
            "v3_exclusive_count": v3_output["vega_exclusive"]["count"],
            "v3_numeric_override_count": sum(
                adjustment["numeric_triple"] is not None
                for adjustment in adjustment_by_vega.values()
                for adjustment in adjustment
            ),
            "effect_adapter_count": len(exclusive_names),
        },
        "provenance": {
            "vega_rom_sha256": vega["provenance"]["rom"]["sha256"],
            "cfru_commit": cfru["source_commit"],
            "cfru_inventory_sha256": cfru["summaries"]["inventory_sha256"],
            "description_reference_sha256": description_rom_sha256,
            "mapping_policy": "V3_EXCLUSIVE_FIRST_THEN_NFKC_EXACT_UNIQUE",
            "duplicate_name_resolution": copy.deepcopy(duplicate_rules),
        },
        "moves": moves,
        "aliases": aliases,
        "v3": v3_output,
        "bridge": {
            "start": bridge_start,
            "gba_address": 0x08000000 + bridge_start,
            "size": len(bridge_bytes),
            "sha256": _sha256(bridge_bytes),
            "tables": layout_tables,
        },
        "_bridge_bytes": bridge_bytes,
        "_charmap": mapping,
        "_charmap_tokens": list(tokens),
    }
    adapter_source_sha256 = _sha256(_adapters_c(model))
    for row in moves:
        adapter = row.get("effect_adapter")
        if adapter is not None:
            adapter["adapter_source_sha256"] = adapter_source_sha256
    model["summary"]["effect_adapter_source_sha256"] = adapter_source_sha256
    validate_move_model(model)
    return model


def validate_move_model(model: Mapping[str, Any]) -> None:
    """T04 acceptanceに直結するID、join、table ABIを失敗閉塞で検証する。"""

    if model.get("schema_version") != 1 or model.get("task") != "T04":
        _fail("move model schema/task mismatch")
    moves = model.get("moves")
    aliases = model.get("aliases")
    summary = model.get("summary")
    if not isinstance(moves, list) or not isinstance(aliases, list) or not isinstance(summary, Mapping):
        _fail("move model collections are missing")
    if len(moves) != 1063 or [row.get("id") for row in moves] != list(range(1063)):
        _fail("canonical move IDs must be exact contiguous range 0..1062")
    if [row.get("vega_id") for row in moves[:512]] != list(range(512)):
        _fail("Vega IDs 0..511 are not frozen")
    if any(row.get("vega_id") is not None for row in moves[512:]):
        _fail("appended CFRU moves must not claim Vega IDs")
    if len({row.get("move_key") for row in moves}) != len(moves):
        _fail("canonical move keys are not unique")
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", str(row.get("move_key", ""))) for row in moves):
        _fail("canonical move key has an invalid format")
    if sum(row["classification"] == "CFRU_APPEND" for row in moves) != 551:
        _fail("appended CFRU count must be 551")
    if sum(row["classification"] == "VEGA_EXCLUSIVE_V3" for row in moves) != 70:
        _fail("V3 Vega-exclusive count must be 70")
    if moves[470]["display_name"] != "ソウルバイト" or moves[470]["move_key"] != "MOVE_KEY_SOUL_BITE":
        _fail("Vega ID 470 rename contract failed")
    if moves[509]["display_name"] != "ダークスナイプ" or moves[509]["move_key"] != "MOVE_KEY_DARK_SNIPE":
        _fail("Vega ID 509 rename contract failed")
    if moves[511]["classification"] != "VEGA_COMPAT_DUPLICATE":
        _fail("Vega duplicate pound ID 511 must remain a compatibility row")

    keys = {row["id"]: row["move_key"] for row in moves}
    if len(aliases) != 992:
        _fail("every CFRU symbol must have exactly one alias")
    if len({row.get("cfru_symbol") for row in aliases}) != 992:
        _fail("CFRU alias symbols are not unique")
    if [row.get("cfru_source_id") for row in aliases] != list(range(992)):
        _fail("CFRU aliases are not complete/source ordered")
    if any(keys.get(row.get("canonical_id")) != row.get("canonical_key") for row in aliases):
        _fail("CFRU alias points at an unknown canonical move")
    pound = next(row for row in aliases if row["cfru_symbol"] == "MOVE_POUND")
    if pound["canonical_id"] != 1:
        _fail("MOVE_POUND must map to the lowest Vega pound ID")
    for symbol in ("MOVE_JAWLOCK", "MOVE_SNIPESHOT"):
        alias = next(row for row in aliases if row["cfru_symbol"] == symbol)
        if alias["canonical_id"] < 512:
            _fail(f"{symbol} must remain a distinct CFRU append")

    mapping = model.get("_charmap")
    tokens = model.get("_charmap_tokens")
    if not isinstance(mapping, Mapping) or not isinstance(tokens, list):
        _fail("internal charmap is missing")
    for row in moves:
        encoded = _encode_text(row["display_name"], mapping, tokens)
        if not encoded or len(encoded) > 15:
            _fail(f"move name storage limit failed at ID {row['id']}")
        battle = row.get("battle")
        if not isinstance(battle, Mapping) or set(battle) != set(MOVE_FIELDS):
            _fail(f"battle record schema failed at ID {row['id']}")
        for field in MOVE_FIELDS:
            value = battle[field]
            lower, upper = (-128, 127) if field == "priority" else (0, 255)
            if not isinstance(value, int) or isinstance(value, bool) or not lower <= value <= upper:
                _fail(f"battle field {field} is outside storage at ID {row['id']}")
        description_text = str(row.get("description", {}).get("text", ""))
        if not description_text or len(description_text) > 1024:
            _fail(f"description is empty at ID {row['id']}")
        description_raw = row.get("description", {}).get("raw_hex")
        if not isinstance(description_raw, str):
            _fail(f"description game bytes are missing at ID {row['id']}")
        try:
            encoded_description = bytes.fromhex(description_raw)
        except ValueError:
            _fail(f"description game bytes are invalid at ID {row['id']}")
        if not encoded_description or encoded_description[-1] != 0xFF:
            _fail(f"description terminator is missing at ID {row['id']}")
        effect = row.get("effect_map", {})
        if not isinstance(effect.get("id"), int) or not 0 <= effect["id"] < 256:
            _fail(f"effect map is invalid at ID {row['id']}")
        animation = row.get("animation", {})
        if not animation.get("symbol") and not animation.get("vega_pointer"):
            _fail(f"animation map is unresolved at ID {row['id']}")

    v3 = model.get("v3")
    if not isinstance(v3, Mapping):
        _fail("V3 join evidence is missing")
    if v3["modern_effects"]["count"] != 61 or v3["vega_exclusive"]["count"] != 70:
        _fail("V3 join counts differ from fixed input")
    exclusive_ids = {row["vega_id"] for row in v3["vega_exclusive"]["joins"]}
    if any(moves[move_id]["classification"] != "VEGA_EXCLUSIVE_V3" for move_id in exclusive_ids):
        _fail("V3 exclusive precedence was not applied")
    adapters = [row["effect_adapter"] for row in moves if row.get("effect_adapter") is not None]
    if len(adapters) != 70 or len({row["handler_symbol"] for row in adapters}) != 70:
        _fail("V3 effect adapter count/symbol uniqueness failed")
    adapter_source_sha256 = _sha256(_adapters_c(model))
    for adapter in adapters:
        if (
            adapter.get("kind") != "GENERATED_ADAPTER"
            or not isinstance(adapter.get("source_script_pointer"), int)
            or adapter.get("adapter_source") != f"{ARTIFACT_ROOT}/move_effect_adapters.c"
            or adapter.get("adapter_source_sha256") != adapter_source_sha256
            or adapter.get("binding_status") != "COMPILED_INTERFACE_T06_RUNTIME_BIND_PENDING"
            or not adapter.get("effect_plan", {}).get("operations")
        ):
            _fail("V3 effect adapter contract is unresolved")
    if summary.get("effect_adapter_source_sha256") != adapter_source_sha256:
        _fail("V3 effect adapter source hash differs")

    bridge = model.get("bridge")
    blob = model.get("_bridge_bytes")
    if not isinstance(bridge, Mapping) or not isinstance(blob, bytes) or len(blob) != 44032:
        _fail("Vega bridge must be exactly 44,032 bytes")
    if bridge.get("sha256") != _sha256(blob) or bridge.get("size") != len(blob):
        _fail("Vega bridge hash/size differs")
    expected_offsets = {"names": 0, "battle": 4096, "descriptions": 10240, "animations": 40960, "effects": 43008}
    for name, offset in expected_offsets.items():
        table = bridge["tables"][name]
        if table["offset"] != offset or table["offset"] % 4 or table["size"] <= 0:
            _fail(f"Vega bridge {name} layout mismatch")
        part = blob[table["offset"] : table["offset"] + table["size"]]
        if table["sha256"] != _sha256(part):
            _fail(f"Vega bridge {name} hash mismatch")
    if sum(table["reference_count"] for table in bridge["tables"].values()) != 178:
        _fail("Vega bridge reference count must remain 178")


def _public_model(model: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in model.items() if not key.startswith("_")}


def _c_bytes(text: str) -> str:
    return '"' + "".join(f"\\x{byte:02X}" for byte in text.encode("utf-8")) + '"'


def _header(model: Mapping[str, Any]) -> bytes:
    operation_names = sorted(
        {
            operation
            for row in model["moves"]
            if row.get("effect_adapter") is not None
            for operation in row["effect_adapter"]["effect_plan"]["operations"]
        }
    )
    lines = [
        "/* generated by scripts/build_move_port.py; do not edit */",
        "#ifndef VEGA_MOVE_PORT_GENERATED_H",
        "#define VEGA_MOVE_PORT_GENERATED_H",
        "#include <stdint.h>",
        f"#define MOVE_PORT_COUNT {len(model['moves'])}",
        "enum MovePortId {",
    ]
    lines.extend(f"    {row['move_key']} = {row['id']}," for row in model["moves"])
    lines.extend(
        [
            "};",
        ]
    )
    for row in model["aliases"]:
        symbol = row["cfru_symbol"]
        lines.extend((f"#ifdef {symbol}", f"#undef {symbol}", "#endif"))
        lines.append(f"#define {symbol} {row['canonical_key']}")
    lines.extend(
        [
            "struct MovePortBattleMove { uint8_t effect, power, type, accuracy, pp, secondary, target; int8_t priority; uint8_t flags, z_move_power, split, z_move_effect; };",
            "struct MovePortEffectMap { uint8_t effect; uint32_t vega_pointer; const char *symbol; };",
            "struct MovePortAnimationMap { uint32_t vega_pointer; const char *symbol; };",
            "struct MovePortAdjustment { uint16_t move_id; uint8_t power, accuracy, pp; const char *dataset; const char *spec; };",
            "enum MovePortAdapterOperation {",
        ]
    )
    lines.extend(
        f"    MOVE_PORT_OP_{name} = {index},"
        for index, name in enumerate(operation_names)
    )
    lines.extend(
        [
            "};",
            "struct MovePortEffectAdapter { uint16_t move_id; uint8_t source_effect, cfru_effect, power, accuracy, pp, secondary, target; int8_t priority; uint8_t operation_count; uint32_t source_script; const enum MovePortAdapterOperation *operations; const char *proposal; };",
            "struct MovePortEffectRuntime { void *battle_context; int32_t (*apply)(void *battle_context, enum MovePortAdapterOperation operation); };",
            "typedef int32_t (*MovePortEffectHandler)(struct MovePortEffectRuntime *runtime);",
            "struct MovePortEffectDispatch { uint16_t move_id; MovePortEffectHandler handler; };",
            "extern const struct MovePortBattleMove gMovePortBattleMoves[MOVE_PORT_COUNT];",
            "extern const uint8_t *const gMovePortNames[MOVE_PORT_COUNT];",
            "extern const uint8_t *const gMovePortDescriptions[MOVE_PORT_COUNT];",
            "extern const struct MovePortEffectMap gMovePortEffects[MOVE_PORT_COUNT];",
            "extern const struct MovePortAnimationMap gMovePortAnimations[MOVE_PORT_COUNT];",
            "extern const struct MovePortEffectDispatch gMovePortEffectAdapters[70];",
            "extern const uint32_t gMovePortEffectAdapterCount;",
            "#endif",
            "",
        ]
    )
    return "\n".join(lines).encode("ascii")


def _battle_c(model: Mapping[str, Any]) -> bytes:
    lines = ['#include "moves_merged.h"', "const struct MovePortBattleMove gMovePortBattleMoves[MOVE_PORT_COUNT] = {"]
    for row in model["moves"]:
        battle = row["battle"]
        values = ", ".join(str(battle[field]) for field in MOVE_FIELDS)
        lines.append(f"    /* {row['id']} {row['move_key']} */ {{ {values} }},")
    lines.extend(["};", ""])
    return "\n".join(lines).encode("utf-8")


def _game_byte_array(name: str, raw: bytes) -> str:
    values = ", ".join(f"0x{byte:02X}" for byte in raw)
    return f"static const uint8_t {name}[] = {{ {values} }};"


def _name_c(model: Mapping[str, Any]) -> bytes:
    mapping = model["_charmap"]
    tokens = model["_charmap_tokens"]
    lines = ['#include "moves_merged.h"']
    for row in model["moves"]:
        raw = _terminated_game_text(row["display_name"], mapping, tokens)
        lines.append(_game_byte_array(f"sMoveName_{row['id']}", raw))
    lines.append("const uint8_t *const gMovePortNames[MOVE_PORT_COUNT] = {")
    lines.extend(f"    sMoveName_{row['id']}," for row in model["moves"])
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _description_c(model: Mapping[str, Any]) -> bytes:
    lines = ['#include "moves_merged.h"']
    for row in model["moves"]:
        raw = bytes.fromhex(row["description"]["raw_hex"])
        lines.append(_game_byte_array(f"sMoveDescription_{row['id']}", raw))
    lines.append("const uint8_t *const gMovePortDescriptions[MOVE_PORT_COUNT] = {")
    lines.extend(f"    sMoveDescription_{row['id']}," for row in model["moves"])
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _effect_c(model: Mapping[str, Any]) -> bytes:
    lines = ['#include "moves_merged.h"', "const struct MovePortEffectMap gMovePortEffects[MOVE_PORT_COUNT] = {"]
    for row in model["moves"]:
        effect = row["effect_map"]
        symbol = effect.get("script_symbol") or effect.get("symbol") or ""
        lines.append(
            f"    /* {row['id']} */ {{ {effect['id']}, UINT32_C({effect['vega_pointer']}), {_c_bytes(str(symbol))} }},"
        )
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _animation_c(model: Mapping[str, Any]) -> bytes:
    lines = ['#include "moves_merged.h"', "const struct MovePortAnimationMap gMovePortAnimations[MOVE_PORT_COUNT] = {"]
    for row in model["moves"]:
        animation = row["animation"]
        lines.append(
            f"    /* {row['id']} */ {{ UINT32_C({animation['vega_pointer']}), {_c_bytes(str(animation.get('symbol') or ''))} }},"
        )
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _adapters_c(model: Mapping[str, Any]) -> bytes:
    rows = [row for row in model["moves"] if row.get("effect_adapter") is not None]
    lines = [
        '#include "moves_merged.h"',
        "/* Compileable T04 adapter interface. T06 binds these per-move plans to CFRU. */",
    ]
    for row in rows:
        adapter = row["effect_adapter"]
        plan = adapter["effect_plan"]
        suffix = row["move_key"].removeprefix("MOVE_KEY_")
        operations = ", ".join(f"MOVE_PORT_OP_{value}" for value in plan["operations"])
        lines.append(
            f"static const enum MovePortAdapterOperation sOps_{suffix}[] = {{ {operations} }};"
        )
        battle = row["battle"]
        lines.append(
            f"static const struct MovePortEffectAdapter sAdapter_{suffix} = {{ "
            f"{row['id']}, {adapter['source_vega_effect_id']}, {adapter['cfru_effect_id']}, "
            f"{battle['power']}, {battle['accuracy']}, {battle['pp']}, {battle['secondary']}, "
            f"{battle['target']}, {battle['priority']}, {len(plan['operations'])}, "
            f"UINT32_C({adapter['source_script_pointer']}), sOps_{suffix}, "
            f"{_c_bytes(plan['proposal'])} }};"
        )
        lines.extend(
            [
                f"int32_t {adapter['handler_symbol']}(struct MovePortEffectRuntime *runtime) {{",
                "    if (runtime == 0 || runtime->apply == 0) return -1;",
                f"    for (uint8_t index = 0; index < sAdapter_{suffix}.operation_count; ++index) {{",
                f"        int32_t result = runtime->apply(runtime->battle_context, sAdapter_{suffix}.operations[index]);",
                "        if (result != 0) return result;",
                "    }",
                "    return 0;",
                "}",
            ]
        )
    lines.extend(
        [
            f"const uint32_t gMovePortEffectAdapterCount = UINT32_C({len(rows)});",
            f"const struct MovePortEffectDispatch gMovePortEffectAdapters[{len(rows)}] = {{",
        ]
    )
    for row in rows:
        lines.append(f"    {{ {row['id']}, {row['effect_adapter']['handler_symbol']} }},")
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _manifest(model: Mapping[str, Any]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(MANIFEST_HEADER)
    for row in model["moves"]:
        note = (
            "V3独自技をVega固定IDで保持"
            if row["classification"] == "VEGA_EXCLUSIVE_V3"
            else "CFRU-JP技をappend-onlyで追加"
            if row["classification"] == "CFRU_APPEND"
            else "同名互換IDを別canonicalとして保持"
            if row["classification"] == "VEGA_COMPAT_DUPLICATE"
            else "NFKC完全一致でCFRU identityを対応"
        )
        writer.writerow(
            [
                row["move_key"],
                row["id"],
                "" if row["vega_id"] is None else row["vega_id"],
                row["cfru_symbol"] or "",
                row["classification"],
                row["display_name"],
                "FROZEN" if row["vega_id"] is not None else "APPENDED",
                note,
            ]
        )
    return stream.getvalue().encode("utf-8")


def render_artifacts(model: Mapping[str, Any]) -> dict[str, bytes]:
    """検証済みモデルをrepo-relative path -> bytesへ副作用なしで描画する。"""

    validate_move_model(model)
    layout = copy.deepcopy(model["bridge"])
    layout["schema_version"] = 1
    artifacts = {
        f"{ARTIFACT_ROOT}/move_port.json": _stable_json(_public_model(model)),
        f"{ARTIFACT_ROOT}/moves_merged.h": _header(model),
        f"{ARTIFACT_ROOT}/battle_moves.c": _battle_c(model),
        f"{ARTIFACT_ROOT}/move_names.c": _name_c(model),
        f"{ARTIFACT_ROOT}/move_descriptions.c": _description_c(model),
        f"{ARTIFACT_ROOT}/move_effect_map.c": _effect_c(model),
        f"{ARTIFACT_ROOT}/move_animation_map.c": _animation_c(model),
        f"{ARTIFACT_ROOT}/move_effect_adapters.c": _adapters_c(model),
        f"{ARTIFACT_ROOT}/vega_bridge.bin": model["_bridge_bytes"],
        f"{ARTIFACT_ROOT}/layout.json": _stable_json(layout),
        "manifests/move_ids.csv": _manifest(model),
    }
    if len(artifacts) != 11 or any(not value for value in artifacts.values()):
        _fail("artifact set is incomplete")
    return artifacts


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    config_path = args.config.resolve() if args.config else root / "config/move_port.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        model = build_move_model(root, config)
        artifacts = render_artifacts(model)
        if args.write:
            for relative, data in artifacts.items():
                path = _relative_file(root, relative, "artifact path")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        print(json.dumps({"summary": model["summary"], "artifacts": sorted(artifacts)}, ensure_ascii=False, sort_keys=True))
    except (OSError, json.JSONDecodeError, MovePortError, ValueError, TypeError) as error:
        print(f"build-move-port: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
