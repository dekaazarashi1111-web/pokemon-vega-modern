"""P03 Stage65のキャタピー代表縦切りを実consumer表へ決定的に生成する。

このmoduleは全118,528経路の実装器ではない。P03契約で訂正採用された
SPECIES_KEY_CATERPIEの4経路だけを、Stage64上のlevel-up pointer tableと
TM/HM compatibility bitsetへ接続するcheckpoint generatorである。
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROM_BASE = 0x08000000
ROM_END = 0x0A000000
ROM_SIZE = 32 * 1024 * 1024
SPECIES_COUNT = 1621
TASK = "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
STAGE = 65

EXPECTED_LEVEL_ROUTES = (
    ("e84468471e2a5389cab08c6e", "MOVE_KEY_TACKLE", 33, 1),
    ("bcf11b7de237f5503621f3b4", "MOVE_KEY_STRINGSHOT", 81, 1),
    ("9d24844ef808e40888791e37", "MOVE_KEY_BUGBITE", 535, 9),
)
EXPECTED_MACHINE_ROUTE = (
    "f47d1fe9a44cbb635c1de248",
    "MOVE_KEY_ELECTROWEB",
    489,
    "TM82",
    116,
)
EXPECTED_REFERENCE_RECORD_SHA256 = (
    "af76db5dc3ba8ea36dd72de8271f9318261471ea1d2ad746c28acc3f35694e79"
)


class ModernizationP03Stage65Error(ValueError):
    """P03契約、ROM preimage、identity、allocationのfail-closed違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage65Error(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


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
        _fail(f"Stage65 configが通常ファイルではありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"Stage65 configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("Stage65 config rootがobjectではありません")
    return value


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


def _manifest(raw: bytes, key_field: str, label: str) -> dict[str, dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        rows = list(reader)
    except UnicodeDecodeError as error:
        _fail(f"{label}がUTF-8 CSVではありません: {error}")
    if reader.fieldnames is None or key_field not in reader.fieldnames or "id" not in reader.fieldnames:
        _fail(f"{label} headerが不正です")
    by_key: dict[str, dict[str, str]] = {}
    ids: set[int] = set()
    for row in rows:
        key = row.get(key_field, "")
        try:
            entity_id = int(row.get("id", ""))
        except ValueError:
            _fail(f"{label} IDが10進数ではありません: {row.get('id')!r}")
        if not key or key in by_key or entity_id in ids:
            _fail(f"{label} key/ID重複または欠落: {key!r}/{entity_id}")
        by_key[key] = row
        ids.add(entity_id)
    if ids != set(range(len(rows))):
        _fail(f"{label} ID空間が0..N-1連続ではありません")
    return by_key


def _validate_config(config: Mapping[str, Any]) -> None:
    if (config.get("schema_version"), config.get("task"), config.get("stage")) != (
        1,
        TASK,
        STAGE,
    ):
        _fail("Stage65 config schema/task/stage不一致")
    acceptance = config.get("acceptance", {})
    if (
        acceptance.get("static_contract_gate") != "REQUIRED"
        or acceptance.get("real_consumer_mgba_gate") != "REQUIRED"
        or acceptance.get("independent_processes") != 2
        or acceptance.get("incremental_bps_round_trip") != "REQUIRED"
        or acceptance.get("clean_bps_round_trip") != "REQUIRED"
        or acceptance.get("task_completion") != "CHECKPOINT_NOT_P03_DONE"
    ):
        _fail("Stage65 acceptanceがcheckpoint境界を固定していません")


def _validate_parent(
    parent: bytes,
    metadata: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    expected_path = config["inputs"]["parent_rom"]["path"]
    if len(parent) != ROM_SIZE:
        _fail(f"Stage64 parent ROM size不一致: {len(parent)}")
    if (
        metadata.get("schema_version") != 1
        or metadata.get("stage") != 64
        or metadata.get("status") != "CHECKPOINT"
        or metadata.get("done") is not False
        or metadata.get("output", {}).get("path") != expected_path
        or metadata.get("output", {}).get("sha256") != sha256(parent)
    ):
        _fail("Stage64 metadataがexact checkpoint parentを保証していません")
    acceptance = metadata.get("acceptance", {})
    for gate in (
        "static_patch_gate",
        "incremental_bps_round_trip",
        "clean_bps_round_trip",
        "mgba_runtime_gate",
    ):
        if acceptance.get(gate) != "PASS":
            _fail(f"Stage64 parent gate未達: {gate}")
    if acceptance.get("task_completion") != "CHECKPOINT_NOT_DONE":
        _fail("Stage64 parentのcheckpoint境界が不正です")
    if (
        checkpoint.get("stage") != 64
        or checkpoint.get("status") != "CHECKPOINT"
        or checkpoint.get("done") is not False
        or checkpoint.get("output", {}).get("sha256") != sha256(parent)
    ):
        _fail("P02 Stage64 checkpointとparent ROMが一致しません")


def _route_projection(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("route_id"),
        row.get("consumer"),
        row.get("method"),
        int(row.get("project_move_id", -1)),
        row.get("source_machine_item", ""),
        row.get("runtime_slot_zero_based"),
    )


def _validate_p03_contracts(
    contract: Mapping[str, Any],
    index: Mapping[str, Any],
    handoff: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        contract.get("schema_version") != 1
        or contract.get("task") != "USER-MODERNIZATION-P03"
        or contract.get("status") != "PASS"
    ):
        _fail("P03 learnset contractがPASS schema 1ではありません")
    corrected = contract.get("corrected_adoption", {})
    if corrected.get("records") != 1300 or corrected.get("routes") != 118528:
        _fail("P03 corrected adoption全体件数が固定値と一致しません")
    if contract.get("policy", {}).get("adoption") != config["target"]["adoption_policy"]:
        _fail("P03 adoption policy不一致")
    correction = contract.get("correction", {})
    caterpie = correction.get("caterpie", {})
    if (
        caterpie.get("species_key") != "SPECIES_KEY_CATERPIE"
        or caterpie.get("canonical_id") != 649
        or caterpie.get("reference_id") != "swordshield:0010.00"
        or caterpie.get("route_count") != 4
    ):
        _fail("P03 Caterpie訂正identity不一致")
    egg = correction.get("egg", {})
    if egg.get("species_key") != "SPECIES_KEY_EGG" or egg.get("canonical_id") != 412 \
            or egg.get("apply") is not False:
        _fail("P03内部Egg除外境界が失われています")

    configured_routes = config["target"]["level_up_routes"]
    configured_machine = config["target"]["machine_route"]
    expected_contract = {
        (route_id, "level_up", "level_up", move_id, "", None)
        for route_id, _move_key, move_id, _level in EXPECTED_LEVEL_ROUTES
    }
    expected_contract.add(
        (
            EXPECTED_MACHINE_ROUTE[0],
            "machine",
            "tm",
            EXPECTED_MACHINE_ROUTE[2],
            EXPECTED_MACHINE_ROUTE[3],
            EXPECTED_MACHINE_ROUTE[4],
        )
    )
    actual_contract = {_route_projection(row) for row in caterpie.get("compiled_routes", [])}
    if actual_contract != expected_contract:
        _fail("P03 Caterpie route集合が4経路の固定契約と一致しません")
    configured_projection = {
        (
            row.get("route_id"), row.get("consumer"), row.get("method"),
            int(row.get("project_move_id", -1)), "", None,
        )
        for row in configured_routes
    }
    configured_projection.add(_route_projection(configured_machine))
    if configured_projection != expected_contract:
        _fail("Stage65 configがP03 Caterpie route集合を変更しています")

    if (
        index.get("schema_version") != 1
        or index.get("task") != "USER-MODERNIZATION-P03"
        or index.get("status") != "PASS"
        or index.get("record_count") != 1300
        or index.get("route_count") != 118528
        or index.get("materialization")
        != "COMPACT_HASH_INDEX_ONLY; full routes remain solely in immutable source ZIP"
    ):
        _fail("P03 compiled indexの全体境界が不正です")
    indexed = [
        row for row in index.get("records", [])
        if row.get("species_key") == "SPECIES_KEY_CATERPIE"
    ]
    if len(indexed) != 1:
        _fail("P03 compiled indexのCaterpie recordが一意ではありません")
    indexed_row = indexed[0]
    if (
        indexed_row.get("canonical_id") != 649
        or indexed_row.get("origin") != "ADD_CATERPIE_FROM_REFERENCE"
        or indexed_row.get("route_count") != 4
        or indexed_row.get("consumer_counts") != {"level_up": 3, "machine": 1}
        or indexed_row.get("reference_content_sha256") != EXPECTED_REFERENCE_RECORD_SHA256
    ):
        _fail("P03 compiled indexのCaterpie内容hash/count不一致")

    abi = handoff.get("connection_points", {}).get("current_abi", {})
    if (
        handoff.get("schema_version") != 1
        or handoff.get("status") != "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS"
        or abi.get("level_up", {}).get("row") != "U16_PROJECT_MOVE_ID + U8_LEVEL"
        or abi.get("level_up", {}).get("terminator") != "0000FF"
        or abi.get("machine_compatibility", {}).get("stride") != 16
        or abi.get("machine_compatibility", {}).get("tm_slots") != 120
        or handoff.get("side_change_1063", {}).get("status")
        != "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED"
    ):
        _fail("P03 runtime handoff ABIまたは未完了境界が不正です")
    return {
        "status": "PASS",
        "corrected_records": 1300,
        "corrected_routes": 118528,
        "caterpie_routes_selected": 4,
        "caterpie_reference_content_sha256": EXPECTED_REFERENCE_RECORD_SHA256,
        "adoption_policy": config["target"]["adoption_policy"],
        "move_1063_status": "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
    }


def _validate_target_and_manifests(
    config: Mapping[str, Any],
    species: Mapping[str, Mapping[str, str]],
    moves: Mapping[str, Mapping[str, str]],
) -> tuple[bytes, bytes]:
    target = config["target"]
    if (
        target.get("species_key") != "SPECIES_KEY_CATERPIE"
        or target.get("species_id") != 649
        or target.get("reference_id") != "swordshield:0010.00"
    ):
        _fail("Stage65 targetがstable Caterpie ID649ではありません")
    species_row = species.get("SPECIES_KEY_CATERPIE")
    if species_row is None or int(species_row["id"]) != 649 or species_row.get("form_key"):
        _fail("Species manifestのCaterpie normal-form identity不一致")

    actual_level = tuple(
        (
            row.get("route_id"), row.get("move_key"),
            int(row.get("project_move_id", -1)), int(row.get("learning_level", -1)),
        )
        for row in target.get("level_up_routes", [])
    )
    if actual_level != EXPECTED_LEVEL_ROUTES:
        _fail("Caterpie level-up経路が採用済み1/1/9の3行ではありません")
    machine = target.get("machine_route", {})
    actual_machine = (
        machine.get("route_id"), machine.get("move_key"),
        int(machine.get("project_move_id", -1)), machine.get("source_machine_item"),
        int(machine.get("runtime_slot_zero_based", -1)),
    )
    if actual_machine != EXPECTED_MACHINE_ROUTE:
        _fail("Caterpie TM82→Move489/runtime slot116契約不一致")
    for _route_id, key, move_id, _level in EXPECTED_LEVEL_ROUTES:
        row = moves.get(key)
        if row is None or int(row["id"]) != move_id:
            _fail(f"Move manifest key/ID不一致: {key}/{move_id}")
    machine_row = moves.get(EXPECTED_MACHINE_ROUTE[1])
    if machine_row is None or int(machine_row["id"]) != EXPECTED_MACHINE_ROUTE[2]:
        _fail("Move manifestのElectroweb ID489不一致")

    level_payload = b"".join(
        struct.pack("<HB", move_id, level)
        for _route_id, _key, move_id, level in EXPECTED_LEVEL_ROUTES
    ) + b"\x00\x00\xFF"
    compatibility = bytearray(16)
    compatibility[EXPECTED_MACHINE_ROUTE[4] // 8] = 1 << (EXPECTED_MACHINE_ROUTE[4] % 8)
    return level_payload, bytes(compatibility)


def _rom_offset(address: int, label: str) -> int:
    if not (ROM_BASE <= address < ROM_END):
        _fail(f"{label}が32MiB ROM runtime範囲外です: 0x{address:08X}")
    return address - ROM_BASE


def _read_u32(raw: bytes, offset: int, label: str) -> int:
    if not (0 <= offset <= len(raw) - 4):
        _fail(f"{label} offsetがROM範囲外です: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _set_bits(row: bytes) -> list[int]:
    return [index for index in range(len(row) * 8) if row[index // 8] & (1 << (index % 8))]


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


def _first_fit(allocation: Mapping[str, Any], region_name: str, size: int, alignment: int) -> int:
    regions = [row for row in allocation.get("regions", []) if row.get("name") == region_name]
    if len(regions) != 1 or regions[0].get("kind") != "allocatable":
        _fail(f"allocatable regionが一意ではありません: {region_name}")
    region = regions[0]
    cursor = int(region["start"])
    intervals = sorted(
        (int(row["start"]), int(row["end_exclusive"]), str(row["name"]))
        for row in allocation.get("allocations", []) if row.get("region") == region_name
    )
    previous_end = int(region["start"])
    for start, end, name in intervals:
        if start < previous_end or end <= start or end > int(region["end_exclusive"]):
            _fail(f"parent allocation overlap/range不正: {name}")
        previous_end = end
        candidate = (cursor + alignment - 1) // alignment * alignment
        if candidate + size <= start:
            return candidate
        cursor = max(cursor, end)
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
        _fail("Stage65 allocation size/alignment不一致")
    first_fit = _first_fit(result, str(declaration.get("region")), size, alignment)
    if start != first_fit:
        _fail(f"Stage65 allocationが決定的FIRST_FITではありません: 0x{first_fit:X}")
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
        _fail("Stage65 allocation owner/placement不一致")
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
            int(row["size"]) for row in result["regions"] if row["kind"] == "reserved"
        ),
        "reserved_region_count": sum(
            row["kind"] == "reserved" for row in result["regions"]
        ),
        "rom_size": ROM_SIZE,
    })
    return result


@dataclass(frozen=True)
class Stage65Image:
    config: dict[str, Any]
    rom: bytes
    allocation: dict[str, Any]
    audit: dict[str, Any]
    input_audit: dict[str, Any]
    contract_audit: dict[str, Any]


def build_stage65_image(root: Path, config_path: Path) -> Stage65Image:
    """固定Stage64から代表4経路だけを反映したexact Stage65 bytesを返す。"""

    config = read_config(root, config_path)
    _validate_config(config)
    inputs = config["inputs"]
    parent = fixed_input(root, inputs["parent_rom"], "Stage64 parent ROM")
    metadata_raw = fixed_input(root, inputs["parent_metadata"], "Stage64 metadata")
    checkpoint_raw = fixed_input(root, inputs["parent_checkpoint"], "P02 checkpoint")
    allocation_raw = fixed_input(root, inputs["parent_allocation"], "parent allocation")
    contract_raw = fixed_input(root, inputs["p03_contract"], "P03 contract")
    index_raw = fixed_input(root, inputs["p03_compiled_index"], "P03 compiled index")
    handoff_raw = fixed_input(root, inputs["p03_runtime_handoff"], "P03 runtime handoff")
    species_raw = fixed_input(root, inputs["species_manifest"], "Species manifest")
    moves_raw = fixed_input(root, inputs["move_manifest"], "Move manifest")

    metadata = _json(metadata_raw, "Stage64 metadata")
    checkpoint = _json(checkpoint_raw, "P02 checkpoint")
    parent_allocation = _json(allocation_raw, "parent allocation")
    contract = _json(contract_raw, "P03 contract")
    index = _json(index_raw, "P03 compiled index")
    handoff = _json(handoff_raw, "P03 runtime handoff")
    _validate_parent(parent, metadata, checkpoint, config)
    contract_audit = _validate_p03_contracts(contract, index, handoff, config)
    species = _manifest(species_raw, "species_key", "Species manifest")
    moves = _manifest(moves_raw, "move_key", "Move manifest")
    level_payload, compatibility_target = _validate_target_and_manifests(
        config, species, moves
    )

    tables = config["runtime_tables"]
    level = tables["level_up"]
    level_root_site = hex_int(level["root_pointer_site_rom_offset"], "level root site")
    literal_site = hex_int(level["runtime_literal_site_rom_offset"], "level literal site")
    level_root = _read_u32(parent, level_root_site, "level root")
    literal_root = _read_u32(parent, literal_site, "level runtime literal")
    expected_level_root = hex_int(
        level["expected_parent_root_runtime_address"], "expected level root"
    )
    if level_root != expected_level_root or literal_root != level_root:
        _fail("Stage64 level-up root producer/consumer pointer不一致")
    level_root_offset = _rom_offset(level_root, "level root")
    pointer_stride = int(level["pointer_stride"])
    pointer_offset = level_root_offset + config["target"]["species_id"] * pointer_stride
    parent_species_pointer = _read_u32(parent, pointer_offset, "Caterpie level pointer")
    if parent_species_pointer != hex_int(
        level["expected_parent_species_pointer"], "expected Caterpie pointer"
    ):
        _fail("Stage64 Caterpie level pointer preimage不一致")
    parent_row_offset = _rom_offset(parent_species_pointer, "Caterpie parent rows")
    parent_rows = bytes.fromhex(level["expected_parent_rows_hex"])
    if parent[parent_row_offset:parent_row_offset + len(parent_rows)] != parent_rows:
        _fail("Stage64 Caterpie level rows preimage不一致")
    if bytes.fromhex(level["replacement_rows_hex"]) != level_payload:
        _fail("Stage65 level row serializerとconfig replacement不一致")

    allocation_start = hex_int(config["allocation"]["start"], "allocation.start")
    if parent[allocation_start:allocation_start + len(level_payload)] != b"\xFF" * len(level_payload):
        _fail("Stage65 level payload allocation preimageが全FFではありません")
    allocation = _updated_allocation(parent_allocation, config["allocation"], level_payload)
    new_level_pointer = ROM_BASE + allocation_start

    machine = tables["machine"]
    compatibility_root_site = hex_int(
        machine["compatibility_root_site_rom_offset"], "TM compatibility root site"
    )
    compatibility_root = _read_u32(parent, compatibility_root_site, "TM compatibility root")
    if compatibility_root != hex_int(
        machine["expected_parent_compatibility_root_runtime_address"],
        "expected TM compatibility root",
    ):
        _fail("Stage64 TM compatibility root不一致")
    compatibility_stride = int(machine["compatibility_stride"])
    compatibility_offset = (
        _rom_offset(compatibility_root, "TM compatibility root")
        + config["target"]["species_id"] * compatibility_stride
    )
    compatibility_parent = bytes.fromhex(machine["expected_parent_compatibility_row_hex"])
    if len(compatibility_parent) != compatibility_stride \
            or parent[compatibility_offset:compatibility_offset + compatibility_stride] != compatibility_parent:
        _fail("Stage64 Caterpie TM compatibility preimage不一致")
    if bytes.fromhex(machine["replacement_compatibility_row_hex"]) != compatibility_target:
        _fail("Stage65 TM compatibility serializerとconfig replacement不一致")
    if _set_bits(compatibility_parent) != [44, 63] or _set_bits(compatibility_target) != [116]:
        _fail("Caterpie TM compatibility replacementがREPLACE policy外です")

    catalog_root_site = hex_int(machine["catalog_root_site_rom_offset"], "TM catalog root site")
    catalog_root = _read_u32(parent, catalog_root_site, "TM catalog root")
    if catalog_root != hex_int(machine["expected_catalog_root_runtime_address"], "expected catalog root"):
        _fail("Stage64 TM catalog root不一致")
    slot = config["target"]["machine_route"]["runtime_slot_zero_based"]
    if not (0 <= slot < int(machine["catalog_slot_count"])):
        _fail("TM runtime slotがcatalog範囲外です")
    catalog_offset = _rom_offset(catalog_root, "TM catalog root") + slot * 2
    catalog_move = struct.unpack_from("<H", parent, catalog_offset)[0]
    if catalog_move != config["target"]["machine_route"]["project_move_id"]:
        _fail("TM runtime slot116がproject Move489を供給していません")

    output = bytearray(parent)
    output[allocation_start:allocation_start + len(level_payload)] = level_payload
    struct.pack_into("<I", output, pointer_offset, new_level_pointer)
    output[compatibility_offset:compatibility_offset + compatibility_stride] = compatibility_target
    result = bytes(output)
    if len(result) != ROM_SIZE:
        _fail("Stage65 ROM sizeが変わりました")
    if _read_u32(result, level_root_site, "output level root") != level_root \
            or _read_u32(result, literal_site, "output level literal") != level_root:
        _fail("Stage65が共有level rootを変更しました")
    if _read_u32(result, pointer_offset, "output Caterpie pointer") != new_level_pointer:
        _fail("Stage65 Caterpie pointer patch不一致")
    if result[allocation_start:allocation_start + len(level_payload)] != level_payload:
        _fail("Stage65 Caterpie level payload readback不一致")
    if result[compatibility_offset:compatibility_offset + compatibility_stride] != compatibility_target:
        _fail("Stage65 Caterpie TM compatibility readback不一致")

    spans = _changed_spans(parent, result)
    allowed_ranges = (
        range(pointer_offset, pointer_offset + 4),
        range(compatibility_offset, compatibility_offset + compatibility_stride),
        range(allocation_start, allocation_start + len(level_payload)),
    )
    changed_offsets = [
        offset for offset, (before, after) in enumerate(zip(parent, result, strict=True))
        if before != after
    ]
    if any(not any(offset in area for area in allowed_ranges) for offset in changed_offsets):
        _fail("Stage65に宣言範囲外の変更があります")

    audit = {
        "species_key": "SPECIES_KEY_CATERPIE",
        "species_id": 649,
        "reference_id": "swordshield:0010.00",
        "adoption_policy": config["target"]["adoption_policy"],
        "level_up": {
            "root_pointer_site_rom_offset": level_root_site,
            "runtime_literal_site_rom_offset": literal_site,
            "root_runtime_address": f"0x{level_root:08X}",
            "species_pointer_entry_rom_offset": pointer_offset,
            "parent_species_pointer": f"0x{parent_species_pointer:08X}",
            "stage65_species_pointer": f"0x{new_level_pointer:08X}",
            "payload_rom_offset": allocation_start,
            "parent_rows": [
                {"project_move_id": 33, "level": 1},
                {"project_move_id": 81, "level": 1},
                {"project_move_id": 535, "level": 9},
                {"project_move_id": 562, "level": 26},
            ],
            "stage65_rows": [
                {"project_move_id": move_id, "level": learning_level}
                for _route_id, _key, move_id, learning_level in EXPECTED_LEVEL_ROUTES
            ],
            "terminator_hex": "0000ff",
            "replacement_not_union": True,
        },
        "machine": {
            "compatibility_root_site_rom_offset": compatibility_root_site,
            "compatibility_root_runtime_address": f"0x{compatibility_root:08X}",
            "compatibility_row_rom_offset": compatibility_offset,
            "parent_set_slots": _set_bits(compatibility_parent),
            "stage65_set_slots": _set_bits(compatibility_target),
            "catalog_root_site_rom_offset": catalog_root_site,
            "catalog_root_runtime_address": f"0x{catalog_root:08X}",
            "source_machine_item": "TM82",
            "runtime_slot_zero_based": 116,
            "catalog_project_move_id": catalog_move,
            "replacement_not_union": True,
        },
        "allocation": allocation["allocations"][-1],
        "changed_byte_count": len(changed_offsets),
        "changed_span_count": len(spans),
        "changed_spans": spans,
        "outside_declared_range_count": 0,
        "rom_size_changed": False,
    }
    input_audit = {
        key: {"path": value["path"], "size": value["size"], "sha256": value["sha256"]}
        for key, value in inputs.items()
        if isinstance(value, dict) and {"path", "size", "sha256"} <= set(value)
        and key != "clean_rom"
    }
    return Stage65Image(config, result, allocation, audit, input_audit, contract_audit)
