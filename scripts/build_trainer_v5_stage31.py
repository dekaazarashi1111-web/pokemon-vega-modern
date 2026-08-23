#!/usr/bin/env python3
"""Trainer Redesign V5の先行25戦をStage 31実ROMへ接続する。"""

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
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release import bps as bps_codec  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402

TASK = "USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/31_factory_shiny_memorial_runtime.gba")
INPUT_META = Path("build/stages/31_factory_shiny_memorial_runtime.json")
INPUT_ALLOC = Path("build/stages/31_allocation.json")
STAGE17_META = Path("build/stages/17_regression.json")
STAGE07_META = Path("build/stages/07_species.json")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
OUTPUT_ROM = Path("build/stages/32_trainer_v5_foundation.gba")
OUTPUT_META = Path("build/stages/32_trainer_v5_foundation.json")
OUTPUT_ALLOC = Path("build/stages/32_allocation.json")
RUNTIME_BIN = Path("generated/runtime/trainer_v5_stage31_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/trainer_v5_stage31_runtime_symbols.json")
GENERATED_HEADER = Path("generated/runtime/trainer_v5_stage31_generated.h")
SERIALIZED_JSON = Path("generated/runtime/trainer_v5_stage31_serialized.json")
BINDING_REPORT = Path("reports/generated/trainer_v5_stage31_bindings.csv")
MGBA_FIXTURE = Path("build/stages/32_mgba_trainer_v5_foundation.json")
REPORT = Path("reports/generated/trainer_v5_stage31.md")
PATCH_INCREMENTAL = Path("build/patches/factory-shiny-memorial-stage31-to-trainer-v5-stage32.bps")
PATCH_CUMULATIVE = Path("build/patches/vega-modern-kanto-v1.4.0-to-trainer-v5-stage32.bps")
RUNNER = Path("tools/mgba_trainer_v5_stage31_smoke.c")
SOURCE_DIR = Path("content/trainer_v5_stage31")

EXPECTED_INPUT_SHA256 = "46b668346def44c9fe9bc11590f961db3133543342165052c91fcaab92e70d5f"
EXPECTED_BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"
PAYLOAD_HEADER_SIZE = 0x100
TRAMPOLINE_SIZE = 0x10
TRAMPOLINE_NAMES = ("get_rematch", "build_trainer_party")
HOOK_NAMES = (
    "configure_trainer_battle",
    "script_flag_get", "script_flag_set", "script_flag_set_alt",
    "has_trainer_fought", "set_trainer_flag", "clear_trainer_flag",
    "get_rematch", "build_trainer_party",
)
CODE_RELATIVE_OFFSET = PAYLOAD_HEADER_SIZE + TRAMPOLINE_SIZE * len(TRAMPOLINE_NAMES)
ALLOCATION_NAME = "trainer_v5_stage31_foundation_payload"
TRAINER_TABLE_COUNT = 1367
TRAINER_RECORD_SIZE = 32
PARTY_MEMBER_SIZE = 16
OLD_TRAINER_TABLE_COUNT = 917
SIDECAR_SIZE = 16
FLAG_START = 0x500
FORBIDDEN_GBA_START = 0x092DBEF4
FORBIDDEN_GBA_END = 0x092DD0E4

HOOKS = {
    "configure_trainer_battle": {"address": 0x0807F948, "expected": bytes.fromhex("00490847d9e01109"), "entry": "TrainerV5Runtime_ConfigureTrainerBattle"},
    "script_flag_get": {"address": 0x0807FB04, "expected": bytes.fromhex("00b5fff767fe0004"), "entry": "TrainerV5Runtime_ScriptFlagGet"},
    "script_flag_set": {"address": 0x0807FB1C, "expected": bytes.fromhex("00b5fff75bfe0004"), "entry": "TrainerV5Runtime_ScriptFlagSet"},
    "script_flag_set_alt": {"address": 0x0807FB30, "expected": bytes.fromhex("00b5fff751fe0004"), "entry": "TrainerV5Runtime_ScriptFlagSet"},
    "has_trainer_fought": {"address": 0x0807FB44, "expected": bytes.fromhex("00b50004a021c904"), "entry": "TrainerV5Runtime_HasTrainerBeenFought"},
    "set_trainer_flag": {"address": 0x0807FB5C, "expected": bytes.fromhex("00b50004a021c904"), "entry": "TrainerV5Runtime_SetTrainerFlag"},
    "clear_trainer_flag": {"address": 0x0807FB70, "expected": bytes.fromhex("00b50004a021c904"), "entry": "TrainerV5Runtime_ClearTrainerFlag"},
    "get_rematch": {"address": 0x0810D93C, "expected": bytes.fromhex("30b581b0011c0904"), "entry": "TrainerV5Runtime_GetRematchTrainerId"},
    "build_trainer_party": {"address": 0x090DD2A4, "expected": bytes.fromhex("f0b5de464e464546"), "entry": "TrainerV5Runtime_BuildTrainerPartySetup"},
}
CONFIGURE_TRAINER_BATTLE_ADDRESS = 0x0911E0D9
GET_TRAINER_FLAG_ADDRESS = 0x0807F7D9
FLAG_SET_ADDRESS = 0x0806DE75
FLAG_CLEAR_ADDRESS = 0x0806DE9D
FLAG_GET_ADDRESS = 0x0806DEC5
CALCULATE_MON_STATS_ADDRESS = 0x090D939D
ENEMY_PARTY_ADDRESS = 0x02023F8C
TRAINER_OPPONENT_A_ADDRESS = 0x020385E2
REQUIRED_ENTRYPOINTS = {
    "TrainerV5Runtime_Probe",
    "TrainerV5Runtime_ScriptFlagGet",
    "TrainerV5Runtime_ScriptFlagSet",
    "TrainerV5Runtime_HasTrainerBeenFought",
    "TrainerV5Runtime_SetTrainerFlag",
    "TrainerV5Runtime_ClearTrainerFlag",
    "TrainerV5Runtime_ConfigureTrainerBattle",
    "TrainerV5Runtime_GetRematchTrainerId",
    "TrainerV5Runtime_BuildTrainerPartySetup",
    "TrainerV5Runtime_SidecarTable",
    "TrainerV5Runtime_RematchTable",
    "TrainerV5Runtime_FlagTable",
}
AI_FLAGS = {"AI_BASIC": 1, "AI_SEMI_SMART": 3, "AI_FULL_SMART": 5}
SINGLE_KINDS = {0, 5, 9}
DOUBLE_KINDS = {4, 7}
MULTI_KINDS: set[int] = set()


class TrainerV5BuildError(ValueError):
    """V5正本、Stage 31 ABI、配置、または受入契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise TrainerV5BuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> bytes:
    if not rows:
        return b""
    names = list(fieldnames or rows[0].keys())
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in names})
    return stream.getvalue().encode("utf-8")


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(list(command), cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-6000:]}")
    return completed.stdout.strip()


def _arm_tool(root: Path, name: str) -> str:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    for candidate in (
        root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/arm-toolchain/bin" / name,
        root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/arm-toolchain/bin-real" / name,
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    _fail(f"required ARM tool is missing: {name}")


def _host_cc(root: Path) -> str:
    kit = root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/host-toolchain/bin/cc"
    if kit.is_file() and os.access(kit, os.X_OK):
        return str(kit)
    configured = os.environ.get("CC")
    if configured:
        resolved = shutil.which(configured)
        if resolved:
            return resolved
    resolved = shutil.which("cc")
    if resolved:
        return resolved
    _fail("host C compiler is missing")


def _rom_offset(address: int, size: int, label: str) -> int:
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"{label}: ROM address outside image: 0x{address:08X}+{size}")
    return offset


def _u16(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 2 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _sparse_bps(source: bytes, target: bytes) -> bytes:
    if len(source) != len(target):
        _fail("sparse BPS requires equal-size source and target")
    spans: list[tuple[int, int]] = []
    for block_start in range(0, len(target), 0x1000):
        block_end = min(block_start + 0x1000, len(target))
        left, right = source[block_start:block_end], target[block_start:block_end]
        if left == right:
            continue
        index = 0
        while index < len(right):
            while index < len(right) and left[index] == right[index]:
                index += 1
            if index == len(right):
                break
            start = block_start + index
            while index < len(right) and left[index] != right[index]:
                index += 1
            end = block_start + index
            if spans and start - spans[-1][1] < 4:
                spans[-1] = (spans[-1][0], end)
            else:
                spans.append((start, end))
    patch = bytearray(bps_codec.MAGIC)
    patch.extend(bps_codec._encode_number(len(source)))
    patch.extend(bps_codec._encode_number(len(target)))
    patch.extend(bps_codec._encode_number(0))
    cursor = 0
    for start, end in spans:
        if start > cursor:
            patch.extend(bps_codec._action(bps_codec.SOURCE_READ, start - cursor))
        patch.extend(bps_codec._action(bps_codec.TARGET_READ, end - start))
        patch.extend(target[start:end])
        cursor = end
    if cursor < len(target):
        patch.extend(bps_codec._action(bps_codec.SOURCE_READ, len(target) - cursor))
    patch.extend(bps_codec._crc32(source).to_bytes(4, "little"))
    patch.extend(bps_codec._crc32(target).to_bytes(4, "little"))
    patch.extend(bps_codec._crc32(patch).to_bytes(4, "little"))
    encoded = bytes(patch)
    if apply_bps(source, encoded) != target:
        _fail("sparse BPS round-trip differs")
    return encoded


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, object]]:
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"], "owner": row["owner"],
        "purpose": row["purpose"], "content_sha256": row["content_sha256"],
    } for row in allocation["allocations"]]


def _input_contract(root: Path) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage = (root / INPUT_ROM).read_bytes()
    base = (root / BASE_ROM).read_bytes()
    input_meta = _read_json(root / INPUT_META)
    previous_alloc = _read_json(root / INPUT_ALLOC)
    trainer_meta = _read_json(root / STAGE17_META)
    species_meta = _read_json(root / STAGE07_META)
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_INPUT_SHA256:
        _fail("Stage 31 input size or hash differs")
    if len(base) != ROM_SIZE or _sha(base) != EXPECTED_BASE_SHA256:
        _fail("v1.4.0 base size or hash differs")
    if input_meta.get("output", {}).get("sha256") != EXPECTED_INPUT_SHA256:
        _fail("Stage 31 metadata output hash differs")
    if previous_alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage 31 allocator overlap contract failed")
    trainer = trainer_meta.get("trainers", {})
    if (trainer.get("record_size") != TRAINER_RECORD_SIZE
            or trainer.get("expanded_count") != OLD_TRAINER_TABLE_COUNT
            or trainer.get("repoint_count") != 24):
        _fail("Stage 17 trainer ABI metadata differs")
    base_stats = species_meta.get("base_stats", {})
    if base_stats.get("count") != 1621 or base_stats.get("stride") != 32:
        _fail("Stage 07 base stats ABI differs")
    return stage, base, input_meta, previous_alloc, trainer_meta, species_meta


def _index(rows: Sequence[Mapping[str, str]], key: str, label: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            _fail(f"{label}: missing or duplicate {key}: {value!r}")
        result[value] = row
    return result


def validate_format_contracts(
    bindings: Sequence[Mapping[str, str]],
    parties: Sequence[Mapping[str, str]],
    members: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """SINGLE/DOUBLE/MULTIの別契約とhardcoded kind整合を検証する。"""
    party_by_key = _index(parties, "party_key", "parties")
    members_by_party: dict[str, list[Mapping[str, str]]] = {}
    for row in members:
        members_by_party.setdefault(row.get("party_key", ""), []).append(row)
    counts: Counter[str] = Counter()
    for binding in bindings:
        key = binding.get("party_key", "")
        if key not in party_by_key:
            _fail(f"binding party missing: {key}")
        party = party_by_key[key]
        binding_format = binding.get("battle_format", "")
        party_format = party.get("battle_format", "")
        if binding_format != party_format:
            _fail(f"{key}: binding/party battle format mismatch ({binding_format}/{party_format})")
        kind = int(binding.get("trainerbattle_kind", "-1"), 0)
        size = int(party.get("party_size", "0"), 0)
        slots = sorted(int(row.get("slot", "0"), 0) for row in members_by_party.get(key, []))
        if slots != list(range(1, size + 1)):
            _fail(f"{key}: party slots differ: {slots}")
        if binding_format == "SINGLE":
            if kind not in SINGLE_KINDS:
                _fail(f"{key}: SINGLE party rejected for trainerbattle kind {kind}")
            if not 1 <= size <= 6:
                _fail(f"{key}: SINGLE party size outside 1..6")
        elif binding_format == "DOUBLE":
            if kind not in DOUBLE_KINDS:
                _fail(f"{key}: DOUBLE party rejected for trainerbattle kind {kind}")
            if not 2 <= size <= 6:
                _fail(f"{key}: DOUBLE party size outside 2..6")
        elif binding_format == "MULTI":
            if kind not in MULTI_KINDS:
                _fail(f"{key}: MULTI party has no supported hardcoded kind")
            if binding.get("pair_or_partner_key", "NONE") in ("", "NONE"):
                _fail(f"{key}: MULTI party lacks partner binding")
        else:
            _fail(f"{key}: unsupported battle format {binding_format!r}")
        if int(binding.get("party_size", "0"), 0) != size:
            _fail(f"{key}: binding party_size differs")
        counts[binding_format] += 1
    return {
        "status": "PASS", "single": counts["SINGLE"], "double": counts["DOUBLE"],
        "multi": counts["MULTI"], "hardcoded_double_rejects_single": True,
    }


def load_and_validate_source(root: Path = ROOT, stage: bytes | None = None) -> dict[str, Any]:
    root = Path(root)
    source = root / SOURCE_DIR
    manifest = _read_json(source / "source_manifest.json")
    if manifest.get("task") != TASK or manifest.get("schema_version") != 1:
        _fail("Trainer V5 source manifest task/schema differs")
    for relative, expected in manifest.get("files", {}).items():
        raw = (source / relative).read_bytes()
        if len(raw) != int(expected["size"]) or _sha(raw) != expected["sha256"]:
            _fail(f"Trainer V5 source file identity differs: {relative}")
    for archive in manifest.get("source_archives", {}).values():
        path = root.parent / archive["package_path"]
        raw = path.read_bytes()
        if len(raw) != int(archive["size"]) or _sha(raw) != archive["sha256"]:
            _fail(f"bundled reference archive identity differs: {archive['package_path']}")

    encounters = _rows(source / "trainer_encounters_v5.csv")
    parties = _rows(source / "trainer_parties_v5.csv")
    members = _rows(source / "trainer_party_members_v5.csv")
    bindings = _rows(source / "trainer_stage31_bindings.csv")
    if (len(encounters), len(parties), len(members), len(bindings)) != (25, 25, 71, 25):
        _fail("selected V5 source counts differ from 25/25/71/25")
    encounter_by_key = _index(encounters, "encounter_key", "encounters")
    party_by_key = _index(parties, "party_key", "parties")
    binding_by_key = _index(bindings, "encounter_key", "bindings")
    if set(encounter_by_key) != set(binding_by_key):
        _fail("encounter/binding key sets differ")
    if {row["party_key"] for row in encounters} != set(party_by_key):
        _fail("encounter/party key sets differ")
    if len({row["adoption_reason"] for row in bindings}) != 25 or any(not row["adoption_reason"].strip() for row in bindings):
        _fail("individual adoption reasons are missing or reused")
    for binding in bindings:
        encounter = encounter_by_key[binding["encounter_key"]]
        party = party_by_key[binding["party_key"]]
        for field in ("trainer_id", "party_key", "ai_profile_key"):
            if binding[field] != encounter[field]:
                _fail(f"{binding['encounter_key']}: binding/encounter {field} differs")
        if party["encounter_key"] != binding["encounter_key"]:
            _fail(f"{binding['encounter_key']}: party encounter key differs")
        if party["shared_party_policy"] != "UNIQUE_INSTANCE":
            _fail(f"{binding['party_key']}: shared party policy is not UNIQUE_INSTANCE")
    format_audit = validate_format_contracts(bindings, parties, members)

    schema = _read_json(source / "trainer_v5_stage31.schema.json")
    x_contract = schema.get("x-stage31-contract", {})
    if (x_contract.get("single_kinds") != [0, 5, 9]
            or x_contract.get("double_kinds") != [4, 7]
            or not x_contract.get("hardcoded_double_must_not_accept_single")
            or x_contract.get("party_member_size") != PARTY_MEMBER_SIZE
            or x_contract.get("trainer_record_size") != TRAINER_RECORD_SIZE):
        _fail("Trainer V5 Stage31 schema contract differs")

    runtime_registries: dict[str, dict[str, int]] = {}
    id_rebindings: list[dict[str, Any]] = []
    for domain, key, subset_name, live_name in (
        ("species", "species_key", "species_ids.csv", "manifests/species_ids.csv"),
        ("ability", "ability_key", "ability_ids.csv", "manifests/ability_ids.csv"),
        ("move", "move_key", "move_ids.csv", "manifests/move_ids.csv"),
        ("item", "item_key", "item_ids.csv", "manifests/item_ids.csv"),
    ):
        subset = _index(_rows(source / subset_name), key, f"V5 {domain} registry")
        live = _index(_rows(root / live_name), key, f"Stage31 {domain} registry")
        runtime: dict[str, int] = {}
        for name, original in subset.items():
            if name not in live:
                _fail(f"V5 {domain} key missing from Stage31 registry: {name}")
            source_id = int(original["id"], 0)
            runtime_id = int(live[name]["id"], 0)
            runtime[name] = runtime_id
            if source_id != runtime_id:
                id_rebindings.append({
                    "domain": domain, "key": name, "v5_id": source_id,
                    "stage31_id": runtime_id, "reason": "key-based canonical Stage31 resolution",
                })
        runtime_registries[domain] = runtime
    nature_rows = _index(_rows(source / "nature_ids.csv"), "nature_key", "nature registry")
    runtime_registries["nature"] = {key: int(row["id"], 0) for key, row in nature_rows.items()}
    ai_rows = _index(_rows(source / "trainer_ai_profiles.csv"), "ai_profile_key", "AI profiles")
    if set(ai_rows) != {"AI_BASIC", "AI_SEMI_SMART"}:
        _fail("selected AI profile set differs")

    if stage is not None:
        for binding in bindings:
            instruction = int(binding["script_instruction_address"], 0)
            offset = _rom_offset(instruction, 4, binding["encounter_key"])
            expected_kind = int(binding["trainerbattle_kind"], 0)
            expected_source = int(binding["source_trainer_id"], 0)
            if stage[offset] != 0x5C or stage[offset + 1] != expected_kind or _u16(stage, offset + 2, "trainerbattle source") != expected_source:
                _fail(f"{binding['encounter_key']}: exact Stage31 trainerbattle bytes differ")

    return {
        "manifest": manifest, "schema": schema, "encounters": encounters,
        "parties": parties, "members": members, "bindings": bindings,
        "encounter_by_key": encounter_by_key, "party_by_key": party_by_key,
        "binding_by_key": binding_by_key, "runtime_registries": runtime_registries,
        "id_rebindings": id_rebindings, "format_audit": format_audit,
    }


def _resolve_ability_mode(stage: bytes, species_meta: Mapping[str, Any], species_id: int, ability_id: int) -> int:
    base = int(species_meta["base_stats"]["address"]) - GBA_ROM_BASE
    stride = int(species_meta["base_stats"]["stride"])
    offset = base + species_id * stride
    abilities = (
        _u16(stage, offset + 0x16, "ability1"),
        _u16(stage, offset + 0x1A, "ability2"),
        _u16(stage, offset + 0x1C, "hidden ability"),
    )
    matches = [index for index, value in enumerate(abilities) if value == ability_id and value != 0]
    if not matches:
        _fail(f"species {species_id}: requested ability {ability_id} absent from Stage31 base stats {abilities}")
    return matches[0]


def _serialize_catalog(source: Mapping[str, Any], stage: bytes, species_meta: Mapping[str, Any]) -> dict[str, Any]:
    registries = source["runtime_registries"]
    party_by_key = source["party_by_key"]
    members_by_party: dict[str, list[Mapping[str, str]]] = {}
    for row in source["members"]:
        members_by_party.setdefault(row["party_key"], []).append(row)
    sidecars: list[dict[str, int]] = []
    party_rows: list[dict[str, Any]] = []
    party_bytes_by_key: dict[str, bytes] = {}
    binding_by_key = source["binding_by_key"]
    for party_key in sorted(party_by_key, key=lambda key: int(binding_by_key[party_by_key[key]["encounter_key"]]["trainer_id"], 0)):
        party = party_by_key[party_key]
        binding = binding_by_key[party["encounter_key"]]
        trainer_id = int(binding["trainer_id"], 0)
        raw = bytearray()
        serialized_members: list[dict[str, Any]] = []
        for member in sorted(members_by_party[party_key], key=lambda row: int(row["slot"], 0)):
            species_id = registries["species"][member["species_key"]]
            ability_id = registries["ability"][member["ability_key"]]
            nature_id = registries["nature"][member["nature_key"]]
            ability_mode = _resolve_ability_mode(stage, species_meta, species_id, ability_id)
            item_id = registries["item"][member["held_item_key"]]
            move_ids = [registries["move"][member[f"move{index}_key"]] for index in range(1, 5)]
            level = int(member["level"], 0)
            iv = int(member["iv_floor"], 0)
            evs = {name: int(member[name], 0) for name in ("hp_ev", "atk_ev", "def_ev", "spa_ev", "spd_ev", "spe_ev")}
            if not 1 <= level <= 100 or not 0 <= iv <= 31 or any(not 0 <= value <= 255 for value in evs.values()):
                _fail(f"{party_key} slot {member['slot']}: level/IV/EV outside ABI")
            # CFRU's legacy field is kept zero. Exact IV is applied by live sidecar.
            raw.extend(struct.pack("<8H", 0, level, species_id, item_id, *move_ids))
            sidecar = {
                "trainer_id": trainer_id, "species_id": species_id, "side": 1,
                "slot": int(member["slot"], 0) - 1, "nature_id": nature_id,
                "ability_mode": ability_mode, "iv": iv,
                "hp_ev": evs["hp_ev"], "atk_ev": evs["atk_ev"], "def_ev": evs["def_ev"],
                "spe_ev": evs["spe_ev"], "spa_ev": evs["spa_ev"], "spd_ev": evs["spd_ev"],
                "reserved": 0, "ability_id": ability_id,
            }
            sidecars.append(sidecar)
            serialized_members.append({
                **sidecar, "source_slot": int(member["slot"], 0),
                "species_key": member["species_key"], "ability_key": member["ability_key"],
                "nature_key": member["nature_key"], "item_id": item_id,
                "move_ids": move_ids, "level": level,
            })
        party_raw = bytes(raw)
        party_bytes_by_key[party_key] = party_raw
        party_rows.append({
            "party_key": party_key, "encounter_key": party["encounter_key"],
            "trainer_id": trainer_id, "battle_format": party["battle_format"],
            "party_size": int(party["party_size"], 0), "ai_profile_key": party["ai_profile_key"],
            "party_sha256": _sha(party_raw), "members": serialized_members,
        })
    sidecars.sort(key=lambda row: (row["trainer_id"], row["side"], row["slot"]))
    if len(sidecars) != 71:
        _fail("serialized sidecar count differs")
    rematch_map = sorted({
        (int(row["source_trainer_id"], 0), int(row["trainer_id"], 0))
        for row in source["bindings"]
        if row["runtime_id_resolution"] == "REMATCH_HOOK_SOURCE_TO_V5_ID"
    } | {(702, 702)})
    flag_map = sorted({
        (FLAG_START + int(row["trainer_id"], 0), FLAG_START + int(row["defeat_flag_owner_trainer_id"], 0))
        for row in source["bindings"]
        if int(row["trainer_id"], 0) != int(row["defeat_flag_owner_trainer_id"], 0)
    })
    return {
        "sidecars": sidecars, "rematch_map": rematch_map, "flag_map": flag_map,
        "party_rows": party_rows, "party_bytes_by_key": party_bytes_by_key,
    }


def _generated_header(serialized: Mapping[str, Any]) -> bytes:
    sidecar_lines = []
    for row in serialized["sidecars"]:
        sidecar_lines.append(
            "    {%du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du}," % (
                row["trainer_id"], row["species_id"], row["side"], row["slot"],
                row["nature_id"], row["ability_mode"], row["iv"], row["hp_ev"],
                row["atk_ev"], row["def_ev"], row["spe_ev"], row["spa_ev"],
                row["spd_ev"], row["reserved"],
            )
        )
    rematch_lines = [f"    {{{source}u, {target}u}}," for source, target in serialized["rematch_map"]]
    flag_lines = [f"    {{{external}u, {physical}u}}," for external, physical in serialized["flag_map"]]
    text = f"""#ifndef VEGA_TRAINER_V5_STAGE31_GENERATED_H
#define VEGA_TRAINER_V5_STAGE31_GENERATED_H

#include <stdint.h>

#define TRAINER_V5_ABILITY_PRIMARY 0u
#define TRAINER_V5_ABILITY_SECONDARY 1u
#define TRAINER_V5_ABILITY_HIDDEN 2u
#define TRAINER_V5_GENERATED_ENCOUNTER_COUNT 25u
#define TRAINER_V5_GENERATED_SIDECAR_COUNT {len(serialized['sidecars'])}u
#define TRAINER_V5_GENERATED_REMATCH_MAP_COUNT {len(serialized['rematch_map'])}u
#define TRAINER_V5_GENERATED_FLAG_MAP_COUNT {len(serialized['flag_map'])}u
#define TRAINER_V5_GENERATED_TRAINER_TABLE_COUNT {TRAINER_TABLE_COUNT}u

struct __attribute__((packed)) TrainerV5MemberSidecarV1 {{
    uint16_t trainer_id;
    uint16_t species_id;
    uint8_t side;
    uint8_t slot;
    uint8_t nature_id;
    uint8_t ability_mode;
    uint8_t iv;
    uint8_t hp_ev;
    uint8_t atk_ev;
    uint8_t def_ev;
    uint8_t speed_ev;
    uint8_t sp_atk_ev;
    uint8_t sp_def_ev;
    uint8_t reserved;
}};
struct __attribute__((packed)) TrainerV5RematchMapV1 {{ uint16_t source_trainer_id; uint16_t v5_trainer_id; }};
struct __attribute__((packed)) TrainerV5FlagMapV1 {{ uint16_t external_flag; uint16_t physical_flag; }};

static const struct TrainerV5MemberSidecarV1 gTrainerV5MemberSidecars[TRAINER_V5_GENERATED_SIDECAR_COUNT] = {{
{chr(10).join(sidecar_lines)}
}};
static const struct TrainerV5RematchMapV1 gTrainerV5RematchMap[TRAINER_V5_GENERATED_REMATCH_MAP_COUNT] = {{
{chr(10).join(rematch_lines)}
}};
static const struct TrainerV5FlagMapV1 gTrainerV5FlagMap[TRAINER_V5_GENERATED_FLAG_MAP_COUNT] = {{
{chr(10).join(flag_lines)}
}};

#endif
"""
    return text.encode("ascii")


def _compile_runtime(
    root: Path, load_address: int, header: bytes, trampoline_addresses: Mapping[str, int],
) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(root, "arm-none-eabi-gcc")
    objcopy = _arm_tool(root, "arm-none-eabi-objcopy")
    nm = _arm_tool(root, "arm-none-eabi-nm")
    source = root / "overlays/trainer_v5_stage31_runtime/trainer_v5_stage31_runtime.c"
    if not source.is_file():
        _fail(f"Trainer V5 runtime source missing: {source}")
    with tempfile.TemporaryDirectory(prefix="vega-trainer-v5-runtime-") as temporary:
        directory = Path(temporary)
        (directory / "trainer_v5_stage31_generated.h").write_bytes(header)
        obj = directory / "runtime.o"
        macros = {
            "VEGA_GET_TRAINER_FLAG_ADDRESS": GET_TRAINER_FLAG_ADDRESS,
            "VEGA_FLAG_SET_ADDRESS": FLAG_SET_ADDRESS,
            "VEGA_FLAG_CLEAR_ADDRESS": FLAG_CLEAR_ADDRESS,
            "VEGA_FLAG_GET_ADDRESS": FLAG_GET_ADDRESS,
            "VEGA_GET_REMATCH_TRAMPOLINE_ADDRESS": trampoline_addresses["get_rematch"] | 1,
            "VEGA_BUILD_TRAINER_PARTY_TRAMPOLINE_ADDRESS": trampoline_addresses["build_trainer_party"] | 1,
            "VEGA_CONFIGURE_TRAINER_BATTLE_ADDRESS": CONFIGURE_TRAINER_BATTLE_ADDRESS,
            "VEGA_CALCULATE_MON_STATS_ADDRESS": CALCULATE_MON_STATS_ADDRESS,
            "VEGA_ENEMY_PARTY_ADDRESS": ENEMY_PARTY_ADDRESS,
            "VEGA_TRAINER_OPPONENT_A_ADDRESS": TRAINER_OPPONENT_A_ADDRESS,
        }
        command = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", f"-I{directory}", f"-I{root}",
        ] + [f"-D{name}=0x{value:08X}u" for name, value in macros.items()]
        _run([*command, "-c", str(source), "-o", str(obj)], "compile Trainer V5 runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.TrainerV5Runtime_*)) *(.text*) *(.rodata*) *(.data*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "runtime.elf"
        binary = directory / "runtime.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections", "-Wl,-e,TrainerV5Runtime_Probe",
            f"-Wl,-T,{linker}", str(obj), "-lgcc", "-o", str(elf),
        ], "link Trainer V5 runtime")
        undefined = _run([nm, "-u", str(elf)], "Trainer V5 undefined-symbol audit")
        if undefined:
            _fail("Trainer V5 runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Trainer V5 objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Trainer V5 nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing:
            _fail(f"Trainer V5 linked exports missing: {missing}")
        code = binary.read_bytes()
        if not code or len(code) > 64 * 1024:
            _fail(f"unexpected Trainer V5 runtime size: {len(code)}")
        for name in REQUIRED_ENTRYPOINTS:
            if not load_address <= symbols[name] < load_address + len(code):
                _fail(f"Trainer V5 symbol outside linked image: {name}")
        return code, symbols


def _jump_stub(target_thumb: int) -> bytes:
    return struct.pack("<HHI", 0x4B00, 0x4718, target_thumb)


def _trampoline(original: bytes, return_thumb: int) -> bytes:
    if len(original) != 8:
        _fail("trampoline prologue must be 8 bytes")
    return original + _jump_stub(return_thumb)


def _allocation(root: Path, previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules", "size": size,
        "alignment": 16, "owner": TASK,
        "purpose": "Trainer V5 25 encounters, expanded trainer table, sidecar runtime, save-compatible hooks",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage32 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Trainer V5 allocation is not unique")
    return matches[0], report


def _layout_for_code(code_size: int) -> dict[str, int]:
    table_relative = _align(CODE_RELATIVE_OFFSET + code_size, 16)
    party_relative = _align(table_relative + TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE, 4)
    return {
        "code_relative": CODE_RELATIVE_OFFSET,
        "table_relative": table_relative,
        "party_relative": party_relative,
    }


def _party_blob(serialized: Mapping[str, Any], party_base_address: int) -> tuple[bytes, dict[str, int]]:
    blob = bytearray()
    pointers: dict[str, int] = {}
    for row in serialized["party_rows"]:
        while len(blob) & 3:
            blob.append(0)
        key = row["party_key"]
        pointers[key] = party_base_address + len(blob)
        blob.extend(serialized["party_bytes_by_key"][key])
    return bytes(blob), pointers


def _trainer_table(
    stage: bytes, trainer_meta: Mapping[str, Any], source: Mapping[str, Any], party_pointers: Mapping[str, int],
) -> tuple[bytes, list[dict[str, Any]]]:
    trainer = trainer_meta["trainers"]
    old_address = int(trainer["address"])
    old_offset = _rom_offset(old_address, OLD_TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE, "old trainer table")
    table = bytearray(TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE)
    table[:OLD_TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE] = stage[
        old_offset:old_offset + OLD_TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE
    ]
    audit_rows: list[dict[str, Any]] = []
    for binding in sorted(source["bindings"], key=lambda row: int(row["trainer_id"], 0)):
        target = int(binding["trainer_id"], 0)
        physical = int(binding["source_trainer_id"], 0)
        if target >= TRAINER_TABLE_COUNT or physical >= OLD_TRAINER_TABLE_COUNT:
            _fail(f"trainer record outside source/target table: {target}/{physical}")
        source_record = stage[
            old_offset + physical * TRAINER_RECORD_SIZE:
            old_offset + (physical + 1) * TRAINER_RECORD_SIZE
        ]
        record = bytearray(source_record)
        record[0] = 3
        record[0x0A:0x12] = b"\0" * 8
        record[0x12] = 1 if binding["battle_format"] == "DOUBLE" else 0
        ai_flags = AI_FLAGS[binding["ai_profile_key"]]
        struct.pack_into("<I", record, 0x14, ai_flags)
        record[0x18] = int(binding["party_size"], 0)
        pointer = party_pointers[binding["party_key"]]
        struct.pack_into("<I", record, 0x1C, pointer)
        start = target * TRAINER_RECORD_SIZE
        table[start:start + TRAINER_RECORD_SIZE] = record
        audit_rows.append({
            **binding, "trainer_id": target, "source_trainer_id": physical,
            "ai_flags": ai_flags, "party_pointer": pointer,
            "record_sha256": _sha(record), "source_record_sha256": _sha(source_record),
        })
    return bytes(table), audit_rows


def _build_payload(
    root: Path, stage: bytes, trainer_meta: Mapping[str, Any], source: Mapping[str, Any],
    serialized: Mapping[str, Any], header: bytes, payload_offset: int,
) -> tuple[bytes, dict[str, Any], list[dict[str, Any]], bytes]:
    payload_address = GBA_ROM_BASE + payload_offset
    tramp_addresses = {
        name: payload_address + PAYLOAD_HEADER_SIZE + index * TRAMPOLINE_SIZE
        for index, name in enumerate(TRAMPOLINE_NAMES)
    }
    code_address = payload_address + CODE_RELATIVE_OFFSET
    code, symbols = _compile_runtime(root, code_address, header, tramp_addresses)
    layout = _layout_for_code(len(code))
    party_base = payload_address + layout["party_relative"]
    party_blob, party_pointers = _party_blob(serialized, party_base)
    table, audit_rows = _trainer_table(stage, trainer_meta, source, party_pointers)
    payload_size = layout["party_relative"] + len(party_blob)
    payload = bytearray(payload_size)
    for index, name in enumerate(TRAMPOLINE_NAMES):
        hook = HOOKS[name]
        start = PAYLOAD_HEADER_SIZE + index * TRAMPOLINE_SIZE
        payload[start:start + TRAMPOLINE_SIZE] = _trampoline(hook["expected"], hook["address"] + 8 | 1)
    payload[layout["code_relative"]:layout["code_relative"] + len(code)] = code
    payload[layout["table_relative"]:layout["table_relative"] + len(table)] = table
    payload[layout["party_relative"]:layout["party_relative"] + len(party_blob)] = party_blob
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    struct.pack_into(
        "<8sIIIIIIIIIIIIIIII",
        payload, 0, b"VEGATV32", 2, len(payload), len(code), TRAINER_TABLE_COUNT,
        len(source["bindings"]), len(serialized["sidecars"]), len(serialized["rematch_map"]),
        len(serialized["flag_map"]), payload_address + layout["table_relative"],
        party_base, entrypoints["TrainerV5Runtime_Probe"],
        entrypoints["TrainerV5Runtime_ScriptFlagGet"],
        entrypoints["TrainerV5Runtime_ScriptFlagSet"],
        entrypoints["TrainerV5Runtime_HasTrainerBeenFought"],
        entrypoints["TrainerV5Runtime_GetRematchTrainerId"],
        entrypoints["TrainerV5Runtime_BuildTrainerPartySetup"],
    )
    runtime = {
        "payload": {
            "magic": "VEGATV32", "offset": payload_offset, "address": payload_address,
            "size": len(payload), "sha256": _sha(payload), "header_size": PAYLOAD_HEADER_SIZE,
            "code_offset": payload_offset + layout["code_relative"], "code_address": code_address,
            "code_size": len(code), "code_sha256": _sha(code),
            "trainer_table_offset": payload_offset + layout["table_relative"],
            "trainer_table_address": payload_address + layout["table_relative"],
            "trainer_table_size": len(table), "party_blob_offset": payload_offset + layout["party_relative"],
            "party_blob_address": party_base, "party_blob_size": len(party_blob),
        },
        "trampolines": {name: tramp_addresses[name] | 1 for name in TRAMPOLINE_NAMES},
        "entrypoints": entrypoints,
        "symbols": {name: address for name, address in sorted(symbols.items()) if code_address <= address < code_address + len(code)},
    }
    return bytes(payload), runtime, audit_rows, code


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage, base, input_meta, previous_alloc, trainer_meta, species_meta = _input_contract(root)
    source = load_and_validate_source(root, stage)
    serialized = _serialize_catalog(source, stage, species_meta)
    header = _generated_header(serialized)

    # Link once at a harmless provisional address to obtain an address-independent size.
    provisional_tramps = {name: GBA_ROM_BASE + PAYLOAD_HEADER_SIZE + index * TRAMPOLINE_SIZE for index, name in enumerate(TRAMPOLINE_NAMES)}
    provisional_code, _ = _compile_runtime(root, GBA_ROM_BASE + CODE_RELATIVE_OFFSET, header, provisional_tramps)
    provisional_layout = _layout_for_code(len(provisional_code))
    provisional_party_blob, _ = _party_blob(serialized, GBA_ROM_BASE + provisional_layout["party_relative"])
    provisional_size = provisional_layout["party_relative"] + len(provisional_party_blob)
    allocation, _ = _allocation(root, previous_alloc, provisional_size, "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime, binding_rows, code = _build_payload(
        root, stage, trainer_meta, source, serialized, header, payload_offset,
    )
    if len(code) != len(provisional_code) or len(payload) != provisional_size:
        _fail("address-dependent Trainer V5 payload size changed")
    allocation, allocation_report = _allocation(root, previous_alloc, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Trainer V5 allocation changed after final link")
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Trainer V5 payload destination is not erased FF")
    gba_start, gba_end = GBA_ROM_BASE + payload_offset, GBA_ROM_BASE + payload_end
    if not (gba_end <= FORBIDDEN_GBA_START or gba_start >= FORBIDDEN_GBA_END):
        _fail("Trainer V5 payload intersects forbidden P4B2c allocation")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{"start": payload_offset, "end_exclusive": payload_end, "kind": "payload"}]
    old_table = int(trainer_meta["trainers"]["address"])
    new_table = int(runtime["payload"]["trainer_table_address"])
    repoints: list[dict[str, Any]] = []
    for row in trainer_meta["trainers"]["repoints"]:
        site = int(row["site_offset"])
        expected_pointer = _u32(stage, site, row["label"])
        delta = expected_pointer - old_table
        if delta not in (0, 4, 10):
            _fail(f"trainer table repoint delta differs at 0x{site:X}: {delta}")
        replacement = new_table + delta
        struct.pack_into("<I", output, site, replacement)
        declared.append({"start": site, "end_exclusive": site + 4, "kind": "trainer_table_repoint"})
        repoints.append({
            "site_offset": site, "site_address": GBA_ROM_BASE + site,
            "field_offset": delta, "expected_pointer": expected_pointer,
            "replacement_pointer": replacement,
        })

    hook_rows: list[dict[str, Any]] = []
    for name in HOOK_NAMES:
        hook = HOOKS[name]
        site = _rom_offset(hook["address"], 8, name)
        if bytes(stage[site:site + 8]) != hook["expected"]:
            _fail(f"{name}: Stage31 hook prologue differs")
        target = runtime["entrypoints"][hook["entry"]]
        output[site:site + 8] = _jump_stub(target)
        declared.append({"start": site, "end_exclusive": site + 8, "kind": f"hook::{name}"})
        hook_rows.append({
            "name": name, "site_address": hook["address"], "site_offset": site,
            "expected_hex": hook["expected"].hex(), "replacement_hex": _jump_stub(target).hex(),
            "entrypoint": hook["entry"], "target": target,
            "trampoline": runtime["trampolines"].get(name),
        })

    initial_double_binding = next(row for row in source["bindings"] if row["runtime_id_resolution"] == "INITIAL_DOUBLE_SCRIPT_ID_PATCH")
    double_site = _rom_offset(int(initial_double_binding["script_instruction_address"], 0) + 2, 2, "initial double ID")
    if _u16(stage, double_site, "initial double source trainer") != int(initial_double_binding["source_trainer_id"], 0):
        _fail("initial double source ID differs")

    changed = [index for index, (before, after) in enumerate(zip(stage, output)) if before != after]
    outside = [index for index in changed if not any(row["start"] <= index < row["end_exclusive"] for row in declared)]
    if outside:
        _fail(f"Stage32 changed bytes outside declared spans: {outside[:16]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    cumulative = _sparse_bps(base, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(base, cumulative) != output_raw:
        _fail("Stage32 BPS round-trip differs")

    binding_report_rows: list[dict[str, Any]] = []
    party_doc = {row["party_key"]: row for row in serialized["party_rows"]}
    for row in binding_rows:
        party = party_doc[row["party_key"]]
        binding_report_rows.append({
            "encounter_key": row["encounter_key"], "reference_index": row["reference_index"],
            "trainer_id": row["trainer_id"], "source_trainer_id": row["source_trainer_id"],
            "group_id": row["group_id"], "map_id": row["map_id"], "root_kind": row["root_kind"],
            "root_index": row["root_index"], "local_id": row["local_id"], "x": row["x"], "y": row["y"],
            "script_instruction_address": row["script_instruction_address"],
            "trainerbattle_kind": row["trainerbattle_kind"], "battle_format": row["battle_format"],
            "party_key": row["party_key"], "party_size": row["party_size"],
            "party_pointer": f"0x{row['party_pointer']:08X}", "party_sha256": party["party_sha256"],
            "ai_profile_key": row["ai_profile_key"], "ai_flags": row["ai_flags"],
            "defeat_flag_owner_trainer_id": row["defeat_flag_owner_trainer_id"],
            "runtime_id_resolution": row["runtime_id_resolution"], "format_contract": row["format_contract"],
            "adoption_reason": row["adoption_reason"], "record_sha256": row["record_sha256"],
        })

    serialized_doc = {
        "schema_version": 2, "task": TASK, "status": "PASS",
        "selected_scope": {"encounter_count": 25, "party_count": 25, "member_count": 71},
        "battle_contracts": source["format_audit"],
        "member_sidecar_v1": {
            "record_size": SIDECAR_SIZE,
            "required_fields": ["trainer_id", "species_id", "side", "slot", "nature_id", "ability_mode", "iv", "hp_ev", "atk_ev", "def_ev", "spe_ev", "spa_ev", "spd_ev", "reserved"],
            "ev_source_order": ["hp_ev", "atk_ev", "def_ev", "spa_ev", "spd_ev", "spe_ev"],
            "ev_runtime_order": ["hp_ev", "atk_ev", "def_ev", "spe_ev", "spa_ev", "spd_ev"],
            "rows": serialized["sidecars"],
        },
        "rematch_map": [{"source_trainer_id": a, "v5_trainer_id": b} for a, b in serialized["rematch_map"]],
        "flag_map": [{"external_flag": a, "physical_flag": b} for a, b in serialized["flag_map"]],
        "parties": serialized["party_rows"],
        "id_rebindings": source["id_rebindings"],
    }

    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input": {"path": INPUT_ROM.as_posix(), "size": len(stage), "sha256": _sha(stage), "upstream_task": input_meta.get("task")},
        "base_release": {"path": BASE_ROM.as_posix(), "size": len(base), "sha256": _sha(base)},
        "output": {"path": OUTPUT_ROM.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        **runtime,
        "source": {
            "directory": SOURCE_DIR.as_posix(), "manifest_sha256": _sha((root / SOURCE_DIR / "source_manifest.json").read_bytes()),
            "encounter_count": 25, "party_count": 25, "member_count": 71,
            "reference_archives_verified": 4, "id_rebindings": source["id_rebindings"],
        },
        "serializer": {
            "trainer_record_size": TRAINER_RECORD_SIZE, "party_member_size": PARTY_MEMBER_SIZE,
            "sidecar_record_size": SIDECAR_SIZE, "trainer_table_count": TRAINER_TABLE_COUNT,
            "legacy_iv_field": 0, "live_sidecar_fields": ["ability", "nature", "iv", "hp_ev", "atk_ev", "def_ev", "spa_ev", "spd_ev", "spe_ev"],
            "serialized_path": SERIALIZED_JSON.as_posix(), "generated_header_path": GENERATED_HEADER.as_posix(),
        },
        "battle_contracts": source["format_audit"],
        "bindings": {"path": BINDING_REPORT.as_posix(), "count": len(binding_report_rows), "rows": binding_report_rows},
        "trainer_table": {
            "old_address": old_table, "old_count": OLD_TRAINER_TABLE_COUNT,
            "new_address": new_table, "new_count": TRAINER_TABLE_COUNT,
            "record_size": TRAINER_RECORD_SIZE, "repoint_count": len(repoints), "repoints": repoints,
        },
        "hooks": hook_rows,
        "hook_policy": {
            "global_flag_api_untouched": True,
            "trainer_specific_flag_hooks": 6,
            "rematch_hooks": 1,
            "exact_trainerbattle_rebind_hooks": 1,
            "stable_party_setup_hooks": 1,
            "optimized_private_create_npc_party_hooked": False,
        },
        "runtime_id_rebindings": [{
            "label": "map 3/20 initial double after trainerbattle argument load",
            "script_site_offset": double_site,
            "script_site_address": GBA_ROM_BASE + double_site,
            "script_trainer_id_preserved": int(initial_double_binding["source_trainer_id"], 0),
            "runtime_trainer_id": int(initial_double_binding["trainer_id"], 0),
            "physical_defeat_flag_owner": int(initial_double_binding["defeat_flag_owner_trainer_id"], 0),
        }],
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(), "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
            "forbidden_gba_range": [FORBIDDEN_GBA_START, FORBIDDEN_GBA_END],
            "forbidden_range_avoided": gba_end <= FORBIDDEN_GBA_START or gba_start >= FORBIDDEN_GBA_END,
        },
        "release_patches": {
            "incremental": {"path": PATCH_INCREMENTAL.as_posix(), "source_sha256": _sha(stage), "target_sha256": _sha(output_raw), "size": len(incremental), "sha256": _sha(incremental), "exact": True},
            "cumulative": {"path": PATCH_CUMULATIVE.as_posix(), "source_sha256": _sha(base), "target_sha256": _sha(output_raw), "size": len(cumulative), "sha256": _sha(cumulative), "exact": True},
        },
        "change_audit": {"changed_byte_count": len(changed), "declared_spans": declared, "outside_declared_span_count": 0},
        "invariants": {
            "input_stage31_hash_pinned": _sha(stage) == EXPECTED_INPUT_SHA256,
            "base_v1_4_0_hash_pinned": _sha(base) == EXPECTED_BASE_SHA256,
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "selected_encounters_25": len(source["bindings"]) == 25,
            "selected_parties_unique_25": len(serialized["party_rows"]) == 25 and len({row["party_sha256"] for row in serialized["party_rows"]}) == 25,
            "sidecar_members_71": len(serialized["sidecars"]) == 71,
            "normal_single_23_double_2": source["format_audit"]["single"] == 23 and source["format_audit"]["double"] == 2,
            "hardcoded_double_rejects_single": source["format_audit"]["hardcoded_double_rejects_single"],
            "trainer_table_repoints_24": len(repoints) == 24,
            "trainer_specific_runtime_hooks_9": len(hook_rows) == 9,
            "initial_double_script_keeps_physical_id":
                _u16(output, double_site, "initial double output trainer")
                == int(initial_double_binding["source_trainer_id"], 0),
            "global_flag_api_untouched": all(
                output[_rom_offset(address, 8, "global flag API"):
                       _rom_offset(address, 8, "global flag API") + 8]
                == stage[_rom_offset(address, 8, "global flag API"):
                         _rom_offset(address, 8, "global flag API") + 8]
                for address in (FLAG_SET_ADDRESS & ~1, FLAG_CLEAR_ADDRESS & ~1, FLAG_GET_ADDRESS & ~1)
            ),
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "forbidden_p4b2c_range_avoided": gba_end <= FORBIDDEN_GBA_START or gba_start >= FORBIDDEN_GBA_END,
            "declared_changes_only": not outside,
            "incremental_bps_exact": True, "cumulative_bps_exact": True,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("Trainer V5 static invariant failed")
    symbols_doc = {
        "schema_version": 1, "task": TASK, "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"], "trampolines": runtime["trampolines"],
        "symbols": runtime["symbols"], "hooks": hook_rows,
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbols_doc),
        GENERATED_HEADER.as_posix(): header,
        SERIALIZED_JSON.as_posix(): _stable(serialized_doc),
        BINDING_REPORT.as_posix(): _csv_bytes(binding_report_rows),
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CUMULATIVE.as_posix(): cumulative,
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: Mapping[str, Any]) -> dict[str, Any]:
    runner = root / RUNNER
    if not runner.is_file():
        _fail(f"Trainer V5 mGBA runner missing: {runner}")
    with tempfile.TemporaryDirectory(prefix="vega-trainer-v5-smoke-") as temporary:
        temp = Path(temporary)
        executable = temp / "mgba-trainer-v5-smoke"
        _run([
            _host_cc(root), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(RUNNER), "-o", str(executable), "-lmgba",
        ], "Trainer V5 libmGBA smoke compile", cwd=root)
        entry = metadata["entrypoints"]
        common_args = [
            hex(entry["TrainerV5Runtime_Probe"]),
            hex(entry["TrainerV5Runtime_SetTrainerFlag"]),
            hex(entry["TrainerV5Runtime_ClearTrainerFlag"]),
            hex(entry["TrainerV5Runtime_HasTrainerBeenFought"]),
            hex(entry["TrainerV5Runtime_GetRematchTrainerId"]),
            hex(metadata["payload"]["trainer_table_address"]),
        ]
        payloads: list[str] = []
        processes: list[subprocess.Popen[str]] = []
        for index in (1, 2):
            rom = temp / f"32_trainer_v5_run{index}.gba"
            save = temp / f"32_trainer_v5_run{index}.sav"
            rom.write_bytes(stage)
            processes.append(subprocess.Popen(
                [str(executable), str(rom), str(save), *common_args], cwd=root,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ))
        for index, process in enumerate(processes, start=1):
            try:
                stdout, stderr = process.communicate(timeout=150)
            except subprocess.TimeoutExpired:
                for pending in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending in processes:
                    pending.communicate()
                _fail(f"Trainer V5 exact-ROM smoke run {index} timed out")
            if process.returncode:
                for pending in processes:
                    if pending.poll() is None:
                        pending.kill()
                detail = (stderr or stdout).strip()
                _fail(f"Trainer V5 exact-ROM smoke run {index} failed ({process.returncode}): {detail[-6000:]}")
            payloads.append(stdout.strip())
        first, second = (json.loads(payload) for payload in payloads)
        if first != second or first.get("status") != "PASS" or not all(first.get("checks", {}).values()):
            _fail("Trainer V5 exact-ROM smoke is not deterministic all-PASS")
        first["process_runs"] = 2
        first["rom_sha256"] = _sha(stage)
        return first


def _report(metadata: Mapping[str, Any], mgba: Mapping[str, Any]) -> bytes:
    checks = mgba["checks"]
    text = f"""# Trainer Redesign V5 / Stage 32 integration foundation

## 結論

- 同梱V5からTohoku開始～第一badge前の25 encounterを選定し、23 SINGLE / 2 DOUBLEを実ROMへ接続した。
- 25 partyはすべて一意で、71 memberを16-byte party ABIと16-byte sidecar V1へserializeした。
- 従来catalog-onlyだったability、nature、exact IV、6EVを安定した公開`BuildTrainerPartySetup`後のlive consumerで適用する。
- rematch高IDは物理trainerのdefeat flagへ写像し、既存saveの範囲と再戦状態を維持する。
- 初回DOUBLEのrooted scriptは物理ID 702のまま保持し、trainerbattle引数消費後だけV5 ID 1342へ再束縛する。
- kind 4/7はDOUBLE契約を必須とし、SINGLE partyをvalidatorが拒否する。

## ROM結合

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Payload: `{metadata['payload']['address']:#010x}` / {metadata['payload']['size']} bytes
- Expanded trainer table: `{metadata['trainer_table']['new_address']:#010x}` / {metadata['trainer_table']['new_count']} records
- Trainer table repoints: {metadata['trainer_table']['repoint_count']}
- Runtime hooks: {len(metadata['hooks'])}
- Allocator overlap: {metadata['allocation']['overlap_count']}
- P4B2c forbidden range avoided: {metadata['allocation']['forbidden_range_avoided']}
- Declared span外変更: {metadata['change_audit']['outside_declared_span_count']}

## focused exact-ROM smoke

- ABI probe / hook binding: {checks['probe_and_hook_binding']}
- normal field entry to first rival: {checks['normal_entry']}
- SINGLE party + sidecar live fields: {checks['single_party_sidecar']}
- trainer AI record consumption: {checks['ai_records']}
- rooted kind-4 DOUBLE / party sidecar / four-controller entry: {checks['double_entry']}
- scheduler win path: {checks['win_path']}
- scheduler loss path: {checks['loss_path']}
- rematch ID mapping: {checks['rematch_mapping']}
- high-ID defeat flag mapping: {checks['flag_mapping']}
- save/reload persistence: {checks['save_reload']}
- deterministic process runs: {mgba['process_runs']}

Stage 31の全fresh監査は再実行せず、このtaskのbuilder、source hash、schema/format、allocator、変更span、BPS往復、focused libmGBA exact-ROM smokeを実行した。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT, *, run_mgba: bool = True) -> dict[str, bytes]:
    outputs = build_runtime_outputs(root)
    repeated = build_runtime_outputs(root)
    if outputs != repeated:
        _fail("Trainer V5 runtime build is not byte deterministic")
    if not run_mgba:
        return outputs
    stage = outputs[OUTPUT_ROM.as_posix()]
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    mgba = _mgba_fixture(Path(root), stage, metadata)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(), "status": mgba["status"],
        "process_runs": mgba["process_runs"], "all_checks": all(mgba["checks"].values()),
    }
    metadata["invariants"]["exact_rom_process_runs_2"] = mgba["process_runs"] == 2
    metadata["invariants"]["exact_rom_all_checks"] = all(mgba["checks"].values())
    if not all(metadata["invariants"].values()):
        _fail("Trainer V5 exact-ROM invariant failed")
    outputs[OUTPUT_META.as_posix()] = _stable(metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


def _write_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: Mapping[str, bytes]) -> None:
    differences = [relative for relative, expected in outputs.items() if not (root / relative).is_file() or (root / relative).read_bytes() != expected]
    if differences:
        _fail("Trainer V5 generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT, run_mgba=args.mode != "build-runtime-only")
        if args.mode in ("build", "build-runtime-only"):
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, TrainerV5BuildError) as error:
        print(f"Trainer V5 Stage31 integration failed: {error}", file=sys.stderr)
        return 1
    print(f"Trainer V5 Stage31 integration {args.mode}: PASS stage={_sha(outputs[OUTPUT_ROM.as_posix()])} artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
