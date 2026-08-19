#!/usr/bin/env python3
"""Trainer ChangeKit Task 01--06 を最終統合用の正規形へ変換する。

入力ZIPや展開済みChangeKitは変更しない。出力は
``content/trainer_changekit_final`` 以下の決定的な生成物だけである。

正規化で扱うStage 34監査事項は次の3点。

* UNKNOWN 54件のうちkind 9の3件をEARLY_RIVAL/SINGLEとして確定する。
* trainer flag参照を戦闘と誤認した51件と、共有commandの余剰caller 20件を
  元命令非破壊のARCHIVE_REMATCH consumerへ移す。
* 重複trainer IDのcanonical ownerだけ元IDを保持し、残りを未使用帯へ移す。
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


TASK_DIRS = (
    "VEGA_TRAINER_CHANGEKIT_TASK02_TOHOKU_EARLY",
    "VEGA_TRAINER_CHANGEKIT_TASK03_TOHOKU_MID",
    "VEGA_TRAINER_CHANGEKIT_TASK04_TOHOKU_LATE",
    "VEGA_TRAINER_CHANGEKIT_TASK05_LEAGUE_POSTGAME",
    "VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
)
AUTHORING_DIR = "Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819"
GLOBAL_DIR = "VEGA_TRAINER_CHANGEKIT_TASK01_GLOBAL"
DATA_FILES = (
    "coverage.csv",
    "trainer_encounters.csv",
    "trainer_parties.csv",
    "trainer_party_members.csv",
    "trainer_physical_bindings.csv",
    "trainer_dialogue.csv",
    "trainer_rewards.csv",
    "trainer_gimmicks.csv",
)
GLOBAL_FILES = (
    ("global/encounter_directives.csv", "encounter_directives.csv"),
    ("global/difficulty_policy.csv", "difficulty_policy.csv"),
    ("global/gimmick_policy.csv", "gimmick_policy.csv"),
    ("runtime_requirements/required_features.csv", "required_features.csv"),
    ("runtime_requirements/shared_runtime_requests.csv", "shared_runtime_requests.csv"),
)
REGISTRY_FILES = {
    "species_key": "species_ids.csv",
    "move_key": "move_ids.csv",
    "ability_key": "ability_ids.csv",
    "nature_key": "nature_ids.csv",
    "item_key": "item_ids.csv",
}
ARCHIVE_BAND_START = 1367
ARCHIVE_BAND_END = 4095
EXPECTED_ENCOUNTERS = 1302
EXPECTED_MEMBERS = 6490
EXPECTED_FLAG_FALSE_POSITIVES = 51
EXPECTED_SHARED_COMMAND_EXTRAS = 20
EXPECTED_ARCHIVE_CONSUMERS = 71
EXPECTED_KIND9 = 3
EXPECTED_DUPLICATE_REALLOCATIONS = 16
EXPECTED_RESERVED_REALLOCATIONS = 1
EXPECTED_REALLOCATIONS = (
    EXPECTED_DUPLICATE_REALLOCATIONS + EXPECTED_RESERVED_REALLOCATIONS
)
EXPECTED_MAX_RUNTIME_ID = 4283
EXPECTED_TABLE_COUNT = 4284
# CFRU dispatches these values through facility/Secret Base builders instead
# of indexing gTrainers.  Physical source IDs may retain them in script data,
# but an ordinary ChangeKit consumer must resolve to a non-reserved target.
RESERVED_RUNTIME_TRAINER_IDS = frozenset({0x395, 0x396, 0x397, 0x398, 0x399, 1024})

EVIDENCE_INSTRUCTION_RE = re.compile(r"instruction=(0x[0-9A-Fa-f]+)")
EVIDENCE_PHYSICAL_ID_RE = re.compile(r"trainer_id=(\d+)")
SOURCE_TEMPLATE_RE = re.compile(r"\b(TPL_[A-Z0-9_]+)\b")
TRAINERBATTLE_KIND = {
    "TRAINER_BATTLE_SINGLE": 0,
    "TRAINER_BATTLE_CONTINUE_SCRIPT_NO_MUSIC": 1,
    "TRAINER_BATTLE_CONTINUE_SCRIPT": 2,
    "TRAINER_BATTLE_SINGLE_NO_INTRO_TEXT": 3,
    "TRAINER_BATTLE_DOUBLE": 4,
    "TRAINER_BATTLE_REMATCH": 5,
    "TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE": 6,
    "TRAINER_BATTLE_REMATCH_DOUBLE": 7,
    "TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE_NO_MUSIC": 8,
    "TRAINER_BATTLE_EARLY_RIVAL": 9,
}


class BuildError(RuntimeError):
    """入力または正規化結果が契約を満たさない。"""


@dataclass(frozen=True)
class SourceTable:
    fields: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class ArchiveReason:
    kind: str
    original_owner: str
    original_command: str
    original_address: str


def _read_csv(path: Path) -> SourceTable:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise BuildError(f"CSV headerがありません: {path}")
        rows = tuple(dict(row) for row in reader)
        return SourceTable(tuple(reader.fieldnames), rows)


def _write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _instruction(row: Mapping[str, str]) -> int:
    match = EVIDENCE_INSTRUCTION_RE.search(row.get("evidence", ""))
    if not match:
        raise BuildError(f"instruction evidenceがありません: {row.get('encounter_key')}")
    return int(match.group(1), 16)


def _physical_trainer_id(row: Mapping[str, str]) -> int:
    match = EVIDENCE_PHYSICAL_ID_RE.search(row.get("evidence", ""))
    if match:
        return int(match.group(1))
    return int(row["trainer_id"])


def discover_input_root(repo: Path) -> Path:
    candidates = (
        repo / "userfile/imports/trainer_changekit_final/integration_inputs",
        repo / "userfile/imports/integration_inputs",
        repo.parent / "PRIVATE_INPUTS/trainer_changekit_final/integration_inputs",
        repo.parent / "PRIVATE_INPUTS/integration_inputs",
        repo.parent / "integration_inputs",
        repo.parent.parent / "integration_inputs",
    )
    for candidate in candidates:
        if all((candidate / name).is_dir() for name in (*TASK_DIRS, AUTHORING_DIR, GLOBAL_DIR)):
            return candidate.resolve()
    raise BuildError("integration_inputsを自動検出できません。--input-rootを指定してください")


def _load_union(input_root: Path) -> dict[str, SourceTable]:
    union: dict[str, SourceTable] = {}
    for filename in DATA_FILES:
        fields: tuple[str, ...] | None = None
        rows: list[dict[str, str]] = []
        for task_dir in TASK_DIRS:
            table = _read_csv(input_root / task_dir / "data" / filename)
            if fields is None:
                fields = table.fields
            elif fields != table.fields:
                raise BuildError(f"Task間でheaderが不一致です: {filename}")
            rows.extend(table.rows)
        assert fields is not None
        union[filename] = SourceTable(fields, tuple(rows))
    return union


def _load_inventory(repo: Path) -> list[dict[str, object]]:
    path = repo / "reports/generated/id_inventory.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    references = data.get("script_references")
    if not isinstance(references, list):
        raise BuildError(f"T02 inventoryにscript_referencesがありません: {path}")
    return [dict(row) for row in references]


def _validate_unique(rows: Sequence[Mapping[str, str]], field: str, label: str) -> None:
    values = [row[field] for row in rows]
    duplicates = [value for value, count in Counter(values).items() if count != 1]
    if duplicates:
        raise BuildError(f"{label}が一意ではありません: {duplicates[:5]}")


def _classify_archives(
    encounters: Sequence[dict[str, str]],
    inventory: Sequence[dict[str, object]],
) -> tuple[dict[str, ArchiveReason], set[str]]:
    by_address: dict[int, list[str]] = defaultdict(list)
    for row in encounters:
        if row["region"] == "TOHOKU":
            by_address[_instruction(row)].append(row["encounter_key"])

    graph_at: dict[int, list[dict[str, object]]] = defaultdict(list)
    battles_by_physical_id: dict[int, dict[int, dict[str, object]]] = defaultdict(dict)
    for reference in inventory:
        address = reference.get("instruction_address")
        if isinstance(address, int):
            graph_at[address].append(reference)
        if (
            reference.get("category") == "trainer"
            and reference.get("access") == "battle"
            and isinstance(reference.get("value"), int)
            and isinstance(address, int)
        ):
            battles_by_physical_id[int(reference["value"])][address] = reference

    archive: dict[str, ArchiveReason] = {}
    kind9: set[str] = set()
    unknown = [row for row in encounters if row["battle_type"] == "UNKNOWN"]
    for row in unknown:
        key = row["encounter_key"]
        address = _instruction(row)
        physical_id = _physical_trainer_id(row)
        matching = [
            ref
            for ref in graph_at.get(address, ())
            if ref.get("category") == "trainer" and int(ref.get("value", -1)) == physical_id
        ]
        if len(matching) != 1:
            raise BuildError(f"UNKNOWNのT02 graph照合が一意ではありません: {key} hits={len(matching)}")
        reference = matching[0]
        if reference.get("access") == "battle":
            if int(reference.get("battle_type", -1)) != 9:
                raise BuildError(f"UNKNOWN実戦闘がkind 9ではありません: {key}")
            kind9.add(key)
            continue
        if reference.get("access") != "flag":
            raise BuildError(f"UNKNOWN参照がbattle/flagではありません: {key}")

        candidate_owners: list[str] = []
        for candidate_address in sorted(battles_by_physical_id.get(physical_id, {})):
            candidate_owners.extend(sorted(by_address.get(candidate_address, ())))
        if not candidate_owners:
            raise BuildError(f"flag参照の物理trainer battle ownerがありません: {key}")
        archive[key] = ArchiveReason(
            kind="FLAG_REFERENCE_FALSE_POSITIVE",
            original_owner="|".join(candidate_owners),
            original_command=str(reference.get("command", "trainer_flag")),
            original_address=f"0x{address:08X}",
        )

    if len(kind9) != EXPECTED_KIND9:
        raise BuildError(f"kind 9件数が不正です: {len(kind9)}")
    flag_count = sum(reason.kind == "FLAG_REFERENCE_FALSE_POSITIVE" for reason in archive.values())
    if flag_count != EXPECTED_FLAG_FALSE_POSITIVES:
        raise BuildError(f"flag誤認件数が不正です: {flag_count}")

    # flag誤認を除外した実戦闘行だけで共有commandを判定する。各commandの最小keyを
    # canonical ownerとし、残りcallerをArchiveへ移す。
    battle_address_groups: dict[int, list[str]] = defaultdict(list)
    for row in encounters:
        key = row["encounter_key"]
        if row["region"] == "TOHOKU" and key not in archive:
            battle_address_groups[_instruction(row)].append(key)
    shared_extra_count = 0
    for address, keys in sorted(battle_address_groups.items()):
        if len(keys) < 2:
            continue
        canonical = sorted(keys)[0]
        for key in sorted(keys)[1:]:
            archive[key] = ArchiveReason(
                kind="SHARED_COMMAND_EXTRA_CALLER",
                original_owner=canonical,
                original_command="trainerbattle_shared_command",
                original_address=f"0x{address:08X}",
            )
            shared_extra_count += 1
    if shared_extra_count != EXPECTED_SHARED_COMMAND_EXTRAS:
        raise BuildError(f"共有command余剰件数が不正です: {shared_extra_count}")
    if len(archive) != EXPECTED_ARCHIVE_CONSUMERS:
        raise BuildError(f"Archive consumer件数が不正です: {len(archive)}")
    return archive, kind9


def _allocate_runtime_ids(
    encounters: Sequence[dict[str, str]], archive: Mapping[str, ArchiveReason]
) -> dict[str, tuple[int, int, str]]:
    by_original: dict[int, list[str]] = defaultdict(list)
    by_key = {row["encounter_key"]: row for row in encounters}
    for row in encounters:
        by_original[int(row["trainer_id"])].append(row["encounter_key"])

    allocations: dict[str, tuple[int, int, str]] = {}
    duplicate_reallocate: list[str] = []
    reserved_reallocate: list[str] = []
    for original_id, keys in sorted(by_original.items()):
        ordered = sorted(keys)
        if len(ordered) == 1:
            key = ordered[0]
            if original_id in RESERVED_RUNTIME_TRAINER_IDS:
                reserved_reallocate.append(key)
                continue
            reason = "RETAIN_KANTO_ALLOCATED_ID" if original_id >= 4096 else "RETAIN_UNIQUE_ORIGINAL_ID"
            allocations[key] = (original_id, original_id, reason)
            continue
        canonical_candidates = [key for key in ordered if key not in archive]
        if not canonical_candidates:
            raise BuildError(f"重複ID {original_id} に非Archive ownerがありません")
        canonical = canonical_candidates[0]
        allocations[canonical] = (
            original_id,
            original_id,
            "RETAIN_FIRST_CANONICAL_NON_ARCHIVE_OWNER",
        )
        duplicate_reallocate.extend(key for key in ordered if key != canonical)

    used_original_ids = set(by_original)
    available = [
        value
        for value in range(ARCHIVE_BAND_START, ARCHIVE_BAND_END + 1)
        if value not in used_original_ids
    ]
    next_available = iter(available)
    for key in sorted(duplicate_reallocate):
        runtime_id = next(next_available)
        original_id = int(by_key[key]["trainer_id"])
        allocations[key] = (
            original_id,
            runtime_id,
            "REALLOCATE_DUPLICATE_TO_UNUSED_BAND",
        )
    for key in sorted(reserved_reallocate):
        runtime_id = next(next_available)
        original_id = int(by_key[key]["trainer_id"])
        allocations[key] = (
            original_id,
            runtime_id,
            "REALLOCATE_RESERVED_CFRU_TRAINER_ID",
        )
    reallocation_count = len(duplicate_reallocate) + len(reserved_reallocate)
    if reallocation_count > len(available):
        raise BuildError("trainer ID未使用帯が不足しています")
    if len(duplicate_reallocate) != EXPECTED_DUPLICATE_REALLOCATIONS:
        raise BuildError(
            f"重複trainer ID再割当件数が不正です: {len(duplicate_reallocate)}"
        )
    if len(reserved_reallocate) != EXPECTED_RESERVED_REALLOCATIONS:
        raise BuildError(
            f"予約trainer ID再割当件数が不正です: {len(reserved_reallocate)}"
        )
    runtime_ids = [runtime for _, runtime, _ in allocations.values()]
    if len(runtime_ids) != len(set(runtime_ids)):
        raise BuildError("runtime trainer IDが一意ではありません")
    return allocations


def _archive_unlock(original: str, index: int) -> str:
    preserved = original.strip() or "TRUE"
    return f"ARCHIVE_REMATCH_AVAILABLE && ARCHIVE_ENTRY_{index:04d}_UNLOCKED && ({preserved})"


def _normalize(
    union: Mapping[str, SourceTable],
    archive: Mapping[str, ArchiveReason],
    kind9: set[str],
    allocations: Mapping[str, tuple[int, int, str]],
) -> tuple[dict[str, SourceTable], list[dict[str, object]], list[dict[str, object]]]:
    source_encounters = union["trainer_encounters.csv"]
    encounters = [copy.deepcopy(row) for row in source_encounters.rows]
    parties = [copy.deepcopy(row) for row in union["trainer_parties.csv"].rows]
    party_by_encounter = {row["encounter_key"]: row for row in parties}
    archive_indices = {key: index for index, key in enumerate(sorted(archive), 1)}

    ledger: list[dict[str, object]] = []
    consumers: list[dict[str, object]] = []
    for row in encounters:
        key = row["encounter_key"]
        original_id, runtime_id, allocation_reason = allocations[key]
        original_battle_type = row["battle_type"]
        original_physical_map = row["physical_map_key"]
        original_script = row["script_key"]
        original_defeat = row["defeat_state_key"]
        original_unlock = row["unlock_expression"]
        row["trainer_id"] = str(runtime_id)
        row["original_trainer_id"] = str(original_id)
        row["runtime_trainer_id"] = str(runtime_id)
        row["trainer_id_allocation_reason"] = allocation_reason
        action = "PRESERVE_ORIGINAL_CONSUMER"
        consumer_key = ""
        original_owner = key
        if key in kind9:
            row["battle_type"] = "TRAINER_BATTLE_EARLY_RIVAL"
            row["status"] = "READY_TO_SERIALIZE"
            row["notes"] += " | exact ROM audit: kind 9 EARLY_RIVAL/SINGLE"
            action = "NORMALIZE_KIND9_EARLY_RIVAL_SINGLE"
        if key in archive:
            reason = archive[key]
            index = archive_indices[key]
            consumer_key = f"ARCHIVE_REMATCH_{index:04d}"
            battle_format = party_by_encounter[key]["battle_format"]
            row["physical_map_key"] = "VEGA_ARCHIVE_REMATCH"
            row["group_id"] = ""
            row["map_id"] = ""
            row["root_kind"] = "archive_rematch"
            row["root_index"] = str(index)
            for field in ("local_id", "x", "y", "elevation", "graphics_id"):
                row[field] = ""
            row["movement_type"] = "ARCHIVE_MENU_CONSUMER"
            row["sight_range"] = "0"
            row["script_key"] = f"SCRIPT_{consumer_key}"
            row["battle_type"] = (
                "TRAINER_BATTLE_DOUBLE" if battle_format == "DOUBLE" else "TRAINER_BATTLE_SINGLE"
            )
            row["initial_or_rematch"] = "REMATCH"
            row["rematch_tier"] = "ARCHIVE_REMATCH"
            row["mandatory"] = "false"
            row["avoidable_path_evidence"] = "ARCHIVE_MENU_OPTIONAL"
            row["unlock_expression"] = _archive_unlock(original_unlock, index)
            row["defeat_state_key"] = f"FLAG_{consumer_key}_DEFEATED"
            row["status"] = "READY_TO_SERIALIZE"
            row["evidence"] += (
                f"; original command preserved; archive_consumer={consumer_key}; "
                f"archive_reason={reason.kind}"
            )
            row["notes"] += " | original ROM command non-destructive ARCHIVE_REMATCH normalization"
            action = f"MOVE_TO_ARCHIVE_REMATCH:{reason.kind}"
            original_owner = reason.original_owner
            consumers.append(
                {
                    "consumer_key": consumer_key,
                    "consumer_index": index,
                    "encounter_key": key,
                    "runtime_trainer_id": runtime_id,
                    "original_trainer_id": original_id,
                    "original_owner": reason.original_owner,
                    "normalization_reason": reason.kind,
                    "original_command": reason.original_command,
                    "original_address": reason.original_address,
                    "battle_format": battle_format,
                    "battle_type": row["battle_type"],
                    "unlock_expression": row["unlock_expression"],
                    "defeat_state_key": row["defeat_state_key"],
                    "party_key": row["party_key"],
                    "dialogue_set_key": row["dialogue_set_key"],
                    "reward_key": row["reward_key"],
                    "gimmick_key": party_by_encounter[key]["gimmick_key"],
                }
            )
        ledger.append(
            {
                "encounter_key": key,
                "normalization_action": action,
                "original_trainer_id": original_id,
                "runtime_trainer_id": runtime_id,
                "trainer_id_allocation_reason": allocation_reason,
                "original_battle_type": original_battle_type,
                "normalized_battle_type": row["battle_type"],
                "original_physical_map_key": original_physical_map,
                "normalized_physical_map_key": row["physical_map_key"],
                "original_script_key": original_script,
                "normalized_script_key": row["script_key"],
                "original_owner": original_owner,
                "archive_consumer_key": consumer_key,
                "unlock_expression": row["unlock_expression"],
                "original_defeat_state_key": original_defeat,
                "normalized_defeat_state_key": row["defeat_state_key"],
            }
        )

    binding_rows = [copy.deepcopy(row) for row in union["trainer_physical_bindings.csv"].rows]
    binding_by_key = {row["encounter_key"]: row for row in binding_rows}
    for key, row in binding_by_key.items():
        original_id, runtime_id, allocation_reason = allocations[key]
        row["trainer_id"] = str(runtime_id)
        row["original_trainer_id"] = str(original_id)
        row["runtime_trainer_id"] = str(runtime_id)
        row["trainer_id_allocation_reason"] = allocation_reason
        if key in kind9:
            row["status"] = "READY_TO_SERIALIZE"
            row["evidence"] += "; exact ROM kind=9 TRAINER_BATTLE_EARLY_RIVAL"
        if key in archive:
            index = archive_indices[key]
            consumer_key = f"ARCHIVE_REMATCH_{index:04d}"
            row["map_event_owner"] = "VEGA_ARCHIVE_REMATCH"
            row["object_or_script_address"] = consumer_key
            row["rematch_state_key"] = f"STATE_{consumer_key}"
            row["defeat_flag_key"] = f"FLAG_{consumer_key}_DEFEATED"
            row["serializer_owner"] = "scripts/build_trainer_changekit_content.py"
            row["status"] = "READY_TO_SERIALIZE"
            row["evidence"] += f"; original binding preserved; archive_consumer={consumer_key}"

    normalized: dict[str, SourceTable] = {}
    encounter_extra = (
        "original_trainer_id",
        "runtime_trainer_id",
        "trainer_id_allocation_reason",
    )
    binding_extra = encounter_extra
    normalized["trainer_encounters.csv"] = SourceTable(
        source_encounters.fields + encounter_extra,
        tuple(sorted(encounters, key=lambda row: row["encounter_key"])),
    )
    normalized["trainer_physical_bindings.csv"] = SourceTable(
        union["trainer_physical_bindings.csv"].fields + binding_extra,
        tuple(sorted(binding_rows, key=lambda row: row["encounter_key"])),
    )
    for filename in DATA_FILES:
        if filename in normalized:
            continue
        table = union[filename]
        rows = [copy.deepcopy(row) for row in table.rows]
        if filename == "coverage.csv":
            for row in rows:
                key = row["encounter_key"]
                if key in archive:
                    row["decision"] = "READY_ARCHIVE_REMATCH_NON_DESTRUCTIVE"
                    row["notes"] += f"; archive_consumer=ARCHIVE_REMATCH_{archive_indices[key]:04d}"
                elif key in kind9:
                    row["decision"] = "READY_EXACT_KIND9_EARLY_RIVAL"
        sort_fields = {
            "coverage.csv": ("encounter_key",),
            "trainer_parties.csv": ("encounter_key",),
            "trainer_party_members.csv": ("party_key", "slot"),
            "trainer_dialogue.csv": ("encounter_key", "state_key"),
            "trainer_rewards.csv": ("encounter_key",),
            "trainer_gimmicks.csv": ("encounter_key",),
        }[filename]
        if filename == "trainer_party_members.csv":
            rows.sort(key=lambda row: (row["party_key"], int(row["slot"])))
        else:
            rows.sort(key=lambda row: tuple(row[field] for field in sort_fields))
        normalized[filename] = SourceTable(table.fields, tuple(rows))
    return normalized, sorted(ledger, key=lambda row: str(row["encounter_key"])), sorted(
        consumers, key=lambda row: int(row["consumer_index"])
    )


def _build_runtime_consumers(
    source_encounters: Sequence[Mapping[str, str]],
    normalized: Mapping[str, SourceTable],
    archive_consumers: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    source_by_key = {row["encounter_key"]: row for row in source_encounters}
    encounter_by_key = {
        row["encounter_key"]: row for row in normalized["trainer_encounters.csv"].rows
    }
    party_by_key = {
        row["encounter_key"]: row for row in normalized["trainer_parties.csv"].rows
    }
    gimmick_by_key = {
        row["encounter_key"]: row for row in normalized["trainer_gimmicks.csv"].rows
    }
    binding_by_key = {
        row["encounter_key"]: row
        for row in normalized["trainer_physical_bindings.csv"].rows
    }
    archive_by_key = {str(row["encounter_key"]): row for row in archive_consumers}
    result: list[dict[str, object]] = []
    for key in sorted(encounter_by_key):
        source = source_by_key[key]
        encounter = encounter_by_key[key]
        party = party_by_key[key]
        gimmick = gimmick_by_key[key]
        binding = binding_by_key[key]
        if key in archive_by_key:
            mode = "ARCHIVE"
            command_address = str(archive_by_key[key]["consumer_key"])
            original_binding_owner = str(archive_by_key[key]["original_owner"])
        elif encounter["region"] == "KANTO":
            mode = "KANTO_NEW"
            command_address = binding["object_or_script_address"]
            original_binding_owner = encounter["physical_map_key"]
        else:
            mode = "CANONICAL"
            command_address = f"0x{_instruction(source):08X}"
            original_binding_owner = key
        battle_type = encounter["battle_type"]
        if battle_type not in TRAINERBATTLE_KIND:
            raise BuildError(f"trainerbattle kind未定義です: {key} {battle_type}")
        template = SOURCE_TEMPLATE_RE.search(source.get("notes", ""))
        result.append(
            {
                "encounter_key": key,
                "runtime_trainer_id": encounter["runtime_trainer_id"],
                "source_trainer_id": _physical_trainer_id(source),
                "original_trainer_id": encounter["original_trainer_id"],
                "binding_mode": mode,
                "command_address": command_address,
                "trainerbattle_kind": TRAINERBATTLE_KIND[battle_type],
                "battle_type": battle_type,
                "battle_format": party["battle_format"],
                "party_key": party["party_key"],
                "ai_profile_key": encounter["ai_profile_key"],
                "gimmick_type": gimmick["gimmick_type"],
                "gimmick_user_party_slot": gimmick["user_party_slot"],
                "gimmick_required_item_key": gimmick["required_item_key"],
                "source_template_id": (
                    template.group(1) if template else f"INSTANCE::{party['party_key']}"
                ),
                "physical_flag": encounter["defeat_state_key"],
                "unlock_expression": encounter["unlock_expression"],
                "dialogue_set_key": encounter["dialogue_set_key"],
                "reward_key": encounter["reward_key"],
                "original_binding_owner": original_binding_owner,
            }
        )
    return result


def _registry_values(path: Path, key_column: str) -> set[str]:
    table = _read_csv(path)
    if key_column not in table.fields:
        raise BuildError(f"registry key列がありません: {path} / {key_column}")
    return {row[key_column] for row in table.rows}


def _validate_content(
    input_root: Path,
    normalized: Mapping[str, SourceTable],
    ledger: Sequence[Mapping[str, object]],
    consumers: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    encounters = list(normalized["trainer_encounters.csv"].rows)
    parties = list(normalized["trainer_parties.csv"].rows)
    members = list(normalized["trainer_party_members.csv"].rows)
    bindings = list(normalized["trainer_physical_bindings.csv"].rows)
    dialogues = list(normalized["trainer_dialogue.csv"].rows)
    rewards = list(normalized["trainer_rewards.csv"].rows)
    gimmicks = list(normalized["trainer_gimmicks.csv"].rows)
    coverage = list(normalized["coverage.csv"].rows)
    directives = list(
        _read_csv(input_root / GLOBAL_DIR / "global/encounter_directives.csv").rows
    )

    if len(encounters) != EXPECTED_ENCOUNTERS or len(members) != EXPECTED_MEMBERS:
        raise BuildError(f"union件数が不正です: encounters={len(encounters)} members={len(members)}")
    for rows, field, label in (
        (encounters, "encounter_key", "encounter"),
        (parties, "party_key", "party"),
        (parties, "encounter_key", "party encounter"),
        (bindings, "encounter_key", "binding"),
        (rewards, "encounter_key", "reward"),
        (gimmicks, "encounter_key", "gimmick"),
        (coverage, "encounter_key", "coverage"),
    ):
        _validate_unique(rows, field, label)
    encounter_keys = {row["encounter_key"] for row in encounters}
    if any({row["encounter_key"] for row in rows} != encounter_keys for rows in (parties, bindings, rewards, gimmicks, coverage)):
        raise BuildError("encounter coverage集合が一致しません")
    if {row["encounter_key"] for row in dialogues} != encounter_keys:
        raise BuildError("dialogue coverage集合が一致しません")
    if len(directives) != EXPECTED_ENCOUNTERS or {
        row["encounter_key"] for row in directives
    } != encounter_keys:
        raise BuildError("Task01 encounter directive coverageが一致しません")

    runtime_ids = [int(row["runtime_trainer_id"]) for row in encounters]
    if len(runtime_ids) != len(set(runtime_ids)):
        raise BuildError("runtime trainer IDが重複しています")
    if max(runtime_ids) != EXPECTED_MAX_RUNTIME_ID:
        raise BuildError(f"runtime trainer ID最大値が不正です: {max(runtime_ids)}")
    reallocations = sum(
        int(row["runtime_trainer_id"]) != int(row["original_trainer_id"])
        for row in encounters
    )
    if reallocations != EXPECTED_REALLOCATIONS:
        raise BuildError(f"runtime trainer ID再割当件数が不正です: {reallocations}")

    party_by_key = {row["party_key"]: row for row in parties}
    party_by_encounter = {row["encounter_key"]: row for row in parties}
    binding_by_encounter = {row["encounter_key"]: row for row in bindings}
    reward_by_encounter = {row["encounter_key"]: row for row in rewards}
    gimmick_by_encounter = {row["encounter_key"]: row for row in gimmicks}
    dialogue_by_encounter: dict[str, list[dict[str, str]]] = defaultdict(list)
    for dialogue in dialogues:
        dialogue_by_encounter[dialogue["encounter_key"]].append(dialogue)
    members_by_party: dict[str, list[dict[str, str]]] = defaultdict(list)
    for member in members:
        members_by_party[member["party_key"]].append(member)
    for party_key, party in party_by_key.items():
        party_members = sorted(members_by_party.get(party_key, ()), key=lambda row: int(row["slot"]))
        size = int(party["party_size"])
        slots = [int(row["slot"]) for row in party_members]
        if slots != list(range(1, size + 1)):
            raise BuildError(f"party slotが連続していません: {party_key} {slots}")
        # UNIQUE_BOSS/PRESERVE_EXISTING_RECORDも入力上のprovenance labelとして保持する。
        # party_keyとencounter_keyの双方が1:1なので、実データ共有は発生しない。
        for member in party_members:
            level = int(member["level"])
            if not int(party["level_floor"]) <= level <= int(party["level_cap"]):
                raise BuildError(f"member levelがparty帯外です: {party_key}:{member['slot']}")
            iv = int(member["iv_floor"])
            evs = [int(member[field]) for field in ("hp_ev", "atk_ev", "def_ev", "spa_ev", "spd_ev", "spe_ev")]
            if not 0 <= iv <= 31 or any(not 0 <= ev <= 252 for ev in evs) or sum(evs) > 510:
                raise BuildError(f"IV/EVが不正です: {party_key}:{member['slot']}")
            if not member["legality_evidence"].strip():
                raise BuildError(f"legality evidenceがありません: {party_key}:{member['slot']}")

    registry_root = input_root / AUTHORING_DIR / "source/v5/registries"
    registries = {
        key: _registry_values(registry_root / filename, key)
        for key, filename in REGISTRY_FILES.items()
    }
    for member in members:
        checks = (
            ("species_key", member["species_key"]),
            ("ability_key", member["ability_key"]),
            ("nature_key", member["nature_key"]),
            ("item_key", member["held_item_key"]),
            *(("move_key", member[f"move{slot}_key"]) for slot in range(1, 5)),
        )
        for registry, value in checks:
            if value not in registries[registry]:
                raise BuildError(f"registry未登録です: {registry}={value}")
    for encounter in encounters:
        key = encounter["encounter_key"]
        party = party_by_encounter[key]
        binding = binding_by_encounter[key]
        reward = reward_by_encounter[key]
        gimmick = gimmick_by_encounter[key]
        if party["party_key"] != encounter["party_key"]:
            raise BuildError(f"encounter/party key不一致: {key}")
        if party["ai_profile_key"] != encounter["ai_profile_key"]:
            raise BuildError(f"encounter/party AI不一致: {key}")
        if (
            binding["party_pointer"].startswith("ALLOCATOR::PARTY::")
            and binding["party_pointer"].split("::")[-1] != encounter["party_key"]
        ):
            raise BuildError(f"binding party pointer不一致: {key}")
        if binding["defeat_flag_key"] != encounter["defeat_state_key"]:
            raise BuildError(f"binding defeat flag不一致: {key}")
        if reward["reward_key"] != encounter["reward_key"]:
            raise BuildError(f"encounter/reward key不一致: {key}")
        if gimmick["encounter_key"] != key:
            raise BuildError(f"encounter/gimmick key不一致: {key}")
        if any(dialogue["dialogue_set_key"] != encounter["dialogue_set_key"] for dialogue in dialogue_by_encounter[key]):
            raise BuildError(f"encounter/dialogue set不一致: {key}")
        for raw_items in (encounter["trainer_item_keys"], party["trainer_item_keys"]):
            try:
                trainer_items = json.loads(raw_items)
            except json.JSONDecodeError as exc:
                raise BuildError(f"trainer_item_keys JSON不正: {key}") from exc
            if not isinstance(trainer_items, list) or any(
                item not in registries["item_key"] for item in trainer_items
            ):
                raise BuildError(f"trainer itemが未登録です: {key}")
    for gimmick in gimmicks:
        party = next(row for row in parties if row["encounter_key"] == gimmick["encounter_key"])
        slot = int(gimmick["user_party_slot"])
        if gimmick["gimmick_type"] == "NONE":
            if slot != 0:
                raise BuildError(f"NONE gimmick slotが0ではありません: {gimmick['encounter_key']}")
        elif not 1 <= slot <= int(party["party_size"]):
            raise BuildError(f"gimmick slotがparty外です: {gimmick['encounter_key']}")
        if gimmick["required_item_key"] not in registries["item_key"]:
            raise BuildError(f"gimmick itemが未登録です: {gimmick['encounter_key']}")

    encounter_by_key = {row["encounter_key"]: row for row in encounters}
    for party in parties:
        encounter = encounter_by_key[party["encounter_key"]]
        expected_format = "DOUBLE" if "DOUBLE" in encounter["battle_type"] else "SINGLE"
        if party["battle_format"] != expected_format:
            raise BuildError(
                f"party/encounter format不一致: {party['encounter_key']} "
                f"{party['battle_format']} != {encounter['battle_type']}"
            )
    if len(consumers) != EXPECTED_ARCHIVE_CONSUMERS:
        raise BuildError(f"Archive件数が不正です: {len(consumers)}")
    if [int(row["consumer_index"]) for row in consumers] != list(range(1, EXPECTED_ARCHIVE_CONSUMERS + 1)):
        raise BuildError("Archive consumer indexが連続していません")
    if len({row["defeat_state_key"] for row in consumers}) != len(consumers):
        raise BuildError("Archive defeat stateが一意ではありません")
    consumer_by_encounter = {str(row["encounter_key"]): row for row in consumers}
    alias = consumer_by_encounter.get("ENC_TOHOKU_REF_1012")
    if not alias or alias["battle_format"] != "DOUBLE" or "ENC_TOHOKU_REF_1013" not in str(alias["original_owner"]):
        raise BuildError("REF_1012のSINGLE/DOUBLE alias正規化が不正です")

    mechanics = Counter(row["gimmick_type"] for row in gimmicks)
    formats = Counter(row["battle_format"] for row in parties)
    archive_reasons = Counter(str(row["normalization_reason"]) for row in consumers)
    return {
        "schema_version": 1,
        "encounter_count": len(encounters),
        "party_count": len(parties),
        "member_count": len(members),
        "dialogue_row_count": len(dialogues),
        "reward_count": len(rewards),
        "gimmick_count": len(gimmicks),
        "archive_consumer_count": len(consumers),
        "archive_reason_counts": dict(sorted(archive_reasons.items())),
        "battle_format_counts": dict(sorted(formats.items())),
        "gimmick_type_counts": dict(sorted(mechanics.items())),
        "kind9_early_rival_count": sum(
            row["normalization_action"] == "NORMALIZE_KIND9_EARLY_RIVAL_SINGLE" for row in ledger
        ),
        "runtime_trainer_id_unique_count": len(set(runtime_ids)),
        "runtime_trainer_id_reallocation_count": reallocations,
        "runtime_trainer_id_max": max(runtime_ids),
        "trainer_table_count": max(runtime_ids) + 1,
        "original_zip_mutated": False,
        "validation": "PASS",
    }


def build(repo: Path, input_root: Path, output: Path) -> dict[str, object]:
    union = _load_union(input_root)
    encounters = list(union["trainer_encounters.csv"].rows)
    _validate_unique(encounters, "encounter_key", "union encounter")
    inventory = _load_inventory(repo)
    archive, kind9 = _classify_archives(encounters, inventory)
    allocations = _allocate_runtime_ids(encounters, archive)
    normalized, ledger, consumers = _normalize(union, archive, kind9, allocations)
    coverage = _validate_content(input_root, normalized, ledger, consumers)
    runtime_consumers = _build_runtime_consumers(encounters, normalized, consumers)
    if len(runtime_consumers) != EXPECTED_ENCOUNTERS:
        raise BuildError(f"runtime consumer件数が不正です: {len(runtime_consumers)}")

    source_files: list[Path] = []
    for task_dir in TASK_DIRS:
        source_files.extend(input_root / task_dir / "data" / filename for filename in DATA_FILES)
        source_files.append(input_root / task_dir / "KIT_MANIFEST.json")
    source_files.extend(
        (
            input_root / GLOBAL_DIR / "KIT_MANIFEST.json",
            input_root / AUTHORING_DIR / "AUTHORING_MANIFEST_SHA256.tsv",
            input_root / AUTHORING_DIR / "BASELINE.json",
        )
    )
    source_files.extend(input_root / GLOBAL_DIR / source for source, _ in GLOBAL_FILES)
    source_files.extend(
        input_root / AUTHORING_DIR / "source/v5/registries" / filename
        for filename in REGISTRY_FILES.values()
    )
    source_files.append(repo / "reports/generated/id_inventory.json")
    # Absolute parent placement differs between the live recovered workspace
    # and a freshly extracted full snapshot.  Sort by the portable manifest
    # path so the generated file remains byte-identical in both layouts.
    source_manifest_inputs = [
        {
            "path": (
                str(path.relative_to(input_root))
                if path.is_relative_to(input_root)
                else str(path.relative_to(repo))
            ),
            "sha256": _sha256(path),
            "size": path.stat().st_size,
        }
        for path in source_files
    ]
    source_manifest_inputs.sort(key=lambda row: str(row["path"]))
    source_manifest = {
        "schema_version": 1,
        "inputs": source_manifest_inputs,
    }

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for filename, table in sorted(normalized.items()):
        _write_csv(output / filename, table.fields, table.rows)
    for source, destination in GLOBAL_FILES:
        table = _read_csv(input_root / GLOBAL_DIR / source)
        _write_csv(output / destination, table.fields, table.rows)
    _write_csv(
        output / "normalization_ledger.csv",
        tuple(ledger[0].keys()),
        ledger,
    )
    _write_csv(
        output / "archive_rematch_consumers.csv",
        tuple(consumers[0].keys()),
        consumers,
    )
    allocation_rows = [
        {
            "encounter_key": key,
            "original_trainer_id": original,
            "runtime_trainer_id": runtime,
            "allocation_reason": reason,
        }
        for key, (original, runtime, reason) in sorted(allocations.items())
    ]
    _write_csv(
        output / "trainer_id_allocations.csv",
        ("encounter_key", "original_trainer_id", "runtime_trainer_id", "allocation_reason"),
        allocation_rows,
    )
    _write_csv(
        output / "trainer_runtime_consumers.csv",
        tuple(runtime_consumers[0].keys()),
        runtime_consumers,
    )
    _write_json(output / "coverage.json", coverage)
    _write_json(output / "source_manifest.json", source_manifest)
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    input_root = (args.input_root or discover_input_root(repo)).resolve()
    output = (args.output or repo / "content/trainer_changekit_final").resolve()
    coverage = build(repo, input_root, output)
    print(json.dumps(coverage, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
