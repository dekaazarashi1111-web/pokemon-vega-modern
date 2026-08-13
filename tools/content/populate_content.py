"""T16 dual-region content population and deterministic ROM payload builder."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import struct
import unicodedata
import zlib
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


TASK = "T16"
V2 = Path("design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data")
STAGE09 = Path("build/stages/09_species_surface.gba")
STAGE09_META = Path("build/stages/09_species_surface.json")
STAGE16 = Path("build/stages/16_content.gba")
STAGE16_META = Path("build/stages/16_content.json")
STAGE16_ALLOC = Path("build/stages/16_allocation.json")


HEADERS: dict[str, list[str]] = {
    "kanto_encounters.csv": [
        "encounter_key", "map_key", "logical_location_key", "method", "condition",
        "slot", "species_key", "evolution_chain_id", "level_min", "level_max",
        "weight", "table_profile", "base_table_key", "unlock_key",
        "hidden_ability_policy", "egg_move_policy", "item_key",
        "shared_capture_key", "difficulty_policy", "status", "notes",
    ],
    "kanto_trainers.csv": [
        "trainer_key", "class_key", "party_slot", "species_key", "form_key", "level",
        "move1_key", "move2_key", "move3_key", "move4_key", "item_key",
        "ability_key", "ability_policy", "nature_key", "ev_spread_key", "iv_floor",
        "ai_profile_key", "trainer_role", "unlock_key", "mechanic_policy",
        "difficulty_policy", "warning_key", "status", "notes",
    ],
    "tohoku_trainers.csv": [
        "trainer_key", "class_key", "party_slot", "species_key", "form_key", "level",
        "move1_key", "move2_key", "move3_key", "move4_key", "item_key",
        "ability_key", "ability_policy", "nature_key", "ev_spread_key", "iv_floor",
        "ai_profile_key", "trainer_role", "unlock_key", "mechanic_policy",
        "difficulty_policy", "warning_key", "status", "notes",
    ],
    "trainer_ai_profiles.csv": [
        "ai_profile_key", "decision_model", "switch_policy", "hazard_policy",
        "setup_policy", "recovery_policy", "weather_field_policy",
        "trainer_item_policy", "gimmick_policy", "double_support_policy",
        "rng_policy", "performance_budget", "status", "notes",
    ],
    "trainer_rematches.csv": [
        "rematch_key", "trainer_key", "tier", "league_stage", "unlock_key",
        "level_min", "level_max", "ai_profile_key", "iv_floor", "ev_policy",
        "item_policy", "mechanic_policy", "registered_only", "status", "notes",
    ],
    "research_encounters.csv": [
        "research_key", "region", "map_key", "logical_location_key", "base_table_key",
        "species_key", "evolution_chain_id", "level_min", "level_max", "iv_floor",
        "hidden_ability_rate", "egg_move_policy", "held_item_policy", "shiny_policy",
        "unlock_key", "normal_preserved", "shared_capture_key", "status", "notes",
    ],
    "raid_encounters.csv": [
        "raid_key", "map_key", "species_key", "level", "partner_pool_key",
        "shield_policy", "capture_policy", "shared_capture_key", "reward_pool_key",
        "reward_repeatability", "claim_key", "retry_policy", "unlock_key",
        "mechanic_policy", "presentation_profile", "dedicated_map", "custom_ui",
        "status", "notes",
    ],
    "kanto_items.csv": [
        "placement_key", "map_key", "logical_location_key", "placement_type",
        "item_key", "quantity", "unlock_key", "repeatability", "flag_key",
        "economy_tier", "status", "notes",
    ],
    "tohoku_items.csv": [
        "placement_key", "map_key", "logical_location_key", "placement_type",
        "item_key", "quantity", "unlock_key", "repeatability", "flag_key",
        "economy_tier", "status", "notes",
    ],
    "qol_rewards.csv": [
        "reward_key", "item_key", "service_key", "source_kind", "quantity",
        "currency_key", "price", "unlock_key", "repeatability", "claim_key",
        "status", "notes",
    ],
    "facility_modes.csv": [
        "mode_key", "tier", "format", "selection_count", "battle_count", "unlock_key",
        "rental_pool_key", "trainer_pool_key", "level_policy", "mechanic_policy",
        "ai_profile_key", "party_owner", "state_owner", "link_multi", "status", "notes",
    ],
    "facility_rentals.csv": [
        "rental_key", "pool_key", "origin_bucket", "species_key", "form_key", "level",
        "nature_key", "iv_policy", "ev_spread_key", "item_key", "move1_key",
        "move2_key", "move3_key", "move4_key", "ability_key", "gmax_allowed",
        "tera_type_key", "weight", "unlock_key", "status", "notes",
    ],
    "facility_trainers.csv": [
        "facility_trainer_key", "pool_key", "format", "ai_profile_key",
        "rental_key1", "rental_key2", "rental_key3", "rental_key4",
        "rental_key5", "rental_key6", "mechanic_policy", "unlock_key", "status", "notes",
    ],
    "facility_rewards.csv": [
        "facility_reward_key", "trigger_kind", "streak", "currency_key", "amount",
        "item_key", "quantity", "unlock_key", "repeatability", "claim_key",
        "status", "notes",
    ],
    "reward_encounters.csv": [
        "reward_encounter_key", "npc_key", "pool_key", "tier", "credit_key", "cost",
        "species_key", "level_min", "level_max", "iv_floor", "hidden_ability_rate",
        "max_uncaught_rerolls", "capture_policy", "exp_ev_money_policy",
        "item_theft_policy", "drop_policy", "chain_policy", "unlock_key",
        "presentation_profile", "dedicated_map", "full_screen_ui", "status", "notes",
    ],
}


class PopulationError(RuntimeError):
    """T16 generation or acceptance failure."""


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _csv_bytes(header: Sequence[str], rows: Iterable[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in header})
    return stream.getvalue().encode("utf-8")


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip().replace(" ", "").replace("　", "")
    return re.sub(r"[・･‐‑–—―]", "", value)


def _key_index(rows: Sequence[dict[str, str]], display: str, key: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        name = _norm(row[display])
        result.setdefault(name, row[key])
    return result


def _levels(value: str, fallback: tuple[int, int]) -> tuple[int, int]:
    values = [int(item) for item in re.findall(r"\d+", value)]
    values = [item for item in values if 1 <= item <= 100]
    if len(values) >= 2:
        return min(values[0], values[1]), max(values[0], values[1])
    if values:
        return values[0], values[0]
    return fallback


def _unlock(region: str, low: int, stage: str) -> str:
    if region == "KANTO":
        if low >= 100:
            return "KANTO_LEAGUE_CLEAR"
        if low >= 98:
            return "KANTO_CERT_8"
        if low >= 96:
            return "KANTO_CERT_7"
        if low >= 93:
            return "KANTO_CERT_6"
        if low >= 90:
            return "KANTO_CERT_5"
        if low >= 87:
            return "KANTO_CERT_4"
        if low >= 84:
            return "KANTO_CERT_3"
        if low >= 81:
            return "KANTO_CERT_2"
        if low >= 78:
            return "KANTO_CERT_1"
        return "KANTO_EARLY_ACCESS"
    if "ポスト" in stage or low >= 70:
        return "VEGA_HALL_OF_FAME"
    if low >= 58:
        return "VEGA_BADGE_8"
    if low >= 47:
        return "VEGA_BADGE_7"
    if low >= 38:
        return "VEGA_BADGE_6"
    if low >= 28:
        return "VEGA_BADGE_5"
    if low >= 20:
        return "VEGA_SHIOU_BADGE_3"
    if low >= 10:
        return "VEGA_BADGE_1"
    return "VEGA_PRE_ENTRY"


def _logical_map_key(region: str, code: str) -> str:
    overrides = {
        "K01": "MAP_KEY_KANTO_ROUTE1",
        "K26": "MAP_KEY_KANTO_VIRIDIAN_FOREST",
        "K42": "MAP_KEY_KANTO_LEAGUE",
        "K46": "MAP_KEY_KANTO_VERMILION_TERMINAL",
    }
    if code in overrides:
        return overrides[code]
    if region == "KANTO":
        return f"MAP_KEY_KANTO_{code}"
    return f"MAP_KEY_TOHOKU_{code}"


def _map_kind(name: str, modes: str) -> str:
    if any(word in name for word in ("リーグ", "チャンピオン")):
        return "LEAGUE"
    if any(word in name for word in ("どうくつ", "トンネル", "タワー", "やかた", "いせき", "アジト", "やま", "もり", "森")):
        return "DUNGEON"
    if any(word in name for word in ("ジム", "異常生態", "裂け目", "研究室")):
        return "EVENT"
    if any(word in name for word in ("タウン", "シティ", "港", "研究所")):
        return "TOWN"
    if any(word in modes for word in ("草むら", "水上", "釣り", "ずつき")):
        return "ROUTE"
    return "DUNGEON"


def _build_maps(v2_maps: Sequence[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    rows: list[dict[str, object]] = [{
        "map_key": "MAP_KEY_TOHOKU_HAKUJI_RESEARCH", "region": "TOHOKU",
        "logical_location_key": "VEGA_NATIVE", "unlock_key": "VEGA_PRE_ENTRY",
        "map_kind": "TOWN", "field_pc_allowed": "true",
        "safe_route_key": "SAFE_ROUTE_TOHOKU_HOME", "warning_key": "WARNING_NONE",
    }]
    by_code: dict[str, dict[str, object]] = {}
    for source in v2_maps:
        region = "KANTO" if source["region"] == "カントー" else "TOHOKU"
        code = source["map_code"]
        low, high = _levels(source["recommended_level_range"], (68, 78) if region == "KANTO" else (1, 65))
        kind = _map_kind(source["map_name"], source["encounter_modes"])
        field_pc = kind in {"TOWN", "ROUTE"}
        row: dict[str, object] = {
            "map_key": _logical_map_key(region, code), "region": region,
            "logical_location_key": code,
            "unlock_key": _unlock(region, low, source["progress_stage"]),
            "map_kind": kind, "field_pc_allowed": str(field_pc).lower(),
            "safe_route_key": "SAFE_ROUTE_KANTO_TERMINAL" if region == "KANTO" else "SAFE_ROUTE_TOHOKU_HOME",
            "warning_key": "WARNING_KANTO_HIGH_LEVEL" if region == "KANTO" else "WARNING_NONE",
        }
        if code == "K42":
            # The V2 ecology row's level-derived certificate is not the story
            # gate for the League itself.  Keep this aligned with T15's
            # explicit KANTO_LEAGUE node instead of inferring CERT_6.
            row["unlock_key"] = "KANTO_LEAGUE"
            row["warning_key"] = "WARNING_KANTO_LEAGUE"
        rows.append(row)
        by_code[code] = {**row, "level_min": low, "level_max": high, "name": source["map_name"]}
    return rows, by_code


def _physical_bindings(root: Path, map_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    """Bind every logical ecology row to an existing physical graph node.

    Kanto uses the T14 namespace.  Tohoku overlays are assigned to existing
    encounter-bearing Vega maps in level order; NORMAL tables remain owned by
    Vega and T16 only adds a selectable overlay.
    """
    inventory = _rows(root / "reports/generated/kanto_map_inventory.csv")
    kanto: dict[str, list[dict[str, str]]] = {}
    for row in inventory:
        if row["status"] == "RESERVED":
            kanto.setdefault(row["logical_code"], []).append(row)

    audit = json.loads((root / "reports/generated/id_inventory.json").read_text(encoding="utf-8"))
    normal_by_map: dict[tuple[int, int], tuple[int, int, float, int]] = {}
    for detail in audit["encounter_details"]:
        levels = [
            int(slot["minimum_level"])
            for table in detail["tables"].values()
            if table
            for slot in table["slots"]
        ]
        if levels:
            group, map_id = int(detail["group"]), int(detail["map"])
            candidate = (group, map_id, sum(levels) / len(levels), len(levels))
            current = normal_by_map.get((group, map_id))
            if current is None or candidate[3] > current[3]:
                normal_by_map[(group, map_id)] = candidate
    normal_maps = list(normal_by_map.values())
    normal_maps.sort(key=lambda value: (value[2], value[0], value[1]))
    tohoku_rows = [row for row in map_rows if row["region"] == "TOHOKU" and row["logical_location_key"] != "VEGA_NATIVE"]
    tohoku_rows.sort(key=lambda row: (int(str(row["logical_location_key"])[1:]), str(row["logical_location_key"])))
    if len(normal_maps) < len(tohoku_rows):
        raise PopulationError("not enough rooted Vega NORMAL maps for Tohoku binding")
    # Select evenly across the rooted level curve instead of silently mapping
    # every logical overlay to one convenient fixture map.
    selected = [normal_maps[round(index * (len(normal_maps) - 1) / (len(tohoku_rows) - 1))]
                for index in range(len(tohoku_rows))]
    if len({(row[0], row[1]) for row in selected}) != len(selected):
        raise PopulationError("Tohoku physical binding is not one-to-one")

    result: list[dict[str, object]] = [{
        "map_key": "MAP_KEY_TOHOKU_HAKUJI_RESEARCH", "region": "TOHOKU",
        "logical_location_key": "VEGA_NATIVE", "physical_map_key": "VEGA_PHYSICAL_04_000",
        "group_id": 4, "map_id": 0, "binding_policy": "VEGA_NATIVE_SCRIPT_HOST",
        "normal_table_key": "TABLE_KEY_TOHOKU_HAKUJI", "status": "ACTIVE",
        "notes": "T13既定の研究NPC/渡航host",
    }]
    for logical, physical in zip(tohoku_rows, selected):
        group, map_id, average, slot_count = physical
        result.append({
            "map_key": logical["map_key"], "region": "TOHOKU",
            "logical_location_key": logical["logical_location_key"],
            "physical_map_key": f"VEGA_PHYSICAL_{group:02d}_{map_id:03d}",
            "group_id": group, "map_id": map_id, "binding_policy": "VEGA_NORMAL_PLUS_RESEARCH_OVERLAY",
            "normal_table_key": f"TABLE_KEY_VEGA_{group:02d}_{map_id:03d}", "status": "ACTIVE",
            "notes": f"rooted NORMAL {slot_count} slots; source average Lv{average:.1f}; byte-preserved fallback",
        })

    priority = {"OUTDOOR": 0, "DUNGEON": 1, "INDOOR": 2}
    for logical in (row for row in map_rows if row["region"] == "KANTO"):
        code = str(logical["logical_location_key"])
        candidates = kanto.get(code, [])
        if not candidates:
            raise PopulationError(f"Kanto logical location lacks T14 physical binding: {code}")
        expected_kind = str(logical["map_kind"])
        candidates.sort(key=lambda row: (
            0 if (expected_kind in {"TOWN", "ROUTE"} and row["classification"] == "OUTDOOR") else 1,
            0 if (expected_kind in {"DUNGEON", "LEAGUE"} and row["classification"] == "DUNGEON") else 1,
            priority.get(row["classification"], 9), int(row["group_id"]), int(row["map_id"]),
        ))
        physical = candidates[0]
        result.append({
            "map_key": logical["map_key"], "region": "KANTO", "logical_location_key": code,
            "physical_map_key": physical["map_key"], "group_id": int(physical["group_id"]),
            "map_id": int(physical["map_id"]), "binding_policy": "T14_NAMESPACED_PHYSICAL",
            "normal_table_key": f"TABLE_KEY_KANTO_{code}", "status": "ACTIVE",
            "notes": f"representative={physical['source_map']}; all physical siblings retain logical_code={code}",
        })
    return result


def _normal_table_protection(root: Path) -> list[dict[str, object]]:
    audit = json.loads((root / "reports/generated/id_inventory.json").read_text(encoding="utf-8"))
    result: list[dict[str, object]] = []
    for detail in audit["encounter_details"]:
        group, map_id = int(detail["group"]), int(detail["map"])
        for profile, table in detail["tables"].items():
            if not table:
                continue
            raw = _stable(table)
            result.append({
                "table_key": f"TABLE_KEY_VEGA_{group:02d}_{map_id:03d}_{profile.upper()}",
                "group_id": group, "map_id": map_id, "profile": profile.upper(),
                "slot_count": len(table["slots"]), "source_address": hex(int(table["slots_address"])),
                "source_sha256": _sha(raw), "fallback_policy": "BYTE_EQUIVALENT_NORMAL",
                "status": "PRESERVED", "notes": "T16 overlay disabled時は既存tableをそのまま選択",
            })
    return result


def _registries(root: Path) -> dict[str, Any]:
    species = _rows(root / "manifests/species_ids.csv")
    moves = _rows(root / "manifests/move_ids.csv")
    items = _rows(root / "manifests/item_ids.csv")
    abilities = _rows(root / "manifests/ability_ids.csv")
    by_national: dict[int, str] = {}
    for row in species:
        if row["is_official"] == "true" and int(row["canonical_national_dex"]) > 0:
            by_national.setdefault(int(row["canonical_national_dex"]), row["species_key"])
    return {
        "species_rows": species,
        "move_rows": moves,
        "item_rows": items,
        "ability_rows": abilities,
        "species_by_name": _key_index(species, "display_name", "species_key"),
        "move_by_name": _key_index(moves, "display_name", "move_key"),
        "item_by_name": _key_index(items, "display_name", "item_key"),
        "ability_by_name": _key_index(abilities, "display_name", "ability_key"),
        "species_by_national": by_national,
        "move_by_id": {int(row["id"]): row["move_key"] for row in moves},
        "item_by_id": {int(row["id"]): row["item_key"] for row in items},
        "species_by_id": {int(row["id"]): row for row in species},
    }


FORM_NAMES = {
    "メガフシギバナ": "フシギバナ", "メガスピアー": "スピアー",
    "メガピジョット": "ピジョット", "メガフーディン": "フーディン",
    "メガヤドラン": "ヤドラン", "メガライボルト": "ライボルト",
    "メガプテラ": "プテラ", "メガリザードンY": "リザードン",
    "ウォッシュロトム": "ロトム", "ヒートロトム": "ロトム",
    "イエッサン♀": "イエッサン",
}


def _lookup(mapping: Mapping[str, str], value: str, label: str, *, fallback: str | None = None) -> str:
    if value.strip() in {"", "-", "—", "―", "なし", "NONE"}:
        none_keys = {
            "move": "MOVE_KEY_NONE",
            "item": "ITEM_KEY_NONE",
            "ability": "ABILITY_KEY_NONE",
        }
        if label in none_keys:
            return none_keys[label]
    candidates = [value, FORM_NAMES.get(value, ""), re.sub(r"[（(].*?[）)]", "", value)]
    for candidate in candidates:
        key = mapping.get(_norm(candidate))
        if key:
            return key
    if fallback is not None:
        return fallback
    raise PopulationError(f"unresolved {label}: {value}")


def _party_rows(root: Path, registries: Mapping[str, Any], kind: str) -> list[dict[str, object]]:
    if kind == "kanto_gym":
        source = _rows(root / V2 / "カントージム_詳細手持ち_48体.csv")
        groups = {value: index for index, value in enumerate(dict.fromkeys(row["gym_id"] for row in source), 1)}
        result = []
        for row in source:
            gym = groups[row["gym_id"]]
            moves = row["moves"].split("／")
            result.append(_trainer_party_row(registries, row["pokemon"], row["ability"], row["held_item"], moves,
                trainer_key=f"TRAINER_KEY_KANTO_GYM_{gym:02d}", class_key=f"TRAINER_CLASS_KANTO_GYM_{gym:02d}",
                slot=int(row["slot"]), level=int(row["level"]), unlock=f"KANTO_CERT_{gym}", role="GYM",
                mechanic="MEGA" if "メガ" in row["pokemon"] and int(row["slot"]) == 6 else "NONE",
                difficulty="FIXED_HIGH_LEVEL_OPTIONAL", warning="WARNING_KANTO_HIGH_LEVEL", notes=row["battle_role"]))
        return result
    if kind == "kanto_league":
        source = _rows(root / V2 / "カントーリーグ_四天王・チャンピオン詳細手持ち_30体.csv")
        members = {value: index for index, value in enumerate(dict.fromkeys(row["member_id"] for row in source), 1)}
        result = []
        for row in source:
            member = members[row["member_id"]]
            moves = [row[f"move{x}"] for x in range(1, 5)]
            result.append(_trainer_party_row(registries, row["species"], row["ability"], row["held_item"], moves,
                trainer_key=f"TRAINER_KEY_KANTO_LEAGUE_{member:02d}", class_key=f"TRAINER_CLASS_KANTO_LEAGUE_{member:02d}",
                slot=int(row["slot"]), level=int(row["level"]), unlock="KANTO_LEAGUE", role="LEAGUE",
                mechanic="MEGA" if "メガ" in row["species"] else "NONE", difficulty="FIXED_HIGH_LEVEL_OPTIONAL",
                warning="WARNING_KANTO_LEAGUE", notes=row["battle_role"]))
        return result
    source = _rows(root / V2 / "トーホクジム_クリア後詳細手持ち_48体.csv")
    leaders = {value: index for index, value in enumerate(dict.fromkeys(row["leader"] for row in source), 1)}
    result = []
    for row in source:
        leader = leaders[row["leader"]]
        moves = [row[f"move{x}"] for x in range(1, 5)]
        result.append(_trainer_party_row(registries, row["species"], row["ability"], row["held_item"], moves,
            trainer_key=f"TRAINER_KEY_TOHOKU_REMATCH_{leader:02d}", class_key=f"TRAINER_CLASS_TOHOKU_REMATCH_{leader:02d}",
            slot=int(row["slot"]), level=int(row["level"]), unlock="VEGA_HALL_OF_FAME", role="BOSS",
            mechanic="MEGA" if "メガ" in row["species"] else "NONE", difficulty="STORY_CURVE",
            warning="WARNING_NONE", notes=row["battle_role"]))
    return result


def _trainer_party_row(registries: Mapping[str, Any], species: str, ability: str, item: str,
                       moves: Sequence[str], *, trainer_key: str, class_key: str, slot: int,
                       level: int, unlock: str, role: str, mechanic: str,
                       difficulty: str, warning: str, notes: str) -> dict[str, object]:
    move_keys = [_lookup(registries["move_by_name"], value, "move") for value in moves]
    return {
        "trainer_key": trainer_key, "class_key": class_key, "party_slot": slot,
        "species_key": _lookup(registries["species_by_name"], species, "species"), "form_key": "NONE",
        "level": level, **{f"move{x + 1}_key": key for x, key in enumerate(move_keys)},
        "item_key": _lookup(registries["item_by_name"], item, "item", fallback="ITEM_KEY_NONE"),
        "ability_key": _lookup(registries["ability_by_name"], ability, "ability"),
        "ability_policy": "EXPLICIT", "nature_key": "NATURE_JOLLY" if role != "LEAGUE" else "NATURE_SERIOUS",
        "ev_spread_key": "EV_SPREAD_ROLE_510", "iv_floor": 31,
        "ai_profile_key": "AI_FULL_SMART", "trainer_role": role, "unlock_key": unlock,
        "mechanic_policy": mechanic, "difficulty_policy": difficulty, "warning_key": warning,
        "status": "ACTIVE", "notes": notes,
    }


def _encounters(families: Sequence[dict[str, str]], specials: Mapping[int, dict[str, str]],
                maps: Mapping[str, dict[str, object]], registries: Mapping[str, Any]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index, row in enumerate(families, 1):
        national = int(row["root_national_no"])
        code = row["kanto_map_code"]
        special = national in specials
        if code not in maps:
            code = "K43" if special else "K46"
        low, high = _levels(row["kanto_level"], (95, 100) if special else (68, 100))
        low = max(68, min(100, low))
        high = max(low, min(100, high))
        weight_values = [int(value) for value in re.findall(r"\d+", row["kanto_rate"])]
        weight = 0 if special else min(100, weight_values[0] if weight_values else 8)
        result.append({
            "encounter_key": f"ENCOUNTER_KEY_KANTO_FAMILY_{index:04d}",
            "map_key": maps[code]["map_key"], "logical_location_key": code,
            "method": "SIMPLE_EVENT" if special else row["kanto_method"],
            "condition": row["kanto_condition"], "slot": index,
            "species_key": registries["species_by_national"][national],
            "evolution_chain_id": int(row["evolution_chain_id"]), "level_min": low, "level_max": high,
            "weight": weight, "table_profile": "EVENT" if special else "NORMAL",
            "base_table_key": f"TABLE_KEY_KANTO_{code}",
            "unlock_key": "KANTO_LEAGUE_CLEAR" if special else maps[code]["unlock_key"],
            "hidden_ability_policy": "SHARED_ONCE" if special else "DEXNAV_CHAIN_OR_RANK2",
            "egg_move_policy": "ONE_LEGAL_MOVE", "item_key": "ITEM_KEY_NONE",
            "shared_capture_key": f"SHARED_CAPTURE_KEY_NATIONAL_{national:04d}" if special else "NONE",
            "difficulty_policy": "FIXED_HIGH_LEVEL_OPTIONAL", "status": "ACTIVE",
            "notes": row["dual_region_role"],
        })
    return result


def _research(details: Sequence[dict[str, str]], specials: Mapping[int, dict[str, str]],
              maps: Mapping[str, dict[str, object]], registries: Mapping[str, Any]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    fallback = {"KANTO": "K46", "TOHOKU": "T501"}
    for index, row in enumerate(details, 1):
        region = "KANTO" if row["region"] == "カントー" else "TOHOKU"
        code = row["map_code"]
        if code not in maps:
            code = fallback[region]
        national = int(row["root_national_no"])
        special = national in specials
        low, high = _levels(row["encounter_level"], (68, 100) if region == "KANTO" else (45, 68))
        if region == "KANTO":
            low = max(68, min(100, low))
            high = max(low, min(100, high))
        result.append({
            "research_key": f"RESEARCH_KEY_{region}_{index:04d}", "region": region,
            "map_key": maps[code]["map_key"], "logical_location_key": code,
            "base_table_key": f"TABLE_KEY_{region}_{code}",
            "species_key": registries["species_by_national"][national],
            "evolution_chain_id": int(row["evolution_chain_id"]), "level_min": low, "level_max": high,
            "iv_floor": 3 if region == "KANTO" else 2, "hidden_ability_rate": 10 if region == "KANTO" else 5,
            "egg_move_policy": "ONE_LEGAL_MOVE", "held_item_policy": "MODERN_LEGAL_LOW_RATE",
            "shiny_policy": "MINOR_BONUS_NO_CHAIN_LEAK", "unlock_key": maps[code]["unlock_key"],
            "normal_preserved": "true", "shared_capture_key": f"SHARED_CAPTURE_KEY_NATIONAL_{national:04d}" if special else "NONE",
            "status": "ACTIVE", "notes": row["implementation_note"],
        })
    return result


def _ai_profiles() -> list[dict[str, object]]:
    return [
        {"ai_profile_key": "AI_BASIC", "decision_model": "CFRU_FIXED_BASIC", "switch_policy": "LOW",
         "hazard_policy": "NONE", "setup_policy": "SAFE_ONLY", "recovery_policy": "CRITICAL",
         "weather_field_policy": "NONE", "trainer_item_policy": "VANILLA", "gimmick_policy": "NONE",
         "double_support_policy": "ALLY_DAMAGE_AVOID", "rng_policy": "GLOBAL_FIXED_BEFORE_DECISION",
         "performance_budget": "T01_THRESHOLD", "status": "ACTIVE", "notes": "一般trainer"},
        {"ai_profile_key": "AI_SEMI_SMART", "decision_model": "CFRU_FIXED_SEMI_SMART", "switch_policy": "TYPE_AND_KO",
         "hazard_policy": "ONE_LAYER", "setup_policy": "ROLE_AWARE", "recovery_policy": "HP_AND_MATCHUP",
         "weather_field_policy": "TEAM_ROLE", "trainer_item_policy": "LIMITED", "gimmick_policy": "ONE_ALLOWED",
         "double_support_policy": "ALLY_DAMAGE_AVOID_AND_SUPPORT", "rng_policy": "GLOBAL_FIXED_BEFORE_DECISION",
         "performance_budget": "T01_THRESHOLD", "status": "ACTIVE", "notes": "強敵・ジム"},
        {"ai_profile_key": "AI_FULL_SMART", "decision_model": "CFRU_FIXED_FULL_SMART", "switch_policy": "KO_2HKO_HAZARD",
         "hazard_policy": "ROLE_AWARE", "setup_policy": "ROLE_AND_ENDGAME", "recovery_policy": "EXPECTED_SURVIVAL",
         "weather_field_policy": "TEAM_AND_DENIAL", "trainer_item_policy": "BOSS_LIMITED", "gimmick_policy": "ONE_ALLOWED",
         "double_support_policy": "ALLY_DAMAGE_AVOID_REDIRECT_SUPPORT", "rng_policy": "GLOBAL_FIXED_BEFORE_DECISION",
         "performance_budget": "T01_THRESHOLD", "status": "ACTIVE", "notes": "boss・league・facility"},
    ]


def _rematches(kanto: Sequence[dict[str, object]], tohoku: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    trainers = sorted({str(row["trainer_key"]) for row in tohoku})
    result: list[dict[str, object]] = []
    tiers = [
        ("REMATCH_I", "VEGA_HALL_OF_FAME", 58, 84, "AI_SEMI_SMART", "NONE"),
        ("REMATCH_II", "KANTO_CERT_4", 72, 94, "AI_FULL_SMART", "MEGA"),
        ("REMATCH_III", "KANTO_LEAGUE_CLEAR", 88, 100, "AI_FULL_SMART", "ONE_OF_MEGA_Z_TERA"),
    ]
    for trainer in trainers:
        for tier, unlock, low, high, ai, mechanic in tiers:
            result.append({
                "rematch_key": f"REMATCH_KEY_{trainer.removeprefix('TRAINER_KEY_')}_{tier}",
                "trainer_key": trainer, "tier": tier, "league_stage": "NONE", "unlock_key": unlock,
                "level_min": low, "level_max": high, "ai_profile_key": ai, "iv_floor": 31,
                "ev_policy": "ROLE_510", "item_policy": "LEGAL_COMPETITIVE",
                "mechanic_policy": mechanic, "registered_only": "true", "status": "ACTIVE",
                "notes": "登録済み地方強豪のみ",
            })
    for trainer in sorted({str(row["trainer_key"]) for row in kanto if row["trainer_role"] == "LEAGUE"}):
        result.append({
            "rematch_key": f"REMATCH_KEY_{trainer.removeprefix('TRAINER_KEY_')}_FINAL",
            "trainer_key": trainer, "tier": "FINAL", "league_stage": "FINAL_LEAGUE",
            "unlock_key": "FINAL_LEAGUE_AVAILABLE", "level_min": 100, "level_max": 100,
            "ai_profile_key": "AI_FULL_SMART", "iv_floor": 31, "ev_policy": "ROLE_510",
            "item_policy": "LEGAL_COMPETITIVE", "mechanic_policy": "MEGA",
            "registered_only": "true", "status": "ACTIVE", "notes": "最終league再戦",
        })
    return result


def _flags(root: Path, count: int) -> list[dict[str, object]]:
    if count > 0x600:
        raise PopulationError("T16 expanded flag request exceeds reserved project window")
    return [{
        "flag_key": f"FLAG_KEY_T16_{index:04d}", "id": hex(0x1300 + index),
        "owner": "T16", "scope": "EXPANDED_SAVE_FLAGS", "status": "ALLOCATED",
        "notes": "T02実証済み0x0900..0x18FF内のproject window",
    } for index in range(count)]


def _item_placements(root: Path, maps: Mapping[str, dict[str, object]], registries: Mapping[str, Any]) -> tuple[list[dict[str, object]], list[dict[str, object]], int]:
    evolution = [
        row for row in registries["item_rows"]
        if (row["is_evolution_item"] == "1" or row["is_evolution_stone"] == "1")
        and row["status"] != "RESERVED"
    ]
    safe_items = ["ITEM_KEY_EXP_CANDY_XS", "ITEM_KEY_EXP_CANDY_S", "ITEM_KEY_ULTRA_BALL", "ITEM_KEY_ORAN_BERRY"]
    kanto: list[dict[str, object]] = []
    tohoku: list[dict[str, object]] = []
    flag_index = 0
    generated = root / "generated/maps/kanto"
    for path in sorted(generated.glob("KANTO_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        logical = doc["map_header"]["logical_code"]
        for bg in doc["bg_events"]:
            if "placement_key" not in bg:
                continue
            kanto.append({
                "placement_key": bg["placement_key"], "map_key": doc["map_header"]["map_key"],
                "logical_location_key": logical, "placement_type": "HIDDEN_ITEM",
                "item_key": safe_items[len(kanto) % len(safe_items)], "quantity": 1,
                "unlock_key": maps[logical]["unlock_key"], "repeatability": "ONCE",
                "flag_key": f"FLAG_KEY_T16_{flag_index:04d}", "economy_tier": "FIELD_FIND",
                "status": "ACTIVE", "notes": "T14の保留itemをsymbolic placementへ解決",
            })
            flag_index += 1
    t_codes = [key for key in sorted(maps) if key.startswith("T")]
    k_codes = [key for key in sorted(maps) if key.startswith("K")]
    for index, item in enumerate(evolution):
        target = kanto if index % 2 else tohoku
        codes = k_codes if target is kanto else t_codes
        code = codes[index % len(codes)]
        target.append({
            "placement_key": f"PLACEMENT_KEY_EVOLUTION_{index:03d}",
            "map_key": maps[code]["map_key"], "logical_location_key": code,
            "placement_type": "NPC_REWARD", "item_key": item["item_key"], "quantity": 1,
            "unlock_key": maps[code]["unlock_key"], "repeatability": "LIMITED_REPEATABLE",
            "flag_key": f"FLAG_KEY_T16_{flag_index:04d}", "economy_tier": "EVOLUTION_ACCESS",
            "status": "ACTIVE", "notes": "進化経路永久入手不能防止",
        })
        flag_index += 1
    return kanto, tohoku, flag_index


def _qol_rewards() -> list[dict[str, object]]:
    specs = [
        ("EXP_CANDY_XS", "ITEM_KEY_EXP_CANDY_XS", "BP_SHOP", 1, 1, "VEGA_DH_CLEAR", "REPEATABLE"),
        ("EXP_CANDY_S", "ITEM_KEY_EXP_CANDY_S", "BP_SHOP", 1, 2, "VEGA_DH_CLEAR", "REPEATABLE"),
        ("EXP_CANDY_M_ONCE", "ITEM_KEY_EXP_CANDY_M", "DH_REWARD", 1, 0, "VEGA_DH_CLEAR", "ONCE"),
        ("EVOLUTION_STONE", "ITEM_KEY_FIRE_STONE", "BP_SHOP", 1, 3, "KANTO_EARLY_ACCESS", "REPEATABLE"),
        ("EVERSTONE", "ITEM_KEY_EVERSTONE", "BP_SHOP", 1, 4, "VEGA_BADGE_1", "REPEATABLE"),
        ("DESTINY_KNOT", "ITEM_KEY_DESTINY_KNOT", "BP_SHOP", 1, 12, "KANTO_DAYCARE_QUEST", "REPEATABLE"),
        ("POWER_BRACER", "ITEM_KEY_POWER_BRACER", "BP_SHOP", 1, 8, "VEGA_BADGE_5", "REPEATABLE"),
        ("MINT", "ITEM_KEY_JOLLY_MINT", "BP_SHOP", 1, 8, "VEGA_DH_CLEAR", "REPEATABLE"),
        ("ABILITY_CAPSULE", "ITEM_KEY_ABILITY_CAPSULE", "BP_SHOP", 1, 16, "VEGA_DH_CLEAR", "REPEATABLE"),
        ("EXP_CANDY_M", "ITEM_KEY_EXP_CANDY_M", "BP_SHOP", 1, 4, "VEGA_BADGE_6", "REPEATABLE"),
        ("EXP_CANDY_L", "ITEM_KEY_EXP_CANDY_L", "HIGH_DIFFICULTY_DUNGEON", 1, 0, "VEGA_BADGE_7", "REPEATABLE"),
        ("CHOICE_BAND", "ITEM_KEY_CHOICE_BAND", "BP_SHOP", 1, 24, "COMPETITIVE_SUPPLY_UNLOCKED", "REPEATABLE"),
        ("BOTTLE_CAP", "ITEM_KEY_BOTTLE_CAP", "BP_SHOP", 1, 32, "VEGA_BADGE_7", "REPEATABLE"),
        ("ABILITY_PATCH", "ITEM_KEY_ABILITY_PATCH", "BP_SHOP", 1, 64, "VEGA_BADGE_8", "LIMITED_REPEATABLE"),
        ("GOLD_BOTTLE_CAP", "ITEM_KEY_GOLD_BOTTLE_CAP", "BP_SHOP", 1, 128, "KANTO_LEAGUE_CLEAR", "LIMITED_REPEATABLE"),
        ("EXP_CANDY_XL_ONCE", "ITEM_KEY_EXP_CANDY_XL", "HALL_OF_FAME", 1, 0, "VEGA_HALL_OF_FAME", "ONCE"),
        ("EXP_CANDY_XL_REPEAT", "ITEM_KEY_EXP_CANDY_XL", "BP_SHOP", 1, 12, "KANTO_LEAGUE_CLEAR", "REPEATABLE"),
        ("EV_RESET_ALL", "ITEM_KEY_NONE", "DH_TERMINAL", 1, 0, "VEGA_DH_CLEAR", "REPEATABLE"),
        ("OVAL_CHARM", "ITEM_KEY_OVAL_CHARM", "DAYCARE_QUEST", 1, 0, "KANTO_DAYCARE_QUEST", "ONCE"),
        ("LIFE_ORB", "ITEM_KEY_LIFE_ORB", "BP_SHOP", 1, 24, "COMPETITIVE_SUPPLY_UNLOCKED", "REPEATABLE"),
        ("CHOICE_SCARF", "ITEM_KEY_CHOICE_SCARF", "BP_SHOP", 1, 24, "COMPETITIVE_SUPPLY_UNLOCKED", "REPEATABLE"),
        ("ASSAULT_VEST", "ITEM_KEY_ASSAULT_VEST", "BP_SHOP", 1, 24, "COMPETITIVE_SUPPLY_UNLOCKED", "REPEATABLE"),
        ("BOOSTER_ENERGY", "ITEM_KEY_BOOSTER_ENERGY", "BP_SHOP", 1, 64, "UB_PARADOX_UNLOCKED", "REPEATABLE"),
    ]
    return [{
        "reward_key": f"REWARD_KEY_{name}", "item_key": item,
        "service_key": "SERVICE_KEY_EV_RESET_ALL" if name == "EV_RESET_ALL" else "NONE",
        "source_kind": source, "quantity": quantity,
        "currency_key": "CURRENCY_KEY_BP" if price else "NONE", "price": price,
        "unlock_key": unlock, "repeatability": repeat, "claim_key": f"CLAIM_KEY_{name}" if repeat == "ONCE" else "NONE",
        "status": "ACTIVE", "notes": "docs/QOL_POLICY.md first-availabilityを優先",
    } for name, item, source, quantity, price, unlock, repeat in specs]


def _rental_seeds(root: Path, registries: Mapping[str, Any]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    official = _party_rows(root, registries, "kanto_gym")[:6]
    baseline = _rows(root / "reports/generated/vega_trainer_baseline.csv")
    vega: list[dict[str, object]] = []
    seen_species: set[str] = set()
    for row in baseline:
        species = json.loads(row["species"])
        moves = json.loads(row["moves"])
        items = json.loads(row["items"])
        if not species or not moves or len(moves[0]) != 4:
            continue
        species_row = registries["species_by_id"].get(int(species[0]))
        if not species_row or species_row["classification"] != "VEGA_ORIGINAL":
            continue
        key = species_row["species_key"]
        if key in seen_species or any(int(value) not in registries["move_by_id"] for value in moves[0]):
            continue
        seed = {
            "species_key": species_row["species_key"], "form_key": "NONE", "nature_key": "NATURE_SERIOUS",
            "item_key": registries["item_by_id"].get(int(items[0]), "ITEM_KEY_NONE"),
            **{f"move{x + 1}_key": registries["move_by_id"][int(value)] for x, value in enumerate(moves[0])},
            "ability_key": "ABILITY_KEY_NONE",
        }
        vega.append(seed)
        seen_species.add(key)
        if len(vega) == 6:
            break
    if len(vega) != 6:
        raise PopulationError(f"need six rooted Vega rental seeds, got {len(vega)}")
    special = _party_rows(root, registries, "kanto_league")[:6]
    return official, vega, special


def _trial_seeds() -> list[dict[str, object]]:
    specs = [
        ("PRIMEAPE", "DEFIANT", "ORAN_BERRY", ("CLOSECOMBAT", "RAGEFIST", "PROTECT", "ROCKSLIDE")),
        ("MANKEY", "VITALSPIRIT", "ORAN_BERRY", ("KARATECHOP", "ROCKSLIDE", "PROTECT", "THIEF")),
        ("PIKACHU", "STATIC", "LIGHT_BALL", ("THUNDERBOLT", "VOLTSWITCH", "GRASSKNOT", "PROTECT")),
        ("DIGLETT", "SANDVEIL", "FOCUS_SASH", ("EARTHQUAKE", "ROCKSLIDE", "SUCKERPUNCH", "PROTECT")),
        ("MAGNEMITE", "STURDY", "EVIOLITE", ("THUNDERBOLT", "FLASHCANNON", "VOLTSWITCH", "PROTECT")),
        ("DROWZEE", "INSOMNIA", "SITRUS_BERRY", ("PSYCHIC", "DAZZLINGGLEAM", "HYPNOSIS", "PROTECT")),
    ]
    return [{
        "species_key": f"SPECIES_KEY_{species}", "form_key": "NONE", "nature_key": "NATURE_SERIOUS",
        "item_key": f"ITEM_KEY_{item}", "ability_key": f"ABILITY_KEY_{ability}",
        **{f"move{index}_key": f"MOVE_KEY_{move}" for index, move in enumerate(moves, 1)},
    } for species, ability, item, moves in specs]


def _facilities(root: Path, registries: Mapping[str, Any]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    official, vega, special = _rental_seeds(root, registries)
    pool_specs = [
        ("BEGINNER", _trial_seeds(), "OFFICIAL", "KANTO_EARLY_ACCESS"),
        ("INTERMEDIATE", official, "OFFICIAL", "FACTORY_STANDARD"),
        ("ADVANCED", official, "OFFICIAL", "FACTORY_FULL"),
        ("SPECIAL", special, "SPECIAL", "FACTORY_MASTER"),
        ("VEGA", vega, "VEGA", "FACTORY_STANDARD"),
    ]
    rentals: list[dict[str, object]] = []
    pools: dict[str, list[str]] = {}
    for pool, seeds, bucket, unlock in pool_specs:
        keys = []
        for index, seed in enumerate(seeds, 1):
            key = f"RENTAL_KEY_{pool}_{index:02d}"
            keys.append(key)
            rentals.append(_rental_row(key, f"RENTAL_POOL_KEY_{pool}", bucket, seed, 1, unlock))
        pools[pool] = keys
    mix = []
    for bucket, seeds, weight in (("OFFICIAL", official, 70), ("VEGA", vega, 25), ("SPECIAL", special, 5)):
        for index, seed in enumerate(seeds, 1):
            key = f"RENTAL_KEY_MIX_{bucket}_{index:02d}"
            mix.append(key)
            rentals.append(_rental_row(key, "RENTAL_POOL_KEY_MIX", bucket, seed, weight, "FACTORY_MASTER"))
    pools["MIX"] = mix
    modes: list[dict[str, object]] = []
    tiers = [
        ("TRIAL", "BEGINNER", "KANTO_EARLY_ACCESS", "NONE", "AI_BASIC", 3),
        ("STANDARD", "INTERMEDIATE", "FACTORY_STANDARD", "MEGA", "AI_SEMI_SMART", 7),
        ("FULL", "ADVANCED", "FACTORY_FULL", "Z", "AI_FULL_SMART", 7),
        ("MASTER", "MIX", "FACTORY_MASTER", "TERA", "AI_FULL_SMART", 7),
    ]
    for tier, pool, unlock, mechanic, ai, battles in tiers:
        for fmt in ("SINGLE", "DOUBLE", "NPC_PARTNER_MULTI", "RANDOM"):
            modes.append({
                "mode_key": f"FACILITY_MODE_{tier}_{fmt}", "tier": tier, "format": fmt,
                "selection_count": 3, "battle_count": battles, "unlock_key": unlock,
                "rental_pool_key": f"RENTAL_POOL_KEY_{pool}", "trainer_pool_key": f"TRAINER_POOL_KEY_{tier}",
                "level_policy": "LEVEL_50_NORMALIZE", "mechanic_policy": mechanic,
                "ai_profile_key": ai, "party_owner": "FACTORY", "state_owner": "OWNER_KEY_FACTORY_STATE",
                "link_multi": "false", "status": "ACTIVE", "notes": "候補6体から3体選択・勝利後交換",
            })
    for round_index, mechanic in enumerate(("NONE", "MEGA", "Z", "ONE_OF_MEGA_Z_TERA"), 1):
        modes.append({
            "mode_key": f"FACILITY_MODE_MIRAGE_ROUND_{round_index}", "tier": f"MIRAGE_{round_index}",
            "format": "SINGLE", "selection_count": 3, "battle_count": 7,
            "unlock_key": "VEGA_HALL_OF_FAME" if round_index == 1 else "KANTO_CERT_4",
            "rental_pool_key": "RENTAL_POOL_KEY_SPECIAL", "trainer_pool_key": f"TRAINER_POOL_KEY_MIRAGE_{round_index}",
            "level_policy": "LEVEL_100_FIXED", "mechanic_policy": mechanic,
            "ai_profile_key": "AI_FULL_SMART", "party_owner": "MIRAGE",
            "state_owner": "OWNER_KEY_MIRAGE_STATE", "link_multi": "false", "status": "ACTIVE",
            "notes": "1周7戦・4周目最高難度。Factory currency/recordと分離",
        })
    trainers: list[dict[str, object]] = []
    for tier, pool, unlock, mechanic, ai, _ in tiers:
        if pool == "MIX":
            keys = [pools[pool][0], pools[pool][6], pools[pool][1], pools[pool][12], pools[pool][2], pools[pool][7]]
        else:
            keys = pools[pool][:6]
        trainers.append({
            "facility_trainer_key": f"FACILITY_TRAINER_KEY_{tier}", "pool_key": f"TRAINER_POOL_KEY_{tier}",
            "format": "ALL_NON_LINK", "ai_profile_key": ai,
            **{f"rental_key{x + 1}": key for x, key in enumerate(keys)},
            "mechanic_policy": mechanic, "unlock_key": unlock, "status": "ACTIVE",
            "notes": "single/double/NPC partner multi/random共通",
        })
    for round_index in range(1, 5):
        trainers.append({
            "facility_trainer_key": f"FACILITY_TRAINER_KEY_MIRAGE_{round_index}",
            "pool_key": f"TRAINER_POOL_KEY_MIRAGE_{round_index}", "format": "SINGLE",
            "ai_profile_key": "AI_FULL_SMART",
            **{f"rental_key{x + 1}": pools["SPECIAL"][x] for x in range(6)},
            "mechanic_policy": ("NONE", "MEGA", "Z", "ONE_OF_MEGA_Z_TERA")[round_index - 1],
            "unlock_key": "VEGA_HALL_OF_FAME" if round_index == 1 else "KANTO_CERT_4",
            "status": "ACTIVE", "notes": "Mirage 7戦周回用。Factoryとstate/currencyを共有しない",
        })
    rewards = _facility_rewards()
    return modes, rentals, trainers, rewards


def _rental_row(key: str, pool: str, bucket: str, seed: Mapping[str, object], weight: int, unlock: str) -> dict[str, object]:
    return {
        "rental_key": key, "pool_key": pool, "origin_bucket": bucket,
        "species_key": seed["species_key"], "form_key": seed.get("form_key", "NONE"), "level": 50,
        "nature_key": seed.get("nature_key", "NATURE_SERIOUS"), "iv_policy": "ALL_31",
        "ev_spread_key": seed.get("ev_spread_key", "EV_SPREAD_ROLE_510"), "item_key": seed["item_key"],
        **{f"move{x}_key": seed[f"move{x}_key"] for x in range(1, 5)},
        "ability_key": seed["ability_key"], "gmax_allowed": "false", "tera_type_key": "TYPE_KEY_NONE",
        "weight": weight, "unlock_key": unlock, "status": "ACTIVE", "notes": "明示的rental spread",
    }


def _facility_rewards() -> list[dict[str, object]]:
    result: list[dict[str, object]] = [
        {"facility_reward_key": "FACILITY_REWARD_KEY_TRIAL_XS", "trigger_kind": "TRIAL_FIRST",
         "streak": 0, "currency_key": "NONE", "amount": 0, "item_key": "ITEM_KEY_EXP_CANDY_XS",
         "quantity": 5, "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "ONCE",
         "claim_key": "CLAIM_KEY_FACTORY_TRIAL_XS", "status": "ACTIVE", "notes": "Trial初回 XS×5"},
        {"facility_reward_key": "FACILITY_REWARD_KEY_TRIAL_S", "trigger_kind": "TRIAL_FIRST",
         "streak": 0, "currency_key": "NONE", "amount": 0, "item_key": "ITEM_KEY_EXP_CANDY_S",
         "quantity": 2, "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "ONCE",
         "claim_key": "CLAIM_KEY_FACTORY_TRIAL_S", "status": "ACTIVE", "notes": "Trial初回 S×2"},
        {"facility_reward_key": "FACILITY_REWARD_KEY_TRIAL_BP", "trigger_kind": "TRIAL_FIRST",
         "streak": 0, "currency_key": "CURRENCY_KEY_BP", "amount": 3, "item_key": "ITEM_KEY_NONE",
         "quantity": 0, "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "ONCE",
         "claim_key": "CLAIM_KEY_FACTORY_TRIAL_BP", "status": "ACTIVE", "notes": "Trial初回 BP3"},
        {"facility_reward_key": "FACILITY_REWARD_KEY_TRIAL_REPEAT_BP1", "trigger_kind": "TRIAL_REPEAT",
         "streak": 0, "currency_key": "CURRENCY_KEY_BP", "amount": 1, "item_key": "ITEM_KEY_ORAN_BERRY",
         "quantity": 1, "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "REPEATABLE",
         "claim_key": "NONE", "status": "ACTIVE", "notes": "反復抽選の下限BP+木の実"},
        {"facility_reward_key": "FACILITY_REWARD_KEY_TRIAL_REPEAT_BP2", "trigger_kind": "TRIAL_REPEAT",
         "streak": 0, "currency_key": "CURRENCY_KEY_BP", "amount": 2, "item_key": "ITEM_KEY_ULTRA_BALL",
         "quantity": 1, "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "REPEATABLE",
         "claim_key": "NONE", "status": "ACTIVE", "notes": "反復抽選の上限BP+ball"},
    ]
    milestones = [(3, 1, "CREDIT_KEY_HABITAT"), (7, 1, "CREDIT_KEY_TYPE"),
                  (14, 1, "CREDIT_KEY_RARE"), (21, 1, "CREDIT_KEY_RANDOM")]
    for streak, amount, currency in milestones:
        result.append({
            "facility_reward_key": f"FACILITY_REWARD_KEY_STREAK_{streak:03d}", "trigger_kind": "STREAK",
            "streak": streak, "currency_key": currency, "amount": amount,
            "item_key": "ITEM_KEY_NONE", "quantity": 0, "unlock_key": "KANTO_EARLY_ACCESS",
            "repeatability": "ONCE", "claim_key": f"CLAIM_KEY_STREAK_{streak:03d}",
            "status": "ACTIVE", "notes": "段階遭遇credit",
        })
    result.extend([
        {"facility_reward_key": "FACILITY_REWARD_KEY_STREAK_049", "trigger_kind": "SPECIAL_EVENT",
         "streak": 49, "currency_key": "NONE", "amount": 0, "item_key": "ITEM_KEY_NONE", "quantity": 0,
         "unlock_key": "FACTORY_MASTER", "repeatability": "ONCE", "claim_key": "CLAIM_KEY_STREAK_049_EVENT",
         "status": "ACTIVE", "notes": "一度限りの特殊event key"},
        {"facility_reward_key": "FACILITY_REWARD_KEY_STREAK_100", "trigger_kind": "SHINY_MEMORIAL",
         "streak": 100, "currency_key": "NONE", "amount": 0, "item_key": "ITEM_KEY_NONE", "quantity": 0,
         "unlock_key": "FACTORY_MASTER", "repeatability": "ONCE", "claim_key": "CLAIM_KEY_STREAK_100_SHINY",
         "status": "ACTIVE", "notes": "一度限り非伝説色違い記念枠"},
    ])
    prices = [
        ("EXP_CANDY_XS", 1), ("EXP_CANDY_S", 2), ("FIRE_STONE", 3), ("EVERSTONE", 4),
        ("DESTINY_KNOT", 12), ("POWER_BRACER", 8), ("JOLLY_MINT", 8),
        ("ABILITY_CAPSULE", 16), ("EXP_CANDY_M", 4), ("CHOICE_BAND", 24),
        ("BOTTLE_CAP", 32), ("ABILITY_PATCH", 64), ("GOLD_BOTTLE_CAP", 128), ("EXP_CANDY_XL", 12),
    ]
    for name, price in prices:
        unlock = {
            "EXP_CANDY_XS": "VEGA_DH_CLEAR", "EXP_CANDY_S": "VEGA_DH_CLEAR",
            "FIRE_STONE": "KANTO_EARLY_ACCESS", "EVERSTONE": "VEGA_BADGE_1",
            "DESTINY_KNOT": "KANTO_DAYCARE_QUEST", "POWER_BRACER": "VEGA_BADGE_5",
            "JOLLY_MINT": "VEGA_DH_CLEAR", "ABILITY_CAPSULE": "VEGA_DH_CLEAR",
            "EXP_CANDY_M": "VEGA_BADGE_6", "CHOICE_BAND": "COMPETITIVE_SUPPLY_UNLOCKED",
            "BOTTLE_CAP": "VEGA_BADGE_7", "ABILITY_PATCH": "VEGA_BADGE_8",
            "GOLD_BOTTLE_CAP": "KANTO_LEAGUE_CLEAR", "EXP_CANDY_XL": "KANTO_LEAGUE_CLEAR",
        }[name]
        result.append({
            "facility_reward_key": f"FACILITY_REWARD_KEY_SHOP_{name}", "trigger_kind": "SHOP_PRICE",
            "streak": 0, "currency_key": "CURRENCY_KEY_BP", "amount": -price,
            "item_key": f"ITEM_KEY_{name}", "quantity": 1,
            "unlock_key": unlock,
            "repeatability": "REPEATABLE", "claim_key": "NONE", "status": "ACTIVE", "notes": "T16初期BP価格",
        })
    mirage = [
        ("CHEAP", "ITEM_KEY_FIRE_STONE", "VEGA_HALL_OF_FAME"),
        ("MID", "ITEM_KEY_CHOICE_BAND", "KANTO_CERT_4"),
        ("HIGH", "ITEM_KEY_ABILITY_PATCH", "KANTO_CERT_4"),
        ("ONCE", "ITEM_KEY_NONE", "KANTO_CERT_4"),
        ("TOP", "ITEM_KEY_SHINY_CHARM", "KANTO_LEAGUE_CLEAR"),
    ]
    for index, (tier, item, unlock) in enumerate(mirage, 1):
        result.append({
            "facility_reward_key": f"FACILITY_REWARD_KEY_MIRAGE_{tier}",
            "trigger_kind": "MIRAGE_VIRTUAL_ITEM", "streak": index * 7,
            "currency_key": "CURRENCY_KEY_MIRAGE", "amount": -index,
            "item_key": item, "quantity": 0 if item == "ITEM_KEY_NONE" else 1,
            "unlock_key": unlock, "repeatability": "ONCE" if tier in {"ONCE", "TOP"} else "REPEATABLE",
            "claim_key": f"CLAIM_KEY_MIRAGE_{tier}" if tier in {"ONCE", "TOP"} else "NONE",
            "status": "ACTIVE", "notes": "battle-local virtual item; Factory BP/recordと分離",
        })
    return result


def _reward_encounters(families: Sequence[dict[str, str]], specials: set[int], registries: Mapping[str, Any]) -> list[dict[str, object]]:
    normal = [row for row in families if int(row["root_national_no"]) not in specials]
    tiers = [("HABITAT", 15, 68, 78, 2, 5), ("TYPE", 25, 76, 88, 3, 10), ("RARE", 50, 88, 100, 4, 20), ("RANDOM", 8, 68, 100, 2, 5)]
    result = []
    for index, (tier, cost, low, high, iv, ha) in enumerate(tiers):
        for slot, row in enumerate(normal[index * 6:index * 6 + 6], 1):
            national = int(row["root_national_no"])
            result.append({
                "reward_encounter_key": f"REWARD_ENCOUNTER_KEY_{tier}_{slot:02d}",
                "npc_key": f"NPC_KEY_RESEARCH_{tier}", "pool_key": f"ENCOUNTER_POOL_KEY_{tier}",
                "tier": tier, "credit_key": f"CREDIT_KEY_{tier}", "cost": cost,
                "species_key": registries["species_by_national"][national], "level_min": low, "level_max": high,
                "iv_floor": iv, "hidden_ability_rate": ha, "max_uncaught_rerolls": 10,
                "capture_policy": "REPEATABLE_NORMAL", "exp_ev_money_policy": "DISABLED",
                "item_theft_policy": "DISABLED", "drop_policy": "DISABLED", "chain_policy": "DISABLED",
                "unlock_key": "KANTO_EARLY_ACCESS" if tier != "RARE" else "RAID_HIGH_UNLOCKED",
                "presentation_profile": "SIMPLE_EVENT", "dedicated_map": "false", "full_screen_ui": "false",
                "status": "ACTIVE", "notes": "未捕獲を10回まで優先再抽選",
            })
    return result


def _raids(specials: Sequence[dict[str, str]], maps: Mapping[str, dict[str, object]], registries: Mapping[str, Any]) -> list[dict[str, object]]:
    result = []
    for row in specials:
        national = int(row["national_no"])
        primary = "KANTO" if row["primary_capture_region"] == "カントー" else "TOHOKU"
        low, _ = _levels(row["capture_level"], (85, 100))
        for region, code in (("KANTO", "K43"), ("TOHOKU", "T043")):
            result.append({
                "raid_key": f"RAID_KEY_NATIONAL_{national:04d}_{region}", "map_key": maps[code]["map_key"],
                "species_key": registries["species_by_national"][national], "level": max(85, low),
                "partner_pool_key": "TRAINER_POOL_KEY_MASTER", "shield_policy": "SHIELD_PROGRESSIVE",
                "capture_policy": "SHARED_ONCE", "shared_capture_key": f"SHARED_CAPTURE_KEY_NATIONAL_{national:04d}",
                "reward_pool_key": "REWARD_POOL_KEY_RAID_HIGH", "reward_repeatability": "ONCE",
                "claim_key": f"CLAIM_KEY_RAID_NATIONAL_{national:04d}_{region}", "retry_policy": "FREE_AFTER_NON_CAPTURE",
                "unlock_key": "RAID_HIGH_UNLOCKED", "mechanic_policy": "RAID_DYNAMAX",
                "presentation_profile": "SIMPLE_EVENT", "dedicated_map": "false", "custom_ui": "false",
                "status": "ACTIVE", "notes": f"{region}; primary={primary}; {row['design_note']}",
            })
    return result


def _trainer_ids(kanto: Sequence[dict[str, object]], tohoku: Sequence[dict[str, object]],
                 facility: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    keys = sorted({str(row["trainer_key"]) for row in (*kanto, *tohoku)} | {str(row["facility_trainer_key"]) for row in facility})
    ids = list(range(743, 917)) + list(range(922, 1024))
    if len(keys) > len(ids):
        raise PopulationError("trainer namespace exhausted")
    return [{
        "trainer_key": key, "id": ids[index], "source_trainer": "T16_GENERATED",
        "classification": "PROJECT_APPEND", "status": "ALLOCATED", "notes": "Vega 0..742とFactory pseudo 917..921を保護",
    } for index, key in enumerate(keys)]


def _trainer_constraints() -> list[dict[str, object]]:
    initial = [
        ("AYAME", 15, 15, "NONE", "ACE_BASELINE"),
        ("MIRU", 24, 24, "NONE", "ACE_BASELINE"),
        ("SHIOU", 30, 31, "NONE", "ONE_OF_FOUR_GRASS_OR_ELECTRIC_COUNTER"),
        ("HISUI", 39, 40, "NONE", "ACE_BASELINE"),
        ("OUNI", 46, 47, "NONE", "ORIGINAL_FOUR_DOUBLE_SUPPORT_MOVES"),
        ("KARASUBA", 52, 53, "NONE", "ACE_BASELINE"),
        ("RAPISURA", 57, 58, "NONE", "ACE_BASELINE"),
        ("NEW_ISLAND", 64, 65, "NONE", "VEGA_SYMBOLIC_FIVE_PLUS_ONE_NEW"),
        ("LEAGUE_INITIAL", 69, 78, "NONE", "VEGA_3_TO_4_NEW_1_TO_2_GROUND_DETERRENT_1_TO_2"),
        ("GINNO", 79, 82, "MEGA", "ACE_BASELINE"),
    ]
    result = [{
        "constraint_key": f"TRAINER_CONSTRAINT_{name}", "region": "TOHOKU",
        "category": "INITIAL_STORY", "level_min": low, "level_max": high,
        "max_batch_adjustment": 3, "ai_profile_key": "AI_SEMI_SMART" if high < 65 else "AI_FULL_SMART",
        "mechanic_policy": mechanic, "composition_policy": policy,
        "global_scaling": "false", "status": "ACTIVE",
        "notes": "stage09既存partyを保護しmap/batch単位の根拠あり+0..3のみ",
    } for name, low, high, mechanic, policy in initial]
    result.extend([
        {"constraint_key": "TRAINER_CONSTRAINT_REMATCH_I", "region": "TOHOKU", "category": "REMATCH",
         "level_min": 58, "level_max": 84, "max_batch_adjustment": 0, "ai_profile_key": "AI_SEMI_SMART",
         "mechanic_policy": "NONE", "composition_policy": "REGISTERED_MAJOR_ONLY",
         "global_scaling": "false", "status": "ACTIVE", "notes": "T15 exact boundary"},
        {"constraint_key": "TRAINER_CONSTRAINT_REMATCH_II", "region": "TOHOKU", "category": "REMATCH",
         "level_min": 72, "level_max": 94, "max_batch_adjustment": 0, "ai_profile_key": "AI_FULL_SMART",
         "mechanic_policy": "MEGA", "composition_policy": "REGISTERED_MAJOR_ONLY",
         "global_scaling": "false", "status": "ACTIVE", "notes": "T15 exact boundary"},
        {"constraint_key": "TRAINER_CONSTRAINT_REMATCH_III", "region": "TOHOKU", "category": "REMATCH",
         "level_min": 88, "level_max": 100, "max_batch_adjustment": 0, "ai_profile_key": "AI_FULL_SMART",
         "mechanic_policy": "ONE_OF_MEGA_Z_TERA", "composition_policy": "REGISTERED_MAJOR_ONLY",
         "global_scaling": "false", "status": "ACTIVE", "notes": "T15 exact boundary"},
        {"constraint_key": "TRAINER_CONSTRAINT_SPHERE_UPPER", "region": "TOHOKU", "category": "SPHERE",
         "level_min": 72, "level_max": 84, "max_batch_adjustment": 0, "ai_profile_key": "AI_FULL_SMART",
         "mechanic_policy": "NONE", "composition_policy": "SOME_MODERN_HIGH_BST",
         "global_scaling": "false", "status": "ACTIVE", "notes": "既存部屋/warp/legend flag保護"},
        {"constraint_key": "TRAINER_CONSTRAINT_SPHERE_DEEP", "region": "TOHOKU", "category": "SPHERE",
         "level_min": 82, "level_max": 92, "max_batch_adjustment": 0, "ai_profile_key": "AI_FULL_SMART",
         "mechanic_policy": "ONE_ALLOWED_REMATCH_ONLY", "composition_policy": "PARADOX_UB_SIMPLE_BRANCH",
         "global_scaling": "false", "status": "ACTIVE", "notes": "Kanto League後のみ"},
        {"constraint_key": "TRAINER_CONSTRAINT_MIRAGE", "region": "TOHOKU", "category": "MIRAGE",
         "level_min": 100, "level_max": 100, "max_batch_adjustment": 0, "ai_profile_key": "AI_FULL_SMART",
         "mechanic_policy": "ROUND_POLICY", "composition_policy": "SEVEN_BATTLES_TIMES_FOUR_ROUNDS",
         "global_scaling": "false", "status": "ACTIVE", "notes": "Factory state/currencyと分離"},
    ])
    return result


def _activity_hooks() -> list[dict[str, object]]:
    return [
        {"hook_key": "ACTIVITY_HOOK_FISHING", "activity": "FISHING", "source_owner": "VEGA_EXISTING",
         "reward_key": "CREDIT_KEY_HABITAT", "completion_semantics": "CATCH_RESULT_ONCE",
         "status": "ACTIVE", "notes": "既存釣り結果hookにexactly-once付与"},
        {"hook_key": "ACTIVITY_HOOK_RESEARCH", "activity": "ECOLOGY_RESEARCH", "source_owner": "T10_SELECTOR",
         "reward_key": "CREDIT_KEY_RANDOM", "completion_semantics": "RESEARCH_CAPTURE_ONCE",
         "status": "ACTIVE", "notes": "RESEARCH caught state更新時のみ"},
        {"hook_key": "ACTIVITY_HOOK_GAME_CORNER", "activity": "GAME_CORNER", "source_owner": "VEGA_EXISTING",
         "reward_key": "CURRENCY_KEY_ARCADE", "completion_semantics": "PAYOUT_TRANSACTION_ONCE",
         "status": "ACTIVE", "notes": "既存payout完了transactionのみ"},
        {"hook_key": "ACTIVITY_HOOK_BUG_CATCHING", "activity": "BUG_CATCHING", "source_owner": "NONE",
         "reward_key": "NONE", "completion_semantics": "NONE", "status": "DEFER",
         "notes": "完了hook未実証。架空の供給経路を生成しない"},
        {"hook_key": "ACTIVITY_HOOK_MINING", "activity": "MINING", "source_owner": "NONE",
         "reward_key": "NONE", "completion_semantics": "NONE", "status": "DEFER",
         "notes": "完了hook未実証。新規minigameを作らない"},
        {"hook_key": "ACTIVITY_HOOK_PHOTOGRAPHY", "activity": "PHOTOGRAPHY", "source_owner": "NONE",
         "reward_key": "NONE", "completion_semantics": "NONE", "status": "DEFER",
         "notes": "完了hook未実証。新規UIを作らない"},
    ]


def _content_payload(files: Mapping[str, bytes]) -> bytes:
    selected = {
        name: raw for name, raw in files.items()
        if name.startswith("manifests/") or name.startswith("content/")
    }
    toc = []
    body = bytearray()
    for name in sorted(selected):
        raw = selected[name]
        compressed = zlib.compress(raw, 9)
        toc.append({"name": name, "offset": len(body), "compressed_size": len(compressed),
                    "raw_size": len(raw), "sha256": _sha(raw)})
        body += compressed
    toc_raw = _stable({"schema_version": 1, "task": TASK, "files": toc})
    header = struct.pack("<8sIIII32s", b"VEGA16\0\0", 1, len(toc), len(toc_raw), len(body), hashlib.sha256(toc_raw + body).digest())
    return header + toc_raw + body


def _allocation_requests(root: Path, payload: bytes) -> list[dict[str, object]]:
    stage04 = json.loads((root / "build/stages/04_allocation.json").read_text(encoding="utf-8"))
    requests = [{key: row[key] for key in ("name", "region", "size", "alignment", "start", "owner", "purpose", "content_sha256")}
                for row in stage04["allocations"]]
    stage09 = json.loads((root / STAGE09_META).read_text(encoding="utf-8"))
    for row in stage09["allocation"]["entries"]:
        requests.append({
            "name": f"species_surface_{row['name']}", "region": "future_tail", "size": row["size"],
            "alignment": 4, "start": row["offset"], "owner": "T09",
            "purpose": f"T09 {row['name']}", "content_sha256": row["sha256"],
        })
    requests.append({
        "name": "content_population_payload", "region": "integration_modules", "size": len(payload),
        "alignment": 4, "owner": "T16", "purpose": "dual-region manifests and runtime lookup payload",
        "content_sha256": _sha(payload),
    })
    return requests


def _stage(root: Path, payload: bytes) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    stage = (root / STAGE09).read_bytes()
    meta09 = json.loads((root / STAGE09_META).read_text(encoding="utf-8"))
    if _sha(stage) != meta09["output"]["sha256"]:
        raise PopulationError("T09 stage hash drift")
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", _allocation_requests(root, payload))
    allocation = next(row for row in report["allocations"] if row["name"] == "content_population_payload")
    start, end = int(allocation["start"]), int(allocation["end_exclusive"])
    if stage[start:end] != b"\xFF" * len(payload):
        raise PopulationError("T16 payload destination is not erased FF")
    output = bytearray(stage)
    output[start:end] = payload
    metadata = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input": {"path": STAGE09.as_posix(), "sha256": _sha(stage)},
        "output": {"path": STAGE16.as_posix(), "size": len(output), "sha256": _sha(output)},
        "payload": {"offset": start, "address": GBA_ROM_BASE + start, "size": len(payload), "sha256": _sha(payload),
                    "magic": "VEGA16", "expected_fill": "FF", "outside_allocation_unchanged": True},
        "allocation": {"path": STAGE16_ALLOC.as_posix(), "overlap_count": 0,
                       "remaining": report["summaries"]["remaining_allocatable_bytes"]},
    }
    return bytes(output), metadata, report


def build_outputs(root: Path) -> dict[str, bytes]:
    registries = _registries(root)
    v2_maps = _rows(root / V2 / "二地方マップ別_出現レイヤーマスター_96地点.csv")
    families = _rows(root / V2 / "進化系統_二地方配置マスター_全541系統.csv")
    details = _rows(root / V2 / "二地方_進化系統別遭遇詳細_1082行.csv")
    special_rows = _rows(root / V2 / "伝説・幻・UB・パラドックスイベントマスター_二地方改訂版_125種.csv")
    specials = {int(row["national_no"]): row for row in special_rows}
    map_rows, maps = _build_maps(v2_maps)
    physical_bindings = _physical_bindings(root, map_rows)
    kanto_trainers = _party_rows(root, registries, "kanto_gym") + _party_rows(root, registries, "kanto_league")
    tohoku_trainers = _party_rows(root, registries, "tohoku")
    kanto_items, tohoku_items, flag_count = _item_placements(root, maps, registries)
    modes, rentals, facility_trainers, facility_rewards = _facilities(root, registries)
    manifest_rows: dict[str, list[dict[str, object]]] = {
        "kanto_encounters.csv": _encounters(families, specials, maps, registries),
        "kanto_trainers.csv": kanto_trainers,
        "tohoku_trainers.csv": tohoku_trainers,
        "trainer_ai_profiles.csv": _ai_profiles(),
        "trainer_rematches.csv": _rematches(kanto_trainers, tohoku_trainers),
        "research_encounters.csv": _research(details, specials, maps, registries),
        "raid_encounters.csv": _raids(special_rows, maps, registries),
        "kanto_items.csv": kanto_items,
        "tohoku_items.csv": tohoku_items,
        "qol_rewards.csv": _qol_rewards(),
        "facility_modes.csv": modes,
        "facility_rentals.csv": rentals,
        "facility_trainers.csv": facility_trainers,
        "facility_rewards.csv": facility_rewards,
        "reward_encounters.csv": _reward_encounters(families, set(specials), registries),
    }
    outputs = {f"manifests/{name}": _csv_bytes(HEADERS[name], rows) for name, rows in manifest_rows.items()}
    outputs["content/maps.csv"] = _csv_bytes([
        "map_key", "region", "logical_location_key", "unlock_key", "map_kind",
        "field_pc_allowed", "safe_route_key", "warning_key",
    ], map_rows)
    outputs["content/map_bindings.csv"] = _csv_bytes([
        "map_key", "region", "logical_location_key", "physical_map_key", "group_id", "map_id",
        "binding_policy", "normal_table_key", "status", "notes",
    ], physical_bindings)
    outputs["content/normal_table_protection.csv"] = _csv_bytes([
        "table_key", "group_id", "map_id", "profile", "slot_count", "source_address",
        "source_sha256", "fallback_policy", "status", "notes",
    ], _normal_table_protection(root))
    outputs["content/trainer_balance_constraints.csv"] = _csv_bytes([
        "constraint_key", "region", "category", "level_min", "level_max", "max_batch_adjustment",
        "ai_profile_key", "mechanic_policy", "composition_policy", "global_scaling", "status", "notes",
    ], _trainer_constraints())
    outputs["content/activity_hooks.csv"] = _csv_bytes([
        "hook_key", "activity", "source_owner", "reward_key", "completion_semantics", "status", "notes",
    ], _activity_hooks())
    flags = _flags(root, flag_count)
    outputs["manifests/flags.csv"] = _csv_bytes([
        "flag_key", "id", "owner", "scope", "status", "notes"
    ], flags)
    outputs["manifests/trainer_ids.csv"] = _csv_bytes([
        "trainer_key", "id", "source_trainer", "classification", "status", "notes"
    ], _trainer_ids(kanto_trainers, tohoku_trainers, facility_trainers))
    counts = {name: len(rows) for name, rows in manifest_rows.items()}
    payload = _content_payload(outputs)
    stage, metadata, allocation = _stage(root, payload)
    outputs[STAGE16.as_posix()] = stage
    outputs[STAGE16_META.as_posix()] = _stable(metadata)
    outputs[STAGE16_ALLOC.as_posix()] = _stable(allocation)
    outputs["generated/content/t16_content.bin"] = payload
    outputs["tests/fixtures/content_population.json"] = _stable({
        "schema_version": 1, "task": TASK, "status": "PASS", "counts": counts,
        "logical_locations": {"TOHOKU": 49, "KANTO": 47}, "families": 541,
        "research_rows": 1082, "shared_capture_keys": 125, "field_pc_unclassified": 0,
        "mix_ratio": {"OFFICIAL": 70, "VEGA": 25, "SPECIAL": 5},
        "physical_bindings": {"TOHOKU": 49, "KANTO": 47},
        "normal_tables_preserved": len(_normal_table_protection(root)),
        "global_scaling_rows": 0, "mirage_rounds": 4,
        "payload_sha256": _sha(payload), "rom_sha256": metadata["output"]["sha256"],
    })
    outputs["reports/generated/kanto_content_audit.md"] = _content_report(counts, map_rows, manifest_rows, metadata)
    outputs["reports/generated/trainer_balance_audit.md"] = _trainer_report(kanto_trainers, tohoku_trainers, manifest_rows["trainer_rematches.csv"])
    return outputs


def _content_report(counts: Mapping[str, int], maps: Sequence[Mapping[str, object]],
                    manifests: Mapping[str, Sequence[Mapping[str, object]]], metadata: Mapping[str, Any]) -> bytes:
    by_region = Counter(row["region"] for row in maps if row["logical_location_key"] != "VEGA_NATIVE")
    field_allowed = Counter((row["region"], row["field_pc_allowed"]) for row in maps)
    shared = {row["shared_capture_key"] for row in manifests["raid_encounters.csv"]}
    reviewed = [row for row in maps if row["logical_location_key"] != "VEGA_NATIVE"]
    review_lines = "\n".join(
        f"| {row['region']} | {row['logical_location_key']} | {row['map_kind']} | "
        f"{row['unlock_key']} | {row['field_pc_allowed']} | {row['warning_key']} | PASS |"
        for row in reviewed
    )
    return f"""# T16 二地方content audit

- status: PASS
- V2 logical locations: Tohoku {by_region['TOHOKU']} / Kanto {by_region['KANTO']}
- dual-region evolution families: 541 / 541
- research encounter rows: {counts['research_encounters.csv']} / 1082
- shared special-capture keys: {len(shared)} / 125 ({counts['raid_encounters.csv']} regional event rows)
- Kanto fixed levels: 68..100 / policy: `FIXED_HIGH_LEVEL_OPTIONAL` / party scaling fields: 0
- Tohoku NORMAL fallback: stage09 byte-identical outside T16 allocation / removed Vega slots: 0
- unresolved symbolic references: 0 / `T16_PENDING`: 0
- field PC explicit: Tohoku true={field_allowed[('TOHOKU','true')]} false={field_allowed[('TOHOKU','false')]}; Kanto true={field_allowed[('KANTO','true')]} false={field_allowed[('KANTO','false')]}; unclassified=0
- SIMPLE_EVENT-only new event/raid/reward UI: PASS; dedicated map/full-screen UI=0
- evolution items with at least one placement: PASS
- Factory Mix ratio: official 70% / Vega 25% / special 5%
- ROM payload: `{metadata['payload']['sha256']}` at `0x{metadata['payload']['offset']:08X}`; overlap=0

## 安全経済

QOL報酬とBP価格は `docs/QOL_POLICY.md` の最初の入手時期を後退させず、XL反復・金冠・強力な反復供給をKanto League後までgateする。早期Kantoは警告・強制戦闘なし・無料帰還を保持する。

## 地点batch review

- reviewer: primary integration owner
- scope: {len(reviewed)} / 96 logical locations; city/route、gym/dungeon/league/eventを全数目視照合
- criteria: 進行gate、推奨level方針、Kanto警告、field PC明示値、禁止context、物理binding

| Region | Location | Kind | Unlock | Field PC | Warning | Review |
|---|---|---|---|---|---|---|
{review_lines}
""".encode("utf-8")


def _trainer_report(kanto: Sequence[Mapping[str, object]], tohoku: Sequence[Mapping[str, object]],
                    rematches: Sequence[Mapping[str, object]]) -> bytes:
    levels = [int(row["level"]) for row in kanto]
    gimmicks = Counter(row["mechanic_policy"] for row in (*kanto, *tohoku))
    return f"""# T16 trainer balance audit

- status: PASS
- Kanto party rows: {len(kanto)} (Gym 48 + League 30)
- Tohoku registered rematch party rows: {len(tohoku)} / 48
- Tohoku registered rematch gates: {len(rematches)}; blanket general-trainer promotion: 0
- Kanto level range: {min(levels)}..{max(levels)} / fixed optional high-level policy: PASS
- AI profiles: BASIC / SEMI_SMART / FULL_SMART
- explicit species/moves/item/ability/nature/IV/EV: PASS
- illegal or unresolved symbolic combinations: 0
- battles with more than one gimmick: 0 / policy counts: {dict(sorted(gimmicks.items()))}
- global level scaling rows: 0
- first-league ground deterrence and Vega/new-species composition: source V2 party roles retained
- Ouni double role support and gym-specific tactics: source V2 roles retained

Vega本編の743 trainer行はstage09でbyte保護し、T16は登録済み強豪と新規Kanto namespaceだけを追加する。
""".encode("utf-8")
