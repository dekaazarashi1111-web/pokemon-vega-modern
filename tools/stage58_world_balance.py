#!/usr/bin/env python3
"""Stage58向けKanto野生表と「薄い場所」追加イベント候補を決定的に設計する。

Stage17の実装は、logical locationに属する全encounter行をmethodやweightに関係なく
4種類すべてのstock wild tableへ循環配置していた。本モジュールは次の境界を正本化する。

* manifestのmethodをstock FireRed channelへ厳密に分類する。
* EVENT、weight=0、DexNav、時間帯、タマゴ、化石などの非native行を除外する。
* imported physical mapがFireRed原本で持っていたchannelだけを使用する。
* FireRed標準slot確率へmanifest weightを決定的に割り当てる。
* condition / unlock_keyはserializer非適用のmetadata要件として保持する。
* Stage57 exact ROM上のevent/collisionと衝突しない追加イベント候補だけを返す。
* 旧新wild tableのrate、level、diversity、species確率massを定量化する。

ROMへの書き込みは行わない。返却planはStage58 builderがserializeするためのread-only
入力であり、同じ入力から常に同じJSONを生成する。
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import struct
from collections import Counter, defaultdict, deque
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


GBA_ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x00054B0C
WILD_HEADERS_POINTER_SITE = 0x0008257C
WILD_HEADER_SIZE = 20
EVENT_HEADER_SIZE = 20
OBJECT_EVENT_SIZE = 24
MAP_CONNECTION_SIZE = 12
CONNECTION_DIRECTIONS = {1: "south", 2: "north", 3: "west", 4: "east"}
WILD_SLOT_COUNTS = {"land": 12, "water": 5, "rock": 5, "fishing": 10}
FIRERED_SLOT_PROBABILITIES = {
    "land": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1],
    "water": [60, 30, 5, 4, 1],
    "rock": [60, 30, 5, 4, 1],
    "fishing": [70, 30, 60, 20, 20, 40, 40, 15, 4, 1],
}
FIRERED_SLOT_GROUPS = {
    "land": [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]],
    "water": [[0, 1, 2, 3, 4]],
    "rock": [[0, 1, 2, 3, 4]],
    "fishing": [[0, 1], [2, 3, 4], [5, 6, 7, 8, 9]],
}

# Stock tableへ安全に落とせるmethodだけを列挙する。部分一致は使わない。
NATIVE_METHODS = {
    "草むらオーバーレイ": "land_outdoor",
    "草むらオーバーレイ＋追加進化道具": "land_outdoor",
    "洞窟・屋内オーバーレイ": "land_dungeon",
    "洞窟・屋内オーバーレイ＋追加進化道具": "land_dungeon",
    "水上オーバーレイ": "water",
    "いわくだき／DexNav": "rock",
    "釣りオーバーレイ": "fishing",
}
METHOD_TO_MODE = {
    "land_outdoor": "land",
    "land_dungeon": "land",
    "water": "water",
    "rock": "rock",
    "fishing": "fishing",
}
METHOD_TO_UPSTREAM_FIELD = {
    "land_outdoor": "land_mons",
    "land_dungeon": "land_mons",
    "water": "water_mons",
    "rock": "rock_smash_mons",
    "fishing": "fishing_mons",
}
EXPECTED_NATIVE_CONDITION = (
    "ベガ初回殿堂入り後。認定章数でエリアと中間進化枠を段階解禁。"
)
DEFAULT_RATES = {
    "land_outdoor": 7,
    "land_dungeon": 10,
    "water": 2,
    "rock": 25,
    "fishing": 20,
}
EXPECTED_STAGE58_MODE_TABLE_COUNTS = {
    "land": 52, "water": 11, "rock": 1, "fishing": 13,
}
WEIGHT_FIDELITY_LIMIT = Fraction(15, 1)
WEIGHT_FIDELITY_TOLERANCE = Fraction(1, 10_000)
FISHING_TIER_NAMES = ("OLD_ROD", "GOOD_ROD", "SUPER_ROD")
FISHING_WEIGHT_PATTERN = re.compile(r"(?:^| )\[ROD_WEIGHTS=(\d+)/(\d+)/(\d+)\]$")

# FireRed JSONはSafariの草地mapを屋内groupへ収容するが、実際のmap tileと
# wild land tableは屋外草地である。inventoryの構造分類を変更せず、遭遇channelの
# 適格性だけをこの小さな正本で補正する。
PHYSICAL_ENCOUNTER_CLASSIFICATION_OVERRIDES = {
    "SafariZone_Center": "OUTDOOR",
    "SafariZone_West": "OUTDOOR",
}
CRITICAL_EVENT_MAP_TOKENS = (
    "PokemonLeague",
    "HallOfFame",
    "Elevator",
    "TradeCenter",
    "UnionRoom",
    "RecordCorner",
    "Colosseum",
    "CableClub",
    "Unused",
)


class WorldBalanceError(RuntimeError):
    """入力または生成planが契約を満たさない。"""


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _int(value: object, what: str) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError) as error:
        raise WorldBalanceError(f"{what}が整数ではありません: {value!r}") from error


def _rom_offset(pointer: int, size: int, rom_size: int, what: str) -> int:
    offset = pointer - GBA_ROM_BASE
    if pointer < GBA_ROM_BASE or offset < 0 or offset + size > rom_size:
        raise WorldBalanceError(f"{what} pointerがROM外です: 0x{pointer:08X}")
    return offset


def _normalize_map_name(value: str) -> str:
    value = value.removeprefix("MAP_")
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _fire_red_encounters(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = root / "vendor/upstream/pokefirered/src/data/wild_encounters.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    groups = document.get("wild_encounter_groups", [])
    if len(groups) != 1:
        raise WorldBalanceError("pokefirered wild encounter group数が不正です")
    group = groups[0]
    fields = {str(row["type"]): list(row["encounter_rates"])
              for row in group.get("fields", [])}
    expected = {
        "land_mons": FIRERED_SLOT_PROBABILITIES["land"],
        "water_mons": FIRERED_SLOT_PROBABILITIES["water"],
        "rock_smash_mons": FIRERED_SLOT_PROBABILITIES["rock"],
        "fishing_mons": FIRERED_SLOT_PROBABILITIES["fishing"],
    }
    if fields != expected:
        raise WorldBalanceError("FireRed標準slot確率がupstreamからdriftしました")

    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in group.get("encounters", []):
        if "FireRed" not in str(row.get("base_label", "")):
            continue
        candidates[_normalize_map_name(str(row["map"]))].append(row)
    result: dict[str, dict[str, Any]] = {}
    for key, choices in candidates.items():
        # Altering Cave等の複数variantはspeciesだけが異なる。physical channel/rateが
        # 一意であることを確認したうえでlabel順の先頭をeligibility正本にする。
        signatures = {
            tuple((field, int(choice[field]["encounter_rate"]))
                  for field in expected if choice.get(field) is not None)
            for choice in choices
        }
        if len(signatures) != 1:
            raise WorldBalanceError(f"FireRed map {key} のchannel/rateがvariant間で不一致です")
        result[key] = min(choices, key=lambda row: str(row.get("base_label", "")))
    return result, {"path": str(path.relative_to(root)), "sha256": _sha(path.read_bytes())}


def classify_manifest_row(row: Mapping[str, object]) -> tuple[str | None, str]:
    """manifest 1行をnative methodへ分類し、除外理由も明示する。"""
    if str(row.get("status", "")) != "ACTIVE":
        return None, "inactive"
    if str(row.get("table_profile", "")) != "NORMAL":
        return None, "event_profile"
    weight = _int(row.get("weight", ""), "encounter weight")
    if weight <= 0:
        return None, "zero_weight"
    method = str(row.get("method", ""))
    native = NATIVE_METHODS.get(method)
    if native is None:
        lowered = method.lower()
        if "タマゴ" in method or "egg" in lowered:
            return None, "egg_method"
        if "復元" in method or "化石" in method or "fossil" in lowered:
            return None, "fossil_method"
        if method == "SIMPLE_EVENT" or "イベント" in method:
            return None, "event_method"
        return None, "non_native_method"
    if str(row.get("condition", "")) != EXPECTED_NATIVE_CONDITION:
        return None, "unsupported_condition"
    if not str(row.get("unlock_key", "")):
        return None, "missing_unlock"
    return native, "native"


def _map_inventory(root: Path) -> dict[tuple[int, int], dict[str, str]]:
    path = root / "reports/generated/kanto_map_inventory.csv"
    rows = _rows(path)
    result: dict[tuple[int, int], dict[str, str]] = {}
    for row in rows:
        coordinate = (_int(row["group_id"], "map group"), _int(row["map_id"], "map id"))
        if coordinate in result:
            raise WorldBalanceError(f"Kanto map inventory座標重複: {coordinate}")
        result[coordinate] = row
    return result


def _candidate_key(row: Mapping[str, object]) -> tuple[int, str]:
    return (_int(row.get("slot", ""), "encounter slot"),
            str(row.get("encounter_key", "")))


def _fishing_tier_weights(row: Mapping[str, object]) -> tuple[int, int, int]:
    """既存manifest schemaを保ったnotes末尾の竿別正本を厳密に読む。"""
    match = FISHING_WEIGHT_PATTERN.search(str(row.get("notes", "")))
    if match is None:
        raise WorldBalanceError(
            f"釣りrowにROD_WEIGHTS正本がありません: {row.get('encounter_key')}"
        )
    weights = tuple(int(value) for value in match.groups())
    if not any(weights):
        raise WorldBalanceError("釣りrowは少なくとも1竿でpositive weightが必要です")
    return weights


@lru_cache(maxsize=None)
def _solve_exact_partition(slot_probabilities: tuple[int, ...],
                           weights: tuple[int, ...]) \
        -> tuple[Fraction, Fraction, tuple[int, ...]] | None:
    """weight signature単位で再利用できるexact slot partition solver。"""
    total_weight = sum(weights)
    targets = tuple(Fraction(100 * value, total_weight) for value in weights)
    full_mask = (1 << len(slot_probabilities)) - 1

    @lru_cache(maxsize=None)
    def solve(candidate_index: int, remaining_mask: int) \
            -> tuple[Fraction, Fraction, tuple[int, ...]] | None:
        remaining_candidates = len(weights) - candidate_index
        if remaining_candidates == 0:
            return (Fraction(0), Fraction(0), ()) if remaining_mask == 0 else None
        if remaining_mask.bit_count() < remaining_candidates:
            return None
        best: tuple[Fraction, Fraction, tuple[int, ...]] | None = None
        remaining_indices = [index for index in range(len(slot_probabilities))
                             if remaining_mask & (1 << index)]
        max_take = len(remaining_indices) - (remaining_candidates - 1)
        for take in range(1, max_take + 1):
            for chosen_indices in combinations(remaining_indices, take):
                submask = sum(1 << index for index in chosen_indices)
                actual = sum(slot_probabilities[index]
                             for index in chosen_indices)
                tail = solve(candidate_index + 1, remaining_mask ^ submask)
                if tail is not None:
                    error = abs(Fraction(actual) - targets[candidate_index])
                    candidate = (max(error, tail[0]), error + tail[1],
                                 (submask,) + tail[2])
                    if best is None or candidate < best:
                        best = candidate
        return best

    return solve(0, full_mask)


def _allocate_group(candidates: Sequence[Mapping[str, object]],
                    probabilities: Sequence[int],
                    target_weights: Mapping[str, int]) \
        -> tuple[list[Mapping[str, object]], dict[str, Any]]:
    """全slotの分割をexact DPし、最大誤差→総誤差→manifest順を最小化する。"""
    if not candidates:
        raise WorldBalanceError("空candidateをslotへ割り当てようとしました")
    ordered = sorted(candidates, key=_candidate_key)
    if len(ordered) > len(probabilities):
        raise WorldBalanceError(
            f"positive candidateがstock slot容量を超えています: "
            f"{len(ordered)}>{len(probabilities)}"
        )
    weights = tuple(int(target_weights[str(row["encounter_key"])]) for row in ordered)
    if any(value <= 0 for value in weights):
        raise WorldBalanceError("eligible candidateのtarget weightは正数が必要です")
    total_weight = sum(weights)
    targets = tuple(Fraction(100 * value, total_weight) for value in weights)
    slot_probabilities = tuple(map(int, probabilities))
    optimum = _solve_exact_partition(slot_probabilities, weights)
    if optimum is None:
        raise WorldBalanceError("exact weight allocationを解けませんでした")
    max_error, total_error, masks = optimum
    if max_error > WEIGHT_FIDELITY_LIMIT + WEIGHT_FIDELITY_TOLERANCE:
        raise WorldBalanceError(
            "manifest weightをstock slotで再現できません: "
            f"max_error={float(max_error):.4f} > 15.0001"
        )
    output: list[Mapping[str, object] | None] = [None] * len(slot_probabilities)
    actual: Counter[str] = Counter()
    for candidate_index, mask in enumerate(masks):
        row = ordered[candidate_index]
        key = str(row["encounter_key"])
        for slot_index, probability in enumerate(slot_probabilities):
            if mask & (1 << slot_index):
                output[slot_index] = row
                actual[key] += probability
    if any(row is None for row in output):
        raise WorldBalanceError("exact weight allocationに未割当slotがあります")
    audit = {
        "allocator": "EXACT_SUBSET_DP_MINIMAX_THEN_L1",
        "optimality_status": "EXACT",
        "target_weight_by_source_key": {
            str(row["encounter_key"]): weights[index]
            for index, row in enumerate(ordered)
        },
        "serialized_probability_mass": {
            key: int(actual[key]) for key in sorted(actual)
        },
        "target_probability_mass": {
            str(row["encounter_key"]): round(float(targets[index]), 4)
            for index, row in enumerate(ordered)
        },
        "zero_probability_candidate_count": 0,
        "max_absolute_weight_error": round(float(max_error), 4),
        "optimal_max_absolute_weight_error": round(float(max_error), 4),
        "optimality_tolerance_points": float(WEIGHT_FIDELITY_TOLERANCE),
        "within_optimality_tolerance": True,
        "total_absolute_weight_error": round(float(total_error), 4),
        "quality_limit_points": float(WEIGHT_FIDELITY_LIMIT),
        "quality_tolerance_points": float(WEIGHT_FIDELITY_TOLERANCE),
    }
    return [row for row in output if row is not None], audit


def _allocate_slots(candidates: Sequence[Mapping[str, object]], mode: str,
                    species_by_key: Mapping[str, int]) -> dict[str, Any]:
    probabilities = FIRERED_SLOT_PROBABILITIES[mode]
    selected: list[Mapping[str, object] | None] = [None] * len(probabilities)
    group_contracts: list[dict[str, Any]] = []
    fishing_union: set[str] = set()
    for group_index, indices in enumerate(FIRERED_SLOT_GROUPS[mode]):
        if mode == "fishing":
            group_candidates = [row for row in candidates
                                if _fishing_tier_weights(row)[group_index] > 0]
            target_weights = {
                str(row["encounter_key"]): _fishing_tier_weights(row)[group_index]
                for row in group_candidates
            }
            fishing_union.update(target_weights)
        else:
            group_candidates = list(candidates)
            target_weights = {
                str(row["encounter_key"]): _int(row["weight"], "encounter weight")
                for row in group_candidates
            }
        group, allocation_audit = _allocate_group(
            group_candidates, [probabilities[index] for index in indices], target_weights,
        )
        for index, row in zip(indices, group):
            selected[index] = row
        group_contracts.append({
            "slot_group_index": group_index,
            "rod_tier": FISHING_TIER_NAMES[group_index] if mode == "fishing" else None,
            "slot_indices": list(indices),
            "eligible_source_keys": [str(row["encounter_key"])
                                     for row in group_candidates],
            **allocation_audit,
        })
    if mode == "fishing" and fishing_union != {
        str(row["encounter_key"]) for row in candidates
    }:
        raise WorldBalanceError("釣りcandidateに竿別positive weight未設定があります")
    if any(row is None for row in selected):
        raise WorldBalanceError(f"{mode} slot割当が未完了です")

    slots: list[list[int]] = []
    source_keys: list[str] = []
    source_slots: list[int] = []
    source_weights: list[int] = []
    species_keys: list[str] = []
    for raw in selected:
        assert raw is not None
        species_key = str(raw["species_key"])
        if species_key not in species_by_key:
            raise WorldBalanceError(f"Species ID未解決です: {species_key}")
        low = max(1, min(100, _int(raw["level_min"], "level_min")))
        high = max(low, min(100, _int(raw["level_max"], "level_max")))
        species = int(species_by_key[species_key])
        if not 1 <= species <= 1620:
            raise WorldBalanceError(f"Species IDがruntime範囲外です: {species_key}={species}")
        slots.append([low, high, species])
        source_keys.append(str(raw["encounter_key"]))
        source_slots.append(_int(raw["slot"], "encounter slot"))
        source_weights.append(_int(raw["weight"], "encounter weight"))
        species_keys.append(species_key)
    return {
        "slots": slots,
        "slot_probabilities": list(probabilities),
        "slot_probability_groups": [list(group) for group in FIRERED_SLOT_GROUPS[mode]],
        "source_keys": source_keys,
        "source_slots": source_slots,
        "source_weights": source_weights,
        "species_keys": species_keys,
        "candidate_count": len(candidates),
        "diversity": len(set(species_keys)),
        "group_allocation_contracts": group_contracts,
        "rod_tier_policy": (
            "MANIFEST_AUTHORED_OLD_GOOD_SUPER_ELIGIBILITY_AND_WEIGHT"
            if mode == "fishing" else None
        ),
    }


def _header_rows(stage17_metadata: Mapping[str, Any]) -> list[dict[str, Any]]:
    wild = stage17_metadata.get("wild", stage17_metadata)
    rows = wild.get("rows") if isinstance(wild, Mapping) else None
    if not isinstance(rows, list) or len(rows) != 133:
        raise WorldBalanceError("Stage17 Kanto wild metadataは133行必要です")
    coordinates = [(_int(row.get("group"), "wild group"),
                    _int(row.get("map"), "wild map")) for row in rows]
    if len(set(coordinates)) != 133:
        raise WorldBalanceError("Stage17 Kanto wild metadataの物理座標が重複しています")
    return [dict(row) for row in rows]


def _legacy_headers(rom: bytes) -> tuple[dict[tuple[int, int], dict[str, Any]], int]:
    pointer = struct.unpack_from("<I", rom, WILD_HEADERS_POINTER_SITE)[0]
    root = _rom_offset(pointer, WILD_HEADER_SIZE, len(rom), "gWildMonHeaders")
    result: dict[tuple[int, int], dict[str, Any]] = {}
    zero_coordinate_orphans = 0
    for index in range(1025):
        at = root + index * WILD_HEADER_SIZE
        if at + WILD_HEADER_SIZE > len(rom):
            raise WorldBalanceError("gWildMonHeaders terminatorがROM境界までにありません")
        group, number = rom[at], rom[at + 1]
        if (group, number) == (0xFF, 0xFF):
            return result, zero_coordinate_orphans
        coordinate = (group, number)
        duplicate_zero_orphan = coordinate == (0, 0) and coordinate in result
        if duplicate_zero_orphan:
            zero_coordinate_orphans += 1
        if coordinate in result and not duplicate_zero_orphan:
            raise WorldBalanceError(f"Stage57 wild header座標重複: {coordinate}")
        pointers = struct.unpack_from("<IIII", rom, at + 4)
        species: dict[str, list[int]] = {}
        tables: dict[str, dict[str, Any] | None] = {}
        for mode, info_pointer in zip(("land", "water", "rock", "fishing"), pointers):
            if not info_pointer:
                species[mode] = []
                tables[mode] = None
                continue
            info = _rom_offset(info_pointer, 8, len(rom), f"legacy {coordinate} {mode} info")
            slots_pointer = struct.unpack_from("<I", rom, info + 4)[0]
            slots = _rom_offset(slots_pointer, WILD_SLOT_COUNTS[mode] * 4, len(rom),
                                f"legacy {coordinate} {mode} slots")
            decoded_slots = [list(struct.unpack_from("<BBH", rom, slots + offset * 4))
                             for offset in range(WILD_SLOT_COUNTS[mode])]
            species[mode] = [slot[2] for slot in decoded_slots]
            tables[mode] = {
                "rate": int(rom[info]),
                "slots": decoded_slots,
                "slot_probabilities": list(FIRERED_SLOT_PROBABILITIES[mode]),
            }
        if not duplicate_zero_orphan:
            result[coordinate] = {
                "pointers": list(pointers), "species": species, "tables": tables,
            }
    raise WorldBalanceError("gWildMonHeaders scan上限を超えました")


def _map_header_offset(rom: bytes, group: int, number: int) -> int:
    groups_pointer = struct.unpack_from("<I", rom, MAP_GROUPS_POINTER_SITE)[0]
    groups = _rom_offset(groups_pointer, (group + 1) * 4, len(rom), "gMapGroups")
    group_pointer = struct.unpack_from("<I", rom, groups + group * 4)[0]
    group_table = _rom_offset(group_pointer, (number + 1) * 4, len(rom),
                              f"map group {group}")
    header_pointer = struct.unpack_from("<I", rom, group_table + number * 4)[0]
    return _rom_offset(header_pointer, 0x1C, len(rom), f"map header {group}/{number}")


def _map_dimensions(rom: bytes, group: int, number: int) -> tuple[int, int]:
    header = _map_header_offset(rom, group, number)
    layout_pointer = struct.unpack_from("<I", rom, header)[0]
    layout = _rom_offset(layout_pointer, 16, len(rom), f"layout {group}/{number}")
    width, height = struct.unpack_from("<II", rom, layout)
    if not width or not height or width * height > 1_000_000:
        raise WorldBalanceError(f"map寸法が不正です: {group}/{number} {width}x{height}")
    return width, height


def _map_geometry(rom: bytes, group: int, number: int) -> dict[str, Any]:
    header = _map_header_offset(rom, group, number)
    layout_pointer = struct.unpack_from("<I", rom, header)[0]
    layout = _rom_offset(layout_pointer, 16, len(rom), f"layout {group}/{number}")
    width, height = struct.unpack_from("<II", rom, layout)
    if not width or not height or width * height > 1_000_000:
        raise WorldBalanceError(f"map寸法が不正です: {group}/{number} {width}x{height}")
    block_pointer = struct.unpack_from("<I", rom, layout + 12)[0]
    block_offset = _rom_offset(block_pointer, width * height * 2, len(rom),
                               f"blockdata {group}/{number}")
    blocks = list(struct.unpack_from(f"<{width * height}H", rom, block_offset))
    events_pointer = struct.unpack_from("<I", rom, header + 4)[0]
    events = _rom_offset(events_pointer, EVENT_HEADER_SIZE, len(rom),
                         f"events {group}/{number}")
    object_count, warp_count, coord_count, bg_count = rom[events:events + 4]
    pointers = struct.unpack_from("<IIII", rom, events + 4)
    sizes = (object_count * OBJECT_EVENT_SIZE, warp_count * 8,
             coord_count * 16, bg_count * 12)
    arrays: list[bytes] = []
    for kind, pointer, size in zip(("object", "warp", "coord", "bg"), pointers, sizes):
        if not size:
            arrays.append(b"")
            continue
        offset = _rom_offset(pointer, size, len(rom), f"{kind} events {group}/{number}")
        arrays.append(rom[offset:offset + size])
    objects = [arrays[0][offset:offset + OBJECT_EVENT_SIZE]
               for offset in range(0, len(arrays[0]), OBJECT_EVENT_SIZE)]
    state = {
        "counts": {"objects": object_count, "warps": warp_count,
                   "coords": coord_count, "bg": bg_count},
        "objects": objects,
        "warps_hex": arrays[1].hex(), "coords_hex": arrays[2].hex(),
        "bg_hex": arrays[3].hex(),
    }
    reserved: set[tuple[int, int]] = set()
    for raw in state["objects"]:
        reserved.add(struct.unpack_from("<HH", raw, 4))
    event_coordinates: dict[str, list[tuple[int, int]]] = {}
    for kind, size, key in (("warp", 8, "warps_hex"),
                            ("coord", 16, "coords_hex"),
                            ("bg", 12, "bg_hex")):
        raw = bytes.fromhex(str(state[key]))
        coordinates = [struct.unpack_from("<HH", raw, offset)
                       for offset in range(0, len(raw), size)]
        event_coordinates[kind] = coordinates
        reserved.update(coordinates)

    def walkable(x: int, y: int) -> bool:
        if not (0 <= x < width and 0 <= y < height):
            return False
        value = blocks[y * width + x]
        return ((value >> 10) & 3) == 0 and ((value >> 12) & 0xF) in {0, 3}

    def neighbors(x: int, y: int) -> Iterable[tuple[int, int]]:
        yield x, y - 1
        yield x - 1, y
        yield x + 1, y
        yield x, y + 1

    warp_seeds: set[tuple[int, int]] = set()
    for x, y in event_coordinates["warp"]:
        if walkable(x, y):
            warp_seeds.add((x, y))
        warp_seeds.update((nx, ny) for nx, ny in neighbors(x, y) if walkable(nx, ny))

    # MapConnections ABI: s32 count + pointer, followed by 12-byte records
    # {u8 direction; pad; s32 offset; u8 mapGroup; u8 mapNum; pad}.
    # Stage57のconnection pointerがあるだけで全4辺をseed化せず、
    # FireRed IsPosInConnectingMapと同じ offset <= axis < offset + dest_size
    # の実際の接続辺だけを到達入口にする。
    connection_seeds: set[tuple[int, int]] = set()
    connections: list[dict[str, Any]] = []
    connection_pointer = struct.unpack_from("<I", rom, header + 12)[0]
    if connection_pointer:
        root = _rom_offset(connection_pointer, 8, len(rom),
                           f"map connections {group}/{number}")
        count, records_pointer = struct.unpack_from("<iI", rom, root)
        if count < 0 or count > 64:
            raise WorldBalanceError(
                f"map connection数が不正です: {group}/{number} count={count}"
            )
        records = (_rom_offset(records_pointer, count * MAP_CONNECTION_SIZE, len(rom),
                               f"map connection records {group}/{number}")
                   if count else 0)
        for index in range(count):
            direction, offset, dest_group, dest_map = struct.unpack_from(
                "<B3xiBB2x", rom, records + index * MAP_CONNECTION_SIZE
            )
            direction_name = CONNECTION_DIRECTIONS.get(direction)
            dest_width, dest_height = _map_dimensions(rom, dest_group, dest_map)
            span: list[int] | None = None
            record_seeds: set[tuple[int, int]] = set()
            if direction_name in {"north", "south"}:
                start, stop = max(0, offset), min(width, offset + dest_width)
                span = [start, stop - 1] if start < stop else None
                y = 0 if direction_name == "north" else height - 1
                record_seeds.update((x, y) for x in range(start, stop) if walkable(x, y))
            elif direction_name in {"west", "east"}:
                start, stop = max(0, offset), min(height, offset + dest_height)
                span = [start, stop - 1] if start < stop else None
                x = 0 if direction_name == "west" else width - 1
                record_seeds.update((x, y) for y in range(start, stop) if walkable(x, y))
            connection_seeds.update(record_seeds)
            connections.append({
                "record_index": index, "direction_id": direction,
                "direction": direction_name or "unsupported",
                "offset": offset, "destination_group": dest_group,
                "destination_map": dest_map, "destination_width": dest_width,
                "destination_height": dest_height, "source_axis_span": span,
                "walkable_seed_count": len(record_seeds),
            })
    seeds = warp_seeds | connection_seeds
    reached = set(seeds)
    pending = deque(sorted(seeds))
    while pending:
        x, y = pending.popleft()
        for point in neighbors(x, y):
            if point not in reached and walkable(*point):
                reached.add(point)
                pending.append(point)

    safe: list[tuple[int, int, int]] = []
    warps = event_coordinates["warp"]
    for x, y in reached:
        if ((x, y) in reserved or x < 2 or y < 2
                or x >= width - 2 or y >= height - 2):
            continue
        adjacent = sum(point in reached and point not in reserved for point in neighbors(x, y))
        if adjacent < 2:
            continue
        warp_distance = min((abs(x - wx) + abs(y - wy) for wx, wy in warps), default=8)
        if warp_distance < 2:
            continue
        safe.append((warp_distance, y, x))
    safe.sort()
    return {
        "width": width,
        "height": height,
        "area": width * height,
        "state": state,
        "reserved": reserved,
        "connections": connections,
        "warp_seed_count": len(warp_seeds),
        "connection_seed_count": len(connection_seeds),
        "reachability_seed_count": len(seeds),
        "reachable_count": len(reached),
        "safe_tiles": safe,
        "collision_at": lambda x, y: (blocks[y * width + x] >> 10) & 3,
    }


def _logical_unlocks(encounter_rows: Sequence[Mapping[str, object]]) -> dict[str, str]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in encounter_rows:
        if str(row.get("status", "")) == "ACTIVE":
            grouped[str(row.get("logical_location_key", ""))][str(row.get("unlock_key", ""))] += 1
    return {logical: sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            for logical, counts in grouped.items() if counts}


def _reward_tier(unlock: str) -> str:
    if unlock == "KANTO_EARLY_ACCESS":
        return "EARLY_CONSUMABLE"
    if unlock in {"KANTO_CERT_1", "KANTO_CERT_2"}:
        return "MID_EXPLORATION"
    if unlock in {"KANTO_CERT_3", "KANTO_CERT_4"}:
        return "LATE_EXPLORATION"
    return "POSTGAME_RARE"


def _table_balance_metrics(mode: str, table: Mapping[str, Any] | None) \
        -> dict[str, Any] | None:
    """1 wild tableをFireRed slot group単位の確率massへ正規化する。"""
    if table is None:
        return None
    slots = [list(slot) for slot in table.get("slots", [])]
    probabilities = [int(value) for value in table.get(
        "slot_probabilities", FIRERED_SLOT_PROBABILITIES[mode]
    )]
    if len(slots) != WILD_SLOT_COUNTS[mode] \
            or probabilities != FIRERED_SLOT_PROBABILITIES[mode]:
        raise WorldBalanceError(f"{mode} balance metricsのslot ABIが不正です")
    groups: list[dict[str, Any]] = []
    all_species: set[int] = set()
    for group_index, indices in enumerate(FIRERED_SLOT_GROUPS[mode]):
        mass: Counter[int] = Counter()
        expected_level = 0.0
        for index in indices:
            low, high, species = map(int, slots[index])
            probability = probabilities[index]
            mass[species] += probability
            all_species.add(species)
            expected_level += probability * (low + high) / 2.0
        groups.append({
            "slot_group_index": group_index,
            "slot_indices": list(indices),
            "probability_total": sum(probabilities[index] for index in indices),
            "level_min": min(int(slots[index][0]) for index in indices),
            "level_max": max(int(slots[index][1]) for index in indices),
            "expected_level": round(expected_level / 100.0, 4),
            "diversity": len(mass),
            "species_probability_mass": {
                str(species): mass[species] for species in sorted(mass)
            },
        })
    return {
        "rate": int(table["rate"]),
        "slot_count": len(slots),
        "level_min": min(int(slot[0]) for slot in slots),
        "level_max": max(int(slot[1]) for slot in slots),
        "diversity": len(all_species),
        "species_ids": sorted(all_species),
        "slot_groups": groups,
    }


def _mass_delta(mode: str, before: Mapping[str, Any] | None,
                after: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    before_groups = list(before.get("slot_groups", [])) if before else []
    after_groups = list(after.get("slot_groups", [])) if after else []
    for group_index in range(len(FIRERED_SLOT_GROUPS[mode])):
        left = before_groups[group_index].get("species_probability_mass", {}) \
            if before_groups else {}
        right = after_groups[group_index].get("species_probability_mass", {}) \
            if after_groups else {}
        species = sorted({int(value) for value in left} | {int(value) for value in right})
        result.append({
            "slot_group_index": group_index,
            "species_probability_mass": {
                str(value): int(right.get(str(value), 0)) - int(left.get(str(value), 0))
                for value in species
            },
        })
    return result


def _table_balance_delta(mode: str, before: Mapping[str, Any] | None,
                         after: Mapping[str, Any] | None) -> dict[str, Any]:
    def value(row: Mapping[str, Any] | None, key: str) -> int:
        return int(row[key]) if row else 0

    return {
        "enabled_table_count": int(after is not None) - int(before is not None),
        "rate": value(after, "rate") - value(before, "rate"),
        "slot_count": value(after, "slot_count") - value(before, "slot_count"),
        "level_min": (int(after["level_min"]) - int(before["level_min"])
                      if before and after else None),
        "level_max": (int(after["level_max"]) - int(before["level_max"])
                      if before and after else None),
        "diversity": value(after, "diversity") - value(before, "diversity"),
        "species_probability_mass_by_slot_group": _mass_delta(mode, before, after),
    }


def _aggregate_balance_metrics(mode: str,
                               rows: Sequence[Mapping[str, Any] | None]) -> dict[str, Any]:
    present = [row for row in rows if row is not None]
    masses = [Counter() for _ in FIRERED_SLOT_GROUPS[mode]]
    species: set[int] = set()
    for row in present:
        assert row is not None
        species.update(int(value) for value in row["species_ids"])
        for group_index, group in enumerate(row["slot_groups"]):
            masses[group_index].update({
                int(key): int(value)
                for key, value in group["species_probability_mass"].items()
            })
    rate_sum = sum(int(row["rate"]) for row in present)
    return {
        "physical_header_count": len(rows),
        "enabled_table_count": len(present),
        "rate_sum": rate_sum,
        "rate_min": min((int(row["rate"]) for row in present), default=None),
        "rate_max": max((int(row["rate"]) for row in present), default=None),
        "rate_mean": round(rate_sum / len(present), 4) if present else None,
        "slot_count": sum(int(row["slot_count"]) for row in present),
        "level_min": min((int(row["level_min"]) for row in present), default=None),
        "level_max": max((int(row["level_max"]) for row in present), default=None),
        "diversity": len(species),
        "species_ids": sorted(species),
        "species_probability_mass_by_slot_group": [
            {
                "slot_group_index": index,
                "probability_total": sum(mass.values()),
                "species_probability_mass": {
                    str(species_id): mass[species_id] for species_id in sorted(mass)
                },
            }
            for index, mass in enumerate(masses)
        ],
    }


def _aggregate_balance_delta(mode: str, before: Mapping[str, Any],
                             after: Mapping[str, Any]) -> dict[str, Any]:
    def optional_delta(key: str) -> int | float | None:
        if before[key] is None or after[key] is None:
            return None
        return round(float(after[key]) - float(before[key]), 4)

    before_groups = before["species_probability_mass_by_slot_group"]
    after_groups = after["species_probability_mass_by_slot_group"]
    mass_groups: list[dict[str, Any]] = []
    for index in range(len(FIRERED_SLOT_GROUPS[mode])):
        left = before_groups[index]["species_probability_mass"]
        right = after_groups[index]["species_probability_mass"]
        species = sorted({int(value) for value in left} | {int(value) for value in right})
        mass_groups.append({
            "slot_group_index": index,
            "probability_total": (int(after_groups[index]["probability_total"])
                                  - int(before_groups[index]["probability_total"])),
            "species_probability_mass": {
                str(value): int(right.get(str(value), 0)) - int(left.get(str(value), 0))
                for value in species
            },
        })
    return {
        "physical_header_count": int(after["physical_header_count"])
        - int(before["physical_header_count"]),
        "enabled_table_count": int(after["enabled_table_count"])
        - int(before["enabled_table_count"]),
        "rate_sum": int(after["rate_sum"]) - int(before["rate_sum"]),
        "rate_min": optional_delta("rate_min"),
        "rate_max": optional_delta("rate_max"),
        "rate_mean": optional_delta("rate_mean"),
        "slot_count": int(after["slot_count"]) - int(before["slot_count"]),
        "level_min": optional_delta("level_min"),
        "level_max": optional_delta("level_max"),
        "diversity": int(after["diversity"]) - int(before["diversity"]),
        "species_probability_mass_by_slot_group": mass_groups,
    }


def _balance_metrics(headers: Sequence[Mapping[str, Any]],
                     legacy: Mapping[tuple[int, int], Mapping[str, Any]]) -> dict[str, Any]:
    physical: list[dict[str, Any]] = []
    for header in headers:
        coordinate = (int(header["group"]), int(header["map"]))
        modes: dict[str, Any] = {}
        for mode in WILD_SLOT_COUNTS:
            before = _table_balance_metrics(mode, legacy[coordinate]["tables"][mode])
            after = _table_balance_metrics(mode, header["modes"][mode])
            modes[mode] = {
                "before": before, "after": after,
                "delta": _table_balance_delta(mode, before, after),
            }
        physical.append({
            "group": coordinate[0], "map": coordinate[1],
            "logical_code": header["logical_code"],
            "classification": header["classification"], "modes": modes,
        })

    logical: list[dict[str, Any]] = []
    for logical_code in sorted({str(row["logical_code"]) for row in physical}):
        members = [row for row in physical if row["logical_code"] == logical_code]
        modes: dict[str, Any] = {}
        for mode in WILD_SLOT_COUNTS:
            before = _aggregate_balance_metrics(
                mode, [row["modes"][mode]["before"] for row in members]
            )
            after = _aggregate_balance_metrics(
                mode, [row["modes"][mode]["after"] for row in members]
            )
            modes[mode] = {
                "before": before, "after": after,
                "delta": _aggregate_balance_delta(mode, before, after),
            }
        logical.append({
            "logical_code": logical_code, "physical_header_count": len(members),
            "modes": modes,
        })

    aggregate_modes: dict[str, Any] = {}
    for mode in WILD_SLOT_COUNTS:
        before = _aggregate_balance_metrics(
            mode, [row["modes"][mode]["before"] for row in physical]
        )
        after = _aggregate_balance_metrics(
            mode, [row["modes"][mode]["after"] for row in physical]
        )
        aggregate_modes[mode] = {
            "before": before, "after": after,
            "delta": _aggregate_balance_delta(mode, before, after),
        }
    return {
        "schema_version": 1,
        "probability_unit": "percent_mass_per_fire_red_slot_group",
        "physical": physical, "logical": logical,
        "aggregate": {"modes": aggregate_modes},
    }


def _progression_owner_contract(root: Path, headers: Sequence[Mapping[str, Any]]) \
        -> tuple[dict[str, str], dict[str, Any]]:
    """T15のmap access ownerを正本sourceから読み、metadataと分離して監査する。"""
    source_path = root / "tools/content/progression.py"
    scope_path = root / "content/kanto_map_scope.csv"
    nodes_path = root / "content/kanto_progression.csv"
    serializer_path = root / "scripts/build_stage58_qol_world_convenience_debug.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    functions = [node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == "_area_gate"]
    if len(functions) != 1 or isinstance(functions[0], ast.AsyncFunctionDef):
        raise WorldBalanceError("Kanto map access owner _area_gateを一意に解決できません")
    isolated = ast.Module(body=[functions[0]], type_ignores=[])
    ast.fix_missing_locations(isolated)
    namespace: dict[str, Any] = {"ContentError": WorldBalanceError}
    exec(compile(isolated, str(source_path), "exec"), namespace)  # trusted tracked source
    area_gate = namespace["_area_gate"]

    scope_rows = _rows(scope_path)
    scope_by_map = {row["map_key"]: row for row in scope_rows
                    if row["scope_decision"] != "DEFER"}
    if len(scope_by_map) != len([row for row in scope_rows
                                if row["scope_decision"] != "DEFER"]):
        raise WorldBalanceError("Kanto map access ownerのmap_keyが重複しています")
    node_rows = _rows(nodes_path)
    node_sequences = {
        row["unlock_key"]: _int(row["sequence"], "progression sequence")
        for row in node_rows
    }
    node_keys = set(node_sequences)
    owner_by_logical: dict[str, str] = {}
    physical_rows: list[dict[str, Any]] = []
    for header in headers:
        map_key = str(header["map_key"])
        logical = str(header["logical_code"])
        scope = scope_by_map.get(map_key)
        if scope is None or scope["logical_code"] != logical:
            raise WorldBalanceError(f"Kanto map access ownerにphysical mapがありません: {map_key}")
        owner = str(area_gate(logical))
        if owner not in node_keys:
            raise WorldBalanceError(f"Kanto map access ownerが未知nodeを参照します: {owner}")
        previous = owner_by_logical.setdefault(logical, owner)
        if previous != owner:
            raise WorldBalanceError(f"{logical}のmap access ownerが一意ではありません")
        requirements = sorted({
            str(table["progression_requirement"]["unlock_key"])
            for table in header["modes"].values() if table is not None
        })
        physical_rows.append({
            "group": int(header["group"]), "map": int(header["map"]),
            "map_key": map_key, "logical_code": logical,
            "runtime_map_access_owner_unlock_key": owner,
            "metadata_requirement_unlock_keys": requirements,
            "metadata_owner_aligned": not requirements or requirements == [owner],
            "runtime_map_access_owner_sequence": node_sequences[owner],
            "metadata_requirement_sequences": [node_sequences[key]
                                                   for key in requirements],
            "premature_exposure": bool(requirements) and any(
                node_sequences[key] > node_sequences[owner] for key in requirements
            ),
        })
    mismatches = [row for row in physical_rows
                  if row["metadata_requirement_unlock_keys"]
                  and not row["metadata_owner_aligned"]]
    mismatch_logicals = sorted({str(row["logical_code"]) for row in mismatches})
    premature = [row for row in physical_rows if row["premature_exposure"]]

    serializer_source = serializer_path.read_text(encoding="utf-8")
    serializer_tree = ast.parse(serializer_source, filename=str(serializer_path))
    serializers = [node for node in serializer_tree.body
                   if isinstance(node, ast.FunctionDef)
                   and node.name == "_emit_wild_payload"]
    if len(serializers) != 1:
        raise WorldBalanceError("Stage58 wild serializerを一意に解決できません")
    serializer_literals = {
        str(node.value) for node in ast.walk(serializers[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if not {"modes", "slots", "rate"} <= serializer_literals \
            or {"gate", "progression_requirement"} & serializer_literals:
        raise WorldBalanceError("Stage58 wild serializerのprogression metadata非適用契約がdriftしました")
    return owner_by_logical, {
        "policy": "progression_requirement_metadata_only",
        "runtime_gate_claimed_by_world_plan": False,
        "serializer_applies_progression_requirement": False,
        "serializer_non_application_status": "PASS",
        "runtime_map_access_owner_coverage_status": "PASS",
        "runtime_map_access_owner_physical_count": len(physical_rows),
        "metadata_runtime_owner_alignment_status": (
            "PASS" if not mismatches else "SAFE_LATE_ACCESS"
            if not premature else "FAIL_PREMATURE_EXPOSURE"
        ),
        "metadata_runtime_owner_mismatch_count": len(mismatches),
        "metadata_runtime_owner_mismatch_logical_count": len(mismatch_logicals),
        "metadata_runtime_owner_mismatch_logical_codes": mismatch_logicals,
        "metadata_runtime_owner_mismatches": mismatches,
        "premature_exposure_count": len(premature),
        "premature_exposure_physical_rows": premature,
        "serializer_source": {
            "path": str(serializer_path.relative_to(root)),
            "function": "_emit_wild_payload",
            "consumed_table_fields": ["rate", "slots"],
            "ignored_metadata_fields": ["progression_requirement"],
            "sha256": _sha(serializer_source.encode()),
        },
        "owner_sources": [
            {"path": str(source_path.relative_to(root)), "sha256": _sha(source.encode())},
            {"path": str(scope_path.relative_to(root)), "sha256": _sha(scope_path.read_bytes())},
            {"path": str(nodes_path.relative_to(root)), "sha256": _sha(nodes_path.read_bytes())},
        ],
    }


def _thin_places(rom: bytes, headers: Sequence[Mapping[str, Any]],
                 inventory: Mapping[tuple[int, int], Mapping[str, str]],
                 root: Path, encounter_rows: Sequence[Mapping[str, object]],
                 runtime_owner_unlocks: Mapping[str, str]) \
        -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item_counts: Counter[str] = Counter()
    item_path = root / "manifests/kanto_items.csv"
    if item_path.exists():
        for row in _rows(item_path):
            if row.get("status") == "ACTIVE":
                item_counts[row["map_key"]] += 1
    unlocks = _logical_unlocks(encounter_rows)
    scored: list[dict[str, Any]] = []
    geometries: dict[tuple[int, int], dict[str, Any]] = {}
    for header in headers:
        coordinate = (int(header["group"]), int(header["map"]))
        row = inventory[coordinate]
        geometry = _map_geometry(rom, *coordinate)
        geometries[coordinate] = geometry
        counts = geometry["state"]["counts"]
        active_modes = sum(value is not None for value in header["modes"].values())
        item_count = item_counts[str(row["map_key"])]
        interactions = int(counts["objects"]) + int(counts["coords"]) + int(counts["bg"]) \
            + item_count + active_modes
        density = interactions * 1000.0 / max(1, geometry["area"])
        score = (
            (24 if int(counts["objects"]) == 0 else 0)
            + (12 if int(counts["bg"]) == 0 else 0)
            + (6 if int(counts["coords"]) == 0 else 0)
            + (12 if item_count == 0 else 0)
            + (18 if active_modes == 0 else 0)
            + max(0, 20 - min(20, int(density)))
            + min(8, geometry["area"] // 400)
        )
        scored.append({
            "group": coordinate[0], "map": coordinate[1],
            "map_key": row["map_key"], "source_map": row["source_map"],
            "logical_code": row["logical_code"], "classification": row["classification"],
            "runtime_map_access_owner_unlock_key":
                runtime_owner_unlocks[str(row["logical_code"])],
            "width": geometry["width"], "height": geometry["height"],
            "area": geometry["area"], "object_count": int(counts["objects"]),
            "warp_count": int(counts["warps"]), "coord_count": int(counts["coords"]),
            "bg_count": int(counts["bg"]), "item_count": item_count,
            "native_mode_count": active_modes, "interaction_count": interactions,
            "interactions_per_1000_tiles": round(density, 4),
            "connection_count": len(geometry["connections"]),
            "connections": geometry["connections"],
            "warp_seed_count": geometry["warp_seed_count"],
            "connection_seed_count": geometry["connection_seed_count"],
            "reachability_seed_count": geometry["reachability_seed_count"],
            "reachable_tile_count": geometry["reachable_count"],
            "safe_tile_count": len(geometry["safe_tiles"]), "thin_score": score,
        })
    scored.sort(key=lambda row: (-int(row["thin_score"]), int(row["group"]), int(row["map"])))

    # 既にStage58の実装対象になった6イベントはwild table追加でthin scoreが
    # 相対変化しても候補から黙って消してはならない。config座標を読み、geometry
    # 安全性を毎回再検証したうえで候補集合へ必須投入する。
    config_path = root / "config/stage58_qol_world_convenience_debug.json"
    configured: dict[tuple[int, int], tuple[int, int]] = {}
    if config_path.exists():
        config_document = json.loads(config_path.read_text(encoding="utf-8"))
        for row in config_document.get("thin_events", []):
            coordinate = (_int(row.get("group"), "thin event group"),
                          _int(row.get("map"), "thin event map"))
            if coordinate in configured:
                raise WorldBalanceError(f"thin event config物理座標重複: {coordinate}")
            configured[coordinate] = (_int(row.get("x"), "thin event x"),
                                      _int(row.get("y"), "thin event y"))
    scored_by_coordinate = {
        (int(row["group"]), int(row["map"])): row for row in scored
    }
    missing_configured = sorted(set(configured) - set(scored_by_coordinate))
    if missing_configured:
        raise WorldBalanceError(f"thin event config map欠落: {missing_configured}")
    selection_order = [scored_by_coordinate[coordinate]
                       for coordinate in configured]
    selection_order.extend(row for row in scored if (
        int(row["group"]), int(row["map"])
    ) not in configured)

    selected: list[dict[str, Any]] = []
    used_logical: set[str] = set()
    for thin in selection_order:
        if len(selected) >= 8:
            break
        coordinate = (int(thin["group"]), int(thin["map"]))
        geometry = geometries[coordinate]
        source_map = str(thin["source_map"])
        logical = str(thin["logical_code"])
        if (logical in used_logical or geometry["area"] < 100
                or int(thin["object_count"]) >= 14 or not geometry["safe_tiles"]
                or any(token in source_map for token in CRITICAL_EVENT_MAP_TOKENS)):
            continue
        if coordinate in configured:
            x, y = configured[coordinate]
            if not any(tile_y == y and tile_x == x
                       for _, tile_y, tile_x in geometry["safe_tiles"]):
                raise WorldBalanceError(
                    f"thin event config座標が安全候補ではありません: {coordinate}/{x},{y}"
                )
        else:
            _, y, x = geometry["safe_tiles"][0]
        conflicts: list[str] = []
        if (x, y) in geometry["reserved"]:
            conflicts.append("existing_event")
        collision = int(geometry["collision_at"](x, y))
        if collision:
            conflicts.append("collision")
        if conflicts:
            continue
        metadata_unlock = unlocks.get(logical, "KANTO_EARLY_ACCESS")
        runtime_owner_unlock = runtime_owner_unlocks[logical]
        selected.append({
            "group": coordinate[0], "map": coordinate[1], "x": x, "y": y,
            "elevation": 3, "map_key": thin["map_key"], "source_map": source_map,
            "logical_code": logical, "event_kind": "ONE_TIME_EXPLORATION_REWARD_NPC",
            "unlock_key": runtime_owner_unlock,
            "reward_tier": _reward_tier(runtime_owner_unlock),
            "metadata_unlock_key": metadata_unlock,
            "runtime_map_access_owner_unlock_key": runtime_owner_unlock,
            "reward_tier_owner_policy": "runtime_map_access_owner",
            "progression_requirement_policy": "progression_requirement_metadata_only",
            "collision": collision, "event_conflicts": conflicts,
            "thin_score": thin["thin_score"],
            "connection_count": len(geometry["connections"]),
            "warp_seed_count": geometry["warp_seed_count"],
            "connection_seed_count": geometry["connection_seed_count"],
            "reachability_seed_count": geometry["reachability_seed_count"],
            "reason": (
                f"{source_map}は{geometry['area']} tilesに対しinteraction "
                f"{thin['interaction_count']}件（1000 tiles当たり"
                f"{thin['interactions_per_1000_tiles']}件）で、到達可能な空き座標を持つため"
            ),
        })
        used_logical.add(logical)
    selected_coordinates = {(int(row["group"]), int(row["map"])) for row in selected}
    if not set(configured) <= selected_coordinates:
        raise WorldBalanceError("thin event config必須候補が選定集合から脱落しました")
    if len(selected) < 4:
        raise WorldBalanceError(f"安全な薄い場所候補が不足しています: {len(selected)}")
    return scored, selected


def build_world_balance_plan(
    root: Path,
    rom: bytes,
    stage17_metadata: Mapping[str, Any],
    encounter_rows: Sequence[Mapping[str, object]],
    species_by_key: Mapping[str, int],
    rates: Mapping[str, int],
) -> dict[str, Any]:
    """Stage58 builderが利用する決定的なworld balance planを返す。"""
    root = root.resolve()
    required_rates = set(DEFAULT_RATES)
    if set(rates) != required_rates:
        raise WorldBalanceError(
            f"wild rates key不一致: {sorted(rates)} != {sorted(required_rates)}"
        )
    normalized_rates = {key: _int(rates[key], f"wild rate {key}") for key in required_rates}
    if any(not 1 <= value <= 255 for value in normalized_rates.values()):
        raise WorldBalanceError("wild rateは1..255である必要があります")
    inventory = _map_inventory(root)
    upstream, upstream_meta = _fire_red_encounters(root)
    stage17_rows = _header_rows(stage17_metadata)

    native_by_logical: dict[str, dict[str, list[Mapping[str, object]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    native_manifest_source_keys: set[str] = set()
    exclusion_by_logical: dict[str, Counter[str]] = defaultdict(Counter)
    excluded: Counter[str] = Counter()
    manifest_slots: set[int] = set()
    logical_locations: set[str] = set()
    for row in encounter_rows:
        logical = str(row.get("logical_location_key", ""))
        logical_locations.add(logical)
        slot = _int(row.get("slot", ""), "encounter slot")
        if slot in manifest_slots:
            raise WorldBalanceError(f"manifest slotが重複しています: {slot}")
        manifest_slots.add(slot)
        native, reason = classify_manifest_row(row)
        if native is None:
            excluded[reason] += 1
            exclusion_by_logical[logical][reason] += 1
            continue
        native_manifest_source_keys.add(str(row["encounter_key"]))
        native_by_logical[logical][native].append(row)

    headers: list[dict[str, Any]] = []
    physical_channel_rejections: Counter[str] = Counter()
    physically_eligible_source_keys: set[str] = set()
    expected_physical_tuples: set[tuple[int, int, str, str]] = set()
    serialized_physical_tuples: set[tuple[int, int, str, str]] = set()
    for metadata_row in sorted(stage17_rows,
                               key=lambda row: (_int(row["group"], "group"),
                                                _int(row["map"], "map"))):
        coordinate = (_int(metadata_row["group"], "group"),
                      _int(metadata_row["map"], "map"))
        if coordinate not in inventory:
            raise WorldBalanceError(f"Kanto inventoryにphysical mapがありません: {coordinate}")
        map_row = inventory[coordinate]
        logical = str(map_row["logical_code"])
        if logical != str(metadata_row["logical_code"]):
            raise WorldBalanceError(f"logical/physical crosswalk不一致: {coordinate}")
        classification = str(map_row["classification"])
        encounter_classification = PHYSICAL_ENCOUNTER_CLASSIFICATION_OVERRIDES.get(
            str(map_row["source_map"]), classification
        )
        source = upstream.get(_normalize_map_name(str(map_row["source_map"])))
        modes: dict[str, dict[str, Any] | None] = {
            "land": None, "water": None, "rock": None, "fishing": None,
        }
        for native_method, candidates in sorted(native_by_logical.get(logical, {}).items()):
            mode = METHOD_TO_MODE[native_method]
            expected_class = ("OUTDOOR" if native_method == "land_outdoor"
                              else "DUNGEON" if native_method == "land_dungeon" else None)
            if expected_class and encounter_classification != expected_class:
                physical_channel_rejections["classification_mismatch"] += len(candidates)
                continue
            upstream_field = METHOD_TO_UPSTREAM_FIELD[native_method]
            if source is None or source.get(upstream_field) is None:
                physical_channel_rejections["upstream_channel_absent"] += len(candidates)
                continue
            physically_eligible_source_keys.update(
                str(row["encounter_key"]) for row in candidates
            )
            expected_physical_tuples.update(
                (coordinate[0], coordinate[1], mode, str(row["encounter_key"]))
                for row in candidates
            )
            if modes[mode] is not None:
                raise WorldBalanceError(f"{coordinate} {mode}へ複数methodが競合しました")
            unlocks = {str(row["unlock_key"]) for row in candidates}
            conditions = {str(row["condition"]) for row in candidates}
            if len(unlocks) != 1 or conditions != {EXPECTED_NATIVE_CONDITION}:
                raise WorldBalanceError(
                    f"{logical}/{native_method} progression metadataが一意ではありません"
                )
            allocation = _allocate_slots(candidates, mode, species_by_key)
            candidate_records = []
            for row in sorted(candidates, key=_candidate_key):
                species_key = str(row["species_key"])
                candidate_records.append({
                    "encounter_key": str(row["encounter_key"]),
                    "manifest_slot": _int(row["slot"], "encounter slot"),
                    "species_key": species_key,
                    "species_id": int(species_by_key[species_key]),
                    "level_min": max(1, min(100, _int(row["level_min"], "level_min"))),
                    "level_max": max(1, min(100, _int(row["level_max"], "level_max"))),
                    "weight": _int(row["weight"], "encounter weight"),
                    "fishing_tier_weights": {
                        tier: _fishing_tier_weights(row)[index]
                        for index, tier in enumerate(FISHING_TIER_NAMES)
                    } if mode == "fishing" else None,
                })
            modes[mode] = {
                "rate": normalized_rates[native_method],
                **allocation,
                "progression_requirement": {
                    "condition": next(iter(conditions)),
                    "unlock_key": next(iter(unlocks)),
                    "policy": "progression_requirement_metadata_only",
                    "serializer_applied": False,
                },
                "native_method": native_method,
                "candidate_records": candidate_records,
                "upstream_source_map": str(map_row["source_map"]),
                "upstream_channel": upstream_field,
                "upstream_original_rate": int(source[upstream_field]["encounter_rate"]),
            }
        if any(value is not None for value in modes.values()):
            disabled_reason = None
        elif logical not in native_by_logical:
            reasons = exclusion_by_logical.get(logical, Counter())
            disabled_reason = "NO_POSITIVE_WEIGHT_STOCK_METHOD:" + ",".join(
                f"{key}={value}" for key, value in sorted(reasons.items())
            )
        else:
            disabled_reason = "NO_MATCHING_FIRERED_PHYSICAL_CHANNEL"
        headers.append({
            "group": coordinate[0], "map": coordinate[1],
            "map_key": map_row["map_key"], "source_map": map_row["source_map"],
            "logical_code": logical, "classification": classification,
            "encounter_classification": encounter_classification,
            "classification_override": (
                encounter_classification if encounter_classification != classification else None
            ),
            "enabled": any(value is not None for value in modes.values()),
            "disabled_reason": disabled_reason,
            "modes": modes,
        })

    runtime_owner_unlocks, progression_contract = _progression_owner_contract(root, headers)
    thin_scores, thin_candidates = _thin_places(
        rom, headers, inventory, root, encounter_rows, runtime_owner_unlocks
    )
    legacy, legacy_zero_orphans = _legacy_headers(rom)
    header_by_coordinate = {(int(row["group"]), int(row["map"])): row for row in headers}
    missing_legacy = sorted(set(header_by_coordinate) - set(legacy))
    if missing_legacy:
        raise WorldBalanceError(f"Stage57 ROMからKanto wild headerが欠落: {missing_legacy[:3]}")
    balance_metrics = _balance_metrics(headers, legacy)
    legacy_all_four = 0
    legacy_non_native_modes = 0
    legacy_two_species_all_mode = 0
    for coordinate, header in header_by_coordinate.items():
        before = legacy[coordinate]
        present = [mode for mode, pointer in zip(
            ("land", "water", "rock", "fishing"), before["pointers"]
        ) if pointer]
        if len(present) == 4:
            legacy_all_four += 1
            distinct = set().union(*(before["species"][mode] for mode in present))
            if len(distinct) <= 2:
                legacy_two_species_all_mode += 1
        legacy_non_native_modes += sum(
            header["modes"][mode] is None for mode in present
        )

    mode_counts = Counter()
    native_slot_count = 0
    included_source_keys: list[str] = []
    for header in headers:
        for mode, table in header["modes"].items():
            if table is None:
                continue
            mode_counts[mode] += 1
            native_slot_count += len(table["slots"])
            included_source_keys.extend(table["source_keys"])
    included_unique = set(included_source_keys)
    for header in headers:
        coordinate = (int(header["group"]), int(header["map"]))
        for mode, table in header["modes"].items():
            if table is not None:
                serialized_physical_tuples.update(
                    (coordinate[0], coordinate[1], mode, key)
                    for key in set(map(str, table["source_keys"]))
                )
    positive_channel_drops = sorted(native_manifest_source_keys - included_unique)
    physical_tuple_drops = sorted(expected_physical_tuples - serialized_physical_tuples)
    unexpected_physical_tuples = sorted(serialized_physical_tuples - expected_physical_tuples)
    event_inclusions = [key for key in included_unique if any(
        str(row.get("encounter_key")) == key and str(row.get("table_profile")) == "EVENT"
        for row in encounter_rows
    )]
    zero_weight_inclusions = [key for key in included_unique if any(
        str(row.get("encounter_key")) == key and _int(row.get("weight", 0), "weight") <= 0
        for row in encounter_rows
    )]
    forbidden_method_inclusions = [key for key in included_unique if any(
        str(row.get("encounter_key")) == key and str(row.get("method")) not in NATIVE_METHODS
        for row in encounter_rows
    )]
    egg_inclusions = [key for key in included_unique if any(
        str(row.get("encounter_key")) == key and "タマゴ" in str(row.get("method", ""))
        for row in encounter_rows
    )]
    fossil_inclusions = [key for key in included_unique if any(
        str(row.get("encounter_key")) == key
        and ("復元" in str(row.get("method", "")) or "化石" in str(row.get("method", "")))
        for row in encounter_rows
    )]
    candidate_conflicts = sum(bool(row["event_conflicts"]) or int(row["collision"]) != 0
                              for row in thin_candidates)
    audits = {
        "status": "PASS",
        "physical_header_count": len(headers),
        "unique_physical_header_count": len(header_by_coordinate),
        "duplicate_physical_header_count": len(headers) - len(header_by_coordinate),
        "enabled_physical_header_count": sum(bool(row["enabled"]) for row in headers),
        "disabled_non_native_physical_header_count": sum(not row["enabled"] for row in headers),
        "logical_manifest_location_count": len(logical_locations),
        "logical_physical_location_count": len({row["logical_code"] for row in headers}),
        "logical_native_location_count": len(native_by_logical),
        "logical_enabled_location_count": len({row["logical_code"] for row in headers
                                                if row["enabled"]}),
        "mode_table_counts": dict(sorted(mode_counts.items())),
        "native_slot_count": native_slot_count,
        "included_unique_manifest_row_count": len(included_unique),
        "positive_weight_physical_channel_candidate_count":
            len(native_manifest_source_keys),
        "positive_weight_serialized_unique_count":
            len(native_manifest_source_keys & included_unique),
        "positive_weight_physical_channel_drop_count": len(positive_channel_drops),
        "positive_weight_physical_channel_drop_keys": positive_channel_drops,
        "positive_weight_native_manifest_candidate_count": len(native_manifest_source_keys),
        "positive_weight_native_manifest_unmapped_count": len(
            native_manifest_source_keys - physically_eligible_source_keys
        ),
        "positive_weight_native_manifest_unmapped_keys": sorted(
            native_manifest_source_keys - physically_eligible_source_keys
        ),
        "positive_weight_physical_tuple_expected_count": len(expected_physical_tuples),
        "positive_weight_physical_tuple_serialized_count": len(serialized_physical_tuples),
        "positive_weight_physical_tuple_drop_count": len(physical_tuple_drops),
        "positive_weight_physical_tuple_drop_keys": [
            f"{group}:{number}:{mode}:{key}"
            for group, number, mode, key in physical_tuple_drops
        ],
        "unexpected_physical_tuple_count": len(unexpected_physical_tuples),
        "excluded_manifest_rows": dict(sorted(excluded.items())),
        "physical_channel_rejections": dict(sorted(physical_channel_rejections.items())),
        "method_misplacement_count": len(forbidden_method_inclusions),
        "zero_weight_native_inclusion_count": len(zero_weight_inclusions),
        "event_native_inclusion_count": len(event_inclusions),
        "egg_native_inclusion_count": len(egg_inclusions),
        "fossil_native_inclusion_count": len(fossil_inclusions),
        "legacy_all_four_mode_header_count": legacy_all_four,
        "legacy_two_species_all_mode_header_count": legacy_two_species_all_mode,
        "legacy_non_native_mode_pointer_count": legacy_non_native_modes,
        "legacy_zero_coordinate_orphan_header_count": legacy_zero_orphans,
        "balance_physical_row_count": len(balance_metrics["physical"]),
        "balance_logical_row_count": len(balance_metrics["logical"]),
        "progression_requirement_policy": "progression_requirement_metadata_only",
        "runtime_gate_claim_count": 0,
        "serializer_progression_requirement_applied": False,
        "progression_metadata_runtime_owner_alignment_status":
            progression_contract["metadata_runtime_owner_alignment_status"],
        "progression_metadata_runtime_owner_mismatch_count":
            progression_contract["metadata_runtime_owner_mismatch_count"],
        "logical_without_enabled_native_table": {
            logical: sorted({str(row["disabled_reason"]) for row in headers
                             if row["logical_code"] == logical and row["disabled_reason"]})
            for logical in sorted({str(row["logical_code"]) for row in headers
                                   if not any(item["logical_code"] == row["logical_code"]
                                              and item["enabled"] for item in headers)})
        },
        "thin_scored_map_count": len(thin_scores),
        "thin_candidate_count": len(thin_candidates),
        "thin_candidate_collision_or_event_conflict_count": candidate_conflicts,
    }
    required_zero = (
        audits["duplicate_physical_header_count"], audits["method_misplacement_count"],
        audits["zero_weight_native_inclusion_count"], audits["event_native_inclusion_count"],
        audits["egg_native_inclusion_count"], audits["fossil_native_inclusion_count"],
        audits["thin_candidate_collision_or_event_conflict_count"],
        audits["positive_weight_physical_channel_drop_count"],
        audits["positive_weight_native_manifest_unmapped_count"],
        audits["positive_weight_physical_tuple_drop_count"],
        audits["unexpected_physical_tuple_count"],
        progression_contract["premature_exposure_count"],
    )
    if len(headers) != 133 or any(required_zero) \
            or dict(sorted(mode_counts.items())) \
            != dict(sorted(EXPECTED_STAGE58_MODE_TABLE_COUNTS.items())):
        raise WorldBalanceError(f"生成plan監査FAIL: {audits}")
    audits["required_mode_table_counts"] = dict(
        sorted(EXPECTED_STAGE58_MODE_TABLE_COUNTS.items())
    )
    return {
        "schema_version": 2,
        "tool": "stage58_world_balance",
        "rom_sha256": _sha(rom),
        "inputs": {"fire_red_wild_encounters": upstream_meta},
        "rates": dict(sorted(normalized_rates.items())),
        "slot_probabilities": FIRERED_SLOT_PROBABILITIES,
        "native_manifest_source_keys": sorted(native_manifest_source_keys),
        "expected_positive_physical_tuples": [
            f"{group}:{number}:{mode}:{key}"
            for group, number, mode, key in sorted(expected_physical_tuples)
        ],
        "physical_encounter_classification_overrides": dict(
            sorted(PHYSICAL_ENCOUNTER_CLASSIFICATION_OVERRIDES.items())
        ),
        "headers": headers,
        "audit": audits,
        "progression_contract": progression_contract,
        "balance_metrics": balance_metrics,
        "thin_score_formula": {
            "object_zero": 24, "bg_zero": 12, "coord_zero": 6, "item_zero": 12,
            "native_mode_zero": 18, "low_density_max": 20, "large_area_max": 8,
        },
        "thin_places": thin_scores,
        "thin_candidates": thin_candidates,
    }


def _audit_metric_table(mode: str, metric: Mapping[str, Any] | None,
                        what: str) -> None:
    if metric is None:
        return
    if (int(metric["slot_count"]) != WILD_SLOT_COUNTS[mode]
            or int(metric["level_min"]) < 1
            or int(metric["level_min"]) > int(metric["level_max"])
            or int(metric["level_max"]) > 100
            or int(metric["diversity"]) != len(metric["species_ids"])):
        raise WorldBalanceError(f"{what} balance metricが不正です")
    groups = metric.get("slot_groups", [])
    if len(groups) != len(FIRERED_SLOT_GROUPS[mode]):
        raise WorldBalanceError(f"{what} slot group数が不正です")
    for index, group in enumerate(groups):
        mass = group.get("species_probability_mass", {})
        if (int(group["slot_group_index"]) != index
                or group["slot_indices"] != FIRERED_SLOT_GROUPS[mode][index]
                or int(group["probability_total"]) != 100
                or sum(int(value) for value in mass.values()) != 100
                or int(group["diversity"]) != len(mass)):
            raise WorldBalanceError(f"{what} species確率massが不正です")


def _audit_balance_metrics(plan: Mapping[str, Any],
                           headers: Sequence[Mapping[str, Any]]) -> None:
    balance = plan.get("balance_metrics")
    physical = balance.get("physical") if isinstance(balance, Mapping) else None
    if not isinstance(physical, list) or len(physical) != 133:
        raise WorldBalanceError("balance metrics physicalは133行必要です")
    physical_by_coordinate = {
        (int(row["group"]), int(row["map"])): row for row in physical
    }
    if len(physical_by_coordinate) != 133:
        raise WorldBalanceError("balance metrics physical座標が重複しています")
    for header in headers:
        coordinate = (int(header["group"]), int(header["map"]))
        row = physical_by_coordinate.get(coordinate)
        if row is None or row["logical_code"] != header["logical_code"]:
            raise WorldBalanceError(f"balance metrics physical crosswalk不一致: {coordinate}")
        for mode in WILD_SLOT_COUNTS:
            metrics = row["modes"][mode]
            before, after = metrics["before"], metrics["after"]
            _audit_metric_table(mode, before, f"{coordinate}/{mode}/before")
            _audit_metric_table(mode, after, f"{coordinate}/{mode}/after")
            expected_after = _table_balance_metrics(mode, header["modes"][mode])
            if after != expected_after:
                raise WorldBalanceError(f"{coordinate}/{mode} after metricsがheaderと不一致です")
            if metrics["delta"] != _table_balance_delta(mode, before, after):
                raise WorldBalanceError(f"{coordinate}/{mode} metrics deltaが不一致です")

    logical = balance.get("logical")
    if not isinstance(logical, list):
        raise WorldBalanceError("balance metrics logicalがありません")
    expected_codes = sorted({str(row["logical_code"]) for row in physical})
    if [str(row["logical_code"]) for row in logical] != expected_codes:
        raise WorldBalanceError("balance metrics logical codeが不一致です")
    for logical_row in logical:
        members = [row for row in physical
                   if row["logical_code"] == logical_row["logical_code"]]
        if int(logical_row["physical_header_count"]) != len(members):
            raise WorldBalanceError("balance metrics logical physical数が不一致です")
        for mode in WILD_SLOT_COUNTS:
            before = _aggregate_balance_metrics(
                mode, [row["modes"][mode]["before"] for row in members]
            )
            after = _aggregate_balance_metrics(
                mode, [row["modes"][mode]["after"] for row in members]
            )
            expected = {
                "before": before, "after": after,
                "delta": _aggregate_balance_delta(mode, before, after),
            }
            if logical_row["modes"][mode] != expected:
                raise WorldBalanceError(
                    f"balance metrics logical {logical_row['logical_code']}/{mode}不一致"
                )
    aggregate = balance.get("aggregate", {}).get("modes", {})
    if set(aggregate) != set(WILD_SLOT_COUNTS):
        raise WorldBalanceError("balance metrics aggregate modeが不一致です")
    for mode in WILD_SLOT_COUNTS:
        before = _aggregate_balance_metrics(
            mode, [row["modes"][mode]["before"] for row in physical]
        )
        after = _aggregate_balance_metrics(
            mode, [row["modes"][mode]["after"] for row in physical]
        )
        expected = {
            "before": before, "after": after,
            "delta": _aggregate_balance_delta(mode, before, after),
        }
        if aggregate[mode] != expected:
            raise WorldBalanceError(f"balance metrics aggregate {mode}が不一致です")


def _audit_connection_spans(thin_places: Sequence[Mapping[str, Any]]) -> None:
    if len(thin_places) != 133:
        raise WorldBalanceError("薄い場所監査は133 physical map必要です")
    for row in thin_places:
        width, height = int(row["width"]), int(row["height"])
        for connection in row.get("connections", []):
            direction = connection["direction"]
            offset = int(connection["offset"])
            if direction in {"north", "south"}:
                start = max(0, offset)
                stop = min(width, offset + int(connection["destination_width"]))
            elif direction in {"west", "east"}:
                start = max(0, offset)
                stop = min(height, offset + int(connection["destination_height"]))
            else:
                if connection["source_axis_span"] is not None:
                    raise WorldBalanceError("unsupported connectionがseed spanを持っています")
                continue
            expected = [start, stop - 1] if start < stop else None
            if connection["source_axis_span"] != expected:
                raise WorldBalanceError(
                    f"connection direction/offset span不一致: "
                    f"{row['group']}/{row['map']} {connection}"
                )


def audit_world_balance_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    """serialize直前のplanを独立にfail-closed監査する。"""
    headers = plan.get("headers")
    if not isinstance(headers, list) or len(headers) != 133:
        raise WorldBalanceError("plan headersは133行必要です")
    coordinates: set[tuple[int, int]] = set()
    mode_counts: Counter[str] = Counter()
    actual_physical_tuples: set[str] = set()
    actual_native_source_keys: set[str] = set()
    observed_overrides: dict[str, str] = {}
    for header in headers:
        coordinate = (int(header["group"]), int(header["map"]))
        if coordinate in coordinates:
            raise WorldBalanceError(f"plan physical header重複: {coordinate}")
        coordinates.add(coordinate)
        source_map = str(header.get("source_map", ""))
        expected_encounter_classification = (
            PHYSICAL_ENCOUNTER_CLASSIFICATION_OVERRIDES.get(
                source_map, str(header.get("classification", ""))
            )
        )
        if (header.get("encounter_classification") != expected_encounter_classification
                or header.get("classification_override") != (
                    expected_encounter_classification
                    if expected_encounter_classification != header.get("classification")
                    else None
                )):
            raise WorldBalanceError(f"plan encounter分類override不一致: {coordinate}")
        if header.get("classification_override") is not None:
            observed_overrides[source_map] = expected_encounter_classification
        modes = header.get("modes")
        if set(modes or {}) != {"land", "water", "rock", "fishing"}:
            raise WorldBalanceError(f"plan mode key不一致: {coordinate}")
        for mode, table in modes.items():
            if table is None:
                continue
            mode_counts[mode] += 1
            slots = table.get("slots", [])
            probabilities = table.get("slot_probabilities", [])
            if len(slots) != WILD_SLOT_COUNTS[mode] or probabilities != FIRERED_SLOT_PROBABILITIES[mode]:
                raise WorldBalanceError(f"{coordinate}/{mode} slot ABI不一致")
            for group in FIRERED_SLOT_GROUPS[mode]:
                if sum(probabilities[index] for index in group) != 100:
                    raise WorldBalanceError(f"{coordinate}/{mode} slot確率合計不一致")
            if any(len(slot) != 3 or not 1 <= int(slot[0]) <= int(slot[1]) <= 100
                   or not 1 <= int(slot[2]) <= 1620 for slot in slots):
                raise WorldBalanceError(f"{coordinate}/{mode} slot値不一致")
            candidate_records = table.get("candidate_records", [])
            record_by_key = {
                str(row.get("encounter_key")): row for row in candidate_records
            }
            if (not candidate_records or len(record_by_key) != len(candidate_records)
                    or set(record_by_key) != set(map(str, table.get("source_keys", [])))):
                raise WorldBalanceError(f"{coordinate}/{mode} candidate正本不一致")
            parallel_lengths = [
                len(table.get(field, [])) for field in
                ("source_keys", "source_slots", "source_weights", "species_keys")
            ]
            if parallel_lengths != [len(slots)] * 4:
                raise WorldBalanceError(f"{coordinate}/{mode} slot source配列長不一致")
            for slot_index, (slot, key) in enumerate(zip(slots, table["source_keys"])):
                record = record_by_key.get(str(key))
                if record is None:
                    raise WorldBalanceError(f"{coordinate}/{mode} 未知source key")
                low = int(record["level_min"])
                high = max(low, int(record["level_max"]))
                if (list(map(int, slot)) != [low, high, int(record["species_id"])]
                        or int(table["source_slots"][slot_index])
                        != int(record["manifest_slot"])
                        or int(table["source_weights"][slot_index])
                        != int(record["weight"])
                        or str(table["species_keys"][slot_index])
                        != str(record["species_key"])):
                    raise WorldBalanceError(
                        f"{coordinate}/{mode} slot/source/species/level/weight不一致"
                    )
                actual_physical_tuples.add(
                    f"{coordinate[0]}:{coordinate[1]}:{mode}:{key}"
                )
                actual_native_source_keys.add(str(key))
            group_contracts = table.get("group_allocation_contracts", [])
            if len(group_contracts) != len(FIRERED_SLOT_GROUPS[mode]):
                raise WorldBalanceError(f"{coordinate}/{mode} weight契約数不一致")
            for indices, group_contract in zip(
                FIRERED_SLOT_GROUPS[mode], group_contracts,
            ):
                masses = group_contract.get("serialized_probability_mass", {})
                targets = group_contract.get("target_probability_mass", {})
                eligible = group_contract.get("eligible_source_keys", [])
                if (group_contract.get("slot_indices") != indices
                        or int(group_contract.get("slot_group_index", -1))
                        != FIRERED_SLOT_GROUPS[mode].index(indices)
                        or set(masses) != set(eligible)
                        or set(targets) != set(eligible)
                        or set(group_contract.get(
                            "target_weight_by_source_key", {}
                        )) != set(eligible)
                        or sum(int(value) for value in masses.values()) != 100
                        or int(group_contract.get(
                            "zero_probability_candidate_count", -1
                        )) != 0):
                    raise WorldBalanceError(
                        f"{coordinate}/{mode} positive weight割当契約不一致"
                    )
                pseudo_candidates = [
                    {"encounter_key": key,
                     "slot": int(record_by_key[key]["manifest_slot"])}
                    for key in eligible
                ]
                exact_slots, exact_audit = _allocate_group(
                    pseudo_candidates,
                    [probabilities[index] for index in indices],
                    {str(key): int(value) for key, value in group_contract[
                        "target_weight_by_source_key"
                    ].items()},
                )
                actual_group_keys = [str(table["source_keys"][index])
                                     for index in indices]
                if (actual_group_keys != [str(row["encounter_key"])
                                          for row in exact_slots]
                        or any(group_contract.get(key) != exact_audit[key] for key in (
                            "allocator", "optimality_status",
                            "serialized_probability_mass", "target_probability_mass",
                            "zero_probability_candidate_count",
                            "max_absolute_weight_error",
                            "optimal_max_absolute_weight_error",
                            "optimality_tolerance_points", "within_optimality_tolerance",
                            "total_absolute_weight_error",
                            "quality_limit_points", "quality_tolerance_points",
                        ))
                        or float(group_contract.get(
                            "max_absolute_weight_error", 999
                        )) > float(group_contract.get(
                            "optimal_max_absolute_weight_error", -999
                        )) + 0.0001
                        or float(group_contract.get(
                            "max_absolute_weight_error", 999
                        )) > 15.0001):
                    raise WorldBalanceError(
                        f"{coordinate}/{mode} exact weight最適性不一致"
                    )
            if (mode == "fishing") != (
                table.get("rod_tier_policy")
                == "MANIFEST_AUTHORED_OLD_GOOD_SUPER_ELIGIBILITY_AND_WEIGHT"
            ):
                raise WorldBalanceError(f"{coordinate}/{mode} 竿tier契約不一致")
            contract_union = set().union(*(
                set(contract["eligible_source_keys"]) for contract in group_contracts
            ))
            if set(table.get("source_keys", [])) != contract_union:
                raise WorldBalanceError(
                    f"{coordinate}/{mode} positive candidate coverage不一致"
                )
            if "gate" in table:
                raise WorldBalanceError(f"{coordinate}/{mode} runtime gate過剰主張が残っています")
            requirement = table.get("progression_requirement", {})
            if (requirement.get("condition") != EXPECTED_NATIVE_CONDITION
                    or not requirement.get("unlock_key")
                    or requirement.get("policy")
                    != "progression_requirement_metadata_only"
                    or requirement.get("serializer_applied") is not False):
                raise WorldBalanceError(f"{coordinate}/{mode} progression metadata欠落")
    contract = plan.get("progression_contract", {})
    if (contract.get("policy") != "progression_requirement_metadata_only"
            or contract.get("runtime_gate_claimed_by_world_plan") is not False
            or contract.get("serializer_applies_progression_requirement") is not False
            or contract.get("serializer_non_application_status") != "PASS"
            or contract.get("serializer_source", {}).get("consumed_table_fields")
            != ["rate", "slots"]
            or contract.get("serializer_source", {}).get("ignored_metadata_fields")
            != ["progression_requirement"]
            or contract.get("runtime_map_access_owner_coverage_status") != "PASS"
            or int(contract.get("runtime_map_access_owner_physical_count", 0)) != 133
            or contract.get("metadata_runtime_owner_alignment_status")
            not in {"PASS", "SAFE_LATE_ACCESS"}
            or int(contract.get("premature_exposure_count", -1)) != 0):
        raise WorldBalanceError("progression metadata/runtime owner契約が不正です")
    _audit_balance_metrics(plan, headers)
    thin_places = plan.get("thin_places", [])
    _audit_connection_spans(thin_places)
    candidates = plan.get("thin_candidates", [])
    if not candidates or any(int(row.get("collision", -1)) != 0
                             or row.get("event_conflicts")
                             or int(row.get("reachability_seed_count", 0)) <= 0
                             for row in candidates):
        raise WorldBalanceError("薄い場所候補にcollision/event衝突があります")
    owner_by_logical = {
        str(row["logical_code"]): str(row["runtime_map_access_owner_unlock_key"])
        for row in thin_places
    }
    if any(row.get("progression_requirement_policy")
           != "progression_requirement_metadata_only"
           or row.get("unlock_key")
           != row.get("runtime_map_access_owner_unlock_key")
           or row.get("reward_tier_owner_policy") != "runtime_map_access_owner"
           or row.get("reward_tier")
           != _reward_tier(str(row.get("runtime_map_access_owner_unlock_key")))
           or row.get("runtime_map_access_owner_unlock_key")
           != owner_by_logical.get(str(row["logical_code"]))
           for row in candidates):
        raise WorldBalanceError("薄い場所候補のmap access ownerが不一致です")
    if dict(sorted(mode_counts.items())) \
            != dict(sorted(EXPECTED_STAGE58_MODE_TABLE_COUNTS.items())) \
            or plan.get("audit", {}).get("required_mode_table_counts") \
            != dict(sorted(EXPECTED_STAGE58_MODE_TABLE_COUNTS.items())):
        raise WorldBalanceError("Stage58 mode table coverage不一致")
    audit = plan.get("audit", {})
    expected_tuples = set(map(str, plan.get("expected_positive_physical_tuples", [])))
    native_keys = set(map(str, plan.get("native_manifest_source_keys", [])))
    if (int(audit.get("positive_weight_physical_channel_drop_count", -1)) != 0
            or audit.get("positive_weight_physical_channel_drop_keys") != []
            or int(audit.get(
                "positive_weight_physical_channel_candidate_count", -1
            )) != int(audit.get(
                "positive_weight_serialized_unique_count", -2
            ))
            or int(audit.get("positive_weight_native_manifest_unmapped_count", -1)) != 0
            or audit.get("positive_weight_native_manifest_unmapped_keys") != []
            or int(audit.get("positive_weight_physical_tuple_drop_count", -1)) != 0
            or audit.get("positive_weight_physical_tuple_drop_keys") != []
            or int(audit.get("unexpected_physical_tuple_count", -1)) != 0
            or expected_tuples != actual_physical_tuples
            or native_keys != actual_native_source_keys
            or int(audit.get("positive_weight_physical_tuple_expected_count", -1))
            != len(expected_tuples)
            or int(audit.get("positive_weight_physical_tuple_serialized_count", -1))
            != len(actual_physical_tuples)
            or plan.get("physical_encounter_classification_overrides")
            != dict(sorted(PHYSICAL_ENCOUNTER_CLASSIFICATION_OVERRIDES.items()))
            or observed_overrides != PHYSICAL_ENCOUNTER_CLASSIFICATION_OVERRIDES):
        raise WorldBalanceError("positive-weight physical candidate脱落があります")
    return {
        "status": "PASS", "physical_header_count": len(headers),
        "unique_physical_header_count": len(coordinates),
        "mode_table_counts": dict(sorted(mode_counts.items())),
        "thin_candidate_count": len(candidates),
        "balance_physical_row_count": len(plan["balance_metrics"]["physical"]),
        "progression_requirement_policy": "progression_requirement_metadata_only",
        "serializer_progression_requirement_applied": False,
        "positive_weight_physical_channel_drop_count": 0,
        "progression_metadata_runtime_owner_alignment_status":
            contract["metadata_runtime_owner_alignment_status"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path,
                        default=Path("build/stages/57_comprehensive_debug_repair.gba"))
    parser.add_argument("--stage17", type=Path,
                        default=Path("build/stages/17_regression.json"))
    parser.add_argument("--encounters", type=Path,
                        default=Path("manifests/kanto_encounters.csv"))
    parser.add_argument("--species", type=Path, default=Path("manifests/species_ids.csv"))
    parser.add_argument("--rates", default=json.dumps(DEFAULT_RATES, ensure_ascii=False))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).resolve().parents[1]
        rom = (root / args.rom).read_bytes() if not args.rom.is_absolute() else args.rom.read_bytes()
        stage17_path = root / args.stage17 if not args.stage17.is_absolute() else args.stage17
        encounter_path = root / args.encounters if not args.encounters.is_absolute() else args.encounters
        species_path = root / args.species if not args.species.is_absolute() else args.species
        species = {row["species_key"]: int(row["id"]) for row in _rows(species_path)}
        plan = build_world_balance_plan(
            root, rom, json.loads(stage17_path.read_text(encoding="utf-8")),
            _rows(encounter_path), species, json.loads(args.rates),
        )
        audit_world_balance_plan(plan)
        rendered = _stable(plan)
        if args.output:
            output = root / args.output if not args.output.is_absolute() else args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, WorldBalanceError) as error:
        print(f"Stage58 world balance plan failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
