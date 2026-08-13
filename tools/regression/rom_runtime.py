"""T17 Kanto map/QOL-B runtimeをstage 16へ決定的に結合する。

T14のJSON map modelをFireRedの実MapHeader ABIへserializeし、clean BPRJ01から
layout/tileset assetを複製する。Vega既存group/layout/wild tableは保持してrootだけを
repointする。全配置はT16 allocationを入力に中央allocatorへ通す。
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


TASK = "T17"
ROM_SIZE = 32 * 1024 * 1024
STAGE16 = Path("build/stages/16_content.gba")
STAGE16_META = Path("build/stages/16_content.json")
STAGE16_ALLOC = Path("build/stages/16_allocation.json")
STAGE17 = Path("build/stages/17_regression.gba")
STAGE17_META = Path("build/stages/17_regression.json")
STAGE17_ALLOC = Path("build/stages/17_allocation.json")
RUNTIME_BIN = Path("generated/runtime/t17_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/t17_runtime_symbols.json")

MAP_GROUPS_POINTER_SITE = 0x00054B0C
MAP_LAYOUTS_POINTER_SITE = 0x00054A54
WILD_HEADERS_POINTER_SITE = 0x0008257C
EXPECTED_MAP_GROUPS_ROOT = 0x08316758
EXPECTED_MAP_LAYOUTS_ROOT = 0x08312C3C
EXPECTED_WILD_HEADERS_ROOT = 0x08390B34
EXISTING_MAP_GROUP_COUNT = 43
EXPANDED_MAP_GROUP_COUNT = 99
EXISTING_MAP_LAYOUT_COUNT = 383
KANTO_GROUPS = (96, 97, 98)
KANTO_ENTRY = (96, 5)
VEGA_PORTAL_MAP = (4, 0)
VEGA_PORTAL_LOCAL_ID = 1
INTEGRATION_ALLOCATION_NAME = "regression_runtime_payload"
TRAINER_TABLE_ADDRESS = 0x081FDFD8
EXISTING_TRAINER_COUNT = 743
EXPANDED_TRAINER_COUNT = 917
TRAINER_RECORD_SIZE = 0x20
TRAINER_FIELD_POINTER_OFFSETS = (0, 4, 0x0A)
FLAG_SYS_GAME_CLEAR = 0x082C
KANTO_CERT_FLAGS = tuple(range(0x1400, 0x1408))
KANTO_LEAGUE_FLAGS = tuple(range(0x1408, 0x140D))

# source map, source object index, generated trainer key, completion flag,
# required project flag, and whether Vega Hall of Fame is also required.
PROGRESSION_OBJECTS: dict[str, tuple[int, str, int, int | None, bool]] = {
    "PewterCity_Gym": (0, "TRAINER_KEY_KANTO_GYM_01", KANTO_CERT_FLAGS[0], None, False),
    "CeruleanCity_Gym": (2, "TRAINER_KEY_KANTO_GYM_02", KANTO_CERT_FLAGS[1], KANTO_CERT_FLAGS[0], False),
    "VermilionCity_Gym": (0, "TRAINER_KEY_KANTO_GYM_03", KANTO_CERT_FLAGS[2], KANTO_CERT_FLAGS[1], False),
    "CeladonCity_Gym": (6, "TRAINER_KEY_KANTO_GYM_04", KANTO_CERT_FLAGS[3], KANTO_CERT_FLAGS[2], False),
    "FuchsiaCity_Gym": (6, "TRAINER_KEY_KANTO_GYM_05", KANTO_CERT_FLAGS[4], KANTO_CERT_FLAGS[3], True),
    "SaffronCity_Gym": (6, "TRAINER_KEY_KANTO_GYM_06", KANTO_CERT_FLAGS[5], KANTO_CERT_FLAGS[4], True),
    "CinnabarIsland_Gym": (7, "TRAINER_KEY_KANTO_GYM_07", KANTO_CERT_FLAGS[6], KANTO_CERT_FLAGS[5], True),
    "ViridianCity_Gym": (7, "TRAINER_KEY_KANTO_GYM_08", KANTO_CERT_FLAGS[7], KANTO_CERT_FLAGS[6], True),
    "PokemonLeague_LoreleisRoom": (0, "TRAINER_KEY_KANTO_LEAGUE_01", KANTO_LEAGUE_FLAGS[0], KANTO_CERT_FLAGS[7], True),
    "PokemonLeague_BrunosRoom": (0, "TRAINER_KEY_KANTO_LEAGUE_02", KANTO_LEAGUE_FLAGS[1], KANTO_LEAGUE_FLAGS[0], True),
    "PokemonLeague_AgathasRoom": (0, "TRAINER_KEY_KANTO_LEAGUE_03", KANTO_LEAGUE_FLAGS[2], KANTO_LEAGUE_FLAGS[1], True),
    "PokemonLeague_LancesRoom": (0, "TRAINER_KEY_KANTO_LEAGUE_04", KANTO_LEAGUE_FLAGS[3], KANTO_LEAGUE_FLAGS[2], True),
    "PokemonLeague_ChampionsRoom": (0, "TRAINER_KEY_KANTO_LEAGUE_05", KANTO_LEAGUE_FLAGS[4], KANTO_LEAGUE_FLAGS[3], True),
}

CONNECTION_DIRECTIONS = {"down": 1, "up": 2, "left": 3, "right": 4,
                         "dive": 5, "emerge": 6}
RUNTIME_DESTINATIONS = {"RUNTIME_UNION_ROOM", "RUNTIME_TRADE_CENTER",
                        "RUNTIME_DYNAMIC_WARP"}


class RuntimeBuildError(ValueError):
    """ROM ABI、入力hash、配置contractの違反。"""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _u32(raw: bytes | bytearray, offset: int, label: str = "u32") -> int:
    if offset < 0 or offset + 4 > len(raw):
        raise RuntimeBuildError(f"{label}: offset out of range: {offset:#x}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(pointer: int, size: int, label: str) -> int:
    offset = pointer - GBA_ROM_BASE
    if pointer & 1:
        offset = (pointer & ~1) - GBA_ROM_BASE
    if offset < 0 or offset + size > 16 * 1024 * 1024:
        raise RuntimeBuildError(f"{label}: invalid clean ROM pointer {pointer:#010x}")
    return offset


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


@dataclass(frozen=True)
class _Fixup:
    offset: int
    label: str
    thumb: bool = False


class _Blob:
    def __init__(self) -> None:
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[_Fixup] = []

    def align(self, alignment: int = 4, fill: int = 0) -> None:
        if alignment <= 0 or alignment & (alignment - 1):
            raise RuntimeBuildError("blob alignment must be a power of two")
        while len(self.data) % alignment:
            self.data.append(fill)

    def add(self, label: str, raw: bytes, alignment: int = 4) -> int:
        if label in self.labels:
            raise RuntimeBuildError(f"duplicate blob label: {label}")
        self.align(alignment)
        offset = len(self.data)
        self.labels[label] = offset
        self.data.extend(raw)
        return offset

    def reserve(self, label: str, size: int, alignment: int = 4) -> int:
        return self.add(label, bytes(size), alignment)

    def patch(self, offset: int, raw: bytes) -> None:
        if offset < 0 or offset + len(raw) > len(self.data):
            raise RuntimeBuildError(f"blob patch outside payload: {offset:#x}")
        self.data[offset:offset + len(raw)] = raw

    def pointer(self, offset: int, label: str, *, thumb: bool = False) -> None:
        self.fixups.append(_Fixup(offset, label, thumb))

    def finish(self, payload_offset: int) -> bytes:
        result = bytearray(self.data)
        for fixup in self.fixups:
            if fixup.label not in self.labels:
                raise RuntimeBuildError(f"unresolved blob label: {fixup.label}")
            address = GBA_ROM_BASE + payload_offset + self.labels[fixup.label]
            if fixup.thumb:
                address |= 1
            struct.pack_into("<I", result, fixup.offset, address)
        return bytes(result)


def _compile_qol_b(root: Path, load_address: int) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        raise RuntimeBuildError("ARM GNU toolchain is required for QOL-B runtime")
    source = root / "overlays/qol_b/qol_b.c"
    header = root / "overlays/qol_b/qol_b.h"
    if not source.is_file() or not header.is_file():
        raise RuntimeBuildError("QOL-B source/header is missing")
    with tempfile.TemporaryDirectory(prefix="vega-t17-qol-") as temporary:
        directory = Path(temporary)
        linker = directory / "linker.ld"
        elf = directory / "qol_b.elf"
        binary = directory / "qol_b.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        command = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-nostdlib", "-Wl,--build-id=none",
            f"-I{source.parent}", f"-Wl,-T,{linker}", str(source), "-o", str(elf),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise RuntimeBuildError("QOL-B ARM link failed: " + completed.stderr.strip())
        undefined = subprocess.run(
            [nm, "-u", str(elf)], capture_output=True, text=True, check=False
        )
        if undefined.returncode or undefined.stdout.strip():
            raise RuntimeBuildError("QOL-B ARM image has undefined symbols: " + undefined.stdout.strip())
        extracted = subprocess.run(
            [objcopy, "-O", "binary", str(elf), str(binary)],
            capture_output=True, text=True, check=False,
        )
        if extracted.returncode:
            raise RuntimeBuildError("QOL-B objcopy failed: " + extracted.stderr.strip())
        symbols_raw = subprocess.run(
            [nm, "-n", "--defined-only", str(elf)], capture_output=True,
            text=True, check=False,
        )
        if symbols_raw.returncode:
            raise RuntimeBuildError("QOL-B nm failed: " + symbols_raw.stderr.strip())
        symbols: dict[str, int] = {}
        for line in symbols_raw.stdout.splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2].startswith("QolB_"):
                symbols[fields[2]] = int(fields[0], 16)
        required = {
            "QolB_Search", "QolB_MoveSelected", "QolB_ReleaseSelected",
            "QolB_TakeHeldItems", "QolB_FieldPcAllowed", "QolB_RelearnMove",
            "QolB_EggBasketAdvance", "QolB_AutoBattleAllowed", "QolB_RuntimeProbe",
            "QolB_PortalWarp", "QolB_ReturnWarp",
        }
        if required - set(symbols):
            raise RuntimeBuildError(f"QOL-B entrypoints missing: {sorted(required - set(symbols))}")
        raw = binary.read_bytes()
        if not raw or len(raw) > 8192:
            raise RuntimeBuildError(f"unexpected QOL-B runtime size: {len(raw)}")
        return raw, symbols


def _charmap(root: Path) -> tuple[dict[str, int], list[str]]:
    mapping: dict[str, int] = {}
    path = root / "vendor/upstream/CFRU-JP/charmap.tbl"
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            value = int(line[:2], 16)
        except ValueError:
            continue
        token = line[3:]
        if token != "$":
            mapping.setdefault(token, value)
    tokens = sorted((token for token in mapping if token), key=lambda item: (-len(item), item))
    return mapping, tokens


def _encode_text(text: str, mapping: Mapping[str, int], tokens: Sequence[str]) -> bytes:
    text = text.replace("\n", "\\n")
    result = bytearray()
    cursor = 0
    while cursor < len(text):
        for token in tokens:
            if text.startswith(token, cursor):
                result.append(mapping[token])
                cursor += len(token)
                break
        else:
            raise RuntimeBuildError(f"unencodable game text at {text[cursor:]!r}")
    result.append(0xFF)
    return bytes(result)


def _lz77_size(raw: bytes, pointer: int) -> tuple[int, int]:
    offset = _rom_offset(pointer, 4, "tileset LZ77")
    if raw[offset] != 0x10:
        raise RuntimeBuildError(f"tileset graphics at {pointer:#010x} is not GBA LZ77")
    decompressed = raw[offset + 1] | (raw[offset + 2] << 8) | (raw[offset + 3] << 16)
    produced = 0
    cursor = offset + 4
    while produced < decompressed:
        if cursor >= len(raw):
            raise RuntimeBuildError("truncated LZ77 flags")
        flags = raw[cursor]
        cursor += 1
        for bit in range(7, -1, -1):
            if produced >= decompressed:
                break
            if flags & (1 << bit):
                if cursor + 2 > len(raw):
                    raise RuntimeBuildError("truncated LZ77 back-reference")
                produced += ((raw[cursor] >> 4) & 0xF) + 3
                cursor += 2
            else:
                if cursor >= len(raw):
                    raise RuntimeBuildError("truncated LZ77 literal")
                produced += 1
                cursor += 1
    return cursor - offset, decompressed


def _metatile_paths(root: Path) -> dict[str, Path]:
    source = root / "vendor/upstream/pokefirered/src/data/tilesets/metatiles.h"
    expression = re.compile(
        r"const u(?:16|32) (g(?:Metatiles|MetatileAttributes)_[A-Za-z0-9_]+)"
        r"\[\] = INCBIN_U(?:16|32)\(\"([^\"]+)\"\);"
    )
    result = {
        symbol: root / "vendor/upstream/pokefirered" / logical
        for symbol, logical in expression.findall(source.read_text(encoding="utf-8"))
    }
    if len(result) < 100:
        raise RuntimeBuildError("failed to parse fixed tileset metatile paths")
    return result


def _canonical_maps(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted((root / "generated/maps/kanto").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if "map_header" not in value:
            continue
        if value["map_header"]["scope_decision"] not in {"INCLUDE", "REBUILD"}:
            continue
        value["_path"] = path.relative_to(root).as_posix()
        result.append(value)
    result.sort(key=lambda row: (
        int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"]),
        row["map_header"]["map_key"],
    ))
    keys = [row["map_header"]["map_key"] for row in result]
    coordinates = [(int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"]))
                   for row in result]
    if len(result) != 253 or len(set(keys)) != 253 or len(set(coordinates)) != 253:
        raise RuntimeBuildError("T14 operational map set must contain 253 unique maps")
    if set(group for group, _ in coordinates) != set(KANTO_GROUPS):
        raise RuntimeBuildError("Kanto physical maps must use groups 96..98")
    return result


def _source_locations(root: Path, clean: bytes) -> tuple[dict[str, tuple[int, int]], list[int]]:
    groups = json.loads(
        (root / "vendor/upstream/pokefirered/data/maps/map_groups.json").read_text(encoding="utf-8")
    )
    order = groups["group_order"]
    if len(order) != EXISTING_MAP_GROUP_COUNT:
        raise RuntimeBuildError("clean map group count drift")
    locations = {
        name: (group_index, map_index)
        for group_index, group_name in enumerate(order)
        for map_index, name in enumerate(groups[group_name])
    }
    root_pointer = _u32(clean, MAP_GROUPS_POINTER_SITE, "clean gMapGroups site")
    if root_pointer != EXPECTED_MAP_GROUPS_ROOT:
        raise RuntimeBuildError(f"clean gMapGroups root drift: {root_pointer:#010x}")
    root_offset = _rom_offset(root_pointer, len(order) * 4, "clean gMapGroups")
    pointers = [_u32(clean, root_offset + index * 4, "clean map group") for index in range(len(order))]
    return locations, pointers


def _source_header(clean: bytes, locations: Mapping[str, tuple[int, int]],
                   group_pointers: Sequence[int], source: str) -> tuple[int, int]:
    if source not in locations:
        raise RuntimeBuildError(f"source map missing from clean map groups: {source}")
    group, number = locations[source]
    group_offset = _rom_offset(group_pointers[group], (number + 1) * 4, f"source group {group}")
    header_pointer = _u32(clean, group_offset + number * 4, f"source header {source}")
    header_offset = _rom_offset(header_pointer, 0x1C, f"source header {source}")
    return header_pointer, header_offset


def _find_portal_object(stage: bytes) -> tuple[int, int]:
    root_pointer = _u32(stage, MAP_GROUPS_POINTER_SITE, "stage16 gMapGroups site")
    if root_pointer != EXPECTED_MAP_GROUPS_ROOT:
        raise RuntimeBuildError(f"stage16 gMapGroups root drift: {root_pointer:#010x}")
    root = root_pointer - GBA_ROM_BASE
    group_pointer = _u32(stage, root + VEGA_PORTAL_MAP[0] * 4, "Vega portal group")
    header_pointer = _u32(stage, group_pointer - GBA_ROM_BASE + VEGA_PORTAL_MAP[1] * 4,
                          "Vega portal map header")
    header = header_pointer - GBA_ROM_BASE
    events_pointer = _u32(stage, header + 4, "Vega portal events")
    events = events_pointer - GBA_ROM_BASE
    count = stage[events]
    objects_pointer = _u32(stage, events + 4, "Vega portal objects")
    objects = objects_pointer - GBA_ROM_BASE
    for index in range(count):
        offset = objects + index * 0x18
        if stage[offset] == VEGA_PORTAL_LOCAL_ID:
            return offset, _u32(stage, offset + 0x10, "Vega portal old script")
    raise RuntimeBuildError("Vega portal local object 1 was not found")


def _previous_requests(root: Path) -> list[dict[str, object]]:
    report = json.loads((root / STAGE16_ALLOC).read_text(encoding="utf-8"))
    requests = []
    for row in report["allocations"]:
        requests.append({
            "name": row["name"], "region": row["region"], "size": row["size"],
            "alignment": row["alignment"], "start": row["start"],
            "owner": row["owner"], "purpose": row["purpose"],
            "content_sha256": row["content_sha256"],
        })
    return requests


def _allocation(root: Path, size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(root)
    requests.append({
        "name": INTEGRATION_ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 4,
        "owner": TASK,
        "purpose": "Kanto map roots/assets/wild tables, portal, and QOL-B runtime",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    row = next(item for item in report["allocations"] if item["name"] == INTEGRATION_ALLOCATION_NAME)
    return row, report


def _trainer_party_rows(root: Path) -> tuple[dict[str, int], dict[str, list[dict[str, str]]], dict[str, str]]:
    trainer_ids = {row["trainer_key"]: int(row["id"]) for row in _rows(root / "manifests/trainer_ids.csv")}
    parties: dict[str, list[dict[str, str]]] = defaultdict(list)
    profiles: dict[str, str] = {}
    for filename in ("kanto_trainers.csv", "tohoku_trainers.csv"):
        for row in _rows(root / "manifests" / filename):
            if row["status"] != "ACTIVE":
                continue
            parties[row["trainer_key"]].append(row)
            profiles[row["trainer_key"]] = row["ai_profile_key"]

    rentals = {row["rental_key"]: row for row in _rows(root / "manifests/facility_rentals.csv")
               if row["status"] == "ACTIVE"}
    for trainer in _rows(root / "manifests/facility_trainers.csv"):
        if trainer["status"] != "ACTIVE":
            continue
        key = trainer["facility_trainer_key"]
        profiles[key] = trainer["ai_profile_key"]
        for slot in range(1, 7):
            rental_key = trainer[f"rental_key{slot}"]
            if rental_key not in rentals:
                raise RuntimeBuildError(f"{key}: unresolved facility rental {rental_key}")
            rental = dict(rentals[rental_key])
            rental["party_slot"] = str(slot)
            rental["iv_floor"] = "31"
            parties[key].append(rental)

    if set(trainer_ids) != set(parties):
        missing = sorted(set(trainer_ids) - set(parties))
        extra = sorted(set(parties) - set(trainer_ids))
        raise RuntimeBuildError(f"T16 trainer binding mismatch: missing={missing} extra={extra}")
    for key, rows in parties.items():
        rows.sort(key=lambda row: int(row["party_slot"]))
        if not 1 <= len(rows) <= 6 or [int(row["party_slot"]) for row in rows] != list(range(1, len(rows) + 1)):
            raise RuntimeBuildError(f"{key}: trainer party slots are not contiguous 1..6")
    return trainer_ids, dict(parties), profiles


def _trainer_name(root: Path, key: str) -> bytes:
    mapping, tokens = _charmap(root)
    if "KANTO_GYM" in key:
        label = "KG" + key[-2:]
    elif "KANTO_LEAGUE" in key:
        label = "KL" + key[-2:]
    elif "TOHOKU" in key:
        label = "TR" + key[-2:]
    else:
        label = "FAC" + key[-1:]
    encoded = _encode_text(label, mapping, tokens)
    if len(encoded) > 6:
        raise RuntimeBuildError(f"trainer name exceeds six-byte Vega ABI: {key}")
    return encoded.ljust(6, b"\0")


def _trainer_runtime(root: Path, blob: _Blob, stage: bytes) -> dict[str, Any]:
    trainer_ids, parties, profiles = _trainer_party_rows(root)
    species_ids = {row["species_key"]: int(row["id"]) for row in _rows(root / "manifests/species_ids.csv")}
    move_ids = {row["move_key"]: int(row["id"]) for row in _rows(root / "manifests/move_ids.csv")}
    item_ids = {row["item_key"]: int(row["id"]) for row in _rows(root / "manifests/item_ids.csv")}
    profile_bits = {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5}

    old_offset = TRAINER_TABLE_ADDRESS - GBA_ROM_BASE
    old_size = EXISTING_TRAINER_COUNT * TRAINER_RECORD_SIZE
    original = stage[old_offset:old_offset + old_size]
    if len(original) != old_size:
        raise RuntimeBuildError("Vega trainer table is truncated")
    table = bytearray(original + bytes((EXPANDED_TRAINER_COUNT - EXISTING_TRAINER_COUNT) * TRAINER_RECORD_SIZE))
    table_offset = blob.add("trainer_table", bytes(table), 4)

    bound_rows = 0
    metadata_rows: list[dict[str, Any]] = []
    for key in sorted(trainer_ids, key=lambda item: trainer_ids[item]):
        trainer_id = trainer_ids[key]
        if not EXISTING_TRAINER_COUNT <= trainer_id < EXPANDED_TRAINER_COUNT:
            raise RuntimeBuildError(f"{key}: generated trainer id outside append range: {trainer_id}")
        rows = parties[key]
        party_raw = bytearray()
        for row in rows:
            species_key = row["species_key"]
            item_key = row.get("item_key", "ITEM_KEY_NONE")
            moves = [row[f"move{slot}_key"] for slot in range(1, 5)]
            if species_key not in species_ids or item_key not in item_ids or any(move not in move_ids for move in moves):
                raise RuntimeBuildError(f"{key}: unresolved trainer species/move/item registry key")
            level = int(row["level"])
            if not 1 <= level <= 100:
                raise RuntimeBuildError(f"{key}: trainer level outside 1..100")
            iv_floor = int(row.get("iv_floor", "31"))
            encoded_iv = min(255, iv_floor * 8 + 7)
            party_raw += struct.pack(
                "<8H", encoded_iv, level, species_ids[species_key], item_ids[item_key],
                *(move_ids[move] for move in moves),
            )
        party_label = f"trainer_party::{key}"
        blob.add(party_label, bytes(party_raw), 4)

        template_id = 350 if "GYM" in key or "TOHOKU" in key else 410 if "LEAGUE" in key else 1
        record = bytearray(original[template_id * TRAINER_RECORD_SIZE:(template_id + 1) * TRAINER_RECORD_SIZE])
        record[0] = 3  # held item plus explicit four-move party ABI
        record[4:10] = _trainer_name(root, key)
        record[0x0A:0x12] = bytes(8)
        record[0x12] = 0
        struct.pack_into("<I", record, 0x14, profile_bits[profiles[key]])
        record[0x18] = len(rows)
        struct.pack_into("<I", record, 0x1C, 0)
        record_offset = table_offset + trainer_id * TRAINER_RECORD_SIZE
        blob.patch(record_offset, record)
        blob.pointer(record_offset + 0x1C, party_label)
        bound_rows += len(rows)
        metadata_rows.append({
            "trainer_key": key, "id": trainer_id, "party_size": len(rows),
            "ai_profile": profiles[key], "party_sha256": _sha(bytes(party_raw)),
        })

    return {
        "address": 0, "existing_count": EXISTING_TRAINER_COUNT,
        "expanded_count": EXPANDED_TRAINER_COUNT,
        "generated_trainers": len(metadata_rows), "production_rows_bound": bound_rows,
        "record_size": TRAINER_RECORD_SIZE, "existing_prefix_sha256": _sha(original),
        "rows": metadata_rows,
    }


def _progression_script(blob: _Blob, label: str, trainer_id: int,
                        completion_flag: int, required_flag: int | None,
                        hall_of_fame: bool) -> None:
    script = bytearray([0x5A])  # faceplayer
    gate_fixups: list[int] = []
    if required_flag is not None:
        script += bytes([0x2B]) + struct.pack("<H", required_flag)
        gate_fixups.append(len(script) + 2)
        script += bytes([0x06, 0x00]) + bytes(4)
    if hall_of_fame:
        script += bytes([0x2B]) + struct.pack("<H", FLAG_SYS_GAME_CLEAR)
        gate_fixups.append(len(script) + 2)
        script += bytes([0x06, 0x00]) + bytes(4)
    script += bytes([0x5C, 0x00]) + struct.pack("<HH", trainer_id, 0)
    intro_fixup = len(script)
    script += bytes(4)
    defeat_fixup = len(script)
    script += bytes(4)
    script += bytes([0x29]) + struct.pack("<H", completion_flag)
    script += bytes([0x0F, 0x00])
    complete_fixup = len(script)
    script += bytes(4) + bytes([0x09, 0x06, 0x02])
    offset = blob.add(label, bytes(script), 4)
    for relative in gate_fixups:
        blob.pointer(offset + relative, "text_progression_locked_script")
    blob.pointer(offset + intro_fixup, "text_progression_intro")
    blob.pointer(offset + defeat_fixup, "text_progression_defeat")
    blob.pointer(offset + complete_fixup, "text_progression_complete")


def _progression_scripts(root: Path, blob: _Blob, trainer_ids: Mapping[str, int]) -> None:
    mapping, tokens = _charmap(root)
    blob.add("text_progression_intro", _encode_text("カントー にんていせんを はじめます！", mapping, tokens), 1)
    blob.add("text_progression_defeat", _encode_text("みごとな しょうりです！", mapping, tokens), 1)
    blob.add("text_progression_complete", _encode_text("にんてい きろくを こうしんしました", mapping, tokens), 1)
    locked = bytearray([0x0F, 0x00]) + bytes(4) + bytes([0x09, 0x06, 0x02])
    locked_offset = blob.add("text_progression_locked_script", bytes(locked), 4)
    text_offset = blob.add("text_progression_locked", _encode_text("まだ ちょうせん できません", mapping, tokens), 1)
    blob.pointer(locked_offset + 2, "text_progression_locked")
    for source, (_, trainer_key, completion, required, hof) in PROGRESSION_OBJECTS.items():
        if trainer_key not in trainer_ids:
            raise RuntimeBuildError(f"progression trainer id missing: {trainer_key}")
        _progression_script(blob, f"progress::{source}", trainer_ids[trainer_key], completion, required, hof)


def _script_main(root: Path, blob: _Blob, qol_probe: str,
                 portal_warp: str, return_warp: str) -> None:
    mapping, tokens = _charmap(root)
    blob.add("text_portal_prompt", _encode_text("カントーは レベル68いじょうです！\nわたりますか？", mapping, tokens), 1)
    blob.add("text_portal_locked", _encode_text("まだ ふねは うごいていません", mapping, tokens), 1)
    blob.add("text_return_prompt", _encode_text("トーホクへ もどりますか？", mapping, tokens), 1)

    portal = bytearray([0x6A, 0x5A, 0x23, 0, 0, 0, 0])
    portal += bytes([0x2B]) + struct.pack("<H", FLAG_SYS_GAME_CLEAR)
    portal += bytes([0x06, 0x01]) + bytes(4)
    portal += bytes([0x2B]) + struct.pack("<H", 0x0824)
    portal += bytes([0x06, 0x00]) + bytes(4)
    portal += bytes([0x2B]) + struct.pack("<H", 0x114B)
    portal += bytes([0x06, 0x00]) + bytes(4)
    portal += bytes([0x05]) + bytes(4)
    portal_offset = blob.add("script_portal", bytes(portal), 4)
    blob.pointer(portal_offset + 3, qol_probe, thumb=True)
    blob.pointer(portal_offset + 12, "script_portal_prompt")
    blob.pointer(portal_offset + 21, "script_portal_locked")
    blob.pointer(portal_offset + 30, "script_portal_locked")
    blob.pointer(portal_offset + 35, "script_portal_prompt")

    locked = bytearray([0x0F, 0x00]) + bytes(4) + bytes([0x09, 0x04, 0x6C, 0x02])
    locked_offset = blob.add("script_portal_locked", bytes(locked), 4)
    blob.pointer(locked_offset + 2, "text_portal_locked")
    prompt = bytearray([0x0F, 0x00]) + bytes(4) + bytes([0x09, 0x05])
    prompt += bytes([0x21]) + struct.pack("<HH", 0x800D, 1)
    prompt += bytes([0x06, 0x01]) + bytes(4) + bytes([0x6C, 0x02])
    prompt_offset = blob.add("script_portal_prompt", bytes(prompt), 4)
    blob.pointer(prompt_offset + 2, "text_portal_prompt")
    blob.pointer(prompt_offset + 15, "script_portal_travel")
    portal_travel_offset = blob.add(
        "script_portal_travel", bytes([0x23]) + bytes(4) + bytes([0x02]), 4
    )
    blob.pointer(portal_travel_offset + 1, portal_warp, thumb=True)

    returned = bytearray([0x6A, 0x5A, 0x23, 0, 0, 0, 0, 0x0F, 0x00])
    returned += bytes(4) + bytes([0x09, 0x05, 0x21])
    returned += struct.pack("<HH", 0x800D, 1)
    returned += bytes([0x06, 0x01]) + bytes(4) + bytes([0x6C, 0x02])
    return_offset = blob.add("script_return", bytes(returned), 4)
    blob.pointer(return_offset + 3, qol_probe, thumb=True)
    blob.pointer(return_offset + 9, "text_return_prompt")
    blob.pointer(return_offset + 22, "script_return_travel")
    return_travel_offset = blob.add(
        "script_return_travel", bytes([0x23]) + bytes(4) + bytes([0x02]), 4
    )
    blob.pointer(return_travel_offset + 1, return_warp, thumb=True)
    blob.add("script_map_none", b"\x00", 1)


def _build_blob(root: Path, stage: bytes, clean: bytes, payload_offset: int) -> tuple[bytes, dict[str, Any]]:
    maps = _canonical_maps(root)
    locations, clean_group_pointers = _source_locations(root, clean)
    source_headers: dict[str, int] = {}
    source_header_offsets: dict[str, int] = {}
    layout_pointers: dict[str, int] = {}
    tileset_pointers: dict[str, int] = {}
    tileset_name_by_pointer: dict[int, str] = {}
    map_by_key = {row["map_header"]["map_key"]: row for row in maps}

    for row in maps:
        header = row["map_header"]
        source = header["source_map"]
        pointer, offset = _source_header(clean, locations, clean_group_pointers, source)
        source_headers[source] = pointer
        source_header_offsets[source] = offset
        layout_pointer = _u32(clean, offset, f"{source} layout")
        layout_name = header["layout"]
        prior = layout_pointers.setdefault(layout_name, layout_pointer)
        if prior != layout_pointer:
            raise RuntimeBuildError(f"layout pointer mismatch for {layout_name}")
        layout_offset = _rom_offset(layout_pointer, 0x1C, f"layout {layout_name}")
        for tileset_name, field in ((row["layout"]["primary_tileset"], 0x10),
                                    (row["layout"]["secondary_tileset"], 0x14)):
            tileset_pointer = _u32(clean, layout_offset + field, f"{layout_name} tileset")
            prior_tileset = tileset_pointers.setdefault(tileset_name, tileset_pointer)
            if prior_tileset != tileset_pointer:
                raise RuntimeBuildError(f"tileset pointer mismatch for {tileset_name}")
            if tileset_pointer in tileset_name_by_pointer and tileset_name_by_pointer[tileset_pointer] != tileset_name:
                raise RuntimeBuildError("clean tileset pointer aliases different symbols")
            tileset_name_by_pointer[tileset_pointer] = tileset_name

    if len(layout_pointers) != 180 or len(tileset_pointers) != 51:
        raise RuntimeBuildError(
            f"unexpected runtime inventory: layouts={len(layout_pointers)} tilesets={len(tileset_pointers)}"
        )

    blob = _Blob()
    runtime_header_offset = blob.reserve("runtime_header", 64, 16)
    qol_load = GBA_ROM_BASE + payload_offset + ((len(blob.data) + 3) & ~3)
    qol_raw, qol_symbols = _compile_qol_b(root, qol_load)
    qol_offset = blob.add("qol_b_runtime", qol_raw, 4)
    if qol_offset + GBA_ROM_BASE + payload_offset != qol_load:
        raise RuntimeBuildError("QOL-B linker address disagrees with blob placement")
    for name, address in qol_symbols.items():
        relative = address - qol_load
        if relative < 0 or relative >= len(qol_raw):
            raise RuntimeBuildError(f"QOL-B symbol outside binary: {name}")
        blob.labels[f"qol::{name}"] = qol_offset + relative
    _script_main(root, blob, "qol::QolB_RuntimeProbe",
                 "qol::QolB_PortalWarp", "qol::QolB_ReturnWarp")
    trainer_meta = _trainer_runtime(root, blob, stage)
    trainer_ids, _, _ = _trainer_party_rows(root)
    _progression_scripts(root, blob, trainer_ids)

    metatile_paths = _metatile_paths(root)
    layout_catalog = {
        item["id"]: item
        for item in json.loads(
            (root / "vendor/upstream/pokefirered/data/layouts/layouts.json").read_text(encoding="utf-8")
        )["layouts"]
        if item.get("id")
    }
    tileset_meta: list[dict[str, Any]] = []
    for name in sorted(tileset_pointers):
        pointer = tileset_pointers[name]
        offset = _rom_offset(pointer, 0x18, name)
        raw_struct = bytearray(clean[offset:offset + 0x18])
        if raw_struct[0] != 1:
            raise RuntimeBuildError(f"unsupported uncompressed tileset: {name}")
        graphics_pointer = _u32(raw_struct, 4, f"{name} graphics")
        palette_pointer = _u32(raw_struct, 8, f"{name} palettes")
        metatiles_pointer = _u32(raw_struct, 0x0C, f"{name} metatiles")
        attributes_pointer = _u32(raw_struct, 0x14, f"{name} attributes")
        graphics_size, decompressed_size = _lz77_size(clean, graphics_pointer)
        symbol_suffix = name.removeprefix("gTileset_")
        metatiles_path = metatile_paths.get(f"gMetatiles_{symbol_suffix}")
        attributes_path = metatile_paths.get(f"gMetatileAttributes_{symbol_suffix}")
        if not metatiles_path or not attributes_path or not metatiles_path.is_file() or not attributes_path.is_file():
            raise RuntimeBuildError(f"fixed source asset size missing for {name}")
        assets = {
            "graphics": clean[_rom_offset(graphics_pointer, graphics_size, name):
                              _rom_offset(graphics_pointer, graphics_size, name) + graphics_size],
            "palettes": clean[_rom_offset(palette_pointer, 512, name):
                              _rom_offset(palette_pointer, 512, name) + 512],
            "metatiles": clean[_rom_offset(metatiles_pointer, metatiles_path.stat().st_size, name):
                               _rom_offset(metatiles_pointer, metatiles_path.stat().st_size, name) + metatiles_path.stat().st_size],
            "attributes": clean[_rom_offset(attributes_pointer, attributes_path.stat().st_size, name):
                                _rom_offset(attributes_pointer, attributes_path.stat().st_size, name) + attributes_path.stat().st_size],
        }
        for kind, raw in assets.items():
            blob.add(f"tileset::{name}::{kind}", raw, 4)
        struct_offset = blob.add(f"tileset::{name}", bytes(raw_struct), 4)
        blob.pointer(struct_offset + 4, f"tileset::{name}::graphics")
        blob.pointer(struct_offset + 8, f"tileset::{name}::palettes")
        blob.pointer(struct_offset + 0x0C, f"tileset::{name}::metatiles")
        blob.patch(struct_offset + 0x10, bytes(4))  # clean callback must not enter overwritten code
        blob.pointer(struct_offset + 0x14, f"tileset::{name}::attributes")
        tileset_meta.append({
            "name": name, "source_pointer": pointer,
            "is_secondary": bool(raw_struct[1]), "graphics_size": graphics_size,
            "graphics_decompressed_size": decompressed_size,
            "palettes_size": 512, "metatiles_size": len(assets["metatiles"]),
            "attributes_size": len(assets["attributes"]),
            "assets_sha256": {key: _sha(value) for key, value in assets.items()},
        })

    layout_ids = {name: EXISTING_MAP_LAYOUT_COUNT + index + 1
                  for index, name in enumerate(sorted(layout_pointers))}
    layout_meta: list[dict[str, Any]] = []
    for name in sorted(layout_pointers):
        pointer = layout_pointers[name]
        offset = _rom_offset(pointer, 0x1C, name)
        raw_layout = bytearray(clean[offset:offset + 0x1C])
        width, height = struct.unpack_from("<ii", raw_layout, 0)
        border_width, border_height = raw_layout[0x18], raw_layout[0x19]
        if width <= 0 or height <= 0 or width * height > 65536:
            raise RuntimeBuildError(f"invalid clean layout dimensions for {name}: {width}x{height}")
        map_size = width * height * 2
        border_size = border_width * border_height * 2
        primary_pointer = _u32(raw_layout, 0x10, f"{name} primary")
        secondary_pointer = _u32(raw_layout, 0x14, f"{name} secondary")
        primary_name = tileset_name_by_pointer.get(primary_pointer)
        secondary_name = tileset_name_by_pointer.get(secondary_pointer)
        if not primary_name or not secondary_name:
            raise RuntimeBuildError(f"layout {name} references an unregistered tileset")
        catalog = layout_catalog.get(name)
        if catalog is None:
            raise RuntimeBuildError(f"fixed source layout metadata missing for {name}")
        map_raw = (
            root / "vendor/upstream/pokefirered" / catalog["blockdata_filepath"]
        ).read_bytes()
        border_raw = (
            root / "vendor/upstream/pokefirered" / catalog["border_filepath"]
        ).read_bytes()
        if len(map_raw) != map_size or len(border_raw) != border_size:
            raise RuntimeBuildError(f"source layout dimensions disagree for {name}")
        canonical = next(row for row in maps if row["map_header"]["layout"] == name)
        if (len(map_raw) != canonical["layout"]["blockdata_size"]
                or _sha(map_raw) != canonical["layout"]["blockdata_sha256"]
                or len(border_raw) != canonical["layout"]["border_size"]
                or _sha(border_raw) != canonical["layout"]["border_sha256"]):
            raise RuntimeBuildError(f"T14 clean layout hash drift for {name}")
        blob.add(f"layout::{name}::map", map_raw, 4)
        blob.add(f"layout::{name}::border", border_raw, 4)
        layout_offset = blob.add(f"layout::{name}", bytes(raw_layout), 4)
        blob.pointer(layout_offset + 8, f"layout::{name}::border")
        blob.pointer(layout_offset + 0x0C, f"layout::{name}::map")
        blob.pointer(layout_offset + 0x10, f"tileset::{primary_name}")
        blob.pointer(layout_offset + 0x14, f"tileset::{secondary_name}")
        layout_meta.append({
            "name": name, "id": layout_ids[name], "source_pointer": pointer,
            "width": width, "height": height, "border_width": border_width,
            "border_height": border_height, "map_size": map_size,
            "border_size": border_size, "primary_tileset": primary_name,
            "secondary_tileset": secondary_name,
        })

    map_header_labels: dict[str, str] = {}
    map_meta: list[dict[str, Any]] = []
    redirected_runtime_warps = 0
    for row in maps:
        header = row["map_header"]
        key = header["map_key"]
        group, number = int(header["group_id"]), int(header["map_id"])
        warp_raw = bytearray()
        for warp in row["warps"]:
            if warp["dest_map"] in RUNTIME_DESTINATIONS:
                # Link/elevator dynamic destinations require state owned by the original
                # FireRed scripts. Those scripts are intentionally not imported. Route the
                # tile to Vermilion's safe outdoor door instead of leaving a trap/invalid map.
                redirected_runtime_warps += 1
                destination_group, destination_number, warp_id = KANTO_ENTRY[0], KANTO_ENTRY[1], 3
            else:
                destination = map_by_key.get(warp["dest_map"])
                if destination is None:
                    raise RuntimeBuildError(f"{key}: unresolved runtime warp {warp['dest_map']}")
                destination_group = int(destination["map_header"]["group_id"])
                destination_number = int(destination["map_header"]["map_id"])
                warp_id_text = str(warp["dest_warp_id"])
                warp_id = 0x7F if warp_id_text == "WARP_ID_DYNAMIC" else int(warp_id_text, 10)
            if not 0 <= warp_id <= 0xFF:
                raise RuntimeBuildError(f"{key}: invalid warp id {warp_id}")
            warp_raw += struct.pack(
                "<hhBBBB", int(warp["x"]), int(warp["y"]), int(warp["elevation"]),
                warp_id, destination_number, destination_group,
            )
        warp_label = f"map::{key}::warps"
        if warp_raw:
            blob.add(warp_label, bytes(warp_raw), 4)

        object_label = f"map::{key}::objects"
        object_raw = bytearray()
        object_scripts: list[str] = []
        if (group, number) == KANTO_ENTRY:
            _, vermilion_offset = _source_header(clean, locations, clean_group_pointers, "VermilionCity")
            source_events_pointer = _u32(clean, vermilion_offset + 4, "clean Vermilion events")
            source_events = _rom_offset(source_events_pointer, 0x14, "clean Vermilion events")
            source_objects_pointer = _u32(clean, source_events + 4, "clean Vermilion objects")
            source_objects = _rom_offset(source_objects_pointer, 6 * 0x18, "clean Vermilion objects")
            return_object = bytearray(clean[source_objects + 5 * 0x18:source_objects + 6 * 0x18])
            return_object[0] = 1
            struct.pack_into("<H", return_object, 0x14, 0)
            object_raw += return_object
            object_scripts.append("script_return")

        source_name = header["source_map"]
        progression = PROGRESSION_OBJECTS.get(source_name)
        if progression is not None:
            source_object_index = progression[0]
            source_header = source_header_offsets[source_name]
            source_events_pointer = _u32(clean, source_header + 4, f"{source_name} events")
            source_events = _rom_offset(source_events_pointer, 0x14, f"{source_name} events")
            source_count = clean[source_events]
            if source_object_index >= source_count:
                raise RuntimeBuildError(f"{source_name}: progression object index outside source events")
            source_objects_pointer = _u32(clean, source_events + 4, f"{source_name} objects")
            source_objects = _rom_offset(
                source_objects_pointer, source_count * 0x18, f"{source_name} objects"
            )
            at = source_objects + source_object_index * 0x18
            progression_object = bytearray(clean[at:at + 0x18])
            progression_object[0] = len(object_scripts) + 1
            struct.pack_into("<H", progression_object, 0x14, 0)
            object_raw += progression_object
            object_scripts.append(f"progress::{source_name}")

        object_count = len(object_scripts)
        if object_count:
            object_offset = blob.add(object_label, bytes(object_raw), 4)
            for index, script_label in enumerate(object_scripts):
                blob.pointer(object_offset + index * 0x18 + 0x10, script_label)

        events = bytearray(struct.pack("<BBBBIIII", object_count, len(warp_raw) // 8, 0, 0,
                                       0, 0, 0, 0))
        events_offset = blob.add(f"map::{key}::events", bytes(events), 4)
        if object_count:
            blob.pointer(events_offset + 4, object_label)
        if warp_raw:
            blob.pointer(events_offset + 8, warp_label)

        connection_raw = bytearray()
        for connection in row["connections"]:
            destination = map_by_key.get(connection["map"])
            if destination is None:
                raise RuntimeBuildError(f"{key}: unresolved connection {connection['map']}")
            direction = CONNECTION_DIRECTIONS.get(connection["direction"])
            if direction is None:
                raise RuntimeBuildError(f"{key}: unsupported connection direction")
            connection_raw += struct.pack(
                "<B3xiBB2x", direction, int(connection["offset"]),
                int(destination["map_header"]["group_id"]),
                int(destination["map_header"]["map_id"]),
            )
        connections_struct_label: str | None = None
        if connection_raw:
            connection_data_label = f"map::{key}::connection_data"
            blob.add(connection_data_label, bytes(connection_raw), 4)
            connections_struct_label = f"map::{key}::connections"
            connections_offset = blob.add(
                connections_struct_label,
                struct.pack("<iI", len(connection_raw) // 12, 0), 4,
            )
            blob.pointer(connections_offset + 4, connection_data_label)

        source_offset = source_header_offsets[header["source_map"]]
        raw_header = bytearray(clean[source_offset:source_offset + 0x1C])
        header_label = f"map::{key}::header"
        map_header_offset = blob.add(header_label, bytes(raw_header), 4)
        blob.pointer(map_header_offset, f"layout::{header['layout']}")
        blob.pointer(map_header_offset + 4, f"map::{key}::events")
        blob.pointer(map_header_offset + 8, "script_map_none")
        if connections_struct_label:
            blob.pointer(map_header_offset + 0x0C, connections_struct_label)
        else:
            blob.patch(map_header_offset + 0x0C, bytes(4))
        struct.pack_into("<H", blob.data, map_header_offset + 0x12, layout_ids[header["layout"]])
        map_header_labels[key] = header_label
        map_meta.append({
            "map_key": key, "source_map": header["source_map"], "group": group,
            "map": number, "layout_id": layout_ids[header["layout"]],
            "warp_count": len(warp_raw) // 8, "connection_count": len(connection_raw) // 12,
            "object_count": object_count, "logical_code": header["logical_code"],
            "classification": header["classification"],
        })

    safe_header = map_header_labels[map_by_key["KANTO_OUTDOOR_VERMILION_CITY"]["map_header"]["map_key"]]
    group_labels: dict[int, str] = {}
    for group in KANTO_GROUPS:
        group_maps = [item for item in map_meta if item["group"] == group]
        maximum = max(int(item["map"]) for item in group_maps)
        table_offset = blob.reserve(f"map_group::{group}", (maximum + 1) * 4, 4)
        labels = {int(item["map"]): map_header_labels[str(item["map_key"])] for item in group_maps}
        for number in range(maximum + 1):
            blob.pointer(table_offset + number * 4, labels.get(number, safe_header))
        group_labels[group] = f"map_group::{group}"
    filler_group_offset = blob.reserve("map_group::filler", 4, 4)
    blob.pointer(filler_group_offset, safe_header)

    stage_groups_root = _u32(stage, MAP_GROUPS_POINTER_SITE, "stage16 gMapGroups")
    if stage_groups_root != EXPECTED_MAP_GROUPS_ROOT:
        raise RuntimeBuildError("stage16 map group root no longer matches expected bytes")
    stage_groups_offset = stage_groups_root - GBA_ROM_BASE
    root_offset = blob.reserve("map_groups_root", EXPANDED_MAP_GROUP_COUNT * 4, 4)
    for group in range(EXPANDED_MAP_GROUP_COUNT):
        if group < EXISTING_MAP_GROUP_COUNT:
            pointer = _u32(stage, stage_groups_offset + group * 4, "stage16 map group pointer")
            blob.patch(root_offset + group * 4, struct.pack("<I", pointer))
        elif group in group_labels:
            blob.pointer(root_offset + group * 4, group_labels[group])
        else:
            blob.pointer(root_offset + group * 4, "map_group::filler")

    stage_layouts_root = _u32(stage, MAP_LAYOUTS_POINTER_SITE, "stage16 gMapLayouts")
    if stage_layouts_root != EXPECTED_MAP_LAYOUTS_ROOT:
        raise RuntimeBuildError("stage16 map layout root no longer matches expected bytes")
    stage_layouts_offset = stage_layouts_root - GBA_ROM_BASE
    layouts_root_offset = blob.reserve(
        "map_layouts_root", (EXISTING_MAP_LAYOUT_COUNT + len(layout_pointers)) * 4, 4
    )
    for index in range(EXISTING_MAP_LAYOUT_COUNT):
        pointer = _u32(stage, stage_layouts_offset + index * 4, "stage16 map layout pointer")
        blob.patch(layouts_root_offset + index * 4, struct.pack("<I", pointer))
    for index, name in enumerate(sorted(layout_pointers)):
        blob.pointer(layouts_root_offset + (EXISTING_MAP_LAYOUT_COUNT + index) * 4,
                     f"layout::{name}")

    species_by_key = {row["species_key"]: int(row["id"])
                      for row in _rows(root / "manifests/species_ids.csv")}
    encounters_by_location: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(root / "manifests/kanto_encounters.csv"):
        if row["status"] == "ACTIVE" and row["species_key"] in species_by_key:
            encounters_by_location[row["logical_location_key"]].append(row)
    wild_entries: list[dict[str, Any]] = []
    wild_info_labels: dict[tuple[int, int], list[str]] = {}
    slot_counts = (12, 5, 5, 10)
    for item in map_meta:
        if item["classification"] not in {"OUTDOOR", "DUNGEON"}:
            continue
        candidates = encounters_by_location.get(str(item["logical_code"]), [])
        if not candidates:
            continue
        labels: list[str] = []
        for method_index, slot_count in enumerate(slot_counts):
            slots = bytearray()
            for slot in range(slot_count):
                candidate = candidates[(slot + method_index) % len(candidates)]
                low = max(1, min(100, int(candidate["level_min"])))
                high = max(low, min(100, int(candidate["level_max"])))
                species = species_by_key[candidate["species_key"]]
                slots += struct.pack("<BBH", low, high, species)
            slot_label = f"wild::{item['group']}::{item['map']}::{method_index}::slots"
            info_label = f"wild::{item['group']}::{item['map']}::{method_index}::info"
            blob.add(slot_label, bytes(slots), 4)
            info_offset = blob.add(info_label, bytes([20, 0, 0, 0]) + bytes(4), 4)
            blob.pointer(info_offset + 4, slot_label)
            labels.append(info_label)
        wild_info_labels[(int(item["group"]), int(item["map"]))] = labels
        wild_entries.append({
            "group": item["group"], "map": item["map"],
            "logical_code": item["logical_code"], "candidate_species": len(candidates),
            "level_min": min(max(1, int(row["level_min"])) for row in candidates),
            "level_max": max(min(100, int(row["level_max"])) for row in candidates),
        })

    wild_root = _u32(stage, WILD_HEADERS_POINTER_SITE, "stage16 wild root")
    if wild_root != EXPECTED_WILD_HEADERS_ROOT:
        raise RuntimeBuildError("stage16 wild root no longer matches expected bytes")
    wild_offset = wild_root - GBA_ROM_BASE
    original_count = 0
    while True:
        record = stage[wild_offset + original_count * 20:wild_offset + (original_count + 1) * 20]
        if len(record) != 20:
            raise RuntimeBuildError("unterminated stage16 wild header table")
        if record[0] == 0xFF and record[1] == 0xFF:
            terminator = record
            break
        original_count += 1
        if original_count > 1024:
            raise RuntimeBuildError("stage16 wild header count is unreasonable")
    original_wild = stage[wild_offset:wild_offset + original_count * 20]
    wild_root_offset = blob.add("wild_headers_root", original_wild, 4)
    for coordinate in sorted(wild_info_labels):
        labels = wild_info_labels[coordinate]
        record_offset = len(blob.data)
        blob.data.extend(struct.pack("<BBHIIII", coordinate[0], coordinate[1], 0, 0, 0, 0, 0))
        for index, label in enumerate(labels):
            blob.pointer(record_offset + 4 + index * 4, label)
    blob.data.extend(terminator)

    runtime_size = len(blob.data)
    struct.pack_into(
        "<8sIIIIIIII", blob.data, runtime_header_offset,
        b"VEGA17\0\0", 1, runtime_size, len(map_meta), len(layout_meta),
        len(tileset_meta), len(wild_entries), original_count, len(qol_raw),
    )
    blob.pointer(runtime_header_offset + 40, "map_groups_root")
    blob.pointer(runtime_header_offset + 44, "map_layouts_root")
    blob.pointer(runtime_header_offset + 48, "wild_headers_root")
    blob.pointer(runtime_header_offset + 52, "script_portal")
    blob.pointer(runtime_header_offset + 56, "script_return")
    blob.pointer(runtime_header_offset + 60, "qol::QolB_RuntimeProbe", thumb=True)
    payload = blob.finish(payload_offset)
    trainer_relative = blob.labels["trainer_table"]
    trainer_size = EXPANDED_TRAINER_COUNT * TRAINER_RECORD_SIZE
    trainer_meta["address"] = GBA_ROM_BASE + payload_offset + trainer_relative
    trainer_meta["sha256"] = _sha(payload[trainer_relative:trainer_relative + trainer_size])
    trainer_meta["pointer_field_offsets"] = list(TRAINER_FIELD_POINTER_OFFSETS)

    metadata = {
        "payload": {
            "magic": "VEGA17", "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset, "size": len(payload),
            "sha256": _sha(payload), "expected_fill": "FF",
        },
        "maps": {
            "physical_count": len(map_meta), "groups": list(KANTO_GROUPS),
            "entry": {"group": KANTO_ENTRY[0], "map": KANTO_ENTRY[1],
                      "warp_id": 0xFF, "x": 20, "y": 20},
            "existing_groups_preserved": EXISTING_MAP_GROUP_COUNT,
            "expanded_group_count": EXPANDED_MAP_GROUP_COUNT,
            "safe_redirected_runtime_warps": redirected_runtime_warps,
            "rows": map_meta,
        },
        "layouts": {
            "existing_count": EXISTING_MAP_LAYOUT_COUNT,
            "appended_count": len(layout_meta),
            "expanded_count": EXISTING_MAP_LAYOUT_COUNT + len(layout_meta),
            "rows": layout_meta,
        },
        "tilesets": {"count": len(tileset_meta), "rows": tileset_meta},
        "wild": {
            "original_header_count": original_count,
            "original_headers_sha256": _sha(original_wild),
            "kanto_header_count": len(wild_entries), "rows": wild_entries,
        },
        "qol_b": {
            "binary_offset": payload_offset + qol_offset,
            "binary_address": GBA_ROM_BASE + payload_offset + qol_offset,
            "size": len(qol_raw), "sha256": _sha(qol_raw),
            "entrypoints": {name: address | 1 for name, address in sorted(qol_symbols.items())},
            "portal_callnative": True, "runtime_probe_marker": 0x0B17,
        },
        "trainers": trainer_meta,
        "progression": {
            "physical_battle_objects": len(PROGRESSION_OBJECTS),
            "certification_flags": list(KANTO_CERT_FLAGS),
            "league_flags": list(KANTO_LEAGUE_FLAGS),
            "hall_of_fame_flag": FLAG_SYS_GAME_CLEAR,
            "final_objective": "KANTO_LEAGUE_CLEAR",
            "final_objective_flag": KANTO_LEAGUE_FLAGS[-1],
            "ordered": True,
        },
        "symbols": {
            label: GBA_ROM_BASE + payload_offset + relative
            for label, relative in sorted(blob.labels.items())
            if label in {"map_groups_root", "map_layouts_root", "wild_headers_root",
                         "script_portal", "script_portal_prompt", "script_portal_travel",
                         "script_return", "script_return_travel", "trainer_table"}
            or label.startswith("qol::") or label.startswith("progress::")
        },
    }
    return payload, metadata


def _patch_expected(output: bytearray, site: int, expected: bytes, replacement: bytes,
                    label: str, evidence: list[dict[str, Any]]) -> None:
    actual = bytes(output[site:site + len(expected)])
    if actual != expected:
        raise RuntimeBuildError(
            f"{label}: expected bytes {expected.hex()} at {site:#x}, got {actual.hex()}"
        )
    if len(replacement) != len(expected):
        raise RuntimeBuildError(f"{label}: replacement width mismatch")
    output[site:site + len(replacement)] = replacement
    evidence.append({
        "label": label, "site_offset": site, "site_address": GBA_ROM_BASE + site,
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    })


def _trainer_pointer_sites(stage: bytes) -> list[tuple[int, int]]:
    expected_counts = {0: 20, 4: 3, 0x0A: 1}
    result: list[tuple[int, int]] = []
    for field_offset in TRAINER_FIELD_POINTER_OFFSETS:
        pointer = TRAINER_TABLE_ADDRESS + field_offset
        encoded = struct.pack("<I", pointer)
        sites = [site for site in range(0, len(stage) - 3, 4)
                 if stage[site:site + 4] == encoded]
        if len(sites) != expected_counts[field_offset]:
            raise RuntimeBuildError(
                f"gTrainers+{field_offset:#x} literal inventory drift: "
                f"{len(sites)} != {expected_counts[field_offset]}"
            )
        result.extend((site, field_offset) for site in sites)
    return sorted(result)


def build_runtime_outputs(root: Path) -> dict[str, bytes]:
    root = Path(root)
    stage = (root / STAGE16).read_bytes()
    clean = (root / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
    if len(stage) != ROM_SIZE or len(clean) != 16 * 1024 * 1024:
        raise RuntimeBuildError("stage16/clean ROM size contract failed")
    stage_meta = json.loads((root / STAGE16_META).read_text(encoding="utf-8"))
    if _sha(stage) != stage_meta["output"]["sha256"]:
        raise RuntimeBuildError("stage16 hash drift")

    preliminary, _ = _build_blob(root, stage, clean, 0)
    allocation, _ = _allocation(root, len(preliminary), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime = _build_blob(root, stage, clean, payload_offset)
    if len(payload) != len(preliminary):
        raise RuntimeBuildError("address-dependent runtime size changed between passes")
    allocation, allocation_report = _allocation(root, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        raise RuntimeBuildError("central allocator placement changed after final payload")
    end = int(allocation["end_exclusive"])
    if stage[payload_offset:end] != b"\xFF" * len(payload):
        raise RuntimeBuildError("T17 payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:end] = payload
    patches: list[dict[str, Any]] = []
    for site, expected_pointer, symbol, label in (
        (MAP_GROUPS_POINTER_SITE, EXPECTED_MAP_GROUPS_ROOT, "map_groups_root", "gMapGroups root"),
        (MAP_LAYOUTS_POINTER_SITE, EXPECTED_MAP_LAYOUTS_ROOT, "map_layouts_root", "gMapLayouts root"),
        (WILD_HEADERS_POINTER_SITE, EXPECTED_WILD_HEADERS_ROOT, "wild_headers_root", "gWildMonHeaders root"),
    ):
        replacement = runtime["symbols"][symbol]
        _patch_expected(output, site, struct.pack("<I", expected_pointer),
                        struct.pack("<I", replacement), label, patches)

    trainer_table = int(runtime["symbols"]["trainer_table"])
    trainer_repoints = []
    for site, field_offset in _trainer_pointer_sites(stage):
        _patch_expected(
            output, site, struct.pack("<I", TRAINER_TABLE_ADDRESS + field_offset),
            struct.pack("<I", trainer_table + field_offset),
            f"gTrainers+{field_offset:#x} literal", trainer_repoints,
        )
    patches.extend(trainer_repoints)
    runtime["trainers"]["repoint_count"] = len(trainer_repoints)
    runtime["trainers"]["repoints"] = trainer_repoints

    portal_object, old_script = _find_portal_object(stage)
    _patch_expected(
        output, portal_object + 0x10, struct.pack("<I", old_script),
        struct.pack("<I", runtime["symbols"]["script_portal"]),
        "Hakuji research object local-id 1 portal script", patches,
    )

    output_raw = bytes(output)
    outside_changed = []
    allowed = [(payload_offset, end)] + [(row["site_offset"], row["site_offset"] + 4) for row in patches]
    for index, (before, after) in enumerate(zip(stage, output_raw)):
        if before == after:
            continue
        if not any(start <= index < stop for start, stop in allowed):
            outside_changed.append(index)
            if len(outside_changed) == 8:
                break
    if outside_changed:
        raise RuntimeBuildError(f"bytes changed outside declared spans: {outside_changed}")

    metadata = {
        "schema_version": 2, "task": TASK, "status": "PASS",
        "input": {"path": STAGE16.as_posix(), "size": len(stage), "sha256": _sha(stage)},
        "output": {"path": STAGE17.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        **runtime,
        "repoints": patches,
        "portal": {
            "host_map": {"group": VEGA_PORTAL_MAP[0], "map": VEGA_PORTAL_MAP[1]},
            "local_id": VEGA_PORTAL_LOCAL_ID, "object_offset": portal_object,
            "previous_script": old_script, "unlock_flags": [0x0824, 0x114B],
            "unlock_operator": "HALL_OF_FAME_OR_ALL_EARLY_FLAGS",
            "hall_of_fame_flag": FLAG_SYS_GAME_CLEAR,
            "hall_of_fame_required": False,
            "national_dex_required": False, "return_unconditional": True,
        },
        "allocation": {
            "path": STAGE17_ALLOC.as_posix(), "name": INTEGRATION_ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "stage16_unchanged_outside_payload_and_repoints": True,
            "tohoku_wild_headers_byte_preserved": True,
            "all_imported_maps_serialized": runtime["maps"]["physical_count"] == 253,
            "all_generated_trainers_bound": runtime["trainers"]["generated_trainers"] == 29,
            "trainer_production_rows_bound": runtime["trainers"]["production_rows_bound"] > 0,
            "kanto_progression_objects_bound": runtime["progression"]["physical_battle_objects"] == 13,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
        },
    }
    symbols = {
        "schema_version": 1, "task": TASK, "payload": metadata["payload"],
        "symbols": runtime["symbols"], "qol_b_entrypoints": runtime["qol_b"]["entrypoints"],
        "repoints": patches,
    }
    return {
        STAGE17.as_posix(): output_raw,
        STAGE17_META.as_posix(): _stable(metadata),
        STAGE17_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbols),
    }
