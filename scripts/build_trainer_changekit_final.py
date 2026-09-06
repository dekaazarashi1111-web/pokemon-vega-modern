#!/usr/bin/env python3
"""Trainer ChangeKit Task 01--06をStage 34へ完全serializeする。

入力ChangeKitは変更しない。正規化済み ``content/trainer_changekit_final`` と
Stage 34、clean FireRed日本版Rev.0から、全1302戦に一意な物理consumerを持つ
Stage 35を決定的に再構築する。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _jump_stub,
    _previous_requests,
    _rom_offset,
    _rows,
    _sha,
    _sparse_bps,
    _stable,
    _trampoline,
    _u16,
    _u32,
)
from tools.release.bps import apply_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402
from tools.trainer_final.kanto_events import (  # noqa: E402
    LEGACY_PUBLISHED,
    build_kanto_event_plan,
)


TASK = "USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION"
RAM_LAYOUT_OWNER = "USER_20260819_TRAINER_CHANGEKIT_FINAL"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/34_trainer_v5_tohoku_batch03.gba")
INPUT_META = Path("build/stages/34_trainer_v5_tohoku_batch03.json")
INPUT_ALLOC = Path("build/stages/34_allocation.json")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE17_META = Path("build/stages/17_regression.json")
STAGE17_SYMBOLS = Path("generated/runtime/t17_runtime_symbols.json")
STAGE07_META = Path("build/stages/07_species.json")
ACQUISITION_META = Path("build/stages/26_acquisition_events.json")
SOURCE_DIR = Path("content/trainer_changekit_final")
DIALOGUE_READINGS = Path("content/trainer_changekit_dialogue_readings.csv")
OUTPUT_ROM = Path("build/stages/35_trainer_changekit_final.gba")
OUTPUT_META = Path("build/stages/35_trainer_changekit_final.json")
OUTPUT_ALLOC = Path("build/stages/35_allocation.json")
OUTPUT_PLAN = Path("generated/runtime/trainer_changekit_final_event_plan.json")
OUTPUT_SERIALIZED = Path("generated/runtime/trainer_changekit_final_serialized.json")
OUTPUT_HEADER = Path("generated/runtime/trainer_changekit_final_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/trainer_changekit_final_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/trainer_changekit_final_symbols.json")
OUTPUT_BINDINGS = Path("reports/generated/trainer_changekit_final_bindings.csv")
OUTPUT_REPORT = Path("reports/generated/trainer_changekit_final.md")
OUTPUT_MGBA_QUICK = Path("build/stages/35_mgba_trainer_changekit_quick.json")
OUTPUT_MGBA_FULL = Path("build/stages/35_mgba_trainer_changekit_full.json")
OUTPUT_MGBA_CASES = Path("generated/runtime/trainer_changekit_final_mgba_cases.csv")
PATCH_INCREMENTAL = Path("build/patches/trainer-stage34-to-changekit-final-stage35.bps")
PATCH_CUMULATIVE = Path("build/patches/vega-modern-kanto-v1.4.0-to-trainer-changekit-final-stage35.bps")

EXPECTED_STAGE34_SHA256 = "6cb980539001977a88d92b1388a5d917653a6331a2f17f183c7ac6a683f0bd20"
EXPECTED_CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"

EXPECTED_BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"

ENCOUNTER_COUNT = 1302
PARTY_COUNT = 1302
MEMBER_COUNT = 6490
TRAINER_TABLE_COUNT = 4284
TRAINER_RECORD_SIZE = 32
PARTY_MEMBER_SIZE = 16
SIDECAR_SIZE = 18
ARCHIVE_COUNT = 71
KANTO_COUNT = 201
KANTO_EXISTING_COUNT = 13
KANTO_NEW_COUNT = 188
CANONICAL_COUNT = 1030
PHYSICAL_COMMAND_COUNT = 1302
FLAG_START = 0x0500

PAYLOAD_HEADER_SIZE = 0x200
TRAMPOLINE_SIZES = {"get_rematch": 0x10, "build_trainer_party": 0x10, "save_load": 0x18}
TRAMPOLINE_NAMES = tuple(TRAMPOLINE_SIZES)


def _trampoline_relatives() -> dict[str, int]:
    result: dict[str, int] = {}
    cursor = PAYLOAD_HEADER_SIZE
    for name in TRAMPOLINE_NAMES:
        result[name] = cursor
        cursor += TRAMPOLINE_SIZES[name]
    return result


TRAMPOLINE_RELATIVES = _trampoline_relatives()
CODE_RELATIVE_OFFSET = _align(
    max(TRAMPOLINE_RELATIVES[name] + TRAMPOLINE_SIZES[name] for name in TRAMPOLINE_NAMES), 16
)
ALLOCATION_NAME = "trainer_changekit_final_stage35_payload"

AI_FLAGS = {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5}
GIMMICK_MODE = {"NONE": 0, "MEGA": 1, "Z_MOVE": 2, "DYNAMAX": 3, "TERASTAL": 4}
KIND_SIZES = {0: 14, 1: 18, 2: 18, 3: 10, 4: 18, 5: 14, 6: 22, 7: 18, 8: 22, 9: 14}
DOUBLE_KINDS = {4, 6, 7, 8}

# Stage 34 public hook ABI.
HOOKS = {
    "configure_trainer_battle": (0x0807F948, "TrainerV5Runtime_ConfigureTrainerBattle"),
    "script_flag_get": (0x0807FB04, "TrainerV5Runtime_ScriptFlagGet"),
    "script_flag_set": (0x0807FB1C, "TrainerV5Runtime_ScriptFlagSet"),
    "script_flag_set_alt": (0x0807FB30, "TrainerV5Runtime_ScriptFlagSet"),
    "has_trainer_fought": (0x0807FB44, "TrainerV5Runtime_HasTrainerBeenFought"),
    "set_trainer_flag": (0x0807FB5C, "TrainerV5Runtime_SetTrainerFlag"),
    "clear_trainer_flag": (0x0807FB70, "TrainerV5Runtime_ClearTrainerFlag"),
    "get_rematch": (0x0810D93C, "TrainerV5Runtime_GetRematchTrainerId"),
    "build_trainer_party": (0x090DD2A4, "TrainerV5Runtime_BuildTrainerPartySetup"),
}

GET_TRAINER_FLAG_ADDRESS = 0x0807F7D9
FLAG_SET_ADDRESS = 0x0806DE75
FLAG_CLEAR_ADDRESS = 0x0806DE9D
FLAG_GET_ADDRESS = 0x0806DEC5
CONFIGURE_TRAINER_BATTLE_ADDRESS = 0x0911E0D9
CALCULATE_MON_STATS_ADDRESS = 0x090D939D
ENEMY_PARTY_ADDRESS = 0x02023F8C
TRAINER_OPPONENT_A_ADDRESS = 0x020385E2
CONFIGURE_NEXT_BATTLE_POLICY_ADDRESS = 0x091261F5
CFRU_PENDING_CLEAR_ADDRESS = 0x0910EE79
BATTLE_POLICY_ADDRESSES = {
    "CAN_MEGA": 0x09126B61,
    "MARK_MEGA": 0x09126B8D,
    "CAN_Z": 0x09126BB5,
    "MARK_Z": 0x09126BE1,
    "CAN_DYNAMAX": 0x09126C09,
    "MARK_DYNAMAX": 0x09126C35,
    "CAN_TERA": 0x09126C5D,
    "MARK_TERA": 0x09126C89,
    "BEGIN": 0x091266F5,
    "END": 0x09126961,
}
BATTLERS_COUNT_ADDRESS = 0x02023B2C
ABSENT_BATTLER_FLAGS_ADDRESS = 0x02023CD0
BATTLER_PARTY_INDEXES_ADDRESS = 0x02023B2E
ACTIVE_BATTLER_ADDRESS = 0x02023B24
BATTLE_MONS_ADDRESS = 0x02023B44
LOAD_PROPER_ABILITY_BATTLE_DATA_ADDRESS = 0x090BB34D
TRAINER_CHANGEKIT_STATE_ADDRESS = 0x0203EDC0
TRAINER_CHANGEKIT_STATE_SIZE = 48


class FinalBuildError(ValueError):
    """入力、ABI、物理binding、または出力の完了契約違反。"""


def _fail(message: str) -> NoReturn:
    raise FinalBuildError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _validate_runtime_ram_layout(root: Path) -> dict[str, Any]:
    """Fail closed unless the explicit EWRAM storage owns an unshared range."""
    path = root / "config/ram_layout.csv"
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
    except OSError as exc:
        _fail(f"runtime RAM ledger is unavailable: {exc}")
    required = {
        "address_space", "start", "end_exclusive", "size", "owner",
        "symbol", "status",
    }
    if not rows or not required.issubset(rows[0]):
        _fail("runtime RAM ledger schema differs")

    parsed: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        try:
            start = int(row["start"], 0)
            end = int(row["end_exclusive"], 0)
            size = int(row["size"], 0)
        except (KeyError, ValueError) as exc:
            _fail(f"runtime RAM ledger row {index} is invalid: {exc}")
        if start >= end or end - start != size:
            _fail(f"runtime RAM ledger row {index} has an inconsistent range")
        parsed.append({**row, "start_value": start, "end_value": end})

    owned = [
        row for row in parsed
        if row["owner"] == RAM_LAYOUT_OWNER
        and row["symbol"] == "gTrainerChangeKitRuntimeState"
        and row["status"] == "LIVE"
    ]
    if len(owned) != 1:
        _fail(f"runtime RAM ledger ownership row differs: {len(owned)}")
    target = owned[0]
    expected_end = TRAINER_CHANGEKIT_STATE_ADDRESS + TRAINER_CHANGEKIT_STATE_SIZE
    if (
        target["address_space"] != "EWRAM"
        or target["start_value"] != TRAINER_CHANGEKIT_STATE_ADDRESS
        or target["end_value"] != expected_end
        or not (0x02000000 <= target["start_value"] < target["end_value"] <= 0x02040000)
    ):
        _fail("runtime RAM ledger range differs from the production ABI")

    overlaps = [
        row for row in parsed
        if row is not target
        and row["status"] == "LIVE"
        and row["address_space"] == target["address_space"]
        and target["start_value"] < row["end_value"]
        and row["start_value"] < target["end_value"]
    ]
    if overlaps:
        _fail(
            "runtime RAM ledger overlaps another live owner: "
            + ", ".join(f"{row['owner']}/{row['symbol']}" for row in overlaps)
        )

    contract = _read_json(
        root / "overlays/trainer_changekit_final_runtime/hook_contract_stage34.json"
    )
    address = int(
        contract.get("runtime_defines", {}).get(
            "VEGA_TRAINER_CHANGEKIT_STATE_ADDRESS", "-1"
        ),
        0,
    )
    if address != TRAINER_CHANGEKIT_STATE_ADDRESS:
        _fail("runtime RAM hook contract differs from the ledger")
    return {
        "ledger": path.relative_to(root).as_posix(),
        "address_space": target["address_space"],
        "start": target["start_value"],
        "end_exclusive": target["end_value"],
        "size": TRAINER_CHANGEKIT_STATE_SIZE,
        "owner": target["owner"],
        "symbol": target["symbol"],
        "live_overlap_count": 0,
    }


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str] | None = None) -> bytes:
    if not rows:
        return b""
    names = list(fields or rows[0].keys())
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in names})
    return stream.getvalue().encode("utf-8")


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT, timeout: int | None = None) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=cwd, text=True, capture_output=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        _fail(f"{label} timed out after {timeout}s: {exc}")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _index(rows: Sequence[Mapping[str, str]], key: str, label: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            _fail(f"{label}: missing or duplicate {key}: {value!r}")
        result[value] = row
    return result


@dataclass(frozen=True)
class Fixup:
    offset: int
    label: str
    thumb: bool = False


class Blob:
    """Payload-relative data with deterministic symbolic pointer fixups."""

    def __init__(self) -> None:
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[Fixup] = []

    def align(self, alignment: int = 4, fill: int = 0) -> None:
        if alignment <= 0 or alignment & (alignment - 1):
            _fail(f"blob alignment is not a power of two: {alignment}")
        while len(self.data) % alignment:
            self.data.append(fill)

    def mark(self, label: str, alignment: int = 1) -> int:
        if label in self.labels:
            _fail(f"duplicate blob label: {label}")
        self.align(alignment)
        self.labels[label] = len(self.data)
        return len(self.data)

    def add(self, label: str, raw: bytes, alignment: int = 4) -> int:
        offset = self.mark(label, alignment)
        self.data.extend(raw)
        return offset

    def append(self, raw: bytes) -> int:
        offset = len(self.data)
        self.data.extend(raw)
        return offset

    def pointer(self, offset: int, label: str, *, thumb: bool = False) -> None:
        if offset < 0 or offset + 4 > len(self.data):
            _fail(f"fixup outside blob: {offset:#x} -> {label}")
        self.fixups.append(Fixup(offset, label, thumb))

    def finish(self, absolute_base: int) -> bytes:
        result = bytearray(self.data)
        for fixup in self.fixups:
            if fixup.label not in self.labels:
                _fail(f"unresolved blob label: {fixup.label}")
            address = absolute_base + self.labels[fixup.label]
            if fixup.thumb:
                address |= 1
            struct.pack_into("<I", result, fixup.offset, address)
        return bytes(result)


def _input_contract(root: Path) -> dict[str, Any]:
    stage = (root / INPUT_ROM).read_bytes()
    base = (root / BASE_ROM).read_bytes()
    clean = (root / CLEAN_ROM).read_bytes()
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_STAGE34_SHA256:
        _fail("Stage 34 input size/hash differs")
    if len(base) != ROM_SIZE or _sha(base) != EXPECTED_BASE_SHA256:
        _fail("v1.4.0 base size/hash differs")
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != EXPECTED_CLEAN_SHA256:
        _fail("clean FireRed JPN Rev.0 size/hash differs")
    input_meta = _read_json(root / INPUT_META)
    previous_alloc = _read_json(root / INPUT_ALLOC)
    if input_meta.get("output", {}).get("sha256") != EXPECTED_STAGE34_SHA256:
        _fail("Stage 34 metadata hash differs")
    if previous_alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage 34 allocator is not overlap-free")
    return {
        "stage": stage,
        "base": base,
        "clean": clean,
        "input_meta": input_meta,
        "previous_alloc": previous_alloc,
        "trainer_meta": _read_json(root / STAGE17_META),
        "stage17_symbols": _read_json(root / STAGE17_SYMBOLS),
        "species_meta": _read_json(root / STAGE07_META),
        "acquisition_meta": _read_json(root / ACQUISITION_META),
    }


def _load_live_registry(root: Path, path: str, key: str) -> dict[str, int]:
    rows = _rows(root / path)
    indexed = _index(rows, key, path)
    return {name: int(row["id"], 0) for name, row in indexed.items()}


def _discover_authoring_registry(root: Path) -> Path:
    candidates = (
        root.parent / "integration_inputs/Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819/source/v5/registries",
        root.parent.parent / "integration_inputs/Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819/source/v5/registries",
        root / "userfile/imports/trainer_changekit_final/integration_inputs/Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819/source/v5/registries",
    )
    for candidate in candidates:
        if (candidate / "nature_ids.csv").is_file():
            return candidate
    from scripts.prepare_trainer_unit_inputs import restore_inputs
    return restore_inputs(root, profile="registries") / "Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819/source/v5/registries"


def _discover_task06(root: Path) -> Path:
    candidates = (
        root.parent / "integration_inputs/VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
        root.parent.parent / "integration_inputs/VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
        root / "userfile/imports/trainer_changekit_final/integration_inputs/VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
    )
    for candidate in candidates:
        if (candidate / "KIT_MANIFEST.json").is_file():
            return candidate
    from scripts.prepare_trainer_unit_inputs import restore_inputs
    return restore_inputs(root, profile="task06") / "VEGA_TRAINER_CHANGEKIT_TASK06_KANTO"


def load_source(root: Path, stage: bytes, species_meta: Mapping[str, Any]) -> dict[str, Any]:
    source = root / SOURCE_DIR
    coverage = _read_json(source / "coverage.json")
    if coverage.get("validation") != "PASS" or (
        coverage.get("encounter_count"), coverage.get("party_count"), coverage.get("member_count")
    ) != (ENCOUNTER_COUNT, PARTY_COUNT, MEMBER_COUNT):
        _fail("normalized ChangeKit coverage differs")
    encounters = _rows(source / "trainer_encounters.csv")
    parties = _rows(source / "trainer_parties.csv")
    members = _rows(source / "trainer_party_members.csv")
    dialogues = _rows(source / "trainer_dialogue.csv")
    rewards = _rows(source / "trainer_rewards.csv")
    gimmicks = _rows(source / "trainer_gimmicks.csv")
    consumers = _rows(source / "trainer_runtime_consumers.csv")
    archives = _rows(source / "archive_rematch_consumers.csv")
    if tuple(map(len, (encounters, parties, members, dialogues, rewards, gimmicks, consumers, archives))) != (
        1302, 1302, 6490, 4662, 1302, 1302, 1302, 71
    ):
        _fail("normalized ChangeKit table cardinality differs")
    encounter_by_key = _index(encounters, "encounter_key", "encounters")
    party_by_key = _index(parties, "party_key", "parties")
    consumer_by_key = _index(consumers, "encounter_key", "runtime consumers")
    gimmick_by_key = _index(gimmicks, "encounter_key", "gimmicks")
    encounter_keys = set(encounter_by_key)
    if encounter_keys != set(consumer_by_key) or encounter_keys != set(gimmick_by_key):
        _fail("normalized encounter/consumer/gimmick key sets differ")
    runtime_ids = [int(row["runtime_trainer_id"], 0) for row in consumers]
    if len(set(runtime_ids)) != ENCOUNTER_COUNT or max(runtime_ids) != TRAINER_TABLE_COUNT - 1:
        _fail("runtime trainer IDs are not unique or do not cover max 4283")

    registries = {
        "species": _load_live_registry(root, "manifests/species_ids.csv", "species_key"),
        "ability": _load_live_registry(root, "manifests/ability_ids.csv", "ability_key"),
        "move": _load_live_registry(root, "manifests/move_ids.csv", "move_key"),
        "item": _load_live_registry(root, "manifests/item_ids.csv", "item_key"),
    }
    authoring = _discover_authoring_registry(root)
    registries["nature"] = {
        row["nature_key"]: int(row["id"], 0)
        for row in _rows(authoring / "nature_ids.csv")
    }
    required_keys = {
        "species": {row["species_key"] for row in members},
        "ability": {row["ability_key"] for row in members},
        "move": {row[f"move{slot}_key"] for row in members for slot in range(1, 5)},
        "item": {row["held_item_key"] for row in members},
        "nature": {row["nature_key"] for row in members},
    }
    for row in parties:
        required_keys["item"].update(json.loads(row["trainer_item_keys"]))
    for domain, keys in required_keys.items():
        missing = sorted(keys - set(registries[domain]))
        if missing:
            _fail(f"live {domain} registry misses ChangeKit keys: {missing[:8]}")

    # The Stage07 ABI is required for deterministic ability mode validation.
    base_stats = species_meta.get("base_stats", {})
    if base_stats.get("count") != 1621 or base_stats.get("stride") != 32:
        _fail("Stage07 base stats ABI differs")
    return {
        "coverage": coverage,
        "encounters": encounters,
        "parties": parties,
        "members": members,
        "dialogues": dialogues,
        "rewards": rewards,
        "gimmicks": gimmicks,
        "consumers": consumers,
        "archives": archives,
        "encounter_by_key": encounter_by_key,
        "party_by_key": party_by_key,
        "consumer_by_key": consumer_by_key,
        "gimmick_by_key": gimmick_by_key,
        "registries": registries,
    }


def _resolve_ability_mode(
    stage: bytes, species_meta: Mapping[str, Any], species_id: int, ability_id: int
) -> tuple[int, bool]:
    if ability_id == 0:
        return 0, True
    base = int(species_meta["base_stats"]["address"]) - GBA_ROM_BASE
    stride = int(species_meta["base_stats"]["stride"])
    offset = base + species_id * stride
    abilities = (
        _u16(stage, offset + 0x16, "ability1"),
        _u16(stage, offset + 0x1A, "ability2"),
        _u16(stage, offset + 0x1C, "hidden ability"),
    )
    matches = [index for index, value in enumerate(abilities) if value == ability_id and value]
    # ChangeKit authoring deliberately assigns some abilities outside a
    # species' three persistent slots.  Those are installed directly into the
    # live BattlePokemon by the ability-load adapter; the party Pokemon keeps
    # its primary slot as a deterministic fallback before battle setup.
    return (matches[0], True) if matches else (0, False)


def serialize_parties(
    source: Mapping[str, Any], stage: bytes, species_meta: Mapping[str, Any]
) -> dict[str, Any]:
    registries = source["registries"]
    consumer_by_key = source["consumer_by_key"]
    consumer_by_party = {
        row["party_key"]: row for row in source["consumers"]
    }
    if len(consumer_by_party) != PARTY_COUNT:
        _fail("party/runtime consumer relation is not 1:1")
    members_by_party: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in source["members"]:
        members_by_party[row["party_key"]].append(row)
    sidecars: list[dict[str, int]] = []
    party_rows: list[dict[str, Any]] = []
    party_bytes: dict[str, bytes] = {}
    for party in sorted(
        source["parties"],
        key=lambda row: int(consumer_by_key[row["encounter_key"]]["runtime_trainer_id"], 0),
    ):
        key = party["party_key"]
        consumer = consumer_by_party[key]
        trainer_id = int(consumer["runtime_trainer_id"], 0)
        rows = sorted(members_by_party[key], key=lambda row: int(row["slot"], 0))
        if [int(row["slot"], 0) for row in rows] != list(range(1, int(party["party_size"], 0) + 1)):
            _fail(f"{key}: party slot sequence differs")
        raw = bytearray()
        audit_members: list[dict[str, Any]] = []
        for member in rows:
            species_id = registries["species"][member["species_key"]]
            ability_id = registries["ability"][member["ability_key"]]
            ability_mode, ability_native = _resolve_ability_mode(
                stage, species_meta, species_id, ability_id
            )
            nature_id = registries["nature"][member["nature_key"]]
            item_id = registries["item"][member["held_item_key"]]
            move_ids = [registries["move"][member[f"move{i}_key"]] for i in range(1, 5)]
            level = int(member["level"], 0)
            iv = int(member["iv_floor"], 0)
            evs = {
                name: int(member[name], 0)
                for name in ("hp_ev", "atk_ev", "def_ev", "spa_ev", "spd_ev", "spe_ev")
            }
            if not 1 <= level <= 100 or not 0 <= iv <= 31:
                _fail(f"{key}:{member['slot']}: invalid level/IV")
            if any(not 0 <= value <= 252 for value in evs.values()) or sum(evs.values()) > 510:
                _fail(f"{key}:{member['slot']}: invalid EV spread")
            raw.extend(struct.pack("<8H", 0, level, species_id, item_id, *move_ids))
            sidecar = {
                "trainer_id": trainer_id,
                "species_id": species_id,
                "ability_id": ability_id,
                "ability_native": ability_native,
                "side": 1,
                "slot": int(member["slot"], 0) - 1,
                "nature_id": nature_id,
                "ability_mode": ability_mode,
                "iv": iv,
                "hp_ev": evs["hp_ev"],
                "atk_ev": evs["atk_ev"],
                "def_ev": evs["def_ev"],
                "speed_ev": evs["spe_ev"],
                "sp_atk_ev": evs["spa_ev"],
                "sp_def_ev": evs["spd_ev"],
                "level": level,
            }
            sidecars.append(sidecar)
            audit_members.append({
                **sidecar,
                "species_key": member["species_key"],
                "ability_key": member["ability_key"],
                "nature_key": member["nature_key"],
                "item_id": item_id,
                "move_ids": move_ids,
                "level": level,
            })
        party_raw = bytes(raw)
        party_bytes[key] = party_raw
        party_rows.append({
            "party_key": key,
            "encounter_key": party["encounter_key"],
            "trainer_id": trainer_id,
            "battle_format": party["battle_format"],
            "party_size": int(party["party_size"], 0),
            "ai_profile_key": party["ai_profile_key"],
            "trainer_item_keys": json.loads(party["trainer_item_keys"]),
            "party_sha256": _sha(party_raw),
            "members": audit_members,
        })
    sidecars.sort(key=lambda row: (row["trainer_id"], row["side"], row["slot"]))
    if len(sidecars) != MEMBER_COUNT or len(party_rows) != PARTY_COUNT:
        _fail("serialized party/sidecar count differs")
    if len({row["trainer_id"] for row in party_rows}) != PARTY_COUNT:
        _fail("serialized trainer IDs are not unique")
    return {"sidecars": sidecars, "party_rows": party_rows, "party_bytes": party_bytes}


def _load_dialogue_readings(root: Path, source: Mapping[str, Any]) -> dict[str, Any]:
    readings = _rows(root / DIALOGUE_READINGS)
    by_original = _index(readings, "original_text", "dialogue readings")
    missing = sorted({row["text"] for row in source["dialogues"]} - set(by_original))
    if missing:
        _fail(f"dialogue readings miss source lines: {missing[:3]}")
    if any(row["status"] != "ADOPTED_CURRENT_1BYTE_FONT" for row in readings):
        _fail("dialogue reading status differs")
    labels = {
        original: f"dialogue::reading::{row['reading_id']}"
        for original, row in by_original.items()
    }
    dialogue_states: dict[str, dict[str, str]] = defaultdict(dict)
    for row in source["dialogues"]:
        states = dialogue_states[row["encounter_key"]]
        if row["state_key"] in states:
            _fail(f"duplicate dialogue state: {row['encounter_key']} {row['state_key']}")
        states[row["state_key"]] = labels[row["text"]]
    return {"rows": readings, "by_original": by_original, "labels": labels,
            "states": dict(dialogue_states)}


def _trainer_command_pointers(kind: int) -> tuple[str, ...]:
    layouts = {
        0: ("intro", "defeat"),
        1: ("intro", "defeat", "continuation"),
        2: ("intro", "defeat", "continuation"),
        3: ("defeat",),
        4: ("intro", "defeat", "not_enough"),
        5: ("intro", "defeat"),
        6: ("intro", "defeat", "not_enough", "continuation"),
        7: ("intro", "defeat", "not_enough"),
        8: ("intro", "defeat", "not_enough", "continuation"),
        9: ("defeat", "victory"),
    }
    if kind not in layouts:
        _fail(f"unsupported trainerbattle kind: {kind}")
    return layouts[kind]


def _read_trainer_command(stage: bytes, address: int, expected_kind: int | None = None,
                          expected_id: int | None = None) -> dict[str, Any]:
    offset = _rom_offset(address, 4, "trainerbattle command")
    if stage[offset] != 0x5C:
        _fail(f"not a trainerbattle command at 0x{address:08X}: {stage[offset]:#x}")
    kind = stage[offset + 1]
    trainer_id = _u16(stage, offset + 2, "trainerbattle trainer ID")
    if expected_kind is not None and kind != expected_kind:
        _fail(f"trainerbattle kind differs at 0x{address:08X}: {kind} != {expected_kind}")
    if expected_id is not None and trainer_id != expected_id:
        _fail(f"trainerbattle ID differs at 0x{address:08X}: {trainer_id} != {expected_id}")
    size = KIND_SIZES.get(kind)
    if size is None:
        _fail(f"trainerbattle kind has no size: {kind}")
    raw = stage[offset:offset + size]
    pointers = {}
    for index, role in enumerate(_trainer_command_pointers(kind)):
        pointers[role] = struct.unpack_from("<I", raw, 6 + index * 4)[0]
    return {"address": address, "offset": offset, "kind": kind,
            "trainer_id": trainer_id, "size": size, "raw": raw, "pointers": pointers}


def _locate_stage17_progression_commands(
    stage: bytes, symbols: Mapping[str, Any]
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    table = symbols.get("symbols", {})
    progression = sorted(
        (
            (str(label), int(address))
            for label, address in table.items()
            if str(label).startswith("progress::")
        ),
        key=lambda row: row[1],
    )
    for position, (label, address) in enumerate(progression):
        next_address = progression[position + 1][1] if position + 1 < len(progression) else address + 0x40
        span = min(next_address - address, 0x40)
        if span <= 0:
            _fail(f"{label}: invalid progression script span")
        start = _rom_offset(address, span, str(label))
        hits: list[dict[str, Any]] = []
        for relative in range(span):
            if stage[start + relative] != 0x5C:
                continue
            candidate = GBA_ROM_BASE + start + relative
            try:
                command = _read_trainer_command(stage, candidate)
            except FinalBuildError:
                continue
            if 751 <= command["trainer_id"] <= 763:
                hits.append(command)
        unique = {row["address"]: row for row in hits}
        if len(unique) != 1:
            _fail(f"{label}: progression trainerbattle is not unique: {list(unique)}")
        command = next(iter(unique.values()))
        command["script_key"] = label
        if command["trainer_id"] in result:
            _fail(f"duplicate Kanto existing trainer command: {command['trainer_id']}")
        result[command["trainer_id"]] = command
    if set(result) != set(range(751, 764)):
        _fail(f"Kanto existing command IDs differ: {sorted(result)}")
    return result


def _canonical_commands(stage: bytes, source: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    commands: dict[str, dict[str, Any]] = {}
    seen_addresses: set[int] = set()
    for consumer in source["consumers"]:
        if consumer["binding_mode"] != "CANONICAL":
            continue
        address = int(consumer["command_address"], 0)
        if address in seen_addresses:
            _fail(f"canonical physical command reused after normalization: 0x{address:08X}")
        seen_addresses.add(address)
        command = _read_trainer_command(
            stage, address,
            int(consumer["trainerbattle_kind"], 0),
            int(consumer["source_trainer_id"], 0),
        )
        command["encounter_key"] = consumer["encounter_key"]
        commands[consumer["encounter_key"]] = command
    if len(commands) != CANONICAL_COUNT:
        _fail(f"canonical command count differs: {len(commands)}")
    return commands


def _msgbox_bytes(blob: Blob, text_label: str, *, callstd: int = 4) -> None:
    start = blob.append(bytes([0x0F, 0x00, 0, 0, 0, 0, 0x09, callstd]))
    blob.pointer(start + 2, text_label)


def _goto_bytes(blob: Blob, target: str) -> None:
    start = blob.append(bytes([0x05, 0, 0, 0, 0]))
    blob.pointer(start + 1, target)


def _goto_absolute(address: int) -> bytes:
    return bytes([0x05]) + struct.pack("<I", address)


def _build_proxy(
    blob: Blob,
    consumer: Mapping[str, str],
    command: Mapping[str, Any],
    states: Mapping[str, str],
    physical_flag: int,
    *,
    return_label: str | None = None,
) -> dict[str, Any]:
    key = consumer["encounter_key"]
    script_label = f"proxy::{key}"
    battle_label = f"battle::{key}"
    post_label = f"proxy::{key}::post"
    runtime_id = int(consumer["runtime_trainer_id"], 0)
    kind = int(consumer["trainerbattle_kind"], 0)
    if kind != int(command["kind"]):
        _fail(f"{key}: proxy kind differs from physical command")
    blob.mark(script_label, 4)
    rematch_intro = states.get("REMATCH_INTRO")
    command_intro = states.get("INTRO")
    empty_label = "dialogue::empty"
    if rematch_intro:
        # checkflag physical defeat flag; goto_if TRUE to authored rematch intro.
        blob.append(bytes([0x2B]) + struct.pack("<H", physical_flag))
        branch = blob.append(bytes([0x06, 0x01, 0, 0, 0, 0]))
        blob.pointer(branch + 2, f"proxy::{key}::rematch_intro")
        if not command_intro:
            _fail(f"{key}: rematch dialogue lacks normal intro")
        _msgbox_bytes(blob, command_intro)
        _goto_bytes(blob, battle_label)
        blob.mark(f"proxy::{key}::rematch_intro", 1)
        _msgbox_bytes(blob, rematch_intro)
        _goto_bytes(blob, battle_label)
        command_intro = empty_label
    elif kind in {3, 9}:
        if command_intro:
            _msgbox_bytes(blob, command_intro)
        command_intro = empty_label

    blob.mark(battle_label, 1)
    command_offset = len(blob.data)
    raw = bytearray([0x5C, kind])
    raw.extend(struct.pack("<HH", runtime_id, 0))
    roles = _trainer_command_pointers(kind)
    fixups: list[tuple[int, str]] = []
    for role in roles:
        relative = len(raw)
        raw.extend(b"\0\0\0\0")
        if role == "intro":
            target = command_intro or empty_label
        elif role in {"defeat", "victory"}:
            target = states.get("DEFEAT") or empty_label
        elif role == "not_enough":
            target = states.get("NOT_ENOUGH_PARTY_FOR_DOUBLE") or empty_label
        elif role == "continuation":
            target = post_label
        else:
            _fail(f"{key}: unsupported trainerbattle pointer role {role}")
        fixups.append((relative, target))
    if len(raw) != KIND_SIZES[kind]:
        _fail(f"{key}: emitted trainerbattle size differs")
    raw_at = blob.append(bytes(raw))
    for relative, target in fixups:
        blob.pointer(raw_at + relative, target)

    blob.mark(post_label, 1)
    post = states.get("POST_BATTLE")
    if post:
        _msgbox_bytes(blob, post)
    original_next = command["address"] + command["size"]
    if "continuation" in command["pointers"]:
        original_next = int(command["pointers"]["continuation"])
    if return_label is None:
        blob.append(_goto_absolute(original_next))
    else:
        _goto_bytes(blob, return_label)
    return {
        "encounter_key": key,
        "owner_kind": "CANONICAL_PROXY" if consumer["binding_mode"] == "CANONICAL" else "KANTO_EXISTING_PROXY",
        "original_command_address": command["address"],
        "original_command_size": command["size"],
        "original_command_sha256": _sha(command["raw"]),
        "script_label": script_label,
        "battle_label": battle_label,
        "battle_relative": command_offset,
        "trainer_id": runtime_id,
        "source_trainer_id": int(consumer["source_trainer_id"], 0),
        "kind": kind,
        "battle_format": consumer["battle_format"],
        "physical_flag": physical_flag,
        "post_return_address": original_next,
        "post_return_label": return_label,
        "rematch_intro_connected": bool(rematch_intro),
    }


def _build_existing_kanto_gate(
    blob: Blob,
    encounter_key: str,
    plan_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebuild one Stage17 progression gate with Task06 locked dialogue."""
    from tools.regression.rom_runtime import FLAG_SYS_GAME_CLEAR, PROGRESSION_OBJECTS

    script_key = str(plan_binding["script_key"])
    source_name = script_key.split("progress::", 1)[-1]
    if source_name not in PROGRESSION_OBJECTS:
        _fail(f"{encounter_key}: existing progression owner is unknown: {source_name}")
    _, _, completion, required, hall_of_fame = PROGRESSION_OBJECTS[source_name]
    gate_label = f"kanto_existing::{encounter_key}::gate"
    locked_label = f"kanto_existing::{encounter_key}::locked"
    completion_label = f"kanto_existing::{encounter_key}::complete"
    blob.mark(gate_label, 4)
    blob.append(bytes([0x5A]))
    for flag in ([required] if required is not None else []) + ([FLAG_SYS_GAME_CLEAR] if hall_of_fame else []):
        blob.append(bytes([0x2B]) + struct.pack("<H", int(flag)))
        branch = blob.append(bytes([0x06, 0x00, 0, 0, 0, 0]))
        blob.pointer(branch + 2, locked_label)
    _goto_bytes(blob, f"proxy::{encounter_key}")
    blob.mark(locked_label, 1)
    _msgbox_bytes(blob, str(plan_binding["locked_text_key"]))
    blob.append(bytes([0x02]))
    blob.mark(completion_label, 1)
    blob.append(bytes([0x29]) + struct.pack("<H", int(completion)) + bytes([0x02]))
    return {
        "encounter_key": encounter_key,
        "gate_label": gate_label,
        "locked_label": locked_label,
        "completion_label": completion_label,
        "completion_flag": int(completion),
        "required_flag": int(required) if required is not None else None,
        "hall_of_fame_required": bool(hall_of_fame),
        "group_id": int(plan_binding["group_id"]),
        "map_id": int(plan_binding["map_id"]),
        "local_id": int(plan_binding["local_ids"][0]),
        "expected_object_script_address": int(plan_binding["existing_object_script_address"]),
    }


def _append_plan_data(blob: Blob, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Append Kanto/Archive plan and return battle-label ownership metadata."""
    for text in sorted(plan["texts"], key=lambda row: row["text_key"]):
        label = str(text["text_key"])
        raw = bytes.fromhex(text["data_hex"])
        if label in blob.labels:
            if bytes(blob.data[blob.labels[label]:blob.labels[label] + len(raw)]) != raw:
                _fail(f"plan text label collides with different bytes: {label}")
            continue
        blob.add(label, raw, 1)

    script_roles: dict[str, dict[str, Any]] = {}
    for script in sorted(plan["scripts"], key=lambda row: (row["script_key"], row["role"])):
        label = str(script["script_key"])
        if label in blob.labels:
            _fail(f"duplicate plan script label: {label}")
        raw = bytes.fromhex(script["data_hex"])
        offset = blob.add(label, raw, 4)
        for fixup in script.get("fixups", []):
            blob.pointer(offset + int(fixup["offset"]), str(fixup["target"]),
                         thumb=bool(fixup.get("thumb", False)))
        script_roles[label] = dict(script)

    map_rows: list[dict[str, Any]] = []
    for map_row in plan["maps"]:
        prefix = f"map::{map_row['map_key']}"
        preserved_labels = {
            "WARPS": "warps_hex", "COORDS": "coords_hex", "BG": "bg_hex"
        }
        for upper, field in preserved_labels.items():
            raw = bytes.fromhex(map_row["preserved_arrays"][field])
            if raw:
                blob.add(f"{prefix}::preserved::{upper}", raw, 4)
        object_offset = blob.add(f"{prefix}::objects", bytes.fromhex(map_row["object_table_hex"]), 4)
        for fixup in map_row.get("object_table_fixups", []):
            blob.pointer(object_offset + int(fixup["offset"]), str(fixup["target"]))
        event = map_row["new_event_header"]
        event_offset = blob.add(f"{prefix}::event_header", bytes.fromhex(event["data_hex"]), 4)
        for fixup in event.get("fixups", []):
            target = str(fixup["target"])
            if target == "OBJECT_TABLE":
                target = f"{prefix}::objects"
            elif target.startswith("PRESERVED_"):
                target = f"{prefix}::preserved::{target.removeprefix('PRESERVED_')}"
            blob.pointer(event_offset + int(fixup["offset"]), target)
        map_rows.append({
            "map_key": map_row["map_key"],
            "group_id": map_row["group_id"],
            "map_id": map_row["map_id"],
            "patch_address": map_row["patch"]["map_header_pointer_field_address"],
            "event_label": f"{prefix}::event_header",
            "old_event_header_address": map_row["old_event_header_address"],
            "object_count": len(map_row["preserved_objects"]) + len(map_row["new_objects"]),
            "new_object_count": len(map_row["new_objects"]),
        })

    battle_labels: dict[str, str] = {}
    for binding in plan["bindings"]:
        if binding["owner_kind"] == "EXISTING":
            continue
        script_key = str(binding["script_key"])
        label = f"{script_key}::battle"
        if label not in script_roles or script_roles[label].get("role") != "trainerbattle":
            _fail(f"{binding['encounter_key']}: plan trainerbattle script missing")
        battle_labels[str(binding["encounter_key"])] = label
    return {"map_rows": map_rows, "battle_labels": battle_labels,
            "script_roles": script_roles}


def _stage_object_script_site(
    stage: bytes, group_id: int, map_id: int, local_id: int
) -> tuple[int, int]:
    root_pointer = _u32(stage, 0x54B0C, "gMapGroups root")
    root = _rom_offset(root_pointer, (group_id + 1) * 4, "gMapGroups")
    group_pointer = _u32(stage, root + group_id * 4, f"map group {group_id}")
    group = _rom_offset(group_pointer, (map_id + 1) * 4, f"map group {group_id}")
    header_pointer = _u32(stage, group + map_id * 4, f"map {group_id}/{map_id}")
    header = _rom_offset(header_pointer, 0x1C, f"map header {group_id}/{map_id}")
    events_pointer = _u32(stage, header + 4, f"map events {group_id}/{map_id}")
    events = _rom_offset(events_pointer, 0x14, f"map events {group_id}/{map_id}")
    object_count = stage[events]
    object_pointer = _u32(stage, events + 4, f"objects {group_id}/{map_id}")
    objects = _rom_offset(object_pointer, object_count * 0x18, f"objects {group_id}/{map_id}")
    matches = [
        objects + index * 0x18
        for index in range(object_count)
        if stage[objects + index * 0x18] == local_id
    ]
    if len(matches) != 1:
        _fail(f"map {group_id}/{map_id}: local {local_id} object is not unique")
    site = matches[0] + 0x10
    return GBA_ROM_BASE + site, _u32(stage, site, "object script pointer")


def build_event_blob(
    root: Path,
    stage: bytes,
    clean: bytes,
    source: Mapping[str, Any],
    stage17_symbols: Mapping[str, Any],
    acquisition_meta: Mapping[str, Any],
) -> tuple[Blob, dict[str, Any], dict[str, Any]]:
    readings = _load_dialogue_readings(root, source)
    archive_rows = []
    archive_by_key = _index(source["archives"], "encounter_key", "archive rows")
    for consumer in source["consumers"]:
        if consumer["binding_mode"] != "ARCHIVE":
            continue
        archive = archive_by_key[consumer["encounter_key"]]
        archive_rows.append({
            **archive,
            "trainer_id": int(consumer["runtime_trainer_id"], 0),
            "battle_format": consumer["battle_format"],
            "text_keys": {
                **readings["states"][consumer["encounter_key"]],
                "NOT_ENOUGH_POKEMON": readings["states"][consumer["encounter_key"]].get(
                    "NOT_ENOUGH_PARTY_FOR_DOUBLE", ""
                ),
            },
        })
    plan = build_kanto_event_plan(
        stage, clean, root, _discover_task06(root),
        archive_rows=archive_rows,
        acquisition_metadata=acquisition_meta,
        policy=LEGACY_PUBLISHED,
    )
    summary = plan.get("summary", {})
    if (
        summary.get("task06_encounters") != KANTO_COUNT
        or summary.get("existing_bindings") != KANTO_EXISTING_COUNT
        or summary.get("normal_bindings", 0) + summary.get("relocated_bindings", 0) != 188
        or summary.get("archive_bindings") != ARCHIVE_COUNT
    ):
        _fail(f"Kanto/Archive event plan summary differs: {summary}")

    blob = Blob()
    blob.add("dialogue::empty", b"\xFF", 1)
    for row in readings["rows"]:
        blob.add(readings["labels"][row["original_text"]], bytes.fromhex(row["encoded_hex"]), 1)
    plan_meta = _append_plan_data(blob, plan)

    canonical = _canonical_commands(stage, source)
    kanto_existing = _locate_stage17_progression_commands(stage, stage17_symbols)
    plan_bindings = _index(plan["bindings"], "encounter_key", "event plan bindings")
    existing_gates: dict[str, dict[str, Any]] = {}
    for consumer in sorted(source["consumers"], key=lambda row: row["encounter_key"]):
        key = consumer["encounter_key"]
        if (
            consumer["binding_mode"] == "KANTO_NEW"
            and plan_bindings[key]["owner_kind"] == "EXISTING"
        ):
            existing_gates[key] = _build_existing_kanto_gate(blob, key, plan_bindings[key])
    proxy_rows: list[dict[str, Any]] = []
    for consumer in sorted(source["consumers"], key=lambda row: row["encounter_key"]):
        key = consumer["encounter_key"]
        if consumer["binding_mode"] == "CANONICAL":
            command = canonical[key]
            physical_flag = FLAG_START + int(consumer["source_trainer_id"], 0)
        elif consumer["binding_mode"] == "KANTO_NEW" and plan_bindings[key]["owner_kind"] == "EXISTING":
            command = kanto_existing[int(consumer["runtime_trainer_id"], 0)]
            physical_flag = FLAG_START + int(consumer["runtime_trainer_id"], 0)
        else:
            continue
        proxy_rows.append(_build_proxy(
            blob, consumer, command, readings["states"][key], physical_flag,
            return_label=(existing_gates[key]["completion_label"] if key in existing_gates else None),
        ))
    if len(proxy_rows) != CANONICAL_COUNT + KANTO_EXISTING_COUNT:
        _fail(f"proxy count differs: {len(proxy_rows)}")

    battle_labels = dict(plan_meta["battle_labels"])
    battle_labels.update({row["encounter_key"]: row["battle_label"] for row in proxy_rows})
    if set(battle_labels) != set(source["consumer_by_key"]):
        missing = sorted(set(source["consumer_by_key"]) - set(battle_labels))
        extra = sorted(set(battle_labels) - set(source["consumer_by_key"]))
        _fail(f"physical battle label coverage differs: missing={missing[:5]} extra={extra[:5]}")

    plan_maps_by_coordinate = {
        (int(row["group_id"]), int(row["map_id"])): row for row in plan["maps"]
    }
    for gate in existing_gates.values():
        coordinate = (gate["group_id"], gate["map_id"])
        if coordinate in plan_maps_by_coordinate:
            row = plan_maps_by_coordinate[coordinate]
            matches = [
                int(item["index"])
                for item in row["preserved_objects"]
                if int(item["local_id"]) == gate["local_id"]
            ]
            if len(matches) != 1:
                _fail(f"{gate['encounter_key']}: copied existing object is not unique")
            object_label = f"map::{row['map_key']}::objects"
            site = blob.labels[object_label] + matches[0] * 0x18 + 0x10
            blob.pointer(site, gate["gate_label"])
            gate["object_patch_mode"] = "RELOCATED_EVENT_OBJECT_FIXUP"
            gate["event_object_relative_site"] = site
        else:
            site_address, actual = _stage_object_script_site(
                stage, gate["group_id"], gate["map_id"], gate["local_id"]
            )
            if actual != gate["expected_object_script_address"]:
                _fail(f"{gate['encounter_key']}: live object script pointer differs")
            gate["object_patch_mode"] = "IN_PLACE_OBJECT_POINTER"
            gate["object_script_pointer_site_address"] = site_address

    return blob, {
        "readings": readings,
        "proxy_rows": proxy_rows,
        "battle_labels": battle_labels,
        "map_rows": plan_meta["map_rows"],
        "script_roles": plan_meta["script_roles"],
        "plan": plan,
        "plan_bindings": plan_bindings,
        "existing_gates": existing_gates,
    }, plan


def _event_battle_rows(
    event_blob: Blob,
    event_info: Mapping[str, Any],
    source: Mapping[str, Any],
    event_base: int,
) -> list[dict[str, Any]]:
    plan_bindings = event_info["plan_bindings"]
    archive_indices = {
        row["encounter_key"]: int(row["consumer_index"], 0)
        for row in source["archives"]
    }
    rows: list[dict[str, Any]] = []
    for consumer in source["consumers"]:
        key = consumer["encounter_key"]
        label = event_info["battle_labels"][key]
        if label not in event_blob.labels:
            _fail(f"{key}: physical battle label is absent")
        command_address = event_base + event_blob.labels[label]
        kind = int(consumer["trainerbattle_kind"], 0)
        if consumer["binding_mode"] != "CANONICAL":
            binding_kind = int(plan_bindings[key]["trainerbattle_kind"])
            if plan_bindings[key]["owner_kind"] == "EXISTING":
                binding_kind = kind
            if binding_kind != kind:
                _fail(f"{key}: normalized/physical trainerbattle kind differs ({kind}/{binding_kind})")
        rows.append({
            "encounter_key": key,
            "binding_mode": consumer["binding_mode"],
            "command_address": command_address,
            "data_address": command_address + 1,
            "source_trainer_id": int(consumer["runtime_trainer_id"], 0),
            "target_trainer_id": int(consumer["runtime_trainer_id"], 0),
            "kind": kind,
            "battle_format": consumer["battle_format"],
            "archive_id": archive_indices.get(key, 0),
            "physical_flag": (
                int(plan_bindings[key].get("defeat_flag", 0))
                if consumer["binding_mode"] == "ARCHIVE"
                else FLAG_START + int(consumer["source_trainer_id"], 0)
                if consumer["binding_mode"] == "CANONICAL"
                else FLAG_START + int(consumer["runtime_trainer_id"], 0)
            ),
            "battle_label": label,
        })
    rows.sort(key=lambda row: (row["data_address"], row["source_trainer_id"], row["kind"]))
    if len(rows) != PHYSICAL_COMMAND_COUNT or len({row["command_address"] for row in rows}) != PHYSICAL_COMMAND_COUNT:
        _fail("physical trainerbattle command addresses are not 1302 unique rows")
    for row in rows:
        physical_kind = event_blob.data[event_blob.labels[row["battle_label"]] + 1]
        physical_id = struct.unpack_from(
            "<H", event_blob.data, event_blob.labels[row["battle_label"]] + 2
        )[0]
        if physical_kind != row["kind"] or physical_id != row["target_trainer_id"]:
            _fail(f"{row['encounter_key']}: emitted physical command bytes differ")
    return rows


def _tera_type_id(root: Path, gimmick: Mapping[str, str]) -> int:
    if gimmick["gimmick_type"] != "TERASTAL":
        return 0
    import re

    match = re.search(r"TERA_TYPE=([A-Z0-9_]+)", gimmick["runtime_feature_required"])
    if match:
        authored = match.group(1)
    else:
        # 37 source rows state the type consistently in policy/test prose but
        # omit the redundant TERA_TYPE= token.  Accept that mechanical format
        # defect only when all explicit English type tokens resolve to exactly
        # one value; ambiguity remains fail-closed.
        type_names = (
            "NORMAL|FIRE|WATER|ELECTRIC|GRASS|ICE|FIGHTING|POISON|GROUND|"
            "FLYING|PSYCHIC|BUG|ROCK|GHOST|DRAGON|DARK|STEEL|FAIRY"
        )
        evidence = " | ".join(
            gimmick.get(field, "")
            for field in ("ai_activation_policy", "activation_test", "design_reason")
        )
        candidates = set(re.findall(
            rf"(?<![A-Z_])(?:TYPE_)?({type_names})(?![A-Z_])", evidence
        ))
        if len(candidates) != 1:
            _fail(
                f"{gimmick['encounter_key']}: TERA_TYPE prose inference is not unique: "
                f"{sorted(candidates)}"
            )
        authored = next(iter(candidates))
    key = f"TYPE_KEY_{authored}"
    types = _load_live_registry(root, "manifests/type_ids.csv", "type_key")
    if key not in types or not 0 <= types[key] <= 0x18:
        _fail(f"{gimmick['encounter_key']}: invalid live tera type {key}")
    return types[key]


def build_runtime_tables(
    root: Path,
    source: Mapping[str, Any],
    serialized: Mapping[str, Any],
    battle_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    consumer_by_key = source["consumer_by_key"]
    battle_by_key = {row["encounter_key"]: row for row in battle_rows}
    exact = [{
        "data_address": row["data_address"],
        "source_trainer_id": row["source_trainer_id"],
        "target_trainer_id": row["target_trainer_id"],
        "kind": row["kind"],
        "flags": 1,
        "dispatch_id": 0,
        "encounter_key": row["encounter_key"],
    } for row in battle_rows]
    exact.sort(key=lambda row: (
        row["data_address"], row["source_trainer_id"], row["kind"], row["target_trainer_id"]
    ))
    if len({(row["data_address"], row["source_trainer_id"], row["kind"]) for row in exact}) != ENCOUNTER_COUNT:
        _fail("exact binding key is not one-to-one")

    rematch = [{
        "data_address": row["data_address"],
        "stock_trainer_id": row["source_trainer_id"],
        "target_trainer_id": row["target_trainer_id"],
        "encounter_key": row["encounter_key"],
    } for row in battle_rows if row["kind"] in {5, 7}]
    rematch.sort(key=lambda row: (
        row["data_address"], row["stock_trainer_id"], row["target_trainer_id"]
    ))

    archives = [{
        "data_address": row["data_address"],
        "source_trainer_id": row["source_trainer_id"],
        "target_trainer_id": row["target_trainer_id"],
        "archive_id": row["archive_id"],
        "physical_flag": row["physical_flag"],
        "kind": row["kind"],
        "battle_format": 1 if row["battle_format"] == "DOUBLE" else 0,
        "encounter_key": row["encounter_key"],
    } for row in battle_rows if row["archive_id"]]
    archives.sort(key=lambda row: row["archive_id"])
    if [row["archive_id"] for row in archives] != list(range(1, ARCHIVE_COUNT + 1)):
        _fail("archive IDs are not continuous 1..71")

    gimmicks: list[dict[str, Any]] = []
    for gimmick in source["gimmicks"]:
        key = gimmick["encounter_key"]
        consumer = consumer_by_key[key]
        mode = GIMMICK_MODE.get(gimmick["gimmick_type"])
        if mode is None:
            _fail(f"{key}: unsupported gimmick type {gimmick['gimmick_type']}")
        slot = int(gimmick["user_party_slot"], 0)
        flags = 0
        if mode:
            if not 1 <= slot <= 6:
                _fail(f"{key}: gimmick user slot outside 1..6")
            flags = 1
            if battle_by_key[key]["battle_format"] == "DOUBLE":
                flags |= 2
            slot -= 1
        elif slot != 0:
            _fail(f"{key}: NONE gimmick has nonzero user slot")
        gimmicks.append({
            "trainer_id": int(consumer["runtime_trainer_id"], 0),
            "dispatch_id": 0,
            "mechanic_mode": mode,
            "ai_profile": AI_FLAGS[consumer["ai_profile_key"]],
            "user_slot": slot,
            "flags": flags,
            "tera_type": _tera_type_id(root, gimmick),
            "encounter_key": key,
        })
    gimmicks.sort(key=lambda row: (row["trainer_id"], row["dispatch_id"]))
    if len({(row["trainer_id"], row["dispatch_id"]) for row in gimmicks}) != ENCOUNTER_COUNT:
        _fail("gimmick runtime keys are not unique")

    flags: set[tuple[int, int]] = set()
    for row in battle_rows:
        external = FLAG_START + row["target_trainer_id"]
        physical = row["physical_flag"]
        if external != physical:
            flags.add((external, physical))
    flag_rows = [{"external_flag": a, "physical_flag": b} for a, b in sorted(flags)]
    if len({row["external_flag"] for row in flag_rows}) != len(flag_rows):
        _fail("external flag map keys are not unique")

    return {
        "sidecars": serialized["sidecars"],
        "exact": exact,
        "rematch": rematch,
        "archives": archives,
        "gimmicks": gimmicks,
        "flags": flag_rows,
    }


def generated_header(tables: Mapping[str, Any], trainer_table_address: int) -> bytes:
    sidecar_lines = [
        "    {%du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du}," % (
            row["trainer_id"], row["species_id"], row["ability_id"], row["side"], row["slot"],
            row["nature_id"], row["ability_mode"], row["iv"], row["hp_ev"],
            row["atk_ev"], row["def_ev"], row["speed_ev"], row["sp_atk_ev"],
            row["sp_def_ev"], row["level"],
        ) for row in tables["sidecars"]
    ]
    exact_lines = [
        f"    {{UINT32_C(0x{row['data_address']:08X}), {row['source_trainer_id']}u, "
        f"{row['target_trainer_id']}u, {row['kind']}u, {row['flags']}u, {row['dispatch_id']}u}},"
        for row in tables["exact"]
    ]
    rematch_lines = [
        f"    {{UINT32_C(0x{row['data_address']:08X}), {row['stock_trainer_id']}u, "
        f"{row['target_trainer_id']}u}}," for row in tables["rematch"]
    ]
    archive_lines = [
        f"    {{UINT32_C(0x{row['data_address']:08X}), {row['source_trainer_id']}u, "
        f"{row['target_trainer_id']}u, {row['archive_id']}u, {row['physical_flag']}u, "
        f"{row['kind']}u, {row['battle_format']}u, {{0u, 0u}}}},"
        for row in tables["archives"]
    ]
    gimmick_lines = [
        f"    {{{row['trainer_id']}u, {row['dispatch_id']}u, {row['mechanic_mode']}u, "
        f"{row['ai_profile']}u, {row['user_slot']}u, {row['flags']}u, "
        f"{row['tera_type']}u, {{0u, 0u, 0u}}}}," for row in tables["gimmicks"]
    ]
    flag_lines = [
        f"    {{{row['external_flag']}u, {row['physical_flag']}u}}," for row in tables["flags"]
    ]
    text = f"""#ifndef TRAINER_CHANGEKIT_FINAL_GENERATED_H
#define TRAINER_CHANGEKIT_FINAL_GENERATED_H
#include <stdint.h>

#define TRAINER_CHANGEKIT_FINAL_GENERATED_ENCOUNTER_COUNT {ENCOUNTER_COUNT}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT {len(tables['sidecars'])}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_EXACT_BINDING_COUNT {len(tables['exact'])}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_REMATCH_COUNT {len(tables['rematch'])}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT {len(tables['archives'])}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT {len(tables['gimmicks'])}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_FLAG_MAP_COUNT {len(tables['flags'])}u
#define TRAINER_CHANGEKIT_FINAL_GENERATED_TRAINER_TABLE_COUNT {TRAINER_TABLE_COUNT}u
#define TRAINER_CHANGEKIT_FINAL_TRAINER_TABLE_ADDRESS UINT32_C(0x{trainer_table_address:08X})

struct __attribute__((packed)) TrainerChangeKitMemberSidecarV1 {{
    uint16_t trainer_id; uint16_t species_id; uint16_t ability_id;
    uint8_t side, slot, nature_id, ability_mode, iv;
    uint8_t hp_ev, atk_ev, def_ev, speed_ev, sp_atk_ev, sp_def_ev, level;
}};
struct __attribute__((packed)) TrainerChangeKitExactBindingV1 {{
    uint32_t data_address; uint16_t source_trainer_id, target_trainer_id;
    uint8_t kind, flags; uint16_t dispatch_id;
}};
struct __attribute__((packed)) TrainerChangeKitRematchV2 {{
    uint32_t data_address; uint16_t stock_trainer_id, target_trainer_id;
}};
struct __attribute__((packed)) TrainerChangeKitArchiveBindingV1 {{
    uint32_t data_address; uint16_t source_trainer_id, target_trainer_id;
    uint16_t archive_id, physical_flag; uint8_t kind, battle_format, reserved[2];
}};
struct __attribute__((packed)) TrainerChangeKitGimmickV1 {{
    uint16_t trainer_id, dispatch_id; uint8_t mechanic_mode, ai_profile;
    uint8_t user_slot, flags, tera_type, reserved[3];
}};
struct __attribute__((packed)) TrainerChangeKitFlagMapV1 {{
    uint16_t external_flag, physical_flag;
}};

static const struct TrainerChangeKitMemberSidecarV1
gTrainerChangeKitMemberSidecars[TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT] = {{
{chr(10).join(sidecar_lines)}
}};
static const struct TrainerChangeKitExactBindingV1
gTrainerChangeKitExactBindings[TRAINER_CHANGEKIT_FINAL_GENERATED_EXACT_BINDING_COUNT] = {{
{chr(10).join(exact_lines)}
}};
static const struct TrainerChangeKitRematchV2
gTrainerChangeKitRematchMap[TRAINER_CHANGEKIT_FINAL_GENERATED_REMATCH_COUNT] = {{
{chr(10).join(rematch_lines)}
}};
static const struct TrainerChangeKitArchiveBindingV1
gTrainerChangeKitArchiveBindings[TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT] = {{
{chr(10).join(archive_lines)}
}};
static const struct TrainerChangeKitGimmickV1
gTrainerChangeKitGimmicks[TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT] = {{
{chr(10).join(gimmick_lines)}
}};
static const struct TrainerChangeKitFlagMapV1
gTrainerChangeKitFlagMap[TRAINER_CHANGEKIT_FINAL_GENERATED_FLAG_MAP_COUNT] = {{
{chr(10).join(flag_lines)}
}};
#endif
"""
    return text.encode("ascii")


REQUIRED_ENTRYPOINTS = {
    "TrainerV5Runtime_Probe",
    "TrainerV5Runtime_ScriptFlagGet",
    "TrainerV5Runtime_ScriptFlagSet",
    "TrainerV5Runtime_HasTrainerBeenFought",
    "TrainerV5Runtime_SetTrainerFlag",
    "TrainerV5Runtime_ClearTrainerFlag",
    "TrainerV5Runtime_GetRematchTrainerId",
    "TrainerV5Runtime_ConfigureTrainerBattle",
    "TrainerV5Runtime_BuildTrainerPartySetup",
    "TrainerChangeKitFinalRuntime_PolicyBeginAdapter",
    "TrainerChangeKitFinalRuntime_PolicyEndAdapter",
    "TrainerChangeKitFinalRuntime_SaveLoadAdapter",
    "TrainerChangeKitFinalRuntime_SelectArchive",
    "TrainerChangeKitFinalRuntime_BattleBegin",
    "TrainerChangeKitFinalRuntime_BattleEnd",
    "TrainerChangeKitFinalRuntime_CanMegaAdapter",
    "TrainerChangeKitFinalRuntime_MarkMegaAdapter",
    "TrainerChangeKitFinalRuntime_CanZAdapter",
    "TrainerChangeKitFinalRuntime_MarkZAdapter",
    "TrainerChangeKitFinalRuntime_CanDynamaxAdapter",
    "TrainerChangeKitFinalRuntime_MarkDynamaxAdapter",
    "TrainerChangeKitFinalRuntime_CanTeraAdapter",
    "TrainerChangeKitFinalRuntime_MarkTeraAdapter",
    "TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter",
    "TrainerChangeKitFinalRuntime_ExactBindingTable",
    "TrainerChangeKitFinalRuntime_ArchiveTable",
    "TrainerChangeKitFinalRuntime_GimmickTable",
}


def compile_runtime(
    root: Path,
    load_address: int,
    header: bytes,
    trampolines: Mapping[str, int],
    *,
    legacy_published: bool = False,
) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(root, "arm-none-eabi-gcc")
    objcopy = _arm_tool(root, "arm-none-eabi-objcopy")
    nm = _arm_tool(root, "arm-none-eabi-nm")
    source = root / "overlays/trainer_changekit_final_runtime/trainer_changekit_final_runtime.c"
    with tempfile.TemporaryDirectory(prefix="vega-trainer-changekit-final-") as temporary:
        directory = Path(temporary)
        (directory / "trainer_changekit_final_generated.h").write_bytes(header)
        obj = directory / "runtime.o"
        macros = {
            "VEGA_GET_TRAINER_FLAG_ADDRESS": GET_TRAINER_FLAG_ADDRESS,
            "VEGA_FLAG_SET_ADDRESS": FLAG_SET_ADDRESS,
            "VEGA_FLAG_CLEAR_ADDRESS": FLAG_CLEAR_ADDRESS,
            "VEGA_FLAG_GET_ADDRESS": FLAG_GET_ADDRESS,
            "VEGA_GET_REMATCH_TRAMPOLINE_ADDRESS": trampolines["get_rematch"] | 1,
            "VEGA_BUILD_TRAINER_PARTY_TRAMPOLINE_ADDRESS": trampolines["build_trainer_party"] | 1,
            "VEGA_SAVE_LOAD_GAME_DATA_TRAMPOLINE_ADDRESS": trampolines["save_load"] | 1,
            "VEGA_CONFIGURE_TRAINER_BATTLE_ADDRESS": CONFIGURE_TRAINER_BATTLE_ADDRESS,
            "VEGA_CALCULATE_MON_STATS_ADDRESS": CALCULATE_MON_STATS_ADDRESS,
            "VEGA_ENEMY_PARTY_ADDRESS": ENEMY_PARTY_ADDRESS,
            "VEGA_TRAINER_OPPONENT_A_ADDRESS": TRAINER_OPPONENT_A_ADDRESS,
            "VEGA_BATTLE_TYPE_FLAGS_ADDRESS": 0x02022AAC,
            "VEGA_CONFIGURE_NEXT_BATTLE_POLICY_ADDRESS": CONFIGURE_NEXT_BATTLE_POLICY_ADDRESS,
            "VEGA_CFRU_PENDING_CLEAR_ADDRESS": CFRU_PENDING_CLEAR_ADDRESS,
            "VEGA_BATTLE_POLICY_CAN_MEGA_ADDRESS": BATTLE_POLICY_ADDRESSES["CAN_MEGA"],
            "VEGA_BATTLE_POLICY_MARK_MEGA_ADDRESS": BATTLE_POLICY_ADDRESSES["MARK_MEGA"],
            "VEGA_BATTLE_POLICY_CAN_Z_ADDRESS": BATTLE_POLICY_ADDRESSES["CAN_Z"],
            "VEGA_BATTLE_POLICY_MARK_Z_ADDRESS": BATTLE_POLICY_ADDRESSES["MARK_Z"],
            "VEGA_BATTLE_POLICY_CAN_DYNAMAX_ADDRESS": BATTLE_POLICY_ADDRESSES["CAN_DYNAMAX"],
            "VEGA_BATTLE_POLICY_MARK_DYNAMAX_ADDRESS": BATTLE_POLICY_ADDRESSES["MARK_DYNAMAX"],
            "VEGA_BATTLE_POLICY_CAN_TERA_ADDRESS": BATTLE_POLICY_ADDRESSES["CAN_TERA"],
            "VEGA_BATTLE_POLICY_MARK_TERA_ADDRESS": BATTLE_POLICY_ADDRESSES["MARK_TERA"],
            "VEGA_BATTLE_POLICY_BEGIN_ADDRESS": BATTLE_POLICY_ADDRESSES["BEGIN"],
            "VEGA_BATTLE_POLICY_END_ADDRESS": BATTLE_POLICY_ADDRESSES["END"],
            "VEGA_BATTLERS_COUNT_ADDRESS": BATTLERS_COUNT_ADDRESS,
            "VEGA_BATTLER_PARTY_INDEXES_ADDRESS": BATTLER_PARTY_INDEXES_ADDRESS,
            "VEGA_ABSENT_BATTLER_FLAGS_ADDRESS": ABSENT_BATTLER_FLAGS_ADDRESS,
            "VEGA_ACTIVE_BATTLER_ADDRESS": ACTIVE_BATTLER_ADDRESS,
            "VEGA_BATTLE_MONS_ADDRESS": BATTLE_MONS_ADDRESS,
            "VEGA_LOAD_PROPER_ABILITY_BATTLE_DATA_ADDRESS": LOAD_PROPER_ABILITY_BATTLE_DATA_ADDRESS,
            "VEGA_TRAINER_CHANGEKIT_STATE_ADDRESS": TRAINER_CHANGEKIT_STATE_ADDRESS,
        }
        command = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", f"-I{directory}", f"-I{root}",
        ]
        if legacy_published:
            command.append("-DTRAINER_CHANGEKIT_LEGACY_PUBLISHED=1")
        command += [
            f"-D{name}=0x{value:08X}u" for name, value in macros.items()
        ]
        _run([*command, "-c", str(source), "-o", str(obj)], "compile final Trainer ChangeKit runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.TrainerV5Runtime_*)) KEEP(*(.text.TrainerChangeKitFinalRuntime_*)) *(.text*) *(.rodata*) *(.data*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "runtime.elf"
        binary = directory / "runtime.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,TrainerV5Runtime_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link final Trainer ChangeKit runtime")
        undefined = _run([nm, "-u", str(elf)], "final runtime undefined symbol audit")
        if undefined:
            _fail("final runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "final runtime objcopy")
        symbols: dict[str, int] = {}
        nm_output = _run(
            [nm, "-n", "--defined-only", str(elf)], "final runtime nm"
        )
        mutable_rom_symbols: list[str] = []
        for line in nm_output.splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
                if fields[1] in {"B", "b", "C", "c"}:
                    mutable_rom_symbols.append(fields[2])
        if mutable_rom_symbols:
            _fail(
                "final runtime has ROM-linked mutable state: "
                + ", ".join(mutable_rom_symbols)
            )
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing:
            _fail(f"final runtime exports are missing: {missing}")
        raw = binary.read_bytes()
        if not raw or len(raw) > 512 * 1024:
            _fail(f"final runtime linked size is unreasonable: {len(raw)}")
        return raw, symbols


def _party_blob(
    serialized: Mapping[str, Any], party_base_address: int
) -> tuple[bytes, dict[str, int]]:
    blob = bytearray()
    pointers: dict[str, int] = {}
    for row in serialized["party_rows"]:
        while len(blob) & 3:
            blob.append(0)
        key = row["party_key"]
        pointers[key] = party_base_address + len(blob)
        blob.extend(serialized["party_bytes"][key])
    return bytes(blob), pointers


def _trainer_table(
    root: Path,
    stage: bytes,
    clean: bytes,
    input_meta: Mapping[str, Any],
    source: Mapping[str, Any],
    serialized: Mapping[str, Any],
    event_info: Mapping[str, Any],
    party_pointers: Mapping[str, int],
) -> tuple[bytes, list[dict[str, Any]]]:
    current_address = int(input_meta["trainer_table"]["new_address"])
    current_count = int(input_meta["trainer_table"]["new_count"])
    if current_count != 1367 or input_meta["trainer_table"]["record_size"] != TRAINER_RECORD_SIZE:
        _fail("Stage34 trainer table ABI differs")
    current_offset = _rom_offset(
        current_address, current_count * TRAINER_RECORD_SIZE, "Stage34 trainer table"
    )
    clean_address = 0x081FDFD8
    clean_count = 743
    clean_offset = clean_address - GBA_ROM_BASE
    if clean_offset + clean_count * TRAINER_RECORD_SIZE > len(clean):
        _fail("clean trainer table is truncated")
    table = bytearray(TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE)
    table[:current_count * TRAINER_RECORD_SIZE] = stage[
        current_offset:current_offset + current_count * TRAINER_RECORD_SIZE
    ]
    party_by_key = {row["party_key"]: row for row in serialized["party_rows"]}
    plan_bindings = event_info["plan_bindings"]
    audit: list[dict[str, Any]] = []
    populated: set[int] = set()
    for consumer in sorted(source["consumers"], key=lambda row: int(row["runtime_trainer_id"], 0)):
        key = consumer["encounter_key"]
        target = int(consumer["runtime_trainer_id"], 0)
        if target in populated or not 0 <= target < TRAINER_TABLE_COUNT:
            _fail(f"{key}: duplicate/out-of-range trainer target {target}")
        populated.add(target)
        template_kind: str
        template_id: int
        if consumer["binding_mode"] == "KANTO_NEW":
            binding = plan_bindings[key]
            if binding["owner_kind"] == "EXISTING":
                template_kind = "STAGE34_EXISTING_KANTO"
                template_id = target
                start = current_offset + template_id * TRAINER_RECORD_SIZE
                source_record = stage[start:start + TRAINER_RECORD_SIZE]
            else:
                template_kind = "CLEAN_FIRERED_ROOTED_IDENTITY"
                template_id = int(binding["source_template_trainer_id"])
                if not 0 <= template_id < clean_count:
                    _fail(f"{key}: clean template ID outside 0..742: {template_id}")
                start = clean_offset + template_id * TRAINER_RECORD_SIZE
                source_record = clean[start:start + TRAINER_RECORD_SIZE]
        else:
            template_kind = "STAGE34_PHYSICAL_TRAINER"
            template_id = int(consumer["source_trainer_id"], 0)
            if not 0 <= template_id < current_count:
                _fail(f"{key}: Stage34 template ID outside table: {template_id}")
            start = current_offset + template_id * TRAINER_RECORD_SIZE
            source_record = stage[start:start + TRAINER_RECORD_SIZE]
        if len(source_record) != TRAINER_RECORD_SIZE:
            _fail(f"{key}: trainer template is truncated")
        party = party_by_key[consumer["party_key"]]
        record = bytearray(source_record)
        record[0] = 3  # F_TRAINER_PARTY_CUSTOM_MOVESET | F_TRAINER_PARTY_HELD_ITEM
        items = party["trainer_item_keys"]
        if len(items) > 4:
            _fail(f"{key}: more than four trainer items")
        item_ids = [source["registries"]["item"][item] for item in items]
        item_ids += [0] * (4 - len(item_ids))
        struct.pack_into("<4H", record, 0x0A, *item_ids)
        record[0x12] = 1 if party["battle_format"] == "DOUBLE" else 0
        struct.pack_into("<I", record, 0x14, AI_FLAGS[party["ai_profile_key"]])
        record[0x18] = int(party["party_size"])
        pointer = party_pointers[party["party_key"]]
        struct.pack_into("<I", record, 0x1C, pointer)
        target_offset = target * TRAINER_RECORD_SIZE
        table[target_offset:target_offset + TRAINER_RECORD_SIZE] = record
        audit.append({
            "encounter_key": key,
            "trainer_id": target,
            "binding_mode": consumer["binding_mode"],
            "template_kind": template_kind,
            "template_trainer_id": template_id,
            "template_sha256": _sha(source_record),
            "record_sha256": _sha(record),
            "party_key": party["party_key"],
            "party_size": party["party_size"],
            "party_pointer": pointer,
            "battle_format": party["battle_format"],
            "ai_flags": AI_FLAGS[party["ai_profile_key"]],
            "trainer_item_ids": item_ids,
        })
    if len(populated) != ENCOUNTER_COUNT:
        _fail("trainer table populated row count differs")
    return bytes(table), audit


def _layout(code_size: int) -> dict[str, int]:
    table = _align(CODE_RELATIVE_OFFSET + code_size, 16)
    party = _align(table + TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE, 4)
    return {"code": CODE_RELATIVE_OFFSET, "table": table, "party": party}


def _allocation(
    root: Path, previous: Mapping[str, Any], size: int, digest: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "Trainer ChangeKit 1302 physical battles, 4284 trainer table, 6490-member "
            "sidecars, Kanto/Archive events, dialogue and four-mechanic policy runtime"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage35 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage35 allocation is not unique")
    return matches[0], report


def _thumb_bl(site_address: int, target_address: int) -> bytes:
    site = site_address & ~1
    target = target_address & ~1
    delta = target - (site + 4)
    if delta & 1 or not -0x400000 <= delta < 0x400000:
        _fail(f"Thumb BL out of range: {site:#010x} -> {target:#010x}")
    return struct.pack(
        "<HH", 0xF000 | ((delta >> 12) & 0x7FF), 0xF800 | ((delta >> 1) & 0x7FF)
    )


def _build_payload(
    root: Path,
    inputs: Mapping[str, Any],
    source: Mapping[str, Any],
    serialized: Mapping[str, Any],
    event_blob: Blob,
    event_info: Mapping[str, Any],
    payload_offset: int,
    provisional_code_size: int,
) -> tuple[bytes, dict[str, Any], bytes, list[dict[str, Any]], list[dict[str, Any]], bytes]:
    payload_address = GBA_ROM_BASE + payload_offset
    layout = _layout(provisional_code_size)
    party_size = sum(_align(len(serialized["party_bytes"][row["party_key"]]), 4)
                     for row in serialized["party_rows"])
    # _party_blob aligns before each row; all parties are already multiples of 16.
    if party_size != sum(len(serialized["party_bytes"][row["party_key"]])
                         for row in serialized["party_rows"]):
        _fail("unexpected non-aligned party bytes")
    event_relative = _align(layout["party"] + party_size, 4)
    event_base = payload_address + event_relative
    battle_rows = _event_battle_rows(event_blob, event_info, source, event_base)
    tables = build_runtime_tables(root, source, serialized, battle_rows)
    table_address = payload_address + layout["table"]
    header = generated_header(tables, table_address)
    trampolines = {
        name: payload_address + TRAMPOLINE_RELATIVES[name] for name in TRAMPOLINE_NAMES
    }
    code_address = payload_address + layout["code"]
    code, symbols = compile_runtime(
        root, code_address, header, trampolines, legacy_published=True,
    )
    if len(code) != provisional_code_size or _layout(len(code)) != layout:
        _fail("final runtime code size changed after absolute table linking")
    party_blob, party_pointers = _party_blob(
        serialized, payload_address + layout["party"]
    )
    table, table_audit = _trainer_table(
        root, inputs["stage"], inputs["clean"], inputs["input_meta"], source,
        serialized, event_info, party_pointers,
    )
    event = event_blob.finish(event_base)
    payload_size = event_relative + len(event)
    payload = bytearray(payload_size)
    input_hooks = {row["name"]: row for row in inputs["input_meta"]["hooks"]}
    for name in ("get_rematch", "build_trainer_party"):
        stock = bytes.fromhex(input_hooks[name]["stock_prologue_hex"])
        if len(stock) != 8:
            _fail(f"{name}: stock trampoline prologue is not eight bytes")
        address = HOOKS[name][0]
        raw = _trampoline(stock, (address + 8) | 1)
        if len(raw) != TRAMPOLINE_SIZES[name]:
            _fail(f"{name}: trampoline size differs")
        start = TRAMPOLINE_RELATIVES[name]
        payload[start:start + len(raw)] = raw
    hook_contract = _read_json(root / "overlays/trainer_changekit_final_runtime/hook_contract_stage34.json")
    save_raw = bytes.fromhex(hook_contract["save_load_entry_rewrite"]["trampoline_bytes"])
    if len(save_raw) != TRAMPOLINE_SIZES["save_load"]:
        _fail("Save_LoadGameData trampoline is not 24 bytes")
    start = TRAMPOLINE_RELATIVES["save_load"]
    payload[start:start + len(save_raw)] = save_raw
    payload[layout["code"]:layout["code"] + len(code)] = code
    payload[layout["table"]:layout["table"] + len(table)] = table
    payload[layout["party"]:layout["party"] + len(party_blob)] = party_blob
    payload[event_relative:event_relative + len(event)] = event
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    struct.pack_into(
        "<8s16I", payload, 0, b"VEGATC35",
        1, len(payload), len(code), TRAINER_TABLE_COUNT, ENCOUNTER_COUNT,
        MEMBER_COUNT, len(tables["rematch"]), ARCHIVE_COUNT,
        sum(row["mechanic_mode"] != 0 for row in tables["gimmicks"]),
        table_address, payload_address + layout["party"], event_base,
        entrypoints["TrainerV5Runtime_Probe"],
        entrypoints["TrainerChangeKitFinalRuntime_GimmickTable"],
        entrypoints["TrainerChangeKitFinalRuntime_PolicyBeginAdapter"],
        entrypoints["TrainerChangeKitFinalRuntime_SaveLoadAdapter"],
    )
    runtime = {
        "payload": {
            "magic": "VEGATC35", "offset": payload_offset, "address": payload_address,
            "size": len(payload), "sha256": _sha(payload),
            "code_address": code_address, "code_size": len(code), "code_sha256": _sha(code),
            "trainer_table_address": table_address, "trainer_table_size": len(table),
            "party_blob_address": payload_address + layout["party"], "party_blob_size": len(party_blob),
            "event_blob_address": event_base, "event_blob_size": len(event),
        },
        "layout": layout | {"event": event_relative},
        "trampolines": {name: address | 1 for name, address in trampolines.items()},
        "entrypoints": entrypoints,
        "symbols": {name: value for name, value in sorted(symbols.items())
                    if code_address <= value < code_address + len(code)},
        "table_counts": {name: len(tables[name]) for name in
                         ("sidecars", "exact", "rematch", "archives", "gimmicks", "flags")},
    }
    serialized_doc = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "encounter_count": ENCOUNTER_COUNT, "party_count": PARTY_COUNT,
        "member_count": MEMBER_COUNT, "trainer_table_count": TRAINER_TABLE_COUNT,
        "battle_rows": battle_rows, "tables": tables,
        "party_rows": serialized["party_rows"], "trainer_records": table_audit,
    }
    return bytes(payload), runtime, header, battle_rows, table_audit, _stable(serialized_doc)


def _provisional_link(
    root: Path,
    source: Mapping[str, Any],
    serialized: Mapping[str, Any],
    event_blob: Blob,
    event_info: Mapping[str, Any],
) -> int:
    layout_guess = _layout(0)
    party_size = sum(len(serialized["party_bytes"][row["party_key"]])
                     for row in serialized["party_rows"])
    event_base = GBA_ROM_BASE + _align(layout_guess["party"] + party_size, 4)
    battles = _event_battle_rows(event_blob, event_info, source, event_base)
    tables = build_runtime_tables(root, source, serialized, battles)
    header = generated_header(tables, GBA_ROM_BASE + layout_guess["table"])
    trampolines = {
        name: GBA_ROM_BASE + TRAMPOLINE_RELATIVES[name] for name in TRAMPOLINE_NAMES
    }
    code, _ = compile_runtime(
        root, GBA_ROM_BASE + CODE_RELATIVE_OFFSET, header, trampolines,
        legacy_published=True,
    )
    return len(code)


def _patch_bytes(
    output: bytearray,
    stage: bytes,
    declared: list[dict[str, Any]],
    address: int,
    expected: bytes,
    replacement: bytes,
    kind: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{kind}: expected/replacement sizes differ")
    offset = _rom_offset(address, len(expected), kind)
    actual = bytes(stage[offset:offset + len(expected)])
    if actual != expected:
        _fail(f"{kind}: expected bytes differ at 0x{address:08X}: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement), "kind": kind})
    return {
        "address": address, "offset": offset, "size": len(replacement),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }


def _report(metadata: Mapping[str, Any]) -> bytes:
    counts = metadata["runtime"]["table_counts"]
    plan = metadata["physical_events"]["summary"]
    mechanics = metadata["coverage"]["gimmick_type_counts"]
    text = f"""# Trainer ChangeKit Task 01--06 最終統合 / Stage 35

## 結論

- Task 01--06を検証し、全1,302 encounterを1,302個の一意な実trainerbattle commandへ接続した。
- Tohoku canonical 1,030戦、Kanto既存13戦、新規188戦、Archive補完71戦を物理実装した。
- 1,302 party / 6,490 memberを16-byte party recordとlive sidecarへserializeし、trainer tableを4,284件へ拡張した。
- 会話4,662行は元文対応を保持し、現行1-byte fontで表示可能な104本文へ決定変換した。
- Mega {mechanics['MEGA']}、Zワザ {mechanics['Z_MOVE']}、ダイマックス {mechanics['DYNAMAX']}、テラスタル {mechanics['TERASTAL']} をconsumer限定policyへ接続した。
- Can/Mark、battle begin/end、敗北/abort、交代・瀕死再走査、save/reload cleanupをStage34 CFRU実callsiteへ接続した。

## 物理配置

- Kanto existing: {plan['existing_bindings']}
- Kanto normal: {plan['normal_bindings']}
- Kanto relocated: {plan['relocated_bindings']}
- Archive: {plan['archive_bindings']}
- New object records: {plan['new_object_records']}
- Max objects/map: {plan['max_objects_per_map']} / 15
- Max Archive/map: {plan['max_archive_per_map']} / 5
- 一意physical commands: {metadata['physical_bindings']['unique_command_count']}

## Runtime tables

- Sidecars: {counts['sidecars']}
- Exact bindings: {counts['exact']}
- Rematch bindings: {counts['rematch']}
- Archive bindings: {counts['archives']}
- Gimmick rows: {counts['gimmicks']}
- Flag mappings: {counts['flags']}

## ROM

- Input Stage34: `{metadata['input']['sha256']}`
- Output Stage35: `{metadata['output']['sha256']}`
- Payload: `{metadata['runtime']['payload']['address']:#010x}` / {metadata['runtime']['payload']['size']} bytes
- Allocator overlap: {metadata['allocation']['overlap_count']}
- Declared span外変更: {metadata['change_audit']['outside_declared_span_count']}
- incremental / cumulative BPS exact round trip: PASS / PASS

元のChangeKit ZIPは変更していない。Task05 REF1012を含む51 flag false-positiveと20 shared-command extra callerは、元命令を破壊せず独立Archive戦として実装した。取得hostと競合したKanto 3戦は同一mapの最近傍walkable tileへ移設し、元hostを保持した。
"""
    return text.encode("utf-8")


def _mgba_cases(
    source: Mapping[str, Any],
    serialized: Mapping[str, Any],
    battle_rows: Sequence[Mapping[str, Any]],
    tables: Mapping[str, Any],
) -> bytes:
    """Build the flat exact-ROM fixture consumed by the libmGBA runner."""
    battle_by_key = {row["encounter_key"]: row for row in battle_rows}
    gimmick_by_key = {row["encounter_key"]: row for row in tables["gimmicks"]}
    party_by_key = {row["encounter_key"]: row for row in serialized["party_rows"]}
    record_by_id = {row["trainer_id"]: row for row in serialized["trainer_records"]}
    quick_keys: set[str] = set()

    def select(predicate: Any) -> None:
        match = next((row for row in sorted(battle_rows, key=lambda item: item["encounter_key"])
                      if predicate(row)), None)
        if match is not None:
            quick_keys.add(match["encounter_key"])

    for mode in ("CANONICAL", "ARCHIVE", "KANTO_NEW"):
        select(lambda row, expected=mode: row["binding_mode"] == expected)
    for mechanic_mode in range(5):
        select(lambda row, expected=mechanic_mode:
               gimmick_by_key[row["encounter_key"]]["mechanic_mode"] == expected)
    select(lambda row: row["kind"] == 8)
    select(lambda row: row["battle_format"] == "DOUBLE")
    select(lambda row: row["target_trainer_id"] == 4283)
    select(lambda row: any(not member["ability_native"]
                           for member in party_by_key[row["encounter_key"]]["members"]))

    rows: list[dict[str, Any]] = []
    for battle in sorted(battle_rows, key=lambda row: row["target_trainer_id"]):
        key = battle["encounter_key"]
        party = party_by_key[key]
        gimmick = gimmick_by_key[key]
        trainer_record = record_by_id[battle["target_trainer_id"]]
        for member in party["members"]:
            rows.append({
                "encounter_key": key,
                "binding_mode": battle["binding_mode"],
                "quick": int(key in quick_keys),
                "trainer_id": battle["target_trainer_id"],
                "slot": member["slot"],
                "party_size": party["party_size"],
                "battle_format": battle["battle_format"],
                "species_id": member["species_id"],
                "level": member["level"],
                "held_item_id": member["item_id"],
                "move1_id": member["move_ids"][0],
                "move2_id": member["move_ids"][1],
                "move3_id": member["move_ids"][2],
                "move4_id": member["move_ids"][3],
                "ability_id": member["ability_id"],
                "ability_native": int(member["ability_native"]),
                "nature_id": member["nature_id"],
                "ability_mode": member["ability_mode"],
                "iv": member["iv"],
                "hp_ev": member["hp_ev"],
                "atk_ev": member["atk_ev"],
                "def_ev": member["def_ev"],
                "speed_ev": member["speed_ev"],
                "sp_atk_ev": member["sp_atk_ev"],
                "sp_def_ev": member["sp_def_ev"],
                "command_address": f"0x{battle['command_address']:08X}",
                "data_address": f"0x{battle['data_address']:08X}",
                "source_trainer_id": battle["source_trainer_id"],
                "kind": battle["kind"],
                "archive_id": battle["archive_id"],
                "physical_flag": f"0x{battle['physical_flag']:04X}",
                "gimmick_mode": gimmick["mechanic_mode"],
                "gimmick_slot": gimmick["user_slot"],
                "tera_type": gimmick["tera_type"],
                "ai_flags": trainer_record["ai_flags"],
                "trainer_item1": trainer_record["trainer_item_ids"][0],
                "trainer_item2": trainer_record["trainer_item_ids"][1],
                "trainer_item3": trainer_record["trainer_item_ids"][2],
                "trainer_item4": trainer_record["trainer_item_ids"][3],
            })
    if len(rows) != MEMBER_COUNT or not 8 <= len(quick_keys) <= 16:
        _fail(f"mGBA fixture cardinality differs: rows={len(rows)} quick={len(quick_keys)}")
    return _csv_bytes(rows)


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    ram_audit = _validate_runtime_ram_layout(root)
    inputs = _input_contract(root)
    source = load_source(root, inputs["stage"], inputs["species_meta"])
    serialized = serialize_parties(source, inputs["stage"], inputs["species_meta"])
    event_blob, event_info, event_plan = build_event_blob(
        root, inputs["stage"], inputs["clean"], source,
        inputs["stage17_symbols"], inputs["acquisition_meta"],
    )
    provisional_code_size = _provisional_link(
        root, source, serialized, event_blob, event_info
    )
    provisional_layout = _layout(provisional_code_size)
    party_size = sum(len(serialized["party_bytes"][row["party_key"]])
                     for row in serialized["party_rows"])
    provisional_event = _align(provisional_layout["party"] + party_size, 4)
    provisional_size = provisional_event + len(event_blob.data)
    allocation, _ = _allocation(
        root, inputs["previous_alloc"], provisional_size, "0" * 64
    )
    payload_offset = int(allocation["start"])
    payload, runtime, header, battle_rows, table_audit, serialized_doc = _build_payload(
        root, inputs, source, serialized, event_blob, event_info,
        payload_offset, provisional_code_size,
    )
    if len(payload) != provisional_size:
        _fail(f"provisional/final payload size differs: {provisional_size}/{len(payload)}")
    allocation, allocation_report = _allocation(
        root, inputs["previous_alloc"], len(payload), _sha(payload)
    )
    if int(allocation["start"]) != payload_offset:
        _fail("final payload placement changed after content hash")
    payload_end = int(allocation["end_exclusive"])
    stage = inputs["stage"]
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage35 payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_offset, "end_exclusive": payload_end, "kind": "stage35_payload"
    }]
    patch_rows: list[dict[str, Any]] = []

    # All previous trainer table consumers are repointed to the 4,284-row table.
    previous_table = int(inputs["input_meta"]["trainer_table"]["new_address"])
    new_table = int(runtime["payload"]["trainer_table_address"])
    trainer_repoints: list[dict[str, Any]] = []
    for row in inputs["input_meta"]["trainer_table"]["repoints"]:
        site = GBA_ROM_BASE + int(row["site_offset"])
        field_offset = int(row["field_offset"])
        expected = struct.pack("<I", previous_table + field_offset)
        replacement = struct.pack("<I", new_table + field_offset)
        trainer_repoints.append(_patch_bytes(
            output, stage, declared, site, expected, replacement, "trainer_table_repoint"
        ) | {"field_offset": field_offset})
    if len(trainer_repoints) != 24:
        _fail("trainer table repoint count differs")

    # Stage34 Trainer V5 hook ABI remains stable through same-name wrappers.
    input_hooks = {row["name"]: row for row in inputs["input_meta"]["hooks"]}
    trainer_hooks: list[dict[str, Any]] = []
    for name, (address, symbol) in HOOKS.items():
        expected = bytes.fromhex(input_hooks[name]["replacement_hex"])
        replacement = _jump_stub(runtime["entrypoints"][symbol])
        trainer_hooks.append(_patch_bytes(
            output, stage, declared, address, expected, replacement, f"trainer_hook::{name}"
        ) | {"name": name, "symbol": symbol, "target": runtime["entrypoints"][symbol],
             "trampoline": runtime["trampolines"].get(name)})

    hook_contract = _read_json(
        root / "overlays/trainer_changekit_final_runtime/hook_contract_stage34.json"
    )
    policy_hooks: list[dict[str, Any]] = []
    for row in hook_contract["bl_rewrites"]:
        address = int(row["callsite"], 0)
        expected = bytes.fromhex(row["expected"])
        target = runtime["entrypoints"][row["adapter"]]
        replacement = _thumb_bl(address, target)
        policy_hooks.append(_patch_bytes(
            output, stage, declared, address, expected, replacement,
            f"policy_hook::{row['name']}"
        ) | {"name": row["name"], "adapter": row["adapter"], "target": target,
             "original_target": int(row["original_target"], 0)})
    if len(policy_hooks) != 17:
        _fail("policy BL hook count differs")

    ability_contract = hook_contract["ability_load_rewrite"]
    ability_address = int(ability_contract["callsite"], 0)
    ability_target = runtime["entrypoints"][ability_contract["adapter"]]
    ability_hook = _patch_bytes(
        output, stage, declared, ability_address,
        bytes.fromhex(ability_contract["expected"]),
        _thumb_bl(ability_address, ability_target),
        "ability_load_hook",
    ) | {
        "name": ability_contract["name"],
        "adapter": ability_contract["adapter"],
        "target": ability_target,
        "original_target": int(ability_contract["original_target"], 0),
    }

    save_contract = hook_contract["save_load_entry_rewrite"]
    save_address = int(save_contract["entry"], 0)
    save_target = runtime["entrypoints"][save_contract["adapter"]]
    save_hook = _patch_bytes(
        output, stage, declared, save_address,
        bytes.fromhex(save_contract["expected"]), _jump_stub(save_target),
        "save_load_entry_hook",
    ) | {"adapter": save_contract["adapter"], "target": save_target,
         "trampoline": runtime["trampolines"]["save_load"]}

    # Replace every old physical command with a bounded goto to its unique proxy.
    proxy_patches: list[dict[str, Any]] = []
    event_base = int(runtime["payload"]["event_blob_address"])
    for row in event_info["proxy_rows"]:
        address = int(row["original_command_address"])
        expected = _read_trainer_command(stage, address, row["kind"])["raw"]
        target = event_base + event_blob.labels[row["script_label"]]
        replacement = _goto_absolute(target) + bytes(len(expected) - 5)
        proxy_patches.append(_patch_bytes(
            output, stage, declared, address, expected, replacement,
            f"trainer_proxy::{row['encounter_key']}"
        ) | {"encounter_key": row["encounter_key"], "target": target,
             "battle_address": event_base + event_blob.labels[row["battle_label"]]})
    if len(proxy_patches) != CANONICAL_COUNT + KANTO_EXISTING_COUNT:
        _fail("proxy patch count differs")

    # Map event headers for all new Kanto/Archive object tables.
    map_patches: list[dict[str, Any]] = []
    for row in event_info["map_rows"]:
        target = event_base + event_blob.labels[row["event_label"]]
        map_patches.append(_patch_bytes(
            output, stage, declared, int(row["patch_address"]),
            struct.pack("<I", int(row["old_event_header_address"])),
            struct.pack("<I", target), f"map_event::{row['map_key']}"
        ) | {"map_key": row["map_key"], "target": target,
             "object_count": row["object_count"], "new_object_count": row["new_object_count"]})

    object_patches: list[dict[str, Any]] = []
    for gate in event_info["existing_gates"].values():
        if gate["object_patch_mode"] != "IN_PLACE_OBJECT_POINTER":
            continue
        target = event_base + event_blob.labels[gate["gate_label"]]
        object_patches.append(_patch_bytes(
            output, stage, declared, int(gate["object_script_pointer_site_address"]),
            struct.pack("<I", int(gate["expected_object_script_address"])),
            struct.pack("<I", target), f"kanto_existing_object::{gate['encounter_key']}"
        ) | {"encounter_key": gate["encounter_key"], "target": target})

    changed = [index for index, (before, after) in enumerate(zip(stage, output)) if before != after]
    outside = [
        index for index in changed
        if not any(row["start"] <= index < row["end_exclusive"] for row in declared)
    ]
    if outside:
        _fail(f"Stage35 changed bytes outside declared spans: {outside[:16]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    cumulative = _sparse_bps(inputs["base"], output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(inputs["base"], cumulative) != output_raw:
        _fail("Stage35 BPS exact round trip differs")

    mechanics = Counter(row["gimmick_type"] for row in source["gimmicks"])
    formats = Counter(row["battle_format"] for row in source["parties"])
    direct_ability_overrides = sum(
        not row["ability_native"] for row in serialized["sidecars"]
    )
    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input": {"path": INPUT_ROM.as_posix(), "sha256": _sha(stage), "size": len(stage)},
        "clean_input": {"path": CLEAN_ROM.as_posix(), "sha256": _sha(inputs["clean"]),
                        "size": len(inputs["clean"])},
        "base_release": {"path": BASE_ROM.as_posix(), "sha256": _sha(inputs["base"]),
                         "size": len(inputs["base"])},
        "output": {"path": OUTPUT_ROM.as_posix(), "sha256": _sha(output_raw),
                   "size": len(output_raw)},
        "coverage": {
            **source["coverage"], "battle_format_counts": dict(formats),
            "gimmick_type_counts": dict(mechanics),
            "authored_ability_direct_override_count": direct_ability_overrides,
        },
        "runtime": runtime,
        "runtime_ram": ram_audit,
        "trainer_table": {
            "old_address": previous_table, "old_count": 1367,
            "new_address": new_table, "new_count": TRAINER_TABLE_COUNT,
            "record_size": TRAINER_RECORD_SIZE, "repoint_count": len(trainer_repoints),
            "repoints": trainer_repoints,
        },
        "physical_events": {
            "summary": event_plan["summary"], "relocations": event_plan["relocations"],
            "map_patch_count": len(map_patches), "object_pointer_patch_count": len(object_patches),
            "existing_gate_count": len(event_info["existing_gates"]),
        },
        "physical_bindings": {
            "count": len(battle_rows),
            "unique_command_count": len({row["command_address"] for row in battle_rows}),
            "rows": battle_rows,
        },
        "hooks": {
            "trainer_v5": trainer_hooks, "policy_bl": policy_hooks,
            "ability_load": ability_hook, "save_load": save_hook,
        },
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(), "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patches": {
            "incremental": {"path": PATCH_INCREMENTAL.as_posix(), "size": len(incremental),
                            "sha256": _sha(incremental), "source_sha256": _sha(stage),
                            "target_sha256": _sha(output_raw), "exact": True},
            "cumulative": {"path": PATCH_CUMULATIVE.as_posix(), "size": len(cumulative),
                           "sha256": _sha(cumulative), "source_sha256": _sha(inputs["base"]),
                           "target_sha256": _sha(output_raw), "exact": True},
        },
        "change_audit": {"changed_byte_count": len(changed), "declared_spans": declared,
                         "outside_declared_span_count": len(outside)},
        "invariants": {
            "stage34_hash_pinned": _sha(stage) == EXPECTED_STAGE34_SHA256,
            "clean_hash_pinned": _sha(inputs["clean"]) == EXPECTED_CLEAN_SHA256,
            "encounters_1302": len(battle_rows) == 1302,
            "physical_commands_unique_1302": len({row["command_address"] for row in battle_rows}) == 1302,
            "parties_1302": len(serialized["party_rows"]) == 1302,
            "members_6490": len(serialized["sidecars"]) == 6490,
            "all_member_ability_ids_serialized": all(
                0 <= row["ability_id"] <= 0xFFFF for row in serialized["sidecars"]
            ),
            "ability_direct_overrides_924": direct_ability_overrides == 924,
            "single_1228_double_74": formats == Counter({"SINGLE": 1228, "DOUBLE": 74}),
            "trainer_table_4284": TRAINER_TABLE_COUNT == 4284,
            "archive_71": runtime["table_counts"]["archives"] == 71,
            "kanto_existing_13_new_188": event_plan["summary"]["existing_bindings"] == 13
                and event_plan["summary"]["normal_bindings"] + event_plan["summary"]["relocated_bindings"] == 188,
            "dialogue_rows_4662": len(source["dialogues"]) == 4662,
            "dialogue_readings_104": len(event_info["readings"]["rows"]) == 104,
            "policy_bl_hooks_17": len(policy_hooks) == 17,
            "authored_ability_load_hook": ability_hook["target"] == ability_target,
            "save_load_relocated_trampoline_24": TRAMPOLINE_SIZES["save_load"] == 24,
            "runtime_ram_exact_unshared_48": ram_audit["live_overlap_count"] == 0
                and ram_audit["size"] == TRAINER_CHANGEKIT_STATE_SIZE,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "declared_changes_only": not outside,
            "incremental_bps_exact": True, "cumulative_bps_exact": True,
            "original_zips_untouched": True,
        },
    }
    if not all(metadata["invariants"].values()):
        failed = [key for key, value in metadata["invariants"].items() if not value]
        _fail(f"Stage35 static invariants failed: {failed}")
    symbols_doc = {
        "schema_version": 1, "task": TASK, **runtime,
        "hooks": metadata["hooks"],
    }
    binding_report = [{
        **row,
        "command_address": f"0x{row['command_address']:08X}",
        "data_address": f"0x{row['data_address']:08X}",
        "physical_flag": f"0x{row['physical_flag']:04X}",
    } for row in battle_rows]
    serialized_object = json.loads(serialized_doc)
    mgba_cases = _mgba_cases(
        source, serialized_object, battle_rows, serialized_object["tables"]
    )
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        OUTPUT_PLAN.as_posix(): _stable(event_plan),
        OUTPUT_SERIALIZED.as_posix(): serialized_doc,
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): payload,
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols_doc),
        OUTPUT_BINDINGS.as_posix(): _csv_bytes(binding_report),
        OUTPUT_REPORT.as_posix(): _report(metadata),
        OUTPUT_MGBA_CASES.as_posix(): mgba_cases,
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CUMULATIVE.as_posix(): cumulative,
    }


def _write_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (root / relative).is_file() or (root / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Trainer ChangeKit final generated outputs differ: " + ", ".join(differences))


def _mgba_outputs(root: Path, outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    runner = root / "tools/mgba_trainer_changekit_final_smoke.c"
    if not runner.is_file():
        _fail(f"final Trainer ChangeKit mGBA runner is missing: {runner}")
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    runtime = metadata["runtime"]
    entry = runtime["entrypoints"]
    names = [
        "TrainerV5Runtime_Probe",
        "TrainerV5Runtime_SetTrainerFlag",
        "TrainerV5Runtime_ClearTrainerFlag",
        "TrainerV5Runtime_HasTrainerBeenFought",
        "TrainerV5Runtime_GetRematchTrainerId",
        "TrainerV5Runtime_ConfigureTrainerBattle",
        "TrainerV5Runtime_BuildTrainerPartySetup",
        "TrainerChangeKitFinalRuntime_SelectArchive",
        "TrainerChangeKitFinalRuntime_BattleBegin",
        "TrainerChangeKitFinalRuntime_BattleEnd",
        "TrainerChangeKitFinalRuntime_PolicyBeginAdapter",
        "TrainerChangeKitFinalRuntime_PolicyEndAdapter",
        "TrainerChangeKitFinalRuntime_SaveLoadAdapter",
        "TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter",
        "TrainerChangeKitFinalRuntime_CanMegaAdapter",
        "TrainerChangeKitFinalRuntime_MarkMegaAdapter",
        "TrainerChangeKitFinalRuntime_CanZAdapter",
        "TrainerChangeKitFinalRuntime_MarkZAdapter",
        "TrainerChangeKitFinalRuntime_CanDynamaxAdapter",
        "TrainerChangeKitFinalRuntime_MarkDynamaxAdapter",
        "TrainerChangeKitFinalRuntime_CanTeraAdapter",
        "TrainerChangeKitFinalRuntime_MarkTeraAdapter",
    ]
    missing = [name for name in names if name not in entry]
    if missing:
        _fail(f"mGBA required runtime entrypoints are missing: {missing}")
    with tempfile.TemporaryDirectory(prefix="vega-trainer-changekit-mgba-") as temporary:
        directory = Path(temporary)
        executable = directory / "mgba-trainer-changekit-final"
        rom = directory / "stage35.gba"
        cases = directory / "cases.csv"
        rom.write_bytes(outputs[OUTPUT_ROM.as_posix()])
        cases.write_bytes(outputs[OUTPUT_MGBA_CASES.as_posix()])
        _run([
            _host_cc(root), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "final Trainer ChangeKit libmGBA compile", cwd=root)
        result: dict[str, bytes] = {}
        for mode, output_path, timeout in (
            ("quick", OUTPUT_MGBA_QUICK, 300),
            ("full", OUTPUT_MGBA_FULL, 1200),
        ):
            save = directory / f"{mode}.sav"
            command = [
                str(executable), str(rom), str(save), str(cases), mode,
                *[hex(entry[name]) for name in names],
                hex(runtime["payload"]["trainer_table_address"]),
            ]
            stdout = _run(
                command, f"final Trainer ChangeKit mGBA {mode}",
                cwd=root, timeout=timeout,
            )
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as exc:
                _fail(f"mGBA {mode} output is not JSON: {exc}: {stdout[-1000:]}")
            if (document.get("status") != "PASS" or not all(
                document.get("checks", {}).values()
            )) or document.get("warnings_errors") != 0:
                _fail(f"mGBA {mode} did not report deterministic all-PASS")
            document.update({
                "fixture": "trainer_changekit_final_exact_rom",
                "rom_sha256": _sha(outputs[OUTPUT_ROM.as_posix()]),
                "cases_sha256": _sha(outputs[OUTPUT_MGBA_CASES.as_posix()]),
                "runner_sha256": _sha(runner.read_bytes()),
                "process_runs": 1,
            })
            result[output_path.as_posix()] = _stable(document)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only", "mgba"))
    args = parser.parse_args()
    try:
        outputs = build_runtime_outputs(ROOT)
        repeated = build_runtime_outputs(ROOT)
        if outputs != repeated:
            _fail("Trainer ChangeKit final build is not byte deterministic")
        if args.mode in {"build", "build-runtime-only"}:
            _write_outputs(ROOT, outputs)
        elif args.mode == "check":
            _check_outputs(ROOT, outputs)
        mgba_outputs: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba_outputs = _mgba_outputs(ROOT, outputs)
            if args.mode in {"build", "mgba"}:
                _write_outputs(ROOT, mgba_outputs)
            else:
                _check_outputs(ROOT, mgba_outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, FinalBuildError) as error:
        print(f"Trainer ChangeKit final build failed: {error}", file=sys.stderr)
        return 1
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    print(
        "Trainer ChangeKit final %s: PASS stage=%s encounters=%d members=%d artifacts=%d"
        % (args.mode, metadata["output"]["sha256"], ENCOUNTER_COUNT, MEMBER_COUNT,
           len(outputs) + len(mgba_outputs))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
