#!/usr/bin/env python3
"""Stage57の通常戦／再戦trainer分離をROM rootからfail-closed監査する。

検査対象は、誤ったmap bindingによって通常戦にもLv.80～100 partyが接続された
8 mapである。全map event rootからCFGを再構築し、通常戦66 command、再戦66
command、共有trainer 348のKanto側caller、および分離先1384の未使用条件を
ROM tableと突き合わせる。成功時も失敗時もCLI出力はJSONで、失敗時は非ゼロ終了
する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage57_debug_suite import _collect_contactable_roots  # noqa: E402
from tools.t02.rom_inventory import (  # noqa: E402
    RomImage,
    ScriptWalker,
    _decode_trainer_party,
)


ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024

TRAINER_TABLE_ADDRESS = 0x09329070
TRAINER_TABLE_COUNT = 4284
TRAINER_RECORD_SIZE = 32
TRAINER_PARTY_ADDRESS = 0x0934A7F0
TRAINER_PARTY_SIZE = 103840

EXACT_TABLE_ADDRESS = 0x09308B08
EXACT_COUNT = 1302
EXACT_ROW_SIZE = 12
REMATCH_TABLE_ADDRESS = 0x093083F0
REMATCH_COUNT = 227
REMATCH_ROW_SIZE = 8
ARCHIVE_TABLE_ADDRESS = 0x09307F80
ARCHIVE_COUNT = 71
ARCHIVE_ROW_SIZE = 16
GIMMICK_TABLE_ADDRESS = 0x09304278
GIMMICK_COUNT = 1302
GIMMICK_ROW_SIZE = 12
SIDECAR_TABLE_ADDRESS = 0x0930C810
SIDECAR_COUNT = 6490
SIDECAR_ROW_SIZE = 18
FLAG_TABLE_ADDRESS = 0x09303CA8
FLAG_COUNT = 372
FLAG_ROW_SIZE = 4

SHARED_TRAINER_ID = 348
SHARED_CLONE_ID = 1384
TRAINER_FLAG_START = 0x0500

EXPECTED_ROM_SHA256 = (
    "546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d"
)
EXPECTED_TABLE_SHA256: Mapping[str, tuple[int, int, str]] = {
    "trainer": (
        TRAINER_TABLE_ADDRESS,
        TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE,
        "bf886961e9afc22682a3b50bfcbe8ef9629a3d51ac34a128c585b7eee43fdc40",
    ),
    "party": (
        TRAINER_PARTY_ADDRESS,
        TRAINER_PARTY_SIZE,
        "86bec35c4ac4b526a8668cbbe99b8e67d3dd22311ab17d0df3dcea21fda143ed",
    ),
    "exact": (
        EXACT_TABLE_ADDRESS,
        EXACT_COUNT * EXACT_ROW_SIZE,
        "be1080cf81630a1071f805a60d0d73174695d823a04aae4e9d34ee2ba20e8245",
    ),
    "sidecar": (
        SIDECAR_TABLE_ADDRESS,
        SIDECAR_COUNT * SIDECAR_ROW_SIZE,
        "5ae7dac1293eb32de21d691f873621acf30cc5e7bf32d0869c1257b8c055a0a2",
    ),
    "gimmick": (
        GIMMICK_TABLE_ADDRESS,
        GIMMICK_COUNT * GIMMICK_ROW_SIZE,
        "5f86b0151af5b7dc42a8294a262563a3ade054ca7f36c2a6c100d7fc1c612a72",
    ),
}

STORY_MAPS = frozenset(
    {(3, 21), (3, 23), (3, 28), (3, 31), (3, 32), (3, 33), (3, 41), (3, 42)}
)
EXPECTED_MAP_AUDIT: Mapping[tuple[int, int], Mapping[str, Any]] = {
    (3, 21): {"commands": 12, "objects": 13, "level_range": (6, 13)},
    (3, 23): {"commands": 4, "objects": 6, "level_range": (9, 14)},
    (3, 28): {"commands": 12, "objects": 13, "level_range": (41, 45)},
    (3, 31): {"commands": 7, "objects": 7, "level_range": (41, 47)},
    (3, 32): {"commands": 9, "objects": 10, "level_range": (32, 38)},
    (3, 33): {"commands": 3, "objects": 3, "level_range": (34, 37)},
    (3, 41): {"commands": 4, "objects": 4, "level_range": (24, 32)},
    (3, 42): {"commands": 15, "objects": 17, "level_range": (14, 27)},
}


@dataclass(frozen=True)
class RepairSpec:
    data_address: int
    target_id: int
    template_id: int
    group: int
    map_number: int
    object_indices: tuple[int, ...]
    kind: int
    record_hex: str

    @property
    def runtime_id(self) -> int:
        return SHARED_CLONE_ID if self.target_id == SHARED_TRAINER_ID else self.target_id


REPAIR_SPECS: tuple[RepairSpec, ...] = (
    RepairSpec(0x0936D268, 1092, 169, 3, 42, (13, 14), 4,
               "035e02816868145b98ff000000000000000001000100000003000000a4db2c09"),
    RepairSpec(0x0936DA54, 194, 194, 3, 42, (7,), 0,
               "034b04156a5896ffffff16000000000000000000030000000300000094dc2c09"),
    RepairSpec(0x0936E614, 23, 23, 3, 32, (4,), 0,
               "035004697c5a53ffffff150000000000000000000300000003000000f4dc2c09"),
    RepairSpec(0x0936EC0C, 24, 24, 3, 32, (5,), 0,
               "0366058e555387ffffff15000000000000000000030000000300000084dd2c09"),
    RepairSpec(0x0936F62C, 273, 273, 3, 42, (10,), 0,
               "03120b125c8a5162ffff160000000000000000000300000003000000c4dc2c09"),
    RepairSpec(0x09370834, 347, 347, 3, 41, (1,), 0,
               "032581315b5877ffffff16000000000000000000030000000300000064dc2c09"),
    RepairSpec(0x093708B4, 348, 348, 3, 33, (1,), 0,
               "034c00657752ffffffff15000000000000000000030000000300000054dd2c09"),
    RepairSpec(0x093709E0, 354, 354, 3, 41, (3,), 0,
               "034e0b67717553ffffff15000000000000000000030000000300000034dc2c09"),
    RepairSpec(0x09370C94, 373, 373, 3, 32, (0,), 0,
               "032e0d175b578653ffff15000000000000000000030000000300000084dd2c09"),
    RepairSpec(0x09370E30, 377, 377, 3, 28, (6,), 0,
               "0346085f5b5287ffffff150000000000000000000300000003000000e4dd2c09"),
    RepairSpec(0x09370F04, 380, 380, 3, 32, (3,), 0,
               "0314031469986056ffff150000000000000000000300000003000000f4dc2c09"),
    RepairSpec(0x093711C4, 387, 387, 3, 31, (1,), 0,
               "0364028c61525affffff150000000000000000000300000003000000e4dd2c09"),
    RepairSpec(0x09372138, 47, 47, 3, 28, (3,), 0,
               "030800076e5357ffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x09372404, 48, 48, 3, 28, (5,), 0,
               "0346085f728768ffffff150000000000000000000500000003000000b4dd2c09"),
    RepairSpec(0x093725D4, 49, 49, 3, 28, (9,), 0,
               "03080007597e64ffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x09372F4C, 52, 52, 3, 31, (5,), 0,
               "0308000759977effffff150000000000000000000300000003000000e4dd2c09"),
    RepairSpec(0x093733D4, 537, 537, 3, 33, (0,), 0,
               "034800616978765cffff15000000000000000000030000000300000054dd2c09"),
    RepairSpec(0x09373544, 542, 542, 3, 33, (2,), 0,
               "0323002f6a7957ffffff15000000000000000000030000000300000054dd2c09"),
    RepairSpec(0x09373B40, 577, 577, 3, 28, (0,), 0,
               "0346080f537055ffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x09373BE0, 579, 579, 3, 28, (1,), 0,
               "0349810c517556ffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x09373CE0, 580, 580, 3, 28, (4,), 0,
               "034a81636f6562ffffff150000000000000000000300000003000000e4dd2c09"),
    RepairSpec(0x09373D60, 581, 581, 3, 28, (8,), 0,
               "0346080f60565cffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x09373E44, 1299, 583, 3, 28, (11, 12), 4,
               "036008837065146998ff15000000000000000100030000000400000014de2c09"),
    RepairSpec(0x09373EA8, 585, 585, 3, 28, (10,), 0,
               "034a813278525bffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x0937457C, 605, 605, 3, 31, (0,), 0,
               "034a81326b7270ffffff15000000000000000000030000000300000054de2c09"),
    RepairSpec(0x09374B48, 621, 621, 3, 31, (6,), 0,
               "0346080f677255ffffff15000000000000000000030000000300000054de2c09"),
)

SHARED_HIGH_RECORD = bytes.fromhex(
    "034c00657752ffffffff000000000000000000000500000006000000a00d3509"
)
EXPECTED_EXTERNAL_REFERENCE = {
    "trainer_id": SHARED_TRAINER_ID,
    "access": "battle",
    "kind": 3,
    "instruction_address": 0x0816637A,
    "root": "map:97:45:object:5",
}

ROOT_RE = re.compile(r"^map:(\d+):(\d+):object:(\d+)$")


class StoryTrainerAuditError(ValueError):
    """Stage57 trainer invariantが成立しない。"""


def _fail(message: str) -> NoReturn:
    raise StoryTrainerAuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _raw(raw: bytes, address: int, size: int) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or size < 0 or offset + size > len(raw):
        _fail(f"ROM範囲外read: address=0x{address:08X} size={size}")
    return raw[offset:offset + size]


def _trainer_record(raw: bytes, trainer_id: int) -> bytes:
    if not 0 <= trainer_id < TRAINER_TABLE_COUNT:
        _fail(f"trainer ID範囲外: {trainer_id}")
    return _raw(
        raw,
        TRAINER_TABLE_ADDRESS + trainer_id * TRAINER_RECORD_SIZE,
        TRAINER_RECORD_SIZE,
    )


def _trainer_levels(rom: RomImage, trainer_id: int) -> list[int]:
    address = TRAINER_TABLE_ADDRESS + trainer_id * TRAINER_RECORD_SIZE
    flags = rom.u8(address, what=f"trainer {trainer_id} flags")
    size = rom.u8(address + 0x18, what=f"trainer {trainer_id} party size")
    pointer = rom.u32(address + 0x1C, what=f"trainer {trainer_id} party pointer")
    return [
        int(member["level"])
        for member in _decode_trainer_party(rom, pointer, size, flags)
    ]


def _decode_exact(raw: bytes) -> list[tuple[int, int, int, int, int, int]]:
    return [
        struct.unpack(
            "<IHHBBH",
            _raw(raw, EXACT_TABLE_ADDRESS + index * EXACT_ROW_SIZE, EXACT_ROW_SIZE),
        )
        for index in range(EXACT_COUNT)
    ]


def _decode_rematch(raw: bytes) -> list[tuple[int, int, int]]:
    return [
        struct.unpack(
            "<IHH",
            _raw(
                raw,
                REMATCH_TABLE_ADDRESS + index * REMATCH_ROW_SIZE,
                REMATCH_ROW_SIZE,
            ),
        )
        for index in range(REMATCH_COUNT)
    ]


def _decode_archives(raw: bytes) -> list[tuple[int, int, int, int, int, int, int]]:
    rows: list[tuple[int, int, int, int, int, int, int]] = []
    for index in range(ARCHIVE_COUNT):
        values = struct.unpack(
            "<IHHHHBB2s",
            _raw(
                raw,
                ARCHIVE_TABLE_ADDRESS + index * ARCHIVE_ROW_SIZE,
                ARCHIVE_ROW_SIZE,
            ),
        )
        rows.append(values[:7])
    return rows


def _decode_sidecars(raw: bytes) -> list[tuple[int, ...]]:
    return [
        struct.unpack(
            "<HHH12B",
            _raw(
                raw,
                SIDECAR_TABLE_ADDRESS + index * SIDECAR_ROW_SIZE,
                SIDECAR_ROW_SIZE,
            ),
        )
        for index in range(SIDECAR_COUNT)
    ]


def _decode_gimmicks(raw: bytes) -> list[tuple[int, int, int, int, int, int, int]]:
    rows: list[tuple[int, int, int, int, int, int, int]] = []
    for index in range(GIMMICK_COUNT):
        values = struct.unpack(
            "<HH5B3s",
            _raw(
                raw,
                GIMMICK_TABLE_ADDRESS + index * GIMMICK_ROW_SIZE,
                GIMMICK_ROW_SIZE,
            ),
        )
        rows.append(values[:7])
    return rows


def _decode_flags(raw: bytes) -> list[tuple[int, int]]:
    return [
        struct.unpack(
            "<HH",
            _raw(raw, FLAG_TABLE_ADDRESS + index * FLAG_ROW_SIZE, FLAG_ROW_SIZE),
        )
        for index in range(FLAG_COUNT)
    ]


def _map_object(label: str) -> tuple[int, int, int] | None:
    match = ROOT_RE.fullmatch(label)
    if match is None:
        return None
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


def _audit_runtime_tables(
    raw: bytes,
    exact_rows: Sequence[tuple[int, int, int, int, int, int]],
) -> dict[str, Any]:
    sidecars = _decode_sidecars(raw)
    gimmicks = _decode_gimmicks(raw)
    rematches = _decode_rematch(raw)
    archives = _decode_archives(raw)
    flags = _decode_flags(raw)

    exact_by_key: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for index, (data, source, target, kind, row_flags, dispatch) in enumerate(exact_rows):
        key = (data, source, kind)
        if key in exact_by_key:
            _fail(f"exact binding key重複: {key}")
        exact_by_key[key] = (target, row_flags, dispatch)

    repair_rows: list[dict[str, Any]] = []
    for spec in REPAIR_SPECS:
        binding = exact_by_key.get((spec.data_address, spec.target_id, spec.kind))
        expected_binding = (spec.runtime_id, 1, 0)
        if binding != expected_binding:
            _fail(
                "通常戦exact binding不一致: "
                f"data=0x{spec.data_address:08X} actual={binding} "
                f"expected={expected_binding}"
            )
        actual_record = _trainer_record(raw, spec.runtime_id)
        expected_record = bytes.fromhex(spec.record_hex)
        if actual_record != expected_record:
            _fail(
                f"trainer record不一致: trainer={spec.runtime_id} "
                f"actual={actual_record.hex()} expected={spec.record_hex}"
            )

        if spec.target_id == SHARED_TRAINER_ID:
            if _trainer_record(raw, SHARED_TRAINER_ID) != SHARED_HIGH_RECORD:
                _fail("共有trainer 348のKanto用高レベルrecordが変化しています")
        else:
            member_rows = [row for row in sidecars if row[0] == spec.target_id]
            if len(member_rows) != 6:
                _fail(
                    f"sidecar件数不一致: trainer={spec.target_id} "
                    f"actual={len(member_rows)} expected=6"
                )
            if [(row[3], row[4]) for row in member_rows] != [
                (1, slot) for slot in range(6)
            ]:
                _fail(f"sidecar side/slot不一致: trainer={spec.target_id}")
            if any(row[1] != 0 or row[2] != 0 for row in member_rows):
                _fail(f"sidecar species/abilityが有効なままです: trainer={spec.target_id}")
            gimmick_rows = [row for row in gimmicks if row[0] == spec.target_id]
            if len(gimmick_rows) != 1 or gimmick_rows[0][1] != 0:
                _fail(f"gimmick dispatch inventory不一致: trainer={spec.target_id}")
            if gimmick_rows[0][3] != 0:
                _fail(f"gimmick ai_profileが有効なままです: trainer={spec.target_id}")

        repair_rows.append(
            {
                "map": f"{spec.group}/{spec.map_number}",
                "objects": list(spec.object_indices),
                "command_address": f"0x{spec.data_address - 1:08X}",
                "source_trainer_id": spec.target_id,
                "runtime_trainer_id": spec.runtime_id,
                "template_trainer_id": spec.template_id,
            }
        )

    clone_exact = [
        (index, row)
        for index, row in enumerate(exact_rows)
        if row[2] == SHARED_CLONE_ID
    ]
    if clone_exact != [(694, (0x093708B4, 348, 1384, 0, 1, 0))]:
        _fail(f"clone 1384 exact consumer不一致: {clone_exact}")
    if any(row[1] == SHARED_CLONE_ID for row in exact_rows):
        _fail("clone 1384がcommand sourceとして使用されています")
    if any(row[1] == SHARED_CLONE_ID or row[2] == SHARED_CLONE_ID for row in rematches):
        _fail("clone 1384がrematch tableで使用されています")
    if any(row[1] == SHARED_CLONE_ID or row[2] == SHARED_CLONE_ID for row in archives):
        _fail("clone 1384がarchive tableで使用されています")
    if any(row[0] == SHARED_CLONE_ID for row in sidecars):
        _fail("clone 1384にsidecarが存在します")
    if any(row[0] == SHARED_CLONE_ID for row in gimmicks):
        _fail("clone 1384にgimmickが存在します")
    clone_external_flag = TRAINER_FLAG_START + SHARED_CLONE_ID
    if any(external == clone_external_flag for external, _ in flags):
        _fail(f"clone 1384 external flag 0x{clone_external_flag:04X}が割当済みです")

    affected = {spec.target_id for spec in REPAIR_SPECS}
    if any(
        row[1] in affected or row[2] in affected
        for row in rematches
    ):
        _fail("通常戦修復targetがrematch tableでも共有されています")
    if any(
        row[1] in affected or row[2] in affected
        for row in archives
    ):
        _fail("通常戦修復targetがarchive tableでも共有されています")

    return {
        "repair_count": len(repair_rows),
        "in_place_count": len(repair_rows) - 1,
        "shared_split_count": 1,
        "shared_clone": {
            "trainer_id": SHARED_CLONE_ID,
            "exact_consumers": 1,
            "command_source_consumers": 0,
            "rematch_consumers": 0,
            "archive_consumers": 0,
            "sidecar_rows": 0,
            "gimmick_rows": 0,
            "external_flag_mapping": 0,
        },
        "rows": sorted(repair_rows, key=lambda row: row["command_address"]),
    }


def _resolve_binding(
    exact: Mapping[tuple[int, int, int], tuple[int, int, int]],
    reference: Mapping[str, Any],
) -> int:
    key = (
        int(reference["instruction_address"]) + 1,
        int(reference["value"]),
        int(reference["battle_type"]),
    )
    binding = exact.get(key)
    if binding is None:
        _fail(f"story map trainerbattleにexact bindingなし: {key}")
    target, flags, dispatch = binding
    if (flags, dispatch) != (1, 0):
        _fail(f"story map exact binding policy不一致: {key} -> {binding}")
    return target


def _audit_world_cfg(
    raw: bytes,
    exact_rows: Sequence[tuple[int, int, int, int, int, int]],
) -> dict[str, Any]:
    rom = RomImage("Stage57 story trainer", raw)
    roots, root_counts = _collect_contactable_roots(rom)
    walker = ScriptWalker(rom)
    for root in roots:
        walker.add_root(root)
    graph = walker.walk()
    if graph["diagnostics"]:
        _fail(
            "event CFG diagnostics残存: "
            + json.dumps(graph["diagnostics"][:8], ensure_ascii=False, sort_keys=True)
        )

    root_addresses = {root.label: root.address for root in roots}
    exact = {
        (data, source, kind): (target, flags, dispatch)
        for data, source, target, kind, flags, dispatch in exact_rows
    }
    story_rows: list[dict[str, Any]] = []
    affected = {spec.target_id for spec in REPAIR_SPECS}
    affected_references: list[Mapping[str, Any]] = []
    clone_references: list[Mapping[str, Any]] = []

    for reference in graph["references"]:
        if reference.get("category") != "trainer":
            continue
        value = int(reference["value"])
        if value in affected:
            affected_references.append(reference)
        if value == SHARED_CLONE_ID:
            clone_references.append(reference)
        if reference.get("access") != "battle":
            continue
        relevant_labels: list[str] = []
        for label in reference.get("roots", []):
            parsed = _map_object(str(label))
            if parsed is not None and parsed[:2] in STORY_MAPS:
                relevant_labels.append(str(label))
        if not relevant_labels:
            continue
        direct_labels = [
            label
            for label in relevant_labels
            if root_addresses.get(label) == int(reference["instruction_address"])
        ]
        target = _resolve_binding(exact, reference)
        levels = _trainer_levels(rom, target)
        if not levels:
            _fail(f"空party trainerがstory mapに接続: {target}")
        story_rows.append(
            {
                "phase": "direct" if direct_labels else "rematch",
                "instruction_address": int(reference["instruction_address"]),
                "data_address": int(reference["instruction_address"]) + 1,
                "source_trainer_id": value,
                "target_trainer_id": target,
                "kind": int(reference["battle_type"]),
                "levels": levels,
                "root_labels": sorted(direct_labels if direct_labels else relevant_labels),
            }
        )

    direct = [row for row in story_rows if row["phase"] == "direct"]
    rematch = [row for row in story_rows if row["phase"] == "rematch"]
    if len(direct) != 66 or Counter(row["kind"] for row in direct) != {0: 59, 4: 7}:
        _fail(f"direct command inventory不一致: count={len(direct)} kinds={Counter(row['kind'] for row in direct)}")
    if len(rematch) != 66 or Counter(row["kind"] for row in rematch) != {5: 59, 7: 7}:
        _fail(f"rematch command inventory不一致: count={len(rematch)} kinds={Counter(row['kind'] for row in rematch)}")

    direct_labels = [label for row in direct for label in row["root_labels"]]
    rematch_labels = [label for row in rematch for label in row["root_labels"]]
    if len(direct_labels) != 73 or len(set(direct_labels)) != 73:
        _fail("direct object root inventory不一致")
    if len(rematch_labels) != 73 or Counter(rematch_labels) != Counter(direct_labels):
        _fail("各direct rootに対応するrematch continuationが一意ではありません")

    high_direct = [row for row in direct if min(row["levels"]) >= 80]
    high_rematch = [row for row in rematch if min(row["levels"]) >= 80]
    if high_direct:
        _fail(
            "通常戦にLv80以上partyが残存: "
            + ",".join(f"0x{row['instruction_address']:08X}" for row in high_direct)
        )
    if len(high_rematch) != 26 or sum(len(row["root_labels"]) for row in high_rematch) != 28:
        _fail("高難度rematch partyの保存件数不一致")

    by_map: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in direct:
        parsed_maps = {
            _map_object(label)[:2]  # type: ignore[index]
            for label in row["root_labels"]
        }
        if len(parsed_maps) != 1:
            _fail(f"direct commandが複数mapから共有されています: {row}")
        by_map[next(iter(parsed_maps))].append(row)

    map_rows: list[dict[str, Any]] = []
    for map_id, expected in EXPECTED_MAP_AUDIT.items():
        values = by_map.get(map_id, [])
        objects = [label for row in values for label in row["root_labels"]]
        levels = [level for row in values for level in row["levels"]]
        actual_range = (min(levels), max(levels)) if levels else None
        if (
            len(values) != expected["commands"]
            or len(objects) != expected["objects"]
            or actual_range != expected["level_range"]
        ):
            _fail(
                f"map {map_id[0]}/{map_id[1]}通常戦不一致: "
                f"commands={len(values)} objects={len(objects)} levels={actual_range}"
            )
        map_rows.append(
            {
                "map": f"{map_id[0]}/{map_id[1]}",
                "direct_commands": len(values),
                "object_roots": len(objects),
                "level_min": actual_range[0],
                "level_max": actual_range[1],
            }
        )

    expected_specs = {spec.data_address: spec for spec in REPAIR_SPECS}
    repaired_direct = [row for row in direct if row["data_address"] in expected_specs]
    if len(repaired_direct) != len(REPAIR_SPECS):
        _fail(f"修復対象direct command到達数不一致: {len(repaired_direct)}")
    for row in repaired_direct:
        spec = expected_specs[row["data_address"]]
        actual_objects = sorted(
            parsed[2]
            for label in row["root_labels"]
            if (parsed := _map_object(label)) is not None
        )
        if (
            row["source_trainer_id"] != spec.target_id
            or row["target_trainer_id"] != spec.runtime_id
            or row["kind"] != spec.kind
            or actual_objects != list(spec.object_indices)
        ):
            _fail(f"修復対象direct root/binding不一致: data=0x{spec.data_address:08X}")

    external_rows: list[dict[str, Any]] = []
    for reference in affected_references:
        for label in reference.get("roots", []):
            parsed = _map_object(str(label))
            if parsed is None or parsed[:2] in STORY_MAPS:
                continue
            external_rows.append(
                {
                    "trainer_id": int(reference["value"]),
                    "access": str(reference["access"]),
                    "kind": reference.get("battle_type"),
                    "instruction_address": int(reference["instruction_address"]),
                    "root": str(label),
                }
            )
    if external_rows != [EXPECTED_EXTERNAL_REFERENCE]:
        _fail(f"8 map外の共有参照不一致: {external_rows}")
    if clone_references:
        _fail("clone 1384がROM event commandから直接参照されています")

    return {
        "all_world": {
            "root_count": len(roots),
            "root_counts": dict(sorted(root_counts.items())),
            "visited_script_count": graph["visited_script_count"],
            "diagnostic_count": 0,
        },
        "direct": {
            "commands": len(direct),
            "kinds": {str(key): value for key, value in sorted(Counter(row["kind"] for row in direct).items())},
            "object_roots": len(direct_labels),
            "level_80_or_higher_commands": 0,
            "repaired_commands": len(repaired_direct),
        },
        "rematch": {
            "commands": len(rematch),
            "kinds": {str(key): value for key, value in sorted(Counter(row["kind"] for row in rematch).items())},
            "object_roots": len(rematch_labels),
            "level_80_or_higher_commands": len(high_rematch),
            "level_80_or_higher_object_roots": sum(len(row["root_labels"]) for row in high_rematch),
        },
        "maps": map_rows,
        "external_references": external_rows,
        "clone_direct_event_references": 0,
    }


def audit_story_trainers(
    raw: bytes,
    *,
    expected_rom_sha256: str | None = EXPECTED_ROM_SHA256,
) -> dict[str, Any]:
    """Stage57 ROM bytesを監査し、PASS時の機械可読結果を返す。"""

    started = time.monotonic()
    if len(raw) != ROM_SIZE:
        _fail(f"ROM size不一致: actual={len(raw)} expected={ROM_SIZE}")
    exact_rows = _decode_exact(raw)
    runtime = _audit_runtime_tables(raw, exact_rows)
    world = _audit_world_cfg(raw, exact_rows)

    section_hashes: dict[str, str] = {}
    for label, (address, size, expected) in EXPECTED_TABLE_SHA256.items():
        actual = _sha(_raw(raw, address, size))
        if actual != expected:
            _fail(
                f"{label} table SHA-256不一致: actual={actual} expected={expected}"
            )
        section_hashes[label] = actual

    rom_sha256 = _sha(raw)
    if expected_rom_sha256 is not None and rom_sha256 != expected_rom_sha256:
        _fail(
            f"ROM SHA-256不一致: actual={rom_sha256} expected={expected_rom_sha256}"
        )
    return {
        "status": "PASS",
        "rom_sha256": rom_sha256,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "section_sha256": section_hashes,
        "runtime_tables": runtime,
        "world_cfg": world,
    }


def _stable(document: Mapping[str, Any]) -> str:
    return json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--expected-rom-sha256",
        default=EXPECTED_ROM_SHA256,
        help="固定ROM identity。空文字ならtable/CFGのみ監査する。",
    )
    args = parser.parse_args(argv)
    try:
        expected = args.expected_rom_sha256 or None
        result = audit_story_trainers(
            args.rom.read_bytes(),
            expected_rom_sha256=expected,
        )
        document: Mapping[str, Any] = {
            "schema_version": 1,
            "tool": "stage57_story_trainer_audit",
            **result,
        }
        exit_code = 0
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        document = {
            "schema_version": 1,
            "tool": "stage57_story_trainer_audit",
            "status": "FAIL",
            "error": str(error),
        }
        exit_code = 1
    rendered = _stable(document)
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        except OSError as error:
            print(f"output write failed: {error}", file=sys.stderr)
            return 1
    print(rendered, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
