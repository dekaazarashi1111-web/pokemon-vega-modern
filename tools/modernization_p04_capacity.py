#!/usr/bin/env python3
"""工程4/5の追加ID予約とruntime consumer容量を決定的に監査する。

このmoduleはROM、save、共有manifest、allocation ledgerを変更しない。工程1の
exact-ROM容量監査、工程4の公式候補・素材監査、工程5のMove/Ability要件を結合し、
後続工程が採番を再解釈せずに使える予約checkpointを作る。
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence

from tools.modernization_capacity import (
    CapacityAuditError,
    build_modernization_capacity_audit,
    require_pass as require_capacity_pass,
)


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P04-CAPACITY-RESERVATION"
CHECKPOINT_STATUS = "CHECKPOINT_NOT_RUNTIME_READY"
DEFAULT_OUTPUT = Path("content/modernization/p04_capacity_allocation_manifest.json")
ROM_BASE = 0x08000000
U16_MAX = 0xFFFF

P04_CANDIDATES = Path("content/modernization/p04_candidate_manifest.json")
P04_ASSETS = Path("content/modernization/p04_asset_import_manifest.json")
P05_CONTRACT = Path("content/modernization/p05_battle_content_contract.json")
P05_HANDOFF = Path("content/modernization/p05_runtime_handoff.json")
STAGE65_ROM = Path("build/stages/65_modernization_p03_caterpie_slice.gba")
STAGE65_METADATA = Path("build/stages/65_modernization_p03_caterpie_slice.json")
STAGE65_ALLOCATION = Path("build/stages/65_modernization_p03_allocation.json")
STAGE56_ROM = Path("build/stages/56_collection_supply_v1.gba")
STAGE09_METADATA = Path("build/stages/09_species_surface.json")
STAGE39_METADATA = Path("build/stages/39_move_distribution_v4.json")
STAGE61_HOTFIX = Path("generated/runtime/stage61_runtime_hotfix_tables.json")
CFRU_OFFSETS = Path(
    "build/battle-core/"
    "a356f976cfbb991d5768d8000e9863d3f2b6ba9d10fa27d799bea3c158dba7fa/"
    "run-1/offsets.ini"
)
CFRU_SOURCE = Path("vendor/upstream/CFRU-JP")
CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"

# 上流契約を更新する場合は、差分監査の上でこのpinも明示更新する。単に現在の
# fileを読み直して採番が動くことを許さない。
PINNED_SHA256 = {
    P04_CANDIDATES.as_posix():
        "64e9ffbc80a4344eef82726c191da25b008c6f7d87312c2bf8186c00a36c5644",
    P04_ASSETS.as_posix():
        "107f6830b0faf4c3372a872c2f91f6945145ad7503f17f64c4dd1d17c5168235",
    P05_CONTRACT.as_posix():
        "2fcf0c75a4424325e4e6418ba7726e7978d143dd5d4bfc4e7652cb25e1295ef3",
    P05_HANDOFF.as_posix():
        "36326ff9ab43ff26767513be0e7e175cb1a11f7cfb95363108e06a32a70e3cc0",
}

EXPECTED_STAGE65_SHA256 = (
    "116781c8be7cbd327ba7783ebdad9d9dda77554c33839eebed15ae6b065bb680"
)
EXPECTED_STAGE65_SIZE = 32 * 1024 * 1024

PINNED_LOCAL_INPUT_SHA256 = {
    STAGE65_ALLOCATION.as_posix():
        "7393007cfb6ed0f5d6f9264b60f8b73c1fdd5454ce767b1cdfb7cf268c867e18",
    STAGE09_METADATA.as_posix():
        "e44db6be50a2bb82c3d53ab7a3327446f0729d8d43414bd3ea6e275a6cd5b6f8",
    STAGE39_METADATA.as_posix():
        "c39a7903d1801c791fae6f983f766a8a4a009e6d3c360bfa3ca533290b9527b3",
    STAGE61_HOTFIX.as_posix():
        "85927fb2fd5249046a93ef575a3e2560160691745d8e019aee129e9287b2d91a",
    CFRU_OFFSETS.as_posix():
        "f9851fb5eea759573d1e4e0b923e69c34c85ddb171fb03321f5b7ce380870523",
    "config/save_layout.csv":
        "1f84b47301f5e2b45b612c5a8e1009ec7c1932407d8050081ca290ce3423cb98",
}
EXPECTED_STAGE65_METADATA_CONTRACT_SHA256 = (
    "0dbd943c86b4ef0228ad1348ffc3aa89460a22a7c42ebf846283ce015900b6fa"
)

# Stage06 metadataが公開していないものの、同じID countで添字アクセスされる
# live CFRU表。offsets.iniのsymbolとStage65 exact ROM sliceを二重に照合する。
ANCILLARY_TABLE_SPECS = {
    "move_dynamax_powers": {
        "symbol": "gDynamaxMovePowers",
        "domain": "move",
        "address": 0x0914CA68,
        "old_count": 1063,
        "new_count": 1064,
        "stride": 1,
        "sha256": "69824572e19fca15799b58a8aa32e41566db94317f50dc3cc76146ee25048434",
    },
    "ability_ratings": {
        "symbol": "gAbilityRatings",
        "domain": "ability",
        "address": 0x0915F8B4,
        "old_count": 312,
        "new_count": 318,
        "stride": 1,
        "sha256": "d0c9a32f764f5a6858ee4cd36bca2601d10d8fe7db7d75d51cc88682240cf3cf",
    },
    "ability_mold_breaker_ignored": {
        "symbol": "gMoldBreakerIgnoredAbilities",
        "domain": "ability",
        "address": 0x0915F77C,
        "old_count": 312,
        "new_count": 318,
        "stride": 1,
        "sha256": "4296ce4fb1a4107a4c137de646a94740169013be4c2c2b3f742b73e2f2ec02de",
        "extent_end_address": 0x0915F8B4,
        "extent_next_symbol": "gAbilityRatings",
    },
    "item_type_by_id": {
        "symbol": "gItemsByType",
        "domain": "item",
        "address": 0x0915A984,
        "old_count": 999,
        "new_count": 1044,
        "stride": 2,
        "sha256": "22e768b0dc9bdcf259936a3ce4fa3aee77359c26d42a14855f49589bc7769d9e",
    },
    "item_fling": {
        "symbol": "gFlingTable",
        "domain": "item",
        "address": 0x0915B198,
        "old_count": 999,
        "new_count": 1044,
        "stride": 2,
        "sha256": "4181cebbafe6f747408123c63e2c50b7c80ca5d50aa8b1305dbe066035e7937f",
    },
    "item_effect_pointer2": {
        "symbol": "gItemEffectTable2",
        "domain": "item",
        "address": 0x0915B9D0,
        "old_count": 999,
        "new_count": 1044,
        "stride": 4,
        "sha256": "a8d4c36bad4fccd73297b70b73008e31cccef86f08824f44035acb86bbe1a77a",
    },
}

ANCILLARY_SOURCE_DEFINITIONS = {
    "gDynamaxMovePowers": "src/Tables/battle_moves.c",
    "gAbilityRatings": "src/ability_battle_effects.c",
    "gMoldBreakerIgnoredAbilities": "src/ability_battle_effects.c",
    "gItemsByType": "src/Tables/item_tables.c",
    "gFlingTable": "src/Tables/item_tables.c",
    "gItemEffectTable2": "include/new/item_effects.h",
}

BITFIELD_CONSUMER_PATTERNS = (
    {
        "field": "CodexBattlePublicEventV2.last_item_id",
        "path": "scripts/build_codex_battle_runtime.py",
        "pattern": r'\{"name":\s*"last_item_id",\s*"bits":\s*10\}',
        "declared_bits": 10,
    },
    {
        "field": "CodexBattlePublicEventV2.last_item_id",
        "path": "overlays/codex_battle_runtime/codex_battle_runtime.c",
        "pattern": r"pack_bits\(event->packed,\s*31u,\s*last_item,\s*10u\)",
        "declared_bits": 10,
    },
    {
        "field": "MirageProduction_Probe.virtual_items_packed",
        "path": "overlays/mirage_production/mirage_production.c",
        "pattern": r"virtual_items\[[012]\]\s*&\s*0x3FFu",
        "declared_bits": 10,
        "expected_occurrences": 3,
    },
    {
        "field": "BattlePokemon.oldAbility",
        "path": "vendor/upstream/CFRU-JP/include/pokemon.h",
        "pattern": r"\bu8\s+oldAbility\s*;",
        "declared_bits": 8,
        "required_max": 317,
        "source_status": "DECLARED_BUT_NO_DIRECT_SOURCE_REFERENCE_FOUND",
    },
    {
        "field": "BattleStruct.abilityPreventingSwitchout",
        "path": "vendor/upstream/CFRU-JP/include/battle.h",
        "pattern": r"\bu8\s+abilityPreventingSwitchout\s*;",
        "declared_bits": 8,
        "required_max": 317,
        "source_status": "LEGACY_STRUCT_DECLARATION",
    },
    {
        "field": "NewBattleStruct.abilityPreventingSwitchout",
        "path": "vendor/upstream/CFRU-JP/include/battle.h",
        "pattern": r"\bu16\s+abilityPreventingSwitchout\s*;",
        "declared_bits": 16,
        "required_max": 317,
        "source_status": "ACTIVE_GNEWBS_FIELD",
    },
    {
        "field": "AbilityBattleEffects.ability",
        "path": "vendor/upstream/CFRU-JP/src/ability_battle_effects.c",
        "pattern": r"AbilityBattleEffects\(u8\s+caseID,\s*u8\s+bank,\s*u16\s+ability,",
        "declared_bits": 16,
        "required_max": 317,
        "source_status": "ACTIVE_IMPLEMENTATION_SIGNATURE",
    },
)

MANIFEST_SPACES = {
    "species_form": {
        "path": "manifests/species_ids.csv",
        "key_field": "species_key",
        "current_count": 1621,
        "current_max_id": 1620,
        "append_count": 52,
    },
    "move": {
        "path": "manifests/move_ids.csv",
        "key_field": "move_key",
        "current_count": 1063,
        "current_max_id": 1062,
        "append_count": 1,
    },
    "ability": {
        "path": "manifests/ability_ids.csv",
        "key_field": "ability_key",
        "current_count": 312,
        "current_max_id": 311,
        "append_count": 6,
    },
    "item": {
        "path": "manifests/item_ids.csv",
        "key_field": "item_key",
        "current_count": 999,
        "current_max_id": 998,
        "append_count": 45,
    },
}

EXPECTED_NEW_ABILITY_KEYS = frozenset(
    {
        "ABILITY_KEY_DRAGONIZE",
        "ABILITY_KEY_EELEVATE",
        "ABILITY_KEY_FIREMANE",
        "ABILITY_KEY_MEGASOL",
        "ABILITY_KEY_PIERCINGDRILL",
        "ABILITY_KEY_SPICYSPRAY",
    }
)

CLASS_SIMPLE = "SIMPLE_APPEND"
CLASS_ENGINE = "ENGINE_PATCH_REQUIRED"
CLASS_SAVE = "SAVE_DESIGN_REQUIRED"

# 固定値consumerの探索範囲。build/generated/content/testsは結果・fixtureであり、
# runtime/source consumerの発見対象には含めない。
SOURCE_SCAN_ROOTS = (
    "config",
    "overlays",
    "scripts",
    "tools",
    "vendor/upstream/CFRU-JP",
    "vendor/vega_acquisition",
)
SOURCE_SCAN_SUFFIXES = frozenset({".c", ".h", ".py", ".json"})
SOURCE_SCAN_EXCLUDED_PREFIXES = (
    "tools/modernization_p04_capacity.py",
    "scripts/build_modernization_p04_capacity.py",
    # downstreamの統合台帳は容量監査結果をpinするため、consumer入力へ戻すと
    # 自己参照で件数が変動する。runtime consumerではないので明示除外する。
    "tools/modernization_p08_integration.py",
    "scripts/build_modernization_p08.py",
)

BOUNDARY_VALUES = {
    "species_form": {1621: "CURRENT_COUNT_OR_NEXT_ID", 1620: "CURRENT_MAX_ID"},
    "move": {1063: "CURRENT_COUNT_OR_NEXT_ID", 1062: "CURRENT_MAX_ID"},
    "ability": {312: "CURRENT_COUNT_OR_NEXT_ID", 311: "CURRENT_MAX_ID"},
    "item": {999: "CURRENT_COUNT_OR_NEXT_ID", 998: "CURRENT_MAX_ID"},
}

DOMAIN_TEXT = {
    "species_form": re.compile(r"species|pokemon|pok[eé]mon|canonical[_ ]?mon", re.I),
    "move": re.compile(r"move", re.I),
    "ability": re.compile(r"abilit", re.I),
    "item": re.compile(r"item|inventory|bag", re.I),
}
BOUNDARY_CONTEXT = re.compile(
    r"count|max|last|capacity|range|rows?|entries|bound|namespace|canonical|"
    r"manifest|limit|len\s*\(|list\s*\(|\[[^\]]*\]|<=|>=|==|!=|<|>",
    re.I,
)

REQUIRED_CONSUMER_ANCHORS = {
    "species_form": {
        "config/species_surface.json",
        "config/move_distribution_v4.json",
        "scripts/build_codex_battle_runtime.py",
        "tools/modernization_identity.py",
        "vendor/vega_acquisition/generated/acquisition_collection_defs.h",
    },
    "move": {
        "config/battle_core.json",
        "config/move_distribution_v4.json",
        "overlays/cfru/runtime.h",
        "scripts/build_codex_battle_runtime.py",
        "tools/modernization_identity.py",
    },
    "ability": {
        "config/battle_core.json",
        "overlays/cfru/runtime.h",
        "scripts/build_codex_battle_runtime.py",
        "tools/modernization_identity.py",
    },
    "item": {
        "config/battle_core.json",
        "overlays/cfru/runtime.h",
        "overlays/save_migration/save_migration.h",
        "scripts/build_codex_battle_runtime.py",
        "tools/modernization_identity.py",
    },
}


class P04CapacityError(ValueError):
    """ID予約または容量証跡を安全に確定できない場合の例外。"""


def _fail(message: str) -> NoReturn:
    raise P04CapacityError(message)


def canonical_json_bytes(value: Any) -> bytes:
    """順序と改行を固定したJSON byte列を返す。"""

    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular_file(root: Path, relative: str | Path, label: str) -> bytes:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常fileではありません: {relative}")
    try:
        return path.read_bytes()
    except OSError as exc:
        _fail(f"{label}を読めません: {relative}: {exc}")


def _identity(root: Path, relative: str | Path, label: str) -> dict[str, Any]:
    raw = _regular_file(root, relative, label)
    return {
        "path": Path(relative).as_posix(),
        "size": len(raw),
        "sha256": _sha256(raw),
    }


def _pinned_local_identity(
    root: Path, relative: str | Path, label: str
) -> dict[str, Any]:
    identity = _identity(root, relative, label)
    expected = PINNED_LOCAL_INPUT_SHA256.get(Path(relative).as_posix())
    if not expected or identity["sha256"] != expected:
        _fail(
            f"{label}のlocal pinが不一致です: expected={expected}, "
            f"actual={identity['sha256']}"
        )
    identity["pin_status"] = "MATCH"
    return identity


def _json(root: Path, relative: str | Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    identity = _identity(root, relative, label)
    raw = _regular_file(root, relative, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"{label}がUTF-8 JSONではありません: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label}のrootはobject必須です")
    return value, identity


def _pinned_json(
    root: Path, relative: Path, label: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    value, identity = _json(root, relative, label)
    expected = PINNED_SHA256.get(relative.as_posix())
    if not expected or identity["sha256"] != expected:
        _fail(
            f"{label}のpinが不一致です: expected={expected}, "
            f"actual={identity['sha256']}"
        )
    identity["pin_status"] = "MATCH"
    return value, identity


def _stage65_metadata_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    """再生成時の非本質証跡を除いたStage65 semantic contractを返す。"""

    return {
        "schema_version": value.get("schema_version"),
        "task": value.get("task"),
        "stage": value.get("stage"),
        "status": value.get("status"),
        "checkpoint_marker": value.get("checkpoint_marker"),
        "done": value.get("done"),
        "output": {
            key: value.get("output", {}).get(key)
            for key in ("path", "size", "sha256")
        },
        "allocation": {
            key: value.get("allocation", {}).get(key)
            for key in (
                "path", "size", "sha256", "remaining_allocatable_bytes",
                "added_allocations", "added_bytes",
            )
        },
        "scope": {
            key: value.get("scope", {}).get(key)
            for key in (
                "active_play_baseline_changed", "move_ids_changed",
                "species_ids_changed", "save_layout_changed",
                "existing_party_box_save_rewritten",
            )
        },
        "acceptance": {
            key: value.get("acceptance", {}).get(key)
            for key in (
                "allocation_gate", "manifest_identity_gate", "parent_preimage_gate",
                "static_contract_gate", "task_completion",
            )
        },
    }


def _csv_rows(
    root: Path, relative: str | Path, label: str
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    identity = _identity(root, relative, label)
    raw = _regular_file(root, relative, label)
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(text.splitlines())
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        _fail(f"{label}をCSVとして読めません: {exc}")
    if not reader.fieldnames or not rows:
        _fail(f"{label}が空です")
    return rows, identity


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}は整数必須です: {value!r}")
    try:
        result = int(value)
    except (TypeError, ValueError):
        _fail(f"{label}は整数必須です: {value!r}")
    if not isinstance(value, int) and str(result) != str(value):
        _fail(f"{label}は正規10進整数必須です: {value!r}")
    return result


def _require_unique(values: Sequence[str], label: str) -> None:
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if not values or any(not value for value in values) or duplicates:
        _fail(f"{label}が空または重複しています: {duplicates}")


def _manifest_inventory(
    rows: Sequence[Mapping[str, Any]], *, key_field: str, expected_count: int, label: str
) -> dict[str, Any]:
    keys = [str(row.get(key_field, "")).strip() for row in rows]
    ids = [_integer(row.get("id"), f"{label} id") for row in rows]
    _require_unique(keys, f"{label} key")
    if len(rows) != expected_count or ids != list(range(expected_count)):
        _fail(f"{label}は0..{expected_count - 1}の連続表ではありません")
    return {
        "row_count": len(rows),
        "minimum_id": ids[0],
        "maximum_id": ids[-1],
        "contiguous_zero_based": True,
        "key_count": len(keys),
        "keys": frozenset(keys),
    }


def allocate_append_ids(
    existing_rows: Sequence[Mapping[str, Any]],
    requested_rows: Sequence[Mapping[str, Any]],
    *,
    key_field: str,
    expected_current_count: int,
    maximum_id: int = U16_MAX,
) -> list[dict[str, Any]]:
    """既存連続IDの末尾へstable keyを純粋関数として予約する。"""

    current = _manifest_inventory(
        existing_rows,
        key_field=key_field,
        expected_count=expected_current_count,
        label=key_field,
    )
    requested_keys = [str(row.get(key_field, "")).strip() for row in requested_rows]
    _require_unique(requested_keys, f"追加{key_field}")
    collisions = sorted(current["keys"].intersection(requested_keys))
    if collisions:
        _fail(f"既存{key_field}とのkey衝突です: {collisions}")
    last_id = expected_current_count + len(requested_rows) - 1
    if last_id > maximum_id:
        _fail(
            f"{key_field}追加IDが上限を超えます: last={last_id}, max={maximum_id}"
        )
    result: list[dict[str, Any]] = []
    for offset, source in enumerate(requested_rows):
        row = dict(source)
        row["id"] = expected_current_count + offset
        row["id_hex"] = f"0x{row['id']:04X}"
        row["reservation_status"] = CHECKPOINT_STATUS
        result.append(row)
    return result


def materialize_reserved_id_rows(
    existing_rows: Sequence[Mapping[str, Any]],
    reservations: Sequence[Mapping[str, Any]],
    *,
    key_field: str,
) -> list[dict[str, Any]]:
    """共有manifest候補を変更せず、最小ID行へ射影する純粋関数。

    返値は正本manifestへの直接書込みを意味しない。後続工程は各manifest固有の
    必須contentを補い、checkpointのruntime gateを全て閉じてから採用する。
    """

    output = [dict(row) for row in existing_rows]
    existing_keys = {str(row.get(key_field, "")) for row in output}
    existing_ids = {_integer(row.get("id"), f"既存{key_field} id") for row in output}
    for reservation in reservations:
        key = str(reservation.get(key_field, "")).strip()
        identifier = _integer(reservation.get("id"), f"予約{key_field} id")
        if not key or key in existing_keys or identifier in existing_ids:
            _fail(f"materialize時の{key_field}/ID衝突です: {key}/{identifier}")
        output.append(
            {
                key_field: key,
                "id": str(identifier),
                "status": "RESERVED_NOT_RUNTIME_READY",
                "source_record_key": str(reservation.get("source_record_key", "")),
            }
        )
        existing_keys.add(key)
        existing_ids.add(identifier)
    ids = [_integer(row.get("id"), f"materialized {key_field} id") for row in output]
    if ids != list(range(len(ids))):
        _fail(f"materialize後の{key_field} IDが連続ではありません")
    return output


def _tracked_source_paths(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", *SOURCE_SCAN_ROOTS],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        _fail(f"tracked consumer一覧を取得できません: {detail!r}: {exc}")
    paths = [raw.decode("utf-8") for raw in completed.stdout.split(b"\0") if raw]
    output = []
    for relative in paths:
        if relative.startswith(SOURCE_SCAN_EXCLUDED_PREFIXES):
            continue
        if Path(relative).suffix.lower() not in SOURCE_SCAN_SUFFIXES:
            continue
        output.append(relative)
    return sorted(output)


def _json_scalar_rows(
    value: Any, *, relative: str, path: tuple[str, ...] = ()
) -> Iterable[tuple[str, int]]:
    if isinstance(value, dict):
        for key in sorted(value):
            yield from _json_scalar_rows(
                value[key], relative=relative, path=(*path, str(key))
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _json_scalar_rows(
                child, relative=relative, path=(*path, f"[{index}]")
            )
    elif isinstance(value, int) and not isinstance(value, bool):
        yield ".".join(path), value


def audit_hardcoded_consumers(root: Path) -> dict[str, Any]:
    """tracked source/configの現行count/max境界をscope内でfail closedに列挙する。"""

    root = root.resolve()
    rows: list[dict[str, Any]] = []
    scanned = _tracked_source_paths(root)
    for relative in scanned:
        raw = _regular_file(root, relative, "consumer scan source")
        if Path(relative).suffix.lower() == ".json":
            try:
                value = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                _fail(f"consumer scan対象JSONが不正です: {relative}: {exc}")
            for json_path, number in _json_scalar_rows(value, relative=relative):
                context = json_path.lower()
                for domain, boundaries in BOUNDARY_VALUES.items():
                    if number not in boundaries or not DOMAIN_TEXT[domain].search(context):
                        continue
                    if not BOUNDARY_CONTEXT.search(context):
                        continue
                    rows.append(
                        {
                            "domain": domain,
                            "boundary_kind": boundaries[number],
                            "value": number,
                            "path": relative,
                            "locator": json_path,
                            "source_kind": "JSON_SCALAR",
                            "evidence_sha256": _sha256(
                                f"{relative}\0{json_path}\0{number}".encode("utf-8")
                            ),
                        }
                    )
            continue

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            _fail(f"consumer scan対象sourceがUTF-8ではありません: {relative}: {exc}")
        for line_number, line in enumerate(text.splitlines(), 1):
            if not BOUNDARY_CONTEXT.search(line):
                continue
            for domain, boundaries in BOUNDARY_VALUES.items():
                if not DOMAIN_TEXT[domain].search(line):
                    continue
                for number, kind in boundaries.items():
                    pattern = re.compile(
                        rf"(?<![0-9A-Za-z_]){number}(?:[uUlL]+)?(?![0-9A-Za-z_])"
                    )
                    if not pattern.search(line):
                        continue
                    excerpt = line.strip()
                    rows.append(
                        {
                            "domain": domain,
                            "boundary_kind": kind,
                            "value": number,
                            "path": relative,
                            "locator": f"line:{line_number}",
                            "source_kind": "SOURCE_LINE",
                            "excerpt": excerpt[:240],
                            "evidence_sha256": _sha256(
                                f"{relative}\0{line_number}\0{line}".encode("utf-8")
                            ),
                        }
                    )
    rows.sort(
        key=lambda row: (
            row["domain"], row["path"], row["locator"], row["value"]
        )
    )
    if not rows:
        _fail("hard-coded consumer scanが0件です")
    paths_by_domain = {
        domain: sorted({row["path"] for row in rows if row["domain"] == domain})
        for domain in BOUNDARY_VALUES
    }
    missing_anchors = {
        domain: sorted(REQUIRED_CONSUMER_ANCHORS[domain] - set(paths_by_domain[domain]))
        for domain in BOUNDARY_VALUES
    }
    missing_anchors = {key: value for key, value in missing_anchors.items() if value}
    if missing_anchors:
        _fail(f"必須hard-coded consumer anchorを発見できません: {missing_anchors}")
    fingerprint_payload = [
        {
            key: row[key]
            for key in (
                "domain",
                "boundary_kind",
                "value",
                "path",
                "locator",
                "evidence_sha256",
            )
        }
        for row in rows
    ]
    counts = Counter(row["domain"] for row in rows)
    return {
        "scope": {
            "tracked_files_only": True,
            "roots": list(SOURCE_SCAN_ROOTS),
            "suffixes": sorted(SOURCE_SCAN_SUFFIXES),
            "excluded_prefixes": list(SOURCE_SCAN_EXCLUDED_PREFIXES),
            "scanned_file_count": len(scanned),
            "completeness_claim": "SCOPED_FAIL_CLOSED_NOT_GLOBAL_STATIC_PROOF",
        },
        "match_count": len(rows),
        "counts_by_domain": dict(sorted(counts.items())),
        "paths_by_domain": paths_by_domain,
        "required_anchor_status": "PASS",
        "inventory_sha256": _sha256(canonical_json_bytes(fingerprint_payload)),
        "rows": rows,
    }


def _git_text(root: Path, arguments: Sequence[str], label: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "")
        _fail(f"{label}を取得できません: {detail!r}: {exc}")
    return completed.stdout


def _git_bytes(root: Path, arguments: Sequence[str], label: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        _fail(f"{label}を取得できません: {detail!r}: {exc}")
    return completed.stdout


def audit_ancillary_source_consumers(root: Path) -> dict[str, Any]:
    """pin済CFRU source内の補助表定義と直接参照を別枠で列挙する。"""

    source_root = (root / CFRU_SOURCE).resolve()
    if not source_root.is_dir() or source_root.is_symlink():
        _fail("CFRU source rootが通常directoryではありません")
    head = _git_text(source_root, ["rev-parse", "HEAD"], "CFRU HEAD").strip()
    if head != CFRU_COMMIT:
        _fail(f"CFRU source commitが不一致です: {head}")
    tree_paths = _git_text(
        source_root,
        ["ls-tree", "-r", "--name-only", CFRU_COMMIT],
        "CFRU pinned tree paths",
    ).splitlines()
    candidates = sorted(
        relative for relative in tree_paths
        if Path(relative).suffix.lower() in {".c", ".h"}
    )
    if not candidates:
        _fail("CFRU source consumer探索対象が0件です")
    combined_pattern = "|".join(
        re.escape(symbol) for symbol in sorted(ANCILLARY_SOURCE_DEFINITIONS)
    )
    grep_output = _git_text(
        source_root,
        [
            "grep", "-l", "-E", combined_pattern, CFRU_COMMIT,
            "--", "*.c", "*.h",
        ],
        "CFRU pinned ancillary symbol paths",
    )
    relevant_paths = sorted(
        line.split(":", 1)[1] if line.startswith(f"{CFRU_COMMIT}:") else line
        for line in grep_output.splitlines()
        if line
    )
    relevant_blobs = {
        relative: _git_bytes(
            source_root,
            ["show", f"{CFRU_COMMIT}:{relative}"],
            f"CFRU pinned blob {relative}",
        )
        for relative in relevant_paths
    }

    by_symbol: dict[str, Any] = {}
    all_fingerprint_rows: list[dict[str, Any]] = []
    for symbol, definition_path in sorted(ANCILLARY_SOURCE_DEFINITIONS.items()):
        pattern = re.compile(rf"\b{re.escape(symbol)}\b")
        occurrences: list[dict[str, Any]] = []
        for relative, raw in relevant_blobs.items():
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            lines = [
                number for number, line in enumerate(text.splitlines(), 1)
                if pattern.search(line)
            ]
            if not lines:
                continue
            row = {
                "path": relative,
                "line_numbers": lines,
                "line_occurrence_count": len(lines),
                "file_sha256": _sha256(raw),
            }
            occurrences.append(row)
            all_fingerprint_rows.append({"symbol": symbol, **row})
        if not occurrences:
            _fail(f"CFRU ancillary symbol参照がありません: {symbol}")
        definition = next(
            (row for row in occurrences if row["path"] == definition_path), None
        )
        if definition is None:
            _fail(f"CFRU ancillary定義fileが見つかりません: {symbol}")
        definition_raw = _git_bytes(
            source_root,
            ["show", f"{CFRU_COMMIT}:{definition_path}"],
            f"CFRU pinned {symbol} definition",
        )
        definition_text = definition_raw.decode("utf-8")
        count_macro = {
            "gDynamaxMovePowers": "MOVES_COUNT",
            "gAbilityRatings": "ABILITIES_COUNT",
            "gMoldBreakerIgnoredAbilities": None,
            "gItemsByType": "ITEMS_COUNT",
            "gFlingTable": "ITEMS_COUNT",
            "gItemEffectTable2": "ITEMS_COUNT",
        }[symbol]
        if count_macro is None:
            if not re.search(
                rf"\b{re.escape(symbol)}\s*\[\s*\]\s*=",
                definition_text,
            ):
                _fail(f"CFRU ancillary implicit配列ではありません: {symbol}")
            count_contract = "IMPLICIT_DESIGNATED_INDEX_COMPILED_EXTENT"
        else:
            if not re.search(
                rf"\b{re.escape(symbol)}\s*\[\s*{count_macro}\s*\]",
                definition_text,
            ):
                _fail(f"CFRU ancillary定義が{count_macro}配列ではありません: {symbol}")
            count_contract = count_macro
        by_symbol[symbol] = {
            "definition_path": definition_path,
            "count_macro": count_macro,
            "count_contract": count_contract,
            "source_file_count": len(occurrences),
            "source_line_occurrence_count": sum(
                row["line_occurrence_count"] for row in occurrences
            ),
            "definition_confirmed": True,
            "occurrences": occurrences,
        }
    return {
        "source_root": CFRU_SOURCE.as_posix(),
        "source_lock_commit": CFRU_COMMIT,
        "actual_commit": head,
        "commit_matches": True,
        "working_tree_bytes_ignored": True,
        "snapshot_read_via": "git show <pinned-commit>:<path>",
        "compiled_identity_source": CFRU_OFFSETS.as_posix(),
        "candidate_c_h_file_count": len(candidates),
        "matched_source_file_count": len(relevant_paths),
        "symbols": by_symbol,
        "inventory_sha256": _sha256(canonical_json_bytes(all_fingerprint_rows)),
        "completeness_claim": "PINNED_SOURCE_DIRECT_SYMBOL_SCOPE_NOT_GLOBAL_CALL_GRAPH",
    }


def audit_cfru_count_macro_consumers(root: Path) -> dict[str, Any]:
    """pin済CFRU treeのcanonical count macro出現を保守的に全件列挙する。"""

    source_root = (root / CFRU_SOURCE).resolve()
    if not source_root.is_dir() or source_root.is_symlink():
        _fail("CFRU source rootが通常directoryではありません")
    head = _git_text(source_root, ["rev-parse", "HEAD"], "CFRU HEAD").strip()
    if head != CFRU_COMMIT:
        _fail(f"CFRU source commitが不一致です: {head}")
    macros = ("ABILITIES_COUNT", "ITEMS_COUNT", "MOVES_COUNT", "NUM_SPECIES")
    output = _git_text(
        source_root,
        [
            "grep", "-n", "-I", "-w", "-E", "|".join(macros), CFRU_COMMIT,
            "--", "*.c", "*.h", "*.s",
        ],
        "CFRU pinned count macro inventory",
    )
    blobs: dict[str, bytes] = {}
    rows: list[dict[str, Any]] = []
    prefix = f"{CFRU_COMMIT}:"
    for raw_line in output.splitlines():
        line = raw_line.removeprefix(prefix)
        parts = line.split(":", 2)
        if len(parts) != 3 or not parts[1].isdigit():
            _fail(f"CFRU count macro grep形式が不正です: {raw_line!r}")
        relative, line_number_text, source_line = parts
        if relative not in blobs:
            blobs[relative] = _git_bytes(
                source_root,
                ["show", f"{CFRU_COMMIT}:{relative}"],
                f"CFRU pinned count consumer {relative}",
            )
        matched = sorted(set(re.findall(r"\b(?:" + "|".join(macros) + r")\b", source_line)))
        if not matched:
            _fail(f"CFRU count macro grep結果を再解析できません: {raw_line!r}")
        for macro in matched:
            rows.append(
                {
                    "macro": macro,
                    "path": relative,
                    "line": int(line_number_text),
                    "line_sha256": _sha256(source_line.encode("utf-8")),
                    "file_sha256": _sha256(blobs[relative]),
                    "comment_status": "UNCLASSIFIED_CONSERVATIVE_REVIEW_REQUIRED",
                }
            )
    rows.sort(key=lambda row: (row["macro"], row["path"], row["line"]))
    required = {
        ("ABILITIES_COUNT", "include/constants/abilities.h"),
        ("ABILITIES_COUNT", "src/ability_battle_effects.c"),
        ("ABILITIES_COUNT", "src/build_pokemon.c"),
        ("ABILITIES_COUNT", "src/util.c"),
        ("ITEMS_COUNT", "include/constants/items.h"),
        ("ITEMS_COUNT", "include/new/item_effects.h"),
        ("ITEMS_COUNT", "src/Tables/item_tables.c"),
        ("ITEMS_COUNT", "src/debug_menu.c"),
        ("ITEMS_COUNT", "src/item.c"),
        ("ITEMS_COUNT", "src/scripting.c"),
        ("MOVES_COUNT", "include/constants/moves.h"),
        ("MOVES_COUNT", "src/Tables/battle_moves.c"),
        ("MOVES_COUNT", "src/battle_strings.c"),
        ("MOVES_COUNT", "src/build_pokemon.c"),
        ("MOVES_COUNT", "src/daycare.c"),
        ("MOVES_COUNT", "src/move_menu.c"),
        ("NUM_SPECIES", "include/constants/species.h"),
        ("NUM_SPECIES", "src/build_pokemon.c"),
        ("NUM_SPECIES", "src/evolution.c"),
        ("NUM_SPECIES", "src/form_change.c"),
        ("NUM_SPECIES", "src/wild_encounter.c"),
    }
    actual = {(row["macro"], row["path"]) for row in rows}
    missing = sorted(required - actual)
    if missing:
        _fail(f"CFRU count macro必須consumerがありません: {missing}")
    counts = Counter(str(row["macro"]) for row in rows)
    return {
        "status": "PINNED_TREE_CONSERVATIVE_INVENTORY",
        "source_lock_commit": CFRU_COMMIT,
        "actual_commit": head,
        "working_tree_bytes_ignored": True,
        "snapshot_read_via": "git grep/show <pinned-commit>",
        "match_count": len(rows),
        "counts_by_macro": dict(sorted(counts.items())),
        "required_macro_path_pairs": [
            {"macro": macro, "path": path} for macro, path in sorted(required)
        ],
        "required_anchor_status": "PASS",
        "rows": rows,
        "inventory_sha256": _sha256(canonical_json_bytes(rows)),
        "completeness_claim": "PINNED_C_H_S_WORD_MATCHES_COMMENTS_INCLUDED",
    }


def audit_move_effect_dispatch(
    root: Path, rom: bytes, *, move_data_address: int
) -> dict[str, Any]:
    """pin済CFRUのu8 move-effect dispatch 256枠とblank候補を監査する。"""

    source_root = (root / CFRU_SOURCE).resolve()
    head = _git_text(source_root, ["rev-parse", "HEAD"], "CFRU HEAD").strip()
    if head != CFRU_COMMIT:
        _fail(f"CFRU source commitが不一致です: {head}")
    relative = "assembly/data/move_effect_table.s"
    raw = _git_bytes(
        source_root,
        ["show", f"{CFRU_COMMIT}:{relative}"],
        "CFRU pinned move effect dispatch",
    )
    text = raw.decode("utf-8")
    match = re.search(
        r"^gBattleScriptsForMoveEffects:\s*$\n(.*?)(?=^@{8,}|^gSetStatusMoveEffects:)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        _fail("move effect dispatch表を抽出できません")
    entries = re.findall(r"^\.word\s+([^\s@]+)", match.group(1), re.MULTILINE)
    if len(entries) != 256:
        _fail(f"move effect dispatchが256 entryではありません: {len(entries)}")
    expected_tail = {
        251: "BS_251_Blank",
        252: "BS_252_Blank",
        253: "BS_253_MaxMove",
        254: "BS_254_Blank",
        255: "BS_255_Blank",
    }
    if {index: entries[index] for index in expected_tail} != expected_tail:
        _fail("move effect dispatch末尾が想定値から変わりました")
    candidates = [251, 252, 255]
    move_offset = move_data_address - ROM_BASE
    move_count = 1063
    move_stride = 12
    if move_offset < 0 or move_offset + move_count * move_stride > len(rom):
        _fail("Stage65 move dataがROM外です")
    effects = rom[move_offset : move_offset + move_count * move_stride : move_stride]
    effect_counts = Counter(effects)
    observed_tail_counts = {
        str(effect): effect_counts[effect] for effect in range(251, 256)
    }
    if observed_tail_counts != {
        "251": 0, "252": 0, "253": 102, "254": 0, "255": 0
    }:
        _fail(f"Stage65 move effect末尾利用数が想定外です: {observed_tail_counts}")
    return {
        "status": "SEMANTIC_RESERVATION_NOT_ASSIGNED",
        "storage": "u8",
        "entry_count": len(entries),
        "table_bytes": len(entries) * 4,
        "maximum_effect_id": 255,
        "blank_candidate_ids": candidates,
        "blank_candidate_active_move_use_count": {
            str(effect): effect_counts[effect] for effect in candidates
        },
        "stage65_tail_effect_use_count": observed_tail_counts,
        "stage65_move_data": {
            "address": move_data_address,
            "address_hex": f"0x{move_data_address:08X}",
            "row_count": move_count,
            "stride_bytes": move_stride,
            "effect_offset": 0,
            "effect_column_sha256": _sha256(effects),
        },
        "excluded_blank_id": 254,
        "excluded_reason": "既存定義済み特殊処理のため再利用候補外",
        "ally_switch_effect_id": None,
        "in_place_table_growth_possible": False,
        "semantic_reuse_requires_review": True,
        "classification": CLASS_ENGINE,
        "required_action": "251/252/255から専用script・AI・target semantics込みで明示採用",
        "source": {
            "path": f"{CFRU_SOURCE.as_posix()}/{relative}",
            "commit": CFRU_COMMIT,
            "file_sha256": _sha256(raw),
            "working_tree_bytes_ignored": True,
        },
        "entry_inventory_sha256": _sha256(canonical_json_bytes(entries)),
    }


def audit_bitfield_consumers(root: Path) -> dict[str, Any]:
    """既知の狭幅Item/Ability consumerをexact patternで再検出する。"""

    rows: list[dict[str, Any]] = []
    for spec in BITFIELD_CONSUMER_PATTERNS:
        relative = str(spec["path"])
        cfru_prefix = CFRU_SOURCE.as_posix() + "/"
        if relative.startswith(cfru_prefix):
            source_root = (root / CFRU_SOURCE).resolve()
            head = _git_text(
                source_root, ["rev-parse", "HEAD"], "CFRU HEAD"
            ).strip()
            if head != CFRU_COMMIT:
                _fail(f"CFRU source commitが不一致です: {head}")
            source_relative = relative.removeprefix(cfru_prefix)
            raw = _git_bytes(
                source_root,
                ["show", f"{CFRU_COMMIT}:{source_relative}"],
                f"CFRU pinned narrow consumer {source_relative}",
            )
            byte_source = "PINNED_GIT_BLOB"
        else:
            raw = _regular_file(root, relative, "bitfield consumer")
            byte_source = "WORKSPACE_TRACKED_FILE"
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            _fail(f"bitfield consumerがUTF-8ではありません: {relative}: {exc}")
        pattern = re.compile(str(spec["pattern"]), re.MULTILINE)
        matches = list(pattern.finditer(source))
        expected = _integer(spec.get("expected_occurrences", 1), "bitfield expected count")
        if len(matches) != expected:
            _fail(
                f"既知bitfield consumer件数が変わりました: {relative}/"
                f"{spec['field']}={len(matches)} expected={expected}"
            )
        bits = _integer(spec["declared_bits"], "declared bits")
        limit = (1 << bits) - 1
        required_max = spec.get("required_max", 1043 if "item" in str(spec["field"]).lower() else None)
        rows.append(
            {
                "field": spec["field"],
                "path": relative,
                "declared_bits": bits,
                "limit": limit,
                "required_max": required_max,
                "known_limit_exceeded": (
                    required_max is not None
                    and _integer(required_max, "narrow field required max") > limit
                ),
                "source_status": spec.get("source_status", "ACTIVE_KNOWN_CONSUMER"),
                "byte_source": byte_source,
                "occurrence_count": len(matches),
                "line_numbers": [source.count("\n", 0, match.start()) + 1 for match in matches],
                "file_sha256": _sha256(raw),
            }
        )
    return {
        "status": "KNOWN_CONSUMERS_FOUND",
        "rows": rows,
        "inventory_sha256": _sha256(canonical_json_bytes(rows)),
    }


def _metadata_patch_summary(
    rom: bytes, rows: Sequence[Mapping[str, Any]], label: str
) -> dict[str, Any]:
    measured: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        site = _integer(row.get("site"), f"{label}[{index}] site")
        replacement_hex = str(row.get("replacement_hex", ""))
        try:
            replacement = bytes.fromhex(replacement_hex)
        except ValueError:
            _fail(f"{label}[{index}] replacement_hexが不正です")
        if not replacement or site < 0 or site + len(replacement) > len(rom):
            _fail(f"{label}[{index}] site/sizeがROM外です")
        actual = rom[site : site + len(replacement)]
        measured.append(
            {
                "site_offset": site,
                "label": row.get("label"),
                "replacement_hex": replacement_hex.lower(),
                "stage65_actual_hex": actual.hex(),
                "replacement_retained": actual == replacement,
            }
        )
    retained = sum(row["replacement_retained"] for row in measured)
    return {
        "declared_count": len(rows),
        "stage65_replacement_retained_count": retained,
        "stage65_superseded_count": len(rows) - retained,
        "rows": measured,
        "inventory_sha256": _sha256(canonical_json_bytes(measured)),
    }


def audit_stage_consumer_ownership(
    rom: bytes,
    stage09: Mapping[str, Any],
    stage39: Mapping[str, Any],
    hotfix: Mapping[str, Any],
) -> dict[str, Any]:
    """Stage09以降のrepoint、instruction veneer、可変表rootを実ROMで実測する。"""

    repoints = stage09.get("repoints")
    runtime_patches = stage09.get("runtime", {}).get("patches")
    name_patches = stage09.get("species_name_consumers", {}).get(
        "instruction_patches"
    )
    learn_hooks = stage09.get("learn_move_hooks")
    if not isinstance(repoints, dict) or not all(
        isinstance(rows, list) for rows in (runtime_patches, name_patches, learn_hooks)
    ):
        _fail("Stage09 consumer ownership metadataが不正です")
    repoint_rows = []
    for name, row in sorted(repoints.items()):
        if not isinstance(row, dict):
            _fail(f"Stage09 repoint rowが不正です: {name}")
        sites_value = row.get("sites")
        sites = sites_value if isinstance(sites_value, list) else (
            [row["site"]] if isinstance(row.get("site"), int) else []
        )
        target = _integer(row.get("new"), f"Stage09 {name} new target")
        actual_targets = []
        for site_value in sites:
            site = _integer(site_value, f"Stage09 {name} site")
            if site < 0 or site + 4 > len(rom):
                _fail(f"Stage09 repoint siteがROM外です: {name}/{site}")
            actual_targets.append(struct.unpack_from("<I", rom, site)[0])
        repoint_rows.append(
            {
                "name": name,
                "stage09_target": target,
                "declared_site_count": len(sites),
                "stage65_exact_target_count": sum(
                    actual == target for actual in actual_targets
                ),
                "stage65_distinct_values": sorted(set(actual_targets)),
                "later_stage_or_instruction_supersession_present": any(
                    actual != target for actual in actual_targets
                ),
            }
        )

    stage39_tables = stage39.get("runtime", {}).get("tables")
    hotfix_addresses = hotfix.get("addresses")
    if not isinstance(stage39_tables, dict) or not isinstance(hotfix_addresses, dict):
        _fail("Stage39/61 consumer root metadataが不正です")
    root_specs = {
        "stage39_level_up_data": stage39_tables.get("level_up_data", {}).get("address"),
        "stage39_level_up_pointers": stage39_tables.get("level_up_pointers", {}).get("address"),
        "stage39_egg_moves": stage39_tables.get("egg_moves", {}).get("address"),
        "stage39_form_table": stage39_tables.get("form_table", {}).get("address"),
        "stage39_wild_table": stage39_tables.get("wild_table", {}).get("address"),
        "stage39_tmhm_compatibility_superseded": stage39_tables.get("tmhm", {}).get("address"),
        "stage39_tutor_compatibility": stage39_tables.get("tutor", {}).get("address"),
        "stage61_tmhm_catalog": hotfix_addresses.get("tmhm"),
        "stage61_tutor_catalog": hotfix_addresses.get("tutor"),
        "stage61_tmhm_compatibility_active": hotfix_addresses.get("compatibility"),
    }
    literal_roots = {}
    for name, address_value in root_specs.items():
        address = _integer(address_value, f"{name} address")
        sites = _literal_sites(rom, address)
        if not sites:
            _fail(f"Stage65 ROMで可変/catalog rootを検出できません: {name}")
        literal_roots[name] = {
            "target_address": address,
            "target_address_hex": f"0x{address:08X}",
            "occurrence_count": len(sites),
            "site_offsets": sites,
            "site_set_sha256": _sha256(canonical_json_bytes(sites)),
        }
    return {
        "stage09_repoints": {
            "declared_record_count": len(repoint_rows),
            "rows": repoint_rows,
            "inventory_sha256": _sha256(canonical_json_bytes(repoint_rows)),
        },
        "stage09_runtime_instruction_patches": _metadata_patch_summary(
            rom, runtime_patches, "Stage09 runtime patch"
        ),
        "stage09_species_name_stride_instruction_patches": _metadata_patch_summary(
            rom, name_patches, "Stage09 species name instruction patch"
        ),
        "stage09_learn_move_hooks": _metadata_patch_summary(
            rom, learn_hooks, "Stage09 learn move hook"
        ),
        "stage39_and_stage61_literal_roots": literal_roots,
        "interpretation": (
            "supersededは見落としではなく後続Stageのchain候補。現行targetと命令を"
            "再解決するまでruntime-readyにしない"
        ),
    }


def _free_segments(
    rom: bytes, allocation: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    regions = allocation.get("regions")
    allocations = allocation.get("allocations")
    summaries = allocation.get("summaries")
    if not isinstance(regions, list) or not isinstance(allocations, list) \
            or not isinstance(summaries, dict):
        _fail("Stage65 allocation ledger構造が不正です")
    region_by_name = {str(row.get("name")): row for row in regions}
    by_region: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in allocations:
        name = str(row.get("name", ""))
        region_name = str(row.get("region", ""))
        region = region_by_name.get(region_name)
        if not name or not isinstance(region, dict):
            _fail(f"Stage65 allocationのregionが不明です: {name}/{region_name}")
        start = _integer(row.get("start"), f"allocation {name} start")
        end = _integer(row.get("end_exclusive"), f"allocation {name} end")
        size = _integer(row.get("size"), f"allocation {name} size")
        if end - start != size:
            _fail(f"Stage65 allocation size不一致です: {name}")
        if start < _integer(region.get("start"), "region start") \
                or end > _integer(region.get("end_exclusive"), "region end"):
            _fail(f"Stage65 allocationがregion外です: {name}")
        by_region[region_name].append(row)

    output: list[dict[str, Any]] = []
    total_allocated = 0
    for region in regions:
        if region.get("kind") != "allocatable":
            continue
        region_name = str(region.get("name"))
        cursor = _integer(region.get("start"), f"region {region_name} start")
        region_end = _integer(region.get("end_exclusive"), f"region {region_name} end")
        for row in sorted(
            by_region.get(region_name, []), key=lambda item: _integer(item["start"], "start")
        ):
            start = _integer(row.get("start"), "allocation start")
            end = _integer(row.get("end_exclusive"), "allocation end")
            if start < cursor:
                _fail(f"Stage65 allocation overlapです: {row.get('name')}")
            if cursor < start:
                raw = rom[cursor:start]
                output.append(
                    {
                        "region": region_name,
                        "start": cursor,
                        "start_hex": f"0x{cursor:08X}",
                        "gba_start": ROM_BASE + cursor,
                        "gba_start_hex": f"0x{ROM_BASE + cursor:08X}",
                        "end_exclusive": start,
                        "size": start - cursor,
                        "all_ff": raw == b"\xFF" * len(raw),
                    }
                )
            total_allocated += end - start
            cursor = end
        if cursor < region_end:
            raw = rom[cursor:region_end]
            output.append(
                {
                    "region": region_name,
                    "start": cursor,
                    "start_hex": f"0x{cursor:08X}",
                    "gba_start": ROM_BASE + cursor,
                    "gba_start_hex": f"0x{ROM_BASE + cursor:08X}",
                    "end_exclusive": region_end,
                    "size": region_end - cursor,
                    "all_ff": raw == b"\xFF" * len(raw),
                }
            )
    if any(not row["all_ff"] for row in output):
        _fail("Stage65のallocation未使用spanに非FF byteがあります")
    declared_free = sum(row["size"] for row in output)
    if declared_free != _integer(
        summaries.get("remaining_allocatable_bytes"), "remaining allocatable bytes"
    ):
        _fail("Stage65 allocation summaryの空きbyte数が実geometryと不一致です")
    if total_allocated != _integer(summaries.get("allocated_bytes"), "allocated bytes"):
        _fail("Stage65 allocation summaryの使用byte数が実geometryと不一致です")
    output.sort(key=lambda row: (row["start"], row["end_exclusive"]))
    return output, {
        "declared_free_bytes": declared_free,
        "actual_erased_free_bytes": declared_free,
        "segment_count": len(output),
        "largest_contiguous_free_bytes": max(row["size"] for row in output),
    }


def _literal_sites(rom: bytes, address: int) -> list[int]:
    needle = struct.pack("<I", address)
    sites: list[int] = []
    cursor = 0
    while True:
        cursor = rom.find(needle, cursor)
        if cursor < 0:
            break
        sites.append(cursor)
        cursor += 1
    return sites


def _p01_root_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    rows = value.get("rows")
    sites = []
    matched = 0
    targets: set[int] = set()
    expected_hex: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("site_offset"), int):
                sites.append(row["site_offset"])
            if row.get("matches") is True:
                matched += 1
            if isinstance(row.get("expected_target"), int):
                targets.add(row["expected_target"])
            if isinstance(row.get("expected_hex"), str):
                expected_hex.add(row["expected_hex"])
    direct_sites = value.get("site_offsets")
    if isinstance(direct_sites, list):
        sites.extend(_integer(item, "consumer site") for item in direct_sites)
        matched = len(direct_sites)
    count = value.get("occurrence_count")
    if count is None:
        count = len(sites)
    return {
        "kind": value.get("kind"),
        "declared_or_observed_count": _integer(count, "root count"),
        "matched_count": matched,
        "site_offsets": sorted(set(sites)),
        "expected_targets": sorted(targets),
        "expected_pointer_bytes_hex": sorted(expected_hex),
    }


def _table_row(
    *,
    table_key: str,
    domain: str,
    address: int,
    old_count: int,
    new_count: int,
    stride: int,
    alignment: int = 4,
    count_semantics: str = "ROWS",
    classification: str = CLASS_ENGINE,
    notes: Sequence[str] = (),
) -> dict[str, Any]:
    old_size = old_count * stride
    new_size = new_count * stride
    return {
        "table_key": table_key,
        "domain": domain,
        "current_address": address,
        "current_address_hex": f"0x{address:08X}",
        "old_count": old_count,
        "new_count": new_count,
        "count_semantics": count_semantics,
        "stride_bytes": stride,
        "old_size_bytes": old_size,
        "new_size_bytes": new_size,
        "delta_bytes": new_size - old_size,
        "alignment": alignment,
        "in_place_append_authorized": False,
        "relocation_required": True,
        "classification": classification,
        "notes": list(notes),
    }


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def _dry_run_layout(
    tables: Sequence[Mapping[str, Any]], free_segments: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    candidates = sorted(
        (row for row in free_segments if row.get("all_ff") is True),
        key=lambda row: (-_integer(row["size"], "free size"), row["start"]),
    )
    if not candidates:
        _fail("allocator候補spanがありません")
    selected = next(
        (row for row in candidates if row.get("region") == "integration_modules"),
        candidates[0],
    )
    cursor = _align(_integer(selected["start"], "selected start"), 16)
    placements: list[dict[str, Any]] = []
    for table in sorted(tables, key=lambda row: str(row["table_key"])):
        alignment = _integer(table["alignment"], "table alignment")
        cursor = _align(cursor, alignment)
        size = _integer(table["new_size_bytes"], "new table size")
        end = cursor + size
        placements.append(
            {
                "table_key": table["table_key"],
                "start": cursor,
                "start_hex": f"0x{cursor:08X}",
                "gba_start": ROM_BASE + cursor,
                "gba_start_hex": f"0x{ROM_BASE + cursor:08X}",
                "end_exclusive": end,
                "size": size,
                "alignment": alignment,
            }
        )
        cursor = end
    selected_end = _integer(selected["end_exclusive"], "selected end")
    if cursor > selected_end:
        _fail(
            f"known fixed table bundleがcandidate spanを超えます: "
            f"end={cursor}, limit={selected_end}"
        )
    start = _align(_integer(selected["start"], "selected start"), 16)
    return {
        "status": "NON_BINDING_DRY_RUN_ONLY",
        "source_stage": 65,
        "region": selected["region"],
        "candidate_span_start": selected["start"],
        "candidate_span_end_exclusive": selected_end,
        "candidate_span_bytes": selected["size"],
        "bundle_start": start,
        "bundle_end_exclusive": cursor,
        "bundle_bytes_including_alignment": cursor - start,
        "sum_of_table_bytes": sum(
            _integer(row["new_size_bytes"], "table new size") for row in tables
        ),
        "remaining_candidate_bytes_after_bundle": selected_end - cursor,
        "fits": True,
        "placements": placements,
        "allocation_ledger_mutated": False,
        "rom_mutated": False,
        "warning": (
            "既知の固定tableだけの配置試算であり、可変長learnset/egg/text/code/"
            "graphicsを含む全runtime容量証明ではない"
        ),
    }


def _assess_allocator_spans(
    tables: Sequence[Mapping[str, Any]], free_segments: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """4 KiB以上の各空きspanへ同じ固定table束が入るか比較する。"""

    output = []
    for segment in sorted(
        (row for row in free_segments if _integer(row["size"], "free size") >= 4096),
        key=lambda row: (_integer(row["start"], "free start"), str(row["region"])),
    ):
        start = _align(_integer(segment["start"], "candidate start"), 16)
        cursor = start
        for table in sorted(tables, key=lambda row: str(row["table_key"])):
            cursor = _align(cursor, _integer(table["alignment"], "table alignment"))
            cursor += _integer(table["new_size_bytes"], "table size")
        end = _integer(segment["end_exclusive"], "candidate end")
        output.append(
            {
                "region": segment["region"],
                "start": segment["start"],
                "start_hex": segment["start_hex"],
                "end_exclusive": end,
                "size": segment["size"],
                "required_bundle_bytes_including_alignment": cursor - start,
                "fits_known_fixed_bundle": cursor <= end,
                "shortfall_bytes": max(0, cursor - end),
                "remaining_bytes_if_fit": max(0, end - cursor),
                "binding_allocation": False,
            }
        )
    if len(output) != 2 \
            or {row["region"] for row in output} != {"integration_modules", "future_tail"}:
        _fail("Stage65+ allocator大型span集合が想定外です")
    by_region = {str(row["region"]): row for row in output}
    if by_region["integration_modules"]["fits_known_fixed_bundle"] is not True \
            or by_region["future_tail"]["fits_known_fixed_bundle"] is not False:
        _fail("Stage65+ allocator span適合判定が想定外です")
    return output


def _build_reservations(
    manifests: Mapping[str, Sequence[Mapping[str, Any]]],
    p04: Mapping[str, Any],
    p05: Mapping[str, Any],
) -> dict[str, Any]:
    records = p04.get("records")
    if not isinstance(records, list) or len(records) != 54:
        _fail("P04 candidate record数が54ではありません")
    adopted = [row for row in records if row.get("implementation_scope") == "ADOPT_CANDIDATE"]
    holds = [row for row in records if row.get("implementation_scope") == "HOLD_CLASSIFICATION"]
    if len(adopted) != 52 or len(holds) != 2:
        _fail("P04 candidateの採用52/hold 2件が不一致です")
    if Counter(row.get("classification") for row in adopted) != {
        "BATTLE_ONLY_MEGA": 49,
        "NEW_SPECIES": 3,
    }:
        _fail("P04採用候補のMega 49/新Species 3分類が不一致です")

    species_requested = []
    for row in sorted(adopted, key=lambda item: str(item.get("proposed_species_key"))):
        key = str(row.get("proposed_species_key") or "")
        if row.get("id_assignment") != "BLOCKED_PENDING_CAPACITY_EXPANSION":
            _fail(f"P04 candidateが未採番状態ではありません: {row.get('record_key')}")
        species_requested.append(
            {
                "species_key": key,
                "source_record_key": row.get("record_key"),
                "identity_species_key": row.get("identity_species_key"),
                "identity_form_key": row.get("identity_form_key"),
                "classification": row.get("classification"),
                "source_species_key": row.get("source_species_key"),
                "mega_stone_key": row.get("mega_stone_key"),
                "ability_key": row.get("ability_key"),
                "ability_status": row.get("ability_status"),
                "ability_replacement_key": row.get("ability_replacement_key"),
                "provenance_profile_key": row.get("provenance_profile_key"),
                "materialization_ready": False,
            }
        )
    species = allocate_append_ids(
        manifests["species_form"],
        species_requested,
        key_field="species_key",
        expected_current_count=MANIFEST_SPACES["species_form"]["current_count"],
    )

    stone_subjects: dict[str, list[str]] = defaultdict(list)
    for row in adopted:
        stone = row.get("mega_stone_key")
        if stone:
            stone_subjects[str(stone)].append(str(row.get("record_key")))
    if len(stone_subjects) != 45:
        _fail(f"P04 unique Mega Stone数が45ではありません: {len(stone_subjects)}")
    item_requested = [
        {
            "item_key": key,
            "source_record_key": sorted(subjects)[0],
            "subject_record_keys": sorted(subjects),
            "classification": "MEGA_STONE",
            "materialization_ready": False,
        }
        for key, subjects in sorted(stone_subjects.items())
    ]
    items = allocate_append_ids(
        manifests["item"],
        item_requested,
        key_field="item_key",
        expected_current_count=MANIFEST_SPACES["item"]["current_count"],
    )

    requirements = p05.get("new_ability_requirements")
    if not isinstance(requirements, list) or len(requirements) != 6:
        _fail("P05新Ability要件が6件ではありません")
    by_ability = {str(row.get("ability_key")): row for row in requirements}
    if set(by_ability) != EXPECTED_NEW_ABILITY_KEYS or len(by_ability) != len(requirements):
        _fail("P05新Ability key集合が不一致です")
    ability_requested = []
    for key in sorted(by_ability):
        row = by_ability[key]
        if row.get("canonical_id") is not None \
                or row.get("id_status") != "UNASSIGNED_APPEND_ALLOCATION_REQUIRED":
            _fail(f"P05 Abilityが未採番状態ではありません: {key}")
        ability_requested.append(
            {
                "ability_key": key,
                "source_record_key": f"P05_{key.removeprefix('ABILITY_KEY_')}",
                "subject_record_keys": sorted(str(item) for item in row.get("subjects", [])),
                "technical_source_symbol": row.get("technical_reference", {}).get("source_symbol"),
                "do_not_copy_source_numeric_id": row.get("do_not_copy_source_numeric_id"),
                "official_status": row.get("official_status"),
                "materialization_ready": False,
            }
        )
    abilities = allocate_append_ids(
        manifests["ability"],
        ability_requested,
        key_field="ability_key",
        expected_current_count=MANIFEST_SPACES["ability"]["current_count"],
    )
    for row in abilities:
        row["source_numeric_id_same_by_coincidence"] = (
            row["id"] == row["do_not_copy_source_numeric_id"]
        )

    move_requirements = p05.get("new_move_requirements")
    if not isinstance(move_requirements, list) or len(move_requirements) != 1:
        _fail("P05新Move要件が1件ではありません")
    move_requirement = move_requirements[0]
    if move_requirement.get("move_key") != "MOVE_KEY_ALLYSWITCH" \
            or move_requirement.get("requested_project_id") != 1063 \
            or move_requirement.get("canonical_id") is not None \
            or move_requirement.get("runtime_status") \
            != "BLOCKED_SPECIFICATION_AND_CAPACITY_INCOMPLETE":
        _fail("P05 Ally Switch未実装契約が不一致です")
    moves = allocate_append_ids(
        manifests["move"],
        [
            {
                "move_key": "MOVE_KEY_ALLYSWITCH",
                "source_record_key": "P05_MOVE_ALLYSWITCH",
                "official_move_id": move_requirement.get("official", {}).get("move_id"),
                "missing_specification_fields": move_requirement.get(
                    "missing_specification_fields"
                ),
                "serialization_gate": move_requirement.get("p03_routes", {}).get(
                    "serialization_gate"
                ),
                "route_count": move_requirement.get("p03_routes", {}).get("route_count"),
                "materialization_ready": False,
            }
        ],
        key_field="move_key",
        expected_current_count=MANIFEST_SPACES["move"]["current_count"],
    )
    if moves[0]["id"] != 1063:
        _fail("Ally Switch予約IDが1063ではありません")

    result: dict[str, Any] = {}
    for domain, rows in (
        ("species_form", species),
        ("item", items),
        ("ability", abilities),
        ("move", moves),
    ):
        current = MANIFEST_SPACES[domain]["current_count"]
        result[domain] = {
            "key_field": MANIFEST_SPACES[domain]["key_field"],
            "current_count": current,
            "current_max_id": current - 1,
            "append_count": len(rows),
            "reserved_start_id": rows[0]["id"],
            "reserved_end_id": rows[-1]["id"],
            "new_count": current + len(rows),
            "new_max_id": rows[-1]["id"],
            "storage_limit": U16_MAX,
            "within_u16": rows[-1]["id"] <= U16_MAX,
            "allocation_order": "STABLE_KEY_LEXICOGRAPHIC",
            "classification": CLASS_SIMPLE,
            "shared_manifest_mutated": False,
            "rows": rows,
        }
    return result


def _temporary_ability_contract(
    p04: Mapping[str, Any], p05: Mapping[str, Any]
) -> dict[str, Any]:
    records = p04.get("records", [])
    temporary = [row for row in records if row.get("ability_status") == "TEMPORARY_REPLACEABLE"]
    adopted = [row for row in temporary if row.get("implementation_scope") == "ADOPT_CANDIDATE"]
    held = [row for row in temporary if row.get("implementation_scope") == "HOLD_CLASSIFICATION"]
    if len(temporary) != 16 or len(adopted) != 14 or len(held) != 2:
        _fail("TEMPORARY_REPLACEABLE 16件（採用14/hold 2）が不一致です")
    replacement_keys = [str(row.get("ability_replacement_key") or "") for row in temporary]
    _require_unique(replacement_keys, "temporary ability replacement key")

    p05_rows = p05.get("temporary_ability_assignments")
    if not isinstance(p05_rows, list) or len(p05_rows) != 14:
        _fail("P05 temporary ability assignmentが14件ではありません")
    p05_by_record = {str(row.get("record_key")): row for row in p05_rows}
    if len(p05_by_record) != 14 or set(p05_by_record) != {
        str(row.get("record_key")) for row in adopted
    }:
        _fail("P04/P05 temporary ability対象が不一致です")
    rows = []
    for row in sorted(temporary, key=lambda item: str(item.get("record_key"))):
        record_key = str(row.get("record_key"))
        if record_key in p05_by_record:
            handoff = p05_by_record[record_key]
            if handoff.get("replacement_trigger_key") != row.get("ability_replacement_key") \
                    or handoff.get("ability_key") != row.get("ability_key"):
                _fail(f"P04/P05 temporary ability内容が不一致です: {record_key}")
        rows.append(
            {
                "record_key": record_key,
                "identity_species_key": row.get("identity_species_key"),
                "identity_form_key": row.get("identity_form_key"),
                "proposed_species_key": row.get("proposed_species_key"),
                "ability_key": row.get("ability_key"),
                "ability_status": "TEMPORARY_REPLACEABLE",
                "ability_replacement_key": row.get("ability_replacement_key"),
                "ability_provenance_key": row.get("ability_provenance_key"),
                "scope": (
                    "RESERVED_SPECIES_ASSIGNMENT"
                    if row.get("implementation_scope") == "ADOPT_CANDIDATE"
                    else "CLASSIFICATION_HOLD_NO_ID_RESERVED"
                ),
            }
        )
    return {
        "policy": "TEMPORARY_REPLACEABLE",
        "replacement_must_preserve_species_and_form_key": True,
        "adopted_binding_count": 14,
        "classification_hold_binding_count": 2,
        "unique_replacement_key_count": 16,
        "rows": rows,
    }


def _asset_separation(
    assets: Mapping[str, Any], reservations: Mapping[str, Any]
) -> dict[str, Any]:
    coverage = assets.get("coverage")
    if not isinstance(coverage, dict):
        _fail("P04 asset coverageがありません")
    mega = coverage.get("mega_candidate_records", {})
    stones = coverage.get("mega_stones", {})
    winds = coverage.get("winds_waves_new_species", {})
    palettes = coverage.get("gba_full_species_palette_compatibility", {})
    if mega != {"covered": 49, "required": 49} \
            or stones != {"covered": 45, "required": 45} \
            or winds != {"covered": 0, "required": 3} \
            or palettes != {"ready": 49, "required": 49}:
        _fail("P04 asset coverage契約が想定件数と不一致です")
    missing = assets.get("missing_assets")
    issues = assets.get("palette_coverage_issues")
    if not isinstance(missing, list) or not isinstance(issues, list):
        _fail("P04 asset gap一覧がありません")
    missing_records = sorted(str(row.get("record_key")) for row in missing)
    palette_records = sorted({str(row.get("record_key")) for row in issues})
    expected_missing = sorted(
        {"P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA"}
    )
    expected_palette: list[str] = []
    if missing_records != expected_missing or palette_records != expected_palette:
        _fail("Winds/WavesまたはMega palette素材gap対象が不一致です")
    reserved_records = {
        str(row.get("source_record_key"))
        for row in reservations["species_form"]["rows"]
    }
    if not set(missing_records + palette_records).issubset(reserved_records):
        _fail("asset gapが予約Species集合に解決できません")
    return {
        "id_reservation_is_independent_from_asset_readiness": True,
        "asset_gap_does_not_become_fake_payload": True,
        "winds_waves": {
            "reserved_ids": 3,
            "source_assets_ready": 0,
            "consumer_ready": False,
            "missing_record_keys": missing_records,
            "fake_or_placeholder_generated": False,
        },
        "mega_species": {
            "reserved_ids": 49,
            "source_assets_mapped": 49,
            "gba_palette_ready": 49,
            "consumer_ready": False,
            "palette_blocked_record_keys": palette_records,
        },
        "mega_stones": {
            "reserved_ids": 45,
            "gba_assets_ready": 45,
            "consumer_ready": False,
            "reason": "item row/callback/rights/runtime integration未実装",
        },
        "rights": {
            "root_license_file": assets.get("rights", {}).get("root_license_file"),
            "redistribution_allowed": assets.get("rights", {}).get(
                "redistribution_allowed"
            ),
            "staging_scope": assets.get("rights", {}).get("staging_scope"),
        },
    }


def _mega_stone_variable_components(
    assets: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """45 Mega Stoneの既知raw graphicsと未確定Item payloadを分離する。"""

    stones = assets.get("stone_assets")
    if not isinstance(stones, list) or len(stones) != 45:
        _fail("P04 Mega Stone assetが45件ではありません")
    keys = [str(row.get("mega_stone_key", "")) for row in stones]
    _require_unique(keys, "Mega Stone asset key")
    icon_bytes = []
    palette_bytes = []
    for row in stones:
        icon = row.get("png_asset", {}).get("gba_conversion", {})
        palette = row.get("palette_asset", {}).get("gba_conversion", {})
        if icon.get("status") != "CONVERTED" or icon.get("size") != 288 \
                or palette.get("status") != "CONVERTED" \
                or palette.get("size") != 32:
            _fail(f"Mega Stone GBA asset geometryが不一致です: {row.get('mega_stone_key')}")
        icon_bytes.append(_integer(icon["size"], "Mega Stone icon bytes"))
        palette_bytes.append(_integer(palette["size"], "Mega Stone palette bytes"))
    raw_bytes = sum(icon_bytes) + sum(palette_bytes)
    if raw_bytes != 14400:
        _fail(f"Mega Stone raw GBA asset合計が14,400 byteではありません: {raw_bytes}")
    return [
        {
            "component_key": "mega_stone_icon_palette_payload",
            "current_size_bytes": 0,
            "new_size_bytes": None,
            "source_record_count": len(stones),
            "source_icon_bytes": sum(icon_bytes),
            "source_palette_bytes": sum(palette_bytes),
            "minimum_raw_payload_bytes": raw_bytes,
            "linked_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": (
                "45件の4bpp 288B+palette 32Bは実測済みだが、配置alignment・"
                "consumer pointer・private-use rights gateを含むlink未実施"
            ),
        },
        {
            "component_key": "mega_stone_item_description_effect",
            "current_size_bytes": 0,
            "new_size_bytes": None,
            "source_record_count": len(stones),
            "classification": CLASS_ENGINE,
            "reason": "45 Itemの日本語名/説明、field/battle callback、Mega条件との接続が未提出",
        },
    ]


def _parse_generated_c_byte_array(
    raw: bytes, symbol: str, expected_size: int
) -> bytes:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        _fail(f"generated headerがASCIIではありません: {symbol}: {exc}")
    match = re.search(
        rf"\b{re.escape(symbol)}\[([0-9]+)\]\s*=\s*\{{(.*?)\}};",
        text,
        re.DOTALL,
    )
    if match is None or int(match.group(1)) != expected_size:
        _fail(f"generated配列宣言sizeが不一致です: {symbol}")
    values = bytes(
        int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})u", match.group(2))
    )
    if len(values) != expected_size:
        _fail(f"generated配列payload sizeが不一致です: {symbol}")
    return values


def audit_generated_item_index_consumers(
    root: Path, rom: bytes, allocation: Mapping[str, Any]
) -> dict[str, Any]:
    """Codex系overlayに埋め込まれたItem index表と全Stage65複製を実測する。"""

    runtime_config, runtime_config_identity = _json(
        root, "config/codex_battle_runtime.json", "Codex battle runtime config"
    )
    reward_config, reward_config_identity = _json(
        root, "config/codex_battle_rewards.json", "Codex battle reward config"
    )
    if runtime_config.get("battle", {}).get("item_max") != 998 \
            or reward_config.get("limits", {}).get("item_max") != 998:
        _fail("Codex overlay current item_maxが998ではありません")

    runtime_header_path = "generated/runtime/codex_battle_runtime_generated.h"
    reward_header_path = "generated/runtime/codex_battle_rewards_generated.h"
    runtime_header = _regular_file(root, runtime_header_path, "Codex runtime header")
    reward_header = _regular_file(root, reward_header_path, "Codex reward header")
    specs = [
        {
            "table_key": "codex_runtime_held_item_safe_bitmap",
            "symbol": "gCodexRuntimeHeldItemSafe",
            "header": runtime_header,
            "header_path": runtime_header_path,
            "old_size": 125,
            "new_size": 131,
            "expected_instances": 1,
            "expected_allocation_names": ["codex_battle_runtime_stage44_payload"],
            "count_semantics": "999→1044 one-bit Item rows",
        },
        {
            "table_key": "codex_reward_ball_item_bitmap",
            "symbol": "gCodexRewardBallItems",
            "header": reward_header,
            "header_path": reward_header_path,
            "old_size": 125,
            "new_size": 131,
            "expected_instances": 3,
            "expected_allocation_names": [
                "codex_battle_rewards_stage45_payload",
                "windows_battle_catalog_stage46_payload",
                "windows_box14_vault_stage47_payload",
            ],
            "count_semantics": "999→1044 one-bit Item rows",
        },
        {
            "table_key": "codex_reward_ball_type_by_item",
            "symbol": "gCodexRewardBallTypes",
            "header": reward_header,
            "header_path": reward_header_path,
            "old_size": 999,
            "new_size": 1044,
            "expected_instances": 3,
            "expected_allocation_names": [
                "codex_battle_rewards_stage45_payload",
                "windows_battle_catalog_stage46_payload",
                "windows_box14_vault_stage47_payload",
            ],
            "count_semantics": "999→1044 one-byte Item rows",
        },
    ]
    allocation_rows = allocation.get("allocations")
    if not isinstance(allocation_rows, list):
        _fail("Stage65 allocation一覧がありません")
    rows = []
    for spec in specs:
        old_size = _integer(spec["old_size"], "generated item table old size")
        payload = _parse_generated_c_byte_array(
            spec["header"], str(spec["symbol"]), old_size
        )
        sites = []
        cursor = 0
        while True:
            cursor = rom.find(payload, cursor)
            if cursor < 0:
                break
            sites.append(cursor)
            cursor += 1
        expected_instances = _integer(
            spec["expected_instances"], "generated item table instance count"
        )
        if len(sites) != expected_instances:
            _fail(
                f"Stage65 generated Item table instance数が不一致です: "
                f"{spec['symbol']}={len(sites)} expected={expected_instances}"
            )
        site_allocations = []
        for site in sites:
            owners = [
                row for row in allocation_rows
                if isinstance(row, dict)
                and _integer(row.get("start"), "allocation start") <= site
                and site + old_size <= _integer(
                    row.get("end_exclusive"), "allocation end"
                )
            ]
            if len(owners) != 1:
                _fail(
                    f"generated Item table siteのallocation ownerが一意ではありません: "
                    f"{spec['symbol']}@{site}: {len(owners)}"
                )
            owner = owners[0]
            site_allocations.append(
                {
                    "site_offset": site,
                    "allocation_name": owner.get("name"),
                    "allocation_owner": owner.get("owner"),
                    "allocation_region": owner.get("region"),
                    "allocation_start": owner.get("start"),
                    "allocation_end_exclusive": owner.get("end_exclusive"),
                }
            )
        observed_names = sorted(
            str(row["allocation_name"]) for row in site_allocations
        )
        if observed_names != sorted(str(value) for value in spec["expected_allocation_names"]):
            _fail(
                f"generated Item table allocation owner集合が不一致です: "
                f"{spec['symbol']}={observed_names}"
            )
        new_size = _integer(spec["new_size"], "generated item table new size")
        rows.append(
            {
                "table_key": spec["table_key"],
                "symbol": spec["symbol"],
                "source_header": spec["header_path"],
                "source_payload_sha256": _sha256(payload),
                "old_size_bytes_per_instance": old_size,
                "new_size_bytes_per_instance": new_size,
                "delta_bytes_per_instance": new_size - old_size,
                "stage65_instance_count": len(sites),
                "stage65_instance_offsets": sites,
                "stage65_instance_addresses": [ROM_BASE + site for site in sites],
                "stage65_instance_allocations": site_allocations,
                "old_physical_bytes": old_size * len(sites),
                "new_physical_bytes_if_all_instances_relinked": new_size * len(sites),
                "physical_delta_bytes_if_all_instances_relinked": (
                    new_size - old_size
                ) * len(sites),
                "count_semantics": spec["count_semantics"],
                "classification": CLASS_ENGINE,
                "in_place_append_authorized": False,
                "required_action": "owner overlayと全downstream埋込みcopyを再link/repack",
            }
        )

    source_anchors = {
        "scripts/build_codex_battle_runtime.py": (
            "if len(rows) != 999",
            "bits = bytearray(125)",
            "gCodexRuntimeHeldItemSafe[125]",
        ),
        "overlays/codex_battle_runtime/codex_battle_runtime.c": (
            "item > CODEX_RUNTIME_ITEM_MAX",
            "gCodexRuntimeHeldItemSafe[item >> 3]",
        ),
        "scripts/build_codex_battle_rewards.py": (
            "if len(rows) != 999",
            "bits = bytearray(125)",
            'types = bytearray(b"\\xFF" * 999)',
            "gCodexRewardBallItems[125]",
            "gCodexRewardBallTypes[999]",
        ),
        "overlays/codex_battle_rewards/codex_battle_rewards.c": (
            "item > CODEX_REWARD_ITEM_MAX",
            "gCodexRewardBallItems[item >> 3]",
            "gCodexRewardBallTypes[item]",
        ),
    }
    anchor_rows = []
    for relative, snippets in sorted(source_anchors.items()):
        raw = _regular_file(root, relative, "generated Item consumer source")
        text = raw.decode("utf-8")
        missing = [snippet for snippet in snippets if snippet not in text]
        if missing:
            _fail(f"generated Item consumer anchorが変わりました: {relative}: {missing}")
        anchor_rows.append(
            {
                "path": relative,
                "file_sha256": _sha256(raw),
                "required_anchor_count": len(snippets),
                "all_required_anchors_found": True,
            }
        )
    rows.sort(key=lambda row: row["table_key"])
    return {
        "status": "ENGINE_RELINK_REQUIRED",
        "current_item_count": 999,
        "new_item_count": 1044,
        "logical_old_bytes": sum(row["old_size_bytes_per_instance"] for row in rows),
        "logical_new_bytes": sum(row["new_size_bytes_per_instance"] for row in rows),
        "logical_delta_bytes": sum(row["delta_bytes_per_instance"] for row in rows),
        "stage65_physical_old_bytes": sum(row["old_physical_bytes"] for row in rows),
        "stage65_physical_new_bytes_if_all_instances_relinked": sum(
            row["new_physical_bytes_if_all_instances_relinked"] for row in rows
        ),
        "stage65_physical_delta_bytes_if_all_instances_relinked": sum(
            row["physical_delta_bytes_if_all_instances_relinked"] for row in rows
        ),
        "tables": rows,
        "source_anchors": anchor_rows,
        "inputs": {
            "runtime_config": runtime_config_identity,
            "reward_config": reward_config_identity,
            "runtime_header": _identity(root, runtime_header_path, "Codex runtime header"),
            "reward_header": _identity(root, reward_header_path, "Codex reward header"),
        },
        "inventory_sha256": _sha256(
            canonical_json_bytes({"tables": rows, "source_anchors": anchor_rows})
        ),
    }


def audit_codex_public_event_abi(root: Path) -> dict[str, Any]:
    """Codex公開eventの88-bit/11-byte固定ABIとItem拡張影響を監査する。"""

    config, config_identity = _json(
        root, "config/codex_battle_runtime.json", "Codex battle runtime config"
    )
    builder_path = "scripts/build_codex_battle_runtime.py"
    header_path = "overlays/codex_battle_runtime/codex_battle_runtime.h"
    reader_path = "tools/vega_codex_battle.py"
    builder = _regular_file(root, builder_path, "Codex battle runtime builder")
    header = _regular_file(root, header_path, "Codex battle runtime header")
    reader = _regular_file(root, reader_path, "Codex Windows public-state reader")
    try:
        builder_text = builder.decode("utf-8")
        header_text = header.decode("utf-8")
        reader_text = reader.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(f"Codex public event sourceがUTF-8ではありません: {exc}")
    layout_match = re.search(
        r'"event_bit_layout":\s*\[(.*?)\n\s*\],\n\s*"event_flag_high_bits"',
        builder_text,
        re.DOTALL,
    )
    if layout_match is None:
        _fail("Codex public event bit layoutを抽出できません")
    layout = [
        {"name": name, "bits": int(bits)}
        for name, bits in re.findall(
            r'\{"name":\s*"([^"]+)",\s*"bits":\s*([0-9]+)\}',
            layout_match.group(1),
        )
    ]
    expected_names = [
        "message_id", "current_move_id", "original_move_id", "last_item_id",
        "last_ability_id", "custom_text_crc16", "banks", "flags", "context_flags",
    ]
    if [row["name"] for row in layout] != expected_names \
            or sum(row["bits"] for row in layout) != 88 \
            or next(row["bits"] for row in layout if row["name"] == "last_item_id") != 10:
        _fail("Codex public event bit layoutが想定88-bitから変わりました")
    header_patterns = (
        r"uint8_t\s+packed\[11\];",
        r"CodexBattlePublicEventV2\s+events\[4\];",
        r"sizeof\(CodexBattlePublicEventV2\)\s*==\s*11u",
        r"sizeof\(CodexBattlePublicStateV2\)\s*==\s*180u",
    )
    if any(len(re.findall(pattern, header_text)) != 1 for pattern in header_patterns):
        _fail("Codex public event header ABI anchorが変わりました")
    ram = config.get("ram", {})
    if ram.get("public_event_capacity") != 4 \
            or ram.get("public_state_size") != 180:
        _fail("Codex public event config ABIが想定値から変わりました")
    reader_size_anchor = r"^\s{4}if len\(raw\) != 180:\s*$"
    if len(re.findall(reader_size_anchor, reader_text, re.MULTILINE)) != 1:
        _fail("Codex Windows public-state readerの180-byte ABI anchorが変わりました")
    required_layout = [dict(row) for row in layout]
    next(row for row in required_layout if row["name"] == "last_item_id")["bits"] = 11
    required_bits = sum(row["bits"] for row in required_layout)
    required_event_bytes = math.ceil(required_bits / 8)
    fingerprint = {
        "current_layout": layout,
        "required_layout": required_layout,
        "builder_sha256": _sha256(builder),
        "header_sha256": _sha256(header),
        "reader_sha256": _sha256(reader),
        "config_sha256": config_identity["sha256"],
    }
    return {
        "status": "ABI_EXPANSION_REQUIRED",
        "current_bit_layout": layout,
        "minimum_required_bit_layout": required_layout,
        "current_bits_per_event": 88,
        "minimum_required_bits_per_event": required_bits,
        "current_bytes_per_event": 11,
        "minimum_required_bytes_per_event": required_event_bytes,
        "event_capacity": 4,
        "current_event_ring_bytes": 44,
        "minimum_required_event_ring_bytes": required_event_bytes * 4,
        "minimum_public_state_size_if_only_ring_grows": 184,
        "current_public_state_size": 180,
        "classification": CLASS_ENGINE,
        "required_action": (
            "公開state/後続offset/builder/Windows readerを同一ABI versionで再生成するか、"
            "別encodingを仕様化"
        ),
        "inputs": {
            "config": config_identity,
            "builder": _identity(root, builder_path, "Codex runtime builder"),
            "header": _identity(root, header_path, "Codex runtime header"),
            "windows_reader": _identity(
                root, reader_path, "Codex Windows public-state reader"
            ),
        },
        "inventory_sha256": _sha256(canonical_json_bytes(fingerprint)),
    }


def audit_collection_supply_consumers(
    root: Path, rom: bytes, allocation: Mapping[str, Any]
) -> dict[str, Any]:
    """Stage56取得overlayのItem/Form添字表とsave accessorを実測する。"""

    config, config_identity = _json(
        root, "config/collection_supply_v1.json", "Collection Supply config"
    )
    header_path = "generated/runtime/collection_supply_v1_generated.h"
    source_path = "overlays/collection_supply_v1/collection_supply_v1.c"
    builder_path = "scripts/build_collection_supply_v1.py"
    header = _regular_file(root, header_path, "Collection Supply generated header")
    source = _regular_file(root, source_path, "Collection Supply source")
    builder = _regular_file(root, builder_path, "Collection Supply builder")
    try:
        header_text = header.decode("utf-8")
        source_text = source.decode("utf-8")
        builder_text = builder.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(f"Collection Supply sourceがUTF-8ではありません: {exc}")

    def define_count(name: str) -> int:
        match = re.search(
            rf"^#define\s+{re.escape(name)}\s+([0-9]+)u$",
            header_text,
            re.MULTILINE,
        )
        if match is None:
            _fail(f"Collection Supply count macroがありません: {name}")
        return int(match.group(1))

    def initializer_count(symbol: str) -> int:
        match = re.search(
            rf"static const \w+\s+{re.escape(symbol)}\[\]\s*=\s*\{{"
            rf"(.*?)^\}};",
            header_text,
            re.MULTILINE | re.DOTALL,
        )
        if match is None:
            _fail(f"Collection Supply generated配列がありません: {symbol}")
        return len(re.findall(r"^\s*\{.*\},\s*$", match.group(1), re.MULTILINE))

    current_items = define_count("COLLECTION_ITEM_COUNT")
    current_forms = define_count("COLLECTION_FORM_COUNT")
    if current_items != 999 or current_forms != 388 \
            or initializer_count("gCollectionItemRows") != current_items \
            or initializer_count("gCollectionFormRows") != current_forms:
        _fail("Collection Supply generated count/row数が不一致です")
    configured_counts = config.get("counts", {})
    if configured_counts.get("items") != current_items \
            or configured_counts.get("forms") != current_forms:
        _fail("Collection Supply config/generated countが不一致です")

    allocations = allocation.get("allocations")
    if not isinstance(allocations, list):
        _fail("Stage65 allocation一覧がありません")
    payloads = [
        row for row in allocations
        if isinstance(row, dict)
        and row.get("name") == "collection_supply_v1_stage56_payload"
    ]
    if len(payloads) != 1:
        _fail("Collection Supply Stage65 allocationが一意ではありません")
    payload = payloads[0]
    start = _integer(payload.get("start"), "Collection Supply allocation start")
    end = _integer(
        payload.get("end_exclusive"), "Collection Supply allocation end"
    )
    if start < 0 or end <= start or end > len(rom) \
            or end - start != _integer(payload.get("size"), "payload size"):
        _fail("Collection Supply Stage65 payload geometryが不一致です")
    if payload.get("size") != 58800 or start != 20994544:
        _fail("Collection Supply Stage65 payload geometryが想定値から変わりました")
    stage56_rom = _regular_file(root, STAGE56_ROM, "Stage56 Collection Supply ROM")
    if len(stage56_rom) != len(rom) \
            or _sha256(stage56_rom[start:end]) != payload.get("content_sha256"):
        _fail("Collection Supply Stage56 original payload identityが不一致です")
    stage65_payload_sha256 = _sha256(rom[start:end])

    source_snippets = (
        "typedef struct CollectionItemRow {",
        "typedef struct CollectionFormRow {",
        "if (item >= COLLECTION_ITEM_COUNT)",
        "gVegaModernSaveData->item_obtained_flags[item >> 3]",
        "row = &gCollectionItemRows[item_index];",
        "row = &gCollectionFormRows[form_index];",
        "for (index = 0u; index < COLLECTION_ITEM_COUNT; ++index)",
    )
    builder_snippets = (
        'f"#define COLLECTION_FORM_COUNT {len(model[\'forms\'])}u"',
        'f"#define COLLECTION_ITEM_COUNT {len(model[\'items\'])}u"',
        '"static const CollectionItemRow gCollectionItemRows[] = {"',
        '"static const CollectionFormRow gCollectionFormRows[] = {"',
    )
    missing_source = [value for value in source_snippets if value not in source_text]
    missing_builder = [value for value in builder_snippets if value not in builder_text]
    if missing_source or missing_builder:
        _fail(
            "Collection Supply consumer/builder anchorが変わりました: "
            f"source={missing_source}, builder={missing_builder}"
        )

    item_row_size = 12
    form_row_size = 12
    item_new_count = 1044
    mega_form_new_count = 437
    rows = {
        "item_rows": {
            "symbol": "gCollectionItemRows",
            "current_count": current_items,
            "new_count": item_new_count,
            "stride_bytes": item_row_size,
            "current_fixed_bytes": current_items * item_row_size,
            "new_fixed_bytes": item_new_count * item_row_size,
            "fixed_delta_bytes": (item_new_count - current_items) * item_row_size,
            "new_name_blob_bytes": None,
            "classification": CLASS_ENGINE,
            "required_action": "45 Itemの供給policy・名称をmaterializeしてoverlayを再link",
        },
        "mega_form_rows_if_adopted": {
            "symbol": "gCollectionFormRows",
            "current_count": current_forms,
            "new_count": mega_form_new_count,
            "stride_bytes": form_row_size,
            "current_fixed_bytes": current_forms * form_row_size,
            "new_fixed_bytes": mega_form_new_count * form_row_size,
            "fixed_delta_bytes": (mega_form_new_count - current_forms) * form_row_size,
            "new_name_blob_bytes": None,
            "conditional": True,
            "included_record_scope": "49 battle-only Mega; Winds/Waves 3 Speciesは自動追加しない",
            "classification": CLASS_ENGINE,
            "required_action": "form acquisition policy採用時だけ49 rowと名称をmaterialize",
        },
    }
    identities = {
        "config": config_identity,
        "generated_header": _identity(root, header_path, "Collection Supply header"),
        "source": _identity(root, source_path, "Collection Supply source"),
        "builder": _identity(root, builder_path, "Collection Supply builder"),
        "stage56_rom": _identity(root, STAGE56_ROM, "Stage56 Collection Supply ROM"),
    }
    fingerprint = {
        "payload": {
            "start": start,
            "end_exclusive": end,
            "size": end - start,
            "stage56_original_sha256": payload.get("content_sha256"),
            "stage65_current_sha256": stage65_payload_sha256,
            "downstream_mutated": stage65_payload_sha256
            != payload.get("content_sha256"),
        },
        "tables": rows,
        "identities": identities,
    }
    return {
        "status": "DERIVED_OVERLAY_REBUILD_REQUIRED",
        "stage65_payload": fingerprint["payload"],
        "tables": rows,
        "item_obtained_accessor": {
            "current_bitmap_bytes": 125,
            "new_bitmap_bytes": 131,
            "direct_index_by_item_id": True,
            "sidecar_aware_accessor_patch_required": True,
            "classification": CLASS_SAVE,
        },
        "required_item_fixed_delta_bytes_excluding_names": 540,
        "conditional_mega_fixed_delta_bytes_excluding_names": 588,
        "maximum_fixed_delta_bytes_excluding_names": 1128,
        "not_in_known_fixed_relocation_bundle": True,
        "reason": "overlay code/dataは独立moduleとして一体再link/repackが必要",
        "source_anchor_counts": {
            "runtime_source": len(source_snippets),
            "builder": len(builder_snippets),
        },
        "inputs": identities,
        "inventory_sha256": _sha256(canonical_json_bytes(fingerprint)),
    }


def _build_tables(
    root: Path, capacity: Mapping[str, Any], stage65_rom: bytes
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    stage06, _ = _json(root, "build/stages/06_battle_core.json", "Stage06 metadata")
    stage09, _ = _json(root, STAGE09_METADATA, "Stage09 metadata")
    stage39, _ = _json(root, STAGE39_METADATA, "Stage39 metadata")
    hotfix, _ = _json(
        root,
        STAGE61_HOTFIX,
        "Stage61 runtime table metadata",
    )
    p01_runtime, _ = _json(
        root, "config/modernization_p01_runtime.json", "P01 collection runtime contract"
    )

    runtime = stage06.get("runtime_tables", {})
    surface_entries = {
        str(row.get("name")): row
        for row in stage09.get("allocation", {}).get("entries", [])
    }
    stage39_tables = stage39.get("runtime", {}).get("tables", {})
    if not isinstance(runtime, dict) or not isinstance(stage39_tables, dict):
        _fail("table metadata構造が不正です")
    hotfix_addresses = hotfix.get("addresses", {})
    if not isinstance(hotfix_addresses, dict):
        _fail("Stage61 hotfix address契約がありません")

    def runtime_table(name: str, domain: str, new_count: int) -> dict[str, Any]:
        row = runtime.get(name)
        if not isinstance(row, dict):
            _fail(f"Stage06 runtime tableがありません: {name}")
        old_count = _integer(row.get("count"), f"{name} count")
        stride = _integer(row.get("stride"), f"{name} stride")
        size = _integer(row.get("size"), f"{name} size")
        if old_count * stride != size:
            _fail(f"Stage06 runtime table shape不一致です: {name}")
        return _table_row(
            table_key=name,
            domain=domain,
            address=_integer(row.get("address"), f"{name} address"),
            old_count=old_count,
            new_count=new_count,
            stride=stride,
        )

    tables = [
        runtime_table("move_names", "move", 1064),
        runtime_table("move_data", "move", 1064),
        runtime_table("move_descriptions", "move", 1064),
        runtime_table("move_animations", "move", 1064),
        runtime_table("ability_names", "ability", 318),
        runtime_table("ability_descriptions", "ability", 318),
        runtime_table("item_data", "item", 1044),
        runtime_table("item_graphics", "item", 1044),
    ]
    base = capacity.get("runtime_tables", {}).get("species_base_stats")
    if not isinstance(base, dict):
        _fail("P01 species base stats tableがありません")
    tables.append(
        _table_row(
            table_key="species_base_stats",
            domain="species_form",
            address=_integer(base.get("address"), "base stats address"),
            old_count=1621,
            new_count=1673,
            stride=32,
            notes=("BaseStatsのAbility/held item fieldはu16、type/stat fieldはu8",),
        )
    )

    surface_shapes = {
        "front": (8, 1621, 1673),
        "back": (8, 1621, 1673),
        "palette": (8, 1621, 1673),
        "shiny_palette": (8, 1621, 1673),
        "icon": (4, 1621, 1673),
        "icon_palette": (1, 1621, 1673),
        "front_coords": (4, 1621, 1673),
        "back_coords": (4, 1621, 1673),
        "elevation": (1, 1621, 1673),
        "footprint": (4, 1621, 1673),
        "cry": (12, 1621, 1673),
        "cry2": (12, 1621, 1673),
        "dex_entries": (28, 1621, 1673),
        "national_dex": (2, 1621, 1673),
        "national_dex_runtime": (2, 1620, 1672),
        "evolutions": (128, 1621, 1673),
        "level_up_pointers": (4, 1621, 1673),
        "tmhm": (16, 1621, 1673),
        "tutor": (16, 1621, 1673),
        "species_names": (11, 1621, 1673),
        "species_names_legacy": (8, 1621, 1673),
    }
    for name, (stride, old_count, new_count) in surface_shapes.items():
        source = surface_entries.get(name)
        if not isinstance(source, dict):
            _fail(f"Stage09 surface tableがありません: {name}")
        old_size = _integer(source.get("size"), f"{name} size")
        if old_size != old_count * stride:
            _fail(
                f"Stage09 surface shape不一致です: {name}: "
                f"{old_size} != {old_count}*{stride}"
            )
        notes: list[str] = []
        if name in {"tmhm", "tutor"}:
            notes.append("現行128-bit rowを維持する条件付きgeometry")
            if name == "tutor":
                notes.append("runtime到達可能なのは下位64 bitだけで上位64 bitは空き扱い禁止")
        if name == "icon_palette":
            notes.append("u8はpalette selectorでありSpecies ID格納欄ではない")
        if name == "national_dex_runtime":
            notes.append("SPECIES_NONEを除く1620→1672 row")
        active_address = _integer(source.get("address"), f"{name} address")
        active_source = "STAGE09_SPECIES_SURFACE"
        if name == "level_up_pointers":
            active_address = _integer(
                stage39_tables.get("level_up_pointers", {}).get("address"),
                "Stage39 level pointer address",
            )
            active_source = "STAGE39_MOVE_DISTRIBUTION_V4"
        elif name == "tmhm":
            active_address = _integer(
                hotfix_addresses.get("compatibility"),
                "Stage61 TM/HM compatibility address",
            )
            active_source = "STAGE61_RUNTIME_HOTFIX"
        elif name == "tutor":
            active_address = _integer(
                stage39_tables.get("tutor", {}).get("address"),
                "Stage39 tutor compatibility address",
            )
            active_source = "STAGE39_MOVE_DISTRIBUTION_V4"
        table = _table_row(
            table_key=f"species_{name}" if name != "evolutions" else "evolution",
            domain="species_form",
            address=active_address,
            old_count=old_count,
            new_count=new_count,
            stride=stride,
            notes=notes,
        )
        table["active_address_source"] = active_source
        table["stage09_original_address"] = _integer(
            source.get("address"), f"{name} Stage09 address"
        )
        tables.append(table)

    wild = stage39_tables.get("wild_table")
    if not isinstance(wild, dict) or _integer(wild.get("size"), "wild size") != 1621 * 8:
        _fail("Stage39 wild table shape不一致です")
    tables.append(
        _table_row(
            table_key="species_wild_table",
            domain="species_form",
            address=_integer(wild.get("address"), "wild address"),
            old_count=1621,
            new_count=1673,
            stride=8,
        )
    )

    offsets_identity = _pinned_local_identity(
        root, CFRU_OFFSETS, "CFRU compiled offsets"
    )
    offsets_text = _regular_file(root, CFRU_OFFSETS, "CFRU compiled offsets").decode(
        "utf-8"
    )
    for table_key, spec in sorted(ANCILLARY_TABLE_SPECS.items()):
        symbol = str(spec["symbol"])
        address = _integer(spec["address"], f"{symbol} address")
        match = re.search(
            rf"^{re.escape(symbol)}:\s+([0-9A-Fa-f]{{8}})\s*$",
            offsets_text,
            re.MULTILINE,
        )
        if match is None or int(match.group(1), 16) != address:
            _fail(f"CFRU offsetsの補助table addressが不一致です: {symbol}")
        old_count = _integer(spec["old_count"], f"{symbol} old count")
        stride = _integer(spec["stride"], f"{symbol} stride")
        offset = address - ROM_BASE
        if offset < 0 or offset + old_count * stride > len(stage65_rom):
            _fail(f"Stage65補助tableがROM外です: {symbol}")
        slice_sha256 = _sha256(stage65_rom[offset : offset + old_count * stride])
        if slice_sha256 != spec["sha256"]:
            _fail(
                f"Stage65補助table slice hashが不一致です: {symbol}: {slice_sha256}"
            )
        table = _table_row(
            table_key=table_key,
            domain=str(spec["domain"]),
            address=address,
            old_count=old_count,
            new_count=_integer(spec["new_count"], f"{symbol} new count"),
            stride=stride,
            notes=(
                f"compiled symbol={symbol}",
                "main runtime_tables外だがcanonical IDで直接添字アクセスされる補助表",
            ),
        )
        table["compiled_symbol"] = symbol
        if "extent_end_address" in spec:
            extent_end = _integer(
                spec["extent_end_address"], f"{symbol} extent end"
            )
            next_symbol = str(spec.get("extent_next_symbol", ""))
            next_match = re.search(
                rf"^{re.escape(next_symbol)}:\s+([0-9A-Fa-f]{{8}})\s*$",
                offsets_text,
                re.MULTILINE,
            )
            if address + old_count * stride != extent_end \
                    or next_match is None \
                    or int(next_match.group(1), 16) != extent_end:
                _fail(f"{symbol} implicit compiled extentが不一致です")
            table["compiled_extent_end_address"] = extent_end
            table["compiled_extent_next_symbol"] = next_symbol
            table["compiled_extent_evidence"] = "ADJACENT_NEXT_SYMBOL"
        if symbol == "gMoldBreakerIgnoredAbilities":
            table["new_rows_default_fill_authorized"] = False
            table["new_rows_required_action"] = (
                "新Ability 6件ごとにMold Breaker無視対象かをsemantic reviewして明示値を生成"
            )
        table["compiled_offsets_input"] = offsets_identity
        table["expected_stage65_old_slice_sha256"] = spec["sha256"]
        tables.append(table)

    form = stage39_tables.get("form_table")
    if not isinstance(form, dict) or _integer(form.get("size"), "form size") != 509 * 14:
        _fail("Stage39 form table shape不一致です")
    tables.append(
        _table_row(
            table_key="form_resolution",
            domain="species_form",
            address=_integer(form.get("address"), "form address"),
            old_count=509,
            new_count=558,
            stride=14,
            count_semantics="FORM_RESOLUTION_RECORDS_509_PLUS_49_MEGA",
            notes=("3 Winds/Waves base Speciesはform resolution追加対象外",),
        )
    )

    acquisition = p01_runtime.get("runtime_table")
    if not isinstance(acquisition, dict) \
            or _integer(acquisition.get("row_count"), "acquisition rows") != 1621 \
            or _integer(acquisition.get("row_size"), "acquisition stride") != 8:
        _fail("P01 acquisition collection table shape不一致です")
    tables.append(
        _table_row(
            table_key="acquisition_collection_defs",
            domain="species_form",
            address=ROM_BASE + _integer(
                acquisition.get("rom_offset"), "acquisition table offset"
            ),
            old_count=1621,
            new_count=1673,
            stride=8,
            notes=("新52件のcollection ledger bit採用可否は未決定",),
        )
    )

    expected_size_by_key = {
        "species_level_up_pointers": _integer(
            stage39_tables.get("level_up_pointers", {}).get("size"),
            "Stage39 level pointer size",
        ),
        "form_resolution": _integer(form.get("size"), "Stage39 form size"),
    }
    for table in tables:
        key = str(table["table_key"])
        if key in expected_size_by_key \
                and table["old_size_bytes"] != expected_size_by_key[key]:
            _fail(f"active logical table size不一致です: {key}")

    variable = [
        {
            "component_key": "level_up_data",
            "current_size_bytes": capacity["logical_capacity"]["level_up"][
                "declared_data_bytes"
            ],
            "free_trailing_bytes": 0,
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "新Species learnsetとMove1063 route payloadが未materialize",
        },
        {
            "component_key": "egg_moves",
            "current_size_bytes": capacity["logical_capacity"]["egg_moves"][
                "declared_bytes"
            ],
            "free_trailing_bytes": 0,
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "Move1063 egg/shared-egg routeを含む可変長payloadが未materialize",
        },
        {
            "component_key": "move_description_blob",
            "current_size_bytes": runtime.get("gMoveDescriptionBlob", {}).get("size"),
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "Ally Switch日本語説明未提出",
        },
        {
            "component_key": "ability_description_blob",
            "current_size_bytes": runtime.get("gAbilityDescriptionBlob", {}).get("size"),
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "新Ability 6件の日本語名/説明未提出",
        },
        {
            "component_key": "ally_switch_effect_ai_animation",
            "current_size_bytes": None,
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": (
                "u8 dispatchは256枠でappend不可。blank 251/252/255のsemantic再利用、"
                "target/flags/script/animation/AI specificationが未確定"
            ),
        },
        {
            "component_key": "new_ability_effect_ai",
            "current_size_bytes": None,
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "6 Abilityのeffect/AI portとsemantic review未実施",
        },
        {
            "component_key": "mega_form_runtime",
            "current_size_bytes": surface_entries.get("species_runtime", {}).get("size"),
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "49 Megaのchange condition・battle-exit normalization未実装",
        },
        {
            "component_key": "species_graphics_payload",
            "current_size_bytes": None,
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": "Winds/Waves 3件欠落、全species graphicsの圧縮/link未実施",
        },
        {
            "component_key": "machine_and_tutor_catalog_policy",
            "current_size_bytes": 128 * 2 + 64 * 2,
            "new_size_bytes": None,
            "classification": CLASS_ENGINE,
            "reason": (
                "TM120+HM8/Tutor64は満杯。Move1063 routeを置換・増設・非採用の"
                "どれにするか未決定"
            ),
        },
    ]
    catalog_audit = {
        "tm_hm": {
            "current_slots": 128,
            "free_slots": 0,
            "catalog_address": _integer(hotfix_addresses.get("tmhm"), "TM/HM address"),
            "compatibility_row_bits": 128,
            "append_slot_classification": CLASS_ENGINE,
        },
        "tutor": {
            "current_slots": 64,
            "free_slots": 0,
            "catalog_address": _integer(hotfix_addresses.get("tutor"), "tutor address"),
            "physical_compatibility_row_bits": 128,
            "runtime_reachable_bits": 64,
            "dormant_upper_bits_are_free": False,
            "append_slot_classification": CLASS_ENGINE,
        },
    }
    for table in tables:
        address = _integer(table["current_address"], "current table address")
        offset = address - ROM_BASE
        size = _integer(table["old_size_bytes"], "current table size")
        if offset < 0 or offset + size > len(stage65_rom):
            _fail(f"fixed tableがStage65 ROM外です: {table['table_key']}")
        raw = stage65_rom[offset : offset + size]
        table["stage65_old_slice_sha256"] = _sha256(raw)
        table["stage65_old_slice_non_erased_bytes"] = sum(value != 0xFF for value in raw)
        table["stage65_old_slice_measured"] = True
    return sorted(tables, key=lambda row: row["table_key"]), variable, catalog_audit


def audit_mega_evolution_slots(
    rom: bytes,
    species_manifest: Sequence[Mapping[str, Any]],
    species_reservations: Sequence[Mapping[str, Any]],
    *,
    evolution_address: int,
) -> dict[str, Any]:
    """49 Mega条件を置く既存48 base rowの連続空slotを実ROMで検証する。"""

    species_ids = {
        str(row.get("species_key")): _integer(row.get("id"), "species manifest id")
        for row in species_manifest
    }
    mega_rows = [
        row for row in species_reservations
        if row.get("classification") == "BATTLE_ONLY_MEGA"
    ]
    if len(mega_rows) != 49:
        _fail(f"Mega reservationが49件ではありません: {len(mega_rows)}")
    required_by_base: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in mega_rows:
        base_key = str(row.get("source_species_key", ""))
        if base_key not in species_ids:
            _fail(f"Mega source base keyが現行manifestにありません: {base_key}")
        required_by_base[base_key].append(row)
    if len(required_by_base) != 48:
        _fail(f"Mega source baseが48件ではありません: {len(required_by_base)}")

    table_offset = evolution_address - ROM_BASE
    row_stride = 16 * 8
    table_bytes = 1621 * row_stride
    if table_offset < 0 or table_offset + table_bytes > len(rom):
        _fail("evolution tableがStage65 ROM外です")
    output_rows: list[dict[str, Any]] = []
    for base_key, targets in sorted(required_by_base.items()):
        species_id = species_ids[base_key]
        raw = rom[
            table_offset + species_id * row_stride:
            table_offset + (species_id + 1) * row_stride
        ]
        entries = [struct.unpack_from("<HHHH", raw, slot * 8) for slot in range(16)]
        free_indices = [slot for slot, entry in enumerate(entries) if entry[0] == 0]
        if any(entries[slot][2] or entries[slot][3] for slot in free_indices):
            _fail(f"EVO_NONE rowにtarget/extra residueがあります: {base_key}")
        first_free = free_indices[0] if free_indices else 16
        if any(entry[0] != 0 for entry in entries[first_free + 1:]):
            _fail(f"EVO_NONE後にbattle-visible rowがあります: {base_key}")
        used = 16 - len(free_indices)
        required = len(targets)
        free = len(free_indices)
        if free < required:
            _fail(
                f"Mega evolution row空き不足です: {base_key}: "
                f"required={required}, free={free}"
            )
        output_rows.append(
            {
                "source_species_key": base_key,
                "source_species_id": species_id,
                "current_used_slots": used,
                "current_free_slots": free,
                "current_free_slot_indices": free_indices,
                "current_free_parameter_residue_count": sum(
                    entries[slot][1] != 0 for slot in free_indices
                ),
                "required_mega_rows": required,
                "remaining_slots_after_reservation": free - required,
                "target_species_keys": sorted(
                    str(row.get("species_key")) for row in targets
                ),
                "target_species_ids": sorted(
                    _integer(row.get("id"), "reserved target species id")
                    for row in targets
                ),
                "mega_stone_keys": sorted(
                    str(row.get("mega_stone_key")) for row in targets
                ),
                "slot_capacity_sufficient": True,
            }
        )
    raichu = next(
        row for row in output_rows
        if row["source_species_key"] == "SPECIES_KEY_RAICHU"
    )
    if raichu["required_mega_rows"] != 2:
        _fail("Raichu X/Yの2-row要件が失われています")
    return {
        "status": "ROW_SLOT_CAPACITY_SUFFICIENT_CONTENT_UNMATERIALIZED",
        "table_address": evolution_address,
        "table_address_hex": f"0x{evolution_address:08X}",
        "row_stride_bytes": row_stride,
        "slots_per_species": 16,
        "slot_stride_bytes": 8,
        "source_base_count": len(output_rows),
        "required_mega_row_count": sum(
            row["required_mega_rows"] for row in output_rows
        ),
        "minimum_current_free_slots": min(
            row["current_free_slots"] for row in output_rows
        ),
        "minimum_remaining_slots_after_reservation": min(
            row["remaining_slots_after_reservation"] for row in output_rows
        ),
        "raichu_required_rows": raichu["required_mega_rows"],
        "raichu_current_free_slots": raichu["current_free_slots"],
        "classification": CLASS_ENGINE,
        "content_materialized": False,
        "rows": output_rows,
        "inventory_sha256": _sha256(canonical_json_bytes(output_rows)),
    }


def _numeric_width_audit() -> list[dict[str, Any]]:
    rows = [
        {
            "field": "BoxPokemon.substruct0.species",
            "storage": "u16",
            "required_max": 1672,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "BoxPokemon.substruct0.heldItem",
            "storage": "u16",
            "required_max": 1043,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "BoxPokemon.substruct1.moves[4]",
            "storage": "u16",
            "required_max": 1063,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "PokemonSubstruct3.abilityNum/hiddenAbility",
            "storage": "1-bit selection flags",
            "required_max": 1,
            "limit": 1,
            "classification": CLASS_SIMPLE,
            "guard": "canonical Ability IDを書かずSpecies tableからu16導出",
        },
        {
            "field": "BattlePokemon.ability",
            "storage": "u16",
            "required_max": 317,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "BattlePokemon.oldAbility",
            "storage": "u8 legacy field",
            "required_max": 317,
            "limit": 255,
            "classification": CLASS_ENGINE,
            "active_reachability": "NO_DIRECT_PINNED_SOURCE_REFERENCE_FOUND",
            "reason": "linked imageで非到達またはu16 replacement済みであることの回帰証明が必要",
        },
        {
            "field": "BattleStruct.abilityPreventingSwitchout",
            "storage": "u8 legacy field; NewBattleStruct counterpart is u16",
            "required_max": 317,
            "limit": 255,
            "classification": CLASS_ENGINE,
            "active_reachability": "LEGACY_DECLARATION_PRESENT_ACTIVE_PATH_USES_GNEWBS",
            "reason": "gBattleStruct側へ高IDが流れないことをlinked ABI testで固定する",
        },
        {
            "field": "VegaEncounterRequest/PendingEncounter.species/form",
            "storage": "u16",
            "required_max": 1672,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "VegaEncounterRequest/PendingEncounter.ability",
            "storage": "u8 slot selector",
            "required_max": 2,
            "limit": 255,
            "classification": CLASS_SIMPLE,
            "guard": "canonical Ability IDではなくprimary/secondary/hiddenの選択値だけを保存",
        },
        {
            "field": "BaseStats.item1/item2/ability1/ability2/hiddenAbility",
            "storage": "u16",
            "required_max": 1043,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
            "note": "Ability側required maxは317",
        },
        {
            "field": "BattleMove.effect",
            "storage": "u8",
            "required_max": None,
            "limit": 255,
            "classification": CLASS_ENGINE,
            "current_dispatch_entries": 256,
            "blank_semantic_candidate_ids": [251, 252, 255],
            "excluded_candidate_id": 254,
            "reason": (
                "append容量はないがblank semantic枠候補あり。専用dispatch script/AI/target"
                "処理を確定するまでID未割当。既存effectへの近似は禁止"
            ),
        },
        {
            "field": "BattleMove.type/target/flags/power/pp/accuracy/secondaryChance",
            "storage": "u8 (priorityはs8)",
            "required_max": None,
            "limit": 255,
            "classification": CLASS_ENGINE,
            "reason": "P05でtarget/effect/flags/secondary/animation等が未提出",
        },
        {
            "field": "TM/HM compatibility per Species",
            "storage": "128-bit fixed row",
            "required_max": 127,
            "limit": 127,
            "classification": CLASS_ENGINE,
            "reason": "現行128 slot満杯、Move1063 machine route方針未決定",
        },
        {
            "field": "Tutor compatibility per Species",
            "storage": "128-bit physical / 64-bit reachable",
            "required_max": None,
            "limit": 63,
            "classification": CLASS_ENGINE,
            "reason": "現行64 runtime slot満杯、上位64 bitはengine patchなしに使用不可",
        },
        {
            "field": "Egg move Species header",
            "storage": "u16 value=20000+species_id",
            "required_max": 21672,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "form resolution canonical/base/level/egg/tm/wild/action",
            "storage": "u16",
            "required_max": 1672,
            "limit": U16_MAX,
            "classification": CLASS_SIMPLE,
        },
        {
            "field": "species icon palette row",
            "storage": "u8 palette selector",
            "required_max": None,
            "limit": 255,
            "classification": CLASS_SIMPLE,
            "guard": "Species IDそのものをu8へ格納する欄ではない",
        },
        {
            "field": "CodexBattlePublicEventV2.last_item_id",
            "storage": "10-bit transient public event ABI",
            "required_max": 1043,
            "limit": 1023,
            "classification": CLASS_ENGINE,
            "abi_change_required": True,
            "persistent_save_field": False,
            "current_total_event_bits": 88,
            "required_total_event_bits": 89,
            "current_event_bytes": 11,
            "minimum_required_event_bytes": 12,
            "event_capacity": 4,
            "minimum_public_state_growth_bytes": 4,
            "reason": (
                "Item ID 1024..1043を現行pack_bits幅では切り捨てる。11-bit化すると"
                "eventは88→89 bit/11→12 byteとなり4-event ringと後続offsetのABI更新が必要"
            ),
        },
        {
            "field": "MirageProduction_Probe.virtual_items_packed",
            "storage": "3 x 10-bit diagnostic probe view",
            "required_max": 1043,
            "limit": 1023,
            "classification": CLASS_ENGINE,
            "abi_change_required": True,
            "persistent_save_field": False,
            "reason": "Probe返値だけが0x3FF maskで切り詰める。内部virtual_itemsはu16",
        },
    ]
    for row in rows:
        required = row.get("required_max")
        row["known_limit_exceeded"] = (
            required is not None
            and _integer(required, f"{row['field']} required max")
            > _integer(row["limit"], f"{row['field']} limit")
        )
        if row["known_limit_exceeded"] and row.get("classification") != CLASS_ENGINE:
            _fail(f"上限超過consumerがENGINE_PATCH_REQUIREDではありません: {row['field']}")
    return rows


def _save_abi_audit(
    root: Path, capacity: Mapping[str, Any]
) -> dict[str, Any]:
    save_rows, identity = _csv_rows(root, "config/save_layout.csv", "save layout")
    expected_save_sha = PINNED_LOCAL_INPUT_SHA256["config/save_layout.csv"]
    if identity["sha256"] != expected_save_sha:
        _fail(
            "save layout pinが不一致です: "
            f"expected={expected_save_sha}, actual={identity['sha256']}"
        )
    identity["pin_status"] = "MATCH"
    by_symbol = {row.get("symbol"): row for row in save_rows}
    item = by_symbol.get("itemObtainedFlags_999")
    research = by_symbol.get("OWNER_KEY_RESEARCH_ECONOMY_V1")
    acquisition = by_symbol.get("acquisition_save_block")
    acquisition_reserved = by_symbol.get("reserved_dex_migration")
    reserved_v2_tail = by_symbol.get("reserved_v2_tail")
    if not all(
        isinstance(row, dict)
        for row in (item, research, acquisition, acquisition_reserved, reserved_v2_tail)
    ):
        _fail("save layoutの必須ownerがありません")
    item_start = int(str(item["start"]), 0)
    item_end = int(str(item["end_exclusive"]), 0)
    research_start = int(str(research["start"]), 0)
    old_item_bytes = math.ceil(999 / 8)
    new_item_bytes = math.ceil(1044 / 8)
    if item_end - item_start != old_item_bytes or research_start != item_end:
        _fail("itemObtainedFlagsと後続ownerのlayoutが想定と不一致です")
    acq_start = int(str(acquisition["start"]), 0)
    acq_end = int(str(acquisition["end_exclusive"]), 0)
    reserved_start = int(str(acquisition_reserved["start"]), 0)
    reserved_end = int(str(acquisition_reserved["end_exclusive"]), 0)
    if acq_end - acq_start != 240 or reserved_start != acq_end \
            or reserved_end - reserved_start != 15:
        _fail("acquisition save owner/reserved geometryが想定と不一致です")
    tail_start = int(str(reserved_v2_tail["start"]), 0)
    tail_end = int(str(reserved_v2_tail["end_exclusive"]), 0)
    if tail_start != 0x2697 or tail_end != 0x2718 \
            or tail_end - tail_start != 129:
        _fail("reserved_v2_tail geometryが想定と不一致です")
    dex = capacity.get("save_layout", {}).get("legacy_dex_bitmaps")
    if not isinstance(dex, list) or len(dex) != 4:
        _fail("P01 legacy dex bitmap監査がありません")
    return {
        "input": identity,
        "persistent_mon_numeric_fields": {
            "species_u16_max": 1672,
            "move_u16_max": 1063,
            "held_item_u16_max": 1043,
            "ability_storage": "selection bits; canonical ID is table-derived u16",
            "numeric_width_classification": CLASS_SIMPLE,
            "required_runtime_tests": [
                "new_base_species_1672_save_load_roundtrip",
                "move_1063_save_load_roundtrip",
                "held_item_1043_save_load_roundtrip",
                "ability_317_species_derivation_and_battle_roundtrip",
                "battle_only_mega_reverts_before_persistent_save_and_facility_resume",
            ],
        },
        "item_obtained_bitmap": {
            "current_item_count": 999,
            "new_item_count": 1044,
            "current_bytes": old_item_bytes,
            "new_bytes": new_item_bytes,
            "delta_bytes": new_item_bytes - old_item_bytes,
            "current_storage_bits": old_item_bytes * 8,
            "current_unused_padding_bits": old_item_bytes * 8 - 999,
            "new_storage_bits": new_item_bytes * 8,
            "new_unused_padding_bits": new_item_bytes * 8 - 1044,
            "first_reserved_id_uses_existing_padding_bit": 999,
            "reserved_ids_requiring_new_bytes": [1000, 1043],
            "reserved_id_count_requiring_new_bytes": 44,
            "reserved_ids_exceeding_10_bit_telemetry": [1024, 1043],
            "reserved_id_count_exceeding_10_bit_telemetry": 20,
            "current_start": item_start,
            "current_end_exclusive": item_end,
            "adjacent_following_owner": research.get("owner"),
            "adjacent_free_bytes": research_start - item_end,
            "in_place_append_possible": False,
            "classification": CLASS_SAVE,
            "required": "version bump、owner再配置または別bitmap owner、旧125 byte zero-extend migration",
            "non_binding_sidecar_candidate": {
                "source_owner": reserved_v2_tail.get("owner"),
                "source_symbol": reserved_v2_tail.get("symbol"),
                "source_start": tail_start,
                "source_end_exclusive": tail_end,
                "source_bytes": tail_end - tail_start,
                "candidate_start": tail_start,
                "candidate_end_exclusive": tail_start + (new_item_bytes - old_item_bytes),
                "candidate_bytes": new_item_bytes - old_item_bytes,
                "remaining_reserved_bytes": (
                    tail_end - tail_start - (new_item_bytes - old_item_bytes)
                ),
                "binding_allocation": False,
                "save_layout_mutated": False,
                "requires": (
                    "owner version/migrationと125-byte本体+6-byte sidecarを読む"
                    "segment-aware accessor"
                ),
            },
        },
        "acquisition_collection": {
            "current_canonical_species_rows": 1621,
            "new_canonical_species_rows": 1673,
            "current_ledger_bits": 1216,
            "new_ledger_bits": None,
            "additional_bits_range": [0, 52],
            "current_collection_bytes": 152,
            "maximum_collection_bytes_if_all_reserved_ids_tracked": 159,
            "maximum_delta_bytes": 7,
            "current_owner_bytes": 240,
            "following_explicit_reserved_bytes": 15,
            "same_outer_offset_envelope_can_fit_maximum": True,
            "classification": CLASS_SAVE,
            "required": (
                "52件ごとのcollection/completion policy決定、Acquisition block version migration、"
                "最大7 byte分を15-byte予約から再配分する設計"
            ),
        },
        "legacy_dex": {
            "bitmap_count": 4,
            "bytes_per_bitmap": 52,
            "representable_species_ids": [0, 411],
            "new_reserved_ids_outside_legacy_scope": 52,
            "classification": CLASS_SAVE,
            "required": (
                "legacy bitmapを拡張せず、stable species/form keyに対応するmodern collection ownerへ"
                "明示mappingする"
            ),
        },
        "battle_only_mega_policy": {
            "reserved_ids": 49,
            "persistent_numeric_width_sufficient": True,
            "classification": CLASS_ENGINE,
            "required": "battle終了/中断/facility再開時のbase form復帰とsave非残存を実ROM検証",
        },
        "outer_save_layout_mutated": False,
    }


def validate_checkpoint_document(document: Mapping[str, Any]) -> None:
    """生成済みcheckpointの内部算術とfail-closed markerを検証する。"""

    if document.get("schema_version") != SCHEMA_VERSION \
            or document.get("task") != TASK \
            or document.get("status") != CHECKPOINT_STATUS:
        _fail("checkpoint header/statusが不正です")
    if document.get("runtime_ready") is not False \
            or document.get("rom_mutated") is not False \
            or document.get("save_mutated") is not False \
            or document.get("shared_manifests_mutated") is not False:
        _fail("checkpointがruntime反映済みを誤って宣言しています")

    reservations = document.get("id_reservations")
    if not isinstance(reservations, dict):
        _fail("id_reservationsがありません")
    for domain, expected in MANIFEST_SPACES.items():
        group = reservations.get(domain)
        if not isinstance(group, dict):
            _fail(f"reservation domainがありません: {domain}")
        rows = group.get("rows")
        if not isinstance(rows, list) or len(rows) != expected["append_count"]:
            _fail(f"reservation件数不一致です: {domain}")
        keys = [str(row.get(expected["key_field"], "")) for row in rows]
        ids = [_integer(row.get("id"), f"{domain} reservation id") for row in rows]
        _require_unique(keys, f"{domain} reservation key")
        wanted = list(
            range(expected["current_count"], expected["current_count"] + len(rows))
        )
        if ids != wanted or group.get("reserved_start_id") != wanted[0] \
                or group.get("reserved_end_id") != wanted[-1] \
                or group.get("new_count") != expected["current_count"] + len(rows):
            _fail(f"reservation範囲/連続性不一致です: {domain}")
        if any(row.get("materialization_ready") is not False for row in rows):
            _fail(f"未完成reservationがmaterialization readyです: {domain}")
        if max(ids) > U16_MAX:
            _fail(f"reservationがu16を超えます: {domain}")

    tables = document.get("table_capacity")
    if not isinstance(tables, dict) or not isinstance(tables.get("fixed_tables"), list):
        _fail("fixed table capacityがありません")
    table_keys: list[str] = []
    for row in tables["fixed_tables"]:
        key = str(row.get("table_key", ""))
        table_keys.append(key)
        old_count = _integer(row.get("old_count"), f"{key} old count")
        new_count = _integer(row.get("new_count"), f"{key} new count")
        stride = _integer(row.get("stride_bytes"), f"{key} stride")
        if row.get("old_size_bytes") != old_count * stride \
                or row.get("new_size_bytes") != new_count * stride \
                or row.get("delta_bytes") != (new_count - old_count) * stride \
                or row.get("relocation_required") is not True \
                or row.get("in_place_append_authorized") is not False:
            _fail(f"fixed table算術/relocation marker不一致です: {key}")
        if row.get("classification") != CLASS_ENGINE \
                or row.get("stage65_old_slice_measured") is not True \
                or not row.get("stage65_old_slice_sha256"):
            _fail(f"fixed tableの実測/classificationが不正です: {key}")
        if key == "ability_mold_breaker_ignored" \
                and (
                    row.get("new_rows_default_fill_authorized") is not False
                    or row.get("compiled_extent_evidence")
                    != "ADJACENT_NEXT_SYMBOL"
                ):
            _fail("Mold Breaker補助表のsemantic/extent gateが不正です")
    _require_unique(table_keys, "fixed table key")
    if len(table_keys) != 39 \
            or not set(ANCILLARY_TABLE_SPECS).issubset(table_keys) \
            or tables.get("known_fixed_old_bytes") != sum(
                row["old_size_bytes"] for row in tables["fixed_tables"]
            ) \
            or tables.get("known_fixed_new_bytes") != sum(
                row["new_size_bytes"] for row in tables["fixed_tables"]
            ) \
            or tables.get("known_fixed_delta_bytes") != sum(
                row["delta_bytes"] for row in tables["fixed_tables"]
            ):
        _fail("fixed table集合または合計byte数が不一致です")
    if (
        tables["known_fixed_old_bytes"],
        tables["known_fixed_new_bytes"],
        tables["known_fixed_delta_bytes"],
    ) != (655852, 676757, 20905):
        _fail("fixed table既知geometryが想定値から変わりました")
    variable_rows = tables.get("variable_or_policy_blocked_components")
    if not isinstance(variable_rows, list):
        _fail("可変長/方針未確定component一覧がありません")
    variable_by_key = {
        str(row.get("component_key")): row
        for row in variable_rows if isinstance(row, dict)
    }
    if len(variable_by_key) != len(variable_rows):
        _fail("可変長/方針未確定component keyが空または重複です")
    stone_graphics = variable_by_key.get("mega_stone_icon_palette_payload")
    stone_semantics = variable_by_key.get("mega_stone_item_description_effect")
    if not isinstance(stone_graphics, dict) or not isinstance(stone_semantics, dict) \
            or stone_graphics.get("source_record_count") != 45 \
            or stone_graphics.get("source_icon_bytes") != 12960 \
            or stone_graphics.get("source_palette_bytes") != 1440 \
            or stone_graphics.get("minimum_raw_payload_bytes") != 14400 \
            or stone_graphics.get("linked_size_bytes") is not None \
            or stone_semantics.get("source_record_count") != 45 \
            or stone_semantics.get("new_size_bytes") is not None:
        _fail("Mega Stone可変payload容量契約が不正です")

    evolution_slots = tables.get("mega_evolution_slot_capacity")
    if not isinstance(evolution_slots, dict) \
            or evolution_slots.get("source_base_count") != 48 \
            or evolution_slots.get("required_mega_row_count") != 49 \
            or evolution_slots.get("minimum_current_free_slots") != 15 \
            or evolution_slots.get("raichu_required_rows") != 2 \
            or evolution_slots.get("raichu_current_free_slots") != 16 \
            or evolution_slots.get("content_materialized") is not False:
        _fail("Mega evolution row空き監査が不正です")
    evolution_rows = evolution_slots.get("rows")
    if not isinstance(evolution_rows, list) or len(evolution_rows) != 48 \
            or any(
                row.get("slot_capacity_sufficient") is not True
                or row.get("current_free_slots", 0) < row.get("required_mega_rows", 0)
                for row in evolution_rows
            ) \
            or _sha256(canonical_json_bytes(evolution_rows)) \
            != evolution_slots.get("inventory_sha256"):
        _fail("Mega evolution row詳細/hashが不正です")

    generated_items = tables.get("generated_relink_item_index_tables")
    if not isinstance(generated_items, dict) \
            or generated_items.get("status") != "ENGINE_RELINK_REQUIRED" \
            or generated_items.get("current_item_count") != 999 \
            or generated_items.get("new_item_count") != 1044 \
            or generated_items.get("logical_old_bytes") != 1249 \
            or generated_items.get("logical_new_bytes") != 1306 \
            or generated_items.get("logical_delta_bytes") != 57 \
            or generated_items.get("stage65_physical_old_bytes") != 3497 \
            or generated_items.get(
                "stage65_physical_new_bytes_if_all_instances_relinked"
            ) != 3656 \
            or generated_items.get(
                "stage65_physical_delta_bytes_if_all_instances_relinked"
            ) != 159:
        _fail("generated Item index table合計が不正です")
    generated_rows = generated_items.get("tables")
    if not isinstance(generated_rows, list) or len(generated_rows) != 3:
        _fail("generated Item index table集合が不正です")
    expected_instances = {
        "codex_runtime_held_item_safe_bitmap": 1,
        "codex_reward_ball_item_bitmap": 3,
        "codex_reward_ball_type_by_item": 3,
    }
    expected_allocation_names = {
        "codex_runtime_held_item_safe_bitmap": {
            "codex_battle_runtime_stage44_payload"
        },
        "codex_reward_ball_item_bitmap": {
            "codex_battle_rewards_stage45_payload",
            "windows_battle_catalog_stage46_payload",
            "windows_box14_vault_stage47_payload",
        },
        "codex_reward_ball_type_by_item": {
            "codex_battle_rewards_stage45_payload",
            "windows_battle_catalog_stage46_payload",
            "windows_box14_vault_stage47_payload",
        },
    }
    if {str(row.get("table_key")) for row in generated_rows} \
            != set(expected_instances) \
            or any(
                row.get("stage65_instance_count")
                != expected_instances[str(row.get("table_key"))]
                or not isinstance(row.get("stage65_instance_allocations"), list)
                or len(row.get("stage65_instance_allocations", []))
                != expected_instances[str(row.get("table_key"))]
                or {
                    str(site.get("allocation_name"))
                    for site in row.get("stage65_instance_allocations", [])
                    if isinstance(site, dict)
                } != expected_allocation_names[str(row.get("table_key"))]
                or row.get("classification") != CLASS_ENGINE
                or row.get("in_place_append_authorized") is not False
                for row in generated_rows
            ) \
            or generated_items.get("inventory_sha256") != _sha256(
                canonical_json_bytes(
                    {
                        "tables": generated_rows,
                        "source_anchors": generated_items.get("source_anchors"),
                    }
                )
            ):
        _fail("generated Item index table instance/hashが不正です")

    collection = tables.get("collection_supply_derived_overlay")
    collection_rows = collection.get("tables") if isinstance(collection, dict) else None
    if not isinstance(collection_rows, dict) \
            or collection.get("status") != "DERIVED_OVERLAY_REBUILD_REQUIRED" \
            or collection.get("required_item_fixed_delta_bytes_excluding_names") != 540 \
            or collection.get("conditional_mega_fixed_delta_bytes_excluding_names") != 588 \
            or collection.get("maximum_fixed_delta_bytes_excluding_names") != 1128 \
            or collection.get("not_in_known_fixed_relocation_bundle") is not True:
        _fail("Collection Supply derived overlay容量が不正です")
    item_rows = collection_rows.get("item_rows")
    form_rows = collection_rows.get("mega_form_rows_if_adopted")
    if not isinstance(item_rows, dict) or not isinstance(form_rows, dict) \
            or (
                item_rows.get("current_count"), item_rows.get("new_count"),
                item_rows.get("stride_bytes"), item_rows.get("fixed_delta_bytes"),
            ) != (999, 1044, 12, 540) \
            or (
                form_rows.get("current_count"), form_rows.get("new_count"),
                form_rows.get("stride_bytes"), form_rows.get("fixed_delta_bytes"),
            ) != (388, 437, 12, 588) \
            or form_rows.get("conditional") is not True \
            or collection.get("item_obtained_accessor", {}).get(
                "sidecar_aware_accessor_patch_required"
            ) is not True:
        _fail("Collection Supply Item/Form/accessor契約が不正です")
    collection_fingerprint = {
        "payload": collection.get("stage65_payload"),
        "tables": collection_rows,
        "identities": collection.get("inputs"),
    }
    if collection.get("inventory_sha256") != _sha256(
        canonical_json_bytes(collection_fingerprint)
    ):
        _fail("Collection Supply derived overlay hashが不一致です")

    dry = document.get("allocator_audit", {}).get("known_fixed_table_dry_run")
    if not isinstance(dry, dict) or dry.get("status") != "NON_BINDING_DRY_RUN_ONLY" \
            or dry.get("allocation_ledger_mutated") is not False \
            or dry.get("rom_mutated") is not False or dry.get("fits") is not True:
        _fail("allocator dry-run markerが不正です")
    placements = dry.get("placements")
    if not isinstance(placements, list) or len(placements) != len(table_keys):
        _fail("allocator dry-run placement数が不一致です")
    cursor = dry.get("bundle_start")
    for row in placements:
        start = _integer(row.get("start"), "placement start")
        end = _integer(row.get("end_exclusive"), "placement end")
        size = _integer(row.get("size"), "placement size")
        alignment = _integer(row.get("alignment"), "placement alignment")
        if start < cursor or start % alignment or end - start != size:
            _fail(f"allocator placement geometry不一致です: {row.get('table_key')}")
        cursor = end
    if cursor != dry.get("bundle_end_exclusive") \
            or cursor > dry.get("candidate_span_end_exclusive"):
        _fail("allocator bundle末尾が不正です")
    span_rows = document.get("allocator_audit", {}).get(
        "candidate_span_assessments"
    )
    if not isinstance(span_rows, list) or len(span_rows) != 2:
        _fail("allocator span比較がありません")
    by_region = {str(row.get("region")): row for row in span_rows}
    if set(by_region) != {"integration_modules", "future_tail"} \
            or by_region["integration_modules"].get("fits_known_fixed_bundle") is not True \
            or by_region["future_tail"].get("fits_known_fixed_bundle") is not False \
            or any(row.get("binding_allocation") is not False for row in span_rows):
        _fail("allocator span適合判定が不正です")

    temporary = document.get("temporary_ability_replacement_contract")
    if not isinstance(temporary, dict) \
            or temporary.get("adopted_binding_count") != 14 \
            or temporary.get("classification_hold_binding_count") != 2 \
            or temporary.get("unique_replacement_key_count") != 16:
        _fail("temporary ability replacement契約が不正です")
    temporary_rows = temporary.get("rows")
    if not isinstance(temporary_rows, list) or len(temporary_rows) != 16:
        _fail("temporary ability row数が不正です")
    _require_unique(
        [str(row.get("ability_replacement_key", "")) for row in temporary_rows],
        "temporary replacement key",
    )

    asset = document.get("asset_readiness_separate_gate")
    if not isinstance(asset, dict) \
            or asset.get("id_reservation_is_independent_from_asset_readiness") is not True \
            or asset.get("winds_waves", {}).get("source_assets_ready") != 0 \
            or asset.get("mega_species", {}).get("gba_palette_ready") != 49:
        _fail("asset readiness分離gateが不正です")

    scan = document.get("consumer_audit", {}).get("hard_coded_boundaries")
    if not isinstance(scan, dict) or scan.get("required_anchor_status") != "PASS" \
            or not scan.get("rows") or not scan.get("inventory_sha256"):
        _fail("hard-coded consumer inventoryが不正です")
    fingerprint_payload = [
        {
            key: row[key]
            for key in (
                "domain",
                "boundary_kind",
                "value",
                "path",
                "locator",
                "evidence_sha256",
            )
        }
        for row in scan["rows"]
    ]
    if _sha256(canonical_json_bytes(fingerprint_payload)) != scan["inventory_sha256"]:
        _fail("hard-coded consumer inventory hashが不一致です")

    consumer = document.get("consumer_audit")
    if not isinstance(consumer, dict):
        _fail("consumer auditがありません")
    literal_roots = consumer.get("stage65_exact_literal_candidates")
    if not isinstance(literal_roots, dict) or set(literal_roots) != set(table_keys):
        _fail("Stage65 fixed table literal集合が不一致です")
    for key, row in literal_roots.items():
        sites = row.get("site_offsets")
        if not isinstance(sites, list) or not sites \
                or row.get("occurrence_count") != len(sites) \
                or row.get("site_set_sha256") != _sha256(canonical_json_bytes(sites)):
            _fail(f"Stage65 literal root/hashが不正です: {key}")

    ancillary = consumer.get("pinned_cfru_ancillary_source_symbols")
    if not isinstance(ancillary, dict) \
            or ancillary.get("actual_commit") != CFRU_COMMIT \
            or ancillary.get("working_tree_bytes_ignored") is not True \
            or set(ancillary.get("symbols", {})) != set(ANCILLARY_SOURCE_DEFINITIONS):
        _fail("CFRU ancillary source inventoryが不正です")
    source_fingerprint_rows = []
    for symbol, group in sorted(ancillary["symbols"].items()):
        if group.get("definition_path") != ANCILLARY_SOURCE_DEFINITIONS[symbol] \
                or group.get("definition_confirmed") is not True:
            _fail(f"CFRU ancillary定義が不正です: {symbol}")
        occurrences = group.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            _fail(f"CFRU ancillary参照がありません: {symbol}")
        source_fingerprint_rows.extend(
            {"symbol": symbol, **row} for row in occurrences
        )
    if _sha256(canonical_json_bytes(source_fingerprint_rows)) \
            != ancillary.get("inventory_sha256"):
        _fail("CFRU ancillary source inventory hashが不一致です")

    cfru_counts = consumer.get("pinned_cfru_count_macro_consumers")
    if not isinstance(cfru_counts, dict) \
            or cfru_counts.get("actual_commit") != CFRU_COMMIT \
            or cfru_counts.get("working_tree_bytes_ignored") is not True \
            or cfru_counts.get("required_anchor_status") != "PASS" \
            or cfru_counts.get("match_count") != 37 \
            or cfru_counts.get("counts_by_macro") != {
                "ABILITIES_COUNT": 8,
                "ITEMS_COUNT": 9,
                "MOVES_COUNT": 9,
                "NUM_SPECIES": 11,
            }:
        _fail("CFRU count macro consumer集合が不正です")
    cfru_count_rows = cfru_counts.get("rows")
    if not isinstance(cfru_count_rows, list) \
            or cfru_counts.get("inventory_sha256") != _sha256(
                canonical_json_bytes(cfru_count_rows)
            ):
        _fail("CFRU count macro consumer hashが不一致です")

    move_dispatch = consumer.get("pinned_move_effect_dispatch")
    if not isinstance(move_dispatch, dict) \
            or move_dispatch.get("status") != "SEMANTIC_RESERVATION_NOT_ASSIGNED" \
            or move_dispatch.get("entry_count") != 256 \
            or move_dispatch.get("table_bytes") != 1024 \
            or move_dispatch.get("blank_candidate_ids") != [251, 252, 255] \
            or move_dispatch.get("blank_candidate_active_move_use_count") != {
                "251": 0, "252": 0, "255": 0
            } \
            or move_dispatch.get("stage65_tail_effect_use_count") != {
                "251": 0, "252": 0, "253": 102, "254": 0, "255": 0
            } \
            or move_dispatch.get("excluded_blank_id") != 254 \
            or move_dispatch.get("ally_switch_effect_id") is not None \
            or move_dispatch.get("classification") != CLASS_ENGINE:
        _fail("move effect dispatch予約契約が不正です")

    event_abi = consumer.get("codex_public_event_abi")
    if not isinstance(event_abi, dict) \
            or event_abi.get("status") != "ABI_EXPANSION_REQUIRED" \
            or event_abi.get("current_bits_per_event") != 88 \
            or event_abi.get("minimum_required_bits_per_event") != 89 \
            or event_abi.get("current_bytes_per_event") != 11 \
            or event_abi.get("minimum_required_bytes_per_event") != 12 \
            or event_abi.get("event_capacity") != 4 \
            or event_abi.get("current_event_ring_bytes") != 44 \
            or event_abi.get("minimum_required_event_ring_bytes") != 48 \
            or event_abi.get("current_public_state_size") != 180 \
            or event_abi.get("minimum_public_state_size_if_only_ring_grows") != 184 \
            or event_abi.get("classification") != CLASS_ENGINE:
        _fail("Codex public event ABI拡張契約が不正です")

    narrow = consumer.get("known_narrow_field_source_evidence")
    narrow_rows = narrow.get("rows") if isinstance(narrow, dict) else None
    if not isinstance(narrow_rows, list) or len(narrow_rows) != len(BITFIELD_CONSUMER_PATTERNS) \
            or _sha256(canonical_json_bytes(narrow_rows)) \
            != narrow.get("inventory_sha256"):
        _fail("狭幅consumer source証跡が不正です")

    ownership = consumer.get("stage09_to_stage65_consumer_ownership")
    if not isinstance(ownership, dict):
        _fail("Stage09→65 consumer ownership監査がありません")
    expected_patch_counts = {
        "stage09_runtime_instruction_patches": 31,
        "stage09_species_name_stride_instruction_patches": 48,
        "stage09_learn_move_hooks": 5,
    }
    for key, count in expected_patch_counts.items():
        group = ownership.get(key)
        rows = group.get("rows") if isinstance(group, dict) else None
        if not isinstance(rows, list) or group.get("declared_count") != count \
                or len(rows) != count \
                or _sha256(canonical_json_bytes(rows)) != group.get("inventory_sha256"):
            _fail(f"Stage consumer patch inventoryが不正です: {key}")
    variable_roots = ownership.get("stage39_and_stage61_literal_roots")
    if not isinstance(variable_roots, dict) or len(variable_roots) != 10 \
            or any(row.get("occurrence_count", 0) <= 0 for row in variable_roots.values()):
        _fail("Stage39/61 variable/catalog root監査が不正です")

    widths = document.get("numeric_width_audit")
    expected_width_blockers = {
        "BattlePokemon.oldAbility",
        "BattleStruct.abilityPreventingSwitchout",
        "CodexBattlePublicEventV2.last_item_id",
        "MirageProduction_Probe.virtual_items_packed",
    }
    if not isinstance(widths, list) or {
        str(row.get("field")) for row in widths
        if row.get("known_limit_exceeded") is True
    } != expected_width_blockers \
            or any(
                row.get("classification") != CLASS_ENGINE
                for row in widths if row.get("known_limit_exceeded") is True
            ):
        _fail("numeric width blocker集合/classificationが不正です")
    classifications = document.get("implementation_classification")
    if not isinstance(classifications, dict) \
            or set(classifications) != {CLASS_SIMPLE, CLASS_ENGINE, CLASS_SAVE} \
            or classifications[CLASS_ENGINE].get("fixed_table_keys") != table_keys:
        _fail("実装classification索引が不正です")

    save = document.get("save_abi")
    item_bitmap = save.get("item_obtained_bitmap") if isinstance(save, dict) else None
    if not isinstance(item_bitmap, dict) \
            or item_bitmap.get("current_bytes") != 125 \
            or item_bitmap.get("new_bytes") != 131 \
            or item_bitmap.get("delta_bytes") != 6 \
            or item_bitmap.get("classification") != CLASS_SAVE \
            or item_bitmap.get("in_place_append_possible") is not False:
        _fail("Item save bitmap ABI監査が不正です")
    sidecar = item_bitmap.get("non_binding_sidecar_candidate")
    if not isinstance(sidecar, dict) \
            or sidecar.get("candidate_start") != 0x2697 \
            or sidecar.get("candidate_end_exclusive") != 0x269D \
            or sidecar.get("candidate_bytes") != 6 \
            or sidecar.get("remaining_reserved_bytes") != 123 \
            or sidecar.get("binding_allocation") is not False \
            or sidecar.get("save_layout_mutated") is not False:
        _fail("Item bitmap sidecar候補が不正です")

    unresolved = document.get("runtime_blockers")
    if not isinstance(unresolved, list) or len(unresolved) < 8:
        _fail("runtime blockerを過少申告しています")
    checks = document.get("checks")
    if not isinstance(checks, list) or not checks \
            or any(row.get("passed") is not True for row in checks):
        _fail("checkpoint checkにFAILがあります")


def build_p04_capacity_checkpoint(root: Path) -> dict[str, Any]:
    """入力を再監査し、副作用なしでcapacity checkpointを構築する。"""

    root = root.resolve()
    p04, p04_identity = _pinned_json(root, P04_CANDIDATES, "P04 candidate manifest")
    assets, assets_identity = _pinned_json(root, P04_ASSETS, "P04 asset manifest")
    p05_contract, p05_contract_identity = _pinned_json(
        root, P05_CONTRACT, "P05 battle content contract"
    )
    p05, p05_identity = _pinned_json(root, P05_HANDOFF, "P05 runtime handoff")
    source_lock, source_lock_identity = _json(
        root, "state/source-lock.json", "source lock"
    )
    cfru_locks = [
        row for row in source_lock.get("sources", [])
        if isinstance(row, dict) and row.get("name") == "cfru"
    ]
    if len(cfru_locks) != 1 \
            or cfru_locks[0].get("resolved_commit") != CFRU_COMMIT \
            or cfru_locks[0].get("configured_commit_verified") is not True:
        _fail("source-lockのCFRU commit契約が不一致です")
    if p04.get("research_cutoff_date") != "2026-09-08" \
            or p04.get("task") != "USER-MODERNIZATION-P04":
        _fail("P04 research cutoff/taskが不一致です")
    if assets.get("status") != "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS":
        _fail("P04 asset statusが不一致です")
    if p05.get("status") != "CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS" \
            or p05_contract.get("status") \
            != "CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS":
        _fail("P05 runtime未実装statusが不一致です")

    manifest_rows: dict[str, list[dict[str, str]]] = {}
    manifest_identities: dict[str, dict[str, Any]] = {}
    for domain, spec in MANIFEST_SPACES.items():
        rows, identity = _csv_rows(root, spec["path"], f"{domain} manifest")
        _manifest_inventory(
            rows,
            key_field=spec["key_field"],
            expected_count=spec["current_count"],
            label=f"{domain} manifest",
        )
        manifest_rows[domain] = rows
        manifest_identities[domain] = identity

    try:
        capacity = build_modernization_capacity_audit(root)
        require_capacity_pass(capacity)
    except CapacityAuditError as exc:
        _fail(f"P01 capacity auditがPASSしません: {exc}")
    capacity_bytes = (
        json.dumps(capacity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")

    stage65_rom = _regular_file(root, STAGE65_ROM, "Stage65 ROM")
    stage65_rom_identity = {
        "path": STAGE65_ROM.as_posix(),
        "size": len(stage65_rom),
        "sha256": _sha256(stage65_rom),
    }
    if stage65_rom_identity["size"] != EXPECTED_STAGE65_SIZE \
            or stage65_rom_identity["sha256"] != EXPECTED_STAGE65_SHA256:
        _fail("Stage65 exact ROM identityが不一致です")
    stage65_meta, stage65_meta_identity = _json(
        root, STAGE65_METADATA, "Stage65 metadata"
    )
    stage65_allocation, stage65_allocation_identity = _json(
        root, STAGE65_ALLOCATION, "Stage65 allocation"
    )
    for relative, identity, label in (
        (STAGE65_ALLOCATION, stage65_allocation_identity, "Stage65 allocation"),
    ):
        expected = PINNED_LOCAL_INPUT_SHA256[relative.as_posix()]
        if identity["sha256"] != expected:
            _fail(
                f"{label} pinが不一致です: expected={expected}, "
                f"actual={identity['sha256']}"
            )
        identity["pin_status"] = "MATCH"
    stage65_meta_contract = _stage65_metadata_contract(stage65_meta)
    stage65_meta_contract_sha256 = _sha256(
        canonical_json_bytes(stage65_meta_contract)
    )
    if stage65_meta_contract_sha256 != EXPECTED_STAGE65_METADATA_CONTRACT_SHA256:
        _fail(
            "Stage65 metadata semantic contractが不一致です: "
            f"{stage65_meta_contract_sha256}"
        )
    stage65_meta_contract_identity = {
        "path": STAGE65_METADATA.as_posix(),
        "semantic_projection_sha256": stage65_meta_contract_sha256,
        "semantic_projection": stage65_meta_contract,
        "full_file_sha256_excluded_from_checkpoint": True,
        "reason": "再生成で変わり得る非本質的な下流証跡を容量予約identityへ混入させない",
    }
    if stage65_meta.get("checkpoint_marker") != "CHECKPOINT_NOT_P03_DONE" \
            or stage65_meta.get("done") is not False \
            or stage65_meta.get("output", {}).get("sha256") != EXPECTED_STAGE65_SHA256 \
            or stage65_meta.get("allocation", {}).get("sha256") \
            != stage65_allocation_identity["sha256"]:
        _fail("Stage65 metadata/allocation identityが不一致です")
    free_segments, free_summary = _free_segments(stage65_rom, stage65_allocation)

    stage09, stage09_identity = _json(root, STAGE09_METADATA, "Stage09 metadata")
    stage39, stage39_identity = _json(root, STAGE39_METADATA, "Stage39 metadata")
    hotfix, hotfix_identity = _json(root, STAGE61_HOTFIX, "Stage61 hotfix tables")
    for relative, identity, label in (
        (STAGE09_METADATA, stage09_identity, "Stage09 metadata"),
        (STAGE39_METADATA, stage39_identity, "Stage39 metadata"),
        (STAGE61_HOTFIX, hotfix_identity, "Stage61 hotfix tables"),
    ):
        expected = PINNED_LOCAL_INPUT_SHA256[relative.as_posix()]
        if identity["sha256"] != expected:
            _fail(
                f"{label} pinが不一致です: expected={expected}, "
                f"actual={identity['sha256']}"
            )
        identity["pin_status"] = "MATCH"

    reservations = _build_reservations(manifest_rows, p04, p05)
    temporary = _temporary_ability_contract(p04, p05)
    asset_gate = _asset_separation(assets, reservations)
    fixed_tables, variable_components, catalog_audit = _build_tables(
        root, capacity, stage65_rom
    )
    variable_components.extend(_mega_stone_variable_components(assets))
    generated_item_consumers = audit_generated_item_index_consumers(
        root, stage65_rom, stage65_allocation
    )
    collection_supply_consumers = audit_collection_supply_consumers(
        root, stage65_rom, stage65_allocation
    )
    dry_run = _dry_run_layout(fixed_tables, free_segments)
    span_assessments = _assess_allocator_spans(fixed_tables, free_segments)

    literal_roots: dict[str, Any] = {}
    for table in fixed_tables:
        address = _integer(table["current_address"], "current table address")
        sites = _literal_sites(stage65_rom, address)
        if not sites:
            _fail(f"Stage65 ROM上にtable literalがありません: {table['table_key']}")
        literal_roots[str(table["table_key"])] = {
            "target_address": address,
            "target_address_hex": f"0x{address:08X}",
            "occurrence_count": len(sites),
            "site_offsets": sites,
            "site_set_sha256": _sha256(canonical_json_bytes(sites)),
            "classification": CLASS_ENGINE,
            "interpretation": "全一致literal候補。偶然一致を含め保守的にsemantic review対象とする",
        }
    p01_roots = {
        key: _p01_root_summary(value)
        for key, value in sorted(capacity.get("consumer_roots", {}).items())
        if isinstance(value, dict)
    }
    hardcoded = audit_hardcoded_consumers(root)
    ancillary_source = audit_ancillary_source_consumers(root)
    cfru_count_consumers = audit_cfru_count_macro_consumers(root)
    move_data_table = next(
        row for row in fixed_tables if row["table_key"] == "move_data"
    )
    move_effect_dispatch = audit_move_effect_dispatch(
        root,
        stage65_rom,
        move_data_address=_integer(
            move_data_table["current_address"], "move data address"
        ),
    )
    codex_public_event_abi = audit_codex_public_event_abi(root)
    narrow_consumers = audit_bitfield_consumers(root)
    stage_ownership = audit_stage_consumer_ownership(
        stage65_rom, stage09, stage39, hotfix
    )
    evolution_table = next(
        row for row in fixed_tables if row["table_key"] == "evolution"
    )
    evolution_slots = audit_mega_evolution_slots(
        stage65_rom,
        manifest_rows["species_form"],
        reservations["species_form"]["rows"],
        evolution_address=_integer(
            evolution_table["current_address"], "evolution table address"
        ),
    )
    widths = _numeric_width_audit()
    expected_width_blockers = {
        "BattlePokemon.oldAbility",
        "BattleStruct.abilityPreventingSwitchout",
        "CodexBattlePublicEventV2.last_item_id",
        "MirageProduction_Probe.virtual_items_packed",
    }
    actual_width_blockers = {
        str(row["field"]) for row in widths if row["known_limit_exceeded"]
    }
    if actual_width_blockers != expected_width_blockers:
        _fail(f"既知の狭幅consumer集合が不一致です: {actual_width_blockers}")
    save_abi = _save_abi_audit(root, capacity)

    checks = [
        {"name": "p01_exact_rom_capacity_pass", "passed": capacity.get("status") == "PASS"},
        {"name": "stage65_exact_rom_and_allocation", "passed": True},
        {"name": "existing_manifests_contiguous_and_collision_free", "passed": True},
        {"name": "append_reservations_are_contiguous_u16", "passed": True},
        {"name": "temporary_ability_replacement_keys_preserved", "passed": True},
        {"name": "asset_gaps_are_separate_and_not_filled", "passed": True},
        {"name": "main_and_ancillary_fixed_table_geometry_measured", "passed": True},
        {"name": "generated_item_index_consumers_measured", "passed": True},
        {"name": "collection_supply_derived_consumers_measured", "passed": True},
        {"name": "mega_evolution_base_row_slots_sufficient", "passed": True},
        {"name": "stage65_literal_consumers_nonempty", "passed": True},
        {"name": "scoped_hard_coded_consumer_anchors_found", "passed": True},
        {"name": "pinned_cfru_ancillary_source_consumers_found", "passed": True},
        {"name": "pinned_cfru_count_macro_consumers_inventoried", "passed": True},
        {"name": "move_effect_dispatch_semantic_candidates_measured", "passed": True},
        {"name": "codex_public_event_abi_growth_measured", "passed": True},
        {"name": "known_narrow_consumers_found_and_blocked", "passed": True},
        {"name": "later_stage_consumer_ownership_measured", "passed": True},
        {"name": "known_fixed_tables_fit_allocator_candidate", "passed": dry_run["fits"]},
        {"name": "save_abi_impacts_classified", "passed": True},
        {"name": "no_runtime_or_shared_state_mutation", "passed": True},
    ]
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": CHECKPOINT_STATUS,
        "runtime_ready": False,
        "rom_mutated": False,
        "save_mutated": False,
        "shared_manifests_mutated": False,
        "active_play_baseline_changed": False,
        "inputs": {
            "p01_capacity_audit": {
                "kind": "DETERMINISTIC_IN_MEMORY_REPORT",
                "status": capacity.get("status"),
                "active_stage": capacity.get("input_identity", {}).get("stage"),
                "canonical_compact_sha256": _sha256(capacity_bytes),
                "canonical_compact_size": len(capacity_bytes),
            },
            "p04_candidate_manifest": p04_identity,
            "p04_asset_manifest": assets_identity,
            "p05_battle_content_contract": p05_contract_identity,
            "p05_runtime_handoff": p05_identity,
            "source_lock": source_lock_identity,
            "canonical_manifests": manifest_identities,
            "stage65_rom": stage65_rom_identity,
            "stage65_metadata": stage65_meta_contract_identity,
            "stage65_allocation": stage65_allocation_identity,
            "stage09_species_surface_metadata": stage09_identity,
            "stage39_move_distribution_metadata": stage39_identity,
            "stage61_hotfix_table_metadata": hotfix_identity,
            "cfru_compiled_offsets": _pinned_local_identity(
                root, CFRU_OFFSETS, "CFRU compiled offsets"
            ),
        },
        "id_reservations": reservations,
        "temporary_ability_replacement_contract": temporary,
        "asset_readiness_separate_gate": asset_gate,
        "numeric_width_audit": widths,
        "implementation_classification": {
            CLASS_SIMPLE: {
                "fields": [
                    "canonical species/form ID append 1621..1672",
                    "canonical item ID append 999..1043",
                    "canonical ability ID append 312..317",
                    "canonical move ID append 1063",
                    "u16 persistent Pokemon species/item/move fields",
                ],
                "meaning": "ID namespace/primary u16 fieldだけの採番可否。runtime-ready宣言ではない",
            },
            CLASS_ENGINE: {
                "fixed_table_keys": [row["table_key"] for row in fixed_tables],
                "narrow_field_blockers": sorted(expected_width_blockers),
                "variable_component_keys": [
                    row["component_key"] for row in variable_components
                ],
                "derived_overlay_component_keys": [
                    "codex_generated_item_index_tables",
                    "collection_supply_v1",
                ],
                "meaning": "relocation、root/count/loop、effect、ABIまたはruntime code変更が必須",
            },
            CLASS_SAVE: {
                "fields": [
                    "itemObtainedFlags 125→131 byte",
                    "Acquisition collection policy最大+7 byte",
                    "legacy Dex外の52 stable species/form key mapping",
                ],
                "meaning": "owner version、migration、rollbackを含む保存設計が必須",
            },
        },
        "table_capacity": {
            "fixed_tables": fixed_tables,
            "known_fixed_table_count": len(fixed_tables),
            "known_fixed_old_bytes": sum(row["old_size_bytes"] for row in fixed_tables),
            "known_fixed_new_bytes": sum(row["new_size_bytes"] for row in fixed_tables),
            "known_fixed_delta_bytes": sum(row["delta_bytes"] for row in fixed_tables),
            "variable_or_policy_blocked_components": variable_components,
            "generated_relink_item_index_tables": generated_item_consumers,
            "collection_supply_derived_overlay": collection_supply_consumers,
            "machine_tutor_catalogs": catalog_audit,
            "mega_evolution_slot_capacity": evolution_slots,
            "all_current_tables_are_full_or_non_appendable": True,
        },
        "consumer_audit": {
            "p01_verified_roots_on_active_stage": p01_roots,
            "stage65_exact_literal_candidates": literal_roots,
            "hard_coded_boundaries": hardcoded,
            "pinned_cfru_ancillary_source_symbols": ancillary_source,
            "pinned_cfru_count_macro_consumers": cfru_count_consumers,
            "pinned_move_effect_dispatch": move_effect_dispatch,
            "codex_public_event_abi": codex_public_event_abi,
            "known_narrow_field_source_evidence": narrow_consumers,
            "stage09_to_stage65_consumer_ownership": stage_ownership,
            "relocation_rule": (
                "P01宣言root、Stage65全一致literal候補、hard-coded count/boundaryの全件を"
                "後続patch対象へ解決するまでruntime-readyにしない"
            ),
        },
        "allocator_audit": {
            "source_stage": 65,
            "free_summary": free_summary,
            "free_segments": free_segments,
            "candidate_spans": [
                row
                for row in sorted(free_segments, key=lambda item: -item["size"])
                if row["size"] >= 4096
            ],
            "candidate_span_assessments": span_assessments,
            "known_fixed_table_dry_run": dry_run,
            "allocator_claim": "KNOWN_FIXED_TABLES_FIT_ONLY_NOT_FULL_RUNTIME_CAPACITY_PROOF",
        },
        "save_abi": save_abi,
        "materialization_contract": {
            "pure_function": "tools.modernization_p04_capacity.materialize_reserved_id_rows",
            "projection_only": True,
            "allocation_order": "STABLE_KEY_LEXICOGRAPHIC",
            "shared_manifest_write_performed": False,
            "required_before_shared_materialization": [
                "各manifest固有の日本語名・説明・semantic fieldを提出",
                "全table relocationとpointer/count consumer patchを設計",
                "Ally Switch effect/target/flags/animation/AIを実装",
                "6 Ability effect/AI/UIを実装",
                "TM/Tutor route方針を決定",
                "save owner version/migrationを決定",
                "Winds/Waves素材gapを解消または対象を明示延期",
            ],
        },
        "runtime_blockers": [
            "共有Species/Move/Ability/Item manifest未変更",
            "固定table未relocate・consumer未repoint",
            "Codex runtime/reward内Item index表の全copy未再生成・未再link",
            "Collection Supplyの45 Item row/名称・条件付き49 Mega form row/名称未再生成",
            "Collection Supplyのitem obtained accessorがsidecar未対応",
            "Mega Stone 45件のraw graphics 14,400Bは配置/pointer/rights未統合",
            "Mega Stone 45 Itemの日本語text/effect/callback未提出",
            "Ally Switch runtime fields/effect/AI/animation未実装",
            "Ally Switch effectはblank 251/252/255のsemantic採用を未決定（254は対象外）",
            "新Ability 6件の日本語text/effect/AI/UI未実装",
            "新Ability 6件のMold Breaker無視table値を未審査（zero-fill自動採用禁止）",
            "TM/HM128とTutor64が満杯でMove1063 route方針未決定",
            "新Species level-up/egg/evolution/base stats/dex content未提出",
            "Mega change conditionとbattle-only save normalization未実装",
            "item obtained bitmap 125→131 byteのsave migration未設計",
            "Item 1024..1043はCodex battle公開event 10-bit ABIを超え、event 11→12B化が必要",
            "Mirage virtual item ProbeはItem 1024..1043を0x3FFで切り捨てる",
            "legacy Ability u8宣言2箇所の非到達/u16 replacementをlinked testで未証明",
            "collection ledger追加bit数とAcquisition owner migration未設計",
            "Winds/Waves 3件素材欠落",
            "外部素材root license不在のためprivate-use staging限定",
            "可変長code/text/learnset/graphicsを含む総ROM容量未確定",
        ],
        "checks": checks,
    }
    validate_checkpoint_document(document)
    return document


def _checkpoint_output_path(
    root: Path, output_path: str | Path
) -> tuple[Path, Path]:
    """task固有の既定成果以外への上書きを拒否する。"""

    root = root.resolve()
    candidate = Path(output_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.is_symlink():
        _fail(f"出力先symlinkは禁止です: {output_path}")
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        _fail(f"出力先はworkspace内に限定されます: {output_path}")
    if relative != DEFAULT_OUTPUT:
        _fail(
            "P04 capacity出力先はtask固有pathだけに限定されます: "
            f"expected={DEFAULT_OUTPUT}, actual={relative}"
        )
    return resolved, relative


def audit_p04_capacity_checkpoint(
    root: Path, *, output_path: str | Path = DEFAULT_OUTPUT
) -> dict[str, Any]:
    """tracked checkpointを副作用なしで再計算結果と照合する。"""

    root = root.resolve()
    resolved_output, relative_output = _checkpoint_output_path(root, output_path)
    expected = build_p04_capacity_checkpoint(root)
    output_identity = _identity(root, relative_output, "P04 capacity checkpoint")
    actual, _ = _json(root, relative_output, "P04 capacity checkpoint")
    validate_checkpoint_document(actual)
    if canonical_json_bytes(actual) != canonical_json_bytes(expected):
        _fail("P04 capacity checkpointが現入力からの再計算結果と不一致です")
    return {
        "status": "PASS",
        "mode": "CHECK",
        "checkpoint_status": actual["status"],
        "output": output_identity,
        "counts": {
            domain: group["append_count"]
            for domain, group in actual["id_reservations"].items()
        },
        "known_fixed_table_bytes": actual["table_capacity"]["known_fixed_new_bytes"],
        "allocator_candidate_fit": actual["allocator_audit"][
            "known_fixed_table_dry_run"
        ]["fits"],
        "runtime_ready": False,
    }


def write_p04_capacity_checkpoint(
    root: Path, *, output_path: str | Path = DEFAULT_OUTPUT
) -> dict[str, Any]:
    """task固有checkpointだけを明示的に書き出す。"""

    root = root.resolve()
    destination, relative_destination = _checkpoint_output_path(root, output_path)
    document = build_p04_capacity_checkpoint(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(canonical_json_bytes(document))
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, 0o644)
        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return {
        "status": "PASS",
        "mode": "WRITE",
        "checkpoint_status": document["status"],
        "output": _identity(root, relative_destination, "P04 capacity checkpoint"),
        "counts": {
            domain: group["append_count"]
            for domain, group in document["id_reservations"].items()
        },
        "known_fixed_table_bytes": document["table_capacity"]["known_fixed_new_bytes"],
        "allocator_candidate_fit": document["allocator_audit"][
            "known_fixed_table_dry_run"
        ]["fits"],
        "runtime_ready": False,
    }
