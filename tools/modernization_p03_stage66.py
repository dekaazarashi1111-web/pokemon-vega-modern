"""P03 Stage66 bulk learnset checkpointの決定的ROM imageを構築する。

訂正採用1300 targetのlevel-up経路を置換表へcompileし、現行catalogで供給済みの
machine経路だけをcompatibility bitsetへ接続する。未実装Move 1063、供給不足、
および残るconsumer familyは削除せず明示的なdeferred集合として監査する。
"""

from __future__ import annotations

import copy
import hashlib
import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn

from tools.modernization_learnsets import iter_compiled_p03_routes


ROM_BASE = 0x08000000
ROM_END = 0x0A000000
ROM_SIZE = 32 * 1024 * 1024
SPECIES_COUNT = 1621
TASK = "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT"
STAGE = 66
P03_TASK = "USER-MODERNIZATION-P03"
EXPECTED_CONSUMER_COUNTS = {
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
EXPECTED_SIDE_CHANGE_COUNTS = {
    "egg": 9,
    "level_up": 15,
    "machine": 68,
    "pre_evolution_carry": 42,
    "reminder": 3,
    "shared_egg": 18,
    "tutor": 4,
}


class ModernizationP03Stage66Error(ValueError):
    """Stage66 input identity、route、ROM preimage、allocation違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage66Error(message)


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
        _fail(f"Stage66 configが通常ファイルではありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"Stage66 configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("Stage66 config rootがobjectではありません")
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
    if not (0 <= offset <= len(raw) - 4):
        _fail(f"{label} offsetがROM範囲外です: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, label: str) -> int:
    if not (ROM_BASE <= address < ROM_END):
        _fail(f"{label}が32MiB ROM runtime範囲外です: 0x{address:08X}")
    return address - ROM_BASE


def _set_bits(row: bytes) -> list[int]:
    return [slot for slot in range(len(row) * 8) if row[slot // 8] & 1 << slot % 8]


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
        _fail("Stage66 config schema/task/stage不一致")
    scope = config.get("bulk_scope", {})
    expected_scope = {
        "corrected_target_count": 1300,
        "contract_route_count": 118528,
        "level_up_input_routes": 18530,
        "level_up_runtime_ready_routes": 18515,
        "level_up_move_1063_deferred_routes": 15,
        "machine_input_routes": 55380,
        "machine_existing_slot_routes": 29033,
        "machine_supply_required_routes": 26347,
        "materialized_routes": 47548,
        "remaining_routes": 70980,
        "adoption_policy": "REPLACE_NORMAL_TARGET_WITH_FIXED_REFERENCE_NOT_UNION",
    }
    if scope != expected_scope:
        _fail("Stage66 bulk scope固定値不一致")
    acceptance = config.get("acceptance", {})
    if acceptance != {
        "static_contract_gate": "REQUIRED",
        "real_consumer_mgba_gate": "REQUIRED",
        "independent_processes": 2,
        "incremental_bps_round_trip": "REQUIRED",
        "clean_bps_round_trip": "REQUIRED",
        "task_completion": "CHECKPOINT_NOT_P03_DONE",
    }:
        _fail("Stage66 acceptanceがcheckpoint境界を固定していません")


def _validate_parent(
    parent: bytes,
    metadata: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    expected_path = config["inputs"]["parent_rom"]["path"]
    parent_sha = sha256(parent)
    if len(parent) != ROM_SIZE:
        _fail(f"Stage65 parent ROM size不一致: {len(parent)}")
    if (
        metadata.get("schema_version") != 1
        or metadata.get("stage") != 65
        or metadata.get("status") != "CHECKPOINT"
        or metadata.get("done") is not False
        or metadata.get("checkpoint_marker") != "CHECKPOINT_NOT_P03_DONE"
        or metadata.get("output", {}).get("path") != expected_path
        or metadata.get("output", {}).get("sha256") != parent_sha
    ):
        _fail("Stage65 metadataがexact checkpoint parentを保証していません")
    acceptance = metadata.get("acceptance", {})
    for gate in (
        "static_contract_gate",
        "allocation_gate",
        "incremental_bps_round_trip",
        "clean_bps_round_trip",
        "real_consumer_mgba_gate",
    ):
        if acceptance.get(gate) != "PASS":
            _fail(f"Stage65 parent gate未達: {gate}")
    if acceptance.get("task_completion") != "CHECKPOINT_NOT_P03_DONE":
        _fail("Stage65 parentのcheckpoint境界が不正です")
    if (
        checkpoint.get("schema_version") != 1
        or checkpoint.get("stage") != 65
        or checkpoint.get("status") != "CHECKPOINT"
        or checkpoint.get("done") is not False
        or checkpoint.get("checkpoint_marker") != "CHECKPOINT_NOT_P03_DONE"
        or checkpoint.get("output", {}).get("sha256") != parent_sha
    ):
        _fail("P03 Stage65 checkpointとparent ROMが一致しません")


@dataclass(frozen=True)
class BulkRoutes:
    target_records: tuple[dict[str, Any], ...]
    level_rows: dict[int, tuple[dict[str, Any], ...]]
    machine_rows: dict[int, tuple[dict[str, Any], ...]]
    route_audit: dict[str, Any]


def _compile_bulk_routes(
    root: Path,
    learnsets_zip: Path,
    contract: Mapping[str, Any],
    index: Mapping[str, Any],
    handoff: Mapping[str, Any],
    config: Mapping[str, Any],
) -> BulkRoutes:
    corrected = contract.get("corrected_adoption", {})
    consumers = corrected.get("consumers", {})
    if (
        contract.get("schema_version") != 1
        or contract.get("task") != P03_TASK
        or contract.get("status") != "PASS"
        or corrected.get("records") != 1300
        or corrected.get("routes") != 118528
        or {key: value.get("count") for key, value in consumers.items()}
        != EXPECTED_CONSUMER_COUNTS
    ):
        _fail("P03 learnset contractの訂正済み集合/count不一致")
    runtime_supply = contract.get("runtime_supply", {})
    if (
        runtime_supply.get("projected_rows_by_family")
        != {"machine": 29033, "tutor": 740}
        or runtime_supply.get("supply_required_rows_by_family")
        != {"machine": 26347, "tutor": 373}
    ):
        _fail("P03 runtime supply family件数不一致")
    if (
        index.get("schema_version") != 1
        or index.get("task") != P03_TASK
        or index.get("status") != "PASS"
        or index.get("record_count") != 1300
        or index.get("route_count") != 118528
        or index.get("ordering")
        != "canonical Species ID ascending; source route order preserved"
    ):
        _fail("P03 compiled indexの全体境界不一致")
    raw_records = index.get("records")
    if not isinstance(raw_records, list) or len(raw_records) != 1300:
        _fail("P03 compiled index records不一致")
    target_records = tuple(dict(row) for row in raw_records)
    target_ids = [row.get("canonical_id") for row in target_records]
    target_keys = [row.get("species_key") for row in target_records]
    if (
        any(isinstance(value, bool) or not isinstance(value, int) for value in target_ids)
        or target_ids != sorted(target_ids)
        or len(set(target_ids)) != 1300
        or len(set(target_keys)) != 1300
        or not all(0 <= value < SPECIES_COUNT for value in target_ids)
    ):
        _fail("P03 corrected target ID/key/order不一致")
    side_change = handoff.get("side_change_1063", {})
    abi = handoff.get("connection_points", {}).get("current_abi", {})
    if (
        handoff.get("schema_version") != 1
        or handoff.get("task") != P03_TASK
        or handoff.get("status") != "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS"
        or side_change.get("status") != "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED"
        or side_change.get("project_move_id") != 1063
        or side_change.get("routes_by_consumer") != EXPECTED_SIDE_CHANGE_COUNTS
        or abi.get("implemented_move_ids") != "0..1062"
        or abi.get("level_up", {}).get("row") != "U16_PROJECT_MOVE_ID + U8_LEVEL"
        or abi.get("level_up", {}).get("terminator") != "0000FF"
        or abi.get("machine_compatibility", {}).get("stride") != 16
        or abi.get("machine_compatibility", {}).get("tm_slots") != 120
        or abi.get("machine_compatibility", {}).get("hm_runtime_indices") != "120..127"
    ):
        _fail("P03 runtime handoff ABI/Move1063未実装境界不一致")

    targets_by_id = {int(row["canonical_id"]): row for row in target_records}
    level_work: dict[int, list[dict[str, Any]]] = defaultdict(list)
    machine_work: dict[int, list[dict[str, Any]]] = defaultdict(list)
    consumer_counts: Counter[str] = Counter()
    consumer_digests = {name: FramedDigest() for name in EXPECTED_CONSUMER_COUNTS}
    move1063_counts: Counter[str] = Counter()
    materialized_digest = FramedDigest()
    deferred_digest = FramedDigest()
    level_deferred: list[dict[str, Any]] = []
    machine_supply_moves: set[int] = set()
    machine_projection_keys: set[tuple[int, int]] = set()
    seen_route_keys: set[str] = set()

    for compiled in iter_compiled_p03_routes(root, learnsets_zip):
        consumer = str(compiled.get("consumer", ""))
        if consumer not in EXPECTED_CONSUMER_COUNTS:
            _fail(f"未知のcompiled consumerです: {consumer}")
        consumer_counts[consumer] += 1
        consumer_digests[consumer].add(compiled)
        source = compiled.get("source_route")
        if not isinstance(source, dict):
            _fail("compiled routeにsource_route objectがありません")
        species_id = compiled.get("target_species_id")
        species_key = str(compiled.get("target_species_key", ""))
        target = targets_by_id.get(species_id)
        if target is None or target.get("species_key") != species_key:
            _fail(f"compiled route target identity不一致: {species_key}/{species_id}")
        route_id = str(source.get("route_id", ""))
        route_key = f"{species_key}:{route_id}"
        if route_key in seen_route_keys:
            _fail(f"compiled target+route重複: {route_key}")
        seen_route_keys.add(route_key)
        move_id = source.get("project_move_id")
        if isinstance(move_id, bool) or not isinstance(move_id, int):
            _fail(f"project Move IDが整数ではありません: {route_key}")
        if move_id == 1063:
            move1063_counts[consumer] += 1

        if consumer == "level_up":
            level = source.get("target_learning_level")
            if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 100:
                _fail(f"level-up learning level不正: {route_key}/{level!r}")
            normalized = {
                "target_species_key": species_key,
                "target_species_id": species_id,
                "route_id": route_id,
                "move_key": compiled.get("move_key"),
                "project_move_id": move_id,
                "learning_level": level,
            }
            if compiled.get("runtime_move_ready") is True and 1 <= move_id <= 1062:
                level_work[species_id].append(normalized)
                materialized_digest.add({"consumer": consumer, **normalized})
            elif move_id == 1063 and compiled.get("runtime_move_ready") is False:
                deferred = {
                    **normalized,
                    "reason": "MOVE_1063_ENGINE_AND_TABLES_NOT_IMPLEMENTED",
                }
                level_deferred.append(deferred)
                deferred_digest.add({"consumer": consumer, **deferred})
            else:
                _fail(f"level-up runtime readinessが契約外です: {route_key}")
        elif consumer == "machine":
            supply = compiled.get("runtime_supply")
            if not isinstance(supply, dict):
                _fail(f"machine routeにruntime_supplyがありません: {route_key}")
            status = supply.get("status")
            normalized = {
                "target_species_key": species_key,
                "target_species_id": species_id,
                "route_id": route_id,
                "method": source.get("method"),
                "source_machine_item": source.get("machine_item"),
                "move_key": compiled.get("move_key"),
                "project_move_id": move_id,
                "runtime_slot_zero_based": supply.get("runtime_slot_zero_based"),
            }
            if status == "EXISTING_RUNTIME_SLOT":
                slot = supply.get("runtime_slot_zero_based")
                if (
                    compiled.get("runtime_move_ready") is not True
                    or isinstance(slot, bool)
                    or not isinstance(slot, int)
                    or not 0 <= slot < 128
                    or not 1 <= move_id <= 1062
                ):
                    _fail(f"existing machine slot route不正: {route_key}")
                projection_key = (species_id, slot)
                if projection_key in machine_projection_keys:
                    _fail(f"machine target+runtime slot重複: {projection_key}")
                machine_projection_keys.add(projection_key)
                machine_work[species_id].append(normalized)
                materialized_digest.add({"consumer": consumer, **normalized})
            elif status == "SUPPLY_REQUIRED":
                if supply.get("runtime_slot_zero_based") is not None:
                    _fail(f"SUPPLY_REQUIRED routeにruntime slotがあります: {route_key}")
                machine_supply_moves.add(move_id)
                deferred_digest.add({
                    "consumer": consumer,
                    **normalized,
                    "reason": "MACHINE_RUNTIME_SUPPLY_REQUIRED",
                })
            else:
                _fail(f"machine runtime supply status不正: {route_key}/{status!r}")
        else:
            deferred_digest.add({
                "consumer": consumer,
                "target_species_key": species_key,
                "target_species_id": species_id,
                "route_id": route_id,
                "project_move_id": move_id,
                "reason": "CONSUMER_NOT_IN_STAGE66_BULK_SCOPE",
            })

    if len(seen_route_keys) != 118528 or dict(consumer_counts) != EXPECTED_CONSUMER_COUNTS:
        _fail("Stage66 streaming全route集合/count不一致")
    if dict(move1063_counts) != EXPECTED_SIDE_CHANGE_COUNTS:
        _fail(f"Move1063 consumer count不一致: {dict(move1063_counts)}")
    compiled_consumer_gate: dict[str, Any] = {}
    for name in EXPECTED_CONSUMER_COUNTS:
        expected = consumers.get(name, {})
        actual_hash = consumer_digests[name].hexdigest()
        if expected.get("count") != consumer_counts[name] \
                or expected.get("content_sha256") != actual_hash:
            _fail(f"P03 {name} compiled content digest不一致")
        compiled_consumer_gate[name] = {
            "count": consumer_counts[name],
            "content_sha256": actual_hash,
            "matches_p03_contract": True,
        }

    level_count = sum(len(rows) for rows in level_work.values())
    machine_count = sum(len(rows) for rows in machine_work.values())
    scope = config["bulk_scope"]
    if (
        level_count != scope["level_up_runtime_ready_routes"]
        or len(level_deferred) != scope["level_up_move_1063_deferred_routes"]
        or machine_count != scope["machine_existing_slot_routes"]
        or consumer_counts["machine"] - machine_count
        != scope["machine_supply_required_routes"]
        or level_count + machine_count != scope["materialized_routes"]
        or len(level_work) != 1300
        or len(machine_projection_keys) != machine_count
    ):
        _fail("Stage66 materialized/deferred route count不一致")

    representatives = config["runtime_gate"]["representatives"]
    if [row["species_id"] for row in representatives[:3]] != [
        target_ids[0], target_ids[len(target_ids) // 2], target_ids[-1]
    ] or representatives[3].get("species_id") != 649:
        _fail("Stage66 representative first/middle/last/Caterpie選択不一致")
    samples: list[dict[str, Any]] = []
    for representative in representatives:
        species_id = int(representative["species_id"])
        target = targets_by_id[species_id]
        level_rows = level_work[species_id]
        machine_rows = machine_work.get(species_id, [])
        by_slot = {int(row["runtime_slot_zero_based"]): row for row in machine_rows}
        positive = int(representative["positive_machine_slot"])
        negative = int(representative["negative_machine_slot"])
        positive_row = by_slot.get(positive)
        if (
            target.get("species_key") != representative.get("species_key")
            or len(level_rows) != representative.get("level_count")
            or positive_row is None
            or positive_row.get("project_move_id")
            != representative.get("positive_machine_move")
            or negative in by_slot
        ):
            _fail(f"Stage66 representative contract不一致: {species_id}")
        samples.append({
            "role": representative["role"],
            "species_key": target["species_key"],
            "species_id": species_id,
            "reference_id": target["reference_id"],
            "level_rows": [
                {"project_move_id": row["project_move_id"], "level": row["learning_level"]}
                for row in level_rows
            ],
            "machine_set_slots": sorted(by_slot),
            "positive_machine_slot": positive,
            "positive_machine_move": positive_row["project_move_id"],
            "negative_machine_slot": negative,
        })

    non_scope_counts = {
        name: consumer_counts[name]
        for name in EXPECTED_CONSUMER_COUNTS
        if name not in {"level_up", "machine"}
    }
    route_audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT",
        "done": False,
        "checkpoint_marker": "CHECKPOINT_NOT_P03_DONE",
        "source_validation": {
            "corrected_target_count": len(target_records),
            "compiled_route_count": len(seen_route_keys),
            "ordering": index["ordering"],
            "all_nine_consumers_streamed_and_validated": True,
            "compiled_consumers": compiled_consumer_gate,
        },
        "materialization": {
            "adoption_policy": config["bulk_scope"]["adoption_policy"],
            "level_up": {
                "input_routes": consumer_counts["level_up"],
                "target_count": len(level_work),
                "runtime_ready_routes_materialized": level_count,
                "move_1063_routes_deferred": len(level_deferred),
                "deferred_route_content_sha256": _framed_digest(level_deferred),
                "deferred_routes": level_deferred,
            },
            "machine": {
                "input_routes": consumer_counts["machine"],
                "existing_slot_routes_materialized": machine_count,
                "unique_target_slot_bits": len(machine_projection_keys),
                "targets_with_set_bits": len(machine_work),
                "targets_with_zero_bits": len(target_records) - len(machine_work),
                "supply_required_routes_deferred": consumer_counts["machine"] - machine_count,
                "supply_required_distinct_moves": len(machine_supply_moves),
                "supply_required_move_ids_sha256": sha256(
                    stable_json(sorted(machine_supply_moves))
                ),
            },
            "materialized_routes": level_count + machine_count,
            "materialized_route_content_sha256": materialized_digest.hexdigest(),
            "deferred_routes": 118528 - level_count - machine_count,
            "deferred_route_content_sha256": deferred_digest.hexdigest(),
            "non_scope_consumer_routes": non_scope_counts,
            "move_1063_routes_by_consumer": dict(sorted(move1063_counts.items())),
            "move_1063_status": "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
        },
        "representatives": samples,
        "claims": {
            "all_level_up_input_routes_accounted": True,
            "all_runtime_ready_level_up_routes_materialized": True,
            "all_existing_slot_machine_routes_materialized": True,
            "move_1063_serialized": False,
            "supply_required_routes_dropped": False,
            "other_consumer_routes_dropped": False,
            "full_p03_implemented": False,
        },
    }
    return BulkRoutes(
        target_records,
        {key: tuple(value) for key, value in level_work.items()},
        {key: tuple(value) for key, value in machine_work.items()},
        route_audit,
    )


def _serialize_level_payload(
    routes: BulkRoutes,
    config: Mapping[str, Any],
) -> tuple[bytes, dict[int, int]]:
    payload = bytearray()
    offsets: dict[int, int] = {}
    row_alignment = int(config["allocation"]["row_start_alignment"])
    if row_alignment != 2:
        _fail("Stage66 level row start alignmentは2必須です")
    for target in routes.target_records:
        species_id = int(target["canonical_id"])
        while len(payload) % row_alignment:
            payload.append(0xFF)
        offsets[species_id] = len(payload)
        for row in routes.level_rows[species_id]:
            payload.extend(struct.pack(
                "<HB", int(row["project_move_id"]), int(row["learning_level"])
            ))
        payload.extend(b"\x00\x00\xFF")
    expected = config["allocation"]
    if len(payload) != int(expected["size"]) or sha256(payload) != expected["content_sha256"]:
        _fail(
            "Stage66 level payload size/hash不一致: "
            f"{len(payload)}/{sha256(payload)}"
        )
    return bytes(payload), offsets


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
            _fail(f"parent allocation overlap/range不正: {name}")
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
    parent: Mapping[str, Any], declaration: Mapping[str, Any], payload: bytes,
) -> dict[str, Any]:
    result = copy.deepcopy(parent)
    if result.get("schema_version") != 1:
        _fail("parent allocation schema不一致")
    start = hex_int(declaration.get("start"), "allocation.start")
    size = int(declaration.get("size", -1))
    alignment = int(declaration.get("alignment", -1))
    if size != len(payload) or alignment != 4 or start % alignment:
        _fail("Stage66 allocation size/alignment不一致")
    first_fit = _first_fit(result, str(declaration.get("region")), size, alignment)
    if start != first_fit:
        _fail(f"Stage66 allocationが決定的FIRST_FITではありません: 0x{first_fit:X}")
    sequence_values = [int(row.get("sequence", -1)) for row in result.get("allocations", [])]
    if sorted(sequence_values) != list(range(len(sequence_values))):
        _fail("parent allocation sequenceが0..N-1連続ではありません")
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
        "sequence": len(sequence_values),
        "size": size,
        "start": start,
    }
    if entry["placement"] != "FIRST_FIT" or entry["owner"] != TASK:
        _fail("Stage66 allocation owner/placement不一致")
    result["allocations"].append(entry)

    summaries = result.get("summaries")
    if not isinstance(summaries, dict):
        _fail("parent allocation summariesがありません")
    allocatable_bytes = 0
    allocated_bytes = 0
    region_usage = []
    for region in result["regions"]:
        rows = [row for row in result["allocations"] if row["region"] == region["name"]]
        used = sum(int(row["size"]) for row in rows)
        if region["kind"] == "allocatable":
            allocatable_bytes += int(region["size"])
            allocated_bytes += used
            remaining = int(region["size"]) - used
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
    summaries.update({
        "allocatable_bytes": allocatable_bytes,
        "allocatable_region_count": sum(
            row["kind"] == "allocatable" for row in result["regions"]
        ),
        "allocated_bytes": allocated_bytes,
        "allocation_count": len(result["allocations"]),
        "gba_rom_base": ROM_BASE,
        "overlap_count": 0,
        "region_bytes": sum(int(row["size"]) for row in result["regions"]),
        "region_count": len(result["regions"]),
        "region_usage": region_usage,
        "remaining_allocatable_bytes": allocatable_bytes - allocated_bytes,
        "reserved_bytes": sum(
            int(row["size"]) for row in result["regions"]
            if row["kind"] == "reserved"
        ),
        "reserved_region_count": sum(
            row["kind"] == "reserved" for row in result["regions"]
        ),
        "rom_size": ROM_SIZE,
    })
    return result


@dataclass(frozen=True)
class Stage66Image:
    config: dict[str, Any]
    rom: bytes
    allocation: dict[str, Any]
    route_audit: dict[str, Any]
    change_audit: dict[str, Any]
    input_audit: dict[str, Any]


def build_stage66_image(root: Path, config_path: Path) -> Stage66Image:
    """固定Stage65からbulk level/machine checkpointのexact bytesを返す。"""

    config = read_config(root, config_path)
    _validate_config(config)
    inputs = config["inputs"]
    parent = fixed_input(root, inputs["parent_rom"], "Stage65 parent ROM")
    metadata = _json(
        fixed_input(root, inputs["parent_metadata"], "Stage65 metadata"),
        "Stage65 metadata",
    )
    checkpoint = _json(
        fixed_input(root, inputs["parent_checkpoint"], "P03 Stage65 checkpoint"),
        "P03 Stage65 checkpoint",
    )
    parent_allocation = _json(
        fixed_input(root, inputs["parent_allocation"], "Stage65 allocation"),
        "Stage65 allocation",
    )
    contract = _json(
        fixed_input(root, inputs["p03_contract"], "P03 contract"), "P03 contract"
    )
    index = _json(
        fixed_input(root, inputs["p03_compiled_index"], "P03 compiled index"),
        "P03 compiled index",
    )
    handoff = _json(
        fixed_input(root, inputs["p03_runtime_handoff"], "P03 runtime handoff"),
        "P03 runtime handoff",
    )
    fixed_input(root, inputs["identity_contract"], "P01 identity contract")
    fixed_input(root, inputs["species_manifest"], "Species manifest")
    fixed_input(root, inputs["move_manifest"], "Move manifest")
    learnsets_zip = fixed_path(root, inputs["learnsets_zip"], "P03 immutable learnsets ZIP")
    _validate_parent(parent, metadata, checkpoint, config)
    routes = _compile_bulk_routes(
        root, learnsets_zip, contract, index, handoff, config
    )
    level_payload, relative_level_offsets = _serialize_level_payload(routes, config)

    tables = config["runtime_tables"]
    level = tables["level_up"]
    level_root_site = hex_int(level["root_pointer_site_rom_offset"], "level root site")
    literal_site = hex_int(level["runtime_literal_site_rom_offset"], "level literal site")
    level_root = _read_u32(parent, level_root_site, "level root")
    level_literal = _read_u32(parent, literal_site, "level runtime literal")
    expected_level_root = hex_int(
        level["expected_parent_root_runtime_address"], "expected level root"
    )
    if level_root != expected_level_root or level_literal != level_root:
        _fail("Stage65 level-up root producer/consumer pointer不一致")
    level_root_offset = _rom_offset(level_root, "level root")
    pointer_stride = int(level["pointer_stride"])
    if pointer_stride != 4 or level_root_offset + SPECIES_COUNT * 4 > len(parent):
        _fail("Stage65 level-up pointer table ABI/range不一致")

    machine = tables["machine"]
    compatibility_root_site = hex_int(
        machine["compatibility_root_site_rom_offset"], "TM compatibility root site"
    )
    compatibility_root = _read_u32(parent, compatibility_root_site, "TM compatibility root")
    if compatibility_root != hex_int(
        machine["expected_parent_compatibility_root_runtime_address"],
        "expected TM compatibility root",
    ):
        _fail("Stage65 TM compatibility root不一致")
    compatibility_root_offset = _rom_offset(compatibility_root, "TM compatibility root")
    compatibility_stride = int(machine["compatibility_stride"])
    if compatibility_stride != 16 \
            or compatibility_root_offset + SPECIES_COUNT * 16 > len(parent):
        _fail("Stage65 TM compatibility table ABI/range不一致")
    catalog_root_site = hex_int(machine["catalog_root_site_rom_offset"], "TM catalog root site")
    catalog_root = _read_u32(parent, catalog_root_site, "TM catalog root")
    if catalog_root != hex_int(
        machine["expected_catalog_root_runtime_address"], "expected TM catalog root"
    ):
        _fail("Stage65 TM catalog root不一致")
    catalog_root_offset = _rom_offset(catalog_root, "TM catalog root")
    slot_count = int(machine["catalog_slot_count"])
    if slot_count != 128 or catalog_root_offset + slot_count * 2 > len(parent):
        _fail("Stage65 TM catalog range/count不一致")
    catalog = tuple(
        struct.unpack_from("<H", parent, catalog_root_offset + slot * 2)[0]
        for slot in range(slot_count)
    )

    allocation_start = hex_int(config["allocation"]["start"], "allocation.start")
    allocation_end = allocation_start + len(level_payload)
    if parent[allocation_start:allocation_end] != b"\xFF" * len(level_payload):
        _fail("Stage66 level payload allocation preimageが全FFではありません")
    allocation = _updated_allocation(parent_allocation, config["allocation"], level_payload)

    target_ids = {int(row["canonical_id"]) for row in routes.target_records}
    pointer_preimage = FramedDigest()
    pointer_output = FramedDigest()
    compatibility_preimage = FramedDigest()
    compatibility_output = FramedDigest()
    pointer_entries: dict[int, tuple[int, int]] = {}
    compatibility_rows: dict[int, tuple[int, bytes]] = {}
    for target in routes.target_records:
        species_id = int(target["canonical_id"])
        pointer_offset = level_root_offset + species_id * pointer_stride
        parent_pointer = _read_u32(parent, pointer_offset, f"species {species_id} level pointer")
        _rom_offset(parent_pointer, f"species {species_id} parent level pointer")
        output_pointer = ROM_BASE + allocation_start + relative_level_offsets[species_id]
        if output_pointer % int(level["payload_row_start_alignment"]):
            _fail(f"species {species_id} Stage66 level pointer alignment不一致")
        pointer_entries[species_id] = (pointer_offset, output_pointer)
        pointer_preimage.add({
            "species_id": species_id,
            "entry_rom_offset": pointer_offset,
            "runtime_pointer": f"0x{parent_pointer:08X}",
        })
        pointer_output.add({
            "species_id": species_id,
            "entry_rom_offset": pointer_offset,
            "runtime_pointer": f"0x{output_pointer:08X}",
        })

        compatibility_offset = compatibility_root_offset + species_id * compatibility_stride
        parent_row = parent[compatibility_offset:compatibility_offset + compatibility_stride]
        replacement = bytearray(compatibility_stride)
        for row in routes.machine_rows.get(species_id, ()):
            slot = int(row["runtime_slot_zero_based"])
            move_id = int(row["project_move_id"])
            if catalog[slot] != move_id:
                _fail(
                    f"species {species_id} slot {slot} catalog Move不一致: "
                    f"{catalog[slot]} != {move_id}"
                )
            replacement[slot // 8] |= 1 << slot % 8
        replacement_bytes = bytes(replacement)
        if len(_set_bits(replacement_bytes)) != len(routes.machine_rows.get(species_id, ())):
            _fail(f"species {species_id} machine bit projection count不一致")
        compatibility_rows[species_id] = (compatibility_offset, replacement_bytes)
        compatibility_preimage.add({"species_id": species_id, "row_hex": parent_row.hex()})
        compatibility_output.add({"species_id": species_id, "row_hex": replacement_bytes.hex()})

    output = bytearray(parent)
    output[allocation_start:allocation_end] = level_payload
    for pointer_offset, output_pointer in pointer_entries.values():
        struct.pack_into("<I", output, pointer_offset, output_pointer)
    for compatibility_offset, replacement in compatibility_rows.values():
        output[compatibility_offset:compatibility_offset + compatibility_stride] = replacement
    result = bytes(output)
    if len(result) != ROM_SIZE:
        _fail("Stage66 ROM sizeが変わりました")
    if _read_u32(result, level_root_site, "output level root") != level_root \
            or _read_u32(result, literal_site, "output level literal") != level_root \
            or _read_u32(result, compatibility_root_site, "output TM root") != compatibility_root \
            or _read_u32(result, catalog_root_site, "output TM catalog") != catalog_root:
        _fail("Stage66が共有consumer rootを変更しました")

    changed_offsets = [
        offset
        for offset, (before, after) in enumerate(zip(parent, result, strict=True))
        if before != after
    ]

    def allowed_change(offset: int) -> bool:
        if allocation_start <= offset < allocation_end:
            return True
        if level_root_offset <= offset < level_root_offset + SPECIES_COUNT * pointer_stride:
            return ((offset - level_root_offset) // pointer_stride) in target_ids
        if (
            compatibility_root_offset
            <= offset
            < compatibility_root_offset + SPECIES_COUNT * compatibility_stride
        ):
            return ((offset - compatibility_root_offset) // compatibility_stride) in target_ids
        return False

    outside = [offset for offset in changed_offsets if not allowed_change(offset)]
    if outside:
        _fail(f"Stage66に宣言範囲外の変更があります: 0x{outside[0]:X}")
    if result[allocation_start:allocation_end] != level_payload:
        _fail("Stage66 level payload readback不一致")
    for species_id, (pointer_offset, output_pointer) in pointer_entries.items():
        if _read_u32(result, pointer_offset, f"species {species_id} output pointer") \
                != output_pointer:
            _fail(f"species {species_id} level pointer readback不一致")
    for species_id, (offset, replacement) in compatibility_rows.items():
        if result[offset:offset + compatibility_stride] != replacement:
            _fail(f"species {species_id} machine compatibility readback不一致")

    non_target_ids = sorted(set(range(SPECIES_COUNT)) - target_ids)
    non_target_before = bytearray()
    non_target_after = bytearray()
    for species_id in non_target_ids:
        pointer_offset = level_root_offset + species_id * pointer_stride
        compatibility_offset = compatibility_root_offset + species_id * compatibility_stride
        non_target_before.extend(parent[pointer_offset:pointer_offset + pointer_stride])
        non_target_before.extend(
            parent[compatibility_offset:compatibility_offset + compatibility_stride]
        )
        non_target_after.extend(result[pointer_offset:pointer_offset + pointer_stride])
        non_target_after.extend(
            result[compatibility_offset:compatibility_offset + compatibility_stride]
        )
    if non_target_before != non_target_after or len(non_target_ids) != 321:
        _fail("非採用Vega Speciesのlevel/machine rowsが保持されていません")

    sample_by_id = {
        row["species_id"]: row for row in routes.route_audit["representatives"]
    }
    sample_runtime: list[dict[str, Any]] = []
    for representative in config["runtime_gate"]["representatives"]:
        species_id = int(representative["species_id"])
        pointer_offset, output_pointer = pointer_entries[species_id]
        compatibility_offset, replacement = compatibility_rows[species_id]
        row = dict(sample_by_id[species_id])
        row.update({
            "level_pointer_entry_rom_offset": pointer_offset,
            "level_payload_runtime_pointer": f"0x{output_pointer:08X}",
            "level_payload_rom_offset": output_pointer - ROM_BASE,
            "compatibility_row_rom_offset": compatibility_offset,
            "machine_set_slots": _set_bits(replacement),
        })
        sample_runtime.append(row)

    spans = _changed_spans(parent, result)
    change_audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "roots": {
            "level_root_pointer_site_rom_offset": level_root_site,
            "level_runtime_literal_site_rom_offset": literal_site,
            "level_root_runtime_address": f"0x{level_root:08X}",
            "machine_compatibility_root_site_rom_offset": compatibility_root_site,
            "machine_compatibility_root_runtime_address": f"0x{compatibility_root:08X}",
            "machine_catalog_root_site_rom_offset": catalog_root_site,
            "machine_catalog_root_runtime_address": f"0x{catalog_root:08X}",
            "measured_from_exact_stage65_parent": True,
        },
        "preimage": {
            "parent_rom_sha256": sha256(parent),
            "target_level_pointer_entries": 1300,
            "target_level_pointer_entries_sha256": pointer_preimage.hexdigest(),
            "target_machine_compatibility_rows": 1300,
            "target_machine_compatibility_rows_sha256": compatibility_preimage.hexdigest(),
            "allocation_start": allocation_start,
            "allocation_size": len(level_payload),
            "allocation_expected_byte": "FF",
            "allocation_preimage_sha256": sha256(parent[allocation_start:allocation_end]),
            "allocation_all_ff": True,
            "machine_catalog_rows": slot_count,
            "machine_catalog_sha256": sha256(
                parent[catalog_root_offset:catalog_root_offset + slot_count * 2]
            ),
        },
        "output_tables": {
            "target_level_pointer_entries": 1300,
            "target_level_pointer_entries_sha256": pointer_output.hexdigest(),
            "level_payload_rom_offset": allocation_start,
            "level_payload_runtime_address": f"0x{ROM_BASE + allocation_start:08X}",
            "level_payload_size": len(level_payload),
            "level_payload_sha256": sha256(level_payload),
            "level_rows_serialized": config["bulk_scope"]["level_up_runtime_ready_routes"],
            "row_start_alignment": config["allocation"]["row_start_alignment"],
            "target_machine_compatibility_rows": 1300,
            "target_machine_compatibility_rows_sha256": compatibility_output.hexdigest(),
            "machine_bits_set": config["bulk_scope"]["machine_existing_slot_routes"],
        },
        "preservation": {
            "non_adopted_species_count": len(non_target_ids),
            "non_adopted_level_pointer_and_machine_rows_sha256": sha256(non_target_after),
            "non_adopted_rows_unchanged": True,
            "parent_level_payloads_destructively_overwritten": False,
            "replacement_policy_applies_only_to_corrected_targets": True,
            "rom_size_changed": False,
            "shared_roots_changed": False,
        },
        "representatives": sample_runtime,
        "changed_byte_count": len(changed_offsets),
        "changed_offsets_sha256": sha256(stable_json(changed_offsets)),
        "changed_span_count": len(spans),
        "changed_spans": spans,
        "outside_declared_range_count": 0,
        "allowed_domains": [
            "1300 corrected target level pointer entries",
            "1300 corrected target machine compatibility rows",
            "one FIRST_FIT bulk level payload allocation",
        ],
    }
    route_audit = copy.deepcopy(routes.route_audit)
    route_audit["serialization"] = {
        "level_payload_size": len(level_payload),
        "level_payload_sha256": sha256(level_payload),
        "level_row_start_alignment": config["allocation"]["row_start_alignment"],
        "machine_compatibility_stride": compatibility_stride,
        "representative_runtime_pointers": [
            {
                "role": row["role"],
                "species_id": row["species_id"],
                "runtime_pointer": row["level_payload_runtime_pointer"],
            }
            for row in sample_runtime
        ],
    }
    input_audit = {
        key: {"path": value["path"], "size": value["size"], "sha256": value["sha256"]}
        for key, value in inputs.items()
        if isinstance(value, dict) and {"path", "size", "sha256"} <= set(value)
        and key != "clean_rom"
    }
    return Stage66Image(
        config,
        result,
        allocation,
        route_audit,
        change_audit,
        input_audit,
    )
