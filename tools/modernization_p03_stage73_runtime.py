#!/usr/bin/env python3
"""Stage73 P03 conditional/shared/carry/reminder/form consumer runtime builder."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_learnsets import iter_compiled_p03_routes
from tools.release.bps import apply_bps, create_bps
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P03-STAGE73-CONSUMER-RUNTIME"
PREFLIGHT_TASK = "USER-MODERNIZATION-P03-STAGE73-CONSUMER-PREFLIGHT"
STAGE = 73
ROM_SIZE = 32 * 1024 * 1024
SPECIES_COUNT = 1621
MOVE_LAST = 1062
SIDE_CHANGE_MOVE_ID = 1063
CANONICAL_PICHU_SPECIES = 24
LIGHT_BALL_ITEM = 202
VOLT_TACKLE_MOVE = 344
VOLT_TACKLE_BUILD_IMMEDIATE = 172
CONSUMERS = ("egg", "shared_egg", "pre_evolution_carry", "reminder", "form_change")
EXACT_EGG_SPECIES = frozenset({203, 324, 364, 608, 719, 724, 727})
ROTOM_SIGNATURE_MOVES = {894: 315, 895: 56, 896: 59, 897: 373, 898: 401}
FIXED_FORM_SPECIES = frozenset({1260, 1261, 1386, 1387})
DEFAULT_CONFIG = Path("config/modernization_p03_stage73_runtime.json")
PROVISIONAL_LOAD_ADDRESS = 0x09500000
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class ModernizationP03Stage73RuntimeError(ValueError):
    """Stage73 input identity、consumer境界、ABI、allocation違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage73RuntimeError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}がboolです")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _rom_offset(address: int, width: int, label: str) -> int:
    offset = address - GBA_ROM_BASE
    if width < 0 or not 0 <= offset <= ROM_SIZE - width:
        _fail(f"{label}がROM範囲外です: 0x{address:08X}+{width}")
    return offset


def existing_light_ball_owner_evidence() -> dict[str, Any]:
    """Stage72 BuildEggMovesetに残るconditional routeの命令契約。"""

    return {
        "source_route_count": 1,
        "canonical_species": CANONICAL_PICHU_SPECIES,
        "light_ball_item": LIGHT_BALL_ITEM,
        "volt_tackle_move": VOLT_TACKLE_MOVE,
        "runtime_owner": "PARENT_BUILD_EGG_MOVESET",
        "parent_function_entry": "0x090EA930",
        "instruction_evidence": {
            "egg_species_load": {
                "address": "0x090EA946", "hex": "048c",
                "instruction": "ldrh r4,[r0,#32]",
            },
            "egg_species_stack_store": {
                "address": "0x090EA94E", "hex": "0694",
                "instruction": "str r4,[sp,#24]",
            },
            "canonical_species_compare": {
                "address": "0x090EAA74", "hex": "069b182b46d0",
                "instructions": "ldr r3,[sp,#24]; cmp r3,#24; beq conditional block",
            },
            "light_ball_compares": [
                {"address": "0x090EAB14", "hex": "ca2807d0", "instruction": "cmp r0,#202; beq"},
                {"address": "0x090EAB24", "hex": "ca28a8d1", "instruction": "cmp r0,#202; bne exit"},
            ],
            "volt_tackle_build": {
                "address": "0x090EAB28", "hex": "ac21124b05984900",
                "instructions": "movs r1,#172; lsls r1,r1,#1",
                "immediate": VOLT_TACKLE_BUILD_IMMEDIATE,
                "shift": 1,
                "result": VOLT_TACKLE_MOVE,
            },
        },
    }


def verify_existing_light_ball_owner(parent: bytes) -> dict[str, Any]:
    """親ROMのPichu/Light Ball/Volt Tackle ownerをexact byteで確認する。"""

    evidence = existing_light_ball_owner_evidence()
    rows = evidence["instruction_evidence"]
    checks = [
        rows["egg_species_load"],
        rows["egg_species_stack_store"],
        rows["canonical_species_compare"],
        *rows["light_ball_compares"],
        rows["volt_tackle_build"],
    ]
    for row in checks:
        expected = bytes.fromhex(row["hex"])
        offset = _rom_offset(int(row["address"], 0), len(expected), "Light Ball owner evidence")
        if parent[offset:offset + len(expected)] != expected:
            _fail(f"Stage72 Light Ball owner命令不一致: {row['address']}")
    move_build = rows["volt_tackle_build"]
    if move_build["immediate"] << move_build["shift"] != move_build["result"]:
        _fail("Stage72 Volt Tackle Move ID命令解釈不一致")
    return evidence


def _fixed_raw(root: Path, contract: Mapping[str, Any], label: str) -> bytes:
    relative = contract.get("path")
    expected_size = contract.get("size")
    expected_sha = contract.get("sha256")
    if not isinstance(relative, str) or not relative or not isinstance(expected_sha, str):
        _fail(f"{label} contractが不正です")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が固定通常fileではありません: {path}")
    raw = path.read_bytes()
    if expected_size is not None and len(raw) != _integer(expected_size, f"{label}.size"):
        _fail(f"{label} size不一致: {len(raw)} != {expected_size}")
    if not _SHA_RE.fullmatch(expected_sha) or sha256(raw) != expected_sha:
        _fail(f"{label} SHA-256不一致: {sha256(raw)} != {expected_sha}")
    return raw


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label} JSON不正: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"Stage73 configが固定通常fileではありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"Stage73 configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("Stage73 config rootがobjectではありません")
    if (value.get("schema_version"), value.get("task"), value.get("stage")) != (
        SCHEMA_VERSION, TASK, STAGE,
    ):
        _fail("Stage73 config schema/task/stage不一致")
    if value.get("status") not in {"PARENT_PENDING_FAIL_CLOSED", "STAGE72_IDENTITY_PINNED"}:
        _fail("Stage73 config status不一致")
    runtime = value.get("runtime", {})
    if (
        runtime.get("species_count") != SPECIES_COUNT
        or runtime.get("move_count") != MOVE_LAST + 1
        or runtime.get("candidate_capacity") != 40
    ):
        _fail("Stage73 species/move ABI不一致")
    if runtime.get("side_change_project_move_id") != SIDE_CHANGE_MOVE_ID:
        _fail("Side Change除外ID不一致")
    if runtime.get("exact_egg_species") != sorted(EXACT_EGG_SPECIES):
        _fail("exact egg species集合不一致")
    if runtime.get("prohibited_species_keys") != [
        "SPECIES_KEY_BROWT", "SPECIES_KEY_POMBON", "SPECIES_KEY_GECQUA",
    ]:
        _fail("Browt/Pombon/Gecqua除外契約不一致")
    if runtime.get("prohibited_coercions") != [
        "SHARED_EGG_TO_NORMAL_EGG_TABLE",
        "PRE_EVOLUTION_CARRY_TO_TARGET_LEVEL_OR_EGG",
        "FORM_CHANGE_TO_TARGET_LEVEL_OR_EGG",
        "REMINDER_TO_LEVEL_ZERO",
        "SPECIAL_BREEDING_TO_UNCONDITIONAL_EGG",
    ]:
        _fail("consumer coercion禁止契約不一致")
    if {int(key): value for key, value in runtime.get("rotom_signature_moves", {}).items()} != ROTOM_SIGNATURE_MOVES:
        _fail("Rotom signature Move対応不一致")
    contract = value.get("consumer_contract", {})
    expected_consumer_contract = {
        "accounted_route_count": 40570,
        "new_runtime_materialized_route_count": 5363,
        "existing_owner_accounted_route_count": 35207,
        "conditional_egg": {"routes": 41, "exact_rows": 40, "existing_light_ball_owner": 1},
        "shared_egg": {"routes": 5023, "consumer": "MOVE_MEMORY_MIRROR_HERB_DISTINCT_TABLE"},
        "pre_evolution_carry": {"routes": 35141, "consumer": "EXISTING_FOUR_MOVE_SLOT_PERSISTENCE"},
        "reminder": {"routes": 295, "consumer": "MOVE_MEMORY_NORMAL_MODE_DEDICATED_TABLE"},
        "form_change": {"routes": 70, "generic_carry": 61, "existing_fixed_transition": 4, "rotom_runtime": 5},
        "remaining_full_p03_routes": {"machine": 26279, "tutor": 369, "total": 26648},
        "completion_claim": "FIVE_GROUP_CONSUMER_BOUNDARY_CHECKPOINT_NOT_FULL_P03",
    }
    if contract != expected_consumer_contract:
        _fail("consumer completion claim境界不一致")
    parent_abi = value.get("parent_abi", {})
    hooks = parent_abi.get("hooks")
    expected_hooks = [
        {"name": "GetAllEggMoves", "address": "0x090EB970", "width": 12, "target": "Stage73_GetAllEggMoves", "parent_hex": "f0b5de4657464e464546e0b5"},
        {"name": "VegaMoveMemory_GetMoveRelearnerMoves", "address": "0x091141D4", "width": 8, "target": "Stage73_GetMoveRelearnerMoves", "parent_hex": "004b184745012d09"},
        {"name": "CollectionSupply_ApplySelectedForm", "address": "0x09405BD4", "width": 8, "target": "Stage73_CollectionApplySelectedForm", "parent_hex": "10b5064b5889064b"},
    ]
    if hooks != expected_hooks:
        _fail("Stage73 hook exact ABI不一致")
    occupied: list[tuple[int, int, str]] = []
    for row in hooks:
        address = _integer(row.get("address"), "hook.address")
        width = _integer(row.get("width"), "hook.width")
        try:
            preimage = bytes.fromhex(str(row.get("parent_hex")))
        except ValueError:
            _fail(f"hook preimage hex不正: {row.get('name')}")
        if width not in {8, 12} or len(preimage) != width:
            _fail(f"hook width/preimage不一致: {row.get('name')}")
        start = _rom_offset(address, width, f"hook {row.get('name')}")
        occupied.append((start, start + width, str(row.get("name"))))
    for left, right in zip(sorted(occupied), sorted(occupied)[1:]):
        if right[0] < left[1]:
            _fail(f"hook重複: {left[2]} / {right[2]}")
    collection_abi = parent_abi.get("collection_form_service", {})
    expected_collection_abi = {
        "entry": "0x09405BD5", "continuation_after_8_byte_prologue": "0x09405BDD",
        "state": "0x0203F720", "last_result_offset": 8, "pending_index_offset": 10,
        "test_mode_offset": 27, "try_saving_data": "0x093789E5",
        "get_mon_data": "0x0803F355", "set_mon_data": "0x0803FA71",
        "set_mon_move_slot": "0x09114699", "remove_mon_pp_bonus": "0x08040755",
        "shift_move_slot": "0x080C0C79",
    }
    if collection_abi != expected_collection_abi:
        _fail("Collection form service ABI pin不一致")
    return value


def require_pinned_parent(config: Mapping[str, Any]) -> None:
    parent = config.get("parent_identity", {})
    missing: list[str] = []
    if config.get("status") != "STAGE72_IDENTITY_PINNED":
        missing.append("status")
    commit = parent.get("stage72_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        missing.append("stage72_commit")
    for name in ("rom", "metadata", "allocation", "checkpoint"):
        row = parent.get(name)
        if not isinstance(row, dict):
            missing.append(name)
            continue
        if (
            not isinstance(row.get("path"), str)
            or not isinstance(row.get("size"), int)
            or not isinstance(row.get("sha256"), str)
            or not _SHA_RE.fullmatch(row["sha256"])
        ):
            missing.append(name)
    if parent.get("policy") != "FAIL_CLOSED_UNTIL_EXACT_STAGE72_COMMIT_AND_FOUR_ARTIFACT_IDENTITIES_ARE_PINNED":
        missing.append("policy")
    if missing:
        _fail("Stage72 identity未確定のためROM工程を拒否: " + ", ".join(missing))


class FramedDigest:
    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self.count = 0

    def add(self, value: Any) -> None:
        raw = stable_json(value)
        self._digest.update(len(raw).to_bytes(8, "big"))
        self._digest.update(raw)
        self.count += 1

    def hexdigest(self) -> str:
        return self._digest.hexdigest()


def _counter(value: Counter[str]) -> dict[str, int]:
    return dict(sorted(value.items()))


def _assert_mapping(actual: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            _fail(f"{label}.{key}不一致: {actual.get(key)!r} != {expected_value!r}")


@dataclass(frozen=True)
class RouteModel:
    shared_rows: dict[int, tuple[int, ...]]
    reminder_rows: dict[int, tuple[int, ...]]
    exact_egg_rows: dict[int, tuple[int, ...]]
    direct_egg_rows: dict[int, tuple[int, ...]]
    shared_legacy_source_species: dict[int, tuple[int, ...]]
    route_audit: dict[str, Any]


def compile_route_model(root: Path, config: Mapping[str, Any]) -> RouteModel:
    """固定ZIPを一度だけstreamしてStage73の3表と全5群監査を作る。"""

    root = root.resolve()
    preflight = _json(
        _fixed_raw(root, config["inputs"]["consumer_preflight"], "Stage73 preflight config"),
        "Stage73 preflight config",
    )
    if (preflight.get("schema_version"), preflight.get("task"), preflight.get("stage")) != (
        1, PREFLIGHT_TASK, 73,
    ):
        _fail("preflight schema/task/stage不一致")
    preflight_inputs = preflight.get("inputs", {})
    contract = _json(_fixed_raw(root, preflight_inputs["p03_contract"], "P03 contract"), "P03 contract")
    zip_row = preflight_inputs["learnsets_zip"]
    _fixed_raw(root, zip_row, "P03 learnsets ZIP")
    learnsets_zip = root / zip_row["path"]

    source_counts: Counter[str] = Counter()
    selected_counts: Counter[str] = Counter()
    excluded_counts: Counter[str] = Counter()
    source_digests = {name: FramedDigest() for name in CONSUMERS}
    selected_digests = {name: FramedDigest() for name in CONSUMERS}
    targets = {name: set() for name in CONSUMERS}
    rows: dict[str, dict[int, list[int]]] = {
        "shared_egg": defaultdict(list),
        "reminder": defaultdict(list),
        "exact_egg": defaultdict(list),
        "direct_egg": defaultdict(list),
    }
    level_pairs: set[tuple[int, int]] = set()
    egg_pairs: set[tuple[int, int]] = set()
    shared_pairs: set[tuple[int, int]] = set()
    reminder_pairs: set[tuple[int, int]] = set()
    carry_pairs: set[tuple[int, int]] = set()
    form_pairs: set[tuple[int, int]] = set()
    direct_form_pairs: set[tuple[int, int]] = set()
    egg_boundary: Counter[str] = Counter()
    shared_games: Counter[str] = Counter()
    shared_basis: Counter[str] = Counter()
    shared_resolution: Counter[str] = Counter()
    carry_methods: Counter[str] = Counter()
    form_methods: Counter[str] = Counter()
    form_kinds: Counter[str] = Counter()
    global_count = 0
    global_side_change = 0
    prohibited_species_routes = 0
    existing_light_ball_routes = 0
    prohibited_species_keys = set(config["runtime"]["prohibited_species_keys"])
    reference_species: dict[str, set[int]] = defaultdict(set)
    shared_source_references: dict[int, set[str]] = defaultdict(set)

    for row in iter_compiled_p03_routes(root, learnsets_zip):
        global_count += 1
        consumer = str(row["consumer"])
        source = row["source_route"]
        species = int(row["target_species_id"])
        move = int(source["project_move_id"])
        pair = (species, move)
        reference_id = str(row["reference_id"])
        reference_species[reference_id].add(species)
        if row.get("target_species_key") in prohibited_species_keys:
            prohibited_species_routes += 1
        if consumer in CONSUMERS:
            source_counts[consumer] += 1
            source_digests[consumer].add(row)
        if move == SIDE_CHANGE_MOVE_ID:
            global_side_change += 1
            if consumer in CONSUMERS:
                excluded_counts[consumer] += 1
            continue
        if row.get("runtime_move_ready") is not True or not 1 <= move <= MOVE_LAST:
            _fail(f"選択routeのruntime Move境界不一致: {consumer}/{species}/{move}")
        if consumer == "level_up":
            level_pairs.add(pair)
            continue
        if consumer not in CONSUMERS:
            continue
        selected_counts[consumer] += 1
        selected_digests[consumer].add({**row, "selection_status": "ADOPTED_FOR_RUNTIME"})
        targets[consumer].add(species)
        method = str(source["method"])
        if consumer == "egg":
            if method == "special_breeding":
                if pair != (CANONICAL_PICHU_SPECIES, VOLT_TACKLE_MOVE):
                    _fail(f"未知のspecial breeding route: {pair}")
                existing_light_ball_routes += 1
                egg_boundary["special_breeding_existing_owner"] += 1
            else:
                egg_pairs.add(pair)
                rows["direct_egg"][species].append(move)
                if species in EXACT_EGG_SPECIES:
                    rows["exact_egg"][species].append(move)
                    if species in {203, 324}:
                        egg_boundary["legacy_alias_conflict"] += 1
                    else:
                        egg_boundary["incense_union_conflict"] += 1
        elif consumer == "shared_egg":
            if pair in shared_pairs:
                _fail(f"shared egg pair重複: {pair}")
            shared_pairs.add(pair)
            rows["shared_egg"][species].append(move)
            shared_games[str(source["source_game"])] += 1
            shared_basis[str(source["shared_egg_receiver_basis"])] += 1
            shared_resolution[str(source["shared_egg_resolution"])] += 1
            shared_source_references[species].add(
                f"{source['source_game']}:{source['shared_egg_source_key']}"
            )
        elif consumer == "reminder":
            if pair in reminder_pairs:
                _fail(f"reminder pair重複: {pair}")
            reminder_pairs.add(pair)
            rows["reminder"][species].append(move)
        elif consumer == "pre_evolution_carry":
            carry_pairs.add(pair)
            carry_methods[method] += 1
            if row.get("runtime_supply", {}).get("status") != "CARRY_ONLY_NO_TARGET_DIRECT_BIT":
                _fail(f"carry-only supply境界不一致: {species}/{move}")
        else:
            form_pairs.add(pair)
            form_methods[method] += 1
            kind = str(source["route_kind"])
            form_kinds[kind] += 1
            if kind == "form_change":
                if row.get("runtime_supply", {}).get("status") != "CARRY_ONLY_NO_TARGET_DIRECT_BIT":
                    _fail(f"form carry-only supply境界不一致: {species}/{move}")
            elif kind != "direct" or species not in set(ROTOM_SIGNATURE_MOVES) | set(FIXED_FORM_SPECIES):
                _fail(f"未知のdirect form owner: {species}/{move}/{kind}")
            else:
                direct_form_pairs.add(pair)

    expected_groups = preflight["consumer_groups"]
    contract_source = contract["corrected_adoption"]["consumers"]
    contract_selected = contract["runtime_selection"]["consumers"]
    group_base: dict[str, dict[str, Any]] = {}
    for name in CONSUMERS:
        base = {
            "source_count": source_counts[name],
            "source_group_sha256": source_digests[name].hexdigest(),
            "selected_count": selected_counts[name],
            "selected_group_sha256": selected_digests[name].hexdigest(),
        }
        _assert_mapping(base, {key: expected_groups[name][key] for key in base}, name)
        if contract_source[name] != {"count": base["source_count"], "content_sha256": base["source_group_sha256"]}:
            _fail(f"{name} source digestがP03 contractと不一致")
        if contract_selected[name] != {"count": base["selected_count"], "content_sha256": base["selected_group_sha256"]}:
            _fail(f"{name} selected digestがP03 contractと不一致")
        group_base[name] = base

    egg_actual = {
        **group_base["egg"],
        "stage73_scope_count": sum(egg_boundary.values()),
        **_counter(egg_boundary),
        "special_breeding_owner": "PARENT_BUILD_EGG_MOVESET_CANONICAL_PICHU_LIGHT_BALL",
        "exact_override_pending_runtime_hook": len([pair for pair in egg_pairs if pair[0] in EXACT_EGG_SPECIES]),
    }
    shared_actual = {
        **group_base["shared_egg"],
        "target_count": len(targets["shared_egg"]),
        "unique_species_move_pairs": len(shared_pairs),
        "direct_egg_overlap": len(shared_pairs & egg_pairs),
        "shared_only": len(shared_pairs - egg_pairs),
        "source_games": _counter(shared_games),
        "receiver_basis": _counter(shared_basis),
        "resolution": _counter(shared_resolution),
    }
    carry_supply = sum(carry_methods[name] for name in ("tm", "tr", "tutor"))
    carry_actual = {
        **group_base["pre_evolution_carry"],
        "target_count": len(targets["pre_evolution_carry"]),
        "unique_species_move_pairs": len(carry_pairs),
        "duplicate_route_paths": selected_counts["pre_evolution_carry"] - len(carry_pairs),
        "methods": _counter(carry_methods),
        "existing_generic_move_slot_persistence_semantics": selected_counts["pre_evolution_carry"],
        "machine_tutor_upstream_supply_dependency": carry_supply,
        "other_source_owner_dependency": selected_counts["pre_evolution_carry"] - carry_supply,
        "new_runtime_materialized_count": 0,
    }
    reminder_actual = {
        **group_base["reminder"],
        "target_count": len(targets["reminder"]),
        "unique_species_move_pairs": len(reminder_pairs),
        "direct_level_up_overlap": len(reminder_pairs & level_pairs),
        "pending_dedicated_runtime_table": len(reminder_pairs),
    }
    form_actual = {
        **group_base["form_change"],
        "target_count": len(targets["form_change"]),
        "unique_species_move_pairs": len(form_pairs),
        "duplicate_route_paths": selected_counts["form_change"] - len(form_pairs),
        "route_kinds": _counter(form_kinds),
        "methods": _counter(form_methods),
        "existing_generic_carry_owner": form_kinds["form_change"],
        "existing_fixed_transition_owner": 4,
        "rotom_transition_owner_missing": 5,
        "machine_upstream_supply_dependency": form_methods["tm"],
        "new_runtime_materialized_count": 0,
    }
    actual_groups = {
        "egg": egg_actual,
        "shared_egg": shared_actual,
        "pre_evolution_carry": carry_actual,
        "reminder": reminder_actual,
        "form_change": form_actual,
    }
    for name, actual in actual_groups.items():
        _assert_mapping(actual, expected_groups[name], name)

    boundary = {
        "five_group_source_count": sum(source_counts.values()),
        "five_group_selected_count": (
            egg_actual["stage73_scope_count"]
            + selected_counts["shared_egg"]
            + selected_counts["pre_evolution_carry"]
            + selected_counts["reminder"]
            + selected_counts["form_change"]
        ),
        "side_change_project_move_id": SIDE_CHANGE_MOVE_ID,
        "side_change_global_excluded_count": global_side_change,
        "side_change_five_group_excluded_count": sum(excluded_counts.values()),
        "browt_pombon_gecqua_adopted_count": 0,
    }
    _assert_mapping(boundary, preflight["selection_boundary"], "selection_boundary")
    if global_count != 118528:
        _fail(f"全P03 route件数不一致: {global_count}")
    if prohibited_species_routes:
        _fail(f"Browt/Pombon/Gecqua route混入: {prohibited_species_routes}")
    if sum(len(value) for value in rows["exact_egg"].values()) != 40:
        _fail("exact conditional egg rowが40ではありません")
    if set(rows["exact_egg"]) != EXACT_EGG_SPECIES:
        _fail("exact conditional egg target集合不一致")
    if sum(len(value) for value in rows["shared_egg"].values()) != 5023:
        _fail("shared egg rowが5,023ではありません")
    if sum(len(value) for value in rows["reminder"].values()) != 295:
        _fail("reminder rowが295ではありません")
    expected_direct_form_pairs = set(ROTOM_SIGNATURE_MOVES.items()) | {
        (1260, 690), (1261, 669), (1386, 768), (1387, 769),
    }
    if direct_form_pairs != expected_direct_form_pairs:
        _fail(f"direct form species/Move pair不一致: {sorted(direct_form_pairs)}")
    if max(map(len, rows["shared_egg"].values())) > 15 or max(map(len, rows["reminder"].values())) > 17:
        _fail("Stage73 candidate tableの監査済みspecies最大行数を超えました")

    frozen_rows = {
        name: {species: tuple(moves) for species, moves in sorted(table.items())}
        for name, table in rows.items()
    }
    shared_legacy_sources: dict[int, tuple[int, ...]] = {}
    unresolved_shared_sources: dict[int, list[str]] = {}
    for species, references in sorted(shared_source_references.items()):
        resolved = {
            candidate
            for value in references if value in reference_species
            for candidate in reference_species[value]
        }
        missing = sorted(value for value in references if value not in reference_species)
        if resolved:
            # Some Vega aliases intentionally share one official reference.
            # Audit every candidate plus the concrete runtime target.
            shared_legacy_sources[species] = tuple(sorted(resolved | {species}))
        elif missing:
            # One audited battle-only source form has no adopted out-of-battle row.
            shared_legacy_sources[species] = (species,)
            unresolved_shared_sources[species] = missing
        else:
            _fail(f"shared egg legacy source欠落: {species}")
    if unresolved_shared_sources != {1263: ["scarletviolet:0744.01"]}:
        _fail(f"shared egg unresolved source集合不一致: {unresolved_shared_sources}")
    if existing_light_ball_routes != 1:
        _fail(f"existing Pichu Light Ball route件数不一致: {existing_light_ball_routes}")
    materialized_breakdown = {
        "conditional_exact_egg": 40,
        "shared_egg": 5023,
        "reminder": 295,
        "rotom_form_change": 5,
    }
    existing_owner_breakdown = {
        "conditional_light_ball_build_egg_moveset": existing_light_ball_routes,
        "pre_evolution_four_move_slot_persistence": 35141,
        "form_change_four_move_slot_persistence": 61,
        "fixed_form_transition": 4,
    }
    if sum(materialized_breakdown.values()) != config["consumer_contract"]["new_runtime_materialized_route_count"]:
        _fail("Stage73 materialized route内訳不一致")
    if sum(existing_owner_breakdown.values()) != config["consumer_contract"]["existing_owner_accounted_route_count"]:
        _fail("Stage73 existing owner route内訳不一致")
    route_audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS_FIVE_GROUP_ROUTE_BOUNDARY",
        "source_route_count": global_count,
        "consumer_groups": actual_groups,
        "selection_boundary": boundary,
        "serialization_inputs": {
            "shared_egg_species": len(frozen_rows["shared_egg"]),
            "shared_egg_rows": 5023,
            "reminder_species": len(frozen_rows["reminder"]),
            "reminder_rows": 295,
            "conditional_exact_egg_species": len(frozen_rows["exact_egg"]),
            "conditional_exact_egg_rows": 40,
            "shared_legacy_source_targets_resolved": len(shared_legacy_sources) - len(unresolved_shared_sources),
            "shared_battle_only_source_fallbacks": unresolved_shared_sources,
        },
        "accounting": {
            "new_runtime_materialized_routes": sum(materialized_breakdown.values()),
            "new_runtime_materialized_breakdown": materialized_breakdown,
            "existing_owner_accounted_routes": sum(existing_owner_breakdown.values()),
            "existing_owner_accounted_breakdown": existing_owner_breakdown,
            "consumer_boundary_accounted_routes": 40570,
            "machine_tutor_upstream_supply_dependency": carry_supply + form_methods["tm"],
        },
        "conditional_breeding_existing_owner_evidence": existing_light_ball_owner_evidence(),
        "claim": "FIVE_GROUP_CONSUMER_BOUNDARY_CHECKPOINT_NOT_FULL_P03",
        "remaining_full_p03_routes": config["consumer_contract"]["remaining_full_p03_routes"],
        "prohibited_coercions_materialized": 0,
        "side_change_materialized": 0,
        "browt_pombon_gecqua_source_routes": prohibited_species_routes,
        "browt_pombon_gecqua_materialized": 0,
    }
    if route_audit["accounting"]["machine_tutor_upstream_supply_dependency"] != 23595:
        _fail("carry/form upstream supply dependency合計不一致")
    return RouteModel(
        shared_rows=frozen_rows["shared_egg"],
        reminder_rows=frozen_rows["reminder"],
        exact_egg_rows=frozen_rows["exact_egg"],
        direct_egg_rows=frozen_rows["direct_egg"],
        shared_legacy_source_species=shared_legacy_sources,
        route_audit=route_audit,
    )


@dataclass(frozen=True)
class IndexedMoveTable:
    index: bytes
    moves: bytes
    species_count: int
    move_count: int
    max_per_species: int


def build_indexed_table(rows: Mapping[int, Sequence[int]], label: str) -> IndexedMoveTable:
    offsets: list[int] = []
    moves: list[int] = []
    max_per_species = 0
    for species in range(SPECIES_COUNT):
        offsets.append(len(moves))
        values = tuple(rows.get(species, ()))
        if len(values) != len(set(values)):
            _fail(f"{label} species {species} Move重複")
        if any(not 1 <= value <= MOVE_LAST for value in values):
            _fail(f"{label} species {species} Move範囲不一致")
        moves.extend(values)
        max_per_species = max(max_per_species, len(values))
    offsets.append(len(moves))
    if len(offsets) != SPECIES_COUNT + 1 or len(moves) > 0xFFFF:
        _fail(f"{label} indexed U16 ABI容量不一致")
    return IndexedMoveTable(
        index=struct.pack(f"<{len(offsets)}H", *offsets),
        moves=struct.pack(f"<{len(moves)}H", *moves),
        species_count=sum(bool(rows.get(species)) for species in range(SPECIES_COUNT)),
        move_count=len(moves),
        max_per_species=max_per_species,
    )


def build_runtime_tables(model: RouteModel) -> tuple[dict[str, bytes], dict[str, Any]]:
    tables = {
        "Shared": build_indexed_table(model.shared_rows, "shared egg"),
        "Reminder": build_indexed_table(model.reminder_rows, "reminder"),
        "ExactEgg": build_indexed_table(model.exact_egg_rows, "exact egg"),
    }
    if (
        tables["Shared"].move_count != 5023
        or tables["Reminder"].move_count != 295
        or tables["ExactEgg"].move_count != 40
    ):
        _fail("runtime indexed table行数不一致")
    blobs: dict[str, bytes] = {}
    audit: dict[str, Any] = {}
    for name, table in tables.items():
        blobs[f"Stage73_{name}Index"] = table.index
        blobs[f"Stage73_{name}Moves"] = table.moves
        audit[name] = {
            "index_entries": SPECIES_COUNT + 1,
            "index_size": len(table.index),
            "index_sha256": sha256(table.index),
            "species_with_rows": table.species_count,
            "move_rows": table.move_count,
            "move_size": len(table.moves),
            "move_sha256": sha256(table.moves),
            "max_rows_per_species": table.max_per_species,
        }
    return blobs, audit


def _parse_egg_table(rom: bytes, root_address: int) -> tuple[dict[int, tuple[int, ...]], tuple[int, ...], bytes]:
    cursor = _rom_offset(root_address, 2, "egg table root")
    start = cursor
    records: dict[int, list[int]] = {}
    order: list[int] = []
    active: int | None = None
    for _ in range(20_000):
        if cursor + 2 > len(rom):
            _fail("egg tableがROM範囲外です")
        value = struct.unpack_from("<H", rom, cursor)[0]
        cursor += 2
        if value == 0xFFFF:
            if active is None or order != sorted(order) or len(order) != len(set(order)):
                _fail("egg table marker order/uniqueness不一致")
            return {key: tuple(values) for key, values in records.items()}, tuple(order), rom[start:cursor]
        if value >= 20_000:
            species = value - 20_000
            if not 0 <= species < SPECIES_COUNT or species in records:
                _fail(f"egg marker不正: {species}")
            active = species
            order.append(species)
            records[species] = []
        else:
            if active is None or not 1 <= value <= MOVE_LAST:
                _fail(f"egg Move row不正: {value}")
            records[active].append(value)
            if len(records[active]) > 50:
                _fail(f"egg Moveが50行を超えます: {active}")
    _fail("egg tableが20,000 U16以内に終端しません")


@dataclass(frozen=True)
class ExactEggPayload:
    payload: bytes
    rows: dict[int, tuple[int, ...]]
    audit: dict[str, Any]


def build_exact_egg_payload(parent: bytes, model: RouteModel, config: Mapping[str, Any]) -> ExactEggPayload:
    egg = config["parent_abi"]["egg"]
    primary_site = _integer(egg["primary_root_literal_rom_offset"], "egg.primary")
    secondary_site = _integer(egg["secondary_root_literal_rom_offset"], "egg.secondary")
    limit_site = _integer(egg["scan_limit_literal_rom_offset"], "egg.limit")
    root = struct.unpack_from("<I", parent, primary_site)[0]
    secondary = struct.unpack_from("<I", parent, secondary_site)[0]
    limit = struct.unpack_from("<I", parent, limit_site)[0]
    expected_root = _integer(egg["expected_root"], "egg.expected_root")
    if root != expected_root or secondary != expected_root or limit != egg["expected_scan_limit"]:
        _fail("Stage72 egg dual-root/scan-limit preimage不一致")
    parent_rows, parent_order, parent_raw = _parse_egg_table(parent, root)
    if len(parent_raw) != egg["expected_table_size"] or sha256(parent_raw) != egg["expected_table_sha256"]:
        _fail("Stage72 egg table identity不一致")
    if len(parent_rows) != 1399 or sum(map(len, parent_rows.values())) != 6159:
        _fail("Stage72 egg table logical count不一致")
    rows = dict(parent_rows)
    before = {species: rows.get(species, ()) for species in EXACT_EGG_SPECIES}
    for species in sorted(EXACT_EGG_SPECIES):
        values = tuple(model.exact_egg_rows.get(species, ()))
        if not values or len(values) != len(set(values)):
            _fail(f"exact egg replacement row不正: {species}")
        rows[species] = values
    payload = bytearray()
    for species in sorted(rows):
        payload.extend(struct.pack("<H", 20_000 + species))
        for move in rows[species]:
            payload.extend(struct.pack("<H", move))
    payload.extend(b"\xFF\xFF")
    preserved = set(parent_order) - EXACT_EGG_SPECIES
    if any(rows[species] != parent_rows[species] for species in preserved):
        _fail("非対象egg recordが保持されていません")
    raw = bytes(payload)
    audit = {
        "parent_root": f"0x{root:08X}",
        "parent_size": len(parent_raw),
        "parent_sha256": sha256(parent_raw),
        "parent_marker_count": len(parent_rows),
        "parent_move_count": sum(map(len, parent_rows.values())),
        "replaced_species": sorted(EXACT_EGG_SPECIES),
        "replaced_route_count": sum(len(values) for values in model.exact_egg_rows.values()),
        "previous_replaced_rows": {str(key): list(value) for key, value in sorted(before.items())},
        "output_size": len(raw),
        "output_sha256": sha256(raw),
        "output_marker_count": len(rows),
        "output_move_count": sum(map(len, rows.values())),
        "output_scan_limit": len(raw) // 2 - 2,
        "unaffected_records_preserved": len(preserved),
    }
    return ExactEggPayload(raw, rows, audit)


def _level_moves(parent: bytes, species: int) -> tuple[int, ...]:
    root = struct.unpack_from("<I", parent, 0x0004346C)[0]
    root_offset = _rom_offset(root, SPECIES_COUNT * 4, "level pointer root")
    pointer = struct.unpack_from("<I", parent, root_offset + species * 4)[0]
    cursor = _rom_offset(pointer, 3, f"species {species} level rows")
    result: list[int] = []
    for _ in range(40):
        move, level = struct.unpack_from("<HB", parent, cursor)
        cursor += 3
        if move == 0 and level == 0xFF:
            break
        if not 1 <= move <= MOVE_LAST or level > 100:
            _fail(f"species {species} level row ABI不一致: {move}/{level}")
        if move not in result:
            result.append(move)
    return tuple(result)


def build_capacity_audit(
    parent: bytes,
    model: RouteModel,
    output_egg_rows: Mapping[int, Sequence[int]],
) -> dict[str, Any]:
    """40-candidate ABIで専用routeがpriority落ちしないことを静的に証明する。"""

    reminder_cases: list[tuple[int, int, int, int]] = []
    for species, reminder in model.reminder_rows.items():
        level = _level_moves(parent, species)
        union = tuple(dict.fromkeys((*level, *reminder)))
        reminder_cases.append((len(union), species, len(level), len(reminder)))
    reminder_max = max(reminder_cases)
    if reminder_max[0] > 40:
        _fail(f"level+reminder candidateが40超過: {reminder_max}")

    shared_cases: list[tuple[int, int, int, int, int]] = []
    for species, shared in model.shared_rows.items():
        candidate_cases = []
        for source_species in model.shared_legacy_source_species[species]:
            legacy = tuple(output_egg_rows.get(source_species, ()))
            union = tuple(dict.fromkeys((*legacy, *shared)))
            candidate_cases.append((len(union), species, source_species, len(legacy), len(shared)))
        shared_cases.append(max(candidate_cases))
    shared_max = max(shared_cases)
    if shared_max[0] > 40:
        _fail(f"legacy egg+shared candidateが40超過: {shared_max}")
    return {
        "candidate_capacity": 40,
        "normal_relearner": {
            "priority": "existing level/evolution rows first; dedicated reminder rows second",
            "species_audited": len(reminder_cases),
            "max_union_count": reminder_max[0],
            "max_union_species": reminder_max[1],
            "max_case_level_rows": reminder_max[2],
            "max_case_reminder_rows": reminder_max[3],
            "capacity_drop_count": 0,
        },
        "mirror_herb_shared_egg": {
            "priority": "existing normal egg pool first; distinct shared-egg rows second",
            "legacy_source_resolution": "source-game shared_egg_source_key mapped to every adopted canonical alias plus concrete target; one fixed battle-only fallback",
            "species_audited": len(shared_cases),
            "max_union_count": shared_max[0],
            "max_union_species": shared_max[1],
            "max_case_legacy_source_species": shared_max[2],
            "max_case_legacy_rows": shared_max[3],
            "max_case_shared_rows": shared_max[4],
            "capacity_drop_count": 0,
        },
    }


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        _fail(f"{label}失敗\n{result.stdout}\n{result.stderr}")
    return result.stdout


@dataclass(frozen=True)
class CompiledPayload:
    code: bytes
    symbols: dict[str, int]
    compiler: str


def compile_payload(root: Path, load_address: int, blobs: Mapping[str, bytes]) -> CompiledPayload:
    gcc = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not gcc or not objcopy or not nm:
        _fail("arm-none-eabi gcc/objcopy/nmがPATHにありません")
    source_dir = root / "overlays/modernization_p03_stage73_consumer_runtime"
    c_source = source_dir / "modernization_p03_stage73_consumer_runtime.c"
    asm_source = source_dir / "modernization_p03_stage73_consumer_runtime_hooks.S"
    linker = source_dir / "modernization_p03_stage73_consumer_runtime.ld"
    for path in (c_source, asm_source, linker):
        if path.is_symlink() or not path.is_file():
            _fail(f"Stage73 overlay source欠落: {path}")
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage73-p03-runtime-") as temporary:
        work = Path(temporary)
        table_asm = work / "tables.S"
        table_lines = [".syntax unified", ".cpu arm7tdmi", ".thumb", ".section .rodata.Stage73GeneratedTables,\"a\",%progbits", ".balign 2"]
        for index, (name, raw) in enumerate(blobs.items()):
            blob_path = work / f"table-{index}.bin"
            blob_path.write_bytes(raw)
            table_lines.extend([f".global {name}", f".type {name}, %object", f"{name}:", f'.incbin "{blob_path}"', f".size {name}, .-{name}", ".balign 2"])
        table_lines.append('.section .note.GNU-stack,"",%progbits')
        table_asm.write_text("\n".join(table_lines) + "\n", encoding="utf-8")
        c_obj = work / "runtime.o"
        hooks_obj = work / "hooks.o"
        tables_obj = work / "tables.o"
        elf = work / "runtime.elf"
        binary = work / "runtime.bin"
        _run([
            gcc, *common, "-Os", "-std=c11", "-ffreestanding", "-fno-common",
            "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror",
            "-Wconversion", "-Wshadow", "-c", str(c_source), "-o", str(c_obj),
        ], root, "Stage73 C compile")
        _run([gcc, *common, "-c", str(asm_source), "-o", str(hooks_obj)], root, "Stage73 trampoline compile")
        _run([gcc, *common, "-c", str(table_asm), "-o", str(tables_obj)], root, "Stage73 table compile")
        _run([
            gcc, "-nostdlib", *common,
            f"-Wl,--defsym=STAGE73_LOAD_ADDRESS=0x{load_address:08X}",
            f"-Wl,-T,{linker}", str(c_obj), str(hooks_obj), str(tables_obj), "-lgcc", "-o", str(elf),
        ], root, "Stage73 link")
        _run([objcopy, "-O", "binary", str(elf), str(binary)], root, "Stage73 objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", str(elf)], root, "Stage73 nm").splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[0] and all(char in "0123456789abcdefABCDEF" for char in fields[0]):
                symbols[fields[2]] = int(fields[0], 16)
        code = binary.read_bytes()
    required = {
        "Stage73_RuntimeProbe", "Stage73_GetAllEggMoves", "Stage73_GetMoveRelearnerMoves",
        "Stage73_CollectionApplySelectedForm", "Stage73_OriginalGetAllEggMoves",
        "Stage73_OriginalCollectionApplySelectedForm", *blobs,
    }
    missing = sorted(required - set(symbols))
    if missing:
        _fail(f"Stage73 symbol欠落: {missing}")
    if not code or len(code) >= 0x10000:
        _fail(f"Stage73 payload size不正: {len(code)}")
    if symbols["Stage73_RuntimeProbe"] != load_address:
        _fail("Stage73 entry/load address不一致")
    return CompiledPayload(
        code=code,
        symbols=symbols,
        compiler=_run([gcc, "--version"], root, "gcc version").splitlines()[0],
    )


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = allocation.get("allocations")
    if allocation.get("schema_version") != 1 or not isinstance(rows, list):
        _fail("Stage72 allocation schema不一致")
    if [row.get("sequence") for row in rows] != list(range(len(rows))):
        _fail("Stage72 allocation sequence不一致")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"], "owner": row["owner"],
        "purpose": row["purpose"], "content_sha256": row["content_sha256"],
    } for row in rows]


def _allocate(
    root: Path,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    payloads: Sequence[bytes],
    *,
    placeholder: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    declarations = config["allocations"]
    if len(declarations) != len(payloads) or len(payloads) != 2:
        _fail("Stage73 allocation/payload件数不一致")
    requests = _previous_requests(previous)
    previous_count = len(requests)
    for declaration, payload in zip(declarations, payloads, strict=True):
        requests.append({
            "name": declaration["name"], "region": declaration["region"],
            "size": len(payload), "alignment": declaration["alignment"],
            "owner": declaration["owner"], "purpose": declaration["purpose"],
            "content_sha256": "0" * 64 if placeholder else sha256(payload),
        })
    report = build_allocation_report_from_csv(root / config["inputs"]["rom_regions"]["path"], requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage73 allocator overlap")
    allocations = report["allocations"][previous_count:]
    if (
        len(allocations) != 2
        or [row["name"] for row in allocations] != [row["name"] for row in declarations]
        or [row["sequence"] for row in allocations] != [previous_count, previous_count + 1]
        or any(row["placement"] != "FIRST_FIT" for row in allocations)
    ):
        _fail("Stage73 allocation末尾/FIRST_FIT不一致")
    return allocations, report


def _veneer(width: int, target: int) -> bytes:
    target |= 1
    if width == 8:
        return struct.pack("<HHI", 0x4B00, 0x4718, target)
    if width == 12:
        return struct.pack("<HHHHI", 0x469C, 0x4B01, 0x4718, 0x46C0, target)
    _fail(f"未対応hook veneer width: {width}")


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    spans: list[dict[str, int]] = []
    start: int | None = None
    for offset, (left, right) in enumerate(zip(before, after, strict=True)):
        if left != right and start is None:
            start = offset
        elif left == right and start is not None:
            spans.append({"start": start, "end_exclusive": offset, "size": offset - start})
            start = None
    if start is not None:
        spans.append({"start": start, "end_exclusive": len(before), "size": len(before) - start})
    return spans


@dataclass
class BuiltStage73:
    config: dict[str, Any]
    parent: bytes
    rom: bytes
    payload: bytes
    allocation: bytes
    symbols: dict[str, Any]
    metadata: dict[str, Any]
    checkpoint: dict[str, Any]
    route_audit: dict[str, Any]
    audit: dict[str, Any]


def build_stage73_image(root: Path, config_path: Path = DEFAULT_CONFIG) -> BuiltStage73:
    root = root.resolve()
    config = read_config(root, config_path)
    # Must happen before the immutable 82 MiB ZIP is opened.
    require_pinned_parent(config)
    parent_contract = config["parent_identity"]
    parent = _fixed_raw(root, parent_contract["rom"], "Stage72 ROM")
    parent_metadata = _json(_fixed_raw(root, parent_contract["metadata"], "Stage72 metadata"), "Stage72 metadata")
    previous_allocation_raw = _fixed_raw(root, parent_contract["allocation"], "Stage72 allocation")
    parent_checkpoint = _json(_fixed_raw(root, parent_contract["checkpoint"], "Stage72 checkpoint"), "Stage72 checkpoint")
    previous_allocation = _json(previous_allocation_raw, "Stage72 allocation")
    if len(parent) != ROM_SIZE:
        _fail("Stage72 ROM size不一致")
    if parent_metadata.get("output", {}).get("sha256") != sha256(parent):
        _fail("Stage72 metadata→ROM identity不一致")
    if parent_checkpoint.get("output_sha256") != sha256(parent):
        _fail("Stage72 checkpoint→ROM identity不一致")
    light_ball_owner_evidence = verify_existing_light_ball_owner(parent)
    for label in (
        "stage67_checkpoint", "stage67_route_audit", "stage67_config",
        "collection_model", "collection_runtime_source", "rom_regions",
    ):
        _fixed_raw(root, config["inputs"][label], label)
    collection_model = _json(_fixed_raw(root, config["inputs"]["collection_model"], "collection model"), "collection model")
    forms = collection_model.get("forms")
    if not isinstance(forms, list) or [
        (row.get("base_species"), row.get("target_species"), row.get("method"), row.get("distributable"))
        for row in forms[37:42]
    ] != [(742, species, "FORM_CHANGE_SERVICE", True) for species in range(894, 899)]:
        _fail("Collection Rotom form indices 37..41 ABI不一致")

    model = compile_route_model(root, config)
    blobs, table_audit = build_runtime_tables(model)
    exact_egg = build_exact_egg_payload(parent, model, config)
    capacity_audit = build_capacity_audit(parent, model, exact_egg.rows)
    provisional = compile_payload(root, PROVISIONAL_LOAD_ADDRESS, blobs)
    provisional_allocations, _ = _allocate(
        root, config, previous_allocation, (provisional.code, exact_egg.payload), placeholder=True,
    )
    load_address = GBA_ROM_BASE + provisional_allocations[0]["start"]
    compiled = compile_payload(root, load_address, blobs)
    if len(compiled.code) != len(provisional.code):
        _fail("Stage73 link addressでpayload sizeが変化しました")
    payload = compiled.code
    allocations, allocation_report = _allocate(
        root, config, previous_allocation, (payload, exact_egg.payload), placeholder=False,
    )
    if allocations[0]["gba_start"] != load_address:
        _fail("Stage73 allocator/load address再解決不一致")

    output = bytearray(parent)
    allowed = bytearray(ROM_SIZE)
    writes: list[dict[str, Any]] = []

    def patch(offset: int, raw: bytes, label: str, expected: bytes | None = None) -> None:
        if offset < 0 or offset + len(raw) > ROM_SIZE:
            _fail(f"{label} patch範囲外")
        if expected is not None and parent[offset:offset + len(raw)] != expected:
            _fail(f"{label} parent preimage不一致")
        if any(allowed[offset:offset + len(raw)]):
            _fail(f"{label} allowlist overlap")
        output[offset:offset + len(raw)] = raw
        allowed[offset:offset + len(raw)] = b"\x01" * len(raw)
        writes.append({
            "label": label, "start": offset, "end_exclusive": offset + len(raw), "size": len(raw),
            "parent_sha256": sha256(parent[offset:offset + len(raw)]), "output_sha256": sha256(raw),
        })

    payload_start = allocations[0]["start"]
    egg_start = allocations[1]["start"]
    if parent[payload_start:payload_start + len(payload)] != b"\xFF" * len(payload):
        _fail("Stage73 runtime allocation preimageが全FFではありません")
    if parent[egg_start:egg_start + len(exact_egg.payload)] != b"\xFF" * len(exact_egg.payload):
        _fail("Stage73 exact egg allocation preimageが全FFではありません")
    patch(payload_start, payload, "stage73_runtime_payload", b"\xFF" * len(payload))
    patch(egg_start, exact_egg.payload, "stage73_exact_egg_table", b"\xFF" * len(exact_egg.payload))

    hook_rows: list[dict[str, Any]] = []
    for row in config["parent_abi"]["hooks"]:
        target_name = str(row["target"])
        if target_name not in compiled.symbols:
            _fail(f"hook target symbol欠落: {target_name}")
        address = _integer(row["address"], "hook.address")
        width = _integer(row["width"], "hook.width")
        offset = _rom_offset(address, width, f"hook {row['name']}")
        expected = bytes.fromhex(row["parent_hex"])
        veneer = _veneer(width, compiled.symbols[target_name])
        patch(offset, veneer, f"hook:{row['name']}", expected)
        hook_rows.append({
            "name": row["name"], "site": f"0x{address:08X}", "width": width,
            "target": target_name, "target_address": f"0x{compiled.symbols[target_name] | 1:08X}",
            "parent_hex": expected.hex(), "veneer_hex": veneer.hex(),
        })

    egg_abi = config["parent_abi"]["egg"]
    output_egg_root = GBA_ROM_BASE + egg_start
    output_egg_limit = exact_egg.audit["output_scan_limit"]
    for key, value, label in (
        ("primary_root_literal_rom_offset", output_egg_root, "egg_primary_root"),
        ("secondary_root_literal_rom_offset", output_egg_root, "egg_secondary_root"),
        ("scan_limit_literal_rom_offset", output_egg_limit, "egg_scan_limit"),
    ):
        site = _integer(egg_abi[key], key)
        previous = parent[site:site + 4]
        patch(site, struct.pack("<I", value), label, previous)

    result = bytes(output)
    outside = [
        offset for offset, (left, right) in enumerate(zip(parent, result, strict=True))
        if left != right and not allowed[offset]
    ]
    if outside:
        _fail(f"Stage73 allowlist外変更: 0x{outside[0]:X}")
    parsed_rows, _, parsed_raw = _parse_egg_table(result, output_egg_root)
    if parsed_raw != exact_egg.payload or parsed_rows != exact_egg.rows:
        _fail("Stage73 exact egg table readback不一致")
    for key, value in (
        ("primary_root_literal_rom_offset", output_egg_root),
        ("secondary_root_literal_rom_offset", output_egg_root),
        ("scan_limit_literal_rom_offset", output_egg_limit),
    ):
        if struct.unpack_from("<I", result, _integer(egg_abi[key], key))[0] != value:
            _fail(f"Stage73 {key} readback不一致")
    changed = [offset for offset, pair in enumerate(zip(parent, result, strict=True)) if pair[0] != pair[1]]
    spans = _changed_spans(parent, result)
    output_crc32 = f"{zlib.crc32(result) & 0xFFFFFFFF:08x}"

    route_audit = copy.deepcopy(model.route_audit)
    if route_audit["conditional_breeding_existing_owner_evidence"] != light_ball_owner_evidence:
        _fail("Stage73 route audit→Light Ball owner命令証拠不一致")
    route_audit["serialization"] = {
        "runtime_tables": table_audit,
        "payload_size": len(payload),
        "payload_sha256": sha256(payload),
        "exact_egg_table": exact_egg.audit,
        "shared_egg_kept_out_of_normal_egg_table": True,
        "reminder_kept_out_of_level_zero_rows": True,
        "carry_routes_added_to_direct_tables": 0,
        "conditional_breeding_existing_parent_owner": route_audit[
            "conditional_breeding_existing_owner_evidence"
        ],
        "rotom_signature_transition_count": 5,
        "rotom_full_moveset_policy": {
            "base_with_existing_rotom_signature": "replace that signature slot",
            "base_with_empty_slot": "use the first empty slot",
            "base_full_without_signature": "EFFECTLESS; never silently overwrite a user move",
            "user_action": "make one slot empty with Move Memory, then retry the form service",
        },
        "candidate_capacity": capacity_audit,
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "parent_sha256": sha256(parent), "output_sha256": sha256(result), "output_crc32": output_crc32,
        "payload": {
            "start": payload_start, "gba_start": f"0x{GBA_ROM_BASE + payload_start:08X}",
            "size": len(payload), "sha256": sha256(payload),
        },
        "exact_egg_table": {
            "start": egg_start, "gba_start": f"0x{output_egg_root:08X}",
            "size": len(exact_egg.payload), "sha256": sha256(exact_egg.payload),
            "scan_limit": output_egg_limit,
        },
        "writes": writes, "hooks": hook_rows,
        "changed_byte_count": len(changed), "allowed_byte_count": sum(allowed),
        "outside_allowlist_count": 0,
        "changed_offsets_sha256": sha256(b"".join(struct.pack("<I", value) for value in changed)),
        "changed_span_count": len(spans), "changed_spans": spans,
        "existing_rom_outside_allowlist_unchanged": True,
    }
    function_symbols = {
        "Stage73_RuntimeProbe", "Stage73_GetAllEggMoves", "Stage73_GetMoveRelearnerMoves",
        "Stage73_CollectionApplySelectedForm", "Stage73_OriginalGetAllEggMoves",
        "Stage73_OriginalCollectionApplySelectedForm", "Stage73_RotomSignatureMove",
        "Stage73_IsExactEggConflictSpecies",
    }
    symbols = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "load_address": f"0x{load_address:08X}", "compiler": compiled.compiler,
        "symbols": {
            name: {
                "address": f"0x{address:08X}",
                **({"thumb_address": f"0x{address | 1:08X}"} if name in function_symbols else {}),
            }
            for name, address in sorted(compiled.symbols.items()) if name.startswith("Stage73_")
        },
    }
    status = "CHECKPOINT_FIVE_CONSUMER_BOUNDARY_CONNECTED_SUPPLY_DEPENDENCIES_REMAIN"
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": status,
        "release_candidate": False,
        "parent_identity": {
            "commit": parent_contract["stage72_commit"], "path": parent_contract["rom"]["path"],
            "size": len(parent), "sha256": sha256(parent),
        },
        "output": {
            "path": config["outputs"]["rom"], "size": len(result), "sha256": sha256(result),
            "crc32": output_crc32,
        },
        "changed_bytes": len(changed),
        "allocation": allocations,
        "allocation_report": {
            "path": config["outputs"]["allocation"], "size": len(stable_json(allocation_report)),
            "sha256": sha256(stable_json(allocation_report)),
        },
        "payload": {"path": config["outputs"]["payload"], "size": len(payload), "sha256": sha256(payload)},
        "hooks": hook_rows,
        "consumer_accounting": route_audit["accounting"],
        "validation": {
            "single_zip_stream_route_contract": "PASS", "compile_link": "PASS",
            "hook_preimages": "PASS", "thumb_targets": "PASS", "allocation_first_fit": "PASS",
            "existing_light_ball_owner_instruction_evidence": "PASS",
            "egg_dual_root_scan_limit_readback": "PASS", "allowlist_outside": 0,
            "normal_reminder_capacity_drop": 0, "legacy_shared_egg_capacity_drop": 0,
            "prohibited_coercions": 0, "side_change": 0, "browt_pombon_gecqua": 0,
            "mgba": "NOT_RUN_LIGHTWEIGHT_STAGE73_OWNER",
        },
        "completion_claim": "FIVE_GROUP_CONSUMER_BOUNDARY_CHECKPOINT_NOT_FULL_P03",
        "remaining_work": [
            "machine direct routes 26,279 and tutor direct routes 369 remain outside this checkpoint",
            "carry/form routes with 23,595 machine/tutor source dependencies require their upstream supply owners",
            "Rotom base with four user moves and no prior appliance signature returns EFFECTLESS; free one slot and retry",
            "final cumulative mGBA is deferred to the root release gate",
        ],
    }
    checkpoint = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": status,
        "release_candidate": False, "done": False,
        "parent_commit": parent_contract["stage72_commit"], "parent_sha256": sha256(parent),
        "output_path": config["outputs"]["rom"], "output_size": len(result),
        "output_sha256": sha256(result), "output_crc32": output_crc32,
        "changed_bytes": len(changed), "payload_sha256": sha256(payload),
        "allocation_sha256": sha256(stable_json(allocation_report)),
        "route_audit_sha256": sha256(stable_json(route_audit)),
        "consumer_boundary_accounted_routes": 40570,
        "new_runtime_materialized_routes": route_audit["accounting"]["new_runtime_materialized_routes"],
        "conditional_breeding_existing_owner_evidence": route_audit[
            "conditional_breeding_existing_owner_evidence"
        ],
        "remaining_full_p03_routes": 26648,
        "completion_claim": "FIVE_GROUP_CONSUMER_BOUNDARY_CHECKPOINT_NOT_FULL_P03",
        "mgba": "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
    }
    return BuiltStage73(
        config=config, parent=parent, rom=result, payload=payload,
        allocation=stable_json(allocation_report), symbols=symbols,
        metadata=metadata, checkpoint=checkpoint, route_audit=route_audit, audit=audit,
    )


def plan_rotom_move_transition(current_species: int, target_species: int, moves: Sequence[int]) -> tuple[str, tuple[int, ...]]:
    """C runtimeと同じ4-slot policyをhost unitから確認する小さいoracle。"""

    if len(moves) != 4:
        _fail("Rotom movesetは4 slots必須です")
    result = list(moves)
    signature = ROTOM_SIGNATURE_MOVES.get(target_species)
    if signature is None:
        return "DELEGATE", tuple(result)
    if current_species == 742:
        replace = next((index for index, move in enumerate(result) if move in ROTOM_SIGNATURE_MOVES.values()), None)
        if replace is None:
            replace = next((index for index, move in enumerate(result) if move == 0), None)
        if replace is None:
            return "EFFECTLESS_FULL", tuple(result)
        result[replace] = signature
        return "APPLY_FORM", tuple(result)
    if current_species == target_species:
        if signature in result:
            result.remove(signature)
            result.append(0)
        return "RETURN_BASE", tuple(result)
    return "DELEGATE", tuple(result)


def build_outputs(root: Path, config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage73_image(root, config_path)
    outputs = built.config["outputs"]
    bps = create_bps(
        built.parent, built.rom,
        metadata=b"Stage72 to Stage73 P03 five-consumer runtime checkpoint",
    )
    if apply_bps(built.parent, bps) != built.rom:
        _fail("Stage72→Stage73 BPS round-trip不一致")
    bps_identity = {
        "path": outputs["incremental_bps"], "size": len(bps), "sha256": sha256(bps),
        "source_sha256": sha256(built.parent), "target_sha256": sha256(built.rom), "round_trip": True,
    }
    built.metadata["bps"] = bps_identity
    built.checkpoint["bps"] = bps_identity
    return {
        outputs["rom"]: built.rom,
        outputs["metadata"]: stable_json(built.metadata),
        outputs["allocation"]: built.allocation,
        outputs["incremental_bps"]: bps,
        outputs["payload"]: built.payload,
        outputs["symbols"]: stable_json(built.symbols),
        outputs["audit"]: stable_json(built.audit),
        outputs["checkpoint"]: stable_json(built.checkpoint),
        outputs["route_audit"]: stable_json(built.route_audit),
    }


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _compare(root: Path, outputs: Mapping[str, bytes]) -> None:
    mismatches = [
        relative for relative, expected in outputs.items()
        if not (root / relative).is_file() or (root / relative).read_bytes() != expected
    ]
    if mismatches:
        _fail(f"Stage73 published artifact不一致: {mismatches}")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("model", "compile", "build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    config = read_config(root, args.config)
    if args.command == "model":
        model = compile_route_model(root, config)
        print(json.dumps(model.route_audit["accounting"], ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "compile":
        model = compile_route_model(root, config)
        blobs, table_audit = build_runtime_tables(model)
        compiled = compile_payload(root, PROVISIONAL_LOAD_ADDRESS, blobs)
        print(f"Stage73 COMPILE PASS size={len(compiled.code)} sha256={sha256(compiled.code)} tables={json.dumps(table_audit, sort_keys=True)}")
        return 0
    outputs = build_outputs(root, args.config)
    if args.command == "check":
        _compare(root, outputs)
    else:
        for relative, raw in outputs.items():
            _atomic_write(root / relative, raw)
    print(f"Stage73 {args.command.upper()} PASS artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModernizationP03Stage73RuntimeError as error:
        print(f"ERROR: {error}", file=os.sys.stderr)
        raise SystemExit(1)
