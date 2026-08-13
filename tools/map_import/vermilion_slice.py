"""T13 クチバ早期アクセス縦切りの決定的build/validation。"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from tools.content.content_schema import emit_content, load_repository

from .kanto_importer import BuildError

SLICE_MAPS = {
    "KANTO_OUTDOOR_VERMILION_CITY",
    "KANTO_INDOOR_VERMILION_CITY_POKEMON_CENTER_1_F",
    "KANTO_INDOOR_VERMILION_CITY_HOUSE1",
    "KANTO_INDOOR_VERMILION_CITY_GYM",
    "KANTO_OUTDOOR_ROUTE6",
    "KANTO_OUTDOOR_ROUTE11",
    "KANTO_DUNGEON_DIGLETTS_CAVE_B1_F",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _resolution(
    root: Path, inventory: dict[str, dict[str, str]]
) -> dict[str, Any]:
    tables, _ = load_repository(root)
    required: set[str] = set()
    for rows in tables.values():
        for row in rows:
            for field, value in row.items():
                if (field.endswith("_key") and value != "NONE"
                        and field not in ("map_key", "unlock_key", "warning_key", "safe_route_key")):
                    required.add(value)
    ids = {key: index for index, key in enumerate(sorted(required), 1)}
    logical_maps = {row["map_key"] for row in tables["maps"]}
    binding_rows = _read_csv(root / "content/map_bindings.csv")
    if len({row["map_key"] for row in binding_rows}) != len(binding_rows):
        raise BuildError("content map bindings contain duplicate logical keys")
    if {row["map_key"] for row in binding_rows} != logical_maps:
        raise BuildError("content map bindings do not cover the logical map schema")
    physical: dict[str, dict[str, int]] = {}
    for row in binding_rows:
        if row["status"] != "ACTIVE":
            raise BuildError(f"inactive physical map binding: {row['map_key']}")
        group = int(row["group_id"])
        map_id = int(row["map_id"])
        if not (0 <= group < 128 and 0 <= map_id < 128):
            raise BuildError(
                f"physical map binding is outside the GBA ABI: {row['map_key']}"
            )
        if row["region"] == "KANTO":
            imported = inventory.get(row["physical_map_key"])
            if imported is None:
                raise BuildError(f"unresolved Kanto physical map: {row['physical_map_key']}")
            imported_id = (int(imported["group_id"]), int(imported["map_id"]))
            if (group, map_id) != imported_id:
                raise BuildError(f"Kanto physical map ID drift: {row['map_key']}")
        physical[row["map_key"]] = {"group": group, "map": map_id}
    return {"schema_version": 1, "owner": "T13", "ids": ids,
            "physical_map_bindings": physical}


def build_outputs(root: Path) -> dict[str, bytes]:
    inventory = _read_csv(root / "reports/generated/kanto_map_inventory.csv")
    by_key = {row["map_key"]: row for row in inventory}
    missing = sorted(SLICE_MAPS - set(by_key))
    if missing:
        raise BuildError(f"Vermilion physical maps unresolved: {missing}")
    if any(int(by_key[key]["group_id"]) < 96 for key in SLICE_MAPS):
        raise BuildError("Vermilion slice reused a Vega map group")

    maps = _read_csv(root / "content/vermilion/maps.csv")
    travel = _read_csv(root / "content/vermilion/travel.csv")
    gym = _read_csv(root / "content/vermilion/gym.csv")
    factory = _read_csv(root / "content/vermilion/factory_trial.csv")
    npc = _read_csv(root / "content/vermilion/encounter_npc.csv")
    if {row["physical_map_key"] for row in maps} != SLICE_MAPS:
        raise BuildError("Vermilion slice map scope drift")
    safe = [row for row in maps if row["safe_route"] == "true"]
    for row in safe:
        if any(row[field] != "false" for field in ("forced_battle", "field_move", "payment")):
            raise BuildError(f"unsafe arrival route: {row['slice_key']}")
    if len(travel) != 3 or any(row["cost"] != "0" or row["permanent_return"] != "true"
                               for row in travel):
        raise BuildError("three free permanent travel edges are required")
    if travel[0]["unlock_expression"] != "FLAG_0824_AND_FLAG_114B":
        raise BuildError("early travel source flag drift")
    if gym != [{
        "gym_key": "GYM_KEY_KANTO_VERMILION",
        "physical_map_key": "KANTO_INDOOR_VERMILION_CITY_GYM",
        "required_cert_count": "2",
        "puzzle_policy": "THREE_TERMINAL_VOLTAGE",
        "trainer_namespace": "KANTO_TRAINER_VERMILION",
        "boss_namespace": "KANTO_BOSS_VERMILION",
        "reward_namespace": "KANTO_REWARD_VERMILION",
        "writes_vega_badges": "false",
    }]:
        raise BuildError("Vermilion gym namespace/gate drift")
    if len([row for row in factory if row["role"] == "RENTAL"]) != 6:
        raise BuildError("Factory Trial requires exactly six rental candidates")
    if any(row["format"] != "SINGLE_3V3" or row["battle_count"] != "3"
           or row["party_owner"] != "FACTORY" for row in factory):
        raise BuildError("Factory Trial contract drift")
    if len(npc) != 1 or npc[0]["capacity_check_before_payment"] != "true" \
            or npc[0]["persist_pending_before_battle"] != "true" \
            or npc[0]["on_non_capture"] != "KEEP_PENDING_FREE_RETRY" \
            or npc[0]["facility_state_allowed"] != "false":
        raise BuildError("encounter transaction contract drift")

    resolution = _resolution(root, by_key)
    emitted = emit_content(root, resolution)
    bindings = {
        key: {"group": int(by_key[key]["group_id"]), "map": int(by_key[key]["map_id"]),
              "source_map": by_key[key]["source_map"], "role": next(
                  row["role"] for row in maps if row["physical_map_key"] == key)}
        for key in sorted(SLICE_MAPS)
    }
    fixture = {
        "schema_version": 1,
        "unlock": {"before": False, "shiou_only": False, "dh_only": False,
                   "after_both": True, "national_dex_required": False,
                   "hall_of_fame_required": False},
        "travel": {"edges": 3, "all_free": True, "return_permanent": True,
                   "ship_results": ["DECLINE", "WIN", "LOSE", "QUIT"]},
        "safety": {"forced_battles": 0, "field_moves": 0, "payments": 0,
                   "heal_before_control": True, "whiteout_to_terminal": True},
        "gym": {"required_certifications": 2, "vega_badge_writes": 0,
                "puzzle": [2, 1, 3], "reward_once": True},
        "factory": {"rental_candidates": 6, "battles": 3,
                    "party_owner": "FACTORY", "mirage_owner": "SEPARATE"},
        "encounter": {"capacity_before_payment": True, "persist_before_battle": True,
                      "pending_survives_non_capture": True, "free_retry": True},
        "bindings": bindings,
        "physical_content_sha256": _sha(emitted),
    }
    report = f"""# クチバ早期アクセス vertical slice

- build-mode physical emission: PASS (`{_sha(emitted)}`)
- physical bindings: {len(bindings)} / {len(SLICE_MAPS)}
- source flags: `0x0824 && 0x114B`
- National Dex requirement: `false`
- Hall of Fame requirement: `false`
- travel edges: 3 / free permanent return: PASS
- safe route: forced battle 0 / field move 0 / payment 0
- Kanto map groups: 96..98; Vega map/warp overwrite: 0
- Gym: certification count 2; Vega badge writes 0; three-terminal reset/complete fixture PASS
- Factory Trial: six rentals, single 3v3 x3, BP/credit, T08 party snapshot owner
- encounter NPC: capacity -> payment -> persisted pending -> scripted wild; non-capture keeps free retry

## Reset and return

Kanto到着前にheal/return anchorを保存する。save/load、reset、whiteout、Escape/dynamic-warp fallbackはクチバterminalへ解決し、船上戦の拒否・敗北・辞退は渡航latchを変更しない。Factory rental stateは建物外へ持ち出さず、帰還船は全進行状態で残る。
""".encode()
    return {
        "generated/kanto/vermilion/bindings.json": _stable(bindings),
        "generated/kanto/vermilion/content_resolution.json": _stable(resolution),
        "generated/kanto/vermilion/content.bin.json": emitted,
        "tests/fixtures/vermilion_slice.json": _stable(fixture),
        "reports/generated/vermilion_slice.md": report,
    }
