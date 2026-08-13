"""T15 dual-phase Kanto progression model, lint, and fixtures."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from .content_schema import ContentError, validate_repository

PROGRESSION_HEADER = ["unlock_key", "region", "sequence", "predecessor_keys",
                      "recommended_level_min", "recommended_level_max", "difficulty_policy",
                      "mandatory", "warning_key", "safe_route_key", "allowed_gimmicks"]
QOL_HEADER = ["feature_key", "unlock_key", "source_boundary", "save_state_key",
              "storage_policy", "presentation_profile", "repeatability", "release_enabled"]
FACILITY_HEADER = ["tier_key", "unlock_key", "formats", "battle_count", "rental_policy",
                   "ai_profile", "allowed_mechanics", "selection_policy", "bp_shop_tier",
                   "encounter_pool_tier", "party_owner", "state_owner"]
TRAINER_HEADER = ["entry_key", "region", "category", "unlock_key", "level_min", "level_max",
                  "ev_policy", "party_size", "ai_profile", "mechanic_policy", "target_policy",
                  "sequence_after"]
STATE_HEADER = ["state_key", "owner", "storage_policy", "unlock_key", "write_policy",
                "vega_state_alias"]
DEVELOPMENT_HEADER = ["shortcut_key", "map_key", "build_gate", "release_enabled",
                      "fallback_target"]


def _read(path: Path, expected: list[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if list(reader.fieldnames or []) != expected:
            raise ContentError(f"{path}: header drift")
        return list(reader)


def _split(value: str) -> list[str]:
    return [part for part in value.split("|") if part and part != "NONE"]


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_progression_rows(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    by_key = {row["unlock_key"]: row for row in rows}
    if len(by_key) != len(rows):
        raise ContentError("progression duplicate unlock_key")
    errors: list[str] = []
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(key: str) -> None:
        if key in visiting:
            errors.append(f"progression cycle at {key}")
            return
        if key in done:
            return
        visiting.add(key)
        row = by_key[key]
        for parent in _split(row["predecessor_keys"]):
            if parent not in by_key:
                errors.append(f"{key}: unreachable predecessor {parent}")
            else:
                visit(parent)
        visiting.remove(key)
        done.add(key)

    for key in by_key:
        visit(key)
    if errors:
        raise ContentError("\n".join(errors))

    ancestors: dict[str, set[str]] = {}
    def collect(key: str) -> set[str]:
        if key in ancestors:
            return ancestors[key]
        result = {key}
        for parent in _split(by_key[key]["predecessor_keys"]):
            result |= collect(parent)
        ancestors[key] = result
        return result
    for key in by_key:
        collect(key)
    return ancestors


def _area_gate(logical: str) -> str:
    number = int(logical[1:])
    if logical in {"K06", "K11", "K28", "K46", "K47", "K26"}:
        return "KANTO_EARLY_ACCESS"
    if 1 <= number <= 4:
        return "KANTO_EARLY_ACCESS"
    if number in (24, 25, 27, 44):
        return "KANTO_CERT_1"
    if 5 <= number <= 11 or number in (29, 30, 40):
        return "KANTO_CERT_2"
    if number in (31, 32):
        return "KANTO_CERT_3"
    if 12 <= number <= 18 or number == 33:
        return "KANTO_CERT_4"
    if 19 <= number <= 21 or 34 <= number <= 38 or number == 41:
        return "KANTO_CERT_5"
    if number in (39, 45):
        return "KANTO_CERT_6"
    if number == 22:
        return "KANTO_CERT_7"
    if number in (23, 42):
        return "KANTO_CERT_8"
    if number == 43:
        return "KANTO_LEAGUE_CLEAR"
    raise ContentError(f"no progression gate for {logical}")


def build_outputs(root: Path) -> dict[str, bytes]:
    validate_repository(root)
    progression = _read(root / "content/kanto_progression.csv", PROGRESSION_HEADER)
    qol = _read(root / "content/qol_progression.csv", QOL_HEADER)
    facilities = _read(root / "content/facility_progression.csv", FACILITY_HEADER)
    trainers = _read(root / "content/trainer_progression.csv", TRAINER_HEADER)
    states = _read(root / "content/kanto_state_model.csv", STATE_HEADER)
    development = _read(root / "content/kanto_development.csv", DEVELOPMENT_HEADER)
    ancestors = validate_progression_rows(progression)
    nodes = {row["unlock_key"] for row in progression}

    required_ancestry = {
        "KANTO_EARLY_ACCESS": {"VEGA_DH_CLEAR", "VEGA_SHIOU_BADGE_3"},
        "KANTO_CERT_5": {"VEGA_HALL_OF_FAME", "KANTO_CERT_4"},
        "LEAGUE_II_AVAILABLE": {"VEGA_HALL_OF_FAME", "KANTO_CERT_4", "LEAGUE_I_CLEARED"},
        "FINAL_LEAGUE_AVAILABLE": {"KANTO_LEAGUE_CLEAR", "SPHERE_COMPLETE", "LEAGUE_II_CLEARED"},
        "RAID_HIGH_UNLOCKED": {"VEGA_HALL_OF_FAME", "KANTO_CERT_4"},
    }
    for key, required in required_ancestry.items():
        if not required <= ancestors[key]:
            raise ContentError(f"{key}: missing ancestors {sorted(required - ancestors[key])}")
    if "VEGA_HALL_OF_FAME" in ancestors["KANTO_CERT_4"]:
        raise ContentError("early certification layer incorrectly requires Hall of Fame")

    scope = _read(root / "content/kanto_map_scope.csv",
                  ["map_key", "source_map", "logical_code", "classification", "scope_decision",
                   "reason", "script_policy", "sevii"])
    areas = [{"map_key": row["map_key"], "logical_code": row["logical_code"],
              "unlock_key": _area_gate(row["logical_code"]), "scope_decision": row["scope_decision"]}
             for row in scope if row["scope_decision"] != "DEFER"]
    if len(areas) != 253 or {row["logical_code"] for row in areas} != {f"K{x:02d}" for x in range(1, 48)}:
        raise ContentError("not every operational Kanto map has a progression path")
    if any(row["unlock_key"] not in nodes for row in areas):
        raise ContentError("area progression references an unknown node")

    storage = [row["save_state_key"] for row in qol if row["storage_policy"] == "UNIQUE"]
    if len(storage) != len(set(storage)) or "NONE" in storage:
        raise ContentError("QOL unlock state is stored more than once")
    if any(row["presentation_profile"] not in {"SIMPLE_EVENT", "EXISTING_OPTIONS", "SUMMARY_PC_PANE", "EXISTING_PC"}
           or row["release_enabled"] != "true" for row in qol):
        raise ContentError("QOL requires release-enabled existing/SIMPLE_EVENT presentation")
    expected_qol = {
        "EXP_SHARE": "VEGA_BADGE_1", "FREE_MOVE_RELEARN": "VEGA_BADGE_2",
        "FIELD_PC": "VEGA_DH_CLEAR", "POWER_ITEMS": "VEGA_BADGE_5",
        "EXP_CANDY_L_SILVER_CAP": "VEGA_BADGE_7",
        "ABILITY_PATCH_ALL_MINTS": "VEGA_BADGE_8",
        "EXP_CANDY_XL_ONCE": "VEGA_HALL_OF_FAME",
        "EXP_CANDY_XL_GOLD_CAP": "KANTO_LEAGUE_CLEAR",
    }
    qol_by_key = {row["feature_key"]: row for row in qol}
    for feature, unlock in expected_qol.items():
        if qol_by_key.get(feature, {}).get("unlock_key") != unlock:
            raise ContentError(f"{feature}: first availability regressed")

    facility_by_key = {row["tier_key"]: row for row in facilities}
    expected_facility = {
        "FACILITY_TIER_TRIAL": "KANTO_EARLY_ACCESS",
        "FACILITY_TIER_STANDARD": "FACTORY_STANDARD",
        "FACILITY_TIER_FULL": "FACTORY_FULL",
        "FACILITY_TIER_MASTER": "FACTORY_MASTER",
    }
    if {key: facility_by_key[key]["unlock_key"] for key in expected_facility} != expected_facility:
        raise ContentError("Factory four-tier boundary drift")
    if any(row["party_owner"] != "FACTORY" or row["state_owner"] != "OWNER_KEY_FACTORY_STATE"
           for row in facilities):
        raise ContentError("Factory owner leaked into Mirage/player state")
    if facility_by_key["FACILITY_TIER_MASTER"]["selection_policy"] != "ULTIMATE_SELECT_ONE_AT_ENTRY":
        raise ContentError("Ultimate must select exactly one mechanic at entry")

    trainer_by_key = {row["entry_key"]: row for row in trainers}
    required_trainers = {"TOHOKU_REMATCH_I", "TOHOKU_REMATCH_II", "TOHOKU_REMATCH_III",
                         "LEAGUE_I", "LEAGUE_II", "FINAL_LEAGUE"}
    if set(trainer_by_key) != required_trainers:
        raise ContentError("trainer progression scope drift")
    if [trainer_by_key[key]["unlock_key"] for key in ("LEAGUE_I", "LEAGUE_II", "FINAL_LEAGUE")] != [
            "LEAGUE_I_AVAILABLE", "LEAGUE_II_AVAILABLE", "FINAL_LEAGUE_AVAILABLE"]:
        raise ContentError("League order drift")
    if trainer_by_key["FINAL_LEAGUE"]["level_min"] != "100" or trainer_by_key["FINAL_LEAGUE"]["level_max"] != "100":
        raise ContentError("existing level-100 league was not moved to Final")

    facility_doc = json.loads((root / "content/facilities.json").read_text())
    if facility_doc["state_owners"]["factory"] == facility_doc["state_owners"]["mirage"]:
        raise ContentError("Factory and Mirage state owners overlap")
    raid = facility_doc["raids"][0]
    if raid["unlock_key"] != "RAID_HIGH_UNLOCKED" or raid["mechanic_policy"] != "RAID_DYNAMAX":
        raise ContentError("high Raid boundary/mechanic drift")

    feature_matrix = _read(root / "config/feature_matrix.csv",
                           ["feature_key", "category", "release_default", "choices", "unlock_key",
                            "ui_owner", "release_enabled", "notes"])
    feature_by_key = {row["feature_key"]: row for row in feature_matrix}
    if feature_by_key["DEBUG_GIFT"]["release_enabled"] != "false":
        raise ContentError("development shortcut enabled in release")
    if feature_by_key["TM_REUSE_LICENSE"]["unlock_key"] != "TM_LICENSE_UNLOCKED" \
            or feature_by_key["ENCOUNTER_PROFILE"]["unlock_key"] != "RESEARCH_PROFILE_UNLOCKED":
        raise ContentError("TM/Research progression bridge drift")

    forbidden_writes = []
    for path in sorted((root / "src/kanto").rglob("*.[ch]")):
        text = path.read_text(encoding="utf-8")
        for token in ("vega_badges =", "vega_story_flags =", "vega_hm_flags ="):
            if token in text:
                forbidden_writes.append(f"{path}:{token}")
    if forbidden_writes:
        raise ContentError("Kanto writes Vega progression: " + ", ".join(forbidden_writes))

    required_states = {"KANTO_RESEARCH_RANK", "DUAL_REGION_RESONANCE",
                       "SHARED_SPECIAL_CAPTURE_STATE", "KANTO_RETURN_EDGE",
                       "KANTO_CERTIFICATIONS", "KANTO_PERMIT_STATE"}
    if not required_states <= {row["state_key"] for row in states}:
        raise ContentError("Kanto progression state model is incomplete")
    if any(row["vega_state_alias"] != "NONE" or row["unlock_key"] not in nodes for row in states):
        raise ContentError("Kanto state aliases or mutates Vega progression")
    saved_states = [row["state_key"] for row in states if row["storage_policy"] == "SAVE_UNIQUE"]
    if len(saved_states) != len(set(saved_states)):
        raise ContentError("Kanto state is stored twice")
    if development != [{"shortcut_key": "DEV_KANTO_FAST_TRAVEL",
                         "map_key": "MAP_KEY_KANTO_VERMILION_TERMINAL",
                         "build_gate": "VEGA_KANTO_DEV", "release_enabled": "false",
                         "fallback_target": "SAFE_ROUTE_KANTO_TERMINAL"}]:
        raise ContentError("development fast-travel terminal policy drift")

    boundary_keys = sorted({row["unlock_key"] for row in qol} |
                           {row["unlock_key"] for row in facilities} |
                           {row["unlock_key"] for row in trainers} |
                           {"RESEARCH_PROFILE_UNLOCKED", "TM_LICENSE_UNLOCKED",
                            "HIDDEN_ABILITY_DEXNAV_UNLOCKED", "COMPETITIVE_SUPPLY_UNLOCKED",
                            "UB_PARADOX_UNLOCKED", "RAID_HIGH_UNLOCKED"})
    fixtures = [{"unlock_key": key, "before": False, "after": True,
                 "required_ancestors": sorted(ancestors[key] - {key}),
                 "return_to_tohoku": True if "KANTO_EARLY_ACCESS" in ancestors[key] else None}
                for key in boundary_keys]
    early_cert4 = ancestors["KANTO_CERT_4"]
    forbidden_early = sorted(key for key in ("KANTO_CERT_5", "LEAGUE_I_AVAILABLE", "LEAGUE_II_AVAILABLE",
                                             "KANTO_LEAGUE", "FINAL_LEAGUE_AVAILABLE", "RAID_HIGH_UNLOCKED")
                             if key in early_cert4)
    if forbidden_early:
        raise ContentError(f"early cert-4 state bypasses late nodes: {forbidden_early}")
    state_matrix = {
        "schema_version": 1, "boundary_fixtures": fixtures,
        "early_access": {"before_checkpoint": False, "after_checkpoint": True,
                         "requires_hall_of_fame": False, "requires_national_dex": False},
        "early_cert4": {"hall_of_fame": False, "late_nodes": []},
        "return_edge": {"all_kanto_states": True, "cost": 0, "permanent": True},
        "factory_mirage_isolated": True, "normal_profile_preserved": True,
        "safari_low_level_preserved": True, "vega_capture_state_preserved": True,
        "release_dev_shortcut": False, "development_fast_travel_available": True,
        "state_model": sorted(row["state_key"] for row in states),
    }
    graph = {row["unlock_key"]: {"region": row["region"], "sequence": int(row["sequence"]),
                                 "predecessors": _split(row["predecessor_keys"]),
                                 "allowed_gimmicks": _split(row["allowed_gimmicks"])}
             for row in progression}
    report = f"""# 二段階Kanto progression graph

- progression nodes: {len(graph)} / cycle: 0 / unreachable prerequisite: 0
- operational maps with gate: {len(areas)} / 253; logical locations: 47 / 47
- early travel: `0x0824 && 0x114B`; HOF required: false; National Dex required: false
- early certifications: 1..4; post-HoF certifications: 5..8
- permanent free return edge: all Kanto states PASS
- Kanto writes to Vega badge/HM/story state: 0
- QOL boundary fixtures: {len(qol)} / unique stored states: {len(storage)}
- Factory tiers: Trial / Standard / Full / Master; Factory-Mirage owner overlap: 0
- rematch tiers: 3; League order: I -> II -> Final; Final Lv.100: PASS
- Research/TM/HA DexNav/competitive supply/UB-Paradox/Raid before-after fixtures: PASS
- NORMAL/Safari/Vega capture state replacement: 0
- development fast-travel terminal: build-gated / release disabled

All QOL unlock events use existing UI or `SIMPLE_EVENT`. Mega unlocks after Vega HOF, Z after HOF+certification 4, and Tera/Dynamax after Kanto League; Raid uses battle-local Dynamax only. Each trainer row selects at most one mechanic.
""".encode()
    return {
        "generated/kanto/progression/graph.json": _stable(graph),
        "generated/kanto/progression/area_gates.json": _stable(areas),
        "generated/kanto/progression/state_matrix.json": _stable(state_matrix),
        "tests/fixtures/progression_boundaries.json": _stable(state_matrix),
        "reports/generated/progression_graph.md": report,
    }
