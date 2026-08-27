#!/usr/bin/env python3
"""Stage57向けの高速・決定的なROM横断デバッガ。

quickは今回修復したruntime/table/callsiteを直接検査し、fullは678 mapの
接触可能object・coord・BG・map-scriptから実際のevent CFGを全件走査する。
どちらもbyte-pattern推測ではなく、ROM上の正規pointer rootを辿る。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_qol_production import _load_model  # noqa: E402
from tools.t02.rom_inventory import (  # noqa: E402
    MAP_GROUPS_POINTER_SITE,
    ROM_BASE,
    RomImage,
    ScriptRoot,
    ScriptWalker,
    _decode_map_scripts,
)
from tools.world_runtime_e2e_repair import _coordinates  # noqa: E402


ROM_SIZE = 32 * 1024 * 1024
RESEARCH_TABLE_ADDRESS = 0x0937DF60
RESEARCH_RULE_COUNT = 846
RESEARCH_RULE_SIZE = 12
FIELD_PC_TABLE_ADDRESS = 0x09380708
FIELD_PC_MAP_COUNT = 69
FIELD_PC_ROW_SIZE = 2
ROUTE_505 = (3, 23)
ROUTE_505_FORBIDDEN_SPECIES = frozenset({92, 717, 804})
ROUTE_505_RESEARCH_SPECIES = (
    431, 511, 521, 535, 540, 784, 809, 953, 990, 1003, 1316, 1524,
)
MENU_TILE_BASE = 0x38
MENU_BASE_INSTRUCTIONS = bytes.fromhex("3820c046")  # movs r0,#0x38; nop

MENU_CALLSITES: tuple[tuple[str, int, bytes], ...] = (
    ("wild_overlay", 0x09220610, bytes.fromhex("00f094f8")),
    ("move_memory", 0x092D001E, bytes.fromhex("00f07bf8")),
    ("acquisition", 0x092D18BC, bytes.fromhex("00f0c6f8")),
    ("bp_shop", 0x092DC67A, bytes.fromhex("00f0edf8")),
    ("qol_supply", 0x09378E8A, bytes.fromhex("00f0ebf8")),
    ("qol_quantity", 0x0937A0DA, bytes.fromhex("00f095f8")),
    ("research_economy", 0x093BF05A, bytes.fromhex("00f0ebf8")),
    ("reward_encounters", 0x093C2084, bytes.fromhex("00f0d0f8")),
    ("factory_high_modes", 0x093C4CAC, bytes.fromhex("00f054f8")),
    ("collection_supply", 0x09406DB4, bytes.fromhex("00f0cef8")),
)

SPECIES_SET_CALLSITES: tuple[tuple[str, int, bytes], ...] = (
    ("collection_wild_species", 0x09405E9C, bytes.fromhex("00f018f8")),
    ("collection_form_species", 0x09407022, bytes.fromhex("00f029f8")),
    ("collection_form_rollback", 0x0940703E, bytes.fromhex("00f01bf8")),
)

WILD_GENERATION_HOOK = (
    "land_water_wild_generation",
    0x080826D8,
    bytes.fromhex("004b1847c95d4009"),
)

FACTORY_CURSOR_CALLSITE = (
    "factory_menu_cursor_abi",
    0x093C4D02,
    bytes.fromhex("00f02af8"),
)

NPC_POINTER_REPAIRS: tuple[tuple[str, int, int, int], ...] = (
    ("map96_00_object01_fat_man", 0x093FC1E8, 0x0816F957, 0x093DCF00),
    ("map98_06_object01_school_lass", 0x09401AB0, 0x0817EA26, 0x093DCF0C),
    ("map98_49_object03_tea_woman", 0x09402F7C, 0x081847CE, 0x093DCF0C),
    ("map98_51_object03_writer", 0x09403064, 0x081849D1, 0x093DCF0C),
    ("map98_53_object00_black_belt", 0x0940311C, 0x08184BAA, 0x093DCF0C),
    ("map98_61_object02_beauty_boyfriend", 0x094037E0, 0x0818688C, 0x093DCF0C),
    ("map98_66_object01_woman", 0x09403A3C, 0x08187624, 0x093DCF0C),
    ("map98_86_object01_lass", 0x094044CC, 0x0818AEFC, 0x093DCF0C),
    ("map98_86_object02_youngster", 0x094044E4, 0x0818AF05, 0x093DCF0C),
)

CONTROL_FLOW_REPAIRS: tuple[tuple[str, int, int, int], ...] = (
    ("map03_65_static_escape_00", 0x088B311C, 0x088B312D, 0x088B312A),
    ("map03_65_static_escape_01", 0x088B317C, 0x088B318D, 0x088B318A),
    ("map32_00_call_if_pointer", 0x0818F879, 0xC018F8CB, 0x0818F8CB),
)

BROKEN_BG_TERMINAL = (
    "map97_46_rocket_hideout_elevator",
    0x0938DD2D,
    bytes.fromhex("05f0661608"),
)

EXPECTED_ROOT_COUNTS = {
    "object": 3089,
    "coord": 743,
    "bg": 1031,
    "map_script": 569,
}

# Stage35 Trainer ChangeKitが「バトルサーチャー再戦」向けのLv80～100 partyを
# 同じ物理trainerの通常戦(kind 0/4)へも割り当てていた。通常戦だけをStage34の
# 固定partyへ戻し、kind 5/7の再戦proxyとKanto側の共有trainerは保持する。
STAGE34_TRAINER_TABLE_ADDRESS = 0x092F75C0
STAGE34_TRAINER_COUNT = 1367
TRAINER_TABLE_ADDRESS = 0x09329070
TRAINER_TABLE_COUNT = 4284
TRAINER_RECORD_SIZE = 32
TRAINER_EXACT_TABLE_ADDRESS = 0x09308B08
TRAINER_EXACT_COUNT = 1302
TRAINER_EXACT_ROW_SIZE = 12
TRAINER_SIDECAR_TABLE_ADDRESS = 0x0930C810
TRAINER_SIDECAR_COUNT = 6490
TRAINER_SIDECAR_ROW_SIZE = 18
TRAINER_GIMMICK_TABLE_ADDRESS = 0x09304278
TRAINER_GIMMICK_COUNT = 1302
TRAINER_GIMMICK_ROW_SIZE = 12
TRAINER_REMATCH_TABLE_ADDRESS = 0x093083F0
TRAINER_REMATCH_COUNT = 227
TRAINER_REMATCH_ROW_SIZE = 8
STORY_TRAINER_SHARED_TARGET = 348
STORY_TRAINER_SHARED_CLONE = 1384

# (command data address, target trainer, Stage34 template, trainerbattle kind)
# command data addressはopcode 0x5C直後（runtime exact-binding ABIと同じ）。
STORY_TRAINER_REPAIRS: tuple[tuple[int, int, int, int], ...] = (
    (0x0936D268, 1092, 169, 4),
    (0x0936DA54, 194, 194, 0),
    (0x0936E614, 23, 23, 0),
    (0x0936EC0C, 24, 24, 0),
    (0x0936F62C, 273, 273, 0),
    (0x09370834, 347, 347, 0),
    (0x093708B4, 348, 348, 0),
    (0x093709E0, 354, 354, 0),
    (0x09370C94, 373, 373, 0),
    (0x09370E30, 377, 377, 0),
    (0x09370F04, 380, 380, 0),
    (0x093711C4, 387, 387, 0),
    (0x09372138, 47, 47, 0),
    (0x09372404, 48, 48, 0),
    (0x093725D4, 49, 49, 0),
    (0x09372F4C, 52, 52, 0),
    (0x093733D4, 537, 537, 0),
    (0x09373544, 542, 542, 0),
    (0x09373B40, 577, 577, 0),
    (0x09373BE0, 579, 579, 0),
    (0x09373CE0, 580, 580, 0),
    (0x09373D60, 581, 581, 0),
    (0x09373E44, 1299, 583, 4),
    (0x09373EA8, 585, 585, 0),
    (0x0937457C, 605, 605, 0),
    (0x09374B48, 621, 621, 0),
)

STAGE56_TRAINER_TABLE_SHA256 = (
    "e016cd27f4220966be30954d93d65096a7dd058abd72a4eb2a3d3c3fce7725ae"
)
STAGE34_TRAINER_TABLE_SHA256 = (
    "9ed465ccc77cc70b8db93cad3007bed5dc90be080924e4d21488426afae85b93"
)
STAGE56_TRAINER_EXACT_SHA256 = (
    "fd31baed335ec719d386e49de61c5dddd75ee5acb0745625d3bb8742d3b840f7"
)
STAGE56_TRAINER_SIDECAR_SHA256 = (
    "25a66b403449d3d8a2495c429fbbe3723b234ef05dd9848e623e7c7c5ff8d491"
)
STAGE56_TRAINER_GIMMICK_SHA256 = (
    "4be62114022d64b353d140cdbe095bc963dfa7e36216beeaba0d03ef94990c60"
)
STAGE56_TRAINER_REMATCH_SHA256 = (
    "4adbd332ec24f580d949087b75e94f2211547fe7aece0a3a34c6d2f18c2dc0c4"
)
STAGE56_TRAINER_KIND57_EXACT_SHA256 = (
    "b39e5e5022f0573ca0634b3a4f80d92e2822aff138fd9d2bb7d313af07d692bd"
)
STAGE57_STORY_TRAINER_TABLE_SHA256 = (
    "bf886961e9afc22682a3b50bfcbe8ef9629a3d51ac34a128c585b7eee43fdc40"
)
STAGE57_STORY_TRAINER_EXACT_SHA256 = (
    "be1080cf81630a1071f805a60d0d73174695d823a04aae4e9d34ee2ba20e8245"
)
STAGE57_STORY_TRAINER_SIDECAR_SHA256 = (
    "5ae7dac1293eb32de21d691f873621acf30cc5e7bf32d0869c1257b8c055a0a2"
)
STAGE57_STORY_TRAINER_GIMMICK_SHA256 = (
    "5f86b0151af5b7dc42a8294a262563a3ade054ca7f36c2a6c100d7fc1c612a72"
)


class Stage57DebugError(RuntimeError):
    """Stage57 debug contract違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage57DebugError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _offset(address: int, size: int = 1) -> int:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"ROM address範囲外: 0x{address:08X}+{size}")
    return offset


def _qol_tables() -> tuple[bytes, bytes, Mapping[str, Any]]:
    model = _load_model()
    research = b"".join(
        struct.pack(
            "<BBH8B",
            int(row["group"]), int(row["map"]), int(row["species"]),
            int(row["level_min"]), int(row["level_max"]), int(row["iv_floor"]),
            int(row["hidden_ability_rate"]), int(row["held_item_rate"]),
            int(row["shiny_rolls"]), int(row["unlock"]),
            int(row["normal_preserved"]),
        )
        for row in model["research"]
    )
    field_pc = b"".join(
        struct.pack("<BB", int(row["group"]), int(row["map"]))
        for row in model["field_maps"]
    )
    if len(research) != RESEARCH_RULE_COUNT * RESEARCH_RULE_SIZE:
        _fail("現行research table row数不一致")
    if len(field_pc) != FIELD_PC_MAP_COUNT * FIELD_PC_ROW_SIZE:
        _fail("現行Field PC table row数不一致")
    return research, field_pc, model


def canonical_qol_tables() -> tuple[bytes, bytes]:
    """builderが利用する現行binding由来の正規table bytes。"""
    research, field_pc, _ = _qol_tables()
    return research, field_pc


def _expect(raw: bytes, address: int, expected: bytes, label: str) -> None:
    start = _offset(address, len(expected))
    actual = raw[start:start + len(expected)]
    if actual != expected:
        _fail(
            f"{label} byte不一致@0x{address:08X}: "
            f"{actual.hex()} != {expected.hex()}"
        )


def _table_bytes(raw: bytes, address: int, count: int, row_size: int) -> bytes:
    start = _offset(address, count * row_size)
    return raw[start:start + count * row_size]


def _trainer_row(raw: bytes, address: int, trainer_id: int) -> bytes:
    if not 0 <= trainer_id < TRAINER_TABLE_COUNT:
        _fail(f"trainer ID範囲外: {trainer_id}")
    start = _offset(address + trainer_id * TRAINER_RECORD_SIZE,
                    TRAINER_RECORD_SIZE)
    return raw[start:start + TRAINER_RECORD_SIZE]


def _trainer_levels(raw: bytes, record: bytes, label: str) -> list[int]:
    if len(record) != TRAINER_RECORD_SIZE:
        _fail(f"{label}: trainer record size不一致")
    flags = record[0]
    size = record[0x18]
    pointer = struct.unpack_from("<I", record, 0x1C)[0]
    if flags & ~3 or not 1 <= size <= 6:
        _fail(f"{label}: party flags/size不正 flags={flags} size={size}")
    stride = 16 if flags & 1 else 8
    start = _offset(pointer, size * stride)
    levels = [
        struct.unpack_from("<H", raw, start + slot * stride + 2)[0]
        for slot in range(size)
    ]
    if any(not 1 <= level <= 100 for level in levels):
        _fail(f"{label}: party level不正 {levels}")
    return levels


def _exact_rows(raw: bytes) -> list[tuple[int, tuple[int, int, int, int, int, int], bytes]]:
    table = _table_bytes(
        raw, TRAINER_EXACT_TABLE_ADDRESS, TRAINER_EXACT_COUNT,
        TRAINER_EXACT_ROW_SIZE,
    )
    return [
        (
            index,
            struct.unpack_from("<IHHBBH", table, index * TRAINER_EXACT_ROW_SIZE),
            table[index * TRAINER_EXACT_ROW_SIZE:
                  (index + 1) * TRAINER_EXACT_ROW_SIZE],
        )
        for index in range(TRAINER_EXACT_COUNT)
    ]


def _sidecar_rows(
    raw: bytes, trainer_id: int,
) -> list[tuple[int, tuple[int, ...], bytes]]:
    table = _table_bytes(
        raw, TRAINER_SIDECAR_TABLE_ADDRESS, TRAINER_SIDECAR_COUNT,
        TRAINER_SIDECAR_ROW_SIZE,
    )
    result: list[tuple[int, tuple[int, ...], bytes]] = []
    for index in range(TRAINER_SIDECAR_COUNT):
        start = index * TRAINER_SIDECAR_ROW_SIZE
        row = table[start:start + TRAINER_SIDECAR_ROW_SIZE]
        values = struct.unpack("<HHH12B", row)
        if values[0] == trainer_id:
            result.append((index, values, row))
    return result


def _gimmick_rows(
    raw: bytes, trainer_id: int,
) -> list[tuple[int, tuple[int, ...], bytes]]:
    table = _table_bytes(
        raw, TRAINER_GIMMICK_TABLE_ADDRESS, TRAINER_GIMMICK_COUNT,
        TRAINER_GIMMICK_ROW_SIZE,
    )
    result: list[tuple[int, tuple[int, ...], bytes]] = []
    for index in range(TRAINER_GIMMICK_COUNT):
        start = index * TRAINER_GIMMICK_ROW_SIZE
        row = table[start:start + TRAINER_GIMMICK_ROW_SIZE]
        values = struct.unpack("<HH8B", row)
        if values[0] == trainer_id:
            result.append((index, values, row))
    return result


def _kind57_exact_sha(raw: bytes) -> tuple[int, str]:
    rows = [row for _, values, row in _exact_rows(raw) if values[3] in (5, 7)]
    return len(rows), _sha(b"".join(rows))


def story_trainer_repair_plan(raw: bytes) -> dict[str, Any]:
    """Stage56 high-level leakageをfail-closedでpatch planへ変換する。"""
    baseline_tables = (
        (STAGE34_TRAINER_TABLE_ADDRESS, STAGE34_TRAINER_COUNT,
         TRAINER_RECORD_SIZE, STAGE34_TRAINER_TABLE_SHA256, "Stage34 trainer"),
        (TRAINER_TABLE_ADDRESS, TRAINER_TABLE_COUNT, TRAINER_RECORD_SIZE,
         STAGE56_TRAINER_TABLE_SHA256, "Stage56 trainer"),
        (TRAINER_EXACT_TABLE_ADDRESS, TRAINER_EXACT_COUNT,
         TRAINER_EXACT_ROW_SIZE, STAGE56_TRAINER_EXACT_SHA256, "exact binding"),
        (TRAINER_SIDECAR_TABLE_ADDRESS, TRAINER_SIDECAR_COUNT,
         TRAINER_SIDECAR_ROW_SIZE, STAGE56_TRAINER_SIDECAR_SHA256, "sidecar"),
        (TRAINER_GIMMICK_TABLE_ADDRESS, TRAINER_GIMMICK_COUNT,
         TRAINER_GIMMICK_ROW_SIZE, STAGE56_TRAINER_GIMMICK_SHA256, "gimmick"),
        (TRAINER_REMATCH_TABLE_ADDRESS, TRAINER_REMATCH_COUNT,
         TRAINER_REMATCH_ROW_SIZE, STAGE56_TRAINER_REMATCH_SHA256, "rematch"),
    )
    for address, count, size, digest, label in baseline_tables:
        if _sha(_table_bytes(raw, address, count, size)) != digest:
            _fail(f"{label} table baseline SHA-256不一致")
    kind57_count, kind57_sha = _kind57_exact_sha(raw)
    if (kind57_count, kind57_sha) != (227, STAGE56_TRAINER_KIND57_EXACT_SHA256):
        _fail("kind 5/7 exact binding baseline不一致")

    exact = _exact_rows(raw)
    patches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for command, target, template, kind in STORY_TRAINER_REPAIRS:
        matches = [
            (index, values, row) for index, values, row in exact
            if values[:4] == (command, target, target, kind)
            and values[4:] == (1, 0)
        ]
        if len(matches) != 1:
            _fail(
                f"story trainer exact binding不一致 target={target}: {len(matches)}"
            )
        exact_index, _, exact_raw = matches[0]
        source = _trainer_row(raw, STAGE34_TRAINER_TABLE_ADDRESS, template)
        current = _trainer_row(raw, TRAINER_TABLE_ADDRESS, target)
        source_levels = _trainer_levels(raw, source, f"Stage34 trainer {template}")
        current_levels = _trainer_levels(raw, current, f"Stage56 trainer {target}")
        if max(source_levels) > 45 or min(current_levels) < 80:
            _fail(
                f"story trainer level predicate不一致 target={target}: "
                f"source={source_levels} current={current_levels}"
            )
        row_audit: dict[str, Any] = {
            "command_data_address": command,
            "exact_index": exact_index,
            "target_trainer_id": target,
            "template_trainer_id": template,
            "kind": kind,
            "before_levels": current_levels,
            "after_levels": source_levels,
        }
        if target == STORY_TRAINER_SHARED_TARGET:
            clone = _trainer_row(raw, TRAINER_TABLE_ADDRESS,
                                 STORY_TRAINER_SHARED_CLONE)
            if clone != bytes(TRAINER_RECORD_SIZE):
                _fail("story trainer clone ID 1384が空ではありません")
            patches.append({
                "name": "story_initial_shared_exact_target_348_to_1384",
                "kind": "story_trainer_exact_split",
                "address": (TRAINER_EXACT_TABLE_ADDRESS
                            + exact_index * TRAINER_EXACT_ROW_SIZE + 6),
                "expected": struct.pack("<H", target),
                "replacement": struct.pack("<H", STORY_TRAINER_SHARED_CLONE),
            })
            patches.append({
                "name": "story_initial_clone_1384_from_stage34_348",
                "kind": "story_trainer_record_clone",
                "address": (TRAINER_TABLE_ADDRESS
                            + STORY_TRAINER_SHARED_CLONE * TRAINER_RECORD_SIZE),
                "expected": clone,
                "replacement": source,
            })
            row_audit.update({
                "runtime_trainer_id": STORY_TRAINER_SHARED_CLONE,
                "shared_target_preserved": True,
            })
        else:
            patches.append({
                "name": f"story_initial_trainer_record_{target:04d}",
                "kind": "story_trainer_record_restore",
                "address": TRAINER_TABLE_ADDRESS + target * TRAINER_RECORD_SIZE,
                "expected": current,
                "replacement": source,
            })
            sidecars = _sidecar_rows(raw, target)
            if (len(sidecars) != 6
                    or [(values[3], values[4]) for _, values, _ in sidecars]
                    != [(1, slot) for slot in range(6)]
                    or any(values[1] == 0 for _, values, _ in sidecars)):
                _fail(f"story trainer sidecar inventory不一致 target={target}")
            for sidecar_index, _, sidecar_raw in sidecars:
                patches.append({
                    "name": (
                        f"story_initial_sidecar_{target:04d}_"
                        f"{sidecar_index:04d}"
                    ),
                    "kind": "story_trainer_sidecar_disable",
                    "address": (TRAINER_SIDECAR_TABLE_ADDRESS
                                + sidecar_index * TRAINER_SIDECAR_ROW_SIZE + 2),
                    "expected": sidecar_raw[2:6],
                    "replacement": bytes(4),
                })
            gimmicks = _gimmick_rows(raw, target)
            if (len(gimmicks) != 1 or gimmicks[0][1][1] != 0
                    or gimmicks[0][1][3] != 5):
                _fail(f"story trainer gimmick inventory不一致 target={target}")
            gimmick_index, _, gimmick_raw = gimmicks[0]
            patches.append({
                "name": f"story_initial_gimmick_ai_{target:04d}",
                "kind": "story_trainer_gimmick_disable",
                "address": (TRAINER_GIMMICK_TABLE_ADDRESS
                            + gimmick_index * TRAINER_GIMMICK_ROW_SIZE + 5),
                "expected": gimmick_raw[5:6],
                "replacement": b"\x00",
            })
            row_audit.update({
                "runtime_trainer_id": target,
                "sidecar_rows_disabled": 6,
                "gimmick_ai_disabled": True,
            })
        rows.append(row_audit)
    if len(patches) != 202:
        _fail(f"story trainer patch count不一致: {len(patches)}")
    changed_bytes = sum(
        sum(old != new for old, new in zip(
            row["expected"], row["replacement"], strict=True))
        for row in patches
    )
    if changed_bytes != 579:
        _fail(f"story trainer changed byte count不一致: {changed_bytes}")
    return {
        "status": "PASS",
        "repair_count": len(rows),
        "record_restore_count": 25,
        "shared_clone_count": 1,
        "sidecar_disable_count": 150,
        "gimmick_disable_count": 25,
        "patch_count": len(patches),
        "changed_byte_count": changed_bytes,
        "rows": rows,
        "patches": patches,
    }


def story_trainer_audit(raw: bytes) -> dict[str, Any]:
    """Stage57上で通常戦低レベル化と再戦/Kanto保持を直接検査する。"""
    if _sha(_table_bytes(
            raw, STAGE34_TRAINER_TABLE_ADDRESS, STAGE34_TRAINER_COUNT,
            TRAINER_RECORD_SIZE)) != STAGE34_TRAINER_TABLE_SHA256:
        _fail("Stage57内Stage34 trainer source tableが変化しています")
    if _sha(_table_bytes(
            raw, TRAINER_REMATCH_TABLE_ADDRESS, TRAINER_REMATCH_COUNT,
            TRAINER_REMATCH_ROW_SIZE)) != STAGE56_TRAINER_REMATCH_SHA256:
        _fail("Stage57 rematch tableが変化しています")
    kind57_count, kind57_sha = _kind57_exact_sha(raw)
    if (kind57_count, kind57_sha) != (227, STAGE56_TRAINER_KIND57_EXACT_SHA256):
        _fail("Stage57 kind 5/7 exact bindingが変化しています")

    exact = _exact_rows(raw)
    rows: list[dict[str, Any]] = []
    for command, target, template, kind in STORY_TRAINER_REPAIRS:
        runtime_target = (
            STORY_TRAINER_SHARED_CLONE
            if target == STORY_TRAINER_SHARED_TARGET else target
        )
        matches = [
            (index, values) for index, values, _ in exact
            if values[:2] == (command, target) and values[2] == runtime_target
            and values[3:] == (kind, 1, 0)
        ]
        if len(matches) != 1:
            _fail(f"Stage57 story exact binding不一致 target={target}")
        expected = _trainer_row(raw, STAGE34_TRAINER_TABLE_ADDRESS, template)
        actual = _trainer_row(raw, TRAINER_TABLE_ADDRESS, runtime_target)
        if actual != expected:
            _fail(f"Stage57 story trainer record不一致 target={target}")
        levels = _trainer_levels(raw, actual, f"Stage57 story trainer {target}")
        if max(levels) > 45:
            _fail(f"Stage57 story trainer level leakage target={target}: {levels}")
        if target == STORY_TRAINER_SHARED_TARGET:
            preserved = _trainer_levels(
                raw, _trainer_row(raw, TRAINER_TABLE_ADDRESS, target),
                "Stage57 Kanto shared trainer 348",
            )
            if min(preserved) < 80:
                _fail("Kanto共有trainer348の高難度partyが失われています")
        else:
            sidecars = _sidecar_rows(raw, target)
            if (len(sidecars) != 6
                    or any(values[1] != 0 or values[2] != 0
                           for _, values, _ in sidecars)):
                _fail(f"Stage57 story sidecarが有効なままです target={target}")
            gimmicks = _gimmick_rows(raw, target)
            if len(gimmicks) != 1 or gimmicks[0][1][3] != 0:
                _fail(f"Stage57 story gimmickが有効なままです target={target}")
        rows.append({
            "command_data_address": command,
            "source_trainer_id": target,
            "runtime_trainer_id": runtime_target,
            "template_trainer_id": template,
            "kind": kind,
            "levels": levels,
        })
    table_sha256 = {
        "trainer": _sha(_table_bytes(
            raw, TRAINER_TABLE_ADDRESS, TRAINER_TABLE_COUNT,
            TRAINER_RECORD_SIZE)),
        "exact": _sha(_table_bytes(
            raw, TRAINER_EXACT_TABLE_ADDRESS, TRAINER_EXACT_COUNT,
            TRAINER_EXACT_ROW_SIZE)),
        "sidecar": _sha(_table_bytes(
            raw, TRAINER_SIDECAR_TABLE_ADDRESS, TRAINER_SIDECAR_COUNT,
            TRAINER_SIDECAR_ROW_SIZE)),
        "gimmick": _sha(_table_bytes(
            raw, TRAINER_GIMMICK_TABLE_ADDRESS, TRAINER_GIMMICK_COUNT,
            TRAINER_GIMMICK_ROW_SIZE)),
    }
    expected_table_sha256 = {
        "trainer": STAGE57_STORY_TRAINER_TABLE_SHA256,
        "exact": STAGE57_STORY_TRAINER_EXACT_SHA256,
        "sidecar": STAGE57_STORY_TRAINER_SIDECAR_SHA256,
        "gimmick": STAGE57_STORY_TRAINER_GIMMICK_SHA256,
    }
    if table_sha256 != expected_table_sha256:
        _fail(f"Stage57 story trainer table SHA不一致: {table_sha256}")
    return {
        "status": "PASS",
        "active_command_count": len(rows),
        "level_80_or_higher_count": 0,
        "restored_record_count": 25,
        "shared_clone_count": 1,
        "disabled_sidecar_count": 150,
        "disabled_gimmick_count": 25,
        "rematch_exact_count": kind57_count,
        "rematch_exact_sha256": kind57_sha,
        "rematch_table_sha256": STAGE56_TRAINER_REMATCH_SHA256,
        "kanto_shared_target": STORY_TRAINER_SHARED_TARGET,
        "kanto_shared_minimum_level": min(_trainer_levels(
            raw, _trainer_row(raw, TRAINER_TABLE_ADDRESS,
                              STORY_TRAINER_SHARED_TARGET),
            "Stage57 Kanto shared trainer 348",
        )),
        "rows": rows,
        "table_sha256": table_sha256,
    }


def quick_audit(
    raw: bytes,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    if len(raw) != ROM_SIZE:
        _fail(f"ROM size不一致: {len(raw)}")
    if metadata is not None:
        expected_hash = str(metadata.get("output", {}).get("sha256", ""))
        if expected_hash and _sha(raw) != expected_hash:
            _fail("metadataとROMのSHA-256不一致")

    research, field_pc, model = _qol_tables()
    _expect(raw, RESEARCH_TABLE_ADDRESS, research, "research binding table")
    _expect(raw, FIELD_PC_TABLE_ADDRESS, field_pc, "Field PC binding table")
    for name, address, _ in MENU_CALLSITES:
        _expect(raw, address, MENU_BASE_INSTRUCTIONS, f"menu tile base::{name}")
    for name, address, _, replacement in NPC_POINTER_REPAIRS:
        _expect(raw, address, struct.pack("<I", replacement), f"NPC::{name}")
    for name, address, _, replacement in CONTROL_FLOW_REPAIRS:
        _expect(raw, address, struct.pack("<I", replacement), f"flow::{name}")
    story_trainers = story_trainer_audit(raw)

    route_species = tuple(sorted(
        int(row["species"])
        for row in model["research"]
        if (int(row["group"]), int(row["map"])) == ROUTE_505
    ))
    if route_species != ROUTE_505_RESEARCH_SPECIES:
        _fail(f"505番道路research species不一致: {route_species}")
    leaked = sorted(set(route_species) & ROUTE_505_FORBIDDEN_SPECIES)
    if leaked:
        _fail(f"505番道路へ禁止speciesが流入: {leaked}")

    runtime_checks: dict[str, Any] = {"metadata_available": metadata is not None}
    if metadata is not None:
        patches = metadata.get("patches", {})
        for group_name, expected_count in (
            ("species_calls", len(SPECIES_SET_CALLSITES)),
            ("wild_hook", 1),
            ("factory_cursor", 1),
        ):
            rows = patches.get(group_name, [])
            if not isinstance(rows, list) or len(rows) != expected_count:
                _fail(f"metadata patch inventory不一致: {group_name}")
            for row in rows:
                _expect(
                    raw, int(row["address"]), bytes.fromhex(str(row["replacement_hex"])),
                    f"runtime patch::{row['name']}",
                )
        payload = metadata.get("runtime", {}).get("payload", {})
        start = int(payload.get("offset", -1))
        size = int(payload.get("size", 0))
        if start < 0 or size <= 0 or _sha(raw[start:start + size]) != payload.get("sha256"):
            _fail("Stage57 runtime payload identity不一致")
        bg_script = int(metadata.get("runtime", {}).get("bg_safe_script", 0))
        if not bg_script:
            _fail("BG safe script metadata不足")
        _expect(
            raw, BROKEN_BG_TERMINAL[1], bytes((0x05,)) + struct.pack("<I", bg_script),
            BROKEN_BG_TERMINAL[0],
        )
        runtime_checks.update({"payload": True, "species_calls": True,
                               "wild_hook": True, "factory_cursor": True,
                               "bg_safe_script": True})

    return {
        "status": "PASS",
        "rom_sha256": _sha(raw),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "checks": {
            "research_rules": RESEARCH_RULE_COUNT,
            "field_pc_maps": FIELD_PC_MAP_COUNT,
            "menu_callsites": len(MENU_CALLSITES),
            "npc_pointer_repairs": len(NPC_POINTER_REPAIRS),
            "control_flow_repairs": len(CONTROL_FLOW_REPAIRS),
            "route_505_research_species": list(route_species),
            "route_505_forbidden_species": [],
            "runtime": runtime_checks,
            "story_trainers": story_trainers,
        },
        "table_sha256": {
            "research": _sha(research),
            "field_pc": _sha(field_pc),
        },
    }


def _group_coordinates(rom: RomImage) -> list[tuple[int, int]]:
    del rom  # inventory正本とimport catalogから座標を決定する。
    inventory = json.loads(
        (ROOT / "reports/generated/id_inventory.json").read_text(encoding="utf-8")
    )
    coordinates = _coordinates(ROOT, inventory["map_contract"]["group_sizes"])
    if len(coordinates) != 678:
        _fail(f"physical map数不一致: {len(coordinates)}")
    return coordinates


def _collect_contactable_roots(rom: RomImage) -> tuple[list[ScriptRoot], Counter[str]]:
    roots: list[ScriptRoot] = []
    counts: Counter[str] = Counter()
    groups_address = rom.u32(MAP_GROUPS_POINTER_SITE)
    coordinates = _group_coordinates(rom)
    group_count = max(group for group, _ in coordinates) + 1
    group_pointers = [rom.u32(groups_address + index * 4) for index in range(group_count)]
    for group, number in coordinates:
        header = rom.u32(group_pointers[group] + number * 4)
        layout = rom.u32(header)
        width, height = rom.s32(layout), rom.s32(layout + 4)
        events = rom.u32(header + 4)
        map_scripts = rom.u32(header + 8)
        label = f"map:{group}:{number}"
        if events and rom.raw(events, 4) != b"\xFF" * 4:
            amounts = rom.raw(events, 4)
            pointers = [rom.u32(events + 4 + index * 4) for index in range(4)]
            for index in range(amounts[0]):
                at = pointers[0] + index * 0x18
                kind = rom.u8(at + 2)
                x, y = rom.s16(at + 4), rom.s16(at + 6)
                script = rom.u32(at + 0x10)
                if kind == 0 and 0 <= x < width and 0 <= y < height and script:
                    roots.append(ScriptRoot(script, f"{label}:object:{index}", "object"))
                    counts["object"] += 1
            for index in range(amounts[2]):
                at = pointers[2] + index * 0x10
                x, y = rom.u16(at), rom.u16(at + 2)
                script = rom.u32(at + 0x0C)
                if 0 <= x < width and 0 <= y < height and script:
                    roots.append(ScriptRoot(script, f"{label}:coord:{index}", "coord"))
                    counts["coord"] += 1
            for index in range(amounts[3]):
                at = pointers[3] + index * 0x0C
                x, y = rom.u16(at), rom.u16(at + 2)
                kind = rom.u8(at + 5)
                script = rom.u32(at + 8)
                if (0 <= x < width and 0 <= y < height and kind not in (7, 8)
                        and script):
                    roots.append(ScriptRoot(script, f"{label}:bg:{index}", "bg"))
                    counts["bg"] += 1
        if map_scripts:
            script_roots, _, _ = _decode_map_scripts(rom, map_scripts, label)
            roots.extend(script_roots)
            counts["map_script"] += len(script_roots)
    return roots, counts


def full_audit(
    raw: bytes,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    quick = quick_audit(raw, metadata=metadata)
    rom = RomImage("Stage57", raw)
    roots, counts = _collect_contactable_roots(rom)
    if dict(counts) != EXPECTED_ROOT_COUNTS:
        _fail(f"contactable root inventory drift: {dict(counts)}")
    walker = ScriptWalker(rom)
    for root in roots:
        walker.add_root(root)
    graph = walker.walk()
    if graph["diagnostics"]:
        _fail(
            "event CFG diagnostics残存: "
            + json.dumps(graph["diagnostics"][:8], ensure_ascii=False, sort_keys=True)
        )
    from scripts.build_interaction_ownership_repair import (  # noqa: PLC0415
        _wild_audit,
    )
    inventory = json.loads(
        (ROOT / "reports/generated/id_inventory.json").read_text(encoding="utf-8")
    )
    wild = _wild_audit(raw, inventory["map_contract"]["group_sizes"])
    collection = json.loads(
        (ROOT / "content/collection_supply_v1/canonical_model.json").read_text(
            encoding="utf-8"
        )
    )
    wild_form_indices = [int(value) for value in collection["wild_form_indices"]]
    forms = collection["forms"]
    if len(wild_form_indices) != 78 or any(
        not 1 <= int(forms[index][field]) <= 1620
        for index in wild_form_indices for field in ("base_species", "target_species")
    ):
        _fail("Collection wild form Species range不一致")
    native_slots = (
        int(wild["mode_tables"]["land"]) * 12
        + int(wild["mode_tables"]["water"]) * 5
        + int(wild["mode_tables"]["rock"]) * 5
        + int(wild["mode_tables"]["fishing"]) * 10
    )
    from tools.stage57_story_trainer_audit import (  # noqa: PLC0415
        audit_story_trainers,
    )
    story = audit_story_trainers(raw, expected_rom_sha256=_sha(raw))
    story.pop("elapsed_seconds", None)
    return {
        "status": "PASS",
        "rom_sha256": _sha(raw),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "quick": quick,
        "script_cfg": {
            "physical_maps": 678,
            "root_count": len(roots),
            "root_counts": dict(counts),
            "unique_root_address_count": graph["unique_root_address_count"],
            "visited_script_count": graph["visited_script_count"],
            "diagnostic_count": 0,
        },
        "wild_surface": {
            "status": "PASS",
            "native_headers": int(wild["native_headers"]),
            "unique_coordinate_headers": int(wild["unique_coordinate_headers"]),
            "native_slots_checked": native_slots,
            "mode_tables": wild["mode_tables"],
            "legacy_orphan_headers_classified": len(wild["legacy_orphan_headers"]),
            "qol_research_rules_checked": RESEARCH_RULE_COUNT,
            "collection_wild_forms_checked": len(wild_form_indices),
            "species_range_mismatch_count": 0,
        },
        "story_trainer_surface": story,
    }


def _read_metadata(path: Path | None) -> Mapping[str, Any] | None:
    if path is None:
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail("metadata rootがobjectではありません")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.rom.read_bytes()
        metadata = _read_metadata(args.metadata)
        result = (quick_audit(raw, metadata=metadata) if args.mode == "quick"
                  else full_audit(raw, metadata=metadata))
        document = {
            "schema_version": 1,
            "tool": "stage57_debug_suite",
            "mode": args.mode,
            **result,
        }
        rendered = _stable(document)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, Stage57DebugError) as error:
        print(f"Stage57 debug {args.mode} failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
