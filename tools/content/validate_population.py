"""Focused semantic validator for the T16 content-population manifests."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping, Sequence

from tools.content.populate_content import HEADERS


NONE = {"", "NONE"}
PRIMARY_KEYS = {
    "kanto_encounters.csv": "encounter_key",
    "trainer_ai_profiles.csv": "ai_profile_key",
    "trainer_rematches.csv": "rematch_key",
    "research_encounters.csv": "research_key",
    "raid_encounters.csv": "raid_key",
    "kanto_items.csv": "placement_key",
    "tohoku_items.csv": "placement_key",
    "qol_rewards.csv": "reward_key",
    "facility_modes.csv": "mode_key",
    "facility_rentals.csv": "rental_key",
    "facility_trainers.csv": "facility_trainer_key",
    "facility_rewards.csv": "facility_reward_key",
    "reward_encounters.csv": "reward_encounter_key",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _unique(rows: Sequence[Mapping[str, str]], fields: tuple[str, ...], label: str,
            errors: list[str]) -> None:
    seen: dict[tuple[str, ...], int] = {}
    for line, row in enumerate(rows, 2):
        key = tuple(row[field] for field in fields)
        if key in seen:
            errors.append(f"{label}:{line}: duplicate {fields} {key} (first at {seen[key]})")
        seen[key] = line


def _integer(row: Mapping[str, str], field: str, label: str, line: int,
             errors: list[str], low: int | None = None, high: int | None = None) -> int | None:
    try:
        value = int(row[field], 0)
    except (KeyError, ValueError):
        errors.append(f"{label}:{line}: invalid {field} {row.get(field)!r}")
        return None
    if low is not None and value < low or high is not None and value > high:
        errors.append(f"{label}:{line}: {field} outside {low}..{high}: {value}")
    return value


def _check_refs(rows: Sequence[Mapping[str, str]], fields: Mapping[str, set[str]],
                label: str, errors: list[str]) -> None:
    for line, row in enumerate(rows, 2):
        for field, registry in fields.items():
            value = row[field]
            if value not in NONE and value not in registry:
                errors.append(f"{label}:{line}: unresolved {field} {value}")


def _party(rows: Sequence[Mapping[str, str]], label: str, species: set[str], moves: set[str],
           items: set[str], abilities: set[str], ai: set[str], errors: list[str]) -> None:
    _unique(rows, ("trainer_key", "party_slot"), label, errors)
    grouped: dict[str, list[int]] = defaultdict(list)
    for line, row in enumerate(rows, 2):
        slot = _integer(row, "party_slot", label, line, errors, 1, 6)
        _integer(row, "level", label, line, errors, 1, 100)
        _integer(row, "iv_floor", label, line, errors, 0, 31)
        if slot is not None:
            grouped[row["trainer_key"]].append(slot)
        _check_refs([row], {
            "species_key": species, "item_key": items, "ability_key": abilities,
            "move1_key": moves, "move2_key": moves, "move3_key": moves, "move4_key": moves,
            "ai_profile_key": ai,
        }, label, errors)
        if row["status"] != "ACTIVE" or row["ability_policy"] != "EXPLICIT":
            errors.append(f"{label}:{line}: party row must be ACTIVE with EXPLICIT ability")
        if "|" in row["mechanic_policy"]:
            errors.append(f"{label}:{line}: more than one simultaneous gimmick")
        move_values = [row[f"move{index}_key"] for index in range(1, 5)]
        if row["species_key"] == "SPECIES_KEY_DITTO":
            if move_values != ["MOVE_KEY_TRANSFORM", "MOVE_KEY_NONE", "MOVE_KEY_NONE", "MOVE_KEY_NONE"]:
                errors.append(f"{label}:{line}: Ditto must use Transform-only explicit set")
        elif any(move == "MOVE_KEY_NONE" for move in move_values):
            errors.append(f"{label}:{line}: non-Ditto requires four explicit moves")
    for key, slots in grouped.items():
        if sorted(slots) != list(range(1, len(slots) + 1)) or len(slots) != 6:
            errors.append(f"{label}: {key} party slots must be exact 1..6")


def _load_support(root: Path, errors: list[str]) -> dict[str, list[dict[str, str]]]:
    paths = {
        "maps": root / "content/maps.csv",
        "bindings": root / "content/map_bindings.csv",
        "normal": root / "content/normal_table_protection.csv",
        "constraints": root / "content/trainer_balance_constraints.csv",
        "activities": root / "content/activity_hooks.csv",
    }
    result: dict[str, list[dict[str, str]]] = {}
    for key, path in paths.items():
        if not path.is_file():
            errors.append(f"{path.relative_to(root)}: missing")
            result[key] = []
        else:
            result[key] = _rows(path)
    return result


def collect_population_errors(root: Path,
                              loaded: Mapping[str, list[dict[str, str]]]) -> list[str]:
    if not any(loaded.get(name) for name in HEADERS):
        return []
    errors: list[str] = []
    missing = [name for name in HEADERS if not loaded.get(name)]
    if missing:
        return ["T16 manifests must be emitted as one complete set: " + ", ".join(missing)]
    rows = {name: loaded[name] for name in HEADERS}
    for name, key in PRIMARY_KEYS.items():
        _unique(rows[name], (key,), name, errors)
    for name, manifest_rows in rows.items():
        for line, row in enumerate(manifest_rows, 2):
            if any("T16_PENDING" in value for value in row.values()):
                errors.append(f"{name}:{line}: unresolved T16_PENDING")
            if row.get("status") != "ACTIVE":
                errors.append(f"{name}:{line}: status must be ACTIVE")

    species_rows = _rows(root / "manifests/species_ids.csv")
    item_rows = _rows(root / "manifests/item_ids.csv")
    species = {row["species_key"] for row in species_rows}
    moves = {row["move_key"] for row in _rows(root / "manifests/move_ids.csv")}
    items = {row["item_key"] for row in item_rows}
    abilities = {row["ability_key"] for row in _rows(root / "manifests/ability_ids.csv")}
    flags = {row["flag_key"] for row in _rows(root / "manifests/flags.csv")}
    trainer_ids = {row["trainer_key"] for row in _rows(root / "manifests/trainer_ids.csv")}
    ai = {row["ai_profile_key"] for row in rows["trainer_ai_profiles.csv"]}
    if ai != {"AI_BASIC", "AI_SEMI_SMART", "AI_FULL_SMART"}:
        errors.append("trainer_ai_profiles.csv: exact BASIC/SEMI_SMART/FULL_SMART set required")

    support = _load_support(root, errors)
    map_rows = support["maps"]
    maps = {row["map_key"] for row in map_rows}
    logical = Counter(row["region"] for row in map_rows if row["logical_location_key"] != "VEGA_NATIVE")
    if logical != Counter({"TOHOKU": 49, "KANTO": 47}):
        errors.append(f"content/maps.csv: logical coverage mismatch {dict(logical)}")
    _unique(map_rows, ("map_key",), "content/maps.csv", errors)
    _unique(map_rows, ("region", "logical_location_key"), "content/maps.csv", errors)
    forbidden = {"GYM", "DUNGEON", "LEAGUE", "EVENT"}
    for line, row in enumerate(map_rows, 2):
        expected = "false" if row["map_kind"] in forbidden else "true"
        if row["field_pc_allowed"] != expected:
            errors.append(f"content/maps.csv:{line}: field_pc_allowed must be explicit {expected}")

    bindings = support["bindings"]
    _unique(bindings, ("map_key",), "content/map_bindings.csv", errors)
    if {row["map_key"] for row in bindings} != maps:
        errors.append("content/map_bindings.csv: every logical map must bind exactly once")
    physical_map_ids = {
        (row["map_key"], int(row["group_id"]), int(row["map_id"]))
        for row in _rows(root / "manifests/map_ids.csv")
    }
    audit = json.loads((root / "reports/generated/id_inventory.json").read_text(encoding="utf-8"))
    vega_physical = {(int(row["group"]), int(row["map"])) for row in audit["map_details"]}
    tohoku_nodes: set[tuple[int, int]] = set()
    for line, row in enumerate(bindings, 2):
        pair = (int(row["group_id"]), int(row["map_id"]))
        if row["region"] == "KANTO" and (row["physical_map_key"], *pair) not in physical_map_ids:
            errors.append(f"content/map_bindings.csv:{line}: unresolved Kanto physical map")
        if row["region"] == "TOHOKU" and pair not in vega_physical:
            errors.append(f"content/map_bindings.csv:{line}: unresolved Vega physical map")
        if row["region"] == "TOHOKU" and row["logical_location_key"] != "VEGA_NATIVE":
            if pair in tohoku_nodes:
                errors.append(f"content/map_bindings.csv:{line}: duplicate Tohoku physical binding")
            tohoku_nodes.add(pair)

    _party(rows["kanto_trainers.csv"], "kanto_trainers.csv", species, moves, items, abilities, ai, errors)
    _party(rows["tohoku_trainers.csv"], "tohoku_trainers.csv", species, moves, items, abilities, ai, errors)
    if len(rows["kanto_trainers.csv"]) != 78:
        errors.append("kanto_trainers.csv: expected Gym 48 + League 30 rows")
    for line, row in enumerate(rows["kanto_trainers.csv"], 2):
        level = int(row["level"])
        if not 68 <= level <= 100 or row["difficulty_policy"] != "FIXED_HIGH_LEVEL_OPTIONAL":
            errors.append(f"kanto_trainers.csv:{line}: fixed 68..100 optional policy violation")
    if len(rows["tohoku_trainers.csv"]) != 48:
        errors.append("tohoku_trainers.csv: expected eight registered six-mon rematch parties")
    all_trainers = {row["trainer_key"] for name in ("kanto_trainers.csv", "tohoku_trainers.csv") for row in rows[name]}

    rematches = rows["trainer_rematches.csv"]
    _check_refs(rematches, {"trainer_key": all_trainers, "ai_profile_key": ai}, "trainer_rematches.csv", errors)
    tiers = {
        "REMATCH_I": (58, 84, "VEGA_HALL_OF_FAME", "AI_SEMI_SMART", "NONE"),
        "REMATCH_II": (72, 94, "KANTO_CERT_4", "AI_FULL_SMART", "MEGA"),
        "REMATCH_III": (88, 100, "KANTO_LEAGUE_CLEAR", "AI_FULL_SMART", "ONE_OF_MEGA_Z_TERA"),
    }
    for line, row in enumerate(rematches, 2):
        if row["tier"] in tiers:
            expected = tiers[row["tier"]]
            actual = (int(row["level_min"]), int(row["level_max"]), row["unlock_key"],
                      row["ai_profile_key"], row["mechanic_policy"])
            if actual != expected or row["registered_only"] != "true":
                errors.append(f"trainer_rematches.csv:{line}: T15 rematch boundary mismatch")

    encounters = rows["kanto_encounters.csv"]
    if len(encounters) != 541 or len({row["evolution_chain_id"] for row in encounters}) != 541:
        errors.append("kanto_encounters.csv: exact 541-family coverage required")
    _check_refs(encounters, {"map_key": maps, "species_key": species, "item_key": items},
                "kanto_encounters.csv", errors)
    for line, row in enumerate(encounters, 2):
        low, high = int(row["level_min"]), int(row["level_max"])
        if not 68 <= low <= high <= 100 or row["difficulty_policy"] != "FIXED_HIGH_LEVEL_OPTIONAL":
            errors.append(f"kanto_encounters.csv:{line}: Kanto fixed level policy violation")

    research = rows["research_encounters.csv"]
    if len(research) != 1082 or Counter(row["region"] for row in research) != Counter({"TOHOKU": 541, "KANTO": 541}):
        errors.append("research_encounters.csv: expected 541 rows per region")
    research_chains = Counter(row["evolution_chain_id"] for row in research)
    if len(research_chains) != 541 or set(research_chains.values()) != {2}:
        errors.append("research_encounters.csv: each family must have two regional routes")
    _check_refs(research, {"map_key": maps, "species_key": species}, "research_encounters.csv", errors)
    for line, row in enumerate(research, 2):
        low, high = int(row["level_min"]), int(row["level_max"])
        if row["normal_preserved"] != "true" or not 1 <= low <= high <= 100:
            errors.append(f"research_encounters.csv:{line}: NORMAL/level contract violation")
        if row["region"] == "KANTO" and low < 68:
            errors.append(f"research_encounters.csv:{line}: Kanto RESEARCH below 68")

    raids = rows["raid_encounters.csv"]
    raid_shared = {row["shared_capture_key"] for row in raids}
    raid_shared_counts = Counter(row["shared_capture_key"] for row in raids)
    if len(raids) != 250 or len(raid_shared) != 125 or set(raid_shared_counts.values()) != {2}:
        errors.append("raid_encounters.csv: exact two-region rows for 125 shared captures required")
    _check_refs(raids, {"map_key": maps, "species_key": species}, "raid_encounters.csv", errors)
    for line, row in enumerate(raids, 2):
        if (row["unlock_key"] != "RAID_HIGH_UNLOCKED" or row["capture_policy"] != "SHARED_ONCE"
                or row["presentation_profile"] != "SIMPLE_EVENT" or row["dedicated_map"] != "false"
                or row["custom_ui"] != "false"):
            errors.append(f"raid_encounters.csv:{line}: high-raid/simple-event boundary violation")
    research_shared = Counter(row["shared_capture_key"] for row in research if row["shared_capture_key"] != "NONE")
    if not set(research_shared) <= raid_shared or set(research_shared.values()) != {2}:
        errors.append("research_encounters.csv: represented special-family keys must occur once per region")
    encounter_shared = {row["shared_capture_key"] for row in encounters if row["shared_capture_key"] != "NONE"}
    if encounter_shared != set(research_shared):
        errors.append("kanto_encounters.csv: represented special-family keys differ from research registry")

    placements = rows["kanto_items.csv"] + rows["tohoku_items.csv"]
    physical_maps = {row[0] for row in physical_map_ids}
    _check_refs(placements, {"map_key": maps | physical_maps, "item_key": items, "flag_key": flags}, "item placements", errors)
    placed = {row["item_key"] for row in placements}
    evolution = {
        row["item_key"] for row in item_rows
        if row["status"] != "RESERVED" and (row["is_evolution_item"] == "1" or row["is_evolution_stone"] == "1")
    }
    if not evolution <= placed:
        errors.append("item placements: unobtainable evolution items: " + ", ".join(sorted(evolution - placed)))

    qol = rows["qol_rewards.csv"]
    _check_refs(qol, {"item_key": items}, "qol_rewards.csv", errors)
    required_qol = {row["item_key"] for row in _rows(root / "content/qol_supply.csv") if row["item_key"] != "ITEM_KEY_NONE"}
    supplied = {row["item_key"] for row in qol}
    if not required_qol <= supplied:
        errors.append("qol_rewards.csv: required QOL supply missing: " + ", ".join(sorted(required_qol - supplied)))
    prices = {
        "ITEM_KEY_EXP_CANDY_XS": 1, "ITEM_KEY_EXP_CANDY_S": 2, "ITEM_KEY_FIRE_STONE": 3,
        "ITEM_KEY_EVERSTONE": 4, "ITEM_KEY_DESTINY_KNOT": 12, "ITEM_KEY_POWER_BRACER": 8,
        "ITEM_KEY_JOLLY_MINT": 8, "ITEM_KEY_ABILITY_CAPSULE": 16, "ITEM_KEY_EXP_CANDY_M": 4,
        "ITEM_KEY_CHOICE_BAND": 24, "ITEM_KEY_BOTTLE_CAP": 32, "ITEM_KEY_ABILITY_PATCH": 64,
        "ITEM_KEY_GOLD_BOTTLE_CAP": 128, "ITEM_KEY_EXP_CANDY_XL": 12,
    }
    for item, price in prices.items():
        matches = [row for row in qol if row["item_key"] == item and row["source_kind"] == "BP_SHOP" and int(row["price"]) == price]
        if not matches:
            errors.append(f"qol_rewards.csv: missing initial BP price {item}={price}")

    rentals = rows["facility_rentals.csv"]
    rental_keys = {row["rental_key"] for row in rentals}
    _check_refs(rentals, {
        "species_key": species, "item_key": items, "ability_key": abilities,
        "move1_key": moves, "move2_key": moves, "move3_key": moves, "move4_key": moves,
    }, "facility_rentals.csv", errors)
    for line, row in enumerate(rentals, 2):
        if int(row["level"]) != 50 or row["iv_policy"] != "ALL_31" or row["gmax_allowed"] != "false":
            errors.append(f"facility_rentals.csv:{line}: explicit Lv50/IV/Gmax contract violation")
    mix = [row for row in rentals if row["pool_key"] == "RENTAL_POOL_KEY_MIX"]
    weighted = Counter()
    for row in mix:
        weighted[row["origin_bucket"]] += int(row["weight"])
    total = sum(weighted.values())
    if total == 0 or {key: value * 100 // total for key, value in weighted.items()} != {"OFFICIAL": 70, "VEGA": 25, "SPECIAL": 5}:
        errors.append(f"facility_rentals.csv: Mix ratio mismatch {dict(weighted)}")
    for pool in ("BEGINNER", "INTERMEDIATE", "ADVANCED", "SPECIAL", "VEGA"):
        if sum(row["pool_key"] == f"RENTAL_POOL_KEY_{pool}" for row in rentals) != 6:
            errors.append(f"facility_rentals.csv: {pool} pool must contain six candidates")

    facility_trainers = rows["facility_trainers.csv"]
    _check_refs(facility_trainers, {**{f"rental_key{i}": rental_keys for i in range(1, 7)},
                                      "ai_profile_key": ai}, "facility_trainers.csv", errors)
    if len(rows["facility_modes.csv"]) != 20:
        errors.append("facility_modes.csv: 16 Factory formats plus four Mirage rounds required")
    mirage = [row for row in rows["facility_modes.csv"] if row["party_owner"] == "MIRAGE"]
    if len(mirage) != 4 or any(row["battle_count"] != "7" or row["level_policy"] != "LEVEL_100_FIXED"
                               or row["state_owner"] != "OWNER_KEY_MIRAGE_STATE" for row in mirage):
        errors.append("facility_modes.csv: Mirage must be four isolated Lv100 seven-battle rounds")
    for row in facility_trainers:
        if row["facility_trainer_key"] not in trainer_ids:
            errors.append(f"facility_trainers.csv: missing trainer ID {row['facility_trainer_key']}")

    facility_rewards = rows["facility_rewards.csv"]
    _check_refs(facility_rewards, {"item_key": items}, "facility_rewards.csv", errors)
    reward_by_key = {row["facility_reward_key"]: row for row in facility_rewards}
    trial = {
        "FACILITY_REWARD_KEY_TRIAL_XS": ("ITEM_KEY_EXP_CANDY_XS", "5"),
        "FACILITY_REWARD_KEY_TRIAL_S": ("ITEM_KEY_EXP_CANDY_S", "2"),
        "FACILITY_REWARD_KEY_TRIAL_BP": ("ITEM_KEY_NONE", "0"),
    }
    for key, (item, quantity) in trial.items():
        row = reward_by_key.get(key)
        if row is None or row["item_key"] != item or row["quantity"] != quantity:
            errors.append(f"facility_rewards.csv: invalid Trial first reward {key}")
    for streak in (3, 7, 14, 21, 49, 100):
        if f"FACILITY_REWARD_KEY_STREAK_{streak:03d}" not in reward_by_key:
            errors.append(f"facility_rewards.csv: missing streak {streak}")

    rewards = rows["reward_encounters.csv"]
    _check_refs(rewards, {"species_key": species}, "reward_encounters.csv", errors)
    if len(rewards) != 24 or Counter(row["tier"] for row in rewards) != Counter({"HABITAT": 6, "TYPE": 6, "RARE": 6, "RANDOM": 6}):
        errors.append("reward_encounters.csv: expected six rows in each of four tiers")
    raid_species = {row["species_key"] for row in raids}
    for line, row in enumerate(rewards, 2):
        if (row["species_key"] in raid_species or row["max_uncaught_rerolls"] != "10"
                or any(row[field] != "DISABLED" for field in ("exp_ev_money_policy", "item_theft_policy", "drop_policy", "chain_policy"))
                or row["presentation_profile"] != "SIMPLE_EVENT" or row["dedicated_map"] != "false"
                or row["full_screen_ui"] != "false"):
            errors.append(f"reward_encounters.csv:{line}: repeatable/simple-event exclusion violation")

    normal = support["normal"]
    if not normal or any(row["fallback_policy"] != "BYTE_EQUIVALENT_NORMAL" or row["status"] != "PRESERVED" for row in normal):
        errors.append("content/normal_table_protection.csv: all rooted NORMAL profiles must be preserved")
    constraints = support["constraints"]
    expected_aces = {"AYAME": (15, 15), "MIRU": (24, 24), "SHIOU": (30, 31),
                     "HISUI": (39, 40), "OUNI": (46, 47), "KARASUBA": (52, 53),
                     "RAPISURA": (57, 58), "NEW_ISLAND": (64, 65),
                     "LEAGUE_INITIAL": (69, 78), "GINNO": (79, 82)}
    constraint_by_key = {row["constraint_key"]: row for row in constraints}
    for name, bounds in expected_aces.items():
        row = constraint_by_key.get(f"TRAINER_CONSTRAINT_{name}")
        if row is None or (int(row["level_min"]), int(row["level_max"])) != bounds or row["global_scaling"] != "false":
            errors.append(f"content/trainer_balance_constraints.csv: invalid {name} ace contract")
    if any(int(row["max_batch_adjustment"]) > 3 or row["global_scaling"] != "false" for row in constraints):
        errors.append("content/trainer_balance_constraints.csv: global or >+3 scaling forbidden")
    activities = support["activities"]
    if any(row["status"] == "ACTIVE" and not row["completion_semantics"].endswith("_ONCE") for row in activities):
        errors.append("content/activity_hooks.csv: active hooks must award exactly once")
    if any(row["status"] == "DEFER" and row["reward_key"] != "NONE" for row in activities):
        errors.append("content/activity_hooks.csv: deferred hooks must not create supply")

    return errors


def collect_stage_errors(root: Path) -> list[str]:
    errors: list[str] = []
    paths = [root / "build/stages/16_content.gba", root / "build/stages/16_content.json",
             root / "build/stages/16_allocation.json", root / "generated/content/t16_content.bin"]
    if not all(path.is_file() for path in paths):
        return ["T16 ROM stage artifacts are incomplete"]
    rom = paths[0].read_bytes()
    metadata = json.loads(paths[1].read_text(encoding="utf-8"))
    allocation = json.loads(paths[2].read_text(encoding="utf-8"))
    payload = paths[3].read_bytes()
    if len(rom) != 32 * 1024 * 1024 or hashlib.sha256(rom).hexdigest() != metadata["output"]["sha256"]:
        errors.append("build/stages/16_content.gba: size/hash mismatch")
    if not payload.startswith(b"VEGA16\0\0") or hashlib.sha256(payload).hexdigest() != metadata["payload"]["sha256"]:
        errors.append("generated/content/t16_content.bin: magic/hash mismatch")
    start = int(metadata["payload"]["offset"])
    if rom[start:start + len(payload)] != payload:
        errors.append("build/stages/16_content.gba: embedded payload mismatch")
    stage09 = (root / "build/stages/09_species_surface.gba").read_bytes()
    if rom[:start] != stage09[:start] or rom[start + len(payload):] != stage09[start + len(payload):]:
        errors.append("build/stages/16_content.gba: bytes changed outside T16 allocation")
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        errors.append("build/stages/16_allocation.json: allocation overlap")
    return errors
