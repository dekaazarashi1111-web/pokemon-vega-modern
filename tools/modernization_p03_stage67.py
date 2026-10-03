"""P02 overlayを保持したP03 Stage67 consumer checkpointを決定生成する。

Stage66のlevel-up/machine置換を親に、進化時技、既存slot教え技、通常タマゴ技を
実consumer ABIへ接続する。条件を正確に表現できない経路は明示的に保留し、
Move 1063はユーザー判断どおり全consumerで非採用（代替なし）として扱う。
"""

from __future__ import annotations

import copy
import hashlib
import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence

from scripts.run_modernization_p02_acceptance import (
    ModernizationP02AcceptanceError,
    build_candidate as build_p02_candidate,
)
from tools.modernization_learnsets import iter_compiled_p03_routes


ROM_BASE = 0x08000000
ROM_END = 0x0A000000
ROM_SIZE = 32 * 1024 * 1024
SPECIES_COUNT = 1621
TASK = "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
STAGE = 67
P03_TASK = "USER-MODERNIZATION-P03"
EXPECTED_SOURCE_COUNTS = {
    "level_up": 18_530,
    "evolution": 341,
    "reminder": 298,
    "machine": 55_380,
    "tutor": 1_113,
    "egg": 2_572,
    "shared_egg": 5_041,
    "pre_evolution_carry": 35_183,
    "form_change": 70,
}
EXPECTED_NON_ADOPTED_COUNTS = {
    "egg": 9,
    "level_up": 15,
    "machine": 68,
    "pre_evolution_carry": 42,
    "reminder": 3,
    "shared_egg": 18,
    "tutor": 4,
}
EXPECTED_SELECTED_COUNTS = {
    key: count - EXPECTED_NON_ADOPTED_COUNTS.get(key, 0)
    for key, count in EXPECTED_SOURCE_COUNTS.items()
}
EGG_ALIAS_COLLISIONS = {
    203: (202, (174, 283)),
    324: (323, (32, 90, 174, 246, 321, 578, 683)),
}
EGG_INCENSE_UNION_CONFLICTS = {
    364: 365,  # Happiny -> Chansey
    608: 517,  # Azurill -> Marill
    719: 648,  # Chingling -> Chimecho
    724: 519,  # Bonsly -> Sudowoodo
    727: 491,  # Munchlax -> Snorlax
}


class ModernizationP03Stage67Error(ValueError):
    """Stage67 input identity、route、preimage、allocation違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage67Error(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


class FramedDigest:
    """P03契約と同じlength-framed stable JSON digest。"""

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


def _framed_digest(values: Iterable[Any]) -> str:
    digest = FramedDigest()
    for value in values:
        digest.add(value)
    return digest.hexdigest()


def hex_int(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        _fail(f"{label}は0x付き16進数ではありません: {value!r}")
    try:
        result = int(value, 16)
    except ValueError:
        _fail(f"{label}が不正です: {value!r}")
    if result < 0:
        _fail(f"{label}が負数です")
    return result


def read_config(root: Path, relative: Path) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"Stage67 configが通常ファイルではありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"Stage67 configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("Stage67 config rootがobjectではありません")
    return value


def fixed_path(root: Path, contract: Mapping[str, Any], label: str) -> Path:
    path = root / str(contract.get("path", ""))
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常ファイルではありません: {path}")
    expected_size = int(contract.get("size", -1))
    if path.stat().st_size != expected_size:
        _fail(f"{label} size不一致: {path.stat().st_size} != {expected_size}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != str(contract.get("sha256", "")):
        _fail(f"{label} SHA-256不一致: {actual}")
    return path


def fixed_input(
    root: Path,
    contract: Mapping[str, Any],
    label: str,
    *,
    allow_symlink: bool = False,
) -> bytes:
    path = root / str(contract.get("path", ""))
    if (path.is_symlink() and not allow_symlink) or not path.is_file():
        _fail(f"{label}が通常ファイルではありません: {path}")
    raw = path.read_bytes()
    if len(raw) != int(contract.get("size", -1)):
        _fail(f"{label} size不一致: {len(raw)} != {contract.get('size')}")
    actual = sha256(raw)
    if actual != str(contract.get("sha256", "")):
        _fail(f"{label} SHA-256不一致: {actual}")
    return raw


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}がJSON objectではありません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _read_u32(raw: bytes, offset: int, label: str) -> int:
    if not 0 <= offset <= len(raw) - 4:
        _fail(f"{label} offsetがROM範囲外です: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, label: str) -> int:
    if not ROM_BASE <= address < ROM_END:
        _fail(f"{label}が32MiB ROM runtime範囲外です: 0x{address:08X}")
    return address - ROM_BASE


def _set_bits(row: bytes, *, slots: int) -> list[int]:
    return [slot for slot in range(slots) if row[slot // 8] & 1 << slot % 8]


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    if len(before) != len(after):
        _fail("ROM before/after size不一致")
    spans: list[dict[str, int]] = []
    index = 0
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        while index < len(before) and before[index] != after[index]:
            index += 1
        spans.append({"start": start, "end_exclusive": index, "size": index - start})
    return spans


def _validate_config(config: Mapping[str, Any]) -> None:
    if (config.get("schema_version"), config.get("task"), config.get("stage")) != (
        1,
        TASK,
        STAGE,
    ):
        _fail("Stage67 config schema/task/stage不一致")
    expected_scope = {
        "source_routes": 118528,
        "selected_routes": 118369,
        "non_adopted_move_1063_routes": 159,
        "parent_materialized_routes": 47548,
        "evolution_routes_materialized": 341,
        "tutor_existing_slot_routes_materialized": 740,
        "egg_normal_routes_materialized": 2522,
        "stage67_new_materialized_routes": 3603,
        "cumulative_materialized_routes": 51151,
        "selected_routes_deferred": 67218,
        "egg_special_breeding_routes_deferred": 1,
        "egg_legacy_alias_collision_routes_deferred": 9,
        "egg_incense_union_conflict_routes_deferred": 31,
        "adoption_policy": "REPLACE_SAFE_TARGET_ROWS_NOT_UNION_PRESERVE_UNADOPTED_VEGA_ROWS",
    }
    if config.get("scope") != expected_scope:
        _fail("Stage67 scope固定値不一致")
    acceptance = config.get("acceptance", {})
    if acceptance != {
        "static_contract_gate": "REQUIRED",
        "real_consumer_mgba_gate": "REQUIRED",
        "independent_processes": 2,
        "incremental_bps_round_trip": "REQUIRED",
        "clean_bps_round_trip": "REQUIRED",
        "task_completion": "CHECKPOINT_NOT_P03_DONE",
    }:
        _fail("Stage67 acceptanceがcheckpoint境界を固定していません")


def _validate_stage66_parent(
    stage66: bytes,
    metadata: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    route_audit: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    expected_path = config["inputs"]["stage66_rom"]["path"]
    digest = sha256(stage66)
    if len(stage66) != ROM_SIZE:
        _fail("Stage66 parent ROM size不一致")
    if (
        metadata.get("stage") != 66
        or metadata.get("status") != "CHECKPOINT"
        or metadata.get("done") is not False
        or metadata.get("checkpoint_marker") != "CHECKPOINT_NOT_P03_DONE"
        or metadata.get("output", {}).get("path") != expected_path
        or metadata.get("output", {}).get("sha256") != digest
        or metadata.get("scope", {}).get("routes_materialized_by_this_checkpoint")
        != 47_548
    ):
        _fail("Stage66 metadataがexact bulk checkpointを保証していません")
    if (
        checkpoint.get("stage") != 66
        or checkpoint.get("status") != "CHECKPOINT"
        or checkpoint.get("done") is not False
        or checkpoint.get("checkpoint_marker") != "CHECKPOINT_NOT_P03_DONE"
        or checkpoint.get("output", {}).get("sha256") != digest
    ):
        _fail("Stage66 checkpointとparent ROMが一致しません")
    if (
        route_audit.get("source_validation", {}).get("compiled_route_count") != 118_528
        or route_audit.get("materialization", {}).get("materialized_routes") != 47_548
        or route_audit.get("claims", {}).get("full_p03_implemented") is not False
    ):
        _fail("Stage66 route audit境界不一致")


def _validate_p02_overlay(
    stage66: bytes,
    p02_config: Mapping[str, Any],
    p02_checkpoint: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    try:
        parent, repair = build_p02_candidate(p02_config, parent_bytes=stage66)
    except ModernizationP02AcceptanceError as error:
        _fail(f"P02 overlayを再構築できません: {error}")
    expected = config["inputs"]["p02_overlay_parent"]
    if len(parent) != int(expected.get("size", -1)) or sha256(parent) != expected.get("sha256"):
        _fail("P02 overlay candidate identity不一致")
    claims = p02_checkpoint.get("claims", {})
    if (
        p02_checkpoint.get("status") != "CHECKPOINT_NOT_DONE"
        or p02_checkpoint.get("classification")
        != "ACTUAL_CONSUMER_PARTIAL_ACCEPTANCE_WITH_ROOT_FIX"
        or p02_checkpoint.get("execution", {}).get("process_runs") != 2
        or claims.get("exact_p02_overlay_parent") is not True
        or claims.get("level_held_item_slot_priority_root_fixed") is not True
        or claims.get("full_evolution_acceptance") is not False
        or p02_checkpoint.get("inputs", {}).get("candidate_rom", {}).get("sha256")
        != sha256(parent)
    ):
        _fail("P02 acceptance checkpointを継承できません")
    if repair.get("changed_byte_count") != 60 or repair.get("outside_declared_spans") != 0:
        _fail("P02 overlay changed-span契約不一致")
    return parent, repair


@dataclass(frozen=True)
class ConsumerRoutes:
    target_records: tuple[dict[str, Any], ...]
    evolution_rows: dict[int, tuple[dict[str, Any], ...]]
    tutor_rows: dict[int, tuple[dict[str, Any], ...]]
    egg_rows: dict[int, tuple[dict[str, Any], ...]]
    route_audit: dict[str, Any]


def _compile_routes(
    root: Path,
    learnsets_zip: Path,
    contract: Mapping[str, Any],
    index: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> ConsumerRoutes:
    corrected = contract.get("corrected_adoption", {})
    corrected_consumers = corrected.get("consumers", {})
    selected = contract.get("runtime_selection", {})
    selected_consumers = selected.get("consumers", {})
    if (
        contract.get("schema_version") != 1
        or contract.get("task") != P03_TASK
        or contract.get("status") != "PASS"
        or corrected.get("records") != 1300
        or corrected.get("routes") != 118528
        or {key: value.get("count") for key, value in corrected_consumers.items()}
        != EXPECTED_SOURCE_COUNTS
        or selected.get("records") != 1300
        or selected.get("selected_routes") != 118369
        or selected.get("excluded_routes") != 159
        or {key: value.get("count") for key, value in selected_consumers.items()}
        != EXPECTED_SELECTED_COUNTS
    ):
        _fail("P03 learnset source/selection contract不一致")
    supply = contract.get("runtime_supply", {})
    if (
        supply.get("projected_rows_by_family") != {"machine": 29033, "tutor": 740}
        or supply.get("supply_required_rows_by_family")
        != {"machine": 26279, "tutor": 369}
        or supply.get("excluded_candidate_pairs") != 72
    ):
        _fail("P03 non-adopted後runtime supply件数不一致")
    side = handoff.get("side_change_1063", {})
    abi = handoff.get("connection_points", {}).get("current_abi", {})
    if (
        handoff.get("status") != "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS"
        or side.get("status") != "NOT_ADOPTED_BY_USER_DECISION"
        or side.get("project_move_id") != 1063
        or side.get("adopted_route_count") != 0
        or side.get("excluded_route_count") != 159
        or side.get("routes_by_consumer") != EXPECTED_NON_ADOPTED_COUNTS
        or side.get("decision", {}).get("replacement_move_key") is not None
        or side.get("decision", {}).get("runtime_action") != "DO_NOT_IMPLEMENT_OR_ALLOCATE"
        or abi.get("implemented_move_ids") != "0..1062"
        or abi.get("level_up", {}).get("row") != "U16_PROJECT_MOVE_ID + U8_LEVEL"
        or abi.get("tutor_compatibility", {}).get("slots") != 64
        or abi.get("tutor_compatibility", {}).get("stride") != 16
    ):
        _fail("P03 runtime handoff ABI/Move1063非採用境界不一致")
    if (
        index.get("status") != "PASS"
        or index.get("record_count") != 1300
        or index.get("route_count") != 118528
        or index.get("selected_route_count") != 118369
        or index.get("excluded_route_count") != 159
        or index.get("ordering")
        != "canonical Species ID ascending; source route order preserved"
    ):
        _fail("P03 compiled index境界不一致")
    raw_records = index.get("records")
    if not isinstance(raw_records, list) or len(raw_records) != 1300:
        _fail("P03 compiled index records不一致")
    target_records = tuple(dict(row) for row in raw_records)
    target_ids = [row.get("canonical_id") for row in target_records]
    if (
        any(isinstance(value, bool) or not isinstance(value, int) for value in target_ids)
        or target_ids != sorted(target_ids)
        or len(set(target_ids)) != 1300
        or not all(0 <= value < SPECIES_COUNT for value in target_ids)
    ):
        _fail("P03 corrected target ID/order不一致")
    targets_by_id = {int(row["canonical_id"]): row for row in target_records}

    evolution: dict[int, list[dict[str, Any]]] = defaultdict(list)
    tutor: dict[int, list[dict[str, Any]]] = defaultdict(list)
    egg: dict[int, list[dict[str, Any]]] = defaultdict(list)
    source_counts: Counter[str] = Counter()
    selected_counts: Counter[str] = Counter()
    non_adopted_counts: Counter[str] = Counter()
    source_digests = {name: FramedDigest() for name in EXPECTED_SOURCE_COUNTS}
    selected_digests = {name: FramedDigest() for name in EXPECTED_SOURCE_COUNTS}
    materialized_digest = FramedDigest()
    deferred_digest = FramedDigest()
    non_adopted_digest = FramedDigest()
    seen_keys: set[str] = set()
    tutor_slots: set[tuple[int, int]] = set()
    deferred_counts: Counter[str] = Counter()
    deferred_reasons: Counter[str] = Counter()
    non_adopted_rows: list[dict[str, Any]] = []
    egg_special_rows: list[dict[str, Any]] = []
    egg_alias_rows: list[dict[str, Any]] = []
    egg_incense_rows: list[dict[str, Any]] = []

    for compiled in iter_compiled_p03_routes(root, learnsets_zip):
        consumer = str(compiled.get("consumer", ""))
        if consumer not in EXPECTED_SOURCE_COUNTS:
            _fail(f"未知のconsumerです: {consumer}")
        source_counts[consumer] += 1
        source_digests[consumer].add(compiled)
        source = compiled.get("source_route")
        if not isinstance(source, dict):
            _fail("compiled routeにsource_routeがありません")
        species_id = compiled.get("target_species_id")
        target = targets_by_id.get(species_id)
        species_key = str(compiled.get("target_species_key", ""))
        if target is None or target.get("species_key") != species_key:
            _fail(f"compiled target identity不一致: {species_key}/{species_id}")
        route_id = str(source.get("route_id", ""))
        route_key = f"{species_key}:{route_id}"
        if route_key in seen_keys:
            _fail(f"compiled target+route重複: {route_key}")
        seen_keys.add(route_key)
        move_id = source.get("project_move_id")
        if isinstance(move_id, bool) or not isinstance(move_id, int):
            _fail(f"project Move ID不正: {route_key}")
        base = {
            "target_species_key": species_key,
            "target_species_id": species_id,
            "route_id": route_id,
            "move_key": compiled.get("move_key"),
            "project_move_id": move_id,
        }
        if move_id == 1063:
            non_adopted_counts[consumer] += 1
            row = {
                "consumer": consumer,
                **base,
                "selection_status": "NOT_ADOPTED_BY_USER_DECISION",
                "replacement_move_key": None,
                "reason": "MOVE_1063_EXCLUDED_FROM_ALL_CONSUMERS_NO_REPLACEMENT",
            }
            non_adopted_rows.append(row)
            non_adopted_digest.add(row)
            continue
        if compiled.get("runtime_move_ready") is not True or not 1 <= move_id <= 1062:
            _fail(f"選択routeのruntime move readiness不一致: {route_key}")
        selected_counts[consumer] += 1
        selected_compiled = {**compiled, "selection_status": "ADOPTED_FOR_RUNTIME"}
        selected_digests[consumer].add(selected_compiled)

        if consumer == "evolution":
            if source.get("method") != "evolution" \
                    or source.get("target_learning_level") != 0:
                _fail(f"evolution route ABI不一致: {route_key}")
            row = {**base, "learning_level": 0}
            evolution[int(species_id)].append(row)
            materialized_digest.add({"consumer": consumer, **row})
        elif consumer == "tutor":
            runtime_supply = compiled.get("runtime_supply")
            if not isinstance(runtime_supply, dict):
                _fail(f"tutor runtime supply欠落: {route_key}")
            status = runtime_supply.get("status")
            if status == "EXISTING_RUNTIME_SLOT":
                slot = runtime_supply.get("runtime_slot_zero_based")
                if isinstance(slot, bool) or not isinstance(slot, int) or not 0 <= slot < 64:
                    _fail(f"tutor runtime slot不正: {route_key}")
                if (int(species_id), slot) in tutor_slots:
                    _fail(f"tutor target+slot重複: {species_id}/{slot}")
                tutor_slots.add((int(species_id), slot))
                row = {**base, "runtime_slot_zero_based": slot}
                tutor[int(species_id)].append(row)
                materialized_digest.add({"consumer": consumer, **row})
            elif status == "SUPPLY_REQUIRED":
                if runtime_supply.get("runtime_slot_zero_based") is not None:
                    _fail(f"SUPPLY_REQUIRED tutorにslotがあります: {route_key}")
                deferred_counts[consumer] += 1
                deferred_reasons["TUTOR_RUNTIME_SUPPLY_REQUIRED"] += 1
                deferred_digest.add({
                    "consumer": consumer,
                    **base,
                    "reason": "TUTOR_RUNTIME_SUPPLY_REQUIRED",
                })
            else:
                _fail(f"tutor runtime supply status不正: {route_key}")
        elif consumer == "egg":
            method = source.get("method")
            if method == "special_breeding":
                if species_id != 24 or move_id != 344:
                    _fail(f"未知のspecial breeding routeです: {route_key}")
                row = {
                    **base,
                    "method": method,
                    "reason": "SPECIAL_BREEDING_LIGHT_BALL_CONDITION_NOT_IN_NORMAL_EGG_TABLE",
                }
                egg_special_rows.append(row)
                deferred_counts[consumer] += 1
                deferred_reasons[row["reason"]] += 1
                deferred_digest.add({"consumer": consumer, **row})
            elif int(species_id) in EGG_ALIAS_COLLISIONS:
                row = {
                    **base,
                    "method": method,
                    "runtime_egg_species_id": EGG_ALIAS_COLLISIONS[int(species_id)][0],
                    "reason": "LEGACY_GET_EGG_SPECIES_COLLIDES_WITH_NON_ADOPTED_VEGA_SPECIES",
                }
                egg_alias_rows.append(row)
                deferred_counts[consumer] += 1
                deferred_reasons[row["reason"]] += 1
                deferred_digest.add({"consumer": consumer, **row})
            elif int(species_id) in EGG_INCENSE_UNION_CONFLICTS:
                row = {
                    **base,
                    "method": method,
                    "runtime_incense_union_species_id": EGG_INCENSE_UNION_CONFLICTS[
                        int(species_id)
                    ],
                    "reason": "GET_ALL_EGG_MOVES_INCENSE_UNION_ADDS_PRESERVED_PARENT_MOVES",
                }
                egg_incense_rows.append(row)
                deferred_counts[consumer] += 1
                deferred_reasons[row["reason"]] += 1
                deferred_digest.add({"consumer": consumer, **row})
            elif method == "egg":
                row = {**base, "method": method}
                egg[int(species_id)].append(row)
                materialized_digest.add({"consumer": consumer, **row})
            else:
                _fail(f"未知のegg methodです: {route_key}/{method!r}")
        else:
            reasons = {
                "level_up": "MATERIALIZED_IN_STAGE66",
                "machine": "MATERIALIZED_OR_SUPPLY_DEFERRED_IN_STAGE66",
                "reminder": "NO_DISTINCT_REMINDER_RUNTIME_TABLE_OR_EXACT_ADAPTER",
                "shared_egg": "NO_CONDITION_AWARE_SHARED_EGG_CONSUMER_OR_SEPARATE_TABLE",
                "pre_evolution_carry": "CARRY_ROUTE_REQUIRES_PRE_EVOLUTION_CHAIN_CONSUMER",
                "form_change": "FORM_CONDITION_AND_TRANSITION_CONSUMER_NOT_IMPLEMENTED",
            }
            reason = reasons[consumer]
            if consumer not in {"level_up", "machine"}:
                deferred_counts[consumer] += 1
                deferred_reasons[reason] += 1
                deferred_digest.add({"consumer": consumer, **base, "reason": reason})

    if len(seen_keys) != 118528 or dict(source_counts) != EXPECTED_SOURCE_COUNTS:
        _fail("Stage67全source route集合/count不一致")
    if dict(selected_counts) != EXPECTED_SELECTED_COUNTS:
        _fail(f"Stage67 selected route count不一致: {dict(selected_counts)}")
    if dict(non_adopted_counts) != EXPECTED_NON_ADOPTED_COUNTS:
        _fail(f"Move1063非採用consumer count不一致: {dict(non_adopted_counts)}")
    compiled_gate: dict[str, Any] = {}
    selected_gate: dict[str, Any] = {}
    for name in EXPECTED_SOURCE_COUNTS:
        raw_expected = corrected_consumers.get(name, {})
        if raw_expected.get("count") != source_counts[name] \
                or raw_expected.get("content_sha256") != source_digests[name].hexdigest():
            _fail(f"P03 {name} source digest不一致")
        selected_expected = selected_consumers.get(name, {})
        if selected_expected.get("count") != selected_counts[name] \
                or selected_expected.get("content_sha256") \
                != selected_digests[name].hexdigest():
            _fail(f"P03 {name} selected digest不一致")
        compiled_gate[name] = {
            "count": source_counts[name],
            "content_sha256": source_digests[name].hexdigest(),
            "matches_p03_contract": True,
        }
        selected_gate[name] = {
            "count": selected_counts[name],
            "content_sha256": selected_digests[name].hexdigest(),
            "matches_p03_runtime_selection": True,
        }

    if (
        sum(map(len, evolution.values())) != 341
        or len(evolution) != 330
        or sum(map(len, tutor.values())) != 740
        or len(tutor) != 290
        or len(tutor_slots) != 740
        or sum(map(len, egg.values())) != 2522
        or len(egg) != 450
        or len(egg_special_rows) != 1
        or len(egg_alias_rows) != 9
        or len(egg_incense_rows) != 31
    ):
        _fail("Stage67 materialize/defer family count不一致")
    for species_id, (_, expected_moves) in EGG_ALIAS_COLLISIONS.items():
        actual = tuple(row["project_move_id"] for row in egg_alias_rows
                       if row["target_species_id"] == species_id)
        if actual != expected_moves:
            _fail(f"egg legacy alias衝突集合不一致: {species_id}")

    cumulative_by_consumer = {
        "level_up": 18515,
        "evolution": 341,
        "machine": 29033,
        "tutor": 740,
        "egg": 2522,
    }
    deferred_selected_by_consumer = {
        "reminder": 295,
        "machine": 26279,
        "tutor": 369,
        "egg": 41,
        "shared_egg": 5023,
        "pre_evolution_carry": 35141,
        "form_change": 70,
    }
    if sum(cumulative_by_consumer.values()) != 51151 \
            or sum(deferred_selected_by_consumer.values()) != 67218:
        _fail("Stage67 cumulative partition算術不一致")
    route_audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "checkpoint_marker": "CHECKPOINT_NOT_P03_DONE",
        "source_validation": {
            "corrected_target_count": len(target_records),
            "source_route_count": len(seen_keys),
            "selected_route_count": sum(selected_counts.values()),
            "non_adopted_route_count": sum(non_adopted_counts.values()),
            "ordering": index["ordering"],
            "all_nine_consumers_streamed_and_validated": True,
            "source_consumers": compiled_gate,
            "selected_consumers": selected_gate,
        },
        "materialization": {
            "policy": "REPLACE_SAFE_TARGET_ROWS_NOT_UNION_PRESERVE_UNADOPTED_VEGA_ROWS",
            "parent_stage66_routes_materialized": 47548,
            "stage67_new_routes_materialized": 3603,
            "stage67_new_by_consumer": {
                "evolution": 341,
                "tutor": 740,
                "egg": 2522,
            },
            "cumulative_routes_materialized": 51151,
            "cumulative_by_consumer": cumulative_by_consumer,
            "materialized_route_content_sha256": materialized_digest.hexdigest(),
            "selected_routes_deferred": 67218,
            "deferred_selected_by_consumer": deferred_selected_by_consumer,
            "deferred_reason_counts": dict(sorted(deferred_reasons.items())),
            "deferred_route_content_sha256": deferred_digest.hexdigest(),
        },
        "egg_boundary": {
            "input_routes": 2572,
            "normal_routes_materialized": 2522,
            "materialized_target_count": 450,
            "special_breeding_routes_deferred": len(egg_special_rows),
            "special_breeding_routes": egg_special_rows,
            "legacy_alias_collision_routes_deferred": len(egg_alias_rows),
            "legacy_alias_collision_routes": egg_alias_rows,
            "incense_union_conflict_routes_deferred": len(egg_incense_rows),
            "incense_union_conflict_routes": egg_incense_rows,
            "move_1063_routes_non_adopted": non_adopted_counts["egg"],
        },
        "non_adopted": {
            "decision": "MOVE_1063_NOT_ADOPTED_NO_REPLACEMENT",
            "project_move_id": 1063,
            "route_count": len(non_adopted_rows),
            "routes_by_consumer": dict(sorted(non_adopted_counts.items())),
            "route_content_sha256": non_adopted_digest.hexdigest(),
            "routes": non_adopted_rows,
            "counts_as_remaining_runtime_work": False,
        },
        "claims": {
            "evolution_routes_connected_to_level_zero_abi": True,
            "existing_slot_tutor_routes_connected": True,
            "normal_egg_routes_connected": True,
            "special_breeding_coerced_to_normal_egg": False,
            "legacy_alias_routes_written_to_non_adopted_species": False,
            "incense_union_conflict_routes_claimed_exact": False,
            "shared_egg_union_into_direct_egg": False,
            "reminder_coerced_to_level_zero": False,
            "move_1063_serialized_or_replaced": False,
            "full_p03_implemented": False,
        },
    }
    return ConsumerRoutes(
        target_records=target_records,
        evolution_rows={key: tuple(rows) for key, rows in evolution.items()},
        tutor_rows={key: tuple(rows) for key, rows in tutor.items()},
        egg_rows={key: tuple(rows) for key, rows in egg.items()},
        route_audit=route_audit,
    )


def _read_level_rows(rom: bytes, pointer: int, species_id: int) -> list[tuple[int, int]]:
    cursor = _rom_offset(pointer, f"species {species_id} level pointer")
    rows: list[tuple[int, int]] = []
    for _ in range(50):
        if cursor + 3 > len(rom):
            _fail(f"species {species_id} level rowがROM範囲外です")
        move_id, level = struct.unpack_from("<HB", rom, cursor)
        cursor += 3
        if move_id == 0 and level == 0xFF:
            return rows
        if not 1 <= move_id <= 1062 or not 0 <= level <= 100:
            _fail(f"species {species_id} parent level row ABI不一致")
        rows.append((move_id, level))
    _fail(f"species {species_id} parent level rowが50行で終端しません")


def _serialize_evolution_payload(
    parent: bytes,
    routes: ConsumerRoutes,
    level_root_offset: int,
    config: Mapping[str, Any],
) -> tuple[bytes, dict[int, int], dict[int, tuple[tuple[int, int], ...]]]:
    declaration = config["allocations"][0]
    alignment = int(declaration["row_start_alignment"])
    if alignment != 2:
        _fail("evolution row start alignmentは2必須です")
    payload = bytearray()
    offsets: dict[int, int] = {}
    output_rows: dict[int, tuple[tuple[int, int], ...]] = {}
    for species_id in sorted(routes.evolution_rows):
        while len(payload) % alignment:
            payload.append(0xFF)
        offsets[species_id] = len(payload)
        parent_pointer = _read_u32(
            parent, level_root_offset + species_id * 4,
            f"species {species_id} level pointer",
        )
        inherited = _read_level_rows(parent, parent_pointer, species_id)
        if any(level == 0 for _, level in inherited):
            _fail(f"species {species_id} Stage66表に予期しないlevel0 rowがあります")
        evolution = [
            (int(row["project_move_id"]), 0)
            for row in routes.evolution_rows[species_id]
        ]
        combined = tuple(evolution + inherited)
        if len(combined) > 50:
            _fail(f"species {species_id} evolution追加後50行を超えます")
        output_rows[species_id] = combined
        for move_id, level in combined:
            payload.extend(struct.pack("<HB", move_id, level))
        payload.extend(b"\x00\x00\xFF")
    expected_size = int(declaration["size"])
    expected_hash = str(declaration["content_sha256"])
    if len(payload) != expected_size or sha256(payload) != expected_hash:
        _fail(
            "evolution payload size/hash不一致: "
            f"{len(payload)}/{sha256(payload)}"
        )
    return bytes(payload), offsets, output_rows


def _parse_egg_table(
    rom: bytes, root: int,
) -> tuple[dict[int, tuple[int, ...]], tuple[int, ...], bytes]:
    cursor = _rom_offset(root, "egg table root")
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
            if active is None:
                _fail("egg tableにrecordがありません")
            if order != sorted(order) or len(order) != len(set(order)):
                _fail("parent egg marker order/uniqueness不一致")
            return (
                {key: tuple(rows) for key, rows in records.items()},
                tuple(order),
                rom[start:cursor],
            )
        if value >= 20_000:
            species_id = value - 20_000
            if not 0 <= species_id < SPECIES_COUNT or species_id in records:
                _fail(f"egg species marker不正: {species_id}")
            active = species_id
            order.append(species_id)
            records[species_id] = []
        else:
            if active is None or not 1 <= value <= 1062:
                _fail(f"egg Move row不正: {value}")
            records[active].append(value)
            if len(records[active]) > 50:
                _fail(f"egg rowが50 Moveを超えます: {active}")
    _fail("egg tableが20,000 U16以内に終端しません")


def _serialize_egg_payload(
    parent_records: Mapping[int, Sequence[int]],
    parent_order: Sequence[int],
    routes: ConsumerRoutes,
    config: Mapping[str, Any],
) -> tuple[bytes, dict[int, tuple[int, ...]], dict[str, Any]]:
    declaration = config["allocations"][1]
    rows = {species_id: tuple(moves) for species_id, moves in parent_records.items()}
    replaced = 0
    added: list[int] = []
    for species_id, route_rows in sorted(routes.egg_rows.items()):
        moves = tuple(int(row["project_move_id"]) for row in route_rows)
        if len(moves) != len(set(moves)) or not moves:
            _fail(f"egg replacement route重複/空行: {species_id}")
        if species_id in rows:
            replaced += 1
        else:
            added.append(species_id)
        rows[species_id] = moves
    payload = bytearray()
    for species_id in sorted(rows):
        payload.extend(struct.pack("<H", 20_000 + species_id))
        for move_id in rows[species_id]:
            payload.extend(struct.pack("<H", move_id))
    payload.extend(b"\xFF\xFF")
    if len(payload) != int(declaration["size"]) \
            or sha256(payload) != declaration["content_sha256"]:
        _fail(f"egg payload size/hash不一致: {len(payload)}/{sha256(payload)}")
    if replaced != 439 or added != [885, 925, *range(1040, 1049)]:
        _fail(f"egg replacement/new marker集合不一致: {replaced}/{added}")
    preserved_ids = sorted(set(parent_order) - set(routes.egg_rows))
    if any(rows[species_id] != tuple(parent_records[species_id]) for species_id in preserved_ids):
        _fail("未採用Vega egg recordがbyte値保持されていません")
    if len(rows) != 1399 or sum(map(len, rows.values())) != 6159:
        _fail("Stage67 egg table marker/move件数不一致")
    audit = {
        "parent_marker_count": len(parent_order),
        "output_marker_count": len(rows),
        "output_move_count": sum(map(len, rows.values())),
        "safe_target_rows_replaced": replaced,
        "safe_target_rows_added": len(added),
        "added_species_ids": added,
        "unadopted_parent_rows_preserved": len(preserved_ids),
        "terminator_u16_index": len(payload) // 2 - 1,
        "last_nonterminator_u16_index": len(payload) // 2 - 2,
    }
    return bytes(payload), rows, audit


def _first_fit(
    allocation: Mapping[str, Any], region_name: str, size: int, alignment: int,
) -> int:
    regions = [row for row in allocation.get("regions", []) if row.get("name") == region_name]
    if len(regions) != 1 or regions[0].get("kind") != "allocatable":
        _fail(f"allocatable regionが一意ではありません: {region_name}")
    region = regions[0]
    cursor = int(region["start"])
    previous_end = int(region["start"])
    intervals = sorted(
        (int(row["start"]), int(row["end_exclusive"]), str(row["name"]))
        for row in allocation.get("allocations", [])
        if row.get("region") == region_name
    )
    for start, end, name in intervals:
        if start < previous_end or end <= start or end > int(region["end_exclusive"]):
            _fail(f"allocation overlap/range不正: {name}")
        candidate = (cursor + alignment - 1) // alignment * alignment
        if candidate + size <= start:
            return candidate
        cursor = max(cursor, end)
        previous_end = end
    candidate = (cursor + alignment - 1) // alignment * alignment
    if candidate + size > int(region["end_exclusive"]):
        _fail(f"allocation容量不足: {region_name}/{size}")
    return candidate


def _updated_allocation(
    parent: Mapping[str, Any], declarations: Sequence[Mapping[str, Any]],
    payloads: Sequence[bytes],
) -> dict[str, Any]:
    if len(declarations) != len(payloads):
        _fail("allocation declaration/payload件数不一致")
    result = copy.deepcopy(parent)
    if result.get("schema_version") != 1:
        _fail("parent allocation schema不一致")
    sequences = [int(row.get("sequence", -1)) for row in result.get("allocations", [])]
    if sorted(sequences) != list(range(len(sequences))):
        _fail("parent allocation sequenceが連続していません")
    for declaration, payload in zip(declarations, payloads, strict=True):
        start = hex_int(declaration.get("start"), "allocation.start")
        size = int(declaration.get("size", -1))
        alignment = int(declaration.get("alignment", -1))
        if size != len(payload) or alignment != 4 or start % alignment:
            _fail("Stage67 allocation size/alignment不一致")
        first_fit = _first_fit(result, str(declaration.get("region")), size, alignment)
        if start != first_fit:
            _fail(f"Stage67 allocationがFIRST_FITではありません: 0x{first_fit:X}")
        entry = {
            "alignment": alignment,
            "content_sha256": sha256(payload),
            "end_exclusive": start + size,
            "gba_end_exclusive": ROM_BASE + start + size,
            "gba_start": ROM_BASE + start,
            "name": declaration["name"],
            "owner": declaration["owner"],
            "placement": declaration["placement"],
            "purpose": declaration["purpose"],
            "region": declaration["region"],
            "sequence": len(result["allocations"]),
            "size": size,
            "start": start,
        }
        if entry["owner"] != TASK or entry["placement"] != "FIRST_FIT":
            _fail("Stage67 allocation owner/placement不一致")
        result["allocations"].append(entry)

    allocatable_bytes = 0
    allocated_bytes = 0
    region_usage: list[dict[str, Any]] = []
    for region in result["regions"]:
        rows = [row for row in result["allocations"] if row["region"] == region["name"]]
        intervals = sorted((int(row["start"]), int(row["end_exclusive"])) for row in rows)
        if any(left[1] > right[0] for left, right in zip(intervals, intervals[1:])):
            _fail(f"Stage67 allocation overlap: {region['name']}")
        used = sum(int(row["size"]) for row in rows)
        if region["kind"] == "allocatable":
            allocatable_bytes += int(region["size"])
            allocated_bytes += used
            remaining = int(region["size"]) - used
            if remaining < 0:
                _fail(f"allocation region容量超過: {region['name']}")
        else:
            if rows:
                _fail(f"reserved regionにallocationがあります: {region['name']}")
            remaining = 0
        region_usage.append({
            "allocated_bytes": used,
            "allocation_count": len(rows),
            "kind": region["kind"],
            "region": region["name"],
            "remaining_bytes": remaining,
            "size": int(region["size"]),
        })
    summaries = result.get("summaries")
    if not isinstance(summaries, dict):
        _fail("allocation summariesがありません")
    summaries.update({
        "allocatable_bytes": allocatable_bytes,
        "allocatable_region_count": sum(r["kind"] == "allocatable" for r in result["regions"]),
        "allocated_bytes": allocated_bytes,
        "allocation_count": len(result["allocations"]),
        "gba_rom_base": ROM_BASE,
        "overlap_count": 0,
        "region_bytes": sum(int(r["size"]) for r in result["regions"]),
        "region_count": len(result["regions"]),
        "region_usage": region_usage,
        "remaining_allocatable_bytes": allocatable_bytes - allocated_bytes,
        "reserved_bytes": sum(int(r["size"]) for r in result["regions"] if r["kind"] == "reserved"),
        "reserved_region_count": sum(r["kind"] == "reserved" for r in result["regions"]),
        "rom_size": ROM_SIZE,
    })
    return result


@dataclass(frozen=True)
class Stage67Image:
    config: dict[str, Any]
    stage66: bytes
    parent: bytes
    rom: bytes
    allocation: dict[str, Any]
    route_audit: dict[str, Any]
    change_audit: dict[str, Any]
    input_audit: dict[str, Any]
    runtime_cases: dict[str, Any]


def build_stage67_image(root: Path, config_path: Path) -> Stage67Image:
    """Stage66+P02 overlayからStage67 exact imageを返す。"""

    config = read_config(root, config_path)
    _validate_config(config)
    inputs = config["inputs"]
    stage66 = fixed_input(root, inputs["stage66_rom"], "Stage66 ROM")
    stage66_metadata = _json(
        fixed_input(root, inputs["stage66_metadata"], "Stage66 metadata"),
        "Stage66 metadata",
    )
    stage66_checkpoint = _json(
        fixed_input(root, inputs["stage66_checkpoint"], "Stage66 checkpoint"),
        "Stage66 checkpoint",
    )
    stage66_route_audit = _json(
        fixed_input(root, inputs["stage66_route_audit"], "Stage66 route audit"),
        "Stage66 route audit",
    )
    parent_allocation = _json(
        fixed_input(root, inputs["stage66_allocation"], "Stage66 allocation"),
        "Stage66 allocation",
    )
    _validate_stage66_parent(
        stage66, stage66_metadata, stage66_checkpoint, stage66_route_audit, config,
    )
    p02_config = _json(
        fixed_input(root, inputs["p02_acceptance_config"], "P02 acceptance config"),
        "P02 acceptance config",
    )
    p02_checkpoint = _json(
        fixed_input(root, inputs["p02_acceptance_checkpoint"], "P02 acceptance checkpoint"),
        "P02 acceptance checkpoint",
    )
    fixed_input(root, inputs["p02_acceptance_builder"], "P02 acceptance builder")
    parent, p02_repair = _validate_p02_overlay(
        stage66, p02_config, p02_checkpoint, config,
    )
    contract = _json(fixed_input(root, inputs["p03_contract"], "P03 contract"), "P03 contract")
    index = _json(
        fixed_input(root, inputs["p03_compiled_index"], "P03 compiled index"),
        "P03 compiled index",
    )
    handoff = _json(
        fixed_input(root, inputs["p03_runtime_handoff"], "P03 runtime handoff"),
        "P03 runtime handoff",
    )
    fixed_input(root, inputs["adoption_decisions"], "P03 adoption decisions")
    fixed_input(root, inputs["identity_contract"], "P01 identity contract")
    fixed_input(root, inputs["species_manifest"], "Species manifest")
    fixed_input(root, inputs["move_manifest"], "Move manifest")
    fixed_input(root, inputs["learn_move_source"], "CFRU learn_move source")
    fixed_input(root, inputs["item_source"], "CFRU item source")
    fixed_input(root, inputs["daycare_source"], "CFRU daycare source")
    fixed_input(root, inputs["linker_script"], "CFRU linker script")
    learnsets_zip = fixed_path(root, inputs["learnsets_zip"], "P03 immutable learnsets ZIP")
    routes = _compile_routes(root, learnsets_zip, contract, index, handoff)

    tables = config["runtime_tables"]
    level = tables["level_up_and_evolution"]
    level_root_site = hex_int(level["root_pointer_site_rom_offset"], "level root site")
    level_literal_site = hex_int(level["runtime_literal_site_rom_offset"], "level literal site")
    level_root = _read_u32(parent, level_root_site, "level root")
    if level_root != hex_int(level["expected_parent_root_runtime_address"], "level root") \
            or _read_u32(parent, level_literal_site, "level literal") != level_root:
        _fail("parent level root/literal不一致")
    level_root_offset = _rom_offset(level_root, "level root")
    if level_root_offset + SPECIES_COUNT * 4 > len(parent):
        _fail("level pointer table range不一致")
    evolution_payload, evolution_relative, evolution_rows = _serialize_evolution_payload(
        parent, routes, level_root_offset, config,
    )

    tutor = tables["tutor"]
    tutor_root_site = hex_int(tutor["compatibility_root_site_rom_offset"], "tutor root site")
    tutor_root = _read_u32(parent, tutor_root_site, "tutor root")
    if tutor_root != hex_int(tutor["expected_parent_root_runtime_address"], "tutor root"):
        _fail("parent tutor root不一致")
    tutor_root_offset = _rom_offset(tutor_root, "tutor root")
    tutor_stride = int(tutor["compatibility_stride"])
    if tutor_stride != 16 or tutor_root_offset + SPECIES_COUNT * tutor_stride > len(parent):
        _fail("tutor compatibility ABI/range不一致")
    tutor_catalog_site = hex_int(tutor["catalog_root_site_rom_offset"], "tutor catalog site")
    tutor_catalog_root = _read_u32(parent, tutor_catalog_site, "tutor catalog root")
    if tutor_catalog_root != hex_int(tutor["expected_catalog_root_runtime_address"], "tutor catalog"):
        _fail("parent tutor catalog root不一致")
    tutor_catalog_offset = _rom_offset(tutor_catalog_root, "tutor catalog")
    tutor_slots = int(tutor["catalog_slot_count"])
    if tutor_slots != 64 or tutor_catalog_offset + tutor_slots * 2 > len(parent):
        _fail("tutor catalog range不一致")
    tutor_catalog = tuple(
        struct.unpack_from("<H", parent, tutor_catalog_offset + slot * 2)[0]
        for slot in range(tutor_slots)
    )

    egg = tables["egg"]
    egg_primary_site = hex_int(egg["primary_root_literal_rom_offset"], "egg primary root")
    egg_secondary_site = hex_int(egg["secondary_scan_root_literal_rom_offset"], "egg secondary root")
    egg_limit_site = hex_int(egg["scan_limit_literal_rom_offset"], "egg scan limit")
    parent_egg_root = _read_u32(parent, egg_primary_site, "parent egg primary root")
    parent_secondary = _read_u32(parent, egg_secondary_site, "parent egg secondary root")
    parent_limit = _read_u32(parent, egg_limit_site, "parent egg scan limit")
    if (
        parent_egg_root != hex_int(egg["expected_parent_primary_root"], "parent egg root")
        or parent_secondary != hex_int(egg["expected_parent_secondary_root"], "parent egg secondary")
        or parent_limit != int(egg["expected_parent_scan_limit"])
    ):
        _fail("parent egg dual-root/scan-limit preimage不一致")
    parent_egg_records, parent_egg_order, parent_egg_raw = _parse_egg_table(
        parent, parent_egg_root,
    )
    if len(parent_egg_raw) != int(egg["expected_parent_table_size"]) \
            or sha256(parent_egg_raw) != egg["expected_parent_table_sha256"]:
        _fail("parent egg table identity不一致")
    egg_payload, egg_rows, egg_table_audit = _serialize_egg_payload(
        parent_egg_records, parent_egg_order, routes, config,
    )

    payloads = (evolution_payload, egg_payload)
    allocation = _updated_allocation(parent_allocation, config["allocations"], payloads)
    allocation_starts = [hex_int(row["start"], "allocation.start") for row in config["allocations"]]
    for start, payload in zip(allocation_starts, payloads, strict=True):
        if parent[start:start + len(payload)] != b"\xFF" * len(payload):
            _fail(f"Stage67 allocation preimageが全FFではありません: 0x{start:X}")

    evolution_start, egg_start = allocation_starts
    output = bytearray(parent)
    output[evolution_start:evolution_start + len(evolution_payload)] = evolution_payload
    evolution_pointer_entries: dict[int, tuple[int, int]] = {}
    for species_id, relative in evolution_relative.items():
        entry = level_root_offset + species_id * 4
        pointer = ROM_BASE + evolution_start + relative
        if pointer % 2:
            _fail(f"evolution level pointer alignment不一致: {species_id}")
        evolution_pointer_entries[species_id] = (entry, pointer)
        struct.pack_into("<I", output, entry, pointer)

    target_ids = {int(row["canonical_id"]) for row in routes.target_records}
    tutor_replacements: dict[int, tuple[int, bytes]] = {}
    for target in routes.target_records:
        species_id = int(target["canonical_id"])
        replacement = bytearray(tutor_stride)
        for row in routes.tutor_rows.get(species_id, ()):
            slot = int(row["runtime_slot_zero_based"])
            if tutor_catalog[slot] != int(row["project_move_id"]):
                _fail(f"tutor slot catalog Move不一致: {species_id}/{slot}")
            replacement[slot // 8] |= 1 << slot % 8
        replacement_bytes = bytes(replacement)
        if len(_set_bits(replacement_bytes, slots=tutor_slots)) \
                != len(routes.tutor_rows.get(species_id, ())):
            _fail(f"tutor bit projection count不一致: {species_id}")
        offset = tutor_root_offset + species_id * tutor_stride
        tutor_replacements[species_id] = (offset, replacement_bytes)
        output[offset:offset + tutor_stride] = replacement_bytes

    output[egg_start:egg_start + len(egg_payload)] = egg_payload
    output_egg_root = ROM_BASE + egg_start
    output_egg_limit = egg_table_audit["last_nonterminator_u16_index"]
    if output_egg_limit != int(egg["output_scan_limit"]):
        _fail("output egg scan limit固定値不一致")
    struct.pack_into("<I", output, egg_primary_site, output_egg_root)
    struct.pack_into("<I", output, egg_secondary_site, output_egg_root)
    struct.pack_into("<I", output, egg_limit_site, output_egg_limit)
    result = bytes(output)
    if len(result) != ROM_SIZE:
        _fail("Stage67 ROM sizeが変わりました")

    if (
        _read_u32(result, level_root_site, "output level root") != level_root
        or _read_u32(result, level_literal_site, "output level literal") != level_root
        or _read_u32(result, tutor_root_site, "output tutor root") != tutor_root
        or _read_u32(result, tutor_catalog_site, "output tutor catalog")
        != tutor_catalog_root
        or _read_u32(result, egg_primary_site, "output egg primary") != output_egg_root
        or _read_u32(result, egg_secondary_site, "output egg secondary") != output_egg_root
        or _read_u32(result, egg_limit_site, "output egg limit") != output_egg_limit
    ):
        _fail("Stage67 consumer root readback不一致")

    changed_offsets = [
        offset for offset, (before, after) in enumerate(zip(parent, result, strict=True))
        if before != after
    ]

    def allowed(offset: int) -> bool:
        if evolution_start <= offset < evolution_start + len(evolution_payload):
            return True
        if egg_start <= offset < egg_start + len(egg_payload):
            return True
        if any(site <= offset < site + 4 for site in (
            egg_primary_site, egg_secondary_site, egg_limit_site,
        )):
            return True
        if level_root_offset <= offset < level_root_offset + SPECIES_COUNT * 4:
            return ((offset - level_root_offset) // 4) in evolution_pointer_entries
        if tutor_root_offset <= offset < tutor_root_offset + SPECIES_COUNT * tutor_stride:
            return ((offset - tutor_root_offset) // tutor_stride) in target_ids
        return False

    outside = [offset for offset in changed_offsets if not allowed(offset)]
    if outside:
        _fail(f"Stage67に宣言範囲外変更があります: 0x{outside[0]:X}")
    for species_id, (entry, pointer) in evolution_pointer_entries.items():
        if _read_u32(result, entry, f"species {species_id} output level pointer") != pointer:
            _fail(f"evolution pointer readback不一致: {species_id}")
    for species_id, (offset, row) in tutor_replacements.items():
        if result[offset:offset + tutor_stride] != row:
            _fail(f"tutor compatibility readback不一致: {species_id}")
    parsed_output_egg, output_egg_order, output_egg_raw = _parse_egg_table(
        result, output_egg_root,
    )
    if parsed_output_egg != egg_rows or output_egg_raw != egg_payload:
        _fail("output egg table logical/byte readback不一致")

    p02_offsets = [int(value) for value in p02_repair["changed_rom_offsets"]]
    if any(result[offset] != parent[offset] for offset in p02_offsets):
        _fail("Stage67がP02 overlay修正byteを落としました")
    stage66_to_output = [
        offset for offset, (before, after) in enumerate(zip(stage66, result, strict=True))
        if before != after
    ]
    if not set(p02_offsets) <= set(stage66_to_output):
        _fail("Stage67累積差分にP02 overlayが含まれません")

    non_target_ids = sorted(set(range(SPECIES_COUNT)) - target_ids)
    non_target_before = bytearray()
    non_target_after = bytearray()
    for species_id in non_target_ids:
        level_offset = level_root_offset + species_id * 4
        tutor_offset = tutor_root_offset + species_id * tutor_stride
        non_target_before.extend(parent[level_offset:level_offset + 4])
        non_target_before.extend(parent[tutor_offset:tutor_offset + tutor_stride])
        non_target_after.extend(result[level_offset:level_offset + 4])
        non_target_after.extend(result[tutor_offset:tutor_offset + tutor_stride])
    if non_target_before != non_target_after or len(non_target_ids) != 321:
        _fail("非採用Vega speciesのlevel/tutor rowが保持されていません")

    evolution_cases = []
    for species_id in sorted(routes.evolution_rows):
        pointer = evolution_pointer_entries[species_id][1]
        evolution_moves = [int(row["project_move_id"]) for row in routes.evolution_rows[species_id]]
        evolution_cases.append({
            "species_id": species_id,
            "pointer": f"0x{pointer:08X}",
            "moves": evolution_moves,
            "total_level_rows": len(evolution_rows[species_id]),
        })
    tutor_cases = []
    for species_id in sorted(routes.tutor_rows):
        offset, row = tutor_replacements[species_id]
        set_slots = _set_bits(row, slots=tutor_slots)
        negative = next(slot for slot in range(tutor_slots) if slot not in set_slots)
        tutor_cases.append({
            "species_id": species_id,
            "compatibility_row_rom_offset": offset,
            "set_slots": set_slots,
            "moves": [tutor_catalog[slot] for slot in set_slots],
            "negative_slot": negative,
        })
    egg_cases = []
    for species_id in sorted(routes.egg_rows):
        egg_cases.append({
            "species_id": species_id,
            "moves": list(egg_rows[species_id]),
        })
    runtime_cases = {
        "evolution": evolution_cases,
        "tutor": tutor_cases,
        "egg": egg_cases,
    }

    spans = _changed_spans(parent, result)
    cumulative_spans = _changed_spans(stage66, result)
    change_audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "parent_chain": {
            "stage66_sha256": sha256(stage66),
            "p02_overlay_parent_sha256": sha256(parent),
            "p02_overlay_changed_bytes": len(p02_offsets),
            "p02_overlay_changed_offsets_sha256": sha256(stable_json(p02_offsets)),
            "p02_overlay_bytes_preserved": True,
        },
        "roots": {
            "level_root_pointer_site_rom_offset": level_root_site,
            "level_runtime_literal_site_rom_offset": level_literal_site,
            "level_root_runtime_address": f"0x{level_root:08X}",
            "tutor_root_pointer_site_rom_offset": tutor_root_site,
            "tutor_root_runtime_address": f"0x{tutor_root:08X}",
            "tutor_catalog_root_site_rom_offset": tutor_catalog_site,
            "tutor_catalog_runtime_address": f"0x{tutor_catalog_root:08X}",
            "egg_primary_root_literal_rom_offset": egg_primary_site,
            "egg_parent_primary_root_runtime_address": f"0x{parent_egg_root:08X}",
            "egg_secondary_scan_root_literal_rom_offset": egg_secondary_site,
            "egg_parent_secondary_root_runtime_address": f"0x{parent_secondary:08X}",
            "egg_scan_limit_literal_rom_offset": egg_limit_site,
            "egg_parent_scan_limit": parent_limit,
            "egg_output_root_runtime_address": f"0x{output_egg_root:08X}",
            "egg_output_scan_limit": output_egg_limit,
            "measured_from_exact_p02_overlay_parent": True,
        },
        "preimage": {
            "parent_rom_sha256": sha256(parent),
            "evolution_allocation_all_ff": True,
            "egg_allocation_all_ff": True,
            "parent_egg_table_size": len(parent_egg_raw),
            "parent_egg_table_sha256": sha256(parent_egg_raw),
            "parent_egg_marker_count": len(parent_egg_order),
            "tutor_catalog_sha256": sha256(parent[tutor_catalog_offset:tutor_catalog_offset + tutor_slots * 2]),
        },
        "output_tables": {
            "evolution_target_pointer_entries_repointed": len(evolution_pointer_entries),
            "evolution_routes_added": 341,
            "evolution_combined_level_rows": sum(map(len, evolution_rows.values())),
            "evolution_payload_rom_offset": evolution_start,
            "evolution_payload_size": len(evolution_payload),
            "evolution_payload_sha256": sha256(evolution_payload),
            "tutor_target_rows_replaced": len(tutor_replacements),
            "tutor_bits_set": sum(len(row["set_slots"]) for row in tutor_cases),
            "tutor_catalog_changed": False,
            "egg_payload_rom_offset": egg_start,
            "egg_payload_size": len(egg_payload),
            "egg_payload_sha256": sha256(egg_payload),
            **egg_table_audit,
        },
        "preservation": {
            "non_adopted_species_count": len(non_target_ids),
            "non_adopted_level_and_tutor_rows_sha256": sha256(non_target_after),
            "non_adopted_level_and_tutor_rows_unchanged": True,
            "unadopted_parent_egg_records_preserved": True,
            "parent_level_and_egg_payloads_destructively_overwritten": False,
            "p02_overlay_dropped": False,
            "rom_size_changed": False,
        },
        "changed_byte_count": len(changed_offsets),
        "changed_offsets_sha256": sha256(stable_json(changed_offsets)),
        "changed_span_count": len(spans),
        "changed_spans": spans,
        "outside_declared_range_count": 0,
        "stage66_cumulative_changed_byte_count": len(stage66_to_output),
        "stage66_cumulative_changed_offsets_sha256": sha256(stable_json(stage66_to_output)),
        "stage66_cumulative_changed_span_count": len(cumulative_spans),
        "stage66_cumulative_changed_spans": cumulative_spans,
        "allowed_domains": [
            "330 corrected evolution target level pointer entries",
            "one FIRST_FIT evolution+inherited-level payload",
            "1300 corrected target tutor compatibility rows",
            "one FIRST_FIT egg replacement payload",
            "egg primary root, secondary scan root, and scan-limit literals",
        ],
    }
    route_audit = copy.deepcopy(routes.route_audit)
    route_audit["serialization"] = {
        "evolution_payload_size": len(evolution_payload),
        "evolution_payload_sha256": sha256(evolution_payload),
        "evolution_target_count": len(evolution_cases),
        "tutor_compatibility_stride": tutor_stride,
        "tutor_catalog_slots": tutor_slots,
        "egg_payload_size": len(egg_payload),
        "egg_payload_sha256": sha256(egg_payload),
        "egg_dual_root_and_scan_limit_repaired": True,
        "runtime_case_counts": {
            "evolution_species": len(evolution_cases),
            "evolution_routes": sum(len(row["moves"]) for row in evolution_cases),
            "tutor_species": len(tutor_cases),
            "tutor_routes": sum(len(row["set_slots"]) for row in tutor_cases),
            "egg_species": len(egg_cases),
            "egg_routes": sum(len(row["moves"]) for row in egg_cases),
        },
    }
    input_audit = {
        key: {"path": value["path"], "size": value["size"], "sha256": value["sha256"]}
        for key, value in inputs.items()
        if isinstance(value, dict) and {"path", "size", "sha256"} <= set(value)
        and key != "clean_rom"
    }
    input_audit["p02_overlay_parent"] = {
        "classification": "IN_MEMORY_P02_OVERLAY_PARENT_FOR_STAGE67",
        "size": len(parent),
        "sha256": sha256(parent),
        "changed_bytes_from_stage66": len(p02_offsets),
    }
    return Stage67Image(
        config=config,
        stage66=stage66,
        parent=parent,
        rom=result,
        allocation=allocation,
        route_audit=route_audit,
        change_audit=change_audit,
        input_audit=input_audit,
        runtime_cases=runtime_cases,
    )
