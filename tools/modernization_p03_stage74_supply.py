#!/usr/bin/env python3
"""Stage73を親にP03 direct machine/tutor archive Stage74を生成する。"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
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
from typing import Any, Iterable, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_learnsets import iter_compiled_p03_routes
from tools.release.bps import apply_bps, create_bps
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P03-STAGE74-SUPPLY-RUNTIME"
STAGE = 74
ROM_SIZE = 32 * 1024 * 1024
SPECIES_COUNT = 1621
MOVE_LAST = 1062
SIDE_CHANGE_MOVE_ID = 1063
PAGE_SIZE = 40
MAX_MACHINE_PAGES = 4
MODE_NORMAL = 0
MODE_EGG = 1
MODE_MACHINE_PROBE = 2
MODE_MACHINE_PAGE_0 = 3
MODE_MACHINE_PAGE_LAST = 6
MODE_TUTOR = 7
MOVE_MEMORY_SEQUENCE = 33
EXPECTED_STAGE73_ALLOCATION_COUNT = 77
DEFAULT_CONFIG = Path("config/modernization_p03_stage74_supply.json")
PROVISIONAL_LOAD_ADDRESS = 0x09540000
PROHIBITED_SPECIES_KEYS = (
    "SPECIES_KEY_BROWT", "SPECIES_KEY_POMBON", "SPECIES_KEY_GECQUA",
)
EXPECTED_SOURCE_COUNTS = {
    "level_up": 18530,
    "evolution": 341,
    "reminder": 298,
    "machine": 55380,
    "tutor": 1113,
    "egg": 2572,
    "shared_egg": 5041,
    "pre_evolution_carry": 35183,
    "form_change": 70,
}
EXPECTED_SIDE_CHANGE_COUNTS = {
    "egg": 9,
    "level_up": 15,
    "machine": 68,
    "pre_evolution_carry": 42,
    "reminder": 3,
    "shared_egg": 18,
    "tutor": 4,
}
EXPECTED_MACHINE_SET_SHA256 = "c36479fe7ccca18a2f0861597d7e9667d0f30f2cc1a32d33dc32efea12e107fd"
EXPECTED_TUTOR_SET_SHA256 = "085379dc87fb5127e2f8f29d35d4f51805b138c7c86ecc022a68b5979da24f15"
EXPECTED_UNION_SET_SHA256 = "5ef6be8c533e60c07ec1240c3ee8cc1e56c90c505689f3d41436719f338f7968"
EXPECTED_EXISTING_PROJECTION_SHA256 = "f4be2d83dae734c9339b790583d1e8c427daac49c964c87205b2f970b6deb3f1"
EXPECTED_CROSS_FAMILY_MOVE_IDS = (173, 264, 304, 340, 352, 395, 700, 701, 702, 793)
EXPECTED_PRESERVATION_TRIPLET_SHA256 = "c884e85f0e70ced7f9519d1223c52568710c65aa16b1326df797836b3aa1d312"
EXPECTED_PRESERVATION_TARGET_MOVE_SHA256 = "78658b9659faee8242bd9155e3c88b1b14ec75ea2df0f5bf2a38ca73cb8dba87"
EXPECTED_FULL_PRESERVATION_TARGET_MOVE_SHA256 = "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb"
EXPECTED_PRESERVATION_CONSUMER_COUNTS = {
    "egg": 1,
    "form_change": 70,
    "pre_evolution_carry": 2111,
    "reminder": 186,
    "shared_egg": 1646,
}
EXPECTED_PRESERVATION_METHOD_COUNTS = {
    "battle_transform": 2,
    "egg": 1714,
    "evolution": 5,
    "form_move": 9,
    "level_up": 410,
    "reminder": 192,
    "shared_egg": 1646,
    "special_breeding": 5,
    "tm": 24,
    "tutor": 7,
}
EXPECTED_SCRIPT_ENTRIES = {
    "normal": 0x092D07A0,
    "forget": 0x092D08FC,
    "egg": 0x092D0818,
    "context_rejected": 0x092D09F8,
    "finish": 0x092D0A08,
}
EXPECTED_SCRIPT_SLICES = {
    "normal": (18, "4d3ae3d403ca49277e70e7e451ac85ce8906a8b188e3505c627b9e749e76e139"),
    "forget": (18, "15c288c4983a583b70ab22eb9383b61d5534e110ea7bc52e76acc88853f826a9"),
    "egg": (37, "9be513f433b2d25ee74896df9e23fd73f0126b5001eb0864f6c137463f1cf0c8"),
    "context_rejected": (13, "fe684bf32e852ca5c1914dc8e6efc6870fd3f727d3759adbd12f36c7aa026c1d"),
    "finish": (7, "047b31c9ac1e45b7b9717215c9ce670a96eb112842ef6195ef552e87a03508b4"),
}
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class ModernizationP03Stage74SupplyError(ValueError):
    """Stage74 identity、route、paging、ABI、allocation違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage74SupplyError(message)


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


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label} JSON不正: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _fixed_raw(root: Path, contract: Mapping[str, Any], label: str) -> bytes:
    relative = contract.get("path")
    size = contract.get("size")
    digest = contract.get("sha256")
    if not isinstance(relative, str) or not relative or not isinstance(size, int) \
            or not isinstance(digest, str) or not _SHA_RE.fullmatch(digest):
        _fail(f"{label} identity contract不正")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が固定通常fileではありません: {path}")
    raw = path.read_bytes()
    if len(raw) != size or sha256(raw) != digest:
        _fail(
            f"{label} identity不一致: size={len(raw)}/{size} "
            f"sha={sha256(raw)}/{digest}"
        )
    return raw


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


def _set_sha(values: Iterable[str]) -> str:
    digest = FramedDigest()
    for value in sorted(values):
        digest.add(value)
    return digest.hexdigest()


def read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"Stage74 configが固定通常fileではありません: {path}")
    config = _json(path.read_bytes(), "Stage74 config")
    if (config.get("schema_version"), config.get("task"), config.get("stage")) != (
        SCHEMA_VERSION, TASK, STAGE,
    ):
        _fail("Stage74 config schema/task/stage不一致")
    if config.get("status") != "STAGE73_IDENTITY_PINNED":
        _fail("Stage74 parent status不一致")
    supply = config.get("supply_contract", {})
    if supply != {
        "machine": {
            "routes": 26279, "species_move_pairs": 26279, "species": 1286,
            "distinct_moves": 184, "max_rows_per_species": 131,
            "max_species": 151, "page_size": 40, "max_pages": 4,
            "set_sha256": EXPECTED_MACHINE_SET_SHA256,
        },
        "tutor": {
            "routes": 369, "species_move_pairs": 369, "species": 138,
            "distinct_moves": 31, "max_rows_per_species": 12,
            "max_species": 762, "page_size": 40, "max_pages": 1,
            "set_sha256": EXPECTED_TUTOR_SET_SHA256,
        },
        "total_routes": 26648,
        "total_species_move_pairs": 26648,
        "duplicate_species_family_move_pairs": 0,
        "supply_required_set_sha256": EXPECTED_UNION_SET_SHA256,
        "cross_family_same_move_id_count": 10,
        "cross_family_same_move_ids": list(EXPECTED_CROSS_FAMILY_MOVE_IDS),
        "same_species_cross_family_pair_count": 0,
        "existing_slot_projection": {
            "routes": 29773, "machine": 29033, "tutor": 740,
            "set_sha256": EXPECTED_EXISTING_PROJECTION_SHA256,
        },
        "selected_direct_partition": {"total": 56421, "existing": 29773, "new": 26648},
        "family_adversarial_examples": [
            {"species": 18, "move": 173, "required_family": "machine"},
            {"species": 10, "move": 173, "required_family": "tutor"},
        ],
        "required_machine_rows_using_existing_tutor_move_ids": 2940,
        "required_machine_rows_using_existing_tutor_distinct_moves": 24,
        "required_tutor_rows_using_existing_machine_move_ids": 81,
        "required_tutor_rows_using_existing_machine_distinct_moves": 9,
        "completion_claim": "DIRECT_MACHINE_TUTOR_SUPPLY_26648_COMPLETE_CHECKPOINT_NOT_FULL_P03_DONE",
    }:
        _fail("Stage74 supply contract不一致")
    runtime = config.get("runtime", {})
    if (
        runtime.get("species_count") != SPECIES_COUNT
        or runtime.get("move_ids") != "1..1062"
        or runtime.get("side_change_project_move_id") != SIDE_CHANGE_MOVE_ID
        or runtime.get("side_change_source_routes_excluded") != 159
        or runtime.get("side_change_materialized") != 0
        or runtime.get("prohibited_species_keys") != list(PROHIBITED_SPECIES_KEYS)
        or runtime.get("prohibited_species_materialized") != 0
        or runtime.get("mode_ram") != "0x0203EC00"
        or runtime.get("candidate_capacity") != PAGE_SIZE
    ):
        _fail("Stage74 runtime ID/exclusion/capacity不一致")
    if runtime.get("modes") != {
        "normal": MODE_NORMAL, "egg": MODE_EGG,
        "machine_probe": MODE_MACHINE_PROBE,
        "machine_pages": list(range(MODE_MACHINE_PAGE_0, MODE_MACHINE_PAGE_LAST + 1)),
        "tutor": MODE_TUTOR,
    }:
        _fail("Stage74 transient mode ABI不一致")
    if runtime.get("unlock") != {
        "entry": "BAG_MOVE_MEMORY_ITEM_ONLY",
        "required_flag": "0x082C",
        "required_flag_name": "HALL_OF_FAME",
        "early_game_archive_available": False,
    }:
        _fail("Stage74 archive unlock contract不一致")
    economy = runtime.get("economy", {})
    if economy.get("price") != 0 or economy.get("status") != "PROVISIONAL_REPLACEABLE":
        _fail("Stage74 provisional economy contract不一致")
    if runtime.get("prohibited_coercions") != [
        "MACHINE_TO_EXISTING_TM_SLOT", "TUTOR_TO_EXISTING_TUTOR_SLOT",
        "MACHINE_OR_TUTOR_TO_LEVEL_ZERO", "MACHINE_OR_TUTOR_TO_EGG",
        "MACHINE_AND_TUTOR_TABLE_UNION",
    ]:
        _fail("Stage74 coercion禁止契約不一致")
    if runtime.get("build_learnable_moveset") != {
        "caller_capacity_u16": 429,
        "maximum_runtime_buffer_entries_after_archive_append": 238,
        "maximum_unique_entries_after_archive_append": 234,
        "maximum_species": 151,
        "runtime_buffer_headroom_u16": 191,
        "overflow_rows": 0,
        "preservation_only": {
            "selected_route_count_checked": 118369,
            "missing_path_count": 4014,
            "runtime_target_move_count": 2223,
            "species_count": 501,
            "max_rows_per_species": 22,
            "max_species": 576,
            "target_move_set_sha256": EXPECTED_FULL_PRESERVATION_TARGET_MOVE_SHA256,
            "ui_supply_routes_added": 0,
            "route_accounting_added": 0,
        },
        "purpose": "preserve selected legal P03 moves across battle effect-bank/backup-species restoration",
    }:
        _fail("Stage74 BuildLearnableMoveset capacity契約不一致")
    hooks = config.get("parent_abi", {}).get("hooks")
    if config.get("parent_abi", {}).get("get_move_relearner_consumers") != {
        "party_probe": {
            "call_address": "0x09114328", "call_hex": "fff754ff",
            "buffer_capacity_u16": 40,
        },
        "teach_ui_rebuild": {
            "entry": "0x091147AC", "call_address": "0x091147C2",
            "call_hex": "fff707fd", "candidate_count_store_offset": 26,
            "upstream_caller": "0x09097EDE", "upstream_caller_hex": "7cf065fc",
        },
    }:
        _fail("Stage74 GetMoveRelearner consumer ABI不一致")
    if hooks != [
        {
            "name": "VegaMoveMemory_GetMoveRelearnerMoves",
            "address": "0x091141D4", "width": 8,
            "target": "Stage74_GetMoveRelearnerMoves",
            "parent_hex": "004b184741495309",
        },
        {
            "name": "BuildLearnableMoveset",
            "address": "0x091143B8", "width": 8,
            "target": "Stage74_BuildLearnableMoveset",
            "parent_hex": "f0b5d6464f464646",
            "continuation_thumb": "0x091143C1",
            "continuation_parent_hex": "0022",
            "unique_caller": "0x090CC382",
            "unique_caller_hex": "48f019f8",
            "caller_buffer_capacity_u16": 429,
        },
    ]:
        _fail("Stage74 hook ABI不一致")
    move_memory = config["parent_abi"].get("move_memory", {})
    if (
        move_memory.get("allocation_sequence") != MOVE_MEMORY_SEQUENCE
        or move_memory.get("allocation_name") != "move_memory_runtime"
        or move_memory.get("allocation_start") != 19726128
        or move_memory.get("allocation_size") != 2968
        or move_memory.get("parent_content_sha256")
        != "f62631fbfabd7e1a3af77c0640140a0a27fab2cfe8f9076556aee7cab4cee40a"
        or move_memory.get("parent_rom_content_sha256")
        != "3b0e990853da8e4fa1a1f0c859ab624e7dbced767bf562891820f281bdb317af"
        or move_memory.get("known_parent_declared_effective_diff_spans") != [
            {"start": 19726244, "end_exclusive": 19726246, "size": 2},
            {"start": 19726366, "end_exclusive": 19726370, "size": 4},
            {"start": 19726940, "end_exclusive": 19726941, "size": 1},
            {"start": 19728917, "end_exclusive": 19728921, "size": 4},
        ]
        or move_memory.get("item_script_pointer_address") != "0x092D05B4"
        or move_memory.get("item_script_pointer_parent_hex") != "50072d09"
        or {key: _integer(value, key) for key, value in move_memory.get("old_script_entries", {}).items()}
        != EXPECTED_SCRIPT_ENTRIES
    ):
        _fail("Stage74 Move Memory parent ABI不一致")
    declarations = config.get("allocations")
    if not isinstance(declarations, list) or declarations != [{
        "name": "modernization_p03_stage74_supply_runtime_payload",
        "region": "integration_modules", "alignment": 16,
        "owner": TASK,
        "purpose": "family-separated direct machine/tutor archive tables, BuildLearnable-only preservation table, paged dispatcher, and bag UI scripts",
    }]:
        _fail("Stage74 allocation declaration不一致")
    return config


def require_pinned_parent(config: Mapping[str, Any]) -> None:
    parent = config.get("parent_identity", {})
    missing: list[str] = []
    if config.get("status") != "STAGE73_IDENTITY_PINNED":
        missing.append("status")
    if parent.get("stage73_commit") != "1dd2a9ab8da73f7eb17dbd5b8fa8fcd96109443e":
        missing.append("stage73_commit")
    for name in ("rom", "metadata", "allocation", "checkpoint", "route_audit", "incremental_bps"):
        row = parent.get(name)
        if not isinstance(row, dict) or not isinstance(row.get("path"), str) \
                or not isinstance(row.get("size"), int) \
                or not isinstance(row.get("sha256"), str) \
                or not _SHA_RE.fullmatch(row["sha256"]):
            missing.append(name)
    if parent.get("policy") != "FAIL_CLOSED_EXACT_STAGE73_COMMIT_AND_SIX_ARTIFACT_IDENTITIES":
        missing.append("policy")
    if missing:
        _fail("Stage73 identity未確定のためROM工程を拒否: " + ", ".join(missing))


@dataclass(frozen=True)
class SupplyRouteModel:
    machine_rows: dict[int, tuple[int, ...]]
    tutor_rows: dict[int, tuple[int, ...]]
    dependency_rows: tuple[tuple[str, int, str, str, int, str], ...]
    selected_rows: tuple[tuple[str, int, str, int], ...]
    route_audit: dict[str, Any]


def compile_supply_routes(root: Path, config: Mapping[str, Any]) -> SupplyRouteModel:
    """固定ZIPを一度streamし、direct supply 26,648件をfamily別にcompileする。"""

    contract = _json(_fixed_raw(root, config["inputs"]["p03_contract"], "P03 contract"), "P03 contract")
    handoff = _json(
        _fixed_raw(root, config["inputs"]["p03_runtime_handoff"], "P03 runtime handoff"),
        "P03 runtime handoff",
    )
    index = _json(
        _fixed_raw(root, config["inputs"]["p03_compiled_index"], "P03 compiled index"),
        "P03 compiled index",
    )
    _fixed_raw(root, config["inputs"]["learnsets_zip"], "P03 learnsets ZIP")
    supply_contract = contract.get("runtime_supply", {})
    if (
        contract.get("status") != "PASS"
        or contract.get("corrected_adoption", {}).get("routes") != 118528
        or contract.get("runtime_selection", {}).get("selected_routes") != 118369
        or supply_contract.get("supply_required_rows") != 26648
        or supply_contract.get("supply_required_rows_by_family") != {"machine": 26279, "tutor": 369}
        or supply_contract.get("supply_required_distinct_moves_by_family") != {"machine": 184, "tutor": 31}
        or supply_contract.get("supply_required_set_sha256")
        != config["supply_contract"]["supply_required_set_sha256"]
    ):
        _fail("P03 source supply contract不一致")
    side = handoff.get("side_change_1063", {})
    if (
        handoff.get("status") != "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS"
        or side.get("project_move_id") != SIDE_CHANGE_MOVE_ID
        or side.get("status") != "NOT_ADOPTED_BY_USER_DECISION"
        or side.get("source_route_count") != 159
        or side.get("adopted_route_count") != 0
        or side.get("routes_by_consumer") != EXPECTED_SIDE_CHANGE_COUNTS
        or side.get("decision", {}).get("replacement_move_key") is not None
        or side.get("decision", {}).get("runtime_action") != "DO_NOT_IMPLEMENT_OR_ALLOCATE"
    ):
        _fail("P03 Side Change非採用境界不一致")
    if (
        index.get("record_count") != 1300
        or index.get("route_count") != 118528
        or index.get("selected_route_count") != 118369
        or index.get("excluded_route_count") != 159
    ):
        _fail("P03 compiled index境界不一致")

    rows: dict[str, dict[int, list[int]]] = {
        "machine": defaultdict(list), "tutor": defaultdict(list),
    }
    source_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    supply_counts: Counter[str] = Counter()
    existing_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    supply_moves: dict[str, set[int]] = {"machine": set(), "tutor": set()}
    existing_moves: dict[str, set[int]] = {"machine": set(), "tutor": set()}
    supply_pairs: set[tuple[int, str, int]] = set()
    existing_projection: set[tuple[int, str, int, int]] = set()
    route_keys: set[str] = set()
    selected_rows: list[tuple[str, int, str, int]] = []
    direct_reference: dict[tuple[str, str, int], list[tuple[int, str]]] = defaultdict(list)
    dependency_rows: list[tuple[str, int, str, str, int]] = []
    prohibited_source_routes = 0

    zip_path = root / config["inputs"]["learnsets_zip"]["path"]
    for compiled in iter_compiled_p03_routes(root, zip_path):
        consumer = str(compiled.get("consumer"))
        source = compiled.get("source_route")
        if consumer not in EXPECTED_SOURCE_COUNTS or not isinstance(source, dict):
            _fail(f"未知のcompiled route consumer: {consumer}")
        source_counts[consumer] += 1
        species = _integer(compiled.get("target_species_id"), "target species")
        move = _integer(source.get("project_move_id"), "project move")
        route_key = f"{compiled.get('target_species_key')}:{source.get('route_id')}"
        if route_key in route_keys:
            _fail(f"target+route重複: {route_key}")
        route_keys.add(route_key)
        if compiled.get("target_species_key") in PROHIBITED_SPECIES_KEYS:
            prohibited_source_routes += 1
        if move == SIDE_CHANGE_MOVE_ID:
            side_counts[consumer] += 1
            continue
        if compiled.get("runtime_move_ready") is not True or not 1 <= move <= MOVE_LAST:
            _fail(f"runtime Move境界不一致: {route_key}/{move}")
        method = str(source.get("method"))
        selected_rows.append((consumer, species, method, move))
        family = "tutor" if method == "tutor" else "machine"
        if consumer in {"machine", "tutor"}:
            if (consumer == "machine" and method not in {"tm", "tr"}) \
                    or (consumer == "tutor" and method != "tutor"):
                _fail(f"direct family/method不一致: {route_key}/{consumer}/{method}")
            runtime_supply = compiled.get("runtime_supply")
            if not isinstance(runtime_supply, dict):
                _fail(f"runtime supply欠落: {route_key}")
            status = runtime_supply.get("status")
            direct_reference[(str(compiled.get("reference_id")), family, move)].append(
                (species, str(status))
            )
            if status == "EXISTING_RUNTIME_SLOT":
                slot = runtime_supply.get("runtime_slot_zero_based")
                if not isinstance(slot, int) or isinstance(slot, bool) or slot < 0:
                    _fail(f"EXISTING_RUNTIME_SLOT slot不正: {route_key}/{slot}")
                projection = (species, family, move, slot)
                if projection in existing_projection:
                    _fail(f"existing projection重複: {projection}")
                existing_projection.add(projection)
                existing_counts[family] += 1
                existing_moves[family].add(move)
            elif status == "SUPPLY_REQUIRED":
                if runtime_supply.get("runtime_slot_zero_based") is not None:
                    _fail(f"SUPPLY_REQUIRED routeに既存slotがあります: {route_key}")
                pair = (species, family, move)
                if pair in supply_pairs:
                    _fail(f"species+family+move重複: {pair}")
                supply_pairs.add(pair)
                rows[family][species].append(move)
                supply_counts[family] += 1
                supply_moves[family].add(move)
                method_counts[method] += 1
            else:
                _fail(f"runtime supply status不一致: {route_key}/{status}")
        if consumer in {"pre_evolution_carry", "form_change"} \
                and method in {"tm", "tr", "tutor"}:
            dependency_rows.append((
                consumer,
                species,
                f"{source.get('source_game')}:{source.get('source_key')}",
                family,
                move,
            ))

    if len(route_keys) != 118528 or dict(source_counts) != EXPECTED_SOURCE_COUNTS:
        _fail(f"全P03 source route集合不一致: {len(route_keys)}/{dict(source_counts)}")
    if len(selected_rows) != 118369:
        _fail(f"Side Change除外後selected route件数不一致: {len(selected_rows)}")
    if dict(side_counts) != EXPECTED_SIDE_CHANGE_COUNTS or sum(side_counts.values()) != 159:
        _fail(f"Side Change 159件除外不一致: {dict(side_counts)}")
    if prohibited_source_routes:
        _fail(f"Browt/Pombon/Gecqua route混入: {prohibited_source_routes}")
    if supply_counts != Counter({"machine": 26279, "tutor": 369}):
        _fail(f"supply route件数不一致: {dict(supply_counts)}")
    if existing_counts != Counter({"machine": 29033, "tutor": 740}):
        _fail(f"existing slot route件数不一致: {dict(existing_counts)}")
    if method_counts != Counter({"tm": 24391, "tr": 1888, "tutor": 369}):
        _fail(f"supply method内訳不一致: {dict(method_counts)}")
    if {key: len(value) for key, value in supply_moves.items()} != {"machine": 184, "tutor": 31}:
        _fail("supply distinct Move件数不一致")
    expected_set_sha = config["supply_contract"]["supply_required_set_sha256"]
    actual_set_sha = _set_sha(
        f"{species}:{family}:{move}" for species, family, move in supply_pairs
    )
    if actual_set_sha != expected_set_sha:
        _fail(f"supply triplet set digest不一致: {actual_set_sha}")
    family_hashes = {
        family: _set_sha(
            f"{species}:{pair_family}:{move}"
            for species, pair_family, move in supply_pairs if pair_family == family
        )
        for family in ("machine", "tutor")
    }
    if family_hashes != {
        "machine": EXPECTED_MACHINE_SET_SHA256,
        "tutor": EXPECTED_TUTOR_SET_SHA256,
    }:
        _fail(f"family別supply digest不一致: {family_hashes}")
    existing_projection_sha = _set_sha(
        f"{species}:{family}:{move}:{slot}"
        for species, family, move, slot in existing_projection
    )
    if existing_projection_sha != EXPECTED_EXISTING_PROJECTION_SHA256:
        _fail(f"existing projection digest不一致: {existing_projection_sha}")
    cross_family_move_ids = tuple(sorted(supply_moves["machine"] & supply_moves["tutor"]))
    if cross_family_move_ids != EXPECTED_CROSS_FAMILY_MOVE_IDS:
        _fail(f"machine/tutor cross-family Move ID集合不一致: {cross_family_move_ids}")
    same_species_cross_family = {
        (species, move)
        for species in set(rows["machine"]) & set(rows["tutor"])
        for move in set(rows["machine"][species]) & set(rows["tutor"][species])
    }
    if same_species_cross_family:
        _fail(f"同一species machine/tutor pair重複: {sorted(same_species_cross_family)[:3]}")
    if 173 not in rows["machine"].get(18, ()) or 173 in rows["tutor"].get(18, ()) \
            or 173 not in rows["tutor"].get(10, ()) or 173 in rows["machine"].get(10, ()):
        _fail("family分離adversarial species/move境界不一致")
    cross_existing_stats = {
        "required_machine_rows_using_existing_tutor_move_ids": sum(
            move in existing_moves["tutor"] for species, family, move in supply_pairs
            if family == "machine"
        ),
        "required_machine_distinct_moves_using_existing_tutor_move_ids": len(
            supply_moves["machine"] & existing_moves["tutor"]
        ),
        "required_tutor_rows_using_existing_machine_move_ids": sum(
            move in existing_moves["machine"] for species, family, move in supply_pairs
            if family == "tutor"
        ),
        "required_tutor_distinct_moves_using_existing_machine_move_ids": len(
            supply_moves["tutor"] & existing_moves["machine"]
        ),
    }
    if cross_existing_stats != {
        "required_machine_rows_using_existing_tutor_move_ids": 2940,
        "required_machine_distinct_moves_using_existing_tutor_move_ids": 24,
        "required_tutor_rows_using_existing_machine_move_ids": 81,
        "required_tutor_distinct_moves_using_existing_machine_move_ids": 9,
    }:
        _fail(f"family collapse adversarial集計不一致: {cross_existing_stats}")

    frozen = {
        family: {species: tuple(moves) for species, moves in sorted(group.items())}
        for family, group in rows.items()
    }
    maxima = {
        family: max((len(moves), species) for species, moves in group.items())
        for family, group in frozen.items()
    }
    if maxima != {"machine": (131, 151), "tutor": (12, 762)}:
        _fail(f"species別最大行数不一致: {maxima}")
    if (len(frozen["machine"]), len(frozen["tutor"])) != (1286, 138):
        _fail("supply target species件数不一致")

    dependency_resolution = Counter()
    resolved_dependency_rows: list[tuple[str, int, str, str, int, str]] = []
    fallback_rows: list[dict[str, Any]] = []
    for consumer, target, reference, family, move in dependency_rows:
        candidates = direct_reference.get((reference, family, move), [])
        if candidates:
            statuses = {status for _, status in candidates}
            if "SUPPLY_REQUIRED" in statuses:
                resolution = "REFERENCE_STAGE74_ARCHIVE"
            else:
                resolution = "REFERENCE_EXISTING_SLOT"
            dependency_resolution[resolution.lower()] += 1
            resolved_dependency_rows.append(
                (consumer, target, reference, family, move, resolution)
            )
            continue
        target_candidates = [
            (species, status)
            for (direct_ref, direct_family, direct_move), values in direct_reference.items()
            if direct_family == family and direct_move == move
            for species, status in values if species == target
        ]
        if not target_candidates:
            _fail(f"carry/form upstream owner未解決: {consumer}/{target}/{reference}/{family}/{move}")
        statuses = {status for _, status in target_candidates}
        fallback_status = (
            "TARGET_STAGE74_ARCHIVE" if "SUPPLY_REQUIRED" in statuses
            else "TARGET_EXISTING_SLOT"
        )
        dependency_resolution[fallback_status.lower()] += 1
        resolved_dependency_rows.append(
            (consumer, target, reference, family, move, fallback_status)
        )
        fallback_rows.append({
            "consumer": consumer, "target_species": target,
            "missing_reference": reference, "family": family, "move": move,
            "fallback": fallback_status,
        })
    if len(dependency_rows) != 23595 or len(fallback_rows) != 38 \
            or {row["target_species"] for row in fallback_rows} != {1263} \
            or {row["missing_reference"] for row in fallback_rows} != {"scarletviolet:0744.01"}:
        _fail("carry/form upstream dependency/fallback境界不一致")

    route_audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS_DIRECT_SUPPLY_BOUNDARY",
        "source_route_count": len(route_keys),
        "source_consumer_counts": dict(sorted(source_counts.items())),
        "direct_supply": {
            "route_count": sum(supply_counts.values()),
            "species_family_move_pair_count": len(supply_pairs),
            "duplicate_species_family_move_pairs": 0,
            "families": {
                family: {
                    "routes": supply_counts[family],
                    "species": len(frozen[family]),
                    "distinct_moves": len(supply_moves[family]),
                    "max_rows_per_species": maxima[family][0],
                    "max_species": maxima[family][1],
                }
                for family in ("machine", "tutor")
            },
            "methods": dict(sorted(method_counts.items())),
            "set_sha256": actual_set_sha,
            "family_set_sha256": family_hashes,
            "cross_family_same_move_id_count": len(cross_family_move_ids),
            "cross_family_same_move_ids": list(cross_family_move_ids),
            "same_species_cross_family_pair_count": len(same_species_cross_family),
            "family_adversarial_examples": config["supply_contract"]["family_adversarial_examples"],
            "family_collapse_risk_counts": cross_existing_stats,
            "existing_slot_routes_preserved": dict(sorted(existing_counts.items())),
            "existing_slot_projection_set_sha256": existing_projection_sha,
            "selected_direct_partition": {
                "total": sum(supply_counts.values()) + sum(existing_counts.values()),
                "existing": sum(existing_counts.values()),
                "new": sum(supply_counts.values()),
            },
        },
        "upstream_carry_form_dependency": {
            "path_count": len(dependency_rows),
            "resolution_counts": dict(sorted(dependency_resolution.items())),
            "reference_owner_missing_paths": len(fallback_rows),
            "reference_owner_missing_scope": "OWN_TEMPO_ROCKRUFF_0744_01_ONLY",
            "target_direct_equivalent_fallbacks": fallback_rows,
            "claim": "AUDITED_BUT_FULL_P03_DONE_WITHHELD_PENDING_INDEPENDENT_OWNER_REVIEW",
        },
        "exclusions": {
            "side_change_project_move_id": SIDE_CHANGE_MOVE_ID,
            "side_change_source_routes": 159,
            "side_change_by_consumer": dict(sorted(side_counts.items())),
            "side_change_materialized": 0,
            "browt_pombon_gecqua_source_routes": prohibited_source_routes,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
        },
        "completion_claim": config["supply_contract"]["completion_claim"],
        "full_p03_done": False,
    }
    return SupplyRouteModel(
        machine_rows=frozen["machine"],
        tutor_rows=frozen["tutor"],
        dependency_rows=tuple(resolved_dependency_rows),
        selected_rows=tuple(selected_rows),
        route_audit=route_audit,
    )


@dataclass(frozen=True)
class IndexedMoveTable:
    index: bytes
    moves: bytes
    species_with_rows: int
    move_count: int
    max_rows: int
    max_species: int
    page_histogram: dict[int, int]


def _build_indexed_table(rows: Mapping[int, Sequence[int]], label: str) -> IndexedMoveTable:
    offsets: list[int] = []
    moves: list[int] = []
    page_histogram: Counter[int] = Counter()
    maximum = (0, 0)
    for species in range(SPECIES_COUNT):
        offsets.append(len(moves))
        values = tuple(rows.get(species, ()))
        if len(values) != len(set(values)):
            _fail(f"{label} species {species} Move重複")
        if any(not 1 <= value <= MOVE_LAST for value in values):
            _fail(f"{label} species {species} Move範囲不一致")
        if values:
            pages = (len(values) + PAGE_SIZE - 1) // PAGE_SIZE
            page_histogram[pages] += 1
            if values[(pages - 1) * PAGE_SIZE:] == ():
                _fail(f"{label} species {species} 最終pageが空です")
        moves.extend(values)
        maximum = max(maximum, (len(values), species))
    offsets.append(len(moves))
    if len(offsets) != SPECIES_COUNT + 1 or len(moves) > 0xFFFF:
        _fail(f"{label} indexed U16 ABI容量不一致")
    return IndexedMoveTable(
        index=struct.pack(f"<{len(offsets)}H", *offsets),
        moves=struct.pack(f"<{len(moves)}H", *moves),
        species_with_rows=sum(bool(rows.get(species)) for species in range(SPECIES_COUNT)),
        move_count=len(moves),
        max_rows=maximum[0],
        max_species=maximum[1],
        page_histogram=dict(sorted(page_histogram.items())),
    )


def build_runtime_tables(
    model: SupplyRouteModel,
    capacity_audit: Mapping[str, Any],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    preservation = capacity_audit.get("preservation_only", {})
    preservation_rows = {
        _integer(row.get("species"), "preservation species"):
            tuple(_integer(move, "preservation move") for move in row.get("moves", ()))
        for row in preservation.get("runtime_rows", ())
        if isinstance(row, dict)
    }
    tables = {
        "Machine": _build_indexed_table(model.machine_rows, "machine"),
        "Tutor": _build_indexed_table(model.tutor_rows, "tutor"),
        "Preservation": _build_indexed_table(
            preservation_rows, "BuildLearnable preservation-only"
        ),
    }
    if tables["Machine"].move_count != 26279 or tables["Tutor"].move_count != 369:
        _fail("Stage74 runtime table行数不一致")
    if tables["Machine"].max_rows != 131 or max(tables["Machine"].page_histogram) != 4:
        _fail("Stage74 machine paging上限不一致")
    if tables["Tutor"].max_rows != 12 or max(tables["Tutor"].page_histogram) != 1:
        _fail("Stage74 tutor単一page境界不一致")
    if (
        tables["Preservation"].move_count != 2223
        or tables["Preservation"].species_with_rows != 501
        or tables["Preservation"].max_rows != 22
        or tables["Preservation"].max_species != 576
        or preservation.get("target_move_set_sha256")
        != EXPECTED_FULL_PRESERVATION_TARGET_MOVE_SHA256
    ):
        _fail("Stage74 BuildLearnable preservation-only table境界不一致")
    blobs: dict[str, bytes] = {}
    audit: dict[str, Any] = {}
    for name, table in tables.items():
        blobs[f"Stage74_{name}Index"] = table.index
        blobs[f"Stage74_{name}Moves"] = table.moves
        audit[name.lower()] = {
            "index_entries": SPECIES_COUNT + 1,
            "index_size": len(table.index),
            "index_sha256": sha256(table.index),
            "move_rows": table.move_count,
            "move_size": len(table.moves),
            "move_sha256": sha256(table.moves),
            "species_with_rows": table.species_with_rows,
            "max_rows_per_species": table.max_rows,
            "max_species": table.max_species,
            "page_size": PAGE_SIZE,
            "page_histogram": {str(key): value for key, value in table.page_histogram.items()},
            "empty_final_pages": 0,
            "silent_drop_count": 0,
        }
    return blobs, audit


def archive_page(
    rows: Mapping[int, Sequence[int]], species: int, page: int,
    known_moves: Iterable[int] = (),
) -> tuple[int, ...]:
    """C dispatcherと同じ固定raw-bank/既知技除外をhost unitで確認する。"""

    if not 0 <= species < SPECIES_COUNT or page < 0:
        return ()
    values = tuple(rows.get(species, ()))
    pages = (len(values) + PAGE_SIZE - 1) // PAGE_SIZE
    if page >= pages:
        return ()
    known = set(known_moves)
    return tuple(move for move in values[page * PAGE_SIZE:(page + 1) * PAGE_SIZE] if move not in known)


def archive_probe(
    rows: Mapping[int, Sequence[int]], species: int,
    known_moves: Iterable[int] = (),
) -> tuple[int, ...]:
    """party selector用probe。40件目までではなく全bankから未習得を探す。"""

    if not 0 <= species < SPECIES_COUNT:
        return ()
    known = set(known_moves)
    return tuple(move for move in rows.get(species, ()) if move not in known)[:1]


def audit_build_learnable_capacity(
    root: Path,
    config: Mapping[str, Any],
    parent: bytes,
    model: SupplyRouteModel,
) -> dict[str, Any]:
    """BuildLearnableMovesetとStage74 appendを固定ROMから全種再現する。"""

    def read_u16(offset: int, label: str) -> int:
        if not 0 <= offset <= len(parent) - 2:
            _fail(f"{label} U16範囲外: 0x{offset:X}")
        return struct.unpack_from("<H", parent, offset)[0]

    def read_u32(offset: int, label: str) -> int:
        if not 0 <= offset <= len(parent) - 4:
            _fail(f"{label} U32範囲外: 0x{offset:X}")
        return struct.unpack_from("<I", parent, offset)[0]

    def address_offset(address: int, width: int, label: str) -> int:
        return _rom_offset(address, width, label)

    roots = {
        "level_pointer_table": read_u32(0x0004346C, "level root"),
        "egg_table": read_u32(0x00045214, "egg root"),
        "egg_table_secondary": read_u32(0x0004528C, "egg secondary root"),
        "machine_compatibility": read_u32(0x000432B4, "machine compatibility root"),
        "machine_catalog": read_u32(0x001263D8, "machine catalog root"),
        "tutor_compatibility": read_u32(0x00121420, "tutor compatibility root"),
        "tutor_catalog": read_u32(0x001213D4, "tutor catalog root"),
    }
    expected_roots = {
        "level_pointer_table": 0x094E95A8,
        "egg_table": 0x09FF0BD4,
        "egg_table_secondary": 0x09FF0BD4,
        "machine_compatibility": 0x094EAFC0,
        "machine_catalog": 0x0944BB80,
        "tutor_compatibility": 0x094F1820,
        "tutor_catalog": 0x0944BC80,
    }
    if roots != expected_roots:
        _fail(f"BuildLearnable parent table root不一致: {roots}")

    egg_rows: dict[int, list[int]] = {}
    cursor = address_offset(roots["egg_table"], 2, "egg table")
    active: int | None = None
    egg_raw_start = cursor
    for _ in range(20_000):
        value = read_u16(cursor, "egg table row")
        cursor += 2
        if value == 0xFFFF:
            break
        if value >= 20_000:
            species = value - 20_000
            if not 0 <= species < SPECIES_COUNT or species in egg_rows:
                _fail(f"egg marker不正: {species}")
            active = species
            egg_rows[species] = []
        else:
            if active is None or not 1 <= value <= MOVE_LAST:
                _fail(f"egg Move row不正: {value}")
            egg_rows[active].append(value)
    else:
        _fail("egg tableが20,000 U16以内に終端しません")
    egg_raw = parent[egg_raw_start:cursor]
    if len(egg_rows) != 1399 or sum(map(len, egg_rows.values())) != 6109:
        _fail("Stage73 egg table logical identity不一致")

    manifest_raw = _fixed_raw(root, config["inputs"]["species_manifest"], "species manifest")
    try:
        manifest_rows = list(csv.DictReader(io.StringIO(manifest_raw.decode("utf-8-sig"))))
    except UnicodeDecodeError as error:
        _fail(f"species manifest UTF-8不正: {error}")
    national_dex: dict[int, int] = {}
    for row in manifest_rows:
        species = _integer(row.get("id"), "species manifest id")
        dex = _integer(row.get("canonical_national_dex"), "species manifest national dex")
        if species in national_dex:
            _fail(f"species manifest id重複: {species}")
        national_dex[species] = dex
    if set(range(SPECIES_COUNT)) - set(national_dex):
        _fail("species manifestがStage74全speciesを覆っていません")

    evolution_table = address_offset(0x0821615C, 412 * 40, "GetEggSpecies evolution table")
    exact_egg_species = {203, 324, 364, 608, 719, 724, 727}
    national_override = {25: 24, 479: 742, 666: 953, 676: 965}
    incense_without_item = {
        617: 534, 608: 517, 727: 491, 725: 480, 719: 648,
        724: 519, 696: 618, 734: 546, 364: 365,
    }

    def egg_species(species: int) -> int:
        current = species
        # FireRed GetEggSpecies 0x08044F34: 411 species x 5 slots, at most 5 descents.
        for _ in range(5):
            found: int | None = None
            for candidate in range(1, 412):
                row = evolution_table + candidate * 40
                for slot in range(5):
                    if read_u16(row + slot * 8 + 4, "evolution target") == current:
                        found = candidate
                        break
                if found is not None:
                    break
            if found is None:
                break
            current = found
        return current

    def all_egg_moves(species: int) -> list[int]:
        # Stage73's seven exact-conflict species bypass legacy family union.
        if species in exact_egg_species:
            return list(egg_rows.get(species, ()))
        primary = egg_species(species)
        primary = national_override.get(national_dex.get(primary, 0), primary)
        result = list(egg_rows.get(primary, ()))
        seen = set(result)
        secondary = incense_without_item.get(primary, primary)
        if secondary != primary:
            result.extend(move for move in egg_rows.get(secondary, ()) if move not in seen)
        return result

    level_root = address_offset(roots["level_pointer_table"], SPECIES_COUNT * 4, "level pointer table")
    machine_root = address_offset(roots["machine_compatibility"], SPECIES_COUNT * 16, "machine compatibility")
    machine_catalog_root = address_offset(roots["machine_catalog"], 128 * 2, "machine catalog")
    tutor_root = address_offset(roots["tutor_compatibility"], SPECIES_COUNT * 16, "tutor compatibility")
    tutor_catalog_root = address_offset(roots["tutor_catalog"], 64 * 2, "tutor catalog")
    machine_catalog = [read_u16(machine_catalog_root + slot * 2, "machine catalog") for slot in range(128)]
    tutor_catalog = [read_u16(tutor_catalog_root + slot * 2, "tutor catalog") for slot in range(64)]

    dependencies_by_target: dict[
        int, list[tuple[str, int, str, str, int, str]]
    ] = defaultdict(list)
    for row in model.dependency_rows:
        dependencies_by_target[row[1]].append(row)
    selected_by_target: dict[int, list[tuple[str, int, str, int]]] = defaultdict(list)
    for row in model.selected_rows:
        selected_by_target[row[1]].append(row)
    dependency_missing_paths: list[tuple[str, int, str, str, int, str]] = []
    dependency_missing_triplets: set[tuple[int, str, int]] = set()
    preservation_missing_paths: list[tuple[str, int, str, int]] = []
    preservation_target_moves: set[tuple[int, int]] = set()
    preservation_rows: dict[int, tuple[int, ...]] = {}
    digest = FramedDigest()
    maximum_buffer = (-1, -1)
    maximum_unique = (-1, -1)
    maximum_structural_bound = (-1, -1)
    maximum_detail: dict[str, Any] = {}
    overflow_species: list[int] = []
    max_egg = (-1, -1)
    for species in range(SPECIES_COUNT):
        level_pointer = read_u32(level_root + species * 4, f"species {species} level pointer")
        level_cursor = address_offset(level_pointer, 3, f"species {species} level rows")
        level_moves: list[int] = []
        for _ in range(40):
            move = read_u16(level_cursor, f"species {species} level move")
            level = parent[level_cursor + 2]
            level_cursor += 3
            if move == 0 and level == 0xFF:
                break
            # The parent helper copies non-terminating MOVE_NONE/level rows too.
            if not 0 <= move <= MOVE_LAST:
                _fail(f"species {species} level Move範囲不一致: {move}")
            level_moves.append(move)
        else:
            _fail(f"species {species} level tableが40行以内に終端しません")

        egg_moves = all_egg_moves(species)
        max_egg = max(max_egg, (len(egg_moves), species))
        machine_bits = parent[machine_root + species * 16:machine_root + (species + 1) * 16]
        tutor_bits = parent[tutor_root + species * 16:tutor_root + (species + 1) * 16]
        machine_moves = [
            machine_catalog[slot] for slot in range(128)
            if machine_bits[slot // 8] & (1 << (slot % 8))
        ]
        tutor_moves = [
            tutor_catalog[slot] for slot in range(64)
            if tutor_bits[slot // 8] & (1 << (slot % 8)) and tutor_catalog[slot] != 0
        ]
        parent_buffer = level_moves + egg_moves + machine_moves + tutor_moves
        archive_moves = list(model.machine_rows.get(species, ())) \
            + list(model.tutor_rows.get(species, ()))
        current_learnable = set(parent_buffer) | set(archive_moves)
        species_dependency_missing = [
            row for row in dependencies_by_target.get(species, ())
            if row[4] not in current_learnable
        ]
        dependency_missing_paths.extend(species_dependency_missing)
        dependency_missing_triplets.update(
            (species, row[3], row[4]) for row in species_dependency_missing
        )
        species_missing = [
            row for row in selected_by_target.get(species, ())
            if row[3] not in current_learnable
        ]
        preservation_missing_paths.extend(species_missing)
        preservation_target_moves.update(
            (species, row[3]) for row in species_missing
        )
        preservation_moves = tuple(sorted({row[3] for row in species_missing}))
        if preservation_moves:
            preservation_rows[species] = preservation_moves

        output_buffer = list(parent_buffer)
        for move in archive_moves + list(preservation_moves):
            if move not in output_buffer:
                output_buffer.append(move)
        buffer_count = len(output_buffer)
        unique_count = len(set(output_buffer))
        if buffer_count > 429:
            overflow_species.append(species)
        maximum_buffer = max(maximum_buffer, (buffer_count, species))
        maximum_unique = max(maximum_unique, (unique_count, species))
        structural_bound = 40 + 50 + len(machine_moves) + len(tutor_moves) \
            + len(archive_moves) + len(preservation_moves)
        maximum_structural_bound = max(
            maximum_structural_bound, (structural_bound, species)
        )
        row = {
            "species": species,
            "parent_buffer_entries": len(parent_buffer),
            "parent_unique_entries": len(set(parent_buffer)),
            "level_entries": len(level_moves),
            "egg_entries_after_family_incense_resolution": len(egg_moves),
            "legacy_machine_entries": len(machine_moves),
            "legacy_tutor_entries": len(tutor_moves),
            "archive_machine_entries": len(model.machine_rows.get(species, ())),
            "archive_tutor_entries": len(model.tutor_rows.get(species, ())),
            "preservation_only_entries": len(preservation_moves),
            "output_buffer_entries": buffer_count,
            "output_unique_entries": unique_count,
        }
        digest.add(row)
        if species == 151:
            maximum_detail = row

    dependency_family_counts = Counter(
        family for _species, family, _move in dependency_missing_triplets
    )
    dependency_owner_path_counts = Counter(row[5] for row in dependency_missing_paths)
    dependency_owner_by_triplet: dict[tuple[int, str, int], set[str]] = defaultdict(set)
    for _consumer, target, _reference, family, move, resolution in dependency_missing_paths:
        dependency_owner_by_triplet[(target, family, move)].add(resolution)
    if any(len(values) != 1 for values in dependency_owner_by_triplet.values()):
        _fail("machine/tutor dependency tripletのsource owner resolutionが一意ではありません")
    dependency_owner_unique_counts = Counter(
        next(iter(values)) for values in dependency_owner_by_triplet.values()
    )
    dependency_triplet_sha = _set_sha(
        f"{species}:{family}:{move}"
        for species, family, move in dependency_missing_triplets
    )
    dependency_target_moves = {
        (species, move) for species, _family, move in dependency_missing_triplets
    }
    dependency_target_move_sha = _set_sha(
        f"{species}:{move}" for species, move in dependency_target_moves
    )
    if (
        len(dependency_missing_paths) != 31
        or len(dependency_missing_triplets) != 23
        or len(dependency_target_moves) != 23
        or dependency_family_counts != Counter({"machine": 16, "tutor": 7})
        or dependency_triplet_sha != EXPECTED_PRESERVATION_TRIPLET_SHA256
        or dependency_target_move_sha != EXPECTED_PRESERVATION_TARGET_MOVE_SHA256
    ):
        _fail(
            "carry/form machine/tutor target preservation回帰集合不一致: "
            f"paths={len(dependency_missing_paths)} "
            f"triplets={len(dependency_missing_triplets)} "
            f"target_moves={len(dependency_target_moves)} "
            f"families={dict(dependency_family_counts)} "
            f"triplet_sha={dependency_triplet_sha} "
            f"target_move_sha={dependency_target_move_sha}"
        )

    preservation_consumer_counts = Counter(row[0] for row in preservation_missing_paths)
    preservation_method_counts = Counter(row[2] for row in preservation_missing_paths)
    preservation_origins: dict[tuple[int, int], dict[str, set[str]]] = defaultdict(
        lambda: {"consumers": set(), "methods": set()}
    )
    for consumer, target, method, move in preservation_missing_paths:
        preservation_origins[(target, move)]["consumers"].add(consumer)
        preservation_origins[(target, move)]["methods"].add(method)
    preservation_target_move_sha = _set_sha(
        f"{species}:{move}" for species, move in preservation_target_moves
    )

    maximum_preservation_row = max(
        (len(moves), species) for species, moves in preservation_rows.items()
    )
    if (
        len(preservation_missing_paths) != 4014
        or len(preservation_target_moves) != 2223
        or len(preservation_rows) != 501
        or maximum_preservation_row != (22, 576)
        or preservation_target_move_sha
        != EXPECTED_FULL_PRESERVATION_TARGET_MOVE_SHA256
        or preservation_consumer_counts != Counter(EXPECTED_PRESERVATION_CONSUMER_COUNTS)
        or preservation_method_counts != Counter(EXPECTED_PRESERVATION_METHOD_COUNTS)
    ):
        _fail(
            "full selected-route BuildLearnable preservation集合不一致: "
            f"paths={len(preservation_missing_paths)} "
            f"target_moves={len(preservation_target_moves)} "
            f"species={len(preservation_rows)} max={maximum_preservation_row} "
            f"sha={preservation_target_move_sha} "
            f"consumers={dict(preservation_consumer_counts)} "
            f"methods={dict(preservation_method_counts)}"
        )

    if maximum_buffer != (238, 151) or maximum_unique != (234, 151) \
            or maximum_structural_bound != (319, 151) \
            or overflow_species or max_egg != (37, 390):
        _fail(
            "BuildLearnable全species capacity不一致: "
            f"buffer={maximum_buffer} unique={maximum_unique} "
            f"bound={maximum_structural_bound} egg={max_egg} "
            f"overflow={overflow_species[:3]}"
        )
    if maximum_detail != {
        "species": 151,
        "parent_buffer_entries": 110,
        "parent_unique_entries": 106,
        "level_entries": 12,
        "egg_entries_after_family_incense_resolution": 0,
        "legacy_machine_entries": 98,
        "legacy_tutor_entries": 0,
        "archive_machine_entries": 131,
        "archive_tutor_entries": 0,
        "preservation_only_entries": 0,
        "output_buffer_entries": 238,
        "output_unique_entries": 234,
    }:
        _fail(f"BuildLearnable max species内訳不一致: {maximum_detail}")
    return {
        "status": "PASS_EXACT_ROM_TABLE_ORACLE",
        "species_checked": SPECIES_COUNT,
        "caller_buffer_capacity_u16": 429,
        "maximum_runtime_buffer_entries_after_archive_append": maximum_buffer[0],
        "maximum_unique_entries_after_archive_append": maximum_unique[0],
        "maximum_species": maximum_buffer[1],
        "runtime_buffer_headroom_u16": 429 - maximum_buffer[0],
        "structural_nondeduplicated_upper_bound": maximum_structural_bound[0],
        "structural_upper_bound_species": maximum_structural_bound[1],
        "structural_upper_bound_formula": (
            "level_function_cap40 + egg_function_cap50 + legacy_machine_bit_count "
            "+ legacy_tutor_low64_bit_count + archive_raw_rows "
            "+ preservation_only_raw_rows"
        ),
        "structural_upper_bound_headroom_u16": 429 - maximum_structural_bound[0],
        "overflow_species_count": len(overflow_species),
        "maximum_species_breakdown": maximum_detail,
        "maximum_egg_entries_after_family_incense_resolution": max_egg[0],
        "maximum_egg_species": max_egg[1],
        "species_accounting_sha256": digest.hexdigest(),
        "preservation_only": {
            "derivation": (
                "all 118369 selected non-Side-Change target species+move routes minus "
                "the exact current-target parent BuildLearnable buffer and the "
                "current-target Stage74 direct archive"
            ),
            "selected_route_count_checked": len(model.selected_rows),
            "missing_path_count": len(preservation_missing_paths),
            "runtime_target_move_count": len(preservation_target_moves),
            "species_count": len(preservation_rows),
            "max_rows_per_species": maximum_preservation_row[0],
            "max_species": maximum_preservation_row[1],
            "target_move_set_sha256": preservation_target_move_sha,
            "missing_path_consumer_counts": dict(
                sorted(preservation_consumer_counts.items())
            ),
            "missing_path_method_counts": dict(sorted(preservation_method_counts.items())),
            "unique_pair_origins": [
                {
                    "species": species,
                    "move": move,
                    "consumers": sorted(origins["consumers"]),
                    "methods": sorted(origins["methods"]),
                }
                for (species, move), origins in sorted(preservation_origins.items())
            ],
            "runtime_rows": [
                {"species": species, "moves": list(moves)}
                for species, moves in sorted(preservation_rows.items())
            ],
            "ui_supply_routes_added": 0,
            "route_accounting_added": 0,
            "machine_tutor_carry_form_regression": {
                "missing_path_count": len(dependency_missing_paths),
                "unique_species_family_move_count": len(dependency_missing_triplets),
                "runtime_target_move_count": len(dependency_target_moves),
                "family_counts": dict(sorted(dependency_family_counts.items())),
                "triplet_set_sha256": dependency_triplet_sha,
                "target_move_set_sha256": dependency_target_move_sha,
                "source_owner_path_counts": dict(
                    sorted(dependency_owner_path_counts.items())
                ),
                "source_owner_unique_triplet_counts": dict(
                    sorted(dependency_owner_unique_counts.items())
                ),
            },
        },
        "egg_table": {
            "records": len(egg_rows), "moves": sum(map(len, egg_rows.values())),
            "size": len(egg_raw), "sha256": sha256(egg_raw),
            "exact_override_species": sorted(exact_egg_species),
            "national_dex_override_count": len(national_override),
            "incense_pair_count": len(incense_without_item),
        },
        "parent_roots": {key: f"0x{value:08X}" for key, value in roots.items()},
        "decoder": {
            "get_egg_species_entry": "0x08044F34",
            "evolution_table": "0x0821615C",
            "evolution_source_species": "1..411",
            "evolution_slots": 5,
            "maximum_reverse_steps": 5,
            "level_row_limit": 40,
            "machine_slots": 128,
            "tutor_loop_slots": 128,
            "tutor_nonzero_catalog_slots": "0..63",
            "tutor_slots_64_127_move": 0,
        },
    }


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(
        list(command), cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
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
    source_dir = root / "overlays/modernization_p03_stage74_supply_runtime"
    c_source = source_dir / "modernization_p03_stage74_supply_runtime.c"
    scripts_source = source_dir / "modernization_p03_stage74_supply_runtime_scripts.S"
    linker = source_dir / "modernization_p03_stage74_supply_runtime.ld"
    for path in (c_source, scripts_source, linker):
        if path.is_symlink() or not path.is_file():
            _fail(f"Stage74 overlay source欠落: {path}")
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage74-p03-supply-") as temporary:
        work = Path(temporary)
        table_asm = work / "tables.S"
        lines = [
            ".syntax unified", ".cpu arm7tdmi", ".thumb",
            '.section .rodata.Stage74GeneratedTables,"a",%progbits', ".balign 2",
        ]
        for index, (name, raw) in enumerate(blobs.items()):
            blob_path = work / f"table-{index}.bin"
            blob_path.write_bytes(raw)
            lines.extend([
                f".global {name}", f".type {name}, %object", f"{name}:",
                f'.incbin "{blob_path}"', f".size {name}, .-{name}", ".balign 2",
            ])
        lines.append('.section .note.GNU-stack,"",%progbits')
        table_asm.write_text("\n".join(lines) + "\n", encoding="utf-8")
        c_obj = work / "runtime.o"
        scripts_obj = work / "scripts.o"
        tables_obj = work / "tables.o"
        elf = work / "runtime.elf"
        binary = work / "runtime.bin"
        _run([
            gcc, *common, "-Os", "-std=c11", "-ffreestanding", "-fno-common",
            "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror",
            "-Wconversion", "-Wshadow", "-c", str(c_source), "-o", str(c_obj),
        ], root, "Stage74 C compile")
        _run([gcc, *common, "-c", str(scripts_source), "-o", str(scripts_obj)], root, "Stage74 script compile")
        _run([gcc, *common, "-c", str(table_asm), "-o", str(tables_obj)], root, "Stage74 table compile")
        _run([
            gcc, "-nostdlib", *common,
            f"-Wl,--defsym=STAGE74_LOAD_ADDRESS=0x{load_address:08X}",
            f"-Wl,-T,{linker}", str(c_obj), str(scripts_obj), str(tables_obj),
            "-lgcc", "-o", str(elf),
        ], root, "Stage74 link")
        _run([objcopy, "-O", "binary", str(elf), str(binary)], root, "Stage74 objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", str(elf)], root, "Stage74 nm").splitlines():
            fields = line.split()
            if len(fields) == 3 and re.fullmatch(r"[0-9a-fA-F]+", fields[0]):
                symbols[fields[2]] = int(fields[0], 16)
        code = binary.read_bytes()
    required = {
        "Stage74_RuntimeProbe", "Stage74_GetMoveRelearnerMoves",
        "Stage74_BuildLearnableMoveset", "Stage74_OriginalBuildLearnableMoveset",
        "Stage74_OpenArchiveModeMenu", "Stage74_SetMachineMode",
        "Stage74_SetTutorMode", "Stage74_ResetMode", "Stage74_PrepareMachinePages",
        "Stage74_OpenMachinePageMenu", "Stage74_CommitMachinePage",
        "Stage74_SelectedMachinePageHasMoves", "Stage74_ItemScript",
        "Stage74_ModeMenuScript", "Stage74_MachineGateScript",
        "Stage74_TutorGateScript", "Stage74_FinishScript", *blobs,
    }
    missing = sorted(required - set(symbols))
    if missing:
        _fail(f"Stage74 symbol欠落: {missing}")
    if not code or len(code) >= 0x20000:
        _fail(f"Stage74 payload size不正: {len(code)}")
    if symbols["Stage74_RuntimeProbe"] != load_address:
        _fail("Stage74 entry/load address不一致")
    return CompiledPayload(
        code=code,
        symbols=symbols,
        compiler=_run([gcc, "--version"], root, "gcc version").splitlines()[0],
    )


def _previous_requests(
    allocation: Mapping[str, Any], *, content_overrides: Mapping[int, str] | None = None,
) -> list[dict[str, Any]]:
    rows = allocation.get("allocations")
    if allocation.get("schema_version") != 1 or not isinstance(rows, list) \
            or len(rows) != EXPECTED_STAGE73_ALLOCATION_COUNT:
        _fail("Stage73 allocation schema/count不一致")
    if [row.get("sequence") for row in rows] != list(range(len(rows))):
        _fail("Stage73 allocation sequence不一致")
    overrides = content_overrides or {}
    requests: list[dict[str, Any]] = []
    for row in rows:
        sequence = _integer(row.get("sequence"), "allocation sequence")
        request = {
            "name": row["name"], "region": row["region"], "size": row["size"],
            "alignment": row["alignment"],
            "owner": row["owner"], "purpose": row["purpose"],
            "content_sha256": overrides.get(sequence, row["content_sha256"]),
        }
        if row.get("placement") == "EXPLICIT":
            request["start"] = row["start"]
        elif row.get("placement") != "FIRST_FIT":
            _fail(f"Stage73 allocation placement不正: sequence {sequence}")
        requests.append(request)
    return requests


def _allocate(
    root: Path,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    payload: bytes,
    *,
    placeholder: bool,
    content_overrides: Mapping[int, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous, content_overrides=content_overrides)
    declaration = config["allocations"][0]
    requests.append({
        "name": declaration["name"], "region": declaration["region"],
        "size": len(payload), "alignment": declaration["alignment"],
        "owner": declaration["owner"], "purpose": declaration["purpose"],
        "content_sha256": "0" * 64 if placeholder else sha256(payload),
    })
    report = build_allocation_report_from_csv(
        root / config["inputs"]["rom_regions"]["path"], requests
    )
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage74 allocator overlap")
    rows = report.get("allocations", [])
    if len(rows) != EXPECTED_STAGE73_ALLOCATION_COUNT + 1:
        _fail("Stage74 allocation count不一致")
    allocation = rows[-1]
    if (
        allocation.get("sequence") != EXPECTED_STAGE73_ALLOCATION_COUNT
        or allocation.get("name") != declaration["name"]
        or allocation.get("placement") != "FIRST_FIT"
    ):
        _fail("Stage74 payload allocation/FIRST_FIT不一致")
    return allocation, report


def _veneer(width: int, target: int) -> bytes:
    target |= 1
    if width == 8:
        return struct.pack("<HHI", 0x4B00, 0x4718, target)
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


def _verify_parent_abi(
    root: Path,
    config: Mapping[str, Any],
    parent: bytes,
    metadata: Mapping[str, Any],
    allocation: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    route_audit: Mapping[str, Any],
) -> None:
    parent_sha = sha256(parent)
    if len(parent) != ROM_SIZE or metadata.get("output", {}).get("sha256") != parent_sha \
            or checkpoint.get("output_sha256") != parent_sha:
        _fail("Stage73 metadata/checkpoint→ROM identity不一致")
    if metadata.get("stage") != 73 or metadata.get("release_candidate") is not False \
            or route_audit.get("remaining_full_p03_routes") \
            != {"machine": 26279, "tutor": 369, "total": 26648} \
            or checkpoint.get("remaining_full_p03_routes") != 26648:
        _fail("Stage73 parent completion boundary不一致")
    symbols_doc = _json(
        _fixed_raw(root, config["inputs"]["stage73_symbols"], "Stage73 symbols"),
        "Stage73 symbols",
    )
    if symbols_doc.get("symbols", {}).get("Stage73_GetMoveRelearnerMoves", {}).get("thumb_address") \
            != "0x09534941" \
            or config["parent_abi"]["stage73_get_move_relearner"]["thumb_address"] \
            != "0x09534941":
        _fail("Stage73 GetMoveRelearner delegate ABI不一致")
    move_metadata = _json(
        _fixed_raw(root, config["inputs"]["move_memory_metadata"], "Move Memory metadata"),
        "Move Memory metadata",
    )
    labels = move_metadata.get("runtime", {}).get("payload", {}).get("labels", {})
    expected_metadata_labels = {
        "normal": labels.get("script_remember_entry"),
        "forget": labels.get("script_forget_entry"),
        "egg": labels.get("script_egg_entry"),
        "context_rejected": labels.get("script_context_rejected"),
        "finish": labels.get("script_finish"),
    }
    if expected_metadata_labels != EXPECTED_SCRIPT_ENTRIES:
        _fail("Move Memory old script label ABI不一致")
    rows = allocation.get("allocations", [])
    if not isinstance(rows, list) or len(rows) != EXPECTED_STAGE73_ALLOCATION_COUNT:
        _fail("Stage73 allocation rows不一致")
    memory_row = rows[MOVE_MEMORY_SEQUENCE]
    expected_memory = config["parent_abi"]["move_memory"]
    if (
        memory_row.get("sequence") != MOVE_MEMORY_SEQUENCE
        or memory_row.get("name") != expected_memory["allocation_name"]
        or memory_row.get("start") != expected_memory["allocation_start"]
        or memory_row.get("size") != expected_memory["allocation_size"]
        or memory_row.get("content_sha256") != expected_memory["parent_content_sha256"]
    ):
        _fail("Stage73 Move Memory allocation lineage不一致")
    memory_slice = parent[memory_row["start"]:memory_row["end_exclusive"]]
    if sha256(memory_slice) != expected_memory["parent_rom_content_sha256"]:
        _fail("Stage73 Move Memory effective ROM content hash不一致")
    move_memory_parent = _fixed_raw(
        root, config["inputs"]["move_memory_parent_rom"], "Stage25 Move Memory ROM"
    )
    declared_slice = move_memory_parent[
        memory_row["start"]:memory_row["end_exclusive"]
    ]
    if sha256(declared_slice) != expected_memory["parent_content_sha256"]:
        _fail("Stage25 Move Memory declared allocation content hash不一致")
    effective_spans = [
        {
            "start": memory_row["start"] + span["start"],
            "end_exclusive": memory_row["start"] + span["end_exclusive"],
            "size": span["size"],
        }
        for span in _changed_spans(declared_slice, memory_slice)
    ]
    if effective_spans != expected_memory["known_parent_declared_effective_diff_spans"]:
        _fail(f"Move Memory declared/effective既知差分不一致: {effective_spans}")
    for name, address in EXPECTED_SCRIPT_ENTRIES.items():
        size, digest = EXPECTED_SCRIPT_SLICES[name]
        offset = _rom_offset(address, size, f"old script {name}")
        if sha256(parent[offset:offset + size]) != digest:
            _fail(f"Stage73 old Move Memory script不一致: {name}")
    pointer_address = _integer(expected_memory["item_script_pointer_address"], "item script pointer")
    pointer_offset = _rom_offset(pointer_address, 4, "item script pointer")
    if parent[pointer_offset:pointer_offset + 4].hex() \
            != expected_memory["item_script_pointer_parent_hex"]:
        _fail("Stage73 Move Memory ItemScriptPointer preimage不一致")
    for hook in config["parent_abi"]["hooks"]:
        width = _integer(hook["width"], "hook width")
        offset = _rom_offset(_integer(hook["address"], "hook address"), width, "Stage74 hook")
        if parent[offset:offset + width].hex() != hook["parent_hex"]:
            _fail(f"Stage73 hook preimage不一致: {hook['name']}")
        if hook["name"] == "BuildLearnableMoveset":
            continuation = _integer(hook["continuation_thumb"], "BuildLearnable continuation")
            continuation_offset = _rom_offset(
                continuation & ~1, 2, "BuildLearnable continuation"
            )
            if parent[continuation_offset:continuation_offset + 2].hex() \
                    != hook["continuation_parent_hex"]:
                _fail("BuildLearnableMoveset continuation preimage不一致")
            caller = _integer(hook["unique_caller"], "BuildLearnable caller")
            caller_offset = _rom_offset(caller, 4, "BuildLearnable caller")
            if parent[caller_offset:caller_offset + 4].hex() != hook["unique_caller_hex"]:
                _fail("BuildLearnableMoveset caller preimage不一致")
    for name, consumer in config["parent_abi"]["get_move_relearner_consumers"].items():
        call_address = _integer(consumer["call_address"], f"{name} call")
        call_offset = _rom_offset(call_address, 4, f"{name} call")
        if parent[call_offset:call_offset + 4].hex() != consumer["call_hex"]:
            _fail(f"GetMoveRelearner consumer call不一致: {name}")
        if name == "teach_ui_rebuild":
            upstream = _integer(consumer["upstream_caller"], "teach UI upstream caller")
            upstream_offset = _rom_offset(upstream, 4, "teach UI upstream caller")
            if parent[upstream_offset:upstream_offset + 4].hex() \
                    != consumer["upstream_caller_hex"]:
                _fail("teach UI upstream caller preimage不一致")


@dataclass
class BuiltStage74:
    config: dict[str, Any]
    parent: bytes
    rom: bytes
    payload: bytes
    allocation: bytes
    symbols: dict[str, Any]
    metadata: dict[str, Any]
    route_audit: dict[str, Any]
    audit: dict[str, Any]
    checkpoint: dict[str, Any]


def build_stage74_image(root: Path, config_path: Path = DEFAULT_CONFIG) -> BuiltStage74:
    root = root.resolve()
    config = read_config(root, config_path)
    require_pinned_parent(config)
    parent_contract = config["parent_identity"]
    parent = _fixed_raw(root, parent_contract["rom"], "Stage73 ROM")
    parent_metadata = _json(_fixed_raw(root, parent_contract["metadata"], "Stage73 metadata"), "Stage73 metadata")
    previous_allocation_raw = _fixed_raw(root, parent_contract["allocation"], "Stage73 allocation")
    previous_allocation = _json(previous_allocation_raw, "Stage73 allocation")
    parent_checkpoint = _json(_fixed_raw(root, parent_contract["checkpoint"], "Stage73 checkpoint"), "Stage73 checkpoint")
    parent_route_audit = _json(_fixed_raw(root, parent_contract["route_audit"], "Stage73 route audit"), "Stage73 route audit")
    _fixed_raw(root, parent_contract["incremental_bps"], "Stage72→73 BPS")
    for name in (
        "p03_contract", "p03_runtime_handoff", "p03_compiled_index",
        "rom_regions", "species_manifest", "move_memory_parent_rom",
    ):
        _fixed_raw(root, config["inputs"][name], name)
    _verify_parent_abi(
        root, config, parent, parent_metadata, previous_allocation,
        parent_checkpoint, parent_route_audit,
    )

    model = compile_supply_routes(root, config)
    capacity_audit = audit_build_learnable_capacity(root, config, parent, model)
    blobs, table_audit = build_runtime_tables(model, capacity_audit)
    provisional = compile_payload(root, PROVISIONAL_LOAD_ADDRESS, blobs)
    provisional_allocation, _ = _allocate(
        root, config, previous_allocation, provisional.code, placeholder=True,
    )
    load_address = GBA_ROM_BASE + provisional_allocation["start"]
    compiled = compile_payload(root, load_address, blobs)
    if len(compiled.code) != len(provisional.code):
        _fail("Stage74 link addressでpayload sizeが変化しました")
    payload = compiled.code

    output = bytearray(parent)
    allowed = bytearray(ROM_SIZE)
    writes: list[dict[str, Any]] = []

    def patch(offset: int, raw: bytes, label: str, expected: bytes | None = None) -> None:
        if not 0 <= offset <= ROM_SIZE - len(raw):
            _fail(f"{label} patch範囲外")
        if expected is not None and parent[offset:offset + len(raw)] != expected:
            _fail(f"{label} parent preimage不一致")
        if any(allowed[offset:offset + len(raw)]):
            _fail(f"{label} allowlist overlap")
        output[offset:offset + len(raw)] = raw
        allowed[offset:offset + len(raw)] = b"\x01" * len(raw)
        writes.append({
            "label": label, "start": offset, "end_exclusive": offset + len(raw),
            "size": len(raw), "parent_sha256": sha256(parent[offset:offset + len(raw)]),
            "output_sha256": sha256(raw),
        })

    payload_start = provisional_allocation["start"]
    if parent[payload_start:payload_start + len(payload)] != b"\xFF" * len(payload):
        _fail("Stage74 payload allocation preimageが全FFではありません")
    patch(payload_start, payload, "stage74_supply_runtime_payload", b"\xFF" * len(payload))

    hook_rows: list[dict[str, Any]] = []
    for hook in config["parent_abi"]["hooks"]:
        target_name = str(hook["target"])
        if target_name not in compiled.symbols:
            _fail(f"hook target symbol欠落: {target_name}")
        address = _integer(hook["address"], "hook address")
        width = _integer(hook["width"], "hook width")
        offset = _rom_offset(address, width, f"hook {hook['name']}")
        expected = bytes.fromhex(str(hook["parent_hex"]))
        veneer = _veneer(width, compiled.symbols[target_name])
        patch(offset, veneer, f"hook:{hook['name']}", expected)
        hook_rows.append({
            "name": hook["name"], "site": f"0x{address:08X}", "width": width,
            "target": target_name,
            "target_address": f"0x{compiled.symbols[target_name] | 1:08X}",
            "parent_hex": expected.hex(), "veneer_hex": veneer.hex(),
        })

    memory_abi = config["parent_abi"]["move_memory"]
    pointer_address = _integer(memory_abi["item_script_pointer_address"], "item script pointer")
    pointer_offset = _rom_offset(pointer_address, 4, "item script pointer")
    script_address = compiled.symbols["Stage74_ItemScript"]
    if script_address & 3:
        _fail("Stage74 ItemScriptが4-byte alignmentではありません")
    patch(
        pointer_offset,
        struct.pack("<I", script_address),
        "move_memory_item_script_pointer",
        bytes.fromhex(memory_abi["item_script_pointer_parent_hex"]),
    )

    result = bytes(output)
    outside = [
        offset for offset, (left, right) in enumerate(zip(parent, result, strict=True))
        if left != right and not allowed[offset]
    ]
    if outside:
        _fail(f"Stage74 allowlist外変更: 0x{outside[0]:X}")
    if struct.unpack_from("<I", result, pointer_offset)[0] != script_address:
        _fail("Stage74 ItemScriptPointer readback不一致")
    for name, address in EXPECTED_SCRIPT_ENTRIES.items():
        size, _ = EXPECTED_SCRIPT_SLICES[name]
        offset = _rom_offset(address, size, f"old script {name}")
        if result[offset:offset + size] != parent[offset:offset + size]:
            _fail(f"既存Move Memory scriptが変更されました: {name}")

    previous_rows = previous_allocation["allocations"]
    memory_row = previous_rows[MOVE_MEMORY_SEQUENCE]
    new_memory_sha = sha256(result[memory_row["start"]:memory_row["end_exclusive"]])
    if new_memory_sha == memory_abi["parent_rom_content_sha256"]:
        _fail("Move Memory owner hashがItemScriptPointer変更を反映していません")
    allocation, allocation_report = _allocate(
        root,
        config,
        previous_allocation,
        payload,
        placeholder=False,
        content_overrides={MOVE_MEMORY_SEQUENCE: new_memory_sha},
    )
    if allocation["start"] != payload_start or allocation["gba_start"] != load_address:
        _fail("Stage74 allocator/load address再解決不一致")
    final_rows = allocation_report["allocations"]
    layout_keys = (
        "sequence", "name", "region", "alignment", "start", "end_exclusive",
        "gba_start", "gba_end_exclusive", "size", "owner", "purpose", "placement",
    )
    for index, (before, after) in enumerate(zip(previous_rows, final_rows, strict=False)):
        if index >= len(previous_rows):
            break
        if any(before.get(key) != after.get(key) for key in layout_keys):
            _fail(f"Stage74 inherited allocation layout変更: sequence {index}")
        if index == MOVE_MEMORY_SEQUENCE:
            if after.get("content_sha256") != new_memory_sha:
                _fail("Stage74 Move Memory owner hash更新不一致")
        elif after.get("content_sha256") != before.get("content_sha256"):
            _fail(f"Stage74 inherited allocation content hash変更: sequence {index}")
    if final_rows[MOVE_MEMORY_SEQUENCE]["content_sha256"] != new_memory_sha \
            or final_rows[-1]["content_sha256"] != sha256(payload):
        _fail("Stage74 allocation content identity readback不一致")

    changed = [
        offset for offset, (left, right) in enumerate(zip(parent, result, strict=True))
        if left != right
    ]
    spans = _changed_spans(parent, result)
    output_crc32 = f"{zlib.crc32(result) & 0xFFFFFFFF:08X}"
    route_audit = copy.deepcopy(model.route_audit)
    route_audit["serialization"] = {
        "tables": table_audit,
        "payload_size": len(payload),
        "payload_sha256": sha256(payload),
        "family_tables_distinct": True,
        "machine_or_tutor_written_to_existing_slot_bits": 0,
        "machine_or_tutor_written_to_level_or_egg": 0,
        "all_direct_routes_assigned_to_exactly_one_raw_page": True,
        "candidate_capacity": PAGE_SIZE,
        "silent_drop_count": 0,
    }
    route_audit["ui_supply"] = {
        "entry": "bag Move Memory item",
        "unlock_flag": "0x082C",
        "unlock": "HALL_OF_FAME_REQUIRED",
        "economy": "FREE_PROVISIONAL_REPLACEABLE",
        "main_menu_choices": ["normal", "forget", "egg", "machine", "tutor", "cancel"],
        "machine_page_choices": "1..ceil(raw species rows / 40), then cancel",
        "empty_last_page_displayed": False,
        "known_move_filter_after_fixed_bank_selection": True,
        "empty_filtered_page": "explicit no-moves message then page re-selection",
        "full_four_move_slots": "existing Move Memory replacement/cancel flow",
        "normal_egg_npc_entries_preserved": True,
        "mode_reset": "Stage74 finish for every archive terminal; legacy finish for existing modes",
        "synchronous_menu_failure": "pre-wait cancel sentinel",
    }
    route_audit["build_learnable_preservation"] = {
        "consumer": "RestoreEffectBankHPStatsAndRemoveBackupSpecies",
        "hook": "0x091143B8",
        "parent_preimage": "f0b5d6464f464646",
        "original_continuation_thumb": "0x091143C1",
        "unique_caller": "0x090CC382",
        "ui_rebuild_get_moves_call": "0x091147C2",
        "probe_get_moves_call": "0x09114328",
        "append_order": ["machine", "tutor", "preservation_only"],
        "deduplicated_against_parent_result": True,
        "family_tables_remain_distinct": True,
        "preservation_table_exposed_to_move_memory_ui": False,
        "preservation_route_accounting_added": 0,
        "capacity": capacity_audit,
    }

    function_symbols = {
        "Stage74_RuntimeProbe", "Stage74_GetMoveRelearnerMoves",
        "Stage74_BuildLearnableMoveset", "Stage74_OriginalBuildLearnableMoveset",
        "Stage74_OpenArchiveModeMenu", "Stage74_SetMachineMode",
        "Stage74_SetTutorMode", "Stage74_ResetMode", "Stage74_PrepareMachinePages",
        "Stage74_OpenMachinePageMenu", "Stage74_CommitMachinePage",
        "Stage74_SelectedMachinePageHasMoves", "Stage74_PageCountForRowCount",
        "Stage74_PageStart", "Stage74_PageEnd",
    }
    symbols = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "load_address": f"0x{load_address:08X}", "compiler": compiled.compiler,
        "symbols": {
            name: {
                "address": f"0x{address:08X}",
                **({"thumb_address": f"0x{address | 1:08X}"} if name in function_symbols else {}),
            }
            for name, address in sorted(compiled.symbols.items()) if name.startswith("Stage74_")
        },
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "parent_sha256": sha256(parent), "output_sha256": sha256(result),
        "output_crc32": output_crc32,
        "payload": {
            "start": payload_start, "gba_start": f"0x{load_address:08X}",
            "size": len(payload), "sha256": sha256(payload),
        },
        "writes": writes, "hooks": hook_rows,
        "build_learnable_capacity": capacity_audit,
        "item_script_pointer": {
            "address": f"0x{pointer_address:08X}",
            "parent": memory_abi["item_script_pointer_parent_hex"],
            "output": struct.pack("<I", script_address).hex(),
            "target": f"0x{script_address:08X}",
        },
        "allocation_lineage": {
            "inherited_count": len(previous_rows), "new_sequence": allocation["sequence"],
            "layout_changed_in_inherited_rows": 0,
            "content_hash_changed_sequences": [MOVE_MEMORY_SEQUENCE],
            "move_memory_parent_sha256": memory_row["content_sha256"],
            "move_memory_parent_effective_rom_sha256": memory_abi["parent_rom_content_sha256"],
            "parent_declared_effective_known_diff_spans": memory_abi[
                "known_parent_declared_effective_diff_spans"
            ],
            "move_memory_output_sha256": new_memory_sha,
        },
        "changed_byte_count": len(changed), "allowed_byte_count": sum(allowed),
        "outside_allowlist_count": 0,
        "changed_offsets_sha256": sha256(
            b"".join(struct.pack("<I", value) for value in changed)
        ),
        "changed_span_count": len(spans), "changed_spans": spans,
        "existing_rom_outside_allowlist_unchanged": True,
    }
    status = "CHECKPOINT_DIRECT_MACHINE_TUTOR_SUPPLY_CONNECTED_OWNER_REVIEW_AND_MGBA_REMAIN"
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": status,
        "done": False, "release_candidate": False,
        "parent_identity": {
            "commit": parent_contract["stage73_commit"],
            "path": parent_contract["rom"]["path"], "size": len(parent),
            "sha256": sha256(parent),
        },
        "output": {
            "path": config["outputs"]["rom"], "size": len(result),
            "sha256": sha256(result), "crc32": output_crc32,
        },
        "changed_bytes": len(changed),
        "allocation": [allocation],
        "allocation_mutations": [{
            "sequence": MOVE_MEMORY_SEQUENCE, "name": memory_row["name"],
            "layout_changed": False,
            "parent_content_sha256": memory_row["content_sha256"],
            "parent_effective_rom_content_sha256": memory_abi["parent_rom_content_sha256"],
            "output_content_sha256": new_memory_sha,
            "reason": (
                "normalize the pinned Stage73 effective owner slice (including four known "
                "post-Stage25 patches) and redirect Move Memory ItemScriptPointer to Stage74"
            ),
        }],
        "allocation_report": {
            "path": config["outputs"]["allocation"],
            "size": len(stable_json(allocation_report)),
            "sha256": sha256(stable_json(allocation_report)),
        },
        "payload": {
            "path": config["outputs"]["payload"], "size": len(payload),
            "sha256": sha256(payload),
        },
        "hooks": hook_rows,
        "direct_supply": route_audit["direct_supply"],
        "accounting": {
            "stage67_materialized_routes": 51151,
            "stage73_new_runtime_materialized_routes": 5363,
            "stage73_existing_owner_accounted_routes": 35207,
            "stage74_direct_supply_materialized_routes": 26648,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "selected_direct_supply_routes_remaining": 0,
            "full_p03_done": False,
        },
        "validation": {
            "single_zip_stream": "PASS", "compile_link": "PASS",
            "hook_preimage": "PASS", "stage73_delegate": "PASS",
            "build_learnable_original_prologue_replay": "PASS",
            "build_learnable_buffer_entries": capacity_audit[
                "maximum_runtime_buffer_entries_after_archive_append"
            ],
            "build_learnable_unique_entries": capacity_audit[
                "maximum_unique_entries_after_archive_append"
            ],
            "build_learnable_overflow_species": capacity_audit["overflow_species_count"],
            "build_learnable_selected_routes_checked": capacity_audit[
                "preservation_only"
            ]["selected_route_count_checked"],
            "build_learnable_preservation_missing_paths": capacity_audit[
                "preservation_only"
            ]["missing_path_count"],
            "build_learnable_preservation_target_moves": capacity_audit[
                "preservation_only"
            ]["runtime_target_move_count"],
            "build_learnable_preservation_ui_routes_added": 0,
            "build_learnable_preservation_accounting_added": 0,
            "item_script_pointer_preimage": "PASS", "old_scripts_preserved": "PASS",
            "allocation_first_fit": "PASS", "allocation_sequence33_owner_hash_updated": "PASS",
            "machine_paging_silent_drop": 0, "empty_final_pages": 0,
            "family_table_union": 0, "prohibited_coercions": 0,
            "side_change": 0, "browt_pombon_gecqua": 0,
            "hof_unlock_gate": "PASS", "mode_reset_terminal_paths": "PASS",
            "mgba": "NOT_RUN_LIGHTWEIGHT_STAGE74_OWNER",
        },
        "completion_claim": config["supply_contract"]["completion_claim"],
        "remaining_work": [
            "Own Tempo Rockruff reference 0744.01 carry owner 38 paths need independent semantic review",
            "archive economy is provisional and replaceable by a later central price/NPC policy",
            "final cumulative mGBA is deferred to the root release gate",
        ],
    }
    checkpoint = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT_DIRECT_MACHINE_TUTOR_SUPPLY_CONNECTED_FULL_P03_WITHHELD",
        "done": False,
        "release_candidate": False,
        "parent_commit": parent_contract["stage73_commit"],
        "parent_sha256": sha256(parent),
        "output_path": config["outputs"]["rom"],
        "output_size": len(result),
        "output_sha256": sha256(result),
        "output_crc32": output_crc32,
        "direct_supply_materialized_routes": 26648,
        "direct_supply_species_family_move_pairs": 26648,
        "remaining_direct_supply_routes": 0,
        "cumulative_runtime_materialized_routes": 83162,
        "cumulative_accounted_routes": 118369,
        "full_p03_done": False,
        "build_learnable_preservation": {
            "selected_routes_checked": capacity_audit["preservation_only"][
                "selected_route_count_checked"
            ],
            "missing_paths": capacity_audit["preservation_only"][
                "missing_path_count"
            ],
            "target_move_pairs": capacity_audit["preservation_only"][
                "runtime_target_move_count"
            ],
            "species": capacity_audit["preservation_only"]["species_count"],
            "target_move_set_sha256": capacity_audit["preservation_only"][
                "target_move_set_sha256"
            ],
            "ui_supply_routes_added": 0,
            "route_accounting_added": 0,
            "caller_capacity_u16": capacity_audit["caller_buffer_capacity_u16"],
            "maximum_runtime_buffer_entries": capacity_audit[
                "maximum_runtime_buffer_entries_after_archive_append"
            ],
            "overflow_species_count": capacity_audit["overflow_species_count"],
        },
        "withheld_route_semantics": {
            "count": 38,
            "scope": "OWN_TEMPO_ROCKRUFF_0744_01_CARRY_OWNER",
            "direct_conversion": "FORBIDDEN",
        },
        "exclusions": {
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
        },
        "economy": "PROVISIONAL_REPLACEABLE",
        "mgba": "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "completion_claim": config["supply_contract"]["completion_claim"],
    }
    return BuiltStage74(
        config=config, parent=parent, rom=result, payload=payload,
        allocation=stable_json(allocation_report), symbols=symbols,
        metadata=metadata, route_audit=route_audit, audit=audit,
        checkpoint=checkpoint,
    )


def build_outputs(root: Path, config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage74_image(root, config_path)
    outputs = built.config["outputs"]
    bps = create_bps(
        built.parent,
        built.rom,
        metadata=b"Stage73 to Stage74 P03 direct machine tutor archive checkpoint",
    )
    if apply_bps(built.parent, bps) != built.rom:
        _fail("Stage73→Stage74 BPS round-trip不一致")
    bps_identity = {
        "path": outputs["incremental_bps"], "size": len(bps), "sha256": sha256(bps),
        "source_sha256": sha256(built.parent), "target_sha256": sha256(built.rom),
        "round_trip": True,
    }
    built.metadata["bps"] = bps_identity
    route_audit_raw = stable_json(built.route_audit)
    audit_raw = stable_json(built.audit)
    symbols_raw = stable_json(built.symbols)
    built.metadata["route_audit"] = {
        "path": outputs["route_audit"], "size": len(route_audit_raw),
        "sha256": sha256(route_audit_raw),
    }
    built.metadata["checkpoint"] = {
        "path": outputs["checkpoint"],
        "status": "GENERATED_AS_SEPARATE_PINNABLE_ARTIFACT",
    }
    metadata_raw = stable_json(built.metadata)
    built.checkpoint.update({
        "metadata": {
            "path": outputs["metadata"], "size": len(metadata_raw),
            "sha256": sha256(metadata_raw),
        },
        "allocation": {
            "path": outputs["allocation"], "size": len(built.allocation),
            "sha256": sha256(built.allocation),
            "new_sequence": EXPECTED_STAGE73_ALLOCATION_COUNT,
            "mutated_content_hash_sequences": [MOVE_MEMORY_SEQUENCE],
            "inherited_layout_changes": 0,
            "sequence33_parent_declared_content_sha256": built.config["parent_abi"][
                "move_memory"
            ]["parent_content_sha256"],
            "sequence33_parent_effective_rom_sha256": built.config["parent_abi"][
                "move_memory"
            ]["parent_rom_content_sha256"],
            "sequence33_output_content_sha256": built.metadata["allocation_mutations"][0][
                "output_content_sha256"
            ],
            "parent_declared_effective_known_diff_spans": built.config["parent_abi"][
                "move_memory"
            ]["known_parent_declared_effective_diff_spans"],
            "reason": "effective owner normalization plus ItemScriptPointer replacement",
        },
        "bps": bps_identity,
        "route_audit": {
            "path": outputs["route_audit"], "size": len(route_audit_raw),
            "sha256": sha256(route_audit_raw),
        },
        "runtime_audit": {
            "path": outputs["audit"], "size": len(audit_raw),
            "sha256": sha256(audit_raw),
        },
        "symbols": {
            "path": outputs["symbols"], "size": len(symbols_raw),
            "sha256": sha256(symbols_raw),
        },
    })
    checkpoint_raw = stable_json(built.checkpoint)
    return {
        outputs["rom"]: built.rom,
        outputs["metadata"]: metadata_raw,
        outputs["allocation"]: built.allocation,
        outputs["incremental_bps"]: bps,
        outputs["payload"]: built.payload,
        outputs["symbols"]: symbols_raw,
        outputs["audit"]: audit_raw,
        outputs["route_audit"]: route_audit_raw,
        outputs["checkpoint"]: checkpoint_raw,
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
        _fail(f"Stage74 published artifact不一致: {mismatches}")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("model", "compile", "build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    config = read_config(root, args.config)
    if args.command == "model":
        model = compile_supply_routes(root, config)
        print(json.dumps(model.route_audit["direct_supply"], ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "compile":
        model = compile_supply_routes(root, config)
        parent = _fixed_raw(root, config["parent_identity"]["rom"], "Stage73 ROM")
        capacity_audit = audit_build_learnable_capacity(
            root, config, parent, model
        )
        blobs, audit = build_runtime_tables(model, capacity_audit)
        compiled = compile_payload(root, PROVISIONAL_LOAD_ADDRESS, blobs)
        print(
            f"Stage74 COMPILE PASS size={len(compiled.code)} "
            f"sha256={sha256(compiled.code)} tables={json.dumps(audit, sort_keys=True)}"
        )
        return 0
    outputs = build_outputs(root, args.config)
    if args.command == "check":
        _compare(root, outputs)
    else:
        for relative, raw in outputs.items():
            _atomic_write(root / relative, raw)
    print(f"Stage74 {args.command.upper()} PASS artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModernizationP03Stage74SupplyError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
