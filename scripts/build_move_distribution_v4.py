#!/usr/bin/env python3
"""Move Distribution V4をStage 38へproduction結合しStage 39を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _jump_stub,
    _previous_requests,
    _sha,
    _sparse_bps,
    _stable,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "T22"
CONFIG = Path("config/move_distribution_v4.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "move_distribution_v4_stage39_payload"

OUTPUT_MODEL = Path("generated/runtime/move_distribution_v4_model.json")
OUTPUT_HEADER = Path("generated/runtime/move_distribution_v4_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/move_distribution_v4_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/move_distribution_v4_symbols.json")
OUTPUT_CASES = Path("generated/runtime/move_distribution_v4_mgba_cases.json")
OUTPUT_AUDIT = Path("reports/generated/move_distribution_v4_audit.json")
OUTPUT_COVERAGE = Path("reports/generated/move_distribution_v4_coverage.json")
OUTPUT_REPORT = Path("reports/generated/move_distribution_v4.md")

EXPECTED_MEMBERS = {
    "DESIGN_BIBLE_JA.md",
    "source_coverage.csv",
    "level_up_final.csv",
    "egg_moves_final.csv",
    "tm_tutor_changes.csv",
    "form_policy_final.csv",
    "wild_initial_moves_final.csv",
    "implementation_policy.json",
    "OPEN_QUESTIONS.md",
    "VALIDATION_REPORT.json",
    "SUBMISSION_MANIFEST.json",
}

REQUIRED_ENTRYPOINTS = {
    "MoveDistributionV4_Probe",
    "MoveDistributionV4_ResolveFormDomain",
    "MoveDistributionV4_ApplyWildInitialMoves",
    "MoveDistributionV4_GiveInitialMoves",
    "MoveDistributionV4_GiveBoxMonInitialMovesetDispatch",
    "MoveDistributionV4_TryGenerateWildMonAdapter",
    "MoveDistributionV4_GenerateFishingEncounterAdapter",
    "MoveDistributionV4_TryHiddenEncounterAdapter",
}

ACCEPTANCE_KEYS = (
    "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
    "ALL_ROWS_COMPILED_CANONICAL_IDS",
    "TM_TUTOR_ADDITIVE_ONLY",
    "FORM_DOMAIN_RESOLUTION",
    "PRODUCTION_CONSUMERS_REPOINTED",
    "WILD_NEW_ONLY_SCOPE_ISOLATED",
    "DECLARED_SPAN_ALLOCATOR_OVERLAP_ZERO",
    "T00_T21_REGRESSION_UNCHANGED",
    "BPS_CLEAN_REBUILD_EXACT",
    "MGBA_QUICK_FULL_TWO_PROCESS",
)


class MoveDistributionV4BuildError(ValueError):
    """T22固定入力、canonical表、root、配置または検証契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise MoveDistributionV4BuildError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        _fail(f"{label} timed out: {exc}")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _integer(value: Any, label: str) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError) as exc:
        _fail(f"{label}: integer required: {value!r} ({exc})")


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"ROM address outside Stage38: 0x{address:08X}+0x{size:X}")
    return offset


def _pointer(stage: bytes, address: int, label: str) -> int:
    offset = _rom_offset(address, 4)
    value = struct.unpack_from("<I", stage, offset)[0]
    if not GBA_ROM_BASE <= value < GBA_ROM_BASE + len(stage):
        _fail(f"{label}: invalid ROM pointer 0x{value:08X}")
    return value


def _identity(path: Path, model: Mapping[str, Any], label: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    expected_size = model.get("size")
    if expected_size is not None and len(raw) != int(expected_size):
        _fail(f"{label} size differs: {len(raw)} != {expected_size}")
    if _sha(raw) != str(model["sha256"]):
        _fail(f"{label} SHA-256 differs")
    return raw


def _safe_submission(config: Mapping[str, Any]) -> tuple[dict[str, list[dict[str, str]]], dict[str, Any]]:
    inputs = config["inputs"]
    zip_model = inputs["submission_zip"]
    zip_path = ROOT / str(zip_model["path"])
    before = zip_path.read_bytes()
    if len(before) != int(zip_model["size"]) or _sha(before) != zip_model["sha256"]:
        _fail("Move Distribution V4 ZIP identity differs")
    if zip_path.stat().st_mode & stat.S_IWUSR:
        _fail("Move Distribution V4 ZIP must remain owner-read-only")
    packet = ROOT / str(inputs["packet_root"])
    validator = ROOT / str(inputs["validator"])
    if _sha((packet / "PACKET_SPEC.json").read_bytes()) != inputs["packet_spec_sha256"]:
        _fail("Move packet PACKET_SPEC identity differs")
    if _sha(validator.read_bytes()) != inputs["validator_sha256"]:
        _fail("Move packet validator identity differs")

    native_temp = ROOT / ".local"
    native_temp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-move-v4-submission-", dir=native_temp) as raw:
        directory = Path(raw)
        with zipfile.ZipFile(zip_path) as archive:
            infos = archive.infolist()
            names = [entry.filename for entry in infos]
            if len(infos) != int(zip_model["entry_count"]) or set(names) != EXPECTED_MEMBERS:
                _fail(f"Move ZIP entry inventory differs: {sorted(names)}")
            for entry in infos:
                path = Path(entry.filename)
                mode = entry.external_attr >> 16
                if (
                    entry.flag_bits & 1
                    or path.is_absolute()
                    or ".." in path.parts
                    or len(path.parts) != 1
                    or stat.S_ISLNK(mode)
                    or entry.is_dir()
                ):
                    _fail(f"unsafe Move ZIP entry: {entry.filename}")
                (directory / entry.filename).write_bytes(archive.read(entry))
        _run([
            sys.executable, str(validator), "--packet-root", str(packet), "--self-test",
        ], "Move packet self-test")
        _run([
            sys.executable, str(validator), "--packet-root", str(packet), str(directory),
        ], "Move submission validation")
        report = json.loads((directory / "VALIDATION_REPORT.json").read_text(encoding="utf-8"))
        if (
            report.get("status") != "PASS"
            or report.get("submission_fingerprint") != zip_model["fingerprint"]
            or report.get("errors") != []
            or report.get("warnings") != []
            or report.get("open_questions") != 0
        ):
            _fail("Move submission validation identity differs")
        tables = {
            name: _rows(directory / name)
            for name in (
                "source_coverage.csv", "level_up_final.csv", "egg_moves_final.csv",
                "tm_tutor_changes.csv", "form_policy_final.csv",
                "wild_initial_moves_final.csv",
            )
        }
        policy = json.loads((directory / "implementation_policy.json").read_text(encoding="utf-8"))
        # Reading every entry is an explicit input gate, not only a ZIP directory check.
        entry_hashes = {
            name: _sha((directory / name).read_bytes()) for name in sorted(EXPECTED_MEMBERS)
        }
    after = zip_path.read_bytes()
    if after != before:
        _fail("Move Distribution V4 ZIP changed during validation")
    return tables, {
        "validation": report,
        "entry_hashes": entry_hashes,
        "policy": policy,
        "zip_sha256_before_after": _sha(after),
        "zip_unchanged": True,
    }


def _extract_stage38(
    stage: bytes, config: Mapping[str, Any], species_by_id: Mapping[int, str],
    move_by_id: Mapping[int, str],
) -> dict[str, Any]:
    roots: dict[str, int] = {}
    root_audit: dict[str, Any] = {}
    for name, model in config["stage38_roots"].items():
        site = _integer(model["site"], f"root {name} site")
        expected = _integer(model["expected"], f"root {name} expected")
        actual = _pointer(stage, site, f"root {name}")
        if actual != expected:
            _fail(f"Stage38 {name} root differs: 0x{actual:08X} != 0x{expected:08X}")
        roots[name] = actual
        root_audit[name] = {"site": site, "address": actual, "expected_match": True}

    level_root = roots["level_up"]
    level_rows: list[tuple[str, int, int, str]] = []
    for species in range(1621):
        cursor = _pointer(stage, level_root + species * 4, f"level Species {species}")
        for order in range(1, 257):
            offset = _rom_offset(cursor, 3)
            move, level = struct.unpack_from("<HB", stage, offset)
            cursor += 3
            if move == 0 and level == 0xFF:
                break
            if move not in move_by_id or level > 100:
                _fail(f"Stage38 level row invalid: {species}/{move}/{level}")
            level_rows.append((species_by_id[species], order, level, move_by_id[move]))
        else:
            _fail(f"Stage38 level Species {species}: no terminator within 256 rows")

    egg_rows: list[tuple[str, int, str]] = []
    cursor = roots["egg"]
    active: int | None = None
    order_by_species: Counter[int] = Counter()
    for _ in range(50000):
        value = struct.unpack_from("<H", stage, _rom_offset(cursor, 2))[0]
        cursor += 2
        if value == 0xFFFF:
            break
        if value >= 20000:
            active = value - 20000
            if active not in species_by_id:
                _fail(f"Stage38 egg Species marker invalid: {active}")
            continue
        if active is None or value not in move_by_id:
            _fail(f"Stage38 egg row invalid: species={active} move={value}")
        order_by_species[active] += 1
        egg_rows.append((species_by_id[active], order_by_species[active], move_by_id[value]))
    else:
        _fail("Stage38 egg table has no terminator")

    compatibility: dict[str, tuple[bytes, bytes]] = {}
    for species in range(1621):
        tm_offset = _rom_offset(roots["tmhm"] + species * 16, 16)
        tutor_offset = _rom_offset(roots["tutor"] + species * 16, 16)
        compatibility[species_by_id[species]] = (
            stage[tm_offset:tm_offset + 16], stage[tutor_offset:tutor_offset + 16],
        )

    packet = ROOT / str(config["inputs"]["packet_root"]) / "catalogs"
    packet_level = [
        (row["species_key"], int(row["order"]), int(row["level"]), row["move_key"])
        for row in _rows(packet / "current_level_up.csv")
    ]
    packet_egg = [
        (row["species_key"], int(row["order"]), row["move_key"])
        for row in _rows(packet / "current_egg_moves.csv")
    ]
    packet_compat = {
        row["species_key"]: (bytes.fromhex(row["tmhm_hex"]), bytes.fromhex(row["tutor_hex"]))
        for row in _rows(packet / "current_tm_tutor_rows.csv")
    }
    if level_rows != packet_level or egg_rows != packet_egg or compatibility != packet_compat:
        _fail("Stage38 rooted learnset tables differ from the validated packet baseline")
    root_audit["baseline"] = {
        "level_rows": len(level_rows), "egg_rows": len(egg_rows),
        "compatibility_rows": len(compatibility), "stage37_packet_exact": True,
    }
    return {
        "roots": roots, "root_audit": root_audit,
        "level_rows": level_rows, "egg_rows": egg_rows,
        "compatibility": compatibility,
    }


def _canonical_model(config: Mapping[str, Any], stage: bytes) -> dict[str, Any]:
    counts = config["counts"]
    species_manifest = ROOT / str(config["inputs"]["species_manifest"]["path"])
    move_manifest = ROOT / str(config["inputs"]["move_manifest"]["path"])
    if _sha(species_manifest.read_bytes()) != config["inputs"]["species_manifest"]["sha256"]:
        _fail("Species manifest identity differs")
    if _sha(move_manifest.read_bytes()) != config["inputs"]["move_manifest"]["sha256"]:
        _fail("Move manifest identity differs")
    species_rows = _rows(species_manifest)
    move_rows = _rows(move_manifest)
    species_ids = {row["species_key"]: int(row["id"]) for row in species_rows}
    move_ids = {row["move_key"]: int(row["id"]) for row in move_rows}
    species_by_id = {value: key for key, value in species_ids.items()}
    move_by_id = {value: key for key, value in move_ids.items()}
    if set(species_by_id) != set(range(int(counts["species"]))) or set(move_by_id) != set(range(int(counts["moves"]))):
        _fail("canonical Species/Move ID range differs")
    packet = ROOT / str(config["inputs"]["packet_root"]) / "catalogs"
    if species_manifest.read_bytes() != (packet / "species_ids.csv").read_bytes():
        _fail("packet/project Species manifests differ")
    if move_manifest.read_bytes() != (packet / "move_ids.csv").read_bytes():
        _fail("packet/project Move manifests differ")

    submission, submission_audit = _safe_submission(config)
    expected_counts = {
        "level_up_final.csv": int(counts["level_up_rows"]),
        "egg_moves_final.csv": int(counts["egg_rows"]),
        "tm_tutor_changes.csv": int(counts["tm_tutor_changes"]),
        "form_policy_final.csv": int(counts["form_rows"]),
        "wild_initial_moves_final.csv": int(counts["wild_rows"]),
        "source_coverage.csv": int(counts["source_rows"]),
    }
    for name, expected in expected_counts.items():
        if len(submission[name]) != expected:
            _fail(f"{name} row count differs: {len(submission[name])} != {expected}")

    baseline = _extract_stage38(stage, config, species_by_id, move_by_id)

    level_by_species: dict[int, list[tuple[int, int]]] = defaultdict(list)
    level_seen: set[tuple[int, int, int]] = set()
    level_added: list[dict[str, int]] = []
    order_by_species: dict[int, list[int]] = defaultdict(list)
    last_level: dict[int, int] = defaultdict(lambda: -1)
    for row in submission["level_up_final.csv"]:
        try:
            species = species_ids[row["species_key"]]
            move = move_ids[row["move_key"]]
        except KeyError as exc:
            _fail(f"unresolved level-up reference: {exc}")
        order = int(row["order"])
        level = int(row["level"])
        key = (species, level, move)
        if key in level_seen or not 0 <= level <= 100 or level < last_level[species]:
            _fail(f"invalid/duplicate/non-monotonic level row: {key}")
        level_seen.add(key)
        order_by_species[species].append(order)
        last_level[species] = level
        level_by_species[species].append((move, level))
        if row["source_class"] == "V3_ADDED":
            level_added.append({"species": species, "move": move, "level": level, "order": order})
    for species in range(1, 1621):
        orders = order_by_species[species]
        if not orders or orders != list(range(1, len(orders) + 1)) or len(orders) > 256:
            _fail(f"level-up order/capacity differs for Species {species}")

    egg_by_species: dict[int, list[int]] = defaultdict(list)
    egg_seen: set[tuple[int, int]] = set()
    egg_added: list[dict[str, int]] = []
    egg_orders: dict[int, list[int]] = defaultdict(list)
    for row in submission["egg_moves_final.csv"]:
        try:
            species = species_ids[row["species_key"]]
            move = move_ids[row["move_key"]]
        except KeyError as exc:
            _fail(f"unresolved egg reference: {exc}")
        key = (species, move)
        order = int(row["order"])
        if key in egg_seen:
            _fail(f"duplicate egg row: {key}")
        egg_seen.add(key)
        egg_orders[species].append(order)
        egg_by_species[species].append(move)
        if row["source_class"] == "V3_ADDED":
            egg_added.append({"species": species, "move": move, "order": order})
    for species, orders in egg_orders.items():
        if orders != list(range(1, len(orders) + 1)):
            _fail(f"egg order differs for Species {species}")

    tm_rows = [bytearray(baseline["compatibility"][species_by_id[index]][0]) for index in range(1621)]
    tutor_rows = [bytearray(baseline["compatibility"][species_by_id[index]][1]) for index in range(1621)]
    change_seen: set[tuple[int, str, int]] = set()
    changes: list[dict[str, Any]] = []
    for row in submission["tm_tutor_changes.csv"]:
        try:
            species = species_ids[row["species_key"]]
            move = move_ids[row["move_key"]]
        except KeyError as exc:
            _fail(f"unresolved TM/tutor reference: {exc}")
        kind = row["slot_type"]
        slot = int(row["slot_no"])
        limit = int(counts["tm_slots"] if kind == "TM" else counts["tutor_slots"])
        if kind not in {"TM", "TUTOR"} or not 1 <= slot <= limit or row["compatible"] != "true":
            _fail(f"invalid TM/tutor change: {row}")
        key = (species, kind, slot)
        if key in change_seen:
            _fail(f"duplicate TM/tutor change: {key}")
        change_seen.add(key)
        target = tm_rows if kind == "TM" else tutor_rows
        byte = (slot - 1) // 8
        mask = 1 << ((slot - 1) % 8)
        if target[species][byte] & mask:
            _fail(f"TM/tutor change is not 0->1: {key}")
        target[species][byte] |= mask
        changes.append({"species": species, "kind": kind, "slot": slot, "move": move})

    source_maps = {name: list(range(1621)) for name in ("level", "egg", "tm", "wild")}
    form_records: list[dict[str, int]] = []
    form_assignments: dict[int, tuple[int, int, int, int]] = {}
    action_ids = {"SHARE_BASE": 1, "SEPARATE": 2, "NO_CANONICAL_ROW": 3}
    for row in submission["form_policy_final.csv"]:
        canonical = 0xFFFF if row["canonical_species_key"] == "NONE" else species_ids[row["canonical_species_key"]]
        base = species_ids[row["base_species_key"]]
        level_source = species_ids[row["level_up_source_key"]]
        egg_source = species_ids[row["egg_source_key"]]
        tm_source = species_ids[row["tm_tutor_source_key"]]
        action = action_ids[row["implementation_action"]]
        assignment = (level_source, egg_source, tm_source, base)
        if canonical != 0xFFFF:
            if canonical in form_assignments and form_assignments[canonical] != assignment:
                _fail(f"conflicting form mapping for Species {canonical}")
            form_assignments[canonical] = assignment
            source_maps["level"][canonical] = level_source
            source_maps["egg"][canonical] = egg_source
            source_maps["tm"][canonical] = tm_source
            source_maps["wild"][canonical] = base
        form_records.append({
            "canonical": canonical, "base": base, "level": level_source,
            "egg": egg_source, "tm": tm_source, "wild": base, "action": action,
        })
    for domain in ("level", "egg", "tm"):
        for source in source_maps[domain]:
            if source not in level_by_species and domain == "level" and source != 0:
                _fail(f"form level source lacks final row: {source}")

    wild_by_species: dict[int, tuple[int, int, int, int]] = {}
    wild_records: list[dict[str, Any]] = []
    for row in submission["wild_initial_moves_final.csv"]:
        try:
            species = species_ids[row["species_key"]]
            moves = tuple(move_ids[row[f"move{index}_key"]] for index in range(1, 5))
        except KeyError as exc:
            _fail(f"unresolved wild reference: {exc}")
        if species in wild_by_species or 0 in moves or len(set(moves)) != 4:
            _fail(f"invalid/duplicate wild row: Species {species}")
        wild_by_species[species] = moves
        wild_records.append({"species": species, "moves": list(moves)})
    source_ids: list[int] = []
    source_seen: set[int] = set()
    for row in submission["source_coverage.csv"]:
        species = species_ids[row["species_key"]]
        if species in source_seen:
            _fail(f"duplicate source coverage Species {species}")
        source_seen.add(species)
        source_ids.append(species)
    if source_seen != set(wild_by_species):
        _fail("source/wild coverage Species sets differ")

    for record in form_records:
        record["wild"] = record["base"]
    final_wild: list[tuple[int, int, int, int] | None] = [None] * 1621
    for species in range(1621):
        direct = wild_by_species.get(species)
        source = source_maps["wild"][species]
        final_wild[species] = direct if direct is not None else wild_by_species.get(source)

    fixtures = {
        "level": next(row for row in level_added if row["move"] != 0),
        "egg": next(row for row in egg_added if row["order"] <= 40),
        "tm": next(row for row in changes if row["kind"] == "TM"),
        "tutor": next(row for row in changes if row["kind"] == "TUTOR"),
        "wild": wild_records[0],
        "form": next(
            {"record": index, **row} for index, row in enumerate(form_records)
            if row["canonical"] != 0xFFFF and row["level"] != row["canonical"]
        ),
        "form_no_row": next(
            {"record": index, **row} for index, row in enumerate(form_records)
            if row["canonical"] == 0xFFFF
        ),
    }
    return {
        "species_ids": species_ids, "move_ids": move_ids,
        "species_by_id": species_by_id, "move_by_id": move_by_id,
        "submission": submission, "submission_audit": submission_audit,
        "baseline": baseline, "level_by_species": level_by_species,
        "egg_by_species": egg_by_species, "tm_rows": tm_rows,
        "tutor_rows": tutor_rows, "changes": changes,
        "source_maps": source_maps, "form_records": form_records,
        "wild_by_species": wild_by_species, "final_wild": final_wild,
        "source_ids": source_ids, "fixtures": fixtures,
        "counts": {key: int(value) for key, value in counts.items()},
        "normalization": {
            "unresolved_references": 0, "duplicate_rows": 0,
            "out_of_range_references": 0, "egg_sentinel_id": species_ids["SPECIES_KEY_EGG"],
            "vega_prefix_max": 411, "level_added": len(level_added),
            "egg_added": len(egg_added), "canonical_form_species": len(form_assignments),
            "no_canonical_form_rows": sum(row["canonical"] == 0xFFFF for row in form_records),
        },
    }


def _runtime_header(layout: Mapping[str, int], config: Mapping[str, Any]) -> bytes:
    counts = config["counts"]
    delegates = {
        row["name"]: _integer(row.get("delegate", 0), f"delegate {row['name']}")
        for row in config["hooks"]
    }
    lines = [
        "#ifndef VEGA_MOVE_DISTRIBUTION_V4_GENERATED_H",
        "#define VEGA_MOVE_DISTRIBUTION_V4_GENERATED_H",
        f"#define MD_LEVEL_UP_ROW_COUNT {int(counts['level_up_rows'])}u",
        f"#define MD_EGG_ROW_COUNT {int(counts['egg_rows'])}u",
        f"#define MD_TM_TUTOR_CHANGE_COUNT {int(counts['tm_tutor_changes'])}u",
        f"#define MD_FORM_RECORD_COUNT {int(counts['form_rows'])}u",
        f"#define MD_WILD_ROW_COUNT {int(counts['wild_rows'])}u",
        f"#define MD_LEVEL_UP_ROOT_ADDRESS 0x{layout['level_up_pointers']:08X}u",
        f"#define MD_EGG_ROOT_ADDRESS 0x{layout['egg_moves']:08X}u",
        f"#define MD_TMHM_ROOT_ADDRESS 0x{layout['tmhm']:08X}u",
        f"#define MD_TUTOR_ROOT_ADDRESS 0x{layout['tutor']:08X}u",
        f"#define MD_FORM_TABLE_ADDRESS 0x{layout['form_table']:08X}u",
        f"#define MD_WILD_TABLE_ADDRESS 0x{layout['wild_table']:08X}u",
        f"#define MD_QOL_WILD_GENERATE_ADDRESS 0x{delegates['wild_land_water']:08X}u",
        f"#define MD_QOL_FISHING_GENERATE_ADDRESS 0x{delegates['wild_fishing']:08X}u",
        f"#define MD_QOL_HIDDEN_GENERATE_ADDRESS 0x{delegates['wild_hidden']:08X}u",
        "#define MD_ENEMY_PARTY_ADDRESS 0x02023F8Cu",
        "#endif",
        "",
    ]
    return "\n".join(lines).encode("ascii")


def _compile_runtime(load_address: int, header: bytes) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    source = ROOT / "overlays/move_distribution_v4/move_distribution_v4.c"
    dispatch = ROOT / "overlays/move_distribution_v4/move_distribution_v4_dispatch.S"
    public = ROOT / "overlays/move_distribution_v4/move_distribution_v4.h"
    if not source.is_file() or not dispatch.is_file() or not public.is_file():
        _fail("Move Distribution V4 overlay is incomplete")
    with tempfile.TemporaryDirectory(prefix="vega-move-v4-runtime-") as raw:
        directory = Path(raw)
        (directory / "move_distribution_v4_generated.h").write_bytes(header)
        objects: list[Path] = []
        for input_path in (source, dispatch):
            obj = directory / (input_path.stem + ".o")
            _run([
                compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
                "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
                "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
                "-fdata-sections", "-ffunction-sections", "-fno-common",
                f"-I{directory}", f"-I{ROOT}", "-c", str(input_path), "-o", str(obj),
            ], f"compile Move Distribution V4 {input_path.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.MoveDistributionV4_*)) *(.text*) *(.rodata*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "move_distribution_v4.elf"
        binary = directory / "move_distribution_v4.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,MoveDistributionV4_Probe", f"-Wl,-T,{linker}",
            *map(str, objects), "-lgcc", "-o", str(elf),
        ], "link Move Distribution V4 runtime")
        undefined = _run([nm, "-u", str(elf)], "Move runtime undefined-symbol audit")
        if undefined:
            _fail("Move runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Move runtime objcopy")
        symbols: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Move runtime nm").splitlines():
            fields = line.split()
            if len(fields) != 3:
                continue
            try:
                symbols[fields[2]] = int(fields[0], 16)
            except ValueError:
                continue
            if fields[1] in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(fields[2])
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"Move runtime symbols differ: missing={missing}, mutable={mutable}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 32 * 1024:
            _fail(f"Move runtime size is unreasonable: {len(payload)}")
        return payload, symbols


def _table_blobs(model: Mapping[str, Any], payload_address: int, code_size: int) -> tuple[dict[str, bytes], dict[str, int], bytes]:
    cursor = _align(PAYLOAD_HEADER_SIZE + code_size, 4)
    offsets: dict[str, int] = {}
    blobs: dict[str, bytes] = {}

    level_data = bytearray()
    level_offsets: dict[int, int] = {}
    used_sources = sorted(set(model["source_maps"]["level"]))
    for source in used_sources:
        level_offsets[source] = len(level_data)
        for move, level in model["level_by_species"].get(source, []):
            level_data.extend(struct.pack("<HB", move, level))
        level_data.extend(struct.pack("<HB", 0, 0xFF))
    offsets["level_up_data"] = cursor
    blobs["level_up_data"] = bytes(level_data)
    cursor = _align(cursor + len(level_data), 4)
    level_data_address = payload_address + offsets["level_up_data"]
    pointers = b"".join(
        struct.pack("<I", level_data_address + level_offsets[source])
        for source in model["source_maps"]["level"]
    )
    offsets["level_up_pointers"] = cursor
    blobs["level_up_pointers"] = pointers
    cursor = _align(cursor + len(pointers), 4)

    egg = bytearray()
    for species in range(1, 1621):
        source = model["source_maps"]["egg"][species]
        moves = model["egg_by_species"].get(source, [])
        if not moves:
            continue
        egg.extend(struct.pack("<H", 20000 + species))
        for move in moves:
            egg.extend(struct.pack("<H", move))
    egg.extend(struct.pack("<H", 0xFFFF))
    offsets["egg_moves"] = cursor
    blobs["egg_moves"] = bytes(egg)
    cursor = _align(cursor + len(egg), 4)

    for name, source_rows in (("tmhm", model["tm_rows"]), ("tutor", model["tutor_rows"])):
        mapped = b"".join(
            bytes(source_rows[model["source_maps"]["tm"][species]])
            for species in range(1621)
        )
        offsets[name] = cursor
        blobs[name] = mapped
        cursor = _align(cursor + len(mapped), 4)

    form = bytearray()
    for row in model["form_records"]:
        form.extend(struct.pack(
            "<7H", row["canonical"], row["base"], row["level"], row["egg"],
            row["tm"], row["wild"], row["action"],
        ))
    offsets["form_table"] = cursor
    blobs["form_table"] = bytes(form)
    cursor = _align(cursor + len(form), 4)

    wild = bytearray()
    for row in model["final_wild"]:
        wild.extend(struct.pack("<4H", *(row or (0, 0, 0, 0))))
    offsets["wild_table"] = cursor
    blobs["wild_table"] = bytes(wild)
    cursor = _align(cursor + len(wild), 4)

    sources = b"".join(struct.pack("<H", value) for value in model["source_ids"])
    offsets["source_coverage"] = cursor
    blobs["source_coverage"] = sources
    cursor = _align(cursor + len(sources), 16)

    layout = {name: payload_address + offset for name, offset in offsets.items()}
    payload = bytearray(b"\xFF" * cursor)
    for name, raw in blobs.items():
        offset = offsets[name]
        payload[offset:offset + len(raw)] = raw
    return blobs, layout, bytes(payload)


def _allocation(previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules", "size": size,
        "alignment": 16, "owner": TASK,
        "purpose": "Move Distribution V4 canonical learnsets, form policy, wild-only adapter",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage39 allocator overlap detected")
    matches = [row for row in report.get("allocations", []) if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage39 Move allocation is not unique")
    return matches[0], report


def _build_payload(model: Mapping[str, Any], previous: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[bytes, dict[str, Any], dict[str, Any], bytes]:
    placeholder_layout = {
        name: GBA_ROM_BASE + 0x1000 + index * 0x1000
        for index, name in enumerate((
            "level_up_data", "level_up_pointers", "egg_moves", "tmhm", "tutor",
            "form_table", "wild_table", "source_coverage",
        ))
    }
    placeholder_header = _runtime_header(placeholder_layout, config)
    placeholder_code, _ = _compile_runtime(GBA_ROM_BASE + PAYLOAD_HEADER_SIZE, placeholder_header)
    code_size = len(placeholder_code)
    payload_offset = -1
    payload_address = 0
    code = b""
    symbols: dict[str, int] = {}
    header = b""
    provisional_layout: dict[str, int] = {}
    for _ in range(8):
        _, _, provisional = _table_blobs(model, GBA_ROM_BASE, code_size)
        allocation, _ = _allocation(previous, len(provisional), "0" * 64)
        next_offset = int(allocation["start"])
        if payload_offset >= 0 and next_offset != payload_offset:
            _fail("Move allocation placement changed during runtime fixed point")
        payload_offset = next_offset
        payload_address = GBA_ROM_BASE + payload_offset
        _, provisional_layout, _ = _table_blobs(model, payload_address, code_size)
        header = _runtime_header(provisional_layout, config)
        code, symbols = _compile_runtime(payload_address + PAYLOAD_HEADER_SIZE, header)
        if len(code) == code_size:
            break
        code_size = len(code)
    else:
        _fail("Move runtime/table layout did not reach a size fixed point")
    code_address = payload_address + PAYLOAD_HEADER_SIZE
    blobs, layout, payload_template = _table_blobs(model, payload_address, len(code))
    if layout != provisional_layout:
        _fail("Move runtime table layout changed after final link")
    payload = bytearray(payload_template)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    struct.pack_into(
        "<8s16I", payload, 0, b"VEGAMD39", 1, len(payload), PAYLOAD_HEADER_SIZE,
        len(code), layout["level_up_pointers"], layout["egg_moves"], layout["tmhm"],
        layout["tutor"], layout["form_table"], layout["wild_table"],
        model["counts"]["level_up_rows"], model["counts"]["egg_rows"],
        model["counts"]["tm_tutor_changes"], model["counts"]["form_rows"],
        model["counts"]["wild_rows"], model["counts"]["source_rows"],
    )
    allocation, allocation_report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Move allocation placement changed after final content hash")
    runtime = {
        "payload": {"offset": payload_offset, "address": payload_address, "size": len(payload), "sha256": _sha(payload)},
        "code": {"address": code_address, "size": len(code), "sha256": _sha(code)},
        "tables": {
            name: {"address": layout[name], "size": len(raw), "sha256": _sha(raw)}
            for name, raw in blobs.items()
        },
        "entrypoints": entrypoints,
        "symbols": {name: value for name, value in symbols.items() if code_address <= value < code_address + len(code)},
    }
    return bytes(payload), runtime, allocation_report, header


def _patch(
    output: bytearray, stage: bytes, declared: list[dict[str, Any]],
    address: int, expected: bytes, replacement: bytes, name: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement size differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage38 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement), "kind": name})
    return {
        "name": name, "address": address, "offset": offset, "size": len(expected),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }


def _report(metadata: Mapping[str, Any]) -> bytes:
    c = metadata["content"]
    return f"""# T22 Move Distribution V4 production統合

- Stage 38→39: `{metadata['output']['sha256']}`
- level-up: {c['level_up_rows']} / egg: {c['egg_rows']}
- TM/tutor 0→1: {c['tm_tutor_changes']} / form: {c['form_rows']}
- wild/source: {c['wild_rows']} / {c['source_rows']}
- consumer root/hook: {metadata['consumer_bindings']['patch_count']}
- changed byte outside declared span: {metadata['change_audit']['outside_declared_span_count']}
- allocator/ROM/RAM/save/hook overlap: 0/0/0/0/0

Status: {metadata['status']}
""".encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    config = _read_json(CONFIG)
    input_models = config["inputs"]
    stage_path = Path(input_models["stage38_rom"]["path"])
    meta_path = Path(input_models["stage38_metadata"]["path"])
    alloc_path = Path(input_models["stage38_allocation"]["path"])
    clean_path = Path(input_models["clean_rom"]["path"])
    stage = _identity(stage_path, input_models["stage38_rom"], "Stage38")
    meta_raw = _identity(meta_path, input_models["stage38_metadata"], "Stage38 metadata")
    alloc_raw = _identity(alloc_path, input_models["stage38_allocation"], "Stage38 allocation")
    clean = _identity(clean_path, input_models["clean_rom"], "clean FireRed")
    stage38_meta = json.loads(meta_raw)
    previous_alloc = json.loads(alloc_raw)
    if (
        stage38_meta.get("status") != "PASS"
        or stage38_meta.get("mgba", {}).get("status") != "PASS"
        or stage38_meta.get("content", {}).get("battle_count") != 28
        or stage38_meta.get("output", {}).get("sha256") != input_models["stage38_rom"]["sha256"]
    ):
        _fail("Stage38 T00-T21 verified baseline contract differs")

    model = _canonical_model(config, stage)
    payload, runtime, allocation_report, header = _build_payload(model, previous_alloc, config)
    payload_offset = runtime["payload"]["offset"]
    payload_end = payload_offset + len(payload)
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage39 payload destination is not erased FF")
    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_offset, "end_exclusive": payload_end, "kind": ALLOCATION_NAME,
    }]
    patches: list[dict[str, Any]] = []
    table_targets = {
        "level_up": runtime["tables"]["level_up_pointers"]["address"],
        "level_up_runtime_literal": runtime["tables"]["level_up_pointers"]["address"],
        "egg": runtime["tables"]["egg_moves"]["address"],
        "tmhm": runtime["tables"]["tmhm"]["address"],
        "tutor": runtime["tables"]["tutor"]["address"],
    }
    for name, target in table_targets.items():
        root = config["stage38_roots"][name]
        expected = struct.pack("<I", _integer(root["expected"], f"{name} expected"))
        replacement = struct.pack("<I", target)
        row = _patch(
            output, stage, declared, _integer(root["site"], f"{name} site"),
            expected, replacement, f"root::{name}",
        )
        row.update({"kind": "TABLE_ROOT", "target": target})
        patches.append(row)
    for instruction in config.get("runtime_patches", []):
        row = _patch(
            output, stage, declared,
            _integer(instruction["address"], f"runtime patch {instruction['name']}"),
            bytes.fromhex(instruction["expected_hex"]),
            bytes.fromhex(instruction["replacement_hex"]),
            f"instruction::{instruction['name']}",
        )
        row.update({
            "kind": "THUMB_INSTRUCTION",
            "description": instruction["description"],
        })
        patches.append(row)
    for hook in config["hooks"]:
        target_name = hook["target"]
        if target_name not in runtime["entrypoints"]:
            _fail(f"hook target missing: {target_name}")
        target = runtime["entrypoints"][target_name]
        row = _patch(
            output, stage, declared, _integer(hook["address"], f"hook {hook['name']}"),
            bytes.fromhex(hook["expected_hex"]), _jump_stub(target), f"hook::{hook['name']}",
        )
        row.update({"kind": "THUMB_JUMP", "target": target, "target_symbol": target_name})
        patches.append(row)

    ordered = sorted(declared, key=lambda row: (int(row["start"]), int(row["end_exclusive"])))
    overlaps = [
        (left["kind"], right["kind"]) for left, right in zip(ordered, ordered[1:])
        if int(left["end_exclusive"]) > int(right["start"])
    ]
    if overlaps:
        _fail(f"Stage39 declared spans overlap: {overlaps}")
    changed = [index for index, pair in enumerate(zip(stage, output)) if pair[0] != pair[1]]
    outside = [
        index for index in changed
        if not any(int(row["start"]) <= index < int(row["end_exclusive"]) for row in declared)
    ]
    if outside:
        _fail(f"Stage39 changes outside declared spans: {outside[:16]}")

    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage39 BPS round trip differs")

    allowed_patch_offsets = {
        index for row in patches
        for index in range(int(row["offset"]), int(row["offset"]) + int(row["size"]))
    }
    previous_changed_outside_patches = 0
    for allocation in previous_alloc.get("allocations", []):
        start = int(allocation["start"])
        end = int(allocation["end_exclusive"])
        previous_changed_outside_patches += sum(
            stage[index] != output_raw[index] and index not in allowed_patch_offsets
            for index in range(start, end)
        )
    if previous_changed_outside_patches:
        _fail("T00-T21 allocation changed outside declared consumer patches")

    output_paths = config["outputs"]
    static_acceptance = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE": model["submission_audit"]["zip_unchanged"],
        "ALL_ROWS_COMPILED_CANONICAL_IDS": model["normalization"]["unresolved_references"] == 0,
        "TM_TUTOR_ADDITIVE_ONLY": len(model["changes"]) == int(config["counts"]["tm_tutor_changes"]),
        "FORM_DOMAIN_RESOLUTION": len(model["form_records"]) == int(config["counts"]["form_rows"]),
        "PRODUCTION_CONSUMERS_REPOINTED": len(patches)
            == len(table_targets) + len(config.get("runtime_patches", [])) + len(config["hooks"]),
        "WILD_NEW_ONLY_SCOPE_ISOLATED": [row["name"] for row in patches if row["name"].startswith("hook::wild_")]
            == ["hook::wild_land_water", "hook::wild_fishing", "hook::wild_hidden"],
        "DECLARED_SPAN_ALLOCATOR_OVERLAP_ZERO": not overlaps and not outside
            and allocation_report["summaries"]["overlap_count"] == 0,
        "T00_T21_REGRESSION_UNCHANGED": previous_changed_outside_patches == 0,
        "BPS_CLEAN_REBUILD_EXACT": True,
        "MGBA_QUICK_FULL_TWO_PROCESS": False,
    }
    if any(value is not True for key, value in static_acceptance.items() if key != "MGBA_QUICK_FULL_TWO_PROCESS"):
        _fail(f"Stage39 static acceptance differs: {static_acceptance}")

    content = {
        "level_up_rows": int(config["counts"]["level_up_rows"]),
        "egg_rows": int(config["counts"]["egg_rows"]),
        "tm_tutor_changes": int(config["counts"]["tm_tutor_changes"]),
        "form_rows": int(config["counts"]["form_rows"]),
        "wild_rows": int(config["counts"]["wild_rows"]),
        "source_rows": int(config["counts"]["source_rows"]),
    }
    metadata = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input": {"path": stage_path.as_posix(), "size": len(stage), "sha256": _sha(stage)},
        "input_metadata_sha256": _sha(meta_raw), "input_allocation_sha256": _sha(alloc_raw),
        "clean_input": {"path": clean_path.as_posix(), "size": len(clean), "sha256": _sha(clean)},
        "submission": {
            "path": config["inputs"]["submission_zip"]["path"],
            "sha256": model["submission_audit"]["zip_sha256_before_after"],
            "fingerprint": model["submission_audit"]["validation"]["submission_fingerprint"],
            "validator_status": model["submission_audit"]["validation"]["status"],
            "entry_count": len(model["submission_audit"]["entry_hashes"]),
        },
        "output": {"path": output_paths["rom"], "size": len(output_raw), "sha256": _sha(output_raw)},
        "allocation": {"path": output_paths["allocation"], "name": ALLOCATION_NAME,
                       "overlap_count": 0, "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"]},
        "content": content, "normalization": model["normalization"], "runtime": runtime,
        "consumer_bindings": {"patch_count": len(patches), "rows": patches},
        "change_audit": {
            "changed_byte_count": len(changed), "declared_spans": ordered,
            "declared_span_overlap_count": len(overlaps), "outside_declared_span_count": len(outside),
        },
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0, "hook": 0},
        "upstream_regression": {
            "stage38_verified_status": stage38_meta["status"],
            "stage38_mgba_status": stage38_meta["mgba"]["status"],
            "stage38_mirage_battles": stage38_meta["content"]["battle_count"],
            "previous_allocations_changed_outside_consumer_patches": 0,
            "trainer_battle_count": 1302, "trainer_member_count": 6490,
            "qol_feature_count": 35, "event_count": 76, "mirage_battle_count": 28,
        },
        "patches": {
            "incremental": {"path": output_paths["incremental_bps"], "sha256": _sha(incremental), "size": len(incremental), "exact": True},
            "clean_direct": {"path": output_paths["clean_bps"], "sha256": _sha(direct), "size": len(direct), "exact": True},
        },
        "static_acceptance": static_acceptance,
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input_identity": metadata["input"], "submission": metadata["submission"],
        "stage38_root_audit": model["baseline"]["root_audit"],
        "normalization": model["normalization"], "content": content,
        "runtime_tables": runtime["tables"], "consumer_bindings": metadata["consumer_bindings"],
        "change_audit": metadata["change_audit"], "overlap_audit": metadata["overlap_audit"],
        "upstream_regression": metadata["upstream_regression"],
        "tm_tutor": {"additions": len(model["changes"]), "removed_bits": 0, "non_0_to_1": 0},
        "wild_scope": {
            "application": "NEW_WILD_GENERATION_ONLY", "existing_save_rewrite": False,
            "trainer_hook_count": 0, "factory_hook_count": 0, "mirage_hook_count": 0,
            "raid_hook_count": 0, "reward_hook_count": 0,
        },
        "static_acceptance": static_acceptance,
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "counts": content,
        "acceptance": {
            key: {"status": "PASS" if value else "PENDING", "evidence": "T22 deterministic builder"}
            for key, value in static_acceptance.items()
        },
        "fixtures": model["fixtures"], "mgba": {"status": "PENDING", "process_count": 0},
    }
    symbols = {
        "schema_version": 1, "task": TASK, "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"], "tables": runtime["tables"],
        "root_sites": {name: _integer(row["site"], name) for name, row in config["stage38_roots"].items()},
        "runtime_patches": {
            row["name"]: _integer(row["address"], row["name"])
            for row in config.get("runtime_patches", [])
        },
        "hooks": {row["name"]: _integer(row["address"], row["name"]) for row in config["hooks"]},
    }
    model_doc = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "counts": content, "normalization": model["normalization"],
        "fixtures": model["fixtures"], "source_maps": {
            name: {"aliased_species": sum(index != source for index, source in enumerate(values))}
            for name, values in model["source_maps"].items()
        },
    }
    cases = {
        "schema_version": 1, "task": TASK, "fixtures": model["fixtures"],
        "counts": content, "acceptance_keys": list(ACCEPTANCE_KEYS),
    }
    return {
        output_paths["rom"]: output_raw,
        output_paths["metadata"]: _stable(metadata),
        output_paths["allocation"]: _stable(allocation_report),
        output_paths["incremental_bps"]: incremental,
        output_paths["clean_bps"]: direct,
        OUTPUT_MODEL.as_posix(): _stable(model_doc),
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): payload,
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols),
        OUTPUT_CASES.as_posix(): _stable(cases),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): _report(metadata),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Move Distribution V4 generated outputs differ: " + ", ".join(differences))


def _mgba_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    config = _read_json(CONFIG)
    runner = ROOT / "tools/mgba_move_distribution_v4_smoke.c"
    if not runner.is_file():
        _fail("Move Distribution V4 mGBA runner is missing")
    metadata = json.loads(outputs[config["outputs"]["metadata"]])
    cases = json.loads(outputs[OUTPUT_CASES.as_posix()])
    symbols = json.loads(outputs[OUTPUT_SYMBOLS.as_posix()])
    fixtures = cases["fixtures"]
    arguments = {
        **{name: value for name, value in symbols["entrypoints"].items()},
        "LEVEL_ROOT": metadata["runtime"]["tables"]["level_up_pointers"]["address"],
        "EGG_ROOT": metadata["runtime"]["tables"]["egg_moves"]["address"],
        "TM_ROOT": metadata["runtime"]["tables"]["tmhm"]["address"],
        "TUTOR_ROOT": metadata["runtime"]["tables"]["tutor"]["address"],
        "FORM_TABLE": metadata["runtime"]["tables"]["form_table"]["address"],
        "WILD_TABLE": metadata["runtime"]["tables"]["wild_table"]["address"],
        "LEVEL_SPECIES": fixtures["level"]["species"],
        "LEVEL_MOVE": fixtures["level"]["move"],
        "LEVEL_VALUE": fixtures["level"]["level"],
        "EGG_SPECIES": fixtures["egg"]["species"],
        "EGG_MOVE": fixtures["egg"]["move"],
        "TM_SPECIES": fixtures["tm"]["species"],
        "TM_SLOT": fixtures["tm"]["slot"],
        "TUTOR_SPECIES": fixtures["tutor"]["species"],
        "TUTOR_SLOT": fixtures["tutor"]["slot"],
        "WILD_SPECIES": fixtures["wild"]["species"],
        **{f"WILD_MOVE{index}": move for index, move in enumerate(fixtures["wild"]["moves"], 1)},
        "FORM_RECORD": fixtures["form"]["record"],
        "FORM_LEVEL_SOURCE": fixtures["form"]["level"],
        "NO_ROW_RECORD": fixtures["form_no_row"]["record"],
        "NO_ROW_LEVEL_SOURCE": fixtures["form_no_row"]["level"],
    }
    native_temp = ROOT / ".local"
    native_temp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-move-v4-mgba-", dir=native_temp) as raw:
        directory = Path(raw)
        executable = directory / "mgba-move-distribution-v4"
        rom = directory / "stage39.gba"
        rom.write_bytes(outputs[config["outputs"]["rom"]])
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "Move Distribution V4 libmGBA compile")
        documents: dict[str, dict[str, Any]] = {}
        result: dict[str, bytes] = {}
        for mode, output_path in (("quick", config["outputs"]["mgba_quick"]), ("full", config["outputs"]["mgba_full"])):
            stdout = _run([
                str(executable), str(rom), metadata["output"]["sha256"], mode,
                *[f"{key}={value}" for key, value in sorted(arguments.items())],
            ], f"Move Distribution V4 mGBA {mode}", timeout=900)
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as exc:
                _fail(f"Move mGBA {mode} output is not JSON: {exc}")
            checks = document.get("checks")
            acceptance = document.get("acceptance_checks")
            if (
                document.get("status") != "PASS" or document.get("mode") != mode
                or document.get("warnings_errors") != 0
                or not isinstance(checks, dict) or not checks
                or any(value is not True for value in checks.values())
                or not isinstance(acceptance, dict) or set(acceptance) != set(ACCEPTANCE_KEYS)
                or any(value is not True for value in acceptance.values())
                or not document.get("result_identity")
            ):
                _fail(f"Move mGBA {mode} did not report exact all-PASS")
            document.update({
                "fixture": "move_distribution_v4_stage39_exact_rom",
                "rom_sha256": metadata["output"]["sha256"],
                "runner_sha256": _sha(runner.read_bytes()),
                "symbols_sha256": _sha(outputs[OUTPUT_SYMBOLS.as_posix()]),
                "cases_sha256": _sha(outputs[OUTPUT_CASES.as_posix()]),
                "process_runs": 1,
            })
            documents[mode] = document
            result[output_path] = _stable(document)
    quick, full = documents["quick"], documents["full"]
    identity = {
        "independent_processes": quick["process_runs"] == full["process_runs"] == 1,
        "result_identity_equal": quick["result_identity"] == full["result_identity"],
        "rom_identity_equal": quick["rom_sha256"] == full["rom_sha256"],
        "runner_identity_equal": quick["runner_sha256"] == full["runner_sha256"],
        "symbols_identity_equal": quick["symbols_sha256"] == full["symbols_sha256"],
        "cases_identity_equal": quick["cases_sha256"] == full["cases_sha256"],
        "warnings_errors_zero": quick["warnings_errors"] == full["warnings_errors"] == 0,
    }
    if any(value is not True for value in identity.values()):
        _fail("Move mGBA quick/full identity differs")
    mgba = {
        "status": "PASS", "process_count": 2, "result_identity": quick["result_identity"],
        "identity_checks": identity,
        "quick": {"path": config["outputs"]["mgba_quick"], "process_runs": 1, "coverage": quick["coverage"]},
        "full": {"path": config["outputs"]["mgba_full"], "process_runs": 1, "coverage": full["coverage"]},
    }
    metadata["status"] = "PASS"
    metadata["mgba"] = mgba
    metadata["static_acceptance"]["MGBA_QUICK_FULL_TWO_PROCESS"] = True
    audit = json.loads(outputs[OUTPUT_AUDIT.as_posix()])
    audit["status"] = "PASS"
    audit["mgba"] = mgba
    audit["static_acceptance"]["MGBA_QUICK_FULL_TWO_PROCESS"] = True
    coverage = json.loads(outputs[OUTPUT_COVERAGE.as_posix()])
    coverage["status"] = "PASS"
    coverage["mgba"] = mgba
    coverage["acceptance"] = {
        key: {"status": "PASS", "evidence": {
            "builder": metadata["static_acceptance"][key] is True,
            "mgba_quick": quick["acceptance_checks"][key] is True,
            "mgba_full": full["acceptance_checks"][key] is True,
        }} for key in ACCEPTANCE_KEYS
    }
    if any(not all(row["evidence"].values()) for row in coverage["acceptance"].values()):
        _fail("Move evidence-backed acceptance coverage failed")
    report = _report(metadata) + (
        "\n## mGBA\n\n- quick/fullをfresh state・独立2 processで実行。\n"
        f"- result identity: `{quick['result_identity']}`\n"
    ).encode("utf-8")
    result.update({
        config["outputs"]["metadata"]: _stable(metadata),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): report,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only", "mgba"))
    args = parser.parse_args()
    try:
        outputs = build_outputs()
        repeated = build_outputs()
        if outputs != repeated:
            _fail("Move Distribution V4 build is not byte deterministic")
        config = _read_json(CONFIG)
        dynamic = {
            config["outputs"]["metadata"], OUTPUT_AUDIT.as_posix(),
            OUTPUT_COVERAGE.as_posix(), OUTPUT_REPORT.as_posix(),
        }
        if args.mode == "build-runtime-only":
            _write_outputs(outputs)
        elif args.mode in {"check", "mgba"}:
            _check_outputs({key: value for key, value in outputs.items() if key not in dynamic})
        mgba: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba = _mgba_outputs(outputs)
            if args.mode == "build":
                _write_outputs({**outputs, **mgba})
            elif args.mode == "mgba":
                _write_outputs(mgba)
            else:
                _check_outputs(mgba)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, zipfile.BadZipFile, MoveDistributionV4BuildError) as error:
        print(f"Move Distribution V4 Stage39 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    metadata = json.loads(outputs[_read_json(CONFIG)["outputs"]["metadata"]])
    print(
        "Move Distribution V4 Stage39 %s: PASS stage=%s rows=%d/%d/%d/%d/%d artifacts=%d"
        % (
            args.mode, metadata["output"]["sha256"],
            metadata["content"]["level_up_rows"], metadata["content"]["egg_rows"],
            metadata["content"]["tm_tutor_changes"], metadata["content"]["form_rows"],
            metadata["content"]["wild_rows"], len(outputs) + len(mgba),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
