from __future__ import annotations

"""Stage 61 imported-Kanto Town Map/Fly integration plan.

This module deliberately keeps the three numeric namespaces separate:

* FireRed source map sections (88..142),
* Vega's existing runtime map sections (88..196), and
* imported-Kanto project map sections (0..52).

The stock region-map code assumes the first namespace and subtracts 88 while
placing the player cursor.  Stage 60 uses the same numbers for Vega names.
Consequently, feeding project IDs to the stock consumers is not safe even
after GetMapName itself is fixed.  ``build_region_map_plan`` emits the data and
expected-byte patch contract required by the Stage 61 builder.  Runtime hooks
must activate the project tables only while the physical map group is 96..98;
the stock trampolines preserve every existing Tohoku/Sevii path.
"""

from dataclasses import dataclass
import csv
import hashlib
from pathlib import Path
import struct
from typing import Iterable, Mapping, Sequence


ROM_BASE = 0x08000000
STAGE60_SHA256 = "3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"

PROJECT_SECTION_COUNT = 53
PROJECT_SECTION_MAX = PROJECT_SECTION_COUNT - 1
SOURCE_SECTION_START = 88
SOURCE_SECTION_END = 142
MAPSEC_NONE = 197
MAP_WIDTH = 22
MAP_HEIGHT = 15
LAYER_COUNT = 2
GRID_SIZE = MAP_WIDTH * MAP_HEIGHT * LAYER_COUNT
IMPORTED_KANTO_GROUPS = (96, 97, 98)
EXPANDED_FLAG_START = 0x0900
EXPANDED_FLAG_END = 0x18FF

# Japanese FireRed Rev.0 / Stage 60 exact addresses.  Code at every hook site
# is byte-identical between the fixed clean input and Stage 60.
CLEAN_KANTO_GRID = 0x083B9018
CLEAN_KANTO_REGION_GFX = 0x083B61A4
CLEAN_KANTO_TILEMAP = 0x083B7424
CFRU_STOCK_MAP_SECTION_CORNERS = 0x083B89E8
CFRU_STOCK_MAP_SECTION_DIMENSIONS = 0x083B8D00
CFRU_STOCK_MAP_SECTION_COUNT = 109
CFRU_SAFE_MAP_SECTION_COUNT = 256
CLEAN_KANTO_GRID_SHA256 = (
    "8e5f08171ea661a10dcee51ce154ba3e217a9365f94262e77a8e5c7db02d85f6"
)
# Stage 60 deliberately replaced this stock slot with Vega/Tōhoku data.  The
# different digest is evidence that a conditional clean-Kanto payload is
# required; overwriting or translating this table would regress Tōhoku.
STAGE60_TOHOKU_GRID_SHA256 = (
    "e0bb9785cdaa63b4c75590b1d38ce0e7a03d0cdf48dc98c5d309a3fb902657c2"
)


class RegionMapPlanError(RuntimeError):
    pass


@dataclass(frozen=True)
class SectionRecord:
    runtime_id: int
    source_id: int
    source_symbol: str
    source_name: str
    x: int
    y: int
    width: int
    height: int
    anchor_x: int
    anchor_y: int
    destination_group: int
    destination_map: int
    fly_x: int
    fly_y: int
    fly_enabled: bool
    source_visit_flag: int | None
    source_visit_flag_symbol: str | None


@dataclass(frozen=True)
class VisitFlagRequirement:
    runtime_id: int
    source_flag: int
    source_symbol: str
    category: str


@dataclass(frozen=True)
class PayloadRecord:
    name: str
    macro: str
    alignment: int
    data: bytes
    purpose: str


@dataclass(frozen=True)
class PatchSite:
    name: str
    address: int
    expected: bytes
    kind: str
    runtime_symbol: str
    trampoline: str | None = None
    owner: str = "stage61_region_map"


@dataclass(frozen=True)
class TrampolineSpec:
    name: str
    hook_address: int
    expected_prefix: bytes
    resume_address: int
    relocated_bl_offset: int | None = None
    relocated_bl_target: int | None = None
    preserve_four_args: bool = False


@dataclass(frozen=True)
class RegionMapPlan:
    sections: tuple[SectionRecord, ...]
    visit_flag_requirements: tuple[VisitFlagRequirement, ...]
    payloads: tuple[PayloadRecord, ...]
    patches: tuple[PatchSite, ...]
    trampolines: tuple[TrampolineSpec, ...]
    source_commit: str

    def payload(self, name: str) -> PayloadRecord:
        for row in self.payloads:
            if row.name == name:
                return row
        raise KeyError(name)

    def materialize_visit_flag_payload(
        self, runtime_flags: Mapping[int, int]
    ) -> PayloadRecord:
        """Resolve Kanto visit state into a project-owned flag namespace.

        Stage 60 already uses FireRed's 0x0890-series world-map flags for
        Tōhoku.  Imported Kanto map scripts are namespaced stubs and do not
        retain ``setworldmapflag`` either.  The Stage61 builder must therefore
        allocate one distinct expanded flag for each city/dungeon requirement
        and arrange for the physical-map entry path to set it.  Routes retain
        0xFFFF and are always classified as routes.
        """

        required = {row.runtime_id for row in self.visit_flag_requirements}
        supplied = set(runtime_flags)
        if supplied != required:
            missing = sorted(required - supplied)
            extra = sorted(supplied - required)
            raise RegionMapPlanError(
                f"Kanto visit flag domain mismatch: missing={missing}, extra={extra}"
            )
        values = [int(runtime_flags[key]) for key in sorted(runtime_flags)]
        if len(values) != len(set(values)):
            raise RegionMapPlanError("Kanto visit flags must be unique")
        if any(not EXPANDED_FLAG_START <= value <= EXPANDED_FLAG_END
               for value in values):
            raise RegionMapPlanError(
                "Kanto visit flags must use the 0x0900..0x18FF expanded window"
            )
        legacy = {row.source_flag for row in self.visit_flag_requirements}
        if legacy & set(values):
            raise RegionMapPlanError("Kanto visit flags alias stock/Tōhoku flags")
        table = [0xFFFF] * PROJECT_SECTION_COUNT
        for runtime_id, flag in runtime_flags.items():
            table[int(runtime_id)] = int(flag)
        return PayloadRecord(
            "kanto_visit_flags",
            "STAGE61_KANTO_VISIT_FLAGS",
            4,
            struct.pack("<53H", *table),
            "project-owned city/dungeon visit flags; 0xFFFF marks routes",
        )


_REPRESENTATIVE_SOURCE_MAPS: tuple[str, ...] = (
    "PalletTown",
    "ViridianCity",
    "PewterCity",
    "CeruleanCity",
    "LavenderTown",
    "VermilionCity",
    "CeladonCity",
    "FuchsiaCity",
    "CinnabarIsland",
    "IndigoPlateau_Exterior",
    "SaffronCity",
    "Route1",
    "Route2",
    "Route3",
    "Route4",
    "Route5",
    "Route6",
    "Route7",
    "Route8",
    "Route9",
    "Route10",
    "Route11",
    "Route12",
    "Route13",
    "Route14",
    "Route15",
    "Route16",
    "Route17",
    "Route18",
    "Route19",
    "Route20",
    "Route21_North",
    "Route22",
    "Route23",
    "Route24",
    "Route25",
    "ViridianForest",
    "MtMoon_1F",
    "SSAnne_Exterior",
    "UndergroundPath_NorthSouthTunnel",
    "UndergroundPath_EastWestTunnel",
    "DiglettsCave_B1F",
    "VictoryRoad_1F",
    "RocketHideout_B1F",
    "SilphCo_1F",
    "PokemonMansion_1F",
    "SafariZone_Center",
    "IndigoPlateau_Exterior",
    "RockTunnel_1F",
    "SeafoamIslands_1F",
    "PokemonTower_1F",
    "CeruleanCave_1F",
    "PowerPlant",
)

# Source GetPlayerPositionOnRegionMap_HandleOverrides plus the clean Kanto
# dungeon layer.  Diglett's Cave has two icons; the south/Vermilion-side icon
# is the deterministic fallback.  A production runtime may refine it from the
# escapeWarp, but never indexes the stock -88 tables with a project ID.
_DUNGEON_ANCHORS: Mapping[int, tuple[int, int]] = {
    36: (4, 6),
    37: (9, 3),
    38: (14, 9),
    39: (14, 7),
    40: (12, 6),
    41: (15, 9),
    42: (2, 4),
    43: (11, 6),
    44: (14, 6),
    45: (4, 14),
    46: (12, 12),
    47: (2, 3),
    48: (18, 3),
    49: (8, 14),
    50: (18, 6),
    51: (14, 3),
    52: (18, 4),
}

_CITY_HEAL_COORDS: tuple[tuple[int, int], ...] = (
    (6, 8),
    (26, 27),
    (17, 26),
    (22, 20),
    (6, 6),
    (15, 7),
    (48, 12),
    (25, 32),
    (14, 12),
    (11, 7),
    (24, 39),
)

_CITY_VISIT_FLAG_SYMBOLS: tuple[str, ...] = (
    "FLAG_WORLD_MAP_PALLET_TOWN",
    "FLAG_WORLD_MAP_VIRIDIAN_CITY",
    "FLAG_WORLD_MAP_PEWTER_CITY",
    "FLAG_WORLD_MAP_CERULEAN_CITY",
    "FLAG_WORLD_MAP_LAVENDER_TOWN",
    "FLAG_WORLD_MAP_VERMILION_CITY",
    "FLAG_WORLD_MAP_CELADON_CITY",
    "FLAG_WORLD_MAP_FUCHSIA_CITY",
    "FLAG_WORLD_MAP_CINNABAR_ISLAND",
    "FLAG_WORLD_MAP_INDIGO_PLATEAU_EXTERIOR",
    "FLAG_WORLD_MAP_SAFFRON_CITY",
)

_DUNGEON_VISIT_FLAG_SYMBOLS: tuple[str, ...] = (
    "FLAG_WORLD_MAP_VIRIDIAN_FOREST",
    "FLAG_WORLD_MAP_MT_MOON_1F",
    "FLAG_WORLD_MAP_SSANNE_EXTERIOR",
    "FLAG_WORLD_MAP_UNDERGROUND_PATH_NORTH_SOUTH_TUNNEL",
    "FLAG_WORLD_MAP_UNDERGROUND_PATH_EAST_WEST_TUNNEL",
    "FLAG_WORLD_MAP_DIGLETTS_CAVE_B1F",
    "FLAG_WORLD_MAP_VICTORY_ROAD_1F",
    "FLAG_WORLD_MAP_ROCKET_HIDEOUT_B1F",
    "FLAG_WORLD_MAP_SILPH_CO_1F",
    "FLAG_WORLD_MAP_POKEMON_MANSION_1F",
    "FLAG_WORLD_MAP_SAFARI_ZONE_CENTER",
    "FLAG_WORLD_MAP_POKEMON_LEAGUE_LORELEIS_ROOM",
    "FLAG_WORLD_MAP_ROCK_TUNNEL_1F",
    "FLAG_WORLD_MAP_SEAFOAM_ISLANDS_1F",
    "FLAG_WORLD_MAP_POKEMON_TOWER_1F",
    "FLAG_WORLD_MAP_CERULEAN_CAVE_1F",
    "FLAG_WORLD_MAP_POWER_PLANT",
)


def _source_visit_flag(runtime_id: int) -> tuple[int | None, str | None]:
    if runtime_id <= 10:
        return 0x0890 + runtime_id, _CITY_VISIT_FLAG_SYMBOLS[runtime_id]
    if runtime_id >= 36:
        index = runtime_id - 36
        return 0x08A4 + index, _DUNGEON_VISIT_FLAG_SYMBOLS[index]
    return None, None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rom_offset(address: int) -> int:
    if address < ROM_BASE:
        raise RegionMapPlanError(f"ROM address expected: 0x{address:08X}")
    return address - ROM_BASE


def _read_exact(rom: bytes, address: int, size: int) -> bytes:
    offset = _rom_offset(address)
    end = offset + size
    if offset < 0 or end > len(rom):
        raise RegionMapPlanError(
            f"ROM read out of range: 0x{address:08X}+0x{size:X}"
        )
    return rom[offset:end]


def _read_lz77_block(rom: bytes, address: int) -> bytes:
    offset = _rom_offset(address)
    if offset + 4 > len(rom) or rom[offset] != 0x10:
        raise RegionMapPlanError(f"LZ77 header missing at 0x{address:08X}")
    output_size = int.from_bytes(rom[offset + 1 : offset + 4], "little")
    cursor = offset + 4
    produced = 0
    while produced < output_size:
        if cursor >= len(rom):
            raise RegionMapPlanError("truncated LZ77 flag byte")
        flags = rom[cursor]
        cursor += 1
        for bit in range(8):
            if produced >= output_size:
                break
            if flags & (0x80 >> bit):
                if cursor + 2 > len(rom):
                    raise RegionMapPlanError("truncated LZ77 back-reference")
                produced += (rom[cursor] >> 4) + 3
                cursor += 2
            else:
                if cursor >= len(rom):
                    raise RegionMapPlanError("truncated LZ77 literal")
                produced += 1
                cursor += 1
    return rom[offset:cursor]


def _load_sections(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != PROJECT_SECTION_COUNT:
        raise RegionMapPlanError(
            f"Kanto section catalog must contain 53 rows, got {len(rows)}"
        )
    ids = [int(row["runtime_map_section_id"]) for row in rows]
    if ids != list(range(PROJECT_SECTION_COUNT)):
        raise RegionMapPlanError("runtime map-section IDs must be contiguous 0..52")
    return rows


def _load_crosswalk(path: Path) -> dict[str, tuple[int, int]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result: dict[str, tuple[int, int]] = {}
    for row in rows:
        source = row["source_map"]
        physical = (int(row["new_group_id"]), int(row["new_map_id"]))
        if source in result and result[source] != physical:
            raise RegionMapPlanError(f"ambiguous Kanto source map: {source}")
        result[source] = physical
    missing = [name for name in _REPRESENTATIVE_SOURCE_MAPS if name not in result]
    if missing:
        raise RegionMapPlanError(
            "representative Kanto maps are missing: " + ", ".join(missing)
        )
    return result


def _source_to_runtime(rows: Sequence[Mapping[str, str]]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for row in rows:
        source_id = int(row["source_map_section_id"])
        runtime_id = int(row["runtime_map_section_id"])
        if source_id in mapping:
            raise RegionMapPlanError(f"duplicate source map-section {source_id}")
        mapping[source_id] = runtime_id
    expected = set(range(88, 99)) | set(range(101, 143))
    if set(mapping) != expected:
        raise RegionMapPlanError("source map-section domain drifted from 53-row contract")
    return mapping


def translate_kanto_grid(
    source_grid: bytes, source_to_runtime: Mapping[int, int]
) -> bytes:
    if len(source_grid) != GRID_SIZE:
        raise RegionMapPlanError(
            f"Kanto grid must be {GRID_SIZE} bytes, got {len(source_grid)}"
        )
    translated = bytearray()
    for value in source_grid:
        if value == MAPSEC_NONE:
            translated.append(value)
        elif value == 99:  # Route 4 Pokémon Center icon -> project Route 4
            translated.append(source_to_runtime[104])
        elif value == 100:  # Route 10 Pokémon Center icon -> project Route 10
            translated.append(source_to_runtime[110])
        elif value in source_to_runtime:
            translated.append(source_to_runtime[value])
        else:
            raise RegionMapPlanError(
                f"unmapped source section {value} in clean Kanto grid"
            )
    return bytes(translated)


def _build_section_records(
    rows: Sequence[Mapping[str, str]],
    crosswalk: Mapping[str, tuple[int, int]],
) -> tuple[SectionRecord, ...]:
    records: list[SectionRecord] = []
    for runtime_id, row in enumerate(rows):
        x = int(row["x"])
        y = int(row["y"])
        width = int(row["width"])
        height = int(row["height"])
        if runtime_id in _DUNGEON_ANCHORS:
            anchor_x, anchor_y = _DUNGEON_ANCHORS[runtime_id]
        else:
            anchor_x = x + (width - 1) // 2
            anchor_y = y + (height - 1) // 2
        source_map = _REPRESENTATIVE_SOURCE_MAPS[runtime_id]
        destination_group, destination_map = crosswalk[source_map]
        if runtime_id < len(_CITY_HEAL_COORDS):
            fly_x, fly_y = _CITY_HEAL_COORDS[runtime_id]
            fly_enabled = True
        else:
            fly_x = fly_y = 0xFF
            fly_enabled = False
        source_visit_flag, source_visit_flag_symbol = _source_visit_flag(runtime_id)
        records.append(
            SectionRecord(
                runtime_id=runtime_id,
                source_id=int(row["source_map_section_id"]),
                source_symbol=row["source_map_section_symbol"],
                source_name=row["source_name"],
                x=x,
                y=y,
                width=width,
                height=height,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                destination_group=destination_group,
                destination_map=destination_map,
                fly_x=fly_x,
                fly_y=fly_y,
                fly_enabled=fly_enabled,
                source_visit_flag=source_visit_flag,
                source_visit_flag_symbol=source_visit_flag_symbol,
            )
        )
    return tuple(records)


def _pack_positions(sections: Iterable[SectionRecord]) -> bytes:
    # x/y/width/height are used for outdoor proportional cursor placement;
    # anchor_x/anchor_y are the fail-closed indoor/dungeon fallback.
    return b"".join(
        struct.pack(
            "<BBBBBB",
            row.x,
            row.y,
            row.width,
            row.height,
            row.anchor_x,
            row.anchor_y,
        )
        for row in sections
    )


def _pack_fly_records(sections: Iterable[SectionRecord]) -> bytes:
    # group/map/x/y/flags/runtime_id.  Production runtime uses SetWarpDestination
    # with the exact source heal coordinate for city records.  This avoids using
    # Vega's numerically colliding heal-location table.
    return b"".join(
        struct.pack(
            "<BBBBBB",
            row.destination_group,
            row.destination_map,
            row.fly_x,
            row.fly_y,
            1 if row.fly_enabled else 0,
            row.runtime_id,
        )
        for row in sections
    )


def _pack_legacy_fly_table(sections: Iterable[SectionRecord]) -> bytes:
    # Compatibility for Stage61DisplayNpcEvent_SetFlyWarpDestination's original
    # 3-byte ABI.  heal=0 deliberately selects physical group/map and never a
    # colliding Vega heal-location ID.  Prefer STAGE61_KANTO_FLY_RECORDS because
    # it retains the canonical landing coordinate.
    return b"".join(
        bytes((row.destination_group, row.destination_map, 0)) for row in sections
    )


def _pack_source_sections(sections: Iterable[SectionRecord]) -> bytes:
    rows = sorted(sections, key=lambda row: row.runtime_id)
    if [row.runtime_id for row in rows] != list(range(PROJECT_SECTION_COUNT)):
        raise RegionMapPlanError("project->source map-section domain mismatch")
    return bytes(row.source_id for row in rows)


def _pack_safe_roamer_layout(
    stage60: bytes,
    sections: Iterable[SectionRecord],
    *,
    stock_address: int,
    dimensions: bool,
) -> bytes:
    """Build a total 8-bit index table for CFRU's ``mapsec - 88`` ABI.

    CFRU truncates the subtraction to u8.  Imported project IDs 0..52 thus
    address rows 168..220, beyond the stock 109-row arrays.  Retain every
    stock row at 0..108 and fill those wrapped project rows with the exact
    Kanto top-left/dimension data; all other byte indices are zero-safe.
    """

    stock_offset = stock_address - ROM_BASE
    stock_size = CFRU_STOCK_MAP_SECTION_COUNT * 4
    stock = stage60[stock_offset : stock_offset + stock_size]
    if len(stock) != stock_size:
        raise RegionMapPlanError("CFRU stock roamer layout is outside ROM")
    result = bytearray(CFRU_SAFE_MAP_SECTION_COUNT * 4)
    result[:stock_size] = stock
    seen: set[int] = set()
    for row in sections:
        index = (row.runtime_id - SOURCE_SECTION_START) & 0xFF
        if index in seen or not 168 <= index <= 220:
            raise RegionMapPlanError("CFRU project roamer wrapped index mismatch")
        seen.add(index)
        values = (row.width, row.height) if dimensions else (row.x, row.y)
        struct.pack_into("<HH", result, index * 4, *values)
    if len(seen) != PROJECT_SECTION_COUNT:
        raise RegionMapPlanError("CFRU project roamer layout coverage mismatch")
    return bytes(result)


def _patch_sites() -> tuple[PatchSite, ...]:
    return (
        PatchSite(
            "region_map_gfx_decompress",
            0x080C14F2,
            bytes.fromhex("36f0edf9"),
            "thumb_bl",
            "Stage61RegionMap_DecompressGfx",
        ),
        PatchSite(
            "region_map_tilemap_decompress",
            0x080C153A,
            bytes.fromhex("06f1a9fa"),
            "thumb_bl",
            "Stage61RegionMap_DecompressTilemap",
        ),
        PatchSite(
            "get_mapsec_type",
            0x080C47C0,
            bytes.fromhex("00b50006000e5838"),
            "thumb_far_hook",
            "Stage61RegionMap_GetMapsecType",
            "stock_get_mapsec_type",
        ),
        PatchSite(
            "get_dungeon_mapsec_type",
            0x080C4A5C,
            bytes.fromhex("00b50006000e7e38"),
            "thumb_far_hook",
            "Stage61RegionMap_GetDungeonMapsecType",
            "stock_get_dungeon_mapsec_type",
        ),
        PatchSite(
            "get_player_position_on_region_map_overrides",
            0x080C4F24,
            bytes.fromhex("30b5fff7ddfe0004"),
            "thumb_far_hook",
            "Stage61RegionMap_GetPlayerPosition",
            "stock_get_player_position",
        ),
        PatchSite(
            "get_selected_map_section",
            0x080C5348,
            # This boundary receives (which, layer, y, x), so r3 is live.
            # Own the complete 16-byte argument-normalization prologue: a
            # compact 8-byte far jump would otherwise consume r3 as scratch.
            bytes.fromhex("30b50006000e051c09060c0e1204120c"),
            "thumb_far_hook",
            "Stage61RegionMap_GetSelectedMapSection",
            "stock_get_selected_map_section",
        ),
        # The display overlay owns this existing hook.  Listing it here makes
        # the normal Fly consumer dependency explicit to the Stage 61 builder.
        PatchSite(
            "set_fly_warp_destination",
            0x080C6460,
            bytes.fromhex("30b5000408494018"),
            "thumb_far_hook",
            "Stage61DisplayNpcEvent_SetFlyWarpDestination",
            owner="stage61_display_npc_event_audit",
        ),
    )


def _trampoline_specs() -> tuple[TrampolineSpec, ...]:
    return (
        TrampolineSpec(
            "stock_get_mapsec_type",
            0x080C47C0,
            bytes.fromhex("00b50006000e5838"),
            0x080C47C8,
        ),
        TrampolineSpec(
            "stock_get_dungeon_mapsec_type",
            0x080C4A5C,
            bytes.fromhex("00b50006000e7e38"),
            0x080C4A64,
        ),
        TrampolineSpec(
            "stock_get_player_position",
            0x080C4F24,
            bytes.fromhex("30b5fff7ddfe0004"),
            0x080C4F2C,
            relocated_bl_offset=2,
            relocated_bl_target=0x080C4CE4,
        ),
        TrampolineSpec(
            "stock_get_selected_map_section",
            0x080C5348,
            bytes.fromhex("30b50006000e051c09060c0e1204120c"),
            0x080C5358,
            # The copied prologue has normalized r0-r2 into r5/r4/r2, while
            # r3 still carries x and r4 is now live.  Preserve r0-r4 across
            # the far tail jump instead of borrowing any argument register.
            preserve_four_args=True,
        ),
    )


def thumb_bl(source: int, target: int) -> bytes:
    """Encode an ARMv4T Thumb BL at *source* to an odd/even target address."""
    target &= ~1
    delta = target - (source + 4)
    if delta & 1 or not -(1 << 22) <= delta < (1 << 22):
        raise RegionMapPlanError("Thumb BL target is unaligned or out of range")
    value = delta >> 1
    high = 0xF000 | ((value >> 11) & 0x7FF)
    low = 0xF800 | (value & 0x7FF)
    return struct.pack("<HH", high, low)


def _far_jump(target: int, register: int = 3) -> bytes:
    if not 0 <= register <= 7:
        raise RegionMapPlanError("Thumb literal jump requires a low register")
    return struct.pack(
        "<HHI", 0x4800 | (register << 8), 0x4700 | (register << 3), target | 1
    )


def _preserving_four_arg_far_jump(target: int) -> bytes:
    """Tail-jump without consuming r0-r3 or the caller's live r4."""

    return struct.pack(
        "<HHHHHHI",
        0xB410,  # push {r4}
        0x4C02,  # ldr r4, [pc, #8]
        0x46A4,  # mov ip, r4
        0xBC10,  # pop {r4}
        0x4760,  # bx ip
        0x46C0,  # nop / literal alignment
        target | 1,
    )


def materialize_trampoline(spec: TrampolineSpec, address: int) -> bytes:
    prefix = bytearray(spec.expected_prefix)
    if spec.relocated_bl_offset is not None:
        offset = spec.relocated_bl_offset
        if spec.relocated_bl_target is None or offset + 4 > len(prefix):
            raise RegionMapPlanError(f"invalid trampoline relocation: {spec.name}")
        try:
            prefix[offset : offset + 4] = thumb_bl(
                address + offset, spec.relocated_bl_target
            )
        except RegionMapPlanError:
            # Stage61 overlays live well beyond Thumb-1 BL's +/-4 MiB range.
            # The only relocated-call preimage currently required is:
            #   push; bl callee; trailing-instruction
            # Materialize a local BL thunk so LR retains its Thumb return bit,
            # then use literal BX jumps to the callee and stock resume point.
            if address & 3 or offset != 2 or len(prefix) != 8:
                raise RegionMapPlanError(
                    f"far-call trampoline layout unsupported: {spec.name}"
                )
            local_call = thumb_bl(address + 2, address + 12)
            return b"".join(
                (
                    bytes(prefix[:2]),
                    local_call,
                    bytes(prefix[6:]),
                    struct.pack("<HH", 0x4B02, 0x4718),
                    struct.pack("<HH", 0x4B00, 0x4718),
                    struct.pack("<II", spec.relocated_bl_target | 1,
                                spec.resume_address | 1),
                )
            )
    jump = (
        _preserving_four_arg_far_jump(spec.resume_address)
        if spec.preserve_four_args
        else _far_jump(spec.resume_address)
    )
    return bytes(prefix) + jump


def build_region_map_plan(
    root: Path,
    *,
    stage60_path: Path | None = None,
    clean_path: Path | None = None,
) -> RegionMapPlan:
    root = root.resolve()
    if stage60_path is None:
        stage60_path = root / "build/stages/60_wild_species_root_repair.gba"
    if clean_path is None:
        clean_path = root / "inputs/private/FireRed_JPN_Rev0_clean.gba"
    stage60 = stage60_path.read_bytes()
    clean = clean_path.read_bytes()
    if _sha256(stage60) != STAGE60_SHA256:
        raise RegionMapPlanError("Stage 60 exact-ROM identity mismatch")
    if _sha256(clean) != CLEAN_SHA256:
        raise RegionMapPlanError("clean FireRed JPN Rev.0 identity mismatch")

    section_rows = _load_sections(root / "content/kanto_map_sections.csv")
    crosswalk = _load_crosswalk(root / "reports/generated/kanto_v2_crosswalk.csv")
    source_to_runtime = _source_to_runtime(section_rows)
    clean_grid = _read_exact(clean, CLEAN_KANTO_GRID, GRID_SIZE)
    stage60_grid = _read_exact(stage60, CLEAN_KANTO_GRID, GRID_SIZE)
    if _sha256(clean_grid) != CLEAN_KANTO_GRID_SHA256:
        raise RegionMapPlanError("clean Kanto grid identity mismatch")
    if _sha256(stage60_grid) != STAGE60_TOHOKU_GRID_SHA256:
        raise RegionMapPlanError("Stage 60 Tōhoku grid identity mismatch")
    if stage60_grid == clean_grid:
        raise RegionMapPlanError("Stage 60 unexpectedly lost the Tōhoku grid")
    translated_grid = translate_kanto_grid(clean_grid, source_to_runtime)
    sections = _build_section_records(section_rows, crosswalk)
    visit_flag_requirements = tuple(
        VisitFlagRequirement(
            runtime_id=row.runtime_id,
            source_flag=int(row.source_visit_flag),
            source_symbol=str(row.source_visit_flag_symbol),
            category="CITY" if row.runtime_id <= 10 else "DUNGEON",
        )
        for row in sections
        if row.source_visit_flag is not None
    )

    patches = _patch_sites()
    for patch in patches:
        actual = _read_exact(stage60, patch.address, len(patch.expected))
        if actual != patch.expected:
            raise RegionMapPlanError(
                f"hook preimage mismatch at 0x{patch.address:08X}: "
                f"expected {patch.expected.hex()}, got {actual.hex()}"
            )

    gfx = _read_lz77_block(clean, CLEAN_KANTO_REGION_GFX)
    tilemap = _read_lz77_block(clean, CLEAN_KANTO_TILEMAP)
    if int.from_bytes(gfx[1:4], "little") != 10240:
        raise RegionMapPlanError("clean Kanto region graphics size drifted")
    if int.from_bytes(tilemap[1:4], "little") != 1200:
        raise RegionMapPlanError("clean Kanto tilemap size drifted")

    payloads = (
        PayloadRecord(
            "kanto_region_grid",
            "STAGE61_KANTO_REGION_GRID",
            4,
            translated_grid,
            "physical 96..98 only: project 0..52 map/dungeon grid",
        ),
        PayloadRecord(
            "kanto_section_positions",
            "STAGE61_KANTO_POSITION_TABLE",
            4,
            _pack_positions(sections),
            "53 section top-left/dimensions and safe player-cursor anchors",
        ),
        PayloadRecord(
            "kanto_fly_records",
            "STAGE61_KANTO_FLY_RECORDS",
            4,
            _pack_fly_records(sections),
            "physical destination plus exact source heal coordinate",
        ),
        PayloadRecord(
            "kanto_fly_destinations_legacy",
            "STAGE61_KANTO_FLY_TABLE",
            4,
            _pack_legacy_fly_table(sections),
            "3-byte compatibility table; never uses colliding Vega heal IDs",
        ),
        PayloadRecord(
            "kanto_source_section_ids",
            "STAGE61_KANTO_SOURCE_SECTION_IDS",
            4,
            _pack_source_sections(sections),
            "project 0..52 to exact FireRed source map-section IDs",
        ),
        PayloadRecord(
            "cfru_safe_roamer_corners",
            "STAGE61_CFRU_SAFE_ROAMER_CORNERS",
            4,
            _pack_safe_roamer_layout(
                stage60,
                sections,
                stock_address=CFRU_STOCK_MAP_SECTION_CORNERS,
                dimensions=False,
            ),
            "total u8 index table: stock 0..108 plus wrapped project 168..220",
        ),
        PayloadRecord(
            "cfru_safe_roamer_dimensions",
            "STAGE61_CFRU_SAFE_ROAMER_DIMENSIONS",
            4,
            _pack_safe_roamer_layout(
                stage60,
                sections,
                stock_address=CFRU_STOCK_MAP_SECTION_DIMENSIONS,
                dimensions=True,
            ),
            "total u8 index dimensions for CFRU Town Map roamer sprites",
        ),
        PayloadRecord(
            "kanto_region_gfx_lz",
            "STAGE61_KANTO_REGION_GFX",
            4,
            gfx,
            "clean FireRed Kanto Town Map tiles, conditional on group 96..98",
        ),
        PayloadRecord(
            "kanto_region_tilemap_lz",
            "STAGE61_KANTO_REGION_TILEMAP",
            4,
            tilemap,
            "clean FireRed Kanto Town Map layout, conditional on group 96..98",
        ),
    )

    return RegionMapPlan(
        sections=sections,
        visit_flag_requirements=visit_flag_requirements,
        payloads=payloads,
        patches=patches,
        trampolines=_trampoline_specs(),
        source_commit="c75f352304d529f6ba92d4f74b9cf8b5c3810788",
    )


__all__ = [
    "CLEAN_SHA256",
    "CLEAN_KANTO_GRID_SHA256",
    "EXPANDED_FLAG_END",
    "EXPANDED_FLAG_START",
    "IMPORTED_KANTO_GROUPS",
    "MAPSEC_NONE",
    "PROJECT_SECTION_COUNT",
    "PayloadRecord",
    "PatchSite",
    "RegionMapPlan",
    "RegionMapPlanError",
    "STAGE60_SHA256",
    "STAGE60_TOHOKU_GRID_SHA256",
    "SectionRecord",
    "TrampolineSpec",
    "VisitFlagRequirement",
    "build_region_map_plan",
    "materialize_trampoline",
    "thumb_bl",
    "translate_kanto_grid",
]
