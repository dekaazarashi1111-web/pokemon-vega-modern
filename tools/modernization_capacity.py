"""Stage62の現代化容量とconsumer rootを監査する。

このmoduleは読み取り専用である。明示採用されたROM identity、継承中の最新
allocation ledger、各canonical runtime tableを所有するmetadataを結合する。
物理ROM領域、論理table容量、追跡済みsave/RAM所有範囲を区別し、消去済みbyteや
未追跡addressだけを根拠に安全な空き容量とは判定しない。
"""

from __future__ import annotations

import binascii
import csv
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROM_BASE = 0x08000000
DEFAULT_BASELINE = Path("config/active_play_baseline.json")
DEFAULT_ALLOCATION = Path("build/stages/61_critical_release_allocation.json")
DEFAULT_SAVE_LAYOUT = Path("config/save_layout.csv")
DEFAULT_RAM_LAYOUT = Path("config/ram_layout.csv")

# 現在の物理containerを表す値であり、ledger未記載byteの空きを保証する値ではない。
# 値を所有するsourceもreportへ含める。
SAVE_SPACE_CONTRACTS: Mapping[str, tuple[int, int, str]] = {
    "SAVE_BLOCK1_OFFSET": (
        0,
        0x3D40,
        "overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c",
    ),
    "SAVE_BLOCK2_OFFSET": (
        0,
        0x0F24,
        "overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c",
    ),
    "SAVE_PARASITE_IMAGE_OFFSET": (
        0,
        0x2EA4,
        "tools/stage61_state_namespace_collision_audit.py",
    ),
    # 手持ちPokemonは100 byteで、先頭80 byteがBoxPokemon ABIである。
    "POKEMON_ABI_OFFSET": (0, 100, "config/save_layout.csv"),
}

RAM_SPACE_CONTRACTS: Mapping[str, tuple[int, int, str]] = {
    "EWRAM": (0x02000000, 0x02040000, "GBA EWRAM physical range"),
    "IWRAM": (0x03000000, 0x03008000, "GBA IWRAM physical range"),
}


class CapacityAuditError(RuntimeError):
    """必須入力を安全に監査できない場合に送出する。"""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _number(value: Any, label: str) -> int:
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as error:
        raise CapacityAuditError(f"{label} is not an integer: {value!r}") from error


def _path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _json(root: Path, relative: str | Path, label: str) -> dict[str, Any]:
    path = _path(root, relative)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CapacityAuditError(f"required {label} is missing: {path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CapacityAuditError(f"required {label} is unreadable: {path}: {error}") from error
    if not isinstance(value, dict):
        raise CapacityAuditError(f"required {label} is not a JSON object: {path}")
    return value


def _csv(root: Path, relative: str | Path, label: str) -> list[dict[str, str]]:
    path = _path(root, relative)
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, UnicodeError, csv.Error) as error:
        raise CapacityAuditError(f"required {label} is unreadable: {path}: {error}") from error
    if not rows:
        raise CapacityAuditError(f"required {label} is empty: {path}")
    return rows


def _read(root: Path, relative: str | Path, label: str) -> bytes:
    path = _path(root, relative)
    try:
        return path.read_bytes()
    except OSError as error:
        raise CapacityAuditError(f"required {label} is unreadable: {path}: {error}") from error


def _span(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or size < 0 or offset + size > len(rom):
        raise CapacityAuditError(
            f"{label} is outside the exact ROM: address=0x{address:08X} size={size}"
        )
    return rom[offset : offset + size]


def _pointer_at_offset(rom: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(rom):
        raise CapacityAuditError(f"{label} pointer site is outside ROM: {offset}")
    return struct.unpack_from("<I", rom, offset)[0]


def _pointer_at_address(rom: bytes, address: int, label: str) -> int:
    return _pointer_at_offset(rom, address - ROM_BASE, label)


def _hex(value: int) -> str:
    return f"0x{value:08X}"


def _checks_status(checks: Sequence[Mapping[str, Any]]) -> str:
    return "PASS" if checks and all(bool(row["passed"]) for row in checks) else "FAIL"


def _check(
    checks: list[dict[str, Any]], name: str, passed: bool, **evidence: Any
) -> None:
    checks.append({"name": name, "passed": bool(passed), **evidence})


def _manifest_space(
    rows: Sequence[Mapping[str, str]], key_column: str, declared_capacity: int
) -> dict[str, Any]:
    ids = [_number(row.get("id"), f"{key_column} id") for row in rows]
    keys = [str(row.get(key_column, "")).strip() for row in rows]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    duplicate_keys = sorted({value for value in keys if keys.count(value) > 1})
    expected = list(range(declared_capacity))
    return {
        "declared_capacity": declared_capacity,
        "manifest_rows": len(rows),
        "occupied_slots": len(set(ids)),
        "free_slots": declared_capacity - len(set(ids)),
        "minimum_id": min(ids),
        "maximum_id": max(ids),
        "contiguous_zero_based": sorted(ids) == expected,
        "duplicate_ids": duplicates,
        "duplicate_keys": duplicate_keys,
        "out_of_range_ids": sorted(value for value in ids if not 0 <= value < declared_capacity),
    }


def _root_rows(
    rom: bytes,
    sites: Iterable[int],
    expected_address: int,
    *,
    sites_are_addresses: bool = False,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for site in sites:
        offset = site - ROM_BASE if sites_are_addresses else site
        actual = _pointer_at_offset(rom, offset, "consumer root")
        result.append(
            {
                "site_offset": offset,
                "site_address": _hex(ROM_BASE + offset),
                "expected_target": expected_address,
                "expected_target_hex": _hex(expected_address),
                "actual_target": actual,
                "actual_target_hex": _hex(actual),
                "matches": actual == expected_address,
            }
        )
    return result


def _table(
    rom: bytes,
    *,
    address: int,
    size: int,
    count: int | None = None,
    stride: int | None = None,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    raw = _span(rom, address, size, "runtime table")
    result: dict[str, Any] = {
        "address": address,
        "address_hex": _hex(address),
        "size_bytes": size,
        "current_sha256": _sha256(raw),
        "non_erased_bytes": sum(value != 0xFF for value in raw),
        "erased_bytes_inside_declared_table": raw.count(0xFF),
    }
    if count is not None:
        result["declared_entries"] = count
    if stride is not None:
        result["stride_bytes"] = stride
        result["shape_matches"] = count is None or count * stride == size
    if source_sha256:
        result["origin_sha256"] = source_sha256
        result["matches_origin_bytes"] = result["current_sha256"] == source_sha256
    return result


def _audit_allocator(
    rom: bytes, allocation: Mapping[str, Any], checks: list[dict[str, Any]]
) -> dict[str, Any]:
    regions = list(allocation.get("regions", []))
    allocations = list(allocation.get("allocations", []))
    summaries = allocation.get("summaries", {})
    if not regions or not isinstance(summaries, Mapping):
        raise CapacityAuditError("allocation ledger has no regions/summaries")
    region_by_name = {str(row.get("name")): row for row in regions}
    geometry_errors: list[str] = []
    by_region: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in allocations:
        name = str(row.get("name", ""))
        region_name = str(row.get("region", ""))
        region = region_by_name.get(region_name)
        if not name or region is None:
            geometry_errors.append(f"unknown allocation/region: {name}/{region_name}")
            continue
        start = _number(row.get("start"), f"allocation {name} start")
        end = _number(row.get("end_exclusive"), f"allocation {name} end")
        size = _number(row.get("size"), f"allocation {name} size")
        region_start = _number(region.get("start"), f"region {region_name} start")
        region_end = _number(region.get("end_exclusive"), f"region {region_name} end")
        if end - start != size or start < region_start or end > region_end:
            geometry_errors.append(f"invalid span: {name}")
        by_region[region_name].append(row)

    region_reports: list[dict[str, Any]] = []
    overlap_count = 0
    untracked_non_erased = 0
    total_declared_allocated = 0
    total_declared_free = 0
    for region in regions:
        if str(region.get("kind")) != "allocatable":
            continue
        name = str(region["name"])
        start = _number(region["start"], f"region {name} start")
        end = _number(region["end_exclusive"], f"region {name} end")
        ordered = sorted(
            by_region.get(name, []), key=lambda row: _number(row["start"], "allocation start")
        )
        gaps: list[tuple[int, int]] = []
        cursor = start
        declared = 0
        for row in ordered:
            row_start = _number(row["start"], "allocation start")
            row_end = _number(row["end_exclusive"], "allocation end")
            if row_start < cursor:
                overlap_count += 1
            if row_start > cursor:
                gaps.append((cursor, row_start))
            cursor = max(cursor, row_end)
            declared += row_end - row_start
        if cursor < end:
            gaps.append((cursor, end))
        free_bytes = sum(right - left for left, right in gaps)
        non_erased = sum(
            sum(value != 0xFF for value in rom[left:right]) for left, right in gaps
        )
        erased = free_bytes - non_erased
        untracked_non_erased += non_erased
        total_declared_allocated += declared
        total_declared_free += free_bytes
        allocated_raw = b"".join(
            rom[_number(row["start"], "start") : _number(row["end_exclusive"], "end")]
            for row in ordered
        )
        region_reports.append(
            {
                "name": name,
                "start": start,
                "end_exclusive": end,
                "capacity_bytes": end - start,
                "declared_allocated_bytes": declared,
                "declared_free_bytes": free_bytes,
                "actual_erased_free_bytes": erased,
                "untracked_non_erased_bytes": non_erased,
                "allocated_non_erased_bytes": sum(value != 0xFF for value in allocated_raw),
                "allocated_internal_ff_bytes": allocated_raw.count(0xFF),
                "free_segment_count": len(gaps),
                "largest_contiguous_free_bytes": max(
                    (right - left for left, right in gaps), default=0
                ),
                "free_segments": [
                    {
                        "start": left,
                        "end_exclusive": right,
                        "size": right - left,
                    }
                    for left, right in gaps
                ],
            }
        )
    _check(
        checks,
        "rom_allocation_geometry",
        not geometry_errors and overlap_count == 0,
        geometry_errors=geometry_errors,
        overlap_count=overlap_count,
    )
    _check(
        checks,
        "rom_unallocated_space_is_erased",
        untracked_non_erased == 0,
        untracked_non_erased_bytes=untracked_non_erased,
    )
    summary_matches = (
        total_declared_allocated == _number(summaries.get("allocated_bytes"), "allocated bytes")
        and total_declared_free
        == _number(summaries.get("remaining_allocatable_bytes"), "remaining bytes")
        and len(rom) == _number(summaries.get("rom_size"), "allocation ROM size")
    )
    _check(checks, "rom_allocation_summary_matches", summary_matches)
    return {
        "ledger_schema_version": allocation.get("schema_version"),
        "rom_size": len(rom),
        "allocatable_bytes": _number(summaries.get("allocatable_bytes"), "allocatable bytes"),
        "declared_allocated_bytes": total_declared_allocated,
        "declared_free_bytes": total_declared_free,
        "actual_erased_free_bytes": total_declared_free - untracked_non_erased,
        "untracked_non_erased_bytes": untracked_non_erased,
        "allocation_count": len(allocations),
        "regions": region_reports,
        "free_is_allocator_authority_only": True,
    }


def _audit_intervals(
    rows: Sequence[Mapping[str, str]],
    contracts: Mapping[str, tuple[int, int, str]],
    *,
    status: str = "LIVE",
) -> tuple[dict[str, Any], list[str]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors: list[str] = []
    for source in rows:
        if source.get("status") != status or not source.get("start"):
            continue
        space = str(source.get("address_space", ""))
        start = _number(source.get("start"), f"{space} start")
        end = _number(source.get("end_exclusive"), f"{space} end")
        size = _number(source.get("size"), f"{space} size")
        if start >= end or end - start != size:
            errors.append(f"invalid interval: {source.get('symbol')}")
        grouped[space].append(
            {
                "start": start,
                "end_exclusive": end,
                "size": size,
                "owner": source.get("owner"),
                "symbol": source.get("symbol"),
            }
        )
    output: dict[str, Any] = {}
    for space, intervals in sorted(grouped.items()):
        intervals.sort(key=lambda row: (row["start"], row["end_exclusive"]))
        overlaps: list[dict[str, Any]] = []
        for left, right in zip(intervals, intervals[1:]):
            if left["end_exclusive"] > right["start"]:
                overlaps.append({"left": left["symbol"], "right": right["symbol"]})
        if overlaps:
            errors.append(f"{space} has {len(overlaps)} overlaps")
        occupied = sum(row["size"] for row in intervals)
        report: dict[str, Any] = {
            "live_interval_count": len(intervals),
            "tracked_owned_bytes": occupied,
            "overlap_count": len(overlaps),
            "overlaps": overlaps,
            "minimum_tracked_start": min(row["start"] for row in intervals),
            "maximum_tracked_end_exclusive": max(row["end_exclusive"] for row in intervals),
            "tracked_span_bytes": (
                max(row["end_exclusive"] for row in intervals)
                - min(row["start"] for row in intervals)
            ),
        }
        contract = contracts.get(space)
        if contract:
            lower, upper, source = contract
            outside = [
                row["symbol"]
                for row in intervals
                if row["start"] < lower or row["end_exclusive"] > upper
            ]
            if outside:
                errors.append(f"{space} intervals outside container: {outside}")
            report.update(
                {
                    "container_start": lower,
                    "container_end_exclusive": upper,
                    "container_capacity_bytes": upper - lower,
                    "container_contract_source": source,
                    "untracked_bytes": upper - lower - occupied,
                    "untracked_bytes_are_not_declared_free": True,
                    "outside_container": outside,
                }
            )
        output[space] = report
    return output, errors


def _scan_evolutions(raw: bytes, species_count: int) -> dict[str, Any]:
    stride = 128
    slots = 16
    if len(raw) != species_count * stride:
        raise CapacityAuditError("evolution table shape differs")
    used = 0
    invalid_targets: list[dict[str, int]] = []
    per_species: list[int] = []
    decoded: dict[int, list[dict[str, int]]] = defaultdict(list)
    for species in range(species_count):
        count = 0
        for slot in range(slots):
            method, parameter, target, extra = struct.unpack_from(
                "<HHHH", raw, species * stride + slot * 8
            )
            if method == 0:
                continue
            count += 1
            used += 1
            decoded[species].append(
                {
                    "slot": slot,
                    "method": method,
                    "parameter": parameter,
                    "target_species": target,
                    "extra": extra,
                }
            )
            if target >= species_count:
                invalid_targets.append(
                    {"source_species": species, "slot": slot, "target_species": target}
                )
        per_species.append(count)
    return {
        "species_rows": species_count,
        "slots_per_species": slots,
        "declared_entries": species_count * slots,
        "used_entries": used,
        "free_entries": species_count * slots - used,
        "species_with_evolutions": sum(value > 0 for value in per_species),
        "maximum_used_slots_for_one_species": max(per_species),
        "invalid_target_count": len(invalid_targets),
        "invalid_targets": invalid_targets[:50],
        "decoded": decoded,
    }


def _scan_level_up(
    rom: bytes,
    *,
    pointer_address: int,
    pointer_count: int,
    data_address: int,
    data_size: int,
    move_count: int,
) -> dict[str, Any]:
    pointer_raw = _span(rom, pointer_address, pointer_count * 4, "level-up pointers")
    data_end = data_address + data_size
    pointers = list(struct.unpack(f"<{pointer_count}I", pointer_raw))
    invalid_pointers: list[dict[str, int]] = []
    invalid_moves: list[dict[str, int]] = []
    unterminated: list[int] = []
    meaningful_by_species: list[int] = []
    decoded: dict[int, list[dict[str, int]]] = {}
    end_by_pointer: dict[int, int] = {}
    entries_by_pointer: dict[int, list[dict[str, int]]] = {}
    for species, pointer in enumerate(pointers):
        if pointer < data_address or pointer + 3 > data_end:
            invalid_pointers.append({"species": species, "pointer": pointer})
            meaningful_by_species.append(0)
            decoded[species] = []
            continue
        if pointer not in entries_by_pointer:
            values: list[dict[str, int]] = []
            cursor = pointer
            for _ in range(256):
                if cursor + 3 > data_end:
                    break
                move, level = struct.unpack_from("<HB", rom, cursor - ROM_BASE)
                cursor += 3
                if move == 0 and level == 0xFF:
                    end_by_pointer[pointer] = cursor
                    entries_by_pointer[pointer] = values
                    break
                values.append({"move": move, "level": level})
            else:
                cursor = data_end + 1
            if pointer not in entries_by_pointer:
                unterminated.append(species)
                entries_by_pointer[pointer] = values
            for row in values:
                if not 0 <= row["move"] < move_count:
                    invalid_moves.append({"species": species, **row})
        decoded[species] = entries_by_pointer[pointer]
        meaningful_by_species.append(
            sum(row["move"] != 0 for row in entries_by_pointer[pointer])
        )
    furthest = max(end_by_pointer.values(), default=data_address)
    return {
        "declared_pointer_entries": pointer_count,
        "used_pointer_entries": len(pointers),
        "free_pointer_entries": pointer_count - len(pointers),
        "unique_lists": len(set(pointers)),
        "meaningful_move_entries_across_species": sum(meaningful_by_species),
        "unique_physical_move_entries": sum(
            sum(row["move"] != 0 for row in rows) for rows in entries_by_pointer.values()
        ),
        "placeholder_move_zero_entries": sum(
            sum(row["move"] == 0 for row in rows) for rows in entries_by_pointer.values()
        ),
        "maximum_meaningful_moves_for_one_species": max(meaningful_by_species),
        "declared_data_bytes": data_size,
        "used_data_prefix_bytes": furthest - data_address,
        "free_trailing_data_bytes": data_end - furthest,
        "invalid_pointer_count": len(invalid_pointers),
        "invalid_pointers": invalid_pointers[:50],
        "invalid_move_count": len(invalid_moves),
        "invalid_moves": invalid_moves[:50],
        "unterminated_list_count": len(unterminated),
        "unterminated_species": unterminated[:50],
        "pointers": pointers,
        "decoded": decoded,
    }


def _scan_egg_moves(
    raw: bytes, *, species_count: int, move_count: int
) -> dict[str, Any]:
    records: dict[int, list[int]] = {}
    current: int | None = None
    invalid_species: list[int] = []
    invalid_moves: list[dict[str, int]] = []
    sentinel_offset: int | None = None
    for offset in range(0, len(raw) - 1, 2):
        value = struct.unpack_from("<H", raw, offset)[0]
        if value == 0xFFFF:
            sentinel_offset = offset
            break
        if value >= 20000:
            current = value - 20000
            if current in records:
                invalid_species.append(current)
            records.setdefault(current, [])
            if not 0 <= current < species_count:
                invalid_species.append(current)
            continue
        if current is None:
            invalid_moves.append({"offset": offset, "move": value})
            continue
        records[current].append(value)
        if not 0 < value < move_count:
            invalid_moves.append({"species": current, "offset": offset, "move": value})
    if sentinel_offset is None:
        used = len(raw)
    else:
        used = sentinel_offset + 2
    return {
        "declared_bytes": len(raw),
        "used_bytes_through_sentinel": used,
        "free_trailing_bytes": len(raw) - used,
        "record_count": len(records),
        "move_entry_count": sum(len(values) for values in records.values()),
        "terminator_present": sentinel_offset is not None,
        "invalid_species_count": len(invalid_species),
        "invalid_species": invalid_species[:50],
        "invalid_move_count": len(invalid_moves),
        "invalid_moves": invalid_moves[:50],
        "records": records,
    }


def _scan_form_table(raw: bytes, species_count: int) -> dict[str, Any]:
    if len(raw) % 14:
        raise CapacityAuditError("form table is not a sequence of seven u16 values")
    invalid: list[dict[str, int]] = []
    decoded: list[dict[str, int]] = []
    for index in range(len(raw) // 14):
        canonical, base, level, egg, tm, wild, action = struct.unpack_from(
            "<7H", raw, index * 14
        )
        row = {
            "record": index,
            "canonical": canonical,
            "base": base,
            "level": level,
            "egg": egg,
            "tm": tm,
            "wild": wild,
            "action": action,
        }
        decoded.append(row)
        for field in ("canonical", "base", "level", "egg", "tm", "wild"):
            value = row[field]
            if value != 0xFFFF and value >= species_count:
                invalid.append({"record": index, "field": field, "value": value})
    return {
        "record_size_bytes": 14,
        "declared_records": len(raw) // 14,
        "used_records": len(decoded),
        "free_records": 0,
        "invalid_species_reference_count": len(invalid),
        "invalid_species_references": invalid[:50],
        "decoded": decoded,
    }


def _identity_surface(
    species_id: int,
    *,
    species_row: Mapping[str, str],
    base_stats: bytes,
    evolution: Mapping[int, Sequence[Mapping[str, int]]],
    level_up: Mapping[int, Sequence[Mapping[str, int]]],
    egg_moves: Mapping[int, Sequence[int]],
    tm_compatibility: bytes,
    tutor_compatibility: bytes,
    form_rows: Sequence[Mapping[str, int]],
) -> dict[str, Any]:
    stats = base_stats[species_id * 32 : (species_id + 1) * 32]
    tm = tm_compatibility[species_id * 16 : (species_id + 1) * 16]
    tutor = tutor_compatibility[species_id * 16 : (species_id + 1) * 16]
    form_mentions = [
        int(row["record"])
        for row in form_rows
        if species_id
        in {row["canonical"], row["base"], row["level"], row["egg"], row["tm"], row["wild"]}
    ]
    levels = list(level_up.get(species_id, []))
    eggs = list(egg_moves.get(species_id, []))
    evolutions = list(evolution.get(species_id, []))
    return {
        "manifest": {
            "species_key": species_row.get("species_key"),
            "id": species_id,
            "display_name": species_row.get("display_name"),
            "classification": species_row.get("classification"),
            "form_key": species_row.get("form_key"),
            "is_official": species_row.get("is_official"),
        },
        "rom": {
            "base_stats_sha256": _sha256(stats),
            "base_stats_nonzero_bytes": sum(value != 0 for value in stats),
            "evolution_entries": evolutions,
            "meaningful_level_up_moves": [row for row in levels if row["move"] != 0],
            "move_zero_level_rows": [row for row in levels if row["move"] == 0],
            "egg_move_record_present": species_id in egg_moves,
            "egg_moves": eggs,
            "tm_hm_compatibility_set_bits": sum(value.bit_count() for value in tm),
            "tutor_compatibility_reachable_set_bits": sum(
                value.bit_count() for value in tutor[:8]
            ),
            "tutor_compatibility_dormant_upper_set_bits": sum(
                value.bit_count() for value in tutor[8:]
            ),
            "form_table_record_mentions": form_mentions,
        },
    }


def build_modernization_capacity_audit(
    root: Path,
    *,
    baseline_path: str | Path = DEFAULT_BASELINE,
    allocation_path: str | Path = DEFAULT_ALLOCATION,
    save_layout_path: str | Path = DEFAULT_SAVE_LAYOUT,
    ram_layout_path: str | Path = DEFAULT_RAM_LAYOUT,
) -> dict[str, Any]:
    """決定的かつ読み取り専用のStage62容量監査reportを構築する。"""

    root = root.resolve()
    checks: list[dict[str, Any]] = []
    baseline = _json(root, baseline_path, "active play baseline")
    rom_contract = baseline.get("rom")
    if not isinstance(rom_contract, Mapping):
        raise CapacityAuditError("active play baseline has no ROM contract")
    rom_relative = str(rom_contract.get("path", ""))
    if not rom_relative:
        raise CapacityAuditError("active play baseline ROM path is empty")
    rom = _read(root, rom_relative, "active Stage ROM")
    actual_sha = _sha256(rom)
    actual_crc = f"{binascii.crc32(rom) & 0xFFFFFFFF:08X}"
    identity_ok = (
        len(rom) == _number(rom_contract.get("size"), "baseline ROM size")
        and actual_sha == str(rom_contract.get("sha256", "")).lower()
        and actual_crc == str(rom_contract.get("crc32", "")).upper()
        and baseline.get("policy") == "LATEST_EXPLICITLY_ADOPTED"
        and baseline.get("status") == "ACTIVE"
    )
    _check(checks, "active_play_baseline_exact_rom", identity_ok)

    metadata_relative = str(Path(rom_relative).with_suffix(".json"))
    metadata = _json(root, metadata_relative, "active Stage metadata")
    output_identity = metadata.get("output", {})
    metadata_ok = (
        metadata.get("status") == "PASS"
        and _number(metadata.get("stage"), "metadata stage")
        == _number(baseline.get("stage"), "baseline stage")
        and isinstance(output_identity, Mapping)
        and str(output_identity.get("sha256", "")).lower() == actual_sha
        and _number(output_identity.get("size"), "metadata output size") == len(rom)
        and str(output_identity.get("crc32", "")).upper() == actual_crc
    )
    _check(checks, "active_stage_metadata_owns_rom", metadata_ok)

    allocation = _json(root, allocation_path, "inherited allocation ledger")
    allocator_report = _audit_allocator(rom, allocation, checks)

    stage06 = _json(root, "build/stages/06_battle_core.json", "T06 metadata")
    stage07 = _json(root, "build/stages/07_species.json", "T07 metadata")
    stage09 = _json(root, "build/stages/09_species_surface.json", "T09 metadata")
    stage39 = _json(root, "build/stages/39_move_distribution_v4.json", "T22 metadata")
    hotfix_config = _json(root, "config/stage61_runtime_hotfix.json", "Stage61 hotfix contract")
    hotfix_tables = _json(
        root,
        "generated/runtime/stage61_runtime_hotfix_tables.json",
        "Stage61 hotfix tables",
    )

    species_rows = _csv(root, "manifests/species_ids.csv", "Species manifest")
    move_rows = _csv(root, "manifests/move_ids.csv", "Move manifest")
    ability_rows = _csv(root, "manifests/ability_ids.csv", "Ability manifest")
    item_rows = _csv(root, "manifests/item_ids.csv", "Item manifest")
    models = stage06.get("models", {})
    species_capacity = _number(stage07.get("base_stats", {}).get("count"), "Species count")
    move_capacity = _number(models.get("moves"), "Move count")
    ability_capacity = _number(models.get("abilities"), "Ability count")
    item_capacity = _number(models.get("items"), "Item count")
    id_spaces = {
        "species": _manifest_space(species_rows, "species_key", species_capacity),
        "move": _manifest_space(move_rows, "move_key", move_capacity),
        "ability": _manifest_space(ability_rows, "ability_key", ability_capacity),
        "item": _manifest_space(item_rows, "item_key", item_capacity),
    }
    form_manifest_count = sum(bool(row.get("form_key", "").strip()) for row in species_rows)
    id_spaces["form_species"] = {
        "shared_species_id_capacity": species_capacity,
        "manifest_form_rows": form_manifest_count,
        "non_form_rows": species_capacity - form_manifest_count,
        "free_species_id_slots": id_spaces["species"]["free_slots"],
        "separate_form_id_space": False,
    }
    for name in ("species", "move", "ability", "item"):
        row = id_spaces[name]
        _check(
            checks,
            f"{name}_manifest_matches_runtime_capacity",
            row["contiguous_zero_based"]
            and not row["duplicate_ids"]
            and not row["duplicate_keys"]
            and not row["out_of_range_ids"]
            and row["free_slots"] == 0,
        )

    runtime_tables = stage06.get("runtime_tables", {})
    if not isinstance(runtime_tables, Mapping):
        raise CapacityAuditError("T06 runtime_tables metadata is missing")
    table_reports: dict[str, Any] = {}
    for name in (
        "move_names",
        "move_data",
        "move_descriptions",
        "move_animations",
        "ability_names",
        "ability_descriptions",
        "item_data",
        "item_graphics",
    ):
        source = runtime_tables.get(name)
        if not isinstance(source, Mapping):
            raise CapacityAuditError(f"T06 runtime table is missing: {name}")
        table_reports[name] = _table(
            rom,
            address=_number(source.get("address"), f"{name} address"),
            size=_number(source.get("size"), f"{name} size"),
            count=_number(source.get("count"), f"{name} count"),
            stride=_number(source.get("stride"), f"{name} stride"),
            source_sha256=str(source.get("sha256", "")),
        )
        _check(checks, f"{name}_shape", bool(table_reports[name].get("shape_matches")))

    base = stage07.get("base_stats", {})
    if not isinstance(base, Mapping):
        raise CapacityAuditError("T07 BaseStats metadata is missing")
    base_address = _number(base.get("address"), "BaseStats address")
    base_size = _number(base.get("size"), "BaseStats size")
    base_raw = _span(rom, base_address, base_size, "BaseStats")
    table_reports["species_base_stats"] = _table(
        rom,
        address=base_address,
        size=base_size,
        count=species_capacity,
        stride=_number(base.get("stride"), "BaseStats stride"),
        source_sha256=str(base.get("sha256", "")),
    )
    _check(
        checks,
        "species_base_stats_shape",
        bool(table_reports["species_base_stats"].get("shape_matches")),
    )

    consumer_roots: dict[str, Any] = {}
    base_roots = _root_rows(rom, list(base.get("repoint_sites", [])), base_address)
    consumer_roots["species_base_stats"] = {
        "kind": "pointer_sites",
        "declared_count": len(base_roots),
        "matched_count": sum(row["matches"] for row in base_roots),
        "rows": base_roots,
    }
    _check(
        checks,
        "species_base_stats_consumers_rooted",
        bool(base_roots) and all(row["matches"] for row in base_roots),
    )

    move_root_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in stage06.get("t04_repoints", {}).get("rows", []):
        move_root_groups[str(row.get("table"))].append(row)
    for group, rows in sorted(move_root_groups.items()):
        root_rows: list[dict[str, Any]] = []
        for row in rows:
            offset = _number(row.get("rom_offset"), f"Move {group} root offset")
            expected = bytes.fromhex(str(row.get("after", "")))
            if len(expected) != 4:
                raise CapacityAuditError(f"Move {group} root is not four bytes")
            actual = rom[offset : offset + 4]
            root_rows.append(
                {
                    "site_offset": offset,
                    "site_address": _hex(ROM_BASE + offset),
                    "expected_hex": expected.hex(),
                    "actual_hex": actual.hex(),
                    "matches": actual == expected,
                }
            )
        consumer_roots[f"move_{group}"] = {
            "kind": "pointer_sites",
            "declared_count": len(root_rows),
            "matched_count": sum(row["matches"] for row in root_rows),
            "rows": root_rows,
        }
        _check(
            checks,
            f"move_{group}_consumers_rooted",
            bool(root_rows) and all(row["matches"] for row in root_rows),
        )

    primary_roots = {
        "ability_names": (0x080001C0, table_reports["ability_names"]["address"]),
        "ability_descriptions": (
            0x080001C4,
            table_reports["ability_descriptions"]["address"],
        ),
        "item_data": (0x080001C8, table_reports["item_data"]["address"]),
    }
    for name, (site, address) in primary_roots.items():
        rows = _root_rows(rom, [site], address, sites_are_addresses=True)
        consumer_roots[name] = {"kind": "primary_pointer", "rows": rows}
        _check(checks, f"{name}_primary_root", all(row["matches"] for row in rows))
    graphics_address = table_reports["item_graphics"]["address"]
    graphics_pointer = struct.pack("<I", graphics_address)
    graphics_sites: list[int] = []
    cursor = 0
    while True:
        cursor = rom.find(graphics_pointer, cursor)
        if cursor < 0:
            break
        graphics_sites.append(cursor)
        cursor += 1
    consumer_roots["item_graphics"] = {
        "kind": "compiled_or_pointer_literal_occurrences",
        "target": graphics_address,
        "target_hex": _hex(graphics_address),
        "occurrence_count": len(graphics_sites),
        "site_offsets": graphics_sites,
    }
    _check(checks, "item_graphics_has_consumers", bool(graphics_sites))

    allocation_entries = {
        str(row.get("name")): row for row in stage09.get("allocation", {}).get("entries", [])
    }
    evolution_entry = allocation_entries.get("evolutions")
    if not isinstance(evolution_entry, Mapping):
        raise CapacityAuditError("T09 evolution allocation is missing")
    evolution_address = _number(evolution_entry.get("address"), "evolution address")
    evolution_size = _number(evolution_entry.get("size"), "evolution size")
    evolution_raw = _span(rom, evolution_address, evolution_size, "evolution table")
    evolution_scan = _scan_evolutions(evolution_raw, species_capacity)
    evolution_roots_meta = stage09.get("repoints", {})
    evolution_sites = list(evolution_roots_meta.get("evolution", {}).get("sites", []))
    evolution_sites += list(
        evolution_roots_meta.get("evolution_runtime", {}).get("sites", [])
    )
    evolution_roots = _root_rows(rom, evolution_sites, evolution_address)
    consumer_roots["evolution"] = {
        "kind": "pointer_sites",
        "declared_count": len(evolution_roots),
        "matched_count": sum(row["matches"] for row in evolution_roots),
        "rows": evolution_roots,
    }
    _check(
        checks,
        "evolution_consumers_rooted",
        bool(evolution_roots) and all(row["matches"] for row in evolution_roots),
    )
    _check(
        checks,
        "evolution_references_in_range",
        evolution_scan["invalid_target_count"] == 0,
    )

    stage39_tables = stage39.get("runtime", {}).get("tables", {})
    if not isinstance(stage39_tables, Mapping):
        raise CapacityAuditError("Stage39 runtime table metadata is missing")
    level_pointer_meta = stage39_tables.get("level_up_pointers", {})
    level_data_meta = stage39_tables.get("level_up_data", {})
    level_pointer_address = _number(level_pointer_meta.get("address"), "level pointer address")
    level_data_address = _number(level_data_meta.get("address"), "level data address")
    level_scan = _scan_level_up(
        rom,
        pointer_address=level_pointer_address,
        pointer_count=species_capacity,
        data_address=level_data_address,
        data_size=_number(level_data_meta.get("size"), "level data size"),
        move_count=move_capacity,
    )
    _check(
        checks,
        "level_up_table_valid",
        level_scan["invalid_pointer_count"] == 0
        and level_scan["invalid_move_count"] == 0
        and level_scan["unterminated_list_count"] == 0,
    )
    binding_rows = {
        str(row.get("name")): row
        for row in stage39.get("consumer_bindings", {}).get("rows", [])
    }
    level_bindings = [
        binding_rows[name]
        for name in ("root::level_up", "root::level_up_runtime_literal")
        if name in binding_rows
    ]
    level_roots = _root_rows(
        rom,
        [_number(row.get("offset"), "level root offset") for row in level_bindings],
        level_pointer_address,
    )
    consumer_roots["level_up"] = {"kind": "pointer_sites", "rows": level_roots}
    _check(
        checks,
        "level_up_consumers_rooted",
        len(level_roots) == 2 and all(row["matches"] for row in level_roots),
    )

    egg_meta = stage39_tables.get("egg_moves", {})
    egg_address = _number(egg_meta.get("address"), "egg move address")
    egg_size = _number(egg_meta.get("size"), "egg move size")
    egg_raw = _span(rom, egg_address, egg_size, "egg move table")
    egg_scan = _scan_egg_moves(
        egg_raw, species_count=species_capacity, move_count=move_capacity
    )
    _check(
        checks,
        "egg_move_table_valid",
        egg_scan["terminator_present"]
        and egg_scan["invalid_species_count"] == 0
        and egg_scan["invalid_move_count"] == 0,
    )
    egg_binding = binding_rows.get("root::egg")
    if not isinstance(egg_binding, Mapping):
        raise CapacityAuditError("Stage39 egg consumer root is missing")
    egg_roots = _root_rows(
        rom, [_number(egg_binding.get("offset"), "egg root offset")], egg_address
    )
    consumer_roots["egg_moves"] = {"kind": "pointer_site", "rows": egg_roots}
    _check(checks, "egg_move_consumer_rooted", all(row["matches"] for row in egg_roots))

    form_meta = stage39_tables.get("form_table", {})
    form_address = _number(form_meta.get("address"), "form table address")
    form_size = _number(form_meta.get("size"), "form table size")
    form_raw = _span(rom, form_address, form_size, "form table")
    form_scan = _scan_form_table(form_raw, species_capacity)
    _check(
        checks,
        "form_table_valid",
        form_scan["invalid_species_reference_count"] == 0
        and form_scan["declared_records"]
        == _number(stage39.get("content", {}).get("form_rows"), "form row count"),
    )
    form_pointer = struct.pack("<I", form_address)
    payload = stage39.get("runtime", {}).get("payload", {})
    payload_offset = _number(payload.get("offset"), "Stage39 payload offset")
    payload_size = _number(payload.get("size"), "Stage39 payload size")
    form_sites: list[int] = []
    cursor = payload_offset
    payload_end = payload_offset + payload_size
    while True:
        cursor = rom.find(form_pointer, cursor, payload_end)
        if cursor < 0:
            break
        form_sites.append(cursor)
        cursor += 1
    consumer_roots["form_resolution"] = {
        "kind": "compiled_literal_in_stage39_payload",
        "target": form_address,
        "target_hex": _hex(form_address),
        "occurrence_count": len(form_sites),
        "site_offsets": form_sites,
    }
    _check(checks, "form_consumer_has_compiled_root", bool(form_sites))

    hotfix_addresses = hotfix_tables.get("addresses", {})
    tm_catalog_address = _number(hotfix_addresses.get("tmhm"), "TM/HM catalog address")
    tutor_catalog_address = _number(hotfix_addresses.get("tutor"), "tutor catalog address")
    tm_compat_address = _number(
        hotfix_addresses.get("compatibility"), "TM/HM compatibility address"
    )
    tm_rows = list(hotfix_tables.get("tm", []))
    hm_rows = list(hotfix_tables.get("hm", []))
    tutor_rows = list(hotfix_tables.get("tutor", []))
    tm_catalog = _span(
        rom, tm_catalog_address, (len(tm_rows) + len(hm_rows)) * 2, "TM/HM move catalog"
    )
    tutor_catalog = _span(
        rom, tutor_catalog_address, len(tutor_rows) * 2, "tutor move catalog"
    )
    tm_values = list(struct.unpack(f"<{len(tm_rows) + len(hm_rows)}H", tm_catalog))
    tutor_values = list(struct.unpack(f"<{len(tutor_rows)}H", tutor_catalog))
    expected_tm_values = [_number(row.get("move_id"), "TM move") for row in tm_rows]
    expected_tm_values += [_number(row.get("move_id"), "HM move") for row in hm_rows]
    expected_tutor_values = [_number(row.get("move_id"), "tutor move") for row in tutor_rows]
    _check(
        checks,
        "tm_hm_catalog_matches_declared_slots",
        len(tm_rows) == 120
        and len(hm_rows) == 8
        and tm_values == expected_tm_values
        and all(0 < value < move_capacity for value in tm_values),
    )
    _check(
        checks,
        "tutor_catalog_matches_declared_slots",
        len(tutor_rows) == 64
        and tutor_values == expected_tutor_values
        and all(0 < value < move_capacity for value in tutor_values),
    )
    compatibility_stride = _number(
        hotfix_config.get("rom_contract", {}).get("compatibility_stride"),
        "compatibility stride",
    )
    tm_compatibility = _span(
        rom,
        tm_compat_address,
        species_capacity * compatibility_stride,
        "TM/HM compatibility",
    )
    tutor_compat_meta = stage39_tables.get("tutor", {})
    tutor_compat_address = _number(
        tutor_compat_meta.get("address"), "tutor compatibility address"
    )
    tutor_compatibility = _span(
        rom,
        tutor_compat_address,
        species_capacity * compatibility_stride,
        "tutor compatibility",
    )
    hotfix_contract = hotfix_config.get("rom_contract", {})
    hotfix_roots = {
        "tm_hm_compatibility": (
            _number(hotfix_contract.get("stage61_tmhm_root_site"), "TM/HM root site"),
            tm_compat_address,
        ),
        "tm_hm_move_catalog": (
            _number(hotfix_contract.get("tmhm_moves_root_site"), "TM move root site"),
            tm_catalog_address,
        ),
        "tutor_move_catalog": (
            _number(hotfix_contract.get("tutor_moves_root_site"), "tutor move root site"),
            tutor_catalog_address,
        ),
    }
    for name, (site, target) in hotfix_roots.items():
        rows = _root_rows(rom, [site], target, sites_are_addresses=True)
        consumer_roots[name] = {"kind": "pointer_site", "rows": rows}
        _check(checks, f"{name}_rooted", all(row["matches"] for row in rows))
    tutor_binding = binding_rows.get("root::tutor")
    if not isinstance(tutor_binding, Mapping):
        raise CapacityAuditError("Stage39 tutor compatibility root is missing")
    tutor_roots = _root_rows(
        rom,
        [_number(tutor_binding.get("offset"), "tutor compatibility root")],
        tutor_compat_address,
    )
    consumer_roots["tutor_compatibility"] = {
        "kind": "compiled_literal",
        "rows": tutor_roots,
    }
    _check(
        checks,
        "tutor_compatibility_rooted",
        all(row["matches"] for row in tutor_roots),
    )

    tm_set_bits = sum(value.bit_count() for value in tm_compatibility)
    tutor_reachable_bits = sum(
        value.bit_count()
        for species in range(species_capacity)
        for value in tutor_compatibility[species * 16 : species * 16 + 8]
    )
    tutor_dormant_bits = sum(
        value.bit_count()
        for species in range(species_capacity)
        for value in tutor_compatibility[species * 16 + 8 : (species + 1) * 16]
    )

    save_rows = _csv(root, save_layout_path, "save ownership layout")
    ram_rows = _csv(root, ram_layout_path, "RAM ownership layout")
    save_spaces, save_errors = _audit_intervals(save_rows, SAVE_SPACE_CONTRACTS)
    ram_spaces, ram_errors = _audit_intervals(ram_rows, RAM_SPACE_CONTRACTS)
    _check(checks, "save_layout_live_ranges_valid", not save_errors, errors=save_errors)
    _check(checks, "ram_layout_live_ranges_valid", not ram_errors, errors=ram_errors)
    save_by_symbol = {str(row.get("symbol")): row for row in save_rows}
    reserved_save_bytes = sum(
        _number(row.get("size"), "reserved save size")
        for row in save_rows
        if row.get("status") == "LIVE" and "RESERVED" in str(row.get("owner", ""))
    )
    dex_symbols = (
        "seen_primary_412",
        "seen_secondary_412",
        "owned_412",
        "seen_save2_412",
    )
    dex_bitmaps = []
    for symbol in dex_symbols:
        row = save_by_symbol.get(symbol)
        if not isinstance(row, Mapping):
            raise CapacityAuditError(f"save layout is missing {symbol}")
        size = _number(row.get("size"), f"{symbol} size")
        dex_bitmaps.append(
            {
                "symbol": symbol,
                "size_bytes": size,
                "storage_bits": size * 8,
                "semantic_species_ids": 412,
                "padding_bits": size * 8 - 412,
            }
        )
    item_flags = save_by_symbol.get("itemObtainedFlags_999")
    if not isinstance(item_flags, Mapping):
        raise CapacityAuditError("save layout is missing itemObtainedFlags_999")
    item_flag_bytes = _number(item_flags.get("size"), "item flag size")
    _check(
        checks,
        "save_bitsets_match_current_contracts",
        all(row["storage_bits"] == 416 and row["padding_bits"] == 4 for row in dex_bitmaps)
        and item_flag_bytes * 8 == 1000
        and item_capacity == 999,
    )

    species_by_key = {str(row.get("species_key")): row for row in species_rows}
    caterpie = species_by_key.get("SPECIES_KEY_CATERPIE")
    egg = species_by_key.get("SPECIES_KEY_EGG")
    if not isinstance(caterpie, Mapping) or not isinstance(egg, Mapping):
        raise CapacityAuditError("Caterpie/Egg keys are missing from Species manifest")
    caterpie_id = _number(caterpie.get("id"), "Caterpie id")
    egg_id = _number(egg.get("id"), "Egg id")
    caterpie_surface = _identity_surface(
        caterpie_id,
        species_row=caterpie,
        base_stats=base_raw,
        evolution=evolution_scan["decoded"],
        level_up=level_scan["decoded"],
        egg_moves=egg_scan["records"],
        tm_compatibility=tm_compatibility,
        tutor_compatibility=tutor_compatibility,
        form_rows=form_scan["decoded"],
    )
    egg_surface = _identity_surface(
        egg_id,
        species_row=egg,
        base_stats=base_raw,
        evolution=evolution_scan["decoded"],
        level_up=level_scan["decoded"],
        egg_moves=egg_scan["records"],
        tm_compatibility=tm_compatibility,
        tutor_compatibility=tutor_compatibility,
        form_rows=form_scan["decoded"],
    )
    identity_separated = (
        caterpie_id == 649
        and egg_id == 412
        and caterpie_id != egg_id
        and bool(caterpie_surface["rom"]["meaningful_level_up_moves"])
        and bool(caterpie_surface["rom"]["evolution_entries"])
        and not egg_surface["rom"]["evolution_entries"]
        and not egg_surface["rom"]["egg_move_record_present"]
    )
    _check(
        checks,
        "caterpie_and_internal_egg_rom_surfaces_are_distinguished",
        identity_separated,
        caterpie_id=caterpie_id,
        egg_id=egg_id,
    )

    # identity証跡の抽出後、decoder専用の大きなfieldは公開reportから除外する。
    evolution_scan.pop("decoded")
    level_scan.pop("pointers")
    level_scan.pop("decoded")
    egg_scan.pop("records")
    form_scan.pop("decoded")

    logical_capacity = {
        "id_spaces": id_spaces,
        "evolution": evolution_scan,
        "level_up": level_scan,
        "egg_moves": egg_scan,
        "tm_hm": {
            "tm_slots": 120,
            "hm_slots": 8,
            "declared_catalog_slots": 128,
            "used_catalog_slots": len(tm_values),
            "free_catalog_slots": 128 - len(tm_values),
            "compatibility_species_rows": species_capacity,
            "compatibility_bits_per_species": compatibility_stride * 8,
            "compatibility_set_bits": tm_set_bits,
            "catalog_address": tm_catalog_address,
            "compatibility_address": tm_compat_address,
        },
        "tutor": {
            "runtime_slot_cap": 64,
            "used_catalog_slots": len(tutor_values),
            "free_catalog_slots": 64 - len(tutor_values),
            "physical_compatibility_bits_per_species": compatibility_stride * 8,
            "runtime_reachable_bits_per_species": 64,
            "dormant_upper_bits_per_species": 64,
            "reachable_set_bits": tutor_reachable_bits,
            "dormant_upper_set_bits": tutor_dormant_bits,
            "dormant_bits_are_not_free_without_runtime_change": True,
            "catalog_address": tutor_catalog_address,
            "compatibility_address": tutor_compat_address,
        },
        "form_resolution": form_scan,
    }
    save_report = {
        "spaces": save_spaces,
        "explicit_reserved_bytes": reserved_save_bytes,
        "legacy_dex_bitmaps": dex_bitmaps,
        "item_obtained_bitmap": {
            "size_bytes": item_flag_bytes,
            "storage_bits": item_flag_bytes * 8,
            "semantic_item_ids": item_capacity,
            "padding_bits": item_flag_bytes * 8 - item_capacity,
        },
        "legacy_dex_scope": {
            "representable_species_ids": [0, 411],
            "caterpie_id": caterpie_id,
            "egg_id": egg_id,
            "caterpie_is_outside_legacy_dex_bitmap": caterpie_id >= 412,
            "egg_is_outside_legacy_dex_bitmap": egg_id >= 412,
            "intentional_modern_collection_owner_required": True,
        },
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "task": "USER-MODERNIZATION-P01",
        "audit_kind": "READ_ONLY_EXACT_ROM_CAPACITY_AND_CONSUMER_ROOTS",
        "status": _checks_status(checks),
        "input_identity": {
            "baseline_path": str(baseline_path),
            "policy": baseline.get("policy"),
            "stage": baseline.get("stage"),
            "label": baseline.get("label"),
            "rom": {
                "path": rom_relative,
                "size": len(rom),
                "sha256": actual_sha,
                "crc32": actual_crc,
            },
            "metadata_path": metadata_relative,
            "allocation_path": str(allocation_path),
            "allocation_is_inherited_from_stage61": True,
        },
        "physical_rom_capacity": allocator_report,
        "logical_capacity": logical_capacity,
        "runtime_tables": table_reports,
        "consumer_roots": consumer_roots,
        "save_layout": save_report,
        "ram_layout": {"spaces": ram_spaces},
        "caterpie_egg_rom_identity": {
            "status": "PASS" if identity_separated else "FAIL",
            "interpretation": (
                "ROM上に残る各table rowの有無とspecies identityは別概念。"
                "Caterpie 649のplayable consumerと内部Egg 412を個別に記録する。"
            ),
            "caterpie": caterpie_surface,
            "internal_egg": egg_surface,
        },
        "findings": {
            "confirmed": [
                "ROM allocatorの宣言空きと実ROMの消去状態を別々に測定した",
                "Species/Move/Ability/Itemの現行ID表は各runtime capacityを使い切っている",
                "進化tableは固定16 slot/speciesで未使用entryを持つ",
                "TM120+HM8と教え技64のcatalog slotは埋まっている",
            ],
            "intentional_or_reserved": [
                "legacy Pokédex bitmapはSpecies 0..411だけを表す",
                "Egg 412は内部SpeciesでありCaterpie 649とは別identity",
                "save/RAMのuntracked bytesは安全な空きとして扱わない",
                "tutor compatibility上位64 bitは現runtimeから到達不能で空き扱いしない",
            ],
        },
        "checks": checks,
    }
    return report


def require_pass(report: Mapping[str, Any]) -> None:
    """完全一致ROMのcheckを1件でも証明できなければfail-closedにする。"""

    if report.get("status") != "PASS":
        failed = [
            str(row.get("name"))
            for row in report.get("checks", [])
            if not bool(row.get("passed"))
        ]
        raise CapacityAuditError(f"capacity audit failed: {failed}")
