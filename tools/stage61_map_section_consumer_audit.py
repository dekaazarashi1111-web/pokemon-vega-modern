#!/usr/bin/env python3
"""Stage 61 の project map-section ID (0..52) consumer を監査する。

FireRed の map-section は Kanto=88..142、Stage 60 の既存 Vega 名前空間は
88..196 である。一方、Stage 61 の imported Kanto map header は project 固有の
0..52 を保持する。本モジュールは、次の三つを混同せずに fail-closed で検査する。

* ``mapsec - 88`` 型の stock table index（境界外参照の可能性）
* stock ID との線形一致・定数比較（安全だが意味が欠落する可能性）
* 保存データの 0..52 と Hoenn met-location 0..52 の文脈衝突

監査根拠は pinned decomp、clean FireRed 日本版 Rev.0、Stage 60 の exact SHA、
Thumb BL 逆参照、``gMapHeader+0x14`` の literal load、固定 preimage である。
既存 Stage 61 ROM は並行作業で変化し得るため、candidate は SHA を固定せず、各
site が Stage 60 preimage のままか否かだけを観測する。
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any, Iterable, Mapping, Sequence


ROM_BASE = 0x08000000
G_MAP_HEADER = 0x02036D30
MAP_HEADER_SECTION_OFFSET = 0x14

CLEAN_ROM_RELATIVE = Path("build/reference/FireRed_JPN_Rev0_clean.gba")
STAGE60_ROM_RELATIVE = Path("build/stages/60_wild_species_root_repair.gba")
CANDIDATE_ROM_RELATIVE = Path("build/stages/61_display_npc_event_audit.gba")
DECOMP_RELATIVE = Path("vendor/upstream/pokefirered")
CFRU_RELATIVE = Path("vendor/upstream/CFRU-JP")
DPE_RELATIVE = Path("vendor/upstream/DPE-JP")
CFRU_PROFILE_RELATIVE = Path("config/cfru_vega_minimal.h")
MAP_SECTION_MANIFEST_RELATIVE = Path("content/kanto_map_sections.csv")

CLEAN_ROM_SIZE = 16 * 1024 * 1024
STAGE60_ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE60_ROM_SHA256 = "3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1"
DECOMP_COMMIT = "c75f352304d529f6ba92d4f74b9cf8b5c3810788"
CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
DPE_COMMIT = "10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e"
CFRU_PROFILE_SHA256 = "cbf61ee395af2f61103c29c0bea4b6cddc15499a1e4c1706f2b1f72afeafe4f2"
MAP_SECTION_MANIFEST_SHA256 = (
    "1e548de2712821c041f4b20d432ecd23cfd5d08aeece009a7a4baad68f42de05"
)

PROJECT_SECTION_COUNT = 53
PROJECT_SECTION_IDS = tuple(range(PROJECT_SECTION_COUNT))
SOURCE_SECTION_IDS = tuple(range(88, 99)) + tuple(range(101, 143))


class MapSectionConsumerAuditError(RuntimeError):
    """入力 identity、preimage、逆参照集合のいずれかを証明できない。"""


@dataclass(frozen=True)
class RomSite:
    name: str
    address: int
    expected: bytes
    role: str
    disposition: str

    def to_report(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "address": f"0x{self.address:08X}",
            "size": len(self.expected),
            "expected_hex": self.expected.hex(),
            "role": self.role,
            "disposition": self.disposition,
        }


@dataclass(frozen=True)
class Consumer:
    consumer_id: str
    domain: str
    source_functions: tuple[str, ...]
    input_path: str
    access_kind: str
    status: str
    severity: str
    effect: str
    required_action: str
    rom_sites: tuple[str, ...] = ()

    def to_report(self) -> dict[str, Any]:
        return asdict(self)


# 選択済み Stage 61 hooks。これらは Stage 60 の exact preimage を置換する。
COVERED_BOUNDARY_SITES: tuple[RomSite, ...] = (
    RomSite(
        "region_map_gfx_decompress",
        0x080C14F2,
        bytes.fromhex("36f0edf9"),
        "Town Map Kanto graphics payload selection",
        "COVERED_STAGE61",
    ),
    RomSite(
        "region_map_tilemap_decompress",
        0x080C153A,
        bytes.fromhex("06f1a9fa"),
        "Town Map Kanto tilemap payload selection",
        "COVERED_STAGE61",
    ),
    RomSite(
        "dungeon_name_resolver",
        0x080C1DCE,
        bytes.fromhex(
            "041c583c2404240c0120002104f051f8286822494018012101802348a40024182468"
        ),
        "Town Map small dungeon-name window; replaces mapsec-88 table index",
        "COVERED_STAGE61",
    ),
    RomSite(
        "get_mapsec_type",
        0x080C47C0,
        bytes.fromhex("00b50006000e5838"),
        "Town Map city/route type and visit flag",
        "COVERED_STAGE61",
    ),
    RomSite(
        "get_dungeon_mapsec_type",
        0x080C4A5C,
        bytes.fromhex("00b50006000e7e38"),
        "Town Map dungeon type and visit flag",
        "COVERED_STAGE61",
    ),
    RomSite(
        "get_player_position_on_region_map_overrides",
        0x080C4F24,
        bytes.fromhex("30b5fff7ddfe0004"),
        "Town Map player position; bypasses selectedMapsec-88 indexing",
        "COVERED_STAGE61",
    ),
    RomSite(
        "get_selected_map_section",
        0x080C5348,
        bytes.fromhex("30b50006000e051c"),
        "Town Map project grid lookup",
        "COVERED_STAGE61",
    ),
    RomSite(
        "get_map_name",
        0x080C5F5C,
        bytes.fromhex("70b5061c09041204"),
        "popup/menu/Quest Log name; replaces mapsec-88 name-table index",
        "COVERED_STAGE61",
    ),
    RomSite(
        "set_fly_warp_destination",
        0x080C6460,
        bytes.fromhex("30b5000408494018"),
        "Fly destination; replaces mapsec-88 destination-table index",
        "COVERED_STAGE61",
    ),
)


# Stage 60 で stock のまま残る意味 consumer。いずれも preimage は clean と同じ。
UNRESOLVED_SEMANTIC_SITES: tuple[RomSite, ...] = (
    RomSite(
        "music_override_guard",
        0x080559E4,
        bytes.fromhex(
            "00b50004010c8d204000814202d0173081420bd10448007d842803d07b2801d0612803d1002002e0306d0302012002bc0847"
        ),
        "cycling/surf music guard compares section against 132/123/97",
        "ACTION_REQUIRED",
    ),
    RomSite(
        "pokemon_summary_mapsec_classifier",
        0x0813BFFC,
        bytes.fromhex("00b50006a82109064018000e6c2801d9002000e0012002bc"),
        "trainer memo accepts only unsigned range 88..196",
        "ACTION_REQUIRED_CONTEXTUAL",
    ),
    RomSite(
        "pokedex_species_area",
        0x0813D120,
        bytes.fromhex(
            "f0b557464e464546e0b489b004910004000c039000f0a0f8002804db03980499"
        ),
        "wild header map-section to Pokédex area marker",
        "ACTION_REQUIRED",
    ),
    RomSite(
        "pokedex_roamer_area",
        0x0813D2A0,
        bytes.fromhex(
            "30b583b00d1c0004000cfff7e5ff041c002c29db1248a40024188ff741fe6188"
        ),
        "roamer map-section to Pokédex area marker",
        "DORMANT_RISK",
    ),
    RomSite(
        "pokedex_wild_header_mapsec",
        0x0813D388,
        bytes.fromhex("00b502784178101c17f7b2fb007d02bc08470000"),
        "loads MapHeader.regionMapSectionId from a wild header",
        "ACTION_REQUIRED",
    ),
    RomSite(
        "pokedex_linear_mapsec_lookup",
        0x0813D39C,
        bytes.fromhex(
            "70b5141c049e0004050c1a68a2420eda900041180888a84205d148883080501c"
        ),
        "linear MAPSEC->DEX_AREA equality lookup (not an arithmetic index)",
        "ACTION_REQUIRED_SAFE_MEMORY",
    ),
    RomSite(
        "map_preview_index",
        0x080F9150,
        bytes.fromhex(
            "00b50006030e0021034a1078984205d10806000e07e000008c264008103201311b29f2d91c2002bc0847"
        ),
        "linear preview-table equality lookup",
        "ACTION_REQUIRED_SAFE_MEMORY",
    ),
    RomSite(
        "dungeon_preview_info",
        0x080F95B0,
        bytes.fromhex(
            "00b50006000efff7cbfd0006000e1c2806d000010149401803e000008c264008002002bc0847"
        ),
        "Town Map/field dungeon preview lookup",
        "ACTION_REQUIRED_SAFE_MEMORY",
    ),
    RomSite(
        "map_preview_duration",
        0x080F95D8,
        bytes.fromhex(
            "00b50006000efff7b7fd0006010e1c2901d1002019e00748090109184a884878002809d1101c74f761fc000600280bd006e000008c26400802480078002803d1282002e064ab0302782002bc"
        ),
        "preview first-visit duration lookup",
        "ACTION_REQUIRED_SAFE_MEMORY",
    ),
    RomSite(
        "quest_log_gym_section_compare",
        0x08115DC2,
        bytes.fromhex("00240e4aaf1c2978a018007881421cd182210901601858f7"),
        "departed-gym narration compares record against stock city table",
        "ACTION_REQUIRED",
    ),
    RomSite(
        "quest_log_gym_section_table",
        0x084170AF,
        bytes.fromhex("5a5b5d5e5f626059"),
        "Pewter/Cerulean/Vermilion/Celadon/Fuchsia/Saffron/Cinnabar/Viridian",
        "ACTION_REQUIRED",
    ),
    RomSite(
        "quest_log_teleport_home_compare",
        0x08115F60,
        bytes.fromhex("072813d1687858280cd104480449f2f6c7fc0be0"),
        "Teleport destination compares Pallet against stock section 88",
        "ACTION_REQUIRED",
    ),
    RomSite(
        "roamer_location_mapsec",
        0x08142768,
        bytes.fromhex(
            "00b50748006807494018c07c00280dd005490878497812f7bbf9007d07e0000048500003d030000022f30302c52002bc0847"
        ),
        "active roamer group/map to MapHeader.regionMapSectionId",
        "DORMANT_RISK",
    ),
)


# Stage 60 で実リンクされたCFRU-JP側のconsumer。clean 16 MiB ROMには存在しない。
# Raidの6か所はstatic GetRaidMapSectionIdがinline化されているため、各減算/index
# preimageを個別に固定する。roamerは同じstock座標表へ ``mapsec - 88`` で入る。
STAGE60_EXPANDED_SITES: tuple[RomSite, ...] = (
    RomSite(
        "cfru_raid_determine_species_index",
        0x090F371C,
        bytes.fromhex("573c2006030e440de41a64194a4ee400a559002d58d03619"),
        "DetermineRaidSpecies: u8(mapsec-87) -> gRaidsByMapSection row",
        "ACTION_REQUIRED_OOB",
    ),
    RomSite(
        "cfru_raid_ability_index",
        0x090F3A20,
        bytes.fromhex(
            "70b50400194b1d78194b00f0e7fa194ae3019b18190057380006000e803102e008338b42"
        ),
        "GetRaidSpeciesAbilityNum: u8(mapsec-87) then raid-table lookup",
        "ACTION_REQUIRED_OOB",
    ),
    RomSite(
        "cfru_raid_done_flag_index",
        0x090F3AC8,
        bytes.fromhex(
            "10b5074b00f096fac0235b059c4657380006000a6044034b000c00f08bfa10bd215b0508c5de0608"
        ),
        "HasRaidBattleAlreadyBeenDone: FIRST_RAID_BATTLE_FLAG + u8(mapsec-87)",
        "ACTION_REQUIRED_FLAG_ALIAS",
    ),
    RomSite(
        "cfru_raid_set_flag_index",
        0x090F3AF0,
        bytes.fromhex(
            "10b5074b00f082fac0235b059c4657380006000a6044034b000c00f077fa10bd215b050875de0608"
        ),
        "sp119_SetRaidBattleFlag: FIRST_RAID_BATTLE_FLAG + u8(mapsec-87)",
        "ACTION_REQUIRED_FLAG_ALIAS",
    ),
    RomSite(
        "cfru_raid_clear_flag_index",
        0x090F3B64,
        bytes.fromhex(
            "0a4b00f049fac0235b059c4657380006000a6044034b000c00f03efaefe7c046"
        ),
        "sp11A_ClearRaidBattleFlag: FIRST_RAID_BATTLE_FLAG + u8(mapsec-87)",
        "ACTION_REQUIRED_FLAG_ALIAS",
    ),
    RomSite(
        "cfru_raid_rewards_index",
        0x090F3D24,
        bytes.fromhex(
            "a54c2578a54b8bb0069500f065f957380006030e99460021a14a11804a46ac46430d98469b1a9f4f6344db00fa58002a"
        ),
        "sp11C_GiveRaidBattleRewards: u8(mapsec-87) -> gRaidsByMapSection row",
        "ACTION_REQUIRED_OOB",
    ),
    RomSite(
        "cfru_town_map_roamer_position_index",
        0x09125F12,
        bytes.fromhex(
            "e17d059ba07d00f0e6f8017d404658390906890d7b187a5a5b88405ad204db04120c1b0c012803d9800010180004020c41444988012903d98900591809040b0c0026"
        ),
        "CreateTownMapRoamerSprites: u8(mapsec-88) -> stock corner/dimension tables",
        "ACTION_REQUIRED_OOB_IF_IMPORTED_ROAMER",
    ),
    RomSite(
        "cfru_warp_preview_lookup",
        0x0911FEC8,
        bytes.fromhex(
            "10b5144b00f0ecf9134b04001b7d007d834205d00021114b00f0e2f9002813d10f4b00f0ddf9e17d0e4b00f0d9f90028"
        ),
        "WarpFadeOutScreen forwards destination regionMapSectionId to stock preview lookup",
        "ACTION_REQUIRED_SAFE_MEMORY",
    ),
    RomSite(
        "cfru_evo_map_compare",
        0x090FBB38,
        bytes.fromhex("704b00f089fa6388834200d058e655e6"),
        "GetEvolutionTargetSpecies EVO_MAP equality consumer",
        "DORMANT_ZERO_RUNTIME_ROWS",
    ),
    RomSite(
        "cfru_r_button_mining_mapsec_compare",
        0x091258BE,
        bytes.fromhex("214b00f0b6f87a28aed1d8f708fdd8f78efd"),
        "StartRButtonFunc mining option compares current section with stock Route 22",
        "OPTIONAL_POLICY",
    ),
    RomSite(
        "cfru_swarm_zero_length_guard",
        0x09132E20,
        bytes.fromhex("1c4c248807000e00150000b5002c03d1002080bcb846f0bd"),
        "TryGenerateSwarmMon returns before map-section equality when table length is zero",
        "SAFE_INERT",
    ),
)


POKEDEX_KANTO_TABLE_ADDRESS = 0x0842D4D4
POKEDEX_KANTO_TABLE_ROWS = 55
CLEAN_POKEDEX_KANTO_TABLE_SHA256 = (
    "e8b9a3867ce2f42b373d8ed495708c571a8109a6668303d24421ce3e6687a0f3"
)
STAGE60_POKEDEX_KANTO_TABLE_SHA256 = (
    "d12d4141c0b4d1e347ecf50d0a32aa25b7a94b61025e50e75290814abc81fdad"
)
POKEDEX_TABLE_POINTER_SITES = (0x0813D20C, 0x0813D304)

RAID_TABLE_ADDRESS = 0x09161AF0
RAID_TABLE_ROW_COUNT = 109
RAID_STAR_COUNT = 7
RAID_TABLE_ROW_SIZE = RAID_STAR_COUNT * 8
RAID_TABLE_SIZE = RAID_TABLE_ROW_COUNT * RAID_TABLE_ROW_SIZE
RAID_TABLE_SHA256 = "2106c87f16a8860bd1ee50da0a721eae518d5f209cc5febea3637a9d68ece1f7"
STOCK_KANTO_MAPSEC_DYNAMIC = 87
STOCK_KANTO_MAPSEC_START = 88

STOCK_MAP_SECTION_CORNERS_ADDRESS = 0x083B89E8
STOCK_MAP_SECTION_DIMENSIONS_ADDRESS = 0x083B8D00
STOCK_MAP_SECTION_LAYOUT_ROWS = 109
STOCK_MAP_SECTION_LAYOUT_SIZE = STOCK_MAP_SECTION_LAYOUT_ROWS * 4
STOCK_MAP_SECTION_CORNERS_SHA256 = (
    "405a9aa09bedd6b3a969c5aa9fa51bd3dc285cb4bd65ea9f4f0628ff19027c97"
)
STOCK_MAP_SECTION_DIMENSIONS_SHA256 = (
    "0f909a36f5daa66fbfa6fe4a26cb282f8e5003d27ea612906586439c37c0cc40"
)

CFRU_EVOLUTION_TABLE_ADDRESS = 0x0905BFD8
CFRU_EVOLUTION_SPECIES_COUNT = 1440
CFRU_EVOLUTION_ROWS_PER_SPECIES = 16
CFRU_EVOLUTION_ROW_SIZE = 8
CFRU_EVOLUTION_TABLE_SIZE = (
    CFRU_EVOLUTION_SPECIES_COUNT
    * CFRU_EVOLUTION_ROWS_PER_SPECIES
    * CFRU_EVOLUTION_ROW_SIZE
)
CFRU_EVOLUTION_TABLE_SHA256 = (
    "3fd7eed36fc6c232b92935c67fcd26a8d3347bb6d285f9aac9a95ce2b4e976cc"
)
CFRU_EVO_MAP_METHOD = 19
CFRU_SWARM_TABLE_LENGTH_ADDRESS = 0x0915E7AC

# long_callされたstock routineはlinked CFRU内ではabsolute Thumb pointer literalになる。
# この25件を、raw source scanと独立したStage60 reverse-reference universeとして固定する。
CFRU_GET_CURRENT_LITERAL_SITES: tuple[int, ...] = (
    0x090D90A4,
    0x090EC88C,
    0x090EE4E4,
    0x090EF118,
    0x090EFB58,
    0x090F08F4,
    0x090F3838,
    0x090F3A90,
    0x090F3AE8,
    0x090F3B10,
    0x090F3B90,
    0x090F3FC0,
    0x090FBCFC,
    0x090FDAF0,
    0x090FDBDC,
    0x090FDCD8,
    0x090FDD30,
    0x090FDDE8,
    0x090FDE34,
    0x090FDEF4,
    0x09103B20,
    0x0911F518,
    0x09120D50,
    0x09125944,
    0x09132EA8,
)
CFRU_GET_MAP_NAME_LITERAL_SITES: tuple[int, ...] = (
    0x090EED84,
    0x09103B28,
    0x09129750,
    0x091297C4,
)
CFRU_GET_MAP_HEADER_LITERAL_SITES: tuple[int, ...] = (0x09125FB4, 0x091297C0)


SOURCE_SHA256: Mapping[str, str] = {
    "include/global.fieldmap.h": "34a8c91e10803ba48b97a2df8a721ca37fad7572b2ff951a4ab7ec15a5f050eb",
    "include/overworld.h": "9206bb6c5aa2731070ab0921432020ff3407524c53d60a7f8267cb3834ce179b",
    "include/region_map.h": "b1b9c68ac6832ee5266c5e20b6923cf7bbb2fdd80db507188889a6210de2c57f",
    "include/roamer.h": "905fe2c00fabb28878c436d72ba25bcc712a30ee7052dd6212c5562c74cae344",
    "src/daycare.c": "3509b363c4cadd7bb9de83fe288b49a8decc76d53d8b600c81b557ba052173ba",
    "src/field_fadetransition.c": "6fa3cb3b827470de6c4942b0296bf823529faec41c6473ffe88675a44114851e",
    "src/field_specials.c": "9c49d3702f0f4dcba61ae26bccefce1c26fbd1247475289dd821780bc537d1d9",
    "src/fldeff_flash.c": "e9d52450071d1a7b54c1774c98b1317910fbdbc6916e4839c42d9ae5dc8307a9",
    "src/item.c": "117c3d29617bd779db7c32332ab75fe5859f02ee6165a047508558977a88d01a",
    "src/item_use.c": "035ca3bdb70f5708dc8771d2bc6cc5450e775e3144278e7683aacba218cb9c98",
    "src/map_name_popup.c": "d1eb8b65ee8bc00d6182ead896ffb336695012089b1a6684ce54ae045ae3ca01",
    "src/map_preview_screen.c": "6172d9268cb0f7bb77678b0d814e4fc800f11b5e8d49d009a4f7b33892109264",
    "src/overworld.c": "df352e738b56856765aec65adc6fdea0a4b25fe567bc760d4ce2d34afc6ff7e2",
    "src/party_menu.c": "8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b",
    "src/pokemon.c": "116a470cd9ebfa226aa8d85c2eb63591e176d726837c67baaa1ac6260d50f2ec",
    "src/pokemon_summary_screen.c": "855a17fb555f5497dbb47f90a8c1b8cf620532d3bff96e8196d0790515508583",
    "src/quest_log.c": "75f19a2193d991754b48fc5a859a5731a7ddb853372dd3992842912b44a19d4e",
    "src/quest_log_battle.c": "d93ed19ad9251dde7774c158707e4b2ca36545dae8993593167409e270093b90",
    "src/quest_log_events.c": "e6cade44e4c41d0c2a0b27a718ffaee16a9485d36e7f09d6adc9da752b7b7e36",
    "src/region_map.c": "b761f02803a1c5aada4465b9a93bf2b02c5ef1118432e677a30a5a4a4b78e0cb",
    "src/roamer.c": "b72cd17c1e668b8d483953dd85cc6f0e02c54a1a022f4fabe743841867b9877f",
    "src/save_menu_util.c": "5dcd9e8762939c31a29a60e207ebf5ba6ebf4127e6dffa175281fb95598f793e",
    "src/shop.c": "d326d1498cad7fc610f483237a3ff17b0d27836dcf8213960b41bbd2b58844f8",
    "src/wild_pokemon_area.c": "b37c82d03577722023dec252450cf9ce93fe063b9f33b96ce2d994202c279e58",
    "src/data/region_map/region_map_layout_kanto.h": "62b8f2e60891a97cb44bb16f52c2a1fb45be5f2caff5f0db86dd36dbe3b5c194",
    "src/data/region_map/region_map_sections.json": "82e456cbe86a57ebc4bd0d88d6e000e83e28340895ac038079c38d415bc6de5f",
    "src/data/region_map/region_map_sections.constants.json.txt": "84346d3ffc7572aab79273d7f048521f384e77e78c20a6c8b852966949d182d5",
}


CFRU_SOURCE_SHA256: Mapping[str, str] = {
    "include/global.fieldmap.h": "e281137a65d166f7fc51f7983d58b7159d0b8c9526dc9a0ec3d619fa64f99235",
    "include/new/ram_locs.h": "8c8d7fd53813fefff997173f203aa0c97e1c14062db933e55303d5c498b2f089",
    "include/overworld.h": "ee0e06dfe4b39f2fe5450aa74e4cd8e4fcd0d13e23c9b2e237c2a143b1e07392",
    "include/pokemon.h": "d75972c66e85835a3fc9c859cb695c033995ba6627ba1d44f577b35136356c78",
    "include/wild_encounter.h": "72b45ffb891f0b850f7c008f7490c8eb0ca832436420a0856dbaaf8c914e4ff8",
    "include/constants/region_map_sections.h": (
        "f1826f2e1d419b0aa56815c6a3cc3579b0f5279dd1cfc3f1d3e0d1c60dbcc1cd"
    ),
    "src/Tables/raid_encounters.h": (
        "77b56fb07f0e40ef38e8fb5fbd4053bb90590e7a5af9d7cd73d5ac9abe256c57"
    ),
    "src/Tables/wild_encounter_tables.c": (
        "bbd8d7142ff1b94788b46d14cff22638edd300b7ab92db4f467d62867c3bec32"
    ),
    "src/battle_anims.c": "4893fda793e75356672e8b1be3bca4bd54fe562774fd8b07ed9f8f9ba501aff3",
    "src/build_pokemon.c": "ac81e3a9a8c7a58105573e6ee2abf62a4b22922e88c6c7d3a1ecdc6c9431e824",
    "src/dexnav.c": "8049836072f5f3469cb134ade1d864ab0c2241f6162930ba76028d8b3d1dbd17",
    "src/dynamax.c": "ef0eb85047ec0a7d74b5df38bce8481367828508e2104aa7615de62ddecc2c0a",
    "src/evolution.c": "3f7a70cb0cf080964cbc7742c2a3c61f925617783611044c62a7a6002f151fea",
    "src/field_effects.c": "e79cbe0c54065148cb826ce7c147e93e4830ef837432bbc71cffcc2ad4c9d022",
    "src/form_change.c": "e990dab7a70c6c250d4479461e8a30b5159cf883504d18e8385d405cdb91bc8b",
    "src/frontier_records.c": "eb0ed3f1692ccd9a81420f60c533be7632bbf5835e8361e9a4ba0d4986e93084",
    "src/overworld.c": "1d5877fd2d38747db0a03891e193729cb410d75a653ece57eef444783c197fe6",
    "src/party_menu.c": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
    "src/read_keys.c": "737f8c154f887e9b34a0f95387d808b130da01f03d0e1aeda5c76e51585abee3",
    "src/roamer.c": "0e5b3b628372bf34e996501d4b83b5120a452836eb9cb0b01f43e04e2d40529b",
    "src/scripting.c": "6ab41220852dba87df2a26c6fba3b3c3bebf1c7df5f85a596eb7ae644461544a",
    "src/wild_encounter.c": "a2e57daf75961a550faa034e7f668443b519787d289044e5e0a32d3c933a6249",
}

DPE_SOURCE_SHA256: Mapping[str, str] = {
    "include/evolution.h": "2c90352fed4951ac52b89cd2de2d638b3e79f9269017cf9b25b4bc7abfdfee1e",
    "src/Evolution Table.c": "abc157d25ac7b555a528efdf0d45b7110d654ab277256c88346925019ca650b7",
}


DIRECT_REFERENCE_COUNTS: Mapping[str, int] = {
    "daycare.c": 1,
    "field_fadetransition.c": 1,
    "field_specials.c": 2,
    "fldeff_flash.c": 2,
    "item.c": 1,
    "item_use.c": 1,
    "map_name_popup.c": 1,
    "map_preview_screen.c": 1,
    "overworld.c": 11,
    "party_menu.c": 5,
    "pokemon.c": 3,
    "pokemon_summary_screen.c": 2,
    "quest_log.c": 1,
    "quest_log_battle.c": 2,
    "quest_log_events.c": 11,
    "region_map.c": 14,
    "roamer.c": 2,
    "save_menu_util.c": 1,
    "shop.c": 2,
    "wild_pokemon_area.c": 2,
}

CFRU_DIRECT_REFERENCE_COUNTS: Mapping[str, int] = {
    "battle_anims.c": 1,
    "build_pokemon.c": 2,
    "dexnav.c": 11,
    "dynamax.c": 2,
    "evolution.c": 1,
    "field_effects.c": 3,
    "form_change.c": 2,
    "frontier_records.c": 1,
    "overworld.c": 10,
    "party_menu.c": 2,
    "read_keys.c": 1,
    "roamer.c": 1,
    "scripting.c": 2,
    "wild_encounter.c": 2,
}

MAPSEC_TOKEN_LINE_COUNTS: Mapping[str, int] = {
    "field_specials.c": 1,
    "map_preview_screen.c": 28,
    "overworld.c": 1,
    "pokemon_summary_screen.c": 1,
    "quest_log_events.c": 9,
    "region_map.c": 295,
    "roamer.c": 1,
    "wild_pokemon_area.c": 94,
}


BL_XREFS: Mapping[str, tuple[int, tuple[int, ...]]] = {
    "Overworld_GetMapHeaderByGroupAndId": (
        0x08054AF8,
        (
            0x0805486E, 0x08054B26, 0x08054B4E, 0x08054B96,
            0x08055642, 0x08055A26, 0x08055A8A, 0x08055B10,
            0x08055B38, 0x08055B60, 0x0805828C, 0x0805D988,
            0x0805F658, 0x0806D48C, 0x080C4CFC, 0x080C4DAE,
            0x080C4DEA, 0x080C4E36, 0x080C4E66, 0x080CD7B6,
            0x080CD814, 0x0811227C, 0x0812502E, 0x08125072,
            0x08125554, 0x081255A4, 0x0813D390, 0x0814277E,
        ),
    ),
    "GetCurrentRegionMapSectionId": (
        0x08055B20,
        (0x0803D396, 0x08041A28, 0x08042EF0, 0x08046378, 0x0812C976, 0x0812C9E0),
    ),
    "Overworld_MusicCanOverrideMapMusic": (
        0x080559E4,
        (0x08055710, 0x0805579E, 0x0808654E, 0x080BE8C4),
    ),
    "GetMapName": (
        0x080C5F5C,
        (0x08097E02, 0x080C1D3A, 0x080C5FE4, 0x080F93D0),
    ),
    "GetMapNameGeneric": (
        0x080C5FDC,
        (
            0x080C5FF2, 0x080F910A, 0x08112B46, 0x08114B3A,
            0x08115864, 0x08115972, 0x08115CD0, 0x08115DA6,
            0x08115F5A, 0x08116012, 0x081160DA, 0x081161EA,
            0x081162E8, 0x08125038, 0x0812507C,
        ),
    ),
    "GetMapNameGeneric_": (
        0x080C5FEC,
        (0x08137D9E, 0x08137FFC),
    ),
    "MapSecIsInKantoOrSevii": (
        0x0813BFFC,
        (0x08137D90, 0x08137F3C, 0x08137FEE),
    ),
    "GetSpeciesPokedexAreaMarkers": (
        0x0813D120,
        (0x08134AAC,),
    ),
    "FindDexAreaByMapSec": (
        0x0813D39C,
        (0x0813D1E4, 0x0813D23C, 0x0813D2DE),
    ),
    "GetMapPreviewScreenIdx": (
        0x080F9150,
        (0x080F9188, 0x080F9210, 0x080F95B6, 0x080F95DE),
    ),
    "GetDungeonMapPreviewScreenInfo": (
        0x080F95B0,
        (0x080C2B60, 0x080C2B74),
    ),
    "GetRoamerLocationMapSectionId": (
        0x08142768,
        (0x0813D2C8,),
    ),
}


DIRECT_G_MAP_HEADER_READS: tuple[tuple[int, int], ...] = (
    (0x080551C2, 0x080551C8),
    (0x080559F8, 0x080559FA),
    (0x0805653C, 0x08056542),
    (0x0807D380, 0x0807D384),
    (0x08097DFA, 0x08097DFC),
    (0x0809A280, 0x0809A282),
    (0x0809BB76, 0x0809BB78),
    (0x080A2E8A, 0x080A2E8C),
    (0x080C1240, 0x080C1242),
    (0x080C4D6C, 0x080C4D6E),
    (0x080C4E14, 0x080C4E16),
    (0x080CAECC, 0x080CAED2),
    (0x080F9104, 0x080F9106),
    (0x08112B42, 0x08112B44),
    (0x0811628A, 0x0811628C),
    (0x08125560, 0x08125562),
)

STAGE60_DIRECT_G_MAP_HEADER_READS: tuple[tuple[int, int], ...] = (
    *DIRECT_G_MAP_HEADER_READS,
    (0x0911FED0, 0x0911FED4),  # CFRU-JP WarpFadeOutScreen
)


CONSUMERS: tuple[Consumer, ...] = (
    Consumer(
        "MSC-01", "popup_and_names",
        ("overworld.c:LoadMapFromCameraTransition", "map_name_popup.c:MapNamePopup",
         "region_map.c:GetMapName/GetMapNameGeneric/GetMapNameGeneric_"),
        "gMapHeader+0x14 -> GetMapName",
        "stock arithmetic name-table index",
        "COVERED_STAGE61", "NONE",
        "Stage 61 central name hook handles project 0..52; all direct name wrappers converge here.",
        "Keep the exact GetMapName hook and its 4/15/2 caller sets.",
        ("get_map_name",),
    ),
    Consumer(
        "MSC-02", "town_map_core",
        ("region_map.c:InitRegionMapType", "region_map.c:GetMapsecType",
         "region_map.c:GetDungeonMapsecType", "region_map.c:GetPlayerPositionOnRegionMap",
         "region_map.c:GetSelectedMapSection", "region_map.c:DisplayCurrentDungeonName"),
        "current/project section -> grid, position, type, name",
        "four stock arithmetic/table boundaries",
        "COVERED_STAGE61", "NONE",
        "Grid, cursor, visit type and the small dungeon-name window have explicit project paths.",
        "Retain physical-group 96..98 gating and stock trampolines for Vega/Sevii.",
        ("dungeon_name_resolver", "get_mapsec_type", "get_dungeon_mapsec_type",
         "get_player_position_on_region_map_overrides", "get_selected_map_section"),
    ),
    Consumer(
        "MSC-03", "fly",
        ("region_map.c:SetFlyWarpDestination", "party_menu.c:SetUsedFlyQuestLogEvent"),
        "selected project section -> imported physical group/map",
        "stock arithmetic destination-table index",
        "COVERED_STAGE61", "NONE",
        "Project destination records bypass mapsec-88 and Quest Log re-reads the imported header.",
        "Retain exact hook; never pass project IDs to sMapFlyDestinations.",
        ("set_fly_warp_destination",),
    ),
    Consumer(
        "MSC-04", "bgm",
        ("overworld.c:Overworld_MusicCanOverrideMapMusic",),
        "gMapHeader+0x14",
        "stock constant equality (132/123/97)",
        "ACTION_REQUIRED", "HIGH",
        "Victory Road(42), Route 23(33), Indigo Plateau(9) no longer block cycling/surf override.",
        "In imported groups compare project 42/33/9; delegate every other context to stock logic.",
        ("music_override_guard",),
    ),
    Consumer(
        "MSC-05", "field_preview",
        ("overworld.c:CB2_LoadMap2", "field_fadetransition.c:DoWarp",
         "fldeff_flash.c:UseFlash", "map_preview_screen.c:GetMapPreviewScreenIdx"),
        "current/destination project section -> sMapPreviewScreenData",
        "safe linear equality lookup",
        "ACTION_REQUIRED_SAFE_MEMORY", "MEDIUM",
        "Imported forest/cave preview transitions never match stock IDs and therefore do not run.",
        "Normalize project->source only in imported physical context before preview lookup.",
        ("map_preview_index", "map_preview_duration"),
    ),
    Consumer(
        "MSC-06", "town_map_dungeon_preview",
        ("region_map.c:InitDungeonMapPreview", "region_map.c:GetDungeonName",
         "region_map.c:GetDungeonFlavorText", "map_preview_screen.c:GetDungeonMapPreviewScreenInfo"),
        "Town Map project dungeon section",
        "safe linear equality lookup",
        "ACTION_REQUIRED_SAFE_MEMORY", "MEDIUM",
        "A-button preview falls back to Rock Tunnel graphics while name/flavor become No Data.",
        "Translate project dungeon IDs for preview/name/flavor lookup without changing project grid IDs.",
        ("dungeon_preview_info",),
    ),
    Consumer(
        "MSC-07", "town_map_unlock_gating",
        ("region_map.c:GetDungeonMapsecUnderCursor", "region_map.c:CreateDungeonIcons"),
        "project dungeon section",
        "stock constant equality",
        "POLICY_REQUIRED", "MEDIUM",
        "Project Cerulean Cave(51) does not match stock 141, bypassing FLAG_SYS_CAN_LINK_WITH_RS hiding.",
        "Choose and assert the intended Stage 61 unlock flag/gate for project section 51.",
    ),
    Consumer(
        "MSC-08", "pokemon_met_location_write",
        ("pokemon.c:CreateBoxMon", "daycare.c:CreateEgg"),
        "GetCurrentRegionMapSectionId -> MON_DATA_MET_LOCATION",
        "byte persistence",
        "SAFE_WITH_INVARIANT", "LOW",
        "Project IDs remain distinguishable from Vega 88..196 but collide numerically with Hoenn 0..52.",
        "Keep MON_DATA_MET_GAME provenance; do not globally reinterpret every 0..52 as Kanto.",
    ),
    Consumer(
        "MSC-09", "friendship_same_location",
        ("pokemon.c:ModifyFriendship", "pokemon.c:MonGainEVs/FriendshipEvent"),
        "metLocation == GetCurrentRegionMapSectionId",
        "identity equality",
        "SAFE_IDENTITY", "NONE",
        "Both values use the same project ID while the mon is in imported Kanto.",
        "If persistence encoding changes later, normalize both sides together.",
    ),
    Consumer(
        "MSC-10", "pokemon_trainer_memo",
        ("pokemon_summary_screen.c:PokeSum_PrintTrainerMemo_Mon_HeldByOT",
         "pokemon_summary_screen.c:PokeSum_PrintTrainerMemo_Mon_NotHeldByOT",
         "pokemon_summary_screen.c:MapSecIsInKantoOrSevii"),
        "MON_DATA_MET_LOCATION plus MON_DATA_MET_GAME",
        "stock unsigned range classifier",
        "ACTION_REQUIRED_CONTEXTUAL", "HIGH",
        "Local imported-Kanto mons show Somewhere/trade instead of their map name.",
        "Accept project 0..52 only for FR/LG provenance (or an explicit project marker); preserve R/S/E Hoenn meaning.",
        ("pokemon_summary_mapsec_classifier",),
    ),
    Consumer(
        "MSC-11", "pokedex_wild_area",
        ("wild_pokemon_area.c:GetSpeciesPokedexAreaMarkers",
         "wild_pokemon_area.c:GetMapSecIdFromWildMonHeader",
         "wild_pokemon_area.c:FindDexAreaByMapSec"),
        "wild header -> map header section -> sDexAreas_Kanto",
        "safe linear equality lookup",
        "ACTION_REQUIRED_SAFE_MEMORY", "HIGH",
        "Project 1..52 have no Stage 60 key; project 0 only hits disabled (0,0) rows, so markers vanish.",
        "Use an exact 53-row project->DEX_AREA table or context-gated project->source translation.",
        ("pokedex_species_area", "pokedex_wild_header_mapsec",
         "pokedex_linear_mapsec_lookup"),
    ),
    Consumer(
        "MSC-12", "pokedex_roamer_area",
        ("wild_pokemon_area.c:GetRoamerPokedexAreaMarkers",
         "roamer.c:GetRoamerLocationMapSectionId"),
        "roamer group/map -> map header section -> sDexAreas_Kanto",
        "safe linear equality lookup",
        "DORMANT_RISK", "LOW",
        "Stock roamer is restricted to physical group 3, so it cannot currently produce project IDs.",
        "Share the project DEX-area translator if roamers are ever enabled in groups 96..98.",
        ("pokedex_roamer_area", "roamer_location_mapsec"),
    ),
    Consumer(
        "MSC-13", "quest_log_battles",
        ("quest_log_battle.c:QuestLog_RecordTrainerBattle",
         "quest_log_battle.c:QuestLog_RecordWildBattle",
         "quest_log_events.c:LoadEvent_Defeated*"),
        "GetCurrentRegionMapSectionId -> byte record -> GetMapNameGeneric",
        "byte persistence plus central name hook",
        "COVERED_BY_NAME_HOOK", "NONE",
        "Project IDs round-trip through the byte record and resolve through the Stage 61 name hook.",
        "Preserve the GetMapName wrapper convergence.",
    ),
    Consumer(
        "MSC-14", "quest_log_items_shops_arrival",
        ("item.c", "item_use.c", "shop.c", "quest_log.c",
         "quest_log_events.c:Record/Load item, shop, arrived events"),
        "gMapHeader+0x14 -> byte/u16 record -> GetMapNameGeneric",
        "persistence plus central name hook",
        "COVERED_BY_NAME_HOOK", "NONE",
        "Recorded project IDs receive imported Kanto names.",
        "Keep records as project IDs; no stock arithmetic table is reached after the name hook.",
    ),
    Consumer(
        "MSC-15", "quest_log_gym_narration",
        ("quest_log_events.c:LoadEvent_DepartedLocation",),
        "recorded project city section -> sGymCityMapSecs",
        "stock constant table equality",
        "ACTION_REQUIRED", "MEDIUM",
        "Gym departure text cannot select the badge-specific branch for project city IDs.",
        "Use project gym city IDs 2,3,5,6,7,10,8,1 in imported records or normalize before compare.",
        ("quest_log_gym_section_compare", "quest_log_gym_section_table"),
    ),
    Consumer(
        "MSC-16", "quest_log_teleport_home",
        ("quest_log_events.c:LoadEvent_UsedFieldMove",),
        "recorded Teleport destination section",
        "stock constant equality",
        "ACTION_REQUIRED", "MEDIUM",
        "Project Pallet(0) is called a Pokémon Center instead of Home because code compares 88.",
        "Compare project 0 for imported Quest Log records while retaining stock 88 behavior.",
        ("quest_log_teleport_home_compare",),
    ),
    Consumer(
        "MSC-17", "quest_log_departed_location_source",
        ("field_specials.c:QuestLog_CheckDepartingIndoorsMap",
         "field_specials.c:QuestLog_TryRecordDepartedLocation"),
        "physical map group/number -> inside/outside table -> map section",
        "stock physical-map equality before section read",
        "ACTION_REQUIRED_ADJACENT", "MEDIUM",
        "Imported groups 96..98 do not match stock inside/outside pairs, so departed events are not recorded.",
        "Provide an imported physical-map crosswalk before relying on the downstream section fixes.",
    ),
    Consumer(
        "MSC-18", "party_field_move_history",
        ("party_menu.c:SetUsedFieldMoveQuestLogEvent", "party_menu.c:SetUsedFlyQuestLogEvent"),
        "last-heal/current/destination map header -> Quest Log record",
        "identity copy",
        "SAFE_UPSTREAM", "NONE",
        "Project IDs are recorded correctly; MSC-16 owns the remaining Teleport wording bug.",
        "No independent conversion is needed here.",
    ),
    Consumer(
        "MSC-19", "save_menu",
        ("save_menu_util.c:BufferSaveMenuText",),
        "gMapHeader+0x14 -> GetMapNameGeneric",
        "central name hook",
        "COVERED_BY_NAME_HOOK", "NONE",
        "Save-menu location uses the imported name.",
        "No further action.",
    ),
    Consumer(
        "MSC-20", "celadon_department_name",
        ("region_map.c:IsCeladonDeptStoreMapsec",),
        "map section plus physical group/map",
        "stock constant and physical-map equality",
        "COVERED_STAGE61", "NONE",
        "The Stage 61 name resolver has a project section 6 + imported group/map special case.",
        "Retain contextual handling; a global section-6 special case would collide with Hoenn.",
        ("get_map_name",),
    ),
    Consumer(
        "MSC-21", "cfru_raid_map_section_index",
        (
            "CFRU-JP/dynamax.c:GetRaidMapSectionId",
            "DetermineRaidSpecies",
            "GetRaidSpeciesAbilityNum",
            "HasRaidBattleAlreadyBeenDone",
            "sp119_SetRaidBattleFlag",
            "sp11A_ClearRaidBattleFlag",
            "sp11C_GiveRaidBattleRewards",
        ),
        "GetCurrentRegionMapSectionId -> u8(section-87) -> raid row/flag",
        "unchecked arithmetic table/flag index",
        "ACTION_REQUIRED_DANGEROUS_INDEX", "CRITICAL",
        (
            "Project 0..52 underflows to 169..221 while gRaidsByMapSection has only "
            "109 rows (0..108). Species/ability/reward paths read and dereference beyond "
            "the table; done/set/clear paths alias unrelated flags."
        ),
        (
            "Introduce one physical-context-aware project->source normalizer before every "
            "inline raid index, assert 0<=index<109, and fail closed outside supported sections."
        ),
        (
            "cfru_raid_determine_species_index",
            "cfru_raid_ability_index",
            "cfru_raid_done_flag_index",
            "cfru_raid_set_flag_index",
            "cfru_raid_clear_flag_index",
            "cfru_raid_rewards_index",
        ),
    ),
    Consumer(
        "MSC-22", "cfru_town_map_roamer_position",
        ("CFRU-JP/roamer.c:CreateTownMapRoamerSprites",),
        "roamer map header section -> u8(section-88) -> stock position/dimension rows",
        "unchecked arithmetic table index",
        "ACTION_REQUIRED_DANGEROUS_INDEX", "HIGH",
        (
            "An active CFRU roamer in imported groups 96..98 produces index 168..220 for "
            "two 109-row tables, so even project 0 is outside the declared table."
        ),
        (
            "Resolve project sections to a validated project position table (preferred) or "
            "context-gated source section before subtracting 88; range-check before access."
        ),
        ("cfru_town_map_roamer_position_index",),
    ),
    Consumer(
        "MSC-23", "cfru_warp_preview",
        ("CFRU-JP/overworld.c:WarpFadeOutScreen",),
        "destination/current MapHeader.regionMapSectionId -> MapHasPreviewScreen",
        "safe linear preview equality lookup",
        "ACTION_REQUIRED_SAFE_MEMORY", "MEDIUM",
        "The linked CFRU warp path independently forwards project IDs to the stock preview table.",
        "Share MSC-05's imported-context preview normalizer with WarpFadeOutScreen.",
        ("cfru_warp_preview_lookup",),
    ),
    Consumer(
        "MSC-24", "cfru_met_location_and_friendship",
        (
            "CFRU-JP/build_pokemon.c:CreateBoxMon",
            "CFRU-JP/party_menu.c:AdjustFriendshipForEVReducingBerry",
        ),
        "current project section -> metLocation; metLocation == current section",
        "byte persistence and identity equality",
        "SAFE_WITH_INVARIANT", "NONE",
        "This is the same identity-safe behavior as MSC-08/09 and retains MET_GAME provenance.",
        "Do not normalize only one side of the friendship equality.",
    ),
    Consumer(
        "MSC-25", "cfru_name_consumers",
        (
            "CFRU-JP/dexnav.c:CB2_DexNav",
            "CFRU-JP/frontier_records.c:PrintCurrentRecords",
            "CFRU-JP/scripting.c:sp058_BufferSwarmText/sp059_BufferSpeciesRoamingText",
        ),
        "current/swarm/roamer section -> GetMapName",
        "central name hook",
        "COVERED_BY_NAME_HOOK", "NONE",
        "All four linked GetMapName literals converge on the Stage 61 central name boundary.",
        "Keep non-current saved-location provenance in mind if Hoenn records are added.",
        ("get_map_name",),
    ),
    Consumer(
        "MSC-26", "cfru_evo_map",
        ("CFRU-JP/evolution.c:GetEvolutionTargetSpecies(EVO_MAP)",),
        "current section == evolution row param",
        "constant equality over runtime evolution table",
        "DORMANT_TABLE_CONTRACT", "LOW",
        (
            "The handler is linked, but Stage60's exact 1440x16 canonical evolution table "
            "contains zero EVO_MAP(method 19) rows, so the branch is unreachable today."
        ),
        (
            "When T09/DPE adds EVO_MAP rows, store project 52 for imported Power Plant or "
            "perform a context-aware comparison; do not import stock param 142 blindly."
        ),
        ("cfru_evo_map_compare",),
    ),
    Consumer(
        "MSC-27", "cfru_swarm_and_dexnav",
        (
            "CFRU-JP/wild_encounter.c:TryGenerateSwarmMon",
            "CFRU-JP/dexnav.c:swarm comparison consumers",
        ),
        "current section == gSwarmTable[index].mapName",
        "constant equality guarded by gSwarmTableLength",
        "SAFE_INERT_PROFILE", "NONE",
        "The Stage60 non-UNBOUND profile fixes gSwarmTableLength to zero; every map comparison is unreachable.",
        "Re-audit and translate project keys before enabling swarms.",
        ("cfru_swarm_zero_length_guard",),
    ),
    Consumer(
        "MSC-28", "cfru_profile_gated_mapsec_features",
        (
            "CFRU-JP/overworld.c:IsCurrentArea*/InTanobyRuins",
            "CFRU-JP/field_effects.c grass/footprint palettes",
            "CFRU-JP/battle_anims.c and form_change.c Distortion World checks",
            "CFRU-JP/build_pokemon.c scaled-trainer League check",
            "CFRU-JP/party_menu.c Vs Seeker check",
            "CFRU-JP/read_keys.c mining Route 22 check",
            "CFRU-JP/wild_encounter.c Tanoby/Tomb checks",
        ),
        "current section -> feature-specific stock constant comparisons",
        "profile-gated equality (no table index)",
        "SAFE_OR_OPTIONAL_POLICY", "LOW",
        (
            "UNBOUND, SCALED_TRAINERS and related branches are disabled; Tanoby remains a "
            "Sevii-only range check. The compiled mining Route-22 comparison simply does not "
            "enable mining on project Route 22 unless explicitly adapted."
        ),
        "Only add project constants for features Stage61 intentionally enables.",
        ("cfru_r_button_mining_mapsec_compare",),
    ),
)


_DIRECT_REFERENCE_RE = re.compile(
    r"regionMapSectionId"
    r"|GetCurrentRegionMapSectionId\("
    r"|GetLastUsedWarpMapSectionId\("
    r"|GetSavedWarpRegionMapSectionId\("
    r"|GetRoamerLocationMapSectionId\("
    r"|GetMapName(?:Generic_?)?\("
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise MapSectionConsumerAuditError(f"{what} を読めません: {path}: {exc}") from exc


def _rom_slice(raw: bytes, address: int, size: int, what: str) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(raw):
        raise MapSectionConsumerAuditError(
            f"{what} がROM範囲外です: {address:#010x}+{size:#x}, size={len(raw):#x}"
        )
    return raw[offset:offset + size]


def validate_rom_identity(raw: bytes, *, size: int, sha256: str, label: str) -> None:
    if len(raw) != size:
        raise MapSectionConsumerAuditError(
            f"{label} size mismatch: expected={size}, actual={len(raw)}"
        )
    actual = _sha(raw)
    if actual != sha256:
        raise MapSectionConsumerAuditError(
            f"{label} SHA-256 mismatch: expected={sha256}, actual={actual}"
        )


def verify_preimages(raw: bytes, sites: Iterable[RomSite], *, label: str) -> None:
    for site in sites:
        actual = _rom_slice(raw, site.address, len(site.expected), site.name)
        if actual != site.expected:
            raise MapSectionConsumerAuditError(
                f"{label} preimage mismatch: {site.name}@{site.address:#010x}: "
                f"expected={site.expected.hex()}, actual={actual.hex()}"
            )


def _decode_thumb_bl(raw: bytes, offset: int) -> int | None:
    high, low = struct.unpack_from("<HH", raw, offset)
    if high & 0xF800 != 0xF000 or low & 0xF800 != 0xF800:
        return None
    displacement = ((high & 0x7FF) << 11) | (low & 0x7FF)
    if displacement & (1 << 21):
        displacement -= 1 << 22
    return ROM_BASE + offset + 4 + displacement * 2


def find_thumb_bl_xrefs(raw: bytes, targets: Iterable[int]) -> dict[int, tuple[int, ...]]:
    wanted = set(targets)
    result: dict[int, list[int]] = {target: [] for target in wanted}
    for offset in range(0, len(raw) - 3, 2):
        high = struct.unpack_from("<H", raw, offset)[0]
        if high & 0xF800 != 0xF000:
            continue
        target = _decode_thumb_bl(raw, offset)
        if target in result:
            result[target].append(ROM_BASE + offset)
    return {target: tuple(rows) for target, rows in result.items()}


def find_direct_g_map_header_section_reads(raw: bytes) -> tuple[tuple[int, int], ...]:
    """``ldr Rt, =gMapHeader`` から ``ldrb *, [Rt,#0x14]`` を検出する。

    同じbasic blockの直後8 bytesだけを追う。長く追うと、そのregisterが別値で
    上書きされた後の偶然の``ldrb``まで拾うためである。pinned cleanでは16 root、
    Stage 60ではCFRU ``WarpFadeOutScreen``を加えた17 rootを別々に要求する。
    """

    result: list[tuple[int, int]] = []
    for offset in range(0, len(raw) - 10, 2):
        opcode = struct.unpack_from("<H", raw, offset)[0]
        if opcode & 0xF800 != 0x4800:
            continue
        target_register = (opcode >> 8) & 7
        instruction_address = ROM_BASE + offset
        literal_address = ((instruction_address + 4) & ~3) + (opcode & 0xFF) * 4
        try:
            literal = struct.unpack(
                "<I", _rom_slice(raw, literal_address, 4, "gMapHeader literal")
            )[0]
        except MapSectionConsumerAuditError:
            continue
        if literal != G_MAP_HEADER:
            continue
        for delta in range(2, 10, 2):
            candidate = struct.unpack_from("<H", raw, offset + delta)[0]
            if candidate & 0xF800 != 0x7800:
                continue
            immediate = (candidate >> 6) & 0x1F
            base_register = (candidate >> 3) & 7
            if immediate == MAP_HEADER_SECTION_OFFSET and base_register == target_register:
                result.append((instruction_address, instruction_address + delta))
                break
    return tuple(result)


def find_word_occurrences(raw: bytes, value: int) -> tuple[int, ...]:
    """little-endian 32-bit wordの全出現addressを返す。"""

    needle = struct.pack("<I", value)
    result: list[int] = []
    cursor = 0
    while True:
        cursor = raw.find(needle, cursor)
        if cursor < 0:
            return tuple(result)
        result.append(ROM_BASE + cursor)
        cursor += 1


def _read_git_head(repo: Path) -> str:
    head_path = repo / ".git/HEAD"
    try:
        head = head_path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise MapSectionConsumerAuditError(f"decomp HEADを読めません: {exc}") from exc
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    ref_path = repo / ".git" / ref
    if ref_path.is_file():
        return ref_path.read_text(encoding="ascii").strip()
    packed = repo / ".git/packed-refs"
    try:
        for line in packed.read_text(encoding="ascii").splitlines():
            if line and not line.startswith("#") and not line.startswith("^"):
                commit, name = line.split(" ", 1)
                if name == ref:
                    return commit
    except OSError as exc:
        raise MapSectionConsumerAuditError(f"decomp packed-refsを読めません: {exc}") from exc
    raise MapSectionConsumerAuditError(f"decomp refを解決できません: {ref}")


def validate_repo_snapshot(
    repo: Path,
    *,
    expected_commit: str,
    expected_files: Mapping[str, str],
    label: str,
) -> dict[str, Any]:
    commit = _read_git_head(repo)
    if commit != expected_commit:
        raise MapSectionConsumerAuditError(
            f"{label} commit mismatch: expected={expected_commit}, actual={commit}"
        )
    checked: list[dict[str, Any]] = []
    for relative, expected in expected_files.items():
        raw = _read(repo / relative, f"{label} source {relative}")
        actual = _sha(raw)
        if actual != expected:
            raise MapSectionConsumerAuditError(
                f"{label} source SHA mismatch: {relative}: expected={expected}, actual={actual}"
            )
        checked.append({"path": relative, "sha256": actual, "size": len(raw)})
    return {"commit": commit, "files": checked}


def validate_source_snapshot(decomp: Path) -> dict[str, Any]:
    return validate_repo_snapshot(
        decomp,
        expected_commit=DECOMP_COMMIT,
        expected_files=SOURCE_SHA256,
        label="pokefirered decomp",
    )


def validate_cfru_snapshot(repo: Path, profile_path: Path) -> dict[str, Any]:
    result = validate_repo_snapshot(
        repo,
        expected_commit=CFRU_COMMIT,
        expected_files=CFRU_SOURCE_SHA256,
        label="CFRU-JP",
    )
    profile = _read(profile_path, "CFRU Stage60 profile")
    actual = _sha(profile)
    if actual != CFRU_PROFILE_SHA256:
        raise MapSectionConsumerAuditError(
            f"CFRU profile SHA mismatch: expected={CFRU_PROFILE_SHA256}, actual={actual}"
        )
    text = profile.decode("utf-8")
    required_profile_tokens = (
        "#define DYNAMAX_FEATURE",
        "#undef UNBOUND",
        "#undef VAR_GAME_DIFFICULTY",
        "#undef SCALED_TRAINERS",
    )
    missing = [token for token in required_profile_tokens if token not in text]
    if missing:
        raise MapSectionConsumerAuditError(
            f"CFRU profile semantic tokens missing: {missing}"
        )
    result["profile"] = {
        "path": str(CFRU_PROFILE_RELATIVE),
        "sha256": actual,
        "assertions": {
            "dynamax_compiled": True,
            "unbound_disabled": True,
            "scaled_trainers_disabled": True,
        },
    }
    return result


def validate_dpe_snapshot(repo: Path) -> dict[str, Any]:
    return validate_repo_snapshot(
        repo,
        expected_commit=DPE_COMMIT,
        expected_files=DPE_SOURCE_SHA256,
        label="DPE-JP",
    )


def validate_project_manifest(path: Path) -> list[dict[str, Any]]:
    raw = _read(path, "Kanto map-section manifest")
    actual_sha = _sha(raw)
    if actual_sha != MAP_SECTION_MANIFEST_SHA256:
        raise MapSectionConsumerAuditError(
            "map-section manifest SHA mismatch: "
            f"expected={MAP_SECTION_MANIFEST_SHA256}, actual={actual_sha}"
        )
    try:
        rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise MapSectionConsumerAuditError(f"map-section manifestを解析できません: {exc}") from exc
    project = tuple(int(row["runtime_map_section_id"]) for row in rows)
    source = tuple(int(row["source_map_section_id"]) for row in rows)
    if project != PROJECT_SECTION_IDS or source != SOURCE_SECTION_IDS:
        raise MapSectionConsumerAuditError(
            f"map-section domain mismatch: project={project}, source={source}"
        )
    return [
        {
            "project_id": int(row["runtime_map_section_id"]),
            "source_id": int(row["source_map_section_id"]),
            "symbol": row["source_map_section_symbol"],
            "name": row["source_name"],
        }
        for row in rows
    ]


def scan_source_references(decomp: Path) -> dict[str, Any]:
    references: list[dict[str, Any]] = []
    direct_counts: dict[str, int] = {}
    mapsec_counts: dict[str, int] = {}
    source_dir = decomp / "src"
    for path in sorted(source_dir.glob("**/*.c")):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(source_dir).as_posix()
        direct = 0
        mapsec = 0
        for number, line in enumerate(text.splitlines(), 1):
            if _DIRECT_REFERENCE_RE.search(line):
                direct += 1
                references.append(
                    {"file": relative, "line": number, "text": line.strip()}
                )
            if "MAPSEC_" in line:
                mapsec += 1
        if direct:
            direct_counts[relative] = direct
        if mapsec:
            mapsec_counts[relative] = mapsec
    if direct_counts != dict(DIRECT_REFERENCE_COUNTS):
        raise MapSectionConsumerAuditError(
            f"direct source reference set drifted: expected={dict(DIRECT_REFERENCE_COUNTS)}, "
            f"actual={direct_counts}"
        )
    if mapsec_counts != dict(MAPSEC_TOKEN_LINE_COUNTS):
        raise MapSectionConsumerAuditError(
            f"MAPSEC source file set drifted: expected={dict(MAPSEC_TOKEN_LINE_COUNTS)}, "
            f"actual={mapsec_counts}"
        )
    if len(references) != 66:
        raise MapSectionConsumerAuditError(
            f"direct source reference count drifted: expected=66, actual={len(references)}"
        )
    return {
        "direct_reference_count": len(references),
        "direct_reference_counts_by_file": direct_counts,
        "mapsec_token_line_counts_by_file": mapsec_counts,
        "references": references,
    }


def scan_cfru_source_references(repo: Path) -> dict[str, Any]:
    """CFRUのraw direct-reference universeをpinned file/countで固定する。

    preprocessorで無効になる行も意図的に含める。実リンク有無はStage60のabsolute
    literal集合、profile、table contractsで別に判定するため、sourceから将来riskを
    消してしまわない。
    """

    references: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    source_dir = repo / "src"
    for path in sorted(source_dir.glob("**/*.c")):
        relative = path.relative_to(source_dir).as_posix()
        matches = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _DIRECT_REFERENCE_RE.search(line):
                matches.append(
                    {"file": relative, "line": number, "text": line.strip()}
                )
        if matches:
            counts[relative] = len(matches)
            references.extend(matches)
    if counts != dict(CFRU_DIRECT_REFERENCE_COUNTS):
        raise MapSectionConsumerAuditError(
            "CFRU direct source reference set drifted: "
            f"expected={dict(CFRU_DIRECT_REFERENCE_COUNTS)}, actual={counts}"
        )
    if len(references) != 41:
        raise MapSectionConsumerAuditError(
            f"CFRU direct source reference count drifted: expected=41, actual={len(references)}"
        )
    return {
        "direct_reference_count": len(references),
        "direct_reference_counts_by_file": counts,
        "references": references,
    }


def _validate_xrefs(
    raw: bytes,
    label: str,
    *,
    expected_direct_reads: tuple[tuple[int, int], ...],
) -> dict[str, Any]:
    targets = [target for target, _ in BL_XREFS.values()]
    found = find_thumb_bl_xrefs(raw, targets)
    rows: dict[str, Any] = {}
    for symbol, (target, expected) in BL_XREFS.items():
        actual = found[target]
        if actual != expected:
            raise MapSectionConsumerAuditError(
                f"{label} BL xrefs drifted: {symbol}@{target:#010x}: "
                f"expected={[hex(v) for v in expected]}, actual={[hex(v) for v in actual]}"
            )
        rows[symbol] = {
            "target": f"0x{target:08X}",
            "callers": [f"0x{value:08X}" for value in actual],
        }
    direct = find_direct_g_map_header_section_reads(raw)
    if direct != expected_direct_reads:
        raise MapSectionConsumerAuditError(
            f"{label} direct gMapHeader+0x14 roots drifted: "
            f"expected={expected_direct_reads}, actual={direct}"
        )
    return {
        "thumb_bl": rows,
        "direct_g_map_header_section_reads": [
            {
                "literal_load": f"0x{load:08X}",
                "section_load": f"0x{read:08X}",
            }
            for load, read in direct
        ],
    }


def _validate_cfru_literal_xrefs(stage60: bytes) -> dict[str, Any]:
    contracts = (
        (
            "GetCurrentRegionMapSectionId",
            0x08055B21,
            CFRU_GET_CURRENT_LITERAL_SITES,
        ),
        ("GetMapName", 0x080C5F5D, CFRU_GET_MAP_NAME_LITERAL_SITES),
        (
            "Overworld_GetMapHeaderByGroupAndId",
            0x08054AF9,
            CFRU_GET_MAP_HEADER_LITERAL_SITES,
        ),
    )
    result: dict[str, Any] = {}
    for symbol, thumb_pointer, expected in contracts:
        actual = tuple(
            address
            for address in find_word_occurrences(stage60, thumb_pointer)
            if address >= 0x09000000
        )
        if actual != expected:
            raise MapSectionConsumerAuditError(
                f"Stage60 CFRU literal xrefs drifted: {symbol}: "
                f"expected={[hex(v) for v in expected]}, actual={[hex(v) for v in actual]}"
            )
        result[symbol] = {
            "thumb_pointer": f"0x{thumb_pointer:08X}",
            "literal_sites": [f"0x{address:08X}" for address in actual],
        }
    return result


def _expanded_table_evidence(stage60: bytes) -> dict[str, Any]:
    raid = _rom_slice(stage60, RAID_TABLE_ADDRESS, RAID_TABLE_SIZE, "gRaidsByMapSection")
    if _sha(raid) != RAID_TABLE_SHA256:
        raise MapSectionConsumerAuditError("Stage60 gRaidsByMapSection digest mismatch")
    populated_raid_rows = [
        index
        for index in range(RAID_TABLE_ROW_COUNT)
        if any(raid[index * RAID_TABLE_ROW_SIZE:(index + 1) * RAID_TABLE_ROW_SIZE])
    ]
    if populated_raid_rows != [14]:
        raise MapSectionConsumerAuditError(
            f"Stage60 populated raid rows drifted: {populated_raid_rows}"
        )
    raid_pointer_sites = tuple(
        address
        for address in find_word_occurrences(stage60, RAID_TABLE_ADDRESS)
        if address >= 0x09000000
    )
    if raid_pointer_sites != (0x090F3854, 0x090F3A98, 0x090F3FC8):
        raise MapSectionConsumerAuditError(
            f"Stage60 raid table pointer roots drifted: {raid_pointer_sites}"
        )

    corners = _rom_slice(
        stage60,
        STOCK_MAP_SECTION_CORNERS_ADDRESS,
        STOCK_MAP_SECTION_LAYOUT_SIZE,
        "sMapSectionTopLeftCorners",
    )
    dimensions = _rom_slice(
        stage60,
        STOCK_MAP_SECTION_DIMENSIONS_ADDRESS,
        STOCK_MAP_SECTION_LAYOUT_SIZE,
        "sMapSectionDimensions",
    )
    if _sha(corners) != STOCK_MAP_SECTION_CORNERS_SHA256:
        raise MapSectionConsumerAuditError("Stage60 map-section corners digest mismatch")
    if _sha(dimensions) != STOCK_MAP_SECTION_DIMENSIONS_SHA256:
        raise MapSectionConsumerAuditError("Stage60 map-section dimensions digest mismatch")
    corner_pointer_sites = find_word_occurrences(
        stage60, STOCK_MAP_SECTION_CORNERS_ADDRESS
    )
    dimension_pointer_sites = find_word_occurrences(
        stage60, STOCK_MAP_SECTION_DIMENSIONS_ADDRESS
    )
    if corner_pointer_sites != (0x080C4F20, 0x09125FB8):
        raise MapSectionConsumerAuditError(
            f"Stage60 corner table pointer roots drifted: {corner_pointer_sites}"
        )
    if dimension_pointer_sites != (0x080C4F1C, 0x09125FBC):
        raise MapSectionConsumerAuditError(
            f"Stage60 dimension table pointer roots drifted: {dimension_pointer_sites}"
        )

    evolutions = _rom_slice(
        stage60,
        CFRU_EVOLUTION_TABLE_ADDRESS,
        CFRU_EVOLUTION_TABLE_SIZE,
        "gCfruVegaEvolutionTable",
    )
    if _sha(evolutions) != CFRU_EVOLUTION_TABLE_SHA256:
        raise MapSectionConsumerAuditError("Stage60 canonical evolution table digest mismatch")
    evolution_method_counts: dict[int, int] = {}
    for offset in range(0, len(evolutions), CFRU_EVOLUTION_ROW_SIZE):
        method = struct.unpack_from("<H", evolutions, offset)[0]
        evolution_method_counts[method] = evolution_method_counts.get(method, 0) + 1
    expected_method_counts = {
        0: 22838,
        1: 13,
        2: 1,
        4: 140,
        7: 33,
        8: 2,
        9: 2,
        10: 2,
        11: 3,
        12: 3,
        13: 1,
        14: 1,
        254: 1,
    }
    if evolution_method_counts != expected_method_counts:
        raise MapSectionConsumerAuditError(
            "Stage60 evolution method universe drifted: "
            f"expected={expected_method_counts}, actual={evolution_method_counts}"
        )
    if evolution_method_counts.get(CFRU_EVO_MAP_METHOD, 0) != 0:
        raise MapSectionConsumerAuditError("Stage60 EVO_MAP row is unexpectedly live")

    swarm_length = struct.unpack(
        "<H",
        _rom_slice(
            stage60,
            CFRU_SWARM_TABLE_LENGTH_ADDRESS,
            2,
            "gSwarmTableLength",
        ),
    )[0]
    if swarm_length != 0:
        raise MapSectionConsumerAuditError(
            f"Stage60 gSwarmTableLength drifted: expected=0, actual={swarm_length}"
        )

    raid_project_indices = [
        (section - STOCK_KANTO_MAPSEC_DYNAMIC) & 0xFF
        for section in PROJECT_SECTION_IDS
    ]
    roamer_project_indices = [
        (section - STOCK_KANTO_MAPSEC_START) & 0xFF
        for section in PROJECT_SECTION_IDS
    ]
    if (
        (min(raid_project_indices), max(raid_project_indices)) != (169, 221)
        or (min(roamer_project_indices), max(roamer_project_indices)) != (168, 220)
        or any(index < RAID_TABLE_ROW_COUNT for index in raid_project_indices)
        or any(index < STOCK_MAP_SECTION_LAYOUT_ROWS for index in roamer_project_indices)
    ):
        raise MapSectionConsumerAuditError("project underflow/index proof drifted")

    return {
        "raid": {
            "address": f"0x{RAID_TABLE_ADDRESS:08X}",
            "sha256": _sha(raid),
            "row_count": RAID_TABLE_ROW_COUNT,
            "row_size": RAID_TABLE_ROW_SIZE,
            "populated_rows": populated_raid_rows,
            "pointer_sites": [f"0x{value:08X}" for value in raid_pointer_sites],
            "project_index_range_after_u8_sub_87": [
                min(raid_project_indices),
                max(raid_project_indices),
            ],
            "all_project_indices_out_of_bounds": True,
        },
        "town_map_roamer_layout": {
            "row_count": STOCK_MAP_SECTION_LAYOUT_ROWS,
            "corners_address": f"0x{STOCK_MAP_SECTION_CORNERS_ADDRESS:08X}",
            "corners_sha256": _sha(corners),
            "dimensions_address": f"0x{STOCK_MAP_SECTION_DIMENSIONS_ADDRESS:08X}",
            "dimensions_sha256": _sha(dimensions),
            "corners_pointer_sites": [
                f"0x{value:08X}" for value in corner_pointer_sites
            ],
            "dimensions_pointer_sites": [
                f"0x{value:08X}" for value in dimension_pointer_sites
            ],
            "project_index_range_after_u8_sub_88": [
                min(roamer_project_indices),
                max(roamer_project_indices),
            ],
            "all_project_indices_out_of_bounds": True,
        },
        "evolution": {
            "address": f"0x{CFRU_EVOLUTION_TABLE_ADDRESS:08X}",
            "sha256": _sha(evolutions),
            "species_count": CFRU_EVOLUTION_SPECIES_COUNT,
            "rows_per_species": CFRU_EVOLUTION_ROWS_PER_SPECIES,
            "method_counts": {
                str(method): count
                for method, count in sorted(evolution_method_counts.items())
            },
            "evo_map_method": CFRU_EVO_MAP_METHOD,
            "evo_map_rows": 0,
        },
        "swarm": {
            "length_address": f"0x{CFRU_SWARM_TABLE_LENGTH_ADDRESS:08X}",
            "length": swarm_length,
            "map_section_comparisons_reachable": False,
        },
    }


def _pokedex_table_evidence(clean: bytes, stage60: bytes) -> dict[str, Any]:
    size = POKEDEX_KANTO_TABLE_ROWS * 4
    clean_table = _rom_slice(
        clean, POKEDEX_KANTO_TABLE_ADDRESS, size, "clean sDexAreas_Kanto"
    )
    stage60_table = _rom_slice(
        stage60, POKEDEX_KANTO_TABLE_ADDRESS, size, "Stage60 sDexAreas_Kanto"
    )
    if _sha(clean_table) != CLEAN_POKEDEX_KANTO_TABLE_SHA256:
        raise MapSectionConsumerAuditError("clean sDexAreas_Kanto digest mismatch")
    if _sha(stage60_table) != STAGE60_POKEDEX_KANTO_TABLE_SHA256:
        raise MapSectionConsumerAuditError("Stage60 sDexAreas_Kanto digest mismatch")
    for raw, label in ((clean, "clean"), (stage60, "Stage60")):
        for address in POKEDEX_TABLE_POINTER_SITES:
            pointer = struct.unpack(
                "<I", _rom_slice(raw, address, 4, f"{label} Pokédex table pointer")
            )[0]
            if pointer != POKEDEX_KANTO_TABLE_ADDRESS:
                raise MapSectionConsumerAuditError(
                    f"{label} Pokédex table pointer mismatch: {address:#010x}={pointer:#010x}"
                )
    clean_rows = [struct.unpack_from("<HH", clean_table, i * 4) for i in range(55)]
    stage60_rows = [struct.unpack_from("<HH", stage60_table, i * 4) for i in range(55)]
    project_hits = [
        {"table_index": index, "map_section": key, "dex_area": value}
        for index, (key, value) in enumerate(stage60_rows)
        if key in PROJECT_SECTION_IDS
    ]
    if project_hits != [
        {"table_index": 33, "map_section": 0, "dex_area": 0},
        {"table_index": 37, "map_section": 0, "dex_area": 0},
    ]:
        raise MapSectionConsumerAuditError(
            f"Stage60 project-key Pokédex hits drifted: {project_hits}"
        )
    return {
        "address": f"0x{POKEDEX_KANTO_TABLE_ADDRESS:08X}",
        "row_count": 55,
        "pointer_sites": [f"0x{value:08X}" for value in POKEDEX_TABLE_POINTER_SITES],
        "clean_sha256": _sha(clean_table),
        "stage60_sha256": _sha(stage60_table),
        "clean_keys": [key for key, _ in clean_rows],
        "stage60_keys": [key for key, _ in stage60_rows],
        "project_key_hits": project_hits,
        "conclusion": (
            "project 1..52は一致なし。project 0はStage60の無効化行(0,0)だけに一致し、"
            "markerは生成されない。線形探索なので境界外参照はない。"
        ),
    }


def inspect_candidate(raw: bytes) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for site in (
        *COVERED_BOUNDARY_SITES,
        *UNRESOLVED_SEMANTIC_SITES,
        *STAGE60_EXPANDED_SITES,
    ):
        actual = _rom_slice(raw, site.address, len(site.expected), site.name)
        rows.append(
            {
                "name": site.name,
                "address": f"0x{site.address:08X}",
                "state": "STAGE60_PREIMAGE" if actual == site.expected else "MODIFIED",
                "actual_hex": actual.hex(),
                "expected_stage60_hex": site.expected.hex(),
            }
        )
    return {"size": len(raw), "sha256": _sha(raw), "sites": rows}


def build_audit_report(root: Path, *, candidate_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    clean = _read(root / CLEAN_ROM_RELATIVE, "clean FireRed ROM")
    stage60 = _read(root / STAGE60_ROM_RELATIVE, "Stage 60 ROM")
    validate_rom_identity(
        clean, size=CLEAN_ROM_SIZE, sha256=CLEAN_ROM_SHA256, label="clean FireRed JPN Rev.0"
    )
    validate_rom_identity(
        stage60, size=STAGE60_ROM_SIZE, sha256=STAGE60_ROM_SHA256, label="Stage 60"
    )
    stock_sites = (*COVERED_BOUNDARY_SITES, *UNRESOLVED_SEMANTIC_SITES)
    verify_preimages(clean, stock_sites, label="clean FireRed")
    verify_preimages(stage60, stock_sites, label="Stage 60")
    verify_preimages(stage60, STAGE60_EXPANDED_SITES, label="Stage 60 linked CFRU")

    manifest = validate_project_manifest(root / MAP_SECTION_MANIFEST_RELATIVE)
    source_contract = validate_source_snapshot(root / DECOMP_RELATIVE)
    cfru_contract = validate_cfru_snapshot(
        root / CFRU_RELATIVE,
        root / CFRU_PROFILE_RELATIVE,
    )
    dpe_contract = validate_dpe_snapshot(root / DPE_RELATIVE)
    source_references = scan_source_references(root / DECOMP_RELATIVE)
    cfru_source_references = scan_cfru_source_references(root / CFRU_RELATIVE)
    clean_xrefs = _validate_xrefs(
        clean,
        "clean FireRed",
        expected_direct_reads=DIRECT_G_MAP_HEADER_READS,
    )
    stage60_xrefs = _validate_xrefs(
        stage60,
        "Stage 60",
        expected_direct_reads=STAGE60_DIRECT_G_MAP_HEADER_READS,
    )
    cfru_literal_xrefs = _validate_cfru_literal_xrefs(stage60)
    pokedex = _pokedex_table_evidence(clean, stage60)
    expanded_tables = _expanded_table_evidence(stage60)

    required = [
        row
        for row in CONSUMERS
        if row.status.startswith("ACTION_REQUIRED") or row.status == "POLICY_REQUIRED"
    ]
    dormant = [
        row
        for row in CONSUMERS
        if row.status.startswith("DORMANT_") or row.status == "DORMANT_RISK"
    ]
    dangerous_indices = [
        row
        for row in CONSUMERS
        if row.status == "ACTION_REQUIRED_DANGEROUS_INDEX"
    ]
    report: dict[str, Any] = {
        "schema_version": 2,
        "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
        "status": "FAIL_UNCOVERED_DANGEROUS_INDEX_CONSUMERS",
        "scope": (
            "FireRed stock plus Stage60 linked CFRU/DPE regionMapSectionId consumers "
            "for Stage61 project IDs 0..52"
        ),
        "inputs": {
            "clean_rom": {
                "path": str(CLEAN_ROM_RELATIVE),
                "size": len(clean),
                "sha256": _sha(clean),
            },
            "stage60_rom": {
                "path": str(STAGE60_ROM_RELATIVE),
                "size": len(stage60),
                "sha256": _sha(stage60),
            },
            "decomp": source_contract,
            "cfru": cfru_contract,
            "dpe": dpe_contract,
            "map_section_manifest": {
                "path": str(MAP_SECTION_MANIFEST_RELATIVE),
                "sha256": MAP_SECTION_MANIFEST_SHA256,
                "rows": manifest,
            },
        },
        "proof": {
            "clean_xrefs": clean_xrefs,
            "stage60_xrefs": stage60_xrefs,
            "cfru_literal_xrefs": cfru_literal_xrefs,
            "source_references": source_references,
            "cfru_source_references": cfru_source_references,
            "covered_boundary_preimages": [row.to_report() for row in COVERED_BOUNDARY_SITES],
            "unresolved_semantic_preimages": [
                row.to_report() for row in UNRESOLVED_SEMANTIC_SITES
            ],
            "stage60_expanded_preimages": [
                row.to_report() for row in STAGE60_EXPANDED_SITES
            ],
            "pokedex_table": pokedex,
            "expanded_tables": expanded_tables,
        },
        "consumers": [row.to_report() for row in CONSUMERS],
        "required_fixes": [row.to_report() for row in required],
        "dormant_risks": [row.to_report() for row in dormant],
        "conclusions": {
            "consumer_group_count": len(CONSUMERS),
            "direct_source_reference_count": 66,
            "cfru_direct_source_reference_count": 41,
            "clean_direct_g_map_header_read_count": len(DIRECT_G_MAP_HEADER_READS),
            "stage60_direct_g_map_header_read_count": len(
                STAGE60_DIRECT_G_MAP_HEADER_READS
            ),
            "required_fix_count": len(required),
            "dormant_risk_count": len(dormant),
            "uncovered_dangerous_index_count": len(dangerous_indices),
            "uncovered_raw_stock_table_index_consumers": [
                {
                    "consumer_id": row.consumer_id,
                    "domain": row.domain,
                    "severity": row.severity,
                    "effect": row.effect,
                }
                for row in dangerous_indices
            ],
            "memory_safety": (
                "GetMapName、Town Map、Flyの既知mapsec-88境界はStage61 hook対象。"
                "しかしStage60 linked CFRUのRaid mapsec-87とTown Map roamer mapsec-88は"
                "未変換であり、project 0..52の全値が各109-row tableの範囲外になる。"
            ),
            "semantic_safety": (
                "FAIL: BGM、preview、Pokémon memo、Pokédex、Quest Logに加え、"
                "linked CFRU raid/roamer/warp-previewがproject 0..52を理解しない。"
            ),
            "namespace_collision": (
                "MON_DATA_MET_LOCATION 0..52はHoennと衝突する。"
                "trainer memoはMON_DATA_MET_GAME等のprovenanceなしにglobal変換してはならない。"
            ),
            "roamer": (
                "stock roamerのPokédex pathはphysical group 3限定で現在安全。"
                "一方linked CFRU multi-roamer Town Map pathは任意map headerを読むため、"
                "groups 96..98へ配置した時点でstock座標表OOBになる。"
            ),
            "raid": (
                "FAIL/CRITICAL: project mapsecをu8(section-87)にすると169..221。"
                "raid table valid rows 0..108を越え、pointer read/dereferenceとflag aliasが発生する。"
            ),
            "evolution": (
                "EVO_MAP handlerはlinkedだが現行canonical tableのmethod 19 rowは0。"
                "DPE/T09でmap evolutionを導入する時点で再監査が必要。"
            ),
        },
    }
    selected_candidate = candidate_path
    if selected_candidate is None:
        default_candidate = root / CANDIDATE_ROM_RELATIVE
        if default_candidate.is_file():
            selected_candidate = default_candidate
    if selected_candidate is not None:
        candidate = _read(selected_candidate, "Stage 61 candidate ROM")
        report["candidate"] = {
            "path": str(selected_candidate),
            **inspect_candidate(candidate),
        }
    return report


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_audit_report(args.root, candidate_path=args.candidate)
    except MapSectionConsumerAuditError as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
