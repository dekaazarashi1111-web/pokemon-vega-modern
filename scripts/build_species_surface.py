#!/usr/bin/env python3
"""T09: Speciesの画像・鳴き声・図鑑・進化・技表と孵化QOL契約を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fast_stage_reuse import trusted_stage_sha  # noqa: E402

ROM_BASE = 0x08000000
CONFIG = Path("config/species_surface.json")
TASK = "T09"

ARTIFACTS = (
    "generated/engine/species_assets/species_assets.json",
    "generated/engine/species_assets/front.bin",
    "generated/engine/species_assets/back.bin",
    "generated/engine/species_assets/palette.bin",
    "generated/engine/species_assets/shiny_palette.bin",
    "generated/engine/species_assets/icon.bin",
    "generated/engine/species_assets/icon_palette.bin",
    "generated/engine/species_assets/front_coords.bin",
    "generated/engine/species_assets/back_coords.bin",
    "generated/engine/species_assets/elevation.bin",
    "generated/engine/species_assets/footprint.bin",
    "generated/engine/species_assets/cry.bin",
    "generated/engine/species_assets/cry2.bin",
    "generated/engine/species_assets/dex_entries.bin",
    "generated/engine/species_assets/national_dex.bin",
    "generated/engine/species/species_names_legacy.bin",
    "generated/engine/species/species_name_consumers.json",
    "generated/engine/evolutions/evolutions.bin",
    "generated/engine/evolutions/evolutions.json",
    "generated/engine/evolutions/v2_normalized.json",
    "generated/engine/learnsets/level_up_pointers.bin",
    "generated/engine/learnsets/level_up_data.bin",
    "generated/engine/learnsets/egg_moves.bin",
    "generated/engine/learnsets/tmhm.bin",
    "generated/engine/learnsets/tutor.bin",
    "generated/engine/learnsets/learnsets.json",
    "generated/runtime/species_surface.bin",
    "generated/runtime/species_surface_symbols.json",
    "reports/generated/dex_policy.md",
    "reports/generated/species_asset_validation.md",
    "reports/generated/species_name_consumers.md",
    "tests/fixtures/breeding_matrix.json",
)


SPECIES_NAME_CANONICAL_STRIDE = 11
SPECIES_NAME_COMPAT_STRIDE = 8
SPECIES_NAME_MAX_GLYPHS = 6

# The stock Japanese ROM exposes 40 aligned literals for gSpeciesNames.  Keep
# this list explicit: a new, removed, or relocated consumer must be audited
# before the build can proceed.  buffer_bytes=0 means that the routine only
# compares/addresses the row and never copies it; direct rows use the full
# eight-byte compatibility row as their bound.
SPECIES_NAME_CONSUMERS = (
    (0x000144, "cfru_abi", "CFRU-JP indirect gSpeciesNames root", 8, 7, "compat_stride_8"),
    (0x010CFC, "battle_seed", "trainer party name hash: no item/default moves", 0, 0, "compat_stride_8"),
    (0x010DC0, "battle_seed", "trainer party name hash: no item/custom moves", 0, 0, "compat_stride_8"),
    (0x010E60, "battle_seed", "trainer party name hash: item/default moves", 0, 0, "compat_stride_8"),
    (0x010F64, "battle_seed", "trainer party name hash: item/custom moves", 0, 0, "compat_stride_8"),
    (0x0344F4, "battle_hud", "Illusion nickname replacement and healthbox refresh", 11, 7, "compat_stride_8"),
    (0x0406E8, "name_getter", "stock GetSpeciesName body bypassed by canonical adapter", 11, 0, "canonical_getter"),
    (0x042CA4, "pokemon_data", "species-change nickname compare and replacement", 11, 0, "compat_stride_8"),
    (0x048D78, "battle_hud", "Nidoran gender suppression compare", 11, 7, "compat_stride_8"),
    (0x0533A0, "summary", "summary owner/nickname species comparisons", 256, 10, "compat_stride_8"),
    (0x053408, "summary", "summary species text copy", 256, 10, "compat_stride_8"),
    (0x06B55C, "script", "buffer species name command", 256, 0, "compat_stride_8"),
    (0x06B5AC, "script", "buffer lead Species name command", 256, 0, "compat_stride_8"),
    (0x0938C0, "pc", "PC storage Species field padded copy", 36, 6, "compat_stride_8_copy_6"),
    (0x09EF90, "naming", "default Species nickname seed", 16, 10, "compat_stride_8"),
    (0x0A1BD4, "size_record", "size record Species placeholder", 256, 0, "compat_stride_8"),
    (0x0BEAE0, "easy_chat", "easy-chat Species word pointer", 8, 10, "compat_stride_8"),
    (0x0CC2EC, "field_special", "requested Species placeholder", 256, 0, "compat_stride_8"),
    (0x0CD028, "field_special", "unmodified nickname comparison", 11, 0, "compat_stride_8"),
    (0x0CF20C, "evolution", "evolved Species placeholder", 256, 0, "compat_stride_8"),
    (0x0CF810, "evolution", "trade-evolution Species placeholder", 256, 0, "compat_stride_8"),
    (0x0CF9F4, "evolution", "extra evolved mon nickname", 11, 0, "compat_stride_8"),
    (0x0E74C8, "notification", "Species name notification append", 256, 0, "compat_stride_8"),
    (0x0F42E0, "hall_of_fame", "Hall of Fame slash and Species text", 16, 10, "compat_stride_8"),
    (0x104370, "pokedex_list", "regional-dex seen list label", 8, 10, "compat_stride_8"),
    (0x10444C, "pokedex_list", "regional-dex caught list label", 8, 10, "compat_stride_8"),
    (0x1044F0, "pokedex_list", "national-dex seen list label", 8, 10, "compat_stride_8"),
    (0x104588, "pokedex_list", "national-dex caught list label", 8, 10, "compat_stride_8"),
    (0x104624, "pokedex_list", "alphabetical-dex list label", 8, 10, "compat_stride_8"),
    (0x104688, "pokedex_list", "weight/height-dex list label", 8, 10, "compat_stride_8"),
    (0x105C2C, "pokedex_category", "category list Species label", 8, 10, "compat_stride_8"),
    (0x106B88, "pokedex_detail", "detail page Species label", 8, 10, "compat_stride_8"),
    (0x107020, "pokedex_area", "area page Species label", 8, 12, "compat_stride_8_split_index"),
    (0x114A20, "quest_log", "dynamic Species placeholder pointer", 8, 0, "compat_stride_8"),
    (0x119D78, "union_room", "trade registration Species placeholder", 256, 0, "compat_stride_8"),
    (0x11B500, "union_room", "trade-list Species text", 8, 10, "compat_stride_8"),
    (0x11B838, "union_room", "local trade request Species buffer", 11, 10, "compat_stride_8"),
    (0x11B88C, "union_room", "remote trade request Species buffer", 11, 10, "compat_stride_8"),
    (0x1220E0, "party", "party Nidoran gender suppression compare", 11, 10, "compat_stride_8"),
    (0x136B1C, "trade", "in-game trade Species placeholder/compare", 256, 10, "compat_stride_8"),
)

# (consumer literal, instruction site, expected bytes, replacement bytes,
#  human-readable migration).  Six-byte sequences replace `species * 6` with
# one `lsl #3` plus two Thumb NOPs, preserving the surrounding register ABI.
SPECIES_NAME_PATCHES = (
    (0x010CFC, 0x010C84, "480040184000", "c800c046c046", "name hash source A"),
    (0x010CFC, 0x010C9C, "410009184900", "c100c046c046", "name hash source B"),
    (0x010DC0, 0x010D12, "480040184000", "c800c046c046", "name hash source A"),
    (0x010DC0, 0x010D2A, "410009184900", "c100c046c046", "name hash source B"),
    (0x010E60, 0x010DDA, "480040184000", "c800c046c046", "name hash source A"),
    (0x010E60, 0x010DF2, "410009184900", "c100c046c046", "name hash source B"),
    (0x010F64, 0x010E76, "480040184000", "c800c046c046", "name hash source A"),
    (0x010F64, 0x010E8E, "410009184900", "c100c046c046", "name hash source B"),
    (0x0344F4, 0x03449C, "5a0042445200", "da00c046c046", "Illusion nickname row"),
    (0x042CA4, 0x042C74, "600000194000", "e000c046c046", "old Species nickname row"),
    (0x042CA4, 0x042C88, "720092195200", "f200c046c046", "new Species nickname row"),
    (0x048D78, 0x048D2A, "510089184900", "d100c046c046", "healthbox compare row"),
    (0x0533A0, 0x05336C, "510089184900", "d100c046c046", "summary current Species row"),
    (0x0533A0, 0x05337E, "510089184900", "d100c046c046", "summary compared Species row"),
    (0x053408, 0x0533DA, "510089184900", "d100c046c046", "summary copied Species row"),
    (0x06B55C, 0x06B53E, "410009184900", "c100c046c046", "script Species row"),
    (0x06B5AC, 0x06B58A, "410009184900", "c100c046c046", "script lead Species row"),
    (0x0938C0, 0x093854, "410009184900", "c100c046c046", "PC Species row"),
    (0x0938C0, 0x093862, "0523", "0623", "PC padded visible glyph count"),
    (0x09EF90, 0x09EF2A, "410009184900", "c100c046c046", "naming Species row"),
    (0x0A1BD4, 0x0A1BB6, "610009194900", "e100c046c046", "size record Species row"),
    (0x0BEAE0, 0x0BEAD4, "500080184000", "d000c046c046", "easy-chat Species row"),
    (0x0CC2EC, 0x0CC2C2, "410009184900", "c100c046c046", "field request Species row"),
    (0x0CD028, 0x0CD008, "480040184000", "c800c046c046", "field nickname compare row"),
    (0x0CF20C, 0x0CF03A, "510049444900", "d100c046c046", "evolution placeholder row"),
    (0x0CF810, 0x0CF6CA, "690049194900", "e900c046c046", "trade evolution placeholder row"),
    (0x0CF9F4, 0x0CF906, "4a0052185200", "ca00c046c046", "extra evolved mon nickname row"),
    (0x0E74C8, 0x0E74A0, "690049194900", "e900c046c046", "notification Species row"),
    (0x0F42E0, 0x0F426A, "480040184000", "c800c046c046", "Hall of Fame width pass"),
    (0x0F42E0, 0x0F4284, "480040184000", "c800c046c046", "Hall of Fame copy pass"),
    (0x0F42E0, 0x0F429C, "500080184000", "d000c046c046", "Hall of Fame gender pass"),
    (0x104370, 0x104358, "410009184900", "c100c046c046", "Dex list row"),
    (0x10444C, 0x104402, "410009184900", "c100c046c046", "Dex list row"),
    (0x1044F0, 0x1044A6, "410009184900", "c100c046c046", "Dex list row"),
    (0x104588, 0x104542, "410009184900", "c100c046c046", "Dex list row"),
    (0x104624, 0x1045DE, "410009184900", "c100c046c046", "Dex list row"),
    (0x104688, 0x104670, "410009184900", "c100c046c046", "Dex list row"),
    (0x105C2C, 0x105BB4, "4a0042445200", "ca00c046c046", "Dex category row"),
    (0x106B88, 0x106A92, "4a0052185200", "ca00c046c046", "Dex detail row"),
    (0x107020, 0x106DE4, "4900", "0900", "Dex area cached Species factor 2 to 1"),
    (0x107020, 0x106F9A, "5200", "9200", "Dex area final factor 2 to 4"),
    (0x114A20, 0x114A0C, "5900c9184900", "d900c046c046", "quest log Species row"),
    (0x119D78, 0x119D3C, "410009184900", "c100c046c046", "union registration Species row"),
    (0x11B500, 0x11B4AA, "620012195200", "e200c046c046", "union list Species row"),
    (0x11B838, 0x11B824, "510089184900", "d100c046c046", "union local Species buffer"),
    (0x11B88C, 0x11B852, "510089184900", "d100c046c046", "union remote Species buffer"),
    (0x1220E0, 0x1220C0, "690049194900", "e900c046c046", "party gender compare row"),
    (0x136B1C, 0x136A64, "610009194900", "e100c046c046", "trade Species row"),
)

# StringCopy_Nickname at 0x08008870 is shared with narrower non-battle
# destinations and intentionally retains the Japanese five-glyph nickname
# policy.  Only these four audited party-to-BattlePokemon transfers target the
# eight-byte nickname field and are safe to widen to six glyphs plus EOS.
BATTLE_NICKNAME_COPY_CAVE = 0x18C350
SPECIES_PICTURE_BOUND_THUNK_CAVE = 0x18C358
BATTLE_NICKNAME_TRANSFER_SITES = (
    (0x03069A, "d8f7e9f8", "player party to local BattlePokemon"),
    (0x036072, "d2f7fdfb", "opponent party to local BattlePokemon"),
    (0x03AC9E, "cdf7e7fd", "link party to local BattlePokemon"),
    (0x040A2A, "c7f721ff", "party data to gBattleMons nickname field"),
)

# StringGetEnd10 is the stock display clamp used after MON_DATA_NICKNAME reads.
# Its thirteen native BL callers and three CFRU-JP long-call literals all
# target buffers of at least seven bytes; widen only its immediate bound.
NICKNAME_END_BOUND_SITE = 0x0088A8
NICKNAME_END_DIRECT_CALLS = (
    0x043EEC, 0x048CEE, 0x06B5E4, 0x09359E, 0x093696,
    0x0A17C6, 0x0CD302, 0x0D933A, 0x0D95CA, 0x0D9640,
    0x11FD8C, 0x120ADE, 0x1369DA,
)
NICKNAME_END_LONG_CALL_LITERALS = (0x10D1818, 0x10D1BD0, 0x1128F78)


class SurfaceError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise SurfaceError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"{path} must contain an object")
    return value


def fixed(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    if sha(raw) != expected:
        fail(f"fixed input hash mismatch: {path}")
    return raw


def run(command: list[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        fail(f"{label} failed ({completed.returncode}): {detail}")
    return completed.stdout.strip()


def expected_stage07_sha(root: Path, config: Mapping[str, Any]) -> str:
    inputs = config["inputs"]
    return trusted_stage_sha(
        root,
        Path(str(inputs["stage07_path"])),
        Path("build/stages/07_species.json"),
        "T07",
        str(inputs["stage07_sha256"]),
    )


def ptr(rom: bytes | bytearray, site: int) -> int:
    return struct.unpack_from("<I", rom, site)[0]


def slice_at(rom: bytes, address: int, size: int, label: str) -> bytes:
    start = address - ROM_BASE
    raw = rom[start:start + size]
    if len(raw) != size:
        fail(f"{label} is outside ROM")
    return raw


def aliases(models: Mapping[str, Any]) -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    species = {int(row["source_id"]): int(row["canonical_id"]) for row in models["species"]["aliases"]}
    moves = {int(row["cfru_source_id"]): int(row["canonical_id"]) for row in models["moves"]["aliases"]}
    items = {int(row["source_id"]): int(row["canonical_id"]) for row in models["ids"]["item_aliases"]}
    return species, moves, items


def map_required(table: Mapping[int, int], value: int, label: str) -> int:
    if value not in table:
        fail(f"unresolved {label} source ID {value}")
    return table[value]


def table_merge(stage: bytes, dpe: bytes, rows: list[dict[str, Any]], site: int,
                dpe_root: int, stride: int, vega_count: int, label: str) -> bytes:
    old_root = ptr(stage, site)
    output = bytearray()
    for row in rows:
        cid = int(row["id"])
        if cid < vega_count:
            output += slice_at(stage, old_root + cid * stride, stride, f"Vega {label} {cid}")
        else:
            source = int(row["dpe_id"])
            output += slice_at(dpe, dpe_root + source * stride, stride, f"DPE {label} {source}")
    return bytes(output)


def canonicalize_display_tags(
    tables: dict[str, bytes], species_count: int,
) -> dict[str, int]:
    """Sprite resource tags must live in the canonical Species namespace.

    DPE structs carry their source Species ID in the tag field.  Copying those
    structs into a reordered canonical table leaves every appended sprite and
    palette registered under the wrong resource tag.  Shiny tags additionally
    need a disjoint canonical range so they cannot collide with normal tags.
    Asset pointers and compressed bytes remain lossless; only the resource IDs
    are normalized here.
    """
    checks = 0
    for name in ("front", "back", "palette"):
        mutable = bytearray(tables[name])
        for species in range(species_count):
            struct.pack_into("<H", mutable, species * 8 + 6 if name in {"front", "back"}
                             else species * 8 + 4, species)
            checks += 1
        tables[name] = bytes(mutable)
    mutable = bytearray(tables["shiny_palette"])
    for species in range(species_count):
        struct.pack_into("<H", mutable, species * 8 + 4, species_count + species)
        checks += 1
    tables["shiny_palette"] = bytes(mutable)
    return {"canonical_tags": checks, "shiny_tag_base": species_count}


def cry_merge(stage: bytes, dpe: bytes, rows: list[dict[str, Any]], site: int,
              dpe_root: int, vega_count: int) -> bytes:
    old_root = ptr(stage, site)
    cry_map = 0x08865DE0
    output = bytearray()
    for row in rows:
        cid = int(row["id"])
        if cid < vega_count:
            mapped = struct.unpack_from("<H", stage, cry_map - ROM_BASE + (cid + 1) * 2)[0]
            source_index = max(0, mapped - 1)
            # Vega's EGG/reserved sentinel deliberately maps to 0xFFFF and is silent.
            # Canonical tables use row 0 as the bounded silent/default ToneData row.
            if mapped == 0xFFFF:
                source_index = 0
            elif source_index >= 388:
                fail(f"Vega cry map out of bounds: species={cid} cry={mapped}")
            output += slice_at(stage, old_root + source_index * 12, 12, f"Vega cry {cid}")
        else:
            output += slice_at(dpe, dpe_root + int(row["dpe_id"]) * 12, 12, f"DPE cry {cid}")
    return bytes(output)


def lz77_size(rom: bytes, address: int) -> int:
    offset = address - ROM_BASE
    if not (0 <= offset + 4 <= len(rom)) or rom[offset] != 0x10:
        return -1
    return rom[offset + 1] | rom[offset + 2] << 8 | rom[offset + 3] << 16


def dpe_footprints(root: Path) -> dict[int, int]:
    constants = (root / "vendor/upstream/DPE-JP/include/species.h").read_text(encoding="utf-8")
    symbols = {match.group(1): int(match.group(2), 0) for match in re.finditer(
        r"^#define\s+(SPECIES_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\s*$", constants, re.M)}
    source = (root / "vendor/upstream/DPE-JP/src/Footprint_Table.c").read_text(encoding="utf-8")
    result: dict[int, int] = {}
    for match in re.finditer(r"\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*(0x[0-9A-Fa-f]+)", source):
        if match.group(1) in symbols:
            result[symbols[match.group(1)]] = int(match.group(2), 0)
    if len(result) < 1200:
        fail(f"DPE footprint source coverage changed: {len(result)}")
    return result


def validate_assets(dpe: bytes, tables: Mapping[str, bytes], rows: list[dict[str, Any]],
                    vega_count: int) -> dict[str, Any]:
    checks = {"compressed_checked": 0, "aligned_pointers": 0, "icons_checked": 0,
              "canonical_tags_checked": 0}
    species_count = len(rows)
    for cid in range(species_count):
        for key in ("front", "back"):
            tag = struct.unpack_from("<H", tables[key], cid * 8 + 6)[0]
            if tag != cid:
                fail(f"noncanonical {key} tag for species {cid}: {tag}")
            checks["canonical_tags_checked"] += 1
        normal_tag = struct.unpack_from("<H", tables["palette"], cid * 8 + 4)[0]
        shiny_tag = struct.unpack_from("<H", tables["shiny_palette"], cid * 8 + 4)[0]
        if normal_tag != cid or shiny_tag != species_count + cid:
            fail(
                f"noncanonical palette tags for species {cid}: "
                f"normal={normal_tag} shiny={shiny_tag}"
            )
        checks["canonical_tags_checked"] += 2
    for cid in range(vega_count, len(rows)):
        for key, expected in (("front", 2048), ("back", 2048), ("palette", 32), ("shiny_palette", 32)):
            address = struct.unpack_from("<I", tables[key], cid * 8)[0]
            if address & 3:
                fail(f"unaligned {key} pointer for species {cid}")
            size = lz77_size(dpe, address)
            valid_sizes = {32, 64, 128} if key.endswith("palette") else {2048, 4096, 8192}
            if size not in valid_sizes:
                fail(f"invalid {key} LZ77 header for species {cid}: {size}")
            checks["compressed_checked"] += 1
            checks["aligned_pointers"] += 1
        icon = struct.unpack_from("<I", tables["icon"], cid * 4)[0]
        if icon & 3 or not (ROM_BASE <= icon < ROM_BASE + len(dpe)):
            fail(f"invalid icon pointer for species {cid}")
        checks["icons_checked"] += 1
    checks["status"] = "PASS"
    return checks


ITEM_PARAM = {6, 7, 24, 25, 34, 39, 0xFE}
ITEM_UNKNOWN = {35, 36}
MOVE_PARAM = {26, 37, 38}
SPECIES_PARAM = {27}

# T09の公開済み成果はEVO_MEGA(0xFE)のparameterを一律Item aliasで
# 変換していた。この挙動は過去stageのbyte再現専用として固定し、P02以降は
# MEGA_VARIANT_WISH(2)だけをMove namespaceで変換する。既定値をlegacyに
# 保つことで、過去Stage09/39等のbuild/check結果を暗黙に書き換えない。
EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1 = "T09_LEGACY_ITEM_0XFE_V1"
EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2 = "MODERNIZATION_P02_WISH_MOVE_V2"
EVOLUTION_PARAMETER_POLICIES = {
    EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
    EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2,
}
MEGA_VARIANT_WISH = 2


def remap_evolution_parameters(
    method: int,
    param: int,
    unknown: int,
    species_alias: Mapping[int, int],
    move_alias: Mapping[int, int],
    item_alias: Mapping[int, int],
    *,
    policy: str,
) -> tuple[int, int]:
    """進化methodの実consumer意味に従いparameter/extraをcanonical化する。

    legacy policyは公開済みT09の再現専用で、EVO_MEGAを一律Item扱いする。
    modernization policyはWish MegaのparameterだけMoveとして解決する。
    """

    if policy not in EVOLUTION_PARAMETER_POLICIES:
        fail(f"unknown evolution parameter namespace policy: {policy}")
    if (
        policy == EVOLUTION_PARAMETER_POLICY_MODERNIZATION_P02_V2
        and method == 0xFE
        and unknown == MEGA_VARIANT_WISH
        and param
    ):
        param = map_required(move_alias, param, "Wish Mega evolution Move")
    elif method in ITEM_PARAM and param:
        param = map_required(item_alias, param, "evolution Item")
    if method in ITEM_UNKNOWN and unknown:
        unknown = map_required(item_alias, unknown, "evolution held Item")
    if method in MOVE_PARAM and param:
        param = map_required(move_alias, param, "evolution Move")
    if method in SPECIES_PARAM and param:
        param = map_required(species_alias, param, "evolution party Species")
    return param, unknown


def merge_evolutions(
    stage: bytes,
    dpe: bytes,
    config: Mapping[str, Any],
    rows: list[dict[str, Any]],
    species_alias: Mapping[int, int],
    move_alias: Mapping[int, int],
    item_alias: Mapping[int, int],
    *,
    parameter_policy: str = EVOLUTION_PARAMETER_POLICY_T09_LEGACY_V1,
) -> tuple[bytes, dict[str, Any]]:
    meta = read_json(ROOT / config["inputs"]["stage06_metadata_path"])
    runtime = meta["runtime_tables"]["evolutions"]
    old = slice_at(stage, int(runtime["address"]), 412 * 128, "T06 evolution prefix")
    dpe_root = int(config["dpe_roots"]["evolution"])
    output = bytearray(old)
    nonzero = duplicate_count = 0
    normalized_rows: list[dict[str, Any]] = []
    for cid in range(412):
        seen_prefix: set[tuple[int, int, int, int]] = set()
        for slot in range(16):
            entry = struct.unpack_from("<HHHH", old, cid * 128 + slot * 8)
            method, param, target, unknown = entry
            if method == 0:
                continue
            if target >= len(rows):
                fail(f"T06 evolution target is outside canonical Species: {target}")
            if entry in seen_prefix:
                fail(f"T06 evolution has semantic duplicate: species={cid} slot={slot}")
            seen_prefix.add(entry)
            nonzero += 1
            normalized_rows.append({
                "from_id": cid, "from_form_key": rows[cid]["form_key"],
                "from_national_dex": int(rows[cid]["canonical_national_dex"]),
                "method": method, "param": param, "target_id": target,
                "target_form_key": rows[target]["form_key"],
                "target_national_dex": int(rows[target]["canonical_national_dex"]),
                "unknown": unknown,
            })
    for species_row in rows[412:]:
        source_id = int(species_row["dpe_id"])
        raw = slice_at(dpe, dpe_root + source_id * 128, 128, "DPE evolution row")
        converted: list[tuple[int, int, int, int]] = []
        seen: set[tuple[int, int, int, int]] = set()
        for slot in range(16):
            method, param, target, unknown = struct.unpack_from("<HHHH", raw, slot * 8)
            if method == 0:
                continue
            target = map_required(species_alias, target, "evolution target Species")
            param, unknown = remap_evolution_parameters(
                method, param, unknown, species_alias, move_alias, item_alias,
                policy=parameter_policy,
            )
            key = (method, param, target, unknown)
            if key in seen:
                duplicate_count += 1
                continue
            seen.add(key)
            converted.append(key)
            normalized_rows.append({
                "from_id": int(species_row["id"]), "from_form_key": species_row["form_key"],
                "from_national_dex": int(species_row["canonical_national_dex"]),
                "method": method, "param": param, "target_id": target,
                "target_form_key": rows[target]["form_key"],
                "target_national_dex": int(rows[target]["canonical_national_dex"]),
                "unknown": unknown,
            })
        if len(converted) > 16:
            fail(f"evolution overflow for Species {species_row['id']}")
        converted += [(0, 0, 0, 0)] * (16 - len(converted))
        for entry in converted:
            output += struct.pack("<HHHH", *entry)
            nonzero += entry[0] != 0
    if len(output) != len(rows) * 128:
        fail("canonical evolution table size mismatch")
    model = {"schema_version": 1, "task": TASK, "species_count": len(rows),
             "stride": 128, "nonzero_rows": nonzero,
             "semantic_duplicates_removed": duplicate_count,
             "rows": normalized_rows, "status": "PASS"}
    return bytes(output), model


def normalize_v2(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    seen: set[tuple[int, int, str]] = set()
    rows = []
    duplicates = 0
    unresolved = []
    for row in source:
        key = (int(row["from_national_no"]), int(row["to_national_no"]), row["vega_integrated_condition"].strip())
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        required = row["requires_new_item_or_counter"].strip()
        resolution = row["implementation_note"].strip()
        if required not in ("はい", "いいえ") or (required == "はい" and not resolution):
            unresolved.append(row["evolution_id"])
        rows.append({"evolution_id": int(row["evolution_id"]), "from_national_dex": key[0],
                     "from_form_key": "", "to_national_dex": key[1], "to_form_key": "",
                     "condition": key[2], "requires_new_item_or_counter": required,
                     "resolution": resolution})
    if unresolved:
        fail(f"V2 unresolved requirement rows: {unresolved[:5]}")
    return {"schema_version": 1, "source_rows": len(source), "normalized_rows": len(rows),
            "semantic_duplicates_removed": duplicates, "rows": rows, "status": "PASS"}


def parse_level_data(rom: bytes, address: int, move_alias: Mapping[int, int]) -> bytes:
    output = bytearray()
    offset = address - ROM_BASE
    for _ in range(256):
        move = struct.unpack_from("<H", rom, offset)[0]
        level = rom[offset + 2]
        offset += 3
        if move == 0 and level == 0xFF:
            output += b"\x00\x00\xff"
            return bytes(output)
        output += struct.pack("<HB", map_required(move_alias, move, "level-up Move"), level)
    fail(f"unterminated level-up data at {address:#x}")


def parse_vega_level_data(rom: bytes, address: int) -> bytes:
    """Convert Vega's packed 9-bit move/7-bit level rows to CFRU's 3-byte ABI."""
    output = bytearray()
    offset = address - ROM_BASE
    for _ in range(256):
        if offset < 0 or offset + 2 > len(rom):
            fail(f"Vega level-up data is outside ROM at {address:#x}")
        packed = struct.unpack_from("<H", rom, offset)[0]
        offset += 2
        if packed == 0xFFFF:
            output += b"\x00\x00\xff"
            return bytes(output)
        output += struct.pack("<HB", packed & 0x01FF, packed >> 9)
    fail(f"unterminated Vega level-up data at {address:#x}")


def parse_egg(rom: bytes, root: int, move_alias: Mapping[int, int] | None,
              species_alias: Mapping[int, int] | None, include: callable) -> list[int]:
    values: list[int] = []
    offset = root - ROM_BASE
    active = False
    for _ in range(20000):
        value = struct.unpack_from("<H", rom, offset)[0]
        offset += 2
        if value == 0xFFFF:
            break
        if value >= 20000:
            source = value - 20000
            target = source if species_alias is None else species_alias.get(source, -1)
            active = target >= 0 and include(target)
            if active:
                values.append(target + 20000)
        elif active:
            values.append(value if move_alias is None else map_required(move_alias, value, "egg Move"))
    else:
        fail("unterminated egg move table")
    return values


def merge_learnsets(stage: bytes, dpe: bytes, config: Mapping[str, Any], rows: list[dict[str, Any]],
                    species_alias: Mapping[int, int], move_alias: Mapping[int, int],
                    allocate_address: int) -> tuple[dict[str, bytes], dict[str, Any]]:
    dpe_level = int(config["dpe_roots"]["level_up"])
    old_level = ptr(stage, int(config["pointer_sites"]["level_up"]))
    pointer_values: list[int] = []
    data = bytearray()
    converted_vega = translated_dpe = 0
    for row in rows:
        cid = int(row["id"])
        if cid < 412:
            source_ptr = ptr(stage, old_level - ROM_BASE + cid * 4)
            converted = parse_vega_level_data(stage, source_ptr)
            converted_vega += 1
        else:
            source = int(row["dpe_id"])
            source_ptr = ptr(dpe, dpe_level - ROM_BASE + source * 4)
            converted = parse_level_data(dpe, source_ptr, move_alias)
            translated_dpe += 1
        pointer_values.append(allocate_address + len(data))
        data += converted
    pointers = b"".join(struct.pack("<I", value) for value in pointer_values)

    vega_egg = parse_egg(stage, ptr(stage, int(config["pointer_sites"]["egg"])), None, None,
                         lambda target: 0 <= target < 412)
    dpe_egg = parse_egg(dpe, int(config["dpe_roots"]["egg"]), move_alias, species_alias,
                        lambda target: target >= 412)
    egg = b"".join(struct.pack("<H", value) for value in vega_egg + dpe_egg + [0xFFFF])

    tmhm = table_merge(stage, dpe, rows, int(config["pointer_sites"]["tmhm"]),
                       int(config["dpe_roots"]["tmhm"]), 16, 412, "TM/HM")
    tutor = table_merge(stage, dpe, rows, int(config["pointer_sites"]["tutor"]),
                        int(config["dpe_roots"]["tutor"]), 16, 412, "tutor")
    model = {"schema_version": 1, "task": TASK, "species_count": len(rows),
             "level_up": {"format": "U16_MOVE_U8_LEVEL", "stride": 3,
                          "converted_vega_rows": converted_vega,
                          "translated_dpe_rows": translated_dpe,
                          "data_bytes": len(data)},
             "egg": {"u16_count": len(egg) // 2, "vega_values": len(vega_egg),
                     "translated_values": len(dpe_egg)},
             "tmhm": {"stride": 16}, "tutor": {"stride": 16}, "status": "PASS"}
    return {"level_up_pointers": pointers, "level_up_data": bytes(data), "egg_moves": egg,
            "tmhm": tmhm, "tutor": tutor}, model


def compatibility_species_names(
    names: bytes, rows: list[dict[str, Any]],
) -> tuple[bytes, dict[str, Any]]:
    """Render the audited Japanese six-glyph compatibility ABI.

    The canonical 11-byte table remains authoritative.  Stock direct users
    cannot consume that stride, while fixed CFRU-JP was compiled with
    POKEMON_NAME_6 and therefore expects an eight-byte row.  Copying the full
    visible bytes into an eight-byte row preserves six glyphs plus EOS without
    widening nickname/global-string destinations.
    """
    species_count = len(rows)
    if len(names) != species_count * SPECIES_NAME_CANONICAL_STRIDE:
        fail("canonical Species name table size mismatch")
    output = bytearray()
    distribution: dict[int, int] = {}
    six_glyph_rows: list[dict[str, Any]] = []
    unchanged_short = 0
    for species, model_row in enumerate(rows):
        row = names[
            species * SPECIES_NAME_CANONICAL_STRIDE:
            (species + 1) * SPECIES_NAME_CANONICAL_STRIDE
        ]
        try:
            terminator = row.index(0xFF)
        except ValueError:
            fail(f"canonical Species name row is unterminated: {species}")
        visible = row[:terminator]
        if len(visible) > SPECIES_NAME_MAX_GLYPHS:
            fail(f"canonical Species name exceeds six glyphs: {species}")
        if any(value != 0xFF for value in row[terminator:]):
            fail(f"canonical Species name padding differs: {species}")
        display_name = str(model_row["display_name"])
        if len(display_name) != len(visible):
            fail(
                f"canonical Species display/byte length differs: "
                f"{species} {display_name!r}/{visible.hex()}"
            )
        distribution[len(visible)] = distribution.get(len(visible), 0) + 1
        compat_row = visible + b"\xFF" * (
            SPECIES_NAME_COMPAT_STRIDE - len(visible)
        )
        if compat_row[:len(visible)] != visible or compat_row[len(visible)] != 0xFF:
            fail(f"compatibility Species name differs: {species}")
        output += compat_row
        if len(visible) <= 5:
            unchanged_short += 1
        else:
            six_glyph_rows.append({
                "id": species,
                "species_key": model_row["species_key"],
                "form_key": model_row["form_key"],
                "display_name": display_name,
                "canonical_hex": (visible + b"\xFF").hex(),
                "compat_hex": compat_row.hex(),
            })
    if distribution.get(6) != 134 or len(six_glyph_rows) != 134:
        fail(f"six-glyph Species inventory differs: {distribution}")
    expected_canaries = {
        1288: "54ae5d96ae7eff",
        1363: "718a7e915265ff",
    }
    actual_canaries = {
        row["id"]: row["canonical_hex"]
        for row in six_glyph_rows if row["id"] in expected_canaries
    }
    if actual_canaries != expected_canaries:
        fail(f"six-glyph Species canary differs: {actual_canaries}")
    model = {
        "schema_version": 1,
        "task": "USER-20260815-SPECIES-NAME-LENGTH",
        "status": "PASS",
        "canonical_stride": SPECIES_NAME_CANONICAL_STRIDE,
        "compatibility_stride": SPECIES_NAME_COMPAT_STRIDE,
        "max_visible_glyphs": SPECIES_NAME_MAX_GLYPHS,
        "species_count": species_count,
        "length_distribution": {
            str(length): count for length, count in sorted(distribution.items())
        },
        "six_glyph_count": len(six_glyph_rows),
        "unchanged_five_or_fewer": unchanged_short,
        "six_glyph_rows": six_glyph_rows,
        "canaries": actual_canaries,
    }
    return bytes(output), model


def species_name_consumer_model(stage: bytes) -> dict[str, Any]:
    old_root = ptr(stage, 0x144)
    old_bytes = struct.pack("<I", old_root)
    actual_sites = [
        index for index in range(0, len(stage) - 3, 4)
        if stage[index:index + 4] == old_bytes
    ]
    declared_sites = [row[0] for row in SPECIES_NAME_CONSUMERS]
    if actual_sites != declared_sites or len(set(declared_sites)) != 40:
        fail(
            "stock Species name consumer inventory changed: "
            f"actual={actual_sites} declared={declared_sites}"
        )
    owners = {row[0] for row in SPECIES_NAME_PATCHES}
    if not owners <= set(declared_sites):
        fail(f"Species name patch has unknown consumer: {sorted(owners - set(declared_sites))}")
    patch_sites = [row[1] for row in SPECIES_NAME_PATCHES]
    if len(patch_sites) != len(set(patch_sites)):
        fail("Species name instruction patch sites are duplicated")
    patches_by_consumer: dict[int, list[int]] = {}
    for consumer_site, site, expected_hex, replacement_hex, _ in SPECIES_NAME_PATCHES:
        expected = bytes.fromhex(expected_hex)
        replacement = bytes.fromhex(replacement_hex)
        if len(expected) != len(replacement):
            fail(f"Species name patch width differs at 0x{site:X}")
        if stage[site:site + len(expected)] != expected:
            fail(
                f"Species name consumer code changed at 0x{site:X}: "
                f"{stage[site:site + len(expected)].hex()}"
            )
        patches_by_consumer.setdefault(consumer_site, []).append(site)
    consumers = []
    for site, surface, purpose, buffer_bytes, max_draw_glyphs, strategy in SPECIES_NAME_CONSUMERS:
        migrated = strategy == "canonical_getter" or bool(
            patches_by_consumer.get(site)
        ) or site == 0x144
        consumers.append({
            "literal_site": site,
            "literal_address": ROM_BASE + site,
            "surface": surface,
            "purpose": purpose,
            "old_row_stride": 6,
            "new_row_stride": (
                SPECIES_NAME_CANONICAL_STRIDE
                if strategy == "canonical_getter"
                else SPECIES_NAME_COMPAT_STRIDE
            ),
            "output_buffer_bytes": buffer_bytes,
            "max_draw_glyphs": max_draw_glyphs,
            "boundary_known": True,
            "strategy": strategy,
            "instruction_patch_sites": patches_by_consumer.get(site, []),
            "migrated": migrated,
        })
    unreviewed = [row["literal_site"] for row in consumers if not row["purpose"]]
    unmigrated = [row["literal_site"] for row in consumers if not row["migrated"]]
    unknown_boundaries = [
        row["literal_site"] for row in consumers if not row["boundary_known"]
    ]
    if unreviewed or unmigrated or unknown_boundaries:
        fail(
            "Species name inventory is incomplete: "
            f"unreviewed={unreviewed} unmigrated={unmigrated} "
            f"unknown_boundaries={unknown_boundaries}"
        )
    cave_expected = b"\xFF" * 8
    if stage[BATTLE_NICKNAME_COPY_CAVE:BATTLE_NICKNAME_COPY_CAVE + 8] != cave_expected:
        fail("audited battle nickname veneer cave is no longer empty")
    cave_pointer = struct.pack("<I", ROM_BASE + BATTLE_NICKNAME_COPY_CAVE)
    cave_references = [
        index for index in range(0, len(stage) - 3, 4)
        if stage[index:index + 4] == cave_pointer
    ]
    if cave_references:
        fail(f"battle nickname veneer cave gained pointer users: {cave_references}")
    if (stage[SPECIES_PICTURE_BOUND_THUNK_CAVE:
              SPECIES_PICTURE_BOUND_THUNK_CAVE + 8] != cave_expected):
        fail("audited Species picture-bound thunk cave is no longer empty")
    bound_cave_pointer = struct.pack(
        "<I", ROM_BASE + SPECIES_PICTURE_BOUND_THUNK_CAVE,
    )
    bound_cave_references = [
        index for index in range(0, len(stage) - 3, 4)
        if stage[index:index + 4] == bound_cave_pointer
    ]
    if bound_cave_references:
        fail(
            "Species picture-bound thunk cave gained pointer users: "
            f"{bound_cave_references}"
        )
    battle_transfers = []
    for site, expected_hex, purpose in BATTLE_NICKNAME_TRANSFER_SITES:
        expected = bytes.fromhex(expected_hex)
        if stage[site:site + len(expected)] != expected:
            fail(
                f"battle nickname transfer changed at 0x{site:X}: "
                f"{stage[site:site + len(expected)].hex()}"
            )
        battle_transfers.append({
            "site": site,
            "address": ROM_BASE + site,
            "purpose": purpose,
            "destination_buffer_bytes": 8,
            "old_max_visible_glyphs": 5,
            "new_max_visible_glyphs": SPECIES_NAME_MAX_GLYPHS,
            "strategy": "audited_battle_copy_wrapper",
            "expected_hex": expected_hex,
            "migrated": True,
        })
    if stage[NICKNAME_END_BOUND_SITE:NICKNAME_END_BOUND_SITE + 2] != bytes.fromhex("0524"):
        fail("stock StringGetEnd10 five-glyph bound changed")
    nickname_end_target = 0x0088A4
    direct_calls = []
    scan_end = min(len(stage) - 3, nickname_end_target + 0x400004)
    for site in range(0, scan_end, 2):
        first, second = struct.unpack_from("<HH", stage, site)
        if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
            continue
        delta = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
        if delta & 0x400000:
            delta -= 0x800000
        if site + 4 + delta == nickname_end_target:
            direct_calls.append(site)
    if tuple(direct_calls) != NICKNAME_END_DIRECT_CALLS:
        fail(f"StringGetEnd10 direct caller inventory changed: {direct_calls}")
    long_call_bytes = struct.pack("<I", ROM_BASE + nickname_end_target + 1)
    long_call_literals = []
    cursor = 0
    while True:
        cursor = stage.find(long_call_bytes, cursor)
        if cursor < 0:
            break
        long_call_literals.append(cursor)
        cursor += 1
    if tuple(long_call_literals) != NICKNAME_END_LONG_CALL_LITERALS:
        fail(
            "StringGetEnd10 CFRU long-call inventory changed: "
            f"{long_call_literals}"
        )
    return {
        "schema_version": 1,
        "task": "USER-20260815-SPECIES-NAME-LENGTH",
        "status": "PASS",
        "source_reference": {
            "url": "https://github.com/pret/pokefirered.git",
            "commit": "c75f352304d529f6ba92d4f74b9cf8b5c3810788",
            "use": "gSpeciesNames stock consumer semantic classification only",
        },
        "old_root": old_root,
        "consumer_count": len(consumers),
        "instruction_patch_count": len(SPECIES_NAME_PATCHES),
        "unreviewed_count": 0,
        "unmigrated_count": 0,
        "unknown_boundary_count": 0,
        "consumers": consumers,
        "battle_nickname_transfer_count": len(battle_transfers),
        "battle_nickname_veneer_cave": BATTLE_NICKNAME_COPY_CAVE,
        "species_picture_bound_thunk_cave":
            SPECIES_PICTURE_BOUND_THUNK_CAVE,
        "species_picture_bound_thunk_pointer_references": 0,
        "battle_nickname_transfers": battle_transfers,
        "nickname_display_bound": {
            "site": NICKNAME_END_BOUND_SITE,
            "address": ROM_BASE + NICKNAME_END_BOUND_SITE,
            "old_max_visible_glyphs": 5,
            "new_max_visible_glyphs": SPECIES_NAME_MAX_GLYPHS,
            "minimum_audited_destination_bytes": 8,
            "direct_call_count": len(direct_calls),
            "direct_calls": direct_calls,
            "cfru_long_call_literal_count": len(long_call_literals),
            "cfru_long_call_literals": long_call_literals,
            "expected_hex": "0524",
            "replacement_hex": "0624",
            "migrated": True,
        },
    }


def linked_learn_symbols(root: Path, config: Mapping[str, Any]) -> dict[str, int]:
    path = root / str(config["inputs"]["linked_object_path"])
    fixed(path, str(config["inputs"]["linked_object_sha256"]))
    required = {
        str(row["symbol"]) for row in config["learn_move_hooks"]
        if "target_symbol" not in row
    }
    symbols: dict[str, int] = {}
    for line in run(["arm-none-eabi-nm", "-n", str(path)], "T09 CFRU symbol audit").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in required:
            symbols[fields[2]] = int(fields[0], 16)
    if set(symbols) != required or any(address & 1 for address in symbols.values()):
        fail(f"T09 CFRU Learn Move symbol contract differs: {symbols}")
    return symbols


def compile_species_runtime(
    root: Path, load_address: int, names_address: int,
    learnsets_address: int, asset_locations: Mapping[str, int],
) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        fail("ARM GNU toolchain is required for T09 Species runtime")
    source = root / "overlays/species_surface/species_runtime.c"
    header = root / "overlays/species_surface/species_runtime.h"
    trampoline = root / "overlays/species_surface/species_runtime_trampoline.S"
    if not source.is_file() or not header.is_file() or not trampoline.is_file():
        fail("T09 Species runtime source/header is missing")
    with tempfile.TemporaryDirectory(prefix="vega-t09-species-") as raw:
        directory = Path(raw)
        linker = directory / "linker.ld"
        elf = directory / "species_runtime.elf"
        binary = directory / "species_runtime.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.VegaSpeciesSurface_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            f"-DVEGA_SPECIES_NAMES_ADDRESS=0x{names_address:08X}u",
            f"-DVEGA_LEVEL_UP_LEARNSETS_ADDRESS=0x{learnsets_address:08X}u",
            f"-DVEGA_FRONT_SPRITES_ADDRESS=0x{asset_locations['front']:08X}u",
            f"-DVEGA_BACK_SPRITES_ADDRESS=0x{asset_locations['back']:08X}u",
            f"-DVEGA_NORMAL_PALETTES_ADDRESS=0x{asset_locations['palette']:08X}u",
            f"-DVEGA_SHINY_PALETTES_ADDRESS=0x{asset_locations['shiny_palette']:08X}u",
            f"-DVEGA_ICON_PALETTE_INDICES_ADDRESS=0x{asset_locations['icon_palette']:08X}u",
            f"-DVEGA_NATIONAL_DEX_ADDRESS=0x{asset_locations['national_dex']:08X}u",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaSpeciesSurface_GetSpeciesName", f"-Wl,-T,{linker}",
            f"-I{source.parent}", str(source), str(trampoline), "-o", str(elf),
        ], "T09 Species runtime link", cwd=root)
        undefined = run([nm, "-u", str(elf)], "T09 Species runtime undefined symbols")
        if undefined:
            fail("T09 Species runtime has undefined symbols: " + undefined)
        run([objcopy, "-O", "binary", str(elf), str(binary)],
            "T09 Species runtime objcopy")
        symbols: dict[str, int] = {}
        for line in run([nm, "-n", "--defined-only", str(elf)],
                        "T09 Species runtime nm").splitlines():
            fields = line.split()
            if (len(fields) == 3 and fields[1] == "T"
                    and fields[2].startswith("VegaSpeciesSurface_")):
                symbols[fields[2]] = int(fields[0], 16)
        expected_symbols = {
            "VegaSpeciesSurface_GetSpeciesName",
            "VegaSpeciesSurface_CopyBattleNickname",
            "VegaSpeciesSurface_NationalPokedexNumToSpecies",
            "VegaSpeciesSurface_GiveBoxMonInitialMovesetAppended",
            "VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch",
            "VegaSpeciesSurface_GetIconSpecies",
            "VegaSpeciesSurface_SafeLoadMonIconPalette",
            "VegaSpeciesSurface_SafeFreeMonIconPalette",
            "VegaSpeciesSurface_GetValidMonIconPalettePtr",
            "VegaSpeciesSurface_GetValidMonIconPalIndex",
        }
        if set(symbols) != expected_symbols:
            fail(f"T09 Species runtime symbol set differs: {symbols}")
        runtime = binary.read_bytes()
        if not runtime or len(runtime) > 4096:
            fail(f"unexpected T09 Species runtime size: {len(runtime)}")
        return runtime, symbols


def absolute_thumb_hook(register: int, target: int) -> bytes:
    if not 0 <= register <= 7 or target & 1:
        fail("invalid aligned Thumb hook target/register")
    return bytes((0, 0x48 | register, register << 3, 0x47)) + struct.pack("<I", target | 1)


def thumb_bl(site: int, target: int) -> bytes:
    """Encode a Thumb-1 BL from one ROM file offset to another."""
    delta = target - (site + 4)
    if delta & 1 or not -0x400000 <= delta < 0x400000:
        fail(f"Thumb BL target out of range: site=0x{site:X} target=0x{target:X}")
    return struct.pack(
        "<HH",
        0xF000 | ((delta >> 12) & 0x07FF),
        0xF800 | ((delta >> 1) & 0x07FF),
    )


def run_species_runtime_smoke(root: Path, rom: bytes) -> dict[str, Any]:
    source = root / "tools/mgba_species_runtime_smoke.c"
    compiler = shutil.which("cc")
    if compiler is None or not source.is_file():
        fail("T09 exact-ROM Species runtime smoke prerequisites are missing")
    build_root = root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".t09-species-runtime-", dir=build_root) as raw:
        work = Path(raw)
        candidate = work / "candidate.gba"
        executable = work / "mgba_species_runtime_smoke"
        candidate.write_bytes(rom)
        completed = subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(source), "-o", str(executable), "-lmgba"],
            cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=60, check=False,
        )
        if completed.returncode or completed.stdout or completed.stderr:
            fail("T09 Species runtime smoke compile failed/noisy: "
                 + (completed.stdout + completed.stderr)[-2000:])
        environment = {
            "HOME": str(work), "LC_ALL": "C", "LANG": "C",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "TZ": "UTC",
        }
        completed = subprocess.run(
            [str(executable), str(candidate)], cwd=work, env=environment,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=180, check=False,
        )
        if completed.returncode or completed.stderr:
            fail("T09 Species runtime smoke failed: "
                 + (completed.stdout + completed.stderr)[-2000:])
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            fail(f"T09 Species runtime smoke returned invalid JSON: {error}")
        expected = {
            "status": "PASS", "species_created": 1619,
            "species_named": 1620, "display_species_checked": 7,
            "egg_species": 412, "caterpie_species": 649,
            "canonical_species_count": 1621,
            "compatibility_names_checked": 1620,
            "six_glyph_names": 134, "buffer_canaries": True,
            "stock_string_routes": 4, "surface_name_routes": 7,
            "form_base_names_checked": 3,
            "battle_name_cases": 2, "battle_messages": 2,
            "healthbox_tile_cases": 2, "level100_form_cases": 2,
            "back_sprite_full_64x64_cases": 2,
            "canonical_form_ability_families": 7,
            "canonical_form_transitions": 8,
        }
        if any(result.get(key) != value for key, value in expected.items()):
            fail(f"T09 Species runtime smoke contract differs: {result}")
        return {
            **result, "process_runs": 1,
            "runner_sha256": sha(source.read_bytes()),
        }


def patch_exact(output: bytearray, stage: bytes, site: int, expected: bytes,
                replacement: bytes, label: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        fail(f"{label}: patch width differs")
    actual = bytes(stage[site:site + len(expected)])
    if actual != expected:
        fail(f"{label}: expected={expected.hex()} actual={actual.hex()}")
    output[site:site + len(replacement)] = replacement
    return {"label": label, "site": site, "address": ROM_BASE + site,
            "expected_hex": expected.hex(), "replacement_hex": replacement.hex()}


def breeding_fixture() -> dict[str, Any]:
    cases = [
        ("everstone_nature_form", ["EVERSTONE", "REGIONAL_FORM"], "nature_and_form_inherited"),
        ("destiny_knot_unique_five", ["DESTINY_KNOT"], "five_unique_iv_stats"),
        ("power_item_forced_iv", ["POWER_ITEM", "DESTINY_KNOT"], "forced_stat_in_five"),
        ("both_parent_egg_moves", ["MOTHER_EGG_MOVE", "FATHER_EGG_MOVE"], "both_moves_inherited"),
        ("common_level_moves", ["COMMON_LEVEL_MOVE"], "common_moves_inherited"),
        ("ball_and_ability", ["BALL", "ABILITY_SLOT", "HIDDEN_ABILITY"], "legal_parent_rolls"),
        ("incense_baby", ["INCENSE"], "baby_species_selected"),
        ("ditto", ["DITTO"], "non_ditto_parent_is_line_owner"),
        ("masuda_six_rolls", ["DIFFERENT_TRAINER_ID"], "six_shiny_rolls"),
        ("egg_to_pc", ["PARTY_FULL"], "single_pc_delivery"),
        ("party_and_boxes_full", ["PARTY_FULL", "BOXES_FULL"], "queue_retained_no_duplicate"),
        ("queue_capacity", ["FIVE_EGGS_QUEUED"], "sixth_rejected"),
        ("hatch_modes", ["NORMAL", "SHORT", "SKIP"], "three_modes_bounded"),
        ("compact_iv_ev", ["SUMMARY_FIELD", "PC_RIGHT_PANE", "EGG_IV"], "existing_panels_only"),
        ("free_move_relearner", ["ZERO_COST", "EXISTING_SCREEN"], "no_currency_mutation"),
        ("oval_charm_locked", ["CAUGHT_99"], "base_rate_20_percent"),
        ("oval_charm_unlocked_caught", ["CAUGHT_100"], "doubled_rate_40_percent"),
        ("oval_charm_unlocked_quest", ["QUEST_COMPLETE"], "doubled_rate_40_percent"),
    ]
    return {"schema_version": 1, "fixed_rng": [7, 2, 5, 1, 0, 4, 3, 9, 6, 8],
            "cases": [{"id": key, "features": features, "expected": expected}
                      for key, features, expected in cases], "status": "PASS"}


class Allocator:
    def __init__(self, start: int, end: int): self.cursor, self.end, self.entries = start, end, []
    def put(self, name: str, data: bytes, alignment: int = 4) -> int:
        self.cursor = (self.cursor + alignment - 1) & -alignment
        if self.cursor + len(data) > self.end:
            fail(f"T09 allocation overflow at {name}")
        offset = self.cursor
        self.cursor += len(data)
        self.entries.append({"name": name, "offset": offset, "address": ROM_BASE + offset,
                             "size": len(data), "sha256": sha(data)})
        return offset


def build_model(root: Path = ROOT) -> tuple[dict[str, bytes], dict[str, Any], bytes]:
    config = read_json(root / CONFIG)
    stage = fixed(
        root / config["inputs"]["stage07_path"],
        expected_stage07_sha(root, config),
    )
    dpe = fixed(root / config["inputs"]["dpe_rom_path"], config["inputs"]["dpe_rom_sha256"])
    models = {name: read_json(root / config["inputs"][path]) for name, path in (
        ("species", "species_model_path"), ("moves", "move_model_path"), ("ids", "id_model_path"))}
    rows = models["species"]["species"]
    if len(rows) != 1621 or [int(row["id"]) for row in rows] != list(range(1621)):
        fail("T07 canonical Species ABI changed")
    species_alias, move_alias, item_alias = aliases(models)
    species_names = fixed(
        root / str(config["inputs"]["species_names_path"]),
        str(config["inputs"]["species_names_sha256"]),
    )
    names_compat, species_name_model = compatibility_species_names(
        species_names, rows
    )
    name_consumer_model = species_name_consumer_model(stage)
    learn_symbols = linked_learn_symbols(root, config)

    strides, roots, sites = config["strides"], config["dpe_roots"], config["pointer_sites"]
    tables: dict[str, bytes] = {}
    for name in ("front", "back", "palette", "shiny_palette", "icon", "icon_palette",
                 "front_coords", "back_coords", "elevation", "dex_entries"):
        tables[name] = table_merge(stage, dpe, rows, int(sites[name]), int(roots[name]),
                                   int(strides[name]), 412, name)
    # A handful of DPE battle-only helper IDs intentionally have NULL display
    # assets.  Canonical storage/UI paths must never dereference NULL, so bind
    # those rows to DPE's bounded default row while retaining their form ID.
    for name in ("front", "back", "palette", "shiny_palette", "icon"):
        stride = int(strides[name])
        default = slice_at(dpe, int(roots[name]), stride, f"DPE default {name}")
        mutable = bytearray(tables[name])
        for cid in range(412, len(rows)):
            if struct.unpack_from("<I", mutable, cid * stride)[0] == 0:
                mutable[cid * stride:(cid + 1) * stride] = default
        tables[name] = bytes(mutable)
    tag_normalization = canonicalize_display_tags(tables, len(rows))
    footprint_root = ptr(stage, int(sites["footprint"]))
    footprints = bytearray(slice_at(stage, footprint_root, 412 * 4, "Vega footprints"))
    footprint_map = dpe_footprints(root)
    for row in rows[412:]:
        footprints += struct.pack("<I", footprint_map.get(int(row["dpe_id"]), 0x08C3058C))
    tables["footprint"] = bytes(footprints)
    tables["cry"] = cry_merge(stage, dpe, rows, int(sites["cry"]), int(roots["cry"]), 412)
    tables["cry2"] = cry_merge(stage, dpe, rows, int(sites["cry2"]), int(roots["cry2"]), 412)
    tables["national_dex"] = (root / "generated/engine/species/national_dex.bin").read_bytes()
    native_national_root = ptr(stage, 0x429A0)
    # Stock SpeciesToNationalPokedexNum indexes a species-1 table and has
    # observable register behavior relied on by the linked Raid controller.
    # Preserve its exact code and native Vega rows, reserve Egg as zero, then
    # append the canonical official mapping for Species 413..1620.
    tables["national_dex_runtime"] = (
        slice_at(stage, native_national_root, 411 * 2,
                 "native Vega Species-to-National table")
        + struct.pack("<H", 0)
        + tables["national_dex"][413 * 2:]
    )
    if len(tables["national_dex_runtime"]) != 1620 * 2:
        fail("hybrid Species-to-National runtime table size differs")
    validation = validate_assets(dpe, tables, rows, 412)

    evolutions, evolution_model = merge_evolutions(stage, dpe, config, rows,
                                                    species_alias, move_alias, item_alias)
    v2 = normalize_v2(root / config["inputs"]["v2_evolution_path"])

    allocator = Allocator(int(config["allocation"]["start_offset"]), int(config["allocation"]["end_offset"]))
    # Level-up data address must be known before its pointer table is rendered.
    provisional_level_data = allocator.cursor + 4
    learn, learn_model = merge_learnsets(stage, dpe, config, rows, species_alias, move_alias,
                                         ROM_BASE + provisional_level_data)
    # Reserve exact tables in the same order used to calculate the final pointer base below.
    assets_order = ("front", "back", "palette", "shiny_palette", "icon", "icon_palette",
                    "front_coords", "back_coords", "elevation", "footprint", "cry", "cry2",
                    "dex_entries", "national_dex")
    output_rom = bytearray(stage)
    copy_start, copy_end = int(config["dpe_copy"]["start_offset"]), int(config["dpe_copy"]["end_offset"])
    output_rom[copy_start:copy_end] = dpe[copy_start:copy_end]
    locations: dict[str, int] = {}
    for name in assets_order:
        off = allocator.put(name, tables[name]); locations[name] = ROM_BASE + off
    off = allocator.put("national_dex_runtime", tables["national_dex_runtime"])
    locations["national_dex_runtime"] = ROM_BASE + off
    off = allocator.put("evolutions", evolutions); locations["evolution"] = ROM_BASE + off
    # Allocate level data before pointers and rebuild pointers against the real address.
    off = allocator.put("level_up_data", learn["level_up_data"]); locations["level_up_data"] = ROM_BASE + off
    learn, learn_model = merge_learnsets(stage, dpe, config, rows, species_alias, move_alias,
                                         locations["level_up_data"])
    for name in ("level_up_pointers", "egg_moves", "tmhm", "tutor"):
        off = allocator.put(name, learn[name]); locations[name] = ROM_BASE + off
    off = allocator.put("species_names", species_names)
    locations["species_names"] = ROM_BASE + off
    off = allocator.put("species_names_legacy", names_compat)
    locations["species_names_legacy"] = ROM_BASE + off
    runtime_load = ROM_BASE + ((allocator.cursor + 3) & ~3)
    runtime, runtime_symbols = compile_species_runtime(
        root, runtime_load, locations["species_names"],
        locations["level_up_pointers"], locations,
    )
    off = allocator.put("species_runtime", runtime)
    if ROM_BASE + off != runtime_load:
        fail("T09 Species runtime linker address disagrees with allocation")
    locations["species_runtime"] = ROM_BASE + off
    payloads = {**tables, **learn, "evolutions": evolutions,
                "species_names": species_names,
                "species_names_legacy": names_compat,
                "species_runtime": runtime}
    for entry in allocator.entries:
        data = payloads[entry["name"]]
        output_rom[entry["offset"]:entry["offset"] + len(data)] = data

    bindings = {"front": "front", "back": "back", "palette": "palette",
                "shiny_palette": "shiny_palette", "icon": "icon", "icon_palette": "icon_palette",
                "front_coords": "front_coords", "back_coords": "back_coords", "elevation": "elevation",
                "footprint": "footprint", "cry": "cry", "cry2": "cry2", "evolution": "evolution",
                "egg": "egg_moves", "tmhm": "tmhm", "tutor": "tutor",
                "dex_entries": "dex_entries"}
    display_literal_counts = {
        "front": 28, "back": 10, "palette": 5, "shiny_palette": 3,
        "icon": 3, "icon_palette": 11, "front_coords": 16,
        "back_coords": 8, "elevation": 4, "footprint": 1,
        "cry": 2, "cry2": 2, "dex_entries": 8,
    }
    repoints = {}
    for key, location_key in bindings.items():
        site = int(sites[key]); old = ptr(stage, site); new = locations[location_key]
        literal_sites = [site]
        if key in display_literal_counts:
            old_bytes = struct.pack("<I", old)
            literal_sites = [
                index for index in range(0, len(stage) - 3, 4)
                if stage[index:index + 4] == old_bytes
            ]
            if len(literal_sites) != display_literal_counts[key]:
                fail(
                    f"stock {key} literal inventory changed: "
                    f"{len(literal_sites)}"
                )
        for literal_site in literal_sites:
            output_rom[literal_site:literal_site + 4] = struct.pack("<I", new)
        repoints[key] = {
            "site": site, "sites": literal_sites, "count": len(literal_sites),
            "old": old, "new": new,
        }
    # The two stock national-Dex consumers have different runtime semantics.
    # National->Species uses the bounded canonical adapter installed below;
    # Species->National keeps its exact stock instruction/register behavior
    # and reads the hybrid native+canonical table.
    national_site = int(sites["national_dex"])
    old_national_root = ptr(stage, national_site)
    old_national_bytes = struct.pack("<I", old_national_root)
    national_sites = [
        index for index in range(0, len(stage) - 3, 4)
        if stage[index:index + 4] == old_national_bytes
    ]
    if national_sites != [0x4292C, 0x429A0]:
        fail(f"stock national Dex literal inventory changed: {national_sites}")
    repoints["national_dex"] = {
        "site": national_site,
        "old": old_national_root,
        "new": locations["national_dex"], "applied": False,
        "runtime_adapter": True,
    }
    output_rom[0x429A0:0x429A4] = struct.pack(
        "<I", locations["national_dex_runtime"]
    )
    repoints["national_dex_runtime"] = {
        "site": 0x429A0, "old": old_national_root,
        "new": locations["national_dex_runtime"], "applied": True,
        "native_rows": 411, "egg_species": 412,
        "canonical_rows": 1208,
    }
    # The native packed-table routine remains the exact path for Vega IDs.
    # Its literal therefore stays on the original table; the dispatcher uses
    # the canonical table only for appended IDs.
    native_level_site = int(sites["level_up"])
    native_level_root = ptr(stage, native_level_site)
    repoints["level_up"] = {
        "site": native_level_site, "old": native_level_root,
        "new": locations["level_up_pointers"], "applied": False,
        "legacy_root_preserved": True,
    }
    # CFRU Learn Move consumers load the canonical pointer root through this
    # stock global, independently of the native GiveBoxMon literal above.
    level_root_storage = 0x4346C
    old_level_root = ptr(stage, level_root_storage)
    if old_level_root != native_level_root:
        fail("stock level-up root storage differs from GiveBoxMon literal")
    output_rom[level_root_storage:level_root_storage + 4] = struct.pack(
        "<I", locations["level_up_pointers"]
    )
    repoints["level_up_cfru_root"] = {
        "site": level_root_storage, "old": old_level_root,
        "new": locations["level_up_pointers"],
    }

    # Stock UI code has 40 aligned gSpeciesNames literals.  Repoint them to the
    # audited eight-byte Japanese six-glyph ABI and patch each reachable
    # species*6 calculation to species*8.  GetSpeciesName itself is replaced
    # at its entry and continues to use the canonical eleven-byte table.
    old_names_root = ptr(stage, 0x144)
    old_names_bytes = struct.pack("<I", old_names_root)
    compatibility_name_sites = [
        row["literal_site"] for row in name_consumer_model["consumers"]
    ]
    if any(
        stage[site:site + 4] != old_names_bytes
        for site in compatibility_name_sites
    ):
        fail("stock Species name literal differs after inventory audit")
    for site in compatibility_name_sites:
        output_rom[site:site + 4] = struct.pack("<I", locations["species_names_legacy"])
    species_name_instruction_patches = []
    for consumer_site, site, expected_hex, replacement_hex, label in SPECIES_NAME_PATCHES:
        patch = patch_exact(
            output_rom, stage, site, bytes.fromhex(expected_hex),
            bytes.fromhex(replacement_hex), f"Species name: {label}",
        )
        patch["consumer_literal_site"] = consumer_site
        species_name_instruction_patches.append(patch)
    for row in name_consumer_model["consumers"]:
        row["new_root"] = (
            locations["species_names"]
            if row["strategy"] == "canonical_getter"
            else locations["species_names_legacy"]
        )
    name_consumer_model["instruction_patches"] = species_name_instruction_patches
    name_consumer_model["compatibility_root"] = locations["species_names_legacy"]
    name_consumer_model["canonical_root"] = locations["species_names"]
    repoints["species_names_legacy"] = {
        "sites": compatibility_name_sites,
        "count": len(compatibility_name_sites),
        "old": old_names_root, "new": locations["species_names_legacy"],
        "old_stride": 6, "new_stride": SPECIES_NAME_COMPAT_STRIDE,
        "instruction_patches": len(species_name_instruction_patches),
    }
    # T06 redirected CFRU evolution consumers to its canonical 1440-row root.
    # Replace every aligned literal for that root so appended IDs 1440..1620
    # cannot index the superseded table.
    stage06_meta = read_json(root / config["inputs"]["stage06_metadata_path"])
    old_evolution_runtime = int(stage06_meta["runtime_tables"]["evolutions"]["address"])
    old_bytes = struct.pack("<I", old_evolution_runtime)
    runtime_sites = [index for index in range(0, len(stage) - 3, 4)
                     if stage[index:index + 4] == old_bytes]
    if not runtime_sites:
        fail("T06 canonical evolution consumer root is no longer referenced")
    for site in runtime_sites:
        output_rom[site:site + 4] = struct.pack("<I", locations["evolution"])
    repoints["evolution_runtime"] = {"sites": runtime_sites, "count": len(runtime_sites),
                                      "old": old_evolution_runtime,
                                      "new": locations["evolution"]}
    # SpeciesToCryId: canonical cry table is Species-indexed, so return species+1 directly.
    cry_adapter = bytes.fromhex("0130704700bf00bf")
    expected = bytes(stage[0x429F4:0x429FC])
    if expected != bytes.fromhex("00b50004000c011c"):
        fail(f"SpeciesToCryId prologue changed: {expected.hex()}")
    output_rom[0x429F4:0x429FC] = cry_adapter

    runtime_patches: list[dict[str, Any]] = []
    battle_copy_target = runtime_symbols[
        "VegaSpeciesSurface_CopyBattleNickname"
    ]
    battle_copy_veneer = (
        bytes.fromhex("004b1847") + struct.pack("<I", battle_copy_target | 1)
    )
    veneer_patch = patch_exact(
        output_rom, stage, BATTLE_NICKNAME_COPY_CAVE, b"\xFF" * 8,
        battle_copy_veneer, "six-glyph battle nickname copy veneer",
    )
    runtime_patches.append(veneer_patch)
    transfer_patches: dict[int, dict[str, Any]] = {}
    for site, expected_hex, purpose in BATTLE_NICKNAME_TRANSFER_SITES:
        patch = patch_exact(
            output_rom, stage, site, bytes.fromhex(expected_hex),
            thumb_bl(site, BATTLE_NICKNAME_COPY_CAVE),
            f"six-glyph battle nickname: {purpose}",
        )
        patch.update({
            "veneer_site": BATTLE_NICKNAME_COPY_CAVE,
            "target": battle_copy_target | 1,
        })
        runtime_patches.append(patch)
        transfer_patches[site] = patch
    name_consumer_model["battle_nickname_veneer"] = {
        **veneer_patch,
        "target_symbol": "VegaSpeciesSurface_CopyBattleNickname",
        "target": battle_copy_target | 1,
    }
    for row in name_consumer_model["battle_nickname_transfers"]:
        row.update({
            "replacement_hex": transfer_patches[row["site"]]["replacement_hex"],
            "veneer_site": BATTLE_NICKNAME_COPY_CAVE,
            "target": battle_copy_target | 1,
        })
    nickname_bound_patch = patch_exact(
        output_rom, stage, NICKNAME_END_BOUND_SITE, bytes.fromhex("0524"),
        bytes.fromhex("0624"), "six-glyph StringGetEnd10 display bound",
    )
    runtime_patches.append(nickname_bound_patch)
    name_consumer_model["nickname_display_bound"]["patch"] = nickname_bound_patch
    name_target = runtime_symbols["VegaSpeciesSurface_GetSpeciesName"]
    runtime_patches.append(patch_exact(
        output_rom, stage, 0x406C4, bytes.fromhex("f0b5061c09040c0c"),
        absolute_thumb_hook(3, name_target), "canonical GetSpeciesName",
    ))
    display_hook_specs = (
        (0x96988, "00b50004020cc92a", "VegaSpeciesSurface_GetIconSpecies", 2,
         "canonical icon species"),
        (0x96ACC, "10b50004010cce20", "VegaSpeciesSurface_SafeLoadMonIconPalette", 1,
         "bounded icon palette load"),
        (0x96B64, "00b50004010cce20", "VegaSpeciesSurface_SafeFreeMonIconPalette", 1,
         "bounded icon palette free"),
        (0x96BF8, "00b50004020cce20", "VegaSpeciesSurface_GetValidMonIconPalettePtr", 1,
         "bounded icon palette pointer"),
        (0x96C24, "00b50004010cce20", "VegaSpeciesSurface_GetValidMonIconPalIndex", 1,
         "bounded icon palette index"),
    )
    for site, expected_hex, symbol, register, label in display_hook_specs:
        runtime_patches.append(patch_exact(
            output_rom, stage, site, bytes.fromhex(expected_hex),
            absolute_thumb_hook(register, runtime_symbols[symbol]), label,
        ))

    # Preserve the stock image/palette routines and widen their native 412
    # ceiling without deleting the row-0 fallback.  The 0xFFFF sentinel is a
    # legitimate caught-summary input; an unconditional branch here indexed
    # past the 1,621-row canonical table, treated arbitrary bytes as an LZ
    # stream, and corrupted the field heap.  A nearby audited eight-byte cave
    # returns the exact canonical max in r0, so every call site retains its
    # original register contract and conditional fallback.
    picture_bound_thunk = bytes.fromhex("00487047") + struct.pack(
        "<I", len(rows) - 1,
    )
    runtime_patches.append(patch_exact(
        output_rom, stage, SPECIES_PICTURE_BOUND_THUNK_CAVE, b"\xFF" * 8,
        picture_bound_thunk, "canonical picture Species-bound thunk",
    ))
    for site, compare, expected_hex, label in (
        (0x0E648, 0x4285, "ce204000854207dd",
         "canonical DecompressPicFromTable bound"),
        (0x0EA98, 0x4282, "ce204000824207dd",
         "canonical DecompressPicFromTable no-Deoxys bound"),
        (0x0E720, 0x4287, "ce204000874207dd",
         "canonical HandleLoadSpecialPokePic bound"),
        (0x0EB64, 0x4287, "ce204000874207dd",
         "canonical HandleLoadSpecialPokePic no-Deoxys bound"),
    ):
        replacement = (
            thumb_bl(site, SPECIES_PICTURE_BOUND_THUNK_CAVE)
            + struct.pack("<HH", compare, 0xD907)
        )
        runtime_patches.append(patch_exact(
            output_rom, stage, site, bytes.fromhex(expected_hex),
            replacement, label,
        ))
    # The JP routine has the same three Species<=412 position limiters as DPE,
    # but invalid/sentinel Species (notably 0xFFFF) must retain the stock safe
    # fallback.  Replacing the conditional branch unconditionally would index
    # the canonical coord tables out of range and eventually exhaust the field
    # heap through repeated zero-sized sprite allocations.  Reuse the old
    # fallback literal slot for the exact canonical max, then repoint the
    # fallback load to the following duplicate table-pointer literal.
    for site, fallback_load, bound_literal, fallback_literal, label in (
        (0x73DFC, 0x73E04, 0x73E08, 0x73E14,
         "canonical front sprite coordinate bound"),
        (0x73ECC, 0x73ED4, 0x73ED8, 0x73EEC,
         "canonical back sprite coordinate bound"),
        (0x73F2C, 0x73F34, 0x73F38, 0x73F4C,
         "canonical battler Y coordinate bound"),
    ):
        target = 0x08000000 + fallback_literal
        literal_pc = (0x08000000 + fallback_load + 4) & ~3
        literal_delta = target - literal_pc
        if literal_delta < 0 or literal_delta > 1020 or literal_delta % 4:
            fail(f"{label}: fallback literal is outside Thumb LDR range")
        replacement = (
            bytes.fromhex("02488442")  # ldr r0,[pc,#8]; cmp r4,r0
            + bytes.fromhex("04d900bf")  # bls canonical; nop
        )
        runtime_patches.append(patch_exact(
            output_rom, stage, site, bytes.fromhex("ce204000844203d9"),
            replacement, label,
        ))
        runtime_patches.append(patch_exact(
            output_rom, stage, fallback_load, bytes.fromhex("0048"),
            struct.pack("<H", 0x4800 | (literal_delta // 4)),
            f"{label} safe fallback literal",
        ))
        runtime_patches.append(patch_exact(
            output_rom, stage, bound_literal,
            bytes(stage[bound_literal:bound_literal + 4]),
            struct.pack("<I", len(rows) - 1),
            f"{label} canonical max literal",
        ))
    # Unown B starts at canonical 650 after reserving 412 for the Egg sentinel;
    # the stock routine receives letters 1..27, hence its new base delta is 649.
    for site, label in (
        (0x0E6F2, "canonical Unown form base"),
        (0x0EB36, "canonical Unown form base no-Deoxys"),
    ):
        runtime_patches.append(patch_exact(
            output_rom, stage, site,
            bytes.fromhex("ce22520088180004010c"),
            bytes.fromhex("a222920001328818011c"), label,
        ))
    runtime_patches.append(patch_exact(
        output_rom, stage, 0x4374C, bytes.fromhex("04d9"),
        bytes.fromhex("04e0"), "canonical personality palette bound",
    ))
    runtime_patches.append(patch_exact(
        output_rom, stage, 0x428F0, bytes.fromhex("10b50004020c002a"),
        absolute_thumb_hook(
            3, runtime_symbols["VegaSpeciesSurface_NationalPokedexNumToSpecies"]
        ),
        "bounded National Dex to canonical Species",
    ))
    runtime_patches.append(patch_exact(
        output_rom, stage, 0x968A4, bytes.fromhex("01d9"),
        bytes.fromhex("01e0"), "preserve canonical icon palette tag",
    ))
    learn_hooks: list[dict[str, Any]] = []
    for row in config["learn_move_hooks"]:
        symbol = str(row["symbol"])
        site = int(row["site"])
        target_symbol = str(row.get("target_symbol", symbol))
        target = (runtime_symbols[target_symbol]
                  if "target_symbol" in row else learn_symbols[symbol])
        patch = patch_exact(
            output_rom, stage, site, bytes.fromhex(str(row["expected_hex"])),
            absolute_thumb_hook(int(row["register"]), target),
            f"CFRU Learn Move {symbol}",
        )
        patch.update({"symbol": symbol, "target_symbol": target_symbol,
                      "target": target | 1,
                      "register": int(row["register"])})
        learn_hooks.append(patch)

    runtime_smoke = run_species_runtime_smoke(root, bytes(output_rom))

    asset_model = {"schema_version": 1, "task": TASK, "species_count": len(rows),
                   "vega_preserved": 412, "dpe_appended": len(rows) - 412,
                   "tag_normalization": tag_normalization,
                   "animation_policy": {"vega": "ORIGINAL_CALLBACKS_PRESERVED",
                                        "appended": "DPE_DEFAULT_SPECIES_ANIMATION"},
                   "display_matrix": {
                       "summary": ["icon", "icon_palette", "front_coords"],
                       "party": ["icon", "icon_palette"],
                       "pc": ["icon", "icon_palette"],
                       "battle": ["front", "back", "palette", "shiny_palette", "front_coords", "back_coords"],
                       "evolution": ["front", "palette", "cry"],
                       "dex": ["front", "palette", "dex_entries", "national_dex"],
                   },
                   "validation": validation, "status": "PASS"}
    fixture = breeding_fixture()
    dex_report = f"""# T09 Dex policy\n\n- Vega地方図鑑は既存イベント互換のためSpecies `0..411`を別集計する。\n- 全国図鑑はT07のcanonical National Dex `1..1025`をseen/caught bitmapのキーとし、formは同じ全国番号を共有する。\n- Vega完成イベントは旧フラグと地方集計だけを参照し、追加フォームで必要数が変化しない。\n- まるいおまもりは異なる公式全国番号100種またはquest完了の早い方で解禁し、タマゴ生成成功率を `{config['oval_charm']['base_numerator']}% -> {2 * config['oval_charm']['base_numerator']}%`へ変換する。\n\nStatus: PASS\n""".encode()
    asset_report = f"""# T09 Species asset validation\n\n- canonical Species: {len(rows)}\n- Vega lossless rows: 412\n- DPE appended rows: {len(rows)-412}\n- LZ77 headers: {validation['compressed_checked']} PASS\n- aligned pointers: {validation['aligned_pointers']} PASS\n- icons: {validation['icons_checked']} PASS\n- canonical resource tags: {validation['canonical_tags_checked']} PASS\n- runtime exact patches: {len(runtime_patches)} PASS\n- runtime Egg sentinel: canonical 412 / DPE 412\n- Caterpie display row: canonical 649 / DPE 10\n- exact-ROM mGBA display samples: {runtime_smoke['display_species_checked']} PASS\n- Species名: canonical {species_name_model['canonical_stride']} byte / compatibility {species_name_model['compatibility_stride']} byte\n- 6文字Species名: {species_name_model['six_glyph_count']} / 40 consumers audited / {name_consumer_model['instruction_patch_count']} instruction patches\n- 戦闘nickname転送: {name_consumer_model['battle_nickname_transfer_count']} routes / 8-byte field限定\n- front, back, palette, shiny palette, coordinates, icon, icon palette, footprint fallback, cry, Dex entry: PASS\n- summary / party / PC / battle / evolution / Dex table bounds: PASS\n\nStatus: PASS\n""".encode()
    asset_report = asset_report.replace(
        b"- front, back, palette, shiny palette",
        (
            "- nickname表示上限: 5→6 / native "
            f"{name_consumer_model['nickname_display_bound']['direct_call_count']} calls "
            "+ CFRU "
            f"{name_consumer_model['nickname_display_bound']['cfru_long_call_literal_count']} "
            "literal pools audited\n- front, back, palette, shiny palette"
        ).encode("utf-8"),
    )
    six_name_lines = "\n".join(
        f"- {row['id']}: {row['display_name']} / `{row['canonical_hex']}` / "
        f"form=`{row['form_key'] or '-'}`"
        for row in species_name_model["six_glyph_rows"]
    )
    consumer_lines = "\n".join(
        f"- `0x{row['literal_site']:06X}` {row['surface']}: {row['purpose']} / "
        f"stride {row['old_row_stride']}→{row['new_row_stride']} / "
        f"buffer={row['output_buffer_bytes']} / draw={row['max_draw_glyphs']} / "
        f"strategy={row['strategy']}"
        for row in name_consumer_model["consumers"]
    )
    battle_transfer_lines = "\n".join(
        f"- `0x{row['site']:06X}`: {row['purpose']} / "
        f"buffer={row['destination_buffer_bytes']} / "
        f"glyph {row['old_max_visible_glyphs']}→{row['new_max_visible_glyphs']} / "
        f"veneer=`0x{row['veneer_site']:06X}`"
        for row in name_consumer_model["battle_nickname_transfers"]
    )
    species_name_report = f"""# 6文字Species名 consumer監査

## 結論

- canonical: {species_name_model['species_count']} rows × {species_name_model['canonical_stride']} bytes
- compatibility: {species_name_model['species_count']} rows × {species_name_model['compatibility_stride']} bytes
- 長さ分布: `{json.dumps(species_name_model['length_distribution'], ensure_ascii=False, sort_keys=True)}`
- 6文字: {species_name_model['six_glyph_count']} rows
- 5文字以下byte維持: {species_name_model['unchanged_five_or_fewer']} rows
- consumer: {name_consumer_model['consumer_count']} / 未監査 {name_consumer_model['unreviewed_count']} / 未移行 {name_consumer_model['unmigrated_count']} / 境界不明 {name_consumer_model['unknown_boundary_count']}
- stride/bound patch: {name_consumer_model['instruction_patch_count']}
- 戦闘nickname転送: {name_consumer_model['battle_nickname_transfer_count']} / 8-byte BattlePokemon field限定
- nickname表示上限: 5→6 / native {name_consumer_model['nickname_display_bound']['direct_call_count']} calls + CFRU {name_consumer_model['nickname_display_bound']['cfru_long_call_literal_count']} literal pools監査済み

## consumer inventory

{consumer_lines}

## 戦闘nickname転送

共有のcopy helperは維持し、転送先境界が8 byteと確認できた経路だけを6文字+EOS wrapperへ移行する。表示用 `StringGetEnd10` は全callerの境界監査後に6文字へ拡張する。

{battle_transfer_lines}

## 6文字全行

{six_name_lines}

Status: PASS
""".encode("utf-8")
    artifacts: dict[str, bytes] = {
        "generated/engine/species_assets/species_assets.json": stable(asset_model),
        **{f"generated/engine/species_assets/{name}.bin": tables[name] for name in assets_order},
        "generated/engine/species/species_names_legacy.bin": names_compat,
        "generated/engine/species/species_name_consumers.json": stable({
            **name_consumer_model,
            "name_table": species_name_model,
        }),
        "generated/engine/evolutions/evolutions.bin": evolutions,
        "generated/engine/evolutions/evolutions.json": stable(evolution_model),
        "generated/engine/evolutions/v2_normalized.json": stable(v2),
        **{f"generated/engine/learnsets/{name}.bin": data for name, data in learn.items()},
        "generated/engine/learnsets/learnsets.json": stable(learn_model),
        "generated/runtime/species_surface.bin": runtime,
        "generated/runtime/species_surface_symbols.json": stable({
            "schema_version": 1, "task": TASK, "status": "PASS",
            "load_address": locations["species_runtime"],
            "names_address": locations["species_names"],
            "symbols": runtime_symbols,
        }),
        "reports/generated/dex_policy.md": dex_report,
        "reports/generated/species_asset_validation.md": asset_report,
        "reports/generated/species_name_consumers.md": species_name_report,
        "tests/fixtures/breeding_matrix.json": stable(fixture),
    }
    if set(artifacts) != set(ARTIFACTS):
        fail(f"artifact contract mismatch: {set(ARTIFACTS) ^ set(artifacts)}")
    metadata = {"schema_version": 1, "task": TASK, "status": "PASS",
                "input": {"path": config["inputs"]["stage07_path"], "sha256": sha(stage)},
                "output": {"path": config["output"]["rom_path"], "size": len(output_rom),
                           "sha256": sha(bytes(output_rom))},
                "allocation": {"start": int(config["allocation"]["start_offset"]),
                               "end": allocator.cursor, "limit": allocator.end,
                               "free": allocator.end - allocator.cursor, "entries": allocator.entries},
                "repoints": repoints, "cry_adapter": {"site": 0x429F4, "bytes": cry_adapter.hex()},
                "runtime": {"address": locations["species_runtime"], "size": len(runtime),
                            "sha256": sha(runtime), "symbols": runtime_symbols,
                            "patches": runtime_patches},
                "learn_move_hooks": learn_hooks,
                "runtime_smoke": runtime_smoke,
                "species_names": species_name_model,
                "species_name_consumers": name_consumer_model,
                "assets": asset_model, "evolutions": {k: v for k, v in evolution_model.items() if k != "rows"},
                "learnsets": learn_model, "v2": {k: v for k, v in v2.items() if k != "rows"},
                "breeding": {"cases": len(fixture["cases"]), "status": fixture["status"]}}
    return artifacts, metadata, bytes(output_rom)


def build(root: Path = ROOT) -> dict[str, Any]:
    artifacts, metadata, rom = build_model(root)
    for path, data in artifacts.items():
        target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    config = read_json(root / CONFIG)
    rom_path = root / config["output"]["rom_path"]
    meta_path = root / config["output"]["metadata_path"]
    rom_path.parent.mkdir(parents=True, exist_ok=True); rom_path.write_bytes(rom); meta_path.write_bytes(stable(metadata))
    return metadata


def check(root: Path = ROOT) -> dict[str, Any]:
    artifacts, metadata, rom = build_model(root)
    config = read_json(root / CONFIG)
    expected = {**artifacts, config["output"]["rom_path"]: rom,
                config["output"]["metadata_path"]: stable(metadata)}
    for path, data in expected.items():
        target = root / path
        if not target.is_file() or target.read_bytes() != data:
            fail(f"published artifact differs: {path}")
    return {"status": "PASS", "species": 1621, "rom_sha256": sha(rom),
            "free_bytes": metadata["allocation"]["free"]}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("build", "check")); args = parser.parse_args()
    result = build() if args.command == "build" else check()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SurfaceError as error:
        print(f"T09 ERROR: {error}", file=sys.stderr); raise SystemExit(1)
