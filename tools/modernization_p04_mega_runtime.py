#!/usr/bin/env python3
"""P04追加Mega 49形態を既存CFRU-JP Mega runtimeへ安全に接続する。

Stage71はMega engineをforkしない。Stage70が移設した1670行の進化表へ、
通常Megaの順方向49行とbattle終了時revert用の逆方向49行だけを追加する。
固定source、stable key、slot容量、親ROM preimage、変更allowlistをすべて
fail-closedで検証する。
"""

from __future__ import annotations

import csv
import copy
import hashlib
import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P04-MEGA-RUNTIME-STAGE71"
STAGE = 71
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
EVO_NONE = 0
EVO_MEGA = 0xFE
MEGA_VARIANT_STANDARD = 0
SPECIES_NONE = 0
OLD_SPECIES_COUNT = 1621
NEW_SPECIES_COUNT = 1670
NEW_FIRST = 1621
NEW_LAST = 1669
EVOS_PER_MON = 16
ENTRY_STRIDE = 8
ROW_STRIDE = 128
FORWARD_COUNT = 49
REVERSE_COUNT = 49
EXISTING_MEGA_ENTRY_COUNT = 80
REQUIRED_ABILITY_TABLE_COUNT = 318
STAGE70_ALLOCATION_SEQUENCE = 73
STAGE70_ALLOCATION_NAME = "modernization_p04_species_runtime_stage70_payload"
STAGE70_ALLOCATION_OWNER = "USER-MODERNIZATION-P04-SPECIES-RUNTIME-STAGE70"
DEFAULT_CONFIG = Path("config/modernization_p04_mega_runtime.json")


class ModernizationP04MegaRuntimeError(ValueError):
    """Stage71 contract、preimage、mapping、table容量の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP04MegaRuntimeError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _as_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}がboolです")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            _fail(f"{label}が整数ではありません: {value!r}")
    _fail(f"{label}が整数ではありません: {value!r}")


def _rom_offset(address: int, label: str) -> int:
    if not ROM_BASE <= address < ROM_BASE + ROM_SIZE:
        _fail(f"{label}が32MiB ROM範囲外です: 0x{address:08X}")
    return address - ROM_BASE


def _read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"Stage71 configが通常fileではありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"Stage71 configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("Stage71 config rootがobjectではありません")
    _validate_config(value)
    return value


def _validate_config(config: Mapping[str, Any]) -> None:
    if (config.get("schema_version"), config.get("task"), config.get("stage")) != (
        SCHEMA_VERSION,
        TASK,
        STAGE,
    ):
        _fail("Stage71 config schema/task/stage不一致")
    if config.get("status") not in {
        "WAITING_STAGE70_IDENTITY",
        "STAGE70_IDENTITY_PINNED",
    }:
        _fail("Stage71 config status不一致")
    abi = config.get("fixed_cfru_jp", {}).get("evolution_abi")
    expected = {
        "method": EVO_MEGA,
        "standard_variant": MEGA_VARIANT_STANDARD,
        "slots_per_species": EVOS_PER_MON,
        "entry_stride": ENTRY_STRIDE,
        "row_stride": ROW_STRIDE,
        "old_count": OLD_SPECIES_COUNT,
        "new_count": NEW_SPECIES_COUNT,
        "capacity_baseline_address": "0x09F79F38",
        "capacity_baseline_sha256":
            "3fc4c8cd5d21c5b7f1fa2972223288ec1040f115321298a19e168694ee45e002",
    }
    if abi != expected:
        _fail("固定CFRU-JP evolution ABIが不正です")
    policy = config.get("runtime_policy")
    if not isinstance(policy, dict) or (
        policy.get("required_keystone_item_id") != 580
        or policy.get("forward_rows") != FORWARD_COUNT
        or policy.get("reverse_rows") != REVERSE_COUNT
        or policy.get("new_ability_table_count_required")
        != REQUIRED_ABILITY_TABLE_COUNT
        or policy.get("new_ability_effect_hooks") != "PENDING_STAGE72"
        or policy.get("release_candidate") is not False
    ):
        _fail("Stage71 runtime/release境界が不正です")
    if (
        policy.get("switch") != "KEEP_MEGA_WITHIN_SAME_BATTLE"
        or policy.get("faint")
        != "REVERT_BASE_VIA_TRY_FORM_REVERT_KEEP_MEGA_DATA_DONE"
    ):
        _fail("Stage71 switch/faint lifecycle契約が不正です")
    if policy.get("gate_order") != [
        "PROJECT_VEGA_BATTLE_POLICY_CAN_MEGA",
        "UPSTREAM_MODE_KEYSTONE_GATE",
        "EVOLUTION_ROW_EXACT_STONE",
        "PROJECT_AND_UPSTREAM_USAGE_MARKS",
    ]:
        _fail("Stage71 Mega gate順序契約が不正です")
    if policy.get("keystone_by_mode_after_project_policy") != {
        "normal_owned": True,
        "normal_unowned": False,
        "frontier": True,
        "link": True,
    }:
        _fail("Stage71 mode別keystone契約が不正です")
    if policy.get("project_policy") != {
        "field_pending_standard_mode": "MEGA_DENIED",
        "configured_mega_mode": "MEGA_ELIGIBLE_SUBJECT_TO_REMAINING_GATES",
        "usage_scope": "SIDE_BASED_PROJECT_MARK_PRECEDES_UPSTREAM_MODE_EXCEPTIONS",
    }:
        _fail("Stage71 project battle policy契約が不正です")
    if policy.get("upstream_usage_by_mode") != {
        "normal_double_same_owner": "BANK_OR_PARTNER_DONE_REJECTS_SECOND",
        "ingame_partner_or_two_opponents": "EACH_OWNER_BANK_DONE_ONLY",
        "mega_brawl": "UPSTREAM_DOES_NOT_SET_DONE_OR_PARTNER_DONE",
    }:
        _fail("Stage71 upstream usage mode契約が不正です")
    if policy.get("compiled_project_usage") != {
        "normal": "SIDE_USED_MARK_REJECTS_SECOND",
        "mega_brawl":
            "PROJECT_SIDE_USED_GATE_PRECEDES_UPSTREAM_EXCEPTION_EXACT_RUNTIME_PENDING_MGBA",
    }:
        _fail("Stage71 compiled project usage契約が不正です")
    allocation = config.get("allocation_policy")
    if allocation != {
        "new_allocation_count": 0,
        "target_sequence": STAGE70_ALLOCATION_SEQUENCE,
        "target_name": STAGE70_ALLOCATION_NAME,
        "target_owner": STAGE70_ALLOCATION_OWNER,
        "target_mutation": "CONTENT_SHA256_ONLY_FOR_STAGE71_FULL_SLICE",
        "non_target_allocations": "PRESERVE_LEDGER_ROWS_AND_ROM_SLICES_EXACT",
        "required_overlap_count": 0,
    }:
        _fail("Stage71 allocation更新契約が不正です")


def _fixed_raw(
    root: Path,
    contract: Mapping[str, Any],
    label: str,
    *,
    allow_pending: bool = False,
) -> bytes | None:
    expected = contract.get("sha256")
    if expected == "PENDING_STAGE70_IDENTITY" and allow_pending:
        return None
    if not isinstance(expected, str) or len(expected) != 64:
        _fail(f"{label} SHA-256 pinが未確定です")
    relative = contract.get("path")
    if not isinstance(relative, str) or not relative:
        _fail(f"{label} pathが不正です")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常fileではありません: {path}")
    raw = path.read_bytes()
    size = contract.get("size")
    if size is not None and len(raw) != _as_int(size, f"{label}.size"):
        _fail(f"{label} size不一致: {len(raw)} != {size}")
    actual = sha256(raw)
    if actual != expected:
        _fail(f"{label} SHA-256不一致: {actual} != {expected}")
    return raw


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail(f"{label}がJSON objectではありません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _csv_id_map(raw: bytes, key_field: str, label: str) -> dict[str, int]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as error:
        _fail(f"{label}をUTF-8 decodeできません: {error}")
    rows = list(csv.DictReader(text.splitlines()))
    result: dict[str, int] = {}
    used: dict[int, str] = {}
    for row in rows:
        key = row.get(key_field)
        raw_id = row.get("id")
        if not key or raw_id is None:
            _fail(f"{label} key/id欠落")
        try:
            numeric = int(raw_id)
        except ValueError:
            _fail(f"{label} ID不正: {key}={raw_id}")
        if key in result or numeric in used:
            _fail(f"{label} key/ID重複: {key}={numeric}")
        result[key] = numeric
        used[numeric] = key
    return result


def _parse_offsets(raw: bytes) -> dict[str, int]:
    result: dict[str, int] = {}
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as error:
        _fail(f"offsets.iniをASCII decodeできません: {error}")
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value and all(char in "0123456789ABCDEFabcdef" for char in value):
            result[key.strip()] = int(value, 16)
    return result


def _audit_source_lock(root: Path, expected_commit: str) -> dict[str, Any]:
    path = root / "state/source-lock.json"
    if path.is_symlink() or not path.is_file():
        _fail("state/source-lock.jsonがありません")
    lock = _json(path.read_bytes(), "source-lock")
    rows = lock.get("sources")
    if not isinstance(rows, list):
        _fail("source-lock sourcesが不正です")
    matches = [row for row in rows if isinstance(row, dict) and row.get("name") == "cfru"]
    if len(matches) != 1:
        _fail("source-lock CFRU行が一意ではありません")
    row = matches[0]
    if (
        row.get("configured_commit") != expected_commit
        or row.get("actual_commit") != expected_commit
        or row.get("configured_commit_verified") is not True
    ):
        _fail("固定CFRU-JP commitがsource-lockと不一致です")
    return {
        "path": "state/source-lock.json",
        "commit": expected_commit,
        "configured_commit_verified": True,
    }


def audit_fixed_cfru(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    section = config["fixed_cfru_jp"]
    commit = section.get("commit")
    if not isinstance(commit, str) or len(commit) != 40:
        _fail("固定CFRU-JP commit pinが不正です")
    source_lock = _audit_source_lock(root, commit)
    inputs = config["inputs"]
    run1 = _fixed_raw(root, inputs["battle_core_offsets_run1"], "offsets run1")
    run2 = _fixed_raw(root, inputs["battle_core_offsets_run2"], "offsets run2")
    assert run1 is not None and run2 is not None
    if run1 != run2:
        _fail("独立battle-core buildのoffsets.iniが不一致です")
    symbols = _parse_offsets(run1)
    expected_symbols = section.get("symbols")
    if not isinstance(expected_symbols, dict):
        _fail("fixed symbol契約がありません")
    for name, expected in expected_symbols.items():
        if symbols.get(name) != _as_int(expected, f"symbol.{name}"):
            _fail(f"固定symbol不一致: {name}")

    source_evidence: list[dict[str, Any]] = []
    for group_name in (
        "sources", "compiled_integration_sources", "battle_snapshot_sources"
    ):
        rows = section.get(group_name)
        if not isinstance(rows, list):
            _fail(f"{group_name}がlistではありません")
        for row in rows:
            if not isinstance(row, dict):
                _fail(f"{group_name} rowがobjectではありません")
            contract = {"path": row.get("path"), "sha256": row.get("sha256")}
            raw = _fixed_raw(root, contract, f"source {row.get('path')}")
            assert raw is not None
            try:
                text = raw.decode("utf-8")
            except UnicodeError as error:
                _fail(f"sourceをUTF-8 decodeできません: {error}")
            anchors = row.get("required_anchors")
            if not isinstance(anchors, list) or not anchors:
                _fail(f"source anchor契約欠落: {row.get('path')}")
            missing = [anchor for anchor in anchors if not isinstance(anchor, str) or anchor not in text]
            if missing:
                _fail(f"source anchor欠落: {row.get('path')}: {missing}")
            evidence = {
                "path": row["path"],
                "sha256": sha256(raw),
                "anchor_count": len(anchors),
                "status": "PASS",
            }
            if "owner" in row:
                evidence["owner"] = row["owner"]
            source_evidence.append(evidence)
    return {
        "status": "PASS",
        "source_lock": source_lock,
        "offsets": {
            "independent_runs_equal": True,
            "sha256": sha256(run1),
            "symbols": {key: f"0x{symbols[key]:08X}" for key in expected_symbols},
        },
        "sources": source_evidence,
        "semantics": {
            "gate_order": [
                "VegaBattlePolicyCanMega",
                "MegaEvolutionEnabled/FindBankKeystone",
                "CanMegaEvolve exact held-item row",
                "VegaBattlePolicyMarkMega plus CFRU megaData.done",
            ],
            "project_policy_owner": "VegaBattlePolicyCanMega/VegaBattlePolicyMarkMega",
            "keystone_owner": "MegaEvolutionEnabled/FindBankKeystone after project policy",
            "keystone_modes": {
                "normal_owned": True,
                "normal_unowned": False,
                "frontier": True,
                "link": True,
            },
            "held_item_exact_match_owner": "CanMegaEvolve",
            "usage_owners": "project side-used gate then BankMegaEvolved/mode-specific marking",
            "normal_double_same_owner": "bank or partner done rejects second",
            "ingame_partner": "each owner checks own bank done",
            "mega_brawl_upstream": "does not mark bank/partner done",
            "mega_brawl_compiled_project_gate": "SIDE_USED_GATE_PRESENT_EXACT_MGBA_PENDING",
            "form_change_owner": "DoMegaEvolution -> DoFormChange",
            "normal_battle_cleanup_owner": "EndOfBattleThings -> MegaRevert",
            "snapshot_cleanup_owners": [
                "CODEX_BATTLE_RUNTIME",
                "MIRAGE_PRODUCTION",
                "FACTORY_HIGH_MODES_V2",
            ],
            "switch": "INTENTIONALLY_RETAIN_MEGA_WITHIN_SAME_BATTLE",
            "faint": "TryFormRevert restores backupSpecies; megaData.done remains set",
            "revive_after_faint": "BankMegaEvolved remains true; second Mega is rejected",
        },
    }


def _reservation_rows(
    capacity: Mapping[str, Any], group: str, expected_count: int
) -> list[dict[str, Any]]:
    groups = capacity.get("id_reservations")
    if not isinstance(groups, dict) or not isinstance(groups.get(group), dict):
        _fail(f"capacity reservation欠落: {group}")
    rows = groups[group].get("rows")
    if not isinstance(rows, list) or len(rows) != expected_count:
        _fail(f"capacity reservation row数不一致: {group}")
    if not all(isinstance(row, dict) for row in rows):
        _fail(f"capacity reservation row型不正: {group}")
    return rows


def derive_mappings(root: Path, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    inputs = config["inputs"]
    candidate_raw = _fixed_raw(root, inputs["candidate_manifest"], "P04 candidate")
    capacity_raw = _fixed_raw(root, inputs["capacity_manifest"], "P04 capacity")
    species_raw = _fixed_raw(root, inputs["species_manifest"], "species manifest")
    item_raw = _fixed_raw(root, inputs["item_manifest"], "item manifest")
    ability_raw = _fixed_raw(root, inputs["ability_manifest"], "ability manifest")
    assert all(raw is not None for raw in (candidate_raw, capacity_raw, species_raw, item_raw, ability_raw))
    candidate = _json(candidate_raw, "P04 candidate")  # type: ignore[arg-type]
    capacity = _json(capacity_raw, "P04 capacity")  # type: ignore[arg-type]
    species_ids = _csv_id_map(species_raw, "species_key", "species manifest")  # type: ignore[arg-type]
    item_ids = _csv_id_map(item_raw, "item_key", "item manifest")  # type: ignore[arg-type]
    ability_ids = _csv_id_map(ability_raw, "ability_key", "ability manifest")  # type: ignore[arg-type]

    records = candidate.get("records")
    if not isinstance(records, list):
        _fail("P04 candidate recordsがlistではありません")
    adopted = {
        row.get("record_key"): row
        for row in records
        if isinstance(row, dict) and row.get("implementation_scope") == "ADOPT_CANDIDATE"
    }
    if len(adopted) != FORWARD_COUNT or None in adopted:
        _fail(f"P04 adopted Mega集合が49件ではありません: {len(adopted)}")
    forbidden = {"P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA"}
    if forbidden & set(adopted):
        _fail("非採用Browt/Pombon/GecquaがMega集合へ混入しています")

    species_rows = _reservation_rows(capacity, "species_form", FORWARD_COUNT)
    item_rows = _reservation_rows(capacity, "item", 45)
    ability_rows = _reservation_rows(capacity, "ability", 6)
    target_by_record = {row.get("source_record_key"): row for row in species_rows}
    stone_by_key = {row.get("item_key"): row for row in item_rows}
    new_ability_by_key = {row.get("ability_key"): int(row.get("id", -1)) for row in ability_rows}
    if len(target_by_record) != FORWARD_COUNT or len(stone_by_key) != 45:
        _fail("P04 species/item stable key reservationが一意ではありません")
    if [int(row.get("id", -1)) for row in species_rows] != list(range(NEW_FIRST, NEW_LAST + 1)):
        _fail("P04 Mega target IDが1621..1669連続範囲ではありません")
    if [int(row.get("id", -1)) for row in item_rows] != list(range(999, 1044)):
        _fail("P04 Mega Stone IDが999..1043連続範囲ではありません")

    if item_ids.get(config["runtime_policy"]["required_keystone_item_key"]) != 580:
        _fail("Mega Ring stable keyが固定ID 580ではありません")

    mappings: list[dict[str, Any]] = []
    for record_key, record in adopted.items():
        reservation = target_by_record.get(record_key)
        if not isinstance(reservation, dict):
            _fail(f"Mega species reservation欠落: {record_key}")
        for field in (
            "source_species_key", "proposed_species_key", "mega_stone_key", "ability_key"
        ):
            reserved_field = "species_key" if field == "proposed_species_key" else field
            if reservation.get(reserved_field) != record.get(field):
                _fail(f"candidate/capacity stable key不一致: {record_key}.{field}")
        source_key = record.get("source_species_key")
        target_key = record.get("proposed_species_key")
        stone_key = record.get("mega_stone_key")
        ability_key = record.get("ability_key")
        if source_key not in species_ids:
            _fail(f"base Species stable key未解決: {record_key}: {source_key}")
        stone = stone_by_key.get(stone_key)
        if not isinstance(stone, dict) or record_key not in stone.get("subject_record_keys", []):
            _fail(f"Mega Stone stable key/subject未解決: {record_key}: {stone_key}")
        if ability_key in new_ability_by_key:
            ability_id = new_ability_by_key[ability_key]
            ability_runtime = "SAFE_INDEXED_TABLES_STAGE70_EFFECT_PENDING_STAGE72"
        elif ability_key in ability_ids:
            ability_id = ability_ids[ability_key]
            ability_runtime = "EXISTING_CFRU_EFFECT"
        else:
            _fail(f"Ability stable key未解決: {record_key}: {ability_key}")
        mappings.append(
            {
                "record_key": record_key,
                "source_species_key": source_key,
                "source_species_id": species_ids[source_key],
                "target_species_key": target_key,
                "target_species_id": int(reservation["id"]),
                "mega_stone_key": stone_key,
                "mega_stone_id": int(stone["id"]),
                "ability_key": ability_key,
                "ability_id": ability_id,
                "ability_runtime": ability_runtime,
                "forward_entry": [EVO_MEGA, int(stone["id"]), int(reservation["id"]), MEGA_VARIANT_STANDARD],
                "reverse_entry": [EVO_MEGA, 0, species_ids[source_key], MEGA_VARIANT_STANDARD],
            }
        )
    mappings.sort(key=lambda row: row["target_species_id"])

    pairs = [(row["source_species_id"], row["mega_stone_id"]) for row in mappings]
    if len(set(pairs)) != FORWARD_COUNT:
        _fail("base Species+Mega Stone pairが一意ではありません")
    target_ids = [row["target_species_id"] for row in mappings]
    if target_ids != list(range(NEW_FIRST, NEW_LAST + 1)):
        _fail("Mega mapping target順がstable ID順ではありません")
    source_counts = Counter(row["source_species_id"] for row in mappings)
    if {key: count for key, count in source_counts.items() if count > 1} != {26: 2}:
        _fail("Raichu X/Y以外でbase Species IDが曖昧です")

    by_record = {row["record_key"]: row for row in mappings}
    expected_special = {
        "P04_MEGA_RAICHU_X": (26, 1656, 1032),
        "P04_MEGA_RAICHU_Y": (26, 1657, 1033),
        "P04_MEGA_MEOWSTIC_M": (967, 1654, 1030),
        "P04_MEGA_MEOWSTIC_F": (1013, 1653, 1030),
        "P04_MEGA_MAGEARNA": (1199, 1649, 1027),
        "P04_MEGA_MAGEARNA_ORIGINAL": (1254, 1650, 1027),
        "P04_MEGA_TATSUGIRI_CURLY": (1553, 1664, 1040),
        "P04_MEGA_TATSUGIRI_DROOPY": (1554, 1665, 1040),
        "P04_MEGA_TATSUGIRI_STRETCHY": (1555, 1666, 1040),
        "P04_MEGA_FLOETTE_ETERNAL": (1029, 1639, 1017),
    }
    for record_key, expected in expected_special.items():
        row = by_record.get(record_key)
        actual = None if row is None else (
            row["source_species_id"], row["target_species_id"], row["mega_stone_id"]
        )
        if actual != expected:
            _fail(f"特殊form mapping誤結合: {record_key}: {actual} != {expected}")
    return mappings


def _entries(rom: bytes, root_offset: int, species: int) -> list[tuple[int, int, int, int]]:
    start = root_offset + species * ROW_STRIDE
    end = start + ROW_STRIDE
    if start < 0 or end > len(rom):
        _fail(f"evolution rowがROM範囲外です: species={species}")
    return [struct.unpack_from("<HHHH", rom, start + slot * ENTRY_STRIDE) for slot in range(EVOS_PER_MON)]


def _used_slots(entries: Sequence[tuple[int, int, int, int]], species: int) -> int:
    first_zero = EVOS_PER_MON
    for index, entry in enumerate(entries):
        # 固定CFRUはmethodだけをEVO_NONE判定に使う。Vega旧表には
        # method=0だがparam等に残値がある未使用slotもあるため、全byte zeroを
        # 要求せずentry全体をStage71のallowlist内で置換する。
        if entry[0] == EVO_NONE:
            first_zero = index
            break
    if any(entry[0] != EVO_NONE for entry in entries[first_zero:]):
        _fail(f"first EVO_NONE後にentryがありCFRU探索から隠れます: species={species}")
    return first_zero


def audit_capacity(
    rom: bytes,
    table_address: int,
    species_count: int,
    mappings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    root_offset = _rom_offset(table_address, "evolution table")
    span = species_count * ROW_STRIDE
    if root_offset + span > len(rom):
        _fail("evolution table extentがROM範囲外です")
    groups: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for row in mappings:
        groups[int(row["source_species_id"])].append(row)
    audits: list[dict[str, Any]] = []
    for species, rows in sorted(groups.items()):
        entries = _entries(rom, root_offset, species)
        used = _used_slots(entries, species)
        rows = sorted(rows, key=lambda row: int(row["target_species_id"]))
        if used + len(rows) > EVOS_PER_MON:
            _fail(f"evolution slot不足: species={species}: used={used}, required={len(rows)}")
        for row in rows:
            wanted = tuple(int(value) for value in row["forward_entry"])
            if any(
                entry[0] == EVO_MEGA
                and (entry[1] == wanted[1] or entry[2] == wanted[2])
                for entry in entries[:used]
            ):
                _fail(f"既存Mega rowとstone/target衝突: {row['record_key']}")
        audits.append(
            {
                "source_species_id": species,
                "source_species_keys": sorted({str(row["source_species_key"]) for row in rows}),
                "used_slots_before": used,
                "free_slots_before": EVOS_PER_MON - used,
                "required_forward_slots": len(rows),
                "assigned_slots": list(range(used, used + len(rows))),
                "free_slots_after": EVOS_PER_MON - used - len(rows),
            }
        )
    all_entries = (
        entry
        for species in range(species_count)
        for entry in _entries(rom, root_offset, species)
    )
    existing_megas = sum(1 for entry in all_entries if entry[0] == EVO_MEGA)
    return {
        "status": "PASS",
        "table_address": f"0x{table_address:08X}",
        "species_count": species_count,
        "existing_mega_entry_count": existing_megas,
        "source_row_count": len(groups),
        "mapping_count": len(mappings),
        "minimum_free_slots_before": min(row["free_slots_before"] for row in audits),
        "minimum_free_slots_after": min(row["free_slots_after"] for row in audits),
        "rows": audits,
    }


def resolve_standard_mega(
    entries: Sequence[tuple[int, int, int, int]],
    held_item: int,
    *,
    policy_allowed: bool,
    has_keystone: bool,
    already_used: bool,
) -> int:
    """project policy→keystone→exact stone→usageの順をhost上で表現する。"""
    if not policy_allowed:
        return SPECIES_NONE
    if not has_keystone:
        return SPECIES_NONE
    for method, parameter, target, variant in entries:
        if method == EVO_NONE:
            break
        if (
            method == EVO_MEGA
            and parameter != 0
            and variant == MEGA_VARIANT_STANDARD
            and parameter == held_item
        ):
            if already_used:
                return SPECIES_NONE
            return target
    return SPECIES_NONE


def upstream_keystone_enabled(mode: str, owns_ring: bool) -> bool:
    """project policy通過後の固定CFRU mode別keystone判定。"""
    if mode in {"frontier", "link"}:
        return True
    if mode in {"normal", "mega_brawl"}:
        return owns_ring
    _fail(f"未知のMega battle modeです: {mode}")


def upstream_owner_already_used(
    *, bank_done: bool, partner_done: bool, separate_owner: bool
) -> bool:
    """BankMegaEvolvedの通常double/partner ownership差を表現する。"""
    return bank_done if separate_owner else bank_done or partner_done


def upstream_mark_mega(
    mode: str,
    *,
    bank_done: bool,
    partner_done: bool,
    separate_owner: bool,
) -> tuple[bool, bool]:
    """battle_start_turn_start.cのdone/partner markを表現する。"""
    if mode == "mega_brawl":
        return bank_done, partner_done
    if mode not in {"normal", "frontier", "link"}:
        _fail(f"未知のMega battle modeです: {mode}")
    bank_done = True
    if not separate_owner:
        partner_done = True
    return bank_done, partner_done


def project_policy_allows_mega(*, configured_mega_mode: bool, side_used: bool) -> bool:
    """現行project side-based mechanic gateのhost model。"""
    return configured_mega_mode and not side_used


def resolve_revert(entries: Sequence[tuple[int, int, int, int]]) -> int:
    """固定CFRU TryRevertMegaの逆方向探索をhost上で表現する。"""
    for method, parameter, target, _variant in entries:
        if method == EVO_NONE:
            break
        if method == EVO_MEGA and parameter == 0:
            return target
    return SPECIES_NONE


def _baseline_contract(
    root: Path, config: Mapping[str, Any], mappings: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Any], bytes]:
    raw = _fixed_raw(root, config["inputs"]["capacity_baseline_rom"], "capacity baseline ROM")
    assert raw is not None
    address = _as_int(
        config["fixed_cfru_jp"]["evolution_abi"]["capacity_baseline_address"],
        "capacity baseline address",
    )
    offset = _rom_offset(address, "capacity baseline address")
    table = raw[offset:offset + OLD_SPECIES_COUNT * ROW_STRIDE]
    expected = config["fixed_cfru_jp"]["evolution_abi"]["capacity_baseline_sha256"]
    if sha256(table) != expected:
        _fail("capacity baseline evolution table SHA-256不一致")
    audit = audit_capacity(raw, address, OLD_SPECIES_COUNT, mappings)
    if audit["existing_mega_entry_count"] != EXISTING_MEGA_ENTRY_COUNT:
        _fail("既存Mega entry件数が80ではありません")
    return audit, raw


def build_mapping_contract(
    root: Path, config_path: Path = DEFAULT_CONFIG
) -> dict[str, Any]:
    config = _read_config(root, config_path)
    cfru = audit_fixed_cfru(root, config)
    mappings = derive_mappings(root, config)
    capacity, _rom = _baseline_contract(root, config, mappings)
    new_abilities = [row for row in mappings if int(row["ability_id"]) >= 312]
    contract = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "stage": STAGE,
        "status": "PREFLIGHT_PASS_STAGE70_IDENTITY_REQUIRED"
        if config["status"] == "WAITING_STAGE70_IDENTITY"
        else "MAPPING_READY",
        "release_candidate": False,
        "counts": {
            "mappings": len(mappings),
            "unique_base_species": len({row["source_species_id"] for row in mappings}),
            "unique_stones": len({row["mega_stone_id"] for row in mappings}),
            "forward_entries": FORWARD_COUNT,
            "reverse_entries": REVERSE_COUNT,
            "new_ability_effects_pending_stage72": len(new_abilities),
        },
        "fixed_cfru_jp_audit": cfru,
        "capacity_audit": capacity,
        "mapping_sha256": sha256(stable_json(mappings)),
        "mappings": mappings,
        "special_form_guards": {
            "raichu_xy": "SAME_BASE_DISTINCT_STONES",
            "meowstic_sexes": "DISTINCT_BASE_ROWS_SAME_STONE",
            "magearna_forms": "DISTINCT_BASE_ROWS_SAME_STONE",
            "tatsugiri_forms": "THREE_DISTINCT_BASE_ROWS_SAME_STONE",
            "floette_eternal": "EXISTING_PRE_MEGA_SPECIES_1029",
        },
        "lifecycle": {
            "switch": "RETAIN_MEGA",
            "faint": "REVERT_BASE_VIA_TRY_FORM_REVERT_KEEP_MEGA_DATA_DONE",
            "revive": "BASE_FORM_AND_REMEGA_REJECTED_BY_BANK_MEGA_EVOLVED",
            "battle_end": "REVERSE_ROW_VIA_EXISTING_MEGA_REVERT",
            "interrupt": "PRE_BATTLE_SNAPSHOT_RESTORE_BY_EXISTING_OWNER",
            "save_during_owned_special_battle": "PRE_BATTLE_SNAPSHOT_RESTORE_BY_EXISTING_OWNER",
            "ordinary_mid_battle_save": "NOT_EXPOSED_BY_ENGINE",
        },
        "runtime_mode_contract": {
            "gate_order": config["runtime_policy"]["gate_order"],
            "project_policy": config["runtime_policy"]["project_policy"],
            "keystone_after_project_policy":
                config["runtime_policy"]["keystone_by_mode_after_project_policy"],
            "upstream_usage": config["runtime_policy"]["upstream_usage_by_mode"],
            "compiled_project_usage":
                config["runtime_policy"]["compiled_project_usage"],
            "mega_brawl_exact_runtime": "PENDING_SINGLE_FINAL_MGBA",
        },
        "remaining_work": {
            "stage70_identity": config["status"] != "STAGE70_IDENTITY_PINNED",
            "new_ability_effect_hooks_stage72": 6,
            "exact_mgba_final_parent_once": "NOT_RUN",
            "release_candidate": False,
        },
    }
    if contract["counts"] != {
        "mappings": 49,
        "unique_base_species": 48,
        "unique_stones": 45,
        "forward_entries": 49,
        "reverse_entries": 49,
        "new_ability_effects_pending_stage72": 6,
    }:
        _fail(f"Mega mapping件数契約不一致: {contract['counts']}")
    return contract


def _table_map(metadata: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    tables = metadata.get("tables")
    if isinstance(tables, dict):
        return {str(key): value for key, value in tables.items() if isinstance(value, dict)}
    if isinstance(tables, list):
        result: dict[str, Mapping[str, Any]] = {}
        for row in tables:
            if isinstance(row, dict):
                key = row.get("table_key") or row.get("name")
                if isinstance(key, str):
                    result[key] = row
        return result
    _fail("Stage70 metadata tablesがdict/listではありません")


def _validate_parent_output(metadata: Mapping[str, Any], rom: bytes) -> None:
    output = metadata.get("output_rom", metadata.get("output"))
    if not isinstance(output, dict):
        _fail("Stage70 metadata output identityがありません")
    if output.get("size") != len(rom) or output.get("sha256") != sha256(rom):
        _fail("Stage70 metadata output identityが親ROMと不一致です")
    if metadata.get("stage") != 70:
        _fail("Stage70 metadata stage不一致")


def _audit_compiled_engine(rom: bytes, config: Mapping[str, Any]) -> dict[str, Any]:
    assertions = config["fixed_cfru_jp"].get("compiled_rom_assertions")
    if not isinstance(assertions, dict):
        _fail("compiled Mega ROM assertionsがありません")
    span = assertions.get("keystone_function_span")
    rows = assertions.get("keystone_580_thumb_halfwords")
    if not isinstance(span, dict) or not isinstance(rows, list) or len(rows) != 8:
        _fail("Mega Ring 580 compiled assertion契約が不正です")
    start = _as_int(span.get("start"), "keystone span start")
    end = _as_int(span.get("end_exclusive"), "keystone span end")
    raw = rom[_rom_offset(start, "keystone span start"):_rom_offset(end, "keystone span end")]
    if sha256(raw) != span.get("sha256"):
        _fail("固定CFRU keystone function ROM span hash不一致")
    evidence: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            _fail("keystone halfword assertion row型不正")
        address = _as_int(row.get("address"), "keystone halfword address")
        expected = _as_int(row.get("expected"), "keystone halfword expected")
        offset = _rom_offset(address, "keystone halfword address")
        actual = struct.unpack_from("<H", rom, offset)[0]
        if actual != expected:
            _fail(f"Mega Ring 580 compiled halfword不一致: 0x{address:08X}")
        evidence.append(
            {
                "address": f"0x{address:08X}",
                "halfword": f"0x{actual:04X}",
                "meaning": row.get("meaning"),
            }
        )
    function_rows = assertions.get("function_spans")
    if not isinstance(function_rows, list) or not function_rows:
        _fail("compiled Mega function span契約がありません")
    symbols = config["fixed_cfru_jp"].get("symbols")
    if not isinstance(symbols, dict):
        _fail("compiled Mega symbol契約がありません")
    function_evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in function_rows:
        if not isinstance(row, dict):
            _fail("compiled Mega function span row型不正")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or symbol in seen or symbol not in symbols:
            _fail(f"compiled Mega function span symbol不正: {symbol}")
        function_start = _as_int(row.get("start"), f"{symbol}.start")
        function_end = _as_int(row.get("end_exclusive"), f"{symbol}.end")
        if function_start != _as_int(symbols[symbol], f"symbol.{symbol}"):
            _fail(f"compiled function start/symbol不一致: {symbol}")
        if function_end <= function_start:
            _fail(f"compiled function spanが空です: {symbol}")
        function_raw = rom[
            _rom_offset(function_start, f"{symbol}.start"):
            _rom_offset(function_end, f"{symbol}.end")
        ]
        digest = sha256(function_raw)
        if digest != row.get("sha256"):
            _fail(f"compiled function ROM span hash不一致: {symbol}")
        function_evidence.append(
            {
                "symbol": symbol,
                "start": f"0x{function_start:08X}",
                "end_exclusive": f"0x{function_end:08X}",
                "size": len(function_raw),
                "sha256": digest,
            }
        )
        seen.add(symbol)
    return {
        "status": "PASS",
        "item_id": 580,
        "derivation": "145 << 2",
        "function_span_sha256": sha256(raw),
        "thumb_halfwords": evidence,
        "audited_function_span_count": len(function_evidence),
        "function_spans": function_evidence,
        "assurance_boundary": {
            "source_and_static_rom_preimage": "PASS",
            "mode_matrix_exact_runtime": "PENDING_SINGLE_FINAL_MGBA",
        },
    }


def _validate_ability_safety(
    metadata: Mapping[str, Any], rom: bytes, tables: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    runtime = metadata.get("ability_runtime")
    if not isinstance(runtime, dict) or (
        runtime.get("localization_status")
        != "PROVISIONAL_LOCALIZATION_REPLACEABLE_P05_HAS_NO_JAPANESE_SUBMISSION"
        or runtime.get("effect_runtime_status") != "EFFECT_RUNTIME_PENDING_STAGE72"
    ):
        _fail("Stage70 Ability safe-index/effect境界が不正です")
    aliases = {
        "ability_names": ("ability_names", "ability_name"),
        "ability_descriptions": ("ability_descriptions", "ability_description_pointers"),
        "ability_ratings": ("ability_ratings",),
        "ability_mold_breaker_ignored": (
            "ability_mold_breaker_ignored",
            "ability_moldbreaker_ignored",
        ),
    }
    selected: dict[str, Mapping[str, Any]] = {}
    for canonical, candidates in aliases.items():
        row = next((tables[key] for key in candidates if key in tables), None)
        if row is None:
            _fail(f"Stage70 Ability安全表metadata欠落: {canonical}")
        selected[canonical] = row
    evidence: dict[str, Any] = {}
    for key, row in selected.items():
        new_count = row.get("new_count", row.get("count"))
        if new_count != REQUIRED_ABILITY_TABLE_COUNT:
            _fail(f"Stage70 {key} countが318ではありません: {new_count}")
        address_value = row.get("new_address", row.get("address"))
        stride_value = row.get("stride")
        digest = row.get("new_sha256", row.get("sha256"))
        if address_value is None or stride_value is None or not isinstance(digest, str):
            _fail(f"Stage70 {key} identity情報が不足しています")
        address = _as_int(address_value, f"Stage70 {key}.address")
        stride = _as_int(stride_value, f"Stage70 {key}.stride")
        if stride <= 0:
            _fail(f"Stage70 {key}.strideが正ではありません")
        offset = _rom_offset(address, f"Stage70 {key}.address")
        raw = rom[offset:offset + REQUIRED_ABILITY_TABLE_COUNT * stride]
        if len(raw) != REQUIRED_ABILITY_TABLE_COUNT * stride or sha256(raw) != digest:
            _fail(f"Stage70 {key} ROM slice identity不一致")
        evidence[key] = {
            "address": f"0x{address:08X}",
            "count": REQUIRED_ABILITY_TABLE_COUNT,
            "stride": stride,
            "sha256": digest,
        }
    # 効果hookはこのstageでは未完であることを過大主張しない。
    return {
        "status": "PASS_SAFE_INDEXED_TABLES_ONLY",
        "tables": evidence,
        "new_ids": list(range(312, 318)),
        "effect_hooks": "PENDING_STAGE72",
        "release_candidate": False,
    }


def _evolution_identity(
    metadata: Mapping[str, Any], rom: bytes, tables: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    row = tables.get("evolution")
    if row is None:
        _fail("Stage70 evolution table metadata欠落")
    expected_scalars = {
        "old_count": OLD_SPECIES_COUNT,
        "new_count": NEW_SPECIES_COUNT,
        "stride": ROW_STRIDE,
    }
    for key, expected in expected_scalars.items():
        if row.get(key) != expected:
            _fail(f"Stage70 evolution.{key}不一致: {row.get(key)} != {expected}")
    old_address = _as_int(row.get("old_address"), "evolution.old_address")
    new_address = _as_int(row.get("new_address"), "evolution.new_address")
    pointer_consumers = row.get("pointer_consumers")
    if not isinstance(pointer_consumers, dict):
        _fail("Stage70 evolution pointer_consumers metadata欠落")
    sites = pointer_consumers.get("site_offsets")
    if not isinstance(sites, list) or len(sites) != 39 or len(set(sites)) != 39:
        _fail("Stage70 evolution pointer site 39件が一意ではありません")
    normalized_sites = [_as_int(site, "evolution.site_offset") for site in sites]
    if normalized_sites != sorted(normalized_sites):
        _fail("Stage70 evolution pointer sitesが昇順ではありません")
    for site in normalized_sites:
        if not 0 <= site <= len(rom) - 4:
            _fail(f"Stage70 evolution pointer siteがROM範囲外: 0x{site:X}")
        if struct.unpack_from("<I", rom, site)[0] != new_address:
            _fail(f"Stage70 evolution pointer未接続: 0x{site:X}")
    offset = _rom_offset(new_address, "Stage70 evolution.new_address")
    raw = rom[offset:offset + NEW_SPECIES_COUNT * ROW_STRIDE]
    if len(raw) != NEW_SPECIES_COUNT * ROW_STRIDE:
        _fail("Stage70 evolution tableがROM末尾を越えます")
    prefix = raw[:OLD_SPECIES_COUNT * ROW_STRIDE]
    suffix = raw[OLD_SPECIES_COUNT * ROW_STRIDE:]
    old_prefix_sha = row.get("existing_prefix_sha256")
    new_sha = row.get("new_sha256")
    if sha256(prefix) != old_prefix_sha:
        _fail("Stage70 evolution old prefix hash不一致")
    if old_prefix_sha != "3fc4c8cd5d21c5b7f1fa2972223288ec1040f115321298a19e168694ee45e002":
        _fail("Stage70 evolution old prefixが固定Stage67から変化しています")
    if sha256(raw) != new_sha:
        _fail("Stage70 evolution full table hash不一致")
    if suffix != bytes(len(suffix)):
        _fail("Stage70 new Species evolution 49行がall-zeroではありません")
    return {
        "old_address": old_address,
        "new_address": new_address,
        "new_offset": offset,
        "site_offsets": normalized_sites,
        "old_prefix_sha256": old_prefix_sha,
        "stage70_sha256": new_sha,
    }


def _changed_offsets(before: bytes, after: bytes) -> list[int]:
    if len(before) != len(after):
        _fail("parent/output ROM size不一致")
    return [index for index, pair in enumerate(zip(before, after, strict=True)) if pair[0] != pair[1]]


def _allocation_layout(
    ledger: Mapping[str, Any], rom_size: int
) -> tuple[list[dict[str, Any]], dict[str, tuple[int, int]]]:
    allocations = ledger.get("allocations")
    regions = ledger.get("regions")
    summaries = ledger.get("summaries")
    if not isinstance(allocations, list) or not all(isinstance(row, dict) for row in allocations):
        _fail("allocation ledger allocationsが不正です")
    if not isinstance(regions, list) or not all(isinstance(row, dict) for row in regions):
        _fail("allocation ledger regionsが不正です")
    if not isinstance(summaries, dict):
        _fail("allocation ledger summariesが不正です")
    if summaries.get("allocation_count") != len(allocations):
        _fail("allocation ledger count summary不一致")
    if summaries.get("overlap_count") != 0 or summaries.get("rom_size") != rom_size:
        _fail("allocation ledger overlap/ROM size summary不一致")
    region_extents: dict[str, tuple[int, int]] = {}
    for row in regions:
        name = row.get("name")
        start = row.get("start")
        end = row.get("end_exclusive")
        if (
            not isinstance(name, str)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or not 0 <= start <= end <= rom_size
            or row.get("size") != end - start
            or row.get("gba_start") != ROM_BASE + start
            or row.get("gba_end_exclusive") != ROM_BASE + end
            or name in region_extents
        ):
            _fail(f"allocation region extent不正: {name}")
        region_extents[name] = (start, end)
    sequences: set[int] = set()
    names: set[str] = set()
    for row in allocations:
        sequence = row.get("sequence")
        name = row.get("name")
        start = row.get("start")
        end = row.get("end_exclusive")
        size = row.get("size")
        alignment = row.get("alignment")
        region = row.get("region")
        if (
            not isinstance(sequence, int)
            or sequence in sequences
            or not isinstance(name, str)
            or name in names
            or not isinstance(start, int)
            or not isinstance(end, int)
            or not isinstance(size, int)
            or not isinstance(alignment, int)
            or alignment <= 0
            or size != end - start
            or not 0 <= start < end <= rom_size
            or start % alignment != 0
            or row.get("gba_start") != ROM_BASE + start
            or row.get("gba_end_exclusive") != ROM_BASE + end
            or region not in region_extents
            or not region_extents[region][0] <= start < end <= region_extents[region][1]
        ):
            _fail(f"allocation extent不正: sequence={sequence}, name={name}")
        digest = row.get("content_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            _fail(f"allocation content hash不正: {name}")
        sequences.add(sequence)
        names.add(name)
    ordered = sorted(allocations, key=lambda row: (row["start"], row["end_exclusive"]))
    overlaps = [
        (left["sequence"], right["sequence"])
        for left, right in zip(ordered, ordered[1:])
        if left["end_exclusive"] > right["start"]
    ]
    if overlaps:
        _fail(f"allocation overlap検出: {overlaps[:8]}")
    return allocations, region_extents


def validate_stage71_allocation(
    parent_rom: bytes,
    output_rom: bytes,
    parent_raw: bytes,
    output_raw: bytes,
) -> dict[str, Any]:
    """Stage71が変更したStage70 ownerの全span hashだけを更新したか検証する。"""
    parent = _json(parent_raw, "Stage70 allocation")
    output = _json(output_raw, "Stage71 allocation")
    parent_rows, _regions = _allocation_layout(parent, len(parent_rom))
    output_rows, _output_regions = _allocation_layout(output, len(output_rom))
    if len(parent_rom) != len(output_rom):
        _fail("allocation検証ROM size不一致")
    if len(parent_rows) != len(output_rows):
        _fail("allocation ledger row数が変化しています")
    targets = [
        (index, row)
        for index, row in enumerate(parent_rows)
        if row.get("sequence") == STAGE70_ALLOCATION_SEQUENCE
        and row.get("name") == STAGE70_ALLOCATION_NAME
        and row.get("owner") == STAGE70_ALLOCATION_OWNER
    ]
    if len(targets) != 1:
        _fail("Stage70 P04 allocation ownerが一意ではありません")
    target_index, target_parent = targets[0]
    target_output = output_rows[target_index]
    if (
        target_output.get("sequence") != STAGE70_ALLOCATION_SEQUENCE
        or target_output.get("name") != STAGE70_ALLOCATION_NAME
        or target_output.get("owner") != STAGE70_ALLOCATION_OWNER
    ):
        _fail("Stage71 allocation target rowの位置/identityが変化しています")
    start = target_parent["start"]
    end = target_parent["end_exclusive"]
    parent_slice_sha = sha256(parent_rom[start:end])
    output_slice_sha = sha256(output_rom[start:end])
    if target_parent.get("content_sha256") != parent_slice_sha:
        _fail("Stage70 allocation #73 content hashが親ROM全spanと不一致です")
    if target_output.get("content_sha256") != output_slice_sha:
        _fail("Stage71 allocation #73 content hashが出力ROM全spanと不一致です")
    target_without_hash = {key: value for key, value in target_parent.items() if key != "content_sha256"}
    if target_without_hash != {
        key: value for key, value in target_output.items() if key != "content_sha256"
    }:
        _fail("Stage71 allocation #73でcontent hash以外が変化しています")

    unchanged_rows = 0
    for index, (before, after) in enumerate(zip(parent_rows, output_rows, strict=True)):
        if index == target_index:
            continue
        if before != after:
            _fail(f"非対象allocation ledger rowが変化: sequence={before.get('sequence')}")
        row_start = before["start"]
        row_end = before["end_exclusive"]
        if parent_rom[row_start:row_end] != output_rom[row_start:row_end]:
            _fail(f"非対象allocation ROM sliceが変化: sequence={before.get('sequence')}")
        unchanged_rows += 1
    parent_without_allocations = {key: value for key, value in parent.items() if key != "allocations"}
    output_without_allocations = {key: value for key, value in output.items() if key != "allocations"}
    if parent_without_allocations != output_without_allocations:
        _fail("allocation regions/summariesが変化しています")
    changed = _changed_offsets(parent_rom, output_rom)
    if any(not start <= offset < end for offset in changed):
        _fail("Stage71 ROM変更がallocation #73全span外にあります")
    return {
        "status": "PASS",
        "target_sequence": STAGE70_ALLOCATION_SEQUENCE,
        "target_name": STAGE70_ALLOCATION_NAME,
        "target_owner": STAGE70_ALLOCATION_OWNER,
        "start": start,
        "end_exclusive": end,
        "size": end - start,
        "parent_full_slice_sha256": parent_slice_sha,
        "output_full_slice_sha256": output_slice_sha,
        "content_hash_updated": parent_slice_sha != output_slice_sha,
        "full_target_allocation_slice_verified": True,
        "non_target_allocation_count": unchanged_rows,
        "all_allocation_rom_slices_compared": len(parent_rows),
        "non_target_ledger_rows_unchanged": True,
        "non_target_rom_slices_unchanged": True,
        "overlap_count": 0,
        "changed_rom_bytes_inside_target": len(changed),
        "parent_ledger_sha256": sha256(parent_raw),
        "output_ledger_sha256": sha256(output_raw),
    }


def build_stage71_allocation(
    parent_rom: bytes, output_rom: bytes, parent_raw: bytes
) -> tuple[bytes, dict[str, Any]]:
    parent = _json(parent_raw, "Stage70 allocation")
    parent_rows, _regions = _allocation_layout(parent, len(parent_rom))
    targets = [
        row
        for row in parent_rows
        if row.get("sequence") == STAGE70_ALLOCATION_SEQUENCE
        and row.get("name") == STAGE70_ALLOCATION_NAME
        and row.get("owner") == STAGE70_ALLOCATION_OWNER
    ]
    if len(targets) != 1:
        _fail("Stage70 P04 allocation ownerが一意ではありません")
    target = targets[0]
    start, end = target["start"], target["end_exclusive"]
    if sha256(parent_rom[start:end]) != target.get("content_sha256"):
        _fail("Stage70 P04 allocation parent content hash不一致")
    output = copy.deepcopy(parent)
    output_target = next(
        row for row in output["allocations"]
        if row.get("sequence") == STAGE70_ALLOCATION_SEQUENCE
    )
    output_target["content_sha256"] = sha256(output_rom[start:end])
    output_raw = stable_json(output)
    audit = validate_stage71_allocation(
        parent_rom, output_rom, parent_raw, output_raw
    )
    return output_raw, audit


@dataclass(frozen=True)
class Stage71Build:
    config: dict[str, Any]
    parent: bytes
    rom: bytes
    parent_allocation: bytes
    output_allocation: bytes
    mapping: dict[str, Any]
    metadata: dict[str, Any]
    checkpoint: dict[str, Any]
    generated_rows: bytes
    generated_rows_index: dict[str, Any]


def build_stage71_image(
    root: Path, config_path: Path = DEFAULT_CONFIG
) -> Stage71Build:
    config = _read_config(root, config_path)
    if config.get("status") != "STAGE70_IDENTITY_PINNED":
        _fail("Stage70 identity未確定のためStage71 ROM buildを拒否します")
    inputs = config["inputs"]
    parent = _fixed_raw(root, inputs["stage70_rom"], "Stage70 ROM")
    metadata_raw = _fixed_raw(root, inputs["stage70_metadata"], "Stage70 metadata")
    allocation_raw = _fixed_raw(root, inputs["stage70_allocation"], "Stage70 allocation")
    assert parent is not None and metadata_raw is not None and allocation_raw is not None
    metadata70 = _json(metadata_raw, "Stage70 metadata")
    _validate_parent_output(metadata70, parent)
    compiled_engine = _audit_compiled_engine(parent, config)
    tables = _table_map(metadata70)
    evolution = _evolution_identity(metadata70, parent, tables)
    ability = _validate_ability_safety(metadata70, parent, tables)

    mapping_contract = build_mapping_contract(root, config_path)
    mappings = mapping_contract["mappings"]
    capacity = audit_capacity(parent, evolution["new_address"], NEW_SPECIES_COUNT, mappings)
    if capacity["existing_mega_entry_count"] != EXISTING_MEGA_ENTRY_COUNT:
        _fail("Stage70既存Mega entry件数が80ではありません")
    baseline_rows = {row["source_species_id"]: row for row in mapping_contract["capacity_audit"]["rows"]}
    for row in capacity["rows"]:
        baseline = baseline_rows.get(row["source_species_id"])
        if baseline is None or baseline["assigned_slots"] != row["assigned_slots"]:
            _fail(f"Stage70 evolution slot drift: species={row['source_species_id']}")

    output = bytearray(parent)
    root_offset = evolution["new_offset"]
    source_next_slot = {
        row["source_species_id"]: row["assigned_slots"][0]
        for row in capacity["rows"]
    }
    prescribed: list[dict[str, Any]] = []
    generated_entries: list[bytes] = []
    for mapping in mappings:
        source = int(mapping["source_species_id"])
        target = int(mapping["target_species_id"])
        slot = source_next_slot[source]
        source_next_slot[source] += 1
        forward = struct.pack("<HHHH", *mapping["forward_entry"])
        reverse = struct.pack("<HHHH", *mapping["reverse_entry"])
        forward_offset = root_offset + source * ROW_STRIDE + slot * ENTRY_STRIDE
        reverse_offset = root_offset + target * ROW_STRIDE
        if struct.unpack_from("<H", output, forward_offset)[0] != EVO_NONE:
            _fail(f"Stage71 forward preimage methodがEVO_NONEではありません: {mapping['record_key']}")
        if output[reverse_offset:reverse_offset + ENTRY_STRIDE] != bytes(ENTRY_STRIDE):
            _fail(f"Stage71 reverse preimageがzeroではありません: {mapping['record_key']}")
        output[forward_offset:forward_offset + ENTRY_STRIDE] = forward
        output[reverse_offset:reverse_offset + ENTRY_STRIDE] = reverse
        mapping["forward_slot"] = slot
        mapping["forward_rom_offset"] = forward_offset
        mapping["reverse_slot"] = 0
        mapping["reverse_rom_offset"] = reverse_offset
        for kind, offset, raw in (
            ("forward", forward_offset, forward),
            ("reverse", reverse_offset, reverse),
        ):
            prescribed.append(
                {
                    "record_key": mapping["record_key"],
                    "kind": kind,
                    "rom_offset": offset,
                    "end_exclusive": offset + ENTRY_STRIDE,
                    "entry_hex": raw.hex(),
                }
            )
            generated_entries.append(raw)
    result = bytes(output)

    allowed = {
        offset
        for row in prescribed
        for offset in range(row["rom_offset"], row["end_exclusive"])
    }
    changed = _changed_offsets(parent, result)
    outside = [offset for offset in changed if offset not in allowed]
    if outside:
        _fail(f"Stage71 allowlist外ROM変更: 先頭={outside[:8]}")
    for row in prescribed:
        offset = row["rom_offset"]
        if result[offset:offset + ENTRY_STRIDE].hex() != row["entry_hex"]:
            _fail("Stage71 prescribed entry書込不一致")

    output_allocation, allocation_audit = build_stage71_allocation(
        parent, result, allocation_raw
    )
    if not allocation_audit["content_hash_updated"]:
        _fail("Stage71 allocation owner hashが更新されていません")

    # 実tableを固定CFRU host semanticsで全件検証する。
    all_new_stones = {int(row["mega_stone_id"]) for row in mappings}
    for mapping in mappings:
        source_entries = _entries(result, root_offset, int(mapping["source_species_id"]))
        target_entries = _entries(result, root_offset, int(mapping["target_species_id"]))
        expected_target = int(mapping["target_species_id"])
        held = int(mapping["mega_stone_id"])
        if resolve_standard_mega(
            source_entries,
            held,
            policy_allowed=True,
            has_keystone=True,
            already_used=False,
        ) != expected_target:
            _fail(f"正しい石でMega解決不能: {mapping['record_key']}")
        if resolve_standard_mega(
            source_entries,
            held,
            policy_allowed=False,
            has_keystone=True,
            already_used=False,
        ) != 0:
            _fail(f"project policy拒否時にMega可能: {mapping['record_key']}")
        if resolve_standard_mega(
            source_entries,
            held,
            policy_allowed=True,
            has_keystone=False,
            already_used=False,
        ) != 0:
            _fail(f"通常戦Mega RingなしでMega可能: {mapping['record_key']}")
        if resolve_standard_mega(
            source_entries,
            held,
            policy_allowed=True,
            has_keystone=True,
            already_used=True,
        ) != 0:
            _fail(f"1戦闘2回目のMegaが可能: {mapping['record_key']}")
        valid_for_source = {
            int(row["mega_stone_id"])
            for row in mappings
            if int(row["source_species_id"]) == int(mapping["source_species_id"])
        }
        for wrong in all_new_stones - valid_for_source:
            if resolve_standard_mega(
                source_entries,
                wrong,
                policy_allowed=True,
                has_keystone=True,
                already_used=False,
            ) != 0:
                _fail(f"誤石がMegaを解決: {mapping['record_key']} stone={wrong}")
        if resolve_revert(target_entries) != int(mapping["source_species_id"]):
            _fail(f"Mega reverse解決不一致: {mapping['record_key']}")

    table_raw = result[root_offset:root_offset + NEW_SPECIES_COUNT * ROW_STRIDE]
    generated_rows = b"".join(generated_entries)
    mapping_contract["status"] = "STAGE71_ROM_MATERIALIZED_STAGE72_EFFECTS_PENDING"
    mapping_contract["mappings"] = mappings
    mapping_contract["mapping_sha256"] = sha256(stable_json(mappings))
    mapping_contract["remaining_work"]["stage70_identity"] = False
    mapping_contract["remaining_work"]["exact_mgba_final_parent_once"] = "NOT_RUN"
    generated_index = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "entry_abi": "u16 method,param,target,variant little-endian",
        "entry_stride": ENTRY_STRIDE,
        "entry_count": len(prescribed),
        "content_sha256": sha256(generated_rows),
        "entries": [
            {
                **row,
                "generated_offset": index * ENTRY_STRIDE,
            }
            for index, row in enumerate(prescribed)
        ],
    }
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "stage": STAGE,
        "status": "CHECKPOINT_STAGE72_ABILITY_EFFECTS_PENDING",
        "done": False,
        "release_candidate": False,
        "parent": {
            "path": inputs["stage70_rom"]["path"],
            "size": len(parent),
            "sha256": sha256(parent),
            "stage": 70,
        },
        "output": {
            "path": config["outputs"]["rom"],
            "size": len(result),
            "sha256": sha256(result),
        },
        "evolution_table": {
            "address": f"0x{evolution['new_address']:08X}",
            "count": NEW_SPECIES_COUNT,
            "stride": ROW_STRIDE,
            "stage70_sha256": evolution["stage70_sha256"],
            "stage71_sha256": sha256(table_raw),
            "existing_prefix_sha256": evolution["old_prefix_sha256"],
            "forward_entries_added": FORWARD_COUNT,
            "reverse_entries_added": REVERSE_COUNT,
            "existing_mega_entries_preserved": EXISTING_MEGA_ENTRY_COUNT,
            "final_mega_entry_count": EXISTING_MEGA_ENTRY_COUNT + FORWARD_COUNT + REVERSE_COUNT,
            "pointer_site_count": len(evolution["site_offsets"]),
            "pointer_site_offsets": evolution["site_offsets"],
        },
        "ability_safety": ability,
        "compiled_engine": compiled_engine,
        "change_allowlist": {
            "entry_count": len(prescribed),
            "allowed_byte_count": len(allowed),
            "changed_byte_count": len(changed),
            "outside_allowlist_count": 0,
            "changed_offsets_sha256": sha256(stable_json(changed)),
            "entries": prescribed,
        },
        "allocation": {
            "new_allocation_count": 0,
            "policy": "UPDATE_MUTATED_OWNER_CONTENT_HASH_PRESERVE_LAYOUT",
            "parent_sha256": sha256(allocation_raw),
            "output_sha256": sha256(output_allocation),
            "target_owner_content_hash_changed":
                allocation_audit["content_hash_updated"],
            "audit": allocation_audit,
        },
        "validation": {
            "mapping_49": "PASS",
            "reverse_49": "PASS",
            "wrong_stone_rejected": "PASS_ALL_OTHER_NEW_STONES",
            "gate_order": {
                "order": config["runtime_policy"]["gate_order"],
                "status": "PASS_SOURCE_AND_COMPILED_PREIMAGE",
            },
            "project_policy": {
                "standard_pending_mode": "MEGA_DENIED",
                "configured_mega_mode": "ELIGIBLE_SUBJECT_TO_REMAINING_GATES",
                "status": "PASS_SOURCE_COMPILED_SPAN_AND_HOST_MODEL",
            },
            "keystone_by_mode_after_project_policy": {
                **config["runtime_policy"]["keystone_by_mode_after_project_policy"],
                "status": "PASS_SOURCE_COMPILED_SPAN_AND_HOST_MODEL",
            },
            "usage_by_mode": {
                "normal_same_owner_one_use": "PASS_SOURCE_AND_HOST_MODEL",
                "partner_separate_owner": "PASS_SOURCE_AND_HOST_MODEL",
                "mega_brawl_upstream_no_done_mark": "PASS_SOURCE_AND_HOST_MODEL",
                "mega_brawl_compiled_project_side_used":
                    "EXACT_RUNTIME_PENDING_SINGLE_FINAL_MGBA",
            },
            "special_form_guard": "PASS",
            "existing_mega_regression": "PASS_STATIC_BYTE_PRESERVATION",
            "switch_retains_mega": "PASS_SOURCE_AND_HOST_ORACLE",
            "faint_revert_keep_usage_done":
                "PASS_SOURCE_COMPILED_SPAN_AND_HOST_ORACLE",
            "battle_cleanup": "PASS_EXISTING_OWNER_PLUS_REVERSE_ROWS_HOST_ORACLE",
            "allocation_full_owner_slice": "PASS",
            "host_static_tests": "REQUIRED_SEPARATE_COMMAND",
            "exact_mgba_final_parent_once": "NOT_RUN",
        },
        "remaining_work": {
            "new_ability_effect_hooks_stage72": [312, 313, 314, 315, 316, 317],
            "exact_mgba_final_parent_once": "NOT_RUN",
            "release_candidate_after_stage72_and_final_gate": False,
        },
    }
    checkpoint = {
        **metadata,
        "checkpoint_marker": "STAGE71_NOT_RELEASE_CANDIDATE_STAGE72_REQUIRED",
        "mapping": {
            "path": config["outputs"]["mapping"],
            "count": FORWARD_COUNT,
            "sha256": sha256(stable_json(mapping_contract)),
        },
        "generated_rows": {
            "path": config["outputs"]["generated_rows"],
            "size": len(generated_rows),
            "sha256": sha256(generated_rows),
        },
    }
    return Stage71Build(
        config=config,
        parent=parent,
        rom=result,
        parent_allocation=allocation_raw,
        output_allocation=output_allocation,
        mapping=mapping_contract,
        metadata=metadata,
        checkpoint=checkpoint,
        generated_rows=generated_rows,
        generated_rows_index=generated_index,
    )


__all__ = [
    "DEFAULT_CONFIG",
    "ENTRY_STRIDE",
    "EVO_MEGA",
    "EVOS_PER_MON",
    "MEGA_VARIANT_STANDARD",
    "ModernizationP04MegaRuntimeError",
    "NEW_SPECIES_COUNT",
    "ROW_STRIDE",
    "Stage71Build",
    "audit_capacity",
    "audit_fixed_cfru",
    "build_mapping_contract",
    "build_stage71_allocation",
    "build_stage71_image",
    "derive_mappings",
    "project_policy_allows_mega",
    "resolve_revert",
    "resolve_standard_mega",
    "sha256",
    "stable_json",
    "upstream_keystone_enabled",
    "upstream_mark_mega",
    "upstream_owner_already_used",
    "validate_stage71_allocation",
]
