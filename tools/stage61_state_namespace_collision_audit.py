#!/usr/bin/env python3
"""Stage60/61 expanded Flag namespace と CFRU Raid の exact collision 監査。

このモジュールは ROM を更新しない。Stage60 exact binary、到達可能 event CFG、
object visibility、manifest、trainer binding、Stage61 namespace registry、linked
CFRU config を同じ 0x0900..0x18FF universe に展開し、Raid 109 flags の安全な
移設先と byte-exact patch plan を返す。

また、CFRU の ExpandedFlagsHook/ExpandedVarsHook が linked payload に存在する
だけで stock entrypoint へ接続されていない問題を fail-closed で検出する。
``--mgba`` は一時 ROM に候補 hook だけを適用し、実 libmGBA ARM7TDMI 上で
stock alias と修復後 routing の双方を read/write probe する。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage57_debug_suite import _collect_contactable_roots  # noqa: E402
from tools.t02.rom_inventory import (  # noqa: E402
    MAP_GROUPS_POINTER_SITE,
    RomImage,
    ScriptWalker,
)
from tools.world_runtime_e2e_repair import _coordinates  # noqa: E402


SCHEMA_VERSION = 1
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
STAGE60_ROM_RELATIVE = Path("build/stages/60_wild_species_root_repair.gba")
STAGE60_ROM_SHA256 = (
    "3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1"
)
CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"

CFRU_DYNAMAX_RELATIVE = Path("vendor/upstream/CFRU-JP/src/dynamax.c")
CFRU_DYNAMAX_SHA256 = (
    "ef0eb85047ec0a7d74b5df38bce8481367828508e2104aa7615de62ddecc2c0a"
)
CFRU_HOOK_MANIFEST_RELATIVE = Path("vendor/upstream/CFRU-JP/hooks")
CFRU_HOOK_MANIFEST_SHA256 = (
    "19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5"
)
CFRU_RAM_LOCS_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/include/new/ram_locs.h"
)
CFRU_RAM_LOCS_SHA256 = (
    "8c8d7fd53813fefff997173f203aa0c97e1c14062db933e55303d5c498b2f089"
)
CFRU_ITEM_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/item.c")
CFRU_ITEM_SOURCE_SHA256 = (
    "885c2ae9fa78d145eec1eca4333104b6fdd90a1d5afbbe191e0bc3398e740922"
)
CFRU_ROAMER_HEADER_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/include/new/roamer.h"
)
CFRU_ROAMER_HEADER_SHA256 = (
    "0c65bcde6fbeae553c9a3273cdebeac7e0945c813d840fbed66c7a960a8ce3f2"
)
CFRU_FOLLOWER_HEADER_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/include/new/follow_me.h"
)
CFRU_FOLLOWER_HEADER_SHA256 = (
    "56fa121bc2aabdd2e4ec6cc08b7f69d4073fb5a9b4c1d557db73d4ca7c21a117"
)
CFRU_OVERWORLD_HEADER_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/include/new/overworld.h"
)
CFRU_OVERWORLD_HEADER_SHA256 = (
    "bd044b3d654cc27032532d4139f4830e95287c5f117157c09977be6bc9e50965"
)
CFRU_CATCHING_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/catching.c")
CFRU_CATCHING_SOURCE_SHA256 = (
    "bd965d72f21e1ac35064de02ce628796e6821a482c875eea8249c0331fcf9e16"
)
CFRU_OVERWORLD_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/overworld.c")
CFRU_OVERWORLD_SOURCE_SHA256 = (
    "1d5877fd2d38747db0a03891e193729cb410d75a653ece57eef444783c197fe6"
)
CFRU_PARTY_MENU_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/party_menu.c")
CFRU_PARTY_MENU_SOURCE_SHA256 = (
    "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59"
)
CFRU_WILD_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/wild_encounter.c")
CFRU_WILD_SOURCE_SHA256 = (
    "a2e57daf75961a550faa034e7f668443b519787d289044e5e0a32d3c933a6249"
)
CFRU_ROAMER_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/roamer.c")
CFRU_ROAMER_SOURCE_SHA256 = (
    "0e5b3b628372bf34e996501d4b83b5120a452836eb9cb0b01f43e04e2d40529b"
)
CFRU_SCRIPTING_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/scripting.c")
CFRU_SCRIPTING_SOURCE_SHA256 = (
    "6ab41220852dba87df2a26c6fba3b3c3bebf1c7df5f85a596eb7ae644461544a"
)
CFRU_HOOK_SOURCE_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/assembly/hooks/general_hooks.s"
)
CFRU_HOOK_SOURCE_SHA256 = (
    "d352401ff799e92e6d85b6cc4c68186e409561760364f9bd4d5fc9388b02fe1f"
)
CFRU_SAVE_SOURCE_RELATIVE = Path("vendor/upstream/CFRU-JP/src/save.c")
CFRU_SAVE_SOURCE_SHA256 = (
    "e1c12550fb47ed4d7d5c14bdd20698e019c6913c2568aab917b29fc39636a42a"
)
CFRU_MAPSEC_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/include/constants/region_map_sections.h"
)
CFRU_CONFIG_RELATIVE = Path("vendor/upstream/CFRU-JP/src/config.h")
CFRU_FLAG_CONSTANTS_RELATIVE = Path(
    "vendor/upstream/CFRU-JP/include/constants/flags.h"
)
CFRU_PROFILE_RELATIVE = Path("config/cfru_vega_minimal.h")
CFRU_LINKED_OFFSETS_RELATIVE = Path(
    "build/battle-core/"
    "9215826454ee6023888d2f53d33b662d21a340af868c92637aae2c5c191c5717/"
    "run-1/offsets.ini"
)
CFRU_LINKED_OFFSETS_SHA256 = (
    "f9851fb5eea759573d1e4e0b923e69c34c85ddb171fb03321f5b7ce380870523"
)
CFRU_LINKED_OUTPUT_RELATIVE = CFRU_LINKED_OFFSETS_RELATIVE.with_name("output.bin")
CFRU_LINKED_OUTPUT_SHA256 = (
    "518de9585051557c285f66c7c25defa0a1b82422020cda44b995c41f1cacec04"
)
CFRU_LINKED_OUTPUT_START = 0x09000000
CFRU_LINKED_OUTPUT_SIZE = 0x001DEAAA
CFRU_LINKED_OUTPUT_END_EXCLUSIVE = (
    CFRU_LINKED_OUTPUT_START + CFRU_LINKED_OUTPUT_SIZE
)
BATTLE_HOOK_MATRIX_RELATIVE = Path("reports/generated/battle_hook_matrix.csv")
BATTLE_HOOK_MATRIX_SHA256 = (
    "9ee0162c46635e856aa996ee1ebebb9e8c6316350a3375d17f1e2e1461edf289"
)
STAGE60_TEST_READY_SAVE_RELATIVE = Path(".local/60_wild_species_root_repair.srm")
STAGE60_TEST_READY_SAVE_SHA256 = (
    "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
)
STAGE61_BUILDER_RELATIVE = Path("scripts/build_stage61_display_npc_event_audit.py")
STAGE61_RUNNER_RELATIVE = Path("scripts/run_stage61_mgba_validation.py")
STAGE61_MGBA_SOURCE_RELATIVE = Path("tools/mgba_stage61_display_npc_event_e2e.c")
STAGE61_RUNTIME_SOURCE_RELATIVE = Path(
    "overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c"
)
STAGE61_ROM_RELATIVE = Path("build/stages/61_display_npc_event_audit.gba")
STAGE61_METADATA_RELATIVE = Path("build/stages/61_display_npc_event_audit.json")
STAGE61_AUDIT_RELATIVE = Path("reports/generated/stage61_display_npc_event_audit.json")
STAGE61_EVENT_SEMANTIC_RELATIVE = Path(
    "reports/generated/stage61_event_semantic_relocation.json"
)
STAGE61_BUILD_CONFIG_RELATIVE = Path(
    "config/stage61_display_npc_event_audit.json"
)
RAM_LAYOUT_RELATIVE = Path("config/ram_layout.csv")
SAVE_LAYOUT_RELATIVE = Path("config/save_layout.csv")

FLAG_UNIVERSE_START = 0x0900
FLAG_UNIVERSE_END_EXCLUSIVE = 0x1900
EXPANDED_FLAG_RAM = 0x0203B0E8
EXPANDED_VAR_RAM = 0x0203B2E8
EXPANDED_VAR_END_EXCLUSIVE = 0x0203B6E8
SAVE_PARASITE_RAM = 0x0203B0E8
SAVE_PARASITE_SIZE = 0x0EC4
SAVE_SECTOR_DATA_SIZE = 0x0FF0
SAVE_EXTENSION_SIZE = 0x2EA4
SAVE_SECTOR30_IMAGE = SAVE_PARASITE_RAM + SAVE_PARASITE_SIZE
SAVE_SECTOR31_IMAGE = SAVE_SECTOR30_IMAGE + SAVE_SECTOR_DATA_SIZE
SAVE_EXTENSION_END_EXCLUSIVE = SAVE_SECTOR31_IMAGE + SAVE_SECTOR_DATA_SIZE
SAVE_SECTION_OFFSETS_POINTER_SITE = 0x080DB224
STOCK_SAVE_SECTION_OFFSETS = 0x083C4B28
LINKED_SAVE_SECTION_OFFSETS = 0x09169560
SAVE_BLOCK1_POINTER = 0x03005048
STOCK_FLAG_BITMAP_OFFSET = 0x0EE0
STOCK_FLAG_BITMAP_END = 0x1000
STOCK_VAR_OFFSET = 0x1000
STOCK_VAR_END = 0x1200

OLD_RAID_START = 0x1800
RAID_FLAG_COUNT = 0x6D
OLD_RAID_END_EXCLUSIVE = OLD_RAID_START + RAID_FLAG_COUNT
REQUESTED_RAID_START = 0x1500
REQUESTED_RAID_END_EXCLUSIVE = REQUESTED_RAID_START + RAID_FLAG_COUNT

# 0x15BC is the first free ID after the exact Stage60 KANTO_NEW allocation,
# but the compiled CFRU functions construct the base as ``imm8 << 5``.  The
# first byte-exact encodable 109-ID window is therefore 0x15C0..0x162C.
RECOMMENDED_RAID_START = 0x15C0
RECOMMENDED_RAID_END_EXCLUSIVE = RECOMMENDED_RAID_START + RAID_FLAG_COUNT

GET_VAR_POINTER = 0x0806DC48
GET_VAR_POINTER_THUMB = GET_VAR_POINTER | 1
GET_FLAG_POINTER = 0x0806DDB4
GET_FLAG_POINTER_THUMB = GET_FLAG_POINTER | 1
SPECIAL_FLAG_POINTER_LITERAL = 0x0806DE70
SPECIAL_FLAG_RAM = 0x02037014
FLAG_SET_THUMB = 0x0806DE75
FLAG_CLEAR_THUMB = 0x0806DE9D
FLAG_GET_THUMB = 0x0806DEC5

EXPANDED_VARS_HOOK = 0x090970DC
EXPANDED_VARS_HOOK_THUMB = EXPANDED_VARS_HOOK | 1
EXPANDED_FLAGS_HOOK = 0x09097104
EXPANDED_FLAGS_HOOK_THUMB = EXPANDED_FLAGS_HOOK | 1
GET_EXPANDED_FLAG_POINTER = 0x091281D0
GET_EXPANDED_FLAG_POINTER_THUMB = GET_EXPANDED_FLAG_POINTER | 1
GET_EXPANDED_VAR_POINTER = 0x09128220
GET_EXPANDED_VAR_POINTER_THUMB = GET_EXPANDED_VAR_POINTER | 1

LINKED_SAVE_SYMBOLS = {
    "ExpandedVarsHook": 0x090970DC,
    "ExpandedFlagsHook": 0x09097104,
    "LinkBattleSaveHook": 0x09097140,
    "LinkTradeSaveHook": 0x0909714C,
    "NewGameSaveClearHook": 0x09097168,
    "SaveParasite": 0x09127A28,
    "HandleLoadSector": 0x09127A84,
    "TryLoadSaveSector": 0x09127BE8,
    "GetSaveValidStatus": 0x09127C4C,
    "HandleWriteSector": 0x09127E34,
    "SaveWriteToFlash": 0x09127F40,
    "HandleSavingData": 0x09128050,
    "NewGameWipeNewSaveData": 0x0912818C,
    "GetExpandedFlagPointer": 0x091281D0,
    "GetExpandedVarPointer": 0x09128220,
    "gSaveSectionOffsets": 0x09169560,
}

GET_VAR_POINTER_PREIMAGE = bytes.fromhex("70b50004040c261c")
GET_FLAG_POINTER_PREIMAGE = bytes.fromhex("70b505042c0c261c")
GET_VAR_POINTER_REPLACEMENT = bytes.fromhex("00490847dd700909")
GET_FLAG_POINTER_REPLACEMENT = bytes.fromhex("0049084705710909")

EXPANDED_VARS_HOOK_BODY = bytes.fromhex(
    "70b50004040c261c201c91f09bf8012804d0002801d10248004770bd"
    "0148004751dc060857dc0608"
)
EXPANDED_FLAGS_HOOK_BODY = bytes.fromhex(
    "70b505042c0c261c201c91f05ff80028efd1014800470000bddd0608"
)
GET_EXPANDED_FLAG_POINTER_BODY = bytes.fromhex(
    "80210e4bc3181a044901120c8a420fd30b4b9c22c31800201b041b0c"
    "920193424041084b40421840074b9c4660447047d810064b9c466044"
    "f9e7c04600f7ffff00e7ffff1490fcfdec6f0302e8b00302"
)
GET_EXPANDED_VAR_POINTER_BODY = bytes.fromhex(
    "80220b4bc3181b0492001b0c93420ad3084b9c46fc2360440004000c"
    "9b019842804140427047044b9c4640006044f9e700b0ffff00bfffff"
    "e8120302"
)

EXPECTED_EVENT_ROOT_COUNTS = {
    "object": 3098,
    "coord": 743,
    "map_script": 569,
    "bg": 1031,
}
EXPECTED_EVENT_ROOT_COUNT = 5441
EXPECTED_EVENT_SCRIPT_COUNT = 9021
EXPECTED_EVENT_FLAG_REFERENCE_COUNT = 2365
EXPECTED_OBJECT_TEMPLATE_COUNT = 3102
EXPECTED_NONZERO_VISIBILITY_COUNT = 794
EXPECTED_UNIQUE_VISIBILITY_COUNT = 434

# CFRU ``SAVE_BLOCK_PARASITE`` is a raw 0xEC4-byte image rather than a typed
# save structure.  Consequently a symbol merely residing in this interval is
# not evidence that Stage60 actually consumes it.  These ranges enumerate all
# upstream named/structured occupants in the first image and keep persistent
# gameplay state separate from volatile scratch.
PARASITE_CANDIDATE_REGIONS: tuple[dict[str, Any], ...] = (
    {
        "symbol": "gExpandedFlags",
        "start": 0x0203B0E8,
        "end_exclusive": 0x0203B2E8,
        "kind": "PERSISTENT",
        "stage60_status": "LIVE_AFTER_GLOBAL_HOOK_INSTALL",
    },
    {
        "symbol": "gExpandedVars",
        "start": 0x0203B2E8,
        "end_exclusive": 0x0203B6E8,
        "kind": "PERSISTENT",
        "stage60_status": "LIVE_AFTER_GLOBAL_HOOK_INSTALL",
    },
    {
        "symbol": "gLastUsedBall",
        "start": 0x0203B6EC,
        "end_exclusive": 0x0203B6EE,
        "kind": "PERSISTENT",
        "stage60_status": "LIVE_CONNECTED",
    },
    {
        "symbol": "pc_timer_keypad_state",
        "start": 0x0203B724,
        "end_exclusive": 0x0203B734,
        "kind": "MIXED_VOLATILE",
        "stage60_status": "UNCONNECTED",
    },
    {
        "symbol": "gPedometers",
        "start": 0x0203B734,
        "end_exclusive": 0x0203B740,
        "kind": "PERSISTENT_IF_FEATURE_CONNECTED",
        "stage60_status": "UNCONNECTED",
    },
    {
        "symbol": "gWalkingScript",
        "start": 0x0203B740,
        "end_exclusive": 0x0203B744,
        "kind": "VOLATILE_POINTER",
        "stage60_status": "UNCONNECTED",
    },
    {
        "symbol": "sDynamicOverworldPaletteRefs",
        "start": 0x0203B74C,
        "end_exclusive": 0x0203B78C,
        "kind": "VOLATILE_CACHE",
        "stage60_status": "UNCONNECTED",
    },
    {
        "symbol": "gPlayerCoins",
        "start": 0x0203B78C,
        "end_exclusive": 0x0203B790,
        "kind": "PERSISTENT_IF_FEATURE_CONNECTED",
        "stage60_status": "DECLARED_LIVE_BUT_UPSTREAM_ROOTS_UNCONNECTED",
    },
    {
        "symbol": "gFollowerState",
        "start": 0x0203B790,
        "end_exclusive": 0x0203B7A8,
        "kind": "PERSISTENT_IF_FEATURE_CONNECTED",
        "stage60_status": "UNCONNECTED",
    },
    {
        "symbol": "gIgnoredDNSPalIndices",
        "start": 0x0203B7A8,
        "end_exclusive": 0x0203B9A8,
        "kind": "VOLATILE_CACHE",
        "stage60_status": "COMPILE_DISABLED",
    },
    {
        "symbol": "gRoamers",
        "start": 0x0203B9A8,
        "end_exclusive": 0x0203BA98,
        "kind": "PERSISTENT_IF_FEATURE_CONNECTED",
        "stage60_status": "UNCONNECTED",
    },
    {
        "symbol": "sExpandedBagPrefix",
        "start": 0x0203BA98,
        "end_exclusive": 0x0203BFAC,
        "kind": "PERSISTENT_IF_FEATURE_CONNECTED_PREFIX_ONLY",
        "stage60_status": "UNCONNECTED",
    },
)

# The full expanded bag continues into the raw sector-30 image.  It can never
# be made durable by consuming only the 0xA1C bytes of stock main-save tails.
EXPANDED_BAG_START = 0x0203BA98
EXPANDED_BAG_END_EXCLUSIVE = 0x0203C6C0
EXPANDED_BAG_SIZE = EXPANDED_BAG_END_EXCLUSIVE - EXPANDED_BAG_START
STOCK_MAIN_SAVE_TAIL_CAPACITY = 0x0A1C

PARASITE_FEATURE_HOOK_SECTIONS: tuple[tuple[str, str], ...] = (
    ("pedometers", "##Overworld Hooks"),
    ("roamers", "#Roamer Hooks"),
    ("followers", "##Follow Me"),
    ("expanded_bag", "##Bag"),
    ("expanded_coins", "##Expand Coins"),
    ("updated_repel", "## Updated Repel System"),
)

PARASITE_HOOK_SECTION_SPANS: Mapping[str, tuple[str, str]] = {
    "keypad": ("##Keypad", "##Character Customization"),
    "dynamic_overworld_palettes": (
        "##Dynamic Overworld Palettes",
        "##Whiteout Hack",
    ),
    "followers": ("##Follow Me", "##Learn Move"),
    "updated_repel": ("## Updated Repel System", "##Bag"),
    "expanded_bag": ("##Bag", "##Move Reminder"),
    "expanded_coins": ("##Expand Coins", "##Safari Zone"),
    # StandardWildEncounter reads gRoamers directly.  It sits in a separate
    # hook section from the explicit Roamer hooks, so both root sets are
    # mandatory evidence for classifying the 0xF0-byte owner as dead/live.
    "wild_encounter_roamer_paths": ("##Wild Encounter Hooks", "#Roamer Hooks"),
    "roamers": ("#Roamer Hooks", "##Save Expansion Hooks"),
}


class StateNamespaceCollisionAuditError(RuntimeError):
    """監査入力または exact preimage が既知の Stage60 契約と一致しない。"""


def _fail(message: str) -> NoReturn:
    raise StateNamespaceCollisionAuditError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hex(value: int, width: int = 4) -> str:
    return f"0x{value:0{width}X}"


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def validate_rom_identity(raw: bytes) -> None:
    if len(raw) != ROM_SIZE:
        _fail(f"Stage60 size mismatch: {len(raw)} != {ROM_SIZE}")
    digest = _sha(raw)
    if digest != STAGE60_ROM_SHA256:
        _fail(f"Stage60 SHA-256 mismatch: {digest} != {STAGE60_ROM_SHA256}")


def _require_file_hash(path: Path, expected: str, label: str) -> bytes:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail(f"{label}を読めません: {path}: {exc}")
    actual = _sha(raw)
    if actual != expected:
        _fail(f"{label} SHA-256 mismatch: {actual} != {expected}")
    return raw


def _rom_slice(raw: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(raw):
        _fail(f"{label} ROM range outside image: {_hex(address, 8)} + {size}")
    return raw[offset:offset + size]


def _u32_pointer_sites(raw: bytes, value: int) -> list[int]:
    """ROM内のlittle-endian u32 exact occurrenceを高速に列挙する。"""

    needle = struct.pack("<I", value)
    sites: list[int] = []
    search_at = 0
    while True:
        offset = raw.find(needle, search_at)
        if offset < 0:
            return sites
        sites.append(ROM_BASE + offset)
        search_at = offset + 1


def _require_rom_bytes(raw: bytes, address: int, expected: bytes, label: str) -> None:
    actual = _rom_slice(raw, address, len(expected), label)
    if actual != expected:
        _fail(
            f"{label} preimage mismatch at {_hex(address, 8)}: "
            f"{actual.hex()} != {expected.hex()}"
        )


def _id_ranges(ids: Iterable[int]) -> list[dict[str, Any]]:
    values = sorted(set(ids))
    if not values:
        return []
    result: list[dict[str, Any]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        result.append(
            {
                "start": start,
                "start_hex": _hex(start),
                "end_inclusive": previous,
                "end_inclusive_hex": _hex(previous),
                "count": previous - start + 1,
            }
        )
        start = previous = value
    result.append(
        {
            "start": start,
            "start_hex": _hex(start),
            "end_inclusive": previous,
            "end_inclusive_hex": _hex(previous),
            "count": previous - start + 1,
        }
    )
    return result


def _source_identity(root: Path) -> dict[str, Any]:
    source_lock = json.loads((root / "state/source-lock.json").read_text(encoding="utf-8"))
    cfru_rows = [row for row in source_lock["sources"] if row["name"] == "cfru"]
    if len(cfru_rows) != 1:
        _fail(f"source-lock CFRU row count differs: {len(cfru_rows)}")
    cfru = cfru_rows[0]
    for key in ("configured_commit", "actual_commit", "resolved_commit"):
        if cfru.get(key) != CFRU_COMMIT:
            _fail(f"source-lock CFRU {key} mismatch: {cfru.get(key)!r}")
    if cfru.get("configured_commit_verified") is not True:
        _fail("source-lock CFRU commit is not verified")

    inputs = []
    for relative, expected, label in (
        (CFRU_DYNAMAX_RELATIVE, CFRU_DYNAMAX_SHA256, "CFRU dynamax.c"),
        (CFRU_HOOK_SOURCE_RELATIVE, CFRU_HOOK_SOURCE_SHA256, "CFRU hooks"),
        (CFRU_SAVE_SOURCE_RELATIVE, CFRU_SAVE_SOURCE_SHA256, "CFRU save.c"),
        (CFRU_HOOK_MANIFEST_RELATIVE, CFRU_HOOK_MANIFEST_SHA256, "CFRU hook manifest"),
        (CFRU_RAM_LOCS_RELATIVE, CFRU_RAM_LOCS_SHA256, "CFRU RAM locations"),
        (CFRU_ITEM_SOURCE_RELATIVE, CFRU_ITEM_SOURCE_SHA256, "CFRU item.c"),
        (CFRU_ROAMER_HEADER_RELATIVE, CFRU_ROAMER_HEADER_SHA256, "CFRU roamer.h"),
        (CFRU_FOLLOWER_HEADER_RELATIVE, CFRU_FOLLOWER_HEADER_SHA256, "CFRU follow_me.h"),
        (CFRU_OVERWORLD_HEADER_RELATIVE, CFRU_OVERWORLD_HEADER_SHA256, "CFRU overworld.h"),
        (CFRU_CATCHING_SOURCE_RELATIVE, CFRU_CATCHING_SOURCE_SHA256, "CFRU catching.c"),
        (CFRU_OVERWORLD_SOURCE_RELATIVE, CFRU_OVERWORLD_SOURCE_SHA256, "CFRU overworld.c"),
        (CFRU_PARTY_MENU_SOURCE_RELATIVE, CFRU_PARTY_MENU_SOURCE_SHA256, "CFRU party_menu.c"),
        (CFRU_WILD_SOURCE_RELATIVE, CFRU_WILD_SOURCE_SHA256, "CFRU wild_encounter.c"),
        (CFRU_ROAMER_SOURCE_RELATIVE, CFRU_ROAMER_SOURCE_SHA256, "CFRU roamer.c"),
        (CFRU_SCRIPTING_SOURCE_RELATIVE, CFRU_SCRIPTING_SOURCE_SHA256, "CFRU scripting.c"),
        (BATTLE_HOOK_MATRIX_RELATIVE, BATTLE_HOOK_MATRIX_SHA256, "Stage06 hook matrix"),
        (CFRU_LINKED_OUTPUT_RELATIVE, CFRU_LINKED_OUTPUT_SHA256, "Stage60 linked CFRU output"),
    ):
        raw = _require_file_hash(root / relative, expected, label)
        inputs.append(
            {"path": str(relative), "size": len(raw), "sha256": expected}
        )
    return {
        "commit": CFRU_COMMIT,
        "source_lock_verified": True,
        "files": inputs,
    }


def _parse_mapsec_count(root: Path) -> dict[str, Any]:
    text = (root / CFRU_MAPSEC_RELATIVE).read_text(encoding="utf-8")

    def literal(name: str) -> int:
        match = re.search(
            rf"^\s*#\s*define\s+{re.escape(name)}\s+(0x[0-9A-Fa-f]+)\b",
            text,
            re.MULTILINE,
        )
        if not match:
            _fail(f"CFRU map-section define missing: {name}")
        return int(match.group(1), 16)

    dynamic = literal("MAPSEC_DYNAMIC")
    celadon_dept = literal("MAPSEC_CELADON_DEPT")
    expression = re.search(
        r"^\s*#\s*define\s+KANTO_MAPSEC_COUNT\s+"
        r"\(MAPSEC_CELADON_DEPT\s*-\s*MAPSEC_DYNAMIC\)\s*$",
        text,
        re.MULTILINE,
    )
    if not expression:
        _fail("KANTO_MAPSEC_COUNT expression drifted")
    count = celadon_dept - dynamic
    if (dynamic, celadon_dept, count) != (0x57, 0xC4, RAID_FLAG_COUNT):
        _fail(
            "KANTO_MAPSEC_COUNT operands differ: "
            f"{dynamic:#x}, {celadon_dept:#x}, {count:#x}"
        )
    return {
        "source": str(CFRU_MAPSEC_RELATIVE),
        "mapsec_dynamic": dynamic,
        "mapsec_celadon_dept": celadon_dept,
        "formula": "MAPSEC_CELADON_DEPT - MAPSEC_DYNAMIC",
        "count": count,
    }


def _raid_source_contract(root: Path) -> dict[str, Any]:
    text = (root / CFRU_DYNAMAX_RELATIVE).read_text(encoding="utf-8")
    definition = re.findall(
        r"^#define FIRST_RAID_BATTLE_FLAG\s+(0x[0-9A-Fa-f]+)\s*$",
        text,
        re.MULTILINE,
    )
    if definition != ["0x15C0"]:
        _fail(f"FIRST_RAID_BATTLE_FLAG definition differs: {definition}")
    expressions = {
        "FlagGet": len(re.findall(r"\bFlagGet\(FIRST_RAID_BATTLE_FLAG\s*\+", text)),
        "FlagSet": len(re.findall(r"\bFlagSet\(FIRST_RAID_BATTLE_FLAG\s*\+", text)),
        "FlagClear": len(re.findall(r"\bFlagClear\(FIRST_RAID_BATTLE_FLAG\s*\+", text)),
    }
    if expressions != {"FlagGet": 2, "FlagSet": 1, "FlagClear": 2}:
        _fail(f"Raid source consumer expressions differ: {expressions}")
    return {
        "source": str(CFRU_DYNAMAX_RELATIVE),
        "definition": RECOMMENDED_RAID_START,
        "definition_hex": _hex(RECOMMENDED_RAID_START),
        "status": "SOURCE_RELOCATION_INSTALLED",
        "consumer_expression_counts": expressions,
        "consumer_expression_total": sum(expressions.values()),
        "required_source_change": {
            "before": "#define FIRST_RAID_BATTLE_FLAG 0x1800",
            "after": "#define FIRST_RAID_BATTLE_FLAG 0x15C0",
            "reason": "再生成可能な根本修正。binary patch plan と同じ owner を使用する",
            "installed": True,
        },
    }


def _effective_defines(text: str) -> dict[str, str]:
    """CFRU build helper と同じ define/undef の順序評価を行う。"""

    defines: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = re.match(
            r"^#\s*define\s+([A-Za-z_]\w*)(?:\s+([^/\s][^/]*?))?\s*(?://|/\*|$)",
            line,
        )
        if match:
            defines[match.group(1)] = (match.group(2) or "1").strip()
            continue
        match = re.match(r"^#\s*undef\s+([A-Za-z_]\w*)\b", line)
        if match:
            defines.pop(match.group(1), None)
    return defines


def _linked_cfru_flag_constants(root: Path) -> dict[str, Any]:
    config = (root / CFRU_CONFIG_RELATIVE).read_text(encoding="utf-8")
    profile = (root / CFRU_PROFILE_RELATIVE).read_text(encoding="utf-8")
    constants = (root / CFRU_FLAG_CONSTANTS_RELATIVE).read_text(encoding="utf-8")
    defines = _effective_defines(config + "\n" + profile + "\n" + constants)
    rows: list[dict[str, Any]] = []
    used: set[int] = set()
    for name, expression in sorted(defines.items()):
        if not name.startswith("FLAG_"):
            continue
        if not re.fullmatch(r"0[xX][0-9A-Fa-f]+|[0-9]+", expression):
            continue
        value = int(expression, 0)
        if FLAG_UNIVERSE_START <= value < FLAG_UNIVERSE_END_EXCLUSIVE:
            rows.append({"name": name, "id": value, "id_hex": _hex(value)})
            used.add(value)
    names = {row["name"] for row in rows}
    if "FLAG_RAID_BATTLE_NO_FORCE_END" in names:
        _fail("Vega-minimal profile failed to undef FLAG_RAID_BATTLE_NO_FORCE_END")
    required = {
        "FLAG_INVERSE",
        "FLAG_RAID_BATTLE",
        "FLAG_SYS_DEXNAV",
        "FLAG_DAILY_EVENTS_START",
        "FLAG_ALWAYS_SHOW_LAST_BALL",
    }
    if not required.issubset(names):
        _fail(f"linked CFRU flag constants missing: {sorted(required - names)}")

    # config.h explicitly declares FLAG_DAILY_EVENTS_START through +0xFF.
    daily = next(row["id"] for row in rows if row["name"] == "FLAG_DAILY_EVENTS_START")
    daily_ids = set(range(daily, daily + 0x100))
    if max(daily_ids) >= FLAG_UNIVERSE_END_EXCLUSIVE:
        _fail("daily flag reservation leaves expanded flag universe")
    used.update(daily_ids)
    return {
        "profile": str(CFRU_PROFILE_RELATIVE),
        "constants": rows,
        "direct_constant_count": len(rows),
        "daily_range": {
            "start": daily,
            "start_hex": _hex(daily),
            "end_inclusive": daily + 0xFF,
            "end_inclusive_hex": _hex(daily + 0xFF),
            "count": 0x100,
        },
        "ids": sorted(used),
        "ranges": _id_ranges(used),
    }


def _event_flag_inventory(raw: bytes) -> dict[str, Any]:
    rom = RomImage("Stage60", raw)
    roots, counts = _collect_contactable_roots(rom)
    if len(roots) != EXPECTED_EVENT_ROOT_COUNT or dict(counts) != EXPECTED_EVENT_ROOT_COUNTS:
        _fail(f"Stage60 contactable roots drifted: {len(roots)}, {dict(counts)}")
    walker = ScriptWalker(rom)
    for root in roots:
        walker.add_root(root)
    graph = walker.walk()
    if graph["diagnostics"]:
        _fail(
            "Stage60 event CFG diagnostics remain: "
            + json.dumps(graph["diagnostics"][:8], ensure_ascii=False, sort_keys=True)
        )
    if graph["visited_script_count"] != EXPECTED_EVENT_SCRIPT_COUNT:
        _fail(
            "Stage60 visited script count drifted: "
            f"{graph['visited_script_count']} != {EXPECTED_EVENT_SCRIPT_COUNT}"
        )
    all_flag_refs = [row for row in graph["references"] if row["category"] == "flag"]
    if len(all_flag_refs) != EXPECTED_EVENT_FLAG_REFERENCE_COUNT:
        _fail(
            f"Stage60 event flag refs drifted: {len(all_flag_refs)} "
            f"!= {EXPECTED_EVENT_FLAG_REFERENCE_COUNT}"
        )
    high = [
        row for row in all_flag_refs
        if FLAG_UNIVERSE_START <= int(row["value"]) < FLAG_UNIVERSE_END_EXCLUSIVE
    ]
    compact = [
        {
            "id": int(row["value"]),
            "id_hex": _hex(int(row["value"])),
            "access": str(row["access"]),
            "command": str(row["command"]),
            "instruction_address": int(row["instruction_address"]),
            "instruction_address_hex": _hex(int(row["instruction_address"]), 8),
            "roots": list(row["roots"]),
        }
        for row in high
    ]
    ids = {int(row["value"]) for row in high}
    return {
        "root_count": len(roots),
        "root_counts": dict(counts),
        "visited_script_count": graph["visited_script_count"],
        "diagnostic_count": 0,
        "all_flag_reference_count": len(all_flag_refs),
        "expanded_reference_count": len(high),
        "expanded_unique_id_count": len(ids),
        "access_counts": dict(sorted(Counter(str(row["access"]) for row in high).items())),
        "ids": sorted(ids),
        "ranges": _id_ranges(ids),
        "references": compact,
    }


def _object_visibility_inventory(root: Path, raw: bytes) -> dict[str, Any]:
    rom = RomImage("Stage60", raw)
    inventory = json.loads(
        (root / "reports/generated/id_inventory.json").read_text(encoding="utf-8")
    )
    coordinates = _coordinates(root, inventory["map_contract"]["group_sizes"])
    groups_address = rom.u32(MAP_GROUPS_POINTER_SITE)
    group_count = max(group for group, _ in coordinates) + 1
    group_pointers = [rom.u32(groups_address + index * 4) for index in range(group_count)]
    rows: list[dict[str, Any]] = []
    template_count = 0
    for group, number in coordinates:
        header = rom.u32(group_pointers[group] + number * 4)
        events = rom.u32(header + 4)
        if not events or rom.raw(events, 4) == b"\xFF" * 4:
            continue
        count = rom.u8(events)
        objects = rom.u32(events + 4)
        template_count += count
        for index in range(count):
            address = objects + index * 0x18
            flag = rom.u16(address + 0x14)
            if flag:
                rows.append(
                    {
                        "group": group,
                        "map": number,
                        "object_index": index,
                        "template_address": address,
                        "template_address_hex": _hex(address, 8),
                        "id": flag,
                        "id_hex": _hex(flag),
                    }
                )
    unique = {row["id"] for row in rows}
    if (
        template_count != EXPECTED_OBJECT_TEMPLATE_COUNT
        or len(rows) != EXPECTED_NONZERO_VISIBILITY_COUNT
        or len(unique) != EXPECTED_UNIQUE_VISIBILITY_COUNT
    ):
        _fail(
            "Stage60 object visibility inventory drifted: "
            f"templates={template_count}, nonzero={len(rows)}, unique={len(unique)}"
        )
    high_rows = [
        row for row in rows
        if FLAG_UNIVERSE_START <= row["id"] < FLAG_UNIVERSE_END_EXCLUSIVE
    ]
    ids = {row["id"] for row in high_rows}
    return {
        "map_count": len(coordinates),
        "template_count": template_count,
        "nonzero_visibility_count": len(rows),
        "unique_visibility_id_count": len(unique),
        "expanded_reference_count": len(high_rows),
        "expanded_unique_id_count": len(ids),
        "ids": sorted(ids),
        "ranges": _id_ranges(ids),
        "references": high_rows,
    }


def _manifest_inventory(root: Path) -> dict[str, Any]:
    path = root / "manifests/flags.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    parsed: list[dict[str, Any]] = []
    for row in rows:
        value = int(row["id"], 0)
        if FLAG_UNIVERSE_START <= value < FLAG_UNIVERSE_END_EXCLUSIVE:
            parsed.append(
                {
                    "flag_key": row["flag_key"],
                    "id": value,
                    "id_hex": _hex(value),
                    "owner": row["owner"],
                    "scope": row["scope"],
                    "status": row["status"],
                }
            )
    ids = {row["id"] for row in parsed}
    if len(rows) != 404 or len(parsed) != 404 or len(ids) != 404:
        _fail(
            f"manifests/flags.csv inventory drifted: rows={len(rows)}, "
            f"expanded={len(parsed)}, unique={len(ids)}"
        )
    return {
        "path": "manifests/flags.csv",
        "row_count": len(rows),
        "ids": sorted(ids),
        "ranges": _id_ranges(ids),
        "rows": parsed,
    }


def _trainer_binding_inventory(root: Path) -> dict[str, Any]:
    path = root / "reports/generated/trainer_changekit_final_bindings.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not row["physical_flag"]:
            continue
        value = int(row["physical_flag"], 0)
        if FLAG_UNIVERSE_START <= value < FLAG_UNIVERSE_END_EXCLUSIVE:
            parsed.append(
                {
                    "encounter_key": row["encounter_key"],
                    "binding_mode": row["binding_mode"],
                    "command_address": int(row["command_address"], 0),
                    "command_address_hex": _hex(int(row["command_address"], 0), 8),
                    "id": value,
                    "id_hex": _hex(value),
                }
            )
    ids = {row["id"] for row in parsed}
    modes = Counter(row["binding_mode"] for row in rows)
    if len(rows) != 1302 or modes != Counter({"CANONICAL": 1030, "KANTO_NEW": 201, "ARCHIVE": 71}):
        _fail(f"trainer binding inventory drifted: rows={len(rows)}, modes={dict(modes)}")
    expected_ids = set(range(0x1500, 0x15BC)) | set(range(0x1800, 0x1847))
    if ids != expected_ids:
        _fail("expanded trainer physical flag set drifted")
    return {
        "path": "reports/generated/trainer_changekit_final_bindings.csv",
        "row_count": len(rows),
        "mode_counts": dict(sorted(modes.items())),
        "expanded_row_count": len(parsed),
        "ids": sorted(ids),
        "ranges": _id_ranges(ids),
        "rows": parsed,
    }


def _namespace_registry_inventory(root: Path) -> dict[str, Any]:
    path = root / "config/stage61_namespace_registry.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("schema_version") != 1 or registry.get("stage") != 61:
        _fail("Stage61 namespace registry identity differs")
    ids: set[int] = set()
    ranges: list[dict[str, Any]] = []
    for row in registry.get("flags", []):
        start = int(row["start"], 0)
        end = int(row["end_inclusive"], 0)
        count = end - start + 1
        if count != int(row["count"]):
            _fail(f"Stage61 registry count differs for {row['owner']}")
        current = set(range(start, end + 1))
        overlap = ids & current
        if overlap:
            _fail(f"Stage61 registry self-overlap: {sorted(overlap)[:8]}")
        ids.update(current)
        ranges.append(
            {
                "owner": row["owner"],
                "start": start,
                "start_hex": _hex(start),
                "end_inclusive": end,
                "end_inclusive_hex": _hex(end),
                "count": count,
                "allocation": row["allocation"],
            }
        )
    raid_rows = [
        row for row in ranges if row["owner"] == "CFRU_RAID_COMPLETION_FLAGS"
    ]
    if len(raid_rows) != 1:
        _fail(f"Stage61 Raid registry owner count differs: {len(raid_rows)}")
    raid = raid_rows[0]
    if (
        raid["start"],
        raid["end_inclusive"],
        raid["count"],
        raid["allocation"],
    ) != (
        RECOMMENDED_RAID_START,
        RECOMMENDED_RAID_END_EXCLUSIVE - 1,
        RAID_FLAG_COUNT,
        "raid_map_section_id_ascending",
    ):
        _fail("Stage61 Raid registry reservation differs")
    raid_ids = set(range(RECOMMENDED_RAID_START, RECOMMENDED_RAID_END_EXCLUSIVE))
    topology_ids = set(range(0x162D, 0x163F))
    topology_rows = [
        row for row in ranges
        if row["owner"] == "KANTO_MAP_TOPOLOGY_SOURCE_FLAGS"
    ]
    if len(topology_rows) != 1 or (
        topology_rows[0]["start"],
        topology_rows[0]["end_inclusive"],
        topology_rows[0]["count"],
        topology_rows[0]["allocation"],
    ) != (
        0x162D,
        0x163E,
        18,
        "source_flag_0x0040_through_0x004D_then_0x0058_0x0059_0x02D2_0x02D3",
    ):
        _fail("Stage61 Kanto topology flag registry reservation differs")
    # Only the candidate Raid owner is excluded from collision math.  Topology
    # is a real competing project owner and must remain visible to free-window
    # and overlap calculations.
    project_ids = ids - raid_ids
    expected_project = topology_ids | set(range(0x1800, 0x1900))
    if project_ids != expected_project \
            or ids != expected_project | raid_ids:
        _fail(
            "Stage61 flag registry does not exactly claim Raid 0x15C0..0x162C "
            "plus Kanto topology 0x162D..0x163E and project 0x1800..0x18FF"
        )

    var_ids: set[int] = set()
    var_ranges: list[dict[str, Any]] = []
    for row in registry.get("vars", []):
        start = int(row["start"], 0)
        end = int(row["end_inclusive"], 0)
        count = end - start + 1
        if count != int(row["count"]):
            _fail(f"Stage61 var registry count differs for {row['owner']}")
        current = set(range(start, end + 1))
        overlap = var_ids & current
        if overlap:
            _fail(f"Stage61 var registry self-overlap: {sorted(overlap)[:8]}")
        var_ids.update(current)
        var_ranges.append(
            {
                "owner": row["owner"],
                "start": start,
                "start_hex": _hex(start),
                "end_inclusive": end,
                "end_inclusive_hex": _hex(end),
                "count": count,
                "allocation": row["allocation"],
            }
        )
    expected_var_ranges = {
        "KANTO_MAP_TOPOLOGY_PERSISTENT_VARS": (0x5167, 0x516B, 5),
        "KANTO_LEAGUE_PROJECT_SCENE_VAR": (0x516C, 0x516C, 1),
        "KANTO_FULL_CFG_PERSISTENT_VARS": (0x516D, 0x517F, 19),
        "T19_QOL_VOLATILE_AND_COUNTERS": (0x5180, 0x51FF, 128),
    }
    actual_var_ranges = {
        row["owner"]: (row["start"], row["end_inclusive"], row["count"])
        for row in var_ranges
    }
    if actual_var_ranges != expected_var_ranges \
            or var_ids != set(range(0x5167, 0x5200)):
        _fail("Stage61 var registry ownership differs")
    raw = path.read_bytes()
    return {
        "path": "config/stage61_namespace_registry.json",
        "sha256": _sha(raw),
        "ids": sorted(ids),
        "project_ids_excluding_raid_owner": sorted(project_ids),
        "topology_owner_ids": sorted(topology_ids),
        "topology_owner": topology_rows[0],
        "raid_owner_ids": sorted(raid_ids),
        "raid_owner": raid,
        "ranges": ranges,
        "var_ids": sorted(var_ids),
        "var_ranges": var_ranges,
    }


def _save_layout_contract(root: Path) -> dict[str, Any]:
    path = root / "config/save_layout.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    wanted = {
        "vega_badges_hm_story_flags": ("SAVE_BLOCK1_OFFSET", 0x0EE0, 0x1000),
        "vega_event_vars": ("SAVE_BLOCK1_OFFSET", 0x1000, 0x1200),
        "expanded_flags": ("SAVE_PARASITE_IMAGE_OFFSET", 0x0000, 0x0200),
        "expanded_vars": ("SAVE_PARASITE_IMAGE_OFFSET", 0x0200, 0x0600),
        "last_used_ball_u16": (
            "SAVE_PARASITE_IMAGE_OFFSET", 0x0604, 0x0606
        ),
    }
    found: dict[str, dict[str, Any]] = {}
    for row in rows:
        symbol = row["symbol"]
        if symbol not in wanted:
            continue
        expected_space, expected_start, expected_end = wanted[symbol]
        start = int(row["start"], 0)
        end = int(row["end_exclusive"], 0)
        if (row["address_space"], start, end) != (
            expected_space,
            expected_start,
            expected_end,
        ):
            _fail(f"save_layout {symbol} range differs")
        found[symbol] = {
            "address_space": row["address_space"],
            "start": start,
            "start_hex": _hex(start),
            "end_exclusive": end,
            "end_exclusive_hex": _hex(end),
            "size": end - start,
            "owner": row["owner"],
            "status": row["status"],
            "notes": row["notes"],
        }
    if set(found) != set(wanted):
        _fail(f"save_layout required rows missing: {sorted(set(wanted) - set(found))}")
    return {"path": "config/save_layout.csv", "rows": found}


def _load_stage61_build_configuration(
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Stage61 build configと可変layout入力をcontent identityで結合する。"""

    path = root / STAGE61_BUILD_CONFIG_RELATIVE
    raw = path.read_bytes()
    config = json.loads(raw)
    if (
        config.get("schema_version") != 1
        or config.get("stage") != 61
        or not isinstance(config.get("task"), str)
    ):
        _fail("Stage61 build config identity differs")
    inputs = config.get("inputs")
    if not isinstance(inputs, Mapping):
        _fail("Stage61 build config inputs missing")
    identities: dict[str, Any] = {}
    expected_paths = {
        "ram_layout": RAM_LAYOUT_RELATIVE,
        "save_layout": SAVE_LAYOUT_RELATIVE,
    }
    for key, relative in expected_paths.items():
        declaration = inputs.get(key)
        if not isinstance(declaration, Mapping) \
                or declaration.get("path") != str(relative):
            _fail(f"Stage61 build config {key} path differs")
        data = (root / relative).read_bytes()
        actual = _sha(data)
        if declaration.get("sha256") != actual:
            _fail(
                f"Stage61 build config {key} SHA-256 differs: "
                f"{actual} != {declaration.get('sha256')}"
            )
        declared_size = declaration.get("size")
        if declared_size is not None and int(declared_size) != len(data):
            _fail(f"Stage61 build config {key} size differs")
        identities[key] = {
            "path": str(relative),
            "size": len(data),
            "sha256": actual,
        }
    return config, {
        "path": str(STAGE61_BUILD_CONFIG_RELATIVE),
        "size": len(raw),
        "sha256": _sha(raw),
        "layout_inputs": identities,
    }


def _normalized_layout_rows(
    path: Path,
    *,
    expected_header: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """CSV range/sizeを正規化し、全LIVE ownerの非重複を検証する。"""

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(expected_header):
            _fail(f"{path.name} schema differs: {reader.fieldnames}")
        source_rows = list(reader)
    normalized: list[dict[str, Any]] = []
    live: list[dict[str, Any]] = []
    keys: set[tuple[str, str]] = set()
    for index, source in enumerate(source_rows, start=2):
        space = str(source["address_space"])
        symbol = str(source["symbol"])
        key = (space, symbol)
        if key in keys:
            _fail(f"{path.name} duplicate owner key at line {index}: {key}")
        keys.add(key)
        numeric = (source["start"], source["end_exclusive"], source["size"])
        if not any(numeric):
            if source["status"] == "LIVE":
                _fail(f"{path.name} unbounded LIVE owner at line {index}: {symbol}")
            continue
        if not all(numeric):
            _fail(f"{path.name} partial range at line {index}: {symbol}")
        try:
            start = int(source["start"], 0)
            end = int(source["end_exclusive"], 0)
            declared_size = int(source["size"], 0)
        except ValueError as exc:
            _fail(f"{path.name} invalid integer at line {index}: {exc}")
        if start < 0 or end <= start or declared_size != end - start:
            _fail(f"{path.name} invalid exact range at line {index}: {symbol}")
        row = {
            **source,
            "start": start,
            "start_hex": _hex(start, 8),
            "end_exclusive": end,
            "end_exclusive_hex": _hex(end, 8),
            "size": declared_size,
        }
        normalized.append(row)
        if source["status"] == "LIVE":
            live.append(row)

    by_space: dict[str, list[dict[str, Any]]] = {}
    for row in live:
        by_space.setdefault(str(row["address_space"]), []).append(row)
    for space, rows in by_space.items():
        rows.sort(key=lambda row: (int(row["start"]), int(row["end_exclusive"])))
        for previous, current in zip(rows, rows[1:]):
            if int(current["start"]) < int(previous["end_exclusive"]):
                _fail(
                    f"{path.name} LIVE overlap in {space}: "
                    f"{previous['symbol']} and {current['symbol']}"
                )
    return normalized, live


def _stage61_layout_ownership_contract(root: Path) -> dict[str, Any]:
    """Stage61 persistent 4 ownerのRAM/save exact rangeを一体監査する。"""

    _config, config_identity = _load_stage61_build_configuration(root)
    ram_rows, ram_live = _normalized_layout_rows(
        root / RAM_LAYOUT_RELATIVE,
        expected_header=(
            "address_space", "start", "end_exclusive", "size", "owner",
            "symbol", "lifetime", "persistence", "status", "source_ref",
            "notes",
        ),
    )
    save_rows, save_live = _normalized_layout_rows(
        root / SAVE_LAYOUT_RELATIVE,
        expected_header=(
            "address_space", "start", "end_exclusive", "size", "owner",
            "symbol", "version", "migration", "status", "source_ref",
            "notes",
        ),
    )
    ram_by_symbol = {str(row["symbol"]): row for row in ram_rows}
    save_by_symbol = {str(row["symbol"]): row for row in save_rows}
    ram_expected = {
        "gExpandedFlags": (
            "EWRAM", 0x0203B0E8, 0x0203B2E8, 0x200,
            "CFRU_SAVE_EXPANSION", "FLASH", "LIVE",
        ),
        "gExpandedVars": (
            "EWRAM", 0x0203B2E8, 0x0203B6E8, 0x400,
            "CFRU_SAVE_EXPANSION", "FLASH", "LIVE",
        ),
        "gLastUsedBall": (
            "EWRAM", 0x0203B6EC, 0x0203B6EE, 2,
            "CFRU_SAVE_EXPANSION", "FLASH", "LIVE",
        ),
        "gPlayerCoins": (
            "EWRAM", 0x0203B78C, 0x0203B790, 4,
            "CFRU_SAVE_EXPANSION", "FLASH", "LIVE",
        ),
    }
    save_expected = {
        "expanded_flags": (
            "SAVE_PARASITE_IMAGE_OFFSET", 0x0000, 0x0200, 0x200,
            "CFRU_SAVE_EXPANSION", "KEEP", "LIVE",
        ),
        "expanded_vars": (
            "SAVE_PARASITE_IMAGE_OFFSET", 0x0200, 0x0600, 0x400,
            "CFRU_SAVE_EXPANSION", "KEEP", "LIVE",
        ),
        "last_used_ball_u16": (
            "SAVE_PARASITE_IMAGE_OFFSET", 0x0604, 0x0606, 2,
            "CFRU_SAVE_EXPANSION", "KEEP", "LIVE",
        ),
        "cfru_player_coins_u32": (
            "SAVE_PARASITE_IMAGE_OFFSET", 0x06A4, 0x06A8, 4,
            "CFRU_EXPANDED_COINS", "KEEP", "LIVE",
        ),
    }
    for symbol, expected in ram_expected.items():
        row = ram_by_symbol.get(symbol)
        actual = None if row is None else (
            row["address_space"], row["start"], row["end_exclusive"],
            row["size"], row["owner"], row["persistence"], row["status"],
        )
        if actual != expected:
            _fail(f"ram_layout exact persistent owner differs: {symbol}: {actual}")
    for symbol, expected in save_expected.items():
        row = save_by_symbol.get(symbol)
        actual = None if row is None else (
            row["address_space"], row["start"], row["end_exclusive"],
            row["size"], row["owner"], row["migration"], row["status"],
        )
        if actual != expected:
            _fail(f"save_layout exact persistent owner differs: {symbol}: {actual}")

    crosswalk_names = (
        ("gExpandedFlags", "expanded_flags"),
        ("gExpandedVars", "expanded_vars"),
        ("gLastUsedBall", "last_used_ball_u16"),
        ("gPlayerCoins", "cfru_player_coins_u32"),
    )
    crosswalk: list[dict[str, Any]] = []
    for ram_symbol, save_symbol in crosswalk_names:
        ram = ram_by_symbol[ram_symbol]
        save = save_by_symbol[save_symbol]
        projected_start = SAVE_PARASITE_RAM + int(save["start"])
        projected_end = SAVE_PARASITE_RAM + int(save["end_exclusive"])
        if (
            projected_start != int(ram["start"])
            or projected_end != int(ram["end_exclusive"])
            or int(save["size"]) != int(ram["size"])
        ):
            _fail(f"RAM/save owner affine mapping differs: {ram_symbol}")
        crosswalk.append(
            {
                "ram_symbol": ram_symbol,
                "save_symbol": save_symbol,
                "ram_start": int(ram["start"]),
                "ram_end_exclusive": int(ram["end_exclusive"]),
                "save_image_offset_start": int(save["start"]),
                "save_image_offset_end_exclusive": int(save["end_exclusive"]),
                "size": int(ram["size"]),
                "affine_base": SAVE_PARASITE_RAM,
            }
        )
    live_parasite_prefix = {
        str(row["symbol"])
        for row in save_live
        if row["address_space"] == "SAVE_PARASITE_IMAGE_OFFSET"
        and int(row["start"]) < SAVE_PARASITE_SIZE
    }
    if live_parasite_prefix != set(save_expected):
        _fail(
            "save_layout first 0xEC4 persistent owner set differs: "
            f"{sorted(live_parasite_prefix)}"
        )
    return {
        "status": "EXACT_NON_OVERLAPPING",
        "build_config": config_identity,
        "ram_layout": {
            "path": str(RAM_LAYOUT_RELATIVE),
            "live_owner_count": len(ram_live),
            "all_live_ranges_non_overlapping": True,
            "persistent_owners": {
                symbol: ram_by_symbol[symbol] for symbol in ram_expected
            },
        },
        "save_layout": {
            "path": str(SAVE_LAYOUT_RELATIVE),
            "live_owner_count": len(save_live),
            "all_live_ranges_non_overlapping": True,
            "persistent_owners": {
                symbol: save_by_symbol[symbol] for symbol in save_expected
            },
        },
        "ram_save_affine_crosswalk": crosswalk,
        "first_parasite_live_owner_set": sorted(live_parasite_prefix),
    }


# These are the six stock save entrypoints declared by CFRU-JP's ``hooks``
# file.  Keeping the complete catalog matters: only three are compatible with
# this project's established sector-31 transaction owner.  The other three
# must remain visible as an explicit, byte-exact rejected alternative instead
# of silently disappearing from the repair plan.
SAVE_CORE_HOOKS: tuple[dict[str, Any], ...] = (
    {
        "name": "save_write_to_flash",
        "symbol": "SaveWriteToFlash",
        "address": 0x080DA7B8,
        "expected": bytes.fromhex("f0b50f1c0004020c"),
        "register": 2,
        "expected_calls": (0x080DB2BC, 0x080DB2E2, 0x080DB300, 0x080DB32A),
        "project_policy": "REJECT_SECTOR30_31_DOUBLE_WRITE",
    },
    {
        "name": "handle_write_sector",
        "symbol": "HandleWriteSector",
        "address": 0x080DA858,
        "expected": bytes.fromhex("f0b557464e464546"),
        "register": 2,
        "expected_calls": (0x080DA7D0, 0x080DA812, 0x080DAAA0),
        "project_policy": "REQUIRED_PARASITE_FRAGMENT_WRITE",
    },
    {
        "name": "handle_load_sector",
        "symbol": "HandleLoadSector",
        "address": 0x080DAE3C,
        "expected": bytes.fromhex("f0b5474680b48846"),
        "register": 2,
        "expected_calls": (0x080DAE2E,),
        "project_policy": "REQUIRED_PARASITE_FRAGMENT_AND_SECTOR30_31_LOAD",
    },
    {
        "name": "get_save_valid_status",
        "symbol": "GetSaveValidStatus",
        "address": 0x080DAEF4,
        "expected": bytes.fromhex("f0b557464e464546"),
        "register": 1,
        "expected_calls": (0x080DAE22,),
        "project_policy": "REQUIRED_MATCHED_CHUNK_VALIDATION",
    },
    {
        "name": "try_load_save_sector",
        "symbol": "TryLoadSaveSector",
        "address": 0x080DB108,
        "expected": bytes.fromhex("70b50e1c0006000e"),
        "register": 3,
        "expected_calls": (0x080DB548, 0x080DB55A),
        "project_policy": "NOT_REQUIRED_FOR_NORMAL_14_SECTOR_PARASITE",
    },
    {
        "name": "handle_saving_data",
        "symbol": "HandleSavingData",
        "address": 0x080DB230,
        "expected": bytes.fromhex("70b50006040e0649"),
        "register": 1,
        "expected_calls": (0x080DB35C, 0x080F64C4),
        "project_policy": "REJECT_SECTOR30_31_DOUBLE_WRITE",
    },
)

SAVE_LIFECYCLE_HOOKS: tuple[dict[str, Any], ...] = (
    {
        "name": "link_battle_full_save",
        "symbol": "LinkBattleSaveHook",
        "address": 0x0806F44C,
        "expected": bytes.fromhex("6bf0faff0fe06cf0"),
        "register": 0,
        "project_policy": "REQUIRED_PROMOTE_PARTIAL_LINK_SAVE_TO_NORMAL",
    },
    {
        "name": "link_trade_full_save",
        "symbol": "LinkTradeSaveHook",
        "address": 0x08053A22,
        "expected": bytes.fromhex("87f0b7fc07498722d200"),
        "register": 0,
        "project_policy": "REQUIRED_PROMOTE_PARTIAL_LINK_SAVE_TO_NORMAL",
    },
    {
        "name": "new_game_expanded_save_clear",
        "symbol": "NewGameSaveClearHook",
        "address": 0x08054324,
        "expected": bytes.fromhex("70b5464640b482b0"),
        "register": 0,
        "project_policy": "REQUIRED_CLEAR_FULL_0X2EA4_EXTENSION",
    },
)

STOCK_SAVE_SECTION_ROWS: tuple[tuple[int, int], ...] = (
    (0x0000, 0x0F24),
    (0x0000, 0x0F80),
    (0x0F80, 0x0F80),
    (0x1F00, 0x0F80),
    (0x2E80, 0x0EC0),
    (0x0000, 0x0F80),
    (0x0F80, 0x0F80),
    (0x1F00, 0x0F80),
    (0x2E80, 0x0F80),
    (0x3E00, 0x0F80),
    (0x4D80, 0x0F80),
    (0x5D00, 0x0F80),
    (0x6C80, 0x0F80),
    (0x7C00, 0x07D0),
)

LINKED_SAVE_SECTION_ROWS: tuple[tuple[int, int], ...] = (
    (0x0000, 0x0F24),
    (0x0000, 0x0FF0),
    (0x0FF0, 0x0FF0),
    (0x1FE0, 0x0FF0),
    (0x2FD0, 0x0D98),
    (0x0000, 0x0FF0),
    (0x0FF0, 0x0FF0),
    (0x1FE0, 0x0FF0),
    (0x2FD0, 0x0FF0),
    (0x3FC0, 0x0FF0),
    (0x4FB0, 0x0FF0),
    (0x5FA0, 0x0FF0),
    (0x6F90, 0x0FF0),
    (0x7F80, 0x0450),
)


RAID_CONSUMERS: tuple[dict[str, Any], ...] = (
    {
        "consumer": "HasRaidBeenCompleted",
        "entry": 0x090F3AC8,
        "operation": "FlagGet",
        "call": 0x090F3AE2,
        "target_literal": 0x090F3AEC,
        "target": FLAG_GET_THUMB,
        "base_site": 0x090F3AD0,
        "base_register": 3,
        "exclusive_end_site": None,
    },
    {
        "consumer": "SetRaidBattleCompleted",
        "entry": 0x090F3AF0,
        "operation": "FlagSet",
        "call": 0x090F3B0A,
        "target_literal": 0x090F3B14,
        "target": FLAG_SET_THUMB,
        "base_site": 0x090F3AF8,
        "base_register": 3,
        "exclusive_end_site": None,
    },
    {
        "consumer": "ClearAllRaidBattleFlags",
        "entry": 0x090F3B18,
        "operation": "FlagClear",
        "call": 0x090F3B28,
        "target_literal": 0x090F3B34,
        "target": FLAG_CLEAR_THUMB,
        "base_site": 0x090F3B1A,
        "base_register": 4,
        "exclusive_end_site": 0x090F3B38,
    },
    {
        "consumer": "sp11A_case1_ClearAllRaidBattleFlags_inline",
        "entry": 0x090F3B3C,
        "operation": "FlagClear",
        "call": 0x090F3B58,
        "target_literal": 0x090F3B88,
        "target": FLAG_CLEAR_THUMB,
        "base_site": 0x090F3B4A,
        "base_register": 4,
        "exclusive_end_site": 0x090F3B8C,
    },
    {
        "consumer": "sp11A_case0_ClearCurrentRaid",
        "entry": 0x090F3B64,
        "operation": "FlagClear",
        "call": 0x090F3B7C,
        "target_literal": 0x090F3B88,
        "target": FLAG_CLEAR_THUMB,
        "base_site": 0x090F3B6A,
        "base_register": 3,
        "exclusive_end_site": None,
    },
    {
        "consumer": "sp11B_CheckIncompleteRaid",
        "entry": 0x090F3B94,
        "operation": "FlagGet",
        "call": 0x090F3BB8,
        "target_literal": 0x090F3BEC,
        "target": FLAG_GET_THUMB,
        "base_site": 0x090F3BA2,
        "base_register": 5,
        "exclusive_end_site": 0x090F3BE4,
    },
)


def _movs_immediate(register: int, immediate: int) -> bytes:
    if not 0 <= register <= 7 or not 0 <= immediate <= 0xFF:
        _fail(f"Thumb movs immediate is not encodable: r{register}, {immediate:#x}")
    return struct.pack("<H", 0x2000 | register << 8 | immediate)


def raid_patch_plan(start: int = RECOMMENDED_RAID_START) -> list[dict[str, Any]]:
    if start & 0x1F:
        _fail(
            f"Raid base {_hex(start)} is not 0x20-aligned; existing imm8<<5 ABI cannot encode it"
        )
    end = start + RAID_FLAG_COUNT
    if not (FLAG_UNIVERSE_START <= start < end <= FLAG_UNIVERSE_END_EXCLUSIVE):
        _fail("Raid target leaves expanded flag namespace")
    immediate = start >> 5
    patches: list[dict[str, Any]] = []
    for consumer in RAID_CONSUMERS:
        register = int(consumer["base_register"])
        patches.append(
            {
                "name": f"{consumer['consumer']}_base",
                "kind": "THUMB_MOVS_IMM8_BASE_DIV_32",
                "address": int(consumer["base_site"]),
                "address_hex": _hex(int(consumer["base_site"]), 8),
                "expected_hex": _movs_immediate(register, OLD_RAID_START >> 5).hex(),
                "replacement_hex": _movs_immediate(register, immediate).hex(),
                "register": f"r{register}",
                "semantic_before": OLD_RAID_START,
                "semantic_after": start,
            }
        )
        end_site = consumer["exclusive_end_site"]
        if end_site is not None:
            patches.append(
                {
                    "name": f"{consumer['consumer']}_exclusive_end",
                    "kind": "LITTLE_ENDIAN_U32_EXCLUSIVE_END_LITERAL",
                    "address": int(end_site),
                    "address_hex": _hex(int(end_site), 8),
                    "expected_hex": struct.pack("<I", OLD_RAID_END_EXCLUSIVE).hex(),
                    "replacement_hex": struct.pack("<I", end).hex(),
                    "semantic_before": OLD_RAID_END_EXCLUSIVE,
                    "semantic_after": end,
                }
            )
    patches.sort(key=lambda row: int(row["address"]))
    if len(patches) != 9 or len({row["address"] for row in patches}) != 9:
        _fail("Raid exact patch set is not exactly nine non-overlapping sites")
    return patches


def hook_patch_plan() -> list[dict[str, Any]]:
    return [
        {
            "name": "expanded_var_pointer_global_hook",
            "kind": "THUMB_LDR_R1_LITERAL_BX_R1",
            "address": GET_VAR_POINTER,
            "address_hex": _hex(GET_VAR_POINTER, 8),
            "expected_hex": GET_VAR_POINTER_PREIMAGE.hex(),
            "replacement_hex": GET_VAR_POINTER_REPLACEMENT.hex(),
            "target": EXPANDED_VARS_HOOK_THUMB,
            "target_hex": _hex(EXPANDED_VARS_HOOK_THUMB, 8),
            "reserved_scratch_register": "r1",
        },
        {
            "name": "expanded_flag_pointer_global_hook",
            "kind": "THUMB_LDR_R1_LITERAL_BX_R1",
            "address": GET_FLAG_POINTER,
            "address_hex": _hex(GET_FLAG_POINTER, 8),
            "expected_hex": GET_FLAG_POINTER_PREIMAGE.hex(),
            "replacement_hex": GET_FLAG_POINTER_REPLACEMENT.hex(),
            "target": EXPANDED_FLAGS_HOOK_THUMB,
            "target_hex": _hex(EXPANDED_FLAGS_HOOK_THUMB, 8),
            "reserved_scratch_register": "r1",
        },
    ]


def _register_jump_stub(address: int, target: int, register: int) -> bytes:
    """CFRU ``Hook()`` と同じ Thumb literal tail-jumpを返す。"""

    if address & 1 or not 0 <= register <= 7:
        _fail(f"Thumb hook ABI differs: address={address:#x}, r{register}")
    if address & 2:
        return struct.pack(
            "<HHHI",
            0x4801 | (register << 8),
            0x4700 | (register << 3),
            0,
            target | 1,
        )
    return struct.pack(
        "<HHI",
        0x4800 | (register << 8),
        0x4700 | (register << 3),
        target | 1,
    )


def _all_linked_offsets(root: Path) -> dict[str, int]:
    """Pinned offsets.ini の全一意symbolを読む。重複名はfail-closed。"""

    raw = _require_file_hash(
        root / CFRU_LINKED_OFFSETS_RELATIVE,
        CFRU_LINKED_OFFSETS_SHA256,
        "Stage60 linked CFRU offsets",
    )
    result: dict[str, int] = {}
    duplicates: set[str] = set()
    for line in raw.decode("utf-8").splitlines():
        match = re.match(r"^(.*?):\s+([0-9A-Fa-f]{8})\s*$", line)
        if not match:
            continue
        name = match.group(1).strip()
        value = int(match.group(2), 16)
        if name in result and result[name] != value:
            duplicates.add(name)
        else:
            result[name] = value
    if duplicates:
        _fail(f"linked offsets ambiguous symbols: {sorted(duplicates)[:16]}")
    return result


def _parse_hook_span(
    text: str, *, start_marker: str, end_marker: str
) -> list[dict[str, Any]]:
    """upstream ``hooks`` の指定sectionから有効なhook行だけを読む。"""

    start = text.find(start_marker)
    if start < 0:
        _fail(f"CFRU hook section start missing: {start_marker}")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0 or end <= start:
        _fail(f"CFRU hook section end missing: {end_marker}")
    rows: list[dict[str, Any]] = []
    for line in text[start + len(start_marker):end].splitlines():
        match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_.]*)\s+"
            r"(?:0x)?([0-9A-Fa-f]{6,8})\s+([0-7])\s*$",
            line.strip(),
        )
        if not match:
            continue
        rows.append(
            {
                "symbol": match.group(1),
                "address": int(match.group(2), 16),
                "register": int(match.group(3)),
            }
        )
    if not rows:
        _fail(f"CFRU hook section has no active rows: {start_marker}")
    return rows


def _canonical_hook_observation(
    raw: bytes,
    offsets: Mapping[str, int],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    symbol = str(row["symbol"])
    if symbol not in offsets:
        _fail(f"linked hook symbol missing from offsets.ini: {symbol}")
    address = int(row["address"])
    target = int(offsets[symbol]) & ~1
    expected = _register_jump_stub(address, target, int(row["register"]))
    actual = _rom_slice(raw, address, len(expected), f"hook observation {symbol}")
    return {
        "symbol": symbol,
        "address": address,
        "address_hex": _hex(address, 8),
        "scratch_register": f"r{int(row['register'])}",
        "linked_target": target,
        "linked_target_hex": _hex(target, 8),
        "canonical_stub_hex": expected.hex(),
        "stage60_hex": actual.hex(),
        "canonical_connected": actual == expected,
    }


def _parasite_live_consumer_contract(root: Path, raw: bytes) -> dict[str, Any]:
    """parasite image の各候補をStage60の実接続rootまで追跡する。"""

    hook_raw = _require_file_hash(
        root / CFRU_HOOK_MANIFEST_RELATIVE,
        CFRU_HOOK_MANIFEST_SHA256,
        "CFRU hook manifest",
    )
    hook_text = hook_raw.decode("utf-8")
    offsets = _all_linked_offsets(root)

    features: dict[str, dict[str, Any]] = {}
    for feature, (start_marker, end_marker) in PARASITE_HOOK_SECTION_SPANS.items():
        parsed = _parse_hook_span(
            hook_text,
            start_marker=start_marker,
            end_marker=end_marker,
        )
        observed = [
            _canonical_hook_observation(raw, offsets, row) for row in parsed
        ]
        connected = [row for row in observed if row["canonical_connected"]]
        features[feature] = {
            "hook_count": len(observed),
            "canonical_connected_count": len(connected),
            "canonical_connected_symbols": [row["symbol"] for row in connected],
            "hooks": observed,
        }

    # Pedometers have one stock entry hook inside the broad Overworld section;
    # naming it explicitly avoids treating unrelated battle-safe overworld
    # hooks as evidence for the state owner.
    pedometer_row = None
    last_ball_row = None
    for line in hook_text.splitlines():
        match = re.match(
            r"^(TryStartStepCountScript|LastUsedBallOverrideHook)\s+"
            r"(?:0x)?([0-9A-Fa-f]{6,8})\s+([0-7])\s*$",
            line.strip(),
        )
        if not match:
            continue
        row = {
            "symbol": match.group(1),
            "address": int(match.group(2), 16),
            "register": int(match.group(3)),
        }
        if match.group(1) == "TryStartStepCountScript":
            pedometer_row = row
        else:
            last_ball_row = row
    if pedometer_row is None or last_ball_row is None:
        _fail("pedometer/last-ball canonical hook row missing")
    pedometer = _canonical_hook_observation(raw, offsets, pedometer_row)
    last_ball = _canonical_hook_observation(raw, offsets, last_ball_row)
    features["pedometers"] = {
        "hook_count": 1,
        "canonical_connected_count": int(pedometer["canonical_connected"]),
        "canonical_connected_symbols": (
            [pedometer["symbol"]] if pedometer["canonical_connected"] else []
        ),
        "hooks": [pedometer],
    }
    features["last_used_ball"] = {
        "hook_count": 1,
        "canonical_connected_count": int(last_ball["canonical_connected"]),
        "canonical_connected_symbols": (
            [last_ball["symbol"]] if last_ball["canonical_connected"] else []
        ),
        "hooks": [last_ball],
    }

    all_targets = {
        int(hook["linked_target"])
        for feature in features.values()
        for hook in feature["hooks"]
    }
    calls_by_target = _thumb_bl_calls_by_target(raw, all_targets)
    for feature in features.values():
        external_bl: list[dict[str, Any]] = []
        external_pointers: list[dict[str, Any]] = []
        for hook in feature["hooks"]:
            target = int(hook["linked_target"])
            for call in calls_by_target[target]:
                if not CFRU_LINKED_OUTPUT_START <= call < CFRU_LINKED_OUTPUT_END_EXCLUSIVE:
                    external_bl.append(
                        {
                            "symbol": hook["symbol"],
                            "address": call,
                            "address_hex": _hex(call, 8),
                        }
                    )
            for address in _u32_pointer_sites(raw, target | 1):
                if not (
                    CFRU_LINKED_OUTPUT_START
                    <= address
                    < CFRU_LINKED_OUTPUT_END_EXCLUSIVE
                ):
                    external_pointers.append(
                        {
                            "symbol": hook["symbol"],
                            "address": address,
                            "address_hex": _hex(address, 8),
                        }
                    )
        feature["external_thumb_bl_calls"] = external_bl
        feature["external_thumb_pointer_sites"] = external_pointers
        feature["external_inbound_count"] = len(external_bl) + len(external_pointers)

    expected_counts = {
        "keypad": 6,
        "dynamic_overworld_palettes": 40,
        "followers": 20,
        "updated_repel": 2,
        "expanded_bag": 36,
        "expanded_coins": 6,
        "wild_encounter_roamer_paths": 13,
        "roamers": 12,
        "pedometers": 1,
        "last_used_ball": 1,
    }
    actual_counts = {name: row["hook_count"] for name, row in features.items()}
    if actual_counts != expected_counts:
        _fail(f"parasite feature hook counts differ: {actual_counts}")
    for name in (
        "keypad",
        "dynamic_overworld_palettes",
        "followers",
        "updated_repel",
        "expanded_bag",
        "expanded_coins",
        "wild_encounter_roamer_paths",
        "roamers",
        "pedometers",
    ):
        if features[name]["canonical_connected_count"] != 0:
            _fail(f"unexpected Stage60 CFRU field feature connection: {name}")
        if features[name]["external_inbound_count"] != 0:
            _fail(f"unexpected direct Stage60 inbound edge to field feature: {name}")
    if features["last_used_ball"]["canonical_connected_count"] != 1:
        _fail("Stage60 last-used-ball hook is not connected")
    if not any(
        row["address"] == 0x08032464
        for row in features["last_used_ball"]["external_thumb_pointer_sites"]
    ):
        _fail("Stage60 last-used-ball external hook pointer is absent")

    # The battle scripting command table is a separately repointed indirect
    # root.  Command EF is the write path and must stay pinned to CFRU's
    # atkEF_handleballthrow, which writes gLastUsedBall on a real throw.
    command_table = offsets.get("gBattleScriptingCommandsTable")
    ball_throw = offsets.get("atkEF_handleballthrow")
    if command_table != 0x0903F450 or ball_throw != 0x090DE100:
        _fail("last-used-ball battle command symbols drifted")
    command_pointer_address = command_table + 0xEF * 4
    command_pointer = struct.unpack(
        "<I", _rom_slice(raw, command_pointer_address, 4, "battle command EF")
    )[0]
    if command_pointer != ball_throw | 1:
        _fail("battle command EF no longer reaches atkEF_handleballthrow")
    catching = _require_file_hash(
        root / CFRU_CATCHING_SOURCE_RELATIVE,
        CFRU_CATCHING_SOURCE_SHA256,
        "CFRU catching.c",
    ).decode("utf-8")
    if "gLastUsedBall = gLastUsedItem;" not in catching:
        _fail("last-used-ball write statement missing")

    linked_addresses = sorted({int(value) & ~1 for value in offsets.values()})

    def literal_consumer(symbol: str, value: int) -> dict[str, Any]:
        if symbol not in offsets:
            _fail(f"linked literal consumer symbol missing: {symbol}")
        address = int(offsets[symbol]) & ~1
        later = [candidate for candidate in linked_addresses if candidate > address]
        if not later:
            _fail(f"linked literal consumer has no extent: {symbol}")
        end = later[0]
        body = _rom_slice(raw, address, end - address, symbol)
        literal = struct.pack("<I", value)
        count = body.count(literal)
        if count < 1:
            _fail(f"linked literal consumer no longer references {value:#x}: {symbol}")
        return {
            "symbol": symbol,
            "address": address,
            "address_hex": _hex(address, 8),
            "end_exclusive": end,
            "end_exclusive_hex": _hex(end, 8),
            "literal": value,
            "literal_hex": _hex(value, 8),
            "literal_count": count,
        }

    # Some Stage60/DPE roots invoke CFRU field-move helpers even though the
    # 20 follower feature hooks themselves are absent.  These five paths only
    # read the inactive sentinel/permission bits; the pinned sources and exact
    # linked binary have no reachable follower writer.  Preserve this nuance
    # instead of incorrectly calling the RAM completely unreferenced.
    follower_read_specs = (
        ("GetPlayerSpeed", 0x080BE938),
        ("SetUpFieldMove_Fly", 0x092CF9BC),
        ("SetUpFieldMove_Surf", 0x092CF9EC),
        ("SetUpFieldMove_Waterfall", 0x092CFA1C),
        ("SetUpFieldMove_Dive", 0x092CFA34),
    )
    follower_read_roots: list[dict[str, Any]] = []
    for symbol, pointer_site in follower_read_specs:
        consumer = literal_consumer(symbol, 0x0203B790)
        target = int(consumer["address"]) | 1
        _require_rom_bytes(
            raw,
            pointer_site,
            struct.pack("<I", target),
            f"follower read root {symbol}",
        )
        follower_read_roots.append(
            {
                **consumer,
                "pointer_site": pointer_site,
                "pointer_site_hex": _hex(pointer_site, 8),
                "target_thumb": target,
                "target_thumb_hex": _hex(target, 8),
                "access": "READ_INACTIVE_SENTINEL_OR_PERMISSION_BITS",
            }
        )

    # The routine-pointer table exposes sp097/sp098, which can reach
    # TryStartRoamerEncounter.  The exact relocated event graph invokes
    # neither special and also has no sp129 initializer, while every explicit
    # roamer writer hook remains disconnected.  Therefore gRoamers is a
    # dormant zero-state owner, not additional durable gameplay state.
    roamer_try = literal_consumer("TryStartRoamerEncounter", 0x0203B9A8)
    random_wild = int(offsets.get("StartRandomWildEncounter", 0)) & ~1
    roamer_specials = (
        (0x97, "sp097_StartGroundBattle", 0x081632C4),
        (0x98, "sp098_StartWaterBattle", 0x081632C8),
    )
    roamer_special_roots: list[dict[str, Any]] = []
    random_calls = _thumb_bl_calls_by_target(raw, {random_wild})[random_wild]
    try_calls = _thumb_bl_calls_by_target(raw, {int(roamer_try["address"])})[
        int(roamer_try["address"])
    ]
    if random_calls != [0x09129AE8, 0x09129AF4] \
            or try_calls[:2] != [0x091339EA, 0x09133A0C]:
        _fail("CFRU special-to-roamer read call chain differs")
    for special_id, symbol, pointer_site in roamer_specials:
        target = int(offsets.get(symbol, 0)) & ~1
        if not target:
            _fail(f"CFRU roamer special symbol missing: {symbol}")
        _require_rom_bytes(
            raw,
            pointer_site,
            struct.pack("<I", target | 1),
            f"roamer special root {symbol}",
        )
        roamer_special_roots.append(
            {
                "special_id": special_id,
                "special_id_hex": _hex(special_id, 3),
                "symbol": symbol,
                "pointer_site": pointer_site,
                "pointer_site_hex": _hex(pointer_site, 8),
                "target": target,
                "target_hex": _hex(target, 8),
            }
        )
    # This report is rebuilt whenever the Stage61 owner graph changes, so a
    # source-level fixed SHA would make the namespace audit stale immediately.
    # Bind it to the same generated Stage61 audit instead: both outputs must
    # identify the same task/input and carry the exact same namespace policy.
    semantic_raw = (root / STAGE61_EVENT_SEMANTIC_RELATIVE).read_bytes()
    semantic = json.loads(semantic_raw)
    generated_for_semantic = json.loads(
        (root / STAGE61_AUDIT_RELATIVE).read_text(encoding="utf-8")
    )
    if (
        semantic.get("schema_version") != 1
        or semantic.get("task") != generated_for_semantic.get("task")
        or semantic.get("status") != "PASS"
        or semantic.get("inputs", {}).get("stage60_sha256")
            != STAGE60_ROM_SHA256
        or semantic.get("stage61_namespace_policy")
            != generated_for_semantic.get("namespace_policy")
        or semantic.get("stage61_bill_sevii_scope_guard")
            != generated_for_semantic.get("bill_sevii_scope_guard")
    ):
        _fail("Stage61 event semantic relocation artifact binding differs")
    special_policy = (
        semantic.get("stage61_namespace_policy", {})
        .get("numeric_categories", {})
        .get("special", {})
    )
    event_special_ids = {
        int(row["source"]) for row in special_policy.get("mappings", [])
    }
    forbidden_roamer_specials = {0x97, 0x98, 0x129}
    if forbidden_roamer_specials & event_special_ids:
        _fail(
            "Stage61 event graph reaches dormant CFRU roamer state: "
            f"{sorted(forbidden_roamer_specials & event_special_ids)}"
        )
    if len(event_special_ids) != 90:
        _fail(f"Stage61 event special universe differs: {len(event_special_ids)}")

    noncanonical_state_paths = {
        "gFollowerState": {
            "status": "LIVE_READ_INACTIVE_SENTINEL_NO_CONNECTED_WRITER",
            "read_root_count": len(follower_read_roots),
            "read_roots": follower_read_roots,
            "connected_writer_count": 0,
            "event_initializer_present": False,
            "persistent_owner_live": False,
        },
        "gRoamers": {
            "status": "DORMANT_ROUTINE_POINTER_READ_NOT_IN_EVENT_UNIVERSE",
            "read_special_roots": roamer_special_roots,
            "call_chain": {
                "start_random_wild_encounter": random_wild,
                "start_random_call_sites": random_calls,
                "try_start_roamer_encounter": int(roamer_try["address"]),
                "try_start_call_sites": try_calls,
            },
            "literal_consumer": roamer_try,
            "event_special_id_count": len(event_special_ids),
            "absent_special_ids": sorted(forbidden_roamer_specials),
            "connected_writer_count": 0,
            "persistent_owner_live": False,
        },
    }

    regions: list[dict[str, Any]] = []
    for source in PARASITE_CANDIDATE_REGIONS:
        start = int(source["start"])
        end = int(source["end_exclusive"])
        if not SAVE_PARASITE_RAM <= start < end <= SAVE_SECTOR30_IMAGE:
            _fail(f"parasite candidate outside image: {source['symbol']}")
        regions.append(
            {
                **source,
                "size": end - start,
                "image_offset_start": start - SAVE_PARASITE_RAM,
                "image_offset_end_exclusive": end - SAVE_PARASITE_RAM,
            }
        )
    if any(
        left["end_exclusive"] > right["start"]
        for left, right in zip(regions, regions[1:])
    ):
        _fail("parasite candidate regions overlap or are not ordered")

    full_bag_size = EXPANDED_BAG_END_EXCLUSIVE - EXPANDED_BAG_START
    if full_bag_size != 0x0C28:
        _fail(f"expanded bag size differs: {full_bag_size:#x}")
    if STOCK_MAIN_SAVE_TAIL_CAPACITY != sum(
        SAVE_SECTOR_DATA_SIZE - STOCK_SAVE_SECTION_ROWS[index][1]
        for index in (0, 4, 13)
    ):
        _fail("stock main-save tail capacity differs")

    declared_live = {
        row["symbol"]: row
        for row in _parasite_owner_contract(root)["live_owners"]
        if row["offset_start"] < SAVE_PARASITE_SIZE
    }
    if set(declared_live) != {
        "expanded_flags",
        "expanded_vars",
        "last_used_ball_u16",
        "cfru_player_coins_u32",
    }:
        _fail(f"declared first-parasite LIVE owners differ: {sorted(declared_live)}")

    ram_layout_path = root / "config/ram_layout.csv"
    with ram_layout_path.open(encoding="utf-8", newline="") as handle:
        ram_rows = list(csv.DictReader(handle))
    last_ball_ram_rows = [row for row in ram_rows if row["symbol"] == "gLastUsedBall"]
    if len(last_ball_ram_rows) != 1:
        _fail(f"ram_layout gLastUsedBall row count differs: {len(last_ball_ram_rows)}")
    last_ball_ram = last_ball_ram_rows[0]
    if (
        last_ball_ram["address_space"],
        int(last_ball_ram["start"], 0),
        int(last_ball_ram["end_exclusive"], 0),
        last_ball_ram["persistence"],
        last_ball_ram["status"],
    ) != ("EWRAM", 0x0203B6EC, 0x0203B6EE, "FLASH", "LIVE"):
        _fail("ram_layout gLastUsedBall contract differs")

    # Stage61 replaces the *inner* CFRU town-map renderer to normalize map
    # sections.  That renderer reads gRoamers, but its only two callers are
    # the two CFRU town-map hook adapters.  Prove against the final Stage61 ROM
    # that neither adapter is rooted at its stock entry and that the Stage61
    # wrapper has no second inbound edge.  An installed inner jump by itself
    # must not be mistaken for a LIVE persistent owner.
    stage61_rom = (root / STAGE61_ROM_RELATIVE).read_bytes()
    stage61_metadata = json.loads(
        (root / STAGE61_METADATA_RELATIVE).read_text(encoding="utf-8")
    )
    stage61_generated = json.loads(
        (root / STAGE61_AUDIT_RELATIVE).read_text(encoding="utf-8")
    )
    if (
        len(stage61_rom) != ROM_SIZE
        or _sha(stage61_rom)
        != stage61_metadata.get("output", {}).get("sha256")
    ):
        _fail("Stage61 ROM identity differs during roamer reachability audit")
    town_renderer = offsets.get("CreateTownMapRoamerSprites")
    caller_symbols = (
        "CreateRoamerIconTownMapHook",
        "CreateRoamerIconTownMapPostSwitchMapHook",
    )
    caller_targets = [offsets.get(name) for name in caller_symbols]
    if town_renderer != 0x09125ECC or caller_targets != [0x09097774, 0x0909777C]:
        _fail("Stage61 roamer inner caller symbols drifted")
    inner_calls = _thumb_bl_calls_by_target(stage61_rom, {town_renderer})[
        town_renderer
    ]
    if inner_calls != caller_targets:
        _fail(
            "Stage61 town-map roamer inner call universe differs: "
            f"{[hex(value) for value in inner_calls]}"
        )
    roamer_hooks = {
        str(row["symbol"]): row for row in features["roamers"]["hooks"]
    }
    stage61_caller_roots: list[dict[str, Any]] = []
    for symbol, target in zip(caller_symbols, caller_targets):
        if symbol not in roamer_hooks:
            _fail(f"Stage61 roamer caller hook missing: {symbol}")
        source_row = roamer_hooks[symbol]
        observation = _canonical_hook_observation(
            stage61_rom,
            offsets,
            {
                "symbol": symbol,
                "address": int(source_row["address"]),
                "register": int(str(source_row["scratch_register"])[1:]),
            },
        )
        pointer_sites = [
            address
            for address in _u32_pointer_sites(stage61_rom, int(target) | 1)
            if not (
                CFRU_LINKED_OUTPUT_START
                <= address
                < CFRU_LINKED_OUTPUT_END_EXCLUSIVE
            )
        ]
        direct_calls = [
            address
            for address in _thumb_bl_calls_by_target(
                stage61_rom, {int(target)}
            )[int(target)]
            if not (
                CFRU_LINKED_OUTPUT_START
                <= address
                < CFRU_LINKED_OUTPUT_END_EXCLUSIVE
            )
        ]
        if observation["canonical_connected"] or pointer_sites or direct_calls:
            _fail(f"Stage61 unexpectedly roots CFRU roamer caller: {symbol}")
        stage61_caller_roots.append(
            {
                **observation,
                "external_thumb_pointer_sites": pointer_sites,
                "external_thumb_bl_calls": direct_calls,
            }
        )
    declarations = {
        str(row.get("name")): row
        for row in stage61_generated.get("change_audit", {}).get(
            "declarations", []
        )
    }
    declaration = declarations.get("cfru_town_map_roamer_context")
    wrapper = stage61_metadata.get("runtime", {}).get("symbols", {}).get(
        "Stage61MapSection_CreateTownMapRoamerSprites"
    )
    if declaration is None or wrapper is None:
        _fail("Stage61 town-map roamer context declaration/symbol missing")
    replacement = bytes.fromhex(str(declaration["replacement_hex"]))
    if (
        int(declaration["start"]) + ROM_BASE != town_renderer
        or declaration.get("category") != "MAP_SECTION_CONSUMER_SEMANTICS"
        or len(replacement) != 8
        or struct.unpack_from("<I", replacement, 4)[0] != int(wrapper) | 1
    ):
        _fail("Stage61 town-map roamer context declaration differs")
    _require_rom_bytes(
        stage61_rom, town_renderer, replacement, "Stage61 town-map roamer context"
    )
    wrapper_calls = _thumb_bl_calls_by_target(stage61_rom, {int(wrapper)})[
        int(wrapper)
    ]
    wrapper_pointer_sites = _u32_pointer_sites(stage61_rom, int(wrapper) | 1)
    if wrapper_calls or wrapper_pointer_sites != [town_renderer + 4]:
        _fail("Stage61 town-map roamer wrapper has an unexpected inbound edge")
    stage61_source = (
        root / STAGE61_RUNTIME_SOURCE_RELATIVE
    ).read_text(encoding="utf-8")
    if "volatile u8 *roamer = G_ROAMERS + index * 0x18u;" not in stage61_source:
        _fail("Stage61 town-map roamer adapter source no longer exposes its read")
    stage61_roamer_adapter = {
        "status": "INNER_ADAPTER_INSTALLED_BUT_ALL_CALLER_ROOTS_UNCONNECTED",
        "inner_entry": town_renderer,
        "inner_entry_hex": _hex(town_renderer, 8),
        "inner_call_sites": inner_calls,
        "inner_call_sites_hex": [_hex(value, 8) for value in inner_calls],
        "caller_roots": stage61_caller_roots,
        "wrapper": int(wrapper),
        "wrapper_hex": _hex(int(wrapper), 8),
        "wrapper_pointer_sites": wrapper_pointer_sites,
        "persistent_owner_live": False,
    }

    return {
        "status": "LAST_USED_BALL_ONLY_ADDITIONAL_DURABLE_OWNER",
        "regions": regions,
        "feature_hook_evidence": features,
        "noncanonical_state_paths": noncanonical_state_paths,
        "last_used_ball": {
            "ram_start": 0x0203B6EC,
            "ram_end_exclusive": 0x0203B6EE,
            "image_offset_start": 0x0604,
            "image_offset_end_exclusive": 0x0606,
            "read_root": last_ball,
            "write_root": {
                "table": "gBattleScriptingCommandsTable",
                "command": 0xEF,
                "pointer_address": command_pointer_address,
                "pointer_address_hex": _hex(command_pointer_address, 8),
                "target": command_pointer,
                "target_hex": _hex(command_pointer, 8),
                "statement": "gLastUsedBall = gLastUsedItem;",
            },
            "required_in_custom_record": True,
        },
        "expanded_bag": {
            "ram_start": EXPANDED_BAG_START,
            "ram_end_exclusive": EXPANDED_BAG_END_EXCLUSIVE,
            "size": EXPANDED_BAG_SIZE,
            "parasite_prefix_size": SAVE_SECTOR30_IMAGE - EXPANDED_BAG_START,
            "sector30_suffix_size": (
                EXPANDED_BAG_END_EXCLUSIVE - SAVE_SECTOR30_IMAGE
            ),
            "fits_stock_main_save_tails": (
                EXPANDED_BAG_SIZE <= STOCK_MAIN_SAVE_TAIL_CAPACITY
            ),
            "stage60_status": "UNCONNECTED_STOCK_VEGA_BAG_REMAINS_AUTHORITATIVE",
        },
        "stage61_roamer_context_adapter": stage61_roamer_adapter,
        "stock_main_save_tail_capacity": STOCK_MAIN_SAVE_TAIL_CAPACITY,
        "declared_live_first_parasite_owners": sorted(declared_live),
        "ram_layout_last_used_ball": dict(last_ball_ram),
        "minimum_custom_payload": {
            "expanded_flags": 0x200,
            "expanded_vars": 0x400,
            "last_used_ball": 2,
            "declared_player_coins": 4,
            "total": 0x606,
        },
        "conclusion": (
            "Stage60で追加永続化が必須なのはgLastUsedBall。gFollowerStateには"
            "inactive判定のread-only rootがあるがwriterはなく、gRoamersのroutine "
            "pointer read pathは実event special集合から未到達。expanded bag/"
            "pedometer/expanded coinsもwriter root未接続で保存対象ではない"
        ),
    }


def _save_hook_patch(row: Mapping[str, Any]) -> dict[str, Any]:
    symbol = str(row["symbol"])
    target = LINKED_SAVE_SYMBOLS[symbol]
    address = int(row["address"])
    replacement = _register_jump_stub(address, target, int(row["register"]))
    expected = bytes(row["expected"])
    if len(replacement) != len(expected):
        _fail(f"{symbol} hook size differs: {len(replacement)} != {len(expected)}")
    return {
        "name": f"cfru_save_expansion::{row['name']}",
        "kind": "THUMB_LITERAL_TAIL_JUMP",
        "address": address,
        "address_hex": _hex(address, 8),
        "expected_hex": expected.hex(),
        "replacement_hex": replacement.hex(),
        "target_symbol": symbol,
        "target": target,
        "target_hex": _hex(target, 8),
        "target_thumb": target | 1,
        "target_thumb_hex": _hex(target | 1, 8),
        "scratch_register": f"r{int(row['register'])}",
        "project_policy": str(row["project_policy"]),
    }


def save_core_hook_catalog() -> list[dict[str, Any]]:
    """upstream 6 core entryのbyte-exact候補を安全性判定付きで返す。"""

    return [_save_hook_patch(row) for row in SAVE_CORE_HOOKS]


def save_expansion_patch_plan() -> list[dict[str, Any]]:
    """監査用CFRU direct plan。旧save migrationなしには採用禁止。"""

    required_core = {
        "handle_write_sector",
        "handle_load_sector",
        "get_save_valid_status",
    }
    patches = [
        _save_hook_patch(row)
        for row in SAVE_CORE_HOOKS
        if row["name"] in required_core
    ]
    patches.append(
        {
            "name": "cfru_save_expansion::save_section_offsets",
            "kind": "LITTLE_ENDIAN_U32_POINTER",
            "address": SAVE_SECTION_OFFSETS_POINTER_SITE,
            "address_hex": _hex(SAVE_SECTION_OFFSETS_POINTER_SITE, 8),
            "expected_hex": struct.pack("<I", STOCK_SAVE_SECTION_OFFSETS).hex(),
            "replacement_hex": struct.pack("<I", LINKED_SAVE_SECTION_OFFSETS).hex(),
            "target_symbol": "gSaveSectionOffsets",
            "target": LINKED_SAVE_SECTION_OFFSETS,
            "target_hex": _hex(LINKED_SAVE_SECTION_OFFSETS, 8),
            "project_policy": "REQUIRED_MATCH_PARASITE_SLOT_CAPACITY",
        }
    )
    patches.extend(_save_hook_patch(row) for row in SAVE_LIFECYCLE_HOOKS)
    patches.sort(key=lambda row: int(row["address"]))
    if len(patches) != 7 or len({row["address"] for row in patches}) != 7:
        _fail("recommended save expansion patch set is not exactly seven sites")
    return patches


def all_upstream_save_patch_plan() -> list[dict[str, Any]]:
    """監査用: upstream 6 core + table + lifecycle 3 の全exact候補。"""

    patches = save_core_hook_catalog()
    patches.append(
        {
            "name": "cfru_save_expansion::save_section_offsets",
            "kind": "LITTLE_ENDIAN_U32_POINTER",
            "address": SAVE_SECTION_OFFSETS_POINTER_SITE,
            "address_hex": _hex(SAVE_SECTION_OFFSETS_POINTER_SITE, 8),
            "expected_hex": struct.pack("<I", STOCK_SAVE_SECTION_OFFSETS).hex(),
            "replacement_hex": struct.pack("<I", LINKED_SAVE_SECTION_OFFSETS).hex(),
            "target_symbol": "gSaveSectionOffsets",
            "target": LINKED_SAVE_SECTION_OFFSETS,
            "target_hex": _hex(LINKED_SAVE_SECTION_OFFSETS, 8),
            "project_policy": "REQUIRED_MATCH_PARASITE_SLOT_CAPACITY",
        }
    )
    patches.extend(_save_hook_patch(row) for row in SAVE_LIFECYCLE_HOOKS)
    patches.sort(key=lambda row: int(row["address"]))
    if len(patches) != 10 or len({row["address"] for row in patches}) != 10:
        _fail("upstream save patch catalog is not exactly ten sites")
    return patches


def apply_exact_patches(raw: bytes, patches: Sequence[Mapping[str, Any]]) -> bytes:
    """全 preimage を先に検査してから immutable ROM copy へ patch する。"""

    checked: list[tuple[int, bytes, bytes, str]] = []
    occupied: set[int] = set()
    for row in patches:
        address = int(row["address"])
        expected = bytes.fromhex(str(row["expected_hex"]))
        replacement = bytes.fromhex(str(row["replacement_hex"]))
        name = str(row["name"])
        if len(expected) != len(replacement):
            _fail(f"{name} patch changes size")
        actual = _rom_slice(raw, address, len(expected), name)
        if actual != expected:
            _fail(
                f"{name} preimage mismatch at {_hex(address, 8)}: "
                f"{actual.hex()} != {expected.hex()}"
            )
        bytes_owned = set(range(address, address + len(expected)))
        if occupied & bytes_owned:
            _fail(f"patch ranges overlap at {name}")
        occupied.update(bytes_owned)
        checked.append((address, expected, replacement, name))
    output = bytearray(raw)
    for address, _expected, replacement, _name in checked:
        offset = address - ROM_BASE
        output[offset:offset + len(replacement)] = replacement
    return bytes(output)


def _thumb_bl_calls_to(raw: bytes, target: int) -> list[int]:
    """ROM 全域の ARMv4T two-halfword BL encoding を exact target へ解決する。"""

    calls: list[int] = []
    for offset in range(0, len(raw) - 3, 2):
        high = raw[offset] | raw[offset + 1] << 8
        low = raw[offset + 2] | raw[offset + 3] << 8
        if high & 0xF800 != 0xF000 or low & 0xF800 != 0xF800:
            continue
        displacement = (high & 0x07FF) << 12 | (low & 0x07FF) << 1
        if displacement & (1 << 22):
            displacement -= 1 << 23
        call = ROM_BASE + offset
        if call + 4 + displacement == target:
            calls.append(call)
    return calls


def _thumb_bl_target(address: int, raw: bytes) -> int:
    """4-byte ARMv4T Thumb BLをexact destinationへ解決する。"""

    if len(raw) != 4 or address & 1:
        _fail("Thumb BL address/size differs")
    high, low = struct.unpack("<HH", raw)
    if high & 0xF800 != 0xF000 or low & 0xF800 != 0xF800:
        _fail(f"Thumb BL encoding differs at {_hex(address, 8)}")
    displacement = (high & 0x07FF) << 12 | (low & 0x07FF) << 1
    if displacement & (1 << 22):
        displacement -= 1 << 23
    return address + 4 + displacement


def _hook_binary_contract(raw: bytes) -> dict[str, Any]:
    _require_rom_bytes(raw, GET_VAR_POINTER, GET_VAR_POINTER_PREIMAGE, "GetVarPointer stock entry")
    _require_rom_bytes(raw, GET_FLAG_POINTER, GET_FLAG_POINTER_PREIMAGE, "GetFlagPointer stock entry")
    _require_rom_bytes(
        raw,
        SPECIAL_FLAG_POINTER_LITERAL,
        struct.pack("<I", SPECIAL_FLAG_RAM),
        "GetFlagPointer stock special-flag owner literal",
    )
    _require_rom_bytes(raw, EXPANDED_VARS_HOOK, EXPANDED_VARS_HOOK_BODY, "ExpandedVarsHook body")
    _require_rom_bytes(raw, EXPANDED_FLAGS_HOOK, EXPANDED_FLAGS_HOOK_BODY, "ExpandedFlagsHook body")
    _require_rom_bytes(
        raw,
        GET_EXPANDED_FLAG_POINTER,
        GET_EXPANDED_FLAG_POINTER_BODY,
        "GetExpandedFlagPointer body",
    )
    _require_rom_bytes(
        raw,
        GET_EXPANDED_VAR_POINTER,
        GET_EXPANDED_VAR_POINTER_BODY,
        "GetExpandedVarPointer body",
    )
    flag_calls = _thumb_bl_calls_to(raw, GET_EXPANDED_FLAG_POINTER)
    var_calls = _thumb_bl_calls_to(raw, GET_EXPANDED_VAR_POINTER)
    if flag_calls != [0x0909710E] or var_calls != [0x090970E6]:
        _fail(
            "expanded resolver call universe differs: "
            f"flags={[hex(x) for x in flag_calls]}, vars={[hex(x) for x in var_calls]}"
        )
    return {
        "status": "CRITICAL_UNCONNECTED",
        "global_entries": {
            "GetFlagPointer": {
                "address": GET_FLAG_POINTER,
                "address_hex": _hex(GET_FLAG_POINTER, 8),
                "current_hex": GET_FLAG_POINTER_PREIMAGE.hex(),
                "connected": False,
                "stock_special_flag_fallback": {
                    "id_range": [0x4000, 0x407F],
                    "literal_address": SPECIAL_FLAG_POINTER_LITERAL,
                    "owner_address": SPECIAL_FLAG_RAM,
                    "owner_address_hex": _hex(SPECIAL_FLAG_RAM, 8),
                    "size": 16,
                },
            },
            "GetVarPointer": {
                "address": GET_VAR_POINTER,
                "address_hex": _hex(GET_VAR_POINTER, 8),
                "current_hex": GET_VAR_POINTER_PREIMAGE.hex(),
                "connected": False,
            },
        },
        "linked_entries": {
            "ExpandedFlagsHook": {
                "address": EXPANDED_FLAGS_HOOK,
                "thumb_entry": EXPANDED_FLAGS_HOOK_THUMB,
                "body_sha256": _sha(EXPANDED_FLAGS_HOOK_BODY),
                "resolver_call": flag_calls[0],
                "fallback": {
                    "literal_address": 0x0909711C,
                    "target_thumb": 0x0806DDBD,
                    "target_instruction": 0x0806DDBC,
                    "behavior": "resolver NULL の低/special flag は退避済み prologue state で stock continuation へ戻る",
                },
            },
            "ExpandedVarsHook": {
                "address": EXPANDED_VARS_HOOK,
                "thumb_entry": EXPANDED_VARS_HOOK_THUMB,
                "body_sha256": _sha(EXPANDED_VARS_HOOK_BODY),
                "resolver_call": var_calls[0],
                "fallback": {
                    "null_literal_address": 0x090970FC,
                    "null_target_thumb": 0x0806DC51,
                    "null_target_instruction": 0x0806DC50,
                    "sentinel_literal_address": 0x09097100,
                    "sentinel_target_thumb": 0x0806DC57,
                    "sentinel_target_instruction": 0x0806DC56,
                    "behavior": "NULL は stock continuation、sentinel 1 は stock NULL return path",
                },
            },
        },
        "linked_resolvers": {
            "GetExpandedFlagPointer": {
                "address": GET_EXPANDED_FLAG_POINTER,
                "thumb_entry": GET_EXPANDED_FLAG_POINTER_THUMB,
                "body_sha256": _sha(GET_EXPANDED_FLAG_POINTER_BODY),
                "literal_contract": {
                    "subtract_0x0900_at": 0x0912820C,
                    "subtract_0x1900_at": 0x09128210,
                    "negative_var8000_at": 0x09128214,
                    "var8000_at": 0x09128218,
                    "expanded_flags_at": 0x0912821C,
                },
                "formula": "0x0203B0E8 + ((u16(id) - 0x0900) >> 3), for 0x0900 <= id < 0x1900",
            },
            "GetExpandedVarPointer": {
                "address": GET_EXPANDED_VAR_POINTER,
                "thumb_entry": GET_EXPANDED_VAR_POINTER_THUMB,
                "body_sha256": _sha(GET_EXPANDED_VAR_POINTER_BODY),
                "literal_contract": {
                    "subtract_0x5000_at": 0x09128250,
                    "subtract_0x4100_at": 0x09128254,
                    "affine_base_at": 0x09128258,
                },
                "formula": "0x0203B2E8 + 2 * (u16(id) - 0x5000), for 0x5000 <= id < 0x5200",
            },
        },
        "repair_patches": hook_patch_plan(),
        "repair_order": [
            "両 global entry hook を同一 ROM build transaction で接続する",
            "低 flag/0x4000 vars の stock fallback と expanded flag/var routing を実mGBAで検証する",
            "その後に Stage61 namespace と Raid relocation を有効化する",
        ],
    }


def _linked_offsets_contract(root: Path) -> dict[str, Any]:
    raw = _require_file_hash(
        root / CFRU_LINKED_OFFSETS_RELATIVE,
        CFRU_LINKED_OFFSETS_SHA256,
        "Stage60 linked CFRU offsets",
    )
    text = raw.decode("utf-8")
    resolved: dict[str, int] = {}
    for name, expected in LINKED_SAVE_SYMBOLS.items():
        matches = re.findall(
            rf"^{re.escape(name)}:\s+([0-9A-Fa-f]{{8}})\s*$",
            text,
            re.MULTILINE,
        )
        if len(matches) != 1:
            _fail(f"linked offsets {name} row count differs: {matches}")
        value = int(matches[0], 16)
        if value != expected:
            _fail(f"linked offsets {name} differs: {value:#x} != {expected:#x}")
        resolved[name] = value
    return {
        "path": str(CFRU_LINKED_OFFSETS_RELATIVE),
        "sha256": CFRU_LINKED_OFFSETS_SHA256,
        "symbols": {
            name: {
                "address": value,
                "address_hex": _hex(value, 8),
                "thumb_entry": value | 1,
                "thumb_entry_hex": _hex(value | 1, 8),
            }
            for name, value in resolved.items()
        },
    }


def _thumb_bl_calls_by_target(
    raw: bytes, targets: Iterable[int]
) -> dict[int, list[int]]:
    wanted = set(targets)
    result = {target: [] for target in wanted}
    for offset in range(0, len(raw) - 3, 2):
        high = raw[offset] | raw[offset + 1] << 8
        low = raw[offset + 2] | raw[offset + 3] << 8
        if high & 0xF800 != 0xF000 or low & 0xF800 != 0xF800:
            continue
        displacement = (high & 0x07FF) << 12 | (low & 0x07FF) << 1
        if displacement & (1 << 22):
            displacement -= 1 << 23
        call = ROM_BASE + offset
        target = call + 4 + displacement
        if target in wanted:
            result[target].append(call)
    return result


def _read_save_section_rows(raw: bytes, address: int) -> tuple[tuple[int, int], ...]:
    blob = _rom_slice(raw, address, 14 * 4, "save section offsets")
    return tuple(struct.unpack_from("<HH", blob, index * 4) for index in range(14))


def _save_source_contract(root: Path) -> dict[str, Any]:
    raw = _require_file_hash(
        root / CFRU_SAVE_SOURCE_RELATIVE,
        CFRU_SAVE_SOURCE_SHA256,
        "CFRU save.c",
    )
    text = raw.decode("utf-8")
    required = {
        "parasite_base": "#define SAVE_BLOCK_PARASITE 0x0203B0E8",
        "parasite_size": "#define PARASITE_SIZE 0xEC4",
        "sector_size": "#define SECTOR_DATA_SIZE 0xFF0",
        "save_slots": "case 0:",
        "save_slot4": "case 4:",
        "save_slot13": "case 13:",
        "load_sector30": "DoReadFlashWholeSection(30, saveBuffer);",
        "load_sector31": "DoReadFlashWholeSection(31, saveBuffer);",
        "write_sector30": "TryWriteSector(30, saveBuffer->data);",
        "write_sector31": "TryWriteSector(31, saveBuffer->data);",
        "full_extension_clear": "Memset((void*) SAVE_BLOCK_PARASITE, 0, 0x2EA4);",
        "automatic_sector30_31_write": "SaveSector30And31();",
    }
    missing = [name for name, fragment in required.items() if fragment not in text]
    if missing:
        _fail(f"CFRU save source contract fragments missing: {missing}")
    if text.count("SaveSector30And31();") != 1:
        _fail("CFRU SaveSector30And31 call count differs")
    if text.count("LoadSector30And31();") != 1:
        _fail("CFRU LoadSector30And31 call count differs")
    return {
        "path": str(CFRU_SAVE_SOURCE_RELATIVE),
        "sha256": CFRU_SAVE_SOURCE_SHA256,
        "constants": {
            "parasite_ram": SAVE_PARASITE_RAM,
            "parasite_size": SAVE_PARASITE_SIZE,
            "sector_data_size": SAVE_SECTOR_DATA_SIZE,
            "full_extension_size": SAVE_EXTENSION_SIZE,
        },
        "slot_ids": [0, 4, 13],
        "save_write_to_flash_automatically_writes_sector30_31": True,
        "handle_load_sector_automatically_loads_sector30_31_after_valid_main_save": True,
        "new_game_clears_full_extension": True,
    }


def _parasite_owner_contract(root: Path) -> dict[str, Any]:
    fragments = (
        (0, 0x0000, 0x00CC, 0x0F24, 0x0FF0),
        (4, 0x00CC, 0x0324, 0x0D98, 0x0FF0),
        (13, 0x0324, 0x0EC4, 0x0450, 0x0FF0),
    )
    if sum(end - start for _slot, start, end, _flash, _limit in fragments) \
            != SAVE_PARASITE_SIZE:
        _fail("parasite fragment sizes do not total 0xEC4")
    regions = [
        {
            "owner": "CFRU_PARASITE_IN_MAIN_SAVE_TAILS",
            "offset_start": 0,
            "offset_end_exclusive": SAVE_PARASITE_SIZE,
            "ram_start": SAVE_PARASITE_RAM,
            "ram_end_exclusive": SAVE_SECTOR30_IMAGE,
            "physical_sectors": [0, 4, 13],
        },
        {
            "owner": "CFRU_RAW_SECTOR30_IMAGE",
            "offset_start": SAVE_PARASITE_SIZE,
            "offset_end_exclusive": SAVE_PARASITE_SIZE + SAVE_SECTOR_DATA_SIZE,
            "ram_start": SAVE_SECTOR30_IMAGE,
            "ram_end_exclusive": SAVE_SECTOR31_IMAGE,
            "physical_sectors": [30],
        },
        {
            "owner": "PROJECT_RAW_SECTOR31_IMAGE",
            "offset_start": SAVE_PARASITE_SIZE + SAVE_SECTOR_DATA_SIZE,
            "offset_end_exclusive": SAVE_EXTENSION_SIZE,
            "ram_start": SAVE_SECTOR31_IMAGE,
            "ram_end_exclusive": SAVE_EXTENSION_END_EXCLUSIVE,
            "physical_sectors": [31],
        },
    ]
    if (
        SAVE_SECTOR30_IMAGE,
        SAVE_SECTOR31_IMAGE,
        SAVE_EXTENSION_END_EXCLUSIVE,
    ) != (0x0203BFAC, 0x0203CF9C, 0x0203DF8C):
        _fail("CFRU expanded save RAM geometry differs")

    path = root / "config/save_layout.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    live: list[dict[str, Any]] = []
    occupied: list[tuple[int, int, str]] = []
    for row in rows:
        if row["address_space"] != "SAVE_PARASITE_IMAGE_OFFSET" \
                or row["status"] != "LIVE":
            continue
        start = int(row["start"], 0)
        end = int(row["end_exclusive"], 0)
        if not 0 <= start < end <= SAVE_EXTENSION_SIZE:
            _fail(f"save owner outside 0x2EA4 image: {row['symbol']}")
        for other_start, other_end, other_symbol in occupied:
            if start < other_end and other_start < end:
                _fail(
                    f"save owner overlap: {row['symbol']} and {other_symbol}"
                )
        occupied.append((start, end, row["symbol"]))
        live.append(
            {
                "symbol": row["symbol"],
                "owner": row["owner"],
                "offset_start": start,
                "offset_end_exclusive": end,
                "ram_start": SAVE_PARASITE_RAM + start,
                "ram_end_exclusive": SAVE_PARASITE_RAM + end,
            }
        )
    by_symbol = {row["symbol"]: row for row in live}
    required = {
        "expanded_flags": (0x0000, 0x0200),
        "expanded_vars": (0x0200, 0x0600),
        "magic_version_size_checksum_generation": (0x1F18, 0x1F28),
        "codex_battle_reward_owner": (0x2718, 0x2798),
        "collection_supply_owner": (0x2818, 0x2A18),
    }
    for symbol, interval in required.items():
        row = by_symbol.get(symbol)
        if row is None or (row["offset_start"], row["offset_end_exclusive"]) != interval:
            _fail(f"save owner geometry differs: {symbol}")
    return {
        "parasite_fragments": [
            {
                "main_save_sector_id": slot,
                "image_offset_start": start,
                "image_offset_end_exclusive": end,
                "size": end - start,
                "sector_data_offset_start": flash_start,
                "sector_data_offset_end_exclusive": flash_end,
            }
            for slot, start, end, flash_start, flash_end in fragments
        ],
        "regions": regions,
        "live_owner_count": len(live),
        "live_owners": live,
        "required_owner_geometry": {
            symbol: by_symbol[symbol] for symbol in required
        },
        "geometry_compatible": True,
    }


def _save_checksum(data: bytes, size: int) -> int:
    if size & 3 or size > SAVE_SECTOR_DATA_SIZE:
        _fail(f"invalid save checksum size: {size:#x}")
    total = sum(
        struct.unpack_from("<I", data, offset)[0]
        for offset in range(0, size, 4)
    ) & 0xFFFFFFFF
    return ((total >> 16) + (total & 0xFFFF)) & 0xFFFF


def _legacy_save_compatibility_contract(root: Path) -> dict[str, Any]:
    raw = _require_file_hash(
        root / STAGE60_TEST_READY_SAVE_RELATIVE,
        STAGE60_TEST_READY_SAVE_SHA256,
        "Stage60 two-generation test-ready save",
    )
    if len(raw) != 0x20000:
        _fail(f"Stage60 test-ready save size differs: {len(raw)}")
    slots: list[dict[str, Any]] = []
    mismatch_pairs: list[tuple[int, int]] = []
    for slot in range(2):
        sector_rows: list[dict[str, Any]] = []
        ids: set[int] = set()
        counters: set[int] = set()
        for physical in range(slot * 14, slot * 14 + 14):
            sector = raw[physical * 0x1000:(physical + 1) * 0x1000]
            section_id, stored = struct.unpack_from("<HH", sector, 0x0FF4)
            signature, counter = struct.unpack_from("<II", sector, 0x0FF8)
            if signature != 0x08012025 or not 0 <= section_id < 14:
                _fail(f"Stage60 save sector footer invalid: physical {physical}")
            old_size = STOCK_SAVE_SECTION_ROWS[section_id][1]
            new_size = LINKED_SAVE_SECTION_ROWS[section_id][1]
            old_checksum = _save_checksum(sector, old_size)
            new_checksum = _save_checksum(sector, new_size)
            old_valid = stored == old_checksum
            new_valid = stored == new_checksum
            if not old_valid:
                _fail(f"Stage60 save old checksum invalid: physical {physical}")
            if not new_valid:
                mismatch_pairs.append((slot, section_id))
            ids.add(section_id)
            counters.add(counter)
            sector_rows.append(
                {
                    "physical_sector": physical,
                    "section_id": section_id,
                    "stored_checksum": stored,
                    "stock_checksum": old_checksum,
                    "linked_checksum": new_checksum,
                    "stock_valid": old_valid,
                    "linked_valid": new_valid,
                }
            )
        if ids != set(range(14)) or len(counters) != 1:
            _fail(f"Stage60 save slot {slot} is not one complete generation")
        slots.append(
            {
                "slot": slot,
                "counter": next(iter(counters)),
                "stock_all_14_valid": True,
                "linked_all_14_valid": all(row["linked_valid"] for row in sector_rows),
                "linked_invalid_section_ids": sorted(
                    row["section_id"] for row in sector_rows
                    if not row["linked_valid"]
                ),
                "sectors": sector_rows,
            }
        )
    if sorted(mismatch_pairs) != [(0, 4), (0, 13), (1, 4), (1, 13)]:
        _fail(f"legacy/new table mismatch witness differs: {mismatch_pairs}")
    return {
        "path": str(STAGE60_TEST_READY_SAVE_RELATIVE),
        "sha256": STAGE60_TEST_READY_SAVE_SHA256,
        "size": len(raw),
        "slots": slots,
        "stock_layout_valid": True,
        "linked_layout_valid": False,
        "linked_invalid_section_ids_each_slot": [4, 13],
        "status": "LEGACY_SAVE_MIGRATION_REQUIRED",
        "conclusion": (
            "既存2世代saveはCFRU表のsection 4/13 checksumで両slotとも失効するため、"
            "旧表validation/loadから新表へ変換する互換loaderが必要"
        ),
    }


def _transaction_owner_contract(root: Path) -> dict[str, Any]:
    path = root / "overlays/qol_production/qol_production.c"
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    required = (
        "Transaction owners write sector 31 themselves",
        "VegaQolProduction_OriginalTrySavingData(0u)",
        "return supply_persist_sector();",
        "FN_TRY_WRITE_SECTOR(31u",
    )
    missing = [fragment for fragment in required if fragment not in text]
    if missing:
        _fail(f"sector31 transaction owner source drifted: {missing}")
    save_source = (root / CFRU_SAVE_SOURCE_RELATIVE).read_text(encoding="utf-8")
    if "SaveSector30And31();" not in save_source:
        _fail("linked SaveWriteToFlash no longer owns sector30/31")
    return {
        "source": "overlays/qol_production/qol_production.c",
        "source_sha256": _sha(raw),
        "sector31_image": SAVE_SECTOR31_IMAGE,
        "normal_save_owner": "VegaQolProduction_TrySavingDataAdapter",
        "transaction_bypass": "VegaQolProduction_OriginalTrySavingData",
        "explicit_sector31_writer": "supply_persist_sector",
        "full_upstream_save_write_compatible": False,
        "reason": (
            "linked SaveWriteToFlash(0xFFFF) also writes sector30/31; connecting it "
            "or HandleSavingData would double-write normal saves and bypass the "
            "project PREPARED/STAGED/COMMITTED transaction boundary"
        ),
        "compatible_policy": (
            "keep stock SaveWriteToFlash/HandleSavingData orchestration; hook the "
            "shared HandleWriteSector/HandleLoadSector boundaries"
        ),
    }


def _process_restart_gate_contract(root: Path) -> dict[str, Any]:
    runner_path = root / STAGE61_RUNNER_RELATIVE
    harness_path = root / STAGE61_MGBA_SOURCE_RELATIVE
    builder_path = root / STAGE61_BUILDER_RELATIVE
    runner_raw = runner_path.read_bytes()
    harness_raw = harness_path.read_bytes()
    builder_raw = builder_path.read_bytes()
    runner = runner_raw.decode("utf-8")
    harness = harness_raw.decode("utf-8")
    builder = builder_raw.decode("utf-8")
    runner_fragments = (
        '"catalog_state_persist_write"',
        '"catalog_state_persist_read"',
        "This is intentionally a second OS process",
        '"separate_writer_reader_processes": True',
        '"expanded_flag_var_same_value": True',
    )
    harness_fragments = (
        "s61_normal_input_save(core) || !s61_normal_input_save(core)",
        "s61_open_fresh(rom_path, save_path, &fixture)",
        "expanded state/canary changed across process Continue",
        "fresh_title_continue",
        "legacy_saveblock1_var_canaries",
    )
    builder_fragments = (
        "STAGE61_SAVE_COMPATIBILITY_HOOKS",
        "CFRU_SAVE_LIFECYCLE_HOOKS",
        "Stage61State_HandleWriteSector",
        "Stage61State_HandleLoadSector",
    )
    missing = {
        "runner": [value for value in runner_fragments if value not in runner],
        "harness": [value for value in harness_fragments if value not in harness],
        "builder": [value for value in builder_fragments if value not in builder],
    }
    if any(missing.values()):
        _fail(f"Stage61 process-restart gate source drifted: {missing}")
    return {
        "status": "DEFINED_FAIL_CLOSED_PENDING_RUNTIME_PASS",
        "writer_process": "catalog_state_persist_write",
        "reader_process": "catalog_state_persist_read",
        "writer_save_route": "two ordinary Start-menu saves",
        "reader_load_route": "fresh OS process -> fresh mCore -> title Continue",
        "required_state": [
            "expanded flag >= 0x1000",
            "expanded var > 0x40FF",
            "legacy vars 0x4000/0x4040/0x40FF canaries",
        ],
        "sources": {
            str(STAGE61_BUILDER_RELATIVE): _sha(builder_raw),
            str(STAGE61_RUNNER_RELATIVE): _sha(runner_raw),
            str(STAGE61_MGBA_SOURCE_RELATIVE): _sha(harness_raw),
        },
        "runtime_acceptance": (
            "report must contain separate_writer_reader_processes=true, "
            "fresh_title_continue=true, both expanded readbacks=true, warnings=0"
        ),
    }


def stage61_normal_save_cow_metadata_contract() -> dict[str, Any]:
    """通常SAVE COWについてbuilderが宣言すべきexact metadataを返す。

    source監査とbinary監査はこの宣言を根拠にしない。宣言、source、最終ROMの
    三者を独立に再計算して一致させるため、値やkeyを増減したmetadataは拒否する。
    """

    return {
        "stock_entry_address": "0x080DB230",
        "stock_entry_modified": False,
        "runtime_symbol": "Stage61State_HandleSavingData",
        "save_type": "SAVE_NORMAL_ONLY_0",
        "stock_prewrite_semantics": [
            "UpdateSaveAddresses",
            "SaveSerializedGame",
        ],
        "stock_prewrite_semantics_each_called_once": True,
        "stock_handle_saving_data_delegated": False,
        "stock_try_write_sector_used": False,
        "root_cause": (
            "STOCK_BAD_SECTOR_REPLACEMENT_CAN_ERASE_A_PHYSICAL_"
            "SECTOR_IN_THE_PROTECTED_BANK_AFTER_TARGET_FAILURE"
        ),
        "source_selection": (
            "NEWEST_COMPLETE_HALF_RANGE_U32_WITH_EXACT_ROTATION"
        ),
        "protected_bank_flash_policy": "READ_ONLY_BYTE_EXACT",
        "target_counter_expression": "source_counter + 1 (u32)",
        "target_slot_expression": "14 * ((source_counter + 1) & 1)",
        "target_first_sector_expression": (
            "(source_first_sector + 1) % 14"
        ),
        "record_bearing_logical_sector": 13,
        "target_record_preinvalidated_before_first_live_write": True,
        "preinvalidation_callback_failure_is_not_ignored": True,
        "logical_sector_order": list(range(14)),
        "record_bearing_sector_committed_last": True,
        "per_sector_commit_marker_offset": "0x0FF8",
        "per_sector_commit_marker_programmed_last": True,
        "per_sector_full_4096_byte_readback": True,
        "final_full_generation_rotation_validation": True,
        "final_all_14_sector_live_owner_byte_exact_readback": True,
        "failure_selector": (
            "PROTECTED_SOURCE_OR_ORIGINAL_PREWRITE_COUNTER_AND_ROTATION"
        ),
        "failure_damaged_bits": "TARGET_BANK_ONLY",
        "success_selector_promotion": (
            "AFTER_ALL_14_TARGET_SECTORS_AND_FINAL_READBACK"
        ),
        "first_save_without_complete_generation_supported": True,
        "save_failed_screen_wipe_retry_mgba_required": True,
        "natural_start_menu_second_retry_mgba_required": True,
        "fresh_core_continue_mgba_required": True,
    }


def _c_semantic_text(source: str) -> str:
    """comment/string/character literalを同じ長さの空白へ変換する。

    契約断片をcommentへ移しただけのsourceを合格させず、同時に元sourceとindexを
    共有してbalanced blockを切り出せるよう改行と全体長を保持する。
    """

    output = list(source)
    state = "code"
    index = 0
    while index < len(source):
        current = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if current == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if current == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if current == '"':
                output[index] = " "
                state = "string"
            elif current == "'":
                output[index] = " "
                state = "character"
            index += 1
            continue
        if state == "line_comment":
            if current == "\n":
                state = "code"
            else:
                output[index] = " "
            index += 1
            continue
        if state == "block_comment":
            if current == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "code"
                continue
            if current != "\n":
                output[index] = " "
            index += 1
            continue
        # Quoted literals support the ordinary C backslash escape.  Newlines
        # are retained solely for stable diagnostics; malformed literals remain
        # non-code until their closing delimiter and cannot satisfy a contract.
        delimiter = '"' if state == "string" else "'"
        if current == "\\" and index + 1 < len(source):
            output[index] = " "
            if source[index + 1] != "\n":
                output[index + 1] = " "
            index += 2
            continue
        if current == delimiter:
            output[index] = " "
            state = "code"
        elif current != "\n":
            output[index] = " "
        index += 1
    return "".join(output)


def _c_matching_delimiter(text: str, opening: int, left: str, right: str) -> int:
    if opening < 0 or opening >= len(text) or text[opening] != left:
        _fail(f"C delimiter start differs: {left}@{opening}")
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == left:
            depth += 1
        elif text[index] == right:
            depth -= 1
            if depth == 0:
                return index
    _fail(f"C delimiter is unterminated: {left}@{opening}")


def _c_function_body_from_semantic(
    semantic: str, name: str, *, required: bool = True,
) -> str | None:
    blocks: list[str] = []
    for match in re.finditer(rf"\b{re.escape(name)}\s*\(", semantic):
        opening_parenthesis = semantic.find("(", match.start())
        closing_parenthesis = _c_matching_delimiter(
            semantic, opening_parenthesis, "(", ")"
        )
        cursor = closing_parenthesis + 1
        while cursor < len(semantic) and semantic[cursor].isspace():
            cursor += 1
        if cursor >= len(semantic) or semantic[cursor] != "{":
            continue
        closing_brace = _c_matching_delimiter(semantic, cursor, "{", "}")
        blocks.append(semantic[cursor:closing_brace + 1])
    if not blocks and not required:
        return None
    if len(blocks) != 1:
        _fail(f"C function definition count differs: {name}={len(blocks)}")
    return blocks[0]


def _c_function_body(source: str, name: str) -> str:
    """commentを除いたC sourceから唯一の関数定義bodyを抽出する。"""

    result = _c_function_body_from_semantic(
        _c_semantic_text(source), name, required=True
    )
    assert result is not None
    return result


def _c_reachable_local_functions(
    semantic: str, root_name: str,
) -> dict[str, str]:
    """rootから直接/間接に呼ぶ同一translation unit関数を閉包化する。"""

    pending = [root_name]
    reachable: dict[str, str] = {}
    keywords = {"if", "for", "while", "switch", "sizeof", "return"}
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        body = _c_function_body_from_semantic(
            semantic, name, required=(name == root_name)
        )
        if body is None:
            continue
        reachable[name] = body
        for called in re.findall(r"\b([A-Za-z_]\w*)\s*\(", body):
            if called not in keywords and called not in reachable:
                candidate = _c_function_body_from_semantic(
                    semantic, called, required=False
                )
                if candidate is not None:
                    pending.append(called)
    return reachable


def _c_if_block(function_body: str, condition: str) -> str:
    """関数bodyから指定した単純conditionの唯一のif blockを抽出する。"""

    matches = list(re.finditer(condition, function_body))
    if len(matches) != 1:
        _fail(f"C if condition count differs: {condition}={len(matches)}")
    opening_parenthesis = function_body.rfind("(", 0, matches[0].end())
    if opening_parenthesis < 0:
        _fail(f"C if opening parenthesis missing: {condition}")
    closing_parenthesis = _c_matching_delimiter(
        function_body, opening_parenthesis, "(", ")"
    )
    cursor = closing_parenthesis + 1
    while cursor < len(function_body) and function_body[cursor].isspace():
        cursor += 1
    if cursor >= len(function_body) or function_body[cursor] != "{":
        _fail(f"C if block missing: {condition}")
    closing_brace = _c_matching_delimiter(function_body, cursor, "{", "}")
    return function_body[cursor:closing_brace + 1]


def _c_call_count(body: str, name: str) -> int:
    return len(re.findall(rf"\b{re.escape(name)}\s*\(", body))


def _require_ordered_fragments(
    body: str, fragments: Sequence[str], label: str,
) -> list[int]:
    positions: list[int] = []
    cursor = 0
    for fragment in fragments:
        position = body.find(fragment, cursor)
        if position < 0:
            _fail(f"{label} ordered fragment missing: {fragment}")
        positions.append(position)
        cursor = position + len(fragment)
    return positions


def validate_stage61_normal_save_cow_source(source: str) -> dict[str, Any]:
    """通常SAVE COWの意味契約をartifact SHAと独立にsourceから検証する。"""

    semantic = _c_semantic_text(source)
    if len(re.findall(
        r"\bSTAGE61_SAVE_TYPE_NORMAL\s*=\s*0u\b", semantic
    )) != 1:
        _fail("Stage61 SAVE_NORMAL numeric ABI differs")

    required_function_names = (
        "Stage61State_HandleSavingData",
        "stage61_save_normal_copy_on_write",
        "stage61_save_choose_protected_generation",
        "stage61_save_invalidate_normal_target_record",
        "stage61_save_write_normal_live_sector",
        "stage61_save_readback_matches_prepared",
    )
    function_bodies = {
        name: _c_function_body_from_semantic(semantic, name, required=True)
        for name in required_function_names
    }
    if any(value is None for value in function_bodies.values()):
        _fail("Stage61 SAVE_NORMAL required function body missing")
    wrapper = function_bodies["Stage61State_HandleSavingData"]
    transaction = function_bodies["stage61_save_normal_copy_on_write"]
    selector = function_bodies["stage61_save_choose_protected_generation"]
    invalidator = function_bodies[
        "stage61_save_invalidate_normal_target_record"
    ]
    writer = function_bodies["stage61_save_write_normal_live_sector"]
    readback = function_bodies["stage61_save_readback_matches_prepared"]
    assert all(isinstance(value, str) for value in (
        wrapper, transaction, selector, invalidator, writer, readback,
    ))
    normal_block = _c_if_block(
        wrapper,
        r"if\s*\(\s*save_type\s*==\s*STAGE61_SAVE_TYPE_NORMAL\s*\)",
    )

    if _c_call_count(normal_block, "stage61_save_normal_copy_on_write") != 1 \
            or _c_call_count(wrapper, "stage61_save_normal_copy_on_write") != 1:
        _fail("Stage61 SAVE_NORMAL wrapper transaction dispatch differs")
    normal_forbidden = (
        "FN_STOCK_HANDLE_SAVING_DATA",
        "FN_TRY_WRITE_SECTOR",
        "Stage61State_HandleWriteSector",
        "Stage61State_HandleReplaceSector",
    )
    if any(value in normal_block for value in normal_forbidden):
        _fail("Stage61 SAVE_NORMAL wrapper reaches a stock/destructive writer")
    if _c_call_count(wrapper, "FN_STOCK_HANDLE_SAVING_DATA") != 1 \
            or wrapper.find("stage61_save_normal_copy_on_write") > \
            wrapper.find("FN_STOCK_HANDLE_SAVING_DATA"):
        _fail("Stage61 SAVE_LINK stock path was removed or precedes normal dispatch")
    _require_ordered_fragments(
        normal_block,
        (
            "G_MAIN_VBLANK_COUNTER1 = (volatile u32 *)0;",
            "result = stage61_save_normal_copy_on_write();",
            "G_MAIN_VBLANK_COUNTER1 = backup_counter;",
            "return result == STAGE61_SAVE_STATUS_OK",
        ),
        "Stage61 SAVE_NORMAL wrapper",
    )

    if _c_call_count(transaction, "FN_UPDATE_SAVE_ADDRESSES") != 1 \
            or _c_call_count(transaction, "FN_SAVE_SERIALIZED_GAME") != 1:
        _fail("Stage61 SAVE_NORMAL stock pre-write call count differs")
    update_position = transaction.find("FN_UPDATE_SAVE_ADDRESSES();")
    serialized_position = transaction.find("FN_SAVE_SERIALIZED_GAME();")
    choose_position = transaction.find(
        "stage61_save_choose_protected_generation("
    )
    if not 0 <= update_position < serialized_position < choose_position:
        _fail("Stage61 SAVE_NORMAL pre-write call order differs")
    if any(value in transaction for value in normal_forbidden):
        _fail("Stage61 SAVE_NORMAL transaction reaches a stock writer")
    reachable = _c_reachable_local_functions(
        semantic, "stage61_save_normal_copy_on_write"
    )
    unsafe_reachable = {
        name: forbidden
        for name, body in reachable.items()
        for forbidden in normal_forbidden
        if forbidden in body
    }
    if unsafe_reachable:
        _fail(
            "Stage61 SAVE_NORMAL transitive stock writer reachable: "
            f"{unsafe_reachable}"
        )

    transaction_compact = re.sub(r"\s+", " ", transaction)
    required_geometry = (
        "u16 original_first_sector;",
        "u16 rollback_first_sector;",
        "u16 source_first_sector;",
        "u32 original_counter;",
        "u32 rollback_counter;",
        "original_counter = G_SAVE_COUNTER;",
        "original_first_sector = G_FIRST_SAVE_SECTOR;",
        "source_counter = protected.counter;",
        "source_first_sector = protected.first_save_sector;",
        "rollback_counter = protected.counter;",
        "rollback_first_sector = protected.first_save_sector;",
        "source_counter = original_counter;",
        "original_first_sector % STAGE61_SAVE_SLOT_SECTORS",
        "rollback_counter = original_counter;",
        "rollback_first_sector = original_first_sector;",
        "target_counter = source_counter + 1u;",
        "STAGE61_SAVE_SLOT_SECTORS * (target_counter & 1u)",
        "(source_first_sector + 1u) % STAGE61_SAVE_SLOT_SECTORS",
        "(target_first_sector + 13u) % STAGE61_SAVE_SLOT_SECTORS",
        "has_protected != 0u && target_base == protected_base",
        "u8 physical = (u8)(target_base + written.physical_by_id[id]);",
        "section, id, size, live_chunks[id].data, target_counter, record_crc,",
    )
    missing_geometry = [
        value for value in required_geometry if value not in transaction_compact
    ]
    if missing_geometry:
        _fail(f"Stage61 SAVE_NORMAL target/selector geometry differs: {missing_geometry}")
    if re.search(
        r"(?:erase_sector|program_byte|stage61_save_(?:mark|clear)_damaged|"
        r"stage61_save_(?:reject_written_target_sector|"
        r"write_normal_live_sector|invalidate_normal_target_record))"
        r"\s*\([^;]*protected",
        transaction,
    ):
        _fail("Stage61 SAVE_NORMAL mutates the protected generation")

    if _c_call_count(
        transaction, "stage61_save_choose_protected_generation"
    ) != 1 or _c_call_count(
        transaction, "stage61_save_invalidate_normal_target_record"
    ) != 1 or _c_call_count(
        transaction, "stage61_save_write_normal_live_sector"
    ) != 1 or _c_call_count(
        transaction, "stage61_save_validate_slot"
    ) != 1 or _c_call_count(
        transaction, "stage61_save_readback_matches_prepared"
    ) != 1:
        _fail("Stage61 SAVE_NORMAL phase call cardinality differs")
    loop_pattern = (
        r"for\s*\(\s*id\s*=\s*0u\s*;\s*id\s*<\s*"
        r"STAGE61_SAVE_SLOT_SECTORS\s*;\s*\+\+id\s*\)"
    )
    loops = list(re.finditer(loop_pattern, transaction))
    if len(loops) != 2:
        _fail(f"Stage61 SAVE_NORMAL fourteen-sector loop count differs: {len(loops)}")
    invalidation_position = transaction.find(
        "stage61_save_invalidate_normal_target_record("
    )
    writer_position = transaction.find("stage61_save_write_normal_live_sector(")
    validation_position = transaction.find("stage61_save_validate_slot(")
    final_readback_position = transaction.find(
        "stage61_save_readback_matches_prepared("
    )
    if not (
        0 <= invalidation_position < loops[0].start() < writer_position
        < validation_position < loops[1].start() < final_readback_position
    ):
        _fail("Stage61 SAVE_NORMAL preinvalidate/write/final-readback order differs")

    post_write = transaction[writer_position:]
    rollback_pattern = (
        r"stage61_save_reject_written_target_sector\s*\([^;]+\)\s*;\s*"
        r"G_SAVE_COUNTER\s*=\s*rollback_counter\s*;\s*"
        r"G_FIRST_SAVE_SECTOR\s*=\s*rollback_first_sector\s*;\s*"
        r"return\s+STAGE61_SAVE_STATUS_ERROR\s*;"
    )
    if (
        post_write.count("G_SAVE_COUNTER = rollback_counter;") != 4
        or post_write.count("G_FIRST_SAVE_SECTOR = rollback_first_sector;") != 4
        or post_write.count("return STAGE61_SAVE_STATUS_ERROR;") != 4
        or _c_call_count(
            post_write, "stage61_save_reject_written_target_sector"
        ) != 4
        or re.search(r"if\s*\(\s*has_protected\b", post_write) is not None
        or len(re.findall(rollback_pattern, post_write)) != 4
    ):
        _fail("Stage61 SAVE_NORMAL failure rollback/damaged-sector contract differs")
    success_tail = re.sub(r"\s+", " ", transaction).strip()
    if not success_tail.endswith(
        "G_SAVE_COUNTER = target_counter; "
        "G_FIRST_SAVE_SECTOR = target_first_sector; "
        "return STAGE61_SAVE_STATUS_OK; }"
    ) or transaction.rfind("G_SAVE_COUNTER = target_counter;") < \
            final_readback_position:
        _fail("Stage61 SAVE_NORMAL success selector promotion differs")

    selector_forbidden = (
        "G_ERASE_FLASH_SECTOR",
        "G_PROGRAM_FLASH_BYTE",
        "stage61_save_mark_damaged(",
        "stage61_save_clear_damaged(",
        "stage61_save_reject_written_target_sector(",
        "G_SAVE_COUNTER =",
        "G_FIRST_SAVE_SECTOR =",
    )
    if any(value in selector for value in selector_forbidden) \
            or _c_call_count(selector, "stage61_save_validate_slot") != 3:
        _fail("Stage61 protected-generation selector is not read-only")
    selector_compact = re.sub(r"\s+", " ", selector)
    selector_fragments = (
        "*selected_base = 0xFFu;",
        "first.status == STAGE61_SAVE_STATUS_OK",
        "second.status == STAGE61_SAVE_STATUS_OK",
        "stage61_save_second_counter_is_newer( first.counter, second.counter)",
        "? STAGE61_SAVE_SLOT_SECTORS : 0u;",
        "else if (first.status == STAGE61_SAVE_STATUS_OK)",
        "else if (second.status == STAGE61_SAVE_STATUS_OK)",
        "stage61_save_validate_slot(*selected_base, chunks, selected);",
        "selected->valid_mask == STAGE61_SAVE_FULL_MASK",
    )
    if any(value not in selector_compact for value in selector_fragments) \
            or _c_call_count(
                selector, "stage61_save_second_counter_is_newer"
            ) != 1:
        _fail("Stage61 protected-generation newest selection differs")

    invalidator_order = _require_ordered_fragments(
        invalidator,
        (
            "stage61_save_mark_damaged(target_sector);",
            "erase_status = erase_sector(target_sector);",
            "(void)FN_READ_FLASH_SECTION(target_sector, (void *)section);",
        ),
        "Stage61 SAVE_NORMAL target invalidation",
    )
    if invalidator_order != sorted(invalidator_order) \
            or "stage61_save_clear_damaged(" in invalidator:
        _fail("Stage61 SAVE_NORMAL target id13 invalidation differs")

    if _c_call_count(writer, "FN_TRY_WRITE_SECTOR") != 0 \
            or _c_call_count(writer, "erase_sector") != 1 \
            or _c_call_count(writer, "program_byte") != 3 \
            or _c_call_count(writer, "FN_READ_FLASH_SECTION") != 1 \
            or _c_call_count(
                writer, "stage61_save_readback_matches_prepared"
            ) != 1 \
            or _c_call_count(writer, "stage61_save_clear_damaged") != 1:
        _fail("Stage61 SAVE_NORMAL per-sector writer call graph differs")
    writer_compact = re.sub(r"\s+", " ", writer)
    if (
        "section, id, size, data, target_counter, record_crc, "
        "(u8)STAGE61_SAVE_SIGNATURE" not in writer_compact
    ):
        _fail("Stage61 SAVE_NORMAL per-sector live-owner readback differs")
    writer_positions = _require_ordered_fragments(
        writer,
        (
            "stage61_save_mark_damaged(target_sector);",
            "erase_sector(target_sector)",
            "index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index",
            "index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;",
            "STAGE61_SAVE_SIGNATURE_OFFSET,",
            "(void)FN_READ_FLASH_SECTION(target_sector, (void *)section);",
            "stage61_save_readback_matches_prepared(",
            "stage61_save_clear_damaged(target_sector);",
        ),
        "Stage61 SAVE_NORMAL per-sector signature/readback",
    )
    if writer_positions != sorted(writer_positions):
        _fail("Stage61 SAVE_NORMAL per-sector commit order differs")

    if len(re.findall(
        r"for\s*\(\s*index\s*=\s*0u\s*;\s*index\s*<\s*"
        r"STAGE61_SAVE_SECTION_SIZE\s*;\s*\+\+index\s*\)",
        readback,
    )) != 1 or "section[index] != stage61_save_expected_prepared_byte(" \
            not in readback:
        _fail("Stage61 SAVE_NORMAL full 4096-byte readback differs")

    assertions = {
        "stock_prewrite_once_and_ordered": True,
        "stock_destructive_writers_unreachable": True,
        "protected_generation_read_only": True,
        "opposite_target_counter_and_rotation_exact": True,
        "target_id13_preinvalidated_and_committed_last": True,
        "all_14_sectors_have_two_full_byte_readbacks": True,
        "failure_selector_and_damaged_state_rollback_exact": True,
        "success_selector_promoted_after_final_readback": True,
        "save_link_stock_path_retained": True,
    }
    return {
        "status": "SOURCE_CONTROL_FLOW_EXACT",
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "normal_wrapper_dispatch_count": 1,
        "stock_handle_call_count_outside_normal_dispatch": 1,
        "prewrite_calls": ["UpdateSaveAddresses", "SaveSerializedGame"],
        "logical_sector_write_order": list(range(14)),
        "per_sector_full_readback_bytes": 0x1000,
        "post_generation_full_readback_count": 14,
        "post_write_failure_rollback_count": 4,
        "assertions": assertions,
    }


def _thumb_bl_calls_in_range(
    raw: bytes, start: int, end_exclusive: int,
) -> list[dict[str, int]]:
    if start & 1 or end_exclusive < start:
        _fail("Thumb function range differs")
    result: list[dict[str, int]] = []
    for address in range(start, end_exclusive - 3, 2):
        blob = _rom_slice(raw, address, 4, "Thumb function BL scan")
        high, low = struct.unpack("<HH", blob)
        if high & 0xF800 != 0xF000 or low & 0xF800 != 0xF800:
            continue
        result.append({
            "site": address,
            "target": _thumb_bl_target(address, blob),
        })
    return result


def _stage61_normal_save_cow_object_contract(
    rom: bytes,
    symbols: Mapping[str, Any],
    code_address: int,
    code_size: int,
) -> dict[str, Any]:
    """最終runtime objectの通常SAVE dispatchと危険literal不在を監査する。"""

    required = {
        "Stage61State_HandleSavingData",
        "stage61_save_normal_copy_on_write",
    }
    if not required <= set(symbols):
        _fail(f"Stage61 normal SAVE object symbols missing: {required - set(symbols)}")
    code_end = code_address + code_size
    executable_addresses = sorted({
        int(value) for value in symbols.values()
        if code_address <= int(value) < code_end
    })

    def body(name: str) -> tuple[int, int, bytes]:
        start = int(symbols[name])
        later = [value for value in executable_addresses if value > start]
        end = later[0] if later else code_end
        if not code_address <= start < end <= code_end:
            _fail(f"Stage61 normal SAVE object body range differs: {name}")
        return start, end, _rom_slice(rom, start, end - start, name)

    wrapper_start, wrapper_end, wrapper_body = body(
        "Stage61State_HandleSavingData"
    )
    normal_start, normal_end, normal_body = body(
        "stage61_save_normal_copy_on_write"
    )
    wrapper_calls = _thumb_bl_calls_in_range(rom, wrapper_start, wrapper_end)
    normal_calls = _thumb_bl_calls_in_range(rom, normal_start, normal_end)
    dispatch_sites = [
        row["site"] for row in wrapper_calls if row["target"] == normal_start
    ]
    if len(dispatch_sites) != 1:
        _fail(f"Stage61 normal SAVE object dispatch differs: {dispatch_sites}")

    try_write_literal = struct.pack("<I", 0x080DA9C1)
    stock_handle_literal = struct.pack("<I", 0x080DB231)
    update_literal = struct.pack("<I", 0x080DB1BD)
    serialized_literal = struct.pack("<I", 0x0804BAB9)
    if normal_body.count(update_literal) != 1 \
            or normal_body.count(serialized_literal) != 1:
        _fail("Stage61 normal SAVE object pre-write literal cardinality differs")
    if wrapper_body.count(stock_handle_literal) != 1:
        _fail("Stage61 SAVE_LINK stock object path differs")
    forbidden_direct_targets = {0x080DA9C0, 0x080DB230} | {
        int(symbols[name]) for name in (
            "Stage61State_HandleWriteSector",
            "Stage61State_HandleReplaceSector",
        ) if name in symbols
    }
    names_by_address: dict[int, list[str]] = {}
    for name, value in symbols.items():
        address = int(value)
        if code_address <= address < code_end:
            names_by_address.setdefault(address, []).append(str(name))
    pending = [normal_start]
    reachable_addresses: set[int] = set()
    reachable_bodies: dict[int, bytes] = {}
    reachable_calls: list[dict[str, int]] = []
    while pending:
        start = pending.pop()
        if start in reachable_addresses:
            continue
        later = [value for value in executable_addresses if value > start]
        end = later[0] if later else code_end
        current_body = _rom_slice(
            rom, start, end - start, "Stage61 normal SAVE object closure"
        )
        calls = _thumb_bl_calls_in_range(rom, start, end)
        reachable_addresses.add(start)
        reachable_bodies[start] = current_body
        reachable_calls.extend(calls)
        for call in calls:
            if call["target"] in names_by_address \
                    and call["target"] not in reachable_addresses:
                pending.append(call["target"])
    unsafe_literals = {
        start: {
            "TryWriteSector": current.count(try_write_literal),
            "HandleSavingData": current.count(stock_handle_literal),
        }
        for start, current in reachable_bodies.items()
        if try_write_literal in current or stock_handle_literal in current
    }
    unsafe_calls = [
        row for row in reachable_calls
        if row["target"] in forbidden_direct_targets
    ]
    if unsafe_literals or unsafe_calls:
        _fail(
            "Stage61 normal SAVE object transitively reaches an unsafe writer: "
            f"literals={unsafe_literals}, calls={unsafe_calls}"
        )
    reachable_symbols = sorted({
        name
        for address in reachable_addresses
        for name in names_by_address.get(address, [])
    })
    return {
        "status": "OBJECT_DISPATCH_AND_LITERAL_CLOSURE_EXACT",
        "wrapper_symbol": {
            "address": wrapper_start,
            "address_hex": _hex(wrapper_start, 8),
            "end_exclusive": wrapper_end,
            "body_sha256": _sha(wrapper_body),
        },
        "transaction_symbol": {
            "address": normal_start,
            "address_hex": _hex(normal_start, 8),
            "end_exclusive": normal_end,
            "body_sha256": _sha(normal_body),
        },
        "normal_dispatch_sites": dispatch_sites,
        "normal_dispatch_sites_hex": [_hex(value, 8) for value in dispatch_sites],
        "normal_direct_call_count": len(normal_calls),
        "transitive_local_symbol_count": len(reachable_addresses),
        "transitive_local_symbols": reachable_symbols,
        "transitive_direct_call_count": len(reachable_calls),
        "stock_try_write_literal_count": 0,
        "stock_handle_literal_count": 0,
        "update_save_addresses_literal_count": 1,
        "save_serialized_game_literal_count": 1,
    }


def _validate_stage61_normal_save_cow_metadata(
    declared: Any,
) -> dict[str, Any]:
    expected = stage61_normal_save_cow_metadata_contract()
    if declared != expected:
        _fail("Stage61 generated normal SAVE COW metadata differs")
    return {
        "status": "METADATA_EXACT",
        "contract": expected,
        "contract_sha256": _sha(
            json.dumps(
                expected, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ),
    }


def _stage61_custom_save_compatibility_contract(root: Path) -> dict[str, Any]:
    """旧save/tableを維持するStage61 custom recordをexact ROMまで監査する。"""

    metadata = json.loads((root / STAGE61_METADATA_RELATIVE).read_text(encoding="utf-8"))
    generated = json.loads((root / STAGE61_AUDIT_RELATIVE).read_text(encoding="utf-8"))
    rom = (root / STAGE61_ROM_RELATIVE).read_bytes()
    if (
        metadata.get("schema_version"),
        metadata.get("stage"),
        metadata.get("status"),
        metadata.get("input", {}).get("sha256"),
        metadata.get("output", {}).get("path"),
        metadata.get("output", {}).get("size"),
    ) != (
        1,
        61,
        "PASS",
        STAGE60_ROM_SHA256,
        str(STAGE61_ROM_RELATIVE),
        ROM_SIZE,
    ):
        _fail("Stage61 metadata identity differs for custom save audit")
    if len(rom) != ROM_SIZE or _sha(rom) != metadata["output"]["sha256"]:
        _fail("Stage61 custom save ROM differs from metadata")
    metadata_runtime = metadata.get("runtime", {})
    report_runtime = generated.get("runtime", {})
    symbols = metadata_runtime.get("symbols", {})
    required_symbols = {
        "Stage61State_HandleWriteSector",
        "Stage61State_HandleReplaceSector",
        "Stage61State_EnsureBackupGeneration",
        "Stage61State_UpdateRecordOnly",
        "Stage61State_HandleSavingData",
        "Stage61State_GetSaveValidStatus",
        "Stage61State_HandleLoadSector",
        "stage61_save_normal_copy_on_write",
    }
    if not required_symbols <= set(symbols):
        _fail(f"Stage61 custom save symbols missing: {required_symbols - set(symbols)}")
    report_symbols = report_runtime.get("symbols", {})
    for name in required_symbols:
        if report_symbols.get(name) != symbols[name]:
            _fail(f"Stage61 metadata/report symbol mismatch: {name}")

    source_path = root / STAGE61_RUNTIME_SOURCE_RELATIVE
    source_raw = source_path.read_bytes()
    source = source_raw.decode("utf-8")
    source_sha256 = _sha(source_raw)
    if (
        metadata_runtime.get("source") != str(STAGE61_RUNTIME_SOURCE_RELATIVE)
        or metadata_runtime.get("source_sha256") != source_sha256
        or report_runtime.get("source") != str(STAGE61_RUNTIME_SOURCE_RELATIVE)
        or report_runtime.get("source_sha256") != source_sha256
    ):
        _fail("Stage61 runtime source path/SHA differs from built artifacts")
    normal_save_source_contract = validate_stage61_normal_save_cow_source(
        source
    )

    payload = metadata.get("payload", {})
    code_address = int(payload.get("code_address", 0))
    code_size = int(payload.get("code_size", 0))
    if (
        code_size <= 0
        or code_address < ROM_BASE
        or code_address + code_size > ROM_BASE + len(rom)
        or int(report_runtime.get("code_size", 0)) != code_size
    ):
        _fail("Stage61 runtime code range differs")
    code_raw = _rom_slice(rom, code_address, code_size, "Stage61 runtime code")
    code_sha256 = _sha(code_raw)
    if (
        metadata_runtime.get("code_sha256") != code_sha256
        or report_runtime.get("code_sha256") != code_sha256
    ):
        _fail("Stage61 runtime code SHA differs from ROM")
    normal_save_object_contract = _stage61_normal_save_cow_object_contract(
        rom, symbols, code_address, code_size
    )
    source_fragments = (
        "STAGE61_STATE_MAGIC = 0x45313653u",
        "STAGE61_STATE_VERSION = 1u",
        "STAGE61_STATE_HEADER_SIZE = 16u",
        "STAGE61_STATE_FLAGS_SIZE = 0x200u",
        "STAGE61_STATE_VARS_SIZE = 0x400u",
        "STAGE61_STATE_LAST_BALL_SIZE = 2u",
        "STAGE61_STATE_COINS_SIZE = 4u",
        "STAGE61_STATE_PAYLOAD_SIZE = 0x606u",
        "STAGE61_STATE_RECORD_SIZE = 0x616u",
        "G_LAST_USED_BALL_BYTES[index]",
        "id == 13u && size == 0x7D0u",
        "*record_start = 0u;",
        "*length = STAGE61_STATE_RECORD_SIZE;",
        "0xEDB88320u",
        "stage61_save_build_live_descriptors(",
        "stage61_save_ensure_live_backup_generation(void)",
        "stage61_state_tail_matches_live_crc(",
        "stage61_save_section_crc32(",
        "stage61_save_rewrite_source_record_sector(",
        "stage61_save_invalidate_target_record_sector(",
        "result = FN_STOCK_HANDLE_SAVING_DATA(save_type);",
        "(void)argument;",
        "stage61_save_select_generation(chunks, &physical_base)",
        "if (mask != 1u",
        "stage61_state_crc() != stage61_read32(header + 8u)",
        "STAGE61_EXPORT(Stage61State_EnsureBackupGeneration)",
        "STAGE61_EXPORT(Stage61State_UpdateRecordOnly)",
        "STAGE61_EXPORT(Stage61State_HandleSavingData)",
        "STAGE61_EXPORT(Stage61State_GetSaveValidStatus)",
        "STAGE61_EXPORT(Stage61State_HandleLoadSector)",
        "STAGE61_EXPORT(Stage61State_HandleReplaceSector)",
        "if (erase_sector(sector) != 0u)",
        "if (erase_sector(target_sector) != 0u)",
        "index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index",
        "index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;",
        "u32 delta = second - first;",
        "return (u8)(delta != 0u && delta < 0x80000000u);",
    )
    missing = [fragment for fragment in source_fragments if fragment not in source]
    if missing:
        _fail(f"Stage61 custom save runtime contract drifted: {missing}")
    slot_validator = source[
        source.index("static void stage61_save_validate_slot("):
        source.index("static u8 stage61_save_validations_match(")
    ]
    rotation_fragments = (
        "result->physical_by_id[index]",
        "(result->first_save_sector + index)",
        "% STAGE61_SAVE_SLOT_SECTORS",
        "malformed = 1u;",
    )
    if any(fragment not in slot_validator for fragment in rotation_fragments) \
            or slot_validator.index("result->physical_by_id[index]") > \
            slot_validator.rindex("result->status = STAGE61_SAVE_STATUS_OK"):
        _fail("Stage61 save slot physical rotation validation differs")
    if source.count("G_LAST_USED_BALL_BYTES[index]") != 4:
        _fail(
            "Stage61 last-used-ball serializer path count differs: "
            f"{source.count('G_LAST_USED_BALL_BYTES[index]')} != 4"
        )
    record_update = source[
        source.index("u8 Stage61State_UpdateRecordOnly("):
        source.index("static __attribute__((noinline))\n"
                     "u8 stage61_save_update_live_record_only(void)")
    ]
    ordered_post_steps = (
        "stage61_save_rewrite_source_record_sector(",
        "stage61_save_validate_slot(source_base, chunks, &committed_source)",
        "stage61_save_invalidate_target_record_sector(",
        "stage61_save_clone_complete_generation(",
        "G_SAVE_COUNTER = target_counter",
    )
    positions = [record_update.index(fragment) for fragment in ordered_post_steps]
    if positions != sorted(positions) \
            or "stage61_save_select_generation" in record_update \
            or "target_counter, 0u" not in record_update:
        _fail("Stage61 SAVE_LINK atomic source/target order differs")
    invalidation_failure = record_update[
        record_update.index("stage61_save_invalidate_target_record_sector("):
        record_update.index("stage61_save_clone_complete_generation(")
    ]
    if "stage61_save_mark_damaged(" not in invalidation_failure \
            or "target_base + committed_source.physical_by_id[13]" \
                not in invalidation_failure:
        _fail("Stage61 SAVE_LINK target invalidation early failure mark differs")
    save_wrapper = source[
        source.index("u8 Stage61State_HandleSavingData("):
        source.index("STAGE61_EXPORT(Stage61State_GetSaveValidStatus)")
    ]
    post_wrapper = save_wrapper[
        save_wrapper.index("stage61_save_update_live_record_only()"):
    ]
    if "stage61_save_fail_with_sector" in post_wrapper \
            or "return STAGE61_SAVE_STATUS_ERROR;" not in post_wrapper:
        _fail("Stage61 SAVE_LINK post failure damaged-bank ownership differs")

    # Source identity alone does not demonstrate that the current source was
    # compiled into this ROM.  Pin the generated code hash above and also
    # require the four persistent payload roots to occur in the exact emitted
    # runtime.  This rejects the earlier stale 0x614 binary, which had no
    # gLastUsedBall literal despite the source already declaring it.
    persistent_literals = {
        "gExpandedFlags": 0x0203B0E8,
        "gExpandedVars": 0x0203B2E8,
        "gLastUsedBall": 0x0203B6EC,
        "gPlayerCoins": 0x0203B78C,
    }
    literal_evidence: dict[str, dict[str, Any]] = {}
    for owner, value in persistent_literals.items():
        needle = struct.pack("<I", value)
        offsets = [
            index for index in range(0, len(code_raw) - 3)
            if code_raw[index:index + 4] == needle
        ]
        if not offsets:
            _fail(f"Stage61 compiled runtime lacks persistent literal: {owner}")
        literal_evidence[owner] = {
            "value": value,
            "value_hex": _hex(value, 8),
            "count": len(offsets),
            "rom_addresses": [code_address + offset for offset in offsets],
            "rom_addresses_hex": [
                _hex(code_address + offset, 8) for offset in offsets
            ],
        }

    declarations = generated.get("change_audit", {}).get("declarations", [])
    by_name = {str(row.get("name")): row for row in declarations}
    patch_names = (
        "stage61_save_compatibility::handle_write_sector",
        "stage61_save_compatibility::handle_replace_sector",
        "stage61_save_compatibility::get_save_valid_status",
        "stage61_save_compatibility::handle_load_sector",
        "stage61_save_link_record_near_veneer",
        "stage61_save_link_record_caller::0x080db35c",
        "stage61_save_link_record_caller::0x080f64c4",
        "cfru_save_lifecycle::link_battle_full_save",
        "cfru_save_lifecycle::link_trade_full_save",
        "cfru_save_lifecycle::new_game_expanded_save_clear",
        "expanded_var_pointer_global_hook",
        "expanded_flag_pointer_global_hook",
    )
    if any(name not in by_name for name in patch_names):
        _fail(f"Stage61 custom save declarations missing: {set(patch_names) - set(by_name)}")
    active_patches: list[dict[str, Any]] = []
    for name in patch_names:
        declaration = by_name[name]
        address = ROM_BASE + int(declaration["start"])
        expected = str(declaration["expected_hex"])
        replacement = str(declaration["replacement_hex"])
        _require_rom_bytes(rom, address, bytes.fromhex(replacement), name)
        active_patches.append(
            {
                "name": name,
                "address": address,
                "address_hex": _hex(address, 8),
                "expected_hex": expected,
                "replacement_hex": replacement,
                "category": declaration["category"],
            }
        )
    custom_specs = (
        (
            "stage61_save_compatibility::handle_write_sector",
            0x080DA858,
            "Stage61State_HandleWriteSector",
            2,
        ),
        (
            "stage61_save_compatibility::handle_replace_sector",
            0x080DAB38,
            "Stage61State_HandleReplaceSector",
            2,
        ),
        (
            "stage61_save_compatibility::get_save_valid_status",
            0x080DAEF4,
            "Stage61State_GetSaveValidStatus",
            1,
        ),
        (
            "stage61_save_compatibility::handle_load_sector",
            0x080DAE3C,
            "Stage61State_HandleLoadSector",
            2,
        ),
    )
    for name, address, symbol, register in custom_specs:
        target = int(symbols[symbol])
        replacement = _register_jump_stub(address, target, register)
        row = next(item for item in active_patches if item["name"] == name)
        if row["address"] != address or row["replacement_hex"] != replacement.hex():
            _fail(f"Stage61 custom hook target/stub differs: {name}")

    saving_symbol = int(symbols["Stage61State_HandleSavingData"])
    veneer_row = next(
        item for item in active_patches
        if item["name"] == "stage61_save_link_record_near_veneer"
    )
    expected_veneer = (
        bytes.fromhex("004b1847")
        + struct.pack("<I", saving_symbol | 1)
    )
    if veneer_row["address"] != 0x080C6480 \
            or veneer_row["replacement_hex"] != expected_veneer.hex():
        _fail("Stage61 SAVE_LINK near veneer target/ABI differs")
    caller_contract = {
        "stage61_save_link_record_caller::0x080db35c": (
            0x080DB35C, "fff768ff",
        ),
        "stage61_save_link_record_caller::0x080f64c4": (
            0x080F64C4, "e4f7b4fe",
        ),
    }
    for name, (address, preimage) in caller_contract.items():
        row = next(item for item in active_patches if item["name"] == name)
        if row["address"] != address or row["expected_hex"] != preimage:
            _fail(f"Stage61 SAVE_LINK direct caller preimage differs: {name}")
        replacement = bytes.fromhex(row["replacement_hex"])
        if len(replacement) != 4 \
                or _thumb_bl_target(address, replacement) != 0x080C6480:
            _fail(f"Stage61 SAVE_LINK direct caller target differs: {name}")

    # The compatibility design deliberately retains all stock chunk sizes and
    # orchestration entries other than the two boundary wrappers.
    _require_rom_bytes(
        rom,
        SAVE_SECTION_OFFSETS_POINTER_SITE,
        struct.pack("<I", STOCK_SAVE_SECTION_OFFSETS),
        "Stage61 stock gSaveSectionOffsets pointer",
    )
    untouched = {
        "SaveWriteToFlash": SAVE_CORE_HOOKS[0],
        "TryLoadSaveSector": SAVE_CORE_HOOKS[4],
        "HandleSavingData": SAVE_CORE_HOOKS[5],
    }
    for name, row in untouched.items():
        _require_rom_bytes(
            rom, int(row["address"]), bytes(row["expected"]), f"Stage61 stock {name}"
        )

    segments = (
        {
            "section_id": 13,
            "chunk_size": 0x7D0,
            "record_start": 0,
            "length": 0x616,
        },
    )
    for row in segments:
        if row["chunk_size"] + row["length"] > SAVE_SECTOR_DATA_SIZE:
            _fail(f"Stage61 record segment exceeds checksum-excluded tail: {row}")
    if sum(row["length"] for row in segments) != 0x616 \
            or segments[-1]["record_start"] + segments[-1]["length"] != 0x616:
        _fail("Stage61 record segments do not exactly cover 0x616 bytes")

    persistent_report = generated.get("persistent_state_compatibility", {})
    normal_save_metadata_contract = _validate_stage61_normal_save_cow_metadata(
        persistent_report.get("normal_save_copy_on_write")
    )
    expected_persistent_payload = [
        {"owner": "gExpandedFlags", "address": "0x0203B0E8", "size": 0x200},
        {"owner": "gExpandedVars", "address": "0x0203B2E8", "size": 0x400},
        {"owner": "gLastUsedBall", "address": "0x0203B6EC", "size": 2},
        {"owner": "gPlayerCoins", "address": "0x0203B78C", "size": 4},
    ]
    if persistent_report.get("payload") != expected_persistent_payload:
        _fail("Stage61 generated persistent payload owners differ")
    if persistent_report.get("record") != {
        "magic_little_endian": "S61E",
        "version": 1,
        "header_size": 0x10,
        "payload_size": 0x606,
        "record_size": 0x616,
        "crc": "CRC32_IEEE_AND_ONES_COMPLEMENT",
    }:
        _fail("Stage61 generated S61E record geometry differs")
    if persistent_report.get("stock_tail_fragments") != [
        {"logical_chunk": 13, "stock_size": 0x7D0, "size": 0x616}
    ]:
        _fail("Stage61 generated save tail placement differs")
    if (
        persistent_report.get("partial_save_policy")
        != (
            "ATOMIC_SOURCE_CHUNK13_S61E_COMMIT_THEN_EXACT_SOURCE_"
            "FULL_GENERATION_COPY_ON_WRITE"
        )
        or persistent_report.get("link_full_replace_policy")
        != "DELAYED_SIGNATURE_ATOMIC_CLONE_WITH_RECORD_INJECTION"
        or persistent_report.get("sector31_transaction_owner")
        != "STAGE36_QOL_PRODUCTION_UNCHANGED"
    ):
        _fail("Stage61 generated save orchestration policy differs")

    trampolines = generated.get("region_map", {}).get("stock_trampolines", [])
    if any(
        row.get("name") in {
            "stock_handle_load_sector", "stock_get_save_valid_status",
        }
        for row in trampolines
    ):
        _fail("bounded save readがstock trampolineを保持しています")

    bounded_read = persistent_report.get("bounded_read_contract")
    expected_generation_order = {
        "algorithm": "HALF_RANGE_MODULAR_U32",
        "delta_expression": "second_counter - first_counter",
        "second_is_newer_when": "delta != 0 && delta < 0x80000000",
        "equal_counter_selection": "FIRST",
        "exact_half_range_tie_selection": "FIRST",
        "physical_slot_parity": "slot_base == 14 * (counter & 1)",
        "mgba_reachable_wrap_pair": "slot0=0xFFFFFFFE,slot1=0x00000001",
        "other_comparator_vectors": "UNIT_LEVEL_EXPRESSION_GATE",
        "wrap_examples": {
            "0xFFFFFFFE_vs_0x00000001": "SECOND",
            "0x00000001_vs_0xFFFFFFFE": "FIRST",
        },
    }
    expected_rotation_policy = {
        "first_sector_definition": "PHYSICAL_INDEX_OF_LOGICAL_ID_0",
        "expected_physical_index_by_logical_id": (
            "(first + logical_id) % 14"
        ),
        "all_14_logical_ids_require_exact_relative_rotation": True,
        "permuted_full_bank_status": "ERROR",
        "newest_permuted_full_bank_selection": (
            "FALL_BACK_TO_OLDER_EXACT_ROTATION"
        ),
        "both_banks_permuted_status": "INVALID_NO_RAM_COPY",
        "mgba_required": True,
    }
    if not isinstance(bounded_read, Mapping) \
            or bounded_read.get("footer_id_must_be_below_row_count_before_index") is not True \
            or bounded_read.get("descriptor_row_count") != 14 \
            or bounded_read.get("descriptor_size_must_match_stock_table") is not True \
            or bounded_read.get("descriptor_destination_must_be_ewram") is not True \
            or bounded_read.get("signature_checksum_counter_and_parity_validated") is not True \
            or bounded_read.get("duplicate_ids_rejected") is not True \
            or bounded_read.get("required_id_mask") != "0x3FFF" \
            or bounded_read.get("partial_newer_generation_falls_back_to_complete_older") is not True \
            or bounded_read.get("ram_copy_only_after_selected_slot_full_validation") is not True \
            or bounded_read.get("both_slots_invalid_copy_count") != 0 \
            or bounded_read.get("both_slots_invalid_expanded_state") != "CLEAR" \
            or bounded_read.get("generation_order") != expected_generation_order \
            or bounded_read.get("slot_sector_rotation_policy") \
                != expected_rotation_policy:
        _fail("Stage61 bounded save read contract differs")
    expected_read_hooks = [
        {
            "address": "0x080DAEF4",
            "name": "GetSaveValidStatus",
            "preimage_hex": "f0b557464e464546",
            "runtime_symbol": "Stage61State_GetSaveValidStatus",
            "stock_trampoline_allowed": False,
        },
        {
            "address": "0x080DAE3C",
            "name": "HandleLoadSector",
            "preimage_hex": "f0b5474680b48846",
            "runtime_symbol": "Stage61State_HandleLoadSector",
            "stock_trampoline_allowed": False,
        },
    ]
    if persistent_report.get("bounded_read_entry_hooks") != expected_read_hooks:
        _fail("Stage61 bounded save read entry hooks differ")

    link_commit = persistent_report.get("link_save_record_commit")
    if not isinstance(link_commit, Mapping):
        _fail("Stage61 SAVE_LINK COW contract missing")
    record_transaction = link_commit.get("record_only_transaction")
    preflight = link_commit.get("preflight_before_stock")
    live_descriptors = link_commit.get("live_descriptor_snapshot")
    expected_transaction_sequence = [
        "PREFLIGHT_ENSURE_TWO_COMPLETE_GENERATIONS",
        "STOCK_SAVE_LINK_IDS_0_TO_4_IN_PLACE",
        "POST_STOCK_ATOMIC_SOURCE_RECORD_COMMIT_WITH_OLD_BACKUP_VALID",
        "POST_STOCK_COPY_ON_WRITE_FULL_GENERATION_FROM_EXACT_NEW_SOURCE",
    ]
    expected_source_record_commit = {
        "logical_sector": 13,
        "source_counter": "c",
        "record_policy": "S61E_ONLY_REWRITE_IN_SOURCE_SECTOR",
        "erase_callback_boundaries": 1,
        "program_byte_callback_boundaries": 0x1000,
        "callback_boundaries": 1 + 0x1000,
        "signature_commit_marker_offset": "0x0FF8",
        "signature_first_byte_programmed_last": True,
        "exact_readback_before_next_phase": [
            "FULL_SECTOR_READ",
            "FULL_SECTOR_CRC32_MATCH",
            "FOOTER_ID_13",
            "FOOTER_CHECKSUM",
            "FOOTER_SIGNATURE",
            "S61E_HEADER_PAYLOAD_AND_CRC_ALL_BYTES_EXACT_MATCH",
        ],
    }
    expected_phase_failure_bank = {
        "post_descriptor_rebuild_failure": (
            "SOURCE_PHYSICAL_LOGICAL_ID13_ONLY"
        ),
        "source_record_before_or_during_program_failure": (
            "SOURCE_PHYSICAL_LOGICAL_ID13_ONLY"
        ),
        "source_record_exact_readback_failure": (
            "SOURCE_PHYSICAL_LOGICAL_ID13_ONLY"
        ),
        "target_invalidation_failure": (
            "TARGET_PHYSICAL_LOGICAL_ID13_ONLY"
        ),
        "target_clone_failure": (
            "TARGET_PHYSICAL_FAILED_LOGICAL_SECTOR_ONLY"
        ),
        "target_final_validation_failure": (
            "TARGET_PHYSICAL_LOGICAL_ID13_ONLY"
        ),
        "both_banks_marked_by_one_post_failure": False,
    }
    if (
        link_commit.get("stock_entry_address") != "0x080DB230"
        or link_commit.get("stock_entry_modified") is not False
        or link_commit.get("stock_entry_thumb_pointer") != "0x080DB231"
        or link_commit.get("runtime_symbol") != "Stage61State_HandleSavingData"
        or link_commit.get("record_only_symbol") != "Stage61State_UpdateRecordOnly"
        or link_commit.get("save_type") != "SAVE_LINK_ONLY_1"
        or link_commit.get("save_ereader_type_2_intercepted") is not False
        or link_commit.get("transaction_sequence")
            != expected_transaction_sequence
        or link_commit.get("outer_post_failure_additional_mark") is not False
        or link_commit.get("outer_record_result_non_ok_action")
            != "RETURN_STATUS_ERROR_ONLY"
        or link_commit.get(
            "target_invalidation_early_guard_non_ok_caller_marks_target_id13"
        ) is not True
        or link_commit.get("phase_failure_damaged_bank")
            != expected_phase_failure_bank
        or link_commit.get("save_failed_screen_wipe_and_retry_mgba_required")
            is not True
        or not isinstance(preflight, Mapping)
        or preflight.get("runtime_function")
            != "Stage61State_EnsureBackupGeneration"
        or preflight.get("preflight_promotes_global_counter") is not False
        or preflight.get("stock_called_when_preflight_fails") is not False
        or preflight.get("stock_partial_logical_ids") != [0, 1, 2, 3, 4]
        or preflight.get("stock_fault_invariant")
            != "OPPOSITE_COMPLETE_GENERATION_REMAINS_VALID"
        or not isinstance(live_descriptors, Mapping)
        or live_descriptors.get("descriptor_count") != 14
        or live_descriptors.get("source")
            != "LIVE_SAVE_BLOCK2_SAVE_BLOCK1_POKEMON_STORAGE_OWNERS"
        or live_descriptors.get("preflight_runs_before_stock_cache_refresh") is not True
        or live_descriptors.get("preflight_and_post_snapshots_are_distinct") is not True
        or live_descriptors.get("data_size_padding_exactly_rebuilt") is not True
        or live_descriptors.get("normal_continue_stale_cache_regression")
            != "MGBA_REQUIRED"
        or not isinstance(record_transaction, Mapping)
        or record_transaction.get("strategy")
            != "SOURCE_RECORD_ATOMIC_COMMIT_THEN_COPY_ON_WRITE"
        or record_transaction.get("fault_injection_granularity")
            != (
                "MGBA_STOCK_FLASH_CALLBACK_BEFORE_AND_AFTER_EACH_"
                "ERASE_OR_PROGRAM_BYTE"
            )
        or record_transaction.get(
            "analog_flash_cell_threshold_during_callback_modelled"
        ) is not False
        or record_transaction.get("scope_basis")
            != (
                "MGBA_EMULATOR_AND_STOCK_FLASH_API_OBSERVABLE_BOUNDARIES"
            )
        or record_transaction.get("invariant")
            != "AT_LEAST_ONE_EXACT_GENERATION_ALWAYS"
        or record_transaction.get("source_generation_erased_or_programmed")
            is not True
        or record_transaction.get("source_record_atomic_commit")
            != expected_source_record_commit
        or record_transaction.get(
            "at_least_one_exact_generation_remains_valid_at_every_fault_offset"
        ) is not True
        or record_transaction.get(
            "protected_old_backup_valid_during_source_rewrite"
        ) is not True
        or record_transaction.get("source_exact_new_valid_after_atomic_commit")
            is not True
        or record_transaction.get("source_all_14_sectors_revalidated_after_commit")
            is not True
        or record_transaction.get("generation_selector_rerun_during_transaction")
            is not False
        or record_transaction.get("target_invalidation_after_source_commit")
            is not True
        or record_transaction.get("logical_sector_order") != list(range(14))
        or record_transaction.get("record_bearing_logical_sector") != 13
        or record_transaction.get("record_bearing_sector_committed_last") is not True
        or record_transaction.get("per_sector_commit_marker_offset") != "0x0FF8"
        or record_transaction.get("per_sector_commit_marker_programmed_last") is not True
        or record_transaction.get("preflight_callback_boundaries") != 57358
        or record_transaction.get("stock_callback_boundaries") != 20485
        or record_transaction.get("post_source_record_callback_boundaries")
            != 4097
        or record_transaction.get("post_source_revalidation_callback_boundaries")
            != 0
        or record_transaction.get("post_target_invalidation_callback_boundaries")
            != 1
        or record_transaction.get("post_clone_callback_boundaries") != 57358
        or record_transaction.get("post_callback_boundaries") != 61456
        or record_transaction.get("target_clone") != {
            "source": "EXACT_NEW_SOURCE_C",
            "target": "COUNTER_C_PLUS_ONE_INACTIVE_SLOT",
            "inject_record": 0,
            "callback_boundaries": 57358,
        }
        or record_transaction.get("required_backup_initial_states") != [
            "TWO_VALID", "EMPTY", "ERROR",
            "PARTIAL_OR_SINGLE_GENERATION", "TORN_STOCK_RETRY",
        ]
    ):
        _fail("Stage61 SAVE_LINK COW contract differs")

    # Exact Stage60 save has zeroed checksum-excluded tails.  It remains valid
    # under the retained table; custom header validation deterministically
    # chooses the clear-to-zero migration path.
    legacy_raw = (root / STAGE60_TEST_READY_SAVE_RELATIVE).read_bytes()
    legacy_record = bytearray()
    for section_id, length in ((13, 0x616),):
        physical_sector = None
        for physical in range(14):
            sector = legacy_raw[physical * 0x1000:(physical + 1) * 0x1000]
            if struct.unpack_from("<H", sector, 0xFF4)[0] == section_id:
                physical_sector = sector
                break
        if physical_sector is None:
            _fail(f"Stage60 save section absent for custom migration: {section_id}")
        size = STOCK_SAVE_SECTION_ROWS[section_id][1]
        legacy_record.extend(physical_sector[size:size + length])
    if len(legacy_record) != 0x616 \
            or struct.unpack_from("<I", legacy_record)[0] == 0x45313653:
        _fail("Stage60 legacy tail unexpectedly contains a valid Stage61 header")

    required_addresses = {
        name: int(symbols[name]) for name in required_symbols
    }
    if not (
        required_addresses["Stage61State_HandleWriteSector"]
        < required_addresses["Stage61State_HandleReplaceSector"]
        < required_addresses["Stage61State_HandleLoadSector"]
    ):
        _fail("Stage61 custom save symbol order differs")
    all_symbol_addresses = sorted({int(value) for value in symbols.values()})
    symbol_bodies: dict[str, dict[str, Any]] = {}
    for name in sorted(required_symbols):
        address = required_addresses[name]
        later = [value for value in all_symbol_addresses if value > address]
        end = later[0] if later else code_address + code_size
        if not code_address <= address < end <= code_address + code_size:
            _fail(f"Stage61 custom save symbol body range differs: {name}")
        body = _rom_slice(rom, address, end - address, name)
        symbol_bodies[name] = {
            "address": address,
            "address_hex": _hex(address, 8),
            "thumb_entry": address | 1,
            "body_size": len(body),
            "body_sha256": _sha(body),
        }
    return {
        "status": "PREFERRED_STOCK_LAYOUT_COMPATIBILITY_PLAN_INSTALLED",
        "stage61_rom": {
            "path": str(STAGE61_ROM_RELATIVE),
            "sha256": _sha(rom),
            "size": len(rom),
        },
        "runtime_source": {
            "path": str(STAGE61_RUNTIME_SOURCE_RELATIVE),
            "sha256": source_sha256,
        },
        "runtime_code": {
            "address": code_address,
            "address_hex": _hex(code_address, 8),
            "size": code_size,
            "sha256": code_sha256,
            "persistent_literal_evidence": literal_evidence,
        },
        "symbols": symbol_bodies,
        "active_exact_patches": active_patches,
        "active_patch_count": len(active_patches),
        "record": {
            "magic": 0x45313653,
            "version": 1,
            "header_size": 0x10,
            "payload_size": 0x606,
            "record_size": 0x616,
            "payload": [
                {"owner": "expanded_flags", "size": 0x200},
                {"owner": "expanded_vars", "size": 0x400},
                {"owner": "gLastUsedBall", "size": 2},
                {"owner": "cfru_player_coins_u32", "size": 4},
            ],
            "integrity": "CRC32(IEEE) + bitwise-complement",
            "segments": list(segments),
            "checksum_excluded_tail_only": True,
        },
        "stock_layout_retained": True,
        "stock_orchestration_retained": True,
        "delayed_signature_replace_retained": True,
        "bounded_read_contract": dict(bounded_read),
        "bounded_read_entry_hooks": list(expected_read_hooks),
        "link_save_record_commit": dict(link_commit),
        "normal_save_copy_on_write": {
            "source": normal_save_source_contract,
            "object": normal_save_object_contract,
            "metadata": normal_save_metadata_contract,
        },
        "stock_bounded_read_trampolines_absent": True,
        "legacy_exact_save": {
            "sha256": _sha(legacy_raw),
            "record_magic_present": False,
            "migration_behavior": "stock load succeeds; invalid/absent S61E record clears expanded state",
        },
        "unsafe_cfru_direct_plan_rejected": True,
    }


def _save_expansion_binary_contract(root: Path, raw: bytes) -> dict[str, Any]:
    offsets = _linked_offsets_contract(root)
    source = _save_source_contract(root)
    targets = [int(row["address"]) for row in SAVE_CORE_HOOKS]
    calls = _thumb_bl_calls_by_target(raw, targets)
    core_rows: list[dict[str, Any]] = []
    for row in SAVE_CORE_HOOKS:
        address = int(row["address"])
        _require_rom_bytes(raw, address, bytes(row["expected"]), str(row["symbol"]))
        expected_calls = list(row["expected_calls"])
        if calls[address] != expected_calls:
            _fail(
                f"{row['symbol']} call universe differs: "
                f"{[hex(value) for value in calls[address]]}"
            )
        patch = _save_hook_patch(row)
        target = int(patch["target"])
        if _rom_slice(raw, target, 16, str(row["symbol"])) == b"\xFF" * 16:
            _fail(f"linked target is erased: {row['symbol']}")
        core_rows.append(
            {
                **patch,
                "connected": False,
                "direct_bl_call_count": len(calls[address]),
                "direct_bl_calls": calls[address],
                "direct_bl_calls_hex": [_hex(value, 8) for value in calls[address]],
            }
        )
    for row in SAVE_LIFECYCLE_HOOKS:
        _require_rom_bytes(
            raw, int(row["address"]), bytes(row["expected"]), str(row["symbol"])
        )
    current_table = _read_save_section_rows(raw, STOCK_SAVE_SECTION_OFFSETS)
    linked_table = _read_save_section_rows(raw, LINKED_SAVE_SECTION_OFFSETS)
    if current_table != STOCK_SAVE_SECTION_ROWS:
        _fail("Stage60 stock save-section table rows differ")
    if linked_table != LINKED_SAVE_SECTION_ROWS:
        _fail("Stage60 linked CFRU save-section table rows differ")
    _require_rom_bytes(
        raw,
        SAVE_SECTION_OFFSETS_POINTER_SITE,
        struct.pack("<I", STOCK_SAVE_SECTION_OFFSETS),
        "gSaveSectionOffsets pointer",
    )
    recommended = save_expansion_patch_plan()
    apply_exact_patches(raw, recommended)
    all_candidates = all_upstream_save_patch_plan()
    apply_exact_patches(raw, all_candidates)
    rejected = [
        row for row in core_rows
        if row["project_policy"].startswith("REJECT_")
    ]
    if [row["target_symbol"] for row in rejected] != [
        "SaveWriteToFlash", "HandleSavingData"
    ]:
        _fail("sector31 unsafe core hook classification differs")
    return {
        "status": "CRITICAL_UNCONNECTED_AND_LEGACY_MIGRATION_REQUIRED",
        "linked_offsets": offsets,
        "source": source,
        "stage60_core_entries": core_rows,
        "all_upstream_exact_patches": all_candidates,
        "cfru_direct_exact_patches_rejected_without_migration": recommended,
        "cfru_direct_patch_count": len(recommended),
        # Compatibility aliases for callers created during the investigation.
        "recommended_project_exact_patches": recommended,
        "recommended_patch_count": len(recommended),
        "all_candidate_patch_count": len(all_candidates),
        "stock_table": [
            {"section_id": index, "offset": row[0], "size": row[1]}
            for index, row in enumerate(current_table)
        ],
        "linked_table": [
            {"section_id": index, "offset": row[0], "size": row[1]}
            for index, row in enumerate(linked_table)
        ],
        "table_pointer_patch": next(
            row for row in recommended
            if row["name"] == "cfru_save_expansion::save_section_offsets"
        ),
    }


def _raid_binary_contract(raw: bytes) -> dict[str, Any]:
    operations = Counter()
    rows: list[dict[str, Any]] = []
    for consumer in RAID_CONSUMERS:
        register = int(consumer["base_register"])
        _require_rom_bytes(
            raw,
            int(consumer["base_site"]),
            _movs_immediate(register, OLD_RAID_START >> 5),
            f"{consumer['consumer']} base",
        )
        literal = struct.unpack(
            "<I", _rom_slice(raw, int(consumer["target_literal"]), 4, "Raid target literal")
        )[0]
        if literal != int(consumer["target"]):
            _fail(
                f"{consumer['consumer']} target literal differs: "
                f"{literal:#x} != {int(consumer['target']):#x}"
            )
        end_site = consumer["exclusive_end_site"]
        if end_site is not None:
            _require_rom_bytes(
                raw,
                int(end_site),
                struct.pack("<I", OLD_RAID_END_EXCLUSIVE),
                f"{consumer['consumer']} exclusive end",
            )
        operations[str(consumer["operation"])] += 1
        rows.append(
            {
                **consumer,
                "entry_hex": _hex(int(consumer["entry"]), 8),
                "call_hex": _hex(int(consumer["call"]), 8),
                "target_hex": _hex(int(consumer["target"]), 8),
                "target_literal_hex": _hex(int(consumer["target_literal"]), 8),
                "base_site_hex": _hex(int(consumer["base_site"]), 8),
                "exclusive_end_site_hex": (
                    _hex(int(end_site), 8) if end_site is not None else None
                ),
            }
        )
    if operations != Counter({"FlagGet": 2, "FlagSet": 1, "FlagClear": 3}):
        _fail(f"Raid binary consumer operations differ: {dict(operations)}")
    patches = raid_patch_plan()
    apply_exact_patches(raw, patches)
    return {
        "old_range": {
            "start": OLD_RAID_START,
            "start_hex": _hex(OLD_RAID_START),
            "end_inclusive": OLD_RAID_END_EXCLUSIVE - 1,
            "end_inclusive_hex": _hex(OLD_RAID_END_EXCLUSIVE - 1),
            "end_exclusive": OLD_RAID_END_EXCLUSIVE,
            "end_exclusive_hex": _hex(OLD_RAID_END_EXCLUSIVE),
            "count": RAID_FLAG_COUNT,
        },
        "binary_consumer_count": len(rows),
        "operation_counts": dict(sorted(operations.items())),
        "consumers": rows,
        "patch_site_count": len(patches),
        "patches": patches,
    }


def _stage61_raid_installation_contract(root: Path) -> dict[str, Any]:
    """Stage61 final ROM/source/生成宣言へRaid移設とAPI guardを証明する。"""

    metadata = json.loads(
        (root / STAGE61_METADATA_RELATIVE).read_text(encoding="utf-8")
    )
    generated = json.loads(
        (root / STAGE61_AUDIT_RELATIVE).read_text(encoding="utf-8")
    )
    rom = (root / STAGE61_ROM_RELATIVE).read_bytes()
    if len(rom) != ROM_SIZE or _sha(rom) != metadata.get("output", {}).get("sha256"):
        _fail("Stage61 Raid installation ROM identity differs")
    symbols = metadata.get("runtime", {}).get("symbols", {})
    operation_symbols = {
        "FlagGet": "Stage61MapSection_RaidFlagGet",
        "FlagSet": "Stage61MapSection_RaidFlagSet",
        "FlagClear": "Stage61MapSection_RaidFlagClear",
    }
    missing_symbols = set(operation_symbols.values()) - set(symbols)
    if missing_symbols:
        _fail(f"Stage61 Raid API guard symbols missing: {sorted(missing_symbols)}")
    patches = raid_patch_plan()
    declaration_rows = {
        str(row.get("name")): row
        for row in generated.get("change_audit", {}).get("declarations", [])
    }
    installed: list[dict[str, Any]] = []
    for patch in patches:
        address = int(patch["address"])
        replacement = bytes.fromhex(str(patch["replacement_hex"]))
        _require_rom_bytes(rom, address, replacement, str(patch["name"]))
        declaration_name = f"cfru_raid_flag_namespace::0x{address:08x}"
        candidates = [
            row for name, row in declaration_rows.items()
            if name.lower() == declaration_name
        ]
        if len(candidates) != 1:
            _fail(f"Stage61 Raid declaration missing/ambiguous: {declaration_name}")
        declaration = candidates[0]
        if (
            int(declaration["start"]) + ROM_BASE != address
            or str(declaration["expected_hex"]) != str(patch["expected_hex"])
            or str(declaration["replacement_hex"]) != str(patch["replacement_hex"])
        ):
            _fail(f"Stage61 Raid declaration differs: {declaration_name}")
        installed.append(dict(patch))

    # The six consumers use five unique function-pointer literals.  Redirect
    # every literal through the bounded Stage61 adapter as a defense against a
    # legacy 0x1800 caller reaching the linked routine through another path.
    # This guard set is deliberately reported separately from the nine
    # base/end relocation patches so callers cannot conflate the two counts.
    api_guard_by_address: dict[int, dict[str, Any]] = {}
    for consumer in RAID_CONSUMERS:
        address = int(consumer["target_literal"])
        operation = str(consumer["operation"])
        symbol = operation_symbols[operation]
        expected_target = int(consumer["target"])
        prior = api_guard_by_address.get(address)
        if prior is not None:
            if (
                prior["operation"] != operation
                or prior["expected_target"] != expected_target
                or prior["target_symbol"] != symbol
            ):
                _fail(f"Raid shared API literal has conflicting semantics: {address:#x}")
            continue
        api_guard_by_address[address] = {
            "name": f"cfru_raid_flag_api_guard::{address:#010x}",
            "kind": "LITTLE_ENDIAN_U32_THUMB_FUNCTION_POINTER",
            "address": address,
            "address_hex": _hex(address, 8),
            "operation": operation,
            "expected_target": expected_target,
            "expected_target_hex": _hex(expected_target, 8),
            "expected_hex": struct.pack("<I", expected_target).hex(),
            "target_symbol": symbol,
            "replacement_target": int(symbols[symbol]) | 1,
            "replacement_target_hex": _hex(int(symbols[symbol]) | 1, 8),
            "replacement_hex": struct.pack("<I", int(symbols[symbol]) | 1).hex(),
        }
    api_guards = [api_guard_by_address[key] for key in sorted(api_guard_by_address)]
    if len(api_guards) != 5:
        _fail(f"Stage61 Raid API guard count differs: {len(api_guards)}")
    for guard in api_guards:
        name = str(guard["name"])
        address = int(guard["address"])
        _require_rom_bytes(
            rom,
            address,
            bytes.fromhex(str(guard["replacement_hex"])),
            name,
        )
        declaration = declaration_rows.get(name)
        if declaration is None or (
            int(declaration["start"]) + ROM_BASE != address
            or str(declaration["expected_hex"]) != str(guard["expected_hex"])
            or str(declaration["replacement_hex"]) != str(guard["replacement_hex"])
            or declaration.get("category") != "PERSISTENT_STATE_RAID_FLAG_API_GUARD"
        ):
            _fail(f"Stage61 Raid API guard declaration differs: {name}")

    policy = generated.get("map_section_consumer_policy", {}).get(
        "raid_flag_range", {}
    )
    if policy != {
        "start": "0x15C0",
        "end_inclusive": "0x162C",
        "count": RAID_FLAG_COUNT,
        "legacy_collision_range": "0x1800..0x186C",
        "binary_base_patch_count": 6,
        "binary_end_patch_count": 3,
        "api_adapter_literal_count": 5,
    }:
        _fail("Stage61 generated Raid flag policy differs")
    return {
        "status": "INSTALLED_EXACT",
        "stage61_rom_sha256": _sha(rom),
        "source_definition": RECOMMENDED_RAID_START,
        "source_definition_hex": _hex(RECOMMENDED_RAID_START),
        "target_start": RECOMMENDED_RAID_START,
        "target_end_exclusive": RECOMMENDED_RAID_END_EXCLUSIVE,
        "patch_count": len(installed),
        "patches": installed,
        "api_guard_patch_count": len(api_guards),
        "api_guard_patches": api_guards,
        "total_binary_patch_count": len(installed) + len(api_guards),
    }


def _ram_addressing_contract() -> dict[str, Any]:
    samples = []
    for flag in (0x0900, 0x1300, 0x1500, 0x1800, 0x18FF):
        stock_offset = STOCK_FLAG_BITMAP_OFFSET + (flag >> 3)
        expanded_offset = (flag - FLAG_UNIVERSE_START) >> 3
        owner = (
            "VEGA_EVENT_VARS"
            if STOCK_VAR_OFFSET <= stock_offset < STOCK_VAR_END
            else "OUTSIDE_VEGA_EVENT_VARS"
        )
        samples.append(
            {
                "id": flag,
                "id_hex": _hex(flag),
                "bit_index": flag & 7,
                "stock_normal_saveblock1_offset": stock_offset,
                "stock_normal_saveblock1_offset_hex": _hex(stock_offset),
                "stock_owner": owner,
                "expanded_byte_offset": expanded_offset,
                "expanded_pointer": EXPANDED_FLAG_RAM + expanded_offset,
                "expanded_pointer_hex": _hex(EXPANDED_FLAG_RAM + expanded_offset, 8),
            }
        )
    if any(row["stock_owner"] != "VEGA_EVENT_VARS" for row in samples):
        _fail("sampled high flags do not all alias SaveBlock1 vars under stock routing")
    if samples[-1]["expanded_pointer"] != EXPANDED_VAR_RAM - 1:
        _fail("0x18FF does not resolve to last expanded flag byte")
    return {
        "normal_overworld_stock_formula": {
            "saveblock1_pointer_address": SAVE_BLOCK1_POINTER,
            "formula": "*(u32*)0x03005048 + 0x0EE0 + (u16(id) >> 3)",
            "flag_bitmap_offset": STOCK_FLAG_BITMAP_OFFSET,
            "flag_bitmap_end_exclusive": STOCK_FLAG_BITMAP_END,
            "vars_offset": STOCK_VAR_OFFSET,
            "vars_end_exclusive": STOCK_VAR_END,
        },
        "expanded_flag_formula": {
            "formula": "0x0203B0E8 + ((u16(id) - 0x0900) >> 3)",
            "start": EXPANDED_FLAG_RAM,
            "end_exclusive": EXPANDED_VAR_RAM,
            "size": EXPANDED_VAR_RAM - EXPANDED_FLAG_RAM,
            "id_start": FLAG_UNIVERSE_START,
            "id_end_exclusive": FLAG_UNIVERSE_END_EXCLUSIVE,
        },
        "expanded_var_formula": {
            "formula": "0x0203B2E8 + 2 * (u16(id) - 0x5000)",
            "start": EXPANDED_VAR_RAM,
            "end_exclusive": EXPANDED_VAR_END_EXCLUSIVE,
            "size": EXPANDED_VAR_END_EXCLUSIVE - EXPANDED_VAR_RAM,
            "id_start": 0x5000,
            "id_end_exclusive": 0x5200,
        },
        "samples": samples,
        "conclusion": "stock global hook未接続時は0x0900..0x18FFが512-byte Vega event varsへ重なる",
    }


def _source_summary(ids: Iterable[int]) -> dict[str, Any]:
    values = sorted(set(ids))
    return {"count": len(values), "ids": values, "ranges": _id_ranges(values)}


def _collision_rows(
    start: int,
    end_exclusive: int,
    source_ids: Mapping[str, set[int]],
) -> list[dict[str, Any]]:
    target = set(range(start, end_exclusive))
    rows = []
    for source, ids in sorted(source_ids.items()):
        collision = sorted(target & ids)
        if collision:
            rows.append(
                {
                    "source": source,
                    "count": len(collision),
                    "ids": collision,
                    "ranges": _id_ranges(collision),
                }
            )
    return rows


def _free_windows(used: set[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    universe = set(range(FLAG_UNIVERSE_START, FLAG_UNIVERSE_END_EXCLUSIVE))
    free = universe - used
    runs = _id_ranges(free)
    aligned: list[dict[str, Any]] = []
    for start in range(FLAG_UNIVERSE_START, FLAG_UNIVERSE_END_EXCLUSIVE, 0x20):
        end = start + RAID_FLAG_COUNT
        if end <= FLAG_UNIVERSE_END_EXCLUSIVE and set(range(start, end)) <= free:
            aligned.append(
                {
                    "start": start,
                    "start_hex": _hex(start),
                    "end_inclusive": end - 1,
                    "end_inclusive_hex": _hex(end - 1),
                    "end_exclusive": end,
                    "end_exclusive_hex": _hex(end),
                    "count": RAID_FLAG_COUNT,
                    "movs_imm8": start >> 5,
                    "movs_imm8_hex": _hex(start >> 5, 2),
                }
            )
    return runs, aligned


MGBA_PROBE_SOURCE = r'''
#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

enum {
    PROBE_GET_VAR_POINTER = 0x0806DC49U,
    PROBE_GET_FLAG_POINTER = 0x0806DDB5U,
    PROBE_FLAG_SET = 0x0806DE75U,
    PROBE_FLAG_CLEAR = 0x0806DE9DU,
    PROBE_FLAG_GET = 0x0806DEC5U,
    PROBE_GET_EXPANDED_FLAG_POINTER = 0x091281D1U,
    PROBE_GET_EXPANDED_VAR_POINTER = 0x09128221U,
    PROBE_SAVE_BLOCK1_POINTER = 0x03005048U,
    PROBE_EXPANDED_FLAG_RAM = 0x0203B0E8U,
    PROBE_SPECIAL_FLAG_RAM = 0x02037014U,
};

static const uint16_t probe_flag_ids[] = {
    0x0500U, 0x0900U, 0x1300U, 0x1500U, 0x1800U, 0x18FFU, 0x4001U,
};

static const uint16_t probe_var_ids[] = {
    0x4000U, 0x5000U, 0x51FFU,
};

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM TEMP_SAVE\n", argv[0]);
        return 2;
    }
    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    bootstrap_write_blank_save(argv[2]);
    bootstrap_phase = "stage61-state-namespace-probe";
    struct mCore *core = bootstrap_open_core(argv[1], argv[2], NULL);
    run_trace_prefix(core);
    uint32_t save1 = read32(core, PROBE_SAVE_BLOCK1_POINTER);
    if (save1 < 0x02000000U || save1 >= 0x02040000U)
        bootstrap_die("SaveBlock1 pointer is outside EWRAM");

    printf("{\"saveblock1\":%" PRIu32 ",\"warnings\":%u,\"flags\":[",
           save1, log_problem_count);
    for (unsigned index = 0U; index < ARRAY_LEN(probe_flag_ids); ++index) {
        uint16_t id = probe_flag_ids[index];
        uint32_t stock_pointer = id < 0x4000U
            ? save1 + 0x0EE0U + (id >> 3U) : 0U;
        uint32_t linked_pointer = call_preserving(
            core, PROBE_GET_EXPANDED_FLAG_POINTER, id, 0U, 0U, 0U);
        uint32_t global_pointer = call_preserving(
            core, PROBE_GET_FLAG_POINTER, id, 0U, 0U, 0U);
        uint32_t expanded_pointer = id >= 0x0900U && id < 0x1900U
            ? PROBE_EXPANDED_FLAG_RAM + ((id - 0x0900U) >> 3U) : 0U;
        uint32_t special_pointer = id >= 0x4000U && id <= 0x407FU
            ? PROBE_SPECIAL_FLAG_RAM + ((id - 0x4000U) >> 3U) : 0U;
        uint8_t mask = (uint8_t)(1U << (id & 7U));
        if (stock_pointer != 0U)
            write8(core, stock_pointer, 0U);
        if (expanded_pointer != 0U)
            write8(core, expanded_pointer, 0U);
        if (special_pointer != 0U)
            write8(core, special_pointer, 0U);
        (void)call_preserving(core, PROBE_FLAG_SET, id, 0U, 0U, 0U);
        uint32_t get_after_set = call_preserving(
            core, PROBE_FLAG_GET, id, 0U, 0U, 0U);
        uint8_t stock_after_set = stock_pointer != 0U
            ? read8(core, stock_pointer) : 0U;
        uint8_t expanded_after_set = expanded_pointer != 0U
            ? read8(core, expanded_pointer) : 0U;
        uint8_t special_after_set = special_pointer != 0U
            ? read8(core, special_pointer) : 0U;
        (void)call_preserving(core, PROBE_FLAG_CLEAR, id, 0U, 0U, 0U);
        uint32_t get_after_clear = call_preserving(
            core, PROBE_FLAG_GET, id, 0U, 0U, 0U);
        uint8_t stock_after_clear = stock_pointer != 0U
            ? read8(core, stock_pointer) : 0U;
        uint8_t expanded_after_clear = expanded_pointer != 0U
            ? read8(core, expanded_pointer) : 0U;
        uint8_t special_after_clear = special_pointer != 0U
            ? read8(core, special_pointer) : 0U;
        printf("%s{\"id\":%u,\"mask\":%u,\"stock_pointer\":%" PRIu32
               ",\"linked_pointer\":%" PRIu32 ",\"global_pointer\":%" PRIu32
               ",\"expanded_pointer\":%" PRIu32
               ",\"special_pointer\":%" PRIu32
               ",\"get_after_set\":%" PRIu32
               ",\"stock_after_set\":%u,\"expanded_after_set\":%u"
               ",\"special_after_set\":%u"
               ",\"get_after_clear\":%" PRIu32 ",\"stock_after_clear\":%u"
               ",\"expanded_after_clear\":%u,\"special_after_clear\":%u}",
               index == 0U ? "" : ",", id, mask, stock_pointer,
               linked_pointer, global_pointer, expanded_pointer,
               special_pointer, get_after_set, stock_after_set,
               expanded_after_set, special_after_set, get_after_clear,
               stock_after_clear, expanded_after_clear, special_after_clear);
    }
    printf("],\"vars\":[");
    for (unsigned index = 0U; index < ARRAY_LEN(probe_var_ids); ++index) {
        uint16_t id = probe_var_ids[index];
        uint32_t linked_pointer = call_preserving(
            core, PROBE_GET_EXPANDED_VAR_POINTER, id, 0U, 0U, 0U);
        uint32_t global_pointer = call_preserving(
            core, PROBE_GET_VAR_POINTER, id, 0U, 0U, 0U);
        printf("%s{\"id\":%u,\"linked_pointer\":%" PRIu32
               ",\"global_pointer\":%" PRIu32 "}",
               index == 0U ? "" : ",", id, linked_pointer, global_pointer);
    }
    printf("]}\n");
    bootstrap_close_core(core);
    return log_problem_count == 0U ? 0 : 1;
}
'''


def _run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    label: str,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail(f"{label} execution failed: {exc}")
    if result.returncode:
        detail = (result.stderr + "\n" + result.stdout).strip()
        _fail(f"{label} failed ({result.returncode}): {detail[-8000:]}")
    return result


def _validate_mgba_observation(
    observation: Mapping[str, Any], *, hooks_connected: bool
) -> dict[str, bool]:
    save1 = int(observation["saveblock1"])
    assertions: dict[str, bool] = {
        "saveblock1_in_ewram": 0x02000000 <= save1 < 0x02040000,
        "no_mgba_warnings": int(observation["warnings"]) == 0,
    }
    flag_rows = {int(row["id"]): row for row in observation["flags"]}
    assertions["all_flag_probe_ids_present"] = set(flag_rows) == {
        0x0500, 0x0900, 0x1300, 0x1500, 0x1800, 0x18FF, 0x4001
    }
    for flag, row in flag_rows.items():
        prefix = f"flag_{flag:04X}"
        assertions[f"{prefix}_set_get"] = int(row["get_after_set"]) == 1
        assertions[f"{prefix}_clear_get"] = int(row["get_after_clear"]) == 0
        mask = int(row["mask"])
        if flag == 0x4001:
            assertions[f"{prefix}_not_stock_or_expanded"] = (
                int(row["stock_pointer"]) == 0
                and int(row["expanded_pointer"]) == 0
                and int(row["linked_pointer"]) == 0
            )
            assertions[f"{prefix}_global_special_route"] = (
                int(row["global_pointer"]) == SPECIAL_FLAG_RAM
                and int(row["special_pointer"]) == SPECIAL_FLAG_RAM
            )
            assertions[f"{prefix}_special_written"] = (
                int(row["special_after_set"]) == mask
            )
            assertions[f"{prefix}_special_cleared"] = (
                int(row["special_after_clear"]) == 0
            )
            continue
        stock = save1 + STOCK_FLAG_BITMAP_OFFSET + (flag >> 3)
        expanded = (
            EXPANDED_FLAG_RAM + ((flag - FLAG_UNIVERSE_START) >> 3)
            if flag >= FLAG_UNIVERSE_START
            else 0
        )
        assertions[f"{prefix}_stock_formula"] = int(row["stock_pointer"]) == stock
        assertions[f"{prefix}_linked_formula"] = int(row["linked_pointer"]) == expanded
        expected_global = expanded if hooks_connected and expanded else stock
        assertions[f"{prefix}_global_route"] = int(row["global_pointer"]) == expected_global
        assertions[f"{prefix}_special_unused"] = (
            int(row["special_pointer"]) == 0
            and int(row["special_after_set"]) == 0
            and int(row["special_after_clear"]) == 0
        )
        if hooks_connected and expanded:
            assertions[f"{prefix}_stock_untouched"] = int(row["stock_after_set"]) == 0
            assertions[f"{prefix}_expanded_written"] = int(row["expanded_after_set"]) == mask
        else:
            assertions[f"{prefix}_stock_written"] = int(row["stock_after_set"]) == mask
            assertions[f"{prefix}_expanded_untouched"] = int(row["expanded_after_set"]) == 0
        assertions[f"{prefix}_storage_cleared"] = (
            int(row["stock_after_clear"]) == 0
            and int(row["expanded_after_clear"]) == 0
        )
    var_rows = {int(row["id"]): row for row in observation["vars"]}
    assertions["all_var_probe_ids_present"] = set(var_rows) == {0x4000, 0x5000, 0x51FF}
    assertions["var_4000_stock_fallback"] = (
        int(var_rows[0x4000]["global_pointer"]) == save1 + STOCK_VAR_OFFSET
        and int(var_rows[0x4000]["linked_pointer"]) == 0
    )
    for variable in (0x5000, 0x51FF):
        expanded = EXPANDED_VAR_RAM + 2 * (variable - 0x5000)
        assertions[f"var_{variable:04X}_linked_formula"] = (
            int(var_rows[variable]["linked_pointer"]) == expanded
        )
        if hooks_connected:
            assertions[f"var_{variable:04X}_global_route"] = (
                int(var_rows[variable]["global_pointer"]) == expanded
            )
        else:
            assertions[f"var_{variable:04X}_global_not_expanded"] = (
                int(var_rows[variable]["global_pointer"]) != expanded
            )
    failed = sorted(name for name, passed in assertions.items() if not passed)
    if failed:
        _fail(f"mGBA namespace probe assertions failed: {failed}")
    return assertions


def run_mgba_flag_probe(root: Path = ROOT) -> dict[str, Any]:
    """Stage60 と一時 hook-patched image を実 libmGBA で比較する。"""

    compiler = shutil.which("cc") or shutil.which("gcc")
    if compiler is None:
        _fail("mGBA probe C compiler is unavailable")
    stage60_path = root / STAGE60_ROM_RELATIVE
    raw = stage60_path.read_bytes()
    validate_rom_identity(raw)
    patched = apply_exact_patches(raw, hook_patch_plan())
    with tempfile.TemporaryDirectory(prefix="stage61-namespace-mgba-") as temp_raw:
        directory = Path(temp_raw)
        source = directory / "stage61_namespace_probe.c"
        executable = directory / "stage61_namespace_probe"
        patched_rom = directory / "stage60-hooks-connected.gba"
        source.write_text(MGBA_PROBE_SOURCE, encoding="utf-8", newline="\n")
        patched_rom.write_bytes(patched)
        compile_result = _run_process(
            [
                compiler,
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-pedantic",
                f"-I{root / 'tools'}",
                str(source),
                "-o",
                str(executable),
                "-lmgba",
            ],
            cwd=root,
            label="mGBA namespace probe compile",
            timeout=60,
        )
        observations: dict[str, Any] = {}
        assertion_sets: dict[str, Any] = {}
        for label, rom_path, connected in (
            ("stage60_unconnected", stage60_path, False),
            ("candidate_hooks_connected", patched_rom, True),
        ):
            save = directory / f"{label}.sav"
            result = _run_process(
                [str(executable), str(rom_path), str(save)],
                cwd=root,
                label=f"mGBA namespace probe {label}",
                timeout=240,
            )
            lines = [line for line in result.stdout.splitlines() if line.strip()]
            if not lines:
                _fail(f"mGBA namespace probe {label} emitted no JSON")
            try:
                observation = json.loads(lines[-1])
            except json.JSONDecodeError as exc:
                _fail(f"mGBA namespace probe {label} JSON invalid: {exc}")
            observations[label] = observation
            assertion_sets[label] = _validate_mgba_observation(
                observation, hooks_connected=connected
            )
    return {
        "schema_version": 1,
        "status": "PASS",
        "engine": "libmGBA ARM7TDMI",
        "method": "natural-new-game trace then ROM FlagGet/Set/Clear and pointer entry calls",
        "compiler": compiler,
        "compile_stdout": compile_result.stdout.strip(),
        "temporary_hook_rom_sha256": _sha(patched),
        "observations": observations,
        "assertions": assertion_sets,
    }


def build_stage61_state_namespace_collision_audit(
    root: Path = ROOT, *, run_mgba: bool = False
) -> dict[str, Any]:
    root = root.resolve()
    stage60_path = root / STAGE60_ROM_RELATIVE
    raw = stage60_path.read_bytes()
    validate_rom_identity(raw)

    source_identity = _source_identity(root)
    mapsec = _parse_mapsec_count(root)
    raid_source = _raid_source_contract(root)
    save_layout = _save_layout_contract(root)
    linked_constants = _linked_cfru_flag_constants(root)
    event = _event_flag_inventory(raw)
    visibility = _object_visibility_inventory(root, raw)
    manifest = _manifest_inventory(root)
    bindings = _trainer_binding_inventory(root)
    registry = _namespace_registry_inventory(root)
    hook = _hook_binary_contract(raw)
    save_expansion = _save_expansion_binary_contract(root, raw)
    parasite_owners = _parasite_owner_contract(root)
    parasite_consumers = _parasite_live_consumer_contract(root, raw)
    legacy_save = _legacy_save_compatibility_contract(root)
    transaction_owner = _transaction_owner_contract(root)
    process_restart_gate = _process_restart_gate_contract(root)
    custom_save_compatibility = _stage61_custom_save_compatibility_contract(root)
    raid = _raid_binary_contract(raw)
    stage61_raid = _stage61_raid_installation_contract(root)
    ram = _ram_addressing_contract()

    source_ids: dict[str, set[int]] = {
        "cfru_linked_config": set(linked_constants["ids"]),
        "stage60_event_operands": set(event["ids"]),
        "stage60_object_visibility": set(visibility["ids"]),
        "project_flag_manifest": set(manifest["ids"]),
        "stage60_trainer_bindings": set(bindings["ids"]),
        # The Raid row is the candidate's own installed reservation, not a
        # competing owner.  Keep only other Stage61 owners in collision math.
        "stage61_namespace_registry": set(
            registry["project_ids_excluding_raid_owner"]
        ),
        "current_cfru_raid_completion": set(range(OLD_RAID_START, OLD_RAID_END_EXCLUSIVE)),
    }
    used = set().union(*source_ids.values())
    free_runs, aligned_windows = _free_windows(used)

    requested_collisions = _collision_rows(
        REQUESTED_RAID_START, REQUESTED_RAID_END_EXCLUSIVE, source_ids
    )
    old_collisions = _collision_rows(
        OLD_RAID_START,
        OLD_RAID_END_EXCLUSIVE,
        {key: value for key, value in source_ids.items() if key != "current_cfru_raid_completion"},
    )
    recommended_collisions = _collision_rows(
        RECOMMENDED_RAID_START, RECOMMENDED_RAID_END_EXCLUSIVE, source_ids
    )
    if not requested_collisions:
        _fail("requested 0x1500 Raid range unexpectedly appears free")
    event_requested = next(
        (row for row in requested_collisions if row["source"] == "stage60_event_operands"),
        None,
    )
    binding_requested = next(
        (row for row in requested_collisions if row["source"] == "stage60_trainer_bindings"),
        None,
    )
    if not event_requested or event_requested["count"] != RAID_FLAG_COUNT:
        _fail("0x1500 candidate is not covered by exactly 109 event operands")
    if not binding_requested or binding_requested["count"] != RAID_FLAG_COUNT:
        _fail("0x1500 candidate is not covered by exactly 109 trainer bindings")
    if recommended_collisions:
        _fail(f"recommended Raid range is not free: {recommended_collisions}")
    aligned_by_start = {row["start"]: row for row in aligned_windows}
    if RECOMMENDED_RAID_START not in aligned_by_start:
        _fail("recommended Raid range is absent from aligned free windows")

    four_id_guard = set(range(0x15BC, 0x15C0))
    if four_id_guard & used:
        _fail("0x15BC..0x15BF alignment guard is not free")
    patch_rows = raid_patch_plan()
    raid_only = apply_exact_patches(raw, patch_rows)
    hooks_only = apply_exact_patches(raw, hook_patch_plan())
    save_only = apply_exact_patches(raw, save_expansion_patch_plan())
    hooks_and_save = apply_exact_patches(hooks_only, save_expansion_patch_plan())
    hooks_save_and_raid = apply_exact_patches(hooks_and_save, patch_rows)

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task": "USER-20260830-STAGE61-STATE-NAMESPACE-COLLISION-AUDIT",
        "audit_status": "PASS",
        "status": (
            "CRITICAL_BLOCKED_EXPANDED_STATE_HOOKS_AND_SAVE_MISSING_"
            "LEGACY_MIGRATION_REQUIRED"
        ),
        "inputs": {
            "stage60_rom": {
                "path": str(STAGE60_ROM_RELATIVE),
                "size": len(raw),
                "sha256": _sha(raw),
            },
            "cfru": source_identity,
        },
        "cfru_contract": {
            "map_sections": mapsec,
            "raid_source": raid_source,
            "linked_flag_constants": linked_constants,
        },
        "save_storage": {
            "manifest": save_layout,
            "binary_expansion": save_expansion,
            "parasite_and_sector_owners": parasite_owners,
            "parasite_live_consumers": parasite_consumers,
            "legacy_stage60_compatibility": legacy_save,
            "sector31_transaction_owner": transaction_owner,
            "mgba_process_restart_gate": process_restart_gate,
            "stage61_custom_compatibility": custom_save_compatibility,
        },
        "ram_addressing": ram,
        "global_expanded_hooks": hook,
        "raid_binary": {**raid, "stage61_installation": stage61_raid},
        "usage_universe": {
            "start": FLAG_UNIVERSE_START,
            "start_hex": _hex(FLAG_UNIVERSE_START),
            "end_inclusive": FLAG_UNIVERSE_END_EXCLUSIVE - 1,
            "end_inclusive_hex": _hex(FLAG_UNIVERSE_END_EXCLUSIVE - 1),
            "count": FLAG_UNIVERSE_END_EXCLUSIVE - FLAG_UNIVERSE_START,
            "sources": {
                name: _source_summary(ids) for name, ids in sorted(source_ids.items())
            },
            "union": _source_summary(used),
            "free_runs": free_runs,
            "aligned_109_flag_windows": aligned_windows,
        },
        "evidence": {
            "stage60_event_operands": event,
            "stage60_object_visibility": visibility,
            "project_flag_manifest": manifest,
            "stage60_trainer_bindings": bindings,
            "stage61_namespace_registry": registry,
        },
        "collision_findings": {
            "current_raid_vs_project": {
                "status": "REJECTED_COLLISION",
                "range_start": OLD_RAID_START,
                "range_end_exclusive": OLD_RAID_END_EXCLUSIVE,
                "collisions": old_collisions,
            },
            "requested_0x1500_candidate": {
                "status": "REJECTED_FULL_COLLISION",
                "range_start": REQUESTED_RAID_START,
                "range_end_exclusive": REQUESTED_RAID_END_EXCLUSIVE,
                "collisions": requested_collisions,
                "conclusion": "0x1500..0x156C は exact Stage60 KANTO_NEW 109 flags と全域衝突する",
            },
            "recommended_0x15c0_candidate": {
                "status": "STATICALLY_FREE_REQUIRES_HOOK_REPAIR",
                **aligned_by_start[RECOMMENDED_RAID_START],
                "collisions": [],
                "alignment_guard_before": {
                    "start": 0x15BC,
                    "end_inclusive": 0x15BF,
                    "count": 4,
                },
                "selection_basis": [
                    "exact Stage60 KANTO_NEW maximum 0x15BB の直後",
                    "既存 imm8<<5 code shape で全6 base sitesを2-byte in-place patch可能",
                    "manifest/event/object/binding/CFRU config/Stage61 registry のunionと非衝突",
                    "Stage61 0x1800 namespaceとの間に十分な隔離を保持",
                ],
            },
        },
        "repair_plan": {
            "status": "READY_AFTER_PREREQUISITES",
            "mandatory_order": [
                "expanded_var_pointer_global_hook",
                "expanded_flag_pointer_global_hook",
                "stock-layout compatible Stage61 S61E record wrapper",
                "mGBA separate-process expanded/stock persistence probe",
                "FIRST_RAID_BATTLE_FLAG source owner update",
                "nine exact Raid binary patches",
                "Stage61 full validation",
            ],
            "hook_patches": hook_patch_plan(),
            "active_stage61_save_compatibility_patches": (
                custom_save_compatibility["active_exact_patches"]
            ),
            "rejected_cfru_direct_patches": save_expansion_patch_plan(),
            "raid_patches": patch_rows,
            "raid_target": aligned_by_start[RECOMMENDED_RAID_START],
            "source_change": raid_source["required_source_change"],
            "derived_rom_sha256": {
                "raid_only_forbidden_without_hooks": _sha(raid_only),
                "hooks_only_probe_candidate": _sha(hooks_only),
                "save_only_forbidden_without_global_hooks_or_migration": _sha(save_only),
                "hooks_and_save_requires_legacy_migration": _sha(hooks_and_save),
                "hooks_save_and_raid_requires_legacy_migration": _sha(hooks_save_and_raid),
            },
            "prohibitions": [
                "0x1500..0x156C をRaidへ割り当てない",
                "global expanded Flag/Var hook未接続のまま高IDを有効化しない",
                "旧Stage60 save migrationなしにCFRU gSaveSectionOffsetsへ切り替えない",
                "SaveWriteToFlash/HandleSavingDataをsector31 transaction調停なしに接続しない",
                "source constantを0x1800のままbinaryだけ恒久patchしない",
            ],
        },
        "assertions": {
            "stage60_identity_exact": True,
            "cfru_source_identity_exact": True,
            "raid_source_expression_count_is_five": raid_source["consumer_expression_total"] == 5,
            "raid_binary_consumer_count_is_six": raid["binary_consumer_count"] == 6,
            "raid_patch_site_count_is_nine": raid["patch_site_count"] == 9,
            "raid_relocation_is_installed_in_stage61": (
                stage61_raid["status"] == "INSTALLED_EXACT"
                and stage61_raid["patch_count"] == 9
            ),
            "requested_0x1500_collision_is_all_109": (
                event_requested["count"] == RAID_FLAG_COUNT
                and binding_requested["count"] == RAID_FLAG_COUNT
            ),
            "recommended_0x15c0_is_free": not recommended_collisions,
            "recommended_0x15c0_is_movs_encodable": RECOMMENDED_RAID_START % 0x20 == 0,
            "expanded_flag_hook_is_currently_missing": hook["status"] == "CRITICAL_UNCONNECTED",
            "all_six_cfru_core_save_entries_are_cataloged": (
                len(save_expansion["stage60_core_entries"]) == 6
            ),
            "cfru_direct_save_patch_candidate_is_seven_sites": (
                save_expansion["recommended_patch_count"] == 7
            ),
            "parasite_fragment_total_is_0xec4": (
                sum(
                    row["size"]
                    for row in parasite_owners["parasite_fragments"]
                ) == SAVE_PARASITE_SIZE
            ),
            "last_used_ball_is_connected_and_requires_persistence": (
                parasite_consumers["last_used_ball"]["required_in_custom_record"]
                is True
                and parasite_consumers["feature_hook_evidence"][
                    "last_used_ball"
                ]["canonical_connected_count"] == 1
            ),
            "other_cfru_field_state_clusters_are_unconnected": all(
                parasite_consumers["feature_hook_evidence"][name][
                    "canonical_connected_count"
                ] == 0
                for name in (
                    "keypad",
                    "dynamic_overworld_palettes",
                    "followers",
                    "updated_repel",
                    "expanded_bag",
                    "expanded_coins",
                    "wild_encounter_roamer_paths",
                    "roamers",
                    "pedometers",
                )
            ),
            "full_expanded_bag_does_not_fit_stock_tails": (
                parasite_consumers["expanded_bag"][
                    "fits_stock_main_save_tails"
                ] is False
            ),
            "stage61_roamer_inner_adapter_has_no_live_root": (
                parasite_consumers["stage61_roamer_context_adapter"][
                    "persistent_owner_live"
                ] is False
                and len(
                    parasite_consumers["stage61_roamer_context_adapter"][
                        "caller_roots"
                    ]
                ) == 2
            ),
            "follower_noncanonical_paths_are_read_only": (
                parasite_consumers["noncanonical_state_paths"][
                    "gFollowerState"
                ]["read_root_count"] == 5
                and parasite_consumers["noncanonical_state_paths"][
                    "gFollowerState"
                ]["connected_writer_count"] == 0
            ),
            "roamer_special_paths_are_absent_from_event_universe": (
                parasite_consumers["noncanonical_state_paths"]["gRoamers"][
                    "absent_special_ids"
                ] == [0x97, 0x98, 0x129]
                and parasite_consumers["noncanonical_state_paths"]["gRoamers"][
                    "persistent_owner_live"
                ] is False
            ),
            "sector30_31_geometry_matches_existing_owners": (
                parasite_owners["geometry_compatible"] is True
            ),
            "full_upstream_save_orchestration_is_transaction_unsafe": (
                transaction_owner["full_upstream_save_write_compatible"] is False
            ),
            "stage60_legacy_save_requires_dual_layout_migration": (
                legacy_save["status"] == "LEGACY_SAVE_MIGRATION_REQUIRED"
                and legacy_save["linked_layout_valid"] is False
            ),
            "stage61_custom_plan_retains_stock_layout": (
                custom_save_compatibility["stock_layout_retained"] is True
                and custom_save_compatibility["legacy_exact_save"][
                    "record_magic_present"
                ] is False
            ),
            "stage61_custom_record_is_exact_0x616": (
                custom_save_compatibility["record"]["record_size"] == 0x616
                and sum(
                    row["length"]
                    for row in custom_save_compatibility["record"]["segments"]
                ) == 0x616
            ),
            "separate_process_restart_gate_is_defined": (
                process_restart_gate["status"]
                == "DEFINED_FAIL_CLOSED_PENDING_RUNTIME_PASS"
            ),
            "expanded_storage_is_adjacent_not_overlapping": (
                ram["expanded_flag_formula"]["end_exclusive"]
                == ram["expanded_var_formula"]["start"]
            ),
        },
    }
    if not all(report["assertions"].values()):
        _fail(
            "top-level assertions failed: "
            + repr(sorted(k for k, value in report["assertions"].items() if not value))
        )
    if run_mgba:
        report["mgba_probe"] = run_mgba_flag_probe(root)
    return report


def _stage61_installed_artifact_binding(root: Path) -> dict[str, Any]:
    """可変SHAをbuild config→metadata→embedded audit→ROMで結合する。"""

    config, config_identity = _load_stage61_build_configuration(root)
    metadata_raw = (root / STAGE61_METADATA_RELATIVE).read_bytes()
    generated_raw = (root / STAGE61_AUDIT_RELATIVE).read_bytes()
    rom = (root / STAGE61_ROM_RELATIVE).read_bytes()
    metadata = json.loads(metadata_raw)
    generated = json.loads(generated_raw)
    outputs = config.get("outputs")
    inputs = config.get("inputs")
    if not isinstance(outputs, Mapping) or not isinstance(inputs, Mapping):
        _fail("Stage61 build config artifact maps missing")
    expected_outputs = {
        "rom": str(STAGE61_ROM_RELATIVE),
        "metadata": str(STAGE61_METADATA_RELATIVE),
        "audit": str(STAGE61_AUDIT_RELATIVE),
    }
    for key, expected in expected_outputs.items():
        if outputs.get(key) != expected:
            _fail(f"Stage61 build output path differs: {key}")
    stage60_declaration = inputs.get("stage60_rom")
    if not isinstance(stage60_declaration, Mapping):
        _fail("Stage61 build Stage60 input declaration missing")
    identity = (
        config.get("schema_version"),
        config.get("stage"),
        config.get("task"),
    )
    if identity != (
        metadata.get("schema_version"),
        metadata.get("stage"),
        metadata.get("task"),
    ) or identity != (
        generated.get("schema_version"),
        generated.get("stage"),
        generated.get("task"),
    ):
        _fail("Stage61 config/metadata/audit identity differs")
    if metadata.get("status") != "PASS" or generated.get("status") != "PASS":
        _fail("Stage61 metadata/audit status is not PASS")
    if metadata.get("input") != {
        "path": stage60_declaration.get("path"),
        "sha256": stage60_declaration.get("sha256"),
        "size": stage60_declaration.get("size"),
    }:
        _fail("Stage61 metadata input differs from build config")
    output = metadata.get("output")
    if not isinstance(output, Mapping) or (
        output.get("path"), output.get("size"), output.get("sha256")
    ) != (str(STAGE61_ROM_RELATIVE), len(rom), _sha(rom)):
        _fail("Stage61 final ROM differs from metadata")
    if generated.get("rom_sha256") != _sha(rom):
        _fail("Stage61 generated audit ROM SHA differs from metadata/ROM")
    if metadata.get("audit") != generated:
        _fail("Stage61 metadata embedded audit differs from standalone audit")
    return {
        "status": "CONFIG_METADATA_AUDIT_ROM_EXACT",
        "task": str(metadata["task"]),
        "build_config": config_identity,
        "metadata": {
            "path": str(STAGE61_METADATA_RELATIVE),
            "size": len(metadata_raw),
            "sha256": _sha(metadata_raw),
        },
        "generated_audit": {
            "path": str(STAGE61_AUDIT_RELATIVE),
            "size": len(generated_raw),
            "sha256": _sha(generated_raw),
            "embedded_in_metadata_exactly": True,
        },
        "stage61_rom": {
            "path": str(STAGE61_ROM_RELATIVE),
            "size": len(rom),
            "sha256": _sha(rom),
        },
        "input_stage60": dict(metadata["input"]),
    }


def _stage61_installed_declaration_contract(
    root: Path,
    custom_save: Mapping[str, Any],
    raid: Mapping[str, Any],
) -> dict[str, Any]:
    """全persistent-state宣言26件と最終ROM postimageをexact検証する。"""

    rom = (root / STAGE61_ROM_RELATIVE).read_bytes()
    generated = json.loads(
        (root / STAGE61_AUDIT_RELATIVE).read_text(encoding="utf-8")
    )
    declaration_rows = [
        row for row in generated.get("change_audit", {}).get("declarations", [])
        if str(row.get("category", "")).startswith("PERSISTENT_STATE_")
    ]
    names = [str(row.get("name")) for row in declaration_rows]
    if len(names) != 26 or len(set(names)) != 26:
        _fail(f"Stage61 persistent declaration count differs: {len(names)}")
    combined_names = {
        str(row["name"]) for row in custom_save.get("active_exact_patches", [])
    } | {
        str(row["name"])
        for row in list(raid.get("patches", []))
        + list(raid.get("api_guard_patches", []))
    }
    # Raid base patch plan names describe semantic consumers; generated
    # declarations deliberately identify the exact ROM addresses instead.
    raid_generated_names = {
        f"cfru_raid_flag_namespace::0x{int(row['address']):08x}"
        for row in raid.get("patches", [])
    } | {
        str(row["name"]) for row in raid.get("api_guard_patches", [])
    }
    custom_names = {
        str(row["name"]) for row in custom_save.get("active_exact_patches", [])
    }
    expected_names = custom_names | raid_generated_names
    if set(names) != expected_names or len(expected_names) != 26:
        _fail(
            "Stage61 persistent declaration owner set differs: "
            f"missing={sorted(expected_names - set(names))}, "
            f"unexpected={sorted(set(names) - expected_names)}"
        )
    # Keep this temporary set calculation visible in the report construction
    # above without accepting consumer aliases as declaration identities.
    if len(combined_names) != 26:
        _fail("Stage61 custom/Raid exact patch union count differs")

    spans: list[tuple[int, int, str]] = []
    installed: list[dict[str, Any]] = []
    categories = Counter()
    for row in declaration_rows:
        name = str(row["name"])
        start = int(row["start"])
        end = int(row["end_exclusive"])
        expected_hex = row.get("expected_hex")
        replacement_hex = row.get("replacement_hex")
        if (
            not isinstance(expected_hex, str)
            or not isinstance(replacement_hex, str)
            or len(bytes.fromhex(expected_hex)) != end - start
            or len(bytes.fromhex(replacement_hex)) != end - start
        ):
            _fail(f"Stage61 persistent declaration byte geometry differs: {name}")
        address = ROM_BASE + start
        _require_rom_bytes(
            rom, address, bytes.fromhex(replacement_hex), f"installed {name}"
        )
        spans.append((address, ROM_BASE + end, name))
        categories[str(row["category"])] += 1
        installed.append(
            {
                "name": name,
                "category": str(row["category"]),
                "address": address,
                "address_hex": _hex(address, 8),
                "size": end - start,
                "expected_hex": expected_hex,
                "replacement_hex": replacement_hex,
                "postimage_exact": True,
            }
        )
    spans.sort()
    for previous, current in zip(spans, spans[1:]):
        if current[0] < previous[1]:
            _fail(
                "Stage61 persistent declarations overlap: "
                f"{previous[2]} and {current[2]}"
            )
    expected_categories = Counter(
        {
            "PERSISTENT_STATE_SAVE_COMPATIBILITY": 7,
            "PERSISTENT_STATE_SAVE_LIFECYCLE": 3,
            "PERSISTENT_STATE_NAMESPACE_HOOK": 2,
            "PERSISTENT_STATE_RAID_FLAG_NAMESPACE": 9,
            "PERSISTENT_STATE_RAID_FLAG_API_GUARD": 5,
        }
    )
    if categories != expected_categories:
        _fail(f"Stage61 persistent declaration categories differ: {categories}")

    by_name = {row["name"]: row for row in installed}
    for expected in hook_patch_plan():
        actual = by_name.get(str(expected["name"]))
        if actual is None or (
            actual["address"], actual["expected_hex"], actual["replacement_hex"]
        ) != (
            int(expected["address"]),
            str(expected["expected_hex"]),
            str(expected["replacement_hex"]),
        ):
            _fail(f"Stage61 installed global hook declaration differs: {expected['name']}")
    return {
        "status": "ALL_26_POSTIMAGES_EXACT_NON_OVERLAPPING",
        "declaration_count": len(installed),
        "category_counts": dict(sorted(categories.items())),
        "all_postimages_exact": True,
        "all_spans_non_overlapping": True,
        "global_hook_names": [row["name"] for row in hook_patch_plan()],
        "declarations": installed,
    }


def _stage61_installed_s61e_contract(
    layout: Mapping[str, Any],
    custom_save: Mapping[str, Any],
) -> dict[str, Any]:
    """RAM/save owner 4件がS61E recordへ欠落なくcompact化されることを証明する。"""

    record = custom_save.get("record")
    if not isinstance(record, Mapping):
        _fail("Stage61 installed S61E record missing")
    payload = record.get("payload")
    expected_payload = [
        {"owner": "expanded_flags", "size": 0x200},
        {"owner": "expanded_vars", "size": 0x400},
        {"owner": "gLastUsedBall", "size": 2},
        {"owner": "cfru_player_coins_u32", "size": 4},
    ]
    if payload != expected_payload:
        _fail("Stage61 installed S61E payload owner order differs")
    crosswalk = layout.get("ram_save_affine_crosswalk")
    if not isinstance(crosswalk, list) or len(crosswalk) != 4:
        _fail("Stage61 RAM/save owner crosswalk differs")
    expected_sizes = [0x200, 0x400, 2, 4]
    if [int(row["size"]) for row in crosswalk] != expected_sizes:
        _fail("Stage61 S61E crosswalk sizes differ")
    compact: list[dict[str, Any]] = []
    cursor = 0
    for owner, cross in zip(expected_payload, crosswalk):
        size = int(owner["size"])
        compact.append(
            {
                "owner": owner["owner"],
                "payload_offset_start": cursor,
                "payload_offset_end_exclusive": cursor + size,
                "record_offset_start": 0x10 + cursor,
                "record_offset_end_exclusive": 0x10 + cursor + size,
                "size": size,
                "ram_start": int(cross["ram_start"]),
                "ram_end_exclusive": int(cross["ram_end_exclusive"]),
            }
        )
        cursor += size
    segments = record.get("segments")
    if (
        (record.get("magic"), record.get("version"), record.get("header_size"))
            != (0x45313653, 1, 0x10)
        or (record.get("payload_size"), cursor) != (0x606, 0x606)
        or record.get("record_size") != 0x616
        or segments != [
            {
                "section_id": 13,
                "chunk_size": 0x7D0,
                "record_start": 0,
                "length": 0x616,
            }
        ]
        or 0x7D0 + 0x616 > SAVE_SECTOR_DATA_SIZE
    ):
        _fail("Stage61 installed S61E record/tail geometry differs")
    return {
        "status": "EXACT_COMPLETE_COMPACT_SERIALIZATION",
        "magic": "S61E",
        "version": 1,
        "header_size": 0x10,
        "payload_size": 0x606,
        "record_size": 0x616,
        "record_bearing_logical_chunk": 13,
        "stock_chunk_size": 0x7D0,
        "record_end_exclusive": 0x7D0 + 0x616,
        "sector_data_end_exclusive": SAVE_SECTOR_DATA_SIZE,
        "remaining_checksum_excluded_tail": SAVE_SECTOR_DATA_SIZE - 0x7D0 - 0x616,
        "compact_payload": compact,
        "all_four_layout_owners_serialized_once": True,
    }


def _stage61_installed_raid_namespace_contract(
    stage60_audit: Mapping[str, Any],
    raid: Mapping[str, Any],
) -> dict[str, Any]:
    """Raid自ownerを除く全既知namespaceと15C0..162Cの非衝突を再計算する。"""

    sources = stage60_audit.get("usage_universe", {}).get("sources")
    if not isinstance(sources, Mapping):
        _fail("Stage60 namespace usage sources missing")
    source_ids: dict[str, set[int]] = {}
    for name, summary in sources.items():
        if name == "current_cfru_raid_completion":
            continue
        if not isinstance(summary, Mapping) or not isinstance(summary.get("ids"), list):
            _fail(f"Stage60 namespace source summary differs: {name}")
        source_ids[str(name)] = {int(value) for value in summary["ids"]}
    collisions = _collision_rows(
        RECOMMENDED_RAID_START,
        RECOMMENDED_RAID_END_EXCLUSIVE,
        source_ids,
    )
    registry = stage60_audit.get("evidence", {}).get("stage61_namespace_registry")
    if not isinstance(registry, Mapping):
        _fail("Stage61 namespace registry evidence missing")
    expected_ids = list(range(RECOMMENDED_RAID_START, RECOMMENDED_RAID_END_EXCLUSIVE))
    if registry.get("raid_owner_ids") != expected_ids:
        _fail("Stage61 Raid registry exact ID set differs")
    if collisions:
        _fail(f"Stage61 installed Raid range collides: {collisions}")
    if (
        raid.get("status") != "INSTALLED_EXACT"
        or raid.get("target_start") != RECOMMENDED_RAID_START
        or raid.get("target_end_exclusive") != RECOMMENDED_RAID_END_EXCLUSIVE
        or raid.get("patch_count") != 9
        or raid.get("api_guard_patch_count") != 5
    ):
        _fail("Stage61 Raid installed binary contract differs")
    return {
        "status": "INSTALLED_EXACT_NON_COLLIDING",
        "start": RECOMMENDED_RAID_START,
        "start_hex": _hex(RECOMMENDED_RAID_START),
        "end_inclusive": RECOMMENDED_RAID_END_EXCLUSIVE - 1,
        "end_inclusive_hex": _hex(RECOMMENDED_RAID_END_EXCLUSIVE - 1),
        "count": RAID_FLAG_COUNT,
        "registry_owner": dict(registry["raid_owner"]),
        "competing_source_count": len(source_ids),
        "competing_sources": {
            name: _source_summary(ids) for name, ids in sorted(source_ids.items())
        },
        "collisions": [],
        "binary_base_end_patch_count": 9,
        "bounded_api_guard_count": 5,
    }


def _build_stage61_installed_state_namespace_audit(
    root: Path,
    stage60_audit: Mapping[str, Any],
) -> dict[str, Any]:
    """検証済みStage60監査を土台に最終Stage61 READY reportを構成する。"""

    if (
        stage60_audit.get("audit_status") != "PASS"
        or not isinstance(stage60_audit.get("assertions"), Mapping)
        or not all(stage60_audit["assertions"].values())
    ):
        _fail("Stage60 prerequisite audit is not internally PASS")
    artifact = _stage61_installed_artifact_binding(root)
    layout = _stage61_layout_ownership_contract(root)
    custom_save = stage60_audit.get("save_storage", {}).get(
        "stage61_custom_compatibility"
    )
    raid = stage60_audit.get("raid_binary", {}).get("stage61_installation")
    if not isinstance(custom_save, Mapping) or not isinstance(raid, Mapping):
        _fail("Stage61 installed custom save/Raid prerequisites missing")
    declarations = _stage61_installed_declaration_contract(
        root, custom_save, raid
    )
    record = _stage61_installed_s61e_contract(layout, custom_save)
    raid_namespace = _stage61_installed_raid_namespace_contract(
        stage60_audit, raid
    )
    assertions = {
        "artifact_chain_config_metadata_audit_rom_exact": (
            artifact["status"] == "CONFIG_METADATA_AUDIT_ROM_EXACT"
        ),
        "all_live_ram_and_save_ranges_non_overlapping": (
            layout["status"] == "EXACT_NON_OVERLAPPING"
            and layout["ram_layout"]["all_live_ranges_non_overlapping"] is True
            and layout["save_layout"]["all_live_ranges_non_overlapping"] is True
        ),
        "expanded_flags_vars_last_ball_coins_exact_crosswalk": (
            len(layout["ram_save_affine_crosswalk"]) == 4
        ),
        "all_persistent_declarations_have_exact_postimages": (
            declarations["declaration_count"] == 26
            and declarations["all_postimages_exact"] is True
            and declarations["all_spans_non_overlapping"] is True
        ),
        "global_expanded_flag_var_hooks_installed_exact": (
            declarations["global_hook_names"]
            == [row["name"] for row in hook_patch_plan()]
        ),
        "stock_compatible_s61e_record_serializes_all_four_owners": (
            record["record_size"] == 0x616
            and record["all_four_layout_owners_serialized_once"] is True
        ),
        "normal_save_cow_source_object_metadata_exact": (
            custom_save["normal_save_copy_on_write"]["source"]["status"]
                == "SOURCE_CONTROL_FLOW_EXACT"
            and custom_save["normal_save_copy_on_write"]["object"]["status"]
                == "OBJECT_DISPATCH_AND_LITERAL_CLOSURE_EXACT"
            and custom_save["normal_save_copy_on_write"]["metadata"]["status"]
                == "METADATA_EXACT"
        ),
        "raid_15c0_162c_installed_and_noncolliding": (
            raid_namespace["status"] == "INSTALLED_EXACT_NON_COLLIDING"
            and raid_namespace["collisions"] == []
            and raid_namespace["count"] == 109
        ),
    }
    if not all(assertions.values()):
        _fail(
            "Stage61 installed assertions failed: "
            + repr(sorted(name for name, value in assertions.items() if not value))
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "task": artifact["task"],
        "mode": "STAGE61_INSTALLED_CANDIDATE",
        "audit_status": "PASS",
        "status": "READY",
        "artifact_binding": artifact,
        "layout_ownership": layout,
        "installed_declarations": declarations,
        "s61e_record": record,
        "raid_namespace": raid_namespace,
        "assertions": assertions,
    }


def build_stage61_installed_state_namespace_audit(
    root: Path = ROOT,
) -> dict[str, Any]:
    """最終Stage61 ROMのstate/RAM/save namespace READY監査を返す。"""

    root = root.resolve()
    stage60_audit = build_stage61_state_namespace_collision_audit(root)
    return _build_stage61_installed_state_namespace_audit(root, stage60_audit)


def require_ready(report: Mapping[str, Any]) -> None:
    """READY/PASSかつ全assertion成立だけを受理するfail-closed gate。"""

    assertions = report.get("assertions")
    if (
        report.get("status") != "READY"
        or report.get("audit_status") != "PASS"
        or not isinstance(assertions, Mapping)
        or not assertions
        or not all(value is True for value in assertions.values())
    ):
        raise StateNamespaceCollisionAuditError(
            "expanded state is not READY/PASS with all assertions true"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--mgba", action="store_true", help="実libmGBA read/write probeを実行")
    parser.add_argument(
        "--installed-candidate",
        action="store_true",
        help="最終Stage61 ROMのRAM/save/Flag namespace READY監査を実行",
    )
    parser.add_argument("--output", type=Path, help="明示された場合だけJSONを書き出す")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="READY/PASSかつ全assertion成立でなければ非zero終了する",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.installed_candidate:
            if args.mgba:
                _fail(
                    "--mgba is the Stage60 temporary-hook probe; "
                    "do not combine it with --installed-candidate"
                )
            report = build_stage61_installed_state_namespace_audit(args.root)
        else:
            report = build_stage61_state_namespace_collision_audit(
                args.root, run_mgba=args.mgba
            )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(_stable_json(report), encoding="utf-8", newline="\n")
        print(_stable_json(report), end="")
        if args.require_ready:
            require_ready(report)
    except StateNamespaceCollisionAuditError as exc:
        print(f"stage61-state-namespace-collision-audit: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
