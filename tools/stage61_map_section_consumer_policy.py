#!/usr/bin/env python3
"""Stage 61 map-section consumer の恒久修正契約を生成・検証する。

Stage 61 の imported Kanto map header は物理 group 96..98 で project
``regionMapSectionId`` 0..52 を使う。一方、FireRed/CFRU の consumer は source
ID 88..142（または stock table の 87/88 起点）を前提にする。本モジュールは、
consumer ごとの ABI、最小 hook window、Stage 60 exact preimage、文脈付き変換、
非 imported map の保持条件、休眠条件を機械可読 JSON として返す。

このファイルは ROM を変更しない。統合 builder は本契約を読み、candidate ROM
に対して ``verify_candidate_patch_contract`` で exact patch bytes を検証する。
Raid flag の新 base は意図的に固定しない。呼び出し側が collision audit 済み base
を渡し、本モジュールが既知 owner と追加予約範囲に対して fail-closed で検査する。
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Iterable, Mapping, Sequence

try:
    import tools.stage61_map_section_consumer_audit as audit
except ModuleNotFoundError as exc:
    # ``python3 tools/<script>.py`` でも package root を解決できるようにする。
    if exc.name != "tools":
        raise
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import tools.stage61_map_section_consumer_audit as audit


ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x08054B0C
IMPORTED_PHYSICAL_GROUPS = (96, 97, 98)
PROJECT_SECTION_COUNT = 53
PROJECT_SECTION_IDS = tuple(range(PROJECT_SECTION_COUNT))
SOURCE_SECTION_IDS = tuple(range(88, 99)) + tuple(range(101, 143))

MAPSEC_DYNAMIC = 87
MAPSEC_NONE = 197
RAID_SOURCE_MIN = 87
RAID_SOURCE_MAX = 195
RAID_ROW_COUNT = 109
ROAMER_SOURCE_MIN = 88
ROAMER_SOURCE_MAX = 196
ROAMER_LAYOUT_ROW_COUNT = 109

LEGACY_RAID_FLAG_BASE = 0x1800
LEGACY_RAID_FLAG_END = LEGACY_RAID_FLAG_BASE + RAID_ROW_COUNT - 1
EXPANDED_FLAG_MIN = 0x0900
EXPANDED_FLAG_MAX = 0x18FF

STAGE60_ROM_RELATIVE = audit.STAGE60_ROM_RELATIVE
CLEAN_ROM_RELATIVE = audit.CLEAN_ROM_RELATIVE
STAGE60_ROM_SIZE = audit.STAGE60_ROM_SIZE
STAGE60_ROM_SHA256 = audit.STAGE60_ROM_SHA256
CLEAN_ROM_SIZE = audit.CLEAN_ROM_SIZE
CLEAN_ROM_SHA256 = audit.CLEAN_ROM_SHA256

MAP_SECTION_MANIFEST_RELATIVE = Path("content/kanto_map_sections.csv")
IMPORT_CROSSWALK_RELATIVE = Path("reports/generated/kanto_v2_crosswalk.csv")
MAP_GROUPS_RELATIVE = Path("vendor/upstream/pokefirered/data/maps/map_groups.json")
FIELD_SPECIALS_RELATIVE = Path("vendor/upstream/pokefirered/src/field_specials.c")
QUEST_LOG_CONSTANTS_RELATIVE = Path(
    "vendor/upstream/pokefirered/include/constants/quest_log.h"
)
QUEST_LOG_EXIT_MANIFEST_RELATIVE = Path(
    "config/stage61_quest_log_exit_manifest.json"
)
FLAGS_MANIFEST_RELATIVE = Path("manifests/flags.csv")
NAMESPACE_REGISTRY_RELATIVE = Path("config/stage61_namespace_registry.json")
DISPLAY_AUDIT_CONFIG_RELATIVE = Path("config/stage61_display_npc_event_audit.json")
TRAINER_CONSUMERS_RELATIVE = Path(
    "content/trainer_changekit_final/trainer_runtime_consumers.csv"
)

IMPORT_CROSSWALK_SHA256 = (
    "a08b4b5e2dc6918fb3d264cf4f052209e188ee07aef00f1184b8853ef3596cef"
)
MAP_GROUPS_SHA256 = (
    "ce296c9b54c8bb85cc35870b30a533ab017e72107fd40cf471224a42127af79a"
)
FIELD_SPECIALS_SHA256 = (
    "9c49d3702f0f4dcba61ae26bccefce1c26fbd1247475289dd821780bc537d1d9"
)
QUEST_LOG_CONSTANTS_SHA256 = (
    "90cceec5883201c3d3d2bdb420d1f7b3ebef21f4716eef0760bba507559be2dc"
)
IMPORTED_MAP_ID_SECTION_CANONICAL_SHA256 = (
    "01a07ae620c5f4ac23bc73eb9a0dc3a5d571014190cfafb118fb279a239b412d"
)
QUEST_PAIR_CANONICAL_SHA256 = (
    "61d83bbfbee6afd1b80e43b18387c5a634363e0f9acf520f2d0fa61cc8af2296"
)
# Updated together with the reviewed JSON.  Pinning its bytes prevents a valid
# but semantically different warp from silently becoming a Quest Log exit.
QUEST_LOG_EXIT_MANIFEST_SHA256 = (
    "9bc3489aaf1beb49566d2a694b342cfa0cb6d41c333b7c0a3f8677050b678c15"
)

QUEST_LOG_SOURCE_DISABLED_ROWS = (15, 29)
QUEST_LOG_GAME_CORNER_LOCATION = 32
QUEST_LOG_ROCKET_HIDEOUT_LOCATION = 35
QUEST_LOG_SOURCE_CLASSIFICATION_COUNTS = {
    "DIRECT_BI": 16,
    "DIRECT_ONE_WAY": 6,
    "MULTIHOP_BI": 1,
    "TARGET_MISMATCH": 26,
    "INVALID": 2,
}

MAP_NAME_HOOK_ADDRESS = 0x080C5F5C
MAP_NAME_HOOK_STAGE60_PREIMAGE = bytes.fromhex("70b5061c09041204")
MAP_NAME_IMPORTED_UNUSED_COORDS = {
    (98, 101): "Route6_UnusedHouse",
    (98, 118): "Route19_UnusedHouse",
    (98, 120): "Route23_UnusedHouse",
}
MAP_NAME_PHYSICAL_INVENTORY_CANONICAL_SHA256 = (
    "d2bb66a7dad07640650b1b5629cafd886022f6b4ce8c1373eafd30648678d370"
)


class MapSectionConsumerPolicyError(RuntimeError):
    """契約の入力、preimage、ABI 根拠、flag ownership を証明できない。"""


def _hex(value: int) -> str:
    return f"0x{value:08X}" if value >= ROM_BASE else f"0x{value:04X}"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise MapSectionConsumerPolicyError(
            f"{what} を読めません: {path}: {exc}"
        ) from exc


def _read_json(path: Path, what: str) -> Any:
    raw = _read(path, what)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MapSectionConsumerPolicyError(
            f"{what} を JSON として解析できません: {path}: {exc}"
        ) from exc


def _read_csv(path: Path, what: str) -> tuple[bytes, list[dict[str, str]]]:
    raw = _read(path, what)
    try:
        rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise MapSectionConsumerPolicyError(
            f"{what} を CSV として解析できません: {path}: {exc}"
        ) from exc
    return raw, rows


def _assert_sha(raw: bytes, expected: str, what: str) -> None:
    actual = _sha(raw)
    if actual != expected:
        raise MapSectionConsumerPolicyError(
            f"{what} SHA-256 mismatch: expected={expected}, actual={actual}"
        )


def _rom_slice(raw: bytes, address: int, size: int, what: str) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(raw):
        raise MapSectionConsumerPolicyError(
            f"{what} が ROM 範囲外です: {_hex(address)}+{size:#x}, "
            f"ROM size={len(raw):#x}"
        )
    return raw[offset : offset + size]


def _rom_u32(raw: bytes, address: int, what: str) -> int:
    return struct.unpack("<I", _rom_slice(raw, address, 4, what))[0]


def _stage60_map_section(raw: bytes, group: int, number: int) -> int:
    groups = _rom_u32(raw, MAP_GROUPS_POINTER_SITE, "Stage60 gMapGroups")
    group_table = _rom_u32(
        raw, groups + group * 4, f"Stage60 map group {group}"
    )
    header = _rom_u32(
        raw, group_table + number * 4, f"Stage60 map header {group}/{number}"
    )
    return _rom_slice(
        raw, header + 0x14, 1, f"Stage60 map section {group}/{number}"
    )[0]


@dataclass(frozen=True)
class PatchWindow:
    site_id: str
    consumer_id: str
    owner_function: str
    address: int
    expected: bytes
    write_size: int
    patch_kind: str
    replacement_symbol: str
    install_condition: str = "REQUIRED"
    resume_addresses: tuple[int, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        if self.write_size <= 0 or self.write_size > len(self.expected):
            raise ValueError(f"invalid write_size for {self.site_id}")

    def to_report(self) -> dict[str, Any]:
        return {
            "site_id": self.site_id,
            "consumer_id": self.consumer_id,
            "owner_function": self.owner_function,
            "address": _hex(self.address),
            "assert_size": len(self.expected),
            "expected_stage60_hex": self.expected.hex(),
            "write_size": self.write_size,
            "patch_kind": self.patch_kind,
            "replacement_symbol": self.replacement_symbol,
            "install_condition": self.install_condition,
            "resume_addresses": [_hex(value) for value in self.resume_addresses],
            "note": self.note,
        }


@dataclass(frozen=True)
class FunctionExtent:
    extent_id: str
    consumer_ids: tuple[str, ...]
    function: str
    start: int
    end_exclusive: int
    sha256: str
    role: str = "PATCH_OWNER"

    def to_report(self) -> dict[str, Any]:
        return {
            "extent_id": self.extent_id,
            "consumer_ids": list(self.consumer_ids),
            "function": self.function,
            "start": _hex(self.start),
            "end_exclusive": _hex(self.end_exclusive),
            "size": self.end_exclusive - self.start,
            "stage60_sha256": self.sha256,
            "role": self.role,
        }


@dataclass(frozen=True)
class DataExtent:
    extent_id: str
    consumer_ids: tuple[str, ...]
    name: str
    address: int
    size: int
    sha256: str

    def to_report(self) -> dict[str, Any]:
        return {
            "extent_id": self.extent_id,
            "consumer_ids": list(self.consumer_ids),
            "name": self.name,
            "address": _hex(self.address),
            "size": self.size,
            "stage60_sha256": self.sha256,
        }


def _entry(
    site_id: str,
    consumer_id: str,
    owner_function: str,
    address: int,
    expected_hex: str,
    replacement_symbol: str,
    *,
    install_condition: str = "REQUIRED",
    note: str = "",
) -> PatchWindow:
    return PatchWindow(
        site_id,
        consumer_id,
        owner_function,
        address,
        bytes.fromhex(expected_hex),
        8,
        "THUMB_ABSOLUTE_JUMP_WHOLE_FUNCTION",
        replacement_symbol,
        install_condition,
        (),
        note,
    )


PATCH_WINDOWS: tuple[PatchWindow, ...] = (
    _entry(
        "msc04_music_entry",
        "MSC-04",
        "Overworld_MusicCanOverrideMapMusic",
        0x080559E4,
        "00b50004010c8d20",
        "Stage61MapSection_MusicCanOverrideMapMusic",
    ),
    _entry(
        "msc05_preview_index_entry",
        "MSC-05",
        "GetMapPreviewScreenIdx",
        0x080F9150,
        "00b50006030e0021",
        "Stage61MapSection_GetMapPreviewScreenIdx",
    ),
    _entry(
        "msc05_stock_warp_fade_entry",
        "MSC-05",
        "WarpFadeOutScreen",
        0x0807D378,
        "10b5d7f7c9fb041c",
        "Stage61MapSection_WarpFadeOutScreen",
        note="destination と current の双方を物理 group 文脈で canonical 化する",
    ),
    _entry(
        "msc06_dungeon_flavor_entry",
        "MSC-06",
        "GetDungeonFlavorText",
        0x080C2AC4,
        "30b50004040c0022",
        "Stage61MapSection_GetDungeonFlavorText",
    ),
    _entry(
        "msc06_dungeon_name_entry",
        "MSC-06",
        "GetDungeonName",
        0x080C2B04,
        "30b50004040c0022",
        "Stage61MapSection_GetDungeonName",
    ),
    _entry(
        "msc06_dungeon_preview_info_entry",
        "MSC-06",
        "GetDungeonMapPreviewScreenInfo",
        0x080F95B0,
        "00b50006000efff7",
        "Stage61MapSection_GetDungeonMapPreviewScreenInfo",
        install_condition="OPTIONAL_DIRECT_PATCH_IF_SHARED_PREVIEW_NORMALIZER_IS_NOT_USED",
        note="通常は patched GetMapPreviewScreenIdx を経由するため直接 hook 不要",
    ),
    _entry(
        "msc07_dungeon_cursor_entry",
        "MSC-07",
        "GetDungeonMapsecUnderCursor",
        0x080C4764,
        "10b5064c21684888",
        "Stage61MapSection_GetDungeonMapsecUnderCursor",
    ),
    PatchWindow(
        "msc07_dungeon_icon_gate",
        "MSC-07",
        "CreateDungeonIcons",
        0x080C5A14,
        bytes.fromhex("8d2805d11f48a8f753fa"),
        8,
        "THUMB_ABSOLUTE_JUMP_INTERNAL_CONTINUATION",
        "Stage61MapSection_CreateDungeonIconsCeruleanGate",
        "REQUIRED",
        (0x080C5A1E, 0x080C5A24, 0x080C5A68),
        "10-byte instruction-boundary preimage を assert し、先頭8 byteだけを書く",
    ),
    _entry(
        "msc10_summary_classifier_entry",
        "MSC-10",
        "MapSecIsInKantoOrSevii",
        0x0813BFFC,
        "00b50006a8210906",
        "Stage61MapSection_IsKantoOrSeviiForMemo",
    ),
    _entry(
        "msc11_wild_header_mapsec_entry",
        "MSC-11",
        "GetMapSecIdFromWildMonHeader",
        0x0813D388,
        "00b502784178101c",
        "Stage61MapSection_GetWildHeaderMapSection",
    ),
    PatchWindow(
        "msc15_quest_log_gym_compare",
        "MSC-15",
        "LoadEvent_DepartedLocation",
        0x08115DC8,
        bytes.fromhex("2978a01800788142"),
        8,
        "THUMB_ABSOLUTE_JUMP_INTERNAL_CONTINUATION",
        "Stage61MapSection_QuestLogGymCompare",
        "REQUIRED",
        (0x08115DD0,),
        "r1 project gym section を source 化し、4命令を再生して bne@0x08115DD0へ戻す",
    ),
    PatchWindow(
        "msc16_quest_log_teleport_home",
        "MSC-16",
        "LoadEvent_UsedFieldMove",
        0x08115F64,
        bytes.fromhex("687858280cd10448"),
        8,
        "THUMB_ABSOLUTE_JUMP_INTERNAL_BRANCH",
        "Stage61MapSection_QuestLogTeleportHome",
        "REQUIRED",
        (0x08115F6C, 0x08115F84),
        "project Pallet=0 と stock Pallet=88 を home branch とする",
    ),
    _entry(
        "msc17_check_departing_entry",
        "MSC-17",
        "QuestLog_CheckDepartingIndoorsMap",
        0x080CD6AC,
        "70b50024104e114d",
        "Stage61MapSection_QuestLog_CheckDepartingIndoorsMap",
    ),
    _entry(
        "msc17_record_departed_entry",
        "MSC-17",
        "QuestLog_TryRecordDepartedLocation",
        0x080CD714,
        "f0b582b01548a0f7",
        "Stage61MapSection_QuestLog_TryRecordDepartedLocation",
    ),
    PatchWindow(
        "msc21_raid_getter_determine",
        "MSC-21",
        "DetermineRaidSpecies literal pool",
        0x090F3838,
        bytes.fromhex("215b0508"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_GetRaidCompatibleCurrent",
    ),
    PatchWindow(
        "msc21_raid_getter_ability",
        "MSC-21",
        "GetRaidSpeciesAbilityNum literal pool",
        0x090F3A90,
        bytes.fromhex("215b0508"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_GetRaidCompatibleCurrent",
    ),
    PatchWindow(
        "msc21_raid_getter_done",
        "MSC-21",
        "HasRaidBattleAlreadyBeenDone literal pool",
        0x090F3AE8,
        bytes.fromhex("215b0508"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_GetRaidCompatibleCurrent",
    ),
    PatchWindow(
        "msc21_raid_getter_set",
        "MSC-21",
        "sp119_SetRaidBattleFlag literal pool",
        0x090F3B10,
        bytes.fromhex("215b0508"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_GetRaidCompatibleCurrent",
    ),
    PatchWindow(
        "msc21_raid_getter_clear",
        "MSC-21",
        "sp11A_ClearRaidBattleFlag literal pool",
        0x090F3B90,
        bytes.fromhex("215b0508"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_GetRaidCompatibleCurrent",
    ),
    PatchWindow(
        "msc21_raid_getter_rewards",
        "MSC-21",
        "sp11C_GiveRaidBattleRewards literal pool",
        0x090F3FC0,
        bytes.fromhex("215b0508"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_GetRaidCompatibleCurrent",
    ),
    PatchWindow(
        "msc21_raid_flag_get_done",
        "MSC-21",
        "HasRaidBattleAlreadyBeenDone FlagGet literal",
        0x090F3AEC,
        bytes.fromhex("c5de0608"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_RaidFlagGet",
    ),
    PatchWindow(
        "msc21_raid_flag_set",
        "MSC-21",
        "sp119_SetRaidBattleFlag FlagSet literal",
        0x090F3B14,
        bytes.fromhex("75de0608"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_RaidFlagSet",
    ),
    PatchWindow(
        "msc21_raid_flag_clear_all",
        "MSC-21",
        "ClearAllRaidBattleFlags FlagClear literal",
        0x090F3B34,
        bytes.fromhex("9dde0608"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_RaidFlagClear",
    ),
    PatchWindow(
        "msc21_raid_flag_clear_current",
        "MSC-21",
        "sp11A_ClearRaidBattleFlag FlagClear literal",
        0x090F3B88,
        bytes.fromhex("9dde0608"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_RaidFlagClear",
    ),
    PatchWindow(
        "msc21_raid_flag_get_all",
        "MSC-21",
        "sp11B_AllRaidBattlesCompleted FlagGet literal",
        0x090F3BEC,
        bytes.fromhex("c5de0608"),
        4,
        "LITERAL_THUMB_FUNCTION_POINTER_REPOINT",
        "Stage61MapSection_RaidFlagGet",
    ),
    _entry(
        "msc22_roamer_entry",
        "MSC-22",
        "CreateTownMapRoamerSprites",
        0x09125ECC,
        "f0b5de4657464e46",
        "Stage61MapSection_CreateTownMapRoamerSprites",
        install_condition="PATCH_BEFORE_ANY_ROAMER_HOOK_ACTIVATION",
    ),
    _entry(
        "msc23_cfru_warp_fade_entry",
        "MSC-23",
        "CFRU WarpFadeOutScreen",
        0x0911FEC8,
        "10b5144b00f0ecf9",
        "Stage61MapSection_CfruWarpFadeOutScreen",
        install_condition="PATCH_BEFORE_ANY_CFRU_WARP_REPOINT",
    ),
)


DORMANCY_GUARD_WINDOWS: tuple[PatchWindow, ...] = (
    PatchWindow(
        "msc22_roamer_activation_main_map",
        "MSC-22",
        "CreateDungeonIcons epilogue hook target (BPRJ translation)",
        0x080C5A90,
        bytes.fromhex("f0bc01bc00470000"),
        8,
        "ASSERT_ONLY_STOCK_HOOK_NOT_INSTALLED",
        "CreateRoamerIconTownMapHook",
        "DORMANCY_GUARD",
    ),
    PatchWindow(
        "msc22_roamer_activation_post_switch",
        "MSC-22",
        "Town Map post-switch hook target (BPRJ translation)",
        0x080C23F0,
        bytes.fromhex("29680348091826e0"),
        8,
        "ASSERT_ONLY_STOCK_HOOK_NOT_INSTALLED",
        "CreateRoamerIconTownMapPostSwitchMapHook",
        "DORMANCY_GUARD",
    ),
)


# 親 builder が採用を検討している、より小さい代替 patch。いずれも memory
# safety は満たせるが、map-section 値だけでは物理 group provenance を失うため、
# 列挙した追加証明なしには恒久修正として選択してはならない。
CONDITIONAL_ALTERNATIVE_PATCH_WINDOWS: tuple[PatchWindow, ...] = (
    PatchWindow(
        "msc07_dungeon_cursor_constant_only",
        "MSC-07",
        "GetDungeonMapsecUnderCursor Cerulean compare",
        0x080C47A0,
        bytes.fromhex("8d2c"),
        2,
        "THUMB_IMMEDIATE_COMPARE_REWRITE",
        "FIXED_PROJECT_CERULEAN_CAVE_COMPARE",
        "CONDITIONAL_NONIMPORTED_TOWN_MAP_PATH_PROVEN_UNREACHABLE",
        (),
        "source 141 compare を project 51 compare に無条件置換するため provenance を失う",
    ),
    PatchWindow(
        "msc07_dungeon_icon_constant_only",
        "MSC-07",
        "CreateDungeonIcons Cerulean compare",
        0x080C5A14,
        bytes.fromhex("8d28"),
        2,
        "THUMB_IMMEDIATE_COMPARE_REWRITE",
        "FIXED_PROJECT_CERULEAN_CAVE_COMPARE",
        "CONDITIONAL_NONIMPORTED_TOWN_MAP_PATH_PROVEN_UNREACHABLE",
        (),
        "source 141 compare を project 51 compare に無条件置換するため provenance を失う",
    ),
    PatchWindow(
        "msc22_roamer_total_corners_pointer",
        "MSC-22",
        "CreateTownMapRoamerSprites corners literal",
        0x09125FB8,
        bytes.fromhex("e8893b08"),
        4,
        "LITERAL_DATA_POINTER_REPOINT",
        "STAGE61_CFRU_SAFE_ROAMER_CORNERS",
        "CONDITIONAL_ALL_ACTIVE_ROAMER_MAPS_HAVE_PROVEN_SECTION_DOMAIN",
        (),
        "256 rows eliminate OOB but cannot distinguish imported low IDs from non-Kanto low IDs",
    ),
    PatchWindow(
        "msc22_roamer_total_dimensions_pointer",
        "MSC-22",
        "CreateTownMapRoamerSprites dimensions literal",
        0x09125FBC,
        bytes.fromhex("008d3b08"),
        4,
        "LITERAL_DATA_POINTER_REPOINT",
        "STAGE61_CFRU_SAFE_ROAMER_DIMENSIONS",
        "CONDITIONAL_ALL_ACTIVE_ROAMER_MAPS_HAVE_PROVEN_SECTION_DOMAIN",
        (),
        "256 rows eliminate OOB but invalid/non-Kanto low sections are not skip-capable",
    ),
)


FIXED_PATCH_BYTES: Mapping[str, bytes] = {
    "msc07_dungeon_cursor_constant_only": bytes.fromhex("332c"),
    "msc07_dungeon_icon_constant_only": bytes.fromhex("3328"),
}


ALL_CANDIDATE_PATCH_WINDOWS: tuple[PatchWindow, ...] = (
    *PATCH_WINDOWS,
    *CONDITIONAL_ALTERNATIVE_PATCH_WINDOWS,
)


FUNCTION_EXTENTS: tuple[FunctionExtent, ...] = (
    FunctionExtent("music", ("MSC-04",), "Overworld_MusicCanOverrideMapMusic", 0x080559E4, 0x08055A18, "14a8e7d6c868a2f4079a4c39c0fdfe71d58bd57d5d60c824824b8380186aa738"),
    FunctionExtent("stock_warp", ("MSC-05",), "WarpFadeOutScreen", 0x0807D378, 0x0807D3D0, "e40c737ef5c3e599295783f6386cb58e09819df01c6cd61b70777662862d35d6"),
    FunctionExtent("dungeon_flavor", ("MSC-06",), "GetDungeonFlavorText", 0x080C2AC4, 0x080C2B04, "42b82fc7be333c71fbbf80fc81acf202422d7909883b95d86014d8549a8ea897"),
    FunctionExtent("dungeon_name", ("MSC-06",), "GetDungeonName", 0x080C2B04, 0x080C2B40, "8b37ea2dc0e93c894bfd2507de57fa6b742227edada268df087102f8503b8de7"),
    FunctionExtent("dungeon_cursor", ("MSC-07",), "GetDungeonMapsecUnderCursor", 0x080C4764, 0x080C47C0, "7008878a3a680e5660c6dda0e4f3fd42853cc39633ee1cbd8598d22f237ece33"),
    FunctionExtent("dungeon_icons", ("MSC-07",), "CreateDungeonIcons", 0x080C59D4, 0x080C5AA0, "2a3d5bdad304d413b9a3fd6a3d7822e5bc317d24a49c8019aaf304528335862f"),
    FunctionExtent("preview_index", ("MSC-05",), "GetMapPreviewScreenIdx", 0x080F9150, 0x080F917C, "60a3d4d24619098b4158e7bff7932838955c50538f6a49efbea9b7effd4c3819"),
    FunctionExtent("dungeon_preview", ("MSC-06",), "GetDungeonMapPreviewScreenInfo", 0x080F95B0, 0x080F95D8, "d78ed4299fde7f7d7a3fedc36a7e17de73655776158f5a6c4129d6d01b2fe2be"),
    FunctionExtent("quest_check", ("MSC-17",), "QuestLog_CheckDepartingIndoorsMap", 0x080CD6AC, 0x080CD714, "3a5839694c255c325ac5a363c72c97864dc7406b1c9facb53ba2945a7084507a"),
    FunctionExtent("quest_record", ("MSC-17",), "QuestLog_TryRecordDepartedLocation", 0x080CD714, 0x080CD8A8, "e6ed883058d074885e84ae7dc61b0ec193b7cd8a611ecb2bb05b7ecd429574a7"),
    FunctionExtent("load_departed", ("MSC-15",), "LoadEvent_DepartedLocation", 0x08115D94, 0x08115E6C, "0e1a7b2697641604aa164ac8f00ddba6d0da29b053e8a90ec4d652e3152898ea"),
    FunctionExtent("load_field_move", ("MSC-16",), "LoadEvent_UsedFieldMove", 0x08115F38, 0x08115FA8, "1defc66b7b099261bc320ae8d0350d18a6a59f48272d413e937811a7a192a538"),
    FunctionExtent("summary_classifier", ("MSC-10",), "MapSecIsInKantoOrSevii", 0x0813BFFC, 0x0813C018, "0baf5e9605be49421cf064ccac839bee7ab699630a5ae00beef4356fd985049a"),
    FunctionExtent("summary_provenance", ("MSC-10",), "CurrentMonIsFromGBA", 0x0813BFBC, 0x0813BFFC, "5ece3b779eac0d642477ec21825d3c12be016fab2ae3618f1d46c0f290cc3860", "ABI_CONTEXT_PROOF"),
    FunctionExtent("wild_header", ("MSC-11",), "GetMapSecIdFromWildMonHeader", 0x0813D388, 0x0813D39C, "01c22a44fd8efb801fdd0dda84e74188f4b6c73e222b1355b031809efff7174e"),
    FunctionExtent("raid_determine", ("MSC-21",), "DetermineRaidSpecies", 0x090F36B0, 0x090F387C, "143cac843a8f961f3f0c533c49bcce7a93340ffabfeb61919b9fc06bf61b79f0"),
    FunctionExtent("raid_ability", ("MSC-21",), "GetRaidSpeciesAbilityNum", 0x090F3A20, 0x090F3A9C, "3a06ecd6bd4528cb11ca1b6aa87124b0fda4df4fc18bd8d24209a18588644006"),
    FunctionExtent("raid_has", ("MSC-21",), "HasRaidBattleAlreadyBeenDone", 0x090F3AC8, 0x090F3AF0, "710875e15b1318886161f5c3e0074c91d4885874a4a27b1408580b909f82a837"),
    FunctionExtent("raid_set", ("MSC-21",), "sp119_SetRaidBattleFlag", 0x090F3AF0, 0x090F3B18, "2f1bc9b87c7d2cf9312e2c2851c09757f6f43c9adc8c299d854bc22a3e3fec83"),
    FunctionExtent("raid_clear_all", ("MSC-21",), "ClearAllRaidBattleFlags", 0x090F3B18, 0x090F3B3C, "6c6b3b73995b0dbee8951dc2bae8a3177690347340d014b756ce8171575718ce"),
    FunctionExtent("raid_clear_one", ("MSC-21",), "sp11A_ClearRaidBattleFlag", 0x090F3B3C, 0x090F3B94, "6066839e0611c4d7ab95f20070a27512df17fd790f384e68c86a01a0ad3c05c2"),
    FunctionExtent("raid_all_done", ("MSC-21",), "sp11B_AllRaidBattlesCompleted", 0x090F3B94, 0x090F3BF0, "3ce8df5f8635fdb1c36e0347a2ce8abae37d555294df29c3e1f011d08e19905e"),
    FunctionExtent("raid_rewards", ("MSC-21",), "sp11C_GiveRaidBattleRewards", 0x090F3D18, 0x090F400E, "c422618d9b4df6858be738780621c88b02a3c4f45b0c4a0f7edd086ad9a69a50"),
    FunctionExtent("cfru_warp", ("MSC-23",), "CFRU WarpFadeOutScreen", 0x0911FEC8, 0x0911FF38, "bf9cfbfd510bb3ab12213404cc082e88abfbbf9a2dafc371e0d3473facb44da4"),
    FunctionExtent("cfru_roamer", ("MSC-22",), "CreateTownMapRoamerSprites", 0x09125ECC, 0x09125FD4, "362971f536edaba8bae925efcbe15820c6f1fb5b62767d1ac2654f609bf6799a"),
)


DATA_EXTENTS: tuple[DataExtent, ...] = (
    DataExtent(
        "preview_rows",
        ("MSC-05", "MSC-06", "MSC-23"),
        "sMapPreviewScreenData[28]",
        0x08408C26,
        28 * 16,
        "f65ade805d0eaca3a95f120d8b745cbf14fc4ed8cc5916f7dfa0d7af8a980d69",
    ),
    DataExtent(
        "quest_inside_outside_rows",
        ("MSC-17",),
        "sInsideOutsidePairs[51]",
        0x083BC8E0,
        51 * 8,
        "2c66c714929e1be5e46583d1f0771e679bbdbc1e9befac7d5b38a0747b48e29c",
    ),
    DataExtent(
        "quest_gym_sections",
        ("MSC-15",),
        "sGymCityMapSecs[8]",
        0x084170AF,
        8,
        "48038bfe51a5a639b6720bd7e9a2b044b4b89df191c128c200311349570d4b7d",
    ),
    DataExtent(
        "raid_rows",
        ("MSC-21",),
        "gRaidsByMapSection[109][7]",
        0x09161AF0,
        109 * 7 * 8,
        "2106c87f16a8860bd1ee50da0a721eae518d5f209cc5febea3637a9d68ece1f7",
    ),
    DataExtent(
        "roamer_corners",
        ("MSC-22",),
        "sMapSectionTopLeftCorners[109]",
        0x083B89E8,
        109 * 4,
        "405a9aa09bedd6b3a969c5aa9fa51bd3dc285cb4bd65ea9f4f0628ff19027c97",
    ),
    DataExtent(
        "roamer_dimensions",
        ("MSC-22",),
        "sMapSectionDimensions[109]",
        0x083B8D00,
        109 * 4,
        "0f909a36f5daa66fbfa6fe4a26cb282f8e5003d27ea612906586439c37c0cc40",
    ),
    DataExtent(
        "pokedex_kanto_area_rows",
        ("MSC-11",),
        "sDexAreas_Kanto[55]",
        0x0842D4D4,
        55 * 4,
        "d12d4141c0b4d1e347ecf50d0a32aa25b7a94b61025e50e75290814abc81fdad",
    ),
)


def project_to_source(project_section: int) -> int | None:
    """project 0..52 を exact source section へ変換する。"""

    if not isinstance(project_section, int) or isinstance(project_section, bool):
        return None
    if 0 <= project_section <= 10:
        return 88 + project_section
    if 11 <= project_section <= 52:
        return 90 + project_section
    return None


def normalize_for_stock(
    physical_group: int,
    section: int,
    *,
    unsupported: int = MAPSEC_NONE,
) -> int:
    """imported group だけ project->source 変換し、それ以外は完全保持する。"""

    if physical_group not in IMPORTED_PHYSICAL_GROUPS:
        return section
    converted = project_to_source(section)
    return unsupported if converted is None else converted


def raid_source_section(physical_group: int, section: int) -> int:
    """CFRU inline ``u8(section-87)`` に渡せる安全な section を返す。"""

    if physical_group in IMPORTED_PHYSICAL_GROUPS:
        converted = project_to_source(section)
        return MAPSEC_DYNAMIC if converted is None else converted
    if RAID_SOURCE_MIN <= section <= RAID_SOURCE_MAX:
        return section
    return MAPSEC_DYNAMIC


def roamer_layout_index(physical_group: int, section: int) -> int | None:
    """roamer corner/dimension table の検証済み 0..108 index を返す。"""

    canonical = normalize_for_stock(physical_group, section, unsupported=MAPSEC_NONE)
    if not ROAMER_SOURCE_MIN <= canonical <= ROAMER_SOURCE_MAX:
        return None
    index = canonical - ROAMER_SOURCE_MIN
    return index if 0 <= index < ROAMER_LAYOUT_ROW_COUNT else None


def load_source_crosswalk(root: Path) -> list[dict[str, Any]]:
    """53 行 crosswalk を exact hash/domain とともに読む。"""

    try:
        rows = audit.validate_project_manifest(root / MAP_SECTION_MANIFEST_RELATIVE)
    except audit.MapSectionConsumerAuditError as exc:
        raise MapSectionConsumerPolicyError(str(exc)) from exc
    result: list[dict[str, Any]] = []
    for row in rows:
        project = int(row["project_id"])
        source = int(row["source_id"])
        if project_to_source(project) != source:
            raise MapSectionConsumerPolicyError(
                f"project/source algorithm drifted: {project}->{source}"
            )
        raid_index = source - MAPSEC_DYNAMIC
        layout_index = source - ROAMER_SOURCE_MIN
        if not 0 <= raid_index < RAID_ROW_COUNT:
            raise MapSectionConsumerPolicyError(f"raid index out of range: {raid_index}")
        if not 0 <= layout_index < ROAMER_LAYOUT_ROW_COUNT:
            raise MapSectionConsumerPolicyError(
                f"layout index out of range: {layout_index}"
            )
        result.append(
            {
                **row,
                "raid_index": raid_index,
                "town_map_layout_index": layout_index,
            }
        )
    return result


def _load_imported_maps(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    crosswalk_raw, crosswalk = _read_csv(
        root / IMPORT_CROSSWALK_RELATIVE, "Kanto physical crosswalk"
    )
    _assert_sha(crosswalk_raw, IMPORT_CROSSWALK_SHA256, "Kanto physical crosswalk")
    if len(crosswalk) != 256:
        raise MapSectionConsumerPolicyError(
            f"Kanto physical crosswalk row count mismatch: {len(crosswalk)}"
        )
    records: dict[str, dict[str, Any]] = {}
    canonical: list[tuple[str, str, str]] = []
    maps_dir = root / "vendor/upstream/pokefirered/data/maps"
    for row in crosswalk:
        name = row.get("source_map", "")
        if not name or name in records:
            raise MapSectionConsumerPolicyError(
                f"physical crosswalk source_map duplicate/empty: {name!r}"
            )
        map_json = _read_json(maps_dir / name / "map.json", f"map.json {name}")
        map_id = map_json.get("id")
        section_symbol = map_json.get("region_map_section")
        if not isinstance(map_id, str) or not isinstance(section_symbol, str):
            raise MapSectionConsumerPolicyError(f"map identity incomplete: {name}")
        group = int(row["new_group_id"])
        map_num = int(row["new_map_id"])
        if group not in IMPORTED_PHYSICAL_GROUPS or not 0 <= map_num <= 255:
            raise MapSectionConsumerPolicyError(
                f"imported physical map out of domain: {name}={group}/{map_num}"
            )
        canonical.append((name, map_id, section_symbol))
        records[name] = {
            "name": name,
            "map_id": map_id,
            "section_symbol": section_symbol,
            "project_group": group,
            "project_map": map_num,
        }
    canonical_raw = json.dumps(
        sorted(canonical), ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    _assert_sha(
        canonical_raw,
        IMPORTED_MAP_ID_SECTION_CANONICAL_SHA256,
        "imported map id/section canonical set",
    )
    return records, {
        "path": str(IMPORT_CROSSWALK_RELATIVE),
        "size": len(crosswalk_raw),
        "sha256": _sha(crosswalk_raw),
        "row_count": len(crosswalk),
        "map_id_section_canonical_sha256": _sha(canonical_raw),
    }


_QL_PAIR_RE = re.compile(
    r"\[(QL_LOCATION_[A-Z0-9_]+)\]\s*=\s*"
    r"\{MAP\((MAP_[A-Z0-9_]+)\),\s*MAP\((MAP_[A-Z0-9_]+)\)\}"
)
_QL_CONSTANT_RE = re.compile(
    r"^#define\s+(QL_LOCATION_[A-Z0-9_]+)\s+(\d+)\s*$", re.MULTILINE
)


def _quest_manifest_int(value: Any, what: str) -> int:
    if isinstance(value, bool):
        raise MapSectionConsumerPolicyError(f"{what} は整数である必要があります")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise MapSectionConsumerPolicyError(
                f"{what} は整数ではありません: {value!r}"
            ) from exc
    raise MapSectionConsumerPolicyError(
        f"{what} は整数ではありません: {value!r}"
    )


def _quest_manifest_map(value: Any, what: str) -> tuple[int, int]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise MapSectionConsumerPolicyError(
            f"{what} は [group, map] の2整数である必要があります"
        )
    group, number = value
    if not 0 <= group < 0x7F or not 0 <= number < 0x7F:
        raise MapSectionConsumerPolicyError(
            f"{what} は物理map範囲外です: {value}"
        )
    return group, number


def _quest_source_map_graph(
    stage60: bytes, group_order: Sequence[str], groups: Mapping[str, Any]
) -> dict[tuple[int, int], dict[str, Any]]:
    """Stage60 exact ROM の rooted warp graph を復元する。

    SOURCE/Vega map は Stage61 でも同じ header/event payload を共有するため、
    builder 入力である Stage60 を検査すれば、出力 ROM に未検査の map edge を
    持ち込まずに済む。byte pattern scan は行わず gMapGroups からだけ辿る。
    """

    group_table = _rom_u32(stage60, MAP_GROUPS_POINTER_SITE, "Stage60 gMapGroups")
    graph: dict[tuple[int, int], dict[str, Any]] = {}
    physical = {
        (group, number)
        for group, key in enumerate(group_order)
        for number, _ in enumerate(groups[key])
    }
    for group, key in enumerate(group_order):
        maps = groups[key]
        if not isinstance(maps, list):
            raise MapSectionConsumerPolicyError(
                f"map group が配列ではありません: {key}"
            )
        group_pointer = _rom_u32(
            stage60, group_table + group * 4, f"Stage60 map group {group}"
        )
        for number, _ in enumerate(maps):
            header = _rom_u32(
                stage60,
                group_pointer + number * 4,
                f"Stage60 map header {group}/{number}",
            )
            events = _rom_u32(
                stage60, header + 4, f"Stage60 map events {group}/{number}"
            )
            map_type = _rom_slice(
                stage60, header + 0x17, 1, f"Stage60 map type {group}/{number}"
            )[0]
            section = _rom_slice(
                stage60, header + 0x14, 1, f"Stage60 map section {group}/{number}"
            )[0]
            sentinel = bool(
                events
                and _rom_slice(
                    stage60, events, 4, f"Stage60 event counts {group}/{number}"
                ) == b"\xFF" * 4
            )
            warp_array = 0
            warps: list[dict[str, Any]] = []
            if events and not sentinel:
                warp_count = _rom_slice(
                    stage60, events + 1, 1,
                    f"Stage60 warp count {group}/{number}",
                )[0]
                warp_array = _rom_u32(
                    stage60, events + 8,
                    f"Stage60 warp array {group}/{number}",
                )
                if warp_count and not ROM_BASE <= warp_array < ROM_BASE + len(stage60):
                    raise MapSectionConsumerPolicyError(
                        f"Stage60 warp array がROM外です: {group}/{number} "
                        f"{_hex(warp_array)}"
                    )
                for index in range(warp_count):
                    address = warp_array + index * 8
                    raw = _rom_slice(
                        stage60, address, 8,
                        f"Stage60 warp {group}/{number}/{index}",
                    )
                    x, y = struct.unpack_from("<hh", raw)
                    destination = (raw[7], raw[6])
                    warps.append(
                        {
                            "address": address,
                            "source": (group, number),
                            "destination": destination,
                            "x": x,
                            "y": y,
                            "destination_warp_id": raw[5],
                            "valid_destination": destination in physical,
                        }
                    )
            graph[(group, number)] = {
                "header": header,
                "events": events,
                "events_sentinel": sentinel,
                "warp_array": 0xFFFFFFFF if sentinel else warp_array,
                "map_type": map_type,
                "section": section,
                "warps": warps,
            }
    return graph


def _quest_project_map_graph(
    stage60: bytes, imported: Mapping[str, Mapping[str, Any]]
) -> dict[tuple[int, int], dict[str, Any]]:
    """253 imported physical mapsだけをexact gMapGroupsから復元する。"""

    physical = {
        (int(row["project_group"]), int(row["project_map"]))
        for row in imported.values()
        if (int(row["project_group"]), int(row["project_map"]))
        not in MAP_NAME_IMPORTED_UNUSED_COORDS
    }
    if len(physical) != 253:
        raise MapSectionConsumerPolicyError(
            f"Quest Log project physical inventory drifted: {len(physical)}"
        )
    group_table = _rom_u32(stage60, MAP_GROUPS_POINTER_SITE, "Stage60 gMapGroups")
    graph: dict[tuple[int, int], dict[str, Any]] = {}
    for group, number in sorted(physical):
        group_pointer = _rom_u32(
            stage60, group_table + group * 4, f"Stage60 project group {group}"
        )
        header = _rom_u32(
            stage60,
            group_pointer + number * 4,
            f"Stage60 project map header {group}/{number}",
        )
        events = _rom_u32(
            stage60, header + 4, f"Stage60 project events {group}/{number}"
        )
        map_type = _rom_slice(
            stage60, header + 0x17, 1,
            f"Stage60 project map type {group}/{number}",
        )[0]
        section = _rom_slice(
            stage60, header + 0x14, 1,
            f"Stage60 project section {group}/{number}",
        )[0]
        sentinel = bool(
            events
            and _rom_slice(
                stage60, events, 4,
                f"Stage60 project event counts {group}/{number}",
            ) == b"\xFF" * 4
        )
        warp_array = 0
        warps: list[dict[str, Any]] = []
        if events and not sentinel:
            warp_count = _rom_slice(
                stage60, events + 1, 1,
                f"Stage60 project warp count {group}/{number}",
            )[0]
            warp_array = _rom_u32(
                stage60, events + 8,
                f"Stage60 project warp array {group}/{number}",
            )
            if warp_count and not ROM_BASE <= warp_array < ROM_BASE + len(stage60):
                raise MapSectionConsumerPolicyError(
                    f"Stage60 project warp array ROM外: {group}/{number} "
                    f"{_hex(warp_array)}"
                )
            for index in range(warp_count):
                address = warp_array + index * 8
                raw = _rom_slice(
                    stage60, address, 8,
                    f"Stage60 project warp {group}/{number}/{index}",
                )
                x, y = struct.unpack_from("<hh", raw)
                destination = (raw[7], raw[6])
                warps.append({
                    "address": address,
                    "source": (group, number),
                    "destination": destination,
                    "x": x,
                    "y": y,
                    "destination_warp_id": raw[5],
                    "valid_destination": destination in physical,
                })
        graph[(group, number)] = {
            "header": header,
            "events": events,
            "events_sentinel": sentinel,
            "warp_array": 0xFFFFFFFF if sentinel else warp_array,
            "map_type": map_type,
            "section": section,
            "warps": warps,
        }
    return graph


def _quest_graph_path(
    graph: Mapping[tuple[int, int], Mapping[str, Any]],
    start: tuple[int, int],
    target: tuple[int, int],
) -> list[dict[str, Any]] | None:
    """別 outdoor map を横切らず target へ至る最短warp path。"""

    outdoor = {
        physical
        for physical, row in graph.items()
        if int(row["map_type"]) in (1, 2, 3, 6)
    }
    pending: list[tuple[tuple[int, int], list[dict[str, Any]]]] = [(start, [])]
    seen = {start}
    for current, path in pending:
        if current == target:
            return path
        for edge in graph[current]["warps"]:
            if not edge["valid_destination"]:
                continue
            destination = tuple(edge["destination"])
            candidate = [*path, edge]
            if destination == target:
                return candidate
            if destination in outdoor or destination in seen:
                continue
            seen.add(destination)
            pending.append((destination, candidate))
    return None


def _quest_validate_evidence_path(
    graph: Mapping[tuple[int, int], Mapping[str, Any]],
    start: tuple[int, int],
    target: tuple[int, int],
    encoded: Any,
    what: str,
) -> list[dict[str, Any]]:
    if not isinstance(encoded, list):
        raise MapSectionConsumerPolicyError(f"{what} はaddress配列ではありません")
    current = start
    decoded: list[dict[str, Any]] = []
    for index, value in enumerate(encoded):
        address = _quest_manifest_int(value, f"{what}[{index}]")
        candidates = [
            edge for edge in graph[current]["warps"]
            if int(edge["address"]) == address and edge["valid_destination"]
        ]
        if len(candidates) != 1:
            raise MapSectionConsumerPolicyError(
                f"{what}[{index}] が {current[0]}/{current[1]} のwarpではありません: "
                f"{_hex(address)}"
            )
        edge = candidates[0]
        decoded.append(edge)
        current = tuple(edge["destination"])
    if current != target:
        raise MapSectionConsumerPolicyError(
            f"{what} の終点不一致: {current} != {target}"
        )
    return decoded


def load_quest_log_source_exit_manifest(
    root: Path,
    *,
    stage60: bytes,
    source_rows: Sequence[Mapping[str, Any]],
    group_order: Sequence[str],
    groups: Mapping[str, Any],
) -> dict[str, Any]:
    """meaning-reviewed source exit と exact warp evidence をfail-closed検査する。"""

    raw = _read(root / QUEST_LOG_EXIT_MANIFEST_RELATIVE, "Quest Log exit manifest")
    _assert_sha(raw, QUEST_LOG_EXIT_MANIFEST_SHA256, "Quest Log exit manifest")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MapSectionConsumerPolicyError(
            f"Quest Log exit manifest parse error: {exc}"
        ) from exc
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise MapSectionConsumerPolicyError("Quest Log exit manifest schema mismatch")
    source_rom = document.get("source_rom")
    if not isinstance(source_rom, dict) or source_rom.get("sha256") != STAGE60_ROM_SHA256:
        raise MapSectionConsumerPolicyError(
            "Quest Log exit manifest Stage60 identity mismatch"
        )
    rows = document.get("rows")
    if not isinstance(rows, list) or len(rows) != 51:
        raise MapSectionConsumerPolicyError(
            "Quest Log exit manifest はexact 51行である必要があります"
        )
    graph = _quest_source_map_graph(stage60, group_order, groups)
    normalized: list[dict[str, Any]] = []
    classifications: dict[str, int] = {}
    disabled: list[int] = []
    for index, (manifest_row, source_row) in enumerate(zip(rows, source_rows)):
        if not isinstance(manifest_row, dict) or manifest_row.get("index") != index:
            raise MapSectionConsumerPolicyError(
                f"Quest Log exit manifest index不連続: {index}"
            )
        symbol = str(source_row["location_symbol"])
        if manifest_row.get("location_symbol") != symbol:
            raise MapSectionConsumerPolicyError(
                f"Quest Log exit manifest symbol不一致: {index}/{symbol}"
            )
        legacy_inside = (
            int(source_row["source"]["inside"]["group"]),
            int(source_row["source"]["inside"]["map"]),
        )
        inside = _quest_manifest_map(manifest_row.get("inside"), f"row {index} inside")
        if inside != legacy_inside:
            raise MapSectionConsumerPolicyError(
                f"Quest Log exit manifest inside不一致: row {index}: "
                f"{inside} != {legacy_inside}"
            )
        legacy_outside = (
            int(source_row["source"]["outside"]["group"]),
            int(source_row["source"]["outside"]["map"]),
        )
        declared_outside = _quest_manifest_map(
            manifest_row.get("existing_outside"), f"row {index} existing_outside"
        )
        if declared_outside != legacy_outside:
            raise MapSectionConsumerPolicyError(
                f"Quest Log exit manifest existing outside不一致: row {index}"
            )
        physical = graph[inside]
        evidence = manifest_row.get("evidence")
        if not isinstance(evidence, dict):
            raise MapSectionConsumerPolicyError(f"row {index} evidence missing")
        expected_evidence = {
            "header": int(physical["header"]),
            "events": int(physical["events"]),
            "warp_array": int(physical["warp_array"]),
        }
        for key, expected in expected_evidence.items():
            actual = _quest_manifest_int(evidence.get(key), f"row {index} {key}")
            if actual != expected:
                raise MapSectionConsumerPolicyError(
                    f"Quest Log exit manifest evidence不一致: row {index} {key}: "
                    f"{_hex(actual)} != {_hex(expected)}"
                )
        declared_path = _quest_graph_path(graph, inside, declared_outside)
        reverse_path = _quest_graph_path(graph, declared_outside, inside)
        if physical["events_sentinel"] or not physical["warp_array"]:
            classification = "INVALID"
        elif declared_path is not None and len(declared_path) == 1:
            classification = "DIRECT_BI" if reverse_path is not None else "DIRECT_ONE_WAY"
        elif declared_path is not None:
            classification = "MULTIHOP_BI" if reverse_path is not None else "MULTIHOP_ONE_WAY"
        else:
            classification = "TARGET_MISMATCH"
        if manifest_row.get("classification") != classification:
            raise MapSectionConsumerPolicyError(
                f"Quest Log exit classification不一致: row {index}: "
                f"{manifest_row.get('classification')} != {classification}"
            )
        classifications[classification] = classifications.get(classification, 0) + 1
        enabled = manifest_row.get("enabled")
        if not isinstance(enabled, bool):
            raise MapSectionConsumerPolicyError(f"row {index} enabled must be bool")
        component_raw = manifest_row.get("inside_component")
        exits_raw = manifest_row.get("record_exits")
        if not enabled:
            disabled.append(index)
            if component_raw != [] or exits_raw != [] or classification != "INVALID":
                raise MapSectionConsumerPolicyError(
                    f"disabled Quest Log row {index} must be INVALID with empty runtime sets"
                )
            normalized.append({**manifest_row, "inside_component": [], "record_exits": []})
            continue
        if classification == "INVALID":
            raise MapSectionConsumerPolicyError(f"INVALID row {index} cannot be enabled")
        if not isinstance(component_raw, list) or not component_raw:
            raise MapSectionConsumerPolicyError(f"row {index} inside_component missing")
        component = [
            _quest_manifest_map(value, f"row {index} inside_component")
            for value in component_raw
        ]
        if len(component) != len(set(component)) or component[0] != inside:
            raise MapSectionConsumerPolicyError(
                f"row {index} inside_component must be unique and begin with inside"
            )
        if not isinstance(exits_raw, list) or len(exits_raw) != 1:
            raise MapSectionConsumerPolicyError(
                f"row {index} must have exactly one meaning-reviewed exit variant"
            )
        exit_row = exits_raw[0]
        if not isinstance(exit_row, dict):
            raise MapSectionConsumerPolicyError(f"row {index} record exit invalid")
        destination = _quest_manifest_map(exit_row.get("map"), f"row {index} exit map")
        location_id = _quest_manifest_int(
            exit_row.get("location_id"), f"row {index} exit location_id"
        )
        if location_id != index:
            raise MapSectionConsumerPolicyError(
                f"row {index} exit location_id must remain {index}"
            )
        destination_warp_id_raw = exit_row.get("destination_warp_id")
        if destination_warp_id_raw is None:
            destination_warp_id = None
        else:
            destination_warp_id = _quest_manifest_int(
                destination_warp_id_raw,
                f"row {index} destination_warp_id",
            )
            if destination_warp_id not in (0, 1) or index not in (22, 23, 42, 43):
                raise MapSectionConsumerPolicyError(
                    f"row {index} unexpected destination warp variant"
                )
        path = _quest_validate_evidence_path(
            graph, inside, destination, exit_row.get("path"),
            f"row {index} record exit path",
        )
        path_sources = [tuple(edge["source"]) for edge in path]
        if any(source not in component for source in path_sources):
            raise MapSectionConsumerPolicyError(
                f"row {index} record path escaped inside_component before exit"
            )
        exact_component = list(dict.fromkeys(path_sources))
        if component != exact_component:
            raise MapSectionConsumerPolicyError(
                f"row {index} inside_component はrecord pathのexact source列ではありません: "
                f"{component} != {exact_component}"
            )
        if destination in component:
            raise MapSectionConsumerPolicyError(
                f"row {index} record exit is still inside_component"
            )
        if destination_warp_id is not None and (
            not path or int(path[-1]["destination_warp_id"]) != destination_warp_id
        ):
            raise MapSectionConsumerPolicyError(
                f"row {index} destination warp variant evidence mismatch"
            )
        normalized.append(
            {
                **manifest_row,
                "inside_component": [list(value) for value in component],
                "record_exits": [
                    {
                        **exit_row,
                        "map": list(destination),
                        "destination_warp_id": destination_warp_id,
                        "path": [_hex(int(edge["address"])) for edge in path],
                    }
                ],
            }
        )
    if classifications != QUEST_LOG_SOURCE_CLASSIFICATION_COUNTS:
        raise MapSectionConsumerPolicyError(
            "Quest Log exit classification counts drifted: "
            f"{classifications}"
        )
    if tuple(disabled) != QUEST_LOG_SOURCE_DISABLED_ROWS:
        raise MapSectionConsumerPolicyError(
            f"Quest Log disabled rows drifted: {disabled}"
        )
    warp_variants = {
        row["index"]: row["record_exits"][0]["destination_warp_id"]
        for row in normalized
        if row["enabled"]
        and row["record_exits"][0]["destination_warp_id"] is not None
    }
    if warp_variants != {22: 0, 23: 1, 42: 0, 43: 1}:
        raise MapSectionConsumerPolicyError(
            f"Quest Log destination warp variants drifted: {warp_variants}"
        )
    return {
        "path": str(QUEST_LOG_EXIT_MANIFEST_RELATIVE),
        "sha256": _sha(raw),
        "source_rom_sha256": STAGE60_ROM_SHA256,
        "row_count": len(normalized),
        "enabled_count": len(normalized) - len(disabled),
        "disabled_rows": disabled,
        "classification_counts": classifications,
        "destination_warp_variants": warp_variants,
        "rows": normalized,
    }


def build_quest_log_physical_crosswalk(
    root: Path, *, stage60: bytes | None = None
) -> dict[str, Any]:
    """project stock 51行と、Vega exact-warp再レビュー済み行を派生する。"""

    field_raw = _read(root / FIELD_SPECIALS_RELATIVE, "field_specials.c")
    constants_raw = _read(root / QUEST_LOG_CONSTANTS_RELATIVE, "quest_log.h")
    _assert_sha(field_raw, FIELD_SPECIALS_SHA256, "field_specials.c")
    _assert_sha(constants_raw, QUEST_LOG_CONSTANTS_SHA256, "quest_log.h")
    if stage60 is None:
        stage60 = _read(root / STAGE60_ROM_RELATIVE, "Stage60 ROM")
    if len(stage60) != STAGE60_ROM_SIZE or _sha(stage60) != STAGE60_ROM_SHA256:
        raise MapSectionConsumerPolicyError("Quest Log crosswalkのStage60 identity不一致")
    try:
        field_text = field_raw.decode("utf-8")
        constants_text = constants_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MapSectionConsumerPolicyError(f"Quest Log source decode error: {exc}") from exc

    constants = {
        symbol: int(value)
        for symbol, value in _QL_CONSTANT_RE.findall(constants_text)
    }
    if sorted(constants.values()) != list(range(51)) or len(constants) != 51:
        raise MapSectionConsumerPolicyError(
            f"QL_LOCATION constants are not exact 0..50: {constants}"
        )

    imported, physical_input = _load_imported_maps(root)
    id_to_name = {row["map_id"]: name for name, row in imported.items()}
    if len(id_to_name) != len(imported):
        raise MapSectionConsumerPolicyError("imported map IDs are not unique")

    groups_raw = _read(root / MAP_GROUPS_RELATIVE, "map_groups.json")
    _assert_sha(groups_raw, MAP_GROUPS_SHA256, "map_groups.json")
    try:
        groups = json.loads(groups_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MapSectionConsumerPolicyError(f"map_groups.json parse error: {exc}") from exc
    order = groups.get("group_order")
    if not isinstance(order, list):
        raise MapSectionConsumerPolicyError("map_groups.json group_order missing")
    source_physical: dict[str, tuple[int, int]] = {}
    for group_id, key in enumerate(order):
        maps = groups.get(key)
        if not isinstance(maps, list):
            raise MapSectionConsumerPolicyError(f"map group missing: {key}")
        for map_id, name in enumerate(maps):
            if name in source_physical:
                raise MapSectionConsumerPolicyError(f"source map duplicate: {name}")
            source_physical[name] = (group_id, map_id)

    section_rows = load_source_crosswalk(root)
    section_by_symbol = {
        row["symbol"]: (row["project_id"], row["source_id"])
        for row in section_rows
    }
    parsed = _QL_PAIR_RE.findall(field_text)
    if len(parsed) != 51:
        raise MapSectionConsumerPolicyError(
            f"sInsideOutsidePairs row count mismatch: {len(parsed)}"
        )

    pairs: list[dict[str, Any]] = []
    compact: list[dict[str, Any]] = []
    for symbol, inside_id, outside_id in parsed:
        if symbol not in constants or inside_id not in id_to_name or outside_id not in id_to_name:
            raise MapSectionConsumerPolicyError(
                f"Quest Log map identity unresolved: {symbol}/{inside_id}/{outside_id}"
            )
        inside_name = id_to_name[inside_id]
        outside_name = id_to_name[outside_id]
        inside = imported[inside_name]
        outside = imported[outside_name]
        try:
            inside_project, inside_source = section_by_symbol[inside["section_symbol"]]
            outside_project, outside_source = section_by_symbol[outside["section_symbol"]]
            inside_source_group, inside_source_map = source_physical[inside_name]
            outside_source_group, outside_source_map = source_physical[outside_name]
        except KeyError as exc:
            raise MapSectionConsumerPolicyError(
                f"Quest Log source/project crosswalk missing: {symbol}: {exc}"
            ) from exc
        index = constants[symbol]
        source_inside = {
            "map_name": inside_name,
            "group": inside_source_group,
            "map": inside_source_map,
            "section": inside_source,
        }
        source_inside["stage60_runtime_section"] = _stage60_map_section(
            stage60, inside_source_group, inside_source_map
        )
        source_outside = {
            "map_name": outside_name,
            "group": outside_source_group,
            "map": outside_source_map,
            "section": outside_source,
        }
        project_inside = {
            "map_name": inside_name,
            "group": inside["project_group"],
            "map": inside["project_map"],
            "section": inside_project,
        }
        project_outside = {
            "map_name": outside_name,
            "group": outside["project_group"],
            "map": outside["project_map"],
            "section": outside_project,
        }
        pairs.append(
            {
                "index": index,
                "location_symbol": symbol,
                "source": {"inside": source_inside, "outside": source_outside},
                "project": {"inside": project_inside, "outside": project_outside},
            }
        )
        compact.append(
            {
                "index": index,
                "symbol": symbol,
                "source_inside": [
                    inside_name,
                    inside_source_group,
                    inside_source_map,
                    inside_source,
                ],
                "source_outside": [
                    outside_name,
                    outside_source_group,
                    outside_source_map,
                    outside_source,
                ],
                "project_inside": [
                    inside_name,
                    inside["project_group"],
                    inside["project_map"],
                    inside_project,
                ],
                "project_outside": [
                    outside_name,
                    outside["project_group"],
                    outside["project_map"],
                    outside_project,
                ],
            }
        )
    pairs.sort(key=lambda row: row["index"])
    compact.sort(key=lambda row: row["index"])
    if [row["index"] for row in pairs] != list(range(51)):
        raise MapSectionConsumerPolicyError("Quest Log pair indices are not exact 0..50")
    if any(
        side["group"] not in IMPORTED_PHYSICAL_GROUPS
        for row in pairs
        for side in (row["project"]["inside"], row["project"]["outside"])
    ):
        raise MapSectionConsumerPolicyError("Quest Log project pair escaped groups 96..98")
    compact_raw = json.dumps(
        compact, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    _assert_sha(compact_raw, QUEST_PAIR_CANONICAL_SHA256, "Quest Log pair canonical set")

    by_index = {row["index"]: row for row in pairs}
    runtime_section_mismatches = [
        {
            "index": row["index"],
            "location_symbol": row["location_symbol"],
            "inside_group": row["source"]["inside"]["group"],
            "inside_map": row["source"]["inside"]["map"],
            "clean_section": row["source"]["inside"]["section"],
            "stage60_runtime_section": row["source"]["inside"][
                "stage60_runtime_section"
            ],
        }
        for row in pairs
        if row["source"]["inside"]["section"]
        != row["source"]["inside"]["stage60_runtime_section"]
    ]

    # FireRed の logical map identity は Stage60/Vega の物理 map payload と
    # 一致しない。legacy pair は監査証跡として残し、runtime source table だけを
    # exact rooted warp graph と meaning review に基づく exit へ差し替える。
    # event payload が消去 sentinel の2行は 0xFF marker でfail-closed無効化する。
    exit_manifest = load_quest_log_source_exit_manifest(
        root,
        stage60=stage60,
        source_rows=pairs,
        group_order=order,
        groups=groups,
    )
    project_graph = _quest_project_map_graph(stage60, imported)
    project_multihop_rows: list[int] = []
    project_runtime_rows: list[dict[str, Any]] = []
    project_warp_variants = {22: 0, 23: 1, 42: 0, 43: 1}
    for row in pairs:
        index = int(row["index"])
        inside = (
            int(row["project"]["inside"]["group"]),
            int(row["project"]["inside"]["map"]),
        )
        outside = (
            int(row["project"]["outside"]["group"]),
            int(row["project"]["outside"]["map"]),
        )
        path = _quest_graph_path(project_graph, inside, outside)
        if path is None:
            raise MapSectionConsumerPolicyError(
                f"Quest Log project exit path missing: row {index}: "
                f"{inside}->{outside}"
            )
        if len(path) > 1:
            project_multihop_rows.append(index)
        component = list(dict.fromkeys(tuple(edge["source"]) for edge in path))
        if not component or component[0] != inside:
            raise MapSectionConsumerPolicyError(
                f"Quest Log project component invalid: row {index}: {component}"
            )
        destination_warp_id = project_warp_variants.get(index)
        if destination_warp_id is not None:
            variant_edges = [
                edge for edge in project_graph[inside]["warps"]
                if edge["valid_destination"]
                and tuple(edge["destination"]) == outside
                and int(edge["destination_warp_id"]) == destination_warp_id
            ]
            if len(variant_edges) != 1:
                raise MapSectionConsumerPolicyError(
                    f"Quest Log project warp variant ambiguous: row {index}: "
                    f"{len(variant_edges)}"
                )
            path = variant_edges
        project_runtime = {
            "index": index,
            "enabled": True,
            "inside_component": [list(value) for value in component],
            "record_exits": [{
                "map": list(outside),
                "location_id": index,
                "destination_warp_id": destination_warp_id,
                "path": [_hex(int(edge["address"])) for edge in path],
            }],
        }
        row["project_runtime_policy"] = project_runtime
        project_runtime_rows.append(project_runtime)
    if project_multihop_rows != [19]:
        raise MapSectionConsumerPolicyError(
            f"Quest Log project multihop rows drifted: {project_multihop_rows}"
        )
    if project_runtime_rows[19]["inside_component"] != [[97, 5], [97, 4]]:
        raise MapSectionConsumerPolicyError(
            "Quest Log project SS Anne component drifted"
        )
    source_name_by_physical = {
        physical: name for name, physical in source_physical.items()
    }
    if len(source_name_by_physical) != len(source_physical):
        raise MapSectionConsumerPolicyError("source physical map identity is not unique")
    for row, manifest_row in zip(pairs, exit_manifest["rows"]):
        legacy = row["source"]
        row["source_legacy"] = {
            "inside": dict(legacy["inside"]),
            "outside": dict(legacy["outside"]),
        }
        row["source_runtime_policy"] = manifest_row
        if not manifest_row["enabled"]:
            row["source"] = {
                "inside": {
                    "map_name": "DISABLED_INVALID_STAGE60_EVENTS",
                    "group": 0xFF,
                    "map": 0xFF,
                    "section": MAPSEC_NONE,
                    "stage60_runtime_section": MAPSEC_NONE,
                },
                "outside": {
                    "map_name": "DISABLED_INVALID_STAGE60_EVENTS",
                    "group": 0xFF,
                    "map": 0xFF,
                    "section": MAPSEC_NONE,
                },
            }
            continue
        destination = tuple(manifest_row["record_exits"][0]["map"])
        try:
            destination_name = source_name_by_physical[destination]
        except KeyError as exc:
            raise MapSectionConsumerPolicyError(
                f"Quest Log reviewed exit map identity missing: row {row['index']}: "
                f"{destination}"
            ) from exc
        row["source"]["outside"] = {
            "map_name": destination_name,
            "group": destination[0],
            "map": destination[1],
            "section": _stage60_map_section(stage60, *destination),
        }
    return {
        "row_count": len(pairs),
        "canonical_sha256": _sha(compact_raw),
        "inputs": {
            "field_specials": {
                "path": str(FIELD_SPECIALS_RELATIVE),
                "sha256": _sha(field_raw),
            },
            "quest_log_constants": {
                "path": str(QUEST_LOG_CONSTANTS_RELATIVE),
                "sha256": _sha(constants_raw),
            },
            "map_groups": {
                "path": str(MAP_GROUPS_RELATIVE),
                "sha256": _sha(groups_raw),
            },
            "physical_crosswalk": physical_input,
            "source_exit_manifest": {
                "path": exit_manifest["path"],
                "sha256": exit_manifest["sha256"],
                "source_rom_sha256": exit_manifest["source_rom_sha256"],
            },
        },
        "rows": pairs,
        "source_exit_manifest": exit_manifest,
        "project_component_proof": {
            "physical_map_count": len(project_graph),
            "row_count": len(project_runtime_rows),
            "direct_exit_row_count": len(project_runtime_rows)
                - len(project_multihop_rows),
            "multihop_rows": project_multihop_rows,
            "extra_component_memberships": [
                {
                    "location_id": row["index"],
                    "group": component[0],
                    "map": component[1],
                }
                for row in project_runtime_rows
                for component in row["inside_component"][1:]
            ],
            "runtime_policy": (
                "preserve only inside_component; on departure record the exact exit "
                "or clear stale pending state"
            ),
        },
        "source_runtime_section_contract": {
            "generic_and_league": (
                "resolve the inside physical map header at runtime exactly as Stage60; "
                "do not substitute the clean FireRed section value"
            ),
            "viridian_forest": (
                "retain the stock hard-coded MAPSEC_ROUTE_2 (102) special case"
            ),
            "mismatch_count": len(runtime_section_mismatches),
            "mismatches": runtime_section_mismatches,
        },
        "special_case_rewrites": [
            {
                "case": "VIRIDIAN_FOREST_TWO_EXITS",
                "location_indices": [5, 6],
                "outside_project_maps": [
                    by_index[5]["project"]["outside"],
                    by_index[6]["project"]["outside"],
                ],
                "recorded_project_section": 12,
                "preserve_location_id_increment": True,
            },
            {
                "case": "LEAGUE_GATE_ROUTE22_ROUTE23",
                "location_indices": [3, 4],
                "outside_project_maps": [
                    by_index[3]["project"]["outside"],
                    by_index[4]["project"]["outside"],
                ],
                "recorded_project_section": 32,
                "preserve_location_id_increment": True,
            },
            {
                "case": "ROCK_TUNNEL_DESTINATION_WARP_ID_DISAMBIGUATION",
                "location_indices": [22, 23],
                "destination_warp_ids": [0, 1],
                "save_block1_location_warp_id_offset": 6,
            },
            {
                "case": "SEAFOAM_DESTINATION_WARP_ID_DISAMBIGUATION",
                "location_indices": [42, 43],
                "destination_warp_ids": [0, 1],
                "save_block1_location_warp_id_offset": 6,
            },
            {
                "case": "ROCKET_HIDEOUT_GAME_CORNER_REARM",
                "game_corner_index": 32,
                "rocket_hideout_index": 35,
                "project_game_corner": by_index[32]["project"],
                "project_rocket_hideout": by_index[35]["project"],
            },
        ],
    }


def quest_log_transition_decision(
    crosswalk: Mapping[str, Any],
    *,
    namespace: str,
    pending_location: int,
    current_group: int,
    current_map: int,
    current_warp_id: int | None = None,
) -> dict[str, Any]:
    """C runtimeと共有するMSC17 transitionの実行可能なbranch契約。"""

    if namespace not in {"source", "project"}:
        raise ValueError(f"unknown Quest Log namespace: {namespace}")
    rows = crosswalk.get("rows")
    if not isinstance(rows, list) or len(rows) != 51:
        raise ValueError("Quest Log crosswalk rows missing")
    current = (current_group, current_map)

    def runtime_policy(index: int) -> Mapping[str, Any]:
        return rows[index][f"{namespace}_runtime_policy"]

    def rearm_location() -> int | None:
        for candidate in range(51):
            runtime = runtime_policy(candidate)
            if runtime["enabled"] and tuple(runtime["inside_component"][0]) == current:
                return candidate
        return None

    if not 0 <= pending_location < 51:
        return {
            "action": "CLEAR_PENDING",
            "rearm_location": rearm_location(),
            "reason": "OUT_OF_RANGE_TOKEN",
        }
    pending = runtime_policy(pending_location)
    if not pending["enabled"]:
        return {
            "action": "CLEAR_PENDING",
            "rearm_location": rearm_location(),
            "reason": "DISABLED_TOKEN",
        }
    if current in {
        tuple(value) for value in pending["inside_component"]
    }:
        return {
            "action": "KEEP_PENDING",
            "record_location": None,
            "rearm_location": None,
            "reason": "INSIDE_COMPONENT",
        }

    if pending_location in (3, 4):
        candidates = (3, 4)
    elif pending_location in (5, 6):
        candidates = (5, 6)
    elif pending_location in (22, 23):
        candidates = (22, 23)
    elif pending_location in (42, 43):
        candidates = (42, 43)
    else:
        candidates = (pending_location,)
    matches: list[int] = []
    for candidate in candidates:
        exit_row = runtime_policy(candidate)["record_exits"][0]
        if tuple(exit_row["map"]) != current:
            continue
        expected_warp = exit_row["destination_warp_id"]
        if expected_warp is not None and expected_warp != current_warp_id:
            continue
        matches.append(int(exit_row["location_id"]))
    if len(matches) == 1:
        recorded_location = matches[0]
        return {
            "action": "RECORD_EVENT_35_AND_CLEAR",
            "record_location": recorded_location,
            "rearm_location": (
                QUEST_LOG_GAME_CORNER_LOCATION
                if namespace == "project"
                and recorded_location == QUEST_LOG_ROCKET_HIDEOUT_LOCATION
                else rearm_location()
            ),
            "reason": "MEANING_REVIEWED_EXIT",
        }
    if len(matches) > 1:
        raise MapSectionConsumerPolicyError(
            f"Quest Log transition exit ambiguous: {namespace}/{pending_location}: "
            f"{matches}"
        )
    return {
        "action": "CLEAR_PENDING",
        "record_location": None,
        "rearm_location": rearm_location(),
        "reason": "COMPONENT_DEPARTURE_MISMATCH",
    }


def build_map_name_provenance_contract(
    root: Path, *, stage60: bytes | None = None
) -> dict[str, Any]:
    """GetMapName の低IDを、全物理mapとcaller provenanceから拘束する。"""

    if stage60 is None:
        stage60 = _read(root / STAGE60_ROM_RELATIVE, "Stage60 ROM")
    if len(stage60) != STAGE60_ROM_SIZE or _sha(stage60) != STAGE60_ROM_SHA256:
        raise MapSectionConsumerPolicyError("map-name contractのStage60 identity不一致")
    actual_hook = _rom_slice(
        stage60,
        MAP_NAME_HOOK_ADDRESS,
        len(MAP_NAME_HOOK_STAGE60_PREIMAGE),
        "Stage60 GetMapName entry",
    )
    if actual_hook != MAP_NAME_HOOK_STAGE60_PREIMAGE:
        raise MapSectionConsumerPolicyError(
            "Stage60 GetMapName hook preimage mismatch: "
            f"{actual_hook.hex()}"
        )

    groups_raw = _read(root / MAP_GROUPS_RELATIVE, "map_groups.json")
    _assert_sha(groups_raw, MAP_GROUPS_SHA256, "map_groups.json")
    try:
        groups = json.loads(groups_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MapSectionConsumerPolicyError(
            f"map-name map_groups parse error: {exc}"
        ) from exc
    order = groups.get("group_order")
    if not isinstance(order, list):
        raise MapSectionConsumerPolicyError("map-name map group_order missing")

    inventory: list[dict[str, Any]] = []
    for group, key in enumerate(order):
        maps = groups.get(key)
        if not isinstance(maps, list):
            raise MapSectionConsumerPolicyError(f"map-name source group missing: {key}")
        for number, name in enumerate(maps):
            section = _stage60_map_section(stage60, group, number)
            inventory.append({
                "group": group,
                "map": number,
                "map_key": name,
                "namespace": "VEGA_STOCK_NAMESPACE",
                "stage60_section": section,
                "stage61_section": section,
            })
    if len(inventory) != 425:
        raise MapSectionConsumerPolicyError(
            f"map-name source inventory count drifted: {len(inventory)}"
        )

    section_by_symbol = {
        row["symbol"]: (row["project_id"], row["source_id"])
        for row in load_source_crosswalk(root)
    }
    imported, imported_input = _load_imported_maps(root)
    observed_unused: dict[tuple[int, int], str] = {}
    imported_count = 0
    for name, row in imported.items():
        coordinate = (int(row["project_group"]), int(row["project_map"]))
        if coordinate in MAP_NAME_IMPORTED_UNUSED_COORDS:
            observed_unused[coordinate] = name
            continue
        try:
            project_section, source_section = section_by_symbol[
                row["section_symbol"]
            ]
        except KeyError as exc:
            raise MapSectionConsumerPolicyError(
                f"map-name imported section identity missing: {name}"
            ) from exc
        stage60_section = _stage60_map_section(stage60, *coordinate)
        if stage60_section != source_section:
            raise MapSectionConsumerPolicyError(
                f"map-name imported Stage60 section mismatch: {coordinate}: "
                f"{stage60_section} != {source_section}"
            )
        inventory.append({
            "group": coordinate[0],
            "map": coordinate[1],
            "map_key": name,
            "namespace": "PROJECT_KANTO_NAMESPACE",
            "stage60_section": stage60_section,
            "stage61_section": project_section,
        })
        imported_count += 1
    if observed_unused != MAP_NAME_IMPORTED_UNUSED_COORDS:
        raise MapSectionConsumerPolicyError(
            f"map-name unused imported coordinates drifted: {observed_unused}"
        )
    if imported_count != 253:
        raise MapSectionConsumerPolicyError(
            f"map-name imported inventory count drifted: {imported_count}"
        )

    inventory.sort(key=lambda row: (row["group"], row["map"], row["map_key"]))
    coordinates = [(row["group"], row["map"]) for row in inventory]
    if len(inventory) != 678 or len(set(coordinates)) != 678:
        raise MapSectionConsumerPolicyError(
            f"map-name exact physical inventory mismatch: {len(inventory)}/"
            f"{len(set(coordinates))}"
        )
    low_non_project = [
        row for row in inventory
        if row["namespace"] != "PROJECT_KANTO_NAMESPACE"
        and row["stage61_section"] < PROJECT_SECTION_COUNT
    ]
    if low_non_project:
        raise MapSectionConsumerPolicyError(
            f"non-Kanto physical map acquired project section: {low_non_project[:4]}"
        )
    if any(
        not 0 <= row["stage61_section"] < PROJECT_SECTION_COUNT
        for row in inventory
        if row["namespace"] == "PROJECT_KANTO_NAMESPACE"
    ):
        raise MapSectionConsumerPolicyError(
            "imported physical map escaped project section 0..52"
        )
    compact_raw = json.dumps(
        inventory, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    _assert_sha(
        compact_raw,
        MAP_NAME_PHYSICAL_INVENTORY_CANONICAL_SHA256,
        "map-name 678-map canonical inventory",
    )

    caller_counts = {
        name: len(audit.BL_XREFS[name][1])
        for name in ("GetMapName", "GetMapNameGeneric", "GetMapNameGeneric_")
    }
    if caller_counts != {
        "GetMapName": 4,
        "GetMapNameGeneric": 15,
        "GetMapNameGeneric_": 2,
    }:
        raise MapSectionConsumerPolicyError(
            f"map-name caller set drifted: {caller_counts}"
        )
    return {
        "consumer_id": "MSC-01",
        "status": "PROVENANCE_GATED",
        "hook": {
            "address": _hex(MAP_NAME_HOOK_ADDRESS),
            "stage60_preimage": actual_hook.hex(),
        },
        "physical_inventory": {
            "row_count": len(inventory),
            "source_non_kanto_count": 425,
            "project_kanto_count": imported_count,
            "non_kanto_project_id_count": len(low_non_project),
            "canonical_sha256": _sha(compact_raw),
            "imported_crosswalk": imported_input,
            "excluded_unused_coordinates": [
                {"group": group, "map": number, "map_key": name}
                for (group, number), name in sorted(observed_unused.items())
            ],
        },
        "caller_counts": caller_counts,
        "low_id_acceptance": [
            {
                "provenance": "CURRENT_PHYSICAL_MAP",
                "condition": (
                    "SaveBlock1 location is one of the exact 253 imported coordinates; "
                    "three unused group-98 holes are rejected"
                ),
                "consumers": "map popup, save menu, Town Map, Quest Log playback",
            },
            {
                "provenance": "PENDING_WARP_DESTINATION",
                "condition": (
                    "only direct GetMapName caller 0x080F93D0 (return 0x080F93D4) "
                    "may inspect WarpData; bounded imported group/map must resolve to "
                    "a header whose section equals the argument"
                ),
                "consumers": "pre-commit destination map preview",
            },
            {
                "provenance": "POKEMON_MET_LOCATION",
                "condition": (
                    "summary currentMon metLocation equals the argument and metGame is "
                    "FireRed/LeafGreen (4/5)"
                ),
                "consumers": "the two GetMapNameGeneric_ trainer-memo callers",
            },
        ],
        "rejection": (
            "map section 0..52 without one of the three provenances returns NULL/space-fill; "
            "Hoenn met-location values are never globally reinterpreted as project Kanto"
        ),
    }


def verify_stage60_contract(
    stage60: bytes,
    *,
    clean: bytes | None = None,
) -> dict[str, Any]:
    """全 Stage 60 preimage/extent と linked/dormant 境界を検証する。"""

    try:
        audit.validate_rom_identity(
            stage60,
            size=STAGE60_ROM_SIZE,
            sha256=STAGE60_ROM_SHA256,
            label="Stage 60",
        )
        if clean is not None:
            audit.validate_rom_identity(
                clean,
                size=CLEAN_ROM_SIZE,
                sha256=CLEAN_ROM_SHA256,
                label="clean FireRed JPN Rev.0",
            )
    except audit.MapSectionConsumerAuditError as exc:
        raise MapSectionConsumerPolicyError(str(exc)) from exc

    for site in (*ALL_CANDIDATE_PATCH_WINDOWS, *DORMANCY_GUARD_WINDOWS):
        actual = _rom_slice(stage60, site.address, len(site.expected), site.site_id)
        if actual != site.expected:
            raise MapSectionConsumerPolicyError(
                f"Stage60 preimage mismatch: {site.site_id}@{_hex(site.address)}: "
                f"expected={site.expected.hex()}, actual={actual.hex()}"
            )
    for extent in FUNCTION_EXTENTS:
        raw = _rom_slice(
            stage60,
            extent.start,
            extent.end_exclusive - extent.start,
            extent.extent_id,
        )
        if _sha(raw) != extent.sha256:
            raise MapSectionConsumerPolicyError(
                f"Stage60 function extent mismatch: {extent.extent_id}: "
                f"expected={extent.sha256}, actual={_sha(raw)}"
            )
    for extent in DATA_EXTENTS:
        raw = _rom_slice(stage60, extent.address, extent.size, extent.extent_id)
        if _sha(raw) != extent.sha256:
            raise MapSectionConsumerPolicyError(
                f"Stage60 data extent mismatch: {extent.extent_id}: "
                f"expected={extent.sha256}, actual={_sha(raw)}"
            )

    getter_sites = tuple(
        site.address
        for site in PATCH_WINDOWS
        if site.replacement_symbol == "Stage61MapSection_GetRaidCompatibleCurrent"
    )
    expected_getter_sites = (
        0x090F3838,
        0x090F3A90,
        0x090F3AE8,
        0x090F3B10,
        0x090F3B90,
        0x090F3FC0,
    )
    if getter_sites != expected_getter_sites:
        raise MapSectionConsumerPolicyError(f"Raid getter site set drifted: {getter_sites}")
    literal_hits = tuple(
        address
        for address in audit.find_word_occurrences(stage60, 0x08055B21)
        if 0x090F3000 <= address < 0x090F4500
    )
    if literal_hits != expected_getter_sites:
        raise MapSectionConsumerPolicyError(
            f"Raid inline GetCurrent literal roots drifted: {literal_hits}"
        )

    roamer_xrefs = audit.find_thumb_bl_xrefs(stage60, (0x09125ECC,))[0x09125ECC]
    if roamer_xrefs != (0x09097774, 0x0909777C):
        raise MapSectionConsumerPolicyError(
            f"roamer function xrefs drifted: {roamer_xrefs}"
        )
    cfru_warp_xrefs = audit.find_thumb_bl_xrefs(stage60, (0x0911FEC8,))[0x0911FEC8]
    cfru_warp_ptrs = tuple(
        sorted(
            set(audit.find_word_occurrences(stage60, 0x0911FEC8))
            | set(audit.find_word_occurrences(stage60, 0x0911FEC9))
        )
    )
    if cfru_warp_xrefs or cfru_warp_ptrs:
        raise MapSectionConsumerPolicyError(
            "CFRU WarpFadeOutScreen unexpectedly became reachable: "
            f"BL={cfru_warp_xrefs}, ptr={cfru_warp_ptrs}"
        )

    clean_comparisons: list[dict[str, Any]] = []
    if clean is not None:
        for site in DORMANCY_GUARD_WINDOWS:
            stage_bytes = _rom_slice(stage60, site.address, len(site.expected), site.site_id)
            clean_bytes = _rom_slice(clean, site.address, len(site.expected), site.site_id)
            if stage_bytes != clean_bytes:
                raise MapSectionConsumerPolicyError(
                    f"dormancy hook target differs from clean: {site.site_id}"
                )
            clean_comparisons.append(
                {"site_id": site.site_id, "stage60_equals_clean": True}
            )
        stock_warp = next(row for row in FUNCTION_EXTENTS if row.extent_id == "stock_warp")
        if _rom_slice(
            stage60,
            stock_warp.start,
            stock_warp.end_exclusive - stock_warp.start,
            "Stage60 stock WarpFadeOutScreen",
        ) != _rom_slice(
            clean,
            stock_warp.start,
            stock_warp.end_exclusive - stock_warp.start,
            "clean stock WarpFadeOutScreen",
        ):
            raise MapSectionConsumerPolicyError(
                "stock WarpFadeOutScreen differs from clean; MSC-23 dormancy changed"
            )

    return {
        "stage60_sha256": _sha(stage60),
        "patch_window_count": len(PATCH_WINDOWS),
        "conditional_alternative_patch_window_count": len(
            CONDITIONAL_ALTERNATIVE_PATCH_WINDOWS
        ),
        "function_extent_count": len(FUNCTION_EXTENTS),
        "data_extent_count": len(DATA_EXTENTS),
        "raid_inline_getter_literal_sites": [_hex(value) for value in getter_sites],
        "raid_single_entry_available": False,
        "raid_single_entry_reason": (
            "static GetRaidMapSectionId was fully inlined six times; globally replacing "
            "GetCurrentRegionMapSectionId would alter 19 unrelated CFRU literals"
        ),
        "roamer_direct_bl_xrefs": [_hex(value) for value in roamer_xrefs],
        "roamer_function_boundary_replacement_proven": True,
        "cfru_warp_direct_bl_xrefs": [],
        "cfru_warp_pointer_roots": [],
        "dormancy_clean_comparisons": clean_comparisons,
    }


def _add_occupancy(
    occupancy: dict[int, list[dict[str, str]]],
    flag_id: int,
    *,
    owner: str,
    source: str,
    symbol: str,
) -> None:
    if not 0 <= flag_id <= 0xFFFF:
        raise MapSectionConsumerPolicyError(f"flag ID out of u16 range: {flag_id}")
    occupancy.setdefault(flag_id, []).append(
        {"owner": owner, "source": source, "symbol": symbol}
    )


def _compress_ids(ids: Iterable[int]) -> list[tuple[int, int]]:
    values = sorted(set(ids))
    if not values:
        return []
    result: list[tuple[int, int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            result.append((start, previous))
            start = value
        previous = value
    result.append((start, previous))
    return result


def load_declared_flag_ownership(
    root: Path,
    *,
    additional_reserved_ranges: Sequence[tuple[str, int, int]] = (),
) -> dict[str, Any]:
    """既知 owner を統合する。これは global collision audit の代替ではない。"""

    occupancy: dict[int, list[dict[str, str]]] = {}
    inputs: list[dict[str, Any]] = []

    flags_raw, flag_rows = _read_csv(root / FLAGS_MANIFEST_RELATIVE, "flags manifest")
    required_flag_fields = {"flag_key", "id", "owner", "scope", "status"}
    if flag_rows and not required_flag_fields.issubset(flag_rows[0]):
        raise MapSectionConsumerPolicyError("flags manifest schema mismatch")
    seen_manifest: set[int] = set()
    for row in flag_rows:
        flag_id = int(row["id"], 0)
        if flag_id in seen_manifest:
            raise MapSectionConsumerPolicyError(
                f"flags manifest duplicate ID: {_hex(flag_id)}"
            )
        seen_manifest.add(flag_id)
        _add_occupancy(
            occupancy,
            flag_id,
            owner=row["owner"],
            source=str(FLAGS_MANIFEST_RELATIVE),
            symbol=row["flag_key"],
        )
    inputs.append(
        {
            "path": str(FLAGS_MANIFEST_RELATIVE),
            "sha256": _sha(flags_raw),
            "rows": len(flag_rows),
        }
    )

    registry_raw = _read(root / NAMESPACE_REGISTRY_RELATIVE, "Stage61 namespace registry")
    try:
        registry = json.loads(registry_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MapSectionConsumerPolicyError(f"namespace registry parse error: {exc}") from exc
    registry_ranges: list[dict[str, Any]] = []
    for row in registry.get("flags", []):
        owner = str(row["owner"])
        start = int(str(row["start"]), 0)
        end = int(str(row["end_inclusive"]), 0)
        count = int(row["count"])
        if end - start + 1 != count:
            raise MapSectionConsumerPolicyError(
                f"namespace range count mismatch: {owner}"
            )
        registry_ranges.append(
            {"owner": owner, "start": start, "end_inclusive": end, "count": count}
        )
        for flag_id in range(start, end + 1):
            _add_occupancy(
                occupancy,
                flag_id,
                owner=owner,
                source=str(NAMESPACE_REGISTRY_RELATIVE),
                symbol=owner,
            )
    inputs.append(
        {
            "path": str(NAMESPACE_REGISTRY_RELATIVE),
            "sha256": _sha(registry_raw),
            "ranges": len(registry_ranges),
        }
    )

    display_raw = _read(root / DISPLAY_AUDIT_CONFIG_RELATIVE, "Stage61 display config")
    try:
        display = json.loads(display_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MapSectionConsumerPolicyError(f"display config parse error: {exc}") from exc
    story = display.get("story", {})
    hidden_flags: list[int] = []
    for key in ("route12_hidden_flag", "route16_hidden_flag"):
        if key not in story:
            raise MapSectionConsumerPolicyError(f"display hidden flag missing: {key}")
        flag_id = int(str(story[key]), 0)
        hidden_flags.append(flag_id)
        _add_occupancy(
            occupancy,
            flag_id,
            owner="STAGE61_DISPLAY_STORY_HIDDEN_FLAGS",
            source=str(DISPLAY_AUDIT_CONFIG_RELATIVE),
            symbol=key,
        )
    if hidden_flags != [0x149E, 0x149F]:
        raise MapSectionConsumerPolicyError(
            f"display hidden flags drifted: {hidden_flags}"
        )
    inputs.append(
        {
            "path": str(DISPLAY_AUDIT_CONFIG_RELATIVE),
            "sha256": _sha(display_raw),
            "flags": [_hex(value) for value in hidden_flags],
        }
    )

    trainer_raw, trainer_rows = _read_csv(
        root / TRAINER_CONSUMERS_RELATIVE, "trainer runtime consumers"
    )
    if trainer_rows and not {"binding_mode", "runtime_trainer_id", "encounter_key"}.issubset(
        trainer_rows[0]
    ):
        raise MapSectionConsumerPolicyError("trainer consumer schema mismatch")
    trainer_ids: list[int] = []
    for row in trainer_rows:
        if row["binding_mode"] != "KANTO_NEW":
            continue
        flag_id = 0x0500 + int(row["runtime_trainer_id"])
        trainer_ids.append(flag_id)
        _add_occupancy(
            occupancy,
            flag_id,
            owner="KANTO_NEW_TRAINER_DEFEAT_FLAGS",
            source=str(TRAINER_CONSUMERS_RELATIVE),
            symbol=row["encounter_key"],
        )
    if len(trainer_ids) != 201 or len(set(trainer_ids)) != 201:
        raise MapSectionConsumerPolicyError(
            f"KANTO_NEW trainer flag set drifted: {len(trainer_ids)}"
        )
    inputs.append(
        {
            "path": str(TRAINER_CONSUMERS_RELATIVE),
            "sha256": _sha(trainer_raw),
            "kanto_new_flags": len(trainer_ids),
            "ranges": [
                {"start": _hex(start), "end_inclusive": _hex(end), "count": end - start + 1}
                for start, end in _compress_ids(trainer_ids)
            ],
        }
    )

    for owner, start, end in additional_reserved_ranges:
        if not owner or start > end:
            raise MapSectionConsumerPolicyError(
                f"invalid additional reserved range: {owner!r}/{start:#x}/{end:#x}"
            )
        for flag_id in range(start, end + 1):
            _add_occupancy(
                occupancy,
                flag_id,
                owner=owner,
                source="CALLER_ADDITIONAL_RESERVED_RANGE",
                symbol=owner,
            )

    duplicate_claims = {
        flag_id: claims for flag_id, claims in occupancy.items() if len(claims) > 1
    }
    if duplicate_claims:
        example_id = min(duplicate_claims)
        raise MapSectionConsumerPolicyError(
            f"declared flag owners already collide at {_hex(example_id)}: "
            f"{duplicate_claims[example_id]}"
        )

    unclaimed: list[dict[str, Any]] = []
    free_ids = [
        value
        for value in range(EXPANDED_FLAG_MIN, EXPANDED_FLAG_MAX + 1)
        if value not in occupancy
    ]
    for start, end in _compress_ids(free_ids):
        if end - start + 1 >= RAID_ROW_COUNT:
            unclaimed.append(
                {
                    "start": _hex(start),
                    "end_inclusive": _hex(end),
                    "count": end - start + 1,
                    "classification": "UNCLAIMED_BY_SCANNED_SOURCES_NOT_GLOBALLY_APPROVED",
                }
            )
    return {
        "occupancy": occupancy,
        "inputs": inputs,
        "registry_ranges": registry_ranges,
        "unclaimed_contiguous_windows_at_least_109": unclaimed,
    }


def validate_raid_flag_base(
    root: Path,
    raid_flag_base: int,
    *,
    intended_owner: str | None = None,
    additional_reserved_ranges: Sequence[tuple[str, int, int]] = (),
) -> dict[str, Any]:
    """109-bit Raid window を既知 ownership に対して検査する。"""

    if not isinstance(raid_flag_base, int) or isinstance(raid_flag_base, bool):
        raise MapSectionConsumerPolicyError("raid_flag_base must be an integer")
    raid_flag_end = raid_flag_base + RAID_ROW_COUNT - 1
    if raid_flag_base < EXPANDED_FLAG_MIN or raid_flag_end > EXPANDED_FLAG_MAX:
        raise MapSectionConsumerPolicyError(
            "Raid flag window outside expanded persistent range: "
            f"{_hex(raid_flag_base)}..{_hex(raid_flag_end)}"
        )
    ownership = load_declared_flag_ownership(
        root, additional_reserved_ranges=additional_reserved_ranges
    )
    occupancy = ownership["occupancy"]
    collisions: list[dict[str, Any]] = []
    intended_claimed: set[int] = set()
    for flag_id in range(raid_flag_base, raid_flag_end + 1):
        for claim in occupancy.get(flag_id, []):
            if intended_owner is not None and claim["owner"] == intended_owner:
                intended_claimed.add(flag_id)
            else:
                collisions.append({"flag": _hex(flag_id), **claim})
    if collisions:
        preview = collisions[:8]
        raise MapSectionConsumerPolicyError(
            "Raid flag base collision: "
            f"{_hex(raid_flag_base)}..{_hex(raid_flag_end)}: {preview}"
        )
    expected_window = set(range(raid_flag_base, raid_flag_end + 1))
    if intended_claimed and intended_claimed != expected_window:
        raise MapSectionConsumerPolicyError(
            "intended Raid owner only partially claims selected window: "
            f"claimed={len(intended_claimed)}, expected={RAID_ROW_COUNT}"
        )
    return {
        "base": _hex(raid_flag_base),
        "end_inclusive": _hex(raid_flag_end),
        "count": RAID_ROW_COUNT,
        "intended_owner": intended_owner,
        "status": (
            "PASS_ALREADY_CLAIMED_BY_INTENDED_OWNER"
            if intended_claimed
            else "PASS_UNCLAIMED_BY_DECLARED_OWNERS"
        ),
        "scope_warning": (
            "PASS は本 tool が列挙する owner に限定される。親の global collision "
            "audit が同じ base を承認するまで allocation 確定禁止。"
        ),
        "ownership_inputs": ownership["inputs"],
    }


def _build_flag_conflict_plan(
    root: Path,
    *,
    raid_flag_base: int | None,
    intended_owner: str | None,
    additional_reserved_ranges: Sequence[tuple[str, int, int]],
) -> dict[str, Any]:
    ownership = load_declared_flag_ownership(
        root, additional_reserved_ranges=additional_reserved_ranges
    )
    ranges = ownership["registry_ranges"]
    intersections: list[dict[str, Any]] = []
    covered: set[int] = set()
    for row in ranges:
        start = max(LEGACY_RAID_FLAG_BASE, row["start"])
        end = min(LEGACY_RAID_FLAG_END, row["end_inclusive"])
        if start <= end:
            intersections.append(
                {
                    "raid_owner": "CFRU_RAID_BATTLE_FLAGS",
                    "project_owner": row["owner"],
                    "start": _hex(start),
                    "end_inclusive": _hex(end),
                    "count": end - start + 1,
                }
            )
            covered.update(range(start, end + 1))
    expected_intersections = [
        ("TRAINER_ARCHIVE_DEFEAT_FLAGS", 0x1800, 0x1846, 71),
        ("KANTO_FULL_CFG_SOURCE_FLAGS", 0x1847, 0x186C, 38),
    ]
    actual_intersections = [
        (
            row["project_owner"],
            int(row["start"], 0),
            int(row["end_inclusive"], 0),
            row["count"],
        )
        for row in intersections
    ]
    if actual_intersections != expected_intersections or len(covered) != RAID_ROW_COUNT:
        raise MapSectionConsumerPolicyError(
            "legacy Raid/project conflict set drifted: "
            f"expected={expected_intersections}, actual={actual_intersections}"
        )

    selected = None
    if raid_flag_base is not None:
        selected = validate_raid_flag_base(
            root,
            raid_flag_base,
            intended_owner=intended_owner,
            additional_reserved_ranges=additional_reserved_ranges,
        )
    return {
        "severity": "CRITICAL",
        "legacy_raid_window": {
            "base": _hex(LEGACY_RAID_FLAG_BASE),
            "end_inclusive": _hex(LEGACY_RAID_FLAG_END),
            "count": RAID_ROW_COUNT,
            "first_raid_battle_flag": _hex(LEGACY_RAID_FLAG_BASE),
            "kanto_mapsec_count": RAID_ROW_COUNT,
        },
        "intersection_segments": intersections,
        "aliased_raid_flags": RAID_ROW_COUNT,
        "all_legacy_raid_flags_collide": True,
        "lossless_stage60_migration_possible": False,
        "ambiguity": (
            "Stage60 の 0x1800..0x1846 は Archive と Raid のどちらが set したか "
            "保存 bit だけでは復元不能。0x1847..0x186C も Stage61 namespace と "
            "Raid が同一 bit を所有するため、所有意味を同時に移送できない。"
        ),
        "options": [
            {
                "option": "MOVE_PROJECT_ARCHIVE_AND_STAGE61_WINDOW",
                "target_window_size": 256,
                "logical_id_changes": {
                    "archive_active": 71,
                    "stage61_active": 181,
                    "reserved_buffer": 4,
                    "total": 256,
                },
                "known_consumer_updates": {
                    "archive_trainerbattle_bindings": 71,
                    "stage61_generated_flag_assignments": 181,
                    "registry_or_reserved_assignments": 4,
                    "save_migration_routine": 1,
                },
                "stage60_save_compatibility": (
                    "Raid completion remains at legacy IDs, but Archive migration from "
                    "0x1800..0x1846 is ambiguous and can copy Raid bits as false defeats. "
                    "A blind 256-bit copy also turns pre-Stage61 Raid bits into CFG flags."
                ),
                "lossless": False,
                "risk": "HIGH_TOUCH_AND_AMBIGUOUS",
            },
            {
                "option": "MOVE_RAID_FLAGS_AT_FLAG_API_BOUNDARIES",
                "target_window_size": RAID_ROW_COUNT,
                "logical_id_changes": {"raid_flags": RAID_ROW_COUNT},
                "exact_stage60_pointer_repoints": {
                    "FlagGet": 2,
                    "FlagSet": 1,
                    "FlagClear": 2,
                    "total": 5,
                },
                "adapter_count": 3,
                "stage60_save_compatibility": (
                    "Archive/Stage61 observed bits remain in place. New Raid flags must be "
                    "initialized clear; old ambiguous Raid progress is deliberately not migrated, "
                    "so at most raids reappear rather than project progress being destroyed."
                ),
                "lossless": False,
                "risk": "LOWEST_TOUCH_WITH_EXPLICIT_RAID_PROGRESS_RESET",
            },
        ],
        "selected_architecture": "MOVE_RAID_FLAGS_AT_FLAG_API_BOUNDARIES",
        "selected_base": selected,
        "explicitly_rejected_bases": [
            {
                "base": "0x14A0",
                "end_inclusive": "0x150C",
                "reason": (
                    "0x1500..0x150C overlaps KANTO_NEW trainer defeat flags; "
                    "caller correction makes this candidate permanently invalid"
                ),
            }
        ],
        "declared_ownership_inputs": ownership["inputs"],
        "declared_owned_flag_count": len(ownership["occupancy"]),
        "base_parameter": {
            "required_before_integration": True,
            "provided": raid_flag_base is not None,
            "count": RAID_ROW_COUNT,
            "valid_numeric_domain": [
                _hex(EXPANDED_FLAG_MIN),
                _hex(EXPANDED_FLAG_MAX - RAID_ROW_COUNT + 1),
            ],
            "global_collision_audit_required": True,
            "intended_owner_parameter": intended_owner,
        },
        "unclaimed_windows_observed_not_approved": ownership[
            "unclaimed_contiguous_windows_at_least_109"
        ],
    }


def _abi(
    function: str,
    address: int,
    prototype: str,
    args: Mapping[str, str],
    result: str,
    *,
    context: str = "",
) -> dict[str, Any]:
    return {
        "function": function,
        "stage60_address": _hex(address),
        "calling_convention": "Thumb AAPCS",
        "prototype": prototype,
        "register_arguments": dict(args),
        "result": result,
        "context": context,
    }


def _consumer_contracts() -> list[dict[str, Any]]:
    imported_rule = (
        "physical group 96..98 の時だけ project 0..52 を exact source crosswalk で変換"
    )
    preserve_rule = "group 96..98 以外では入力 section/group/map の stock 意味を保持"
    return [
        {
            "consumer_id": "MSC-04",
            "domain": "overworld music override guard",
            "priority": "HIGH",
            "abis": [_abi("Overworld_MusicCanOverrideMapMusic", 0x080559E4, "bool32(u16 music)", {"r0": "music u16"}, "r0 bool32")],
            "transform": imported_rule,
            "project_special_cases": {"42": 132, "33": 123, "9": 97},
            "non_imported_policy": preserve_rule,
            "unsupported_imported_policy": "TRUE (music override allowed; no invalid table access)",
            "implementation": "whole-function semantic reimplementation",
            "patch_site_ids": ["msc04_music_entry"],
        },
        {
            "consumer_id": "MSC-05",
            "domain": "map preview index and stock warp preview",
            "priority": "HIGH",
            "abis": [
                _abi("GetMapPreviewScreenIdx", 0x080F9150, "u8(u8 mapsec)", {"r0": "mapsec u8"}, "r0 index 0..28"),
                _abi("WarpFadeOutScreen", 0x0807D378, "void(void)", {}, "none", context="gWarpDestination@0x0203F01C and current save location"),
            ],
            "transform": imported_rule,
            "destination_rule": "destination group is gWarpDestination.mapGroup; canonicalize destination and current before equality/preview lookup",
            "prohibited_shortcut": "do not normalize a low mapsec merely because current OR destination is imported; provenance must correspond to that exact argument",
            "non_imported_policy": preserve_rule,
            "unsupported_imported_policy": "preview index=MPS_COUNT(28); Warp path treats preview as absent",
            "implementation": "two whole-function semantic reimplementations sharing one normalizer",
            "patch_site_ids": ["msc05_preview_index_entry", "msc05_stock_warp_fade_entry"],
        },
        {
            "consumer_id": "MSC-06",
            "domain": "Town Map dungeon name/flavor/preview",
            "priority": "HIGH",
            "abis": [
                _abi("GetDungeonFlavorText", 0x080C2AC4, "const u8 *(u16 mapsec)", {"r0": "mapsec u16"}, "r0 text pointer"),
                _abi("GetDungeonName", 0x080C2B04, "const u8 *(u16 mapsec)", {"r0": "mapsec u16"}, "r0 text pointer"),
                _abi("GetDungeonMapPreviewScreenInfo", 0x080F95B0, "const struct MapPreviewScreen *(u8 mapsec)", {"r0": "mapsec u8"}, "r0 pointer or NULL"),
            ],
            "transform": imported_rule,
            "non_imported_policy": preserve_rule,
            "unsupported_imported_policy": "name/flavor=gText_RegionMap_NoData; preview=NULL",
            "implementation": "three whole-function semantic reimplementations",
            "patch_site_ids": ["msc06_dungeon_flavor_entry", "msc06_dungeon_name_entry"],
            "optional_patch_site_ids": ["msc06_dungeon_preview_info_entry"],
            "transitive_coverage": "GetDungeonMapPreviewScreenInfo calls patched GetMapPreviewScreenIdx",
        },
        {
            "consumer_id": "MSC-07",
            "domain": "Cerulean Cave Town Map visibility",
            "priority": "HIGH",
            "abis": [
                _abi("GetDungeonMapsecUnderCursor", 0x080C4764, "u16(void)", {}, "r0 mapsec/MAPSEC_NONE"),
                _abi("CreateDungeonIcons internal gate", 0x080C5A14, "naked continuation", {"r0": "mapsec", "r4": "same mapsec"}, "branches to 0x080C5A1E/24/68", context="preserve r4-r10 and loop state"),
            ],
            "transform": "imported group: project 51; stock/nonimport: source 141",
            "unlock_flag": "FLAG_SYS_CAN_LINK_WITH_RS (0x0844) is preserved",
            "non_imported_policy": preserve_rule,
            "implementation": "one whole function plus one internal continuation",
            "patch_site_ids": ["msc07_dungeon_cursor_entry", "msc07_dungeon_icon_gate"],
            "conditional_alternative_patch_site_ids": [
                "msc07_dungeon_cursor_constant_only",
                "msc07_dungeon_icon_constant_only",
            ],
            "alternative_gate": "non-imported Town Map path must be proven unreachable; otherwise unconditional 141->51 rewrites violate preservation",
        },
        {
            "consumer_id": "MSC-10",
            "domain": "Pokémon summary met-location classifier",
            "priority": "HIGH",
            "abis": [_abi("MapSecIsInKantoOrSevii", 0x0813BFFC, "bool32(u8 mapsec)", {"r0": "persisted metLocation"}, "r0 bool32", context="sMonSummaryScreen pointer slot 0x0203B0B4; currentMon offset 0x323C; MON_DATA_MET_GAME=0x25")],
            "transform": "stock 88..196 stays TRUE; project 0..52 is TRUE only for metGame FireRed(4)/LeafGreen(5)",
            "non_imported_policy": "Ruby/Sapphire/Emerald project-range met locations remain FALSE; stock 88..196 unchanged",
            "unsupported_policy": "FALSE",
            "implementation": "whole-function contextual reimplementation; physical group is unavailable for persisted metadata",
            "patch_site_ids": ["msc10_summary_classifier_entry"],
        },
        {
            "consumer_id": "MSC-11",
            "domain": "Pokédex wild-header map section",
            "priority": "HIGH",
            "abis": [_abi("GetMapSecIdFromWildMonHeader", 0x0813D388, "u16(const struct WildPokemonHeader *header)", {"r0": "header pointer; bytes0/1=group/map"}, "r0 mapsec u16")],
            "transform": "resolve header group/map, then apply crosswalk only when header group is 96..98",
            "non_imported_policy": preserve_rule,
            "unsupported_imported_policy": "MAPSEC_NONE (197), so linear Dex-area search yields no marker",
            "implementation": "whole-function semantic reimplementation",
            "patch_site_ids": ["msc11_wild_header_mapsec_entry"],
        },
        {
            "consumer_id": "MSC-15",
            "domain": "Quest Log departed-gym narration",
            "priority": "MEDIUM",
            "abis": [_abi("LoadEvent_DepartedLocation internal gym compare", 0x08115DC8, "naked continuation", {"r5": "event record", "r6": "locationId", "r4": "badge index", "r2": "gym source-section table", "r7": "event record + 2"}, "canonicalize r1, replay ldrb/add/ldrb/cmp, then execute bne@0x08115DD0")],
            "project_to_source_gym_map": {"2": 90, "3": 91, "5": 93, "6": 94, "7": 95, "10": 98, "8": 96, "1": 89},
            "non_imported_policy": "all other stored values unchanged",
            "implementation": "single internal naked continuation at proven QL_DEPARTED_GYM branch",
            "patch_site_ids": ["msc15_quest_log_gym_compare"],
        },
        {
            "consumer_id": "MSC-16",
            "domain": "Quest Log Teleport home narration",
            "priority": "MEDIUM",
            "abis": [_abi("LoadEvent_UsedFieldMove internal Teleport branch", 0x08115F64, "naked continuation", {"r5": "event record body"}, "home->0x08115F6C, center->0x08115F84")],
            "transform": "stored mapsec project Pallet=0 or stock Pallet=88 selects Home",
            "non_imported_policy": "all other values select Pokémon Center as stock",
            "implementation": "single internal branch continuation; Home text pointer 0x02021C74",
            "patch_site_ids": ["msc16_quest_log_teleport_home"],
        },
        {
            "consumer_id": "MSC-17",
            "domain": "Quest Log inside/outside physical map pairs",
            "priority": "HIGH",
            "abis": [
                _abi("QuestLog_CheckDepartingIndoorsMap", 0x080CD6AC, "void(void)", {}, "none"),
                _abi("QuestLog_TryRecordDepartedLocation", 0x080CD714, "void(void)", {}, "none"),
            ],
            "transform": "current physical group 96..98 dispatches to the generated project table; otherwise 49 enabled Vega rows use exact rooted-warp meaning-reviewed exits and two erased-event rows fail closed",
            "required_crosswalk": "quest_log_physical_crosswalk.rows",
            "required_exit_manifest": str(QUEST_LOG_EXIT_MANIFEST_RELATIVE),
            "special_cases_required": ["VIRIDIAN_FOREST_TWO_EXITS", "LEAGUE_GATE_ROUTE22_ROUTE23", "ROCK_TUNNEL_DESTINATION_WARP_ID_DISAMBIGUATION", "SEAFOAM_DESTINATION_WARP_ID_DISAMBIGUATION", "ROCKET_HIDEOUT_GAME_CORNER_REARM"],
            "non_imported_policy": (
                "preserve an armed token inside its reviewed component; on component "
                "departure record only a matching reviewed exit, otherwise clear stale "
                "state; generic/League section comes from the Stage60 inside header"
            ),
            "implementation": "two whole-function semantic reimplementations; source table is generated from the pinned exit manifest; SaveBlock1 location.warpId selects Rock/Seafoam aliases without coordinate magic",
            "patch_site_ids": ["msc17_check_departing_entry", "msc17_record_departed_entry"],
        },
        {
            "consumer_id": "MSC-21",
            "domain": "CFRU Raid map-section table and completion flags",
            "priority": "CRITICAL",
            "abis": [
                _abi("Stage61MapSection_GetRaidCompatibleCurrent", 0, "u8(void)", {}, "r0 safe source section 87..195"),
                _abi("Stage61MapSection_RaidFlagGet", 0, "bool8(u16 flag)", {"r0": "legacy flag ID"}, "r0 bool8"),
                _abi("Stage61MapSection_RaidFlagSet", 0, "void(u16 flag)", {"r0": "legacy flag ID"}, "none"),
                _abi("Stage61MapSection_RaidFlagClear", 0, "void(u16 flag)", {"r0": "legacy flag ID"}, "none"),
            ],
            "transform": "groups 96..98: project->source; invalid imported or nonimport outside 87..195 -> 87 sentinel; supported nonimport 87..195 unchanged",
            "range_assertion": "inline u8(source-87) must be 0..108 before all table/flag uses",
            "single_entry_finding": "NO: static GetRaidMapSectionId is fully inlined at six functions",
            "minimal_systemic_fix": "six exact GetCurrentRegionMapSectionId literal repoints to one shared resolver; never replace global GetCurrentRegionMapSectionId",
            "flag_fix": "five exact FlagGet/Set/Clear literal repoints to three ABI-compatible adapters; translate only 0x1800..0x186C to parameterized new base and pass through all other IDs",
            "unsupported_imported_policy": "row 0 (MAPSEC_DYNAMIC sentinel); never dereference outside 109 rows",
            "patch_site_ids": [row.site_id for row in PATCH_WINDOWS if row.consumer_id == "MSC-21"],
        },
        {
            "consumer_id": "MSC-22",
            "domain": "CFRU Town Map roamer sprites",
            "priority": "CRITICAL",
            "abis": [_abi("CreateTownMapRoamerSprites", 0x09125ECC, "void(void)", {}, "none")],
            "transform": "for each roamer use stored group/map; imported project->source->source-88, nonimport source88..196->source-88",
            "range_assertion": "skip sprite unless index is 0..108 before both corner and dimension table reads",
            "unsupported_imported_policy": "skip this roamer sprite",
            "non_imported_policy": "source 88..196 exact; invalid sections skip",
            "function_boundary_finding": "YES: one 0x108-byte function, two direct BL stubs, entry replacement covers every loop iteration",
            "dormancy": "linked stubs exist at 0x09097774/7C, but BPRJ-translated stock hook targets 0x080C5A90 and 0x080C23F0 equal clean and are unpatched",
            "implementation": "one whole-function replacement; patch before activating either dormant hook",
            "patch_site_ids": ["msc22_roamer_entry"],
            "conditional_alternative_patch_site_ids": [
                "msc22_roamer_total_corners_pointer",
                "msc22_roamer_total_dimensions_pointer",
            ],
            "alternative_gate": "total 256-row tables prove memory safety only; all active roamer map groups/sections must be constrained or non-imported low IDs can be shown as Kanto",
        },
        {
            "consumer_id": "MSC-23",
            "domain": "linked CFRU warp preview clone",
            "priority": "MEDIUM",
            "abis": [_abi("CFRU WarpFadeOutScreen", 0x0911FEC8, "void(void)", {}, "none", context="same sWarpDestination/current map context as MSC-05")],
            "transform": imported_rule,
            "non_imported_policy": preserve_rule,
            "dormancy": "no direct BL or function-pointer root; active stock WarpFadeOutScreen remains clean in Stage60",
            "implementation": "whole-function replacement must exist before any future repoint; otherwise retain explicit dormant guard",
            "patch_site_ids": ["msc23_cfru_warp_fade_entry"],
        },
    ]


def inspect_candidate(
    candidate: bytes,
    *,
    expected_patches: Mapping[str, bytes] | None = None,
    require_all: bool = False,
) -> dict[str, Any]:
    """candidate site を観測し、指定された exact patch bytes は必ず検証する。"""

    if len(candidate) != STAGE60_ROM_SIZE:
        raise MapSectionConsumerPolicyError(
            f"candidate size mismatch: expected={STAGE60_ROM_SIZE}, actual={len(candidate)}"
        )
    expected_patches = dict(expected_patches or {})
    known_ids = {site.site_id for site in ALL_CANDIDATE_PATCH_WINDOWS}
    unknown = sorted(set(expected_patches) - known_ids)
    if unknown:
        raise MapSectionConsumerPolicyError(f"unknown candidate patch site IDs: {unknown}")
    if require_all:
        required_ids = {
            site.site_id
            for site in PATCH_WINDOWS
            if site.install_condition == "REQUIRED"
        }
        missing = sorted(required_ids - set(expected_patches))
        if missing:
            raise MapSectionConsumerPolicyError(
                f"candidate exact assertions missing required sites: {missing}"
            )
    rows: list[dict[str, Any]] = []
    for site in ALL_CANDIDATE_PATCH_WINDOWS:
        asserted = expected_patches.get(site.site_id)
        read_size = len(asserted) if asserted is not None else len(site.expected)
        actual = _rom_slice(candidate, site.address, read_size, site.site_id)
        if asserted is not None and len(asserted) != site.write_size:
            raise MapSectionConsumerPolicyError(
                f"candidate expected patch size mismatch: {site.site_id}: "
                f"expected write_size={site.write_size}, supplied={len(asserted)}"
            )
        if asserted is not None and actual != asserted:
            raise MapSectionConsumerPolicyError(
                f"candidate patch mismatch: {site.site_id}@{_hex(site.address)}: "
                f"expected={asserted.hex()}, actual={actual.hex()}"
            )
        stage60_prefix = site.expected[:read_size]
        covering_assertions = sorted(
            asserted_site.site_id
            for asserted_site in ALL_CANDIDATE_PATCH_WINDOWS
            if asserted_site.site_id in expected_patches
            and asserted_site.site_id != site.site_id
            and asserted_site.address <= site.address
            and site.address + read_size
                <= asserted_site.address + asserted_site.write_size
        )
        state = (
            "EXACT_PATCH_ASSERTION_PASS"
            if asserted is not None
            else "STAGE60_PREIMAGE"
            if actual == stage60_prefix
            else "COVERED_BY_EXACT_PARENT_ASSERTION"
            if covering_assertions
            else "MODIFIED_WITHOUT_EXACT_ASSERTION"
        )
        rows.append(
            {
                "site_id": site.site_id,
                "address": _hex(site.address),
                "state": state,
                "actual_hex": actual.hex(),
                "asserted_patch_hex": None if asserted is None else asserted.hex(),
                "covering_exact_site_ids": covering_assertions,
            }
        )
    dormancy_rows: list[dict[str, Any]] = []
    for site in DORMANCY_GUARD_WINDOWS:
        actual = _rom_slice(candidate, site.address, len(site.expected), site.site_id)
        dormancy_rows.append(
            {
                "site_id": site.site_id,
                "address": _hex(site.address),
                "state": (
                    "DORMANT_STAGE60_PREIMAGE"
                    if actual == site.expected
                    else "ACTIVATED_OR_MODIFIED"
                ),
                "actual_hex": actual.hex(),
                "expected_dormant_hex": site.expected.hex(),
            }
        )
    return {
        "size": len(candidate),
        "sha256": _sha(candidate),
        "exact_assertion_count": len(expected_patches),
        "require_all": require_all,
        "sites": rows,
        "dormancy_guards": dormancy_rows,
    }


def verify_candidate_patch_contract(
    candidate: bytes,
    expected_patches: Mapping[str, bytes],
    *,
    require_all: bool = True,
    accepted_conditional_proofs: Sequence[str] = (),
) -> dict[str, Any]:
    """統合後 ROM を site 単位 exact bytes で fail-closed 検証する。"""

    report = inspect_candidate(
        candidate, expected_patches=expected_patches, require_all=require_all
    )
    roamer_active = any(
        row["state"] == "ACTIVATED_OR_MODIFIED"
        for row in report["dormancy_guards"]
        if row["site_id"].startswith("msc22_roamer_activation_")
    )
    if roamer_active and "msc22_roamer_entry" not in expected_patches:
        total_table_sites = {
            "msc22_roamer_total_corners_pointer",
            "msc22_roamer_total_dimensions_pointer",
        }
        proof_token = "MSC22_ALL_ACTIVE_ROAMER_SECTION_DOMAIN_PROVEN"
        if not (
            total_table_sites.issubset(expected_patches)
            and proof_token in accepted_conditional_proofs
        ):
            raise MapSectionConsumerPolicyError(
                "roamer hook is active without a group-provenance-safe whole-function "
                "patch; total-table alternative additionally requires exact assertions "
                f"and proof token {proof_token}"
            )
    report["accepted_conditional_proofs"] = list(accepted_conditional_proofs)
    report["roamer_activation_contract"] = (
        "PASS" if roamer_active else "NOT_ACTIVE"
    )
    return report


def pointer_patch_expectations(
    replacement_symbols: Mapping[str, int],
) -> dict[str, bytes]:
    """literal repoint site の exact little-endian Thumb pointer を生成する。"""

    result: dict[str, bytes] = {}
    for site in PATCH_WINDOWS:
        if site.patch_kind != "LITERAL_THUMB_FUNCTION_POINTER_REPOINT":
            continue
        if site.replacement_symbol not in replacement_symbols:
            raise MapSectionConsumerPolicyError(
                f"replacement symbol address missing: {site.replacement_symbol}"
            )
        address = replacement_symbols[site.replacement_symbol]
        if not ROM_BASE <= address < ROM_BASE + STAGE60_ROM_SIZE:
            raise MapSectionConsumerPolicyError(
                f"replacement symbol outside ROM: {site.replacement_symbol}={_hex(address)}"
            )
        result[site.site_id] = struct.pack("<I", address | 1)
    return result


def candidate_patch_expectations(
    replacement_symbols: Mapping[str, int],
    *,
    site_ids: Sequence[str] | None = None,
) -> dict[str, bytes]:
    """symbol map から standard Stage61 exact patch bytes を生成する。

    ``site_ids`` 省略時は ``install_condition == REQUIRED`` の site だけを
    対象にする。conditional alternative を採用する caller はその site IDs を
    明示し、対応する追加証明も report に添付しなければならない。
    """

    by_id = {site.site_id: site for site in ALL_CANDIDATE_PATCH_WINDOWS}
    selected_ids = (
        [
            site.site_id
            for site in PATCH_WINDOWS
            if site.install_condition == "REQUIRED"
        ]
        if site_ids is None
        else list(site_ids)
    )
    if len(selected_ids) != len(set(selected_ids)):
        raise MapSectionConsumerPolicyError("candidate site IDs contain duplicates")
    unknown = sorted(set(selected_ids) - set(by_id))
    if unknown:
        raise MapSectionConsumerPolicyError(f"unknown candidate patch site IDs: {unknown}")

    result: dict[str, bytes] = {}
    for site_id in selected_ids:
        site = by_id[site_id]
        fixed = FIXED_PATCH_BYTES.get(site_id)
        if fixed is not None:
            if len(fixed) != site.write_size:
                raise MapSectionConsumerPolicyError(
                    f"fixed patch size drifted: {site_id}"
                )
            result[site_id] = fixed
            continue
        if site.replacement_symbol not in replacement_symbols:
            raise MapSectionConsumerPolicyError(
                f"replacement symbol address missing: {site.replacement_symbol}"
            )
        target = replacement_symbols[site.replacement_symbol]
        if (
            not isinstance(target, int)
            or isinstance(target, bool)
            or not ROM_BASE <= target < ROM_BASE + STAGE60_ROM_SIZE
        ):
            raise MapSectionConsumerPolicyError(
                f"replacement symbol outside ROM: {site.replacement_symbol}={target!r}"
            )
        if site.patch_kind == "LITERAL_THUMB_FUNCTION_POINTER_REPOINT":
            patch = struct.pack("<I", target | 1)
        elif site.patch_kind == "LITERAL_DATA_POINTER_REPOINT":
            patch = struct.pack("<I", target & ~1)
        elif site.patch_kind in {
            "THUMB_ABSOLUTE_JUMP_WHOLE_FUNCTION",
            "THUMB_ABSOLUTE_JUMP_INTERNAL_CONTINUATION",
            "THUMB_ABSOLUTE_JUMP_INTERNAL_BRANCH",
        }:
            patch = struct.pack("<HHI", 0x4B00, 0x4718, target | 1)
        else:
            raise MapSectionConsumerPolicyError(
                f"no exact patch encoder for {site_id}: {site.patch_kind}"
            )
        if len(patch) != site.write_size:
            raise MapSectionConsumerPolicyError(
                f"encoded patch size mismatch: {site_id}: "
                f"expected={site.write_size}, actual={len(patch)}"
            )
        result[site_id] = patch
    return result


def build_policy_plan(
    root: Path,
    *,
    stage60_path: Path | None = None,
    candidate_path: Path | None = None,
    candidate_expected_patches: Mapping[str, bytes] | None = None,
    raid_flag_base: int | None = None,
    raid_flag_owner: str | None = None,
    additional_reserved_ranges: Sequence[tuple[str, int, int]] = (),
) -> dict[str, Any]:
    root = root.resolve()
    stage60_file = stage60_path or root / STAGE60_ROM_RELATIVE
    if not stage60_file.is_absolute():
        stage60_file = root / stage60_file
    clean_file = root / CLEAN_ROM_RELATIVE
    stage60 = _read(stage60_file, "Stage60 ROM")
    clean = _read(clean_file, "clean FireRed ROM")
    binary_proof = verify_stage60_contract(stage60, clean=clean)
    crosswalk = load_source_crosswalk(root)
    quest = build_quest_log_physical_crosswalk(root, stage60=stage60)
    map_name_provenance = build_map_name_provenance_contract(
        root, stage60=stage60
    )
    flag_plan = _build_flag_conflict_plan(
        root,
        raid_flag_base=raid_flag_base,
        intended_owner=raid_flag_owner,
        additional_reserved_ranges=additional_reserved_ranges,
    )
    consumers = _consumer_contracts()
    required_ids = {
        "MSC-04", "MSC-05", "MSC-06", "MSC-07", "MSC-10", "MSC-11",
        "MSC-15", "MSC-16", "MSC-17", "MSC-21", "MSC-22", "MSC-23",
    }
    if {row["consumer_id"] for row in consumers} != required_ids:
        raise MapSectionConsumerPolicyError("consumer policy set drifted")
    sites_by_id = {site.site_id: site for site in ALL_CANDIDATE_PATCH_WINDOWS}
    for consumer in consumers:
        declared_site_ids = [
            *consumer["patch_site_ids"],
            *consumer.get("optional_patch_site_ids", []),
            *consumer.get("conditional_alternative_patch_site_ids", []),
        ]
        for site_id in declared_site_ids:
            if site_id not in sites_by_id or sites_by_id[site_id].consumer_id != consumer["consumer_id"]:
                raise MapSectionConsumerPolicyError(
                    f"consumer/site ownership mismatch: {consumer['consumer_id']}/{site_id}"
                )

    status = (
        "READY_WITH_CALLER_VALIDATED_RAID_FLAG_BASE"
        if raid_flag_base is not None
        else "READY_EXCEPT_RAID_FLAG_BASE_REQUIRES_GLOBAL_COLLISION_AUDIT"
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
        "policy": "STAGE61_MAP_SECTION_CONSUMER_PERMANENT_FIX_CONTRACT",
        "status": status,
        "scope": {
            "project_map_sections": [0, 52],
            "source_map_sections": [88, 142],
            "imported_physical_groups": list(IMPORTED_PHYSICAL_GROUPS),
            "invariant": (
                "project->source conversion occurs only with an explicit physical/provenance "
                "context; other maps retain stock semantics"
            ),
        },
        "inputs": {
            "stage60_rom": {
                "path": str(stage60_file),
                "size": len(stage60),
                "sha256": _sha(stage60),
            },
            "clean_rom": {
                "path": str(clean_file),
                "size": len(clean),
                "sha256": _sha(clean),
            },
            "map_section_manifest": {
                "path": str(MAP_SECTION_MANIFEST_RELATIVE),
                "sha256": audit.MAP_SECTION_MANIFEST_SHA256,
                "rows": len(crosswalk),
            },
        },
        "source_map_section_crosswalk": crosswalk,
        "map_name_provenance_contract": map_name_provenance,
        "shared_primitives": {
            "project_to_source": {
                "prototype": "bool8 Stage61MapSection_ProjectToSource(u8 project, u8 *source)",
                "table_rows": PROJECT_SECTION_COUNT,
                "invalid": "FALSE; caller chooses consumer-specific sentinel",
            },
            "raid_source_resolver": {
                "prototype": "u8 Stage61MapSection_GetRaidCompatibleCurrent(void)",
                "current_physical_group_source": "gSaveBlock1Ptr->location.mapGroup",
                "imported": "project 0..52 -> source; invalid -> MAPSEC_DYNAMIC(87)",
                "non_imported": "source 87..195 unchanged; other -> 87",
                "postcondition": "u8(result-87) in 0..108",
            },
            "raid_flag_adapters": {
                "legacy_input_range": [_hex(LEGACY_RAID_FLAG_BASE), _hex(LEGACY_RAID_FLAG_END)],
                "translation": "newBase + (flag - 0x1800)",
                "outside_range": "pass through unchanged",
                "new_base": None if raid_flag_base is None else _hex(raid_flag_base),
            },
        },
        "flag_ownership": flag_plan,
        "consumers": consumers,
        "quest_log_physical_crosswalk": quest,
        "patch_windows": [site.to_report() for site in PATCH_WINDOWS],
        "conditional_alternative_patch_windows": [
            site.to_report() for site in CONDITIONAL_ALTERNATIVE_PATCH_WINDOWS
        ],
        "candidate_patch_encoding": {
            "thumb_absolute_jump_8": "00 4B 18 47 <target|1 little-endian u32>",
            "thumb_function_literal_4": "<target|1 little-endian u32>",
            "data_pointer_literal_4": "<target&~1 little-endian u32>",
            "default_required_site_ids": [
                site.site_id
                for site in PATCH_WINDOWS
                if site.install_condition == "REQUIRED"
            ],
            "conditional_proof_tokens": {
                "MSC22_ALL_ACTIVE_ROAMER_SECTION_DOMAIN_PROVEN": (
                    "required with both 256-row table pointer assertions when the "
                    "whole-function roamer patch is not selected"
                )
            },
            "api": "candidate_patch_expectations + verify_candidate_patch_contract",
        },
        "dormancy_guard_windows": [site.to_report() for site in DORMANCY_GUARD_WINDOWS],
        "function_extents": [extent.to_report() for extent in FUNCTION_EXTENTS],
        "data_extents": [extent.to_report() for extent in DATA_EXTENTS],
        "binary_proof": binary_proof,
        "integration_gates": [
            "Stage60 ROM exact SHA and every preimage/extent must pass before patching",
            "all 53 source crosswalk rows and all 51 Quest Log physical pairs must pass",
            "Raid base must be supplied and approved by the parent global collision audit",
            "six Raid getter literals must all target the one shared resolver",
            "five Raid flag API literals must all target the three range-filtering adapters",
            "candidate must pass exact per-site patch assertions; modified-without-assertion is not PASS",
            "MSC-05 warp preview must distinguish current and destination group; an OR-combined context predicate is rejected",
            "MSC-07 two-byte constants and MSC-22 total tables are conditional alternatives, not group-provenance-safe defaults",
            "roamer/CFRU warp fixes must precede activation of their dormant hooks",
        ],
    }
    if candidate_path is not None:
        candidate_file = candidate_path if candidate_path.is_absolute() else root / candidate_path
        candidate = _read(candidate_file, "candidate ROM")
        report["candidate"] = inspect_candidate(
            candidate,
            expected_patches=candidate_expected_patches,
            require_all=False,
        )
    return report


def _parse_int(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"integer expected: {value}") from exc


def _parse_reserved_range(value: str) -> tuple[str, int, int]:
    match = re.fullmatch(r"([^:]+):(0[xX][0-9a-fA-F]+|\d+)-(0[xX][0-9a-fA-F]+|\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError("reserved range must be OWNER:START-END")
    owner, start, end = match.groups()
    return owner, int(start, 0), int(end, 0)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--stage60-rom", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--raid-flag-base", type=_parse_int)
    parser.add_argument("--raid-flag-owner")
    parser.add_argument(
        "--reserved-flag-range",
        action="append",
        default=[],
        type=_parse_reserved_range,
        metavar="OWNER:START-END",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_policy_plan(
            args.root,
            stage60_path=args.stage60_rom,
            candidate_path=args.candidate,
            raid_flag_base=args.raid_flag_base,
            raid_flag_owner=args.raid_flag_owner,
            additional_reserved_ranges=args.reserved_flag_range,
        )
    except MapSectionConsumerPolicyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
