#!/usr/bin/env python3
"""Stage 61 Kanto full-CFG 用の決定論的 namespace policy を構築する。

``stage61_event_semantic_relocator`` は、数値 ID を暗黙に現行 ROM へ流すことを
禁止している。本モジュールは FireRed 日本版 Rev.0 の ID と Stage 60 の ABI を
実データで照合し、全 operand を次のいずれかへ分類する。

* project manifest / Kanto crosswalk による意味 ID 変換
* Kanto 専用 flag / persistent-var namespace への決定論割当
* 命令 ABI または map-local ABI が保存されることを確認した明示 identity
* special の引数用途を呼出 site ごとに監査した operand override

Stage 60 は multichoice 1/13/21/22/23 と 57..60 を別用途に所有している。
そのため単純な identity は禁止し、65..73 へ写した拡張 table を別 payload に
生成する。これにより既存 Vega/QoL menu と clean Kanto menu の双方を壊さずに
保持する。
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.stage61_event_semantic_relocator import (
    FullCfgMaterialization,
    FullCfgRelocationPlan,
    NamespacePolicy,
    SemanticScriptGraph,
    SemanticRelocationError,
    allocate_kanto_state_namespace,
)


ROM_BASE = 0x08000000
ROM_LIMIT = 0x0A000000

# 1/2/3 は FireRed の temporary flags で map load ごとにclearされる。0x4000..407F
# は ``sSpecialFlags`` EWRAM配列のengine volatile ABIでsaveされない。どちらも
# persistent namespaceへ写すと意味が変質するためidentityを保つ。さらに
# 0x0805 (FLAG_SYS_USE_STRENGTH) はpersistentだがnative field engineが直接
# read/clearする固定ABIなのでidentityを保つ。残る124個のstory flagは、旧割当を
# 一切ずらさないよう0x1847..18C3から旧0x0805 shadowの0x18B3だけを除いて
# 割り当てる。0x18B3と0x18C4は再発検出用の未割当guardとして空ける。
TEMP_FLAG_IDS = frozenset({1, 2, 3})
ENGINE_SPECIAL_FLAG_RANGE = range(0x4000, 0x4080)
ENGINE_SYSTEM_FLAG_IDS = frozenset({0x0805})
FLAG_NAMESPACE_RANGE = range(0x1847, 0x18C4)
ENGINE_SYSTEM_FLAG_SHADOW_TARGETS: Mapping[int, int] = {0x0805: 0x18B3}
ALLOCATABLE_SCRIPT_FLAG_IDS = tuple(
    value for value in FLAG_NAMESPACE_RANGE
    if value not in set(ENGINE_SYSTEM_FLAG_SHADOW_TARGETS.values())
)
UNALLOCATED_SCRIPT_FLAG_GUARD = 0x18C4
OBJECT_ONLY_FLAG_NAMESPACE_RANGE = range(0x18C5, 0x18E0)
VISIT_FLAG_NAMESPACE_RANGE = range(0x18E0, 0x18FC)
VAR_NAMESPACE_RANGE = range(0x516D, 0x5180)
# BillのFireRed rootはSevii航路（製品scope外）を開始するためfull-CFGから
# 原子的に除外する。一方、同じ二つのflagはsource object visibility recordの
# ABIでもあるため、Kanto persistent namespace内の従来位置を保持する。
BILL_SCOPE_GUARD_SOURCE_ROOT = 0x08189851
BILL_VISIBILITY_STATE_IDS = frozenset({0x0062, 0x00A2})
BILL_SCENE_VAR_ID = 0x408A
BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID = 0x4001
ENGINE_SPECIAL_FLAG_CONSTANTS_SOURCE = Path(
    "vendor/upstream/pokefirered/include/constants/flags.h"
)
ENGINE_SPECIAL_FLAG_CONSTANTS_SHA256 = (
    "45f31e4dc3d42c1054463974cd31b1173bdd4cb6d9f94b2cdbf2c88b0f745493"
)
ENGINE_SPECIAL_FLAG_CONSUMER_SOURCE = Path(
    "vendor/upstream/pokefirered/src/event_data.c"
)
ENGINE_SPECIAL_FLAG_CONSUMER_SHA256 = (
    "163fcef03561426fc185b499eef1088dc7a4334b612968a82df3a0fa6131d06f"
)

# FireRed JPN Rev.0 / Stage60 双方で ScrCmd_special が参照する table。
SPECIAL_TABLE_ADDRESS = 0x08163068
SPECIAL_TABLE_COUNT = 444
STANDARD_SCRIPT_TABLE_ADDRESS = 0x08163758
STANDARD_SCRIPT_TABLE_COUNT = 10
STANDARD_STRING_TABLE_ADDRESS = 0x083A57BC

# ScriptMenu の全 consumer はこの2 literalだけであることを clean/Stage60で確認する。
MULTICHOICE_TABLE_ADDRESS = 0x083A557C
MULTICHOICE_STOCK_COUNT = 65
MULTICHOICE_TABLE_LITERAL_SITES = (0x0809C534, 0x0809CA08)
MULTICHOICE_REMAP: Mapping[int, int] = {
    1: 65,   # Eeveelutions
    13: 66,  # Bike shop
    21: 67,  # Helix fossil
    22: 68,  # Dome fossil
    23: 69,  # Old Amber
    57: 70,  # Clean Sevii ferry page / Stage60 Bill menu collision
    58: 71,  # Clean Sevii ferry page / Stage60 custom menu collision
    59: 72,  # Clean Sevii ferry page / Stage60 custom menu collision
    60: 73,  # Clean Sevii ferry page / Stage60 custom menu collision
}
MULTICHOICE_CLEAN_SCRIPT_SITES: Mapping[int, tuple[int, str]] = {
    57: (
        0x08172001,
        "f03ce2eea54c0ef309e2c8523a391ef7eedb8afff28c999ba46e729e30f9c587",
    ),
    58: (
        0x081964B7,
        "b6d6efe169fbb86e9e483725bc568f9897250a028da30a8466d314a6e0c7036d",
    ),
    59: (
        0x08196546,
        "dbbb55acb8700de64a121840598a75c8626e784f63471b963f2d98e8788e054e",
    ),
    60: (
        0x08196601,
        "7fd1c2a6ae232ee59078e344195d74e314a54a7505b91111ce7333aabc516c0a",
    ),
}

# Giovanni戦後にaddobjectされるSilph ScopeはStage60 map importerが
# templateを削除している。full CFGだけを移設するとtarget local ID 2の
# 無関係NPCを表示するため、唯一の欠落templateとして明示再配置する。
SILPH_SCOPE_SOURCE_SCRIPT = 0x081663AC
BAG_IS_FULL_SOURCE_SCRIPT = 0x081944C5
SILPH_SCOPE_TARGET_MAP = (97, 45)
SILPH_SCOPE_SOURCE_LOCAL_ID = 2
SILPH_SCOPE_TARGET_LOCAL_ID = 7
SILPH_SCOPE_SCRIPT_PREIMAGE = bytes.fromhex(
    "6a5a5302001a008067011a018001000900210d8000000601c54419086c02"
)

# Stage60で別実装へ差し替えられたが、戻り値契約を保つ既知のspecial。
SEMANTIC_SPECIAL_REPLACEMENTS = {
    0x0083: "CalculatePlayerPartyCount (expanded party互換実装)",
}

ABI_IDENTITY_CATEGORIES = frozenset(
    {
        "collision",
        "cry_mode",
        "fade_mode",
        "field_effect",
        "field_effect_argument",
        "field_effect_value",
        "engine_system_flag",
        "sound",
        "special",
        "special_var",
        "standard_script",
        "standard_string",
        "special_flag",
        "temp_flag",
        "temp_var",
        "text_color",
        "trainerbattle_local_or_flags",
        "trainerbattle_type",
        "warp_id",
    }
)

MAP_LOCAL_IDENTITY_CATEGORIES = frozenset(
    {"map_coordinate", "metatile"}
)


class Stage61NamespacePolicyError(SemanticRelocationError):
    """namespace の意味対応を推測なしで証明できない。"""


@dataclass(frozen=True)
class RuntimePatch:
    """Stage60 ROMに適用する固定preimage付きruntime patch。"""

    address: int
    expected: bytes
    replacement: bytes
    role: str

    def to_report(self) -> dict[str, Any]:
        return {
            "address": f"0x{self.address:08X}",
            "expected_hex": self.expected.hex(),
            "replacement_hex": self.replacement.hex(),
            "role": self.role,
        }


@dataclass(frozen=True)
class MultichoiceRuntimeMaterialization:
    """既存65行を保持し clean Kanto 9行を追加した runtime data。"""

    payload_base: int
    payload: bytes
    table_address: int
    patches: tuple[RuntimePatch, ...]
    source_to_target: Mapping[int, int]
    asset_rows: tuple[Mapping[str, Any], ...]

    def to_report(self) -> dict[str, Any]:
        return {
            "payload_base": f"0x{self.payload_base:08X}",
            "payload_size": len(self.payload),
            "payload_sha256": hashlib.sha256(self.payload).hexdigest(),
            "table_address": f"0x{self.table_address:08X}",
            "table_row_count": max(self.source_to_target.values()) + 1,
            "source_to_target": {
                str(source): target
                for source, target in sorted(self.source_to_target.items())
            },
            "patches": [row.to_report() for row in self.patches],
            "asset_rows": [dict(row) for row in self.asset_rows],
        }


@dataclass(frozen=True)
class ObjectVisibilityNamespacePlan:
    """469 source objectのvisibility flagをtarget recordへ反映する契約。"""

    source_to_target: Mapping[int, int]
    patches: tuple[RuntimePatch, ...]
    owner_rows: tuple[Mapping[str, Any], ...]
    assertions: Mapping[str, bool]

    def to_report(self) -> dict[str, Any]:
        return {
            "status": "PASS" if all(self.assertions.values()) else "FAIL",
            "source_to_target": {
                f"0x{source:04X}": f"0x{target:04X}"
                for source, target in sorted(self.source_to_target.items())
            },
            "owner_count": len(self.owner_rows),
            "patch_count": len(self.patches),
            "assertions": dict(self.assertions),
            "patches": [row.to_report() for row in self.patches],
            "owners": [dict(row) for row in self.owner_rows],
        }


@dataclass(frozen=True)
class MissingObjectTemplateRequirement:
    """target mapに存在しないsource object templateの厳密契約。"""

    source_map: str
    source_group: int
    source_map_id: int
    source_index: int
    source_local_id: int
    source_script_label: str
    source_script_pointer: int
    source_record: bytes
    source_flag: int
    source_graphics_id: int
    target_group: int
    target_map: int
    target_index: int
    target_local_id: int

    def to_report(self) -> dict[str, Any]:
        return {
            "source_map": self.source_map,
            "source_group": self.source_group,
            "source_map_id": self.source_map_id,
            "source_index": self.source_index,
            "source_local_id": self.source_local_id,
            "source_script_label": self.source_script_label,
            "source_script_pointer": f"0x{self.source_script_pointer:08X}",
            "source_record_hex": self.source_record.hex(),
            "source_flag": f"0x{self.source_flag:04X}",
            "source_graphics_id": self.source_graphics_id,
            "target_group": self.target_group,
            "target_map": self.target_map,
            "target_index": self.target_index,
            "target_local_id": self.target_local_id,
            "resolution": "RELOCATE_TARGET_OBJECT_ARRAY_AND_ADD_TEMPLATE",
        }


@dataclass(frozen=True)
class LocalObjectNamespacePlan:
    """full CFGのlocal-object operandをmap contextごとに解決したplan。"""

    operand_overrides: Mapping[tuple[str, int, int, str], int]
    site_rows: tuple[Mapping[str, Any], ...]
    missing_templates: tuple[MissingObjectTemplateRequirement, ...]
    assertions: Mapping[str, bool]

    def to_report(self) -> dict[str, Any]:
        existing_changed = sum(
            row["resolution"] == "TARGET_OBJECT_EXACT_MATCH"
            and row["source"] != row["target"]
            for row in self.site_rows
        )
        return {
            "status": "PASS" if all(self.assertions.values()) else "FAIL",
            "site_count": len(self.site_rows),
            "site_override_count": len(self.operand_overrides),
            "existing_object_nonidentity_override_count": existing_changed,
            "missing_template_count": len(self.missing_templates),
            "runtime_dependency": {
                "required": bool(self.missing_templates),
                "materializer": "materialize_stage61_missing_object_templates",
                "integration": (
                    "full CFG materialization後に呼び、旧object record宛の"
                    "graphics/script/visibility patchを新arrayへrebaseする"
                ),
            },
            "assertions": dict(self.assertions),
            "sites": [dict(row) for row in self.site_rows],
            "missing_templates": [row.to_report() for row in self.missing_templates],
        }


@dataclass(frozen=True)
class MissingObjectTemplateMaterialization:
    """Silph Scope template用adapterと再配置済みobject array。"""

    payload_base: int
    payload: bytes
    script_address: int
    object_array_address: int
    patches: tuple[RuntimePatch, ...]
    record_address_mapping: Mapping[int, int]
    requirement: MissingObjectTemplateRequirement
    verification_assertions: Mapping[str, bool]

    def rebase_object_address(self, address: int) -> int | None:
        """old object record内のpatch siteを新arrayへ写す。対象外はNone。"""

        for old, new in self.record_address_mapping.items():
            delta = address - old
            if 0 <= delta < 24:
                return new + delta
        return None

    def to_report(self) -> dict[str, Any]:
        return {
            "status": "PASS" if all(self.verification_assertions.values()) else "FAIL",
            "payload_base": f"0x{self.payload_base:08X}",
            "payload_size": len(self.payload),
            "payload_sha256": _sha(self.payload),
            "script_address": f"0x{self.script_address:08X}",
            "object_array_address": f"0x{self.object_array_address:08X}",
            "patches": [row.to_report() for row in self.patches],
            "record_address_mapping": {
                f"0x{source:08X}": f"0x{target:08X}"
                for source, target in sorted(self.record_address_mapping.items())
            },
            "integration_contract": {
                "rule": "REBASE_ALL_PENDING_OBJECT_RECORD_PATCHES",
                "details": (
                    "graphics/script/visibilityのold record内patchは"
                    "rebase_object_addressでpayload側へ写す"
                ),
            },
            "requirement": self.requirement.to_report(),
            "verification_assertions": dict(self.verification_assertions),
        }


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _rom_offset(raw: bytes, address: int, size: int, what: str) -> int:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(raw):
        raise Stage61NamespacePolicyError(
            f"{what} がROM範囲外です: {address:#010x}+{size:#x}"
        )
    return offset


def _rom_bytes(raw: bytes, address: int, size: int, what: str) -> bytes:
    offset = _rom_offset(raw, address, size, what)
    return raw[offset:offset + size]


def _u32(raw: bytes, address: int, what: str) -> int:
    return struct.unpack_from("<I", raw, _rom_offset(raw, address, 4, what))[0]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        raise Stage61NamespacePolicyError(f"manifestを読めません: {path}: {exc}") from exc


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage61NamespacePolicyError(f"JSONを読めません: {path}: {exc}") from exc


def _required_values(
    plan: FullCfgRelocationPlan, category: str
) -> tuple[int | tuple[int, int], ...]:
    values = {row.value for row in plan.numeric_references if row.category == category}
    return tuple(sorted(values, key=lambda value: (isinstance(value, tuple), value)))


def _engine_system_flag_contract(
    plan: FullCfgRelocationPlan,
    clean_rom: bytes,
    stage60_rom: bytes,
) -> dict[str, Any]:
    """Strengthのscript/native共有flag ABIを全producer/consumerで固定する。"""

    expected_references = {
        (0x081A48D0, "READ", 0x081A48B8, bytes.fromhex("2b0508")),
        (0x081A4914, "WRITE", 0x081A48B8, bytes.fromhex("290508")),
    }
    actual_references = {
        (
            int(row.source_address),
            str(row.access),
            int(row.root_addresses[0]),
            _rom_bytes(
                clean_rom,
                int(row.source_address),
                3,
                "clean Strength flag opcode",
            ),
        )
        for row in plan.numeric_references
        if row.category == "engine_system_flag"
        and isinstance(row.value, int)
        and int(row.value) == 0x0805
    }
    if actual_references != expected_references:
        raise Stage61NamespacePolicyError(
            "Strength engine system flag script closure不一致: "
            f"actual={actual_references!r}"
        )
    leaked = sorted({
        int(row.source_address)
        for row in plan.numeric_references
        if row.category == "flag"
        and isinstance(row.value, int)
        and int(row.value) in ENGINE_SYSTEM_FLAG_IDS
    })
    if leaked:
        raise Stage61NamespacePolicyError(
            f"Strength engine system flagがstory allocatorへ混入しています: {leaked}"
        )

    # script ownerに加えてnative read 1本・field reset clear 5本をpinする。
    # call命令とliteralを別々に固定し、単に0x0805 byte列がROM内にあるだけでは
    # PASSしないようにする。
    native_sites = (
        ("TryPushBoulder_FlagGet_call", 0x0805B5BA,
         bytes.fromhex("264812f082fc00060028")),
        ("TryPushBoulder_FLAG_SYS_USE_STRENGTH_literal", 0x0805B654,
         bytes.fromhex("05080000")),
        ("Overworld_ResetStateAfterFly_FlagClear_call", 0x0805458C,
         bytes.fromhex("0a4819f085fc")),
        ("Overworld_ResetStateAfterFly_flag_literal", 0x080545B8,
         bytes.fromhex("05080000")),
        ("Overworld_ResetStateAfterTeleport_FlagClear_call", 0x080545F4,
         bytes.fromhex("0a4819f051fc")),
        ("Overworld_ResetStateAfterTeleport_flag_literal", 0x08054620,
         bytes.fromhex("05080000")),
        ("Overworld_ResetStateAfterDigEscRope_FlagClear_call", 0x0805465C,
         bytes.fromhex("0a4819f01dfc")),
        ("Overworld_ResetStateAfterDigEscRope_flag_literal", 0x08054688,
         bytes.fromhex("05080000")),
        ("Overworld_ResetStateAfterWhitingOut_FlagClear_call", 0x080546C4,
         bytes.fromhex("0a4819f0e9fb")),
        ("Overworld_ResetStateAfterWhitingOut_flag_literal", 0x080546F0,
         bytes.fromhex("05080000")),
        ("ClearTempFieldEventData_FlagClear_call", 0x0806D92E,
         bytes.fromhex("084800f0b4fa")),
        ("ClearTempFieldEventData_flag_literal", 0x0806D950,
         bytes.fromhex("05080000")),
    )
    native_rows: list[dict[str, Any]] = []
    for role, address, expected in native_sites:
        clean_actual = _rom_bytes(clean_rom, address, len(expected), role)
        stage60_actual = _rom_bytes(stage60_rom, address, len(expected), role)
        if clean_actual != expected or stage60_actual != expected:
            raise Stage61NamespacePolicyError(
                f"Strength engine system flag native ABI preimage不一致: {role}:"
                f"clean={clean_actual.hex()}:stage60={stage60_actual.hex()}:"
                f"expected={expected.hex()}"
            )
        native_rows.append({
            "role": role,
            "address": f"0x{address:08X}",
            "raw_hex": expected.hex(),
            "raw_sha256": _sha(expected),
        })

    script_rows = []
    for address, access, root, expected in sorted(expected_references):
        stage60_actual = _rom_bytes(
            stage60_rom, address, len(expected), "Stage60 Strength flag opcode"
        )
        if stage60_actual != expected:
            raise Stage61NamespacePolicyError(
                "Stage60 Strength flag opcode preimage不一致: "
                f"{address:#010x}:{stage60_actual.hex()}!={expected.hex()}"
            )
        script_rows.append({
            "address": f"0x{address:08X}",
            "root": f"0x{root:08X}",
            "access": access,
            "flag_id": "0x0805",
            "raw_hex": expected.hex(),
            "raw_sha256": _sha(expected),
        })
    return {
        "status": "PASS",
        "source_id": "0x0805",
        "symbol": "FLAG_SYS_USE_STRENGTH",
        "policy": "EXACT_IDENTITY_SHARED_SCRIPT_NATIVE_FIELD_ABI",
        "former_invalid_shadow_target": "0x18B3",
        "script_sites": script_rows,
        "native_sites": native_rows,
        "native_read_count": 1,
        "native_clear_count": 5,
    }


def _numeric_index(
    rows: Iterable[Mapping[str, str]], source_column: str, target_column: str, what: str
) -> dict[int, int]:
    result: dict[int, int] = {}
    for row in rows:
        source_text = str(row.get(source_column, "")).strip()
        target_text = str(row.get(target_column, "")).strip()
        if not source_text.isdigit() or not target_text.isdigit():
            continue
        source = int(source_text)
        target = int(target_text)
        previous = result.setdefault(source, target)
        if previous != target:
            raise Stage61NamespacePolicyError(
                f"{what} source IDが複数targetへ対応します: {source} -> "
                f"{previous}/{target}"
            )
    return result


def _complete_mapping(
    required: Iterable[int], available: Mapping[int, int], what: str
) -> dict[int, int]:
    required_set = set(required)
    missing = sorted(required_set - set(available))
    if missing:
        raise Stage61NamespacePolicyError(f"{what} mapping不足: {missing}")
    return {source: int(available[source]) for source in sorted(required_set)}


def _species_mapping(root: Path, plan: FullCfgRelocationPlan) -> tuple[dict[int, int], dict[int, str]]:
    rows = _csv_rows(root / "manifests/species_ids.csv")
    available = _numeric_index(rows, "dpe_id", "id", "species")
    names = {
        int(row["dpe_id"]): str(row["species_key"])
        for row in rows if str(row.get("dpe_id", "")).isdigit()
    }
    required = [int(value) for value in _required_values(plan, "species")]
    return _complete_mapping(required, available, "species"), names


def _item_mapping(root: Path, plan: FullCfgRelocationPlan) -> tuple[dict[int, int], dict[int, str]]:
    rows = _csv_rows(root / "manifests/item_ids.csv")
    available = _numeric_index(rows, "cfru_id", "id", "item")
    names = {
        int(row["cfru_id"]): str(row["item_key"])
        for row in rows if str(row.get("cfru_id", "")).isdigit()
    }
    required = [int(value) for value in _required_values(plan, "item")]
    return _complete_mapping(required, available, "item"), names


def _move_mapping(root: Path, plan: FullCfgRelocationPlan) -> tuple[dict[int, int], dict[int, str]]:
    source_header = root / "vendor/upstream/pokefirered/include/constants/moves.h"
    try:
        source_text = source_header.read_text(encoding="utf-8")
    except OSError as exc:
        raise Stage61NamespacePolicyError(f"move定数を読めません: {exc}") from exc
    source_symbols: dict[int, str] = {}
    for symbol, value in re.findall(
        r"^#define\s+(MOVE_[A-Z0-9_]+)\s+([0-9]+)\s*$", source_text, re.MULTILINE
    ):
        source_symbols[int(value)] = symbol

    def normalized(symbol: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", symbol.upper())

    manifest_rows = _csv_rows(root / "manifests/move_ids.csv")
    by_symbol: dict[str, tuple[int, str]] = {}
    for row in manifest_rows:
        symbol = str(row.get("cfru_symbol", "")).strip()
        target = str(row.get("id", "")).strip()
        if not symbol or not target.isdigit():
            continue
        key = normalized(symbol)
        value = (int(target), str(row.get("move_key", "")))
        previous = by_symbol.setdefault(key, value)
        if previous != value:
            raise Stage61NamespacePolicyError(
                f"normalized move symbolが競合します: {symbol}"
            )
    result: dict[int, int] = {}
    names: dict[int, str] = {}
    for source in (int(value) for value in _required_values(plan, "move")):
        symbol = source_symbols.get(source)
        if symbol is None or normalized(symbol) not in by_symbol:
            raise Stage61NamespacePolicyError(
                f"move manifest mapping不足: source={source} symbol={symbol}"
            )
        target, key = by_symbol[normalized(symbol)]
        result[source] = target
        names[source] = f"{symbol}->{key}"
    return result, names


def _map_header(raw: bytes, group: int, number: int) -> tuple[int, bytes]:
    root = _u32(raw, ROM_BASE + 0x54B0C, "gMapGroups pointer")
    group_pointer = _u32(raw, root + group * 4, f"map group {group}")
    header_pointer = _u32(
        raw, group_pointer + number * 4, f"map header {group}/{number}"
    )
    return header_pointer, _rom_bytes(raw, header_pointer, 28, "map header")


def _object_record_address(
    raw: bytes, group: int, number: int, index: int
) -> int:
    _, object_count, array_pointer = _event_object_array(raw, group, number)
    if not 0 <= index < object_count:
        raise Stage61NamespacePolicyError(
            f"object indexが範囲外です: {group}/{number}:{index} >= {object_count}"
        )
    return array_pointer + index * 24


def _event_object_array(
    raw: bytes, group: int, number: int
) -> tuple[int, int, int]:
    """map event header、object数、object array pointerを厳密に読む。"""

    header_pointer, _ = _map_header(raw, group, number)
    event_pointer = _u32(raw, header_pointer + 4, "map event header")
    event_offset = _rom_offset(raw, event_pointer, 20, "map event header")
    object_count = raw[event_offset]
    array_pointer = _u32(raw, event_pointer + 4, "object event array")
    _rom_offset(raw, array_pointer, object_count * 24, "object event array")
    return event_pointer, object_count, array_pointer


def _map_mapping(
    root: Path,
    plan: FullCfgRelocationPlan,
    clean_rom: bytes,
    stage60_rom: bytes,
) -> tuple[dict[tuple[int, int], tuple[int, int]], list[dict[str, Any]]]:
    groups = _json(root / "vendor/upstream/pokefirered/data/maps/map_groups.json")
    if not isinstance(groups, Mapping) or not isinstance(groups.get("group_order"), list):
        raise Stage61NamespacePolicyError("map_groups.json ABIが不正です")
    crosswalk_rows = _csv_rows(root / "reports/generated/kanto_v2_crosswalk.csv")
    crosswalk: dict[str, tuple[int, int]] = {}
    for row in crosswalk_rows:
        try:
            value = (int(row["new_group_id"]), int(row["new_map_id"]))
        except (KeyError, ValueError) as exc:
            raise Stage61NamespacePolicyError("Kanto crosswalk行が不正です") from exc
        name = row["source_map"]
        previous = crosswalk.setdefault(name, value)
        if previous != value:
            raise Stage61NamespacePolicyError(f"source map対応が競合します: {name}")

    result: dict[tuple[int, int], tuple[int, int]] = {}
    evidence: list[dict[str, Any]] = []
    order = groups["group_order"]
    for value in _required_values(plan, "map"):
        if not isinstance(value, tuple) or len(value) != 2:
            raise Stage61NamespacePolicyError(f"map operandがpairではありません: {value!r}")
        source = (int(value[0]), int(value[1]))
        try:
            group_name = order[source[0]]
            source_name = groups[group_name][source[1]]
        except (IndexError, KeyError, TypeError) as exc:
            raise Stage61NamespacePolicyError(f"source map IDが不正です: {source}") from exc
        if source_name in crosswalk:
            target = crosswalk[source_name]
            basis = "KANTO_V2_CROSSWALK"
        elif source[0] == 0:
            # Link map群はKanto import対象外だが、Vegaも同じphysical slotを保持する。
            clean_pointer, clean_header = _map_header(clean_rom, *source)
            stage_pointer, stage_header = _map_header(stage60_rom, *source)
            # musicだけはVega曲へ差替可能。layout/event/script/flagsは同一を必須とする。
            if clean_pointer != stage_pointer or (
                clean_header[:16] + clean_header[18:]
                != stage_header[:16] + stage_header[18:]
            ):
                raise Stage61NamespacePolicyError(
                    f"import外Link mapのphysical ABIが一致しません: {source_name}"
                )
            target = source
            basis = "PHYSICAL_LINK_MAP_HEADER_IDENTITY_EXCEPT_MUSIC"
        else:
            raise Stage61NamespacePolicyError(
                f"Kanto crosswalkにsource mapがありません: {source} {source_name}"
            )
        result[source] = target
        evidence.append(
            {
                "source": list(source),
                "source_map": source_name,
                "target": list(target),
                "basis": basis,
            }
        )
    return result, evidence


def _trainer_mapping(
    root: Path, plan: FullCfgRelocationPlan
) -> tuple[dict[int, int], list[dict[str, Any]]]:
    event_plan = _json(root / "generated/runtime/trainer_changekit_final_event_plan.json")
    bindings = event_plan.get("bindings", []) if isinstance(event_plan, Mapping) else []
    if not isinstance(bindings, list):
        raise Stage61NamespacePolicyError("trainer event plan bindingsが配列ではありません")
    targets: dict[int, set[int]] = {}
    for row in bindings:
        if not isinstance(row, Mapping):
            continue
        source_ids = row.get("source_template_trainer_ids", [])
        if not isinstance(source_ids, list):
            source_ids = []
        if row.get("source_template_trainer_id") is not None:
            source_ids = [*source_ids, row["source_template_trainer_id"]]
        if not isinstance(row.get("trainer_id"), int):
            continue
        for source in source_ids:
            if isinstance(source, int):
                targets.setdefault(source, set()).add(int(row["trainer_id"]))

    result: dict[int, int] = {}
    evidence: list[dict[str, Any]] = []
    for value in _required_values(plan, "trainer"):
        source = int(value)
        candidates = sorted(targets.get(source, set()))
        if len(candidates) > 1:
            raise Stage61NamespacePolicyError(
                f"source trainerが複数project trainerへ対応します: {source}->{candidates}"
            )
        if candidates:
            target = candidates[0]
            basis = "TRAINER_CHANGEKIT_SOURCE_TEMPLATE_BINDING"
        else:
            # Stage57はKanto側の共有trainer IDを正本にし、衝突するTohoku側をcloneした。
            target = source
            basis = "KANTO_SOURCE_TRAINER_ID_RETAINED_STAGE57"
        result[source] = target
        evidence.append({"source": source, "target": target, "basis": basis})
    return result, evidence


def build_stage61_local_object_namespace_plan(
    root: Path,
    full_cfg: FullCfgRelocationPlan,
    clean_rom: bytes,
    stage60_rom: bytes,
) -> LocalObjectNamespacePlan:
    """210 local-object siteを到達rootのmap contextへ戻して解決する。"""

    root = Path(root)
    ledger = _json(root / "reports/generated/world_runtime_owner_ledger.json")
    owner_rows = ledger.get("owner_rows", []) if isinstance(ledger, Mapping) else []
    if not isinstance(owner_rows, list):
        raise Stage61NamespacePolicyError("world owner ledger ABIが不正です")

    groups = _json(root / "vendor/upstream/pokefirered/data/maps/map_groups.json")
    if not isinstance(groups, Mapping) or not isinstance(groups.get("group_order"), list):
        raise Stage61NamespacePolicyError("map_groups.json ABIが不正です")
    source_name_to_pair: dict[str, tuple[int, int]] = {}
    for group, group_name in enumerate(groups["group_order"]):
        names = groups.get(group_name)
        if not isinstance(names, list):
            raise Stage61NamespacePolicyError(
                f"source map groupが配列ではありません: {group_name}"
            )
        for number, name in enumerate(names):
            source_name_to_pair[str(name)] = (group, number)

    target_to_source: dict[tuple[int, int], tuple[str, tuple[int, int]]] = {}
    for row in _csv_rows(root / "reports/generated/kanto_v2_crosswalk.csv"):
        target = (int(row["new_group_id"]), int(row["new_map_id"]))
        source_name = str(row["source_map"])
        if source_name not in source_name_to_pair:
            raise Stage61NamespacePolicyError(
                f"crosswalk source mapがmap_groupsにありません: {source_name}"
            )
        value = (source_name, source_name_to_pair[source_name])
        previous = target_to_source.setdefault(target, value)
        if previous != value:
            raise Stage61NamespacePolicyError(
                f"target mapが複数sourceへ対応します: {target}"
            )

    target_objects: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    root_maps: dict[int, set[tuple[int, int]]] = {}
    for owner in owner_rows:
        if not isinstance(owner, Mapping):
            continue
        if owner.get("event") == "OBJECT":
            pair = (int(owner["group"]), int(owner["map"]))
            target_objects.setdefault(pair, []).append(owner)
        if (
            owner.get("role")
            in {"SOURCE_DIRECT_OBJECT_OWNER", "SOURCE_DIRECT_BG_OWNER"}
            and owner.get("source_script_pointer") is not None
        ):
            root_maps.setdefault(int(owner["source_script_pointer"]), set()).add(
                (int(owner["group"]), int(owner["map"]))
            )

    missing_root_context = sorted(set(full_cfg.root_source_addresses) - set(root_maps))
    if missing_root_context:
        raise Stage61NamespacePolicyError(
            "full CFG rootのmap contextがowner ledgerにありません: "
            + ",".join(f"0x{value:08X}" for value in missing_root_context)
        )

    # SemanticScriptGraphのnodeは連続instructionのbasic block。rootごとに
    # block内の全instructionへmap contextを展開する。
    graph = SemanticScriptGraph(clean_rom)
    graph.walk(full_cfg.root_source_addresses)
    instruction_maps: dict[int, set[tuple[int, int]]] = {}
    for source_root in full_cfg.root_source_addresses:
        contexts = root_maps[source_root]
        for node_address in graph.distances(source_root):
            for instruction in graph.nodes[node_address].instructions:
                instruction_maps.setdefault(instruction.address, set()).update(contexts)

    source_json_cache: dict[str, list[Mapping[str, Any]]] = {}

    def source_objects(source_name: str) -> list[Mapping[str, Any]]:
        if source_name not in source_json_cache:
            map_json = _json(
                root / f"vendor/upstream/pokefirered/data/maps/{source_name}/map.json"
            )
            rows = map_json.get("object_events", []) if isinstance(map_json, Mapping) else []
            if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
                raise Stage61NamespacePolicyError(
                    f"source object_events ABIが不正です: {source_name}"
                )
            source_json_cache[source_name] = list(rows)
        return source_json_cache[source_name]

    def validate_target_owner(
        target_pair: tuple[int, int], owner: Mapping[str, Any]
    ) -> None:
        index = int(owner["index"])
        record = _object_record_address(stage60_rom, *target_pair, index)
        raw = _rom_bytes(stage60_rom, record, 24, "target local-object owner")
        x, y = struct.unpack_from("<hh", raw, 4)
        if raw[0] != int(owner["local_id"]) or (x, y) != (
            int(owner["x"]), int(owner["y"])
        ):
            raise Stage61NamespacePolicyError(
                f"target local-object owner preimage不一致: {target_pair}:{index}"
            )
        script = struct.unpack_from("<I", raw, 16)[0]
        allowed = {int(owner.get("stage51_script", script))}
        if owner.get("source_script_pointer") is not None:
            allowed.add(int(owner["source_script_pointer"]))
        if script not in allowed:
            raise Stage61NamespacePolicyError(
                f"target local-object script owner不一致: {target_pair}:{index}"
            )

    references_by_key: dict[tuple[str, int, int, str], Any] = {}
    for reference in full_cfg.numeric_references:
        if reference.category != "local_object":
            continue
        previous = references_by_key.setdefault(reference.operand_key, reference)
        if previous.value != reference.value:
            raise Stage61NamespacePolicyError(
                f"local-object operand keyが競合します: {reference.operand_key}"
            )

    overrides: dict[tuple[str, int, int, str], int] = {}
    site_rows: list[dict[str, Any]] = []
    missing_by_identity: dict[
        tuple[str, int, int, int, int], MissingObjectTemplateRequirement
    ] = {}
    existing_changed_count = 0
    for reference in sorted(
        references_by_key.values(), key=lambda row: row.operand_key
    ):
        source_value = int(reference.value)
        contexts = sorted(instruction_maps.get(reference.source_address, set()))
        if not contexts:
            raise Stage61NamespacePolicyError(
                f"local-object siteのmap contextを復元できません: "
                f"{reference.source_address:#010x}"
            )
        resolved_values: set[int] = set()
        context_rows: list[dict[str, Any]] = []
        resolutions: set[str] = set()
        for target_pair in contexts:
            if target_pair not in target_to_source:
                raise Stage61NamespacePolicyError(
                    f"local-object contextがcrosswalk外です: {target_pair}"
                )
            source_name, source_pair = target_to_source[target_pair]
            if source_value in {0, 0x7F, 0xFF}:
                target_value = source_value
                resolutions.add("ENGINE_LOCAL_SENTINEL_IDENTITY")
                context_rows.append(
                    {
                        "target_map": list(target_pair),
                        "source_map": source_name,
                        "basis": "ENGINE_LOCAL_SENTINEL_IDENTITY",
                    }
                )
                resolved_values.add(target_value)
                continue

            objects = source_objects(source_name)
            source_indices = []
            _, source_count, _ = _event_object_array(clean_rom, *source_pair)
            for source_index in range(source_count):
                source_record_address = _object_record_address(
                    clean_rom, *source_pair, source_index
                )
                source_raw = _rom_bytes(
                    clean_rom, source_record_address, 24, "source local-object"
                )
                if source_raw[0] == source_value:
                    source_indices.append((source_index, source_record_address, source_raw))
            if len(source_indices) != 1:
                raise Stage61NamespacePolicyError(
                    f"source local IDを一意に解決できません: "
                    f"{source_name}:{source_value} candidates={len(source_indices)}"
                )
            source_index, source_record_address, source_raw = source_indices[0]
            if source_index >= len(objects):
                raise Stage61NamespacePolicyError(
                    f"source object JSON/ROM数が不一致です: {source_name}"
                )
            source_object = objects[source_index]
            source_x, source_y = struct.unpack_from("<hh", source_raw, 4)
            if (source_x, source_y) != (
                int(source_object["x"]), int(source_object["y"])
            ):
                raise Stage61NamespacePolicyError(
                    f"source local-object JSON/ROM座標不一致: "
                    f"{source_name}:{source_index}"
                )
            source_label = str(source_object.get("script", ""))
            candidates = [
                owner for owner in target_objects.get(target_pair, [])
                if int(owner["x"]) == source_x and int(owner["y"]) == source_y
            ]
            exact_label = [
                owner for owner in candidates
                if str(owner.get("source_script_label", "")) == source_label
            ]
            if len(exact_label) == 1:
                candidates = exact_label
            if len(candidates) > 1:
                raise Stage61NamespacePolicyError(
                    f"target local-objectを座標/labelで一意に解決できません: "
                    f"{target_pair} source={source_label} candidates={len(candidates)}"
                )
            if candidates:
                owner = candidates[0]
                validate_target_owner(target_pair, owner)
                target_value = int(owner["local_id"])
                resolution = "TARGET_OBJECT_EXACT_MATCH"
                context_rows.append(
                    {
                        "target_map": list(target_pair),
                        "source_map": source_name,
                        "source_index": source_index,
                        "source_local_id": source_value,
                        "source_label": source_label,
                        "target_index": int(owner["index"]),
                        "target_local_id": target_value,
                        "target_role": str(owner["role"]),
                        "basis": "SOURCE_COORDINATE_AND_OPTIONAL_LABEL_EXACT_MATCH",
                    }
                )
            else:
                event_pointer, target_count, _ = _event_object_array(
                    stage60_rom, *target_pair
                )
                del event_pointer
                target_value = target_count + 1
                resolution = "MISSING_TEMPLATE_ALLOCATED"
                identity = (
                    source_name, source_index, target_pair[0], target_pair[1],
                    target_value,
                )
                requirement = MissingObjectTemplateRequirement(
                    source_map=source_name,
                    source_group=source_pair[0],
                    source_map_id=source_pair[1],
                    source_index=source_index,
                    source_local_id=source_value,
                    source_script_label=source_label,
                    source_script_pointer=struct.unpack_from("<I", source_raw, 16)[0],
                    source_record=source_raw,
                    source_flag=struct.unpack_from("<H", source_raw, 20)[0],
                    source_graphics_id=source_raw[1],
                    target_group=target_pair[0],
                    target_map=target_pair[1],
                    target_index=target_count,
                    target_local_id=target_value,
                )
                previous = missing_by_identity.setdefault(identity, requirement)
                if previous != requirement:
                    raise Stage61NamespacePolicyError(
                        f"missing template requirementが競合します: {identity}"
                    )
                context_rows.append(
                    {
                        "target_map": list(target_pair),
                        "source_map": source_name,
                        "source_index": source_index,
                        "source_local_id": source_value,
                        "source_label": source_label,
                        "target_index": target_count,
                        "target_local_id": target_value,
                        "basis": "MISSING_TEMPLATE_EXPLICIT_ALLOCATION",
                    }
                )
            resolutions.add(resolution)
            resolved_values.add(target_value)

        if len(resolved_values) != 1:
            raise Stage61NamespacePolicyError(
                f"shared local-object siteのmap間対応が競合します: "
                f"{reference.operand_key} -> {sorted(resolved_values)}"
            )
        target_value = next(iter(resolved_values))
        overrides[reference.operand_key] = target_value
        resolution = (
            "MISSING_TEMPLATE_ALLOCATED"
            if "MISSING_TEMPLATE_ALLOCATED" in resolutions
            else "TARGET_OBJECT_EXACT_MATCH"
            if "TARGET_OBJECT_EXACT_MATCH" in resolutions
            else "ENGINE_LOCAL_SENTINEL_IDENTITY"
        )
        if resolution == "TARGET_OBJECT_EXACT_MATCH" and target_value != source_value:
            existing_changed_count += 1
        site_rows.append(
            {
                "operand_key": list(reference.operand_key),
                "source_address": f"0x{reference.source_address:08X}",
                "operand_offset": reference.operand_offset,
                "source": source_value,
                "target": target_value,
                "detail": reference.detail,
                "resolution": resolution,
                "contexts": context_rows,
            }
        )

    missing_templates = tuple(
        row for _, row in sorted(missing_by_identity.items())
    )
    exact_missing = (
        len(missing_templates) == 1
        and missing_templates[0].source_map == "RocketHideout_B4F"
        and missing_templates[0].source_local_id == SILPH_SCOPE_SOURCE_LOCAL_ID
        and missing_templates[0].source_script_pointer == SILPH_SCOPE_SOURCE_SCRIPT
        and (
            missing_templates[0].target_group,
            missing_templates[0].target_map,
        ) == SILPH_SCOPE_TARGET_MAP
        and missing_templates[0].target_local_id == SILPH_SCOPE_TARGET_LOCAL_ID
    )
    assertions = {
        "local_object_site_count_210": len(site_rows) == 210,
        "all_sites_have_operand_override": len(overrides) == len(site_rows),
        "existing_nonidentity_override_count_46": existing_changed_count == 46,
        "missing_template_count_1": len(missing_templates) == 1,
        "missing_template_is_rocket_silph_scope": exact_missing,
        "all_full_roots_have_map_context": not missing_root_context,
    }
    if not all(assertions.values()):
        raise Stage61NamespacePolicyError(
            "local-object namespace assertion FAIL: "
            + ", ".join(name for name, passed in assertions.items() if not passed)
        )
    return LocalObjectNamespacePlan(
        operand_overrides=overrides,
        site_rows=tuple(site_rows),
        missing_templates=missing_templates,
        assertions=assertions,
    )


def _special_names(root: Path) -> list[str]:
    try:
        text = (root / "vendor/upstream/pokefirered/data/specials.inc").read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        raise Stage61NamespacePolicyError(f"specials.incを読めません: {exc}") from exc
    names = re.findall(r"^\s*def_special\s+([A-Za-z0-9_]+)", text, re.MULTILINE)
    if len(names) != SPECIAL_TABLE_COUNT:
        raise Stage61NamespacePolicyError(
            f"special count不一致: {len(names)} != {SPECIAL_TABLE_COUNT}"
        )
    return names


def _special_argument_overrides(
    plan: FullCfgRelocationPlan,
    species_available: Mapping[int, int],
) -> tuple[dict[tuple[str, int, int, str], int], list[dict[str, Any]]]:
    overrides: dict[tuple[str, int, int, str], int] = {}
    evidence: list[dict[str, Any]] = []
    for reference in plan.numeric_references:
        if reference.category != "special_argument":
            continue
        match = re.search(r"special 0x([0-9A-Fa-f]{4}) argument via VAR_0x([0-9A-Fa-f]{4})", reference.detail)
        if match is None:
            raise Stage61NamespacePolicyError(
                f"special_argumentの呼出siteを復元できません: {reference.operand_key}"
            )
        special_id = int(match.group(1), 16)
        variable = int(match.group(2), 16)
        source = int(reference.value)
        if special_id == 0x0163:  # SetSeenMon(VAR_8004=species)
            if source not in species_available:
                raise Stage61NamespacePolicyError(
                    f"SetSeenMon species mapping不足: {source}"
                )
            target = species_available[source]
            semantic = "SPECIES_ID"
        elif special_id == 0x018B and variable == 0x8004:
            # OpenMuseumFossilPic(VAR_8004=species, 8005=x, 8006=y)
            if source not in species_available:
                raise Stage61NamespacePolicyError(
                    f"OpenMuseumFossilPic species mapping不足: {source}"
                )
            target = species_available[source]
            semantic = "SPECIES_ID"
        else:
            target = source
            semantic = "SPECIAL_LOCAL_ENUM_OR_COORDINATE"
        overrides[reference.operand_key] = target
        evidence.append(
            {
                "source_address": f"0x{reference.source_address:08X}",
                "operand_offset": reference.operand_offset,
                "special_id": f"0x{special_id:04X}",
                "variable": f"0x{variable:04X}",
                "source": source,
                "target": target,
                "semantic": semantic,
            }
        )
    return overrides, evidence


def _terminated_text(raw: bytes, pointer: int) -> bytes:
    offset = _rom_offset(raw, pointer, 1, "multichoice text")
    end = raw.find(b"\xFF", offset, min(len(raw), offset + 0x400))
    if end < 0:
        raise Stage61NamespacePolicyError(
            f"multichoice textにEOSがありません: {pointer:#010x}"
        )
    return raw[offset:end + 1]


def _validate_multichoice_contract(clean_rom: bytes, stage60_rom: bytes) -> list[dict[str, Any]]:
    expected_pointer = struct.pack("<I", MULTICHOICE_TABLE_ADDRESS)
    for site in MULTICHOICE_TABLE_LITERAL_SITES:
        if _rom_bytes(clean_rom, site, 4, "clean multichoice literal") != expected_pointer:
            raise Stage61NamespacePolicyError(
                f"clean multichoice table literal preimage不一致: {site:#010x}"
            )
        if _rom_bytes(stage60_rom, site, 4, "Stage60 multichoice literal") != expected_pointer:
            raise Stage61NamespacePolicyError(
                f"Stage60 multichoice table literal preimage不一致: {site:#010x}"
            )

    rows: list[dict[str, Any]] = []
    for source, target in MULTICHOICE_REMAP.items():
        clean_row = _rom_bytes(
            clean_rom, MULTICHOICE_TABLE_ADDRESS + source * 8, 8,
            f"clean multichoice {source}",
        )
        stage_row = _rom_bytes(
            stage60_rom, MULTICHOICE_TABLE_ADDRESS + source * 8, 8,
            f"Stage60 multichoice {source}",
        )
        list_pointer, count = struct.unpack_from("<IB", clean_row)
        if count == 0 or count > 8:
            raise Stage61NamespacePolicyError(
                f"clean multichoice countが不正です: {source}={count}"
            )
        list_raw = _rom_bytes(clean_rom, list_pointer, count * 8, "menu action list")
        text_rows: list[dict[str, Any]] = []
        for index in range(count):
            text_pointer = struct.unpack_from("<I", list_raw, index * 8)[0]
            text_raw = _terminated_text(clean_rom, text_pointer)
            text_rows.append(
                {
                    "index": index,
                    "source_pointer": f"0x{text_pointer:08X}",
                    "size": len(text_raw),
                    "sha256": _sha(text_raw),
                }
            )
        rows.append(
            {
                "source_id": source,
                "target_id": target,
                "source_list_pointer": f"0x{list_pointer:08X}",
                "choice_count": count,
                "clean_row_hex": clean_row.hex(),
                "stage60_row_hex": stage_row.hex(),
                "stage60_conflict": clean_row != stage_row,
                "list_sha256": _sha(list_raw),
                "texts": text_rows,
            }
        )
    if not all(row["stage60_conflict"] for row in rows):
        raise Stage61NamespacePolicyError(
            "専用multichoiceへ退避する9 IDの競合contractが変化しました"
        )
    if set(MULTICHOICE_CLEAN_SCRIPT_SITES) != {57, 58, 59, 60}:
        raise Stage61NamespacePolicyError(
            "Sevii ferry clean script site集合が不正です"
        )
    for source, (site, expected_sha256) in sorted(
        MULTICHOICE_CLEAN_SCRIPT_SITES.items()
    ):
        expected_instruction = bytes((0x6F, 0x13, 0x05, source, 0x00))
        clean_instruction = _rom_bytes(
            clean_rom, site, 5, f"clean ferry multichoice {source}"
        )
        stage_instruction = _rom_bytes(
            stage60_rom, site, 5, f"Stage60 ferry multichoice {source}"
        )
        clean_branch = _rom_bytes(
            clean_rom, site, 66, f"clean ferry choice branch {source}"
        )
        stage_branch = _rom_bytes(
            stage60_rom, site, 66, f"Stage60 ferry choice branch {source}"
        )
        if clean_instruction != expected_instruction \
                or stage_instruction != expected_instruction:
            raise Stage61NamespacePolicyError(
                f"Sevii ferry multichoice instruction preimage不一致: {source}"
            )
        if clean_branch != stage_branch or _sha(clean_branch) != expected_sha256:
            raise Stage61NamespacePolicyError(
                f"Sevii ferry choice branch SHA-256不一致: {source}"
            )
    return rows


def materialize_multichoice_runtime_contract(
    clean_rom: bytes, stage60_rom: bytes, payload_base: int
) -> MultichoiceRuntimeMaterialization:
    """Stage61 payloadへ置ける74行tableと2 literal+4 operand patchを生成する。"""

    _validate_multichoice_contract(clean_rom, stage60_rom)
    if payload_base % 4 or not ROM_BASE <= payload_base < ROM_LIMIT:
        raise Stage61NamespacePolicyError(
            f"multichoice payload baseが不正です: {payload_base:#010x}"
        )
    table_count = max(MULTICHOICE_REMAP.values()) + 1
    output = bytearray(table_count * 8)
    stock = _rom_bytes(
        stage60_rom,
        MULTICHOICE_TABLE_ADDRESS,
        MULTICHOICE_STOCK_COUNT * 8,
        "Stage60 multichoice table",
    )
    output[:len(stock)] = stock
    asset_rows: list[dict[str, Any]] = []

    def align4() -> None:
        while len(output) % 4:
            output.append(0xFF)

    for source, target in sorted(MULTICHOICE_REMAP.items()):
        clean_row = _rom_bytes(
            clean_rom, MULTICHOICE_TABLE_ADDRESS + source * 8, 8,
            f"clean multichoice row {source}",
        )
        source_list, count = struct.unpack_from("<IB", clean_row)
        source_list_raw = _rom_bytes(
            clean_rom, source_list, count * 8, f"clean menu list {source}"
        )
        text_offsets: list[int] = []
        text_rows: list[dict[str, Any]] = []
        for index in range(count):
            source_text = struct.unpack_from("<I", source_list_raw, index * 8)[0]
            text_raw = _terminated_text(clean_rom, source_text)
            align4()
            text_offset = len(output)
            output.extend(text_raw)
            text_offsets.append(text_offset)
            text_rows.append(
                {
                    "index": index,
                    "source_pointer": f"0x{source_text:08X}",
                    "target_pointer": f"0x{payload_base + text_offset:08X}",
                    "size": len(text_raw),
                    "sha256": _sha(text_raw),
                }
            )
        align4()
        list_offset = len(output)
        relocated_list = bytearray(source_list_raw)
        for index, text_offset in enumerate(text_offsets):
            struct.pack_into("<I", relocated_list, index * 8, payload_base + text_offset)
        output.extend(relocated_list)
        struct.pack_into("<I", output, target * 8, payload_base + list_offset)
        output[target * 8 + 4] = count
        asset_rows.append(
            {
                "source_id": source,
                "target_id": target,
                "choice_count": count,
                "target_list_pointer": f"0x{payload_base + list_offset:08X}",
                "texts": text_rows,
            }
        )
    if payload_base + len(output) > ROM_LIMIT:
        raise Stage61NamespacePolicyError("multichoice payloadが32MiB ROM範囲外です")
    pointer = struct.pack("<I", payload_base)
    expected = struct.pack("<I", MULTICHOICE_TABLE_ADDRESS)
    table_patches = tuple(
        RuntimePatch(
            address=site,
            expected=expected,
            replacement=pointer,
            role="MULTICHOICE_TABLE_EXPANSION_LITERAL",
        )
        for site in MULTICHOICE_TABLE_LITERAL_SITES
    )
    operand_patches = tuple(
        RuntimePatch(
            address=site + 3,
            expected=bytes((source,)),
            replacement=bytes((MULTICHOICE_REMAP[source],)),
            role="MULTICHOICE_CLEAN_SCRIPT_OPERAND_REMAP",
        )
        for source, (site, _expected_sha256) in sorted(
            MULTICHOICE_CLEAN_SCRIPT_SITES.items()
        )
    )
    return MultichoiceRuntimeMaterialization(
        payload_base=payload_base,
        payload=bytes(output),
        table_address=payload_base,
        patches=table_patches + operand_patches,
        source_to_target=dict(MULTICHOICE_REMAP),
        asset_rows=tuple(asset_rows),
    )


def _effect_report(
    root: Path,
    plan: FullCfgRelocationPlan,
    clean_rom: bytes,
    stage60_rom: bytes,
) -> list[dict[str, Any]]:
    names = _special_names(root)
    rows: list[dict[str, Any]] = []
    changed_required_specials: set[int] = set()
    for requirement in plan.effect_requirements:
        if requirement.startswith("OPCODE:"):
            _, opcode, name = requirement.split(":", 2)
            rows.append(
                {
                    "requirement": requirement,
                    "class": "RELOCATED_SCRIPT_OPCODE",
                    "symbol": name,
                    "id": f"0x{int(opcode, 16):02X}",
                    "approval_basis": "RELOCATOR_TYPED_OPERAND_AND_EFFECT_CLASSIFICATION",
                }
            )
        elif requirement.startswith("SPECIAL:"):
            special_id = int(requirement.split(":", 1)[1], 16)
            clean_target = _u32(
                clean_rom, SPECIAL_TABLE_ADDRESS + special_id * 4, "clean special"
            )
            stage_target = _u32(
                stage60_rom, SPECIAL_TABLE_ADDRESS + special_id * 4, "Stage60 special"
            )
            if clean_target != stage_target:
                changed_required_specials.add(special_id)
                if special_id not in SEMANTIC_SPECIAL_REPLACEMENTS:
                    raise Stage61NamespacePolicyError(
                        f"required specialの実装が未監査変更です: {special_id:#04x} "
                        f"{clean_target:#010x}->{stage_target:#010x}"
                    )
                basis = "AUDITED_PROJECT_SEMANTIC_REPLACEMENT"
            else:
                basis = "SPECIAL_TABLE_TARGET_EXACT_IDENTITY"
            rows.append(
                {
                    "requirement": requirement,
                    "class": "SPECIAL_CALL",
                    "symbol": names[special_id],
                    "id": f"0x{special_id:04X}",
                    "clean_target": f"0x{clean_target:08X}",
                    "stage60_target": f"0x{stage_target:08X}",
                    "approval_basis": basis,
                }
            )
        elif requirement.startswith("STANDARD_SCRIPT:"):
            script_id = int(requirement.split(":", 1)[1], 16)
            if not 0 <= script_id < STANDARD_SCRIPT_TABLE_COUNT:
                raise Stage61NamespacePolicyError(
                    f"standard script IDがtable外です: {script_id}"
                )
            clean_target = _u32(
                clean_rom,
                STANDARD_SCRIPT_TABLE_ADDRESS + script_id * 4,
                "clean standard script",
            )
            stage_target = _u32(
                stage60_rom,
                STANDARD_SCRIPT_TABLE_ADDRESS + script_id * 4,
                "Stage60 standard script",
            )
            if clean_target != stage_target:
                raise Stage61NamespacePolicyError(
                    f"standard script ABI不一致: {script_id}"
                )
            rows.append(
                {
                    "requirement": requirement,
                    "class": "STANDARD_SCRIPT_CALL",
                    "symbol": f"STD_SCRIPT_{script_id:02d}",
                    "id": f"0x{script_id:02X}",
                    "target": f"0x{clean_target:08X}",
                    "approval_basis": "STANDARD_SCRIPT_TABLE_TARGET_EXACT_IDENTITY",
                }
            )
        else:
            raise Stage61NamespacePolicyError(
                f"未知のeffect requirementです: {requirement}"
            )
    if changed_required_specials - set(SEMANTIC_SPECIAL_REPLACEMENTS):
        raise Stage61NamespacePolicyError("未監査special replacementがあります")
    return rows


def _identity_mapping(
    plan: FullCfgRelocationPlan, category: str
) -> dict[int | tuple[int, int], int | tuple[int, int]]:
    return {value: value for value in _required_values(plan, category)}


def allocate_stage61_object_visibility_namespace(
    full_cfg: FullCfgRelocationPlan,
    source_visibility_flag_ids: Iterable[int],
    shared_persistent_flag_mapping: Mapping[int, int] | None = None,
) -> dict[int, int]:
    """script共有flagとobject-only flagを一つの衝突しない対応へ束ねる。

    ``source_visibility_flag_ids`` は source object templateから得た数値flagの集合。
    0（非表示条件なし）とtemporary flagはvisibility永続namespaceへ入れない。
    scriptからも参照されるflagはscript namespaceと同じtargetを返す。
    """

    script_sources = sorted(
        {
            int(row.value)
            for row in full_cfg.numeric_references
            if row.category == "flag"
        }
        | set(BILL_VISIBILITY_STATE_IDS)
    )
    if set(script_sources) & TEMP_FLAG_IDS:
        raise Stage61NamespacePolicyError(
            "relocatorがtemporary flag 1/2/3をpersistent flagから分離していません"
        )
    if len(script_sources) != len(ALLOCATABLE_SCRIPT_FLAG_IDS):
        raise Stage61NamespacePolicyError(
            f"persistent script flag件数不一致: {len(script_sources)} "
            f"!= {len(ALLOCATABLE_SCRIPT_FLAG_IDS)}"
        )
    script_mapping = dict(
        zip(script_sources, ALLOCATABLE_SCRIPT_FLAG_IDS, strict=True)
    )
    visibility = {
        int(value) for value in source_visibility_flag_ids
        if int(value) != 0 and int(value) not in TEMP_FLAG_IDS
    }
    special_visibility = sorted(
        value for value in visibility if value in ENGINE_SPECIAL_FLAG_RANGE
    )
    persistent_visibility = visibility - set(special_visibility)
    supplied_shared = {
        int(source): int(target)
        for source, target in (shared_persistent_flag_mapping or {}).items()
    }
    shared = {
        source: target for source, target in supplied_shared.items()
        if source in persistent_visibility
    }
    script_shared = set(shared) & set(script_mapping)
    conflicting_script_shared = {
        source for source in script_shared
        if shared[source] != script_mapping[source]
    }
    if conflicting_script_shared:
        raise Stage61NamespacePolicyError(
            "shared visibility mappingがfull-CFG namespaceと競合します: "
            f"{sorted(conflicting_script_shared)}"
        )
    shared_object_only = set(shared) - set(script_mapping)
    if set(shared.values()) & set(script_mapping.values()):
        raise Stage61NamespacePolicyError(
            "shared visibility targetがfull-CFG targetと衝突します"
        )
    object_only = sorted(
        persistent_visibility - set(script_sources) - shared_object_only
    )
    if len(object_only) > len(OBJECT_ONLY_FLAG_NAMESPACE_RANGE):
        raise Stage61NamespacePolicyError(
            f"object-only visibility flag容量不足: {len(object_only)} "
            f"> {len(OBJECT_ONLY_FLAG_NAMESPACE_RANGE)}"
        )
    object_mapping = dict(
        zip(
            object_only,
            tuple(OBJECT_ONLY_FLAG_NAMESPACE_RANGE)[:len(object_only)],
            strict=True,
        )
    )
    special_mapping = {value: value for value in special_visibility}
    mapping = {**script_mapping, **object_mapping, **shared, **special_mapping}
    persistent_targets = [mapping[value] for value in persistent_visibility]
    if len(persistent_targets) != len(set(persistent_targets)):
        raise Stage61NamespacePolicyError(
            "object visibility persistent target mappingがinjectiveではありません"
        )
    return mapping


def build_stage61_object_visibility_namespace_plan(
    root: Path,
    full_cfg: FullCfgRelocationPlan,
    clean_rom: bytes,
    stage60_rom: bytes,
    shared_persistent_flag_mapping: Mapping[int, int] | None = None,
) -> ObjectVisibilityNamespacePlan:
    """source label・clean record・target recordを三重照合してpatch契約を返す。"""

    root = Path(root)
    ledger = _json(root / "reports/generated/world_runtime_owner_ledger.json")
    if not isinstance(ledger, Mapping) or not isinstance(ledger.get("owner_rows"), list):
        raise Stage61NamespacePolicyError("world owner ledger ABIが不正です")
    owners = [
        row for row in ledger["owner_rows"]
        if isinstance(row, Mapping)
        and row.get("role") == "SOURCE_DIRECT_OBJECT_OWNER"
    ]
    if len(owners) != 469:
        raise Stage61NamespacePolicyError(
            f"SOURCE_DIRECT_OBJECT_OWNER件数不一致: {len(owners)} != 469"
        )

    crosswalk_rows = _csv_rows(root / "reports/generated/kanto_v2_crosswalk.csv")
    target_to_source_name: dict[tuple[int, int], str] = {}
    for row in crosswalk_rows:
        target = (int(row["new_group_id"]), int(row["new_map_id"]))
        source_name = str(row["source_map"])
        previous = target_to_source_name.setdefault(target, source_name)
        if previous != source_name:
            raise Stage61NamespacePolicyError(
                f"target mapが複数sourceへ対応します: {target}"
            )

    groups = _json(root / "vendor/upstream/pokefirered/data/maps/map_groups.json")
    if not isinstance(groups, Mapping) or not isinstance(groups.get("group_order"), list):
        raise Stage61NamespacePolicyError("map_groups.json ABIが不正です")
    source_name_to_pair: dict[str, tuple[int, int]] = {}
    for group, group_name in enumerate(groups["group_order"]):
        maps = groups.get(group_name)
        if not isinstance(maps, list):
            raise Stage61NamespacePolicyError(f"source map groupが配列ではありません: {group_name}")
        for number, source_name in enumerate(maps):
            source_name_to_pair[str(source_name)] = (group, number)

    staged: list[dict[str, Any]] = []
    source_flags: set[int] = set()
    seen_target_sites: set[int] = set()
    for owner in sorted(
        owners,
        key=lambda row: (
            int(row["group"]), int(row["map"]), int(row["index"])
        ),
    ):
        target_pair = (int(owner["group"]), int(owner["map"]))
        source_name = target_to_source_name.get(target_pair)
        if source_name is None or source_name not in source_name_to_pair:
            raise Stage61NamespacePolicyError(
                f"owner targetのsource mapを解決できません: {target_pair}"
            )
        source_pair = source_name_to_pair[source_name]
        target_index = int(owner["index"])
        map_json = _json(root / f"vendor/upstream/pokefirered/data/maps/{source_name}/map.json")
        source_objects = map_json.get("object_events", []) if isinstance(map_json, Mapping) else []
        if not isinstance(source_objects, list):
            raise Stage61NamespacePolicyError(
                f"source map object_eventsが配列ではありません: {source_name}"
            )
        expected_label = str(owner.get("source_script_label", ""))
        owner_x = int(owner["x"])
        owner_y = int(owner["y"])
        source_candidates = [
            (index, row)
            for index, row in enumerate(source_objects)
            if isinstance(row, Mapping)
            and str(row.get("script", "")) == expected_label
            and int(row.get("x", -1)) == owner_x
            and int(row.get("y", -1)) == owner_y
        ]
        if len(source_candidates) != 1:
            raise Stage61NamespacePolicyError(
                f"source objectをlabel+座標で一意に解決できません: "
                f"{source_name} label={expected_label} x={owner_x} y={owner_y} "
                f"candidates={len(source_candidates)}"
            )
        source_index, source_object = source_candidates[0]
        declared_local_id = source_object.get("local_id")
        expected_source_local_id = str(owner.get("source_local_id", ""))
        if (
            expected_source_local_id
            and declared_local_id is not None
            and str(declared_local_id) != expected_source_local_id
        ):
            raise Stage61NamespacePolicyError(
                f"source local label不一致: {source_name}:{source_index}"
            )

        source_record = _object_record_address(clean_rom, *source_pair, source_index)
        source_raw = _rom_bytes(clean_rom, source_record, 24, "clean source object")
        source_x, source_y = struct.unpack_from("<hh", source_raw, 4)
        if (source_x, source_y) != (
            int(source_object["x"]), int(source_object["y"])
        ):
            raise Stage61NamespacePolicyError(
                f"source JSON/clean ROM座標不一致: {source_name}:{source_index} "
                f"ROM=({source_x},{source_y}) JSON="
                f"({source_object['x']},{source_object['y']})"
            )
        source_script = struct.unpack_from("<I", source_raw, 16)[0]
        if source_script != int(owner["source_script_pointer"]):
            raise Stage61NamespacePolicyError(
                f"source script pointer不一致: {source_name}:{source_index} "
                f"{source_script:#010x} != {int(owner['source_script_pointer']):#010x}"
            )
        source_flag = struct.unpack_from("<H", source_raw, 20)[0]
        if source_flag in TEMP_FLAG_IDS:
            raise Stage61NamespacePolicyError(
                f"object visibilityにtemporary flagが使われています: {source_flag}"
            )
        if source_flag:
            source_flags.add(source_flag)

        target_record = _object_record_address(stage60_rom, *target_pair, target_index)
        if target_record in seen_target_sites:
            raise Stage61NamespacePolicyError(
                f"target object recordが重複します: {target_record:#010x}"
            )
        seen_target_sites.add(target_record)
        target_raw = _rom_bytes(stage60_rom, target_record, 24, "Stage60 target object")
        if target_raw[0] != int(owner["local_id"]):
            raise Stage61NamespacePolicyError(
                f"target local ID不一致: {target_pair}:{target_index}"
            )
        target_script = struct.unpack_from("<I", target_raw, 16)[0]
        allowed_target_scripts = {
            int(owner["source_script_pointer"]), int(owner["stage51_script"])
        }
        if target_script not in allowed_target_scripts:
            raise Stage61NamespacePolicyError(
                f"target owner script不一致: {target_pair}:{target_index} "
                f"{target_script:#010x} not in "
                f"{sorted(f'{value:#010x}' for value in allowed_target_scripts)}"
            )
        target_x, target_y = struct.unpack_from("<hh", target_raw, 4)
        if (target_x, target_y) != (owner_x, owner_y):
            raise Stage61NamespacePolicyError(
                f"target owner座標不一致: {target_pair}:{target_index} "
                f"ROM=({target_x},{target_y}) ledger=({owner_x},{owner_y})"
            )
        staged.append(
            {
                "owner_id": (
                    f"OBJECT:{target_pair[0]:03d}/{target_pair[1]:03d}:"
                    f"{target_index:03d}"
                ),
                "source_map": source_name,
                "source_group": source_pair[0],
                "source_map_id": source_pair[1],
                "source_index": source_index,
                "source_local_id_numeric": source_raw[0],
                "source_label": expected_label,
                "source_script_pointer": f"0x{source_script:08X}",
                "source_flag": source_flag,
                "target_group": target_pair[0],
                "target_map": target_pair[1],
                "target_index": target_index,
                "target_record": target_record,
                "target_script_pointer": f"0x{target_script:08X}",
                "target_script_owner": (
                    "SOURCE_DIRECT"
                    if target_script == int(owner["source_script_pointer"])
                    else "STAGE51_ADAPTER"
                ),
                "target_flag_before": struct.unpack_from("<H", target_raw, 20)[0],
            }
        )

    shared = {
        int(source): int(target)
        for source, target in (shared_persistent_flag_mapping or {}).items()
    }
    mapping = allocate_stage61_object_visibility_namespace(
        full_cfg, source_flags, shared
    )
    script_sources = {
        int(row.value) for row in full_cfg.numeric_references if row.category == "flag"
    } | set(BILL_VISIBILITY_STATE_IDS)
    object_only = set(source_flags) - script_sources
    shared_object_only = object_only & set(shared)
    exclusive_object_only = object_only - shared_object_only
    if len(source_flags) != 34 or len(object_only) != 27:
        raise Stage61NamespacePolicyError(
            f"object visibility flag集合不一致: all={len(source_flags)} "
            f"object_only={len(object_only)} (expected 34/27)"
        )

    patches: list[RuntimePatch] = []
    owner_reports: list[dict[str, Any]] = []
    for row in staged:
        source_flag = int(row["source_flag"])
        replacement_flag = 0 if source_flag == 0 else mapping[source_flag]
        site = int(row["target_record"]) + 20
        expected = struct.pack("<H", int(row["target_flag_before"]))
        replacement = struct.pack("<H", replacement_flag)
        patches.append(
            RuntimePatch(
                address=site,
                expected=expected,
                replacement=replacement,
                role="SOURCE_OBJECT_VISIBILITY_FLAG_NAMESPACE",
            )
        )
        owner_reports.append(
            {
                **row,
                "target_record": f"0x{int(row['target_record']):08X}",
                "target_flag_after": replacement_flag,
                "mapping_basis": (
                    "NO_VISIBILITY_FLAG"
                    if source_flag == 0
                    else "SHARED_SCRIPT_FLAG_NAMESPACE"
                    if source_flag in script_sources
                    else "SHARED_TOPOLOGY_FLAG_NAMESPACE"
                    if source_flag in shared_object_only
                    else "OBJECT_ONLY_VISIBILITY_NAMESPACE"
                ),
            }
        )
    assertions = {
        "source_owner_count_469": len(owner_reports) == 469,
        "source_label_exact_match_all": len(owner_reports) == len(owners),
        "target_record_unique_all": len(seen_target_sites) == len(owners),
        "persistent_visibility_flag_count_34": len(source_flags) == 34,
        "object_only_flag_count_27": len(object_only) == 27,
        "shared_and_exclusive_object_visibility_partition_exact": (
            len(shared_object_only) + len(exclusive_object_only)
            == len(object_only)
        ),
        "object_only_target_prefix_exact": {
            mapping[value] for value in exclusive_object_only
        } == set(tuple(OBJECT_ONLY_FLAG_NAMESPACE_RANGE)[:len(exclusive_object_only)]),
        "shared_object_visibility_mapping_exact": {
            value: mapping[value] for value in shared_object_only
        } == {value: shared[value] for value in shared_object_only},
        "patch_preimages_match_stage60": all(
            _rom_bytes(stage60_rom, row.address, len(row.expected), "object patch")
            == row.expected
            for row in patches
        ),
    }
    if not all(assertions.values()):
        raise Stage61NamespacePolicyError(
            "object visibility namespace assertion FAIL: "
            + ", ".join(name for name, passed in assertions.items() if not passed)
        )
    return ObjectVisibilityNamespacePlan(
        source_to_target=mapping,
        patches=tuple(patches),
        owner_rows=tuple(owner_reports),
        assertions=assertions,
    )


def materialize_stage61_missing_object_templates(
    root: Path,
    local_object_plan: LocalObjectNamespacePlan,
    full_cfg_materialization: FullCfgMaterialization,
    clean_rom: bytes,
    stage60_rom: bytes,
    payload_base: int,
    *,
    graphics_id_mapping: Mapping[int, int],
    visibility_flag_mapping: Mapping[int, int],
) -> MissingObjectTemplateMaterialization:
    """Rocket Hideoutの欠落Silph Scope templateを安全に復元する。

    呼出順は次のとおり固定する。

    1. ``build_stage61_namespace_policy`` でpolicy/local planを作る。
    2. そのpolicyでfull CFGをmaterializeする。
    3. 未変更の正確なStage60 ROM、欠落source graphics IDを含む明示
       ``graphics_id_mapping``、object visibility planの ``source_to_target`` を
       この関数へ渡す。``payload_base`` はfull CFGと非重複の4-byte
       境界にする。
    4. 返値payloadを書き込む前に、graphics object patches、semantic
       owner-pointer patches、visibility patchesのうち旧RocketHideout B4F array内
       の全siteを ``rebase_object_address`` で新payload側へ写し、そこで
       expected preimageを検証してreplacementを適用する。
    5. 最後に ``patches`` のcount/pointerをStage60 map event headerへ適用する。

    object arrayを再配置するため、旧recordにだけpatchを当てるのは
    禁止。この順序はAPIの安全性契約である。
    """

    root = Path(root)
    if len(local_object_plan.missing_templates) != 1:
        raise Stage61NamespacePolicyError(
            "missing object materializerは監査済み1 templateだけを扱います"
        )
    requirement = local_object_plan.missing_templates[0]
    if (
        requirement.source_map != "RocketHideout_B4F"
        or requirement.source_script_pointer != SILPH_SCOPE_SOURCE_SCRIPT
        or (requirement.target_group, requirement.target_map)
        != SILPH_SCOPE_TARGET_MAP
        or requirement.target_local_id != SILPH_SCOPE_TARGET_LOCAL_ID
    ):
        raise Stage61NamespacePolicyError(
            "未監査のmissing object templateはmaterializeできません"
        )
    if full_cfg_materialization.clean_sha256 != _sha(clean_rom):
        raise Stage61NamespacePolicyError(
            "full CFG materializationとclean ROM provenanceが不一致です"
        )
    if not all(full_cfg_materialization.verification_assertions.values()):
        raise Stage61NamespacePolicyError(
            "未検証full CFG materializationはmissing templateに接続できません"
        )
    if payload_base % 4 or payload_base < ROM_BASE + len(clean_rom):
        raise Stage61NamespacePolicyError(
            f"missing object payload baseが不正です: {payload_base:#010x}"
        )
    full_start = full_cfg_materialization.payload_base
    full_end = full_start + len(full_cfg_materialization.payload)
    if full_start <= payload_base < full_end:
        raise Stage61NamespacePolicyError(
            "missing object payloadがfull CFG payloadと重なります"
        )

    source_script = _rom_bytes(
        clean_rom,
        SILPH_SCOPE_SOURCE_SCRIPT,
        len(SILPH_SCOPE_SCRIPT_PREIMAGE),
        "Silph Scope source script",
    )
    if source_script != SILPH_SCOPE_SCRIPT_PREIMAGE:
        raise Stage61NamespacePolicyError("Silph Scope source script preimage不一致")
    if requirement.source_record != _rom_bytes(
        clean_rom,
        _object_record_address(
            clean_rom,
            requirement.source_group,
            requirement.source_map_id,
            requirement.source_index,
        ),
        24,
        "Silph Scope source object",
    ):
        raise Stage61NamespacePolicyError("Silph Scope source object preimage不一致")

    event_pointer, object_count, old_array = _event_object_array(
        stage60_rom, requirement.target_group, requirement.target_map
    )
    if object_count != requirement.target_index or object_count != 6:
        raise Stage61NamespacePolicyError(
            f"RocketHideout B4F object count不一致: {object_count} != 6"
        )
    old_array_raw = _rom_bytes(
        stage60_rom, old_array, object_count * 24, "RocketHideout old object array"
    )
    if any(old_array_raw[index * 24] != index + 1 for index in range(object_count)):
        raise Stage61NamespacePolicyError(
            "RocketHideout B4F旧object arrayのlocal IDが非連続です"
        )
    source_x, source_y = struct.unpack_from("<hh", requirement.source_record, 4)
    for index in range(object_count):
        target_x, target_y = struct.unpack_from("<hh", old_array_raw, index * 24 + 4)
        if (target_x, target_y) == (source_x, source_y):
            raise Stage61NamespacePolicyError(
                "Silph Scope座標に既存target objectがあります"
            )

    if requirement.source_graphics_id not in graphics_id_mapping:
        raise Stage61NamespacePolicyError(
            "Silph Scope graphics IDの明示mappingがありません"
        )
    target_graphics = int(graphics_id_mapping[requirement.source_graphics_id])
    if not 0 <= target_graphics <= 0xFF:
        raise Stage61NamespacePolicyError(
            f"Silph Scope target graphics IDが不正です: {target_graphics}"
        )
    if requirement.source_flag not in visibility_flag_mapping:
        raise Stage61NamespacePolicyError(
            "Silph Scope visibility flagの明示mappingがありません"
        )
    target_flag = int(visibility_flag_mapping[requirement.source_flag])
    if not 0 < target_flag <= 0xFFFF:
        raise Stage61NamespacePolicyError(
            f"Silph Scope target flagが不正です: {target_flag}"
        )

    item_rows = _csv_rows(root / "manifests/item_ids.csv")
    all_items = _numeric_index(item_rows, "cfru_id", "id", "item")
    source_item = struct.unpack_from("<H", SILPH_SCOPE_SCRIPT_PREIMAGE, 8)[0]
    if source_item not in all_items:
        raise Stage61NamespacePolicyError(
            f"Silph Scope item manifest mapping不足: {source_item}"
        )
    target_item = all_items[source_item]
    bag_full_target = full_cfg_materialization.instruction_addresses.get(
        BAG_IS_FULL_SOURCE_SCRIPT
    )
    if bag_full_target is None:
        raise Stage61NamespacePolicyError(
            "full CFG payloadにEventScript_BagIsFullがありません"
        )

    adapter = bytearray(SILPH_SCOPE_SCRIPT_PREIMAGE)
    struct.pack_into("<H", adapter, 3, requirement.target_local_id)
    struct.pack_into("<H", adapter, 8, target_item)
    struct.pack_into("<I", adapter, 24, bag_full_target)
    output = bytearray(adapter)
    while len(output) % 4:
        output.append(0xFF)
    object_array_offset = len(output)
    object_array_address = payload_base + object_array_offset
    output.extend(old_array_raw)
    clone = bytearray(requirement.source_record)
    clone[0] = requirement.target_local_id
    clone[1] = target_graphics
    struct.pack_into("<I", clone, 16, payload_base)
    struct.pack_into("<H", clone, 20, target_flag)
    output.extend(clone)
    if payload_base + len(output) > ROM_LIMIT:
        raise Stage61NamespacePolicyError("missing object payloadが32MiB ROM範囲外です")
    payload_end = payload_base + len(output)
    if payload_base < full_end and payload_end > full_start:
        raise Stage61NamespacePolicyError(
            "missing object payloadがfull CFG payloadと重なります"
        )

    patches = (
        RuntimePatch(
            address=event_pointer,
            expected=bytes((object_count,)),
            replacement=bytes((object_count + 1,)),
            role="ROCKET_HIDEOUT_B4F_OBJECT_COUNT_EXPANSION",
        ),
        RuntimePatch(
            address=event_pointer + 4,
            expected=struct.pack("<I", old_array),
            replacement=struct.pack("<I", object_array_address),
            role="ROCKET_HIDEOUT_B4F_OBJECT_ARRAY_RELOCATION",
        ),
    )
    record_mapping = {
        old_array + index * 24: object_array_address + index * 24
        for index in range(object_count)
    }
    assertions = {
        "source_script_exact": bytes(adapter[:2]) == SILPH_SCOPE_SCRIPT_PREIMAGE[:2],
        "source_object_exact": len(requirement.source_record) == 24,
        "existing_six_records_copied_exact": (
            bytes(output[object_array_offset:object_array_offset + len(old_array_raw)])
            == old_array_raw
        ),
        "new_local_id_7": clone[0] == SILPH_SCOPE_TARGET_LOCAL_ID,
        "graphics_namespace_applied": clone[1] == target_graphics,
        "visibility_namespace_applied": struct.unpack_from("<H", clone, 20)[0]
        == target_flag,
        "adapter_pointer_applied": struct.unpack_from("<I", clone, 16)[0]
        == payload_base,
        "bag_full_relocated_pointer_applied": struct.unpack_from("<I", adapter, 24)[0]
        == bag_full_target,
        "header_patch_preimages_match_stage60": all(
            _rom_bytes(stage60_rom, patch.address, len(patch.expected), "header patch")
            == patch.expected
            for patch in patches
        ),
        "all_old_record_addresses_rebasable": len(record_mapping) == object_count,
    }
    if not all(assertions.values()):
        raise Stage61NamespacePolicyError(
            "missing object materialization assertion FAIL: "
            + ", ".join(name for name, passed in assertions.items() if not passed)
        )
    return MissingObjectTemplateMaterialization(
        payload_base=payload_base,
        payload=bytes(output),
        script_address=payload_base,
        object_array_address=object_array_address,
        patches=patches,
        record_address_mapping=record_mapping,
        requirement=requirement,
        verification_assertions=assertions,
    )


def _serializable_mapping(mapping: Mapping[Any, Any]) -> list[dict[str, Any]]:
    def value(item: Any) -> Any:
        return list(item) if isinstance(item, tuple) else item

    return [
        {"source": value(source), "target": value(target)}
        for source, target in sorted(mapping.items(), key=lambda row: repr(row[0]))
    ]


def build_stage61_namespace_policy(
    root: Path,
    full_cfg: FullCfgRelocationPlan,
    clean_rom: bytes,
    stage60_rom: bytes,
    canonical_maps: Sequence[Mapping[str, Any]] | None = None,
    object_visibility_flag_ids: Iterable[int] | None = None,
    shared_object_visibility_flag_mapping: Mapping[int, int] | None = None,
) -> tuple[NamespacePolicy, dict[str, Any]]:
    """実 Stage61 full-CFG を欠損なくmaterializeできるpolicyと監査を返す。"""

    root = Path(root)
    if _sha(clean_rom) != full_cfg.clean_sha256 or len(clean_rom) != full_cfg.clean_size:
        raise Stage61NamespacePolicyError("full CFGとclean ROM provenanceが一致しません")
    if len(stage60_rom) < len(clean_rom):
        raise Stage61NamespacePolicyError("Stage60 ROMがclean ROMより小さいです")
    if full_cfg.unsupported_pointer_references:
        raise Stage61NamespacePolicyError(
            f"unsupported pointerが残っています: {len(full_cfg.unsupported_pointer_references)}"
        )
    special_flag_source_sha256 = _sha(
        (root / ENGINE_SPECIAL_FLAG_CONSTANTS_SOURCE).read_bytes()
    )
    special_flag_consumer_sha256 = _sha(
        (root / ENGINE_SPECIAL_FLAG_CONSUMER_SOURCE).read_bytes()
    )
    if special_flag_source_sha256 != ENGINE_SPECIAL_FLAG_CONSTANTS_SHA256 \
            or special_flag_consumer_sha256 \
            != ENGINE_SPECIAL_FLAG_CONSUMER_SHA256:
        raise Stage61NamespacePolicyError(
            "engine special flag ABI source SHA不一致"
        )
    legacy_temp_flags = sorted(
        {
            int(row.value)
            for row in full_cfg.numeric_references
            if row.category == "flag" and int(row.value) in TEMP_FLAG_IDS
        }
    )
    if legacy_temp_flags:
        raise Stage61NamespacePolicyError(
            "relocatorがtemporary flagをpersistent扱いしています: "
            f"{legacy_temp_flags}"
        )
    engine_system_flag_evidence = _engine_system_flag_contract(
        full_cfg, clean_rom, stage60_rom
    )

    allocation = allocate_kanto_state_namespace(
        full_cfg,
        available_flag_ids=FLAG_NAMESPACE_RANGE,
        available_var_ids=VAR_NAMESPACE_RANGE,
        reserved_flag_ids=ENGINE_SYSTEM_FLAG_SHADOW_TARGETS.values(),
        required_source_flag_ids=BILL_VISIBILITY_STATE_IDS,
        required_source_var_ids={BILL_SCENE_VAR_ID},
    )
    species, species_names = _species_mapping(root, full_cfg)
    items, item_names = _item_mapping(root, full_cfg)
    moves, move_names = _move_mapping(root, full_cfg)
    maps, map_evidence = _map_mapping(root, full_cfg, clean_rom, stage60_rom)
    trainers, trainer_evidence = _trainer_mapping(root, full_cfg)

    # special argumentには通常categoryに現れないspecies 141/142も含まれる。
    species_rows = _csv_rows(root / "manifests/species_ids.csv")
    all_species = _numeric_index(species_rows, "dpe_id", "id", "species")
    special_operand_overrides, special_argument_evidence = _special_argument_overrides(
        full_cfg, all_species
    )
    local_object_plan = build_stage61_local_object_namespace_plan(
        root, full_cfg, clean_rom, stage60_rom
    )
    overlap = set(special_operand_overrides) & set(local_object_plan.operand_overrides)
    if overlap:
        raise Stage61NamespacePolicyError(
            f"operand override categoryが競合します: {sorted(overlap)!r}"
        )
    operand_overrides = {
        **special_operand_overrides,
        **local_object_plan.operand_overrides,
    }
    multichoice_evidence = _validate_multichoice_contract(clean_rom, stage60_rom)
    object_visibility_plan = build_stage61_object_visibility_namespace_plan(
        root, full_cfg, clean_rom, stage60_rom,
        shared_object_visibility_flag_mapping,
    )
    derived_visibility_flags = {
        int(row["source_flag"])
        for row in object_visibility_plan.owner_rows
        if int(row["source_flag"]) != 0
    }
    if object_visibility_flag_ids is not None:
        supplied_visibility_flags = {
            int(value)
            for value in object_visibility_flag_ids
            if int(value) != 0 and int(value) not in TEMP_FLAG_IDS
        }
        if supplied_visibility_flags != derived_visibility_flags:
            raise Stage61NamespacePolicyError(
                "caller指定object visibility flagとowner ledger/clean ROMが不一致です: "
                f"missing={sorted(derived_visibility_flags - supplied_visibility_flags)} "
                f"extra={sorted(supplied_visibility_flags - derived_visibility_flags)}"
            )
    object_visibility_mapping = dict(object_visibility_plan.source_to_target)

    mappings: dict[str, Mapping[Any, Any]] = {
        **allocation.as_policy_mappings(),
        # source root自体はexplicit adapterへ置換するが、volatile engine ABIの
        # identity契約は将来の再導入もfail-closedにするためpolicyへ残す。
        "special_flag": {
            BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID:
                BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID,
        },
        "species": species,
        "item": items,
        "move": moves,
        "map": maps,
        "trainer": trainers,
        "multichoice": {
            int(value): MULTICHOICE_REMAP.get(int(value), int(value))
            for value in _required_values(full_cfg, "multichoice")
        },
    }
    handled_categories = {
        "flag", "var", "species", "item", "move", "map", "trainer",
        "multichoice", "special_argument", "local_object",
    }
    for category in sorted(ABI_IDENTITY_CATEGORIES | MAP_LOCAL_IDENTITY_CATEGORIES):
        if _required_values(full_cfg, category):
            mappings[category] = _identity_mapping(full_cfg, category)
            handled_categories.add(category)

    required_categories = {
        row.category for row in full_cfg.numeric_references if row.mapper_required
    }
    missing_category_policies = sorted(required_categories - handled_categories)
    if missing_category_policies:
        raise Stage61NamespacePolicyError(
            f"未分類mapper-required categoryがあります: {missing_category_policies}"
        )

    effect_rows = _effect_report(root, full_cfg, clean_rom, stage60_rom)
    if len(full_cfg.effect_requirements) != 163 or len(effect_rows) != 163:
        raise Stage61NamespacePolicyError(
            f"Stage61 effect contract件数が変化しました: {len(effect_rows)} != 163"
        )
    policy = NamespacePolicy(
        name="STAGE61_KANTO_FULL_CFG_NAMESPACE_V1",
        mappings=mappings,
        identity_categories=frozenset(),
        operand_overrides=operand_overrides,
        approved_effects=frozenset(full_cfg.effect_requirements),
        pointer_mappings={},
        identity_pointer_categories=frozenset(),
    )
    policy_audit = full_cfg.policy_audit(policy)

    standard_string_values = [
        int(value) for value in _required_values(full_cfg, "standard_string")
    ]
    standard_string_identity = all(
        _rom_bytes(
            clean_rom, STANDARD_STRING_TABLE_ADDRESS + value * 4, 4,
            "clean standard string",
        )
        == _rom_bytes(
            stage60_rom, STANDARD_STRING_TABLE_ADDRESS + value * 4, 4,
            "Stage60 standard string",
        )
        for value in standard_string_values
    )
    assertions = {
        "policy_audit_pass": policy_audit["status"] == "PASS",
        "flag_capacity_exact": (
            len(allocation.flag_mapping) == len(ALLOCATABLE_SCRIPT_FLAG_IDS)
        ),
        "var_capacity_exact": len(allocation.var_mapping) == len(VAR_NAMESPACE_RANGE),
        "flag_targets_exact_range": set(allocation.flag_mapping.values())
        == set(ALLOCATABLE_SCRIPT_FLAG_IDS),
        "engine_system_flags_identity_exact": mappings.get(
            "engine_system_flag", {}
        ) == {0x0805: 0x0805},
        "engine_system_flag_source_set_exact": set(
            _required_values(full_cfg, "engine_system_flag")
        ) == set(ENGINE_SYSTEM_FLAG_IDS),
        "engine_system_flag_script_native_closure_pinned": (
            engine_system_flag_evidence.get("status") == "PASS"
            and len(engine_system_flag_evidence.get("script_sites", [])) == 2
            and len(engine_system_flag_evidence.get("native_sites", [])) == 12
            and engine_system_flag_evidence.get("native_read_count") == 1
            and engine_system_flag_evidence.get("native_clear_count") == 5
        ),
        "engine_system_flag_shadow_0x18b3_is_unallocated": (
            0x18B3 not in set(allocation.flag_mapping.values())
            and 0x18B3 not in set(allocation.flag_mapping)
        ),
        "existing_story_flag_targets_preserved_around_strength_shadow": (
            allocation.flag_mapping.get(0x04B7) == 0x18B2
            and allocation.flag_mapping.get(0x0820) == 0x18B4
        ),
        "engine_special_flags_identity_exact": mappings.get(
            "special_flag", {}
        ) == {
            BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID:
                BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID,
        },
        "engine_special_flags_within_ewram_abi_range": all(
            int(value) in ENGINE_SPECIAL_FLAG_RANGE
            for value in _required_values(full_cfg, "special_flag")
        ),
        "engine_special_flag_source_and_consumer_sha_pinned": (
            special_flag_source_sha256
                == ENGINE_SPECIAL_FLAG_CONSTANTS_SHA256
            and special_flag_consumer_sha256
                == ENGINE_SPECIAL_FLAG_CONSUMER_SHA256
        ),
        "engine_special_flag_full_cfg_source_set_empty": set(
            _required_values(full_cfg, "special_flag")
        ) == set(),
        "engine_special_flag_scope_adapter_identity_reserved": mappings.get(
            "special_flag", {}
        ) == {
            BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID:
                BILL_SUPPRESSED_ENGINE_SPECIAL_FLAG_ID,
        },
        "legacy_0x18c4_guard_is_unallocated": (
            UNALLOCATED_SCRIPT_FLAG_GUARD
            not in set(allocation.flag_mapping.values())
        ),
        "var_targets_exact_range": set(allocation.var_mapping.values())
        == set(VAR_NAMESPACE_RANGE),
        "all_mapper_categories_explicit": not missing_category_policies,
        "no_broad_identity_category": not policy.identity_categories,
        "no_unsupported_pointer": not full_cfg.unsupported_pointer_references,
        "all_effects_machine_approved": len(policy.approved_effects) == 163,
        "all_effect_rows_classified": len(effect_rows) == 163,
        "multichoice_conflicts_isolated": len(multichoice_evidence)
        == len(MULTICHOICE_REMAP),
        "standard_string_targets_exact": standard_string_identity,
        "object_visibility_plan_pass": all(
            object_visibility_plan.assertions.values()
        ),
        "local_object_plan_pass": all(local_object_plan.assertions.values()),
    }
    report = {
        "schema_version": 1,
        "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
        "kind": "STAGE61_FULL_CFG_NAMESPACE_POLICY",
        "status": "PASS" if all(assertions.values()) else "FAIL",
        "policy_name": policy.name,
        "inputs": {
            "clean_sha256": _sha(clean_rom),
            "stage60_sha256": _sha(stage60_rom),
            "canonical_map_record_count": len(canonical_maps or ()),
        },
        "assertions": assertions,
        "policy_audit": policy_audit,
        "state_namespace": allocation.to_report(),
        "reserved_state_namespace": {
            "script_persistent_flags": {
                "start": "0x1847", "end": "0x18C3", "capacity": 125,
                "allocated": len(allocation.flag_mapping),
                "allocatable_ids": len(ALLOCATABLE_SCRIPT_FLAG_IDS),
                "unallocated_holes": ["0x18B3"],
                "allocation_policy": (
                    "SOURCE_FLAG_ASCENDING_EXCLUDING_ENGINE_SYSTEM_FLAG_"
                    "0x0805_AND_ITS_FORMER_SHADOW_0x18B3"
                ),
            },
            "engine_system_flags": {
                **engine_system_flag_evidence,
                "mapping": {"0x0805": "0x0805"},
                "unallocated_shadow_guard": "0x18B3",
            },
            "unallocated_script_flag_guard": {
                "id": "0x18C4",
                "policy": (
                    "RESERVED_EMPTY_GUARD_AGAINST_ENGINE_SPECIAL_FLAG_"
                    "PERSISTENCE_REGRESSION"
                ),
            },
            "engine_special_flags": {
                "source_start": "0x4000", "source_end": "0x407F",
                "used_source_ids": [
                    f"0x{int(value):04X}" for value in _required_values(
                        full_cfg, "special_flag"
                    )
                ],
                "adapter_suppressed_source_ids": ["0x4001"],
                "policy": "IDENTITY_EWRAM_NONPERSISTENT_ABI",
                "source_evidence": [{
                    "path": ENGINE_SPECIAL_FLAG_CONSTANTS_SOURCE.as_posix(),
                    "sha256": special_flag_source_sha256,
                    "definition_lines": "1528-1533",
                    "meaning": "0x4000..0x407F sSpecialFlags EWRAM ABI",
                }, {
                    "path": ENGINE_SPECIAL_FLAG_CONSUMER_SOURCE.as_posix(),
                    "sha256": special_flag_consumer_sha256,
                    "definition_line": 284,
                    "meaning": "GetFlagAddr returns sSpecialFlags byte",
                }],
                "reference_sites": sorted({
                    f"0x{row.source_address:08X}"
                    for row in full_cfg.numeric_references
                    if row.category == "special_flag"
                }),
            },
            "object_only_visibility_flags": {
                "start": "0x18C5", "end": "0x18DF", "capacity": 27,
                "mapping": {
                    f"0x{source:04X}": f"0x{target:04X}"
                    for source, target in sorted(object_visibility_mapping.items())
                    if source not in allocation.flag_mapping
                },
            },
            "persistent_visit_flags": {
                "start": "0x18E0", "end": "0x18FB", "capacity": 28,
            },
            "temporary_flags": {
                "source_ids": [1, 2, 3], "policy": "IDENTITY_MAP_LOAD_CLEAR_ABI",
            },
        },
        "numeric_categories": {
            category: {
                "mapping_count": len(mapping),
                "basis": (
                    "ENGINE_ABI_EXPLICIT_IDENTITY"
                    if category in ABI_IDENTITY_CATEGORIES
                    else "SOURCE_MAP_LOCAL_ID_EXPLICIT_IDENTITY"
                    if category in MAP_LOCAL_IDENTITY_CATEGORIES
                    else "MANIFEST_OR_CROSSWALK_TRANSFORMATION"
                ),
                "mappings": _serializable_mapping(mapping),
            }
            for category, mapping in sorted(mappings.items())
        },
        "manifest_evidence": {
            "species": {
                str(source): {
                    "target": target,
                    "key": species_names.get(source, ""),
                }
                for source, target in sorted(species.items())
            },
            "items": {
                str(source): {"target": target, "key": item_names.get(source, "")}
                for source, target in sorted(items.items())
            },
            "moves": {
                str(source): {"target": target, "key": move_names.get(source, "")}
                for source, target in sorted(moves.items())
            },
            "maps": map_evidence,
            "trainers": trainer_evidence,
        },
        "special_argument_overrides": special_argument_evidence,
        "local_object_namespace": local_object_plan.to_report(),
        "effect_approvals": effect_rows,
        "object_visibility_namespace": object_visibility_plan.to_report(),
        "multichoice_runtime_contract": {
            "status": "REQUIRED",
            "reason": (
                "Stage60既存9 menuを上書きせずclean Kanto menuを"
                "65..73へ増設"
            ),
            "source_table_address": f"0x{MULTICHOICE_TABLE_ADDRESS:08X}",
            "literal_sites": [
                f"0x{value:08X}" for value in MULTICHOICE_TABLE_LITERAL_SITES
            ],
            "source_to_target": {
                str(source): target for source, target in sorted(MULTICHOICE_REMAP.items())
            },
            "rows": multichoice_evidence,
            "materializer": "materialize_multichoice_runtime_contract",
        },
    }
    if report["status"] != "PASS":
        raise Stage61NamespacePolicyError(
            "Stage61 namespace policy assertion FAIL: "
            + ", ".join(name for name, passed in assertions.items() if not passed)
        )
    return policy, report


__all__ = [
    "ALLOCATABLE_SCRIPT_FLAG_IDS",
    "ENGINE_SPECIAL_FLAG_RANGE",
    "ENGINE_SYSTEM_FLAG_IDS",
    "ENGINE_SYSTEM_FLAG_SHADOW_TARGETS",
    "FLAG_NAMESPACE_RANGE",
    "MULTICHOICE_REMAP",
    "LocalObjectNamespacePlan",
    "MissingObjectTemplateMaterialization",
    "MissingObjectTemplateRequirement",
    "MultichoiceRuntimeMaterialization",
    "OBJECT_ONLY_FLAG_NAMESPACE_RANGE",
    "ObjectVisibilityNamespacePlan",
    "RuntimePatch",
    "Stage61NamespacePolicyError",
    "TEMP_FLAG_IDS",
    "UNALLOCATED_SCRIPT_FLAG_GUARD",
    "VAR_NAMESPACE_RANGE",
    "VISIT_FLAG_NAMESPACE_RANGE",
    "allocate_stage61_object_visibility_namespace",
    "build_stage61_local_object_namespace_plan",
    "build_stage61_object_visibility_namespace_plan",
    "build_stage61_namespace_policy",
    "materialize_multichoice_runtime_contract",
    "materialize_stage61_missing_object_templates",
]
