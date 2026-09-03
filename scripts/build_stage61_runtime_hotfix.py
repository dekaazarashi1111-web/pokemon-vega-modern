#!/usr/bin/env python3
"""Stage61のTM/HM・教え技runtime接続とfield item復帰を修復する。"""

from __future__ import annotations

import argparse
import binascii
import csv
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _sparse_bps  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402

TASK = "USER-20260903-STAGE61-RUNTIME-HOTFIX"
CONFIG = Path("config/stage61_runtime_hotfix.json")
GBA_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
HEADER_SIZE = 0x100
ALLOCATION_NAME = "stage61_runtime_hotfix_payload"


class BuildError(RuntimeError):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _number(value: Any, label: str) -> int:
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as error:
        raise BuildError(f"{label}: 整数ではありません") from error


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    raw = path.read_bytes()
    expected_size = int(contract.get("size", len(raw)))
    if len(raw) != expected_size or _sha(raw) != str(contract["sha256"]):
        raise BuildError(f"{label} identity differs")
    return raw


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        raise BuildError(f"ROM address outside range: 0x{address:08X}")
    return offset


def _pointer(raw: bytes, site: int, expected: int, label: str) -> int:
    actual = struct.unpack_from("<I", raw, _rom_offset(site, 4))[0]
    if actual != expected:
        raise BuildError(
            f"{label} pointer differs: 0x{actual:08X} != 0x{expected:08X}")
    _rom_offset(actual)
    return actual


def _catalogs(config: Mapping[str, Any], archive_raw: bytes, catalog_raw: bytes) \
        -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    inputs = config["inputs"]
    manifest_rows = _read_csv(ROOT / str(inputs["move_manifest"]["path"]))
    by_key: dict[str, list[int]] = {}
    for row in manifest_rows:
        key = row["move_key"].strip()
        by_key.setdefault(key, []).append(int(row["id"]))
    archive_contract = inputs["move_distribution_v4_zip"]
    with zipfile.ZipFile(io.BytesIO(archive_raw)) as archive:
        def member(suffix: str, label: str) -> bytes:
            matches = [name for name in archive.namelist()
                       if name == suffix or name.endswith("/" + suffix)]
            if len(matches) != 1:
                raise BuildError(f"V4 {label} entry differs: {matches}")
            return archive.read(matches[0])

        changes_raw = member(str(archive_contract["changes_entry"]), "changes")
    if _sha(changes_raw) != str(archive_contract["changes_sha256"]):
        raise BuildError("V4 TM/tutor changes identity differs")
    master = list(csv.DictReader(io.StringIO(catalog_raw.decode("utf-8-sig"))))
    changes = list(csv.DictReader(io.StringIO(changes_raw.decode("utf-8-sig"))))
    if len(changes) != int(archive_contract["changes_count"]):
        raise BuildError("V4 TM/tutor changes count differs")

    def compile_rows(kind: str, count: int) -> list[dict[str, Any]]:
        source = [row for row in master if row["slot_type"].strip() == kind]
        if sorted(int(row["slot_no"]) for row in source) != list(range(1, count + 1)):
            raise BuildError(f"{kind} slot is not exactly 1..{count}")
        result: list[dict[str, Any]] = []
        for row in sorted(source, key=lambda value: int(value["slot_no"])):
            key = row["move_key"].strip()
            name = row["move_name"].strip()
            matches = by_key.get(key, [])
            if len(matches) != 1 or not 0 < matches[0] < 1063:
                raise BuildError(
                    f"{kind}{row['slot_no']} move_key resolution differs: {key}")
            manifest_name = next(
                value["display_name"].strip() for value in manifest_rows
                if value["move_key"].strip() == key)
            if manifest_name != name:
                raise BuildError(
                    f"{kind}{row['slot_no']} move name differs: {name} != {manifest_name}")
            result.append({
                "slot": int(row["slot_no"]), "move_id": matches[0],
                "move_key": key, "move_name": name, "source": row["source"],
            })
        return result

    tm = compile_rows("TM", 120)
    tutor = compile_rows("TUTOR", 64)
    move_by_slot = {
        ("TM", row["slot"]): row["move_key"] for row in tm
    } | {
        ("TUTOR", row["slot"]): row["move_key"] for row in tutor
    }
    seen: set[tuple[str, str, int]] = set()
    for row in changes:
        kind = row["slot_type"]
        slot = int(row["slot_no"])
        key = (row["species_key"], kind, slot)
        if (kind, slot) not in move_by_slot \
                or row["move_key"] != move_by_slot[(kind, slot)] \
                or row["compatible"] != "true" or row["status"] != "FINAL" \
                or key in seen:
            raise BuildError(f"V4 TM/tutor change differs: {row['change_key']}")
        seen.add(key)
    return tm, tutor, changes


def _previous_requests(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    if int(report["summaries"]["overlap_count"]):
        raise BuildError("input allocation has overlaps")
    keys = ("name", "region", "size", "alignment", "owner", "purpose",
            "content_sha256")
    return [{key: row[key] for key in keys} for row in report["allocations"]]


def _allocate(previous: Mapping[str, Any], payload: bytes) \
        -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": len(payload),
        "alignment": 16,
        "owner": TASK,
        "purpose": "TM120+HM8・教え技64の実行時tableと互換bitset",
        "content_sha256": _sha(payload),
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1 or int(report["summaries"]["overlap_count"]):
        raise BuildError("output allocation is invalid")
    return rows[0], report


def _align(value: int, alignment: int = 16) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _payload(tm_moves: list[int], tutor_moves: list[int], compatibility: bytes) \
        -> tuple[bytes, dict[str, int]]:
    tm_offset = HEADER_SIZE
    tutor_offset = _align(tm_offset + len(tm_moves) * 2)
    compatibility_offset = _align(tutor_offset + len(tutor_moves) * 2)
    total = _align(compatibility_offset + len(compatibility))
    raw = bytearray(b"\xFF" * total)
    for index, move in enumerate(tm_moves):
        struct.pack_into("<H", raw, tm_offset + index * 2, move)
    for index, move in enumerate(tutor_moves):
        struct.pack_into("<H", raw, tutor_offset + index * 2, move)
    raw[compatibility_offset:compatibility_offset + len(compatibility)] = compatibility
    struct.pack_into(
        "<8s11I", raw, 0, b"VEGA61HF", 1, HEADER_SIZE, total,
        tm_offset, len(tm_moves), tutor_offset, len(tutor_moves),
        compatibility_offset, 1621, 16, 0,
    )
    return bytes(raw), {
        "tmhm_offset": tm_offset,
        "tutor_offset": tutor_offset,
        "compatibility_offset": compatibility_offset,
        "size": total,
    }


def _jump_stub(target: int, register: int, address: int) -> bytes:
    if not 0 <= register <= 7:
        raise BuildError("hook register outside r0..r7")
    if address & 2:
        return (struct.pack("<HHH", 0x4801 | (register << 8),
                            0x4700 | (register << 3), 0)
                + struct.pack("<I", target | 1))
    return struct.pack(
        "<HHI", 0x4800 | (register << 8),
        0x4700 | (register << 3), target | 1)


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    index = 0
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        while index < len(before) and before[index] != after[index]:
            index += 1
        rows.append({"start": start, "end_exclusive": index, "size": index - start})
    return rows


def _build_artifacts(config_path: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    config_raw = (ROOT / config_path).read_bytes()
    config = json.loads(config_raw)
    inputs = config["inputs"]
    outputs = config["outputs"]
    contract = config["rom_contract"]
    stage = _identity(inputs["stage61_rom"], "Stage61 ROM")
    metadata_raw = _identity(inputs["stage61_metadata"], "Stage61 metadata")
    previous = json.loads(_identity(inputs["stage61_allocation"], "Stage61 allocation"))
    stage38 = _identity(inputs["stage38_rom"], "Stage38 ROM")
    clean = _identity(inputs["clean_rom"], "clean ROM")
    _identity(inputs["move_manifest"], "move manifest")
    _identity(inputs["species_manifest"], "species manifest")
    v4_archive = _identity(inputs["move_distribution_v4_zip"], "Move Distribution V4 ZIP")
    v4_catalog = _identity(inputs["v4_tm_tutor_catalog"], "V4 TM/tutor catalog")
    if len(stage) != ROM_SIZE or len(stage38) != ROM_SIZE or len(clean) * 2 != ROM_SIZE:
        raise BuildError("ROM size contract differs")
    old_metadata = json.loads(metadata_raw)
    if old_metadata.get("output", {}).get("sha256") != _sha(stage):
        raise BuildError("Stage61 metadata does not own input ROM")

    tm_catalog, tutor_catalog, v4_changes = _catalogs(config, v4_archive, v4_catalog)
    tm_moves = [row["move_id"] for row in tm_catalog]
    tutor_moves = [row["move_id"] for row in tutor_catalog]

    tm_root = _pointer(
        stage, _number(contract["tmhm_moves_root_site"], "TM move root site"),
        _number(contract["tmhm_moves_root_expected"], "TM move root expected"),
        "gTMHMMoves")
    old_tm_offset = _rom_offset(tm_root, 58 * 2)
    old_tm = list(struct.unpack_from("<58H", stage, old_tm_offset))
    if old_tm[:50] != tm_moves[:50]:
        raise BuildError("existing TM01..50 differs from V4 master")
    hm_moves = old_tm[50:58]
    if hm_moves != [15, 19, 57, 70, 148, 249, 127, 291]:
        raise BuildError(f"existing HM catalog differs: {hm_moves}")
    combined_moves = tm_moves + hm_moves

    tutor_root = _pointer(
        stage, _number(contract["tutor_moves_root_site"], "tutor move root site"),
        _number(contract["tutor_moves_root_expected"], "tutor move root expected"),
        "gTutorMoves")
    old_tutor_offset = _rom_offset(tutor_root, 32)
    old_tutor = list(struct.unpack_from("<16H", stage, old_tutor_offset))
    expected_old_tutor = [499, 465, 156, 436, 470, 322, 237, 487,
                          433, 92, 56, 91, 387, 475, 459]
    if old_tutor[:15] != expected_old_tutor or old_tutor[15] != 0:
        raise BuildError("existing legacy tutor 1..15/terminator differs")

    stage61_compat_root = _pointer(
        stage, _number(contract["stage61_tmhm_root_site"], "Stage61 TM compat site"),
        _number(contract["stage61_tmhm_root_expected"], "Stage61 TM compat expected"),
        "Stage61 TM compatibility")
    stage38_compat_root = _pointer(
        stage38, _number(contract["stage38_tmhm_root_site"], "Stage38 TM compat site"),
        _number(contract["stage38_tmhm_root_expected"], "Stage38 TM compat expected"),
        "Stage38 TM compatibility")
    species_count = int(contract["species_count"])
    stride = int(contract["compatibility_stride"])
    if species_count != 1621 or stride != 16:
        raise BuildError("compatibility shape differs")
    current_compat = stage[
        _rom_offset(stage61_compat_root, species_count * stride):
        _rom_offset(stage61_compat_root, species_count * stride) + species_count * stride]
    old_compat = stage38[
        _rom_offset(stage38_compat_root, species_count * stride):
        _rom_offset(stage38_compat_root, species_count * stride) + species_count * stride]
    species_rows = _read_csv(ROOT / str(inputs["species_manifest"]["path"]))
    species_ids = {row["species_key"]: int(row["id"]) for row in species_rows}
    if set(species_ids.values()) != set(range(species_count)):
        raise BuildError("species manifest ID range differs")
    collision_changes: set[tuple[int, int]] = set()
    collision_change_counts = {slot: 0 for slot in range(51, 59)}
    for row in v4_changes:
        kind = row["slot_type"]
        slot = int(row["slot_no"])
        if kind != "TM" or not 51 <= slot <= 58:
            continue
        try:
            species = species_ids[row["species_key"]]
        except KeyError as error:
            raise BuildError(f"unresolved V4 Species: {error}") from error
        collision_changes.add((species, slot))
        collision_change_counts[slot] += 1
    if len(collision_changes) != sum(collision_change_counts.values()):
        raise BuildError("duplicate V4 TM51..58 compatibility change")

    compatibility = bytearray(current_compat)
    collision_bits_before = 0
    for species in range(species_count):
        row = species * stride
        for slot in range(51, 59):
            index = slot - 1
            mask = 1 << (index % 8)
            if compatibility[row + index // 8] & mask:
                collision_bits_before += 1
            compatibility[row + index // 8] &= ~mask
    for species, slot in collision_changes:
        index = slot - 1
        compatibility[species * stride + index // 8] |= 1 << (index % 8)
    collision_bits_removed = collision_bits_before - len(collision_changes)
    if collision_bits_removed < 0:
        raise BuildError("V4 collision reconstruction added unexpected missing bits")

    hm_compatible_bits = 0
    for species in range(species_count):
        hm_byte = 0
        old_row = species * stride
        for hm_index in range(8):
            old_index = 50 + hm_index
            if old_compat[old_row + old_index // 8] & (1 << (old_index % 8)):
                hm_byte |= 1 << hm_index
                hm_compatible_bits += 1
        compatibility[old_row + 15] = hm_byte

    payload, layout = _payload(combined_moves, tutor_moves, bytes(compatibility))
    allocation, allocation_report = _allocate(previous, payload)
    payload_offset = int(allocation["start"])
    if stage[payload_offset:payload_offset + len(payload)] != b"\xFF" * len(payload):
        raise BuildError("allocated payload destination is not erased FF")
    table_addresses = {
        "tmhm": GBA_BASE + payload_offset + layout["tmhm_offset"],
        "tutor": GBA_BASE + payload_offset + layout["tutor_offset"],
        "compatibility": GBA_BASE + payload_offset + layout["compatibility_offset"],
    }

    output = bytearray(stage)
    output[payload_offset:payload_offset + len(payload)] = payload
    declarations: list[dict[str, Any]] = [{
        "name": "runtime_payload", "start": payload_offset,
        "end_exclusive": payload_offset + len(payload), "replacement_sha256": _sha(payload),
    }]
    patches: list[dict[str, Any]] = []

    def patch(address: int, expected: bytes, replacement: bytes, name: str,
              category: str) -> None:
        if len(expected) != len(replacement):
            raise BuildError(f"{name}: patch size differs")
        offset = _rom_offset(address, len(expected))
        actual = stage[offset:offset + len(expected)]
        if actual != expected:
            raise BuildError(f"{name}: expected {expected.hex()} got {actual.hex()}")
        output[offset:offset + len(replacement)] = replacement
        row = {
            "name": name, "category": category, "address": address,
            "start": offset, "end_exclusive": offset + len(expected),
            "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
        }
        patches.append(row)
        declarations.append(row)

    patch(
        _number(contract["tmhm_moves_root_site"], "TM move root site"),
        struct.pack("<I", tm_root), struct.pack("<I", table_addresses["tmhm"]),
        "gTMHMMoves_128", "TABLE_ROOT")
    patch(
        _number(contract["tutor_moves_root_site"], "tutor move root site"),
        struct.pack("<I", tutor_root), struct.pack("<I", table_addresses["tutor"]),
        "gTutorMoves_64", "TABLE_ROOT")
    patch(
        _number(contract["stage61_tmhm_root_site"], "TM compat root site"),
        struct.pack("<I", stage61_compat_root),
        struct.pack("<I", table_addresses["compatibility"]),
        "gTMHMLearnsets_128", "TABLE_ROOT")
    patch(
        _number(contract["tutor_learn_limit_site"], "tutor learn cap"),
        bytes.fromhex(contract["tutor_learn_limit_expected_hex"]),
        bytes.fromhex("3f2c"), "CanMonLearnTutorMove_regular_cap_64", "THUMB_INSTRUCTION")
    patch(
        _number(contract["tutor_move_limit_site"], "tutor move cap"),
        bytes.fromhex(contract["tutor_move_limit_expected_hex"]),
        bytes.fromhex("3f2a"), "GetExpandedTutorMove_regular_cap_64", "THUMB_INSTRUCTION")
    stride_site = _number(contract["tutor_stride_site"], "tutor stride site")
    stride_expected = bytes.fromhex(contract["tutor_stride_expected_hex"])
    if stage[_rom_offset(stride_site, len(stride_expected)):
             _rom_offset(stride_site, len(stride_expected)) + len(stride_expected)] != stride_expected:
        raise BuildError("tutor 16-byte stride adapter differs")

    item_root = _pointer(
        stage, _number(contract["item_table_root_site"], "item table root site"),
        _number(contract["item_table_root_expected"], "item table root expected"),
        "item table")
    row_size = int(contract["item_row_size"])
    mystery_offset = int(contract["item_mystery_offset"])
    pocket_offset = int(contract["item_pocket_offset"])
    type_offset = int(contract["item_type_offset"])

    def item_byte(item: int, field_offset: int) -> tuple[int, int]:
        address = item_root + item * row_size + field_offset
        offset = _rom_offset(address)
        return address, stage[offset]

    def require_item(item: int, mystery: int, label: str) -> None:
        _, actual_mystery = item_byte(item, mystery_offset)
        _, pocket = item_byte(item, pocket_offset)
        _, item_type = item_byte(item, type_offset)
        if actual_mystery != mystery or pocket != 4 or item_type != 1:
            raise BuildError(
                f"{label} item {item} differs: mystery={actual_mystery} pocket={pocket} type={item_type}")

    canonical_tm_first = int(contract["canonical_tm_item_first"])
    canonical_tm_last = int(contract["canonical_tm_item_last"])
    if canonical_tm_last - canonical_tm_first + 1 != 50:
        raise BuildError("canonical TM item range differs")
    for slot, item in enumerate(range(canonical_tm_first, canonical_tm_last + 1), 1):
        address, actual = item_byte(item, mystery_offset)
        if actual != 0:
            raise BuildError(f"canonical TM{slot:02d} mystery expected 0 got {actual}")
        patch(address, b"\x00", bytes([slot]), f"canonical_TM{slot:03d}_index", "ITEM_ROW")
    for slot, item in enumerate(
            range(int(contract["alias_tm_item_first"]), int(contract["alias_tm_item_last"]) + 1), 1):
        require_item(item, slot, f"alias TM{slot:02d}")
    for slot, item in enumerate(
            range(int(contract["tm_item_first"]), int(contract["tm_item_last"]) + 1), 51):
        require_item(item, slot, f"expanded TM{slot:03d}")
    for slot, item in enumerate(
            range(int(contract["hm_item_first"]), int(contract["hm_item_last"]) + 1), 121):
        address, actual = item_byte(item, mystery_offset)
        _, pocket = item_byte(item, pocket_offset)
        _, item_type = item_byte(item, type_offset)
        if actual != 0 or pocket != 4 or item_type != 1:
            raise BuildError(f"canonical HM item {item} differs")
        patch(address, b"\x00", bytes([slot]), f"canonical_HM{slot - 120:02d}_index", "ITEM_ROW")
    for slot, item in enumerate(
            range(int(contract["alias_hm_item_first"]), int(contract["alias_hm_item_last"]) + 1), 121):
        require_item(item, slot, f"alias HM{slot - 120:02d}")
    for key, label in (("move_memory_item", "move_memory"),
                       ("ecology_radar_item", "ecology_radar")):
        item = int(contract[key])
        address, actual = item_byte(item, type_offset)
        if actual != 4:
            raise BuildError(f"{label} item type expected 4 got {actual}")
        patch(address, b"\x04", b"\x02", f"{label}_field_item_type", "ITEM_ROW")

    context_gate = _number(
        contract["move_memory_context_battle_gate_site"],
        "move memory context battle gate")
    patch(
        context_gate,
        bytes.fromhex(contract["move_memory_context_battle_gate_expected_hex"]),
        bytes.fromhex(contract["move_memory_context_battle_gate_replacement_hex"]),
        "move_memory_ignore_stale_battle_type", "THUMB_INSTRUCTION")

    hook_rows: list[dict[str, Any]] = []
    for hook in config["hooks"]:
        address = _number(hook["address"], f"hook {hook['name']} address")
        target = _number(hook["target"], f"hook {hook['name']} target")
        target_expected = bytes.fromhex(hook["target_expected_hex"])
        target_offset = _rom_offset(target, len(target_expected))
        if stage[target_offset:target_offset + len(target_expected)] != target_expected:
            raise BuildError(f"hook target differs: {hook['name']}")
        replacement = _jump_stub(target, int(hook["register"]), address)
        patch(address, bytes.fromhex(hook["expected_hex"]), replacement,
              f"runtime_hook::{hook['name']}", "THUMB_JUMP")
        hook_rows.append({
            "name": hook["name"], "address": address, "target": target | 1,
            "register": int(hook["register"]), "replacement_hex": replacement.hex(),
        })

    output_raw = bytes(output)
    ordered = sorted(declarations, key=lambda row: (int(row["start"]), int(row["end_exclusive"])))
    overlaps = [
        (left["name"], right["name"])
        for left, right in zip(ordered, ordered[1:])
        if int(left["end_exclusive"]) > int(right["start"])
    ]
    if overlaps:
        raise BuildError(f"declared patch spans overlap: {overlaps}")
    changed_spans = _changed_spans(stage, output_raw)
    outside = [
        row for row in changed_spans
        if any(not any(int(declared["start"]) <= index
                       < int(declared["end_exclusive"])
                       for declared in ordered)
               for index in range(row["start"], row["end_exclusive"]))
    ]
    if outside:
        raise BuildError(f"changes outside declared spans: {outside[:3]}")

    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw, metadata=b"firered-jpn-rev0-to-stage61-runtime-hotfix")
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        raise BuildError("BPS round trip differs")

    tables = {
        "schema_version": 1, "task": TASK,
        "tm": tm_catalog, "hm": [
            {"slot": index + 1, "runtime_index": 120 + index,
             "move_id": move} for index, move in enumerate(hm_moves)],
        "tutor": tutor_catalog,
        "addresses": table_addresses,
        "compatibility": {
            "species_count": species_count, "stride": stride,
            "tm_slots": 120, "hm_slots": 8, "hm_compatible_bits": hm_compatible_bits,
            "tm51_58_v4_change_counts": collision_change_counts,
            "tm51_58_bits_before": collision_bits_before,
            "tm51_58_legacy_hm_bits_removed": collision_bits_removed,
            "sha256": _sha(bytes(compatibility)),
        },
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input_sha256": _sha(stage), "rom_sha256": _sha(output_raw),
        "rom_crc32": f"{binascii.crc32(output_raw) & 0xFFFFFFFF:08X}",
        "root_causes": {
            "tm": "gTMHMMovesがTM50+HM8の58要素で、TM51以降とHM indexが衝突",
            "tutor": "gTutorMovesは15要素の直後が0で、16以降が別dataへ越境",
            "field_items": "item type=4がCB2_ReturnToFieldWithOpenMenuを選び、gFieldCallback2が専用callbackを破棄",
            "move_memory_context": "gBattleTypeFlagsが戦闘終了後も直前の種別を保持し、通常fieldを戦闘中と誤判定",
        },
        "repair": {
            "tm_slots": 120, "hm_slots": 8, "tutor_slots": 64,
            "canonical_tm_item_indices_patched": 50,
            "canonical_hm_item_indices_patched": 8,
            "field_item_type_patches": 2,
            "stale_battle_type_guard_patches": 1,
            "runtime_hook_count": len(hook_rows), "hooks": hook_rows,
            "tutor_regular_cap": 64, "tutor_stride": 16,
            "tm51_58_v4_change_counts": collision_change_counts,
            "tm51_58_legacy_hm_bits_removed": collision_bits_removed,
        },
        "allocation": allocation,
        "change_audit": {
            "changed_span_count": len(changed_spans), "spans": changed_spans,
            "declared_span_overlap_count": 0, "outside_declared_span_count": 0,
        },
        "bps": {"incremental_round_trip": "PASS", "clean_round_trip": "PASS"},
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": 61, "status": "PASS",
        "candidate_status": "CANDIDATE", "strict_audit_status": "DEFERRED_AUDIT",
        "input": {"path": inputs["stage61_rom"]["path"], "size": len(stage),
                  "sha256": _sha(stage), "metadata_sha256": _sha(metadata_raw)},
        "output": {"path": outputs["rom"], "size": len(output_raw),
                   "sha256": _sha(output_raw),
                   "crc32": f"{binascii.crc32(output_raw) & 0xFFFFFFFF:08X}"},
        "runtime": {
            "payload": {"address": GBA_BASE + payload_offset,
                        "offset": payload_offset, "size": len(payload),
                        "sha256": _sha(payload)},
            "tables": tables["addresses"], "counts": {"tm": 120, "hm": 8, "tutor": 64},
            "hooks": hook_rows,
        },
        "audit": audit,
    }
    report = f"""# Stage61 runtime hotfix

- TM/HM: `gTMHMMoves`をTM120+HM8へ再配置し、16-byte互換表のslot 120..127へ旧HM互換を移送。
- 教え技: `gTutorMoves`をV4の64件へ再配置し、16-byte strideの通常枠を0..63へ制限。
- consumer: CFRU-JP固定buildにあるTM/HM/tutor expansion入口を{len(hook_rows)}か所接続。
- field item: わざメモリー／せいたいレーダーのtypeを`BAG_MENU(4)`から`FIELD(2)`へ修正。
- context: 戦闘終了後に残る`gBattleTypeFlags`をfield使用不可条件から除外し、facility／Raid中だけを拒否。
- ROM SHA-256: `{_sha(output_raw)}` / CRC32: `{binascii.crc32(output_raw) & 0xFFFFFFFF:08X}`
- declared span外変更: 0 / BPS往復: PASS
""".encode("utf-8")
    artifacts = {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["payload"]: payload,
        outputs["tables"]: _stable(tables),
        outputs["audit"]: _stable(audit),
        outputs["report"]: report,
    }
    return artifacts, metadata


def _write(artifacts: Mapping[str, bytes]) -> None:
    for name, raw in artifacts.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _check(artifacts: Mapping[str, bytes]) -> None:
    differences = []
    for name, expected in artifacts.items():
        path = ROOT / name
        if not path.is_file() or path.read_bytes() != expected:
            differences.append(name)
    if differences:
        raise BuildError(f"generated outputs differ: {differences}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()
    try:
        artifacts, metadata = _build_artifacts(args.config)
        if args.action == "build":
            _write(artifacts)
        else:
            _check(artifacts)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            struct.error, zipfile.BadZipFile, BuildError) as error:
        print(f"Stage61 runtime hotfix {args.action}: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS", "action": args.action,
        "sha256": metadata["output"]["sha256"],
        "crc32": metadata["output"]["crc32"],
        "tm": 120, "hm": 8, "tutor": 64,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
