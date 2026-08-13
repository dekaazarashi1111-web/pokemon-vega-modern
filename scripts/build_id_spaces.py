#!/usr/bin/env python3
"""T05: Vega/CFRU/DPEのType・Ability・Item ID空間を決定的に生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.engine.cfru_id_space_inventory import (  # noqa: E402
    CFRUIdSpaceInventoryError,
    extract_cfru_id_spaces,
)
from tools.engine.extract_vega_id_spaces import (  # noqa: E402
    VegaIdSpaceExtractionError,
    extract_vega_id_spaces,
)


SCHEMA_VERSION = 1
TASK_ID = "T05"
CONFIG_PATH = Path("config/id_spaces.json")
REPORT_PATH = Path("reports/generated/id_space_report.md")
GENERATED_ROOT = Path("generated/engine/ids")

ABILITY_MANIFEST_HEADER = (
    "ability_key",
    "id",
    "vega_id",
    "cfru_id",
    "cfru_symbol",
    "dpe_symbol",
    "classification",
    "display_name",
    "description_key",
    "effect_key",
    "runtime_binding",
    "status",
    "notes",
)
ITEM_MANIFEST_HEADER = (
    "item_key",
    "id",
    "vega_id",
    "cfru_id",
    "cfru_symbol",
    "classification",
    "display_name",
    "description_key",
    "icon_key",
    "palette_key",
    "pocket",
    "price",
    "importance",
    "role",
    "item_type_key",
    "item_type_id",
    "item_type_explicit",
    "item_type_source",
    "source_mystery",
    "is_evolution_stone",
    "is_evolution_item",
    "hold_effect_key",
    "hold_effect_param",
    "field_effect_key",
    "field_effect_param",
    "field_use_callback_key",
    "battle_usage",
    "battle_effect_key",
    "battle_effect_param",
    "battle_use_callback_key",
    "secondary_id",
    "ball_kind",
    "consume_policy",
    "target_policy",
    "supply_key",
    "runtime_binding",
    "status",
    "notes",
)
TYPE_MANIFEST_HEADER = (
    "type_key",
    "id",
    "vega_id",
    "cfru_id",
    "cfru_symbol",
    "dpe_symbol",
    "classification",
    "display_name",
    "icon_key",
    "icon_width",
    "icon_height",
    "icon_tile_offset",
    "icon_source",
    "color_key",
    "color_r",
    "color_g",
    "color_b",
    "color_bgr555",
    "color_source",
    "effectiveness_key",
    "special_rule",
    "tera_input_code",
    "status",
    "notes",
)

ARTIFACT_PATHS = (
    "generated/engine/ids/id_spaces.json",
    "generated/engine/ids/ids_generated.h",
    "generated/engine/ids/type_tables.c",
    "generated/engine/ids/ability_tables.c",
    "generated/engine/ids/item_tables.c",
    "generated/engine/ids/qol_item_effects.c",
    "generated/engine/ids/layout.json",
    "generated/engine/ids/text_width.json",
    "generated/engine/ids/metadata.json",
    "manifests/ability_ids.csv",
    "manifests/item_ids.csv",
    "manifests/type_ids.csv",
    "reports/generated/id_space_report.md",
)

FINGERPRINT_FILES = (
    "config/id_spaces.json",
    "manifests/id_ranges.csv",
    "scripts/build_id_spaces.py",
    "scripts/validate_manifests.py",
    "tools/engine/extract_vega_id_spaces.py",
    "tools/engine/cfru_id_space_inventory.py",
    "tests/test_build_id_spaces.py",
    "tests/test_extract_vega_id_spaces.py",
    "tests/test_cfru_id_space_inventory.py",
    "tests/test_validate_manifests.py",
    "docs/QOL_POLICY.md",
    "state/source-lock.json",
    "infra/toolchain_manifest.json",
)

ABILITY_KEY_OVERRIDES = {
    24: "ABILITY_KEY_WOUNDING_BODY",
    76: "ABILITY_KEY_CACOPHONY",
    77: "ABILITY_KEY_AIRLOCK",
}


class IdSpaceBuildError(RuntimeError):
    """固定入力、mapping、生成、または公開成果の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise IdSpaceBuildError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(value: object, *, pretty: bool = True) -> bytes:
    if pretty:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def _stable_digest(value: object) -> str:
    return _sha256(_stable_json(value, pretty=False).rstrip(b"\n"))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"cannot read {label}: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} root must be an object")
    return value


def _c_token(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little")


def _ascii_c_string(value: str) -> str:
    if not value.isascii():
        _fail(f"generated C token is not ASCII: {value!r}")
    return json.dumps(value)


def _none(value: object) -> str:
    if value in (None, "", "NULL", "0", 0):
        return "NONE"
    return str(value)


def _norm(value: str | None) -> str:
    if value is None:
        return ""
    import unicodedata

    return "".join(
        character
        for character in unicodedata.normalize("NFKC", value)
        if not character.isspace()
    )


def _description_key(prefix: str, key: str) -> str:
    return f"{prefix}_DESC_{key.removeprefix(prefix + '_KEY_')}"


def _load_ranges(root: Path) -> list[dict[str, str]]:
    path = root / "manifests/id_ranges.csv"
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
    except OSError as error:
        _fail(f"cannot read ID ranges: {error}")
    expected = ["domain", "owner", "start_id", "end_id", "status", "notes"]
    if not rows or list(rows[0]) != expected:
        _fail("manifests/id_ranges.csv header/rows are invalid")
    return rows


def _require_range(
    rows: Sequence[Mapping[str, str]], domain: str, owner: str, start: int, end: int
) -> None:
    matches = [row for row in rows if row["domain"] == domain and row["owner"] == owner]
    if len(matches) != 1:
        _fail(f"ID range {domain}/{owner} must occur exactly once")
    actual = (int(matches[0]["start_id"], 0), int(matches[0]["end_id"], 0))
    if actual != (start, end):
        _fail(f"ID range {domain}/{owner} changed: {actual} != {(start, end)}")


def _build_types(
    config: Mapping[str, Any], vega: Mapping[str, Any], cfru: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    policy = config["mapping_policy"]["type"]
    active_ids = set(policy["active_ids"])
    reserved_ids = set(policy["reserved_ids"])
    sentinel_ids = set(policy["sentinel_ids"])
    if active_ids | reserved_ids | sentinel_ids != set(range(25)):
        _fail("type policy must classify every ID 0..24 exactly once")
    if (active_ids & reserved_ids) or (active_ids & sentinel_ids) or (reserved_ids & sentinel_ids):
        _fail("type policy classifications overlap")

    rows: list[dict[str, Any]] = []
    manifest: list[dict[str, str]] = []
    display_overrides = {int(key): value for key, value in policy["display_overrides"].items()}
    matrix_overrides = {
        tuple(int(part) for part in key.split(",")): int(value)
        for key, value in policy["vega_matrix_overrides"].items()
    }
    if set(matrix_overrides) != {(7, 8), (17, 8)} or any(
        value != 500 for value in matrix_overrides.values()
    ):
        _fail("Vega type-matrix override contract changed")
    vega_by_id = {row["id"]: row for row in vega["types"]}
    for source in cfru["types"]:
        type_id = source["id"]
        key = source["canonical_key"]
        display = display_overrides.get(type_id, source["name_ja"])
        if display is None:
            _fail(f"type {type_id} has no explicit display name")
        if type_id < 18:
            classification = "VEGA_CFRU_CANONICAL"
            status = "FROZEN"
            vega_id: int | None = type_id
            icon_key = f"TYPE_ICON_VEGA_{type_id:02d}"
        elif type_id in sentinel_ids:
            classification = "CFRU_SENTINEL"
            status = "RESERVED"
            vega_id = None
            icon_key = f"TYPE_ICON_CFRU_{source['symbol'].removeprefix('TYPE_')}"
        elif type_id in reserved_ids:
            classification = "CFRU_RESERVED"
            status = "RESERVED"
            vega_id = None
            icon_key = f"TYPE_ICON_CFRU_{source['symbol'].removeprefix('TYPE_')}"
        else:
            classification = "CFRU_APPEND"
            status = "APPENDED"
            vega_id = None
            icon_key = f"TYPE_ICON_CFRU_{source['symbol'].removeprefix('TYPE_')}"
        special_rule = "NONE"
        runtime_binding = "T06_RUNTIME_BIND_PENDING"
        if type_id == 9:
            special_rule = "MYSTERY_SPECIAL"
        elif type_id == 19:
            special_rule = "ROOSTLESS_SENTINEL"
        elif type_id == 20:
            special_rule = "BLANK_SENTINEL"
        elif type_id == 24:
            special_rule = "STELLAR_CFRU_SPECIAL"
            runtime_binding = "T06_RUNTIME_BIND_PENDING"
        elif type_id in reserved_ids:
            special_rule = "ALIGNMENT_RESERVED"
        elif type_id == 23:
            special_rule = "FAIRY_CFRU_MATRIX"

        matrix = list(source["effectiveness"])
        for (attack, defend), value in matrix_overrides.items():
            if attack == type_id:
                matrix[defend] = value
        if len(matrix) != 25 or any(value not in (1, 500, 1000, 2000) for value in matrix):
            _fail(f"type {type_id} has an invalid effectiveness row")
        vega_evidence = vega_by_id.get(type_id)
        if type_id < 18:
            if not isinstance(vega_evidence, Mapping):
                _fail(f"type {type_id} has no Vega display evidence")
            icon_geometry = {
                "width": vega_evidence["display_icon_width"],
                "height": vega_evidence["display_icon_height"],
                "tile_offset": vega_evidence["display_icon_tile_offset"],
            }
            icon_source = (
                f"Vega ROM gMoveMenuInfoIcons[{vega_evidence['display_icon_index']}]"
            )
        else:
            icon_geometry = dict(source["move_menu_icon"])
            icon_ref = source["source_refs"].get("move_menu_icon")
            if not isinstance(icon_ref, Mapping):
                _fail(f"type {type_id} has no fixed icon source reference")
            icon_source = f"{icon_ref['path']}:{icon_ref['line']}:{icon_ref['symbol']}"
        color = source.get("display_color")
        color_ref = source["source_refs"].get("display_color")
        if not isinstance(color, Mapping) or not isinstance(color_ref, Mapping):
            _fail(f"type {type_id} has no fixed display color mapping")
        if (
            set(color) != {"r", "g", "b", "bgr555"}
            or any(not isinstance(color[channel], int) for channel in color)
            or not all(0 <= color[channel] <= 31 for channel in ("r", "g", "b"))
            or color["bgr555"]
            != color["r"] | (color["g"] << 5) | (color["b"] << 10)
        ):
            _fail(f"type {type_id} display color mapping is invalid")
        color_source = f"{color_ref['path']}:{color_ref['line']}:{color_ref['symbol']}"
        row = {
            "id": type_id,
            "type_key": key,
            "vega_id": vega_id,
            "cfru_id": type_id,
            "cfru_symbol": (
                None if source["symbol"].startswith("TYPE_RESERVED_") else source["symbol"]
            ),
            "dpe_symbol": (
                None if source["symbol"].startswith("TYPE_RESERVED_") else source["symbol"]
            ),
            "classification": classification,
            "display_name": display,
            "icon_key": icon_key,
            "icon_geometry": icon_geometry,
            "icon_source": icon_source,
            "color_key": f"TYPE_COLOR_CFRU_{source['symbol'].removeprefix('TYPE_')}",
            "display_color": dict(color),
            "color_source": color_source,
            "effectiveness_key": f"TYPE_EFFECTIVENESS_ROW_{type_id:02d}",
            "effectiveness": matrix,
            "special_rule": special_rule,
            "tera_input_code": type_id + 1,
            "runtime_binding": runtime_binding,
            "status": status,
            "vega_evidence": vega_evidence,
        }
        rows.append(row)
        manifest.append(
            {
                "type_key": key,
                "id": str(type_id),
                "vega_id": "NONE" if vega_id is None else str(vega_id),
                "cfru_id": str(type_id),
                "cfru_symbol": row["cfru_symbol"] or "NONE",
                "dpe_symbol": row["dpe_symbol"] or "NONE",
                "classification": classification,
                "display_name": display,
                "icon_key": icon_key,
                "icon_width": str(icon_geometry["width"]),
                "icon_height": str(icon_geometry["height"]),
                "icon_tile_offset": str(icon_geometry["tile_offset"]),
                "icon_source": icon_source,
                "color_key": row["color_key"],
                "color_r": str(color["r"]),
                "color_g": str(color["g"]),
                "color_b": str(color["b"]),
                "color_bgr555": str(color["bgr555"]),
                "color_source": color_source,
                "effectiveness_key": row["effectiveness_key"],
                "special_rule": special_rule,
                "tera_input_code": str(type_id + 1),
                "status": status,
                "notes": runtime_binding,
            }
        )

    # Vegaの0..17は疎な3-byte表と同じ意味であることを全組合せで検査する。
    vega_matrix = [[10 for _ in range(18)] for _ in range(18)]
    for relation in vega["type_effectiveness"]:
        vega_matrix[relation["attacking_type_id"]][relation["defending_type_id"]] = relation[
            "multiplier_tenths"
        ]
    for attack in range(18):
        for defend in range(18):
            cfru_value = rows[attack]["effectiveness"][defend]
            normalized = 0 if cfru_value == 1 else cfru_value // 100
            if normalized != vega_matrix[attack][defend]:
                _fail(
                    f"Vega/CFRU type semantic mismatch at {attack}->{defend}: "
                    f"{vega_matrix[attack][defend]} != {normalized}"
                )
    fairy = rows[23]
    required_fairy = {(23, 1): 2000, (23, 16): 2000, (23, 17): 2000, (16, 23): 1}
    for (attack, defend), expected in required_fairy.items():
        if rows[attack]["effectiveness"][defend] != expected:
            _fail(f"Fairy effectiveness contract is incomplete at {attack}->{defend}")
    return rows, manifest


def _build_abilities(
    config: Mapping[str, Any], vega: Mapping[str, Any], cfru: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    policy = config["mapping_policy"]["ability"]
    key_overrides = {int(key): value for key, value in policy["vega_key_overrides"].items()}
    rows: list[dict[str, Any]] = []
    aliases: list[dict[str, Any]] = []
    manifest: list[dict[str, str]] = []
    cfru_by_id = {row["id"]: row for row in cfru["abilities"]}
    cfru_to_canonical: dict[int, int] = {}

    for vega_row in vega["abilities"]:
        ability_id = vega_row["id"]
        if ability_id <= 75:
            source = cfru_by_id[ability_id]
            cfru_id: int | None = ability_id
            cfru_symbol = source["symbol"]
            classification = "VEGA_CFRU_CANONICAL"
            cfru_to_canonical[ability_id] = ability_id
            effect_key = f"ABILITY_EFFECT_{cfru_symbol.removeprefix('ABILITY_')}"
        elif ability_id == 76:
            source = None
            cfru_id = None
            cfru_symbol = ""
            classification = "VEGA_EXCLUSIVE"
            effect_key = "ABILITY_EFFECT_CACOPHONY_VEGA"
        else:
            source = cfru_by_id[76]
            cfru_id = 76
            cfru_symbol = source["symbol"]
            classification = "VEGA_CFRU_CANONICAL"
            cfru_to_canonical[76] = 77
            effect_key = "ABILITY_EFFECT_AIRLOCK"
        key = key_overrides.get(
            ability_id,
            source["canonical_key"] if source is not None else f"ABILITY_KEY_VEGA_{ability_id:03d}",
        )
        row = {
            "id": ability_id,
            "ability_key": key,
            "vega_id": ability_id,
            "cfru_id": cfru_id,
            "cfru_symbol": cfru_symbol,
            "dpe_symbol": cfru_symbol,
            "classification": classification,
            "display_name": vega_row["name_decoded"],
            "description": vega_row["description_decoded"],
            "description_raw": vega_row["description_raw"],
            "effect_key": effect_key,
            "rating": None if source is None else source["rating"],
            "runtime_binding": "VEGA_FROZEN_RUNTIME",
            "vega_raw": vega_row,
        }
        rows.append(row)
        manifest.append(
            {
                "ability_key": key,
                "id": str(ability_id),
                "vega_id": str(ability_id),
                "cfru_id": "NONE" if cfru_id is None else str(cfru_id),
                "cfru_symbol": cfru_symbol or "NONE",
                "dpe_symbol": cfru_symbol or "NONE",
                "classification": classification,
                "display_name": row["display_name"],
                "description_key": _description_key("ABILITY", key),
                "effect_key": effect_key,
                "runtime_binding": row["runtime_binding"],
                "status": "FROZEN",
                "notes": "Vega table row preserved byte-for-byte",
            }
        )

    for source_id in range(77, 311):
        source = cfru_by_id[source_id]
        canonical_id = 78 + (source_id - 77)
        cfru_to_canonical[source_id] = canonical_id
        key = source["canonical_key"]
        row = {
            "id": canonical_id,
            "ability_key": key,
            "vega_id": None,
            "cfru_id": source_id,
            "cfru_symbol": source["symbol"],
            "dpe_symbol": source["symbol"],
            "classification": "CFRU_APPEND",
            "display_name": source["name_ja"],
            "description": source["description_ja"],
            "description_raw": None,
            "effect_key": f"ABILITY_EFFECT_{source['symbol'].removeprefix('ABILITY_')}",
            "rating": source["rating"],
            "runtime_binding": "T06_CFRU_RUNTIME_BIND_PENDING",
            "vega_raw": None,
        }
        rows.append(row)
        manifest.append(
            {
                "ability_key": key,
                "id": str(canonical_id),
                "vega_id": "NONE",
                "cfru_id": str(source_id),
                "cfru_symbol": source["symbol"],
                "dpe_symbol": source["symbol"],
                "classification": "CFRU_APPEND",
                "display_name": source["name_ja"],
                "description_key": _description_key("ABILITY", key),
                "effect_key": row["effect_key"],
                "runtime_binding": row["runtime_binding"],
                "status": "APPENDED",
                "notes": "CFRU/DPE source ID alias generated",
            }
        )

    if [row["id"] for row in rows] != list(range(312)):
        _fail("ability canonical IDs are not contiguous 0..311")
    for source in cfru["abilities"]:
        canonical_id = cfru_to_canonical.get(source["id"])
        if canonical_id is None:
            _fail(f"unresolved CFRU ability {source['symbol']}")
        aliases.append(
            {
                "source_id": source["id"],
                "source_symbol": source["symbol"],
                "canonical_id": canonical_id,
                "ability_key": rows[canonical_id]["ability_key"],
            }
        )
    return rows, aliases, manifest


def _item_role(source: Mapping[str, Any] | None, pocket: str, battle_usage: int) -> str:
    if pocket == "POCKET_POKE_BALLS":
        return "BALL"
    if pocket == "POCKET_TM_CASE":
        return "TM_HM"
    if pocket == "POCKET_BERRIES":
        return "BERRY"
    if pocket == "POCKET_KEY_ITEMS":
        return "KEY_ITEM"
    if battle_usage:
        return "BATTLE_ITEM"
    if source is not None and source["hold_effect"]:
        return "HELD_ITEM"
    return "FIELD_ITEM"


def _cfru_item_projection(source: Mapping[str, Any]) -> dict[str, Any]:
    pocket = (
        "POCKET_BERRIES"
        if source["pocket_symbol"] == "POCKET_BERRY_POUCH"
        else source["pocket_symbol"]
    )
    field_callback = _none(source["field_callback_symbol"])
    battle_callback = _none(source["battle_callback_symbol"])
    ball_kind = (
        f"BALL_KIND_{source['symbol'].removeprefix('ITEM_').removesuffix('_BALL')}"
        if pocket == "POCKET_POKE_BALLS"
        else "NONE"
    )
    return {
        "description": source["description_ja"] or "ー",
        "description_key": source["description_symbol"] or f"DESC_{source['symbol']}",
        "icon_key": source["icon_symbol"],
        "palette_key": source["palette_symbol"],
        "pocket": pocket,
        "price": source["price"],
        "importance": source["importance"],
        "role": _item_role(source, pocket, source["battle_usage"]),
        "item_type_key": source["item_type_key"],
        "item_type_id": source["item_type_id"],
        "item_type_explicit": source["item_type_explicit"],
        "item_type_source": (
            f"{source['item_type_source_ref']['path']}:"
            f"{source['item_type_source_ref']['line']}:"
            f"{source['item_type_source_ref']['symbol']}"
        ),
        "is_evolution_stone": source["is_evolution_stone"],
        "is_evolution_item": source["is_evolution_item"],
        "hold_effect_key": _none(source["hold_effect_symbol"]),
        "hold_effect_param": str(source["hold_effect_param"]),
        "field_effect_key": "NONE",
        "field_effect_param": "NONE",
        "field_use_callback_key": field_callback,
        "battle_usage": source["battle_usage"],
        "battle_effect_key": "NONE" if not source["battle_usage"] else f"BATTLE_USE_{battle_callback}",
        "battle_effect_param": "NONE",
        "battle_use_callback_key": battle_callback,
        "secondary_id": source["secondary_id"],
        "ball_kind": ball_kind,
        "consume_policy": "ON_EFFECT" if source["importance"] == 0 else "NEVER",
        "target_policy": "PARTY_ONE" if source["use_type_symbol"] == "ITEM_USE_PARTY_MENU" else "NONE",
        "supply_key": "SUPPLY_T12_T16_PENDING",
        "runtime_binding": "T06_CFRU_RUNTIME_BIND_PENDING",
        "source_use_type": source["use_type_symbol"],
        "source_mystery": source["mystery"],
    }


def _vega_item_projection(source: Mapping[str, Any]) -> dict[str, Any]:
    pockets = {
        1: "POCKET_ITEMS",
        2: "POCKET_KEY_ITEMS",
        3: "POCKET_POKE_BALLS",
        4: "POCKET_TM_CASE",
        5: "POCKET_BERRIES",
    }
    pocket = pockets.get(source["pocket"])
    if pocket is None:
        _fail(f"Vega item {source['id']} has unsupported pocket {source['pocket']}")
    return {
        "description": source["description_decoded"],
        "description_key": f"VEGA_ITEM_DESC_{source['id']:03d}",
        "icon_key": f"VEGA_ITEM_ICON_{source['id']:03d}",
        "palette_key": f"VEGA_ITEM_PALETTE_{source['id']:03d}",
        "pocket": pocket,
        "price": source["price"],
        "importance": source["importance"],
        "role": _item_role(source, pocket, source["battle_usage"]),
        "item_type_key": "ITEM_TYPE_VEGA_FROZEN",
        "item_type_id": 0,
        "item_type_explicit": False,
        "item_type_source": "Vega ROM frozen item row",
        "is_evolution_stone": False,
        "is_evolution_item": False,
        "hold_effect_key": f"VEGA_HOLD_EFFECT_{source['hold_effect']:03d}" if source["hold_effect"] else "NONE",
        "hold_effect_param": str(source["hold_effect_param"]),
        "field_effect_key": "VEGA_FROZEN_CALLBACK" if source["field_callback_pointer"] else "NONE",
        "field_effect_param": "NONE",
        "field_use_callback_key": (
            f"VEGA_FIELD_CB_{source['field_callback_pointer']:08X}"
            if source["field_callback_pointer"]
            else "NONE"
        ),
        "battle_usage": source["battle_usage"],
        "battle_effect_key": "VEGA_FROZEN_CALLBACK" if source["battle_callback_pointer"] else "NONE",
        "battle_effect_param": "NONE",
        "battle_use_callback_key": (
            f"VEGA_BATTLE_CB_{source['battle_callback_pointer']:08X}"
            if source["battle_callback_pointer"]
            else "NONE"
        ),
        "secondary_id": source["secondary_id"],
        "ball_kind": (
            f"BALL_KIND_VEGA_ITEM_{source['id']:03d}"
            if pocket == "POCKET_POKE_BALLS"
            else "NONE"
        ),
        "consume_policy": "VEGA_FROZEN",
        "target_policy": "VEGA_FROZEN",
        "supply_key": "SUPPLY_VEGA_EXISTING",
        "runtime_binding": "VEGA_FROZEN_RUNTIME",
        "source_use_type": str(source["field_use_type"]),
        "source_mystery": source["registrability"],
    }


def _apply_qol_contracts(
    config: Mapping[str, Any], rows: list[dict[str, Any]], by_symbol: Mapping[str, int]
) -> None:
    contracts = list(config["qol_contracts"])
    mint = config["mint_contract"]
    if len(mint["source_symbols"]) != 21 or len(mint["nature_keys"]) != 21:
        _fail("mint contract must contain exactly 21 aligned symbols/natures")
    for symbol, nature in zip(mint["source_symbols"], mint["nature_keys"]):
        contracts.append(
            {
                "source_symbol": symbol,
                "item_key": f"ITEM_KEY_{symbol.removeprefix('ITEM_')}",
                "field_effect_key": mint["field_effect_key"],
                "field_effect_param": nature,
                "runtime_binding": mint["runtime_binding"],
                "supply_key": mint["supply_key"],
            }
        )
    for contract in contracts:
        symbol = contract["source_symbol"]
        if symbol not in by_symbol:
            _fail(f"QOL source symbol is unresolved: {symbol}")
        row = rows[by_symbol[symbol]]
        if row["item_key"] != contract["item_key"]:
            _fail(f"QOL stable key mismatch for {symbol}: {row['item_key']}")
        row["field_effect_key"] = contract["field_effect_key"]
        row["field_effect_param"] = contract.get("field_effect_param", "NONE")
        row["runtime_binding"] = contract["runtime_binding"]
        row["supply_key"] = contract["supply_key"]
        if symbol in {
            "ITEM_EVERSTONE",
            "ITEM_DESTINY_KNOT",
            "ITEM_POWER_WEIGHT",
            "ITEM_POWER_BRACER",
            "ITEM_POWER_BELT",
            "ITEM_POWER_ANKLET",
            "ITEM_POWER_LENS",
            "ITEM_POWER_BAND",
        }:
            row["consume_policy"] = "NEVER"
            row["target_policy"] = "HELD"
        elif symbol == "ITEM_OVAL_CHARM":
            row["consume_policy"] = "NEVER"
            row["target_policy"] = "PASSIVE_KEY_ITEM"
        else:
            row["consume_policy"] = "ON_EFFECT"
            row["target_policy"] = "PARTY_ONE"
        if symbol in ("ITEM_BOTTLE_CAP", "ITEM_GOLD_BOTTLE_CAP"):
            row["field_use_callback_key"] = "SERVICE_CB_HYPER_TRAIN"


def _build_items(
    config: Mapping[str, Any], vega: Mapping[str, Any], cfru: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    policy = config["mapping_policy"]["item"]
    if policy.get("automatic_match") != "SAME_SOURCE_ID_NFKC_NAME_DESCRIPTION_SEMANTIC_ABI":
        _fail("item automatic match must require name, description, and semantic ABI")
    if policy.get("cross_id_match") != "EXPLICIT_OVERRIDES_ONLY" or policy.get("reuse_holes") is not False:
        _fail("item cross-ID/reuse policy changed")
    key_overrides = {int(key): value for key, value in policy["vega_key_overrides"].items()}
    source_overrides = {int(key): int(value) for key, value in policy["source_overrides"].items()}
    override_evidence = {
        int(key): value for key, value in policy.get("source_override_evidence", {}).items()
    }
    distinct_evidence = {
        int(key): value
        for key, value in policy.get("source_distinct_evidence", {}).items()
    }
    if set(source_overrides) != {74, 186, 348} or set(override_evidence) != set(source_overrides):
        _fail("item semantic source overrides/evidence changed")
    if any(not isinstance(value, str) or not value.strip() for value in override_evidence.values()):
        _fail("item semantic source override evidence must be non-empty")
    if set(distinct_evidence) != {80} or any(
        not isinstance(value, str) or not value.strip() for value in distinct_evidence.values()
    ):
        _fail("item semantic distinct evidence changed")
    explicit_source_for_vega = {vega_id: source_id for source_id, vega_id in source_overrides.items()}
    if len(explicit_source_for_vega) != len(source_overrides):
        _fail("item source overrides target the same Vega ID more than once")
    rows: list[dict[str, Any]] = []
    aliases: list[dict[str, Any]] = []
    manifest: list[dict[str, str]] = []
    cfru_by_id = {row["id"]: row for row in cfru["items"]}
    source_to_canonical: dict[int, int] = {}

    def address(value: object) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value, 0)
        _fail(f"item ABI address has an invalid type: {value!r}")

    def semantic_abi_matches(
        vega_item: Mapping[str, Any], cfru_item: Mapping[str, Any]
    ) -> bool:
        plain_fields = (
            ("hold_effect", "hold_effect"),
            ("hold_effect_param", "hold_effect_param"),
            ("registrability", "mystery"),
            ("importance", "importance"),
            ("pocket", "pocket"),
            ("field_use_type", "use_type"),
            ("battle_usage", "battle_usage"),
            ("secondary_id", "secondary_id"),
        )
        address_fields = (
            ("field_callback_pointer", "field_callback_address"),
            ("battle_callback_pointer", "battle_callback_address"),
        )
        return all(vega_item[left] == cfru_item[right] for left, right in plain_fields) and all(
            address(vega_item[left]) == address(cfru_item[right])
            for left, right in address_fields
        )

    def explicit_identity_matches(
        source_id: int,
        vega_item: Mapping[str, Any],
        cfru_item: Mapping[str, Any],
    ) -> bool:
        if not semantic_abi_matches(vega_item, cfru_item):
            return False
        name_matches = _norm(vega_item["name_decoded"]) == _norm(cfru_item["name_ja"])
        description_matches = _norm(vega_item["description_decoded"]) == _norm(
            cfru_item["description_ja"]
        )
        return {
            74: (not name_matches and description_matches),
            186: (name_matches and not description_matches),
            348: (name_matches and description_matches),
        }.get(source_id, False)

    for source in vega["items"]:
        item_id = source["id"]
        candidate_id = explicit_source_for_vega.get(item_id, item_id)
        candidate = cfru_by_id[candidate_id]
        automatic_match = (
            source["slot_state"] != "unused"
            and _norm(source["name_decoded"]) == _norm(candidate["name_ja"])
            and _norm(source["description_decoded"])
            == _norm(candidate["description_ja"])
            and semantic_abi_matches(source, candidate)
        )
        explicit_match = item_id in explicit_source_for_vega
        if explicit_match and not explicit_identity_matches(candidate_id, source, candidate):
            _fail(f"item explicit semantic identity evidence changed for source {candidate_id}")
        if item_id in distinct_evidence and (explicit_match or automatic_match):
            _fail(f"item {item_id} must remain a distinct Vega/CFRU entity")
        mapped = explicit_match or automatic_match
        if mapped:
            source_to_canonical[candidate_id] = item_id
            cfru_id: int | None = candidate_id
            cfru_symbol = candidate["symbol"]
            key = key_overrides.get(item_id, candidate["canonical_key"])
            classification = "VEGA_CFRU_CANONICAL"
        else:
            cfru_id = None
            cfru_symbol = ""
            key = key_overrides.get(item_id, f"ITEM_KEY_VEGA_{item_id:03d}")
            classification = "VEGA_EXCLUSIVE"
        projection = _vega_item_projection(source)
        if mapped:
            projection.update(
                {
                    "item_type_key": candidate["item_type_key"],
                    "item_type_id": candidate["item_type_id"],
                    "item_type_explicit": candidate["item_type_explicit"],
                    "item_type_source": (
                        f"{candidate['item_type_source_ref']['path']}:"
                        f"{candidate['item_type_source_ref']['line']}:"
                        f"{candidate['item_type_source_ref']['symbol']}"
                    ),
                    "is_evolution_stone": candidate["is_evolution_stone"],
                    "is_evolution_item": candidate["is_evolution_item"],
                    "ball_kind": (
                        f"BALL_KIND_{candidate['symbol'].removeprefix('ITEM_').removesuffix('_BALL')}"
                        if candidate["pocket_symbol"] == "POCKET_POKE_BALLS"
                        else "NONE"
                    ),
                }
            )
        row = {
            "id": item_id,
            "item_key": key,
            "vega_id": item_id,
            "cfru_id": cfru_id,
            "cfru_symbol": cfru_symbol,
            "classification": classification,
            "display_name": source["name_decoded"],
            **projection,
            "vega_raw": source,
            "cfru_source": candidate if mapped else None,
            "status": "FROZEN",
            "notes": (
                f"explicit semantic identity: {override_evidence[candidate_id]}; "
                "Vega 40-byte row and icon/palette pointers preserved"
                if explicit_match
                else "name/description/semantic ABI identity; Vega 40-byte row and icon/palette pointers preserved"
                if automatic_match
                else (
                    f"explicit distinct entity: {distinct_evidence[item_id]}; "
                    "Vega 40-byte row and icon/palette pointers preserved"
                    if item_id in distinct_evidence
                    else "semantic mismatch/distinct entity; Vega 40-byte row and icon/palette pointers preserved"
                )
            ),
        }
        rows.append(row)

    for source in cfru["items"]:
        if source["id"] in source_to_canonical:
            continue
        canonical_id = len(rows)
        source_to_canonical[source["id"]] = canonical_id
        projection = _cfru_item_projection(source)
        reserved = source["id"] == 375
        row = {
            "id": canonical_id,
            "item_key": source["canonical_key"],
            "vega_id": None,
            "cfru_id": source["id"],
            "cfru_symbol": source["symbol"],
            "classification": "CFRU_RESERVED" if reserved else "CFRU_APPEND",
            "display_name": source["name_ja"],
            **projection,
            "vega_raw": None,
            "cfru_source": source,
            "status": "RESERVED" if reserved else "APPENDED",
            "notes": "CFRU source ID alias generated",
        }
        rows.append(row)

    if len(rows) != 988:
        _fail(f"CFRU item merge expected 988 canonical rows before QOL, got {len(rows)}")
    by_symbol = {
        source["symbol"]: source_to_canonical[source["id"]] for source in cfru["items"]
    }
    _apply_qol_contracts(config, rows, by_symbol)

    source_icons = {row["icon_symbol"] for row in cfru["items"]}
    source_palettes = {row["palette_symbol"] for row in cfru["items"]}

    for spec in config["new_items"]:
        if spec["icon_key"] not in source_icons:
            _fail(f"QOL item icon is not resolved by CFRU inventory: {spec['icon_key']}")
        if spec["palette_key"] not in source_palettes:
            _fail(f"QOL item palette is not resolved by CFRU inventory: {spec['palette_key']}")
        canonical_id = len(rows)
        rows.append(
            {
                "id": canonical_id,
                "item_key": spec["item_key"],
                "vega_id": None,
                "cfru_id": None,
                "cfru_symbol": "",
                "classification": "QOL_APPEND",
                "display_name": spec["display_name"],
                "description": spec["description"],
                "description_key": _description_key("ITEM", spec["item_key"]),
                "icon_key": spec["icon_key"],
                "palette_key": spec["palette_key"],
                "pocket": spec["pocket"],
                "price": spec["price"],
                "importance": 0,
                "role": "FIELD_ITEM",
                "item_type_key": "ITEM_TYPE_QOL_FIELD_ITEM",
                "item_type_id": 0,
                "item_type_explicit": False,
                "item_type_source": "docs/QOL_POLICY.md",
                "is_evolution_stone": False,
                "is_evolution_item": False,
                "hold_effect_key": "NONE",
                "hold_effect_param": "0",
                "field_effect_key": spec["field_effect_key"],
                "field_effect_param": spec["field_effect_param"],
                "field_use_callback_key": spec["field_use_callback_key"],
                "battle_usage": 0,
                "battle_effect_key": "NONE",
                "battle_effect_param": "NONE",
                "battle_use_callback_key": "NONE",
                "secondary_id": 0,
                "ball_kind": "NONE",
                "consume_policy": "ON_EFFECT",
                "target_policy": "PARTY_ONE",
                "supply_key": spec["supply_key"],
                "runtime_binding": "T06_RUNTIME_BIND_PENDING",
                "source_use_type": "ITEM_USE_PARTY_MENU",
                "source_mystery": 0,
                "vega_raw": None,
                "cfru_source": None,
                "status": "APPENDED",
                "notes": "docs/QOL_POLICY.md contract; invalid target does not consume",
            }
        )

    if len(rows) != 999 or [row["id"] for row in rows] != list(range(999)):
        _fail("item canonical IDs are not contiguous 0..998")
    if len({row["item_key"] for row in rows}) != len(rows):
        _fail("item stable keys are not unique")

    for source in cfru["items"]:
        canonical_id = source_to_canonical.get(source["id"])
        if canonical_id is None:
            _fail(f"unresolved CFRU item {source['symbol']}")
        aliases.append(
            {
                "source_id": source["id"],
                "source_symbol": source["symbol"],
                "canonical_id": canonical_id,
                "item_key": rows[canonical_id]["item_key"],
            }
        )
    for alias in cfru["aliases"]:
        if alias["space"] != "item":
            continue
        canonical_id = source_to_canonical[alias["id"]]
        aliases.append(
            {
                "source_id": alias["id"],
                "source_symbol": alias["symbol"],
                "canonical_id": canonical_id,
                "item_key": rows[canonical_id]["item_key"],
            }
        )

    for row in rows:
        manifest.append(
            {
                "item_key": row["item_key"],
                "id": str(row["id"]),
                "vega_id": "NONE" if row["vega_id"] is None else str(row["vega_id"]),
                "cfru_id": "NONE" if row["cfru_id"] is None else str(row["cfru_id"]),
                "cfru_symbol": row["cfru_symbol"] or "NONE",
                "classification": row["classification"],
                "display_name": row["display_name"] or "ー",
                "description_key": row["description_key"],
                "icon_key": row["icon_key"],
                "palette_key": row["palette_key"],
                "pocket": row["pocket"],
                "price": str(row["price"]),
                "importance": str(row["importance"]),
                "role": row["role"],
                "item_type_key": row["item_type_key"],
                "item_type_id": str(row["item_type_id"]),
                "item_type_explicit": "1" if row["item_type_explicit"] else "0",
                "item_type_source": row["item_type_source"],
                "source_mystery": str(row["source_mystery"]),
                "is_evolution_stone": "1" if row["is_evolution_stone"] else "0",
                "is_evolution_item": "1" if row["is_evolution_item"] else "0",
                "hold_effect_key": row["hold_effect_key"],
                "hold_effect_param": row["hold_effect_param"],
                "field_effect_key": row["field_effect_key"],
                "field_effect_param": row["field_effect_param"],
                "field_use_callback_key": row["field_use_callback_key"],
                "battle_usage": str(row["battle_usage"]),
                "battle_effect_key": row["battle_effect_key"],
                "battle_effect_param": row["battle_effect_param"],
                "battle_use_callback_key": row["battle_use_callback_key"],
                "secondary_id": str(row["secondary_id"]),
                "ball_kind": row["ball_kind"],
                "consume_policy": row["consume_policy"],
                "target_policy": row["target_policy"],
                "supply_key": row["supply_key"],
                "runtime_binding": row["runtime_binding"],
                "status": row["status"],
                "notes": row["notes"],
            }
        )
    return rows, aliases, manifest


def _game_charmap_glyphs(root: Path, config: Mapping[str, Any]) -> set[str]:
    section = config.get("charmap")
    if not isinstance(section, Mapping):
        _fail("config.charmap is missing")
    logical = section.get("path")
    expected_sha = section.get("sha256")
    if not isinstance(logical, str) or Path(logical).is_absolute():
        _fail("config.charmap.path must be relative")
    path = root / logical
    if path.is_symlink() or not path.is_file():
        _fail("fixed charmap is missing/non-regular")
    raw = path.read_bytes()
    if not isinstance(expected_sha, str) or _sha256(raw) != expected_sha:
        _fail("fixed charmap hash changed")
    glyphs: set[str] = set()
    escapes = {r'\"': '"', r"\$": "$"}
    for line in raw.decode("utf-8-sig").splitlines():
        if len(line) < 3 or line[2] != "=":
            continue
        value = escapes.get(line[3:], line[3:])
        if len(value) == 1 and value not in {r"\n", r"\l", r"\p"}:
            glyphs.add(value)
    if not {" ", "0", "A", "あ", "ア", "。"}.issubset(glyphs):
        _fail("fixed charmap lacks required Japanese/UI glyphs")
    return glyphs


def _text_width_model(
    root: Path,
    config: Mapping[str, Any],
    types: Sequence[Mapping[str, Any]],
    abilities: Sequence[Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    limits = config["text_width"]
    glyphs = _game_charmap_glyphs(root, config)

    def widths(value: str, key: str) -> list[int]:
        normalized = value.replace("<SCROLL>", "\n").replace("<PAGE>", "\n")
        result: list[int] = []
        for line in normalized.split("\n"):
            unresolved = sorted({character for character in line if character not in glyphs})
            if unresolved:
                _fail(f"{key} uses characters absent from game charmap: {unresolved}")
            result.append(len(line))
        return result or [0]

    rows: list[dict[str, Any]] = []
    for domain, records, name_limit, description_limit in (
        ("type", types, limits["type_name_bytes"], None),
        ("ability", abilities, limits["ability_name_bytes"], limits["ability_description_line_bytes"]),
        ("item", items, limits["item_name_bytes"], limits["item_description_line_bytes"]),
    ):
        for record in records:
            key = record[f"{domain}_key"]
            name = record["display_name"] or "ー"
            name_widths = widths(name, key)
            if len(name_widths) != 1:
                _fail(f"{key} display name contains a control line break")
            name_width = name_widths[0]
            description = record.get("description", "") or ""
            line_widths = widths(description, f"{key} description")
            rows.append(
                {
                    "domain": domain,
                    "key": key,
                    "id": record["id"],
                    "name_encoded_width": name_width,
                    "name_limit": name_limit,
                    "description_line_widths": line_widths,
                    "description_line_limit": description_limit,
                    "overflow": name_width > name_limit
                    or (description_limit is not None and max(line_widths) > description_limit),
                }
            )
    overflows = [row for row in rows if row["overflow"]]
    return {
        "encoding": "CFRU-JP/charmap.tbl one-byte glyph ABI",
        "limits": dict(limits),
        "rows": rows,
        "summary": {"row_count": len(rows), "overflow_count": len(overflows)},
    }


def _fingerprint_inputs(root: Path, vega: Mapping[str, Any], cfru: Mapping[str, Any]) -> dict[str, Any]:
    files: dict[str, str] = {}
    for logical in FINGERPRINT_FILES:
        path = root / logical
        if path.is_symlink() or not path.is_file():
            _fail(f"fingerprint input is missing/non-regular: {logical}")
        files[logical] = _sha256_file(path)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_ID,
        "files": files,
        "vega_rom_sha256": vega["metadata"]["rom"]["sha256"],
        "cfru_inventory_sha256": cfru["metadata"]["inventory_sha256"],
        "repeat_count": 2,
    }


def _qol_effect_rows(model: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = [
        row
        for row in model["items"]
        if row["field_effect_key"] not in ("NONE", "VEGA_FROZEN_CALLBACK")
    ]
    config = model.get("qol_contract")
    if not isinstance(config, Mapping):
        _fail("model QOL contract is missing")
    required = config.get("required_item_keys")
    if (
        not isinstance(required, list)
        or len(required) != 45
        or len(set(required)) != 45
        or {row["item_key"] for row in rows} != set(required)
    ):
        _fail("QOL effect table must contain exactly the required 45 stable item keys")
    return rows


def build_id_space_model(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """固定入力から公開可能な統合modelを構築し、全acceptanceを検査する。"""

    if not isinstance(root, Path) or not isinstance(config, Mapping):
        _fail("root/config argument type is invalid")
    if config.get("schema_version") != SCHEMA_VERSION or config.get("task") != TASK_ID:
        _fail("config schema/task mismatch")
    try:
        vega = extract_vega_id_spaces(root, config)
        cfru = extract_cfru_id_spaces(root, config)
    except (VegaIdSpaceExtractionError, CFRUIdSpaceInventoryError) as error:
        _fail(str(error))

    types, type_manifest = _build_types(config, vega, cfru)
    abilities, ability_aliases, ability_manifest = _build_abilities(config, vega, cfru)
    items, item_aliases, item_manifest = _build_items(config, vega, cfru)
    text_width = _text_width_model(root, config, types, abilities, items)
    if text_width["summary"]["overflow_count"]:
        examples = [row["key"] for row in text_width["rows"] if row["overflow"]][:5]
        _fail(f"game text width overflow: {examples}")

    ranges = _load_ranges(root)
    _require_range(ranges, "type", "Vega", 0, 17)
    _require_range(ranges, "type", "CFRU-JP", 18, 24)
    _require_range(ranges, "ability", "Vega", 0, 77)
    _require_range(ranges, "ability", "CFRU-JP", 78, 311)
    _require_range(ranges, "item", "Vega", 0, 374)
    _require_range(ranges, "item", "CFRU-JP", 375, 987)
    _require_range(ranges, "item", "QOL", 988, 998)

    # QOL効果の意味をconfigではなくmodelでも明示的に検査する。
    by_item_key = {row["item_key"]: row for row in items}
    candy_values = [100, 800, 3000, 10000, 30000]
    for suffix, expected in zip(("XS", "S", "M", "L", "XL"), candy_values):
        row = by_item_key[f"ITEM_KEY_EXP_CANDY_{suffix}"]
        if row["field_effect_key"] != "EXP_ADD_FIXED" or int(row["field_effect_param"]) != expected:
            _fail(f"experience candy {suffix} contract mismatch")
    for stat in ("HP", "ATK", "DEF", "SPEED", "SPATK", "SPDEF"):
        row = by_item_key[f"ITEM_KEY_EV_RESET_{stat}"]
        if row["field_effect_key"] != "EV_SET_ZERO" or row["field_effect_param"] != f"STAT_{stat}":
            _fail(f"EV reset {stat} contract mismatch")
    if by_item_key["ITEM_KEY_OVAL_CHARM"]["field_effect_key"] != "BREEDING_CHECK_MULTIPLIER_X2_CAP100":
        _fail("Oval Charm must use the QOL x2/cap100 adapter contract")

    required_qol_keys = [contract["item_key"] for contract in config["qol_contracts"]]
    required_qol_keys.extend(
        f"ITEM_KEY_{symbol.removeprefix('ITEM_')}"
        for symbol in config["mint_contract"]["source_symbols"]
    )
    required_qol_keys.extend(spec["item_key"] for spec in config["new_items"])
    if len(required_qol_keys) != 45 or len(set(required_qol_keys)) != 45:
        _fail("config must define exactly 45 unique QOL item keys")

    fingerprint_inputs = _fingerprint_inputs(root, vega, cfru)
    summary = {
        "type_count": len(types),
        "active_type_count": sum(row["classification"] not in ("CFRU_RESERVED", "CFRU_SENTINEL") for row in types),
        "ability_count": len(abilities),
        "frozen_ability_count": 78,
        "appended_ability_count": 234,
        "item_count": len(items),
        "frozen_item_count": 375,
        "cfru_appended_item_count": 613,
        "qol_appended_item_count": 11,
        "cfru_ability_alias_count": len(ability_aliases),
        "cfru_item_alias_count": len(item_aliases),
        "item_semantic_identity_count": sum(
            row["classification"] == "VEGA_CFRU_CANONICAL" for row in items[:375]
        ),
        "item_type_explicit_count": sum(row["item_type_explicit"] for row in items),
        "evolution_stone_count": sum(row["is_evolution_stone"] for row in items),
        "evolution_item_count": sum(row["is_evolution_item"] for row in items),
        "ball_kind_count": sum(row["ball_kind"] != "NONE" for row in items),
        "qol_effect_count": len(required_qol_keys),
        "text_width_overflow_count": text_width["summary"]["overflow_count"],
        "last_ability_id": abilities[-1]["id"],
        "last_item_id": items[-1]["id"],
    }
    runtime_handoff = {
        "task": "T06",
        "semantic_tables_are_runtime_abi": False,
        "canonical_rebuilds": [
            {
                "table_key": "ITEM_DATA",
                "source_rows": 774,
                "canonical_rows": 999,
                "runtime_abi": "struct Item",
                "mapping": "item_aliases.source_id_to_canonical_id",
            },
            {
                "table_key": "ITEM_GRAPHICS",
                "source_rows": 774,
                "canonical_rows": 999,
                "runtime_abi": "struct ItemIconTemplate",
                "mapping": "item_aliases.source_id_to_canonical_id",
            },
            {
                "table_key": "ABILITY_NAMES",
                "source_rows": 311,
                "canonical_rows": 312,
                "runtime_abi": "game_charmap_strings",
                "mapping": "ability_aliases.source_id_to_canonical_id",
            },
            {
                "table_key": "ABILITY_DESCRIPTIONS",
                "source_rows": 311,
                "canonical_rows": 312,
                "runtime_abi": "game_charmap_strings",
                "mapping": "ability_aliases.source_id_to_canonical_id",
            },
        ],
        "hard_gates": [
            "REBUILD_CANONICAL_POSITIONAL_TABLES",
            "REPOINT_ALL_RUNTIME_CONSUMERS",
            "ROUND_TRIP_ALL_CANONICAL_ROWS",
            "REJECT_SOURCE_ID_DIRECT_INDEXING",
            "KEEP_ITEM_OBTAINED_FLAGS_DISABLED_UNTIL_T08_RESIZE_OR_TRANSLATION",
        ],
    }
    model = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_ID,
        "activation_task": config["activation_task"],
        "summary": summary,
        "fingerprint": _stable_digest(fingerprint_inputs),
        "fingerprint_inputs": fingerprint_inputs,
        "sources": {
            "vega": vega["metadata"],
            "cfru_dpe": cfru["metadata"],
        },
        "types": types,
        "abilities": abilities,
        "ability_aliases": ability_aliases,
        "items": items,
        "item_aliases": item_aliases,
        "text_width": text_width,
        "manifests": {
            "type": type_manifest,
            "ability": ability_manifest,
            "item": item_manifest,
        },
        "range_contracts": [dict(row) for row in ranges if row["domain"] in {"type", "ability", "item"}],
        "qol_contract": {"required_item_keys": sorted(required_qol_keys)},
        "runtime_handoff": runtime_handoff,
    }
    validate_id_space_model(model)
    return model


def validate_id_space_model(model: Mapping[str, Any]) -> None:
    if model.get("schema_version") != SCHEMA_VERSION or model.get("task") != TASK_ID:
        _fail("model schema/task mismatch")
    expectations = (("types", 25), ("abilities", 312), ("items", 999))
    for name, count in expectations:
        rows = model.get(name)
        if not isinstance(rows, list) or len(rows) != count:
            _fail(f"model {name} count mismatch")
        if [row.get("id") for row in rows] != list(range(count)):
            _fail(f"model {name} IDs are not contiguous")
        key_name = {"types": "type_key", "abilities": "ability_key", "items": "item_key"}[name]
        keys = [row.get(key_name) for row in rows]
        if any(not isinstance(key, str) or not key.startswith(key_name.split("_")[0].upper() + "_KEY_") for key in keys):
            _fail(f"model {name} contains invalid stable keys")
        if len(keys) != len(set(keys)):
            _fail(f"model {name} contains duplicate stable keys")
    ability_aliases = model.get("ability_aliases")
    if not isinstance(ability_aliases, list) or len(ability_aliases) != 311:
        _fail("every CFRU ability must resolve exactly once")
    if [row["source_id"] for row in ability_aliases] != list(range(311)):
        _fail("CFRU ability aliases are not source-ID ordered")
    item_aliases = model.get("item_aliases")
    if not isinstance(item_aliases, list) or len(item_aliases) != 827:
        _fail("every CFRU item symbol/alias must resolve exactly once")
    source_symbols = [row["source_symbol"] for row in item_aliases]
    if len(source_symbols) != len(set(source_symbols)):
        _fail("CFRU item symbols resolve more than once")
    stable_pockets = {
        "POCKET_ITEMS",
        "POCKET_KEY_ITEMS",
        "POCKET_POKE_BALLS",
        "POCKET_TM_CASE",
        "POCKET_BERRIES",
    }
    if any(row.get("pocket") not in stable_pockets for row in model["items"]):
        _fail("item model contains an unresolved/non-stable pocket key")
    if sum(
        row["classification"] == "VEGA_CFRU_CANONICAL"
        for row in model["items"][:375]
    ) != 161:
        _fail("item semantic identity set must contain exactly 161 proven entities")
    if sum(bool(row.get("item_type_explicit")) for row in model["items"]) != 465:
        _fail("CFRU item-type explicit set must contain exactly 465 entities")
    if sum(bool(row.get("is_evolution_stone")) for row in model["items"]) != 12:
        _fail("canonical evolution-stone set must contain exactly 12 entities")
    if sum(bool(row.get("is_evolution_item")) for row in model["items"]) != 40:
        _fail("canonical evolution-item set must contain exactly 40 entities")
    if sum(
        bool(row.get("is_evolution_item")) and row.get("hold_effect_key") != "NONE"
        for row in model["items"]
    ) != 9:
        _fail("held+evolution multi-role set must contain exactly 9 entities")
    balls = [row for row in model["items"] if row.get("ball_kind") != "NONE"]
    if (
        len(balls) != 27
        or len({row["ball_kind"] for row in balls}) != 27
        or any(
            row["pocket"] != "POCKET_POKE_BALLS" or row["role"] != "BALL"
            for row in balls
        )
    ):
        _fail("canonical ball-kind mapping must resolve exactly 27 unique balls")
    handoff = model.get("runtime_handoff")
    expected_rebuilds = {
        ("ITEM_DATA", 774, 999, "struct Item"),
        ("ITEM_GRAPHICS", 774, 999, "struct ItemIconTemplate"),
        ("ABILITY_NAMES", 311, 312, "game_charmap_strings"),
        ("ABILITY_DESCRIPTIONS", 311, 312, "game_charmap_strings"),
    }
    if (
        not isinstance(handoff, Mapping)
        or handoff.get("task") != "T06"
        or handoff.get("semantic_tables_are_runtime_abi") is not False
        or {
            (
                row.get("table_key"),
                row.get("source_rows"),
                row.get("canonical_rows"),
                row.get("runtime_abi"),
            )
            for row in handoff.get("canonical_rebuilds", [])
            if isinstance(row, Mapping)
        }
        != expected_rebuilds
        or set(handoff.get("hard_gates", []))
        != {
            "REBUILD_CANONICAL_POSITIONAL_TABLES",
            "REPOINT_ALL_RUNTIME_CONSUMERS",
            "ROUND_TRIP_ALL_CANONICAL_ROWS",
            "REJECT_SOURCE_ID_DIRECT_INDEXING",
            "KEEP_ITEM_OBTAINED_FLAGS_DISABLED_UNTIL_T08_RESIZE_OR_TRANSLATION",
        }
    ):
        _fail("T06 positional runtime-table handoff contract changed")
    for row in model["types"]:
        icon = row.get("icon_geometry")
        color = row.get("display_color")
        if (
            not isinstance(icon, Mapping)
            or set(icon) != {"width", "height", "tile_offset"}
            or any(not isinstance(value, int) or value < 0 for value in icon.values())
            or not isinstance(row.get("icon_source"), str)
            or not row["icon_source"]
        ):
            _fail(f"type {row['type_key']} has unresolved icon geometry/source")
        if (
            not isinstance(color, Mapping)
            or set(color) != {"r", "g", "b", "bgr555"}
            or any(not isinstance(color[key], int) for key in color)
            or not all(0 <= color[key] <= 31 for key in ("r", "g", "b"))
            or color["bgr555"]
            != color["r"] | (color["g"] << 5) | (color["b"] << 10)
            or not isinstance(row.get("color_source"), str)
            or not row["color_source"]
        ):
            _fail(f"type {row['type_key']} has unresolved display color/source")
    stellar = model["types"][24]
    if (
        stellar["classification"] != "CFRU_APPEND"
        or stellar["special_rule"] != "STELLAR_CFRU_SPECIAL"
        or stellar["runtime_binding"] != "T06_RUNTIME_BIND_PENDING"
    ):
        _fail("Stellar must remain an active T06 battle-core input")
    for row in model["items"]:
        required = (
            "description_key",
            "icon_key",
            "palette_key",
            "pocket",
            "role",
            "item_type_key",
            "item_type_source",
            "hold_effect_key",
            "field_effect_key",
            "field_use_callback_key",
            "battle_effect_key",
            "battle_use_callback_key",
            "consume_policy",
            "target_policy",
            "supply_key",
            "runtime_binding",
        )
        if any(row.get(key) in (None, "") for key in required):
            _fail(f"item {row['item_key']} has unresolved logical fields")
        if not isinstance(row.get("source_mystery"), int) or not 0 <= row["source_mystery"] <= 0xFF:
            _fail(f"item {row['item_key']} has invalid source mystery byte")
    _qol_effect_rows(model)


def _render_csv(header: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if set(row) != set(header):
            _fail(f"manifest row/header mismatch for {row}")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _render_header(model: Mapping[str, Any]) -> bytes:
    lines = [
        "/* Generated by scripts/build_id_spaces.py; do not edit. */",
        "#ifndef GUARD_T05_IDS_GENERATED_H",
        "#define GUARD_T05_IDS_GENERATED_H",
        "#include <stdint.h>",
        "",
        f"#define ID_SPACE_TYPE_COUNT {len(model['types'])}u",
        f"#define ID_SPACE_ABILITY_COUNT {len(model['abilities'])}u",
        f"#define ID_SPACE_ITEM_COUNT {len(model['items'])}u",
        "",
    ]
    for row in model["types"]:
        lines.append(f"#define {row['type_key']} {row['id']}u")
    lines.append("")

    def redefine_alias(symbol: str, key: str) -> None:
        lines.extend(
            [
                f"#ifdef {symbol}",
                f"#undef {symbol}",
                "#endif",
                f"#define {symbol} {key}",
            ]
        )

    for row in model["types"]:
        if row["cfru_symbol"] is not None:
            redefine_alias(row["cfru_symbol"], row["type_key"])
    lines.append("")
    for row in model["abilities"]:
        lines.append(f"#define {row['ability_key']} {row['id']}u")
    lines.append("")
    for alias in model["ability_aliases"]:
        redefine_alias(alias["source_symbol"], alias["ability_key"])
    lines.append("")
    for row in model["items"]:
        lines.append(f"#define {row['item_key']} {row['id']}u")
    lines.append("")
    for alias in model["item_aliases"]:
        redefine_alias(alias["source_symbol"], alias["item_key"])
    lines.extend(
        [
            "",
            "struct IdSpaceTypeRow { uint16_t id; uint8_t tera_input_code; uint8_t classification; uint8_t icon_width; uint8_t icon_height; uint16_t icon_tile_offset; uint16_t color_bgr555; uint16_t reserved; uint32_t icon_token; uint32_t color_token; uint32_t special_rule_token; };",
            "struct IdSpaceAbilityRow { uint16_t id; int8_t rating; uint8_t classification; uint32_t effect_token; const char *key; };",
            "#ifdef ABILITIES_COUNT",
            "#undef ABILITIES_COUNT",
            "#endif",
            "#define ABILITIES_COUNT ID_SPACE_ABILITY_COUNT",
            "#ifdef ITEMS_COUNT",
            "#undef ITEMS_COUNT",
            "#endif",
            "#define ITEMS_COUNT ID_SPACE_ITEM_COUNT",
            "",
            "enum { ID_SPACE_ITEM_FLAG_TYPE_EXPLICIT = 1u, ID_SPACE_ITEM_FLAG_EVOLUTION_STONE = 2u, ID_SPACE_ITEM_FLAG_EVOLUTION_ITEM = 4u };",
            "struct IdSpaceItemRow { uint16_t id; uint16_t price; uint8_t importance; uint8_t battle_usage; uint8_t item_type_id; uint8_t item_flags; uint8_t classification; uint8_t source_mystery; uint16_t secondary_id; uint32_t description_token; uint32_t icon_token; uint32_t palette_token; uint32_t pocket_token; uint32_t source_use_type_token; uint32_t role_token; uint32_t hold_token; uint32_t hold_param_token; uint32_t field_token; uint32_t field_param_token; uint32_t field_callback_token; uint32_t battle_token; uint32_t battle_param_token; uint32_t battle_callback_token; uint32_t ball_kind_token; uint32_t consume_policy_token; uint32_t target_policy_token; uint32_t supply_token; uint32_t runtime_binding_token; const char *key; };",
            "struct IdSpaceQolEffect { uint16_t item_id; uint16_t value; uint32_t effect_token; uint32_t parameter_token; };",
            "extern const struct IdSpaceTypeRow gIdSpaceTypes[ID_SPACE_TYPE_COUNT];",
            "extern const uint16_t gIdSpaceTypeEffectiveness[ID_SPACE_TYPE_COUNT][ID_SPACE_TYPE_COUNT];",
            "extern const struct IdSpaceAbilityRow gIdSpaceAbilities[ID_SPACE_ABILITY_COUNT];",
            "extern const struct IdSpaceItemRow gIdSpaceItems[ID_SPACE_ITEM_COUNT];",
            "extern const struct IdSpaceQolEffect gIdSpaceQolEffects[];",
            "extern const uint32_t gIdSpaceQolEffectCount;",
            "#endif",
            "",
        ]
    )
    return "\n".join(lines).encode("ascii")


def _classification_code(value: str) -> int:
    mapping = {
        "VEGA_CFRU_CANONICAL": 1,
        "VEGA_EXCLUSIVE": 2,
        "CFRU_APPEND": 3,
        "CFRU_RESERVED": 4,
        "CFRU_SENTINEL": 5,
        "QOL_APPEND": 6,
    }
    return mapping[value]


def _render_type_c(model: Mapping[str, Any]) -> bytes:
    lines = [
        '#include "ids_generated.h"',
        "const struct IdSpaceTypeRow gIdSpaceTypes[ID_SPACE_TYPE_COUNT] = {",
    ]
    for row in model["types"]:
        lines.append(
            "    { %du, %du, %du, %du, %du, %du, %du, 0u, 0x%08Xu, 0x%08Xu, 0x%08Xu },"
            % (
                row["id"],
                row["tera_input_code"],
                _classification_code(row["classification"]),
                row["icon_geometry"]["width"],
                row["icon_geometry"]["height"],
                row["icon_geometry"]["tile_offset"],
                row["display_color"]["bgr555"],
                _c_token(row["icon_key"]),
                _c_token(row["color_key"]),
                _c_token(row["special_rule"]),
            )
        )
    lines.append("};")
    lines.append("const uint16_t gIdSpaceTypeEffectiveness[ID_SPACE_TYPE_COUNT][ID_SPACE_TYPE_COUNT] = {")
    for row in model["types"]:
        lines.append("    { " + ", ".join(f"{value}u" for value in row["effectiveness"]) + " },")
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _render_ability_c(model: Mapping[str, Any]) -> bytes:
    lines = [
        '#include "ids_generated.h"',
        "const struct IdSpaceAbilityRow gIdSpaceAbilities[ID_SPACE_ABILITY_COUNT] = {",
    ]
    for row in model["abilities"]:
        rating = -1 if row["rating"] is None else row["rating"]
        lines.append(
            "    { %du, %d, %du, 0x%08Xu, %s },"
            % (
                row["id"],
                rating,
                _classification_code(row["classification"]),
                _c_token(row["effect_key"]),
                _ascii_c_string(row["ability_key"]),
            )
        )
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _render_item_c(model: Mapping[str, Any]) -> bytes:
    lines = [
        '#include "ids_generated.h"',
        "const struct IdSpaceItemRow gIdSpaceItems[ID_SPACE_ITEM_COUNT] = {",
    ]
    for row in model["items"]:
        item_flags = (
            (1 if row["item_type_explicit"] else 0)
            | (2 if row["is_evolution_stone"] else 0)
            | (4 if row["is_evolution_item"] else 0)
        )
        lines.append(
            "    { %du, %du, %du, %du, %du, %du, %du, %du, %du, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, 0x%08Xu, %s },"
            % (
                row["id"],
                row["price"],
                row["importance"],
                row["battle_usage"],
                row["item_type_id"],
                item_flags,
                _classification_code(row["classification"]),
                row["source_mystery"],
                row["secondary_id"],
                _c_token(row["description_key"]),
                _c_token(row["icon_key"]),
                _c_token(row["palette_key"]),
                _c_token(row["pocket"]),
                _c_token(row["source_use_type"]),
                _c_token(row["role"]),
                _c_token(row["hold_effect_key"]),
                _c_token(str(row["hold_effect_param"])),
                _c_token(row["field_effect_key"]),
                _c_token(str(row["field_effect_param"])),
                _c_token(row["field_use_callback_key"]),
                _c_token(row["battle_effect_key"]),
                _c_token(str(row["battle_effect_param"])),
                _c_token(row["battle_use_callback_key"]),
                _c_token(row["ball_kind"]),
                _c_token(row["consume_policy"]),
                _c_token(row["target_policy"]),
                _c_token(row["supply_key"]),
                _c_token(row["runtime_binding"]),
                _ascii_c_string(row["item_key"]),
            )
        )
    lines.extend(["};", ""])
    return "\n".join(lines).encode("ascii")


def _render_qol_c(model: Mapping[str, Any]) -> bytes:
    qol = _qol_effect_rows(model)
    lines = [
        '#include "ids_generated.h"',
        "const struct IdSpaceQolEffect gIdSpaceQolEffects[] = {",
    ]
    for row in qol:
        try:
            value = int(row["field_effect_param"], 0)
        except (TypeError, ValueError):
            value = 0
        lines.append(
            "    { %du, %du, 0x%08Xu, 0x%08Xu },"
            % (
                row["id"],
                value,
                _c_token(row["field_effect_key"]),
                _c_token(str(row["field_effect_param"])),
            )
        )
    lines.extend(
        [
            "};",
            "const uint32_t gIdSpaceQolEffectCount = (uint32_t)(sizeof(gIdSpaceQolEffects) / sizeof(gIdSpaceQolEffects[0]));",
            "",
        ]
    )
    return "\n".join(lines).encode("ascii")


def _public_model(model: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in model.items()
        if key not in {"manifests", "text_width"}
    }


def _render_report(model: Mapping[str, Any], artifact_records: Mapping[str, Mapping[str, Any]]) -> bytes:
    summary = model["summary"]
    lines = [
        "# T05 ID space report",
        "",
        f"- Fingerprint: `{model['fingerprint']}`",
        f"- Vega ROM: `{model['sources']['vega']['rom']['sha256']}`",
        f"- CFRU/DPE inventory: `{model['sources']['cfru_dpe']['inventory_sha256']}`",
        "- ROM stage: なし（T06でstage 04へ配置・repoint）",
        "",
        "## 統合結果",
        "",
        "| Domain | Canonical | Frozen | CFRU append | QOL append | Last ID |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Type | {summary['type_count']} | 18 | 7（予約・sentinel含む） | 0 | 24 |",
        f"| Ability | {summary['ability_count']} | {summary['frozen_ability_count']} | {summary['appended_ability_count']} | 0 | {summary['last_ability_id']} |",
        f"| Item | {summary['item_count']} | {summary['frozen_item_count']} | {summary['cfru_appended_item_count']} | {summary['qol_appended_item_count']} | {summary['last_item_id']} |",
        "",
        "- Vega Ability 0..77とItem slot 0..374は未使用行を含め全件凍結した。",
        "- CFRU `ABILITY_AIRLOCK` (source 76) はVega canonical 77へaliasし、Vega 76 `そうおん`を保持した。",
        "- Fairy 23とStellar 24は日本語表示、icon/color key、25×25相性を完全化し、Stellarの特殊ruleはT06でbindする。",
        "- 経験アメ5種と単能力EV reset用品6種を末尾988..998へ配置し、既存Vega IDを移動していない。",
        "- Oval Charmは上流の段階率を流用せず、QOL仕様の2倍・上限100% adapter契約を選択した。",
        "- field/hold/battle effect、callback、pocket、icon、palette、ball kind、supply keyを別fieldで保持した。",
        "- 生成Cは配置前semantic tableであり上流positional ABI表そのものではない。T06はItem/ItemIcon 999行とAbility名/説明312行をcanonical順で再生成し、全consumerをrepoint・全行照合する。",
        "",
        "## 文字幅",
        "",
        f"- 検査行数: {model['text_width']['summary']['row_count']}",
        f"- overflow: {model['text_width']['summary']['overflow_count']}",
        "- Type 5 bytes、Ability 16 bytes、Item 9 bytes、説明各行28 bytesを上限とした。",
        "",
        "## Acceptance",
        "",
        "- duplicate canonical ID/key: 0",
        "- unresolved CFRU ability symbol: 0 / 311",
        "- unresolved CFRU item symbol/alias: 0 / 827",
        "- Vega frozen behavior rows moved: 0",
        "- generated C compile probe: PASS",
        "- check side effects: なし",
        "",
        "## Artifacts",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for logical, record in sorted(artifact_records.items()):
        lines.append(f"| `{logical}` | {record['size']} | `{record['sha256']}` |")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def render_artifacts(model: Mapping[str, Any]) -> dict[str, bytes]:
    validate_id_space_model(model)
    artifacts: dict[str, bytes] = {
        "generated/engine/ids/id_spaces.json": _stable_json(_public_model(model)),
        "generated/engine/ids/ids_generated.h": _render_header(model),
        "generated/engine/ids/type_tables.c": _render_type_c(model),
        "generated/engine/ids/ability_tables.c": _render_ability_c(model),
        "generated/engine/ids/item_tables.c": _render_item_c(model),
        "generated/engine/ids/qol_item_effects.c": _render_qol_c(model),
        "generated/engine/ids/text_width.json": _stable_json(model["text_width"]),
        "manifests/ability_ids.csv": _render_csv(
            ABILITY_MANIFEST_HEADER, model["manifests"]["ability"]
        ),
        "manifests/item_ids.csv": _render_csv(ITEM_MANIFEST_HEADER, model["manifests"]["item"]),
        "manifests/type_ids.csv": _render_csv(TYPE_MANIFEST_HEADER, model["manifests"]["type"]),
    }
    layout = {
        logical: {
            "alignment": 4 if logical.endswith((".c", ".h")) else 1,
            "size": len(payload),
            "sha256": _sha256(payload),
            "allocation_task": "T06",
        }
        for logical, payload in sorted(artifacts.items())
        if logical.startswith("generated/engine/ids/")
    }
    artifacts["generated/engine/ids/layout.json"] = _stable_json(layout)
    records_without_metadata_report = {
        logical: {"size": len(payload), "sha256": _sha256(payload)}
        for logical, payload in sorted(artifacts.items())
    }
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_ID,
        "fingerprint": model["fingerprint"],
        "fingerprint_inputs": model["fingerprint_inputs"],
        "summary": model["summary"],
        "repeatability": {"render_count": 2, "identical": True},
        "compile_probe": {
            "language": "C11",
            "targets": ["host semantic link/run", "ARM7TDMI Thumb freestanding compile"],
            "result": "PASS",
        },
        "artifacts": records_without_metadata_report,
    }
    artifacts["generated/engine/ids/metadata.json"] = _stable_json(metadata)
    report_records = {
        logical: {"size": len(payload), "sha256": _sha256(payload)}
        for logical, payload in sorted(artifacts.items())
        if logical != str(REPORT_PATH)
    }
    artifacts[str(REPORT_PATH)] = _render_report(model, report_records)
    if set(artifacts) != set(ARTIFACT_PATHS):
        _fail(
            f"artifact set mismatch: missing={sorted(set(ARTIFACT_PATHS) - set(artifacts))} "
            f"extra={sorted(set(artifacts) - set(ARTIFACT_PATHS))}"
        )
    return artifacts


def _compile_probe(artifacts: Mapping[str, bytes], root: Path = ROOT) -> dict[str, Any]:
    toolchain = _read_json(root / "infra/toolchain_manifest.json", "toolchain manifest")
    tools = toolchain.get("tools")
    if not isinstance(tools, Mapping):
        _fail("toolchain manifest tools section is missing")

    def compiler_entry(name: str) -> tuple[Path, str]:
        entry = tools.get(name)
        if not isinstance(entry, Mapping):
            _fail(f"toolchain manifest is missing {name}")
        raw_path = entry.get("path")
        expected_sha = entry.get("sha256")
        if not isinstance(raw_path, str) or not isinstance(expected_sha, str):
            _fail(f"toolchain manifest {name} path/hash is invalid")
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            _fail(f"pinned compiler is missing/non-file: {path}")
        actual_sha = _sha256_file(path)
        if actual_sha != expected_sha:
            _fail(f"pinned compiler hash changed for {name}: {actual_sha}")
        return path, str(entry.get("version", ""))

    host_compiler, host_version = compiler_entry("host_cc")
    arm_compiler, arm_version = compiler_entry("arm_none_eabi_gcc")
    with tempfile.TemporaryDirectory(prefix="t05-id-space-compile-") as raw:
        directory = Path(raw)
        for logical, payload in artifacts.items():
            if logical.startswith("generated/engine/ids/") and logical.endswith((".c", ".h")):
                (directory / Path(logical).name).write_bytes(payload)
        probe = directory / "probe.c"
        probe.write_text(
            '#include "ids_generated.h"\n'
            '_Static_assert(ID_SPACE_TYPE_COUNT == 25u, "type count");\n'
            '_Static_assert(ID_SPACE_ABILITY_COUNT == 312u, "ability count");\n'
            '_Static_assert(ID_SPACE_ITEM_COUNT == 999u, "item count");\n'
            'int main(void) { return gIdSpaceTypeEffectiveness[23][16] == 2000u && '
            'gIdSpaceQolEffectCount == 45u ? 0 : 1; }\n',
            encoding="ascii",
        )
        alias_probe = directory / "alias_probe.c"
        alias_probe.write_text(
            '#include "constants/pokemon.h"\n'
            '#include "constants/abilities.h"\n'
            '#include "constants/items.h"\n'
            '#include "ids_generated.h"\n'
            '_Static_assert(TYPE_FAIRY == TYPE_KEY_FAIRY, "type alias");\n'
            '_Static_assert(ABILITY_AIRLOCK == ABILITY_KEY_AIRLOCK, "ability alias");\n'
            '_Static_assert(ITEM_DIRE_HIT == ITEM_KEY_DIRE_HIT, "item alias");\n'
            '_Static_assert(ITEM_TM02_DRAGON_CLAW == ITEM_KEY_TM02, "tm alias");\n'
            '_Static_assert(ITEMS_COUNT == ID_SPACE_ITEM_COUNT, "item bound");\n'
            '_Static_assert(ABILITIES_COUNT == ID_SPACE_ABILITY_COUNT, "ability bound");\n'
            'int alias_probe(void) { return 0; }\n',
            encoding="ascii",
        )
        tmhm_probe = directory / "tmhm_probe.c"
        tmhm_probe.write_text(
            '#include "constants/tmshms.h"\n'
            '#include "ids_generated.h"\n'
            '_Static_assert(ITEM_TM02_DRAGON_CLAW == ITEM_KEY_TM02, "tm alias");\n'
            '_Static_assert(ITEM_HM05_FLASH == ITEM_KEY_HM05_DIVE, "hm alias");\n'
            'int tmhm_probe(void) { return 0; }\n',
            encoding="ascii",
        )
        binary = directory / "probe"
        sources = [directory / name for name in ("type_tables.c", "ability_tables.c", "item_tables.c", "qol_item_effects.c")]
        for source in sources:
            command = [
                str(arm_compiler),
                "-std=c11",
                "-ffreestanding",
                "-mcpu=arm7tdmi",
                "-mthumb",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-c",
                str(source),
                "-I",
                str(directory),
                "-o",
                str(directory / f"{source.stem}.o"),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode:
                _fail("generated ARM C compile failed:\n" + completed.stdout + completed.stderr)
        alias_object = directory / "alias_probe.o"
        alias_command = [
            str(host_compiler),
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-c",
            str(alias_probe),
            "-I",
            str(root / "vendor/upstream/CFRU-JP/include"),
            "-I",
            str(directory),
            "-o",
            str(alias_object),
        ]
        alias_completed = subprocess.run(
            alias_command, capture_output=True, text=True, check=False
        )
        if alias_completed.returncode:
            _fail(
                "generated alias integration compile failed:\n"
                + alias_completed.stdout
                + alias_completed.stderr
            )
        tmhm_object = directory / "tmhm_probe.o"
        tmhm_command = [
            str(host_compiler),
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-c",
            str(tmhm_probe),
            "-I",
            str(root / "vendor/upstream/CFRU-JP/include"),
            "-I",
            str(directory),
            "-o",
            str(tmhm_object),
        ]
        tmhm_completed = subprocess.run(
            tmhm_command, capture_output=True, text=True, check=False
        )
        if tmhm_completed.returncode:
            _fail(
                "generated TM/HM alias integration compile failed:\n"
                + tmhm_completed.stdout
                + tmhm_completed.stderr
            )
        command = [
            str(host_compiler),
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            *map(str, sources),
            str(probe),
            "-I",
            str(directory),
            "-o",
            str(binary),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            _fail("generated C compile failed:\n" + completed.stdout + completed.stderr)
        run = subprocess.run([str(binary)], capture_output=True, text=True, check=False)
        if run.returncode:
            _fail(f"generated C semantic probe failed with {run.returncode}")
    return {
        "host_compiler": {"path": str(host_compiler), "version": host_version},
        "arm_compiler": {"path": str(arm_compiler), "version": arm_version},
        "host_flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"],
        "arm_flags": [
            "-std=c11",
            "-ffreestanding",
            "-mcpu=arm7tdmi",
            "-mthumb",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-c",
        ],
        "result": "PASS",
    }


def _atomic_publish(root: Path, artifacts: Mapping[str, bytes]) -> None:
    targets = {logical: root / logical for logical in artifacts}
    for target in targets.values():
        target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".t05-id-space-publish-", dir=root / "build") as raw:
        temp_root = Path(raw)
        for logical, payload in artifacts.items():
            temporary = temp_root / logical
            temporary.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_bytes(payload)
        for logical, target in targets.items():
            os.replace(temp_root / logical, target)


def build(root: Path) -> dict[str, Any]:
    config = _read_json(root / CONFIG_PATH, "T05 config")
    first_model = build_id_space_model(root, config)
    second_model = build_id_space_model(root, config)
    if _stable_json(first_model) != _stable_json(second_model):
        _fail("consecutive ID space models are not deterministic")
    first = render_artifacts(first_model)
    second = render_artifacts(second_model)
    if first != second:
        _fail("consecutive ID space renders are not deterministic")
    compile_result = _compile_probe(first, root)
    _atomic_publish(root, first)
    return {
        "command": "build",
        "fingerprint": first_model["fingerprint"],
        "summary": first_model["summary"],
        "artifact_count": len(first),
        "compile_probe": compile_result,
    }


def check(root: Path) -> dict[str, Any]:
    config = _read_json(root / CONFIG_PATH, "T05 config")
    model = build_id_space_model(root, config)
    expected = render_artifacts(model)
    compile_result = _compile_probe(expected, root)
    for logical, payload in expected.items():
        path = root / logical
        if path.is_symlink() or not path.is_file():
            _fail(f"published artifact is missing/non-regular: {logical}")
        actual = path.read_bytes()
        if actual != payload:
            _fail(
                f"published artifact is stale: {logical} "
                f"expected {_sha256(payload)}, got {_sha256(actual)}"
            )
    return {
        "command": "check",
        "fingerprint": model["fingerprint"],
        "summary": model["summary"],
        "artifact_count": len(expected),
        "compile_probe": compile_result,
        "side_effects": "NONE",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build(args.root) if args.command == "build" else check(args.root)
    except (IdSpaceBuildError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
